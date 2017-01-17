#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2017 Hector Martin "marcan" <hector@marcansoft.com>
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

from blitzloop.matrix import Matrix

class BaseDisplay(object):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.kbd_handler = None
        self.win_width = self.width = width
        self.win_height = self.height = height
        self.matrix = Matrix()
        self.viewmatrix = Matrix()
        self.set_aspect(aspect)
        self.clear_color = (0.0, 0.0, 0.0, 1.0)

    def set_aspect(self, aspect):
        if aspect is None:
            aspect = self.win_width / self.win_height
        self.aspect = aspect
        display_aspect = self.win_width / self.win_height
        if self.aspect:
            if display_aspect > self.aspect:
                self.width = int(round(self.aspect * self.win_height))
                self.height = self.win_height
            else:
                self.width = self.win_width
                self.height = int(round(self.win_width / self.aspect))
        else:
            self.width = self.win_width
            self.height = self.win_height
        off_x = int((self.win_width - self.width) / 2)
        off_y = int((self.win_height - self.height) / 2)

        self.viewmatrix.reset()
        self.viewmatrix.translate(-1.0, -1.0)
        self.viewmatrix.scale(2.0/self.win_width, 2.0/self.win_height)
        self.viewmatrix.translate(off_x, off_y, 0)
        self.viewmatrix.scale(self.width, self.width, 1)

    def commit_matrix(self, uniform):
        m = self.viewmatrix.m * self.matrix.m
        self.gl.glUniformMatrix4fv(uniform, 1, False, m.transpose())

    def set_render_gen(self, gen):
        self.frames = gen()

    def set_keyboard_handler(self, f):
        self.kbd_handler = f

    def _render(self):
        self.matrix.reset()

        self.gl.glClearColor(*self.clear_color)
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        next(self.frames)

    def main_loop(self):
        while True:
            try:
                self._render()
            except StopIteration:
                break
            self.swap_buffers()
    
    def round_coord(self, c):
        return int(round(c * self.width)) / self.width

    @property
    def top(self):
        return self.height / self.width
