# coding:utf-8
from __future__ import print_function

from sklearn.linear_model import SGDClassifier
import pickle
import mysql
import logging

from model_trainer import _feature_engine, parse_libsvm
from conf.conf import mysql_conf

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class ModelServer(object):
    def __init__(self, model_path='./model', load_n=10):
        self.model_path = model_path
        self.load_n = load_n

        self._load_model()
        self.n = 0
        self._feature_engine = _feature_engine

    def _load_model(self):
        with open(self.model_path, 'rb') as fp:
            self._clf = pickle.load(fp)

    def predict(self, uid, aids, req={}):
        feats = self._feature_engine.get_feature_list(uid, aids, req)
        libsvm = [' ' + feat.to_libsvm() for feat in feats]
        X, _ = parse_libsvm(libsvm)
        score = self._clf.decision_function(X)

        self.n += 1
        if self.n % self.load_n == 0:
            self._load_model()

        return zip(aids, score)


class RecommendServer(object):
    def __init__(self, model_path='./model/model', recall_n=100, rank_n=10):
        self._predictor = ModelServer(model_path)
        self._recall_n = recall_n
        self._rank_n = rank_n
        self._db = mysql.connector.connect(**mysql_conf)

    def _recall(self, uid, view_list=[-1]):
        sql = """
        select id from article
        where id not in ({view_list})
        order by left(`date`, 10) desc, rand() desc
        limit {recall_n}
        """.format(recall_n=self._recall_n,
                   view_list=','.join(str(i) for i in view_list))

        logging.info(sql)

        c = self._db.cursor(dictionary=True)
        c.execute(sql)

        ids = [article['id'] for article in c.fetchall()]
        c.close()

        return ids

    def _rank(self, uid, recall_ids, req):
        score = self._predictor.predict(uid, recall_ids, req)
        score = sorted(score, reverse=True, key=lambda x: x[1])

        logging.info('rank score: {}'.format(score))

        n = min(self._rank_n, len(score))
        return score[:n]

    def _fetch_detail(self, aids):
        sql = """
        select * from article
        where id in ({})
        """.format(','.join(str(a[0]) for a in aids))

        logging.info(sql)

        c = self._db.cursor(dictionary=True)
        c.execute(sql)
        articles = c.fetchall()
        c.close()

        score = dict(aids)
        for a in articles:
            if a['id'] in score:
                a['rank_score'] = score[a['id']]

        return articles

    def recommend(self, uid, req={}):
        aids = self._recall(uid, [-1])
        aids = self._rank(uid, aids, req)
        articles = self._fetch_detail(aids)

        return articles


if __name__ == '__main__':
    rec = RecommendServer(recall_n=20, rank_n=5)
    articles = rec.recommend(1, {})
    print(articles)