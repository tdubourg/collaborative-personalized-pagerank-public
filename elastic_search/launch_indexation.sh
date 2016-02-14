#!/bin/zsh

# Note: with a batch size of 300, it should take about ~150s to arrive to a batch
# and we have 3 processed running
# so if we add a starting delay of 50 seconds between each
# then it should do the following:
# proc1: .... 150s passed=commit................300s passed=commit
# proc2: ............. 200s passed=commit.................350s passed=commit
# proc3: ...................... 250s passed=commit......................400s passed=commit
# and thus there is always more or less 50 secondes between commits, they are not too close to each other
# the delay has to be thought depending on the average speed pages/secondes and the 
# size of the batch, else it could be useless, as even with a delay, workers could end up committing
# together, just with different commit "number" (like 1st commit, 2nd commit...)

delay=16  # seconds
num_of_processes=3
size_of_file=18000000
batch=`expr $size_of_file / $num_of_processes`

for i in `seq 0 \`expr $num_of_processes - 1\``; do \
    echo `date`; \
    start=`expr $i \* $batch`; \
    end=`expr $start + $batch`; \
    logfile="/h/cppr/data/elastic_search_indexation_process_retried_again_${i}.log"; \
    time python elastic_search_import_crawl_data.py \
    /h/cppr/data/web_crawl/ids_to_urls.lst.gz \
    /h/cppr/web_pages_2/ \
    $VPS \
    100 \
    no_html \
    $start \
    $end > $logfile 2>&1 &; \
    echo "Logging to... ${logfile}"; \
    echo "Adding a delay between workers start, so that batches are not sent all together to elasticsearch"; \
    sleep $delay; \
done

