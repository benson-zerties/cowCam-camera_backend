#!/usr/bin/env python3
# -*- coding: utf8 -*-

from process_factory import ProcessFactory
from ffmpeg_cmd_builder import FFMPEGCmdBuilder, FFMPEGHlsStream

import hashlib
import logging
import subprocess
import shlex

def ffmpeg_proc_factory_gen(cam_obj, target_dir):
    """Generates a list of FfmpegProcessFactories
    """
    process_descriptors = list()
    for s in cam_obj['sources']:
        process_descriptors.append(FfmpegProcessFactory(s, target_dir))

    return process_descriptors


class FfmpegProcessFactory(ProcessFactory):
    """Constructs 1 camera processes associated with 1 camera
    """

    def __init__(self, src, target_dir):
        super().__init__()
        self._process_descriptor, self.files = FfmpegProcessFactory._ffmpeg_context_creator(src, target_dir)

    def factoryMethods(self):
        """A callable process closure
        """
        return self._process_descriptor

    def fileList(self):
        return self.files

    def _ffmpeg_context_creator(stream_src, target_dir):
        """ffmpeg_context_creator returns a function that can be executed to create a ffmpeg instance
    
        Assumption: one ffmpeg process can create >= 1 output streams
        """

        uri         = stream_src['uri']
        decoder_str = stream_src['decoder']
        ffmpeg_obj  = FFMPEGCmdBuilder(uri, decoder_str)
        playlist_files = list()
        playlist_file_template = 'playlist_%s_%%d.m3u' % hashlib.sha1(uri.encode()).hexdigest()
        for idx,s in enumerate(stream_src['streams']):
            playlist = target_dir / (playlist_file_template % (idx))
            stream = FFMPEGHlsStream(playlist, s['encoder'])
            if s['width'] != 'default':
                stream['video_width'] = int(s['width'])
            if s['framerate'] != 'default':
                stream['video_framerate'] = int(s['framerate'])
            ffmpeg_obj.addOutputStream(stream)
            playlist_files.append(playlist)

        ffmpeg_cmd = ffmpeg_obj.getCmd()
        logging.info('Composing ffmpeg command: %s' % (ffmpeg_cmd))

        def ffmpeg_process():
            logging.info('starting ffmpeg')
            return subprocess.Popen(shlex.split(ffmpeg_cmd))

        return ffmpeg_process, playlist_files
