#!/usr/bin/python

from algoliasearch import algoliasearch
from json import loads
import sys
from time import time
from hashlib import sha1
from gzip import open as gzopen
from os.path import join as pjoin
import chardet


def decode(s, encodings=('ascii', 'utf8', 'latin1', 'latin9')):
    for encoding in encodings:
        try:
            return s.decode(encoding)
    	except UnicodeDecodeError:
            pass
    return None

def univ_encode(s):
    try:
        snew = decode(s)
        if snew is not None:
            s = snew
        else:
            result = chardet.detect(s)
            charenc = result['encoding']
            s = unicode(s, charenc, errors='ignore')
        return s.encode('utf8')
    except UnicodeDecodeError:
        return unicode(s, 'utf8', errors='ignore').encode('utf8')

CLI_ARGS = ["input_filename", "web_crawl_page_contents_folder_path", "API_KEY"]
OPTIONAL_PARAMS = ["batch_size"]
def main():
    t0 = time()

    if len(sys.argv) < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), " ".join("[%s]" % _ for _ in OPTIONAL_PARAMS)
        exit()

    fname = sys.argv[1]
    web_crawl_page_contents_folder_path = sys.argv[2]
    api_key = sys.argv[3]
    if len(sys.argv) > (len(CLI_ARGS)+1):
        batch_size = int(sys.argv[len(CLI_ARGS)+1])
    else:
        batch_size = 1000  # The batch size is how many rows we commit at once to algolia

    # Iterate through the list of all the URL we crawled, they are in the order of their ids
    # Note that as we are processing things as soon as we read them (though, batched)
    # we should not have memory issues related to the fact that fname file is huge (>1G)
    with open(fname, 'r') as f:
        # Initialize API Client & Index
        client = algoliasearch.Client("H464S0IAB8", api_key)
        index = client.initIndex('web_crawl')
        array = []
        comma_offset = 0
        i = -1
        n = 0
        f.readline()  # Skip the first line, it only contains the opening bracket of the list
        t1 = time()
        for l in f:
            i += 1
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
                with gzopen(contents_fname, 'rb') as fcontents:
                    contents = fcontents.read()  # this reads the entire file
                    contents = univ_encode(contents)
            except IOError:
                sys.stderr.write("\nUnable to read the content of the URL %s (hash=%s, file=%s)" % (url, hashstr, contents_fname))
                sys.stderr.write("\nIt was likely not crawled, skipping it.\n")
                continue
            row = {"url": url, "hash": hashstr, "content": contents}
            row['objectID'] = i  # The id is nothing else than the index in the list that we are currently iterating
            array.append(row)
            n += 1
            if len(array) == batch_size:
                print "Committing a batch of", batch_size, "rows."
                # Commit a batch away!
                index.saveObjects(array)
                array = []
                print "Rows committed, committed", n, "rows so far (", n/(time()-t1), "rows per second)"
                sys.stdout.flush()
        index.saveObjects(array)

    print "Done in", time()-t0


if __name__ == '__main__':
    main()
