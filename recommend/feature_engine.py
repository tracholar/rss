# coding:utf-8
from __future__ import print_function
import logging
from abc import ABCMeta, abstractmethod

from conf.conf import mysql_conf
import mysql.connector
from analysis.html_analysis import element_to_text, html_to_element
import time
from jieba import analyse

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def utf8_en(data):
    if type(data) is unicode:
        return data.encode('utf-8')
    data = str(data)
    return data.encode('utf-8')


def f_hash(s):
    import hashlib
    m = _hash_m
    digest = hashlib.md5(s).hexdigest()
    return int(digest, 16) % m


def _get_user_current_feat():
    db = mysql.connector.connect(**mysql_conf)
    c = db.cursor(dictionary=True)
    now = int(time.time())
    sql = """
        SELECT json_extract(a.evt_attr, '$.article_id') AS ids
        FROM article_event a
        WHERE time > {} AND name in ('like', 'hate')
    """.format(now - 3600 * 48)

    logging.info('SQL:{}'.format(sql))
    c.execute(sql)

    ids = []
    for row in c.fetchall():
        ids.extend([i for i in row['ids'].replace('"', '').split(',')])
    ids = list(set(ids))

    if len(ids) == 0:
        return []

    sql = """
        SELECT title,body FROM article
        WHERE id in ({})
    """.format(','.join(ids))

    logging.info("SQL:{}".format(sql))
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

    return [
        ListCatFeature(1, 'title_kw', title_kw),
        ListCatFeature(2, 'content_kw', content_kw)
    ]



_hash_m = 10 ** 6


class FeatureEngine(object):
    def __init__(self, hash_m=10 ** 6):
        global _hash_m
        _hash_m = hash_m

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(FeatureEngine, cls).__new__(cls, *args, **kwargs)

        return cls.__instance

    def get_feature_list(self, uid, item_id_list, req):
        """
        获取特征列表

        :param uid:  用户ID
        :param item_id_list: itemID列表
        :param req:  请求上下文
        :return: list<Feature>
        """
        flist = FeatureList()
        flist.extend(_get_user_current_feat())
        return flist


from collections import namedtuple

class LibsvmNode():
    def __init__(self, idx, val):
        assert type(idx) in (int, long)
        assert type(val) in (int, float, long)

        self.idx = idx
        self.val = val

    def __str__(self):
        return '{}:{}'.format(self.idx, self.val)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        _it = [self.idx, self.val]
        return iter(_it)


class IFeature(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def to_libsvm(self, hash_m):
        """
        转libsvm格式接口  id:val
        hash_m 是hash的模
        :return: list<LibsvmNode>
        """
        raise NotImplementedError()

    @abstractmethod
    def to_libffm(self, hash_m):
        """
        转libffm格式接口  fid:id:val
        hash_m 是hash的模
        :return:
        """
        raise NotImplementedError()


class Feature(IFeature):
    __metaclass__ = ABCMeta

    def __init__(self, fid, name, value):
        """

        :param fid: 列ID
        :param name: 特征名字
        :param value: 特征值
        """
        assert fid is not None and type(fid) is int, "error fid {}".format(fid)
        assert name is not None and type(name) is str, \
            "name type:{}, name = {}".format(type(name), name)
        assert value is not None, "value is none"

        self.fid = fid
        self.name = name
        self.value = value


class FloatFeature(Feature):
    def __init__(self, fid, name, value):
        assert type(value) in (float, int, long)

        super(FloatFeature, self).__init__(fid, name, value)

    def to_libsvm(self):
        idx = f_hash("{}:{}".format(self.fid, self.name))
        return [LibsvmNode(idx, self.value)]

    def to_libffm(self):
        idx = f_hash(self.name)
        return "{}:{}:{}".format(self.fid, idx, self.value)


class CatFeature(Feature):
    def to_libsvm(self):
        idx = f_hash("{}:{}:{}".format(self.fid, self.name, self.value))
        return [LibsvmNode(idx, 1)]

    def to_libffm(self):
        idx = f_hash(self.name)
        val = f_hash(str(self.value))
        return "{}:{}:{}".format(self.fid, idx, val)


class ListCatFeature(Feature):
    def __init__(self, fid, name, value):
        assert type(value) is list

        super(ListCatFeature, self).__init__(fid, name, value)

    def to_libffm(self):
        s = []
        idx = f_hash(self.name)
        for v in self.value:
            v = f_hash(str(v))
            s.append("{}:{}:{}".format(self.fid, idx, v))
        return ' '.join(s)

    def to_libsvm(self):
        s = []

        for v in self.value:
            idx = f_hash("{}:{}:{}".format(self.name, self.value, v))
            s.append(LibsvmNode(idx, 1))
        return s


class FeatureList:
    def __init__(self, flist=None):
        self._features = []

        if flist is not None:
            for f in flist:
                self.append(f)

    def append(self, feat):
        assert isinstance(feat, IFeature)

        self._features.append(feat)
        return self

    def extend(self, flist):
        assert isinstance(flist, list)

        for f in flist:
            self.append(f)
        return self

    def __len__(self):
        return len(self._features)

    def __getitem__(self, item):
        return self._features[item]

    def to_libsvm(self):
        s = []
        for f in self._features:
            assert isinstance(f, IFeature)
            s.extend(f.to_libsvm())

        _s = {node.idx : node for node in s}
        s = _s.values()
        s.sort(key=lambda n: n.idx)

        return ' '.join(str(si) for si in s)


if __name__ == '__main__':
    f1 = FloatFeature(1, "uid", 123)
    print(f1.to_libsvm())
    print(f1.to_libffm())

    f2 = CatFeature(1, "uid", "Tom")
    print(f2.to_libsvm())
    print(f2.to_libffm())

    f3 = ListCatFeature(1, "clicked_items", "1,2,3".split(','))
    print(f3.to_libsvm())
    print(f3.to_libffm())

    f_list = FeatureList([f1, f2, f3])
    print(f_list.to_libsvm())

    print("====test engine=====")
    engine = FeatureEngine(100)
    f_list = engine.get_feature_list(12, [12, 23], {})
    print(f_list.to_libsvm())
