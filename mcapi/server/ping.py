import logging

from mcstatus import JavaServer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def ping(ip, port):
    server = JavaServer(ip, port)
    try:
        status = server.status()
    except:
        raise Exception
    return status.latency
