#!/usr/bin/python

"""
This file will check whether URLids in the input file are amongst the leaves of
the crawl or the outlinks of those leaves or not and output the ones that are neither of this.
"""

from gzip import open as gzopen
from json import loads
from time import time
import sys

if len(sys.argv) is not 5:
    print "Usage: ", sys.argv[0], " max_depth input_file.gz output_file.gz metadata_file.json.gz"
    sys.exit()
max_depth = int(sys.argv[1])

print "Opening output file for writing..."
with gzopen(sys.argv[3], 'wb+', 6) as out_f:
    id_indexed_metadata = []
    # Note that we're reading the JSON file line by line by hand instead of using json.load() because
    # the json module is a bit stupid and will load the entire file in memory under the form of a string
    # before parsing it and will thus spam our memory quite badly!
    print "Loading metadata file..."
    t0 = time()
    with gzopen(sys.argv[4], 'rb') as metadata_f:
        metadata_f.readline()  # Skip first line
        comma_offset = 0  # No comma on the first element's line
        for line in metadata_f:
            line = line.strip()
            if line == "]":
                # EOF, we're done
                break
            id_indexed_metadata.append(loads(line[comma_offset:]))
            comma_offset = 1

    print "Done in", time()-t0
    found = 0
    set_of_starting_urls = set()
    print "Reading and processing input file..."
    t0 = time()
    with gzopen(sys.argv[2], 'rb') as in_f:
        for line in in_f:
            urlid = int(line.strip())
            if not id_indexed_metadata[urlid][0]:  # Then this was not even crawled, not even a leaf, but an outlink of a leaf
                continue
            # Loop through all the crawl metadata we have (might be multiple ones as a URL might have ended up
            # in multiple crawls)
            for metadata in id_indexed_metadata[urlid][0]:
                if metadata['metadepth'] is not max_depth:
                    set_of_starting_urls.add(metadata['start_url'])
                    out_f.write("%d\t%s\n" % (urlid, metadata['start_url'].strip()))
                    found += 1
                    break  # No need to check further
    print "Done in", time()-t0
    print "Found", found, "URLs that were neither leaves of the crawl nor outlinks of leaves amongt the ones",
    print "in the input file"
    print "They are crawled from ", len(set_of_starting_urls), "different starting urls"
print "Done"