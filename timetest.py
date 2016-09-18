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

from _audio import *

import time, sys
import song

s = song.Song(sys.argv[1], ignore_steps=True)
a = AudioEngine()

print "Sample Rate: %dHz" % a.sample_rate

print "Loading audio file..."
file = AudioFile(s.audiofile, a.sample_rate)
print "Loaded"

a.play(file)
try:
    while True:
        song_time = a.song_time() or 0
        beat = s.timing.time2beat(song_time)
        print beat
        time.sleep(0.01)
finally:
    a.shutdown()