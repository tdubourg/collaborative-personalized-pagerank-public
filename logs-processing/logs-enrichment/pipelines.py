# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sys, os
from items import LogItem, SERPItem

sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../../")))
from utils.shell_utils import execute_shell_and_get_stdout as execsh
from utils.json_utils import load_json, write_json

class CleanUpPipeline(object):
    def process_item(self, item, spider):
        # if item["title"]:
        #     item["title"] = item["title"].encode('utf-8')
        # if item["desc"]:
        #     item["desc"] = item["desc"].encode('utf-8')
        # if item["url"]:
        #     item["url"] = item["url"].encode('utf-8')
        return item

class JSONExportPipeline(object):
    DUMP_DATA_EVERY_X_ITEMS = 1 # Dump data every X items... so that if the program crashes, we do not lose everything
    
    def __init__(self):
        self.fname_log_items = None
        self.fname_serp_items = None
        self.n_item = 0 

    def open_spider(self, spider):
        self.load_log_items(spider)
        self.load_serp_items(spider)

    def load_log_items(self, spider):
        self.fname_log_items = spider.export_results_filename
        try:
            self.log_items = load_json(self.fname_log_items)
        except IOError:
            self.log_items = {}
            
    def load_serp_items(self, spider):
        self.fname_serp_items = spider.export_results_filename.replace('.json', '_serps.json')
        try:
            self.serp_items = load_json(self.fname_serp_items)
        except IOError:
            self.serp_items = {}

    def process_item(self, item, spider):
        print "Processing item for JSON Export..."
        item_dict = item.__dict__["_values"]
        kw = item['kw']
        # Note: We are actually modifying the object, here, as we did not do a deep copy of the dict
        item_dict.pop('kw') # getting rid of the kw attribute, we do not need to store it for every click...
        if type(item) is LogItem:
            self.process_log_item(kw, item_dict, spider)
        elif type(item) is SERPItem:
            self.process_serp_item(kw, item_dict, spider)

        if self.n_item > self.DUMP_DATA_EVERY_X_ITEMS:
            self.n_item = 0
            self.dump_data()
        self.n_item += 1
        return item

    def close_spider(self, spider):
        self.dump_data()
    
    def dump_data(self):
        print "Dumping data to %s" % self.fname_log_items
        write_json(self.log_items, self.fname_log_items)
        print "Dumping data to %s" % self.fname_serp_items
        write_json(self.serp_items, self.fname_serp_items)

    def process_log_item(self, kw, item_dict, spider):
        if self.fname_log_items is None:
            self.load_log_items(spider)
        try:
            self.log_items[kw].append(item_dict)
        except KeyError:
            self.log_items[kw] = [item_dict]

    def process_serp_item(self, kw, item_dict, spider):
        if self.fname_serp_items is None:
            self.load_log_items(spider)
        try:
            self.serp_items[kw].append(item_dict)
        except KeyError:
            self.serp_items[kw] = [item_dict]