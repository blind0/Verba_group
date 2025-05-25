import scrapy
import re
import json
from satu.items import CategoriesItem

class CategoriesSpiderSpider(scrapy.Spider):
    name = "categories_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]

    def parse(self, response):
        item = CategoriesItem()

        script_data = response.xpath("//script[contains(text(), 'window.ApolloCacheState =')]/text()").get()

        raw_data = re.search(
            pattern=r'window\._NEW_CATALOG_UI_SSR\s*=\s*.*?window\.ApolloCacheState\s*=\s*({.*?});',
            string=script_data,
            flags=re.DOTALL
        )

        apollo_data = json.loads(raw_data.group(1))

        root_query = apollo_data.get('ROOT_QUERY', {})

        megamenu_data = None
        for key in root_query:
            if key.startswith('megamenu'):
                megamenu_data = root_query[key]
                break

        if megamenu_data:
            categories = []
            for cat in megamenu_data['categories']:
                category_url = f"https://satu.kz/{cat.get('alias')}"
                categories.append({
                    'url': category_url
                })
            item['categories'] = categories

        return item
