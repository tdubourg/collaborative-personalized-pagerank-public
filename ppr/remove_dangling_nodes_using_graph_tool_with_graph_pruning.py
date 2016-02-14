#!/usr/bin/python
__author__ = 'troll'
from graph_tool.all import *
import graph_tool as gt
from time import time
import sys
from random import randrange
DBG = False

def log(*args):
    if DBG:
        for s in args:
            print s,
        print ""

epsilon = 0.000001
max_iter = 100
def test(g):
    pr, n_iter = gt.centrality.pagerank(g, ret_iter=True, epsilon=epsilon, max_iter=max_iter)
    return n_iter

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage:", sys.argv[0], "number_of_nodes_to_prune input_graph.xml.gz [output_path.xml.gz] [number_of_dangling_nodes_passes] [epsilon] [max_iter]"
        sys.exit()
    nodes_to_prune = int(sys.argv[1])
    graphml_path = sys.argv[2]
    output_path = None
    passes = 2

    if len(sys.argv) > 3:
        output_path = sys.argv[3] if sys.argv[3] != "None" else None
    if len(sys.argv) > 4:
        passes = int(sys.argv[4])
    if len(sys.argv) > 5:
        epsilon = float(sys.argv[5])
    if len(sys.argv) > 6:
        max_iter = int(sys.argv[6])
    
    print "Loading from disk (graphML)"
    g = None  # Will hopefully trigger gc
    g = Graph(directed=True)
    t0 = time()
    # # Testing purposes only:
    # pm_labels = g.new_vertex_property("int32_t")
    # nodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 42, 55, 89]
    # for x in nodes:
    #     v = g.add_vertex()
    #     pm_labels[v] = x
    # g.add_edge(g.vertex(0), g.vertex(1))
    # g.add_edge(g.vertex(2), g.vertex(1))
    # g.add_edge(g.vertex(2), g.vertex(3))
    # g.add_edge(g.vertex(3), g.vertex(2))
    # g.add_edge(g.vertex(2), g.vertex(4))
    # g.add_edge(g.vertex(4), g.vertex(2))
    # g.add_edge(g.vertex(2), g.vertex(5))
    # g.add_edge(g.vertex(6), g.vertex(5))
    # g.add_edge(g.vertex(6), g.vertex(1))
    # g.add_edge(g.vertex(6), g.vertex(7))
    # g.add_edge(g.vertex(6), g.vertex(8))
    # g.add_edge(g.vertex(6), g.vertex(9))
    # ## end of test code

    g.load(graphml_path)
    t1 = time()
    print "Loaded from GraphML in", t1-t0
    print "Loaded", g.num_vertices(), "nodes"
    print "Loaded", g.num_edges(), "edges"
    print g.vertex_properties

    # graph_draw(g, vertex_text=g.vertex_index, vertex_font_size=18,
    #         output_size=(200, 200), output="big_graph_at_pass_-1.svg")

    # Let us first randomly prune some nodes in order to reduce the graph's size...
    print "Randomly removing", nodes_to_prune, "nodes..."
    print_every = nodes_to_prune / 10
    t0 = time()
    for i in xrange(0, nodes_to_prune):
        to_prune = randrange(g.num_vertices())
        g.remove_vertex(to_prune, fast=True)
        if i % print_every is 0:
            print "...Removed", i+1, "nodes..."
    t1 = time()
    print "Done in", t1-t0
    print "Graph now has", g.num_vertices(), "vertices and", g.num_edges(), "edges"

    t0 = time()
    n = 0
    for i in xrange(0, passes):
        g.set_fast_edge_removal(True)
        print "Dangling nodes removal pass", i
        t2 = time()
        # Note: The following way to prune the graph is 100% graph-tool implementation-specific
        # But this is the only efficient way to remove tons of nodes in a graph-tool graph
        # As normal removal is O(N) and at every fast removale (fast=True) indices are invalidated
        v_i = 0
        N = g.num_vertices()
        while v_i < N:  # Nodes are indexed from 0 to N-1
            v = g.vertex(v_i)
            if v.out_degree() is 0:
                n += 1
                g.remove_vertex(v, fast=True)  # This will swap node v with the last node of the graph...
                # So, as a consequence, we re-do the current node index, as the node at this index is now the node
                # that was at the "end" of the graph and we have not walked through it
                v_i -= 1
                N -= 1  # We just removed a node, so the graph now has one node less
            v_i += 1
        t3 = time()
        print "\t\t\tPass", i, "done in", t3-t2, "seconds.", n, "nodes removed so far."
        # graph_draw(g, vertex_text=g.vertex_index, vertex_font_size=18,
        #         output_size=(200, 200), output="big_graph_at_pass_%d.svg" % i)
    t1 = time()
    print "Removed", n, "dangling nodes in", passes, "passes in", t1-t0, "seconds"
    print "Graph now has", g.num_vertices(), "vertices and", g.num_edges(), "edges"

    if output_path is not None:
        print "Saving..."
        t0 = time()
        g.save(output_path)
        t1 = time()
        print "Done in", t1-t0
    print "Drawing..."
    t0 = time()
    # exit()
    t1 = time()
    print "Drawn & saved in", t1-t0
    N = 2
    print "Starting PR computation (", N, "times)"
    t0 = time()
    for x in xrange(0, N):
        t2 = time()
        n_iter = test(g)
        t3 = time()
        print "PR computation time:", t3-t2, "with", n_iter, "iterations for epsilon=", epsilon
    t1 = time()

    print "PageRank computed in", (t1-t0)/float(N), "in average."
    # for v in g.vertices():
    #     print v, "(", pm[v], "):", pr[v]
