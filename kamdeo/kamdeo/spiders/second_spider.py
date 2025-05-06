import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from openpyxl import Workbook


class SecondSpiderSpider(CrawlSpider):
    name = "second_spider"
    allowed_domains = ["kamdeo.ru"]
    start_urls = ["https://kamdeo.ru/shop/"]

    def __init__(self, *args, **kwargs):
        super(SecondSpiderSpider, self).__init__(*args, **kwargs)
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(['URL', 'Category', 'Name', 'Price', 'Weight', 'Article', 'Maker', 'Applicability'])

    rules = (Rule(LinkExtractor(
                restrict_xpaths='//div[contains(@class, "shop-item")]//a[contains(@href, "product")]',
                allow_domains=["kamdeo.ru"]), callback="parse_item", follow=True),
             Rule(LinkExtractor(
                restrict_xpaths='//div[@class="pagination kamdeo-pagination"]//a[@class="page-numbers"]'),
                follow=True),)

    def parse_item(self, response):
        item = {}
        item["url"] = response.url
        category_path = response.xpath('.//div[@class="breadcrumb-prod col-md-12"]//text()').getall()
        item['category'] = ' '.join(category_path).strip()
        name_text = response.xpath('.//div[@class="col-md-6 title-item"]/h1/text()').get().strip()
        item["name"] = ' '.join(name_text.split())
        price_text = response.xpath('.//div[@class="prop-item"]/div[@class="price-item"]'
                                    '/div[@class="prop"]/text()').get().strip()
        cleaned_price = ''.join(e for e in price_text.strip() if e.isdigit())
        item["price"] = int(cleaned_price)
        weight_text = response.xpath('.//div[@class="prop-item"]//div[@class="prop"]'
                                     '[contains(./b/text(), "Вес")]/text()').get()
        cleaned_weight = weight_text.lstrip(":").strip()
        item["weight"] = float(cleaned_weight)
        article_text = response.xpath('.//div[@class="prop-item"]//div[@class="prop"]'
                                      '[contains(./b/text(), "Артикул")]/text()').get()
        item["article"] = article_text.lstrip(":").strip()
        item["maker"] = response.xpath('.//div[@class="chars-item"]//div[@class="title"]'
                                       '[contains(., "Производитель")]/b/text()').get()
        item["applicability"] = response.xpath('.//div[@class="chars-item"]//div[@class="value"]'
                                               '[contains(., "Применимость")]/b/text()').get()

        self.ws.append([
            item['url'],
            item['category'],
            item['name'],
            item['price'],
            item['weight'],
            item['article'],
            item['maker'],
            item['applicability']
        ])

        return item

    def closed(self, reason):
        self.wb.save('kamdeo_spares.xlsx')
