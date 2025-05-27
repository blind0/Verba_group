import scrapy
import re
import json
from satu.items import CategoriesItem

class CategoriesSpiderSpider(scrapy.Spider):
    name = "categories_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]

    def parse(self, response):
        

        script_data = response.xpath("//script[contains(text(), 'window.ApolloCacheState =')]/text()").get()

        raw_data = re.search(
            pattern=r'window\._NEW_CATALOG_UI_SSR\s*=\s*.*?window\.ApolloCacheState\s*=\s*({.*?});',
            string=script_data,
            flags=re.DOTALL
        )

        apollo_data = json.loads(raw_data.group(1))

        for key in apollo_data.keys():
            if key.startswith("CategoriesMegamenu"):
                item = CategoriesItem()
                self.logger.info(key)
                item["alias"] = apollo_data[key]["alias"]
                item["caption"] = apollo_data[key]["caption"]
                yield item