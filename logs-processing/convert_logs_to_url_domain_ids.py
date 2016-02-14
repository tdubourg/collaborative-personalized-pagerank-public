#!/usr/bin/python

"""
Input: AOL logs and url_domain -> ids mapping file (one url domain by line)
Output: Same AOL logs, but with ids in place of the url domain
/!\ RAM: >1.3G
"""
import sys

if len(sys.argv) < 3:
    print "Usage:", sys.argv[0], "input_logs url_domains_to_ids_mapping.lst.gz output_path.gz"
    sys.exit()

from univ_open import univ_open

log_filepath =  sys.argv[1].strip()
url_domain_ids_path = sys.argv[2].strip()
output_path = sys.argv[3].strip()

# If True, the resulting output will be a valid JSON list
# Else, it will just be one line = one item list, ordered by index (no huge difference!)
JSON_OUTPUT = False

# Size of IO batch writes
BATCH_SIZE = 10000

from time import time
batch_str = ''
items_in_queue = 0
t0 = time()
with univ_open(output_path, 'wb') as outfile:
    print "Loading url_domain->ids mapping... (brace yourself, RAM!)"
    t0 = time()
    with univ_open(url_domain_ids_path, 'rb') as idmapfile:
        url_domain_ids = {}
        i = 0
        for line in idmapfile:
            url_domain_ids[line.strip()] = str(i)
            i += 1
    print "Done in", time()-t0

    print "Starting logs parsing + I/O to output file", output_path
    t0 = time()
    with univ_open(log_filepath, mode='r') as f:
        for line in f:
            line = line.strip().split('\t')
            if  len(line) is not 5:  # This is not a clickthrough line
                continue
            # Replace the url domain by the id
            try:
                url = line[4].strip().lower()
                try:
                    url = url[url.index("//")+2:] # getting rid of "protocol://"
                    url = url.strip()  # it seems that sometimes URL domains are "http:// theurl.tld"... 
                except ValueError: # sustring not found, then there is no protocol to get rid of
                    pass
                line[4] = url_domain_ids[url]
            except KeyError as e:
                print "KeyError, the following url domain was not found:", e
                print "The original URL was:", line[4]
            # And put everything back together and push that to the batch queue
            batch_str += '\t'.join(line) + "\n"
            items_in_queue += 1
            if items_in_queue is BATCH_SIZE:
                outfile.write(batch_str)
                batch_str = ''
        # Write the remainder of data to be written, if there is some
        if batch_str != '':
            outfile.write(batch_str)
    print "Done in", time()-t0
