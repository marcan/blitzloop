#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 Hector Martin "marcan" <hector@marcansoft.com>
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

import os, platform

from blitzloop import util
import blitzloop.backend.gles_fixes

import OpenGL.GLES2 as gl
import OpenGL.EGL as egl
import glfw
import sys
from ctypes import c_void_p

from blitzloop.backend.common import *

GLFW_CONTEXT_CREATION_API = 0x0002200B
GLFW_EGL_CONTEXT_API = 0x00036002

class Display(BaseDisplay):
    KEYMAP = {
        glfw.KEY_ESCAPE: "KEY_ESCAPE",
        glfw.KEY_ENTER: "KEY_ENTER",
        glfw.KEY_UP: "KEY_UP",
        glfw.KEY_DOWN: "KEY_DOWN",
        glfw.KEY_LEFT: "KEY_LEFT",
        glfw.KEY_RIGHT: "KEY_RIGHT",
    }
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        if not glfw.init():
            raise Exception("GLFW init failed")

        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_ES_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        glfw.window_hint(glfw.DEPTH_BITS, 24)
        glfw.window_hint(glfw.ALPHA_BITS, 0)
        if platform.system() == "Linux":
            try:
                glfw.window_hint(GLFW_CONTEXT_CREATION_API, GLFW_EGL_CONTEXT_API)
            except:
                pass

        monitor = glfw.get_primary_monitor() if fullscreen else None
        self.window = glfw.create_window(width, height, "BlitzLoop Karaoke",
                                         monitor, None)
        glfw.make_context_current(self.window)
        BaseDisplay.__init__(self, width, height, fullscreen, aspect)
        self._on_reshape(self.window, width, height)
        if fullscreen:
            self.saved_size = (0, 0, width, height)
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)

        glfw.set_key_callback(self.window, self._on_keyboard)
        glfw.set_window_pos_callback(self.window, self._on_move)
        glfw.set_window_size_callback(self.window, self._on_reshape)

        self._initialize()

    def toggle_fullscreen(self):
        if self.fullscreen:
            glfw.set_window_monitor(self.window, None, *self.saved_size,
                                    util.get_opts().fps)
        else:
            self.saved_size = self.x, self.y, self.win_width, self.win_height
            monitor = glfw.get_primary_monitor()
            mode = glfw.get_video_mode(monitor)
            glfw.set_window_monitor(self.window, monitor, 0, 0,
                                    mode.size.width, mode.size.height,
                                    mode.refresh_rate)

        self.fullscreen = not self.fullscreen

    def _on_move(self, window, x, y):
        self.x = x
        self.y = y

    def _on_reshape(self, window, width, height):
        self.win_width = width
        self.win_height = height
        self.gl.glViewport(0, 0, width, height)
        self.set_aspect(self.aspect)

    def _on_keyboard(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return
        if self.kbd_handler:
            if key in self.KEYMAP:
                key = self.KEYMAP[key]
            else:
                key = chr(key).lower()
            self.kbd_handler(key)
        elif key == glfw.KEY_ESCAPE:
            if self.exit_handler:
                self.exit_handler()
            os._exit(0)

    def _render(self):
        try:
            BaseDisplay._render(self)
        except StopIteration:
            pass
        except BaseException as e:
            sys.excepthook(*sys.exc_info())
            os._exit(0)
        self.swap_buffers()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def main_loop(self):
        while True:
            glfw.poll_events()
            if glfw.window_should_close(self.window):
                if self.exit_handler:
                    self.exit_handler()
                return
            self._render()

    def get_proc_address(self, s):
        return glfw.get_proc_address(s.decode("ascii"))

    def get_mpv_params(self):
        params = {}
        try:
            glfw._glfw.glfwGetX11Display.restype = c_void_p
            params["x11_display"] = glfw._glfw.glfwGetX11Display()
        except AttributeError:
            pass
        try:
            glfw._glfw.glfwGetWaylandDisplay.restype = c_void_p
            params["wl_display"] = glfw._glfw.glfwGetWaylandDisplay()
        except AttributeError:
            pass
        return params

if __name__ == "__main__":
    d = Display()
    def render():
        while True:
            for color in (1.,0.,0.,1.), (0.,1.,0.,1.), (0.,0.,1.,1.):
                gl.glClearColor(*color)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                yield None
                time.sleep(0.2)
    d.set_render_gen(render)
    d.main_loop()
