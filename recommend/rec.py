#coding:utf-8
"""计算推荐得分"""
import sys

from conf.conf import mysql_conf
import mysql.connector
from feat import gen_feat
from train import predict
import datetime, time

def calc_rec_score(all = False):
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    if all:
        c.execute("SELECT * from article")
    else:
        c.execute("SELECT * from article where score = 0 or score is null")

    for row in c.fetchall():
        data = [gen_feat(row)]
        score = predict(data)[0]
        aid = row['id']
        c.execute("UPDATE article SET score = %s where id = %s", (float(score), aid))
        print '>>>', row['title'], ' score=', score

    db.commit()
    db.close()

def gen_rec_article_list(top = 50):
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    c.execute("SELECT * FROM article where score > 0.1 AND left(date, 10) = '{}' ".format(time.strftime('%Y-%m-%d', time.localtime())))
    articles = c.fetchall()
    articles.sort(key=lambda x : x['score'], reverse=True)

    from urlparse import urlparse, urljoin, urlsplit
    for article in articles:
        netloc = urlparse(article['link']).netloc
        article['body'] = article['body'].replace('src="/', 'src=' + netloc + '/')\
                                        .replace('href="/', 'href="' + netloc + '/')

    import jieba.analyse
    from sklearn.feature_extraction.text import TfidfVectorizer
    from analysis.html_analysis import html_to_element, element_to_text
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    corpus = [element_to_text(html_to_element(a['body'])) for a in articles]
    corpus = [' '.join(jieba.cut(s)) for s in corpus]
    clf = TfidfVectorizer()
    X = clf.fit_transform(corpus)

    rec_list = []
    for i in range(X.shape[0]):
        if len(rec_list) == 0:
            rec_list.append(i)
            continue
        similar = np.max(cosine_similarity(X[rec_list], X[i]) )
        if similar < 0.05:
            rec_list.append(i)
            continue

    db.close()

    return [articles[i] for i in rec_list[:top]]





if __name__ == '__main__':
    calc_rec_score()

    import json
    fp = open("rec.json", 'w')
    data = {
        'updateTime' : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'articles' : gen_rec_article_list()
    }
    fp.write(json.dumps(data, encoding='utf-8'))
    fp.close()
