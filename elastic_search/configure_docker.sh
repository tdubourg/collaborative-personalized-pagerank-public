#!/bin/bash
echo "This script will get you a shell inside the docker so that you can configure plugins for instance."
echo "You will have to commit your docker to the image afterwards so that changes are registered for the next"
echo "elasticsearch docker run"

data=/home/theo/cppr/elastic_search/data_dir

# Note here we use --rm=true so that we relaunch it everytime. This means do not store anything inside the docker!
docker run -p 9200:9200 -p 9300:9300 -v "${data}:/data" -i -t elasticsearch_cppr /bin/bash
