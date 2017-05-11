# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exporters import CsvItemExporter

class EudicWordsPipeline(object):
    def process_item(self, item, spider):
        return item

class CsvExporterPipeline(object):
    def __init__(self):
        self.files = {}

    def open_spider(self, spider):
        file = open('{}.csv'.format(spider.name), 'w+b')
        self.files[spider] = file
        self.exporter = CsvItemExporter(file, include_headers_line=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item