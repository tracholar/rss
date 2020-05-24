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
import grpc
import time

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


class LibsvmTrainer(ITrainer):
    def __init__(self, model_path=None, dump_path=None, dump_n=100):
        pass

    def on_batch(self, batch):
        assert isinstance(batch, list)

        logging.info('on_batch: {}'.format(batch))

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


def client_test():
    with grpc.insecure_channel('localhost:9000') as channel:
        stub = TrainServerStub(channel)

        ins = ['1 2:1 45:1', '0 3:1 100:1']

        req = TrainRequest(ins=ins)
        resp = stub.onBatch(req)
        print(resp)


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 0 or sys.argv[1] == 'sever':
        server = TrainerRpcServer()
        server.save()
    else:
        client_test()
