#!/usr/bin/python

"""
    This script will merge the converted version of a multiple-part crawl into one big result file    
"""

from gzip import open as gzopen
from json import dumps, load
from time import time
# import pickle
import sys

CLI_ARGS = ["number_of_parts", "file_parts_basename", "output_path_merged.json.gz"]
OPTIONAL_ARGS = ["part_pattern"]

argc = len(sys.argv)
if argc < (len(CLI_ARGS)+1):
    print "Usage:", sys.argv[0], " ".join(CLI_ARGS), "[" + "][".join(OPTIONAL_ARGS) + "]"
    print "file_parts_basename is the filename before the _partX"
    print "number_of_parts is the number of files in _partX....json.gz to load"
    exit()

n_of_parts = int(sys.argv[1])
basename = sys.argv[2]
output_path_merged = sys.argv[3]
# Recall those files contain a dictionary urls => some information
# for every crawled url
if argc > len(CLI_ARGS) + 1:
    part_pattern            = sys.argv[len(CLI_ARGS) + 1]
else:
    part_pattern            = "_part%s"

sets_of_urls_fnames = "%s.json.gz" % part_pattern

# Recall: those files contain a HUGE list of lists as follows:
# [
#   [url_id1, [url_ids of outlinks from url_id1]],
#   [url_id2, [url_ids of outlinks from url_id2]],
#   [url_id3, [url_ids of outlinks from url_id3]]
# ]
graph_fnames = "%%s%s_graph.converted.json.gz" % part_pattern
SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS = 27667698
# HUGE MOTHER FUCKER GRAPH! Hopefully fitting in your RAM... :) 
graph = [None] * SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS
# Then, load the graphs one by one and store in memory the crawl data for URLs of the previously computed intersection
total_items = 0
for i in xrange(1, n_of_parts+1):
    fname = graph_fnames % (basename, i)
    print "Loading file", fname
    with gzopen(fname, 'rb') as f:
        g = load(f)
    print "Loaded", len(g), "items"
    for u in g:
        uid = int(u[0])
        try:
            if graph[uid] is not None:
                # if it has already been assigned it means that it is an URL in common through multiple scripts
                # so just brutally merge it by taking the union
                graph[uid] = (uid, list(set(graph[uid][1]) | set(u[1])))
            else:
                graph[uid] = (uid, u[1])
                total_items += 1
        except IndexError as e:
            print "Wow, you selected a SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS too low"
            print uid
            exit()
    g = None  # Hopefully GC-ed

with gzopen(output_path_merged, "wb+", 6) as outf:
    print "Computing result... (filtering out useless information)"
    result = [_ for _ in graph if _ is not None]
    graph = None
    print "Now writing result (", len(result), "items) to file."
    comma = ""
    outf.write("[")
    for x in result:
        outf.write("\n%s%s" % (comma, dumps(x)))
        comma = ","
    outf.write("\n]")
print "Done"