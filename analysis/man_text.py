#coding:utf-8

import mysql.connector
from readability import Document

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="123456",
    database="rss"
)


c = db.cursor(dictionary=True)
c.execute("select * from rss order by rand() limit 10")
articles = c.fetchall()
for article in articles:
    doc = Document(article['body'])
    print '>>>>[', article['id'], ']', article['title'], '>>>'
    print doc.summary()
