#!/usr/bin/env python3
# -*- coding: utf8 -*-

from transcoding_observer import *
from hls_playlist import analyse_input_format, HLSPlaylist

def m3u_get_items(filename):
    items = list()
    try:
        with pathlib.Path(filename).open('r') as f:
            for line in f:
                if line.strip().startswith('#'):
                    continue
                items.append(line)
    except FileNotFoundError:
        return None
    return items


def export_to_file(filename):
    def func(playlist):
        with pathlib.Path(filename).open('w') as f:
            f.write('#EXTM3U\n')
            for item in playlist:
                f.write('#EXT-X-STREAM-INF:BANDWIDTH=%d\n' % (item['bandwidth']))
                f.write('%s\n' % (item['name']))
    return func

class PlaylistManager(TranscodingObserver):

    def __init__(self, d):
        print('Create a playlist manager in directory: %s' % (d))
        self.global_playlist = None
        self.playlist_file = d / 'playlist.m3u'
        self.global_playlist = HLSPlaylist(list_changed_callback =
                export_to_file(self.playlist_file))

    def update(self, s):
        p = s.m3u_file_list
        print('new playlist: ', p)
        if p:
            self._update_playlists(p)
        
    def _update_playlists(self, files):
        # update playlists
        for playlist in files:
            hls_file_segment = m3u_get_items(playlist)
            if hls_file_segment is not None:
                print(hls_file_segment)
                stream_details = analyse_input_format(playlist.parent / hls_file_segment[0])
                item = PlaylistItem( (('name', playlist.name),
                    ('bandwidth', int(stream_details['format']['bit_rate']))) )
                idx = self.global_playlist.getPlaylistIndex(item['name'])
                if idx == None:
                    #print('Adding new element', item)
                    self.global_playlist.append(item)
                else:
                    #print('Updating existing element')
                    self.global_playlist[idx] = item
