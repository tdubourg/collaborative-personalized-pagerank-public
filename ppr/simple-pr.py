#!/usr/bin/python
__author__ = 'troll'
from graph_tool.all import *
import graph_tool as gt
from time import time
DBG = False

def log(*args):
    if DBG:
        for s in args:
            print s,
        print ""

def load(g, pm, fname):
    f = open(fname, 'r')
    vertices = {}
    for l in f:
        node, edges = l.strip().split(':')
        node = int(node)
        edges = [int(_) for _ in edges.strip().split()]
        try:
            v_node = vertices[node]
            log("Node", node, "already exists")
        except KeyError:
            log("Creating node for", node)
            v_node = g.add_vertex()
            vertices[node] = v_node
            pm[v_node] = node  # Register the actual id of the node as a property of the node

        for e in edges:
            try:
                v = vertices[e]
                log("Node", e, "already exists")
            except KeyError:
                log("Creating node for", e, "to create the corresponding edge")
                v = g.add_vertex()
                vertices[e] = v
                pm[v] = e  # Register the actual id of the node as a property of the node
            g.add_edge(v_node, v)
    f.close()

def test(g):
    pr = gt.centrality.pagerank(g)

if __name__ == '__main__':
    g = Graph(directed=True)
    pm = g.new_vertex_property("int32_t")
    print "Loading graph..."
    t0 = time()
    load(g, pm, "./links-simple-sorted.txt")
    t1 = time()
    print "Graph loaded in", t1-t0
    # print "Printing registered nodes:"
    # for n in g.vertices():
    #     print n
    # print "Printing registered edges:"
    # for e in g.edges():
    #     print e
    N = 1
    print "Starting PR computation (", N, "times)"
    t0 = time()
    for x in xrange(0, N):
        test(g)
    t1 = time()

    print "PageRank computed in", (t1-t0)/float(N), "in average."
    # for v in g.vertices():
    #     print v, "(", pm[v], "):", pr[v]