#!/bin/zsh

clear;

basename="${HOME}/cppr/data/web_crawl/run_with_urls_seed_from_50_serps_of_11_manually_selected_urls_part_third_run"
n=0
for i in ${HOME}/cppr/data/*_web_crawl_urls_seed.lst; do \
n=`expr $n + 1`; \
log_path="${basename}_${n}.log"; \
echo "Launching for seed ${i}, this will be part ${n} and will log to ${log_path}"; \
time scrapy crawl web_crawler \
-a export_path="${basename}_${n}" \
-a urls_fname="${i}" \
-a web_repository_export_path="${HOME}/cppr/web_pages_2" \
> $log_path \
2>&1 &; \
done
