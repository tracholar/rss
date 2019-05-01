#coding:utf-8
from flask import Flask
from flask import render_template
from flask import request, make_response, url_for, redirect, Markup
import mysql.connector
import json
import time
from urllib import quote

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="123456",
    database="rss"
)

@app.template_filter('url_domain')
def url_domain(url):
    from urlparse import urlparse
    obj = urlparse(url)
    return obj.netloc

@app.route("/hello")
def hello():
    return "Hello World!"



from lxml import etree
from StringIO import StringIO
import re

def safe_int(x):
    if type(x) is str:
        if x == '':
            return 0
        return int(x)
    return int(x)

@app.route("/")
def index():
    c = db.cursor(dictionary=True)
    offset = safe_int(request.args.get('offset', 0))
    c.execute("select * from article order by `date` desc limit " + str(offset) + ",10")
    articles = c.fetchall()
    for article in articles:
        article['body'] = Markup(article['body'])

    args = {
        "articles" : articles,
        "next_offset" : offset+10,
        "prev_offset" : max(0, offset - 10)
    }
    return render_template('index.html', **args)


@app.route("/article/<int:article_id>")
def article(article_id):
    c = db.cursor(dictionary=True)
    c.execute("select * from article where id=" + str(article_id))
    articles = c.fetchall()
    for article in articles:
        article['body'] = Markup(article['body'])

    args = {
        "articles" : articles
    }
    return render_template('index.html', **args)

@app.route("/event/<string:evt_name>/<int:article_id>")
def event(evt_name, article_id):
    if evt_name not in ('show', 'click', 'like', 'hate'):
        ret = {'status' : 300, 'msg' : 'unknow event name ' + evt_name}
        resp = make_response(json.dumps(ret))
        resp.headers['Content-Type'] = 'application/json'
        return resp

    evt_attr = {
        'article_id' : article_id
    }
    c = db.cursor()
    c.execute("INSERT INTO article_event (name, time, evt_attr) VALUES (%s, %s, %s)",
              (evt_name, int(time.time()),  json.dumps(evt_attr)))
    db.commit()

    ret = {'status' : 200}
    resp = make_response(json.dumps(ret))
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route("/jump")
def jump():
    url = request.args.get('url', "")
    return redirect(url)

@app.route("/src")
def src():
    """获取站外资源"""
    import requests as rq
    from urlparse import urljoin

    refer = request.args.get('refer', "")
    url = request.args.get('url', "")
    if not url.startswith('http'):
        url = urljoin(refer, url)
    headers = {
        'user-agent' : "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        'Referer' : refer
    }
    r = rq.get(url, headers=headers, stream = True)
    resp = make_response(r.raw.data)
    for h in r.headers:
        resp.headers.set(h, r.headers[h])
    return resp

if __name__ == '__main__':
    app.run()