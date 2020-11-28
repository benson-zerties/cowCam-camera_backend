#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import threading
import time

class CaptureImageThread (threading.Thread):
    """CaptureImageThread periodically captures a picture from each cam
    """
 
    def __init__(self, cam_manager, time_period):
        super().__init__()
        self._cam_manager = cam_manager
        self._time_period = time_period 

    def run(self):
        while True:
            cam_list = self._cam_manager.cam_list
            for c_id in cam_list:
                self._cam_manager.capture_image(c_id)
                logging.debug('Capturing image for cam %d' % c_id)
            time.sleep(self._time_period)
 
