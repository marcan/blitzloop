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

import os, sys, time

from blitzloop.matrix import Matrix
from blitzloop.backend.common import *

import ctypes, ctypes.util
from ctypes import cdll, POINTER, c_char_p, c_int, c_uint, c_void_p, Structure, byref

# The shit we have to do to get stuff to work on the Raspberry Pi...

os.environ["PYOPENGL_PLATFORM"] = "egl" # Get PyOpenGL to use EGL/GLES

# monkeypatch ctypes to pick the right libraries... sigh.
def find_library(name):
    if name in ("GLESv2", "EGL"):
        return "/opt/vc/lib/lib%s.so" % name
    elif name == "GL":
        raise Exception()
    else:
        print(name)
        return old_find_library(name)
old_find_library = ctypes.util.find_library
ctypes.util.find_library = find_library

# Raspberry Pi libs are missing dependencies, we need GLES before EGL...
cdll.LoadLibrary("/opt/vc/lib/libGLESv2.so")

import OpenGL.GLES2 as gl
import OpenGL.EGL as egl
from OpenGL import arrays

# Now fix stupid missing imports in PyOpenGL GLES support...
import OpenGL.GLES2.VERSION.GLES2_2_0 as gl2
from OpenGL._bytes import _NULL_8_BYTE
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL import contextdata
gl2._NULL_8_BYTE = _NULL_8_BYTE
gl2.ArrayDatatype = ArrayDatatype
gl2.contextdata = contextdata
del gl2, _NULL_8_BYTE, ArrayDatatype, contextdata

class DISPMANX_MODEINFO_T(Structure):
    _fields_ = [("width", c_int),
                ("height", c_int),
                ("transform", c_int),
                ("input_format", c_int),
                ("display_num", c_int),
                ]


class EGL_DISPMANX_WINDOW_T(Structure):
    _fields_ = [("element", c_int),
                ("width", c_int),
                ("height", c_int)]

class VC_RECT_T(Structure):
    _fields_ = [("x", c_int),
                ("y", c_int),
                ("width", c_int),
                ("height", c_int)]

class VC_DISPMANX_ALPHA_T(Structure):
    _fields_ = [("flags", c_int),
                ("opacity", c_int),
                ("mask", c_int)]

libbcm_host = cdll.LoadLibrary("libbcm_host.so")

class Display(BaseDisplay):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        libbcm_host.bcm_host_init()
        display = libbcm_host.vc_dispmanx_display_open(0)

        mode = DISPMANX_MODEINFO_T()
        libbcm_host.vc_dispmanx_display_get_info(display, byref(mode))
        print("Display mode: %dx%d" % (mode.width, mode.height))

        self.disp = egl.eglGetDisplay(egl.EGL_DEFAULT_DISPLAY)
        attribList = arrays.GLintArray.asArray([
            egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_ES2_BIT,
            egl.EGL_SURFACE_TYPE, egl.EGL_WINDOW_BIT,
            #egl.EGL_COLOR_BUFFER_TYPE, egl.EGL_RGB_BUFFER,
            egl.EGL_RED_SIZE, 8,
            egl.EGL_GREEN_SIZE, 8,
            egl.EGL_BLUE_SIZE, 8,
            egl.EGL_ALPHA_SIZE, 8,
            egl.EGL_NONE
        ])
        ctxAttrib = arrays.GLintArray.asArray([
            egl.EGL_CONTEXT_CLIENT_VERSION, 2,
            egl.EGL_NONE
        ])
        egl.eglInitialize(self.disp, None, None)
        config = egl.EGLConfig()
        num_configs = ctypes.c_long()
        egl.eglChooseConfig(self.disp, attribList, byref(config), 1, byref(num_configs))

        ret = ctypes.c_int()
        egl.eglBindAPI(egl.EGL_OPENGL_ES_API)

        update = libbcm_host.vc_dispmanx_update_start(0)
        rectDst = VC_RECT_T()
        rectDst.x = rectDst.y = 0
        rectDst.width = mode.width
        rectDst.height = mode.height

        rectSrc = VC_RECT_T()
        rectSrc.x = rectDst.y = 0
        rectSrc.width = mode.width << 16
        rectSrc.height = mode.height << 16

        alpha = VC_DISPMANX_ALPHA_T()
        alpha.flags = 1 << 16  # premultiplied alpha
        alpha.opacity = 255
        alpha.mask = 0

        self.nativeWindow = EGL_DISPMANX_WINDOW_T()
        self.nativeWindow.width = mode.width
        self.nativeWindow.height = mode.height

        layer = 0
        self.nativeWindow.element = libbcm_host.vc_dispmanx_element_add(
            update, display, layer, byref(rectDst), 0, byref(rectSrc),
            0, byref(alpha), 0, 0)

        libbcm_host.vc_dispmanx_update_submit_sync(update)
        libbcm_host.vc_dispmanx_display_close(display)

        self.surface = egl.eglCreateWindowSurface(self.disp, config, byref(self.nativeWindow), None)
        self.context = egl.eglCreateContext(self.disp, config, egl.EGL_NO_CONTEXT, ctxAttrib)
        assert egl.eglMakeCurrent(self.disp, self.surface, self.surface, self.context)

        egl.eglSwapInterval(self.disp, 1)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        for i in range(5):
            gl.glClearColor(0, 0, 0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            egl.eglSwapBuffers(self.disp, self.surface)

        self.win_width = self.width = mode.width
        self.win_height = self.height = mode.height

        gl.glViewport(0, 0, self.win_width, self.win_height)

        BaseDisplay.__init__(self, mode.width, mode.height, True, aspect)

        # Transparent layer
        self.clear_color = self.TRANSPARENT

    def swap_buffers(self):
        egl.eglSwapBuffers(self.disp, self.surface)

if __name__ == "__main__":
    import OpenGL.GLES2 as gl
    d = Display()
    while True:
        for color in (1.,0.,0.,1.), (0.,1.,0.,1.), (0.,0.,1.,1.):
            gl.glClearColor(*color)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            egl.eglSwapBuffers(d.disp, d.surface)
            time.sleep(0.5)
