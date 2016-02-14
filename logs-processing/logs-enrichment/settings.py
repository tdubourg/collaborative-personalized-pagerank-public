
BOT_NAME = 'logs-enrichment'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT_LIST = [
#     # Firefoxes
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/30.0',
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/29.0',
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/28.0',
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/27.0',
#     'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',  # twice, to make it more likely
#     # Chromes
#     'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
#     'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
#     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
#     'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
#     # Opera
#     'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',

#     # Note that we do not use IE because we fear YOLO would send special HTML to it (because of its poor standards support)
#     # and that would screw up the HTML xpath things in the spider
# ]

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

ITEM_PIPELINES = [
      'pipelines.CleanUpPipeline'
    , 'pipelines.JSONExportPipeline'
]

DOWNLOAD_DELAY = 10 # Avoid getting banned, used as we are not using proxies mode

# DOWNLOADER_MIDDLEWARES = { 
    # 'middlewares.RandomUserAgentMiddleware': 400,
    # 'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': 1,
    # 'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
# }

# CONCURRENT_REQUESTS = 500  # large scale proxies army setting
# CONCURRENT_REQUESTS = 50  # medium scale proxies army setting
CONCURRENT_REQUESTS = 1  # tor setting
COOKIES_ENABLED = False

REDIRECT_ENABLED = False  # Disable redirections. YOLO only redirects towards bots-intended fake-pages
REFERER_ENABLED = False  # Why would we want to send referer

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive"
    # Note: We DO NOT supply a cookie as we do not want any kind of search personalization to happen here
}
