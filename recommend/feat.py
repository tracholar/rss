# coding:utf-8
import sys
from conf.conf import mysql_conf
import mysql.connector
from readability import Document
from lxml import etree
from StringIO import StringIO
from jieba import analyse
from analysis.html_analysis import element_to_text, html_to_element
import time


class FeatureProvider(object):
    def __init__(self):
        pass




def url_domain(url):
    from urlparse import urlparse
    obj = urlparse(url)
    return obj.netloc


def utf8_en(data):
    if type(data) is unicode:
        return data.encode('utf-8')
    data = str(data)
    return data.encode('utf-8')


def gen_feat(row):
    body = element_to_text(row['body'])
    feat = {}
    feat['f_site'] = url_domain(row['link'])
    feat['f_title_keywords'] = ','.join(utf8_en(t).lower() for t in analyse.extract_tags(row['title']))
    feat['f_content_keywords'] = ','.join(utf8_en(t).lower() for t in analyse.extract_tags(body, topK=200))
    feat['f_date'] = row['date']
    feat['f_content_len'] = len(body)
    feat['f_img_n'] = sum(1 for n in html_to_element(row['body']).iter() if n.tag in ('img', 'IMG'))
    return feat


def get_user_current_feat():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    now = int(time.time())
    sql = """
        SELECT json_extract(a.evt_attr, '$.article_id') AS ids
        FROM article_event
        WHERE time > {} AND name in ('like', 'hate')
    """.format(now - 3600 * 48)
    c.execute(sql)
    ids = []
    for row in c.fetchall():
        ids.extend([int(i) for i in row['ids'].split(',')])
    ids = list(set(ids))
    sql = """
        SELECT title,body FROM article
        WHERE id in ({})
    """.format(','.join(ids))
    c.execute(sql)
    title_kw = []
    content_kw = []
    for row in c.fetchall():
        body = element_to_text(row['body'])
        title_kw.extend(utf8_en(t).lower() for t in analyse.extract_tags(row['title']))
        content_kw.extend(utf8_en(t).lower() for t in analyse.extract_tags(body, topK=200))
    title_kw = list(set(title_kw))
    content_kw = list(set(content_kw))
    c.close()
    db.close()

    return {
        'title_kw': ','.join(title_kw),
        'content_kw': ','.join(content_kw)
    }


def iter_data():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    # c.execute("delete from article_feat")
    # db.commit()

    sql = """
            SELECT  b.id,
                    if(name='like', 1, -1) as y,
                    b.link,
                    b.title,
                    b.body,
                    b.date
            FROM article_event a
            JOIN article b
            ON cast(json_extract(a.evt_attr, '$.article_id') as SIGNED)=b.id
            WHERE a.name IN ('like', 'hate') AND b.id not in (
                select id from article_feat
            )
        """
    c.execute(sql)
    for row in c.fetchall():
        feat = gen_feat(row)
        y = row['y']
        aid = row['id']

        c.execute("""INSERT INTO article_feat (id, y, f_site, f_title_keywords, f_content_keywords, f_date, f_content_len, f_img_n)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (aid, y, feat['f_site'], feat['f_title_keywords'],
                   feat['f_content_keywords'], feat['f_date'],
                   feat['f_content_len'], feat['f_img_n']))
        print '>>>', aid, '>>>', row['title']
    db.commit()
    db.close()


if __name__ == '__main__':
    iter_data()
