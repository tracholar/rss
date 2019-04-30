#coding:utf-8

import mysql.connector
from readability import Document
from html_analysis import extract_main_content, element_to_text
from lxml import etree
from StringIO import StringIO

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="123456",
    database="rss"
)


c = db.cursor(dictionary=True)
c.execute("select * from rss where id not in (select id from article)")
articles = c.fetchall()
for article in articles:
    body = extract_main_content(article['body'])
    parser = etree.HTMLParser()
    T = etree.parse(StringIO(body), parser)
    text = element_to_text(T)
    if text is None or len(text) < 500:
        continue
    c.execute("INSERT INTO article (id, title, link, body, date) VALUES (%s, %s, %s, %s, %s)",
              (article['id'], article['title'], article['link'], body, article['date']))
    print '>>>>', article['title'] , '>>>>'

db.commit()
db.close()
