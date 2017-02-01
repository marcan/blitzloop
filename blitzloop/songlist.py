#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Hector Martin "marcan" <hector@marcansoft.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os
import threading

from blitzloop.song import Song


class SongDatabase(object):
    def __init__(self, root):
        self.songs = []
        self.load(root)

    def load(self, root):
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            for name in filenames:
                if not name.endswith(".blitz"):
                    continue
                path = os.path.join(dirpath, name)
                print(path)
                song = Song(path)
                song.id = len(self.songs)
                self.songs.append(song)

class SongQueueEntry(object):
    def __init__(self, song):
        self.song = song
        self.qid = None
        self.variant = 0
        self.channels = [3]
        self.speed = 0
        self.pitch = 0
        self.pause = False
        self.stop = False
        self.commands = []

class SongQueue(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.queue = []
        self.qid = 0
        self.qidmap = {}

    def add(self, queue_entry):
        with self.lock:
            queue_entry.qid = self.qid
            self.qid += 1
            self.queue.append(queue_entry)
            self.qidmap[queue_entry.qid] = queue_entry

    def remove(self, qid):
        with self.lock:
            entry = self.qidmap[qid]
            index = self.queue.index(entry)
            entry.stop = True
            del self.queue[index]
            del self.qidmap[qid]

    def pop(self, qid):
        with self.lock:
            top = self.queue[0]
            if top.qid == qid:
                del self.queue[0]
                del self.qidmap[top.qid]

    def get(self, qid):
        return self.qidmap[qid]

    def index(self, qid):
        with self.lock:
            return self.queue.index(self.qidmap[qid])

    def __len__(self):
        return len(self.queue)

    def __getitem__(self, idx):
        return self.queue[0]

    def __iter__(self):
        return iter(self.queue)

