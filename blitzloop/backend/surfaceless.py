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

import os, time, sys

from blitzloop.backend.common import BaseDisplay

import ctypes, ctypes.util
from ctypes import cdll, c_int, Structure, byref, c_void_p, c_uint32, c_char_p

import blitzloop.backend.gles_fixes
import OpenGL.GLES2 as gl
import OpenGL.EGL as egl
from OpenGL import arrays

EGL_PLATFORM_SURFACELESS_MESA = 0x31DD

class Display(BaseDisplay):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        self.bo_next = self.bo_prev = None
        self.last_swap = time.time()
        self.frame_count = 0

        self.disp = egl.eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA, egl.EGL_DEFAULT_DISPLAY, None)
        if not self.disp:
            raise Exception("Failed to get egl display")

        BaseDisplay.__init__(self, width, height, True, aspect)

        attribList = arrays.GLintArray.asArray([
            egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_ES2_BIT,
            egl.EGL_SURFACE_TYPE, egl.EGL_PBUFFER_BIT,
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
        surfaceAttrib = arrays.GLintArray.asArray([
            egl.EGL_WIDTH, width,
            egl.EGL_HEIGHT, height,
            egl.EGL_NONE
        ])

        egl.eglInitialize(self.disp, None, None)
        config = egl.EGLConfig()
        num_configs = ctypes.c_long()
        egl.eglChooseConfig(self.disp, attribList, byref(config), 1, byref(num_configs))

        ret = ctypes.c_int()
        egl.eglBindAPI(egl.EGL_OPENGL_ES_API)

        self.context = egl.eglCreateContext(self.disp, config, egl.EGL_NO_CONTEXT, ctxAttrib)
        self.surface = egl.eglCreatePbufferSurface(self.disp, config, surfaceAttrib); 
        assert egl.eglMakeCurrent(self.disp, self.surface, self.surface, self.context)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        gl.glClearColor(0, 0, 0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        self.win_width = self.width = width
        self.win_height = self.height = height

        gl.glViewport(0, 0, self.win_width, self.win_height)

        self.clear_color = self.TRANSPARENT

        self._initialize()

    def swap_buffers(self):
        egl.eglSwapBuffers(self.disp, self.surface)
        self.frame_count += 1

    def get_proc_address(self, s):
        return egl.eglGetProcAddress(s)

    def get_mpv_params(self):
        return { "drm_display": {
            "fd": self.render_fd,
            "render_fd": self.render_fd,
        } }

if __name__ == "__main__":
    d = Display()
    while True:
        for color in (1.,0.,0.,1.), (0.,1.,0.,1.), (0.,0.,1.,1.):
            gl.glClearColor(*color)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            d.swap_buffers()
