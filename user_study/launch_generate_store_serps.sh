#!/bin/bash

clear;

time ./generate_store_serps.py \
/h/cppr/data/manually_selected_10_query_user_pairs_and_query_str_triplet.lst \
$VPS \
'130.211.108.139' \
/h/cppr/data/web_crawl/graph_graphtool_with_dangling.graphml.xml.gz \
/h/cppr/data/2014_serps_urlid_to_logs_domain_ids.dict.custom.format.lst \
10000
