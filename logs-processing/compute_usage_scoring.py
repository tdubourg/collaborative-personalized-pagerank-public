#!/usr/bin/python

"""
    This file will compute the _usage_scoring_ for a given set of pairs (user, query).
    Uses probably >4G of RAM
"""

from compute_top_similar_users_in_ram import main as similar_users
from univ_open import univ_open
from multiproc_utils import run_in_bg_process
import users_similarity_in_ram as us
from pymongo import MongoClient

from load_similar_users import load_sim_users, load_set_of_similar_users

CLI_ARGS = [
    'pairs_users_queries_file_path',
    'mongodb_host',
    'filter_queries_file',
    'allowed_users_file_including_targeted_and_similar_users_or_more',
    'log_filepath',
    "clusters_file",
    "queries_to_ids.lst"
]

def main(argv, no_compute=False, store_results=True):
    import sys
    # from sys import argv
    from time import time

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print "Usage: %s"  % argv[0], ' '.join(CLI_ARGS)
        print "Currently missing parameters arguments:", ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    pairs_path  = argv[1].strip()
    mdb_host    = argv[2].strip()

    t_init = time()

    with univ_open(pairs_path, 'r') as f:
        pairs = [tuple([int(_) for _ in l.strip().split(" ")]) for l in f]

    targeted_users = [p[1] for p in pairs]

    sim_users = load_sim_users(mdb_host, targeted_users)
    all_allowed_users = load_set_of_similar_users(mdb_host, targeted_users) | set(targeted_users)

    # This will load everything needed to compute sim() function in-ram
    similar_users(argv[1:], True, preset_set_of_users=all_allowed_users)

    print "We loaded", len(us.users_clicks_list_indexed_by_uid), "users' clicks information"

    # Init the sim_users array of the user_similiraty module
    us.init_sim_users(sim_users)

    if no_compute:
        return

    # We're ready to compute!

    for q, u in pairs:
        # Note: The collaborative score is not computed on the user's own clicked pages
        # but using the clicks of the users similar to him
        # so we have to compute scores for all pages clicked BY ITS SIMILAR USERS
        for sim, u_sim in sim_users[u]:
            try:
                pages = us.users_clicks_list_indexed_by_uid[u_sim][q].keys()
            except KeyError as err:
                key = int(err.message)
                if key == q and key != u_sim:
                    # Well, this similar user just does not have queried this query...
                    continue
                print "For u_sim, q", u_sim, q
                print "KeyError with value=", err
                continue
            if pages is None:
                print "?!?! The user", u_sim, "user similar to", u, "has no pages information."
            else:
                print "User", u_sim, "user similar to", u, "has", len(pages), "pages informations for query", q
                for page in pages:
                    # try:
                    sys.stdout.write("score(u=%s, q=%s, p=%s)=" % (u, q, page))
                    sys.stdout.flush()
                    sys.stdout.write("%.5e\n" % us.score(q, page, u))
                    # except KeyError as err:
                    #     print "The KeyError is:", err
                    #     print "For some reason, the user", u, "probably is not in the sim_users cache"
                    #     print "Dump of the sim_users cache:"
                    #     print sim_users
                    #     raise err
                    # except Exception as err:
                    #     print "Errors happen, this time it is:", err

    if store_results:
        print "Storing the computed scores in the DB"
        print "We are going to use the cache of the us module"
        print "The cache currently contains", len(us.scores), "entries"
        t0 = time()
        mdb = MongoClient(host=mdb_host)
        scores_vectors = {}
        for (q, p, u), score in us.scores.items():
            if score == 0.0:
                # Nil score is the same as no score
                continue
            try:
                scores_vectors[(u, q)].append((p, score))
            except KeyError:
                scores_vectors[(u, q)]= [(p, score)]
        print "Precomputation took", time()-t0
        print "We have", len(scores_vectors), "'(u, q) -> score' entries to commit to the DB"
        
        print "Committing new one..."
        t0 = time()
        scores_to_commit = []
        for (user, q), scores in scores_vectors.items():
            print "Dropping previous information..."
            mdb.users.urls_perso_scores.remove({'uid': user, 'qid': q})
            scores_to_commit.append(
                {
                    'uid': user,
                    'qid': q,
                    'vector': scores
                } \
            )
        mdb.users.urls_perso_scores.insert(scores_to_commit)
        print "Done, committing took", time()-t0
        print "Stats:"
        for (user, q), scores in scores_vectors.items():
            print "We have", len(scores), "scores for (q, u)=", (q, user)

    print "Script execution took", time()-t_init

if __name__ == '__main__':
    from sys import argv
    main(argv)