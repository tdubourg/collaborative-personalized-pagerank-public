#!/bin/bash
data=/home/theo/cppr/elastic_search/data_dir

# Note here we use --rm=true so that we relaunch it everytime. This means do not store anything inside the docker!
docker run --rm=true -p 9200:9200 -p 9300:9300 -v "${data}:/data" elasticsearch_cppr /elasticsearch/bin/elasticsearch -f -Des.config=/data/elasticsearch.yml
