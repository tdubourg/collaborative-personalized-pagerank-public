#!/usr/bin/python

"""
    This module provides the necessary functions to compute the personalized version of the PR vector on a given
    graph using personalization collaboratively defined personalization scores

    It basically contains code for PPR(u, q) and CPPR(u, q)
"""
from graph_tool.all import Graph
import graph_tool as gt
import json
from time import time
from gzip import open as gzopen
from numpy import array
from heapq import heappushpop as pp
from heapq import nlargest
from pymongo import MongoClient

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "../logs-processing")))
from univ_open import univ_open
from load_similar_users import load_sim_users

from load_query_url_to_domain_log_id_mapping import load_mapping

DBG = False

# Global graph
g = None
mdb = None
crawl_urlids_to_logs_domainids_mapping = None
sim_users = None

def log(*args):
    if DBG:
        for s in args:
            print s,
        print ""

def init_graph(graphml_path):
    global g
    g = Graph(directed=True)
    t0 = time()
    g.load(graphml_path)
    t1 = time()
    print "Loaded from GraphML in", t1-t0
    print "Loaded", g.num_vertices(), "nodes"
    print "Loaded", g.num_edges(), "edges"

def init_db(host):
    global mdb
    mdb = lambda: MongoClient(host=host)  # Finally we reconnect every time so that we are eduroam-proof
    mdb()  # To test for connection

def init_mapping(mapping_dict):
    global crawl_urlids_to_logs_domainids_mapping
    crawl_urlids_to_logs_domainids_mapping = mapping_dict

    return crawl_urlids_to_logs_domainids_mapping

def init_mapping_from_file(mapping_file):
    return init_mapping(load_mapping(mapping_file))

def CCPPR(u, q):
    """
        Returns the CCPPR vector for user u, combination of CPPR vectors of similar users.
        This PPR computation is a two-level-collaborativeness PPR. It will be tested if we have time.
    """
    sim_scores_and_users = load_sim_users(mdb().host, [u])[u]
    result = {}  # will map urlid -> cppr_score
    original_index = g.vertex_properties['original_ids']
    # For every similar user
    for sim_u_s_u, u_s in sim_scores_and_users:
        # First, compute the PPR vector
        ppr = CPPR(u_s, q)
        # Then, compute the combined score of every URL in the graph
        for v in g.vertices():
            orig_id = original_index[v] 
            result[orig_id] = sim_u_s_u * ppr[v] + result.setdefault(orig_id, 0)
    # result = sum([sim_u_s_u * PPR(u_s, q) for sim_u_s_u, u_s in sim_scores_and_users])
    return result

def scores_vector(uid, qid):
    """
        Returns the personalized scores for all URLS that have a personalized score for a given user
        :return
        {
            'url_id': score,
            'url_id': score,
            'url_id': score,
            ...
        }
        /!\ The url_id values here are the ones from the logs, not from the web graph crawl. You have to use the
        mapping crawl -> logs before accessing a key of this returned dictionary
    """
    try:
        return dict(mdb().users.urls_perso_scores.find_one({'uid': uid, 'qid': qid})['vector'])
    except TypeError:
        print "/!\\ Error, no personalization scores could be loaded for (qid, uid)=", (qid, uid)
        return dict()

# TODO move that to a batter place
epsilon = 1e-6
max_iter=100
CPPR_cache = {}

def CPPR(u, q):
    """
        Returns the Collaboratively personalized PR vector for user u.
        It is collaboratively personalized because the score we make use of have been computed collaboratively
    """
    try:
        pr = CPPR_cache[(u, q)]
    except KeyError:
        # cache miss
        persoed = set()
        found_in_mapping = 0
        scores = scores_vector(u, q)
        print "Retrieved", len(scores)
        print "scores:", scores
        perso_vector = g.new_vertex_property("float")
        default_score = 1/float(g.num_vertices())
        original_index = g.vertex_properties['original_ids']
        # For all nodes of the graph
        # if q in [6904765, 6801505, 7522554, 2651877, 2152093]:
        #     mul = 1.0
        # else:
        mul = 5.0
        for v in g.vertices():
            # get the original URL id...
            index = original_index[v]
            try:
                domainid = crawl_urlids_to_logs_domainids_mapping[(q, index)]
                found_in_mapping += 1
                # and try to assign its personalized score, if any
                score = mul * scores[domainid]
                perso_vector[v] = score
                persoed.add(index)
            except KeyError:  # Either there is no mapping, or no score, in both case just use the default score
                perso_vector[v] = default_score

        print found_in_mapping, "URLs were found mapped to domains ids"
        print "Among them", len(persoed), "were assigned perso-ed score in the E perso vector"
        print "The following were mapped:", persoed
        pr = PR(perso_vector=perso_vector)
        CPPR_cache[(u, q)] = pr

    return pr

