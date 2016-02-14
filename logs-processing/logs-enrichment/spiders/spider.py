# -*- coding: utf-8 -*-

"""

What is the goal of this spider:
    To constitute a list of AOL Search Engine Logs (2006) entries that are still relevant / usable
     by looking at the SERP for the original query (from the logs) and looking for the originally clicked
     result.

What this spider does:
    1) Loads a list of SERP (Search Engine Results Page) URLs
    2) Extracts each result item
    3) Looks for the originally clicked result item among this items list. Note: We only compare the domains as
        the original logs from AOL only include the domain. If there is only one result with the same domain,
        on the same SERP, we assume it's the original one, else we throw things away
    4)  If the item is found in the results, save it (pass it to the item pipelines)
        Else, return nothing

Proxies handling: 
    The final behaviour we want to achieve here is to have a set of external facing IPs and execute a request every X
    seconds through every IP simultaneously so that we maximize our crawling speed.
    The issue is that Scrapy clearly exposes no easy way to schedule requests manually and even Downloader Middlewares
    do not offer an easy way to "delay" a given request. The only easy thing is to add a delay between every request
    on the same domain for instance, but we want the delay to be specific to each externally facing IP (thus, here: 
    a proxy).
    
    So, in order to achieve an approximated version of this behaviour, we keep requests that are too early for the given
    proxy in self.pending_requests and we release inside a the inject_requests() method that is being executed
    on an interval basis.
    
    There is a non negligible flaw here: If ever, we end up in the configuration where ALL requests through ALL proxies
    are executed very fast, crawl will stop, because no new requests have been returned, as all of them are kept in the
    self.pending_requests attribute.
    
    This is a bit unlikely as long as the proxies are slow enough to that the between-requests delay is close to the
    time it takes to make a request through a given proxy but it does happen in real life in the end. 
    
    So, in order to avoid this issue, if this happens, Scrapy will send the spider_idle signal and we will raise DontCloseSpider exception so that the
    spider does not get closed.
"""
import threading
from scrapy.exceptions import DontCloseSpider
from scrapy.http import Request

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
# from BeautifulSoup import BeautifulSoup
import logs_processing
from utils import l
from items import *
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from twisted.internet import reactor, defer
from time import time
from random import uniform as randu, randrange
import sys

PROXY_SPECIFIC_REQUEST_DELAY = 10 # seconds # does not matter in fact if we do not use proxies mode

