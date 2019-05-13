#coding:utf-8
import sys
from flask import Flask
from flask import render_template
from flask import request, make_response, url_for, redirect, Markup, g, current_app
from conf.conf import mysql_conf
import mysql.connector
import MySQLdb
import json
import time
from analysis.html_analysis import filter_script_css

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**mysql_conf)
    return g.db

@app.after_request
def close_db(e=None):
    if 'db' in g:
        db = g.pop('db', None)

        if db is not None:
            db.close()
    return e

@app.template_filter('url_domain')
def url_domain(url):
    from urlparse import urlparse
    obj = urlparse(url)
    return obj.netloc

@app.template_filter('float3')
def float3(x):
    if x is None:
        x = -1.0
    return '{:.3f}'.format(float(x))



@app.template_filter('article_tags')
def article_tags(article_id):
    if type(article_id) is not int:
        return ''
    db = get_db()
    c = db.cursor(dictionary=True)
    c.execute("select name from article_tags where article_id = %s", (article_id, ))
    tags = c.fetchall()
    return [tag['name'] for tag in tags]

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
def trace_id():
    from hashlib import md5
    return md5(str(time.time())).hexdigest()[:10] + str(int(time.time()))

@app.route("/")
def index():
    db = get_db()
    c = db.cursor(dictionary=True)
    offset = safe_int(request.args.get('offset', 0))
    rec = safe_int(request.args.get('rec', 0))  # 推荐
    where = []
    if 'site' in request.args:
        site = MySQLdb.escape_string(request.args.get('site'))
        where.append("link like '%{0}%'".format(site))
    if 'like' in request.args:
        where.append("n_like is not null and n_like>0")
    if 'tag' in request.args:
        where.append(" id in (select article_id from article_tags where name='" + MySQLdb.escape_string(request.args.get('tag').encode('utf-8')) + "')")
    if len(where) > 0:
        where = ' where ' + ' AND '.join(where)
    else:
        where = ''
    print(str(where))

    if rec:
        orderby = ' order by IF(rand()<0.2, rand()*3-1.5, IFNULL(score, 0)) desc '
    elif 'orderby' not in request.args:
        orderby = ' order by left(`date`, 10) desc, CAST(IF(rand()<0.1, rand()*3-1.5, IFNULL(score, 0))*3 AS SIGNED) desc, MD5(id) '
    elif 'orderby' in request.args:
        orderby = ' order by ' + request.args['orderby'] + ' '

    c.execute("select * from article " + where + orderby +" limit " + str(offset) + ",10")
    articles = c.fetchall()
    for article in articles:
        article['body'] = Markup(filter_script_css(article['body']))

    url_args = {}
    for k in request.args:
        if k != 'offset':
            url_args[k] = request.args[k]
    args = {
        "articles" : articles,
        "next_link" : url_for('index', offset=offset+10, **url_args),
        "prev_link" : url_for('index', offset=max(0, offset - 10), **url_args)
    }
    resp = make_response( render_template('index.html', **args) )
    resp.set_cookie('_tid', trace_id())
    return resp

@app.route("/article/<int:article_id>")
def article(article_id):
    db = get_db()
    c = db.cursor(dictionary=True)
    c.execute("select * from article where id=" + str(article_id))
    articles = c.fetchall()
    for article in articles:
        article['body'] = Markup(filter_script_css(article['body']))

    args = {
        "articles" : articles
    }
    return render_template('index.html', **args)

@app.route("/event/<string:evt_name>")
def event(evt_name):
    if evt_name not in ('show', 'click', 'like', 'hate'):
        ret = {'status' : 300, 'msg' : 'unknow event name ' + evt_name}
        resp = make_response(json.dumps(ret))
        resp.headers['Content-Type'] = 'application/json'
        return resp

    tid = request.cookies.get('_tid', '')

    evt_attr = {
        '_tid' : tid,
    }
    for k in request.args:
        evt_attr[k] = request.args[k]

    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO article_event (name, time, evt_attr) VALUES (%s, %s, %s)",
              (evt_name, int(time.time()),  json.dumps(evt_attr)))
    db.commit()

    ret = {'status' : 200}
    resp = make_response(json.dumps(ret))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/like/<int:article_id>")
def like(article_id):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE article SET n_like = IFNULL(n_like, 0) + 1 WHERE id = %s",
              (article_id,))
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

    from analysis.html_analysis import add_sample
    add_sample(html, y)
    return make_response('')

@app.route('/main_content_sample/del/<int:id>')
def del_main_content_sample(id):
    from analysis.html_analysis import remove_sample
    remove_sample(id)
    return redirect(url_for('show_main_content_sample'))

@app.route('/main_content_sample/show')
def show_main_content_sample():
    db = get_db()
    c = db.cursor(dictionary=True)
    c.execute("select id, body, y from main_content_feat order by rand() limit 1")
    articles = c.fetchall()

    from analysis.html_analysis import predict, extract_feat_v2
    for article in articles:
        article['score'] = predict(article['body'])
        article['feat'] = str(extract_feat_v2(article['body']))
    return render_template('main_content_sample.html', articles=articles)



@app.route('/tag_main_content')
def tag_main_content():
    db = get_db()
    if 'id' in request.args:
        where = ' where id = ' + str(safe_int(request.args.get('id')))
    else:
        where = ' order by rand() '
    c = db.cursor(dictionary=True)
    c.execute("select * from rss " + where + " limit 1")
    article = c.fetchone()
    from analysis.html_analysis import predict, element_to_html, extract_feat_v2
    parser = etree.HTMLParser()
    T = etree.parse(StringIO(article['body']), parser)
    score = [(n,predict(n), extract_feat_v2(n)) for n in T.iter() if type(n.tag) is str and n.tag.lower() in ('div', 'section', 'article')]
    score.sort(key=lambda x: x[1], reverse=True)
    articles = [{'body' : Markup(filter_script_css(element_to_html(n)), encoding='utf-8'), 'title': article['title'], 'link' : article['link'], 'date' : article['date'], 'extra' : 'score:' + str(v) + '<br/>feat:' + str(f)} for n,v,f in score]
    #print articles
    return render_template('index.html', articles=articles)

@app.route('/daily-rec')
def daily_rec():
    from recommend.rec import gen_rec_article_list
    articles = gen_rec_article_list()
    for article in articles:
        article['body'] = Markup(filter_script_css(article['body']))
    return render_template('index.html', articles=articles)

if __name__ == '__main__':
    app.run(threaded=True)