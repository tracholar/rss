#coding:utf-8

from lxml import etree
from StringIO import StringIO
import numpy as np
import re
import logging
import jieba

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
    info = [(i.tag, len(element_to_text(i).replace(' ', ''))) for i in e.findall('.//a')]
    text_n = len(element_to_text(e).replace(' ', ''))
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
def extract_img_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower()=='img'])
def extract_form_elem_number(e):
    return len([b for b in e.iter() if type(b.tag) is str and b.tag.lower() in ('form', 'input', 'textarea')])

def extract_element_maxtextlen(e):
    arr = re.findall(r'<.+?>([^<>]+?)</.+?>', element_to_html(e), re.S|re.U|re.M)
    return max([0] + [len(x.replace(' ', '')) for x in arr])

def extract_none_number(e):
    return len(re.findall(r'none|hidden|hide', element_to_html(e)))
def extract_side_number(e):
    return len(re.findall(r'left|right|side', element_to_html(e)))
def extract_main_number(e):
    return len(re.findall(r'main|body|content', element_to_html(e)))

def extract_child_div_number(e):
    return len(e.findall('./div')) + len(e.findall('./section')) + len(e.findall('./article'))
def extract_child_p_number(e):
    return len(e.findall('./p')) + len(e.findall('./blockquote'))
def extract_nv_number(e):
    return len(re.findall(r'nav', element_to_html(e)))
def extract_li_number(e):
    return len(e.findall('.//li')) + len(e.findall('.//ol'))

def extract_li_a_number(e):
    return len([n for n in e.findall('.//li') if n.find('.//a') is not None]) + len([n for n in e.findall('.//ol') if n.find('.//a') is not None])
def extract_h1_number(e):
    return len(e.findall('.//h1'))
def extract_dom_depth(e):
    return max([0] + [extract_dom_depth(n) + 1 for n in e.findall('./*')])
def extract_depth_to_p(e):
    if hasattr(e, 'tag') and e.tag in ('p','P', 'blockquote'):
        return 0
    return min([20] + [extract_depth_to_p(n) + 1 for n in e.findall('./*')])

def extract_all_tags(e):
    tags = set(n.tag for n in e.iter() if hasattr(e, 'tag') and n.tag is not None)
    return list(tags)

def extract_feat(T):
    f_text_n = extract_text_number(T)
    f_p_n = extract_p_number(T)
    f_tag_n = extract_tag_number(T)
    f_h_n = extract_h_number(T)
    f_link_density = extract_link_density(T)
    f_np_n = extract_np_number(T)
    return f_text_n, f_p_n, f_tag_n, f_h_n, f_link_density, f_np_n

def extract_feat_v2(T):
    if type(T) is unicode or type(T) is str:
        T = html_to_element(T)

    feat = {
        'f_text_n' : extract_text_number(T),
        'f_p_n' : extract_p_number(T),
        'f_tag_n' : extract_tag_number(T),
        'f_h_n' : extract_h_number(T),
        'f_link_density' : extract_link_density(T),
        'f_np_n' : extract_np_number(T),
        'f_img_n' : extract_img_number(T),
        'f_a_n' : extract_a_number(T),
        'f_form_element_n' : extract_form_elem_number(T),
        'f_element_maxtextlen' : extract_element_maxtextlen(T),
        'f_none_n' : extract_none_number(T),
        'f_side_n' : extract_side_number(T),
        'f_main_n' : extract_main_number(T),
        'f_child_div_n' : extract_child_div_number(T),
        'f_child_p_n' : extract_child_p_number(T),
        'f_nav_n' : extract_nv_number(T),
        'f_li_n' : extract_li_number(T),
        'f_li_a_n' : extract_li_a_number(T),
        'f_h1_n' : extract_h1_number(T),
        'f_dom_depth' : extract_dom_depth(T),
        'f_depth_to_p' : extract_depth_to_p(T),
        'f_all_tags' : extract_all_tags(T),
    }

    return feat

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

def remove_sample(i):
    import mysql.connector
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="123456",
        database="rss"
    )
    try:
        c = db.cursor()
        c.execute('delete from main_content_feat where id = %s', (i, ))
        db.commit()
    finally:
        db.close()

def ihash(s, m = 10**4):
    import hashlib
    digest = hashlib.md5(s).hexdigest()
    return int(digest, 16) % m

