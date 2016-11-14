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
import sys, os
import song, graphics, layout, ffmsvideo, mpvplayer
import OpenGL.GL as gl
import subprocess

s = song.Song(sys.argv[1])
output = sys.argv[2]
width = int(sys.argv[3])
height = int(sys.argv[4])
fps = float(sys.argv[5])
variant = int(sys.argv[6]) if len(sys.argv) > 6 else 0

headstart = 0.3

display = graphics.Display(width,height,False)

renderer = layout.Renderer(display)
layout = layout.SongLayout(s, list(s.variants.keys())[variant], renderer)

mpv = mpvplayer.Player(None)
mpv.load_song(s)
length = mpv.duration
mpv.shutdown()

if s.videofile is not None:
    v = ffmsvideo.BackgroundVideo(s)
else:
    v = None

song_time = 0

x264 = subprocess.Popen([
    "x264",
    "--crf", "22",
    "--profile", "high",
    "-o", output,
    "--demuxer", "raw",
    "--input-csp", "rgb",
    "--input-res", "%dx%d" % (width, height),
    "-",
    ], stdin=subprocess.PIPE)

def render():
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
    for i in range(10):
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        yield
    try:
        song_time = 0
        while song_time < length:
            gl.glClearColor(0, 0, 0, 1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.glOrtho(0, 1, height / width, 0, -1, 1)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            if v:
                v.draw(song_time, display, length)
            renderer.draw(song_time + headstart, layout)
            gl.glFinish()
            gl.glReadBuffer(gl.GL_BACK)
            data = gl.glReadPixelsub(0, 0, width, height, gl.GL_RGB)
            print("\r%.02f%%" % (100 * song_time / length), end=' ')
            sys.stdout.flush()
            x264.stdin.write(data)
            song_time += 1/fps
            #yield
    except Exception as e:
        print e
    finally:
        x264.stdin.close()
        x264.wait()
        os._exit(0)

display.set_render_gen(render)
display.main_loop()
