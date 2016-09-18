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

import sys

a = AudioEngine()
a.set_mic_volume(0)

print "Sample Rate: %dHz" % a.sample_rate

print "Loading audio file..."
file = AudioFile(sys.argv[1], a.sample_rate)
print "Loaded"

a.play(file)

def build_bpms(beats):
    endpos = beats[-1]
    tolerance = 0.2
    beats = [(beats[i], beats[i+1] - beats[i]) for i in range(len(beats)-1)]
    fbeats = beats
    oldlen = 0
    print >>sys.stderr, "Got %d beats" % len(beats)
    while oldlen != len(fbeats):
        oldlen = len(fbeats)
        avg = sum(l for s,l in fbeats) / len(fbeats)
        fbeats = [b for b in fbeats if abs(avg-b[1]) < avg*tolerance]
    print >>sys.stderr, "After filtering, %d valid beats avg %fBPM" % (len(fbeats), 60.0/avg)
    off = fbeats[0][0]
    error = 0
    for start, length in fbeats:
        beat = (start - off) / avg
        ibeat = int(round(beat))
        error += beat - ibeat
    off += error / len(fbeats)
    last = int(round((endpos - off) / avg))
    last_time = off + avg * last
    print >>sys.stderr, "Offset %f, %d beats" % (off, last + 1)
    while off > avg:
        off -= avg
        last += 1
    return off, last_time, last
    #print "@%f=0" % off
    #print "@%f=%d" % (last_time, last)

off_t = 0
beats = [(off_t, [])]
try:
    while True:
        v = raw_input()
        t = a.song_time()
        if v == "n":
            off_t = beats[-1][1][-1] +beats[-1][0]
            beats.append((off_t, []))
        beats[-1][1].append(t - off_t)
except KeyboardInterrupt:
    print "KeyboardInterrupt!"
    a.shutdown()
    file.close()
finally:
    beat = 0
    bmap = []
    t = 0
    for off, beatlist in beats:
        if len(beatlist) < 2:
            continue
        first_t, last_t, last = build_bpms(beatlist)
        bmap.append((off + first_t - t, beat))
        bmap.append((last_t - first_t, last))
        beat = 1
        t = off + last_t

    i = 0
    last = None
    t = 0
    beat = 0
    for i, (when, delta) in enumerate(bmap):
        t += when
        if i != 0 and when < last * 0.1 and delta == 1:
            continue
        beat += delta
        print "@%f=%d" % (t, beat)
        last = when
    #print "@%f=%d" % (last_time, last)
