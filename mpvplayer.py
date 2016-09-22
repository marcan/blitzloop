#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2016 Hector Martin "marcan" <marcan@marcan.st>
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
import mpv
import time
import OpenGL.GL as gl

class Player(object):
    def __init__(self, song, display):
        self.song = song
        self.mpv = mp = mpv.Context()
        mp.initialize()
        self.display = display
        self.fade_in = 1
        self.fade_out = 1
        self.offset = 0
        self.song_time = None
        if "fade_in" in song.song:
            self.fade_in = float(song.song["fade_in"])
        if "fade_out" in song.song:
            self.fade_out = float(song.song["fade_out"])

        self.set_pause(True)
        mp.set_property("audio-file-auto", "no")
        mp.set_property("terminal", True)
        mp.set_property("quiet", True)
        mp.set_property("vo", "opengl-cb")
        mp.set_property("ao", "jack")
        mp.set_property("af", "@pan:pan=2:[1,0,0,1,0,0,0,0],@rb:rubberband")
        mp.set_property("video-sync", "display-vdrop")
        mp.set_property("display-fps", 60)
        self.poll_props = {"audio-pts": None, "eof-reached": None}
        for i in self.poll_props:
            mp.get_property_async(i)

        def gpa(name):
            return display.get_proc_address(name)
        self.gl = mp.opengl_cb_api()
        self.gl.init_gl(None, gpa)

        # Load just the audio first to find out the duration lower bound
        mp.command('loadfile', song.audiofile)
        self.duration = self._getprop("duration")

        if "video_offset" in song.song:
            self.offset = float(song.song["video_offset"])
            mp.set_property("audio-delay", self.offset)
        if song.videofile is not None and song.audiofile != song.videofile:
            mp.set_property("audio-file", song.audiofile)
            mp.command('loadfile', song.videofile)

        self.duration = min(self.duration, self._getprop("duration"))

        if "duration" in song.song:
            self.duration = float(song.song["duration"])

        ch = self._getprop("audio-params/channel-count")
        assert ch == 1 or (ch % 2 == 0)
        self.channels = ((ch + 1) // 2) - 1
        self.volumes = [0] * self.channels
        self.set_channel(0, 1)

        w = self._getprop("video-params/w")
        h = self._getprop("video-params/h")
        aspect = self._getprop("video-params/aspect")

        if song.aspect:
            if song.aspect > aspect:
                nh = int(h * (aspect / song.aspect))
                mp.set_property("vf", "crop=%d:%d" % (w, nh))
            elif aspect > song.aspect:
                nw = int(w * (song.aspect / aspect))
                mp.set_property("vf", "crop=%d:%d" % (nw, h))
            self.aspect = song.aspect
        else:
            self.aspect = aspect

    def _getprop(self, p):
        while True:
            try:
                return self.mpv.get_property(p)
            except mpv.MPVError: # Wait until available
                continue

    def play(self):
        self.set_pause(False)

    def set_pause(self, pause):
        self.mpv.set_property("pause", pause, async=True)

    def set_pitch(self, pitch):
        self.mpv.command("af-command", "rb", "set-pitch", str(pitch))

    def set_channel(self, channel, value):
        if self.channels == 0:
            return
        self.volumes[channel] = value
        if self.channels == 1:
            mtx = [1-value, 0, 0, 1-value, value, 0, 0, value]
        else:
            mtx = [1, 0, 0, 1]
            for v in self.volumes:
                mtx += [v, 0, 0, v]
        self.mpv.command("af-command", "pan", "set-matrix", ",".join(map(str, mtx)))

    def set_speed(self, speed):
        self.mpv.set_property("speed", 1.0/speed)

    def seek(self, offset):
        self.mpv.command("seek", offset, async=True)
    
    def seek_to(self, t):
        self.mpv.set_property("time-pos", t)

    def poll(self):
        repoll = set()
        while True:
            ev = self.mpv.wait_event(0)
            if ev.id == mpv.Events.none:
                break
            if (ev.id == mpv.Events.get_property_reply
                and ev.data.name in self.poll_props):
                self.poll_props[ev.data.name] = ev.data.data
                repoll.add(ev.data.name)
        for i in repoll:
            self.mpv.get_property_async(i)

    def flip(self):
        self.gl.report_flip(0)

    def draw(self):
        self.gl.draw(0, self.display.win_width, -self.display.win_height)

    def draw_fade(self, songtime):
        brightness = 1
        if songtime > (self.duration - self.fade_out) and self.fade_out:
            brightness *= max(0, min(1, (self.duration - songtime) / self.fade_out))
        if self.offset < 0:
            songtime += self.offset
        if songtime < self.fade_in and self.fade_in:
            brightness *= max(0, min(1, songtime / self.fade_in))
        if brightness != 1:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA);
            gl.glColor4f(0, 0, 0, 1 - brightness)
            gl.glBegin(gl.GL_TRIANGLE_FAN)
            gl.glVertex2f(0, 0)
            gl.glVertex2f(1, 0)
            gl.glVertex2f(1, 1)
            gl.glVertex2f(0, 1)
            gl.glEnd()

    def get_song_time(self):
        return self.poll_props["audio-pts"]

    def eof_reached(self):
        return self.poll_props["eof-reached"] or self.get_song_time() > self.duration

    def shutdown(self):
        self.gl.uninit_gl()
        self.mpv.shutdown()

