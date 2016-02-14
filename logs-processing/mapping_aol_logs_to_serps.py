#!/usr/bin/python

"""

This script will provide a mapping between the URLs from the original AOL 2006 logs and the URLs from
the 2014 SERPs

Uses ~1G RAM
"""

from load_similar_users import load_set_of_similar_users
from univ_open import univ_open
# from extract_domain import extract_domain
from json import load as jload

class LogProcessor(object):
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        # Note: Althought we are not going to use all the indices in this list
        # we are still using a list in order to have fast direct element access
        # in order not to waste memory, though, we initialize everything to None
        # and then only initialize at 0 the users that we encounter in the logs
        self.serps_to_logs_mapping = {}
        self.logs_clicked_domain = {}

        try:
            excluded_qids = options['excluded_qids'] if options['excluded_qids'] is not None else set()
        except KeyError:
            excluded_qids = set()

        web_crawl_urls_to_domain_ids    = options['web_crawl_urls_to_domain_ids']
        query_str_to_ids                = options['query_str_to_ids']
        serps                           = options['serps']
        try:
            allowed_queries             = options['allowed_queries']
        except KeyError:
            allowed_queries             = None
            print "Warning, none set of allowed queries"


        with univ_open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if i % 500000 is 0:
                    print "Currently at line", i
                line = line.strip().split('\t')
                if len(line) is not 5:  # This is not a click log line (it could just be a search log line)
                    continue
                try:
                    user_id = int(line[0])
                    queryid = int(line[1].strip())
                    position = int(line[3].strip())
                    url_domain_id = int(line[4].strip())
                except ValueError as err:
                    print i, "has invalid user, query, position or url_domain id:", err
                except KeyError as err:
                    print "KeyError: ", err
                    print queryid, url_domain_id, user_id
                    exit()
                    
                if user_id not in options['allowed_users']:
                    continue

                if (allowed_queries is not None and queryid not in allowed_queries) or queryid in excluded_qids:
                    continue
                
                self.logs_clicked_domain.setdefault(queryid, {}).setdefault(position, []).append(url_domain_id)

        print "Result of clicks (pos, domain) gathering:"
        print self.logs_clicked_domain

        clicks = list()
        urls_serps = list()
        mapped = list()
        for queryid, click_entries in self.logs_clicked_domain.items():
            query_str = query_str_to_ids[queryid]
            if query_str not in serps:
                print "[INFO] Query", query_str, "was not in the serps results"
                continue
            for position, domain_ids in sorted(click_entries.items()):
                for domain_id in domain_ids:
                    clicks.append(domain_id)
                    for serp in serps[query_str]:
                        i = 0 
                        while i < len(serp['results']):
                            pos, urlid = serp['results'][i]
                            urls_serps.append(urlid)
                            urlid_domain_id = web_crawl_urls_to_domain_ids[urlid]
                            if domain_id == urlid_domain_id:
                                mapped.append((queryid, urlid))
                                if (queryid, urlid) in self.serps_to_logs_mapping:
                                    print (queryid, urlid), "was already mapped to", self.serps_to_logs_mapping[(queryid, urlid)]
                                    print "Remapping it to", domain_id
                                self.serps_to_logs_mapping[(queryid, urlid)] = domain_id
                                serp['results'].pop(i)  # popping it so that we do not insert it twice
                                i -= 1
                            i += 1

        print "We went through", len(set(clicks)), "different domain ids (", \
            len(clicks), "total (domain, pos) entries)" \
            , "from the logs,", \
            len(set(urls_serps)), "different urlids (", len(urls_serps), "(pos,urlids) entries in total)", \
            "from the SERPs and we mapped", len(mapped), "URLs,", len(set(mapped)), "different ones"

