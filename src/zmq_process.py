#!/usr/bin/python3
# -*- coding: utf-8 -*-

import multiprocessing
import threading
from urllib.parse import urlparse
from zmq.eventloop import zmqstream
from tornado import ioloop
import asyncio
import zmq
import logging

#class ZmqProcess(multiprocessing.Process):
class ZmqThread(threading.Thread):
    """
    This is the base for all processes and offers utility functions
    for setup and creating new streams.

    """
    def __init__(self):
        super().__init__()

        self.context = None
        self.loop = None

    def setup(self):
        self.context = zmq.Context()
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = ioloop.IOLoop.current()

    def stream(self, sock_type, addr, bind, callback=None, subscribe=b''):
        port = 0
        sock = self.context.socket(sock_type)
        if bind:
            logging.info('Trying to bind to address %s' % (addr))
            try:
                sock.bind(addr)
                url_obj = urlparse(addr)
                port = url_obj.port
            except zmq.error.ZMQError as e:
                if e.errno == zmq.EADDRINUSE:
                    raise Exception('Address %s already in use' % (addr))
                else:
                    # retry to bind to a random port
                    port = sock.bind_to_random_port(addr)
                    logging.info("Bind to random port: %d" % (port))
        else:
            logging.debug('Connecting to %s' % (addr))
            print('Connecting to %s' % (addr))
            sock.connect(addr)

        # Add a default subscription for SUB sockets
        if sock_type == zmq.SUB:
            sock.setsockopt(zmq.SUBSCRIBE, subscribe)

        # Create the stream and add the callback
        stream = zmqstream.ZMQStream(sock, self.loop)
        if callback:
            stream.on_recv(callback)
    
        if port:
            port = int(port)

        return stream, port
