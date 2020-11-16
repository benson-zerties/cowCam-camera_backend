#!/usr/bin/python3
# -*- coding: utf-8 -*-

# https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

# #EXTM3U
# #EXT-X-STREAM-INF:BANDWIDTH=1227765,RESOLUTION=1008x420,CODECS="avc1.4d401f,mp4a.40.5"
# 84049-bauhaus/420p/pl.m3u8
# #EXT-X-STREAM-INF:BANDWIDTH=2283072,RESOLUTION=1920x800,CODECS="avc1.640029,mp4a.40.5"
# 84049-bauhaus/800p/pl.m3u8

#http://cdn.flowplayer.org/202777/84049-bauhaus/420p/pl.m3u8

from ffmpeg_cmd_builder import *
import pathlib
import collections.abc

from functools import total_ordering

# HLS Playlist handling
@total_ordering
class PlaylistItem(collections.abc.MutableMapping):
    """
    if total ordering decorator is used, not all 6 comparison methods need to be
    implemented for the class
    """
    def __init__(self, playlist_name, stream_details):
        self._data = dict((('name', playlist_name),
                           ('bandwidth', int(stream_details['format']['bit_rate'])),
                           ('width', int(stream_details['streams'][0]['width'])), 
                           ('height', int(stream_details['streams'][0]['height']))))

    def keys(self):
        return self._data.keys()

    def __getitem__(self, key):
        return self._data[key]

    def __eq__(self, other):
        for key in set().union(self.keys(), other.keys()):
            try:
                if not self[key] == other[key]:
                    return False
            except KeyError:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return (self['bandwidth'] < other['bandwidth'])

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __setitem__(self, key, value):
        self._data[key] = value

def export_to_file(filename):
    def func(playlist):
        with pathlib.Path(filename).open('w') as f:
            f.write('#EXTM3U\n')
            for item in playlist:
                f.write('#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=%d,RESOLUTION=%dx%d\n' %
                        (item['bandwidth'],item['width'],item['height']))
                f.write('%s\n' % (item['name']))
    return func

def list_changed_callback(f):
    def deco(*args, **kwargs):
        ret_val = f(*args, **kwargs)
        args[0]._callback()
        return ret_val
    return deco
  
class HLSPlaylist(collections.abc.MutableSequence):

    def __init__(self, list_changed_callback = None):
        self.list = list()
        self.callback_fnc = list_changed_callback

    def _callback(self):
        self.callback_fnc(sorted(self.list))

    def __getitem__(self, idx):
        return self.list[idx]
   
    @list_changed_callback
    def _setitem(self, idx, value):
        self.list[idx] = value

    def __setitem__(self, idx, value):
        if not self.list[idx] == value:
            self._setitem(idx, value)
    
    @list_changed_callback
    def insert(self, idx, value):
        self.list.insert(idx, value)
    
    @list_changed_callback
    def __delitem__(self, idx):
        del self.list[idx]
  
    def getPlaylistIndex(self, playlist):
        for idx,item in enumerate(self.list):
            if item['name'] == playlist:
                return idx
        return None

    def __len__(self):
        return len(self.list)


if __name__ == '__main__':
    playlists = HLSPlaylist(list_changed_callback =
            export_to_file('das_ist_ein_test.m3u'))

    a = PlaylistItem(
                    (('name', 'playlista'),
                    ('bandwidth', 300)))
    playlists.append(a)
    b = PlaylistItem(
                    (('name', 'playlistb'),
                    ('bandwidth', 100)))
    playlists.append(b)
    c = PlaylistItem(
                    (('name', 'playlistc'),
                    ('bandwidth', 600)))
    playlists.append(c)
    d = PlaylistItem(
                    (('name', 'playlistc'),
                    ('bandwidth', 600), ('asdf',400)))
    c_idx = playlists.getPlaylistIndex(c['name'])
    playlists[c_idx] = d
    playlists[c_idx] = d
    playlists[c_idx] = d
    d2 = PlaylistItem(
                    (('name', 'playlistc'),
                    ('bandwidth', 680), ('asdf',400)))

    if c in playlists:
        print('hallo')

