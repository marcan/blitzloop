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

import pykms

from blitzloop.backend.common import BaseDisplay

import ctypes, ctypes.util
from ctypes import cdll, c_int, Structure, byref, c_void_p, c_uint32, c_char_p

import blitzloop.backend.gles_fixes
import OpenGL.GLES2 as gl
import OpenGL.EGL as egl
from OpenGL import arrays

libdrm = cdll.LoadLibrary("libdrm.so")
libdrm.drmGetRenderDeviceNameFromFd.restype = c_char_p

libgbm = cdll.LoadLibrary("libgbm.so")
libgbm.gbm_create_device.restype = c_void_p
libgbm.gbm_surface_create.restype = c_void_p
libgbm.gbm_surface_lock_front_buffer.restype = c_void_p
libgbm.gbm_bo_get_user_data.restype = c_void_p

class gbm_bo_handle(ctypes.Union):
    _fields_ = [("ptr", ctypes.c_void_p),
                ("s32", ctypes.c_int32),
                ("u32", ctypes.c_uint32),
                ("s64", ctypes.c_int64),
                ("u64", ctypes.c_uint64)]

libgbm.gbm_bo_get_handle = gbm_bo_handle

destroy_user_data_t = ctypes.CFUNCTYPE(None, c_void_p, ctypes.py_object)

def py_destroy_fb_object(bo, userdata):
    #print("Destroy FB object at 0x%x" % id(userdata.value))
    ctypes.pythonapi.Py_DecRef(userdata)

destroy_fb_object = destroy_user_data_t(py_destroy_fb_object)

GBM_FORMAT_XRGB8888 = 0x34325258
GBM_BO_USE_SCANOUT   = (1 << 0)
GBM_BO_USE_RENDERING = (1 << 2)

