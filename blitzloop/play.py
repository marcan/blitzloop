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
import time

from blitzloop import graphics, layout, mpvplayer, song, util

parser = util.get_argparser()
parser.add_argument(
    '--show-timings', dest='st', action='store_true',
    help='show mpv timings')
parser.add_argument('songpath', help='path to the song file')
parser.add_argument('offset', nargs='?', default=0, help='song offset')
parser.add_argument('variant', nargs='?', default=0, help='song variant')
opts = util.get_opts()

fullscreen = opts.fullscreen
s = song.Song(opts.songpath)

offset = float(opts.offset)
variant = int(opts.variant)

headstart = 0.3

if fullscreen:
    display = graphics.Display(1920, 1200, fullscreen, None)
else:
    display = graphics.Display(1280, 720, fullscreen, None)
print(display.width, display.height)

mpv = mpvplayer.Player(display)
mpv.load_song(s)

display.set_aspect(mpv.aspect)

renderer = graphics.get_renderer().KaraokeRenderer(display)
layout = layout.SongLayout(s, list(s.variants.keys())[variant], renderer)

song_time = -10

speed_i = 0
pitch_i = 0
vocals_i = 10

if offset:
    mpv.seek_to(offset)

def render():
    t = time.time()
    global song_time
    while not mpv.eof_reached():
        graphics.get_renderer().clear(0, 0, 0, 1)
        t1 = time.time()
        mpv.draw()
        dt = time.time() - t1
        mpv.poll()
        song_time = mpv.get_song_time() or song_time
        mpv.draw_fade(song_time)
        renderer.draw(song_time + headstart * 2**(speed_i/12.0), layout)
        yield None
        t2 = time.time()
        if opts.st:
            print("T:%7.3f/%7.3f B:%7.3f FPS:%.2f draw:%.3f" % (song_time, mpv.duration, s.timing.time2beat(song_time), (1.0/(t2-t)), dt))
        t = t2
        mpv.flip()
    mpv.shutdown()
    os._exit(0)

pause = False

def key(k):
    import OpenGL.GLUT as glut
    global speed_i, pitch_i, vocals_i, pause
    if k == b'\x1b':
        mpv.shutdown()
        os._exit(0)
    if k == b'[' and speed_i > -12:
        speed_i -= 1
        print("Speed: %d" % speed_i)
        mpv.set_speed(2**(-speed_i/12.0))
    elif k == b']' and speed_i < 12:
        speed_i += 1
        print("Speed: %d" % speed_i)
        mpv.set_speed(2**(-speed_i/12.0))
    elif k == glut.GLUT_KEY_UP and pitch_i < 12:
        pitch_i += 1
        print("Pitch: %d" % pitch_i)
        mpv.set_pitch(2**(pitch_i/12.0))
    elif k == glut.GLUT_KEY_DOWN and pitch_i > -12:
        pitch_i -= 1
        print("Pitch: %d" % pitch_i)
        mpv.set_pitch(2**(pitch_i/12.0))
    elif k == b'+' and vocals_i < 30:
        vocals_i += 1
        print("Vocals: %d" % vocals_i)
        mpv.set_channel(0, vocals_i/10.0)
    elif k == b'-' and vocals_i > 0:
        vocals_i -= 1
        print("Vocals: %d" % vocals_i)
        mpv.set_channel(0, vocals_i/10.0)
    elif k == glut.GLUT_KEY_LEFT:
        mpv.seek(-10)
    elif k == glut.GLUT_KEY_RIGHT:
        mpv.seek(10)
    elif k == b' ':
        pause = not pause
        t = time.time()
        mpv.set_pause(pause)
        print("P %.03f" % (time.time()-t))

mpv.play()
display.set_render_gen(render)
display.set_keyboard_handler(key)
display.main_loop()
mpv.shutdown()
