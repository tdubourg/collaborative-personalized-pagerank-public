#!/usr/bin/python

"""
This script aims at outputing the size of the intersection between the set of 
queries searched and clicked by users and a given set of queries (ie. query string)

ids_only parameter will also allow you to only output the ids (not sorted or anything)
of the users with a non null intersection so that for instance you can use this as a 
filtering criteria (with ./store_users_profiles.py for instance)
"""

class LogProcessor(object):
    MAX_USER_ID = 24969596  # We went through the entire log to find the maximum user id (and added 1)
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        self.users_intersection_size = [0] * self.MAX_USER_ID
        with open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                line = line.strip().split('\t')
                if len(line) is not 5:  # This is not a click log line (it could just be a search log line)
                    continue
                try:
                    user_id = int(line[0])
                    querystr = line[1].strip().lower()
                    if querystr in options['allowed_query_strings']:
                        self.users_intersection_size[user_id] += 1
                except ValueError as e:
                    print "Line number", i, "has invalid user id:", e

CLI_ARGS = ["query_strings_one_per_line", "log_file", "users_intersections_sizes.txt"]
OPT_ARGS = ["ids_only", "select_k_first"]
def main():
    import sys
    from time import time
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    input_path = sys.argv[1].strip()
    log_filepath = sys.argv[2].strip()
    output_path = sys.argv[3].strip()
    ids_only = True if len(sys.argv) >= len(CLI_ARGS)+2 and  sys.argv[len(CLI_ARGS)+1] != "" else False

    if ids_only:
        print "We will output only the ids"

    query_strings = set()
    with open(input_path, 'r') as f:
        for line in f:
            query_strings.add(line.strip().lower())

    print "Loaded", len(query_strings), "allowed query strings."
    
    lp = LogProcessor(log_filepath)
    t0 = time()
    lp.process(allowed_query_strings=query_strings)
    print "Processed in", time() - t0
    
    k = len(lp.users_intersection_size) if len(sys.argv) < len(CLI_ARGS)+3 else int(sys.argv[len(CLI_ARGS)+2])
    print "Sorting by intersection_size and selected the ", k, "first among", len(lp.users_intersection_size)
    t0 = time()
    i = 0
    users_entries = []
    while i < len(lp.users_intersection_size):
        number = lp.users_intersection_size[i]
        if number is not 0:
            users_entries.append((i, number))
        i += 1
    l = sorted(users_entries, key=lambda i: i[1], reverse=True)[:k]
    print "Done in", time()-t0
    
    print "Writing result top ", k, "users into file", output_path, "together with their intersection size"
    t0 = time()
    f = open(output_path, 'w+')
    if ids_only:
        f.writelines('\n'.join(['%s' % _[0] for _ in l if _[1] is not 0]))
    else:
        f.writelines('\n'.join(['%s,%s' % _ for _ in l]))
    f.close()
    print "Done in", time()-t0
    print "Terminating script."

if __name__ == '__main__':
    main()
