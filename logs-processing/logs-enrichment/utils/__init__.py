import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from common.config import DATA_PATH, LOCK_FILENAME, DBG
from time import sleep 

def wait_for_file_disappearance(filename):
    while os.path.isfile(filename):
        sleep(0.1) # Wait a bit for the lock to be released...

def lock_lockfile(fname, blocking=True):
    if blocking:
        wait_for_file_disappearance(fname)
    # Lock released! Acquire it:
    f = open(fname, "w+")
    f.close()
    return True

def unlock_job(jobname):
    return release_lockfile(DATA_PATH + jobname + "/" + LOCK_FILENAME)

def release_lockfile(fname):
    os.remove(fname)

def lock_job(jobname, blocking=True):
    return lock_lockfile(DATA_PATH + jobname + "/" + LOCK_FILENAME, blocking)

def load_file(fname):
    f = open(fname, 'r')
    res = f.read()
    f.close()
    return res

def write_file(fname, content):
    """
    If the file already exists, it will be overwritten
    """
    f = open(fname, "w+")
    res = f.write(content)
    f.close()
    return res

def printe(s):
    print >> sys.stderr, s

def l(*args):
    if DBG:
        for s in args:
            print s,
        print ""