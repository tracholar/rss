#coding:utf-8
from flask import Flask
from flask import render_template
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="123456",
    database="rss"
)

@app.route("/hello")
def hello():
    return "Hello World!"



from lxml import etree
from StringIO import StringIO
@app.route("/")
def index():
    c = db.cursor(dictionary=True)
    c.execute("select * from rss order by rand() limit 100")
    articles = c.fetchall()
    parser = etree.HTMLParser()
    for article in articles:
        if article['desc'] is None or len(article['desc'])<1:
            html = etree.parse(StringIO(article['body']), parser=parser)
            article['desc'] = etree.tostring(html, encoding='unicode', method='text')
    return render_template('index.html', articles=articles)


if __name__ == '__main__':
    app.run()