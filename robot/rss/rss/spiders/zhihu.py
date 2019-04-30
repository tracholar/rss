#coding:utf-8
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from rss.items import RssItem
from urlparse import urljoin

class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'

    # 必须是列表
    rules = [
        Rule(LinkExtractor(allow_domains=("arxiv.org"), allow=(r'/abs/'), )),
        Rule(LinkExtractor(allow_domains=("zhihu.com"), allow=(r'/question/'), )),
        Rule(LinkExtractor(allow_domains=("news.ustc.edu.cn", "bbs.ustc.edu.cn"), )),
        Rule(LinkExtractor(allow_domains=("www.jiqizhixin.com"), allow=(r"/articles/"), )),
        Rule(LinkExtractor(allow_domains=("deepmind.com"), allow=(r"/blog/"), )),
        Rule(LinkExtractor(allow_domains=("new.qq.com"), allow=(r"/omn/"), )),
        Rule(LinkExtractor(allow_domains=("leiphone.com", "ai.yanxishe.com"), allow=(r"/news/", r"/page/"), )),
        Rule(LinkExtractor(allow_domains=("wallstreetcn.com"), allow=(r"/articles/"), )),
        Rule(LinkExtractor(allow_domains=("tech.meituan.com"), allow=(r"/\d{4}/"), )),
        Rule(LinkExtractor(allow_domains=("technologyreview.com"), allow=(r"/s/"), )),

    ]
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
        for sel in resp.xpath('//a'):
            urls = sel.xpath('@href').extract()
            for url in urls:
                yield scrapy.Request(urljoin(resp.url, url), self.parse_body)

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
