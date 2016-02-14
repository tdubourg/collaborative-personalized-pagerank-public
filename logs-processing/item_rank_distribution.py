#!/usr/bin/python

"""
    This file computes the distribution of clicked items ranks and the average item rank amongst the clicks
    of the logs.

    It takes as input the path to the logs (converted or not does not matter) and the path to output a CSV file
    to, with following columns:

    rank, number of clicks on items of this rank

"""
from univ_open import univ_open

class LogProcessor(object):
    SERP_TEMPLATE = "{inserer_moteur_de_recherche_au_choix_ici}q=%s"
    MAX_ITEM_RANK = 500 # probably nothng more than that will appear

    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        try:
            queries_filter = options['queries_filter']
        except KeyError:
            queries_filter = None

        self.items_ranks = [0] * (self.MAX_ITEM_RANK + 1)
        with univ_open(self.log_filepath, mode='r') as f:
            for line in f:
                line_arr = line.strip().split('\t')
                if len(line_arr) is 5: # This is a clickthrough line
                    user_id, keywords, date, item_rank, domain = line_arr
                    try:
                        item_rank = int(item_rank)
                    except ValueError as err:
                        print err
                        print "The line that caused this error is the following:"
                        print line
                        continue  # Skip this value as we cannot parse it anyway

                    if queries_filter is not None and keywords not in queries_filter:
                        # Skip this line, not in the filter
                        continue
                    try:
                        self.items_ranks[item_rank] += 1
                    except IndexError:
                        print "Wow! We got an item ranked", item_rank
                        print "Please increase the MAX_ITEM_RANK value"
                        exit()
        avg = sum([self.items_ranks[i]*i for i in xrange(1, len(self.items_ranks))]) / float(sum(self.items_ranks[1:]))
        return avg

    @staticmethod
    def generate_serp_url_from_keywords(keywords):
        return LogProcessor.SERP_TEMPLATE % keywords.replace(' ', '%20')

CLI_ARGS = ['logs_filepath', 'output_path']
def main():
    from sys import argv

    argc = len(argv)
    if argc <= len(CLI_ARGS):
        print "Usage: %s"  % argv[0], ' '.join(CLI_ARGS)
        print "Currently missing parameters arguments:", ' '.join(CLI_ARGS[len(argv)-1:])
        exit()

    logs_filepath   = argv[1].strip()
    output_path     = argv[2].strip()

    lp = LogProcessor(logs_filepath)
    avg = lp.process()

    with open(output_path, 'w+') as f:
        for i in xrange(1, len(lp.items_ranks)):
            f.write("%d,%d\n" % (i, lp.items_ranks[i]))

    print "The average rank overall is", avg


if __name__ == '__main__':
    main()
