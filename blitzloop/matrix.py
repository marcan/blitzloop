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


print("matrix!")
Matrix=True

import numpy as np

print("matrix2!")

class Matrix(object):
    def __init__(self):
        self.stack = []
        self.reset()

    def reset(self):
        self.m = np.matrix([
            [1,0,0,0],
            [0,1,0,0],
            [0,0,1,0],
            [0,0,0,1]], float)

    def push(self):
        self.stack.append(self.m.copy())

    def pop(self):
        self.m = self.stack.pop()

    def scale(self, sx, sy, sz=1.0):
        self.m *= [
            [sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1],
        ]

    def translate(self, tx, ty, tz=0.0):
        self.m *= [
            [1, 0, 0, tx],
            [0, 1, 0, ty],
            [0, 0, 1, tz],
            [0, 0, 0, 1],
        ]
