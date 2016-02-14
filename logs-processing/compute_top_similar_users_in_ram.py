#!/usr/bin/python

"""
This script takes as input:
    - allowed users
    - allowed queries
to be taken into account for the groups of top-K similar users. 
It also takes as input:
    - the necessary files containing this information:
        - the querystr -> id mapping
        - the clicks logs
        - the clusters...

In addition to that, the MDB host where the clusterings, clicks, etc. are stored is also needed.

The script will load all the necessary information in RAM, parsing again the files in some cases (because it's faster 
than retrieving from MDB) and will then compute the all-pairs similarity between users.

The process of this script goes as follows:

It first loads the "extended" list of users: all the users that have clicked once on one of the allowed queries.

Then it computes the new list of "allowed queries" ("big query list"), that is _all the queries that have been clicked_
by the _extended set of users".

Using those lists, it will grab all the clicks information that is related to these users and these queries.

It will constitude the "user profile" using this. And it will compute the all-pairs similarity of the current users.

"""

from time import time
from univ_open import univ_open
from multiprocessing import Pool

# This is the minimum interval between two log lines about the same query to consider that the user issued twice the 
# query and not simply got back to the search result and clicked a new query
SAME_QUERY_TIME_INTERVAL = 600  # In seconds # TODO: Check what the right time would be in the litterature?

from store_users_times_per_query import process_logfile as process_log_times_pq
from store_users_clicks import process_logfile as process_log_clicks
from store_queries_clustering import ClustersProcessor
import users_similarity_in_ram as us
# import users_similarity as us_mdb

from store_similar_users import compute_everything

# Constants already initialized, "arbitraty"/"static" values
N_OF_PRINTS_PER_BATCH   = 15
ZERO_FLOAT              = 1e-10
POOL_SIZE               = 3
'''
It seems that multiprocessing module does not respawn workers between tasks. So a small value for BATCH_SIZE
could actually be OK as it would likely use less RAM but would still not need to regenerate cache.... ? Let's try & see
'''
BATCH_SIZE              = 300
TOP_N_SIMILAR_USERS     = 100

# Constants that will be dynamically computed
DATA_SET_SIZE           = None

# Globals, mainly here for simplifying multiprocessing
users_set               = None
big_queries_set         = None
clusters                = None
mdb_host                = None

from numpy import array

def load_clusters_for_queries(q_set, clusters_path, queries_id_mapping_filepath, pre_initialized_dict=dict(), cp=None):
    """
        Loads all the clustering vectors of the queries in the q_set parameter.
        :param q_set the set of queries to return the clustering vectofs of
        :param queries_id_mapping_filepath The path to the file providing a mapping from query string to query id
        :param clusters_path the path to the clusters file
        :param pre_initialized_dict if passed as a parameter, this dictionary will be used directly instead of 
            instiantiating a new one, this can speed up computation if the dictionary already has keys initialized.
        :param {ClustersProcessor} cp : A pre-initialized ClusterProcessor to be used instead of initializing our own one
        :return a dictionary {query_id (int) => clustering vector (numpy.array)}
    """
    if cp is None:
        cp = ClustersProcessor(clusters_path)
    t0 = time()
    cp.process()
    clusters = pre_initialized_dict
    with univ_open(queries_id_mapping_filepath, mode='r') as f:
        query_id = -1  # will represent both the query_id and the index in the list
        for line in f:
            query_id += 1
            if query_id % 200000 is 0:
                print "Currently at query_id=", query_id
            if query_id not in q_set:
                continue
            clusters[query_id] = array(cp.cluster_vector_for_kw(line))
    return clusters

def load_big_query_set(log_filepath, allowed_users):
    """
        Loads the set of all queries that have been issued by at least one of the allowed users 
        (and thus are part of their profile)
    """
    set_of_queries = set()
    with univ_open(log_filepath) as f:
        for line in f:
            line = line.strip().split('\t')
            n = len(line)
            if n is not 5 and n is not 3:
                continue
            if int(line[0]) in allowed_users:
                set_of_queries.add(int(line[1]))
    return set_of_queries

from gzip import open as gzopen
from pickle import load as pload

from pickle_utils import *
import pickle_utils
pickle_utils.NO_PICKLE = True  # Temporarily disabling questions for debugging

def user_pair(start_user):
    maxi = start_user + BATCH_SIZE - 1
    i = -1
    for u1 in users_set:
        i += 1
        if i < start_user:
            continue
        if i > maxi:
            break
        # We do not want to run similarity against ourselves... so exclude ourselves from the set
        for u2 in (users_set - set([u1])):
            yield (u1, u2)

