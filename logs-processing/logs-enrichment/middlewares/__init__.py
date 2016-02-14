from settings import USER_AGENT_LIST
import random
from scrapy import log

print "RandomUserAgentMiddleware module is being loaded!"

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua  = random.choice(USER_AGENT_LIST)
        if ua:
            request.headers.setdefault('User-Agent', ua)
        else:
            print "WARNING: No UA found?!?"
            request.headers.setdefault('User-Agent', "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0")