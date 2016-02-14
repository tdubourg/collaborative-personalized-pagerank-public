#!/usr/bin/python

"""
This script takes as input the log file (converted, converted) and a path to the output

It output a CSV file with the number of clicks for every query.

This script deprecates the users_statistics.py scripts that did not output 0 for users who were present in the logs
but had no clicks and was also not very verbose on how to use it (CLI args no specified...)

This is to be used in combination with users_clicks_transform_for_spreadsheet_visualization.py to aggregate the data
"""

class LogProcessor(object):
    MAX_QUERY_ID = 24969596  # We went through the entire log to find the maximum user id (and added 1)
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        # Note: Althought we are not going to use all the indices in this list
        # we are still using a list in order to have fast direct element access
        # in order not to waste memory, though, we initialize everything to None
        # and then only initialize at 0 the users that we encounter in the logs
        self.query_clicks_number = [None] * self.MAX_QUERY_ID
        try:
            excluded_qids = options['excluded_qids'] if options['excluded_qids'] is not None else set()
        except KeyError:
            excluded_qids = set()

        with univ_open(self.log_filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if i % 500000 is 0:
                    print "Currently at line", i
                line = line.strip().split('\t')
                try:
                    user_id = int(line[0])
                    queryid = int(line[1].strip())
                    url_domain_id = int(line[4].strip())
                    if queryid in excluded_qids:
                        continue
                except ValueError as err:
                    print "Line number", i, "has invalid user id:", err
                except KeyError as err:
                    print "KeyError: ", err
                    print user_id, queryid, url_domain_id
                    exit()
                    
                if self.query_clicks_number[queryid] is None:
                    self.query_clicks_number[queryid] = 0

                if len(line) is 5:  # This is a click log line (it could just be a search log line)
                    self.query_clicks_number[queryid] += 1

from time import time
def process_logfile(log_filepath, excluded_qids=None):
    lp = LogProcessor(log_filepath)
    t0 = time()
    lp.process(excluded_qids=excluded_qids)
    print "Processed in", time() - t0
    return lp

from univ_open import univ_open

CLI_ARGS = ["log_file.converted.converted", "output_path"]
OPT_ARGS = []
def main():
    import sys
    from sys import argv
    t_init = time()

    argc = len(sys.argv)

    if argc < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    logfile     = argv[1]
    output_path = argv[2]

    lp = LogProcessor(logfile)
    t0 = time()
    print "Starting process..."
    lp.process()
    print "Done in", time() - t0

    print "Outputting result to", output_path, "..."
    with open(output_path, 'w+') as out:
        out.write("QueryID,NofClicks\n")
        out.write('\n'.join(("%d,%d" % (i, lp.query_clicks_number[i]) for i in xrange(lp.MAX_QUERY_ID) if lp.query_clicks_number[i] is not None)))
    print "File written."
    print "Now computing aggregated version, aggregated by number of clicks"
    MAX_N_OF_CLICKS = 1000000
    n_of_clicks = [0] * MAX_N_OF_CLICKS
    for query_n_of_c in lp.query_clicks_number:
        if query_n_of_c is None:
            continue
        n_of_clicks[query_n_of_c] += 1
    output_path_aggregated = output_path[:output_path.index('.')] + "_aggregated" + output_path[output_path.index('.'):]
    with open(output_path_aggregated, 'w+') as out:
        out.write("NOfClicks,QueriesWithThisNOfClicks\n")
        out.write('\n'.join(("%d,%d" % (i, n_of_clicks[i]) for i in xrange(MAX_N_OF_CLICKS) if n_of_clicks[i] != 0)))


    print "Done in", time() - t_init
    print "Terminating script."

if __name__ == '__main__':
    main()