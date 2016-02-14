#!/bin/bash

#clear && time ./compute_top_similar_users_in_ram.py $VPS ~/cppr/data/ids_of_top_urls.lst ~/cppr/data/users_who_queried_top_urls.lst ~/cppr/data/merged.converted.converted.txt.gz
clear && time ./compute_usage_scoring.py \
$HOME/cppr/data/fairy_wings_query_user_pair.txt \
$VPS \
/home/troll/cppr/data/fairy_wings_scoring_computation_filter_query_file.lst \
/home/troll/cppr/data/fairy_wings_user_and_sim_users.lst \
$HOME/cppr/data/merged.converted.converted.txt.gz \
$HOME/cppr/data/clusters_lyes/Clusters-1.314.txt \
$HOME/cppr/data/query_str_to_ids.lst.gz
