"""

This module provides methods to load information about the similar users of a given users set

"""

from pymongo import MongoClient

def load_sim_users(mdb_host, users):
    """
        Will simply return a dictionary of user -> set of (similar user, similarity) taken from the DB
    """
    mdb = MongoClient(host=mdb_host)
    result = {\
        int(item['_id']): item['sim_users'] \
        for item in mdb.users.similar_users.find({
            '_id': {
                '$in': list(users)
            }
        }) \
    }
    print "We received", len(result), "results from MDB and had", len(users), "inputs"
    print "We received results for the following users:", result.keys()
    return result

def load_set_of_similar_users(mdb_host, users):
    sim_users_data = load_sim_users(mdb_host, users)
    result = set()
    for u, sim_users_and_scores in sim_users_data.items():
        for sim_score, sim_u in sim_users_and_scores:
            result.add(sim_u)
    return result