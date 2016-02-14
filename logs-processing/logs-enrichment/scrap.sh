#!/bin/bash

basename='/h/cppr_sync_data/data-gathered/serp_requeries/manually_selected_10_queries_similar_users_queries_grab_all_second_trial'
echo "Removing old data not to be merged..."
rm ${basename}*.json -v

time scrapy crawl serp -a logs_filename="/h/cppr/data/merged-aol-logs.txt"\
 -a query_strings_filename="/h/cppr/data/serp_crawl_queries_to_be_reissued_similar_user_profiles_queries.lst"\
 -a export_path="${basename}.json"\
 -a use_proxies=true