class SERPSpider(BaseSpider):
    total_of_items_url = 0
    name = "serp"
    start_url = None
    start_urls = []
    urls_to_crawl = []
    pending_requests = {}  # We are using a dict in order to be able to remove requests without concurrency issues (by indexing them by ourselves)
    REQUESTS_INJECTION_TIMER_INTERVAL = 1  # in seconds
    PROXIES_INACTIVE_ALLOWANCE_FOR_RETRY_IN_MINUTES = 60  # Up to when to go search for inactive proxies, after this amount of time, proxies will be considered non-functional
    ACTIVE_PROXIES_THRESHOLD_FOR_RETRIES_ON_CONFIRMED = 10
    RETRY_ON_CONFIRMED_MIN_INTERVAL_IN_SEC = 3600
    GRAB_ALL_THE_SERPS = True  # if True, will not check whether there is at least one domain in common with the logs on the first SERP but just always download the SERP

    FORCE_COMPLETENESS = False  # if True, the spider should not close until all URLs have been successfully crawled
    SERPS_PER_QUERY = 50

    def __init__(self, logs_filename, export_path, query_strings_filename=None, use_proxies=False, use_tor_port=None):
        self.last_retry_on_confirmed = time()  # In order to avoid the retry_on_confirmed to be triggered immetiately
        self.closed = False
        self.requests_injection_timer = None
        self.urls_done = set()
        self.export_results_filename = export_path
        self.use_proxies = use_proxies
        print "use_proxies=", use_proxies
        self.logs_filename = logs_filename
        self.query_strings_filename = query_strings_filename
        self.log_processor = logs_processing.LogProcessor(self.logs_filename)
        self.crawled_urls = set()
        self.tor_port = None
        self.tor_proxy_host = None
        if use_proxies and use_tor_port is None:
            print "USING PROXIES"
            self.confirmed_proxies = {}
            self.alived_proxies = {}
            self.inactive_proxies_retry_in_progress = set()

        # In case we are using tor, this overrides the possible "use_proxies" parameter
        if use_tor_port is not None:
            self.tor_port = int(use_tor_port)
            self.tor_proxy_host = 'http://127.0.0.1:%s' % self.tor_port
            self.use_proxies = False
        
        self.connect_signals()

    def connect_signals(self):
        dispatcher.connect(self.spider_idle, signals.spider_idle)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def count_active_proxies_and_retry_on_inactive(self):
        now = time()
        five_minutes_ago = now - 5 * 60
        inactive_allowance_ago = now - self.PROXIES_INACTIVE_ALLOWANCE_FOR_RETRY_IN_MINUTES * 60
        active_proxies_count = 0
        # Note: As we are looping through the "alived proxies" we will not go through the unconfirmed proxies
        # as an alive proxy implies the proxy has been confirmed, too
        for p, t in self.alived_proxies.items():
            if t >= five_minutes_ago:
                active_proxies_count += 1
            # For all proxies that have been alive during the last hour but inactive for >= five minutes
            # it is probably that the proxy was not working properly at this time but we can retry it now, who knows?
            if p not in self.inactive_proxies_retry_in_progress and t <= five_minutes_ago and t >= inactive_allowance_ago:
                req = self.build_request_for_proxy(p, now)
                l("Injecting URL", req.url, "to retry on inactive proxy", p)
                self.inactive_proxies_retry_in_progress.add(p)
                self.inject_request(req)
        return active_proxies_count

    def retry_on_confirmed(self, active_proxies_count):
        # There are too few active proxies, let us retry on all the confirmed proxies
        now = time()
        if active_proxies_count <= self.ACTIVE_PROXIES_THRESHOLD_FOR_RETRIES_ON_CONFIRMED \
                and self.last_retry_on_confirmed <= (now - self.RETRY_ON_CONFIRMED_MIN_INTERVAL_IN_SEC):
            for p, c in self.confirmed_proxies.items():
                if c is True and p:  # Yes, no check on inactive_proxies_retry_in_progress, we want to retry them all!
                    req = self.build_request_for_proxy(p, now)
                    l("Injecting URL", req.url, "to retry on deeply inactive proxy", p)
                    self.inject_request(req)
            self.last_retry_on_confirmed = now

    def alive_proxy(self, p):
        self.confirmed_proxies[p] = True
        self.alived_proxies[p] = time()
        try:
            self.inactive_proxies_retry_in_progress.remove(p)
        except KeyError:
            # Well, this one was not in the retry list, nothing to worry about
            pass

    def inject_request(self, r):
        if r is None:
            l("Asked to inject a None request")
        l("Injecting new URL to crawl in the engine")
        # import scrapy.project
        return self.crawler.engine.crawl(r, self)

    def inject_requests(self):
        print "inject_requests()"
        if self.closed:
            print "But spider is closed!"
            return
        try:
            now = time()
            # Look for pending requests that would now have the right to be processed:
            for url, r in self.pending_requests.items():
                if r.meta['exec_time'] <= now:
                    l("Request to URL=", r.url, "can now be processed")
                    r.meta['exec_time'] = now
                    self.pending_requests.pop(url)  # Remove it from the pending requests
                    self.inject_request(r)
            
            active_proxies_count = self.count_active_proxies_and_retry_on_inactive()
            self.retry_on_confirmed(active_proxies_count)
        finally:  # No matter what happens, we have to schedule ourselves again else the crawler will hang forever
            print "Scheduling ourselves again..."
            self.schedule_requests_injection()

    def schedule_requests_injection(self):
        print "schedule_requests_injection()..."
        if not self.closed:  # Another check won't harm anyone
            l("Scheduling requests injection")
            self.requests_injection_timer = threading.Timer(
                self.REQUESTS_INJECTION_TIMER_INTERVAL,
                self.inject_requests
            )
            self.requests_injection_timer.start()

    def get_not_crawled_urls(self):
        not_crawled = self.set_of_urls_should_be_crawled - self.crawled_urls
        if self.use_proxies:
            # If we are in proxy mode, it is possible that all remaining requests are in the pending
            # requests, that is to say it is planned to crawl them but not right now in order to respect
            # the proxy-specific delay
            # so, remove all urls that are in the pending requests from the not_crawled set
            not_crawled -= set(self.pending_requests.keys())
        return not_crawled

    def inject_not_crawled_urls(self):
        print "inject_not_crawled_urls()..."
        not_crawled = self.get_not_crawled_urls()
        if not_crawled:
            # Some urls have not been crawled
            l("FORCE_COMPLETENESS=True and there are urls that have not been crawled, pushing them back \
into self.urls_to_crawl of urls to be crawled.\
            ")
            l("There are currently", len(not_crawled), "not crawled urls.")
            not_crawled_and_not_scheduled = not_crawled - set(self.urls_to_crawl)
            self.urls_to_crawl.extend(not_crawled_and_not_scheduled)
            i = 0
            if self.use_proxies and len(self.pending_requests) != 0:
                # There are still pending request, do not deal with anything, it is handled by the query scheduling of
                # the proxy mode
                return
            elif self.use_proxies:
                usable_proxies = [p for p, c in self.confirmed_proxies.items() if c]
                now = time()
                # Let us schedule a new query for every usable proxy, the rest of the queries
                # will be scheduled when we received responses from those queries
                for proxy in usable_proxies:
                    r = self.next_request(proxy, now)
                    self.inject_request(r)
            else:
                # When not using proxy, the delay is respected directly by Scrapy
                # so we just schedule everything and it will take care of the rest
                for _ in xrange(len(self.urls_to_crawl)):
                    if self.tor_proxy_host is not None:
                        proxy = self.tor_proxy_host
                    else:
                        proxy = None
                    r = self.build_request_for_proxy(proxy, time())
                    self.inject_request(r)
                    i += 1

    def spider_idle(self, spider):
        l("spider_idle signal received")
        if spider is self:
            dont_close = False
            if self.FORCE_COMPLETENESS:
                self.inject_not_crawled_urls()
                dont_close = True

            if len(self.pending_requests) is not 0 or len(self.urls_to_crawl) is not 0:
                l("Hey, do not close me, I still have things to do! (", len(self.pending_requests), "pending requests)",
                  "and still ", len(self.urls_to_crawl), "urls to be crawled.")
                dont_close = True

            if dont_close:
                raise DontCloseSpider()

    def generate_queries_urls(self):
        # We need to process the logs anyway as we need the inverted dictionary query string -> urls to keep _or not_
        # the resulting SERP
        result = []
        if self.query_strings_filename is not None:
            with open(self.query_strings_filename, 'r') as f:
                queries = set()
                for l in f:
                    l = l.strip().lower()
                    queries.add(l)
                    result.append(logs_processing.LogProcessor.generate_serp_url_from_keywords(l))
                self.log_processor.process(queries_filter=queries)
                if len(self.log_processor.serp_to_kw) < len(queries):
                    print "!!! Warning: we loaded", len(queries), "query string but the log processor only has mapping\
                     for the following queries:", self.log_processor.serp_to_kw
        else:
            result = self.log_processor.process()
        return result

    def start_requests(self):
        self.urls_to_crawl = self.generate_queries_urls()
        from random import shuffle
        # So that we do not always query in the same order, making it less likely for us to be banned
        shuffle(self.urls_to_crawl)
        self.set_of_urls_should_be_crawled = set(self.urls_to_crawl)
        print "----------------------------------------------------------------------------------"
        print "There are", len(self.urls_to_crawl), " SERP URLs to be crawled."
        print "----------------------------------------------------------------------------------"
        if not self.use_proxies:
            print "NOT USING PROXIES"
            if self.tor_port is not None:
                print "USING TOR ON PORT", self.tor_port
            # No use of proxies, fallback to parent's implementation and forward result
            self.start_urls = self.urls_to_crawl[:]
            self.urls_to_crawl = []  # all urls have been transferred to start_urls and will thus be in queue, this starting queue should thus be empty
            for req in super(SERPSpider, self).start_requests():
                if self.tor_port is not None:
                    req.meta['proxy'] = self.tor_proxy_host
                yield req
        else:
            print "USING PROXIES"
            l("Proxies list is", self.PROXIES)
            # Let us shuffle the proxy list so that we do not always do the same queries on the same proxies at start
            proxy_list_tmp = list(self.PROXIES)
            shuffle(proxy_list_tmp)
            self.PROXIES = set(proxy_list_tmp)
            self.schedule_requests_injection()
            # Generate a first request for every proxy (subsequent requests will be generated when parsing responses)
            for p in self.PROXIES:
                proxy = 'http://' + p
                self.confirmed_proxies[proxy] = False
                yield self.build_request_for_proxy(proxy, time())  # Directly executing time() here so that if there is
                                                                   # some delay between yields, we still are accurate

    def build_request_for_proxy(self, proxy, exec_time):
        if not self.urls_to_crawl:
            print "There is no other URLs to be crawled."
            return None
        return Request(
            # Note: Not using choice() because here we are popping from the list at the same time
            url=self.urls_to_crawl.pop(randrange(0, len(self.urls_to_crawl))),
            meta={
                'proxy': proxy,  # Rotating proxies to use different IPs
                'exec_time': exec_time
            },
        )

    PAGE_URL_PATTERN = "&page="
    def parse(self, response):
        l("\n\n--- PARSING ITEMLIST PAGE", response.url, "---\n\n")
        
        self.crawled_urls.add(response.url)
        hxs = HtmlXPathSelector(response)
        page_items = hxs.select('//li[@about="null"]')
        l("Found", len(page_items), "items on this page")

        try:
            pattern_position = response.url.find(self.PAGE_URL_PATTERN)
            is_first_page = pattern_position == -1
            serp_url_without_page_pattern = response.url if is_first_page else response.url[:pattern_position]
            kw = self.log_processor.serp_to_kw[serp_url_without_page_pattern]
            if not is_first_page:
                page_number = int(response.url[pattern_position+len(self.PAGE_URL_PATTERN):].strip())
            else:
                page_number = 1
            # self.urls_done.add(response.url)
            serp_logs_entries = self.log_processor.entries[kw]
            l("Domain of this serp, in the logs, is:", len(serp_logs_entries))
            serp_i = SERPItem()
            serp_i['kw'] = kw
            serp_i['page'] = page_number
            serp_i['results'] = []
            
            found = self.GRAB_ALL_THE_SERPS
            pos = 0 # Result position in the SERP
            for item in page_items:# Note: We assume that hxs.select() returns result in the order of the HTML
                url = item.select('.//a[@rel="f:url"]/@href').extract()[0]
                # Register this SERP result in the SERPItem (serp result= position, url)
                serp_i['results'].append((pos, url))
                l("Found url", url)
                domain = self.extract_domain(url)
                l("Domain is", domain)
                pos += 1
                for entry in serp_logs_entries:
                    if domain == entry[3]:
                        found = True
                        l("Found a result that is the same as before!")
                        # We store a "LogItem" as an item that is coming from the 2006 logs and that has been found
                        # still here in the current 2014 results
                        i = LogItem()
                        i['kw'] = kw
                        i['url'] = url
                        i['page'] = page_number
                        i['user_id'] = entry[0]
                        i['date'] = entry[1]
                        i['orig_pos'] = entry[2]
                        i['pos'] = (page_number-1)*10 + pos
                        l("Orig pos:", i['orig_pos'], "curr_pos:", i['pos'])
                        # Finally we are not going to need those for now, keeping them as a matter of reference on how to do it:
                        # i['title'] = BeautifulSoup(item.select('.//a[@rel="f:url"]/text()').extract()[0]).string
                        # i['desc'] = BeautifulSoup(item.select('.//p[@property="f:desc"]/text()').extract()[0]).string
                        yield i
                        break
            # In the case we found some interesting data for this SERP, also register the SERP item (that includes the
            # full SERP information, basically)
            if found or not is_first_page:
                # Was that the first SERP for this query?
                # If yes, as this SERP indeed has a common ranking link/we are keeping it, we will add the other
                # SERP pages that we want to crawl, if any
                if is_first_page:
                    print "This was the first page and we found common links, adding the other SERPs URLs..."
                    for i in xrange(2, self.SERPS_PER_QUERY + 1):
                        serp_url = response.url + '&page=%d' % i
                        print "Adding", serp_url
                        self.urls_to_crawl.append(serp_url)
                        self.set_of_urls_should_be_crawled.add(serp_url)

                yield serp_i
            else:
                print "There was no common domain between the logs and the returned SERP"
        except KeyError as err:
            print "KeyError? ->", err
            print "The serp URL", serp_url_without_page_pattern, "was not found in the inverted index (full=", response.url, ")"
            print self.log_processor.serp_to_kw
            pass  # Keyword not found? Well, ok, just don't return any item then, so, pass
        finally:
            for x in self.next_request_from_response(response):
                yield x
                
    def next_request_from_response(self, response):
        try:
            proxy = response.meta['proxy']
        except KeyError:
            proxy = None
            
        try:
            exec_time = response.meta['exec_time']
        except KeyError:
            exec_time = time()

        return self.next_request(proxy, exec_time)

    def next_request(self, proxy_param, exec_time_param):
        now = time()                    
        if self.use_proxies:
            # If there are still some URLs to be loaded with the same proxy
            if len(self.urls_to_crawl) > 0:
                # We load the next URL that has been assigned to the same proxy as the one used for the request
                # that triggered this reply
                # But first, let us compute whether this next request should be executed right now or not (in case
                # the proxy would have been exceptionally faster than the between-requests delay)
                delta = now - exec_time_param
                l("delta=", delta)
                if delta < PROXY_SPECIFIC_REQUEST_DELAY:
                    l("Adding a delay to respect between-requests delay for proxy", proxy_param)
                    # The difference between the required delta and the current delta
                    # Note: Randomness is in order not to be detected as bot by having a predictable behaviour
                    r = randu(0.5, 1.5)
                    l("Randomness factor r=", r)
                    exec_time_delay = r * (PROXY_SPECIFIC_REQUEST_DELAY - delta) 
                    exec_time = now + exec_time_delay # Approximation of execution time
                else:
                    exec_time = now
                    exec_time_delay = 0
                
                # Registering the fact that this proxy is working 
                # (we are building a new request for it = it returned some request = it's working)
                self.alive_proxy(proxy_param)
                next_req = self.build_request_for_proxy(proxy_param, exec_time)
                if exec_time_delay is 0:
                    l("Returning request ", next_req.url, "without a delay")
                    yield next_req
                else:
                    l("Storing request", next_req.url, "for later")
                    self.pending_requests[next_req.url] = next_req
        elif self.SERPS_PER_QUERY > 1:
            yield self.build_request_for_proxy(proxy_param, now)
        else:
            yield None

    def process_exception(self, response, exception, spider):
        l("Exception:", response, exception)

    def spider_closed(self, spider):
        # Note: We're using print rather than l() here because we never want this to be disabled, it's NOT debug logs
        if spider is self:
            # Run spider_idle, that might raise something if we should not stop now
            # self.spider_idle(spider)
            self.closed = True  # In order to avoid further request injection scheduling
            if self.requests_injection_timer is not None:
                self.requests_injection_timer.cancel()
            print "Spider is being closed"
            if self.use_proxies:
                if len(self.pending_requests) is not 0:
                    print "-------------------------------------------------------------------------"
                    print "INCOMPLETE CRAWL: the following requests have stayed in the pending list:"
                    print self.pending_requests
                    print "-------------------------------------------------------------------------"
                if len(self.urls_to_crawl) is not 0:
                    print "-------------------------------------------------------------------------"
                    print "UNFINISHED CRAWL:", len(self.urls_to_crawl), " SERP URLS are still to be crawled."
                    print "-------------------------------------------------------------------------"
                print "-------------------------------------------------------------------------"
                print "The following proxies have NOT been confirmed as working and should probably be taken away:"
                for p, confirmed in self.confirmed_proxies.items():
                    if confirmed is False:
                        print p
                print "-------------------------------------------------------------------------"
                print "The following proxies have NOT been alive in the last 15 minutes:"
                limit = time() - 15*60
                for p, t in self.alived_proxies.items():
                    if t <= limit:
                        print p
                print "-------------------------------------------------------------------------"
                print "The following proxies have been alive in the last 15 minutes:"
                for p, t in self.alived_proxies.items():
                    if t >= limit:
                        print p
                print "-------------------------------------------------------------------------"
                print "We did not manage to crawl the following URLs, you may want to try to crawl them again:"
                print self.set_of_urls_should_be_crawled - self.crawled_urls
                print "-------------------------------------------------------------------------"

    @staticmethod
    def extract_domain(url):
        try:
            url = url[url.index("//")+2:] # getting rid of protocol://
        except ValueError:
            # There was no protocol specified
            pass
        try:
            url = url[:url.index("/")] # getting rid of everything after the first "/"
        except ValueError:
            # Maybe it was a domain-onl   y url, with no "/"
            pass
        return url

    # Using a set so that if I put twice the same, it's still here only once
    # List is ephemeral IPs from GG Compute Engine
    PROXIES = {
        '127.0.0.1:8118',  # privoxy -> tor proxy, why not using it
        '127.0.0.1:8121',
        '127.0.0.1:8122',
        '127.0.0.1:8123',
        '127.0.0.1:8124',
        '127.0.0.1:8125',
        '127.0.0.1:8126',
        '127.0.0.1:8127',
        '127.0.0.1:8128',
        '127.0.0.1:8129',
        '127.0.0.1:8130',
    }

