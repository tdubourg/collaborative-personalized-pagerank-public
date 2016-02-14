#!/usr/bin/python

"""
This file will converts web crawl result files from
dict-based urls adjacency lists to list-based ids adjacency lists.
"""


from gzip import open as gzopen
from json import loads, dumps, load
import sys

if len(sys.argv) < 3:
    print "Usage: ./script dict_urls_to_ids.json.gz [input_crawl_graph.json.gz ...]"
    sys.exit()

ids = {}
ordered_urls = load(gzopen(sys.argv[1], 'rb'))
i = 0
for u in ordered_urls:
    ids[u] = i
    i += 1

ordered_urls = None  # Hopefully GC-ed

print "Dictionary loaded"

i = 2
while i < len(sys.argv):
    fname = sys.argv[i]
    with gzopen(fname, 'rb') as f:
        print "Converting file", fname, "..."
        processed = 0
        comma = ""  # No comma before the first line has been inserted
        fname_out = fname.replace(".json", ".converted.json")
        with gzopen(fname_out, 'wb', 6) as outfile:
            outfile.write("[")
            f.readline() # skip the first line
            start_index = 0  # On the first line there is no leading comma
            for line in f:
                line = line.strip()
                if line == "}":
                    continue
                d = loads("{%s}" % line[start_index:])
                start_index = 1  # After the first item, there is a leading comma
                try:
                    li = d.values()[0]
                    outfile.write(
                        "\n%s%s" % 
                        (comma, dumps(
                            (
                                ids[d.keys()[0]],
                                [ids[_] for _ in li]
                            )
                        ))
                    )
                    comma = ","  # Now you've got your comma
                    processed += len(li) + 1
                    if processed % 10000 is 0:
                        print "Processed %s urls" % processed
                except IndexError as e:
                    print "IndexError for line:", line
                    print e
            outfile.write("\n]")
            print "Done:", fname, "->", fname_out
        i += 1