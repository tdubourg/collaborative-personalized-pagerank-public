#!/usr/bin/python

'''

This script takes as input the resulting files of a "SERP Requerying" and outputs the list of URLs of the downloaded
SERPS, to be used as a seed for a web crawl, for instance.

'''

from time import time
from univ_open import univ_open
from json import load as jload
import os

CLI_ARGS = ['serp_crawl_result_file_serp.json', 'output_path']
OPTIONAL_ARGS = ['split_into_n']
def main(stop_after_init=False):
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print 'Usage: %s %s %s' % (argv[0], ' '.join(CLI_ARGS), ' '.join(["[%s]" % x for x in OPTIONAL_ARGS]))
        print 'Currently missing parameters arguments:', ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    crawl_result_file   = argv[1].strip()
    output_path         = argv[2].strip()
    split_into_n        = 1

    if argc > len(CLI_ARGS) + 1:
        split_into_n = int(argv[len(CLI_ARGS) + 1])

    t_init = time()
    t0 = time()
    print "Loading result file..."
    with univ_open(crawl_result_file, 'r') as f:
        serps = jload(f)
    print "Done in", time()-t0

    t0 = time()
    print "Writing URLs to output file", output_path, "..."
    # the set() is because we do not need multiple times the same URL
    # in the seed, and from the SERP it is actually pretty likely to happen 
    # on an example run, we went from 4070 urls to 2387 by adding the set()
    result = list(set([ \
        url \
        for query_serps in serps.values() \
        for serp in query_serps \
        for pos, url in serp['results']
    ]))
    urls_n = len(result)
    batch_size = urls_n/split_into_n
    i = 0
    # print urls_n, batch_size, split_into_n, (urls_n/split_into_n)*split_into_n
    for start in range(0, urls_n, batch_size):
        # print start
        i += 1
        dir, fname = os.path.split(output_path)
        outp = os.path.join(dir, "%03d_%s" % (i, fname))
        print "Dumping into", outp
        with univ_open(outp, 'w+') as out:
            out.write('\n'.join(result[start:start+batch_size]))
    print "Done in", time()-t0

    print "Script executed in", time() - t_init, "seconds"

if __name__ == '__main__':
    main()