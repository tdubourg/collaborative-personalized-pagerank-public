#!/usr/bin/python

"""
    This is a very quick & very dirty script that temporarily takes care of generating the query strings to be reissued
    related to the similar users profiles of the selected targeted users!
"""

from os.path import join as pjoin
from os import getenv

HOME = getenv('HOME')
VPS = getenv('VPS')

from univ_open import univ_open
from load_similar_users import load_set_of_similar_users

s = load_set_of_similar_users(VPS, [220, 41375, 2769343, 204071, 71845, 10718, 71845, 2506339, 215161, 40164, 61656])

print "The total number of users that will be used for computation is", len(s)

from compute_top_similar_users_in_ram import load_big_query_set, compute_removed_queries_because_of_null_clustering, load_clusters_for_queries
qs = load_big_query_set(pjoin(HOME, 'cppr/data/merged.converted.converted.txt.gz'), s)

print "The total number of queries that will be used for computation is", len(qs)

print "Computing clustering information..."
clusters_path = pjoin(HOME, 'cppr/data/clusters_lyes/Clusters-1.314.txt')
queries_id_mapping_filepath = pjoin(HOME, 'cppr/data/query_str_to_ids.lst.gz')
clusters = load_clusters_for_queries(
    qs,
    clusters_path,
    queries_id_mapping_filepath
)

print "Computing the queries that we can remove..."

removed_queries = compute_removed_queries_because_of_null_clustering('/tmp/blorg', clusters)

print "We can remove", len(removed_queries), "from this set"

final_set = qs - removed_queries 
print "That makes the total set of size:", len(final_set)

# Now get the real query strings:
print "Converting from queryids back to query strings..."
query_strings_set = set()
with univ_open(queries_id_mapping_filepath, mode='r') as f:
    queryid = 0
    for l in f:
        if queryid in final_set:
            query_strings_set.add(l.strip().lower())
        queryid += 1  # lines numbers are the ids of the queries

output_path = pjoin(HOME, 'cppr/data/serp_crawl_queries_to_be_reissued_similar_user_profiles_queries.lst')
print "Outputting result to", output_path, "..."
with univ_open(output_path, mode='w+') as out:
    out.write('\n'.join(query_strings_set))

print "Done"