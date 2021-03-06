#!/usr/bin/python
__author__ = 'troll'
from graph_tool.all import *
import graph_tool as gt
import json, sys
from time import time
from gzip import open as gzopen
DBG = False

def log(*args):
    if DBG:
        for s in args:
            print s,
        print ""

def load(g, pm, fname):
    print "Loading file..."
    with gzopen(fname, 'r') as f:
        data = json.load(f)
    print "File loaded"
    vertices = [None] * 16667698
    n = -1
    n_e = -1
    n0 = n
    n_e0 = n_e
    # comma_offset = 0
    t0 = time()
    t1 = t0
    for node, edges in data:
        # node, edges = loads(l.strip()[comma_offset:])
        # comma_offset = 1

        if vertices[node] is not None:
            v_node = g.vertex(vertices[node])
            # log("Node", node, "already exists")
        else:
            # log("Creating node for", node)
            v_node = g.add_vertex()
            n += 1
            vertices[node] = n
            pm[v_node] = node  # Register the actual id of the node as a property of the node
            
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
                pm[v] = e  # Register the actual id of the node as a property of the node
            n_e += 1
            g.add_edge(v_node, v)

        if n % 10000 is 0:
            print "======"
            print "Loaded", n, "nodes in", time()-t0, ". Average:", n/(time()-t0), "nodes/s. Current pace:", (n-n0)/(time()-t1), "n/s"
            print "Loaded", n_e, "edges in", time()-t0, ". Average:", n_e/(time()-t0), "edges/s. Current pace:", (n_e-n_e0)/(time()-t1), "e/s"
            n0 = n
            n_e0 = n_e
            t1 = time()
    print "======"
    print "Loaded ", n, "nodes"
    print "======"

CLI_ARGS = ["input_path.converted.json.gz", "output_path.xml.gz"]
def main():
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS)
        exit()

    input_path = sys.argv[1]
    graphml_path = sys.argv[2].strip()

    g = Graph(directed=True)
    pm = g.new_vertex_property("int32_t")
    print "Loading graph..."
    t0 = time()
    load(g, pm, input_path)
    t1 = time()
    print "Graph loaded in", t1-t0

    print "Saving graph to disk (GraphML)"
    t0 = time()
    g.vertex_properties['nodes_labels'] = pm
    g.save(graphml_path)
    t1 = time()
    print "Saved to graphML in", t1-t0

    print "Done"

if __name__ == '__main__':
    main()