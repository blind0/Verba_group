# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exporters import JsonItemExporter
from scrapy.exceptions import DropItem

from satu.items import CategoriesItem, SatuItem

class SatuPipeline:
    def process_item(self, item, spider):
        if not isinstance(item, SatuItem):
            return item

        adapter = ItemAdapter(item)
        if not adapter.get('product_name'):
            raise DropItem(f"Missing product name in {item}")
        if not adapter.get('url'):
            raise DropItem(f"Missing URL in {item}")

        for field in ['normal_cost', 'discount_cost', 'orders_count', 'product_rating', 'reviews_count']:
            if field in adapter and adapter[field] is not None:
                try:
                    adapter[field] = float(adapter[field])
                except (TypeError, ValueError):
                    adapter[field] = None

        return item

class CategoriesPipeline:
    def open_spider(self, spider):
        self.file = open('reviews.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8')
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        if not isinstance(item, CategoriesItem):
            return item

        self.exporter.export_item(item)
        return item