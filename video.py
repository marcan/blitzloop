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

import threading, time
import ffms
import OpenGL.GL as gl

class VideoThread(threading.Thread):
    def __init__(self, source, maxframe):
        self.source = source
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.fn = 0
        self.count = 10
        self.frames = {}
        self.die = False
        self.maxframe = maxframe
        threading.Thread.__init__(self)

    def run(self):
        with self.lock:
            while not self.die:
                while len(self.frames) >= self.count and not self.die:
                    self.cond.wait()
                if self.die:
                    return
                if self.fn not in self.frames:
                    fn = self.fn
                    self.fn += 1
                    self.lock.release()
                    t = time.time()
                    frame = self.source.get_frame(fn).planes[0].copy()
                    print "Frame %d decode time: %f" % (fn, time.time() - t)
                    self.lock.acquire()
                    self.frames[fn] = frame
                else:
                    self.fn += 1

    def get_frame(self, num):
        with self.lock:
            if num in self.frames:
                for i in self.frames.keys():
                    if i < num or i >= (num + self.count):
                        del self.frames[i]
                self.cond.notifyAll()
                return self.frames[num]
            else:
                best = None
                for i in self.frames.keys():
                    if best is None or abs(num - i) < abs(num - best):
                        best = i
                if best is None:
                    print "Dropped video frame %d" % num
                    return None
                ret = self.frames[best]
                print "Dropped video frame %d, got %d" % (num, best)
                for i in self.frames.keys():
                    if i < best or i >= (num + self.count/2):
                        del self.frames[i]
                self.fn = min(num + 2, self.maxframe)
                self.cond.notifyAll()
                return ret

    def stop(self):
        with self.lock:
            self.die = True
            self.cond.notify()

class BackgroundVideo(object):
    def __init__(self, song, async=True):
        self.offset = 0
        self.fade_in = 1
        self.fade_out = 1
        if "video_offset" in song.song:
            self.offset = float(song.song["video_offset"])
        if "fade_in" in song.song:
            self.fade_in = float(song.song["fade_in"])
        if "fade_out" in song.song:
            self.fade_out = float(song.song["fade_out"])
        self.vsource = ffms.VideoSource(song.videofile)
        self.vsource.set_output_format([ffms.get_pix_fmt("bgr32")])
        self.frameno = 0
        self.frame = None
        self.timecodes = self.vsource.track.timecodes
        self.texid = gl.glGenTextures(1)
        frame = self.vsource.get_frame(0)
        self.width = frame.ScaledWidth
        self.height = frame.ScaledHeight
        self.frame = frame.planes[0].copy()
        self.sar = self.vsource.properties.SARNum / float(self.vsource.properties.SARDen)
        if self.sar == 0:
            self.sar = 1
        self.aspect = self.sar * self.width / float(self.height)
        if async:
            self.vthread = VideoThread(self.vsource, len(self.timecodes)-1)
            self.vthread.start()
        else:
            self.vthread = False

    def advance(self, time):
        time = int(round(time * 1000))
        if self.frameno >= len(self.timecodes)-1:
            return
        cur_frame = self.frameno
        while time > self.timecodes[self.frameno+1]:
            self.frameno += 1
            if self.frameno >= len(self.timecodes)-1:
                break
        #print time, self.frameno, self.timecodes[self.frameno]
        if self.frameno != cur_frame:
            if self.vthread is not None:
                frame = self.vthread.get_frame(self.frameno)
                if frame is not None:
                    self.frame = frame
            else:
                self.frame = self.vsource.get_frame(self.frameno).planes[0].copy()

    def draw(self, time, display, song_length):
        brightness = 1
        last_frame = self.timecodes
        if time > (song_length - self.fade_out) and self.fade_out:
            brightness *= max(0, min(1, (song_length - time) / self.fade_out))
        if self.offset < 0:
            time += self.offset
        if time < self.fade_in and self.fade_in:
            brightness *= max(0, min(1, time/self.fade_in))
        if self.offset > 0:
            time += self.offset

        self.advance(time)
        data = self.frame
        gl.glDisable(gl.GL_BLEND)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP);

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, 3,
                        self.width, self.height, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBegin(gl.GL_TRIANGLE_STRIP)
        h = self.height / float(self.width) / self.sar
        dh = display.height / float(display.width)
        offset = (dh-h) / 2
        gl.glColor4f(brightness,brightness,brightness,1)
        gl.glTexCoord2f(0,1)
        gl.glVertex2f(0,offset)
        gl.glTexCoord2f(1,1)
        gl.glVertex2f(1,offset)
        gl.glTexCoord2f(0,0)
        gl.glVertex2f(0,offset+h)
        gl.glTexCoord2f(1,0)
        gl.glVertex2f(1,offset+h)
        gl.glEnd()
        gl.glDisable(gl.GL_TEXTURE_2D)

    def __del__(self):
        gl.glDeleteTextures(self.texid)
        self.vthread.stop()
