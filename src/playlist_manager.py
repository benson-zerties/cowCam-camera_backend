#!/usr/bin/env python3
# -*- coding: utf8 -*-

import pathlib
import itertools

from transcoding_observer import *
from hls_playlist import analyse_input_format, HLSPlaylist, PlaylistItem, export_to_file

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


class PlaylistManager(TranscodingObserver):

    def __init__(self, d):
        self.global_playlist = None
        self.playlist_file = d / 'playlist.m3u8'
        self.global_playlist = HLSPlaylist(list_changed_callback =
                export_to_file(self.playlist_file))

    def update(self, s):
        proc_desc = s.processFactories
        list_of_lists = [p.fileList() for p in proc_desc]
        combined = list(itertools.chain.from_iterable(list_of_lists))
        if combined:
            self._update_playlists(combined)
        
    def _update_playlists(self, files):
        # update playlists
        for playlist in files:
            hls_file_segment = m3u_get_items(playlist)
            if hls_file_segment is not None:
                print(hls_file_segment)
                stream_details = analyse_input_format(playlist.parent / hls_file_segment[0])
                item = PlaylistItem( playlist.name, stream_details )
                idx = self.global_playlist.getPlaylistIndex(item['name'])
                if idx == None:
                    self.global_playlist.append(item)
                else:
                    self.global_playlist[idx] = item
