# coding:utf-8
from __future__ import print_function
import logging

from feature_engine import FeatureEngine

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class RecEngine(object):
    def __init__(self):
        self.feature_engine = FeatureEngine()

    def get_rec_list(self, uid):
        """
        获取推荐列表
        :param uid: 用户ID
        :return:
        """
        raise NotImplementedError()


