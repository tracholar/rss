# coding:utf-8
"""
模型训练器，在线训练与离线训练统一，支持备份。
"""
from __future__ import print_function
import logging
from abc import ABCMeta, abstractmethod
from rpc_data.rpc_data_pb2_grpc import TrainServerServicer, \
    add_TrainServerServicer_to_server, TrainServerStub
from rpc_data.rpc_data_pb2 import TrainResponse, TrainRequest
from concurrent import futures
from sklearn.linear_model import SGDClassifier
from scipy.sparse import csr_matrix

import grpc
import time
import pickle
import numpy as np

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class ITrainer(object):
    __metaclass__ = ABCMeta

    def on_batch(self, batch):
        """
        利用一个batch的训练样本跟新模型
        :param batch:
        :return: bool
        """
        raise NotImplementedError()


def repr_sparse(arr, limit=10):
    s = []
    assert isinstance(arr, np.ndarray)
    assert arr.ndim == 1

    n = 0
    for i, x in enumerate(arr):
        if x == 0.0:
            continue
        s.append('{}:{:.4g}'.format(i, x))

        n += 1
        if n > limit and limit > 0:
            break

    return ' '.join(s)


def parse_libsvm(libsvm):
    if not isinstance(libsvm, list):
        libsvm = [libsvm]

    d = []
    row_ind = []
    col_ind = []
    y = []

    for i, line in enumerate(libsvm):
        if len(line) == 0:
            continue
        row = line.split(' ')
        if len(row) <= 2:
            continue

        if row[0] == '':
            y = -1
        else:
            y.append(int(row[0]))

        for point in row[1:]:
            kv = point.split(':')
            if len(kv) != 2:
                continue
            row_ind.append(i)
            col_ind.append(int(kv[0]))
            d.append(float(kv[1]))

    n_row = len(libsvm)
    n_col = _feature_n
    X = csr_matrix((d, (row_ind, col_ind)), shape=(n_row, n_col))

    return X, y


class LibsvmTrainer(ITrainer):
    def __init__(self, model_path=None, dump_path='./model', dump_n=10,
                 feature_n=10 ** 4):
        if model_path is None:
            self._clf = SGDClassifier(learning_rate='constant',
                                      eta0=1e-3,
                                      verbose=True)
        else:
            self._clf = pickle.load(open(model_path))
        assert isinstance(self._clf, SGDClassifier)

        self.dump_path = dump_path
        self.dump_n = dump_n
        self.feature_n = feature_n
        self.batch_n = 0



    def _check_point(self):
        if self.batch_n % self.dump_n == 0:
            name = '{}/model'.format(self.dump_path)
            with open(name, 'wb') as fp:
                pickle.dump(self._clf, fp)
                logging.info('dump model to checkpoint {}'.format(name))

    def on_batch(self, batch):
        assert isinstance(batch, list)

        logging.info('on_batch size {}'.format(len(batch)))

        X, y = parse_libsvm(batch)
        self._clf.partial_fit(X, y, classes=[0, 1])
        self.batch_n += 1

        logging.info('weight: {}'.format(repr_sparse(self._clf.coef_[0])))

        self._check_point()
        return True


class TrainerRpcServer(TrainServerServicer):
    def __init__(self):
        self._trainer = LibsvmTrainer()

    def onBatch(self, req, context):
        assert isinstance(req, TrainRequest)

        status = self._trainer.on_batch(list(req.ins))
        resp = TrainResponse(status=status, message='OK')

        return resp

    def save(self):
        server = grpc.server(futures.ThreadPoolExecutor(2))

        add_TrainServerServicer_to_server(self, server)

        server.add_insecure_port('[::]:9000')
        server.start()

        try:
            while True:
                logging.info('server RUNNING')
                time.sleep(60 * 60 * 24)
        except KeyboardInterrupt:
            server.stop(0)


__train_client = None


def _get_train_client():
    global __train_client
    if __train_client is not None:
        return __train_client
    channel = grpc.insecure_channel('localhost:9000')
    __train_client = TrainServerStub(channel)

    return __train_client


def client_test():
    with grpc.insecure_channel('localhost:9000') as channel:
        stub = TrainServerStub(channel)

        ins = ['1 2:1 45:1', '0 3:1 100:1']

        req = TrainRequest(ins=ins)
        resp = stub.onBatch(req)
        print(resp)


from feature_engine import FeatureEngine

_feature_n = 10 ** 4
_feature_engine = FeatureEngine(_feature_n)


def train_sample(batch):
    """
    训练一个样本
    :param batch: (y, uid, aid) 三元组或者这样的三元组列表
    :return:
    """
    if isinstance(batch, tuple):
        batch = [batch]
    assert isinstance(batch, list)

    for s in batch:
        y, uid, aid = s
        feat = _feature_engine.get_feature_list(uid, [aid], {})
        if len(feat) == 1:
            feat = feat[0]
            ins = '{} {}'.format(y, feat.to_libsvm())

            client = _get_train_client()
            req = TrainRequest(ins=[ins])
            resp = client.onBatch(req)

            logging.info('train sample {}, return {}'.format(s, resp))


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 0 or sys.argv[1] == 'sever':
        server = TrainerRpcServer()
        server.save()
    else:
        client_test()
