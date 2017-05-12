# -*- encoding: utf-8 -*-
##
## Copyright (C) 2016 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

cdef extern from "GLFW/glfw3.h" nogil:
    ctypedef void* GLFWmonitor
    ctypedef void* GLFWwindow
    ctypedef void* GLFWglproc

    ctypedef void (* GLFWerrorfun)(int, const char*)
    ctypedef void (* GLFWwindowclosefun)(GLFWwindow*)
    ctypedef void (* GLFWframebuffersizefun)(GLFWwindow*,int,int)
    ctypedef void (* GLFWkeyfun)(GLFWwindow*, int, int, int, int)

    ctypedef struct GLFWvidmode:
        int width
        int height
        int refreshRate

    int glfwInit()
    void glfwTerminate()

    GLFWerrorfun glfwSetErrorCallback(GLFWerrorfun cbfun)

    void glfwWindowHint(int hint, int value)
    GLFWwindow* glfwCreateWindow(int width, int height, const char* title, GLFWmonitor* monitor, GLFWwindow* share)
    void glfwDestroyWindow(GLFWwindow* window)
    void glfwSetWindowShouldClose(GLFWwindow* window, int value)

    GLFWmonitor* glfwGetPrimaryMonitor()
    const GLFWvidmode* glfwGetVideoMode(GLFWmonitor* monitor)
    GLFWmonitor* glfwGetWindowMonitor(GLFWwindow* window)
    void glfwGetWindowPos(GLFWwindow* window, int* xpos, int* ypos)
    void glfwSetWindowMonitor(GLFWwindow* window, GLFWmonitor* monitor, int xpos, int ypos, int width, int height, int refreshRate)

    GLFWwindowclosefun glfwSetWindowCloseCallback(GLFWwindow* window, GLFWwindowclosefun cbfun)
    GLFWframebuffersizefun glfwSetFramebufferSizeCallback(GLFWwindow* window, GLFWframebuffersizefun cbfun)
    void glfwPollEvents()

    GLFWkeyfun glfwSetKeyCallback(GLFWwindow* window, GLFWkeyfun cbfun)

    void glfwMakeContextCurrent(GLFWwindow* window)
    void glfwSwapBuffers(GLFWwindow* window)
    void glfwSetInputMode(GLFWwindow* window, int mode, int value)

    GLFWglproc glfwGetProcAddress(const char* procname)

    ctypedef enum:
        GLFW_DONT_CARE

    ctypedef enum:
        GLFW_KEY_UP
        GLFW_KEY_DOWN
        GLFW_KEY_LEFT
        GLFW_KEY_RIGHT
        GLFW_KEY_LEFT_BRACKET
        GLFW_KEY_RIGHT_BRACKET
        GLFW_KEY_MINUS
        GLFW_KEY_EQUAL
        GLFW_KEY_SPACE
        GLFW_KEY_ESCAPE
        GLFW_KEY_ENTER

    ctypedef enum:
        GLFW_MOD_ALT

    ctypedef enum:
        GLFW_PRESS

    ctypedef enum:
        GLFW_CLIENT_API
        GLFW_OPENGL_PROFILE
        GLFW_CONTEXT_VERSION_MAJOR
        GLFW_CONTEXT_VERSION_MINOR
        GLFW_DEPTH_BITS
        GLFW_ALPHA_BITS
        GLFW_DOUBLEBUFFER
        GLFW_RESIZABLE

    ctypedef enum:
        GLFW_OPENGL_API
        GLFW_OPENGL_ES_API
        GLFW_OPENGL_CORE_PROFILE
        GLFW_NO_API

    ctypedef enum:
        GLFW_CURSOR
        GLFW_CURSOR_NORMAL
        GLFW_CURSOR_HIDDEN

DONT_CARE = GLFW_DONT_CARE

CLIENT_API = GLFW_CLIENT_API
OPENGL_PROFILE = GLFW_OPENGL_PROFILE
CONTEXT_VERSION_MAJOR = GLFW_CONTEXT_VERSION_MAJOR
CONTEXT_VERSION_MINOR = GLFW_CONTEXT_VERSION_MINOR
DEPTH_BITS = GLFW_DEPTH_BITS
ALPHA_BITS = GLFW_ALPHA_BITS
RESIZABLE = GLFW_RESIZABLE
DOUBLEBUFFER = GLFW_DOUBLEBUFFER