# def url_from_serps_to_web_crawl_id_groupped_by_queryid(serps_urls_set, web_crawl_urls_to_ids_file):
#         with univ_open(web_crawl_urls_to_ids_file, 'r') as f:
#             current_index = 0
#             for line in f:
#                 url = line.strip().lower()
#                 if url in serps_urls_set:
#                     urls_from_serps_web_crawl_id[url] = current_index
#                 current_index += 1

from time import time
def process_logfile(log_filepath, excluded_qids=None):
    lp = LogProcessor(log_filepath)
    t0 = time()
    lp.process(excluded_qids=excluded_qids)
    print "Processed in", time() - t0
    return lp

CLI_ARGS = [
    "log_file.converted.converted",
    "mdb_host",
    "targeted_query_users_pairs.lst",  # note: we will load by ourselves the extended list, of similar users
    "query_str_to_ids_mapping_file",
    "serp_requery_result_file_serp.converted.json"
    "web_crawl_graph_url_to_domain_ids_mapping_file",
    "output_path",
]
OPT_ARGS = []
def main():
    # TODO: 
    # load the requeried SERPs and store them as follows:
    # (query_id, [complete_list_of_urls_from_serps_in_order_of_appearance])
    # then when we go through the users' clicks, we do:
    # index = urls_from_serps[queryid].find(current_domain, lamdba: extract_domain())
    # urls_from_serps.pop(index)
    # somehow get the info about the domain ID in the logs, make the mapping, etc. ...
    import sys
    from sys import argv
    t_init = time()

    argc = len(sys.argv)

    if argc < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    logfile                                         = argv[1]
    mdb_host                                        = argv[2]
    queries_users_file                              = argv[3]
    query_str_to_ids_mapping_file                   = argv[4]
    serp_requery_result_file                        = argv[5]
    web_crawl_graph_url_to_domain_ids_mapping_file  = argv[6]
    output_path                                     = argv[-1]

    print "Loading target users..."
    queries_users_pairs = [tuple(map(int, _.strip().split(' '))) for _ in univ_open(queries_users_file, 'r')]
    targeted_users_set = set([_[1] for _ in queries_users_pairs])
    targeted_queries_set = set([_[0] for _ in queries_users_pairs])

    print "Loaded", len(targeted_users_set), "target users."

    print "Loading the set of their top similar users..."
    set_of_similar_users = load_set_of_similar_users(mdb_host, targeted_users_set)
    print "Loaded a total of", len(set_of_similar_users), "new allowed users"
    allowed_users = set_of_similar_users | targeted_users_set
    print len(allowed_users), "users allowed in total"

    print "Loading SERP file..."
    t0 = time()
    serps = jload(univ_open(serp_requery_result_file, 'r'))
    print "Done in", time() - t0

    print "Loading IDs <-> query strings..."
    t0 = time()
    queries_str_indexed_by_ids = [_.strip() for _ in univ_open(query_str_to_ids_mapping_file, 'r')]
    print "Done in", time() - t0

    print "Loading (web crawl) URL IDs <-> (logs) domain ids..."
    t0 = time()
    web_crawl_urls_to_domain_ids = [int(_.strip()) if _ != '\n' else None for _ in univ_open(web_crawl_graph_url_to_domain_ids_mapping_file, 'r')]
    print "Done in", time() - t0

    lp = LogProcessor(logfile)
    t0 = time()
    print "Starting process..."
    lp.process(
        serps=serps,
        allowed_queries=targeted_queries_set,
        allowed_users=allowed_users,
        query_str_to_ids=queries_str_indexed_by_ids,
        web_crawl_urls_to_domain_ids=web_crawl_urls_to_domain_ids
    )
    print "Done in", time() - t0

    print "Outputting result to", output_path, "..."
    with open(output_path, 'w+') as out:
        # q, urlid, domainid
        # meaning (q, urlid) -> domainid
        out.write('\n'.join(("%d,%d,%d" % (item[0][0], item[0][1], item[1]) for item in lp.serps_to_logs_mapping.items())))

    print "Done in", time() - t_init
    print "Terminating script."

if __name__ == '__main__':
    main()