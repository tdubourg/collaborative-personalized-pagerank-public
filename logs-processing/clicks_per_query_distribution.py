#!/usr/bin/python

"""
This script takes as input the log file (converted, converted) and a path to the output

It output a CSV file with the number of clicks for every query.

This script deprecates the users_statistics.py scripts that did not output 0 for users who were present in the logs
but had no clicks and was also not very verbose on how to use it (CLI args no specified...)

This is to be used in combination with users_clicks_transform_for_spreadsheet_visualization.py to aggregate the data
"""

class LogProcessor(object):
    MAX_USER_ID = 24969596  # We went through the entire log to find the maximum user id (and added 1)
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        # Note: Althought we are not going to use all the indices in this list
        # we are still using a list in order to have fast direct element access
        # in order not to waste memory, though, we initialize everything to None
        # and then only initialize at 0 the users that we encounter in the logs
        self.users_queries_clicks_number = [None] * self.MAX_USER_ID
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
                    if queryid in excluded_qids:
                        continue
                except ValueError as err:
                    print "Line number", i, "has invalid user id:", err
                except KeyError as err:
                    print "KeyError: ", err
                    url_domain_id = int(line[4].strip())
                    print user_id, queryid, url_domain_id
                    exit()
                    
                if self.users_queries_clicks_number[user_id] is None:
                    self.users_queries_clicks_number[user_id] = {queryid: 0}

                if len(line) is 5:  # This is a click log line (it could just be a search log line)
                    self.users_queries_clicks_number[user_id][queryid] = 1 + self.users_queries_clicks_number[user_id].setdefault(queryid, 0)

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
    from numpy import mean
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

    print "Aggregation..."
    NUMBER_OF_DIGITS_PER_INTERVAL = -0.5
    QUANTIZATION_FACTOR = 10 ** NUMBER_OF_DIGITS_PER_INTERVAL
    MAX_AVG_OF_CLICKS_PER_Q = int(10000 * QUANTIZATION_FACTOR)
    n_of_users_with_avg = [0] * MAX_AVG_OF_CLICKS_PER_Q
    averages = []
    for user_queries_clicks in lp.users_queries_clicks_number:
        if user_queries_clicks is None:
            continue
        avg = mean(user_queries_clicks.values())
        averages.append(avg)
        avg = int(avg * QUANTIZATION_FACTOR)  # quantization of avg values / grouping by intervals
        n_of_users_with_avg[avg] += 1

    print "Global average of number of clicks per query (avg of the avgs): %f" % (sum(averages)/float(len(averages)))
    
    print "Outputting result to", output_path, "..."
    with open(output_path, 'w+') as out:
        out.write("AvgNOfClicks,NofUserssWithThisAvgNOfClicks\n")
        out.write('\n'.join(
            (
                "%.2f-%.2f,%d" % (i/float(QUANTIZATION_FACTOR), (i+1)/float(QUANTIZATION_FACTOR), n_of_users_with_avg[i]) 
                for i in xrange(MAX_AVG_OF_CLICKS_PER_Q) if n_of_users_with_avg[i] != 0
            )
        ))
    print "File written."


    print "Done in", time() - t_init
    print "Terminating script."

if __name__ == '__main__':
    main()