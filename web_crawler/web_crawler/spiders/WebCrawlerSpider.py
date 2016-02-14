# from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spider import Spider
from web_crawler.items import WebPageItem
from scrapy.http import Request
from time import time
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from random import shuffle
# from scrapy.selector import HtmlXPathSelector
# import re

# deny_links_regexp = re.compile('.*(spampoison.*|cgi\/.*|accounts\.google\.com|login.*|microsoft\.com|\.(js|css|png|jpe?g|gif|bmp|tiff)(\?.*)?)', re.IGNORECASE)

class WebCrawlerSpider(Spider):
    name="web_crawler"
    """docstring for WebCrawlerSpider"""
    start_urls = []
    X_FIRST_LINKS_TO_FOLLOW_SAME_DOMAIN = 1  # We only follow the X first links of every page for same domain
    X_FIRST_LINKS_TO_FOLLOW_OTHER_DOMAINS = 7  # We only follow the X first links of every page for different domains
    MAX_DEPTH = 6  # 1500*50^3 = 1.6M, that's a good start
    PRINT_STATS_EVERY_X_CRAWLED_PAGES = 100
    links_rule = Rule(SgmlLinkExtractor(allow=r'.+', deny=(r'.*(spampoison.*|cgi\/.*|accounts\.google\.com|login.*|\.(js|css|png|jpe?g|gif|bmp|tiff)(\?.*)?)')), follow=False, callback='parse_item')
    def make_requests_from_url(self, url):
        return Request(url, dont_filter=True, meta={'start_url': url, 'metadepth': 0})

    # rules = (
        # Rule(SgmlLinkExtractor(allow=r'.+', deny=(r'.*(spampoison.*|cgi\/.*|accounts\.google\.com|login.*|microsoft\.com|\.(js|css|png|jpe?g|gif|bmp|tiff)(\?.*)?)')), follow=False, callback='parse_item'),
    # )

    def __init__(self, urls_fname, export_path, web_repository_export_path):
        """
            :param urls_fname = file name (or path) of the file containing the list 'seed' URLs - one per line
            :param export_path = the base name of the files we are going to export 'items' to (web graph/linking information)
            :param web_repository_export_path = the directory where we are going to save the GZipped content of the pages
        """
        print "Starting WebCrawlerSpider..."
        self.start_urls = self.get_start_urls(urls_fname)
        self.set_of_starting_urls = set(self.start_urls)
        # Add the starting URLs to the set of seen ones, so that we do not crawl them twice...
        self.urls_seen = set(self.start_urls)  # this set will be modified afterwards, no it is no a duplicated of self.set_of_starting_urls
        print "Loaded", len(self.start_urls), "starting urls"
        self.export_results_filename = export_path
        self.start_time = time()
        self.crawled_pages = 0
        self.web_pages_export_dir = web_repository_export_path
        self.last_stats_print_time = time()
        self.last_stats_print_n_crawled = 0
        # The 4 following variables are going to be used to compute the avg number of outlinks that we are following
        # in order to understand why we crawl so many less pages than expected
        self.outlinks_followed = 0
        self.outlinks_other_domains_followed = 0
        self.outlinks_same_domains_followed = 0
        self.outlinks_average_divider = 0
        super(WebCrawlerSpider, self).__init__()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse(self, response):
        self.crawled_pages += 1
        if (self.crawled_pages % self.PRINT_STATS_EVERY_X_CRAWLED_PAGES) is 0:
            print "\n", response.url, "-> We are currently at depth=", str(response.meta['metadepth']), "of start_url=", response.meta['start_url']
            delta = time()-self.start_time
            print \
                    "[STATS] Average crawl speed: ", \
                    self.crawled_pages, "urls crawled,", \
                    delta, "seconds,", \
                    self.crawled_pages / delta, "pages/second"
            curr_batch = self.crawled_pages - self.last_stats_print_n_crawled
            print \
                    "[STATS] Last batch crawl speed: ", \
                    "urls batch=", curr_batch, \
                    "speed=", curr_batch / (time() - self.last_stats_print_time), "pages/second"
            self.last_stats_print_time = time()
            self.last_stats_print_n_crawled = self.crawled_pages

        item = WebPageItem()
        item['url'] = response.url
        item['meta'] = response.meta
        item['html'] = response.body
        # The items' links are ALL of the links of the page (not only the new ones)
        # Note that only count a link to another page once
        # This is for web graph reconstitution purposes, not for crawling purposes
        item['links'] = set(self.links_rule.link_extractor.extract_links(response))

        if response.meta['metadepth'] >= self.MAX_DEPTH:
            # We're done with the crawl that started at this URL
            return item
        else:
            # But for crawling, we get rid of a couple of links and we also consider that URLs longer than 255 
            # are probably generated URLs that we do not want to crawl (generated URLs, that would lead to more generated ones)
            current_domain = self.extract_domain(response.url)
            unique_new_links = set([l for l in item['links'] if len(l.url) <= 255 and l.nofollow is False]) - self.urls_seen
            reqs = [item]
            n_urls_same_domain = 1
            n_urls_other_domains = 1
            for link in unique_new_links:
                if n_urls_same_domain > self.X_FIRST_LINKS_TO_FOLLOW_SAME_DOMAIN and n_urls_other_domains > self.X_FIRST_LINKS_TO_FOLLOW_OTHER_DOMAINS:
                    # We've got enough links to follow
                    break
                domain = self.extract_domain(link.url)
                if domain is current_domain:
                    if n_urls_same_domain > self.X_FIRST_LINKS_TO_FOLLOW_SAME_DOMAIN:
                        # Skip it, we reached the quota for same-domain links
                        continue
                    else:
                        n_urls_same_domain += 1
                        self.outlinks_same_domains_followed += 1
                else:
                    if n_urls_other_domains > self.X_FIRST_LINKS_TO_FOLLOW_OTHER_DOMAINS:
                        # Skip it, we reached the quota for other-domains links
                        continue
                    else:
                        n_urls_other_domains += 1
                        self.outlinks_other_domains_followed += 1
                # Note: we add the urls to self.urls_seen and we happen the related request to the requests to be performed
                # so only an URL that we will actually try to load will be added to self.urls_seend
                self.outlinks_followed += 1
                self.urls_seen.add(link)
                reqs.append(Request(link.url, meta={'start_url': response.meta['start_url'], 'metadepth': response.meta['metadepth'] + 1}))
            # This basically says "we have just run one more time the outlinks-following-code"
            # it is going to be used to compute the avg in spider_closed()
            self.outlinks_average_divider += 1
            # print "Grabbed following links:", links
            # Shuffle the list so that if a website always have first links to itself and then links to other website
            # we won't always crawl links to itself first
            shuffle(reqs)
            return reqs

    def spider_closed(self, spider):
        if spider is self:
            print "Spider is being closed."
            print "We have crawled a total of", self.crawled_pages, "pages."
            print "We originally loaded", len(self.set_of_starting_urls)
            print "We have tried to load", len(self.urls_seen), "different URLs"
            print "We have followed, in average,", \
                    self.outlinks_followed / float(self.outlinks_average_divider), "outlinks"
            print "We have followed, in average,", \
                    self.outlinks_same_domains_followed / float(self.outlinks_average_divider), "same-domain-outlinks"
            print "We have followed, in average,", \
                    self.outlinks_other_domains_followed / float(self.outlinks_average_divider), "other-domain-outlinks"
            print "Among the starting URLs, the following ones have not been seen afterwards:"
            print self.set_of_starting_urls - self.urls_seen


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

    def get_start_urls(self, fname):
        f = open(fname, 'r')
        res = []
        for url in f:
            res.append(url)
        f.close()
        return res
