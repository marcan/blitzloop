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

from blitzloop import graphics, idlescreen, layout, mpvplayer, songlist, util, web
from blitzloop._audio import *


parser = util.get_argparser()
parser.add_argument(
    '--songdir', default=os.path.expanduser('~/.blitzloop/songs'),
    help='directory with songs')
parser.add_argument('--port', default=10111, help='port for the UI')
parser.add_argument(
    '--width', default=1024, help='width of blitzloop window (ignored in fs)')
parser.add_argument(
    '--height', default=768, help='height of blitzloop window (ignored in fs)')
parser.add_argument(
    '--no-audioengine', default=False, action="store_true",
    help='Disable JACK-based audio engine (mic echo effect)')
opts = util.get_opts()

fullscreen = opts.fullscreen
songs_dir = os.path.expanduser(opts.songdir)
width = int(opts.width)
height = int(opts.height)

print("Loading song DB...")
song_database = songlist.SongDatabase(songs_dir)
print("Done.")

display = graphics.Display(width, height, fullscreen)
renderer = graphics.get_renderer().KaraokeRenderer(display)
mpv = mpvplayer.Player(display)

if not opts.no_audioengine:
    audio = AudioEngine()
    print("Engine sample rate: %dHz" % audio.sample_rate)

queue = songlist.SongQueue()

class AudioConfig(object):
    def __init__(self):
        self.volume = 50
        self.mic_volume = 80
        self.mic_feedback = 20
        self.mic_delay = 12
        self.headstart = 30

    def update(self, song=None):
        mpv.set_volume(self.volume / 200.0)
        if not opts.no_audioengine:
            audio.set_mic_volume(self.mic_volume / 100.0)
            audio.set_mic_feedback(self.mic_feedback / 100.0)
            audio.set_mic_delay(self.mic_delay / 100.0)

audio_config = AudioConfig()

web.database = song_database
web.queue = queue
web.audio_config = audio_config
server = web.ServerThread(host="0.0.0.0", port=opts.port, server="paste")
server.start()

idle_screen = idlescreen.IdleScreen(display)

def main_render():
    # Wait for element in queue
    print("Waiting for song to appear in queue...")
    qe = None
    with queue.lock:
        if len(queue) != 0:
            qe = queue[0]
    if not qe:
        idle_screen.reset()
        for f in idle_screen:
            audio_config.update()
            yield None
            if not qe:
                with queue.lock:
                    if len(queue) != 0:
                        qe = queue[0]
                        idle_screen.close()
    yield None
    yield None

    print("Loading audio/video...")
    mpv.load_song(qe.song)
    display.set_aspect(mpv.aspect)

    print("Laying out song...")
    renderer.reset()
    variant_key = list(qe.song.variants.keys())[qe.variant]
    song_layout = layout.SongLayout(qe.song, variant_key, renderer)
    print("Loaded.")

    def update_params():
        mpv.set_speed(1.0 / (2**(qe.speed / 12.0)))
        mpv.set_pitch(2**(qe.pitch / 12.0))
        for i, j in enumerate(qe.channels):
            mpv.set_channel(i, j / 10.0)
        mpv.set_pause(qe.pause)

    update_params()
    song_time = -10
    stopping = False
    while not (mpv.eof_reached() or (stopping and qe.pause)):
        while qe.commands:
            cmd, arg = qe.commands.pop(0)
            if cmd == "seek":
                mpv.seek(arg)
            elif cmd == "seekto":
                mpv.seek_to(arg)
        mpv.draw()
        mpv.poll()
        song_time = mpv.get_song_time() or song_time

        if qe.stop and not stopping:
            stopping = True
            mpv.fade_out = 2
            mpv.duration = min(mpv.duration, song_time + 2)

        if not stopping:
            mpv.draw_fade(song_time)

        speed = 2**(qe.speed / 12.0)
        renderer.draw(song_time + audio_config.headstart / 100.0 * speed, song_layout)

        if stopping:
            fade = mpv.draw_fade(song_time)
            mpv.set_fadevol(max(fade * 1.3 - 0.3, 0))

        update_params()
        audio_config.update(qe.song)
        yield None
        mpv.flip()

    yield None
    yield None
    print("Song complete.")
    try:
        queue.pop(qe.qid)
    except (IndexError, KeyError):
        pass
    mpv.stop()
    display.set_aspect(None)

def main():
    while True:
        for i in main_render():
            yield i

def key(k):
    if k == b'\x1b':
        mpv.shutdown()
        if not opts.no_audioengine:
            audio.shutdown()
        os._exit(0)

display.set_render_gen(main)
display.set_keyboard_handler(key)
display.main_loop()
