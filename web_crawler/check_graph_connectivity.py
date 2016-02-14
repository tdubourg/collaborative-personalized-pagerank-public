#!/usr/bin/python

"""
This file will check whether the given graph is a connected graph
or not.

The expected graph format is under the form of a list of adjacency lists, as follows:
[
  [url_id1, [url_ids of outlinks from url_id1]],
  [url_id2, [url_ids of outlinks from url_id2]],
  [url_id3, [url_ids of outlinks from url_id3]]
]
"""

from gzip import open as gzopen
from json import load
from time import time
from random import choice
import sys, resource

# Some recursive stuff is being done at the end of the script, we do not want to be 
# killed because of stack-size restrictions
resource.setrlimit(resource.RLIMIT_STACK, (2**29,-1))
sys.setrecursionlimit(10**6)


if len(sys.argv) < 2:
    print "Usage: ./", sys.argv[0], " graph_filepath.json.gz"
    sys.exit()

fname = sys.argv[1].strip()
print "Loading file", fname
t0 = time()
with gzopen(fname, 'rb') as f:
    g = load(f)
t1 = time()
print "Loaded", len(g), "adjacency lists in ", t1-t0
SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS = 16667698
# HUGE MOTHER FUCKER GRAPH! Hopefully fitting in your RAM... :) 
graph = [None] * SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS
print "Generating indexed graph"
t2 = time()
for u in g:
    uid = int(u[0])
    try:
        graph[uid] = (uid, u[1])
    except IndexError as e:
        print "Wow, you selected a SOME_NUMBER_HIGHER_THAN_NUMBER_OF_URLS too low"
        print uid
        exit()
t3 = time()
g = None  # Hopefully GC-ed
print "Generated in", t3 - t2

print "Extracting set of nodes we should walk through (=items for which we have outlinks data=items actually crawled)"
# Those nodes are the ones for which we have outlinks data
should_list = [item[0] for item in graph if item is not None] 
should = set(should_list)

print "The set of crawled nodes contains", len(should), "nodes"

seen_nodes = set()
def dfs(index):
    if graph[index] is None:
        return
    for x in graph[index][1]:
        if x in seen_nodes:
            continue
        seen_nodes.add(x)
        dfs(x)

def bfs(start_index):
    new_ones = [start_index]
    while new_ones:
        index = new_ones.pop()
        if graph[index] is None:
            continue
        for x in graph[index][1]:
            if x not in seen_nodes:
                new_ones.append(x)
                seen_nodes.add(x)
print "Now randomly doing a full DFS through the graph and counting nodes we go through"
not_seen_results = []
list_of_choice = should_list
number_of_consecutive_runs = 1
while True:
    number_of_consecutive_runs -= 1
    print "Choosing from", len(list_of_choice), "nodes"
    first = choice(list_of_choice)
    print "Starting BFS from node", first
    # Launch DFS!
    seen_nodes = set()
    t4 = time()
    bfs(first)
    t5 = time()
    print "Terminated DFS in ", t5-t4
    # print "We have seen", len(seen_nodes), "nodes and should have seen at least", len(should), "nodes"
    not_seen = should - seen_nodes
    not_seen_results.append(len(not_seen))
    print "## Not seen:\t\t\t", len(not_seen), '\t\t##'
    print "Not seen avg until now:", sum(not_seen_results) / float(len(not_seen_results))
    # "i" is for "inverse": We then choose a starting node from the set of the not seen ones
    if number_of_consecutive_runs is 0:
        print "Again? [Y/i/n/[0-9]+]"
        answer = raw_input().strip().lower()
        try:
            number_of_consecutive_runs = int(answer)
        except ValueError:
            # It was not a number ! :(
            number_of_consecutive_runs = 1
            if answer == "n" or answer == "no":
                break
            if answer == "i" or answer == "inverse":
                print "Inversing lists of choice, choosing from the set of not seen nodes"
                list_of_choice = list(not_seen)


# dump_fname = "/tmp/cppr_dump_not_seen.gz"
# print "Those nodes are being dumped to", dump_fname
# with gzopen(dump_fname, "wb+", 6) as fout:
#     fout.write("\n".join([str(_) for _ in not_seen]))

print "Done"