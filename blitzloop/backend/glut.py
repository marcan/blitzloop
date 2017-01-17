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
import os
import sys

from blitzloop.backend.common import *

class Display(BaseDisplay):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        glut.glutInit(sys.argv)
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
        glut.glutInitWindowPosition(0, 0)
        glut.glutCreateWindow("BlitzLoop Karaoke")
        if not fullscreen:
            glut.glutReshapeWindow(width, height)
        else:
            glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
        BaseDisplay.__init__(self, width, height, fullscreen, aspect)
        if fullscreen:
            glut.glutFullScreen()
        glut.glutDisplayFunc(self._render)
        glut.glutIdleFunc(self._render)
        glut.glutReshapeFunc(self._on_reshape)
        glut.glutKeyboardFunc(self._on_keyboard)
        glut.glutSpecialFunc(self._on_keyboard)

    def _on_reshape(self, width, height):
        self.win_width = width
        self.win_height = height
        self.set_aspect(self.aspect)

    def _on_keyboard(self, key, x, y):
        if self.kbd_handler:
            self.kbd_handler(key)
        elif key == "\033":
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
        glut.glutSwapBuffers()

    def main_loop(self):
        glut.glutMainLoop()

    def get_proc_address(self, s):
        return glut.glutGetProcAddress(s)

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
