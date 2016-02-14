#!/usr/bin/python
"""
This script will go through the entire log file and compute for each user
the total number of clicks it has. (original goal of the script was also
to check whether AnonID indeed looked like a user id or more like a session
id (based on how many clicks by AnonID))

The script then outputs this information into a CSV file that you can for
instance use in a spreadsheet to plot the distribution of the data.
"""

from univ_open import univ_open

class LogProcessor(object):
    MAX_USER_ID = 24969596  # We went through the entire log to find the maximum user id (and added 1)
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        self.users_number_of_entries = [0] * self.MAX_USER_ID
        with univ_open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if line.count("\t") is not 4:  # This is not a click log line (it could just be a search log line)
                    continue
                try:
                    user_id = int(line[:line.index("\t")])
                    self.users_number_of_entries[user_id] += 1
                except ValueError as e:
                    print "Line number", i, "has invalid user id:", e

if __name__ == '__main__':
    import sys
    from time import time
    
    lp = LogProcessor(sys.argv[1])
    t0 = time()
    lp.process()
    print "Processed in", time() - t0
    
    k = 1000 if len(sys.argv) < 3 else int(sys.argv[2])
    print "Sorting by clicks and selected the ", k, "first"
    t0 = time()
    i = 0
    users_entries = []
    while i < len(lp.users_number_of_entries):
        number = lp.users_number_of_entries[i]
        if number is not 0:
            users_entries.append((i, number))
        i += 1
    l = sorted(users_entries, key=lambda i: i[1], reverse=True)[:k]
    print "Done in", time()-t0
    
    fname = "result_users.txt" if len(sys.argv) < 4 else sys.argv[3]
    print "Writing result top ", k, "users into file", fname, "together with their numbers of clicks"
    t0 = time()
    f = open(fname, 'w+')
    f.writelines('\n'.join(['%s,%s' % _ for _ in l]))
    f.close()
    print "Done in", time()-t0
    print "Terminating script."