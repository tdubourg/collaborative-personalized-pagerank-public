#!/bin/bash

# use the first argument as $k or default value is 100
k=${1:-100}

clear && time python ./select_top_k_queries.py $k $VPS $HOME/cppr/data/ids_of_top_urls.lst $HOME/cppr/data/users_who_queried_top_urls.lst $HOME/cppr/data/query_str_to_ids.lst.gz "top_${k}_queries_with_non_null_clustering.lst.gz"
