#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
hierarchical prompt usage example
"""
from PyInquirer import style_from_dict, prompt

from examples import custom_style_2

import argparse
import zmq
import json
import time

import logging

from jsonrpc import JSONRPCResponseManager, Dispatcher

class CameraManagerProxy(object):
    def __init__(self):
        super().__init__()
        self._port = None
        self.req_stream = None
        self.context = None
        self.SERVER_ENDPOINT = None

    @property
    def port(self):
        return self._port

    def zmq_socket_creator(f, *args):
        def new_f(*args):
            self = args[0]
            logging.debug("Entering %s" % (f.__name__))
            self.client = self.context.socket(zmq.REQ)
            self.client.connect(self.SERVER_ENDPOINT)
            result = f(*args)
            self.client.close()
            return result
        return new_f

    def setup(self, addr):
        """Sets up PyZMQ and creates all streams."""
        self.SERVER_ENDPOINT = addr
        self.context = zmq.Context()
        print("I: Connecting to server ...")

    @zmq_socket_creator
    def start_cam(self, cam_id):
        print('start stream abcde')
        payload = {
            "method": "start",
            "params": [cam_id],
            "id": 2,
            "jsonrpc": "2.0"
        }
        request = json.dumps(payload)
        self.client.send_unicode(request)


    @zmq_socket_creator
    def stop_cam(self, cam_id):
        payload = {
            "method": "stop",
            "params": [cam_id],
            "id": 2,
            "jsonrpc": "2.0"
        }
        request = json.dumps(payload)
        self.client.send_unicode(request)

    @zmq_socket_creator
    def capture_image(self, cam_id):
        payload = {
            "method": "capture_image",
            "params": [cam_id],
            "id": 2,
            "jsonrpc": "2.0"
        }
        request = json.dumps(payload)
        self.client.send_unicode(request)

    @zmq_socket_creator
    def list(self):
        payload = {
            "method": "list",
            "id": 2,
            "jsonrpc": "2.0"
        }
        request = json.dumps(payload)
        self.client.send_unicode(request)
        msg = self.client.recv_unicode()
        msg_dict = json.loads(msg)
        return msg_dict['result']

def query_cam_id(cam_list_numeric):
    cam_prompt = {
        'type': 'list',
        'name': 'camera_id',
        'message': 'Select a camera',
        'choices': list( map(str, cam_list_numeric) )
    }
    answers = prompt(cam_prompt)
    return answers['camera_id']

def ask_operation(cmd_strs):
    cancel_cmd = 'cancel action'
    cmd_prompt = {
        'type': 'list',
        'name': 'cmd',
        'message': 'Select a command',
        'choices': cmd_strs + [cancel_cmd]
    }
    answers = prompt(cmd_prompt)
    print(answers)
    return cmd_strs.index(answers['cmd']) if answers['cmd'] in cmd_strs else None


def main_loop(cam_manager):
    while True:
        cam_id = query_cam_id(cam_manager.list())
        actions = [ 
        {
            'fnc': lambda cam_id : cam_manager.start_cam(cam_id),
            'choice': 'start stream'
        },
        {
            'fnc': lambda cam_id : cam_manager.stop_cam(cam_id),
            'choice': 'stop stream'
        },
        {
            'fnc': lambda cam_id : cam_manager.capture_image(cam_id),
            'choice': 'capture image'
        }]
        action_idx = ask_operation([o['choice'] for o in actions])
        if action_idx is not None:
            actions[action_idx]['fnc'](int(cam_id))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--cam_mgr', type=str, help="Specify the camera backend uri")
    args = parser.parse_args()

    cam_manager = CameraManagerProxy()
    try:
        cam_manager.setup(args.cam_mgr)
        manager = JSONRPCResponseManager()
    except (AttributeError, TypeError) as e:
        sys.stderr.write('Missing commandline argument\n')
        sys.stderr.write('Error: %s\n' % (str(e)))

        parser.print_help()
        sys.exit(2)

    main_loop(cam_manager)
