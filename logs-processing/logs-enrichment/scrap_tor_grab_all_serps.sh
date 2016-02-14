#!/bin/bash

echo "Removing old data not to be merged..."
rm /h/cppr_sync_data/data-gathered/serp_requeries/manually_selected_10_queries_second_trial*

time scrapy crawl serp -a logs_filename="/h/cppr/data/merged-aol-logs.txt"\
 -a query_strings_filename="/h/cppr/data/manually_selected_10_queries.lst"\
 -a export_path="/h/cppr_sync_data/data-gathered/serp_requeries/manually_selected_11_queries_grab_all.json"\
 -a use_proxies=false\
 -a use_tor_port=8118
