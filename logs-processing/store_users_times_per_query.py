#!/usr/bin/python

"""
This script takes as input the log file and a file containing the ids of the users for which
we want to build and store the profile.

The script expects a MongoDB to run on mongodb_host standard port.

It stores the number of times users have issued each query inside the database called "users" and 
a collection called "queries".

"""

from datetime import datetime
from time import mktime

# This is the minimum interval between two log lines about the same query to consider that the user issued twice the 
# query and not simply got back to the search result and clicked a new query
SAME_QUERY_TIME_INTERVAL = 600  # In seconds # TODO: Check what the right time would be in the litterature?

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
        self.user_queries_number = [None] * self.MAX_USER_ID
        for _ in options['allowed_user_ids']:
            self.user_queries_number[_] = {'_id': _}

        try:
            excluded_qids = options['excluded_qids'] if options['excluded_qids'] is not None else set()
        except KeyError:
            excluded_qids = set()

        last_queryid = -1
        with univ_open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if i % 500000 is 0:
                    print "Currently at line", i
                line = line.strip().split('\t')
                if len(line) is not 5\
                    and len(line) is not 3:  # This is neither a click log line nor it could just be a search log line
                    # Note that if there is no clicks, a "search log line" will appear in the logs
                    # but if there were some clicks, this line will not appear and a "clickthrough log line" (or 
                    # several ones) will appear(s). As a consequence, We cannot simply count the number of "search" type
                    # lines in order to know how many times the user issued the query
                    # we also have to consider the click lines
                    continue
                try:
                    user_id = int(line[0])
                    
                    if user_id in options['allowed_user_ids']:
                        queryid = int(line[1].strip())

                        if queryid in excluded_qids:
                            continue

                        curr_time = mktime(datetime.strptime(line[2].strip(), '%Y-%m-%d %H:%M:%S').timetuple())

                        # When was it the last time that we saw a log line about this query?
                        # Note: clickthrough log lines for the same query are contiguous
                        last_time = self.user_queries_number[user_id] \
                                .setdefault(queryid, (0, float('-inf')))[1]
                        # Has there be enough time since this last time for us to consider that the user
                        # is really re-issuing the query and not just getting back to the SERP and clicking a new 
                        # link
                        # we will also consider that if the user issued another query in between, and then went back
                        # to this query it means it did re-issue this query
                        # note that as the click log lines are groupped by user it seems, we just compare to the last
                        # query id without having a user-specific last query id
                        if abs(curr_time - last_time) >= SAME_QUERY_TIME_INTERVAL or last_queryid is not queryid:
                            self.user_queries_number[user_id][queryid] = (
                                1 + self.user_queries_number[user_id][queryid][0],
                                curr_time
                            )
                        else:
                            # We still update the last time this guy queried this query in order to avoid
                            # someone getting back every 5 seconds to the page 20 times being detected as re-issueing the
                            # query just because the last time we registered was only the first time this guy went on the
                            # page
                            self.user_queries_number[user_id][queryid] = (
                                    # Please note here there is no +1, of course
                                    self.user_queries_number[user_id][queryid][0],
                                    curr_time
                            )

                        # And in any case, we also update the last query that we saw... of course
                        last_queryid = queryid
                except ValueError as err:
                    print "Line number", i, "has invalid user id:", err
                except KeyError as err:
                    print "KeyError: ", err
                    print user_id, queryid
                    exit()

def insert_sublist(mdb, sublist):
    # Not: here we only keep the elements of the list that are not None
    # as the ones that are None are elements filtered out by the allowed_users_ids
    values = [ \
        {'uid': u['_id'], 'qid': qid, 'n': n_t_tuple[0]} \
         for u in sublist if u is not None \
         for qid, n_t_tuple in u.items() if qid != '_id'
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
    mdb = mdb_conn.users.queries

    input_path = sys.argv[1].strip()
    log_filepath = sys.argv[2].strip()

    allowed_user_ids = set()
    with univ_open(input_path, 'r') as f:
        for line in f:
            allowed_user_ids.add(int(line.strip()))

    print "Loaded", len(allowed_user_ids), "allowed user ids."
    lp = process_logfile(log_filepath, allowed_user_ids)

    # Note that we drop the former data only now so that if something goes wrong during processing at least you still
    # have the former data
    print "Dropping previous DB"
    try:
        mdb.drop()
        mdb = mdb_conn.users.queries
    except Exception as err:
        print type(err), err

    print "Dumping everything into MongoDB"
    t0 = time()
    batch_size = 200000
    for i in xrange(batch_size, len(lp.user_queries_number), batch_size):
        start = i-batch_size
        end = i
        print "Batch", start, end
        insert_sublist(mdb, lp.user_queries_number[start:end])
    
    # if len(lp.user_queries_number) was not a multiple of batch_size, let us execute the last batch:
    if i is not len(lp.user_queries_number)-1:
        print "Last batch..."
        insert_sublist(mdb, lp.user_queries_number[i:])

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