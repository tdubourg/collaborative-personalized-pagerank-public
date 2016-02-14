#!/usr/bin/python

"""
	THIS FILE IS DEPRECATED. SEE user_similarity_in_ram.py FOR THE UPDATED VERSION OF THE GRAPH SCORING
    This module provides the necessary methods to compute collaboratively defined personalization scores of the web 
    graph.
"""

from math import log
from numpy import array, inner
from numpy.linalg import norm
from time import time
import user_similarity as us

mdb = None
DBG = False
PERF_DBG = False

def init_mdb(mdb_conn):
    global mdb
    mdb = mdb_conn
    us.init_mdb(mdb_conn)

def score(user, url_id):
	# Preload 
	return \
		sum([us.sim(user, u_other) * us.clicks_page(q, p, u_other) for u_other in us.sim_users(user)]) \
		/ \
		sum([us.clicks(q, u_other) for u_other in us.sim_users(user)])

def test():
	pass

if __name__ == '__main__':
    test()