#coding:utf-8
import sys
sys.path.append('../analysis')
from flask import Flask
from flask import render_template
from flask import request, make_response, url_for, redirect, Markup
import mysql.connector
import MySQLdb
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
    db.close()
    db.reconnect()

    c = db.cursor(dictionary=True)
    offset = safe_int(request.args.get('offset', 0))
    where = []
    if 'site' in request.args:
        site = MySQLdb.escape_string(request.args.get('site'))
        where.append("link like '%{0}%'".format(site))
    if len(where) > 0:
        where = ' where ' + ' AND '.join(where)
    else:
        where = ''

    c.execute("select * from article " + where + " order by `date` desc limit " + str(offset) + ",10")
    articles = c.fetchall()
    for article in articles:
        article['body'] = Markup(article['body'])

    url_args = {}
    for k in request.args:
        if k != 'offset':
            url_args[k] = request.args[k]
    args = {
        "articles" : articles,
        "next_link" : url_for('index', offset=offset+10, **url_args),
        "prev_link" : url_for('index', offset=max(0, offset - 10), **url_args)
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
    try:
        r = rq.get(url, headers=headers, stream = True)
        resp = make_response(r.raw.data)
        for h in r.headers:
            resp.headers.set(h, r.headers[h])
        return resp
    except Exception:
        return make_response('')

@app.route('/main_content_sample', methods=['POST'])
def main_content_sample():
    html = request.form.get('html')
    y = int(request.form.get('y'))
    if y > 0:
        y = 1
    else:
        y = -1

    from html_analysis import add_sample
    add_sample(html, y)
    return make_response('')



@app.route('/tag_main_content')
def tag_main_content():
    if 'id' in request.args:
        where = ' where id = ' + str(safe_int(request.args.get('id')))
    else:
        where = ' order by rand() '
    c = db.cursor(dictionary=True)
    c.execute("select * from rss " + where + " limit 1")
    article = c.fetchone()
    from html_analysis import predict, element_to_html
    parser = etree.HTMLParser()
    T = etree.parse(StringIO(article['body']), parser)
    score = [(n,predict(n)) for n in T.iter() if type(n.tag) is str and n.tag.lower() in ('div', 'section', 'article')]
    score.sort(key=lambda x: x[1], reverse=True)
    articles = [{'body' : Markup(element_to_html(n), encoding='utf-8'), 'title': article['title'], 'link' : article['link'], 'date' : article['date'], 'extra' : 'score:' + str(v)} for n,v in score]
    #print articles
    return render_template('index.html', articles=articles)

if __name__ == '__main__':
    app.run(threaded=True)