#!/usr/bin/python

"""
    This module provides the necessary methods to compute the user profiles and 
    two users similarity.

    Be conscious that this module caches everything. So it is not necessary to store the results in your
    own data structure. Alternatively, this means if you compute an extremely high number of different results
    this module will end up using a lot of memory.
"""

from math import log
from numpy import array, inner
from numpy.linalg import norm
from time import time

mdb = None
DBG = False
PERF_DBG = False

def init_mdb(mdb_conn):
    global mdb
    mdb = mdb_conn

def sim(u1, u2):
    """
        Returns the similarity measures between two users.
        The similarity measures bases itself on the number of clicks users have in common semantic clusters
    """
    v1, v2 = c_l(u1), c_l(u2)
    # Note: Although n.linalg.norm seems like a quite heavy function, it actually still is ~13% faster than
    # doing the same thing in python so...
    n1 = norm(v1)
    n2 = norm(v2)
    if n1 == 0.0 or n2 == 0.0:
        # Note: Although one should normally never use == on floats, it seems that here we indeed want to match 0.0
        # and according to tests, it seems to work, so, keep it like that for now #terriblehack
        return 0.0
    return inner(v1, v2) / float(n1 * n2)

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
        q_list = queries(u)
        cl_dict = clusters(q_list)
        Ps = P(q_list, u)
        result = sum([Ps[q] * w(q) * cl_dict[q] for q in q_list])
        c_l_cache[u] = result
    return result

def queries(u):
    """
        Returns the list of all queries that u issued in the past
    """
    if DBG:
        print "queries(", u, ")"
    return list(set([_['qid'] for _ in mdb.users.clicks.find({'uid': u})]))

clusters_cache = {}
init_vector = array([])
def clusters(q_list):
    """
        Returns the clusters vectors of queries in q_list
        :return
        {
            qid: cluster_vector,
            qid: cluster_vector,
            qid: cluster_vector,
            qid: cluster_vector
        }
    """
    if DBG:
        print "clusters(", q_list, ")"
    try:
        result = dict([(qid, clusters_cache[qid]) for qid in q_list])
    except KeyError:  # cache miss
        try:
            # There might be some queries that we are asked and that are not in the DB
            # this is normally because those queries have null clustering vectors
            # and thus storing them is HUGE (tens of GB) waste of space
            # but then we need to also initialize cache for them the ones that are not fetched,
            # else they won't be put in cache and we would end up in a recursive loop
            
            # So, initialize everything to a given init object that will be overwritten when we fetch the results
            for qid in q_list:
                clusters_cache[qid] = init_vector
            for query_cluster in mdb.queries.clustering.find({'_id': {'$in': q_list}}):  # this query is indexed
                qid = query_cluster['_id']
                clusters_cache[qid] = array(query_cluster['vector'])
            result = clusters(q_list)  # things are now in cache
        except TypeError as err:
            print err
            print "q_list=", q_list
            from sys import exit
            exit()
    return result

def P(q_list, u):
    """
        Returns the "relative user preference to this queries" compared to other queries, for each query of the list.
    """
    if DBG:
        print "P(", q_list, u, ")"
    total = float(clicks(None, u))
    return dict([(qid, c / total) for qid, c in clicks(q_list, u).items()])

clicks_cache = {}
def clicks(q_list, u):
    """
        :return
        {
            qid: user_clicks_number,
            qid: user_clicks_number,
            qid: user_clicks_number,
            qid: user_clicks_number
        }
    """
    global clicks_cache
    try:
        if q_list is not None:
            result = dict([(qid, clicks_cache[(qid, u)]) for qid in q_list])
        else:
            result = clicks_cache[(None, u)]
    except KeyError as err:  # cache miss
        result_set = clicks_urls(q_list, u).items()
        if q_list is not None:
            for q, q_clicks in result_set:
                clicks_cache[(q, u)] = sum(q_clicks.values())
        else:
            clicks_cache[(None, u)] = 0
            for q, q_clicks in result_set:
                clicks_cache[(None, u)] += sum(q_clicks.values())
        result = clicks(q_list, u)
    if DBG:
        print "Result clicks(", q_list, ",", u, ")=", result
    return result

