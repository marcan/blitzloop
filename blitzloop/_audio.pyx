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

from libc.stdint cimport *
from libc.stdio cimport puts
from libc.stdlib cimport malloc, free
from libc.string cimport memset

cdef extern from "stdlib.h" nogil:
    void _exit (int status)

cdef extern from "jack/jack.h":
    enum:
        JackPortIsOutput
        JackPortIsInput
        JackNullOption

    char *JACK_DEFAULT_AUDIO_TYPE

    ctypedef struct jack_port_t
    ctypedef struct jack_client_t
    ctypedef int jack_options_t
    ctypedef uint32_t jack_nframes_t
    ctypedef struct jack_status_t

    ctypedef struct jack_latency_range_t:
        jack_nframes_t min, max

    ctypedef int (*JackProcessCallback)(jack_nframes_t nframes, void *arg)
    ctypedef void (*JackShutdownCallback)(void *arg)

    jack_client_t *jack_client_open(char *client_name, jack_options_t options, jack_status_t *status)
    int jack_activate(jack_client_t *client)
    int jack_set_process_callback(jack_client_t *client, JackProcessCallback process_callback, void *arg)
    void jack_on_shutdown(jack_client_t *client, JackShutdownCallback shutdown_callback, void *arg)
    jack_port_t *jack_port_register(jack_client_t *client, char *port_name, char *port_type, unsigned long flags, unsigned long buffer_size)
    jack_nframes_t jack_get_sample_rate(jack_client_t *)
    char* jack_port_name(jack_port_t * port)
    int jack_connect(jack_client_t *, char *source_port, char *destination_port)
    void *jack_port_get_buffer(jack_port_t *, jack_nframes_t) nogil
    int jack_client_close(jack_client_t *)

class AudioEngineError(Exception):
    pass

cdef int _process_cb(jack_nframes_t nframes, void *arg) nogil:
    return (<AudioEngine>arg).process(nframes)

cdef void _shutdown_cb(void *arg) nogil:
    puts("JACK shutdown called, dying rudely\n")
    _exit(1)

cdef class AudioEngine:
    cdef:
        jack_client_t *client
        jack_port_t *in_mic[32]
        jack_port_t *out_l
        jack_port_t *out_r
        int _sample_rate

        int dead
        int num_mics

        float mic_volume[32]
        float mic_feedback
        float mic_delay

        float *delay_buf
        int delay_ptr, delay_max

    @property
    def sample_rate(self):
        return self._sample_rate

    def __init__(self, mics):
        self.dead = False
        self.mic_delay = 0.12
        self.mic_feedback = 0.3
        self.delay_ptr = 0;

        self.client = jack_client_open("AudioEngine", JackNullOption, NULL)
        if self.client == NULL:
            raise AudioEngineError("Could not create JACK client")
        jack_set_process_callback(self.client, _process_cb, <void *>self)
        jack_on_shutdown(self.client, _shutdown_cb, NULL)

        self.num_mics = len(mics)
        for i in range(self.num_mics):
            self.mic_volume[i] = 0.8
            name = str("mic_%d" % i).encode("ascii")
            self.in_mic[i] = jack_port_register(self.client, name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0)
        self.out_l = jack_port_register(self.client, "l", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)
        self.out_r = jack_port_register(self.client, "r", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)

        self._sample_rate = jack_get_sample_rate(self.client)

        self.delay_max = self._sample_rate
        self.delay_buf = <float *>malloc(self.delay_max * sizeof(float))
        memset(self.delay_buf, 0, self.delay_max * sizeof(float))

        jack_activate(self.client)

        for i in range(self.num_mics):
            jack_connect(self.client, mics[i], jack_port_name(self.in_mic[i]))
        jack_connect(self.client, jack_port_name(self.out_l), "system:playback_1")
        jack_connect(self.client, jack_port_name(self.out_r), "system:playback_2")

    cdef int process(self, jack_nframes_t nframes) nogil:
        cdef float *i_mic[32]
        cdef int i, j

        for i in range(self.num_mics):
            i_mic[i] = <float *>jack_port_get_buffer(self.in_mic[i], nframes)
        cdef float *o_l = <float *>jack_port_get_buffer(self.out_l, nframes)
        cdef float *o_r = <float *>jack_port_get_buffer(self.out_r, nframes)

        cdef int delay_samples = <int>(self.mic_delay * self._sample_rate)
        if delay_samples >= self.delay_max:
            delay_samples = self.delay_max - 1
        if delay_samples < 1:
            delay_samples = 1
        cdef float s, acc
        cdef int p

        for i from 0 <= i < <int>nframes:
            p = (self.delay_ptr - delay_samples)
            if p < 0:
                p += self.delay_max
            acc = 0
            for j in range(self.num_mics):
                v = i_mic[j][i]
                if v > 1.0:
                    v = 1.0
                if v < -1.0:
                    v = -1.0
                acc += self.mic_volume[j] * v
            s = self.delay_buf[p] * self.mic_feedback + acc
            o_l[i] = s
            o_r[i] = s
            self.delay_buf[self.delay_ptr] = s
            self.delay_ptr += 1
            if self.delay_ptr >= self.delay_max:
                self.delay_ptr = 0

    def shutdown(self):
        if self.dead:
            return
        jack_client_close(self.client)
        free(self.delay_buf)
        self.delay_buf = NULL
        self.dead = True

    def set_mic_volume(self, channel, value):
        self.mic_volume[channel] = value

    def set_mic_delay(self, value):
        self.mic_delay = value

    def set_mic_feedback(self, value):
        self.mic_feedback = value

    def __del__(self):
        self.shutdown()