def compute_user_sim_batch(start):
    """
        This function will be executed by the worker process. It computes a batch of user similarities, starting at
        start-th user_id in the global variabl `users_set` and until the (start+BATCH_SIZE)-th user_id

        For every user_id it will compute the similarity against _ALL_ the other users (except the same user) and
        will keep the `TOP_N_SIMILAR_USERS`-th top ones in terms of similarity value.

        It will then commit them directly to mongodb before terminating.

    """
    from heapq import heappushpop as pp
    print "Starting compute_user_sim_batch(", start, ")"
    # Initializing heaps for every user we are going to deal with
    results = {uid:([0] * TOP_N_SIMILAR_USERS) for uid in list(users_set)[start:start+BATCH_SIZE]}
    t0 = time()
    t1 = time()
    i = 0
    print_interval = int(BATCH_SIZE*len(users_set)/N_OF_PRINTS_PER_BATCH)  # So that we approximately print the state X times
    for u1, u2 in user_pair(start):
        # print "Executing process", start, "for", u1, u2
        try:
            sim_res = us.sim(u1, u2)
            if abs(sim_res - 1.0) < ZERO_FLOAT:
                continue  # Do not keep similarities too close to 1.0 (too similar users)
            pp(results[u1], (sim_res, u2))
        except KeyError as err:
            print err
            print "Huh? KeyError u1=", u1, "start=", start, "BATCH_SIZE=", BATCH_SIZE
        i += 1
        if i % print_interval is 0:
            print i+1, \
                "sim() calls\t in     %5.1f"    % (time()-t0), \
                "\t\t avg     %.4e"             % ((time()-t0)/float(i+1)), \
                "\t local_avg     %.4e"         % ((time()-t1)/float(i+1)), \
                "\t(process", start, ")"
            t1 = time()
    print "Computation from", start, "to", start + BATCH_SIZE, "finished in", time()-t0,". Committing..."
    t0 = time()
    commit_user_sims(start, results)
    print "Finished committing in", time()-t0
    return True  # Just to show we finished things properly

def commit_user_sims(start, results):
    """
        This function simply commits a bunch of top similar users vectors to MongoDB.
        :param start: the start index of the user ids batch in the global users_set
        :param results: a list of heaps containing the top similar users. The heap will be transformed into a list using
            heapq.nlargest so make sure it is a valid heap!
        :return None
    """
    from heapq import nlargest
    from pymongo import MongoClient
    mdb = MongoClient(host=mdb_host)
    # save() method does not take bulk inserts, so let us just remove everything and re-insert everything    
    mdb.users.similar_users.remove({'_id': {'$in': list(users_set)[start:start+BATCH_SIZE]}})
    mdb.users.similar_users.insert([ \
        {
            '_id': u1,
            # Now, transform back all the heaps into highest-to-lowest lists
            # using nlargest() that should be able to extract things in O(n) while sorting would be in O(nlogn)
            'sim_users': nlargest(TOP_N_SIMILAR_USERS, sim_users)
        } \
        for u1, sim_users in results.items() \
    ])
    mdb.close()

# def do_process_log_clicks(tu):
#     t0 = time()
#     res = process_log_clicks(*tu)
#     print "!! Took", time()-t0, "to execute process_log_clicks(). Returning"
#     print "The type of the result is:", type(res)
#     return res

def do_process_clusters_pickle(pickle_path_clusters):    
    global big_queries_set, clusters

    try:
        print "Trying to pickle from disk...", pickle_path_clusters
        with gzopen(pickle_path_clusters, 'r') as f:
            print "File", pickle_path_clusters, "was found!"
            clusters = load_pickled_dict_to_np_arrays(f, pre_initialized_dict=clusters)
    except Exception as err:
        print "Error for", pickle_path_clusters, "was:", err
        return False
    return clusters

def do_process_clusters_recompute(big_queries_set, clusters_file, queries_to_ids_file, clusters):
    print "No pickled files or error loading it, recomputing..."
    t0 = time()
    load_clusters_for_queries(big_queries_set, clusters_file, queries_to_ids_file, pre_initialized_dict=clusters)
    print "Done ", time()-t0
    return clusters    

