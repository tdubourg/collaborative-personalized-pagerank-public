#!/usr/bin/python

from pymongo import MongoClient
from os import getenv

VPS = getenv('VPS')
DOMAIN_LIMIT = 2

def extract_domain(url):
    try:
        url = url[url.index("//")+2:] # getting rid of protocol://
    except ValueError:
        # There was no protocol specified
        pass
    try:
        url = url[:url.index("/")] # getting rid of everything after the first "/"
    except ValueError:
        # Maybe it was a domain-only url, with no "/"
        pass
    return url

def osim(r1, r2, k):
    """
        Compute the OSim measure between two rankings
        The OSim is a similarity measures and is thus symmetric: osim(r1, r2, k) == osim(r2, r1, k)
        OSim measures the degree of overlap between two rankings.

        :param{set} r1, r2: sets we are computing the OSim of
        :param{int} k: size of the subset of r1,r2 to be considered
    """
    # Note: We use the notation r1, r2 and a and b so that it corresponds to the formula given in CPPR.md (thesis)
    a = set(r1[:k])
    b = set(r2[:k])
    return len(a & b) / float(k)  # & is the intersection

def ksim(r1, r2):
    """
        Compute the K Similairty between rankings r1 and r2
        KSim measures the degree of _agreement_ between the two rankings. 1 = same rankings, 0 = maximum disagreement
    """

    pos1 = {r1[i]: i for i in range(len(r1))}
    pos2 = {r2[i]: i for i in range(len(r2))}
    a = set(r1)
    b = set(r2)
    U = a | b
    d1 = U - a
    d2 = U - b

    curr_maxi = len(r1)
    for _ in d1:
        pos1[_] = curr_maxi + pos2[_]

    curr_maxi = len(r2)
    for _ in d2:
        pos2[_] = curr_maxi + pos1[_]

    agreement_set = set()
    for u in U:
        for v in U:
            if u == v:
                continue
            # The following condition checks that the relative order of u and v is the same in r1 and r2
            # note that positions cannot be equal (it's a list, with one item per index) so we can use strict comparison
            if (pos1[u] < pos1[v]) == (pos2[u] < pos2[v]):
                agreement_set.add((u, v))
    return len(agreement_set) / float(len(U) * (len(U) - 1))

def postprocess(ranking):
    seen = {}
    result = []
    for __ in ranking:
        # Translation from JavaScript index.js line ~240
        domain = extract_domain(__['url'])
        seen[domain] = seen.setdefault(domain, 0) + 1
        if seen[domain] >= DOMAIN_LIMIT:
            continue
        result.append(__['urlid'])
    return result

def main(argc, argv):
    if argc < 2:
        print "Missing argument: k"
        exit()

    k = int(argv[1].strip())

    output_path_osim = "osim_at_%d.csv" % k
    if argc > 2:
        output_path_osim = argv[2].strip()

    output_path_ksim = "ksim_at_%d.csv" % k
    if argc > 2:
        output_path_ksim = argv[2].strip()

    mdb = MongoClient(host=VPS)
    print "Connected."

    # the final_serps collection should only contain the following queries rankings:
    # u'pizza',
    # u'massage',
    # u'water fountains',
    # u'tattoo art',
    # u'science experiments',
    # for reference, their ids are: [1229065, 5225582, 3987655, 6391715, 9970203]
    print "Downloading SERPs..."
    serps = [
        {
            'qstr': _['qstr'],
            # Note: The goal here is just to have the sorted rankings of URLs, we just need a uniquely
            # identifying information for each URL, urlid is perfect
            'baseline':     postprocess(_['ranking_noperso']),
            'cppr':         postprocess(_['ranking_perso'])
        }
        for _ in 
        mdb.user_study.serps_final.find()
    ]

    print "OSims:"
    for q in serps:
        if len(q['baseline']) < k or len(q['cppr']) < k:
            print "Error! Query", q['qstr'], "had a ranking with less than", k, "elements after postprocessing."
        print "%30s\t%5.2f" % (q['qstr'], osim(q['baseline'], q['cppr'], k))

    print "Outputting to", output_path_osim
    with open(output_path_osim, 'w+') as f:
        f.write('"Query","OSim"\n')
        f.write(
            '\n'.join([
                '%s,%.2f' % (q['qstr'], osim(q['baseline'], q['cppr'], k))
                for q in serps
            ])
        )

    print "KSims:"
    for q in serps:
        r1, r2 = q['baseline'][:k], q['cppr'][:k]
        if len(r1) < k or len(r2) < k:
            print "Error! Query", q['qstr'], "had a ranking with less than", k, "elements after postprocessing."
        print "%30s\t%5.2f" % (q['qstr'], ksim(r1, r2))

    print "Outputting to", output_path_ksim
    with open(output_path_ksim, 'w+') as f:
        f.write('"Query","KSim"\n')
        f.write(
            '\n'.join([
                '%s,%.2f' % (q['qstr'], ksim(q['baseline'][:k], q['cppr'][:k]))
                for q in serps
            ])
        )

if __name__ == '__main__':
    from sys import argv
    main(len(argv), argv)