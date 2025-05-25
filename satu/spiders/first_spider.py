import math
import scrapy
import json
import re
from satu.items import SatuItem


class SatuSpider(scrapy.Spider):
    name = "satu_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]

    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.categories = {}

        with open('categories.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                categories_list = item.get('categories', [])
                for cat in categories_list:
                    full_url = cat.get('url', {}).strip()
                    if full_url:
                        url = full_url.split('/')[-1]
                        self.categories[url] = None

    def parse(self, response):
        if self.category == 'all':
            for cat_url in self.categories:
                yield response.follow(f"https://satu.kz/{cat_url}", self.parse_category)
        elif self.category in self.categories:
            yield response.follow(f"https://satu.kz/{self.category}", self.parse_category)

    def parse_category(self, response):
        product_links = response.xpath('//div[@data-qaid="product_gallery"]'
                                       '//a[@data-qaid and not(@data-qaid="seo_carousel")]/@href').getall()
        for link in product_links:
            yield response.follow(link, self.parse_item)

        script_data = response.xpath("//script[contains(text(), 'window.ApolloCacheState =')]/text()").get()

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
            total_pages = category_data.get('result', {}).get('listing', {}).get('page', {}).get('total', {})
            pages = math.ceil(total_pages / 48)
            base_url = response.url.split(";")[0]
            for page_num in range(2, pages + 1):
                paginated_url = f"{base_url};{page_num}"
                yield scrapy.follow(paginated_url, self.parse_category)

    def parse_item(self, response):
        item = SatuItem()

        item['url'] = response.url

        name_text = response.xpath('.//div[@class="l-GwW fvQVX"]/h1[@data-qaid="product_name"]/text()').get()
        item['product_name'] = ' '.join(name_text.strip().split()) if name_text else None

        item['images'] = response.xpath('.//div[@data-qaid="image_block"]//img/@src').getall()

        script_data = response.xpath("//script[contains(text(), 'window.ApolloCacheState =')]/text()").get()

        json_match = re.search(
            r'window\.ApolloCacheState\s*=\s*({.*?});',
            script_data,
            re.DOTALL
        )

        data = json.loads(json_match.group(1))
        root_query = data.get('ROOT_QUERY', {})

        fast_data = None
        for key in root_query:
            if key.startswith('product'):
                fast_data = root_query[key]
                break

        item['description'] = fast_data.get('descriptionPlain')
        item['availability'] = fast_data.get('presence', {}).get('isAvailable')
        item['discount_price'] = fast_data.get('discountedPrice')
        item['original_price'] = fast_data.get('priceOriginal')
        item['product_count'] = fast_data.get('ordersCount')

        opinion_counters = fast_data.get('productOpinionCounters', {})
        item['product_rating'] = opinion_counters.get('rating')
        item['reviews_count'] = opinion_counters.get('count')

        company = fast_data.get('company', {})
        if company:
            item['company'] = [{
                'name': company.get('name'),
                'url': f"c{company.get('id', 'None')}-{company.get('slug', 'None')}.html",
                'timeOn': company.get('ageYears'),
                'orders': company.get('deliveredOrdersText'),
                'rating': company.get('opinionStats', {}).get('opinionPositivePercent'),
            }]

        attributes = []
        for attr in fast_data.get('attributes', []):
            name = attr.get('name')
            values = attr.get('values', [])
            for val in values:
                if val.get('value'):
                    attributes.append({
                        'name': name,
                        'value': val.get('value')
                    })
        item['attributes'] = attributes if attributes else None

        return item
