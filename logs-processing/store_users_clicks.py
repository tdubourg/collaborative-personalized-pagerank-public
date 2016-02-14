#!/usr/bin/python

"""
This script takes as input the log file and a file containing the ids of the users for which
we want to build and store the profile.

The script expects a MongoDB to run on mongodb_host standard port.

It stores the users clicks as the tuple (user id, query id, url_domain id, number of clicks) inside the database
called "users" and a collection called "clicks".
/!\ RAM usage: >= 2.3G
"""

class LogProcessor(object):
    MAX_USER_ID = 24969596  # We went through the entire log to find the maximum user id (and added 1)
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        # Note: Althought we are not going to use all the indices in this list
        # we are still using a list in order to have fast direct element access
        # in order not to waste memory, though, we initialize everything to None
        # and then only initialize the base dictionary for the elements of the list
        # that are going to be used
        self.user_clicks_number = [None] * self.MAX_USER_ID
        try:
            excluded_qids = options['excluded_qids'] if options['excluded_qids'] is not None else set()
        except KeyError:
            excluded_qids = set()

        for _ in options['allowed_user_ids']:
            self.user_clicks_number[_] = {'_id': _}

        with univ_open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if i % 500000 is 0:
                    print "Currently at line", i
                line = line.strip().split('\t')
                if len(line) is not 5:  # This is not a click log line (it could just be a search log line)
                    continue
                try:
                    user_id = int(line[0])
                    queryid = int(line[1].strip())
                    if queryid in excluded_qids:
                        continue
                    url_domain_id = int(line[4].strip())
                    
                    if user_id in options['allowed_user_ids']:
                        self.user_clicks_number[user_id][queryid][url_domain_id] = \
                                1 + self.user_clicks_number[user_id] \
                                .setdefault(queryid, {url_domain_id: 0}) \
                                .setdefault(url_domain_id, 0)
                except ValueError as err:
                    print "Line number", i, "has invalid user id:", err
                except KeyError as err:
                    print "KeyError: ", err
                    print user_id, queryid, url_domain_id
                    exit()

def insert_sublist(mdb, sublist):
    # Not: here we only keep the elements of the list that are not None
    # as the ones that are None are elements filtered out by the allowed_users_ids
    values = [ \
        {'uid': u['_id'], 'qid': qid, 'urlid': urlid, 'n': n} \
         for u in sublist if u is not None \
         for qid, urls in u.items() if qid != '_id' \
         for urlid, n in urls.items() \
    ]
    if not values:
        return
    try:
        mdb.insert(values)
    except Exception as err:
        print type(err), err
        print "Something went wrong with:"
        import json
        json.dumps(values, indent=4, separators=(',', ': '))

from time import time
def process_logfile(log_filepath, allowed_user_ids, excluded_qids=None):
    lp = LogProcessor(log_filepath)
    t0 = time()
    lp.process(allowed_user_ids=allowed_user_ids, excluded_qids=excluded_qids)
    print "Processed in", time() - t0
    return lp

from univ_open import univ_open

CLI_ARGS = ["users_ids_filter", "log_file.converted.converted", "mongodb_host"]
OPT_ARGS = []
def main():
    import sys
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    # Run that immediately so that we crash on the stop if we cannot connect to the DB anyway
    from pymongo import MongoClient
    mdb_host = sys.argv[3].strip()
    mdb_conn = MongoClient(host=mdb_host)
    mdb = mdb_conn.users.clicks

    allowed_user_filepath   = sys.argv[1].strip()
    log_filepath            = sys.argv[2].strip()

    allowed_user_ids = set()
    with univ_open(allowed_user_filepath, 'r') as f:
        for line in f:
            allowed_user_ids.add(int(line.strip()))

    print "Loaded", len(allowed_user_ids), "allowed user ids."
    
    lp = process_logfile(log_filepath, allowed_user_ids)

    # Note that we drop the former data only now so that if something goes wrong during processing at least you still
    # have the former data
    print "Dropping previous DB"
    try:
        mdb.drop()
        mdb = mdb_conn.users.clicks
    except Exception as err:
        print type(err), err
    
    print "Dumping everything into MongoDB"
    t0 = time()
    batch_size = 200000
    for i in xrange(batch_size, len(lp.user_clicks_number), batch_size):
        start = i-batch_size
        end = i
        print "Batch", start, end
        insert_sublist(mdb, lp.user_clicks_number[start:end])
    
    # if len(lp.user_clicks_number) was not a multiple of batch_size, let us execute the last batch:
    if i is not len(lp.user_clicks_number)-1:
        print "Last batch..."
        insert_sublist(mdb, lp.user_clicks_number[i:])

    print "Creating indexes..."
    mdb.ensure_index([('uid', 1)])
    mdb.ensure_index([('qid', 1)])
    mdb.ensure_index([('uid', 1), ('qid', 1)])

    print "Closing MDB connection"
    mdb_conn.close()
    print "Done in", time()-t0
    print "Terminating script."

if __name__ == '__main__':
    main()