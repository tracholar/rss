#coding:utf-8

from lxml import etree
from StringIO import StringIO
import numpy as np
import re

def element_to_html(e):
    return etree.tostring(e, encoding='utf-8', method="html", pretty_print=True)

def element_to_text(e):
    return etree.tostring(e, encoding='utf-8', method="text")

def extract_link_density(e):
    info = [(i.tag, len(element_to_text(i))) for i in e.iter()]
    return 1.0 * sum(b[1] for b in info if b[0] in ('a', 'A')) / sum(b[1] for b in info)


def extract_p_number(e):
    return len([b for b in e.iter() if b.tag in ('p', 'P')])
def extract_np_number(e):
    return len([b for b in e.iter() if b.tag not in ('p', 'P', 'h1', 'h2', 'h3', 'h4', 'h5', 'blockquote', 'span', 'div', 'table', 'tr', 'td', 'th', 'img')])

def extract_text_number(e):
    return len(element_to_text(e))

def extract_main_content(html):
    html = re.sub(r'<(script|style).*?>.*?</(script|style)>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)
    html = re.sub(r'</?body.*?>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)

    parser = etree.HTMLParser()
    T = etree.parse(StringIO(html), parser)
    blocks = [b for b in T.iter() if b.tag in ('div', 'section')]
    blocks = [b for b in blocks if len(element_to_text(b))>100] # 过滤内容太少的block
    if len(blocks) == 0:
        return ''

    link_density = [extract_link_density(e) for e in blocks]
    p_number = [extract_p_number(e) for e in blocks]
    text_number = [extract_text_number(e) for e in blocks]
    np_number = [extract_np_number(e) for e in blocks]

    score = []
    for v1, v2, v3, v4 in zip(link_density, p_number, text_number, np_number):
        s = 0
        if v1 > 0.1:
            s += -100

        s += -20.0 * v1 + v2 + v3/100.0 - v4
        score.append(s)
    return element_to_html(blocks[np.argmax(score)])

if __name__ == '__main__':
    from urllib2 import urlopen

    data = urlopen('http://news.ustc.edu.cn/2019/0430/c8091a379907/page.htm').read()

    T = extract_main_content(data)
    fp = open('content.html', 'w')
    fp.write(T)
    fp.close()
    print T