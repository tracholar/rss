# coding:utf-8
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def time_cost(fn):
    import time
    def _warp_fn(*inputs, **kwargs):
        t = time.time()
        r = fn(*inputs, **kwargs)
        logging.info('func {} cost {}'.format(fn.__name__, time.time() - t))
        if len(inputs) > 0 and type(inputs[0]) is list:
            logging.info('args0 len {}'.format(len(inputs[0])))
        return r

    return _warp_fn