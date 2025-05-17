import scrapy
import json
import re
from satu.items import SatuItem


class SatuSpider(scrapy.Spider):
    name = "satu_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]

    CATEGORIES = {
        "electronics": "Tehnika-i-elektronika",
        "construction": "Stroitelstvo",
        "home": "Dom-i-sad",
        "repair": "Materialy-dlya-remonta",
        "jewelry": "Ukrasheniya-i-chasy",
        "beauty": "Krasota-i-zdorove",
        "clothes": "Odezhda",
        "food": "Produkty-pitaniya-napitki",
        "medicine": "Medikamenty-meditsinskie-tovary",
        "kids": "Tovary-dlya-detej",
        "tools": "Instrument"
    }

    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

    def parse(self, response):
        if self.category:
            if self.category == 'all':
                for cat_url in self.CATEGORIES.values():
                    yield response.follow(f"/{cat_url}", self.parse_category)
            elif self.category in self.CATEGORIES:
                yield response.follow(f"/{self.CATEGORIES[self.category]}", self.parse_category)
        else:
            yield response.follow("/Tehnika-i-elektronika", self.parse_category)

    def parse_category(self, response):
        product_links = response.xpath('//div[@data-qaid="product_gallery"]'
                                       '//a[@data-qaid="product_link"]/@href').getall()
        for link in product_links:
            yield response.follow(link, self.parse_item)

        next_page = response.xpath('//div[@data-qaid="pagination"]//a[@data-qaid="next_page"]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse_category)

    def parse_item(self, response):
        item = SatuItem()

        MafxA_item = response.xpath('.//div[@class="MafxA _6xArK"]/div[@class="l-GwW"]')
        tqUsL_item = response.xpath('.//div[@class="tqUsL"]')

        item['url'] = response.url

        name_text = response.xpath('.//div[@class="l-GwW fvQVX"]/h1[@data-qaid="product_name"]/text()').get()
        item["product_name"] = ' '.join(name_text.strip().split()) if name_text else None

        item["img"] = response.xpath('.//div[@data-qaid="image_block"]//img/@src').getall()

        item["availability"] = MafxA_item.xpath('.//span[@data-qaid="product_presence"]/text()').get()

        discounted_price = tqUsL_item.xpath('.//div[@class="IP36L bkjEo"]/span[@class="yzKb6"]/text()').get()

        if discounted_price:
            item["current_price"] = discounted_price.strip()
        else:
            regular_price = tqUsL_item.xpath('.//div[@class="bkjEo"]/span[@class="yzKb6"]/text()').get()
            item["current_price"] = regular_price.strip() if regular_price else None

        old_price = tqUsL_item.xpath('.//span[@class="XXdUM bkjEo"]/span[@class="yzKb6"]/text()').get()
        item["old_price"] = old_price.strip() if old_price else None

        item["product_count"] = response.xpath('.//div[@class="MafxA _6xArK"]//div[@class="l-GwW"]'
                                               '/span[@data-qaid="order_counter"]/text()').get()

        rating = response.xpath('.//div[@class="MafxA iU70- WIR6H ZNZm3"]//span[@class="_3Trjq snf--"]/text()').get()
        item["product_rating"] = float(rating) if rating else None

        reviews_count = response.xpath('.//div[@class="MafxA _0NLAD"]//span[@data-qaid="opinion_count"]/text()').get()
        item["reviews_count"] = int(reviews_count) if reviews_count else None

        reviews = []
        for review in response.xpath('.//li[@class="bfetG"]'):
            author = review.xpath('.//span[@data-qaid="author_name"]/text()').get()
            date = review.xpath('.//span[@data-qaid="date_created"]/text()').get()
            text = review.xpath('.//span[@data-qaid="title"]/text()').get()

            if any([author, date, text]):
                reviews.append({
                    'author': author,
                    'date': date,
                    'text': text
                })

        item['reviews'] = reviews if reviews else None

        sellers = []
        for seller in response.xpath('.//div[@class="M3v0L qzGRQ -Zy0Z"]'):
            sellers.append({
                'seller_name': seller.xpath('.//a[@data-qaid="company_name"]/text()').get(),
                'link': response.urljoin(seller.xpath('.//a/@href').get()),
                'time': seller.xpath('.//span[@data-qaid="company_age"]/text()').get(),
                'orders_count': seller.xpath('.//span[@data-qaid="delivered_orders"]/text()').get(),
                'seller_rating': seller.xpath('.//span[@class="_0cNvO jwtUM OX5sJ XCtBJ"]/text()').get()
            })
        item['sellers'] = sellers if sellers else None

        script_data = response.xpath("//script[contains(text(), 'window.ApolloCacheState =')]/text()").get()

        raw_data = re.search(
            pattern=r'window\._NEW_CATALOG_UI_SSR\s*=\s*.*?window\.ApolloCacheState\s*=\s*({.*?});',
            string=script_data,
            flags=re.DOTALL
        )

        if raw_data:
            apollo_data = json.loads(raw_data.group(1))

            root_query = apollo_data.get('ROOT_QUERY', {})

            product_card_data = None
            for key in root_query:
                if key.startswith('product'):
                    product_card_data = root_query[key]
                    break

            if product_card_data:
                description = product_card_data.get('descriptionPlain')
                item['description'] = description

                attributes = product_card_data.get('attributes', [])
                parsed_attributes = []

                for attr in attributes:
                    name = attr.get('name')
                    values = attr.get('values', [])

                    for value_obj in values:
                        value = value_obj.get('value')
                        if name and value:
                            parsed_attributes.append({
                                'name': name,
                                'value': value
                            })

                item['attributes'] = parsed_attributes if parsed_attributes else None
            else:
                item['description'] = None
                item['attributes'] = None

        return item
