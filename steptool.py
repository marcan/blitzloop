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

import time, sys, os.path
import song, graphics, layout, texture_font
import OpenGL.GL as gl

s = song.Song(sys.argv[1], ignore_steps=True)
quant = int(sys.argv[2])
speed = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.0
pos = float(sys.argv[4]) if len(sys.argv) >= 5 else 0.0


a = AudioEngine()
a.set_speed(speed)
a.set_mic_volume(0)

print "Sample Rate: %dHz" % a.sample_rate

print "Loading audio file..."
file = AudioFile(s.audiofile, a.sample_rate, pos)
print "Loaded"

display = graphics.Display(1280,720)
renderer = layout.Renderer(display)
layout = layout.SongLayout(s, s.variants.keys()[-1], renderer)

step = 0

cur_beat = 0

compound = None
compounds = iter(s.compounds)

def render():
    while True:
        gl.glClearColor(0, 0.3, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        renderer.draw(step, layout)
        yield None

def round_beat(b):
    return song.MixedFraction(int(round(quant * float(b))))

def key(k):
    global step, compound, cur_beat
    song_time = a.song_time() or 0
    beat = s.timing.time2beat(song_time)
    if k == ' ':
        if compound is not None:
            time = song.MixedFraction(round_beat(beat - cur_beat), quant)
            cur_beat += time
            compound.timing.append(time)
            print time,
            sys.stdout.flush()
            if len(compound.timing) < (compound.steps-1):
                step += 1
                return
            elif len(compound.timing) == (compound.steps-1):
                step += 0.5
            else:
                step += 0.5
                compound = None
                print
        if compound is None:
            start = song.MixedFraction(round_beat(beat), quant)
            cur_beat = start
            try:
                compound = compounds.next()
            except StopIteration:
                d = s.dump()
                s.save(sys.argv[1] + ".new")
                return
            compound.start = start
            compound.timing = []
            print start, " ",
            sys.stdout.flush()
            if compound.steps == 1:
                step += 0.5
            else:
                step += 1
        song_time = a.song_time() or 0
        beat = s.timing.time2beat(song_time)
    elif k == '\r':
        if compound and len(compound.timing) == (compound.steps - 1):
            time = song.MixedFraction(round_beat(beat - cur_beat), quant)
            compound.timing.append(time)
            step += 0.5
            compound = None
            print time

a.play(file)
display.set_render_gen(render)
display.set_keyboard_handler(key)
display.main_loop()

