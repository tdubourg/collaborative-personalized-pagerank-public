#!/bin/bash

echo "/!\\/!\\ Do not forget to run fix_web_crawl_files.sh before running this script, the files need to have their JSON \
syntax fixed."

clear;

fname_base="run_with_urls_seed_from_50_serps_of_11_manually_selected_urls_part_second_run"
part_pattern="_%s"
folder="${HOME}/cppr/data/web_crawl/"
num_parts=4
tmp_folder="${HOME}/tmp"

./process_crawl_chain.py $folder $fname_base $num_parts $part_pattern $tmp_folder