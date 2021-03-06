#coding:utf-8
import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import  CrawlSpider
from rss.items import RssItem
from urlparse import urljoin
import json


class ZhiHuSpider(scrapy.Spider):
    name = 'zhihu'

    # 必须是列表
    rules = {
        "arxiv.org" : [r'/abs/'],
        "www.solidot.org" : [r'/story'],
        "www.leiphone.com" : [r'/news', r'/latest'],
        "www.nature.com" : [r'/articles/'],
        "vip.stock.finance.sina.com.cn": [r'/q/go.php/vReport_Show/'],
        "www.infoq.cn" : [r'/article/'],
        "36kr.com" : [r'/p/'],
        "cnbeta.com" : [r'/articles/'],
        "www.e0734.com" : [r'/html/2'],
        "hn.rednet.cn" : [r'/content/2'],
        "cn.investing.com" : [r'/news/'],
        "zhuanlan.zhihu.com" : [r'/p/'],
        "www.jiqizhixin.com" : [r'/articles/']
    }

    allowed_domains = ["zhihu.com",
                       "news.ustc.edu.cn", "bbs.ustc.edu.cn",
                       "www.jiqizhixin.com",
                       "deepmind.com", "new.qq.com",
                       "leiphone.com", "ai.yanxishe.com",
                       "wallstreetcn.com",
                       "tech.meituan.com",
                       "technologyreview.com",
                       "arxiv.org",
                       "www.nature.com",
                       "www.solidot.org",
                       "vip.stock.finance.sina.com.cn",
                       "www.infoq.cn",
                       "36kr.com",
                       "cnbeta.com",
                       "www.e0734.com", "hn.rednet.cn",
                       "cn.investing.com",
                       ]

    start_urls = [
        "https://www.zhihu.com/explore/recommendations",
        "http://news.ustc.edu.cn/",
        "https://www.jiqizhixin.com/",
        "https://deepmind.com/blog/",
        "https://new.qq.com/ch/tech/",
        "https://new.qq.com/ch/finance/", "https://new.qq.com/ch/world/",
        "https://new.qq.com/d/bj", "https://news.qq.com/",
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
        "https://arxiv.org/list/cs.AI/recent", "https://arxiv.org/list/cs.CV/recent", "https://arxiv.org/list/cs.LG/recent",
        "https://www.solidot.org/",
        "https://www.nature.com/news",
        "http://vip.stock.finance.sina.com.cn/q/go.php/vReport_List/kind/industry/index.phtml",
        "https://www.infoq.cn/",
        "https://36kr.com/",
        "https://www.cnbeta.com/",
        "http://www.e0734.com/",
        "https://hn.rednet.cn/",
        "https://cn.investing.com/news/", "https://cn.investing.com/news/latest-news",
        "https://www.jiqizhixin.com/columns/paperweekly",
    ]

    def match_url(self, url):
        from urlparse import urlparse
        o = urlparse(url)
        for d in self.rules:
            if len(o.netloc) >= len(d) and o.netloc.rfind(d) >= 0:
                for r in self.rules[d]:
                    if o.path.startswith(r):
                        return True
                    else:
                        return False

        return True
    def parse(self, resp):
        ctx_type = resp.headers.get('Content-Type')
        if ctx_type is None:
            return
        ctx_type = ctx_type.lower()
        urls = []
        if ctx_type == 'application/json':
            data = resp.content
            urls = re.findall(r'https?://[^"\'><]', data, re.S|re.M|re.U|re.I)
        elif re.match(r'^image', ctx_type):
            return
        else:
            for sel in resp.xpath('//a'):
                urls += sel.xpath('@href').extract()

        for url in urls:
            url = urljoin(resp.url, url)
            if self.match_url(url):
                yield scrapy.Request(url, self.parse_body)

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
