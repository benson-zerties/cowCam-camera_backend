#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pathlib
import subprocess
import shlex
import json
from abc import ABC

def analyse_input_format(uri):
    ffprobe_cmd = "ffprobe -v quiet -print_format json -show_format %s" % (uri)
    try:
        ffprobe_output = subprocess.check_output(shlex.split(ffprobe_cmd), bufsize=-1)
        return json.loads(ffprobe_output.decode('utf-8'))
        
    except subprocess.CalledProcessError as e:
        print("Bad input stream: %s" % (uri))
        raise

def analyse_input_stream(uri):
    ffprobe_cmd_stream = "ffprobe -v quiet -print_format json -show_streams %s" % (uri)
    try:
        ffprobe_output = subprocess.check_output(shlex.split(ffprobe_cmd_str), bufsize=-1)

        media_format_obj = json.loads(ffprobe_output.decode('utf-8'))
        # search for first video stream
        for s in media_format_obj['streams']:
            if s['codec_type'] == 'video':
                return s
     
    except subprocess.CalledProcessError as e:
        print("Bad input stream: %s" % (uri))
        raise

class FFMPEGCmdBuilder(object):
    """
    Builder that implementes the construction of a ffmpeg command line
    """
    def __init__(self, uri_input, decoder_str):
        self.ffmpeg_cmd = "ffmpeg -loglevel warning -vcodec %s -i \"%s\" " % (decoder_str, uri_input)

    def addOutputStream(self, output_stream):
        self.ffmpeg_cmd += str(output_stream) + " "

    def getCmd(self):
        return self.ffmpeg_cmd

class FFMPEGOutputStream(ABC):
    """
    Base class for ffmpeg output streams
    """
    cmd_mapping = {
            'video_width'    : '-vf scale=%d:-1',
            'video_framerate': '-r %d',
            'encoder_str'    : '-vcodec %s'
    }

    def __init__(self, encoder_str):
        self.cmd_args = dict()
        self.cmd_args['video_width']     = None
        self.cmd_args['video_framerate'] = None
        self.cmd_args['encoder_str']     = encoder_str
        self.extra_args = ''

    def __getitem__(self, key):
        return self.cmd_args[key]

    def __setitem__(self, key, value):
        self.cmd_args[key] = value

    def __str__(self):
        args = '-map 0 '
        for key in self.cmd_args.keys():
            if self.cmd_args[key]:
                args += (self.cmd_mapping[key] % (self.cmd_args[key])) + " "

        return (args + self.extra_args) 


class FFMPEGHlsStream(FFMPEGOutputStream):
    """
    Specialization of FFMPEGOutputStream to HLS stream
    """
    def __init__(self, playlist_file, encoder_str = 'libx264'):
        super().__init__(encoder_str)
        self.playlist_file = playlist_file
        self.extra_args = ' '.join("-an -f hls -preset ultrafast -hls_wrap 10 -hls_flags delete_segments \
                          -segment_list_size 10 -segment_list_flags +live -hls_time 5 ".split())

    def __str__(self):
        self.cmd_args['hls_segment_filename'] = self.playlist_file.with_suffix('.%03d.ts')
        self.cmd_mapping['hls_segment_filename'] = '-hls_segment_filename %s'
        return super(FFMPEGHlsStream, self).__str__() + ' ' + str(self.playlist_file)


if __name__ == '__main__':
    s = FFMPEGHlsStream('/path/to/playlist', 'enc_xx', 'dec_xx')
    s['video_width'] = 960
    s['video_framerate'] = 10

    ffmpeg_obj = FFMPEGCmdBuilder('/path/to/media/source')
    ffmpeg_obj.addOutputStream(s)

    print(ffmpeg_obj.getCmd())
