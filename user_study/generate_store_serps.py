#!/usr/bin/python

"""
    This script generates and stores into MDB the SERP results to be used in the user study.

    It takes as input:

    - targeted user and queries + query strings (list of triple[t]s)
    - a hostname to MongoDB where it will seek:
        + scores for the queries and users targeted
    - a hostname of ElasticSearch where it will seek:
        + the X top results for each of the targeted queries
    - the web graph GraphML.xml.gz file

    It will output:
    For every (query, user):
    - the complete SERP to be displayed on the frontend, that is to say an ordered list of the following items:
        + title
        + snippet/description
"""
from pymongo import MongoClient
from time import time
from elasticsearch import Elasticsearch

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs-processing/"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
from univ_open import univ_open
from ppr import cppr_computation as cc
# from load_similar_users import load_sim_users
# from load_query_url_to_domain_log_id_mapping import load_mapping

ES_INDEX_NAME = "web_crawl_bm25_with_desc_final"
TOP_K = 2000

def load_user_queries_ids_and_str_triplets(targets_file):
    queries_ids_to_str_mapping = {}
    queries_users_pairs = []
    with univ_open(targets_file, 'r') as f:
        for line in f:
            qid, uid, qstr = line.strip().split('\t')
            qid, uid = int(qid), int(uid)
            queries_users_pairs.append((qid, uid))
            queries_ids_to_str_mapping[qid] = qstr

    return queries_users_pairs, queries_ids_to_str_mapping

def load_es_results(es_host, top_n_results_from_es, queries_ids_to_str_mapping):
    client = Elasticsearch(host=es_host, port=80)

    es_results = {}

    for qid, qstr in queries_ids_to_str_mapping.items():
        print "Querying ES for", qstr, "..."
        results = client.search(
            index=ES_INDEX_NAME,
            doc_type='web_page',
            size=top_n_results_from_es,
            body={
                'query': {
                    'match': {
                        'content': qstr
                    }
                }
            },
            fields=['_id', '_score', 'url', 'title', 'description']
        )['hits']['hits']
        print "Done"

        print "Indexing results..."
        es_results[qid] = {
            'set_of_urlids': set([int(item['fields']['_id']) for item in results]),
            'es_items': [
                {
                    'title': i['fields']['title'][0],
                    'desc': i['fields']['description'][0],
                    'url': i['fields']['url'][0],
                    'urlid': int(i['fields']['_id']),
                    '_score': i['_score']
                }
                for i in results
            ]
        }
        print "Done"

    return es_results

# def merge_rankings_and_take_top_ten(es_result, cppr):
#     return sorted([
#         cppr[int(i['_id'])]
#     ], lambda x: x['score'])[:10]

def commit_serp(mdb_host, qid, uid, query_str, pr, cppr, res):
    """
        :param{MongoClient} mdb_conn
        :param{int} qid
        :param{int} uid
        :param{string} query_str
        :param{dict} cppr: mapping {(int)urlid -> (float) cppr score}
        :param{list} res: [{title, desc, url, urlid, _score}]
    """
    print "Committing..."
    # We'd rather connect here so that as the process if very long, if we get disconnected in between at least
    # we will reconnect
    mdb_conn = MongoClient(host=mdb_host)
    mdb_conn.user_study.serps_tests2.save({
        '_id': qid,
        'qstr': query_str,
        'uid': uid,
        'ranking_noperso': sorted([
            {
                'title':        i['title'],
                'desc':         i['desc'],
                'url':          i['url'],
                'urlid':        i['urlid'],
                'score_es':     i['_score'],
                'score_ppr':    pr[i['urlid']],
                'score':        i['_score'] * pr[i['urlid']]
            } for i in res
        ], key=lambda x: x['score'], reverse=True)[:TOP_K],
        'ranking_perso': sorted([
            {
                'title':        i['title'],
                'desc':         i['desc'],
                'url':          i['url'],
                'urlid':        i['urlid'],
                'score_es':     i['_score'],
                'score_cppr':   cppr[i['urlid']],
                'score':        i['_score'] * cppr[i['urlid']]
            } for i in res
        ], key=lambda x: x['score'], reverse=True)[:TOP_K]
    })
    print "Done"

DBG = False

CLI_ARGS = [
    "users_queries_ids_and_strings_triplets.lst",
    "mongodb_host",
    "es_host",
    "graph_path.xml.gz",
    "urlid_to_log_domainids_mapping_file"
]
OPT_ARGS = ["top_n_results_from_es"]
def main(argv):
    argc = len(argv)
    if argc < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        print "Missing arguments:", " ".join(CLI_ARGS[argc-1:])
        exit()

    targets_file   \
    , mdb_host     \
    , es_host      \
    , graphml_path \
    , mapping_file = [argv[i].strip() for i in range(1, len(CLI_ARGS)+1)]

    print "Connected to MDB"

    top_n_results_from_es = TOP_K
    if argc > len(CLI_ARGS) + 1:
        try:
            top_n_results_from_es = int(argv[len(CLI_ARGS) + 1])
        except ValueError:
            pass

    print "Loading triple[t]s file..."
    t0 = time()
    queries_users_pairs, queries_ids_to_str_mapping = load_user_queries_ids_and_str_triplets(targets_file)
    print "Done in", time()-t0

    print "Loading ES Results..."
    t0 = time()
    es_results = load_es_results(es_host, top_n_results_from_es, queries_ids_to_str_mapping)
    print "Done in", time()-t0
    # print es_results[queries_users_pairs[0][0]].values()  # Debug

    print "Initializating CPPR Computation module..."
    t0 = time()
    cc.init(graphml_path, mdb_host, mapping_file)
    print "Done in", time()-t0

    print "Launching computation..."
    t0 = time()
    for qid, uid in queries_users_pairs:
        res = es_results[qid]
        pr = cc.PRMapped(res['set_of_urlids'])
        cppr = cc.CPPRMapped(uid, qid, res['set_of_urlids'])
        commit_serp(mdb_host, qid, uid, queries_ids_to_str_mapping[qid], pr, cppr, res['es_items'])
    print "Done in", time()-t0

if __name__ == '__main__':
    from sys import argv
    main(argv)