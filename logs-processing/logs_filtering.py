#!/usr/bin/python

"""
This file takes as input the AOL logs and a file containing the keywords of requests to filter.
It will write to the outpout_path all the lines of the logs that match the given keywords
"""

class LogFilter(object):
    """Filters logs"""
    def __init__(self, log_filepath, output_path):
        super(LogFilter, self).__init__()
        self.log_filepath = log_filepath
        self.output_path = output_path
    
    def filter(self, kw_filter):
        with open(self.log_filepath, mode='r') as f:
            with open(self.output_path, mode='w+') as out:
                for line in f:
                    line_arr = line.strip().split('\t')
                    if len(line_arr) is 5: # This is a clickthrough line
                        user_id, keywords, date, pos, domain = line_arr
                        if keywords.strip() in kw_filter:
                            out.write(line)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print "Usage: ./logs_filtering.py log_file kw_to_filter [output_path]"
        sys.exit()
    outpath = "filtered_log.txt" if len(sys.argv) < 4 else sys.argv[3]
    lf = LogFilter(sys.argv[1], outpath)
    with open(sys.argv[2], mode='r') as f_kw:
        kw_filter = set()
        for l in f_kw:
            kw_filter.add(l.strip())
    lf.filter(kw_filter)