# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SatuItem(scrapy.Item):
    url = scrapy.Field()
    product_name = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    availability = scrapy.Field()
    discount_price = scrapy.Field()
    original_price = scrapy.Field()
    product_count = scrapy.Field()
    product_rating = scrapy.Field()
    reviews_count = scrapy.Field()
    reviews = scrapy.Field()
    company = scrapy.Field()
    attributes = scrapy.Field()


class CategoriesItem(scrapy.Item):
    alias = scrapy.Field()
    caption = scrapy.Field()
