#!/usr/bin/python

"""
This script will take as input the clustering from Lyes' thesis and the queries_to_ids mapping
and a MongoDB host.

It will output the clustering vector of every query in the MongoDB host in a db named queries and a "table"
named clustering.

It will use their ids from the mapping.

The final generated "clustering vector" will look like this:

clustering_vector_for_query = [
    number_of_words_in_common_with_cluster_0,
    number_of_words_in_common_with_cluster_1,
    number_of_words_in_common_with_cluster_2,
    number_of_words_in_common_with_cluster_3,
    ...
    number_of_words_in_common_with_cluster_i_with_i_index_in_this_vector,
    ...
]

the "numbers" are positive integers

Uses ~150M RAM
"""

class ClustersProcessor(object):
    def __init__(self, filepath):
        self.filepath = filepath

    def process(self, **options):
        self.clusters = []
        with univ_open(self.filepath, mode='r') as f:
            i = 0
            for line in f:
                i += 1
                if i % 10 is 0:
                    print "Currently at cluster\t", i
                # A cluster line has the following form:
                # Cluster0: longhorn=02404432-n#174#20 bullock=02403820-n#120#20 angus=02405929-n#41#20 
                line = line.strip().split(' ')
                line.pop(0)  # Get rid of the "clusterX:"

                try:
                    self.clusters.append(
                        set([ \
                            kw.strip().split("=")[0].strip().lower() \
                            for kw in line
                        ])
                    )
                except IndexError as err:
                    print err
                    print "Cluster number", i, "IndexError was raised, cluster list is:"
                    print line
        # Compute the overall set of keywords in the clusters:
        self.set_of_kw = set.union(*self.clusters)

    def cluster_vector_for_kw(self, query_str):
       # Initialize an empty vector
        null_vect = [0] * len(self.clusters)
        vector = null_vect[:]
        query_kw = query_str.strip().lower().split(' ')
        j = 0  # cluster index / cluster id
        for cluster in self.clusters:
            for kw in query_kw:
                kw = kw.strip()
                if kw in cluster:
                    vector[j] += 1
            j += 1
        # end for cluster in clusters
        # The query length is the number of keywords of the query, without counting the keywords that are not in the 
        # global set of keywords of the clusters
        query_len = float(len([None for kw in query_kw if kw in self.set_of_kw]))
        if query_len != 0.0:
            # Then we normalize the coordinates by the length of the query, see. section [qclusters] (6.2?) of the thesis
            for i in xrange(len(vector)):
                vector[i] /= query_len
        elif vector != null_vect:
            print "!!! Warning! The following vector is not null but its query length is null:"
            print "Vector:", vector
            print "query:", query_str
            print "keywords:", query_kw
        return vector

def insert_with_ids_range(mdb, li, start, end):
    ra = xrange(start, end) if end is not None else xrange(start, start+len(li))
    null_vect = [0] * len(li[0])
    values = [ \
        {'_id': i, 'vector': li[i-start] } \
        for i in ra
        if li[i-start] != null_vect \
        # We do not commit queries clustering that have a null clustering, this is just wasted space
    ]
    if not values:
        print "Warning: values list was empty for start,end=", start, ",", end
        return
    try:
        values_cpy = values  # because insert() empties the list and we want to be able to output things in error case
        mdb.insert(values)
    except Exception as err:
        print type(err), err
        print "Something went wrong with:"
        import json
        print json.dumps(values_cpy, indent=4, separators=(',', ': '))

from univ_open import univ_open

CLI_ARGS = ["clusters_file", "queries_to_ids.lst", "mongodb_host"]
OPT_ARGS = ['start_index', 'end_index']
def main():
    ################################################################################
    import sys
    from time import time
    t0 = time()

    n_args = len(sys.argv)
    if n_args < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    start_index, end_index = None, None

    if n_args > len(CLI_ARGS)+1:
        start_index = int(sys.argv[len(CLI_ARGS)+1].strip())

    if n_args > len(CLI_ARGS)+2:
        end_index = int(sys.argv[len(CLI_ARGS)+2])

    # Run that immediately so that we crash on the stop if we cannot connect to the DB anyway
    from pymongo import MongoClient
    mdb_host = sys.argv[3].strip()
    mdb_conn = MongoClient(host=mdb_host)
    mdb = mdb_conn.queries.clustering

    clusters_path = sys.argv[1].strip()
    queries_id_mapping_filepath = sys.argv[2].strip()
    ################################################################################

    ################################################################################
    cp = ClustersProcessor(clusters_path)
    t0 = time()
    cp.process()
    print "Loaded", len(cp.clusters), "clusters."
    ################################################################################

    ################################################################################
    if start_index is None and end_index is None:
        print "Dropping previous DB"
        try:
            mdb.drop()
            mdb = mdb_conn.queries.clustering
        except Exception as err:
            print type(err), err
    else:
        if start_index is None:
            # Remove everything up to the end_index
            where_clause = {'_id': {'$lte': end_index}}
        elif end_index is None:
            # Remove everything starting at start_index
            where_clause = {'_id': {'$gte': start_index}}
        else:
            # Remove everything between the bounds
            where_clause = {'$and': [{'_id': {'$gte': start_index}}, {'_id': {'$lte': end_index}}] }
        print "Removing documents with following where_clause=", where_clause
        mdb.remove(where_clause)
    ################################################################################
        

    ################################################################################
    t0 = time()
    # Note: 40k seems to be the limit, more than that and MongoDB will say "query is too large"
    batch_size = 40000
    start = 0
    end = 0
    with univ_open(queries_id_mapping_filepath, mode='r') as f:
        queries_vectors = []
        i = 0
        for line in f:
            # Skip everything up to the starting index
            if start_index is not None and i < start_index:
                i += 1
                continue
            # hop, we reached the end index, break there
            if end_index is not None and i > end_index:
                break
 
            queries_vectors.append(cp.cluster_vector_for_kw(line))
            
            i += 1
            if i % batch_size is 0:
                start = i - batch_size
                end = i
                sys.stdout.write("Committing batch %d %d...\t" % (start, end))
                sys.stdout.flush()
                insert_with_ids_range(mdb, queries_vectors, start, end)
                print "done."
                queries_vectors = [] # GC?
        # end for line in f

    # if len(queries_vectors) was not a multiple of batch_size, let us execute the last batch:
    # not that the variable "end" will still have the last value that was assigned to it:
    # either 0 is the batch size is greater than the total size of data
    # or the last index that was committed
    if end is not len(queries_vectors)-1:
        print "Last batch..."
        insert_with_ids_range(mdb, queries_vectors, end, None)
    print "Committed", i, "vectors in", time()-t0
    ################################################################################

    ################################################################################
    print "No index creations needed"
    ################################################################################

    ################################################################################
    print "Closing MDB connection"
    mdb_conn.close()
    ################################################################################
    print "Done in", time()-t0
    print "Terminating script."

if __name__ == '__main__':
    main()