#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 * Runs the event loops
 * starts/stops cameras via CamManager()
"""
import sys
import logging
import argparse

import zmq
from zmq_process import ZmqThread
from zmq.utils import jsonapi as json
from jsonrpc import JSONRPCResponseManager, Dispatcher

from cam_manager import CamManager
from ffmpeg_process_factory import ffmpeg_proc_factory_gen
my_dispatcher = Dispatcher()

@my_dispatcher.add_method
def start(*cam_id):
    print("Starting cam ", cam_id[0])
    CamManager().start(cam_id[0])
    return "cam_started"

@my_dispatcher.add_method
def stop(*cam_id):
    print("Stopping cam %d" % cam_id[0])
    CamManager().stop(cam_id[0])
    return "cam_stopped"

@my_dispatcher.add_method
def list():
    return CamManager().cam_list

def handle_json(manager, message):
    """Callback function, called if new message is received."""

    logging.log(logging.INFO,  'Request: %s' % (message))
    response = manager.handle(message[0].decode('utf-8'), my_dispatcher)
    result = response.json
    logging.log(logging.INFO,  'Result: %s' % (result))
    return result


class CamHandlerRemote(ZmqThread):
    def __init__(self, bind_addr, on_recv_cb):
        super().__init__()
        self.bind_addr = bind_addr
        #print('Address: %s' % self.bind_addr)
        self._port = None
        self.recv_cb = on_recv_cb
        self.rep_stream = None

    @property
    def port(self):
        return self._port

    def setup(self):
        """Sets up PyZMQ and creates all streams."""
        super().setup()

        # Create the stream and add the message handler
        self.rep_stream, self._port = self.stream(zmq.REP, self.bind_addr, bind=True)
        self.rep_stream.on_recv(lambda msg: self.rep_stream.send_string(self.recv_cb(msg)))

    def run(self):
        """Sets up everything and starts the event loop."""
        self.setup()
        self.loop.start()

    def stop(self):
        """Stops the event loop."""
        self.loop.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, help="Specify the yaml configuration file")
    parser.add_argument('-p', '--port', type=int, help="Specify the port to listen to", )
    args = parser.parse_args()

    logging.basicConfig(
        #filename = "cam_handler_remote.log",
        stream = sys.stdout,
        level = logging.DEBUG,
        filemode = "a",
        format = "%(asctime)s %(funcName)s Line:%(lineno)s [%(levelname)-8s] %(message)s",
        datefmt = "%H:%M:%S")

    #a = cam_handler_remote_factory("tcp://*:5559", '../test/camera_configuration.yaml')
    uri = 'tcp://*:' + str(args.port)
    try:
        manager = JSONRPCResponseManager()
        CamManager().loadConfig(args.config, ffmpeg_proc_factory_gen)
        a = CamHandlerRemote(uri, lambda msg : handle_json(manager, msg))
    except (AttributeError, TypeError) as e:
        sys.stderr.write('Missing commandline argument\n')
        sys.stderr.write('Error: %s\n' % (str(e)))

        parser.print_help()
        sys.exit(2)

    a.setDaemon(True)
    a.start()
    a.join()
    logging.shutdown()
