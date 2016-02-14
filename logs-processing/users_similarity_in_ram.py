#!/usr/bin/python

"""
    This module provides the necessary methods to compute the user profiles and 
    two users similarity IN RAM (you'd better have a lot of it).

    /!\ IT MUST BE INITIALIZED BY RUNNING THE init() FUNCTION /!\
    If you do not initialize it, it will crash because data is not present. It does not retrieve any sort of data
    by itself.

    Be conscious that this module caches everything. So it is not necessary to store the results in your
    own data structure. Alternatively, this means if you compute an extremely high number of different results
    this module will end up using a lot of memory.
"""

from math import log
from numpy import array, inner
from numpy.linalg import norm

DBG = False
PERF_DBG = False

# clusters vectors dict qid -> vector (list object)
query_clusters = None

# total number of users...
tot_users = None

# [
#   {
#     qid: times_issued_per_user_0 
#   },
#   {
#     qid: times_issued_per_user_1 
#   },
#    ...
#   {
#     qid: times_issued_per_user_corresponding_to_list_index
#   },
# ]
# 
queries_times_list_indexed_by_uid = None

# Pretty much the same structure as queries_times_list_indexed_by_uid
# but with an additional dict level for the URLs and
# the final value is not times_issued_per_user_i but clicks_on_this_urls_for_this_query_for_user_i
users_clicks_list_indexed_by_uid = None

# set of the users...
users_set = None

# the sets of top similar users, indexed by user
sim_users = {}

number_of_users_who_queried_cache = {}
number_of_users_who_clicked_cache = {}
clusters_cache = {}

def init(clicks, times_per_query, clustering, users_set_, n_of_u_who_queried, n_of_u_who_clicked, top_sim_users={}):
    global users_set, users_clicks_list_indexed_by_uid, query_clusters, tot_users, queries_times_list_indexed_by_uid
    global number_of_users_who_queried_cache, clusters_cache, number_of_users_who_clicked_cache, sim_users
    users_clicks_list_indexed_by_uid = clicks
    queries_times_list_indexed_by_uid = times_per_query
    query_clusters = clustering
    clusters_cache = clustering
    users_set = users_set_
    tot_users = len(users_set)
    number_of_users_who_queried_cache = n_of_u_who_queried
    number_of_users_who_clicked_cache = n_of_u_who_clicked
    sim_users = top_sim_users

def init_sim_users(top_sim_users):
    global sim_users
    sim_users = top_sim_users

def sim(u1, u2):
    v1, v2 = c_l(u1), c_l(u2)
    # Note: Although n.linalg.norm seems like a quite heavy function, it actually still is ~13% faster than
    # doing the same thing in python so...
    return inner(v1, v2) / float(norm(v1) * norm(v2))

c_l_cache = {}
def c_l(u):
    """
        Returns the user clusters profile as we defined it
        :return Numpry Array: The user clusters vector
    """
    if DBG:
        print "c_l(", u, ")"
    try:
        result = c_l_cache[u]
    except KeyError:  # cache miss
        try:
            result = sum([P(q, u) * w(q) * clusters(q) for q in queries_times_list_indexed_by_uid[u]])
        except TypeError as err:
            print err
            print P(q, u)
            print w(q)
            print type(clusters(q))
            print clusters(q)
        c_l_cache[u] = result
    return result

def clusters(qid):
    """
        Returns the clusters vector of query q
    """
    if DBG:
        print "clusters(", qid, ")"
    try:
        result = clusters_cache[qid]
    except KeyError:  # cache miss
        try:
            result = array(query_clusters[qid])
            clusters_cache[qid] = result
        except TypeError as err:
            print err
            print "qid=", qid
            from sys import exit
            exit()
    return result

def P(q, u):
    if DBG:
        print "P(", q, u, ")"
    return clicks(q, u) / float(clicks(None, u))

