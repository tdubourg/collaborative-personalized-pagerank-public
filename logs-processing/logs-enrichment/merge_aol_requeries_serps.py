#!/usr/bin/python

'''

This script takes as input the resulting files of a "SERP Requerying" and outputs the list of URLs of the downloaded
SERPS, to be used as a seed for a web crawl, for instance.

'''

from time import time
from json import load as jload, dump as jdump

import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))

from univ_open import univ_open

def merge_serps(s1, s2):
    """
        Merges s2's serps into s1
    """
    for querystr, query_serps in s2.iteritems():
        if querystr not in s1:
            s1[querystr] = query_serps
        else:
            # If there were already some results in the previous SERPs results dict
            # we take the one that as the highest number of SERPs (pages) as this is the one
            # that will contain the most data, and they are supposed to return the same results anyway
            if len(query_serps) > len(s1[querystr]):
                s1[querystr] = query_serps

CLI_ARGS = ['serp_crawl_result_file_serp1.json', 'serp_crawl_result_file_serp2.json ...', 'output_path']
OPTIONAL_ARGS = []
def main(stop_after_init=False):
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print 'Usage: %s %s %s' % (argv[0], ' '.join(CLI_ARGS), ' '.join(["[%s]" % x for x in OPTIONAL_ARGS]))
        print 'Currently missing parameters arguments:', ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    files = []
    for x in xrange(1, argc-1):
        files.append(argv[x].strip())

    output_path         = argv[-1].strip()

    t_init = time()
    t0 = time()
    print "Loading result files..."
    serps_combined = {}
    for crawl_result_file in files:
        print "Loading", crawl_result_file, "..."
        t1 = time()
        with univ_open(crawl_result_file, 'r') as f:
            merge_serps(serps_combined, jload(f))
        print "Done in", time()-t1
    print "All files done in", time()-t0

    print "Writing URLs to output file", output_path, "..."
    t0 = time()
    jdump(serps_combined, univ_open(output_path, 'w+'))
    print "Done in", time()-t0

    print "Script executed in", time() - t_init, "seconds"

if __name__ == '__main__':
    main()