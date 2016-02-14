#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
# import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def load_repo(client, index):
    client.indices.put_mapping(
        index=index,
        doc_type='web_page',
        body={
          'web_page': {
            'properties': {        
                'hash': {
                  'type': 'string'
                },
                'content': {
                  'type': 'string'
                }
            }
          }
        }
    )

    ok, result = bulk(
        client,
         [
         {
             '_id': 1,
             'hash': '121098210982aeh0293',
             'content': 'this is a joke'
         }
         , {
             '_id': 2,
             'hash': '121098210982aeh0293',
             'content': 'this is a joke 2'
         }
         ],
        index=index,
        doc_type='web_page'
    )


if __name__ == '__main__':
    # get trace logger and set level
    # tracer = logging.getLogger('elasticsearch.trace')
    # tracer.setLevel(logging.INFO)
    # tracer.addHandler(logging.FileHandler('/tmp/es_trace.log'))

    # instantiate es client, connects to localhost:9200 by default
    es = Elasticsearch(host='tdvps.fr.nf', port=9200)

    load_repo(es, "web_crawl")

    # refresh to make the documents available for search
    es.indices.refresh(index='web_crawl')

    # and now we can count the documents
    print(es.count(index='web_crawl')['count'], 'documents in index')
