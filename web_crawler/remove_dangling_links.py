#!/usr/bin/python

"""
This file takes as input a converted (URL -> ID) graph and output the same graph
but without the "dangling nodes", defined as follows:

A dangling link is node without outlinks information. This can be either a node that simply did not
have any outlink or a node that was not crawled yet (it's in the graph because there is a link to it
but as we did not crawl it, we have not outlink data about it)

The expected input graph format is under the form of a list of adjacency lists, as follows:
[
  [url_id1, [url_ids of outlinks from url_id1]],
  [url_id2, [url_ids of outlinks from url_id2]],
  [url_id3, [url_ids of outlinks from url_id3]]
]
"""

from gzip import open as gzopen
from json import load, dumps
from time import time
from random import choice
import sys, resource

# Some recursive stuff is being done at the end of the script, we do not want to be 
# killed because of stack-size restrictions
resource.setrlimit(resource.RLIMIT_STACK, (2**29,-1))
sys.setrecursionlimit(10**6)


if len(sys.argv) < 3:
    print "Usage: ./", sys.argv[0], "graph_filepath.json.gz dump_filepath.json.gz"
    sys.exit()

fname = sys.argv[1].strip()
print "Loading file", fname
t0 = time()
with gzopen(fname, 'rb') as f:
    g = load(f)
t1 = time()
print "Loaded", len(g), "adjacency lists in ", t1-t0
SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS = 27667698
# HUGE MOTHER FUCKER GRAPH! Hopefully fitting in your RAM... :) 
graph = [None] * SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS
print "Generating indexed graph"
t2 = time()
# Note: Remember that the graph is stored in JSON but not under the standard dictionary-format {X: adjacency list}
# but using tuples: [(X, adjacency list), (Y, adj list), ...]
# because lists can easily be write/read-streamed while dictionary it a little bit more complicated
# and also it is much heavier to use dictionaries while in the end we mostly want to iter through this file anyway
for u in g:
    uid = int(u[0])
    try:
        graph[uid] = [uid, u[1]]
    except IndexError as e:
        print "Wow, you selected a SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS too low"
        print uid
        exit()
t3 = time()
g = None  # Hopefully GC-ed
print "Generated in", t3 - t2

dump_fname = sys.argv[2]
print "Saving to ", dump_fname, "..."
t0 = time()
n = 0
with gzopen(dump_fname, "wb+", 6) as fout:
    fout.write("[")
    comma = ""
    for elem in graph:
        # We only want the links that have been crawled (outlinks data is not None)
        # and have a non-empty list of outlinks
        if elem is not None and elem[1]:
            # Then, we also filter the outlinks of every node to remove links to the 
            # dangling nodes. Else, there are still present in the graph somehow, and 
            # would be created for the need of the edge's creation
            elem[1] = [_ for _ in elem[1] if graph[_] is not None and graph[_][1]]
            fout.write("\n%s%s" % (comma, dumps(elem)))
            comma = ","
            n += 1
    fout.write("\n]")
print "Saved", n, "adjacency lists in", time()-t0
print "Done"