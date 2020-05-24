# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import rpc_data_pb2 as rpc__data__pb2


class TrainServerStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.onBatch = channel.unary_unary(
                '/TrainServer/onBatch',
                request_serializer=rpc__data__pb2.TrainRequest.SerializeToString,
                response_deserializer=rpc__data__pb2.TrainResponse.FromString,
                )


class TrainServerServicer(object):
    """Missing associated documentation comment in .proto file"""

    def onBatch(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TrainServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'onBatch': grpc.unary_unary_rpc_method_handler(
                    servicer.onBatch,
                    request_deserializer=rpc__data__pb2.TrainRequest.FromString,
                    response_serializer=rpc__data__pb2.TrainResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'TrainServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class TrainServer(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def onBatch(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/TrainServer/onBatch',
            rpc__data__pb2.TrainRequest.SerializeToString,
            rpc__data__pb2.TrainResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)
