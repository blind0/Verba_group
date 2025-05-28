import json
import math
import re
from urllib.parse import urljoin

import scrapy
from scrapy.http.response import Response

from satu.items import SatuItem


class SatuSpider(scrapy.Spider):
    name = "satu_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]
    base_url = "https://satu.kz"

    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.categories = {}

        with open('categories.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                self.categories[item["alias"]] = item["caption"]

    def parse(self, response: Response):
        self.logger.info("Recieved initial response")
        if self.category is None:
            for cat_alias, cat_caption in self.categories.items():
                yield response.follow(
                    url=urljoin(self.base_url, cat_alias),
                    callback=self.parse_category,
                    meta={"category": cat_caption}
                )
        elif self.category in self.categories:
            yield response.follow(
                url=f"https://satu.kz/{self.category}",
                callback=self.parse_category,
                meta={
                    "category": self.categories[self.category]
                }
            )

    def parse_category(self, response: Response):
        self.logger.info("Parsing category: %s", response.meta["category"])
        script_data = response.xpath(
            "//script[contains(text(), 'window.ApolloCacheState =')]/text()"
        ).get()

        raw_data = re.search(
            pattern=r'window\._NEW_CATALOG_UI_SSR\s*=\s*.*?window\.ApolloCacheState\s*=\s*({.*?});',
            string=script_data,
            flags=re.DOTALL
        )

        apollo_data = json.loads(raw_data.group(1))

        fast_cache = apollo_data.get('_FAST_CACHE', {})

        category_data = None
        for key in fast_cache:
            if key.startswith('CategoryListingQuery'):
                category_data = fast_cache[key]
                break

        if category_data:
            total_pages = category_data["result"]["listing"]["page"]["total"]
            pages = math.ceil(total_pages / 48)
            for page_num in range(1, pages + 1):
                paginated_url = f"{response.url};{page_num}"
                yield response.follow(
                    url=paginated_url,
                    callback=self.parse_page,
                    meta={
                        "category": response.meta["category"],
                        "page": page_num
                    }
                )

    def parse_page(self, response: Response):
        self.logger.info("Parse %s page: %s", response.meta["category"], response.meta["page"])
        product_links = response.xpath('//div[@data-qaid="product_gallery"]'
                                       '//a[@data-qaid and not(@data-qaid="seo_carousel")]/@href').getall()
        for link in product_links:
            yield response.follow(link, self.parse_item)

    def parse_item(self, response: Response):
        self.logger.info("Parsing item: %s", response.url)
        item = SatuItem()

        item['url'] = response.url

        name_text = response.xpath('//h1[@data-qaid="product_name"]/text()').get()
        item['product_name'] = ' '.join(name_text.strip().split()) if name_text else None

        item['images'] = response.xpath('.//div[@data-qaid="image_block"]//img/@src').getall()

        script_data = response.xpath(
            "//script[contains(text(), 'window.ApolloCacheState =')]/text()"
        ).get()

        json_match = re.search(
            r'window\.ApolloCacheState\s*=\s*({.*?});',
            script_data,
            re.DOTALL
        )

        data = json.loads(json_match.group(1))
        root_query = data.get('_FAST_CACHE', {})

        fast_data = None
        for key in root_query:
            if key.startswith('ProductCardPageQuery'):
                fast_data = root_query[key]
                break
        card_data = fast_data["result"]["product"]

        item['description'] = card_data.get('descriptionPlain')
        item['availability'] = card_data.get('presence', {}).get('isAvailable')
        item['discount_price'] = card_data.get('discountedPrice')
        item['original_price'] = card_data.get('priceOriginal')
        item['product_count'] = card_data.get('ordersCount')

        opinion_counters = card_data.get('productOpinionCounters', {})
        item['product_rating'] = opinion_counters.get('rating')
        item['reviews_count'] = opinion_counters.get('count')

        company = card_data.get('company', {})
        if company:
            item['company'] = {
                'name': company.get('name'),
                'url': f"c{company.get('id', 'None')}-{company.get('slug', 'None')}.html",
                'timeOn': company.get('ageYears'),
                'orders': company.get('deliveredOrdersText'),
                'rating': company['opinionStats']['opinionPositivePercent'],
                'phone': company.get('phone')
            }

        attributes = []
        for attr in card_data.get('attributes', []):
            name = attr.get('name')
            values = attr.get('values', [])
            for val in values:
                if val.get('value'):
                    attributes.append({
                        'name': name,
                        'value': val.get('value')
                    })
        item['attributes'] = attributes if attributes else None

        yield  item
