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

from blitzloop import util

def Display(*args, **kwargs):
    global _display
    display = util.get_opts().display

    if display == "glut":
        from blitzloop.backend import glut
        _display = glut.Display(*args, **kwargs)
    elif display == "glfw":
        from blitzloop.backend import glfw
        _display = glfw.Display(*args, **kwargs)
    elif display == "rpi":
        from blitzloop.backend import rpi
        _display = rpi.Display(*args, **kwargs)
    elif display == "kms":
        from blitzloop.backend import kms
        _display = kms.Display(*args, **kwargs)
    return _display

_renderer = None
def get_renderer():
    global _renderer
    if _renderer is None:
        from blitzloop.renderer import gles as _renderer
    return _renderer

_solid_renderer = None
def get_solid_renderer():
    global _solid_renderer
    if _solid_renderer is None:
        _solid_renderer = get_renderer().SolidRenderer(_display)
    return _solid_renderer

_texture_renderer = None
def get_texture_renderer():
    global _texture_renderer
    if _texture_renderer is None:
        _texture_renderer = get_renderer().TextureRenderer(_display)
    return _texture_renderer

def GL():
    return get_renderer().gl

def arrays():
    return get_renderer().arrays
