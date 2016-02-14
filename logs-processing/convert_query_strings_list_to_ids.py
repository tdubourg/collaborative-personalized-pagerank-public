#!/usr/bin/python

'''
This script takes as input allowed users and queries to be used for the groups of top-K similar users. It also takes as
input the necessary files containing this information: the querystr -> id mapping, the clicks logs, the clusters...

In addition to that, the MDB host where the clusterings, clicks, etc. are stored is also needed.

The script will load all the necessary information in RAM, parsing again the files in some cases (because it's faster 
than retrieving from MDB) and will then compute the all-pairs similarity between users.

'''

from time import time
from univ_open import univ_open

CLI_ARGS = ['file_to_convert', 'query_strings_to_ids.lst', 'output_path']
def main(stop_after_init=False):
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print 'Usage: %s'  % argv[0], ' '.join(CLI_ARGS)
        print 'Currently missing parameters arguments:', ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    file_to_convert = argv[1].strip()
    mapping_file    = argv[2].strip()
    output_path     = argv[3].strip()

    t_init = time()
    query_strings_to_ids = {}
    with univ_open(mapping_file, 'r') as f:
        i = 0
        for l in f:
            query_strings_to_ids[l.strip().lower()] = i
            i += 1

    with univ_open(output_path, 'w+') as out:
        with univ_open(file_to_convert, 'r') as f:
            out.write('\n'.join([str(query_strings_to_ids[l.strip().lower()]) for l in f]))

    print "Script executed in", time() - t_init, "seconds"

if __name__ == '__main__':
    main()