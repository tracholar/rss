#coding:utf-8
"""计算推荐得分"""
import sys
sys.path.append('../conf')

from conf import mysql_conf
import mysql.connector
from feat import gen_feat
from train import predict

def calc_rec_score():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    c.execute("SELECT * from article")

    for row in c.fetchall():
        data = [gen_feat(row)]
        score = predict(data)[0, 0]
        aid = row['id']
        c.execute("UPDATE article SET score = %s where id = %s", (float(score), aid))
        print '>>>', row['title'], ' score=', score

    db.commit()
    db.close()



if __name__ == '__main__':
    calc_rec_score()