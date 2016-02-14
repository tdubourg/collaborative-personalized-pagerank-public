#!/bin/bash

#clear && time ./compute_top_similar_users_in_ram.py $VPS ~/cppr/data/ids_of_top_urls.lst ~/cppr/data/users_who_queried_top_urls.lst ~/cppr/data/merged.converted.converted.txt.gz
clear && time ./compute_usage_scoring.py \
$HOME/cppr/data/manually_selected_10_query_user_pairs.converted.lst \
$VPS \
$HOME/cppr/data/manually_selected_10_queries.converted.lst \
$HOME/cppr/data/targeted_users_and_similar_users.lst \
$HOME/cppr/data/merged.converted.converted.txt.gz \
$HOME/cppr/data/clusters_lyes/Clusters-1.314.txt \
$HOME/cppr/data/query_str_to_ids.lst.gz
