#!/usr/bin/python

"""

/!\ /!\ THIS SCRIPT IS DEPRECATED (though it still works) BY store_users_clicks.py /!\ /!\

This script takes as input the log file and a file containing the ids of the users for which
we want to build and store the profile.

The script expects a MongoDB to run on mongodb_host standard port.

It stores the users clicks number indexed by query id inside the database called "users" and 
a collection called "clicks_per_query".

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
                    queryid = line[1].strip()
                    if user_id in options['allowed_user_ids']:
                        self.user_clicks_number[user_id][queryid] = 1 + self.user_clicks_number[user_id].setdefault(queryid, 0)
                except ValueError as e:
                    print "Line number", i, "has invalid user id:", e

def univ_open(file_path, mode='r'):
    # If the file ends with ".gz" then open it through GZip
    if file_path.split('.')[-1].lower() == 'gz':
        from gzip import open as gzopen
        return gzopen(file_path, mode)
    else:
        return open(file_path, mode)
    
CLI_ARGS = ["users_ids_filter", "log_file", "mongodb_host"]
OPT_ARGS = []
def main():
    import sys
    from time import time
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    # Run that immediately so that we crash on the stop if we cannot connect to the DB anyway
    from pymongo import MongoClient
    mdb_host = sys.argv[3].strip()
    mdb = MongoClient(host=mdb_host).users.clicks_per_query

    input_path = sys.argv[1].strip()
    log_filepath = sys.argv[2].strip()

    allowed_user_ids = set()
    with univ_open(input_path, 'r') as f:
        for line in f:
            allowed_user_ids.add(int(line.strip()))

    print "Loaded", len(allowed_user_ids), "allowed user ids."
    
    lp = LogProcessor(log_filepath)
    t0 = time()
    lp.process(allowed_user_ids=allowed_user_ids)
    print "Processed in", time() - t0

    print "Dropping previous DB"
    mdb.drop()
    
    print "Dumping everything into MongoDB"
    t0 = time()
    batch_size = 200000
    for i in xrange(batch_size, len(lp.user_clicks_number), batch_size):
        start = i-batch_size
        end = i
        print "Batch", start, end
        # Not: here we only keep the elements of the list that are not None
        # as the ones that are None are elements filtered out by the allowed_users_ids
        mdb.insert([_ for _ in lp.user_clicks_number[start:end] if _ is not None])
    # len(lp.user_clicks_number) was not a multiple of batch_size, let us execute the last batch:
    if i is not len(lp.user_clicks_number)-1:
        print "Last batch..."
        mdb.insert(lp.user_clicks_number[i:])
    print "Done in", time()-t0
    print "Terminating script."

if __name__ == '__main__':
    main()