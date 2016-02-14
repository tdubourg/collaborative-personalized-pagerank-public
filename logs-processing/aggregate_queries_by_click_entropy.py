#!/usr/bin/python

"""
This script takes as input a CSV file with columns (QueryID, NOfClicks, ClickEntropyScore)

It output a CSV file with the number of queries for every ClickEntropyScore
"""

from univ_open import univ_open
from time import time
from math import log

PRECISION_DIGITS_TWO_SEPARATED_VALUES_OF_CLICK_ENTROPY = 1
QUANTIZATION_INTERVAL = 0.5
QUANTIZATION_FACTOR = (10**log(1/float(QUANTIZATION_INTERVAL), 10))
OUTPUT_FORMAT = "%%.%df-%%.%df,%%d" % ((PRECISION_DIGITS_TWO_SEPARATED_VALUES_OF_CLICK_ENTROPY,)*2)

CLI_ARGS = ["clicks_analysis.py_result", "output_path"]
OPT_ARGS = []
def main():
    import sys
    from sys import argv
    t_init = time()

    argc = len(sys.argv)

    if argc < (len(CLI_ARGS)+1):
        print "Usage:", argv[0], " ".join(CLI_ARGS), " ".join(OPT_ARGS)
        exit()

    input_file  = argv[1]
    output_path = argv[2]

    t0 = time()
    print "Loading input file..."
    n_of_queries = {}
    with univ_open(input_file, 'r') as f:
        for line in f:
            # We multiply by 10^number of digits to keep and then
            # take its integer part so that all values Y.xxxy will be stored under YXXX and thus groupped together
            entropy_value = int(float(line.split(',')[2])*QUANTIZATION_FACTOR)
            try:
                n_of_queries[entropy_value] += 1
            except KeyError:
                n_of_queries[entropy_value] = 1
    print "Done in", time() - t0

    print "Outputting result to", output_path, "..."
    with open(output_path, 'w+') as out:
        out.write("ClickEntropyScore,NOfQueries\n")
        out.write('\n'.join((OUTPUT_FORMAT % (i/float(QUANTIZATION_FACTOR), (i+1)/float(QUANTIZATION_FACTOR), n) for i, n in sorted(n_of_queries.items()))))
    print "File written."

    print "Tota: done in", time() - t_init
    print "Terminating script."

if __name__ == '__main__':
    main()