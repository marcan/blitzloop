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

class Matrix(object):
    def __init__(self, other=None, nice=None):
        self.stack = []
        if other is not None:
            if isinstance(other, list):
                self.m = other
                self.nice = False
            else:
                self.m = list(other.m)
                self.nice = other.nice
        else:
            self.reset()

        if nice is not None:
            self.nice = nice

    def reset(self):
        self.m = [
            1.0,0.0,0.0,0.0,
            0.0,1.0,0.0,0.0,
            0.0,0.0,1.0,0.0,
            0.0,0.0,0.0,1.0
        ]
        self.nice = True

    def push(self):
        self.stack.append((self.m, self.nice))
        self.m = list(self.m)

    def pop(self):
        self.m, self.nice = self.stack.pop()

    def scale(self, sx, sy, sz=1.0):
        if not self.nice:
            self *= Matrix().scale(sx, sy, sz)
            return self
        else:
            self.m[0] *= sx
            self.m[5] *= sy
            self.m[10] *= sz
        return self

    def translate(self, tx, ty, tz=0.0):
        if not self.nice:
            self *= Matrix().translate(tx, ty, tz)
            return self
        self.m[12] += tx * self.m[0]
        self.m[13] += ty * self.m[5]
        self.m[14] += tz * self.m[10]
        return self

    def __mul__(self, other):
        if self.nice and other.nice:
            return Matrix(self._nicemult(self.m, other.m), True)
        else:
            return Matrix(self._mult(self.m, other.m), False)

    def __imul__(self, other):
        if self.nice and other.nice:
            self.m = self._nicemult(self.m, other.m)
        else:
            self.m = self._mult(self.m, other.m)
            self.nice = False
        return self

    @staticmethod
    def _mult(B, A):
        C = [
            A[0] * B[0] + A[1] * B[4] + A[2] * B[8] + A[3] * B[12],
            A[0] * B[1] + A[1] * B[5] + A[2] * B[9] + A[3] * B[13],
            A[0] * B[2] + A[1] * B[6] + A[2] * B[10] + A[3] * B[14],
            A[0] * B[3] + A[1] * B[7] + A[2] * B[11] + A[3] * B[15],
            A[4] * B[0] + A[5] * B[4] + A[6] * B[8] + A[7] * B[12],
            A[4] * B[1] + A[5] * B[5] + A[6] * B[9] + A[7] * B[13],
            A[4] * B[2] + A[5] * B[6] + A[6] * B[10] + A[7] * B[14],
            A[4] * B[3] + A[5] * B[7] + A[6] * B[11] + A[7] * B[15],
            A[8] * B[0] + A[9] * B[4] + A[10] * B[8] + A[11] * B[12],
            A[8] * B[1] + A[9] * B[5] + A[10] * B[9] + A[11] * B[13],
            A[8] * B[2] + A[9] * B[6] + A[10] * B[10] + A[11] * B[14],
            A[8] * B[3] + A[9] * B[7] + A[10] * B[11] + A[11] * B[15],
            A[12] * B[0] + A[13] * B[4] + A[14] * B[8] + A[15] * B[12],
            A[12] * B[1] + A[13] * B[5] + A[14] * B[9] + A[15] * B[13],
            A[12] * B[2] + A[13] * B[6] + A[14] * B[10] + A[15] * B[14],
            A[12] * B[3] + A[13] * B[7] + A[14] * B[11] + A[15] * B[15],
        ]
        return C

    @staticmethod
    def _nicemult(B, A):
        C = [
            A[0] * B[0], 0.0, 0.0, 0.0,
            0.0, A[5] * B[5], 0.0, 0.0,
            0.0, 0.0, A[10] * B[10], 0.0,
            A[12] * B[0] + B[12], A[13] * B[5] + B[13], A[14] * B[10] + B[14], 1.0,
        ]
        return C
    
    def __str__(self):
        s = ""
        for i in range(4):
            s += " [" + ",".join("%d" % self.m[4*j+i] for j in range(4)) + "],\n"
        return "[\n" + s + "]\n"

    def __eq__(self, other):
        return self.m == other.m

if __name__ == "__main__":
    assert Matrix().translate(1,2).translate(3,4) == Matrix().translate(4,6)
    assert Matrix().scale(1,2).scale(3,4) == Matrix().scale(3,8)
    assert Matrix().scale(2,3).translate(4,5) == Matrix().translate(8,15).scale(2,3)
    assert Matrix().scale(2,3).translate(4,5) == Matrix().scale(2,3) * Matrix().translate(4,5)
    assert Matrix(nice=False).translate(1,2).translate(3,4) == Matrix().translate(4,6)
    assert Matrix(nice=False).scale(1,2).scale(3,4) == Matrix().scale(3,8)
    assert Matrix(nice=False).scale(2,3).translate(4,5) == Matrix().translate(8,15).scale(2,3)
    assert Matrix(nice=False).scale(2,3).translate(4,5) == Matrix().scale(2,3) * Matrix().translate(4,5)
