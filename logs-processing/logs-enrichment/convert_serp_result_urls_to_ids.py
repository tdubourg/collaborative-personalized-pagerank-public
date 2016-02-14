#!/usr/bin/python

'''

This script will convert an SERP requerying "SERP" result file from string URLs to URLs IDs as assigned from the 
web crawl

'''

from time import time
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from univ_open import univ_open
from json import load as jload, dump as jdump

CLI_ARGS = ['serp_result_file', 'url_web_crawl_ids_mapping.lst(WARNING,NOT JSON FORMAT)', 'output_path']
OPTIONAL_ARGS = []
def main(stop_after_init=False):
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print 'Usage: %s %s %s' % (argv[0], ' '.join(CLI_ARGS), ' '.join(["[%s]" % x for x in OPTIONAL_ARGS]))
        print 'Currently missing parameters arguments:', ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    serp_result_file            = argv[1].strip()
    url_web_crawl_ids_mapping   = argv[2].strip()
    output_path                 = argv[-1].strip()

    t_init = time()

    print "Loading SERP..."
    with univ_open(serp_result_file, 'r') as f:
        serps = jload(f)
    print "Loaded"

    print "Loading urls-to-ids dict..."
    urls_to_ids = {}
    with univ_open(url_web_crawl_ids_mapping, 'r') as f:
        i = 0
        for line in f:
            line = line.strip().lower().replace("%0a", '')
            urls_to_ids[line] = i
            i += 1
    print "Loaded"

    print "Converting SERP..."
    t0 = time()
    not_converted = set()
    total_urls = set()
    converted_set = set()
    for query_serps in serps.values():
        for serp in query_serps:
            i = 0
            while i < len(serp['results']):
                pos, url = serp['results'][i]
                url = url.lower().replace('%0a', '')
                total_urls.add(url)
                try:
                    serp['results'][i] = (pos, urls_to_ids[url])
                    converted_set.add(url)
                except KeyError as err:
                    # Looks like this URL has not been seen during the web crawl, as it has no assigned ID
                    not_converted.add(url)
                    serp['results'].pop(i)
                    i -= 1
                i += 1
    print "Over", len(total_urls), "total different URLs from the SERP results,", len(not_converted), "could not be converted"
    if len(total_urls) - len(not_converted) < 600:
        print converted_set
    print "Done in", time()-t0

    print "Writing URLs to output file", output_path, "..."
    t0 = time()
    with univ_open(output_path, 'w+') as out:
        jdump(serps, out)
    print "Done in", time()-t0

    print "Script executed in", time() - t_init, "seconds"

if __name__ == '__main__':
    main()