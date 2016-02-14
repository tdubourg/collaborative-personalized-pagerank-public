# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sys, os
from items import WebPageItem
from threading import Timer
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../../")))
# from utils.json_utils import load_json, write_json
from hashlib import sha1
from gzip import open as gzopen
import json
from os.path import join as pjoin

class ExportPipeline(object):
    DUMP_DATA_EVERY_X_ITEMS = 500 # Dump data every X items... so that if the program crashes, we do not lose everything
    DUMP_PAGES_EVERY_X_SECONDS = 3
    stop_gzip_timer = False

    def __init__(self):
        self.fname_crawled_items = None
        self.fname_web_graph = None
        self.n_item = 0 
        self.gzipped_io_queue = []
        self.gzip_dump_timer = Timer(self.DUMP_PAGES_EVERY_X_SECONDS, self.dump_gzipped_contents)
        self.gzip_dump_timer.start()

    def open_spider(self, spider):
        self.load_crawled_items(spider)

    def load_crawled_items(self, spider):
        self.fname_crawled_items = spider.export_results_filename.replace('.json', '') + ".json.gz"
        # The start of a JSON dict
        f = gzopen(self.fname_crawled_items, 'ab', 6)
        f.write("{")
        f.close()
        self.fname_web_graph = spider.export_results_filename.replace('.json', '') + '_graph.json.gz'  # Not directly replacing ".json" pattern so that if pattern not here, we just append to fname!
        # The start of a JSON dict
        f = gzopen(self.fname_web_graph, 'ab', 6)
        f.write("{")
        f.close()
        self.crawled_items = {}
        self.nodes_edges = {}
            
    def process_item(self, item, spider):
        self.process_crawled_item(item, spider)

    def close_spider(self, spider):
        self.dump_data()
        # The end of JSON dicts
        f = gzopen(self.fname_crawled_items, 'a', 6)
        f.write("\n}")
        f.close()
        f = gzopen(self.fname_web_graph, 'ab', 6)
        f.write("\n}")
        f.close()
        self.gzip_dump_timer.cancel()
        self.gzip_dump_timer = None
        self.stop_gzip_timer = True
        # And execute it by hand synchronously to be sure 
        # we finish dumping everything before closing
        self.dump_gzipped_contents()

    def write_append(self, fname, lines):
        f = gzopen(fname, 'ab', 6)
        for l in lines:
            json_dict_line = "\n,%s: %s" % (json.dumps(l[0]), json.dumps(l[1]))
            f.write(json_dict_line)
        f.close()
    
    def dump_data(self):
        print "Dumping data to %s and %s" % (self.fname_crawled_items, self.fname_web_graph)
        self.write_append(self.fname_crawled_items, self.crawled_items.items())
        self.crawled_items = {}
        self.write_append(self.fname_web_graph, self.nodes_edges.items())
        self.nodes_edges = {} 

    def dump_gzipped_contents(self):
        while self.gzipped_io_queue:
            fname, content = self.gzipped_io_queue.pop()
            print "Dumping gzipped data to file", fname
            f = gzopen(fname, 'wb', 6)  # 6 is supposed to offer very good perf/size ratio
            f.write(content)
            f.close()
        if self.gzip_dump_timer is None or self.stop_gzip_timer is True:
            # It means we should not repeat ourselves
            return
        else:
            self.gzip_dump_timer = Timer(self.DUMP_PAGES_EVERY_X_SECONDS, self.dump_gzipped_contents)
            self.gzip_dump_timer.start()

    def process_crawled_item(self, item, spider):
        if self.fname_crawled_items is None:
            self.load_crawled_items(spider)
        url = item['url']
        h = sha1(url).hexdigest()
        fname = pjoin(spider.web_pages_export_dir, "%s.html.gz" % h)
        self.gzipped_io_queue.append((fname, item['html']))
        self.crawled_items[url] = {
            'hash':h,
            'meta': {
                'start_url': item['meta']['start_url'],
                'metadepth': item['meta']['metadepth']
            }
        }
        self.nodes_edges[url] = [u.url for u in item['links']]
        if len(self.crawled_items) % self.DUMP_DATA_EVERY_X_ITEMS is 0:
            self.dump_data()
