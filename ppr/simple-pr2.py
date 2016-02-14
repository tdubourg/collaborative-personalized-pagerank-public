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
    n = -1
    for l in f:
        node, edges = l.strip().split(':')
        node = int(node)
        edges = [int(_) for _ in edges.strip().split()]

        try:
            v_node = g.vertex(vertices[node])
            log("Node", node, "already exists")
        except KeyError:
            log("Creating node for", node)
            v_node = g.add_vertex()
            n += 1
            vertices[node] = n
            pm[v_node] = node  # Register the actual id of the node as a property of the node
        # except ValueError as ee:
        #     print "crashing for node=", node, " returned value=", vertices[node]
        #     print sorted(vertices.items())
        #     raise ee
            
        for e in edges:
            v = None
            try:
                v = g.vertex(vertices[e])
                log("Node", e, "already exists")
            except KeyError:
                log("Creating node for", e, "(", type(e), ") to create the corresponding edge")
                v = g.add_vertex()
                n += 1
                vertices[e] = n
                pm[v] = e  # Register the actual id of the node as a property of the node
            g.add_edge(v_node, v)

        if n % 10000 is 0:
            print "Loaded", n, "nodes"
    f.close()
    print "Loaded ", n, "nodes"

def test(g):
    pr, n_iter = gt.centrality.pagerank(g, ret_iter=True)
    return n_iter

if __name__ == '__main__':
    # g = Graph(directed=True)
    # pm = g.new_vertex_property("int32_t")
    # print "Loading graph..."
    # t0 = time()
    # load(g, pm, "./links20k.txt")
    # t1 = time()
    # print "Graph loaded in", t1-t0
    # print "Printing registered nodes:"
    # for n in g.vertices():
    #     print n
    # print "Printing registered edges:"
    # for e in g.edges():
    #     print e
    # print "Saving graph to disk (GraphML)"
    # t0 = time()
    # g.save("my_graph.xml.gz")
    # t1 = time()
    # print "Saved to graphML in", t1-t0

    # print "Saving as binary Python object"
    # import pickle
    # f = open('wikipedia-graph-tool.bin', 'w+')
    # t0 = time()
    # pickle.dump(g, f)
    # f.close()
    # t1 = time()
    # print "Saved in binary format in", t1-t0

    print "Reloading from disk (graphML)"
    g = None  # Will hopefully trigger gc
    g = Graph(directed=True)
    t0 = time()
    g.load("my_graph80k.xml.gz")
    t1 = time()
    print "Loaded from GraphML in", t1-t0
    print g.vertex_properties
    print "Loaded", g.num_vertices(), "nodes"
    print "Loaded", g.num_edges(), "edges"

    # print "Reloading from disk (binary)"    
    # g = None  # Will hopefully trigger gc
    # f = open('wikipedia-graph-tool.bin', 'r')
    # t0 = time()
    # g = pickle.load(f)
    # f.close()
    # t1 = time()
    # print "Loaded from binary format in", t1-t0

    N = 1
    print "Starting PR computation (", N, "times)"
    t0 = time()
    for x in xrange(0, N):
        t2 = time()
        n_iter = test(g)
        t3 = time()
        print "PR computation time:", t3-t2, "with", n_iter, "iterations"
    t1 = time()

    print "PageRank computed in", (t1-t0)/float(N), "in average."
    graph_draw(g, vertex_text=g.vertex_index, vertex_font_size=180,
            output="wikipedia_graph.svg")
    # for v in g.vertices():
    #     print v, "(", pm[v], "):", pr[v]
