#!/bin/bash

basename="${HOME}/cppr/data/data-gathered/serp_requeries/${NAME}"
echo "Removing old data not to be merged..."
rm ${basename}*.json -v

time scrapy crawl serp -a logs_filename="$HOME/cppr/data/merged-aol-logs.txt"\
 -a query_strings_filename="$HOME/cppr/data/data-gathered/serp_requeries/20_queries_with_high_clicks_and_seem_interesting.lst"\
 -a export_path="${basename}.json"
