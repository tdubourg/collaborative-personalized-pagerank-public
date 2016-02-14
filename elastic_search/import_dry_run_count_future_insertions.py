#!/usr/bin/python

"""
This file is a sort of dry-run of the import of the data into elastic search.

It will just go through the input file, try to open the contents files and
ultimately display the number of rows that would have been inserted if we 
were actually importing stuff into ES.

"""

from json import loads
import sys
from time import time
from hashlib import sha1
from gzip import open as gzopen
from os.path import join as pjoin

CLI_ARGS = ["input_filename", "web_crawl_page_contents_folder_path"]
OPTIONAL_PARAMS = []
def main():
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join("[%s]" % _ for _ in OPTIONAL_PARAMS)
        exit()

    fname = sys.argv[1]
    web_crawl_page_contents_folder_path = sys.argv[2]

    # Iterate through the list of all the URL we crawled, they are in the order of their ids
    # Note that as we are processing things as soon as we read them (though, batched)
    # we should not have memory issues related to the fact that fname file is huge (>1G)
    with open(fname, 'r') as f:
        # Init vars for the big loop
        comma_offset = 0
        n = 0

        # Skip the first line, it only contains the opening bracket of the list
        f.readline()
        # Big loop!
        for l in f:
            l = l.strip()
            if l == "]":
                # We're done with the file, this is the last line
                break
            l = l[comma_offset:]
            comma_offset = 1
            url = loads(l)
            hashstr = sha1(url).hexdigest()
            contents_fname = pjoin(web_crawl_page_contents_folder_path, hashstr + ".html.gz")
            try:
                # This is just to check we would be able to open the file (as GZ), but we do not actually read the data...
                with gzopen(contents_fname, 'rb') as fcontents:
                    pass
            except IOError:
                continue
            n += 1
    print "Total of", n, " objects to be committed to the DB"
    print "Done in", time()-t0


if __name__ == '__main__':
    main()
