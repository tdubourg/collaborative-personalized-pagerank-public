class LogProcessor(object):
    SERP_TEMPLATE = "{moteur_de_recherc_au_choix_ici}q=%s"
    def __init__(self, log_filepath):
        self.log_filepath = log_filepath

    def process(self, **options):
        """

        /!\ If using options.serp_urls_uniqueness_ and lazy = False, serp_urls returned will be sorted

        """
        # To be c/p-ed example of options
        # try:
        #     self.serp_urls_uniqueness = options['serp_urls_uniqueness']
        # except KeyError:
        #     self.serp_urls_uniqueness = False
        # try:
        #     self.lazy = options['lazy']
        # except KeyError:
        #     self.lazy = True
        # try:
        #     self.return_serp_urls = options['return_serp_urls']
        # except KeyError:
        #     self.return_serp_urls = False
        try:
            queries_filter = options['queries_filter']
        except KeyError:
            queries_filter = None

        self.entries = {}
        with open(self.log_filepath, mode='r') as f:
            for line in f:
                line_arr = line.strip().split('\t')
                if len(line_arr) is 5: # This is a clickthrough line
                    user_id, keywords, date, pos, domain = line_arr
                    keywords = keywords.strip().lower()
                    if queries_filter is not None and keywords not in queries_filter:
                        # Skip this line, not in the filter
                        continue
                    try:
                         domain = domain[domain.index("//")+2:] # Getting rid of something://
                    except ValueError: # Was not found, domain is specified without protocol?
                         pass
                    entry = (user_id, date, pos, domain.strip().lower())
                    try:
                        self.entries[keywords].append(entry)
                    except KeyError:
                        self.entries[keywords] = [entry]
        # Generating another handy data structure:
        # A mapping SERP urls -> entry, to be able to retrieve the keywords from the reply handler in the web scraper
        # And at the same time, this generates the list of SERP urls to be crawl (just do .keys())
        # And at the same time, this allows to retrieve the entry from the SERP url
        # (SERP -> kw, kw -> entry using self.entries)
        self.serp_to_kw = {}
        for kw in self.entries.keys():
            self.serp_to_kw[self.generate_serp_url_from_keywords(kw)] = kw
        return self.serp_to_kw.keys()

    @staticmethod
    def generate_serp_url_from_keywords(keywords):
        return LogProcessor.SERP_TEMPLATE % keywords.replace(' ', '%20')
