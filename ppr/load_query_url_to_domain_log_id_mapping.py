import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../logs-processing")))
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "./logs-processing")))

from univ_open import univ_open

def load_mapping(filepath):
    mapping = {}
    with univ_open(filepath, 'r') as f:
        for line in f:
            queryid, urlid, domainid = map(int, line.strip().split(','))
            mapping[(queryid, urlid)] = domainid
    return mapping