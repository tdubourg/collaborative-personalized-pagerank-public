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

mdb = None
DBG = False
PERF_DBG = False

def init_mdb(mdb_conn):
    global mdb
    mdb = mdb_conn

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
        result = sum([P(q, u) * w(q) * clusters(q) for q in queries(u)])
        c_l_cache[u] = result
    return result

def queries(u):
    """
        Returns the list of all queries that u issued in the past
    """
    if DBG:
        print "queries(", u, ")"
    return mdb.users.clicks.find({'uid': u}).distinct('qid')

clusters_cache = {}
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
            result = array(mdb.queries.clustering.find_one({'_id': qid})['vector'])  # this query is indexed
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
def clicks(q, u):
    try:
        result = clicks_cache[(q, u)]
    except KeyError:  # cache miss
        where_clause = {'uid': u, 'qid': q} if q is not None else {'uid': u}  # this query is indexed
        if PERF_DBG:
            from time import time
            t0 = time()
            print "Computation for clicks(", q, ",", u, ")\t\t\tstarted"
        result = sum([\
            _['n'] for _ in \
            mdb.users.clicks.find(where_clause) \
        ])
        clicks_cache[(q, u)] = result
        if PERF_DBG:
            print "Executed in about\t\t\t\t", time()-t0
    if DBG:
        print "Result clicks(", q, ",", u, ")=", result
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

from time import time
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
    global times
    init_mdb(conn)
    print "Computing similarity..."
    t0 = time()
    print sim(u1, u2)
    t = time()-t0
    times.append(t)
    print "Computed in", t

def test_same_user(host):
    print "Testing similarity of a random user with herself"
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