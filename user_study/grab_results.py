#!/usr/bin/python

from pymongo import MongoClient
import json, pickle
from os import getenv

VPS = getenv('VPS')
dump_filename = 'results_dump_from_mdb.bin'
dump_filename2 = 'results_sessions_dump_from_mdb.json'
dump_filename_completed = 'results_sessions_completed_from_mdb.json'

mdb = MongoClient(host=VPS)

per_session_prefs = [] 

all_unprocessed = list(mdb.user_study.sessions.find())
pickle.dump(all_unprocessed, open(dump_filename, 'w+'))
print "Dumped results in", dump_filename

all_sessions = [json.loads(i['session']) for i in all_unprocessed]
json.dump(all_sessions, open(dump_filename2, 'w+'))
print "Dumped sessions in", dump_filename2

completed_sessions_with_5 = [s for s in all_sessions if s['completed'] is True and len(s['pages']) is 5]

completed_sessions = [s for s in all_sessions if s['completed'] is True]
json.dump(completed_sessions, open(dump_filename_completed, 'w+'))

print "Retrieved", len(completed_sessions_with_5), "completed sessions"

for s in completed_sessions_with_5:
    cppr = sum([1 if res['best'] == 'cppr' else 0 for res in s['pages'].values()])
    std = sum([1 if res['best'] == 'standard' else 0 for res in s['pages'].values()])
    if cppr + std != 5:
        print "Wtf?!?", s; continue;
    print "(cppr, std)=", (cppr, std)
    per_session_prefs.append((cppr, std))

print "\nGlobal averages:"
print "\t%.2f%% preference for CPPR"        % (sum([x[0] for x in per_session_prefs]) / float(len(per_session_prefs))/5.0*100)
print "\t%.2f%% preference for baseline"    % (sum([x[1] for x in per_session_prefs]) / float(len(per_session_prefs))/5.0*100)

for i in xrange(5):
    print "Query", i
    print "\t%.2f%% preference for CPPR"        % (sum([1 if x['pages'][str(i)]['best'] == 'cppr' else 0 for x in completed_sessions_with_5]) / float(len(completed_sessions_with_5))*100)
    print "\t%.2f%% preference for baseline"    % (sum([1 if x['pages'][str(i)]['best'] == 'standard' else 0 for x in completed_sessions_with_5]) / float(len(completed_sessions_with_5))*100)
    
