#!/usr/bin/python
__author__ = 'troll'
from graph_tool.all import *
import graph_tool as gt
from time import time
import sys
DBG = False

def log(*args):
    if DBG:
        for s in args:
            print s,
        print ""

epsilon = 0.000001
max_iter = 100

if __name__ == '__main__':
    g = Graph(directed=True)
    t0 = time()

    pm_labels = g.new_vertex_property("int32_t")
    nodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 42, 55, 89]
    for x in nodes:
        v = g.add_vertex()
        pm_labels[v] = x
    g.add_edge(g.vertex(0), g.vertex(1))
    g.add_edge(g.vertex(2), g.vertex(1))
    g.add_edge(g.vertex(2), g.vertex(3))
    g.add_edge(g.vertex(3), g.vertex(2))
    g.add_edge(g.vertex(2), g.vertex(4))
    g.add_edge(g.vertex(4), g.vertex(2))
    g.add_edge(g.vertex(2), g.vertex(5))
    g.add_edge(g.vertex(6), g.vertex(5))
    g.add_edge(g.vertex(6), g.vertex(1))
    g.add_edge(g.vertex(6), g.vertex(7))
    g.add_edge(g.vertex(6), g.vertex(8))
    g.add_edge(g.vertex(8), g.vertex(6))
    g.add_edge(g.vertex(6), g.vertex(9))

    perso_vector = g.new_vertex_property("int32_t")
    i = 0 
    for _ in g.vertices():
        perso_vector[_] = 1/float(len(nodes))*1000
        print "setting perso factor\t", perso_vector[_], "for node\t", i
        i += 1

    perso_vector[g.vertex(6)] = 1
    pr, n_iter = gt.centrality.pagerank(g, pers=perso_vector, ret_iter=True, epsilon=epsilon, max_iter=max_iter)
    # pr2 = [int(pr[x]*100) for x in g.vertex_index]
    pr3 = gt.draw.prop_to_size(pr, mi=100, ma=300)
    pm2 = g.new_vertex_property("string")
    i = 0
    for _ in g.vertices():
        print "PR for vertex", i, "is\t", pr[_]
        pm2[_] = "i=%d pr=%d" % (i, int(pr[_]))
        i += 1
    # print pr4

    graph_draw(g, vertex_text=pm2, vertex_size=pr3, vertex_font_size=15,
            output_size=(3000, 3000), output="ppr_test_perso_on_6.png")
