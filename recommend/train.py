#coding:utf-8
import sys
sys.path.append('../conf')
from conf import mysql_conf
import mysql.connector
import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle
import hashlib

def ihash(s):
    digest = hashlib.md5(s).hexdigest()
    return int(digest, 16) % (10**4)

def feat_to_df(data):
    d = []
    row_ind = []
    col_ind = []
    y = []
    if type(data) is dict:
        data = [data]
    elif type(data) is not list:
        raise Exception('wrong data type {}'.format(type(data)))
    for i, row in enumerate(data):
        if 'y' in row:
            y.append(row['y'])

def get_data():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    c.execute("select y, f_site, f_title_keywords, f_content_keywords, f_date, f_content_len, f_img_n from article_feat")
    data = c.fetchall()
    db.close()
    y, X = feat_to_df(data)

