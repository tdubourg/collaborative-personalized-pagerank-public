#!/usr/bin/python

"""
Will take as input a list of file resulting of partial web graph crawls
and will insert all the URLs into a unique list. The URLs then have a unique integer ID associated to
them which is their position in the resulting list.
This program will take a lot of RAM if your input files are big, beware.
The output is written Gzipped for space efficiency.
"""


from gzip import open as gzopen
from json import loads, dumps
import sys

if len(sys.argv) < 3:
    print "Usage:", sys.argv[0], "output_path_dict.json.gz output_path_dict.lst.gz [input_crawl_graph.json.gz ...]"
    sys.exit()

with gzopen(sys.argv[1], 'wb', 6) as outfile:
    with gzopen(sys.argv[2], 'wb', 6) as outfile2:
        i = 2
        processed = 0
        set_of_urls = set()
        while i < len(sys.argv):
            with gzopen(sys.argv[i], 'rb') as f:
                f.readline() # skip the first line
                start_index = 0  # On the first line there is no leading comma
                for line in f:
                    line = line.strip()
                    if line == "}":
                        continue
                    d = loads("{%s}" % line[start_index:])
                    start_index = 1  # After the first item, there is a leading comma
                    try:
                        node = d.keys()[0]
                        set_of_urls.add(node)
                        edges = d[node]
                        [set_of_urls.add(_) for _ in edges]
                        processed += len(edges) + 1
                        if processed % 10000 is 0:
                            print "Processed %s urls" % processed
                    except IndexError as e:
                        print "IndexError for line:", line
                        print e
            i += 1
        print "Parsing done. Now slowly writing", len(set_of_urls), "elements to disk in JSON format..."
        comma = ""
        outfile.write("[")
        for u in set_of_urls:
            outfile.write("\n%s%s" % (comma, dumps(u)))
            comma = ","
        outfile.write("\n]")
        # Python won't allocate such a big string, it seems, sucks!
        # outfile.write("\n,".join(set_of_urls))  # Note: We're adding newlines to be able to open the file with vim

        print "Done. Now slowly writing", len(set_of_urls), "elements to disk in LIST format..."
        for u in set_of_urls:
            outfile2.write("%s\n" % u)