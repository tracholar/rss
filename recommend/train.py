#coding:utf-8
import sys
from conf.conf import mysql_conf
import mysql.connector
import pandas as pd
from sklearn.linear_model import LogisticRegression, ElasticNet, SGDClassifier
from sklearn.svm import LinearSVC
import pickle
import hashlib
import time
import datetime
from scipy.sparse import csr_matrix
from math import log

def utf8_en(data):
    if type(data) is unicode:
        return data.encode('utf-8')
    if type(data) is str:
        return data
    data = str(data)
    return data.encode('utf-8')
def ihash(s, m = 10**4):
    digest = hashlib.md5(s).hexdigest()
    return int(digest, 16) % m

def feat_to_df(data):
    d = []
    row_ind = []
    col_ind = []
    y = []
    n_row = len(data)
    n_col = 10**4
    if type(data) is dict:
        data = [data]
    elif type(data) is not list:
        raise Exception('wrong data type {}'.format(type(data)))
    for i, row in enumerate(data):
        if 'y' in row:
            y.append(row['y'])
        if 'f_site' in row:
            idx = ihash('f_site:' + row['f_site'], n_col)
            row_ind.append(i)
            col_ind.append(idx)
            d.append(1.0)
        for col in ['f_title_keywords', 'f_content_keywords']:
            if col in row:
                for kw in row[col].split(','):
                    idx = ihash(col + ':' + utf8_en(kw), n_col)
                    row_ind.append(i)
                    col_ind.append(idx)
                    d.append(1.0)
        if 'f_date' in row:
            t = datetime.datetime.strptime(row['f_date'], '%Y-%m-%d %H:%M:%S')
            t = time.mktime(t.timetuple())
            v = int(log(1 + (time.time() - t) / 3600 / 4, 2))
            idx = ihash('f_date:' + str(v), n_col)
            row_ind.append(i)
            col_ind.append(idx)
            d.append(1.0)
        if 'f_content_len' in row:
            v = int(log(1 + row['f_content_len'] / 500, 2))
            idx = ihash('f_content_len:' + str(v), n_col)
            row_ind.append(i)
            col_ind.append(idx)
            d.append(1.0)
        if 'f_img_n' in row:
            v = int(log(1 + row['f_img_n'], 2))
            idx = ihash('f_img_n:' + str(v), n_col)
            row_ind.append(i)
            col_ind.append(idx)
            d.append(1.0)

    X = csr_matrix((d, (row_ind, col_ind)), shape=(n_row, n_col))

    return X, y

def get_data():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    c.execute("select y, f_site, f_title_keywords, f_content_keywords, f_date, f_content_len, f_img_n from article_feat")
    data = c.fetchall()
    db.close()
    X, y = feat_to_df(data)
    return X,y

from os.path import dirname
clf = pickle.load(open(dirname(__file__) + '/like_model.bin', 'rb'))

def predict(data):
    X, _ = feat_to_df(data)
    return clf.decision_function(X)

def train():
    X, y = get_data()
    clf = LinearSVC(penalty='l1', dual=False, C=0.1, tol=1e-6, max_iter=50000, verbose=True)
    clf.fit(X, y)
    print '#sample:', len(y)
    print 'score:', clf.score(X, y)
    print 'w:', clf.coef_
    print 'nonzw:', [(i,int(w*1e3)/1e3) for i,w in enumerate(clf.coef_[0]) if abs(w)>0]
    fp = open('like_model.bin', 'wb')
    pickle.dump(clf, fp)
    fp.close()

if __name__ == '__main__':
    from feat import iter_data
    iter_data()
    train()

