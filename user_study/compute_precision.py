#!/usr/bin/python

from json import load

N_OF_USERS = 11
N_OF_QUERIES = 5
MAX_N_OF_RELEVANT_RESULTS = 5

COMMON_DIVIDER = float(sum([11 - i for i in xrange(1, MAX_N_OF_RELEVANT_RESULTS)]))

def p(q, u, sessions, ranking):
    """
        :param{int} q: query index (0 to 4)
        :param{int} u: the volunteer anonymous id (0 to 10)
        :param{dict} sessions: the sessions
        :param{string} ranking: either "standard" (baseline) or "cppr"
    """
    relevant_results = sessions[u]['pages'][str(q)][ranking]
    return sum([
        11 - r for r in relevant_results.values()  # the values are the ranks of the selected relevant results
        ]) / COMMON_DIVIDER

def pd(q, u, sessions):
    baseline_precision = p(q, u, sessions, 'standard')
    cppr_precision = p(q, u, sessions, 'cppr')
    if baseline_precision == 0.0:
        if cppr_precision != 0.0:
            # The baseline had a nil precision and the cppr has a non-null one so the difference is basically +infty
            return float('inf')
        else:
            # if both are 0, then the difference is 0 too
            return 0.0
    return (cppr_precision - baseline_precision) / baseline_precision

def main(argc, argv):
    if argc < 2:
        print "Missing argument: results_file_path.json"
        exit()

    output_path = "precisions.csv"

    if argc > 2:
        output_path = argv[2].strip()

    print "Printing precisions measures for", N_OF_USERS, "users"

    results_file_path = argv[1].strip()
    with open(results_file_path, 'r') as f:
        results = load(f)

    avg_precisions_cppr = []
    avg_precisions_baseline = []
    avg_prec_diffs = []
    for q in xrange(N_OF_QUERIES):
        print "\n\n------------------------------------------------------------"
        print "Precision results for query", q
        precisions              = [p(q, u, results, 'cppr') for u in xrange(N_OF_USERS)]
        baseline_precisions     = [p(q, u, results, 'standard') for u in xrange(N_OF_USERS)]
        precisions_diff         = [pd(q, u, results) for u in xrange(N_OF_USERS)]
        avg_cppr_precision      = sum(precisions) / float(len(precisions))
        avg_baseline_precision  = sum(baseline_precisions) / float(len(baseline_precisions))
        avg_precisions_cppr.append(avg_cppr_precision)
        avg_precisions_baseline.append(avg_baseline_precision)
        avg_prec_diff = sum(precisions_diff) / float(len(precisions_diff))
        avg_prec_diffs.append(avg_prec_diff)
        print " CPPR precisions, by user:\t\t\t", " ".join(["%5.2f" % i for i in precisions])
        print " Baseline precisions, by user:\t\t\t", " ".join(["%5.2f" % i for i in baseline_precisions])
        print " Precisions differences from baseline, by user:\t", " ".join(["%5.2f" % i for i in precisions_diff])
        print " Average precision:\t\t\t\t%5.2f" % avg_cppr_precision
        print " Average baseline precision:\t\t\t%5.2f" % avg_baseline_precision
        print " Average precision difference from baseline:\t%5.2f" % avg_prec_diff
        print " Difference in average precision from baseline:\t%5.2f" % (avg_cppr_precision - avg_baseline_precision)

    print "Outputting average precisions and precisions differences avg to", output_path
    with open(output_path, 'w+') as f:
        f.write('"Query Index","Average Precision (baseline)","Average Precision(CPPR)","Average \'Precision Difference\'"\n')
        f.write(
            '\n'.join([
                '%d,%.2f,%.2f,%.2f' % (
                    i,
                    avg_precisions_baseline[i],
                    avg_precisions_cppr[i],
                    avg_prec_diffs[i]
                )
                for i in xrange(N_OF_QUERIES)
            ])
        )

if __name__ == '__main__':
    from sys import argv
    main(len(argv), argv)