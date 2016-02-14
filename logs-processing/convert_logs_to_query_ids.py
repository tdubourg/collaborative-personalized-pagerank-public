#!/usr/bin/python

"""
Input: AOL logs and query_stings -> ids mapping file (one query string by line)
Output: Same AOL logs, but with ids in place of the query string
Beware: Uses ~2.1GB of RAM
"""


from gzip import open as gzopen
import sys

if len(sys.argv) < 3:
    print "Usage:", sys.argv[0], "input_logs query_strings_to_ids_mapping.lst.gz output_path.gz"
    sys.exit()

log_filepath =  sys.argv[1].strip()
qstr_ids_path = sys.argv[2].strip()
output_path = sys.argv[3].strip()

# If True, the resulting output will be a valid JSON list
# Else, it will just be one line = one item list, ordered by index (no huge difference!)
JSON_OUTPUT = False

# Size of IO batch writes
BATCH_SIZE = 10000

from time import time
batch_str = ''
items_in_queue = 0
t0 = time()
with gzopen(output_path, 'wb', 6) as outfile:
    print "Loading qstr->ids mapping... (brace yourself, RAM!)"
    t0 = time()
    with gzopen(qstr_ids_path, 'rb') as idmapfile:
        qstr_ids = {}
        i = 0
        for line in idmapfile:
            qstr_ids[line.strip()] = str(i)
            i += 1
    print "Done in", time()-t0

    print "Starting logs parsing + I/O to output file", output_path
    t0 = time()
    with open(log_filepath, mode='r') as f:
        for line in f:
            line = line.strip().split('\t')
            if  len(line) is not 5 \
                and len(line) is not 3:  # This is neither a clickthrough line nor a search query line
                continue
            # Replace the keywords by the ids
            try:
                line[1] = qstr_ids[line[1].strip().lower()]
            except KeyError as e:
                print "KeyError, the following query string was not found:", e
            # And put everything back together and push that to the batch queue
            batch_str += '\t'.join(line) + "\n"
            items_in_queue += 1
            if items_in_queue is BATCH_SIZE:
                outfile.write(batch_str)
                batch_str = ''
        # Write the remainder of data to be written, if there is some
        if batch_str != '':
            outfile.write(batch_str)
    print "Done in", time()-t0
