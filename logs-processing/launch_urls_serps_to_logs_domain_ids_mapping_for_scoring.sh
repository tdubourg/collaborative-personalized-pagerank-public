#!/bin/bash

time ./mapping_aol_logs_to_serps.py \
$HOME/cppr/data/merged.converted.converted.txt.gz \
$VPS \
$HOME/cppr/data/manually_selected_10_query_user_pairs.converted.lst \
$HOME/cppr/data/query_str_to_ids.lst.gz \
$HOME/cppr/data/data-gathered/serp_requeries/manually_selected_10_queries.converted.json \
$HOME/cppr/data/urls_from_web_crawl_ids_to_domains_logs_ids_mapping.lst.gz \
$HOME/cppr/data/2014_serps_urlid_to_logs_domain_ids.dict.custom.format.lst