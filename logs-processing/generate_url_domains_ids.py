#!/usr/bin/python

"""
Input: AOL logs
Output: A url domain -> unique unsigned integer id mapping, under the form of a list:

[
url_domain_id_0,
url_domain_id_1,
...
url_domain_id_corresponding_to_index_in_the_list,
...
]
"""


from univ_open import univ_open
from json import dumps
import sys

if len(sys.argv) < 3:
    print "Usage:", sys.argv[0], "input_logs output_path.gz"
    sys.exit()

# If True, the resulting output will be a valid JSON list
# Else, it will just be one line = one item list, ordered by index (no huge difference!)
JSON_OUTPUT = False

# Size of IO batch writes
BATCH_SIZE = 10000

from time import time
with univ_open(sys.argv[2], 'wb') as outfile:
    print "Starting logs parsing..."
    t0 = time()
    url_domains = set()
    with univ_open(sys.argv[1], mode='r') as f:
        for line in f:
            line = line.strip().split('\t')
            if  len(line) is not 5:  # This is not a clickthrough line
                continue
            url = line[4].strip().lower()
            try:
                url = url[url.index("//")+2:] # getting rid of "protocol://"
                url = url.strip()  # it seems that sometimes URL domains are "http:// theurl.tld"... 
            except ValueError: # sustring not found, then there is no protocol to get rid of
                pass
            url_domains.add(url)

    print "Done in", time()-t0
    print "Parsing done. Now writing", len(url_domains), "elements to disk in batch of", BATCH_SIZE, "elements"
    t0 = time()
    item_separation = ""
    if JSON_OUTPUT:
        outfile.write("[\n")
    items_in_queue = 0
    batch_str = ''
    for u in url_domains:
        batch_str += "%s%s" % (item_separation, dumps(u) if JSON_OUTPUT else u)
        if JSON_OUTPUT:
            item_separation = "\n,"
        else:
            item_separation = "\n"
        if items_in_queue is BATCH_SIZE:
            outfile.write(batch_str)
            batch_str = ''
    # Write the remainder of data to be written, if there is some
    if batch_str != '':
        outfile.write(batch_str)
    if JSON_OUTPUT:
        outfile.write("\n]")
print "I/O done in", time()-t0
