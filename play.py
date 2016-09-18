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

import time, sys, os
import song, graphics, layout, video
import OpenGL.GL as gl
import OpenGL.GLUT as glut

fullscreen = False
if sys.argv[1] == "-fs":
    sys.argv = sys.argv[1:]
    fullscreen = True

s = song.Song(sys.argv[1])

if s.videofile is not None:
    v = video.BackgroundVideo(s)
    aspect = v.aspect
else:
    v = None
    aspect = None

if s.aspect:
    aspect = s.aspect

offset = float(sys.argv[2]) if len(sys.argv) >= 3 else 0
variant = int(sys.argv[3]) if len(sys.argv) >= 4 else 0

headstart = 0.3

a = AudioEngine()
a.set_mic_volume(0)

print "Sample Rate: %dHz" % a.sample_rate

print "Loading audio file..."
file = AudioFile(s.audiofile, a.sample_rate, offset)
length = file.frames / float(file.rate)
print "Loaded"

if fullscreen:
    display = graphics.Display(1920, 1200, fullscreen, aspect)
else:
    display = graphics.Display(1280, 720, fullscreen, aspect)
print display.width, display.height
renderer = layout.Renderer(display)
layout = layout.SongLayout(s, s.variants.keys()[variant], renderer)

song_time = 0

speed_i = 0
pitch_i = 0
vocals_i = 10

t = time.time()

def render():
    global song_time
    while True:
        song_time = a.song_time() or song_time
        print "%4.3f %4.3f"%(song_time, s.timing.time2beat(song_time))
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        if v:
            v.draw(song_time, display, length)
        renderer.draw(song_time + headstart * 2**(speed_i/12.0), layout)
        yield None

a.set_channel(0, vocals_i/10.0)

pause = False

def key(k):
    global speed_i, pitch_i, vocals_i, pause
    if k == '\033':
        a.shutdown()
        os._exit(0)
    if k == glut.GLUT_KEY_LEFT and speed_i > -12:
        speed_i -= 1
        print "Speed: %d" % speed_i
        a.set_speed(2**(-speed_i/12.0))
    elif k == glut.GLUT_KEY_RIGHT and speed_i < 12:
        speed_i += 1
        print "Speed: %d" % speed_i
        a.set_speed(2**(-speed_i/12.0))
    elif k == glut.GLUT_KEY_UP and pitch_i < 12:
        pitch_i += 1
        print "Pitch: %d" % pitch_i
        a.set_pitch(2**(pitch_i/12.0))
    elif k == glut.GLUT_KEY_DOWN and pitch_i > -12:
        pitch_i -= 1
        print "Pitch: %d" % pitch_i
        a.set_pitch(2**(pitch_i/12.0))
    elif k == '+' and vocals_i < 30:
        vocals_i += 1
        print "Vocals: %d" % vocals_i
        a.set_channel(0, vocals_i/10.0)
    elif k == '-' and vocals_i > 0:
        vocals_i -= 1
        print "Vocals: %d" % vocals_i
        a.set_channel(0, vocals_i/10.0)
    elif k == ' ':
        pause = not pause
        a.set_pause(pause)

try:
    a.play(file)
    display.set_render_gen(render)
    display.set_keyboard_handler(key)
    display.main_loop()
finally:
    a.shutdown()

