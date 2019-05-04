#coding:utf-8

from lxml import etree
from StringIO import StringIO
import numpy as np
import re
import logging

def html_to_element(html):
    parser = etree.HTMLParser()
    T = etree.parse(StringIO(html), parser)
    return T
def element_to_html(e):
    if type(e) is str or type(e) is unicode:
        e =  html_to_element(e)
    return etree.tostring(e, encoding='utf-8', method="html", pretty_print=True)

def element_to_text(e):
    if type(e) is str or type(e) is unicode:
        e =  html_to_element(e)
    return etree.tostring(e, encoding='utf-8', method="text")

def extract_link_density(e):
    info = [(i.tag, len(element_to_text(i))) for i in e.iter() if type(i.tag) is str]
    text_n = sum(b[1] for b in info)
    if text_n == 0:
        return 0
    return 1.0 * sum(b[1] for b in info if b[0].lower() in ('a')) / text_n

def extract_tag_number(e):
    return len(list(e.iter()))
def extract_p_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower() in ('p', 'blockquote')])
def extract_np_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower() not in ('p', 'P', 'h1', 'h2', 'h3', 'h4', 'h5', 'blockquote', 'span', 'div', 'table', 'tr', 'td', 'th', 'img', 'br')])
def extract_a_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower() in ('a')])

def extract_text_number(e):
    return len(element_to_text(e))

def extract_h_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower() in ('h1', 'h2', 'h3', 'h4', 'h5')])

def extract_feat(T):
    f_text_n = extract_text_number(T)
    f_p_n = extract_p_number(T)
    f_tag_n = extract_tag_number(T)
    f_h_n = extract_h_number(T)
    f_link_density = extract_link_density(T)
    f_np_n = extract_np_number(T)
    return f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n

def add_sample(html, y):
    parser = etree.HTMLParser()
    T = etree.parse(StringIO(html), parser)
    f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n = extract_feat(T)
    import mysql.connector
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="123456",
        database="rss"
    )
    try:
        c = db.cursor()
        data = (html, f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n, y)
        c.execute('INSERT INTO main_content_feat (body, f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n, y ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', data)
        db.commit()
    finally:
        db.close()

def feat_preprocess(feats):
    from math import log1p, log
    for feat in feats:
        for f in ['f_p_n', 'f_tag_n', 'f_h_n', 'f_np_n', 'f_text_n']:
            if f in feat and feat[f] is not None:
                feat[f] = log1p(feat[f])
        if 'f_link_density' in feat:
            feat['f_link_density'] = log(1e-4 + feat['f_link_density'])
    import pandas as pd
    df = pd.DataFrame({
        'f_p_n' : [f['f_p_n'] for f in feats],
        'f_tag_n' : [f['f_tag_n'] for f in feats],
        'f_h_n' : [f['f_h_n'] for f in feats],
        'f_np_n' : [f['f_np_n'] for f in feats],
        'f_text_n' : [f['f_text_n'] for f in feats],
        'f_link_density' : [f['f_link_density'] for f in feats],
    })
    if len(feats) >0 and 'y' in feats[0]:
        y = [f['y'] for f in feats]
        return df, y
    return df

def train_model():
    import mysql.connector
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="123456",
        database="rss"
    )
    c = db.cursor(dictionary=True)
    try:
        c.execute("select * from main_content_feat")
        feats = c.fetchall()
        df, y = feat_preprocess(feats)
        from sklearn.svm import LinearSVC
        clf = LinearSVC(C=1.0)
        clf.fit(df, y)
        print 'clf', clf.coef_
        print 'score', clf.score(df, y)
        import pickle
        fp = open('model.bin', 'wb')
        pickle.dump(clf, fp)
        fp.close()
    finally:
        db.close()

import pickle
try:
    fp = open('../analysis/model.bin', 'rb')
    clf = pickle.load(fp)
    fp.close()
except Exception:
    pass

def predict(T):
    if type(T) is str:
        parser = etree.HTMLParser()
        T = etree.parse(StringIO(T), parser)

    f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n = extract_feat(T)
    feat = {
        'f_text_n' : f_text_n,
        'f_p_n' : f_p_n,
        'f_tag_n' : f_tag_n,
        'f_h_n' : f_h_n,
        'f_link_density' : f_link_density,
        'f_np_n' : f_np_n
    }
    df = feat_preprocess([feat])
    return clf.decision_function(df)[0]

def extract_main_content(html):
    html = re.sub(r'<(script|style).*?>.*?</(script|style)>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)
    html = re.sub(r'</?body.*?>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)

    parser = etree.HTMLParser()
    T = etree.parse(StringIO(html), parser)
    blocks = [b for b in T.iter() if b.tag in ('div', 'section', 'article')]
    blocks = [b for b in blocks if len(element_to_text(b))>100] # 过滤内容太少的block
    if len(blocks) == 0:
        return ''

    score = [predict(b) for b in blocks]
    return element_to_html(blocks[np.argmax(score)])

if __name__ == '__main__':
    from urllib2 import urlopen

    data = urlopen('https://arxiv.org/abs/1703.04782').read()

    T = extract_main_content(data)
    fp = open('content.html', 'w')
    fp.write(T)
    fp.close()
    print T