def compute_removed_queries_because_of_null_clustering(pickle_path_removed_queries, clusters, join_clusters=None):
    """
        This function will compute the set of queries that should be removed because they have a null clustering 
        over the clusters we are passed in argument.

        :param clusters: a dict {qid: clustering_vector}
        :param join_clusters: if the clusters are being loaded in a background process, the function to be executed to
            force to wait for this background process to have finished before accessing the clusters object
    """
    from numpy.linalg import norm
    print "Looking for queries with null cluster vector..."
    t0 = time()
    try:
        print "Trying to pickle from disk...", pickle_path_removed_queries
        with gzopen(pickle_path_removed_queries, 'r') as f:
            print "File", pickle_path_removed_queries, "was found!"
            removed_queries = set(load_pickled_list(f))
        pickled = True
    except Exception as err:
        if not isinstance(err, IOError):
            print "Error for", pickle_path_removed_queries, "was:", err
        print "No pickled files or error loading it, recomputing..."
        pickled = False
        removed_queries = set()
        # In case of recomputation we need to wait for the clusters data to be available, if they're loaded in bg
        if join_clusters is not None:
            join_clusters()
        for qid, cl in clusters.items():
            if norm(cl) < ZERO_FLOAT:  # Should be precise enough?
                removed_queries.add(qid)
    print "Done ", time()-t0
    pickle_ask(pickled, pickle_path_removed_queries, removed_queries, dump_f=pickle_list)
    return removed_queries

from multiproc_utils import *

