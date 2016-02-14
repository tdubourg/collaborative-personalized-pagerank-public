#!/bin/bash

clear;

time ./generate_store_serps.py \
/h/cppr/data/fairy_wings_triplet.lst \
$VPS \
$VPS \
/h/cppr/data/web_crawl/graph_graphtool_with_dangling.graphml.xml.gz \
/h/cppr/data/2014_serps_urlid_to_logs_domain_ids.dict.custom.format.lst