import copy
def feat_preprocess(feats):
    from math import log1p, log
    feats = copy.deepcopy(feats)
    for feat in feats:
        for f in ['f_p_n', 'f_tag_n', 'f_h_n', 'f_np_n', 'f_text_n', 'f_img_n' ,'f_a_n', 'f_form_element_n', 'f_element_maxtextlen' , 'f_none_n', 'f_side_n', 'f_main_n', 'f_child_div_n', 'f_child_p_n', 'f_nav_n', 'f_li_n', 'f_li_a_n', 'f_h1_n', 'f_dom_depth', 'f_depth_to_p']:
            if f in feat and feat[f] is not None:
                feat[f] = log1p(feat[f])
        if 'f_link_density' in feat:
            feat['f_link_density'] = log(1e-4 + feat['f_link_density'])
    from scipy.sparse import csr_matrix
    from math import log
    d = []
    row_ind = []
    col_ind = []
    # dense 最多1000维
    sparse_offset = 1000
    n_col = 10**4
    for i, f in enumerate(feats):

        ## dense feature
        for j, col in enumerate(['f_p_n', 'f_tag_n', 'f_h_n', 'f_np_n', 'f_text_n', 'f_img_n' ,'f_a_n', 'f_form_element_n', 'f_element_maxtextlen', 'f_none_n', 'f_side_n', 'f_main_n', 'f_child_div_n', 'f_child_p_n', 'f_link_density', 'f_nav_n', 'f_li_n', 'f_li_a_n', 'f_h1_n', 'f_dom_depth', 'f_depth_to_p']):
            if col in f:
                # dense
                d.append(f[col])
                row_ind.append(i)
                col_ind.append(j)

                # sparse
                v = int(f[col] * 3)
                idx = ihash(col + ':' + str(v), n_col - sparse_offset) + sparse_offset
                d.append(1.0)
                row_ind.append(i)
                col_ind.append(idx)

        ## sparse feature
        for col in ['f_all_tags']:
            if col in f:
                if type(f[col]) in (set, list):
                    for v in f[col]:
                        idx = ihash(col + ':' + str(v), n_col - sparse_offset) + sparse_offset
                        d.append(1.0)
                        row_ind.append(i)
                        col_ind.append(idx)
                else:
                    idx = ihash(col + ':' + str(f[col]), n_col - sparse_offset) + sparse_offset
                    d.append(1.0)
                    row_ind.append(i)
                    col_ind.append(idx)


    df = csr_matrix((d, (row_ind, col_ind)), shape=(len(feats), n_col))
    if len(feats) >0 and 'y' in feats[0]:
        y = [f['y'] for f in feats]
        return df, y
    return df
def array_index(arr, idx):
    return [arr[i] for i in idx]

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
        c.execute("select y, body from main_content_feat")
        feats = c.fetchall()
        df = [extract_feat_v2(feat['body']) for feat in feats]
        y = [feat['y'] for feat in feats]
        from sklearn.svm import LinearSVC

        df = feat_preprocess(df)
        clf = LinearSVC(C=0.05, verbose=True, penalty='l1', dual=False, max_iter=50000)
        clf.fit(df, y)
        print '#sample', len(y)
        print 'clf', clf.coef_
        print 'score', clf.score(df, y)
        print 'w:', [(i, int(w*1e3)/1000.0) for i,w in enumerate(clf.coef_[0]) if abs(w)>0]
        import pickle
        fp = open('model.bin', 'wb')
        pickle.dump(clf, fp)
        fp.close()
    finally:
        db.close()

import pickle

def get_clf():
    try:
        from os.path import dirname
        fp = open(dirname(__file__) + '/model.bin', 'rb')
        clf = pickle.load(fp)
        fp.close()
        return clf
    except Exception as e:
        raise e

clf = get_clf()
def predict(T):
    if type(T) is str or type(T) is unicode:
        parser = etree.HTMLParser()
        T = etree.parse(StringIO(T), parser)

    feat = extract_feat_v2(T)
    df = feat_preprocess([feat])
    return clf.decision_function(df)[0]

def filter_script_css(html):
    html = re.sub(r'<(script|style|embed|object).*?>.*?</(script|style|embed|object)>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)
    html = re.sub(r'</?body.*?>', '', html, flags=re.MULTILINE|re.IGNORECASE|re.UNICODE|re.S)
    return html

def extract_main_content(html):
    html = filter_script_css(html)

    parser = etree.HTMLParser()
    T = etree.parse(StringIO(html), parser)
    blocks = [b for b in T.iter() if b.tag in ('div', 'section', 'article')]
    blocks = [b for b in blocks if len(element_to_text(b))>100] # 过滤内容太少的block
    if len(blocks) == 0:
        return ''

    score = [predict(b) for b in blocks]
    if np.max(score) < -0.1:
        return ''
    return element_to_html(blocks[np.argmax(score)])

if __name__ == '__main__':
    from urllib2 import urlopen

    data = urlopen('https://arxiv.org/abs/1703.04782').read()

    T = extract_main_content(data)
    fp = open('content.html', 'w')
    fp.write(T)
    fp.close()
    print T
