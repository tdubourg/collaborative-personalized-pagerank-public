#!/usr/bin/python

from store_similar_users import compute_everything
from univ_open import univ_open

def top_k_queries(k, host, queries_filter_file, allowed_users_file, ids_mapping_file):
    queries_ids = compute_everything(host, queries_filter_file, allowed_users_file, k)['q_list']
    queries_strings_indexed_by_id = [l.strip() for l in univ_open(ids_mapping_file)]
    queries_strings = [queries_strings_indexed_by_id[i] for i in queries_ids]
    return queries_strings

CLI_ARGS = [
    'top_k_queries',
    'mongodb_host',
    'filter_queries_file',
    'allowed_users_file',
    'queries_ids_to_strings_mapping.lst.gz',
    'output_path.lst.gz'
]

def main():
    from sys import argv
    from time import time
    from pickle_utils import pickle_open_and_write as save, pickle_list_with_newlines as save_list

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print "Usage: %s"  % argv[0], ' '.join(CLI_ARGS)
        print "Currently missing arguments:", ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    global mdb_host
    k                        = int(argv[1].strip())
    mdb_host                 = argv[2].strip()
    filter_queries_file      = argv[3].strip()
    allowed_users_file       = argv[4].strip()
    queries_ids_mapping_file = argv[5].strip()
    output_path              = argv[6].strip()

    t_init = time()
    
    result = top_k_queries(k, mdb_host, filter_queries_file, allowed_users_file, queries_ids_mapping_file)
    print "Done in", time()-t_init
    
    t0 = time()
    save(output_path, result, save_list)
    print "Done in", time()-t0

    print "Script run in", time()-t_init


if __name__ == '__main__':
    main()