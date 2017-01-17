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

import math
import time

from blitzloop import util, graphics

class IdleScreen(object):
    def __init__(self, display):
        self.display = display

        tr = graphics.get_texture_renderer()
        ImageTexture = graphics.get_renderer().ImageTexture
        self.logo = ImageTexture(util.get_resgfx_path("logo.png"), tr)
        self.tablet = ImageTexture(util.get_resgfx_path("tablet.png"), tr)
        self.hand = ImageTexture(util.get_resgfx_path("hand.png"), tr)
        self.silhouette = ImageTexture(util.get_resgfx_path("silhouette.png"), tr)
        self.reset()

    def reset(self):
        self.fade = 0
        self.st = time.time()
        self.closing = False

    def close(self):
        self.closing = True

    def __iter__(self):
        return self

    def __next__(self):
        t = time.time() - self.st
        self.display.set_aspect(4.0/3.0)
        if self.closing:
            self.fade -= 0.015
            if self.fade < 0:
                raise StopIteration()
        elif self.fade < 1:
            self.fade = min(1, self.fade + 0.015)

        self.display.gl.glClearColor(0, 0, 0, 1)
        self.display.gl.glClear(self.display.gl.GL_COLOR_BUFFER_BIT |
                                self.display.gl.GL_DEPTH_BUFFER_BIT)

        sfac = self.silhouette.aspect / self.display.aspect
        self.silhouette.draw(x=0, width=sfac)
        lx = sfac * 0.7
        lw = 1.0-lx
        self.logo.draw(y=(1.0 / self.display.aspect) - (lw / self.logo.aspect) - 0.02, x=lx, width=lw)
        tx = lx + lw/2 - 0.1
        ty = 0.2
        self.tablet.draw(x=tx, y=ty, width=0.2)
        d = math.sin(t / 0.5 * math.pi) * 0.02
        self.hand.draw(x=tx + 0.1 - 0.6 * d, y=ty - 0.09 + d, width=0.1)

        self.display.set_aspect(None)

        graphics.get_solid_renderer().draw((0, 0), (1, 1),
                                           (0., 0., 0., 1 - self.fade))

