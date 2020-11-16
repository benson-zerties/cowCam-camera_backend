#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import threading

class CamHandlerThread (threading.Thread):
    """CamHandlerThread controls 1 camera

    One instance of CamHandlerThread controls 1 camera, which might provide
    multiple streams via 1 or multiple transcoding processes

    Observers:
     * are interested in dead processes to discard to playlist file??
    """
    def __init__(self, process_descriptors, cam_id):
        super().__init__()
        self._cam_id    = cam_id
        self._observers = list()
        # list of factory methods to start processes
        self.process_descriptors = process_descriptors
        self.process_factory_active = list()
        # list of processes to keep track of
        self._stop_event = threading.Event()
        self.EVENT_TIMEOUT_MAX = 10 # seconds

    def __exit__(self):
        pass

    @property
    def processFactories(self):
        return self.process_factory_active

    @property
    def camId(self):
        return self._cam_id

    def attachObserver(self, o):
        logging.info('Observer attached: %s' % (o))
        self._observers.append(o)

    def detachObserver(self, o):
        logging.info('Observer detached: %s' % (o))
        self._observers.remove(o)

    def notify(self):
        for o in self._observers:
            logging.info('Observer notifed: %s' % (type(o).__name__))
            o.update(self)

    def stop(self):
        self._stop_event.set()

    def run(self):
        playlists = list()
        proc_context = list()
        event_timeout_base = 2
        process_factories = [ p.factoryMethods() for p in self.process_descriptors ]
        print('process_factories...', process_factories)
        # start all processes
        ffmpeg_procs      = [ proc() for proc in process_factories ]
        print('ffmpeg_procs...', ffmpeg_procs)
        logging.info('Entering control loop for cam %d' % (self._cam_id))
        event_timeout = event_timeout_base
        while not (self._stop_event.wait(timeout=event_timeout)):
            # check if subprocesses are alive
            self.process_factory_active = list() 
            for idx,proc in enumerate(ffmpeg_procs):
                if proc.poll() == None:
                    # process is still running
                    self.process_factory_active.append(self.process_descriptors[idx])
                else:
                    logging.warning('ffmpeg died -> restart')
                    # process died -> restart
                    ffmpeg_procs[idx] = process_factories[idx]()
            # notify all observers
            self.notify()
            if event_timeout < self.EVENT_TIMEOUT_MAX:
                # throttle update rate after process has started
                event_timeout += 1
        else:
            # received request to terminate thread -> also terminate ffmpeg processes
            for proc in ffmpeg_procs:
                try:
                    proc.terminate()
                except ProcessLookupError:
                    logging.warning('One process for %s has already terminated' % (self._cam_id))
            for proc in ffmpeg_procs:
                try:
                    logging.warning('waiting for ffmpeg to terminate')
                    outs, errs = proc.communicate(timeout=3)
                    if errs:
                        logging.error(errs)
                    if outs:
                        logging.info(outs)
                except TimeoutExpired:
                    logging.warning('ffmpeg refused to terminate')
                    proc.kill()
            logging.info('Stopped thread for cam %d' % (self._cam_id))


if __name__ == '__main__':
    import os
    import signal
    import yaml
    import pathlib

    cfg_obj = None
    os.setpgrp()

    try:
        with open('camera_configuration.yaml', 'r') as f:
            try:
                cfg_obj = yaml.load(f, Loader=yaml.Loader)
            except yaml.scanner.ScannerError:
                print('Bad yaml syntax')
                raise
    except EnvironmentError:
        print('Could not open configuration file')
        raise

    root_dir = pathlib.PurePath(cfg_obj['hls_dir'])
    cam = cfg_obj['cameras'][0]

    cam_thread1 = CamHandlerThread( cfg_obj['cameras'][0], root_dir )
    cam_thread1.start()
    cam_thread1.join()

    os.killpg(0, signal.SIGKILL)
