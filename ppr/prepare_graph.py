#!/usr/bin/python

"""
    This script will generate the GraphML file of the web graph, from the post-processed (process_crawl_chain.py) 
    web crawl results files
"""
from graph_tool.all import *
import graph_tool as gt
from time import time
import sys, os
# Pretty cool line of code, isn't it? Just read it slowly...
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs-processing/")))
from multiproc_utils import run_in_bg_process
from univ_open import univ_open
import json
DBG = False

MAX_URL_ID = 17906759 + 1

# We use a global because, as it's a reference to a C++ object more or less, I am pretty sure passing it as a parameter
# to the multiproc methods will not work
global_graph = None

def save_global_graph(path):
    print "Saving graph to disk (GraphML)"
    t0 = time()
    global_graph.save(path)
    t1 = time()
    print "Saved to graphML in", t1-t0
    return True

CLI_ARGS = ["web_graph_crawl.converted.converted.json.gz", "graphml_output_path.xml.gz"]
OPT_ARGS = []
def main():
    from sys import argv
    t0 = time()

    if len(argv) < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    input_path =        argv[1]
    graphml_path =      argv[2]

    global global_graph
    global_graph = Graph(directed=True)
    original_ids_pm = global_graph.new_vertex_property("int32_t")

    load(global_graph, original_ids_pm, input_path)

    global_graph.vertex_properties['original_ids'] = original_ids_pm
    # p_save_to_disk, mapres = run_in_bg_process(save_global_graph, (graphml_path,))
    save_global_graph(graphml_path)

    if raw_input("Do you want to run a PR Computation test run on this graph before terminating? [y/N]").lower() \
        in ("yes", "y"):
        t0 = time()
        test(global_graph)
        print "PageRank computed in", (time()-t0)

    # p_save_to_disk.join()

    print "Script terminated."

def load(g, original_ids_pm, fname):
    print "Loading file..."
    with univ_open(fname, 'r') as f:
        data = json.load(f)
    print "File loaded"
    vertices = [None] * MAX_URL_ID
    n = -1
    n_e = -1
    n0 = n
    n_e0 = n_e
    # comma_offset = 0
    t0 = time()
    t1 = t0
    # Note: Remember that the graph is stored in JSON but not under the standard dictionary-format {X: edges}
    # but using tuples: [(X, edges), (Y, edges), ...]
    # because lists can easily be write/read-streamed while dictionary it a little bit more complicated
    # and also it is much heavier to use dictionaries while in the end we mostly want to iter through this file anyway
    for node, edges in data:
        if vertices[node] is not None:
            v_node = g.vertex(vertices[node])
            # log("Node", node, "already exists")
        else:
            # log("Creating node for", node)
            v_node = g.add_vertex()
            n += 1
            vertices[node] = n
            original_ids_pm[v_node] = node  # Register the original id of the node as a property of the node
            
        for e in edges:
            v = None
            if vertices[e] is not None:
                v = g.vertex(vertices[e])
                # log("Node", e, "already exists")
            else:
                # log("Creating node for", e, "(", type(e), ") to create the corresponding edge")
                v = g.add_vertex()
                n += 1
                vertices[e] = n
                original_ids_pm[v] = e  # Register the actual id of the node as a property of the node
            n_e += 1
            g.add_edge(v_node, v)

        if n % 10000 is 0:
            print "======"
            print "Loaded", n, "nodes in", time()-t0, ". Average:", n/(time()-t0), "nodes/s. Current pace:", (n-n0)/(time()-t1), "n/s"
            print "Loaded", n_e, "edges in", time()-t0, ". Average:", n_e/(time()-t0), "edges/s. Current pace:", (n_e-n_e0)/(time()-t1), "e/s"
            n0 = n
            n_e0 = n_e
            t1 = time()
    print "Loaded ", n, "nodes"

def test(g):
    pr = gt.centrality.pagerank(g)

if __name__ == '__main__':
    main()