class Display(BaseDisplay):
    def __init__(self, width=640, height=480, fullscreen=False, aspect=None):
        self.gl = gl
        self.bo_next = self.bo_prev = None
        self.last_swap = time.time()
        self.frame_count = 0

        self.card = pykms.Card()
        print("DRM fd: %d" % self.card.fd)
        print("Has atomic: %r" % self.card.has_atomic)

        self.render_fd = -1

        render_name = libdrm.drmGetRenderDeviceNameFromFd(self.card.fd)
        print("Render device name: %r" % render_name)

        if render_name:
            try:
                self.render_fd = os.open(render_name, os.O_RDWR)
            except OSError:
                print("Render node not available")

        print("Render fd: %d" % self.render_fd)
        self.gbm_dev = libgbm.gbm_create_device(self.card.fd)
        if not self.gbm_dev:
            raise Exception("Failed to create GBM device")

        print("GBM dev: %x" % self.gbm_dev)

        self.res = pykms.ResourceManager(self.card)
        self.conn = self.res.reserve_connector()
        self.crtc = self.res.reserve_crtc(self.conn)
        self.root_plane = self.res.reserve_generic_plane(self.crtc)
        if not self.root_plane:
            raise Exception("Root plane not available")

        self.mode = mode = self.conn.get_default_mode()

        print("Creating GBM surface (%dx%d)" % (mode.hdisplay, mode.vdisplay))

        self.gbm_surface = libgbm.gbm_surface_create(
            c_void_p(self.gbm_dev), mode.hdisplay, mode.vdisplay,
            GBM_FORMAT_XRGB8888, GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING)

        if not self.gbm_surface:
            raise Exception("Failed to create GBM surface")
        print("GBM surface: %x" % self.gbm_surface)

        self.disp = egl.eglGetDisplay(self.gbm_dev)
        if not self.disp:
            raise Exception("Failed to get egl display")

        attribList = arrays.GLintArray.asArray([
            egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_ES2_BIT,
            egl.EGL_SURFACE_TYPE, egl.EGL_WINDOW_BIT,
            #egl.EGL_COLOR_BUFFER_TYPE, egl.EGL_RGB_BUFFER,
            egl.EGL_RED_SIZE, 8,
            egl.EGL_GREEN_SIZE, 8,
            egl.EGL_BLUE_SIZE, 8,
            egl.EGL_ALPHA_SIZE, 0,
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

        self.surface = egl.eglCreateWindowSurface(self.disp, config, c_void_p(self.gbm_surface), None)
        self.context = egl.eglCreateContext(self.disp, config, egl.EGL_NO_CONTEXT, ctxAttrib)
        assert egl.eglMakeCurrent(self.disp, self.surface, self.surface, self.context)

        egl.eglSwapInterval(self.disp, 1)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        gl.glClearColor(0, 0, 0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        #fb = self.lock_next()
        #self.crtc.set_mode(self.conn, fb, mode)

        modeb = mode.to_blob(self.card)

        req = pykms.AtomicReq(self.card)
        req.add(self.conn, "CRTC_ID", self.crtc.id)
        req.add(self.crtc, {"ACTIVE": 1,
                            "MODE_ID": modeb.id})
        if req.test(allow_modeset = True):
            raise Exception("Atomic test failed")
        if req.commit_sync(allow_modeset = True):
            raise Exception("Atomic commit failed")

        self.win_width = self.width = mode.hdisplay
        self.win_height = self.height = mode.vdisplay

        gl.glViewport(0, 0, self.win_width, self.win_height)

        BaseDisplay.__init__(self, mode.hdisplay, mode.vdisplay, True, aspect)

        self.clear_color = self.BLACK

        self._initialize()

    def lock_next(self):
        bo = libgbm.gbm_surface_lock_front_buffer(c_void_p(self.gbm_surface))
        bo = c_void_p(bo)

        self.bo_prev = self.bo_next
        self.bo_next = bo

        userdata = libgbm.gbm_bo_get_user_data(bo)
        if userdata:
            pyo = ctypes.cast(userdata, ctypes.py_object)
            fb = pyo.value
            del pyo
            #print("PyObject for fb: 0x%x (%d)" % (id(fb), sys.getrefcount(fb)))
            return fb

        bo_width = libgbm.gbm_bo_get_width(bo)
        bo_height = libgbm.gbm_bo_get_height(bo)
        bo_stride = libgbm.gbm_bo_get_stride(bo)
        bo_fd = libgbm.gbm_bo_get_fd(bo)
        bo_format = libgbm.gbm_bo_get_format(bo)
        #print("BO: 0x%x %dx%d stride:%d format:0x%x fd:%d" % (
              #bo.value, bo_width, bo_height, bo_stride, bo_format, bo_fd))

        assert bo_format == GBM_FORMAT_XRGB8888

        fb = pykms.ExtFramebuffer(self.card, bo_width, bo_height,
                                  pykms.PixelFormat.XRGB8888,
                                  [bo_fd], [bo_stride], [0])
        os.close(bo_fd)

        fbo = ctypes.py_object(fb)
        libgbm.gbm_bo_set_user_data(bo, fbo, destroy_fb_object)
        ctypes.pythonapi.Py_IncRef(fbo)
        del fbo
        #print("PyObject for fb: 0x%x (%d)" % (id(fb), sys.getrefcount(fb)))

        return fb

    def free_prev(self):
        if self.bo_prev:
            #print("Release BO 0x%x" % self.bo_prev.value)
            libgbm.gbm_surface_release_buffer(c_void_p(self.gbm_surface), self.bo_prev)
            self.bo_prev = None

    def swap_buffers(self):
        have_free_buffers = libgbm.gbm_surface_has_free_buffers(c_void_p(self.gbm_surface))
        if not have_free_buffers:
            raise Exception("No free buffers")

        egl.eglSwapBuffers(self.disp, self.surface)

        fb = self.lock_next()

        req = pykms.AtomicReq(self.card)
        req.add(self.root_plane, "FB_ID", fb.id)
        if req.test():
            raise Exception("Atomic test failed")
        if req.commit_sync():
            raise Exception("Atomic commit failed")

        self.free_prev()

        self.frame_count += 1
        if self.frame_count == 30:
            t = time.time()
            print("%.02f FPS" % (30.0/(t - self.last_swap)))
            self.last_swap = t
            self.frame_count = 0

    def get_proc_address(self, s):
        return egl.eglGetProcAddress(s)

    def get_mpv_params(self):
        return { "drm_display": {
            "fd": self.card.fd,
            "render_fd": self.render_fd,
        } }

if __name__ == "__main__":
    d = Display()
    while True:
        for color in (1.,0.,0.,1.), (0.,1.,0.,1.), (0.,0.,1.,1.):
            gl.glClearColor(*color)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            d.swap_buffers()
