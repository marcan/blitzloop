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

import web
import sys, os
import graphics, layout, video, songlist, idlescreen

fullscreen = False
if sys.argv[1] == "-fs":
    sys.argv = sys.argv[1:]
    fullscreen = True

songs_dir = sys.argv[1]
width = int(sys.argv[2])
height = int(sys.argv[3])

print "Loading song DB..."
song_database = songlist.SongDatabase(sys.argv[1])
print "Done."

display = graphics.Display(width, height, fullscreen)
renderer = layout.Renderer(display)

audio = AudioEngine()
print "Engine sample rate: %dHz" % audio.sample_rate

queue = songlist.SongQueue()

class AudioConfig(object):
    def __init__(self):
        self.volume = 50
        self.mic_volume = 80
        self.mic_feedback = 20
        self.mic_delay = 12
        self.headstart = 30

    def update(self, song=None):
        if song is None or "volume" not in song.song:
            audio.set_volume(self.volume / 200.0)
        else:
            audio.set_volume(self.volume / 200.0 * float(song.song["volume"]))
        audio.set_mic_volume(self.mic_volume / 100.0)
        audio.set_mic_feedback(self.mic_feedback / 100.0)
        audio.set_mic_delay(self.mic_delay / 100.0)

audio_config = AudioConfig()

web.database = song_database
web.queue = queue
web.audio_config = audio_config
server = web.ServerThread(host="0.0.0.0", port=10111, server="paste")
server.start()

idle_screen = idlescreen.IdleScreen(display)

def main_render():
    # Wait for element in queue
    print "Waiting for song to appear in queue..."
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

    print "Loading audio file..."
    audiofile = AudioFile(qe.song.audiofile, audio.sample_rate)
    length = audiofile.frames / float(audiofile.rate)

    if qe.song.videofile is not None:
        print "Loading video file..."
        videofile = video.BackgroundVideo(qe.song)
        display.set_aspect(videofile.aspect)
    else:
        videofile = None
        display.set_aspect(None)

    if qe.song.aspect:
        display.set_aspect(float(qe.song.aspect))

    print "Laying out song..."
    renderer.reset()
    variant_key = qe.song.variants.keys()[qe.variant]
    song_layout = layout.SongLayout(qe.song, variant_key, renderer)
    print "Loaded."

    audio.play(audiofile)
    song_time = 0
    while audio.is_playing() and not qe.stop:
        song_time = audio.song_time() or song_time
        if videofile:
            videofile.draw(song_time, display, length)
        speed = 2**(qe.speed / 12.0)
        renderer.draw(song_time + audio_config.headstart / 100.0 * speed, song_layout)

        audio.set_speed(1.0 / speed)
        audio.set_pitch(2**(qe.pitch/12.0))
        for i, j in enumerate(qe.channels):
            audio.set_channel(i, j/10.0)
        audio.set_pause(qe.pause)
        audio_config.update(qe.song)
        yield None
    yield None
    yield None
    print "Song complete."
    try:
        queue.pop(qe.qid)
    except (IndexError, KeyError):
        pass
    audio.stop()
    audiofile.close()
    display.set_aspect(None)

def main():
    while True:
        for i in main_render():
            yield i

def key(k):
    if k == '\033':
        audio.shutdown()
        os._exit(0)

display.set_render_gen(main)
display.set_keyboard_handler(key)
display.main_loop()
