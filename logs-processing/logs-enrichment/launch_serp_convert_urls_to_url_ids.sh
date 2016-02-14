#!/bin/bash

time ./convert_serp_result_urls_to_ids.py \
 $HOME/cppr/data/data-gathered/serp_requeries/manually_selected_10_queries_third_trial_serps.json \
 $HOME/cppr/data/web_crawl/ids_to_urls.lst.gz \
 $HOME/cppr/data/data-gathered/serp_requeries/manually_selected_10_queries.converted.json