clicks_cache = {}
def clicks(q, u, p=None):
    try:
        result = clicks_cache[(q, u, p)]
    except KeyError:  # cache miss
        if PERF_DBG:
            from time import time
            t0 = time()
            print "Computation for clicks(", q, ",", u, ")\t\t\tstarted"
        
        if users_clicks_list_indexed_by_uid[u] is None:
            print "/!\\ WE HAVE NOT INFO ABOUT user=", u, "?!?!?!?!!"

        # if q is None, loop through all queries of current user
        if q is None:
            queries_urls_dict_items = users_clicks_list_indexed_by_uid[u].items()
        else:  # else, only loop through... the given query!
            try:
                queries_urls = users_clicks_list_indexed_by_uid[u][q]
                queries_urls_dict_items = [(q, queries_urls)]
                if queries_urls is None:
                    print "/!\\ WE HAVE NO INFO ABOUT user=", u, "for query q=", q, "?!?!?!?!!"
                    return 0
            except KeyError as err:
                key = int(err.message)
                if key == q:  # query not found in this user's queries, user did not query q
                    # This user simply has no clicks for this query or this page (it can happen that we request this
                    # when computing score() as we will use the clicks of similar users on the queries of OUR profile
                    # but those users might be similar to use without having clicked on this query anyway)
                    clicks_cache[(q, u, p)] = 0
                    return 0

        result = sum([\
            # If p is None, for every query we take all the pages (urls) (thus the sum)
            sum(urls_clicks_dict.values()) if p is None \
            # Else, if a page is specified, we only take its own clicks
            # and only in the case the page actually belongs to the current query's clicks, else 0
            else urls_clicks_dict[p] if p in urls_clicks_dict \
                else 0 \
            for q2, urls_clicks_dict in \
            queries_urls_dict_items \
        ])

        clicks_cache[(q, u, p)] = result
        if PERF_DBG:
            print "Executed in about\t\t\t\t", time()-t0
    if DBG:
        print "Result clicks(", q, ",", u, ")=", result
    return result

def w(q):
    if DBG:
        print "w(", q, ")"
    return log(tot_users / float(number_of_users_who_queried(q)), 10)

def number_of_users_who_queried(qid):
    try:
        result = number_of_users_who_queried_cache[qid]
    except KeyError:  # cache miss
        # The set() is for unique users, the len() counts the unique users...
        # TODO: Optimize that, we could probably scan this thing only once and store stuff...
        print "Warning: cache miss for number_of_users_who_queried(", qid, ")"
        result = len(set([u for u in users_set if qid in queries_times_list_indexed_by_uid[u]]))
        if result == 0:
            print "Warning: number_of_users_who_queried(", qid, ") is 0"
            print queries_times_list_indexed_by_uid[u]
        number_of_users_who_queried_cache[qid] = result
    return result

def number_of_users_who_clicked(qid):
    try:
        result = number_of_users_who_clicked_cache[qid]
    except KeyError:  # cache miss
        # The set() is for unique users, the len() counts the unique users...
        # TODO: Optimize that, we could probably scan this thing only once and store stuff...
        print "Warning: cache miss for number_of_users_who_clicked(", qid, ")"
        result = len(set([u for u in users_set if qid in queries_times_list_indexed_by_uid[u]]))
        if result == 0:
            print "Warning: number_of_users_who_clicked(", qid, ") is 0"
            print queries_times_list_indexed_by_uid[u]
        number_of_users_who_clicked_cache[qid] = result
    return result

SMOOTHING_FACTOR = 0.5  # cf. [#alargescale]

scores = {}
def score(q, p, u):
    """
        :param{int} q: a query id
        :param{int} p: a Web Page/URL/Graph node id
        :param{int} u: a user id
    """
    cache_tuple_key = (q, p, u)
    try:
        return scores[cache_tuple_key]
    except KeyError as err:
        if DBG:
            print "Cache miss:", err,
        result = (
        sum([\
            sim_u_u_s * clicks(q, u_s, p=p)
            for sim_u_u_s, u_s in sim_users[u]
        ]) 
        / (
            float(SMOOTHING_FACTOR) + sum([
                clicks(q, u_s)
                for sim_u_u_s, u_s in sim_users[u]
            ])
          )
        )
        scores[cache_tuple_key] = result
        return result
