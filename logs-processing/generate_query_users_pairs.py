#!/usr/bin/python

"""

    This file is for temporary test purpose only: It takes the first user that queried a given query
    in order to generate the query_user pairs file.

"""


from pymongo import MongoClient

mdb = MongoClient(host='tdvps.fr.nf')

qs = [int(x.strip()) for x in open('/home/troll/cppr/data/manually_selected_10_queries.converted.lst', 'r')]
results = []

for q in qs:
    results.append((q, mdb.users.clicks.find_one({
      'qid': q
    })['uid']))

with open('/home/troll/cppr/data/manually_selected_10_query_user_pairs.converted.lst', 'w+') as out:
    out.write('\n'.join(["%s %s" % _ for _ in results]))
