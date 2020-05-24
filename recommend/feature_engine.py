# coding:utf-8
"""
特征工程模块，提供一个统一的特征工程接口，用于训练和预测

```python
engine = FeatureEngine(10 ** 4)
f_list = engine.get_feature_list(12, [12, 23], {})
```

"""
from __future__ import print_function
import logging
from abc import ABCMeta, abstractmethod

from conf.conf import mysql_conf
import mysql.connector
from analysis.html_analysis import element_to_text, html_to_element
import time
from jieba import analyse
from tools import time_cost

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


def url_domain(url):
    from urlparse import urlparse
    obj = urlparse(url)
    return obj.netloc


_hash_m = 10 ** 4


class FeatureEngine(object):
    def __init__(self, hash_m=10 ** 4):
        global _hash_m
        _hash_m = hash_m

        self._db = mysql.connector.connect(**mysql_conf)
        self._user_feat_offset = 0
        self._item_feat_offset = 100
        self._req_feat_offset = 200
        self._cross_feat_offset = 1000

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(FeatureEngine, cls).__new__(cls, *args, **kwargs)

        return cls.__instance

    @time_cost
    def get_feature_list(self, uid, item_id_list, req):
        """
        获取特征列表

        :param uid:  用户ID
        :param item_id_list: itemID列表
        :param req:  请求上下文
        :return: list<Feature>
        """
        u_flist = FeatureList()
        u_flist.extend(self._get_user_current_feat())

        item_flist = self._get_item_feat(item_id_list, self._item_feat_offset)

        results = []
        for i in item_id_list:
            i = int(i)
            f = FeatureList()

            # user 特征
            f.extend(u_flist)

            # item 特征
            f.extend(item_flist[i])

            # 交叉特征
            f.extend(self._cross_user_item_feat(u_flist, item_flist[i]))

            results.append(f)
        return results

    def _get_item_feat(self, ids, offset=0):
        if len(ids) == 0:
            return {}

        sql = """
            SELECT id,title,body,link FROM article
            WHERE id in ({})
        """.format(','.join(str(i) for i in ids))

        logging.info("SQL:{}".format(sql))

        c = self._db.cursor(dictionary=True)
        c.execute(sql)

        feats = {}

        for row in c.fetchall():
            body = element_to_text(row['body'])
            aid = row['id']
            domain = url_domain(row['link'])

            title_kw = [utf8_en(t).lower() for t in analyse.extract_tags(row['title'])]
            content_kw = [utf8_en(t).lower() for t in analyse.extract_tags(body, topK=200)]

            title_kw = list(set(title_kw))
            content_kw = list(set(content_kw))

            feats[aid] = FeatureList([
                ListCatFeature(1 + offset, 'title_kw', title_kw),
                ListCatFeature(2 + offset, 'content_kw', content_kw),
                CatFeature(3 + offset, 'site_domain', domain)
            ])

        return feats

    def _cross_user_item_feat(self, user_feat, item_feat):
        assert isinstance(user_feat, FeatureList)
        assert isinstance(item_feat, FeatureList)

        feats = FeatureList()

        names = ['title_kw', 'site_domain']
        n = 0
        for u in names:
            fu = user_feat.get_feat_by_name(u)
            fi = item_feat.get_feat_by_name(u)

            cross_f = set()
            for uv in fu.value:
                for iv in fi.value:
                    cross_f.add(uv + ':' + iv)

            n += 1
            cross_f = ListCatFeature(self._cross_feat_offset + n,
                                     'cross:{}'.format(u),
                                     list(cross_f))

            feats.append(cross_f)
        return feats

    def _get_user_current_feat(self):
        c = self._db.cursor(dictionary=True)
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

        item_feats = self._get_item_feat(ids, self._user_feat_offset)

        feat_list = FeatureList()
        for i, feats in item_feats.items():
            feat_list.extend(feats)

        return feat_list


class LibsvmNode(object):
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


from numba import jit


def get_key(n):
    return n.idx


@time_cost
def to_libsvm(features):
    s = []
    for f in features:
        assert isinstance(f, IFeature)
        s.extend(f.to_libsvm())

    _s = dict()
    for node in s:
        _s[node.idx] = node

    s = _s.values()

    s.sort(key=get_key)

    str_s = []
    for si in s:
        str_s.append(str(si))
    return ' '.join(str_s)


class FeatureList(object):
    def __init__(self, flist=None):
        self._features = []

        if flist is not None:
            for f in flist:
                self.append(f)

    def get_feat_by_name(self, name):
        for f in self._features:
            if f.name == name:
                return f
        return None

    def append(self, feat):
        assert isinstance(feat, IFeature)

        self._features.append(feat)
        return self

    def extend(self, flist):
        assert isinstance(flist, list) or isinstance(flist, FeatureList)

        for f in flist:
            self.append(f)
        return self

    def __add__(self, other):
        return self.extend(other)

    def __len__(self):
        return len(self._features)

    def __getitem__(self, item):
        return self._features[item]

    def __iter__(self):
        return iter(self._features)

    def to_libsvm(self):
        return to_libsvm(self._features)


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
    engine = FeatureEngine(10 ** 4)
    f_list = engine.get_feature_list(12, [12, 23], {})
    for i, f in enumerate(f_list):
        print(i, f.to_libsvm())