clicks_urls_cache = {}
def clicks_urls(q_list, u):
    """
        :return
        {
            qid: {
                urlid: user_clicks_urls_number,
                urlid: user_clicks_urls_number,
                ...
            },
            ...
        }
    """
    global clicks_urls_cache
    try:
        if q_list is not None:
            result = dict([(qid, clicks_urls_cache[u][qid]) for qid in q_list])
        else:
            result = clicks_urls_cache[u]
    except KeyError as err:  # cache miss
        # print "cache miss"
        # print err
        where_clause = {'uid': u, 'qid': {'$in': q_list}} if q_list is not None else {'uid': u}  # this query is indexed
        if PERF_DBG:
            t0 = time()
            print "Computation for clicks_urls(", q_list, ",", u, ")\t\t\tstarted"
        
        result_set = mdb.users.clicks.find(where_clause)
        no_results = True
        for item in result_set:
            no_results = False
            # print "blorg??"
            try:
                cache = clicks_urls_cache[u]
            except KeyError:
                cache = dict()
                clicks_urls_cache[u] = cache

            # print "pouet?"
            try:
                cache = cache[item['qid']]
            except KeyError as err:
                # print "ERR?", err
                # print item['qid'], "qid not in cache"
                cache_tmp = cache
                cache = dict()
                cache_tmp[item['qid']] = cache

            cache[item['urlid']] = item['n']
        
        if no_results is True:
            print "WTF? where_clause", where_clause, "returned nothing"
            return {}
        # print clicks_urls_cache
        result = clicks_urls(q_list, u)  # things are now in cache, and we do that for the final formatting ('try' block)
        if PERF_DBG:
            print "Executed in about\t\t\t\t", time()-t0
    if DBG:
        print "Result clicks_urls(", q_list, ",", u, ")=", result
    return result


tot_users = None
def w(q):
    if DBG:
        print "w(", q, ")"
    global tot_users
    if tot_users is None:
        tot_users = len(mdb.users.clicks.distinct('uid'))  # this query is indexed
    return log(tot_users / float(number_of_users_who_queried(q)), 10)

number_of_users_who_queried_cache = {}
def number_of_users_who_queried(qid):
    try:
        result = number_of_users_who_queried_cache[qid]
    except KeyError:  # cache miss
        result = mdb.users.queries.find({"qid": qid}).count()  # this query is indexed
        number_of_users_who_queried_cache[qid] = result
    return result


def sim_users(u):
    """
        Return top K similar users to user u together with their similarity to u:
        [
            {'u': user_id, 'score': similarity(user_id, u)}
        ]
    """
    return mdb.users.similar_users.find_one({'_id': u})['vector']

times = []
def test():
    import sys
    from numpy import mean
    if len(sys.argv) < 2:
        print "Usage: %s mongodb_host"  % sys.argv[0]
        exit()
    host = sys.argv[1].strip()
    # test_wtf(host)
    test_same_user(host)
    from pymongo import MongoClient
    u1 = None
    u2 = None
    conn = None
    previously_used_users = []
    while True:
        print "Connecting to DB..."
        if conn is not None:
            # We were previously connected, let's try to close the connection
            try:
                conn.close()
            except Exception:
                pass
        # Note: We connect inside the loop so that we can connect/disconnect the machine from internet while the script
        # is waiting for an input without havin to launch the script again
        conn = MongoClient(host=host)
        print "Retrieving two random users..."

        t0 = time()
        where_clause = None if u1 is None else {'uid': { '$nin': previously_used_users}}
        if DBG:
            print where_clause
        u1 = conn.users.clicks.find_one(where_clause)['uid']
        u2 = conn.users.clicks.find_one({'uid': { '$nin': [u1] + previously_used_users}})['uid']
        previously_used_users.append(u1)
        previously_used_users.append(u2)
        print "Retrieved users", u1, "and", u2, "in", time()-t0

        test_similarity_for_users(conn, u1, u2)
        print "Average similarity computation time over", len(times), "sim() calls:", mean(times)
        ans = raw_input("Try two other randomly chosen users? [Y/n]").lower()
        if ans == 'n' or ans == 'no':
            print "Exiting..."
            exit()
        print "OK, once again!"

def test_similarity_for_users(conn, u1, u2):
    init_mdb(conn)
    print "Computing similarity..."
    t0 = time()
    print sim(u1, u2)
    t = time()-t0
    times.append(t)
    print "Computed in", t

def test_same_user(host):
    print "Testing similarity of a random user with herself"
    import sys
    sys.stdout.flush()
    from pymongo import MongoClient
    conn = MongoClient(host=host)
    u = conn.users.clicks.find_one()['uid']
    print "Chosen user is", u
    test_similarity_for_users(conn, u, u)

def test_wtf(host):
    print "Testing wtf"
    from pymongo import MongoClient
    conn = MongoClient(host=host)
    test_similarity_for_users(conn, 383, 66)

if __name__ == '__main__':
    test()
    # Note: a good line for testing/debugging in IPython shell: 
    # import users_similarity as us; reload(us); us.init_mdb(a); t0=time(); print "SIM=", us.sim(66, 66), "took=", time()-t0