CLI_ARGS = ['mongodb_host', 'filter_queries_file', 'allowed_users_file', 'log_filepath', "clusters_file", "queries_to_ids.lst"]
def main(argv, stop_after_init=False, preset_set_of_users=None):
    pickle_path_lptq                    = '/tmp/process_log_times_pq.bin.gz'
    pickle_path_clicks                  = '/tmp/process_log_clicks.bin.gz'
    pickle_path_clusters                = '/tmp/process_log_clusters.dict.txt.gz'
    pickle_path_removed_queries         = '/tmp/process_log_removed_queries.lst.txt.gz'
    pickle_path_big_queries_set         = '/tmp/process_log_big_queries_set.lst.txt.gz'
    pickle_path_users                   = '/tmp/process_log_usets_set.lst.txt.gz'

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print "Usage: %s"  % argv[0], ' '.join(CLI_ARGS)
        print "Currently missing parameters arguments:", ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    global mdb_host
    mdb_host                = argv[1].strip()
    filter_queries_file     = argv[2].strip()
    allowed_users_file      = argv[3].strip()
    log_filepath            = argv[4].strip()
    clusters_file           = argv[5].strip()
    queries_to_ids_file     = argv[6].strip()

    t_init = time()

    # print "Starting... compute_everything()"
    # t0 = time()
    # everything = compute_everything(mdb_host, filter_queries_file, allowed_users_file)
    # removed_queries = everything['removed_queries']
    # print "Done ", time()-t0


    ########################################################################################################################
    # We are going to do a lot of "is in allowed users?" so we need a set, not a list
    print "Loading users..."
    # users_set = set([int(line.strip()) for line in univ_open(allowed_users_file, mode='r')])
    # We use compute_everything because it gets rid of the null-clusters queries before retrieving the list
    # of users, thus reducing the dataset overall, as queries are then retrieved from the users set
    t0 = time()
    global users_set
    if preset_set_of_users is not None:
        users_set = preset_set_of_users
    else:
        try:
            print "Trying to pickle from disk...", pickle_path_users
            with gzopen(pickle_path_users, 'r') as f:
                print "File", pickle_path_users, "was found!"
                users_set = set(load_pickled_list(f))
            pickled = True
        except Exception as err:
            print "Error for", pickle_path_users, "was:", err
            # if not isinstance(err, IOError):
            print "No pickled files or error loading it, recomputing..."
            pickled = False
            # Note: here we use compute_everything because it will load the queries clusters OF THE INITIAL QUERIES only
            # remove the ones that have null clusterings
            # and then generate the list of users who queried the pruned list of queries
            # we do not direclty use the clusters from it, nor the queries, because we still have to remove the other queries
            # that have null clustering vectors. By "other queries" we mean not queries we use as the seed to select some user/data
            # any queries that is part of a user profile of one of the allowed users (the ones who queried the query list seed)
            # this bigger queries set is generated by load_big_query_set() in this file
            users_set = set(compute_everything(mdb_host, filter_queries_file, allowed_users_file)['users'])
        print "Done ", time()-t0
        print "Total number of users that will be analyzed:", len(users_set)
        pickle_ask(pickled, pickle_path_users, users_set, dump_f=pickle_list)
        print "Done ", time()-t0
        # everything = None  # We are not using it afterwards, so, this should help the GC

    ####################################################################################################################

    # import itertoolsmodule as iter
    print "Computing the set of allowed queries..."
    t0 = time()
    try:
        print "Trying to pickle from disk...", pickle_path_big_queries_set
        with gzopen(pickle_path_big_queries_set, 'r') as f:
            big_queries_set = set(load_pickled_list(f))
        pickled = True
    except Exception as err:
        if not isinstance(err, IOError):
            print "Error for", pickle_path_big_queries_set, "was:", err
        print "No pickled files or error loading it, recomputing..."
        pickled = False
        big_queries_set = load_big_query_set(log_filepath, users_set)
    print "Done ", time()-t0
    print "Total number of queries that will be analyzed:", len(big_queries_set)
    pickle_ask(pickled, pickle_path_big_queries_set, big_queries_set, dump_f=pickle_list)
    
    ####################################################################################################################

    global clusters
    print "Pre-initializing clusters dict..."
    t0 = time()
    clusters = dict.fromkeys(big_queries_set)
    print "clusters now has", len(clusters), "keys"
    print "Done ", time()-t0

    print "Retrieving big list of clusters for the", len(big_queries_set), "queries..."
    t0 = time()

    global clusters_loaded
    clusters_loaded = False
    p_clusters, mapres_clusters = run_in_bg_process(do_process_clusters_pickle, (pickle_path_clusters,))
    
    def join_clusters():
        p_clusters.join()
        global clusters, clusters_loaded
        if clusters_loaded:
            return clusters
        result = mapres_clusters.get()[0]
        if result is False:  
            # The pickling from disk did not work, recompute it in place (join_clusters() is called when clusters are 
            # NEEDED so we cannot wait/async this))
            print "Error while pickling clusters from disk", pickle_path_clusters, ", recomputing..."
            t0 = time()
            result = do_process_clusters_recompute(big_queries_set, clusters_file, queries_to_ids_file, clusters)
            print "Done do_process_clusters_recompute()", time()-t0
            # Any user input needs to be on the main thread, pickle ask will by itself send the pickling task to a bg
            # worker process if the user answers yes
            pickle_ask(False, pickle_path_clusters, result, dump_f=picke_dict)
        clusters_loaded = True
        clusters = result
        return clusters

    ########################################################################################################################
    removed_queries = compute_removed_queries_because_of_null_clustering(pickle_path_removed_queries, clusters, join_clusters)
    print "Removed", len(removed_queries), "out of", len(big_queries_set)
    ########################################################################################################################
    t1 = time()
    print "Launching process_log_clicks computation in a separated process"
    p_lpc, lpc_mapres = run_in_bg_process(process_log_clicks, (log_filepath, users_set, removed_queries))
    p_lpc.close()
    ########################################################################################################################
    ########################################################################################################################

    print "Starting... process_log_times_pq()"
    t0 = time()
    try:
        print "Trying to pickle from disk...", pickle_path_lptq
        lptpq = pload(gzopen(pickle_path_lptq, 'rb'))
        pickled = True
    except Exception as err:
        if not isinstance(err, IOError):
            print "Error for", pickle_path_lptq, "was:", err
        print "No pickled files or error loading it, recomputing..."
        pickled = False
        lptpq = process_log_times_pq(log_filepath, users_set, removed_queries)
    print "Done process_log_times_pq() in", time()-t0
    pickle_ask(pickled, pickle_path_lptq, lptpq)

    print "Starting... process_log_clicks()"
    t0 = time()
    # Note: Disabled the pickling as, for some reason, it does not work
    # and there is only ~15s difference between recomputation and pickling from disk anyway...
    # try:
    #     print "Trying to pickle from disk..."
    #     lpc = pload(open(pickle_path_clicks, 'rb'))
    #     pickled = True
    # except Exception as err:
    #     if not isinstance(err, IOError):
    #         print "Error was:", err
    #     print "No pickled files or error loading it, recomputing..."
    #     pickled = False
    #     lpc = process_log_clicks(log_filepath, users_set, removed_queries)
    ########################################################################################################################
    ########################################################################################################################
    print "waiting for the pool to finish, if not finished yet..."
    p_lpc.join()
    lpc = lpc_mapres.get()[0]
    print "Took a total time of", time()-t1, "or less"
    ########################################################################################################################
    ########################################################################################################################
    print "Done ", time()-t0
    # pickle_ask(pickled, pickle_path_clicks, lpc)

    print "Some reprocessing..."
    # We need the clusters from now on, so let us wait for the children process to be finished and the data 
    # transferred back to us
    join_clusters()
    print "Removing null-vectors clusters queries from `clusters`..."
    t0 = time()
    for qid in removed_queries:
        try:
            del clusters[qid]
        except KeyError:
            pass  # If it was already not there, that's perfect
    print "Done ", time()-t0


    t0 = time()
    for user_queries_dic in lpc.user_clicks_number:
        if user_queries_dic is None:
            continue
        del user_queries_dic['_id']
    for user_queries_dic in lptpq.user_queries_number:
        if user_queries_dic is None:
            continue
        del user_queries_dic['_id']
    print "Done ", time()-t0

    # Deprecated, for now, but we might switch back to it so, keep it for now
    print "Computing number of users who issued the query, per query..."
    t0 = time()
    number_of_users_who_queried = dict.fromkeys(big_queries_set - removed_queries, 0)
    for query_dict in lptpq.user_queries_number:
        if query_dict is None:
            continue
        for qid in query_dict:
            number_of_users_who_queried[qid] += 1
    print "Done ", time()-t0

    print "Computing number of users who clicked, per query..."
    t0 = time()
    number_of_users_who_clicked = dict.fromkeys(big_queries_set - removed_queries, 0)
    for query_dict in lpc.user_clicks_number:
        if query_dict is None:
            continue
        for qid in query_dict:
            number_of_users_who_clicked[qid] += 1
    print "Done ", time()-t0

    # # GC
    big_queries_set = None
    removed_queries = None

    # print "Some reprocessing..."
    # t0 = time()
    # for user_queries_dic in lpc.user_clicks_number:
    #     if user_queries_dic is None:
    #         continue
    #     del user_queries_dic['_id']
    #     for q in removed_queries:
    #         try:
    #             del user_queries_dic[q]
    #         except KeyError:
    #             # key was not there? fine, we did not need to delete it then
    #             pass
    # for user_queries_dic in lptpq.user_queries_number:
    #     if user_queries_dic is None:
    #         continue
    #     del user_queries_dic['_id']
    #     for q in removed_queries:
    #         try:
    #             del user_queries_dic[q]
    #         except KeyError:
    #             # key was not there? fine, we did not need to delete it then
    #             pass
    print "Done ", time()-t0

    print "Starting..."
    t0 = time()
    us.init(
        lpc.user_clicks_number,
        lptpq.user_queries_number,
        clusters,
        users_set,
        number_of_users_who_queried,
        number_of_users_who_clicked
    )
    print "Done ", time()-t0
    # Note: At this point in the main() execution, the script takes ~2.5G of RAM.

    print "Total initialization phase time:", time()-t_init

    if stop_after_init:
        return

    print "Initializing users similarity computation phase..."
    # Similarity computation benchmark:
    t0 = time()
    i = 0
    global DATA_SET_SIZE
    DATA_SET_SIZE = len(users_set)
    # Note: a too small batch size will waste time respawning processes and re-generating the user_sim module cache
    # but a too high batch size will kill mongodb and the computer's RAM (as 1 batch size unit is 1 user computed by
    # the process and the process commits everything at once)
    print "Generating sorted users set..."

    print "Generating workers pool..."
    p = Pool(processes=POOL_SIZE)
    start_values = range(0, DATA_SET_SIZE, BATCH_SIZE)
    print "Mapping (launching) pool to", len(start_values), "different start_values", start_values
    t0 = time()
    p.map(compute_user_sim_batch, start_values)
    p.close()
    p.join()
    print "Workers finished in %.3f." % (time()-t0)

    # for u in users_set:
    #     for u2 in users_set:
    #         i += 1
    #         try:
    #             us.sim(u, u2)
    #         except KeyError as err:
    #             print err
    #             key = err.args[0]
    #             print key, "in big_queries_set?", key in big_queries_set
    #             print key, "in removed_queries?", key in removed_queries
    #             print key, "in clusters?", key in clusters
    #             res = False
    #             for u_dict in lpc.user_clicks_number:
    #                 if u_dict is not None:
    #                     res |= (key in u_dict)
    #             print key, "in clicks?", res
    #             res = False
    #             for u_dict in lptpq.user_queries_number:
    #                 if u_dict is not None:
    #                     res |= (key in u_dict)
    #             print key, "in user_queries_number?", res
    #         if i % 10000 is 0:
    #             print i+1, "\t\tsim() calls in\t\t", time()-t0, "\t\taverage\t\t", (time()-t0)/float(i+1)

    raw_input("Now what?")

if __name__ == '__main__':
    import sys
    main(sys.argv)