OPENGL_API = GLFW_OPENGL_API
OPENGL_ES_API = GLFW_OPENGL_ES_API
OPENGL_CORE_PROFILE = GLFW_OPENGL_CORE_PROFILE
NO_API = GLFW_NO_API

PRESS = GLFW_PRESS

KEY_UP = GLFW_KEY_UP
KEY_DOWN = GLFW_KEY_DOWN
KEY_LEFT = GLFW_KEY_LEFT
KEY_RIGHT = GLFW_KEY_RIGHT
KEY_LEFT_BRACKET = GLFW_KEY_LEFT_BRACKET
KEY_RIGHT_BRACKET = GLFW_KEY_RIGHT_BRACKET
KEY_MINUS = GLFW_KEY_MINUS
KEY_EQUAL = GLFW_KEY_EQUAL
KEY_SPACE = GLFW_KEY_SPACE
KEY_ESCAPE = GLFW_KEY_ESCAPE
KEY_ENTER = GLFW_KEY_ENTER

MOD_ALT = GLFW_MOD_ALT

CURSOR = GLFW_CURSOR
CURSOR_NORMAL = GLFW_CURSOR_NORMAL
CURSOR_HIDDEN = GLFW_CURSOR_HIDDEN

cdef void error_callback(int a, const char* b) except *:
    print('GLFW error 0x%x: %s' % (a, b.decode('utf-8')))

cdef list _global_events = []

cdef void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods):
    _global_events.append(('key', (key, scancode, action, mods)))

cdef void size_callback(GLFWwindow* window, int width, int height):
    _global_events.append(('resize', (width, height)))

cdef void close_callback(GLFWwindow* window):
    _global_events.append(('exit', None))

def init():
    glfwSetErrorCallback(<GLFWerrorfun>error_callback)
    ret = glfwInit()
    if not ret:
        raise Exception('GLFW: Failed to initialize.')

def terminate():
    glfwTerminate()

def window_hint(int hint, int value):
    glfwWindowHint(hint, value)

def get_primary_monitor():
    monitor = Monitor()
    monitor.monitor = glfwGetPrimaryMonitor()
    if monitor.monitor == NULL:
        raise Exception('GLFW: Failed to obtain the primary monitor.')
    return monitor

def get_proc_address(bytes procname):
    return <long> glfwGetProcAddress(procname)

cdef class Monitor:
    cdef GLFWmonitor* monitor

    def get_video_mode(self):
        vidmode = glfwGetVideoMode(self.monitor)
        return vidmode.width, vidmode.height, vidmode.refreshRate

cdef class Window:
    cdef GLFWwindow* window

    def __init__(self, int width, int height, str title, Monitor monitor=None, Window share=None):
        cdef GLFWmonitor* c_monitor = NULL
        cdef GLFWwindow* c_share = NULL
        if monitor is not None:
            c_monitor = monitor.monitor
        if share is not None:
            c_share = share.window
        self.window = glfwCreateWindow(width, height, title.encode('utf-8'), c_monitor, c_share)
        if self.window == NULL:
            raise Exception('GLFW: Failed to create a window.')
        glfwSetFramebufferSizeCallback(self.window, <GLFWframebuffersizefun>size_callback)
        glfwSetWindowCloseCallback(self.window, <GLFWwindowclosefun>close_callback)
        glfwSetKeyCallback(self.window, <GLFWkeyfun>key_callback)

    def __del__(self):
        glfwDestroyWindow(self.window)

    def make_context_current(self):
        glfwMakeContextCurrent(self.window)

    def swap_buffers(self):
        glfwSwapBuffers(self.window)

    def set_input_mode(self, int mode, int value):
        glfwSetInputMode(self.window, mode, value)

    def poll_events(self):
        glfwPollEvents()
        events = _global_events[:]
        _global_events.clear()
        return events

    def get_pos(self):
        cdef int xpos
        cdef int ypos
        glfwGetWindowPos(self.window, &xpos, &ypos)
        return xpos, ypos

    def get_monitor(self):
        monitor = Monitor()
        monitor.monitor = glfwGetWindowMonitor(self.window)
        if monitor.monitor == NULL:
            return None
        return monitor

    def set_monitor(self, Monitor monitor, int xpos, int ypos, int width, int height, int refreshRate):
        c_monitor = NULL
        if monitor is not None:
            c_monitor = monitor.monitor
        glfwSetWindowMonitor(self.window, c_monitor, xpos, ypos, width, height, refreshRate)
