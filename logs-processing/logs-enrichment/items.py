# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class LogItem(Item):
    url = Field()
    pos = Field()
    orig_pos = Field()
    user_id = Field()
    kw = Field()
    date = Field()
    page = Field()
    # title = Field()
    # desc = Field()

class SERPItem(Item):
    results = Field()
    kw = Field()
    page = Field()