cached_noperso_pr = None
def PR(perso_vector=None):
    if perso_vector is not None:
        pr, n_iter = gt.centrality.pagerank(
            g,
            pers=perso_vector,
            ret_iter=True,
            epsilon=epsilon,
            max_iter=max_iter
        )
    else:
        global cached_noperso_pr
        if cached_noperso_pr is not None:
            return cached_noperso_pr
        pr, n_iter = gt.centrality.pagerank(
            g,
            ret_iter=True,
            epsilon=epsilon,
            max_iter=max_iter
        )
        cached_noperso_pr = pr
    print "Done in", n_iter, "iterations"
    return pr

def CPPRMapped(u, q, urls_set_to_be_mapped):
    """
        This function runs a CPPR(u, q) but then maps the results to the URLIds, for the ones in the set
        passed as a parameter

        :param{int} u: The user id 
        :param{int} q: The query id
        :param{set} urls_set_to_be_mapped: Set of URLs to have their CPPR scores mapped & returned
    """
    return PRMapped(urls_set_to_be_mapped, personalized=(u, q))

def PRMapped(urls_set_to_be_mapped, personalized=None):
    """
        This function runs a PR vector but then maps the results to the URLIds, for the ones in the set
        passed as a parameter. An optional parameter can be passed to allow personalization.

        :param{set} urls_set_to_be_mapped: Set of URLs to have their CPPR scores mapped & returned
        :param{tuple} personalized: (qid, user_id)
    """
    result = {}  # dict.fromkeys(urls_set_to_be_mapped)
    if personalized is not None:
        u, q = personalized
        pr = CPPR(u, q)
    else:
        pr = PR()

    print "PR Computed, mapping URLs..."
    original_index = g.vertex_properties['original_ids']
    for v in g.vertices():
        urlid = original_index[v]
        if urlid in urls_set_to_be_mapped:
            result[urlid] = pr[v]

    not_mapped = urls_set_to_be_mapped - result.viewkeys()
    if not_mapped:
        print "/!\\ Warning, the following urlids were not mapped...:", len(not_mapped), "over", len(urls_set_to_be_mapped)
        print not_mapped
    print "Mapping finished"

    return result

def init(graphml_path, mdb_host, mapping_file):
    # Run that immediately so that we crash immediately if we cannot connect to the DB anyway
    # mdb_conn = MongoClient(host=mdb_host)
    init_db(mdb_host)
    print "Connected to db"

    print "Loading mapping..."
    t0 = time()
    init_mapping_from_file(mapping_file)
    print "Done in", time()-t0
    
    print "Loading graph..."
    t0 = time()
    init_graph(graphml_path)
    print "Done in", time()-t0

CLI_ARGS = ["graph_path.xml.gz", "mongodb_host", "urlid_to_log_domainids_mapping_file"]
OPT_ARGS = []
def main(argv):
    from time import time

    if len(argv) < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    graphml_path    = argv[1].strip()
    mdb_host        = argv[2].strip()
    mapping_file    = argv[3].strip()

    init(graphml_path, mdb_host, mapping_file)

    interactive_tests_CPPR()

def interactive_tests_CPPR():
    while True:
        queryid, user_id = map(int, raw_input("QueryID UserId?").split())
        print "Computing CPPR(u,q)..."
        pr = CPPR(user_id, queryid)
        print "Done. Computing result..."
        result = [0] * 100
        i = 0
        for _ in g.vertices():
            # print "PR for vertex", i, "is\t", pr[_]
            pp(result, (pr[_], i))
            i += 1
        print "Top 100 PR scores="
        print nlargest(100, result)
        # graph_draw(g, vertex_text=res, vertex_size=pr3, vertex_font_size=15,
        #         output_size=(3000, 3000), output="ppr_test_perso_on_6.png")

def interactive_tests_CPPRMapped():
    set_of_urls_to_be_mapped = set()
    while True:
        set_str = raw_input("Set of URLS to be mapped? (press ENTER if you want to reuse the last provided one\n").strip()
        if set_str != "":
            set_of_urls_to_be_mapped = set(map(int, set_str.split(' ')))
        queryid, user_id = map(int, raw_input("QueryID UserId?").split())
        print "Computing CPPR(u,q)..."
        t0 = time()
        print CPPRMapped(user_id, queryid, set_of_urls_to_be_mapped)
        print "Done in", time()-t0

def interactive_tests_CCPPR():
    while True:
        print "New CPPR computation..."
        queryid, user_id = map(int, raw_input("QueryID UserId?").split())
        print "Computing CCPPR(u,q)..."
        t0 = time()
        pr = CCPPR(user_id, queryid)
        print "Done in", time()-t0
        print "Computing top result..."
        result = [0] * 100
        i = 0
        for _ in g.vertices():
            # print "PR for vertex", i, "is\t", pr[_]
            pp(result, (pr[_], i))
            i += 1
        print "Top 100 CPR scores="
        print nlargest(100, result)
        # graph_draw(g, vertex_text=res, vertex_size=pr3, vertex_font_size=15,
        #         output_size=(3000, 3000), output="ppr_test_perso_on_6.png")

if __name__ == '__main__':
    from sys import argv
    main(argv)