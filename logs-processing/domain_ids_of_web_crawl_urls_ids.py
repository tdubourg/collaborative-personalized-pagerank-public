#!/usr/bin/python

'''

This script will build a mapping from URLs IDs from the web graph crawl to the "domain IDs" that have been assigned
to domains from the logs

'''

from time import time
from univ_open import univ_open
from extract_domain import extract_domain
from json import loads as jloads

CLI_ARGS = ['urls_from_logs_to_ids_file', 'web_crawl_urls_to_ids_file', 'output_path']
OPTIONAL_ARGS = []
def main(stop_after_init=False):
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print 'Usage: %s %s %s' % (argv[0], ' '.join(CLI_ARGS), ' '.join(["[%s]" % x for x in OPTIONAL_ARGS]))
        print 'Currently missing parameters arguments:', ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    urls_from_logs_to_ids_file   = argv[1].strip()
    web_crawl_urls_to_ids_file   = argv[2].strip()
    output_path                  = argv[-1].strip()

    t_init = time()

    print "Loading domains string -> id mapping..."
    t0 = time()
    domains_string_to_ids = {}
    with univ_open(urls_from_logs_to_ids_file, 'r') as f:
        current_index = 0
        for line in f:
            domains_string_to_ids[line.strip().lower().replace("%0a", '')] = current_index
            
            current_index += 1
    print "Done in", time()-t0

    print "Counting urls..."
    t0 = time()
    number_of_urls = 0
    with univ_open(web_crawl_urls_to_ids_file, 'r') as f:
        # Note: I thought I'd use len(f.readlines()) but building this huge list in memory takes ages for nothing
        for l in f:
            number_of_urls += 1

    print "Mapping URLs to their domain id...."
    web_crawl_urls_to_domain_ids = [None] * number_of_urls
    with univ_open(web_crawl_urls_to_ids_file, 'r') as f:
        f.readline()  #1st line has no info
        current_index = 0
        start_index = 0  # The second line contains no comma
        for line in f:
            line = line.strip().lower()
            if line == "]":
                continue
            line = jloads(line[start_index:]).replace("%0a", '')
            start_index = 1
            domain = extract_domain(line)
            try:
                web_crawl_urls_to_domain_ids[current_index] = domains_string_to_ids[domain]
            except KeyError:
                pass  # well, not found, then keep no values to assign
            
            current_index += 1

    print "Done in", time()-t0

    print "Writing URLs to output file", output_path, "..."
    t0 = time()
    with univ_open(output_path, 'w+') as out:
        out.write(
            "\n".join( 
                "%d" % web_crawl_urls_to_domain_ids[i] 
                    if web_crawl_urls_to_domain_ids[i] is not None
                    else ""
                for i in xrange(len(web_crawl_urls_to_domain_ids))
            )
        )
    print "Done in", time()-t0

    print "Script executed in", time() - t_init, "seconds"

if __name__ == '__main__':
    main()