#!/usr/bin/python
from time import time
from multiprocessing import Pool

def do_func(args_tuple):
    t0 = time()
    func = args_tuple[0]
    res = func(*args_tuple[1:])
    print "Running", func.func_name, "in a bg process took", time()-t0, "returning value of type", type(res)
    return res

def run_in_bg_process(func, args_tu):
    print "run_in_bg_process", func.func_name
    p = Pool(1)
    mapres = p.map_async(do_func, [tuple([func] + list(args_tu))])
    p.close()
    return (p, mapres)

if __name__ == '__main__':
    print "This file has no main()"