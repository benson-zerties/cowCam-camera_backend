#!/usr/bin/python3
# -*- coding: utf-8 -*-

from contextlib import suppress

import yaml
import pathlib
import shutil
import threading
import queue
import logging

from cam_handler_thread import CamHandlerThread
from playlist_manager import PlaylistManager

def invocer(*queue, **kwargs):
    while(True):
        f = queue[0].get()
        f()

class Borg(object):
    """
    Borg is an alternative to Singleton
     * Borg does not ensure that only a single object exists
     * Borg ensures that all created objects share the same state
    """
    _shared_state = {
        '_lock' : threading.Lock()
    }

    def __init__(self):
        # rebind object dictionary
        self.__dict__ = self._shared_state

class CamManager(Borg):
    """
    CamManager loads configuration files and starts/stops camera threads
    
    It loads config files (with possibly multiple cameras) and creates one command queue per camera.
    """
    def __init__(self):
        """
        proc_factory_generator is an injected function
            returns a list of factories based on a yaml specification and a target directory
        """
        Borg.__init__(self)
        if not hasattr(self,'_cfg_obj'):
            self._cfg_obj = None
        if not hasattr(self,'_cam_obj'):
            self._cam_obj = dict()
        if not hasattr(self,'_proc_factory_generator'):
            self._proc_factory_generator = None
        if not hasattr(self,'_cam_list'):
            self._cam_list = None

    def loadConfig(self, filename, proc_factory_generator):
        self._proc_factory_generator = proc_factory_generator
        try:
            with open(filename, 'r') as f:
                try:
                    logging.info('Loading config %s' % (filename))
                    self._cfg_obj = yaml.load(f, Loader=yaml.Loader)
                except yaml.scanner.ScannerError:
                    logging.error('Bad yaml syntax')
                    raise
        except EnvironmentError:
            logging.error('Could not open configuration file')
            raise

        self._cam_list = list()
        for cam in self._cfg_obj['cameras']:
            # start a command thread for each camera-thread
            q = queue.Queue()
            t = threading.Thread(target=invocer, args=(q,))
            t.setDaemon(True)
            t.start()
            # each cam has a: (command-thread, command-queue, thread that controlls all video processing processes of 1 cam)
            self._cam_obj[cam['cam_no']] = dict(invocer=t, cmd_queue=q, cam_thread=None)
            # add cam-number to cam_list
            self._cam_list.append(cam['cam_no'])

    @property
    def cam_list(self):
        return self._cam_list

    def start(self, cam_id):
        """
        Submit start-stream command to queue and return command queue.
        """
        if not self._cfg_obj:
            raise Exception('No yaml configuration loaded')

        root_dir = pathlib.PurePath(self._cfg_obj['hls_dir'])
        cam_cfg = [ cam for cam in self._cfg_obj['cameras'] if cam['cam_no'] == cam_id ][0]
        def cmd():
            try:
                if self._cam_obj[cam_id]['cam_thread'].isAlive():
                    return
            except AttributeError:
                # no cam-thread is running
                output_dir = pathlib.PurePath(root_dir, str(cam_cfg['cam_no']))
                with suppress(Exception):
                    shutil.rmtree(str(output_dir))
                pathlib.Path(output_dir).mkdir()
                logging.debug('Starting thread for cam %d' % (cam_id))

                process_factory = self._proc_factory_generator(cam_cfg, output_dir)
                print('process_factory: ', process_factory)
                self._cam_obj[cam_id]['cam_thread'] = CamHandlerThread( process_factory, cam_id )
                self._cam_obj[cam_id]['cam_thread'].attachObserver(PlaylistManager(output_dir))
                self._cam_obj[cam_id]['cam_thread'].start()
       
        try:
            self._cam_obj[cam_id]['cmd_queue'].put(cmd)
            return self._cam_obj[cam_id]['cmd_queue']
        except IndexError:
            logging.warning('Invalid cam-id specified: %d' % cam_id)
            return


    def stop(self, cam_id):
        """
        Submit stop-stream command to queue and return command queue.
        """
        def cmd():
            self._cam_obj[cam_id]['cam_thread'].stop()
            self._cam_obj[cam_id]['cam_thread'].join()
            self._cam_obj[cam_id]['cam_thread'] = None

        try:
            self._cam_obj[cam_id]['cmd_queue'].put(cmd)
            return self._cam_obj[cam_id]['cmd_queue']
        except IndexError:
            logging.warning('Invalid cam-id specified: %d' % cam_id)
            return
