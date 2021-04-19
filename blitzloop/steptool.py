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

import OpenGL.GL as gl
import os
import sys

from blitzloop import graphics, layout, mpvplayer, song, util


parser = util.get_argparser()
parser.add_argument(
    'songpath', metavar='SONGPATH', help='path to the song file')
parser.add_argument(
    'quant', metavar='QUANT', type=int, help='quantization of the song')
parser.add_argument(
    '--speed', default=1.0, type=float, help='divisor of the audio speed')
parser.add_argument(
    '--position', default=0.0, type=float,
    help='starting position in the song, in seconds')
opts = util.get_opts()

s = song.Song(opts.songpath, ignore_steps=True)
display = graphics.Display(1280,720)
renderer = graphics.get_renderer().KaraokeRenderer(display)
layout = layout.SongLayout(s, list(s.variants.keys())[-1], renderer)

step = 0

cur_beat = 0

compound = None
cidx = 0

mpv = mpvplayer.Player(None)
mpv.load_song(s)
mpv.set_speed(opts.speed)

if opts.position > 0.0:
    mpv.seek_to(opts.position)

def render():
    while True:
        gl.glClearColor(0, 0.3, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()
        renderer.draw(step, layout)
        mpv.poll()
        yield None

def round_beat(b):
    return song.MixedFraction(int(round(opts.quant * float(b))))

def save_and_quit():
    d = s.dump()
    s.save(opts.songpath + ".new")
    print("Saved!")
    mpv.shutdown()
    os._exit(0)

def key(k):
    global step, compound, cur_beat, cidx
    song_time = mpv.get_song_time() or 0
    beat = s.timing.time2beat(song_time)
    if k == ' ':
        if compound is not None:
            time = song.MixedFraction(round_beat(beat - cur_beat), opts.quant)
            cur_beat += time
            compound.timing.append(time)
            print(time, end=' ')
            sys.stdout.flush()
            if len(compound.timing) < (compound.steps-1):
                step += 1
                return
            elif len(compound.timing) == (compound.steps-1):
                step += 0.5
            else:
                step += 0.5
                compound = None
                cidx += 1
                if cidx >= len(s.compounds):
                    save_and_quit()
                print()
        if compound is None:
            start = song.MixedFraction(round_beat(beat), opts.quant)
            cur_beat = start
            compound = s.compounds[cidx]
            compound.start = start
            compound.timing = []
            compound.start_step = step
            print(start, " ", end=' ')
            sys.stdout.flush()
            if compound.steps == 1:
                step += 0.5
            else:
                step += 1
    elif k == 'KEY_ENTER':
        if compound and len(compound.timing) == (compound.steps - 1):
            time = song.MixedFraction(round_beat(beat - cur_beat), opts.quant)
            compound.timing.append(time)
            step += 0.5
            compound = None
            cidx += 1
            if cidx >= len(s.compounds):
                save_and_quit()
            print(time)
    elif k == '\x08':
        print("<Undo")
        if cidx == 0:
            if compound is None:
                new_time = max(0, song_time - 1)
            else:
                new_time = s.timing.beat2time(s.compounds[0].start) - 1
                compound = None
            step = 0
        elif cidx == 1 and compound is None:
            cidx = 0
            new_time = s.timing.beat2time(s.compounds[0].start) - 1
            step = 0
        else:
            if compound is None:
                cidx -= 1
            compound = None
            new_time = s.timing.beat2time(s.compounds[cidx - 1].end) - 1
            step = s.compounds[cidx - 1].start_step + s.compounds[cidx - 1].steps
        mpv.seek_to(new_time)
    elif k == 'KEY_LEFT':
        mpv.seek(-2)
    elif k == 'KEY_RIGHT':
        mpv.seek(2)
    elif k == 'KEY_ESCAPE':
        mpv.shutdown()
        os._exit(0)

for idx in range(len(s.channel_defaults)):
    mpv.set_channel(idx, 1.0)

mpv.set_pause(False)
display.set_render_gen(render)
display.set_keyboard_handler(key)
display.main_loop()
mpv.shutdown()
