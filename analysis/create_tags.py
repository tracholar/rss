#coding:utf-8
import sys
from conf.conf import mysql_conf

import mysql.connector
import jieba
import jieba.analyse
from summa import keywords

from html_analysis import html_to_element, element_to_text

def get_text(html):
    return element_to_text(html_to_element(html))

def create_tags():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    c.execute("SELECT id, title, link, body FROM article where id not in (select distinct article_id from article_tags)")
    articles = c.fetchall()
    for article in articles:
        body = get_text(article['body'])
        tags = jieba.analyse.textrank(body, topK=10, allowPOS=('ns', 'n', 'vn'))
        if len(tags) == 0:
            try:
                tags = keywords.keywords(body, words=10, language='english').split()
            except Exception:
                tags = jieba.analyse.extract_tags(body, topK=10)
        aid = article['id']
        data = [(n, aid) for n in tags]
        try:
            c.executemany("INSERT INTO article_tags(name, article_id) VALUES (%s, %s)", data)
            db.commit()
        except Exception as e:
            pass
        print '>>>', article['title'],'>>>', ' '.join(tags)
    c.close()
    db.close()

if __name__ == '__main__':
    create_tags()
