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
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GL.shaders as shaders

class Display(object):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.kbd_handler = None
        self.win_width = width
        self.win_height = height
        glut.glutInit(sys.argv)
        glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
        glut.glutInitWindowPosition(0, 0)
        glut.glutCreateWindow("BlitzLoop Karaoke")
        if not fullscreen:
            glut.glutReshapeWindow(width, height)
        else:
            glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
        self.win_width = width
        self.win_height = height
        self.set_aspect(aspect)
        self._on_reshape(width, height)
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
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, width, 0, height, -1, 1)
        display_aspect = width / float(height)
        if self.aspect:
            if display_aspect > self.aspect:
                self.width = int(round(self.aspect * height))
                self.height = height
            else:
                self.width = width
                self.height = int(round(width / self.aspect))
        else:
            self.width = width
            self.height = height
        off_x = int((width - self.width) / 2)
        off_y = int((height - self.height) / 2)
        gl.glTranslate(off_x, off_y, 0)
        gl.glScale(self.width, self.width, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def _on_keyboard(self, key, x, y):
        if self.kbd_handler:
            self.kbd_handler(key)
        elif key == "\033":
            os._exit(0)

    def _render(self):
        try:
            gl.glClearColor(0, 0, 0, 1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glLoadIdentity()
            self.frames.next()
        except StopIteration:
            pass
        except BaseException as e:
            sys.excepthook(*sys.exc_info())
            os._exit(0)
        glut.glutSwapBuffers()

    def set_aspect(self, aspect):
        if aspect is None:
            aspect = self.win_width / float(self.win_height)
        self.aspect = aspect
        self._on_reshape(self.win_width, self.win_height)

    def set_render_gen(self, gen):
        self.frames = gen()

    def set_keyboard_handler(self, f):
        self.kbd_handler = f

    def main_loop(self):
        glut.glutMainLoop()

    def round_coord(self, c):
        return int(round(c * self.width)) / float(self.width)

    @property
    def top(self):
        return self.height / float(self.width)

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
