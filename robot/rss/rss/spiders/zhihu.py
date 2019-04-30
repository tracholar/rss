#coding:utf-8
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import  CrawlSpider
from rss.items import RssItem
from urlparse import urljoin

class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'

    # 必须是列表
    rules = { "arxiv.org" : r'/abs/' }

    allowed_domains = ["zhihu.com",
                       "news.ustc.edu.cn", "bbs.ustc.edu.cn",
                       "www.jiqizhixin.com",
                       "deepmind.com", "new.qq.com",
                       "leiphone.com", "ai.yanxishe.com",
                       "wallstreetcn.com",
                       "tech.meituan.com",
                       "technologyreview.com"]

    start_urls = [
        "https://www.zhihu.com/explore/recommendations",
        "http://news.ustc.edu.cn/",
        "https://www.jiqizhixin.com/",
        "https://deepmind.com/blog/",
        "https://new.qq.com/ch/tech/",
        "https://new.qq.com/ch/finance/",
        "https://new.qq.com/d/bj",
        "https://new.qq.com/d/hn",
        "https://new.qq.com/d/zj",
        "http://bbs.ustc.edu.cn/cgi/bbsdoc?board=Notice",
        "https://www.leiphone.com/",
        "https://ai.yanxishe.com/",
        "https://wallstreetcn.com/news/global",
        "https://wallstreetcn.com/news/economy",
        "https://wallstreetcn.com/news/charts",
        "https://wallstreetcn.com/news/china",
        "https://wallstreetcn.com/news/us",
        "https://wallstreetcn.com/news/shares",
        "https://tech.meituan.com/",
        "https://daily.zhihu.com/",
        "https://www.technologyreview.com/",
        "https://arxiv.org/list/cs.AI/recent"
    ]

    def parse(self, resp):

        for r in self.rules:
            urls = r.link_extractor.extract_links(resp)
            for url in urls:
                yield scrapy.Request(url.url, self.parse_body)

    def take_one(self, list_like):
        if type(list_like) is list:
            if len(list_like) == 0:
                return ''
            return list_like[0]
        return list_like
    def parse_body(self, resp):
        item = RssItem()


        item['title'] = self.take_one(resp.xpath('/html/head/title/text()').extract())
        item['link'] = resp.url
        item['desc'] = self.take_one(resp.xpath('/html/head/meta[@name="description"]/@content').extract())
        item['body'] = str(self.take_one(resp.xpath('/html/body').extract()).encode('utf-8'))
        yield item
