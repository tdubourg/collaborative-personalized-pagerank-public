#!/usr/bin/python

"""
    This script will setup the necessary data for the final evaluation run...
"""

import users_similarity as us

mdb = None
DBG = False
PERF_DBG = False

def init_mdb(mdb_conn):
    global mdb
    mdb = mdb_conn

def users_who_queried(q_list):
    """
        Returns the list of user ids that queried a specific query ids list
    """
    return mdb.users.queries.find({"qid": {'$in': q_list}})

def retrieve_users_clusters(q_list):
    return mdb.queries.clustering.find({"_id": {'$in': q_list}})

ZERO_FLOAT = 1e-30
INNER_PRODUCT_THRESHOLD = 1e-10
N_QUERIES = 100

def compute_everything(host, queries_filter_file, allowed_users_file, top_n=N_QUERIES, null_cluster_norm_threshold=ZERO_FLOAT):
    """
        This function will take as input a list of allowed queries and users and
        output the users and queries after filtering the ones (users and queries) that have null clustering
        vector + will output some other useful information..

        Inputs:
            see CLI arguments corresponding to most of the arguments of this method.
            top_n is maximum the number of queries that we keep, after having pruned the ones with null clustering vectors
            null_cluster_norm_threshold the is floating point threshold under which we consider a clustering vector
                to be null
        Outputs:
            users: the set of users that both queried at least once a query of queries_filter_file 
                and are in the allowed_users_file set of users
            sums_of_clusters: the sum of all clusters of queries the user queried
            q_list: the list of queries that we kept, from queries_filter_file and 
                by removing queries with null clustering vectors
            clusters: the clusters that we loaded, for the given queries
            removed_queries: queries with null clustering vector that we removed
    """


    from univ_open import univ_open
    from numpy.linalg import norm
    from pymongo import MongoClient
    print "Connecting to MongoDB..."
    mdb_conn = MongoClient(host=host)
    init_mdb(mdb_conn)
    us.init_mdb(mdb_conn)

    print "Parsing filter files..."
    print "Queries list..."
    q_list = [int(line.strip()) for line in univ_open(queries_filter_file, mode='r')]

    print "Loaded", len(q_list), "seed queries."

    print "Retrieving queries clusters..."
    # Retrieve all the clusters of the queries
    clusters = us.clusters(q_list)
    # Check for null vectors... just in case...
    print "Checking for null clusters vectors..."
    removed_queries = []
    for qid, cl in clusters.items():
        if norm(cl) < ZERO_FLOAT:  # Should be precise enough?
            print "Warning, query", qid
            print "Removing it"
            del clusters[qid]
            removed_queries.append(qid)

    print "Previously had", len(q_list), "queries. Now have", len(clusters), "queries"
    print "Taking the top", top_n,"out of them"
    q_list2 = []
    for q in q_list:
        if q in clusters:
            q_list2.append(q)
            if len(q_list2) >= top_n:
                print "Reached the", top_n, "queries"
                break
    q_list = q_list2
    
    print "Allowed users list..."
    allowed_users = set([int(line.strip()) for line in univ_open(allowed_users_file, mode='r')])
    
    print "Parsed user file, processing it..."
    users_queries = {}
    for item in users_who_queried(q_list):
        uid = item['uid']
        if uid in allowed_users:
            try:
                users_queries[uid].append(item['qid'])
            except KeyError:
                users_queries[uid] = [item['qid']]

    # Now, we are going to generate the list of pairs to compute similarity against, by only keeping pairs of users
    # that have at least one cluster in common, that is to say, that issued at least one query that has a cluster in
    # common with at least one query of the other user...
    users = users_queries.keys()
    n_users = len(users)
    # We compute all of them at once instead of doing it in the loop because if we did it in the loop we would end up
    # computing them multiple times (i times for the ith item of the 'users' list)
    print "Computing sums of clusters vectors per user... (", n_users, "users)"

    sums_of_clusters = []
    for u in users:
        try:
            for qid in users_queries[u]:
                try:
                    sums_of_clusters.append(sum(clusters[qid]))
                except KeyError as err:
                    print err
                    print "The qid=", qid, "was not found?!?"
                    exit()
        except KeyError as err:
            print err
            print "The user=", u, "was not found?!?"
            exit()

    return {
        'users': users,
        'sums_of_clusters': sums_of_clusters,
        'q_list': q_list,
        'clusters': clusters,
        'removed_queries': removed_queries,
    }


CLI_ARGS = ['mongodb_host', 'filter_urls_file', 'allowed_users_file']
def main():
    from sys import argv
    from time import time
    from numpy import inner
    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print "Usage: %s"  % argv[0], ' '.join(CLI_ARGS)
        exit()
    host = argv[1].strip()
    queries_filter_file = argv[2].strip()
    allowed_users_file = argv[3].strip()


    everything = compute_everything(host, queries_filter_file, allowed_users_file)

    users = everything['users']
    sums_of_clusters = everything['sums_of_clusters']
    n_users = len(users)


     # [sum([cl for u in users for qid in users_queries[u] for cl in clusters[qid]])]
    print "Computing all pairs...(", len(users),"x",len(users),")"
    t0 = time()
    all_pairs = []
    x = 0
    for i in range(n_users):
        u1 = users[i]
        sum1 = sums_of_clusters[i]
        for j in range(i, n_users):  # Note that we do not need to compare to <i indexes, they already compared against us
            u2 = users[j]
            sum2 = sums_of_clusters[j]
            if inner(sum1, sum2) > INNER_PRODUCT_THRESHOLD:  # The two vectors are NOT normal, which basically means common clusters
                all_pairs.append((u1, u2))
            x += 1
            if x % 20000000 is 0:
                print "Already performed\t", x, "\tcomparisons in\t\t", time()-t0
                print "Already inserted", len(all_pairs), "pairs"

    print "Done in", time()-t0, "seconds"
    print "We found", len(all_pairs), "pairs of users that had at least one cluster in common."
    if raw_input("Print this list?[Y/n]").lower() not in ('n', 'no'):
        print ""  # because raw_input() does not add a new line at the end
        print all_pairs

    raise NotImplementedError("TODO: Finish this script?")

if __name__ == '__main__':
    main()