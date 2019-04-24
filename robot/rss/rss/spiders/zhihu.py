import scrapy

class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ["zhihu.com"]
    start_urls = [
        "https://www.zhihu.com/explore/recommendations"
    ]

    def parse(self, resp):
        for sel in response.xpath('//ul/li'):
            title = sel.xpath('a/text()').extract()
            link = sel.xpath('a/@href').extract()
            desc = sel.xpath('text()').extract()
            print title, link, desc