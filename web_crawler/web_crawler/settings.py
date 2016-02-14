# Scrapy settings for web_crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'web_crawler'

SPIDER_MODULES = ['web_crawler.spiders']
NEWSPIDER_MODULE = 'web_crawler.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/28.0'

ITEM_PIPELINES = {
    'web_crawler.pipelines.ExportPipeline': 300
}

CONCURRENT_REQUESTS = 500  # More than that will be CPU bound anyway...

# Those two parameters are to be nice with websites...
CONCURRENT_REQUESTS_PER_DOMAIN = 10
DOWNLOAD_DELAY = 1

# Empirical choice
COOKIES_ENABLED = False

# This should speed the crawl up quite a bit
RETRY_ENABLED = False
# We have 500 concurrent request, so we are OK waiting long for 
# every one of them (especially this goes together with no retries)
DOWNLOAD_TIMEOUT = 20  # seconds

# Why not
AJAXCRAWL_ENABLED = True

# Not sure if this will actually work but could be useful
MEMUSAGE_REPORT = True

# Well, yes, we're nice, I said (and we want to emulate/be a real crawler, too!)
ROBOTSTXT_OBEY = True

from scrapy.log import CRITICAL
# Will avoid scrapy pushing tons of logs like "got this page with status X" to stderr
LOG_LEVEL=CRITICAL

DEFAULT_REQUEST_HEADERS = {
    "Accept-Language": "en-US,en;q=0.5",
}

DEPTH_STATS = True
DEPTH_STATS_VERBOSE = True