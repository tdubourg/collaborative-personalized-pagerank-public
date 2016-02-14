#!/usr/bin/python

"""
This script will go through the entire log file and compute for each entry
the total number of clicks it has and also its click entropy.

The script then outputs this information into a CSV file that you can for
instance use in a spreadsheet to plot the distribution of the data.

Executes in about 60s and uses probably > 3300M RAM.

"""


from math import log
from univ_open import univ_open

class LogProcessor(object):
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        """

        /!\ If using options.serp_urls_uniqueness_ and lazy = False, serp_urls returned will be sorted

        """
        # To be c/p-ed example of options
        # try:
        #     self.serp_urls_uniqueness = options['serp_urls_uniqueness']
        # except KeyError:
        #     self.serp_urls_uniqueness = False
        # try:
        #     self.lazy = options['lazy']
        # except KeyError:
        #     self.lazy = True
        # try:
        #     self.return_serp_urls = options['return_serp_urls']
        # except KeyError:
        #     self.return_serp_urls = False
        
        self.entries = {}
        self.clicks = {}
        with univ_open(self.log_filepath, mode='r') as f:
            for line in f:
                line_arr = line.strip().split('\t')
                if len(line_arr) is 5: # This is a clickthrough line
                    user_id, keywords, date, pos, domain = line_arr
                    # try:
                    #      domain = domain[domain.index("//")+2:] # Getting rid of something://
                    # except ValueError: # Was not found, domain is specified without protocol?
                    #      pass
                    # entry = (user_id, date, pos, domain)
                    # try:
                    #     self.entries[keywords].append(entry)
                    # except KeyError:
                    #     self.entries[keywords] = [entry]
                    if keywords not in self.entries:
                    	self.entries[keywords] = {}
                    try:
                        self.entries[keywords][domain] += 1
                    except KeyError:
                        self.entries[keywords][domain] = 1
                    # try:
                    #     self.clicks[keywords] += 1
                    # except KeyError:
                    #     self.clicks[keywords] = 1

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
    l = sorted([(kw, sum(lp.entries[kw].values())) for kw in lp.entries], key=lambda i: i[1], reverse=True)[:k]
    print "Done in", time()-t0
    
    fname = "result.txt" if len(sys.argv) < 4 else sys.argv[3]
    print "Writing result top ", k, "queries into file", fname, "together with their click entropy"
    t0 = time()
    f = open(fname, 'w+')
    # Click entropy as defined in "A large scale evaluation and analysis of Personalized "
    P = lambda p, q: lp.entries[q][p] / float(sum(lp.entries[q].values()))
    click_entropy = lambda q: sum([-P(p, q) * log(P(p, q), 2) for p in lp.entries[q]])
    f.writelines('\n'.join(['"%s",%s,%s' % (_[0].replace('"', '\\"'), _[1], click_entropy(_[0])) for _ in l]))
    f.close()
    print "Done in", time()-t0
    print "Terminating script."
