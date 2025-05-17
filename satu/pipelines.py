# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class SatuPipeline:
    def process_item(self, item, spider):
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
