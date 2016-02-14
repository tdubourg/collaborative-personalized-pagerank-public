#!/usr/bin/python

"""
This script will go through the entire log file and compute for each entry
the total number of clicks it has and also its click entropy.

The script then outputs this information into a CSV file that you can for
instance use in a spreadsheet to plot the distribution of the data.

Executes in about 60s and uses probably > 2500M RAM.

"""


from univ_open import univ_open

class LogProcessor(object):
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        self.clicks = [0] * 60000000
        allowed_query = options['allowed_query']
        with univ_open(self.log_filepath, mode='r') as f:
            for line in f:
                line_arr = line.strip().split('\t')
                if len(line_arr) is 5: # This is a clickthrough line
                    user_id = int(line_arr[0])
                    queryid = int(line_arr[1].strip())
                    if queryid != allowed_query:
                        continue
                    self.clicks[user_id] += 1

if __name__ == '__main__':
    import sys
    from time import time
    
    lp = LogProcessor(sys.argv[1])
    t0 = time()
    lp.process(allowed_query=int(sys.argv[2]))
    print "Processed in", time() - t0
    
    k = 1000
    print "Sorting by clicks and selected the ", k, "first"
    t0 = time()
    l = sorted([(i, lp.clicks[i]) for i in xrange(len(lp.clicks)) if lp.clicks[i] is not 0], key=lambda i: i[1], reverse=True)[:k]
    print "Done in", time()-t0
    
    fname = "result.txt" if len(sys.argv) < 4 else sys.argv[3]
    print "Writing result top ", k, "queries into file", fname, "together with their click entropy"
    t0 = time()
    with open(fname, 'w+') as f:
        f.writelines("%d,%d\n" % i for i in l)
    print "Done in", time()-t0
    print "Terminating script."
