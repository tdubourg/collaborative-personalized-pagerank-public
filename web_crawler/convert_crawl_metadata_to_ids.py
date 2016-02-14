#!/usr/bin/python

"""
This file will convert the crawl data dictionary from a URL -> metadata dict
to an ID -> metadata dict
It will also merge it at the same time (as it is split into multiple parts, (multiple crawls) at the origin)
"""

from gzip import open as gzopen
from json import load, dumps
from time import time
import sys

if len(sys.argv) < 3:
    print "Usage: ./script dict_urls_to_ids.json.gz [input_crawl_partX.json.gz ...]"
    sys.exit()

print "Loading IDs -> URLs list/mapping and generating URLs -> IDs mapping"
t0 = time()
ids = {}
with gzopen(sys.argv[1], 'rb') as dict_f:
    ordered_urls = load(dict_f)
i = 0
for u in ordered_urls:
    ids[u] = i
    i += 1

number_of_urls_in_mapping = len(ordered_urls)
ordered_urls = None  # Hopefully GC-ed
print "Dictionary loaded in", time()-t0

i = 2
print "Preparing datastructure for", number_of_urls_in_mapping, "URLs' metadata..."
t0 = time()
merged_ids_indexed_dict = [[[], None] for _ in range(number_of_urls_in_mapping)]
print "Done in", time()-t0
while i < len(sys.argv):
    fname = sys.argv[i]
    print "Processing, converting and storing file", fname, "..."
    t0 = time()
    with gzopen(fname, 'rb') as f:
        print "Loading..."
        a = load(f)
        print "Processing..."
        for url, metadata in a.items():
            try:
                uid = ids[url]
                merged_ids_indexed_dict[uid][0].append(metadata["meta"])
                merged_ids_indexed_dict[uid][1] = metadata["hash"]
            except KeyError:
                print "The URL", url, "was not in the URLs -> IDs table, huh?"
        a = None  # GC?
        print "Done:", fname, "in", time()-t0
    i += 1
fname_out = "/tmp/merged_crawling_metadata_list_indexed_by_url_ids.json.gz"
print "Freeing some memory..."
ids = None
print "Saving merged-ids-indexed result to", fname_out
t0 = time()
with gzopen(fname_out, 'wb', 6) as outfile:
    # Note: We are writing the JSON by hand / line by line because dump() calls dumps() and thus
    # creates the full JSON string in memory before dumping... which is not going to work considering
    # the huge amount of data inside merged_ids_indexed_dict
    outfile.write("[")
    comma = ""
    for current_url_metadata in merged_ids_indexed_dict:
        outfile.write("\n%s%s" % (comma, dumps(current_url_metadata)))
        comma = ","
    outfile.write("\n]")
print "Saved in", time()-t0
print "Done"