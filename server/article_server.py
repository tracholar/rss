#coding:utf-8
from flask import Flask
from flask import render_template
from flask import request, make_response, url_for, redirect, Markup
from html_analysis import extract_main_content
import mysql.connector
import json
import time
from urllib import quote

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
import re

@app.route("/")
def index():
    c = db.cursor(dictionary=True)
    offset = int(request.args.get('offset', 0))
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

if __name__ == '__main__':
    app.run()