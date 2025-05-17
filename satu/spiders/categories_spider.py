import scrapy

class CategoriesSpiderSpider(scrapy.Spider):
    name = "categories_spider"
    allowed_domains = ["satu.kz"]
    start_urls = ["https://satu.kz"]

    def parse(self, response):
        categories = response.xpath('//ul[@class="nujFR"]/li[@class="YSmsd"]')
        for category in categories:
            yield {
                'category_name': category.xpath('.//span[@class="_3Trjq"]//text()').get().strip(),
                'category_url': response.urljoin(category.xpath('./a[@class="_0cNvO JcwiH"]/@href').get())
            }