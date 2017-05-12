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
import OpenGL.GL.shaders as shaders
import OpenGL.GLUT as glut
import blitzloop._glfw as glfw
import os
import sys

from blitzloop.backend.common import *

class Display(BaseDisplay):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        glfw.init()
        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        glfw.window_hint(glfw.DEPTH_BITS, 24)
        glfw.window_hint(glfw.ALPHA_BITS, 0)
        monitor = glfw.get_primary_monitor() if fullscreen else None
        self.window = glfw.Window(width, height, "BlitzLoop Karaoke", monitor)
        self.window.make_context_current()
        BaseDisplay.__init__(self, width, height, fullscreen, aspect)
        self._on_reshape(width, height)
        if fullscreen:
            self.saved_size = (0, 0, width, height)
            self.window.set_input_mode(glfw.CURSOR, glfw.CURSOR_HIDDEN)

        self._initialize()

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.window.set_monitor(None, *self.saved_size, 60)
        else:
            x, y = self.window.get_pos()
            self.saved_size = x, y, self.win_width, self.win_height
            monitor = glfw.get_primary_monitor()
            mode = monitor.get_video_mode()
            self.window.set_monitor(monitor, 0, 0, *mode)

        self.fullscreen = not self.fullscreen

    def _on_reshape(self, width, height):
        self.win_width = width
        self.win_height = height
        self.gl.glViewport(0, 0, width, height)
        self.set_aspect(self.aspect)

    def _poll_events(self):
        for evt, data in self.window.poll_events():
            if evt == 'key':
                key, scancode, action, mods = data
                if action != glfw.PRESS:
                    continue
                if self.kbd_handler:
                    if key == glfw.KEY_ESCAPE:
                        key = 0x1b
                    elif key == glfw.KEY_ENTER:
                        key = 0x0d
                    glut_key = chr(key).lower().encode('utf8')

                    if key == glfw.KEY_UP:
                        glut_key = glut.GLUT_KEY_UP
                    elif key == glfw.KEY_DOWN:
                        glut_key = glut.GLUT_KEY_DOWN
                    elif key == glfw.KEY_LEFT:
                        glut_key = glut.GLUT_KEY_LEFT
                    elif key == glfw.KEY_RIGHT:
                        glut_key = glut.GLUT_KEY_RIGHT
                    self.kbd_handler(glut_key)
                elif key == glfw.KEY_ESCAPE:
                    raise StopIteration
            elif evt == 'resize':
                width, height = data
                self._on_reshape(width, height)
            elif evt == 'exit':
                raise StopIteration
            else:
                raise Exception('Unknown event: %s' % evt)

    def _render(self):
        try:
            BaseDisplay._render(self)
        except StopIteration:
            pass
        except BaseException as e:
            sys.excepthook(*sys.exc_info())
            raise StopIteration
        self.swap_buffers()

    def swap_buffers(self):
        self.window.swap_buffers()

    def main_loop(self):
        while True:
            self._poll_events()
            self._render()

    def get_proc_address(self, s):
        return glfw.get_proc_address(s)

if __name__ == "__main__":
    fs_red = """
    void main() {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 0.0);
    }
    """
    vs_null = """
    void main() {
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }
    """
    d = Display()
    shader = shaders.compileProgram(
        shaders.compileShader(vs_null, gl.GL_VERTEX_SHADER),
        shaders.compileShader(fs_red, gl.GL_FRAGMENT_SHADER),
    )
    def render():
        while True:
            gl.glClearColor(0,0,0,1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            with shader:
                gl.glBegin(gl.GL_TRIANGLES)
                gl.glVertex2f(0,0)
                gl.glVertex2f(1,0)
                gl.glVertex2f(0,1)
                gl.glEnd()
            yield None
    d.set_render_gen(render)
    d.main_loop()
