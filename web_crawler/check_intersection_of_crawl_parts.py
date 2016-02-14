#!/usr/bin/python

"""
This file will check whether the same URLs, crawled by different crawlers
have the same linking information or not and dump the ones that are not the same
"""

from gzip import open as gzopen
from json import loads, dumps, load, dump
from time import time
# import pickle
import sys

pickle_ids_fname = '/tmp/ids_pickled.bin'

if len(sys.argv) < 4:
    print "Usage: ./script dict_urls_to_ids.json.gz number_of_parts file_parts_basename"
    print "dict_urls_to_ids.json.gz contains the mapping url => id"
    print "file_parts_basename is the filename before the _partX"
    print "number_of_parts is the number of files in _partX....json.gz to load"
    sys.exit()

n_of_parts = int(sys.argv[2])
basename = sys.argv[3]
# Recall those files contain a dictionary urls => some information
# for every crawled url
sets_of_urls_fnames = "%s_part%d.json.gz"

# Recall: those files contain a HUGE list of lists as follows:
# [
#   [url_id1, [url_ids of outlinks from url_id1]],
#   [url_id2, [url_ids of outlinks from url_id2]],
#   [url_id3, [url_ids of outlinks from url_id3]]
# ]
graph_fnames = "%s_part%d_graph.converted.json.gz"

ids = []
t0 = time()
# Note: Never use pickle, it's just useless: Both slower than recomputing AND takes up all the RAM
# I don't get it
# Try to reload it in case we previously computed it, hopefully saving time
# try:
#     with gzopen(pickle_ids_fname, 'rb') as pf:
#         print "Reusing previously loaded ids mapping from", pickle_ids_fname
#         ids = pickle.load(pf)
# except IOError, EOFError:
print "Loading urls => ids mapping"
# File did not exist or was readable, let us compute it!
ordered_urls = load(gzopen(sys.argv[1], 'rb'))
for u in ordered_urls:
    ids.append(u)
ordered_urls = None  # Hopefully GC-ed
    # # And save it, this time:
    # print "Saving result to", pickle_ids_fname, "for caching"
    # with gzopen(pickle_ids_fname, 'wb+', 6) as pf:
    #     pickle.dump(ids, pf)
    # print "Saved"

print "Dictionary loaded in", time()-t0, "seconds"

# First, load the sets of urls and do the intersection
intersect = None
for i in xrange(1, n_of_parts+1):
    fname = sets_of_urls_fnames % (basename, i)
    print "Loading file", fname
    with gzopen(fname, 'rb') as f:
        s = set(load(f).keys())
    if i is 1:
        intersect = s
    else:
        intersect &= s
print "Loaded the intersection of crawls,", len(intersect), "elements"
# Initializing lists for storing the actual crawl data of those URLs, in the intersection
intersect_data = {}
for x in intersect:
    intersect_data[x] = []

# Then, load the graphs one by one and store in memory the crawl data for URLs of the previously computed intersection
for i in xrange(1, n_of_parts+1):
    fname = graph_fnames % (basename, i)
    print "Loading file", fname
    with gzopen(fname, 'rb') as f:
        g = load(f)
    for u in g:
        uid = int(u[0])
        url = ids[uid]
        if url in intersect:
            intersect_data[url].append(set(u[1]))  # Transforming into sets so that ordering does not matter
    g = None  # Hopefully GC-ed

print "Comparing data of the URLs belonging to the intersection"
inconsistencies = []
for url, olists_list in intersect_data.items():
    # For each list, all elements of the list should be the same
    # so we just eed to compared them 2-by-2 and stop as soon as one comparison
    # is not true and dump all of them
    if not olists_list: 
        # Empty list? (that should only happen in case there is inconsistency between the
        # files describing the same crawl
        print "Inconsistency for url", url, "the list is empty"
        continue
    olist_prev = olists_list[0]
    for outlinks_list in olists_list:
        if outlinks_list != olist_prev:
            inconsistencies.append((url, [list(_) for _ in olists_list]))  # Transforming back to list as sets are not serializable
            break
        outlinks_list = olist_prev

if not inconsistencies:
    print "Great! No inconsistencies found between the crawls."
else:
    print "Found", len(inconsistencies), "inconsistencies, dumping them to",
    print "inconsistencies.json.gz"
    with gzopen("inconsistencies.json.gz", "wb", 6) as outf:
        dump(inconsistencies, outf)
print "Done"