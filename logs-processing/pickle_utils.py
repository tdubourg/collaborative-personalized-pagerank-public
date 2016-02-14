#!/usr/bin/python

from gzip import open as gzopen
from pickle import dump as pdump
from numpy import array
from time import time
from multiproc_utils import run_in_bg_process
from univ_open import univ_open

no_answers = ('n', 'no')
NO_PICKLE = False

def pickle_ask(already_pickled, pickle_path, data, dump_f=pdump):
    if NO_PICKLE:
        return
    if already_pickled is False and raw_input("Pickle result to disk? [Y/n]").lower() not in no_answers:
        run_in_bg_process(pickle_open_and_write, (pickle_path, data, dump_f))

def pickle_open_and_write(pickle_path, data, dump_f=pdump):
    t0 = time()
    with univ_open(pickle_path, 'wb+') as f:
        dump_f(data, f)
    print "Done ", time()-t0

def pickle_list(data, f):
    f.write(' '.join([str(_) for _ in data]))

def pickle_list_with_newlines(data, f):
    f.write('\n'.join([str(_) for _ in data]))

def load_pickled_list(f):
    li = []
    for line in f:
        li.extend([int(_) for _ in line.strip().split()])
    return li

def picke_dict(data, f):
    # Not doing everything in one write because the huge generated string would likely OOM
    newline = ''
    for qid, cluster_vector in data.items():
        f.write("%s%s:%s" % (newline, qid, ' '.join([str(_) for _ in cluster_vector])))
        newline = '\n'

def load_pickled_dict_to_np_arrays(f, pre_initialized_dict=dict()):
    import gc
    gc.disable()
    di = pre_initialized_dict
    for line in f:
        line = line.strip().split(":")
        di[int(line[0])] = array([float(_) for _ in line[1].strip().split(" ")])
    gc.enable()
    return di

if __name__ == '__main__':
    print "This file has no main()"