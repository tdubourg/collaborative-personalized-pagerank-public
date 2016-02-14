#!/bin/zsh

clear;

basename="/w/weather_crawl/weather_crawl_"
n=0
for i in ${HOME}/cppr/data/web_crawl/*_weather_crawl_seed.lst; do \
n=`expr $n + 1`; \
log_path="${basename}_${n}.log"; \
echo "Launching for seed ${i}, this will be part ${n} and will log to ${log_path}"; \
time scrapy crawl web_crawler \
-a export_path="${basename}_${n}" \
-a urls_fname="${i}" \
-a web_repository_export_path="/w/weather_crawl/" \
> $log_path \
2>&1 &; \
done
