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

import os
import time
from threading import Thread

from libc.stdint cimport *
from libc.stdio cimport puts
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memset
from posix.time cimport clock_gettime, CLOCK_MONOTONIC, timespec

cdef extern from *:
    ctypedef int vint "volatile int"
    void __sync_synchronize() nogil

cdef extern from "stdlib.h" nogil:
    void _exit (int status)

cdef extern from "jack/jack.h":
    enum:
        JackPortIsOutput
        JackPortIsInput
        JackNullOption
        JackPlaybackLatency


    char *JACK_DEFAULT_AUDIO_TYPE

    ctypedef struct jack_port_t
    ctypedef struct jack_client_t
    ctypedef int jack_options_t
    ctypedef int jack_latency_callback_mode_t
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
    void jack_port_get_latency_range(jack_port_t * port, jack_latency_callback_mode_t mode, jack_latency_range_t * range)
    jack_nframes_t jack_last_frame_time(jack_client_t *client) nogil
    jack_nframes_t jack_frame_time (jack_client_t *client) nogil
    int jack_client_close(jack_client_t *)

cdef extern from "sndfile.h":
    enum:
        SFM_READ

    ctypedef int sf_count_t
    ctypedef struct SNDFILE
    ctypedef struct SF_INFO:
        sf_count_t frames
        int samplerate
        int channels
        int format
        int sections
        int seekable

    SNDFILE *sf_open(char *path, int mode, SF_INFO *sfinfo)
    sf_count_t sf_readf_float(SNDFILE *sndfile, float *ptr, sf_count_t frames) nogil
    sf_count_t sf_seek(SNDFILE *sndfile, sf_count_t frames, int whence)
    int sf_close(SNDFILE *sndfile)
    char *sf_strerror(SNDFILE *sndfile)

cdef extern from "samplerate.h":
    enum:
        SRC_SINC_FASTEST

    ctypedef struct SRC_STATE

    ctypedef long (*src_callback_t)(void *cb_data, float **data)

    SRC_STATE* src_callback_new(src_callback_t func, int converter_type, int channels, int *error, void* cb_data)
    SRC_STATE* src_delete(SRC_STATE *state)
    long src_callback_read(SRC_STATE *state, double src_ratio, long frames, float *data) nogil
    int src_reset(SRC_STATE *state)
    char *src_strerror(int error)

cdef extern from "rubberband/RubberBandStretcher.h" namespace "RubberBand":
    enum Option:
        OptionProcessRealTime "RubberBand::RubberBandStretcher::OptionProcessRealTime"
        OptionTransientsCrisp "RubberBand::RubberBandStretcher::OptionTransientsCrisp"
        OptionTransientsMixed "RubberBand::RubberBandStretcher::OptionTransientsMixed"
        OptionTransientsSmooth "RubberBand::RubberBandStretcher::OptionTransientsSmooth"
        OptionDetectorCompound "RubberBand::RubberBandStretcher::OptionDetectorCompound"
        OptionDetectorPercussive "RubberBand::RubberBandStretcher::OptionDetectorPercussive"
        OptionDetectorSoft "RubberBand::RubberBandStretcher::OptionDetectorSoft"
        OptionPhaseLaminar "RubberBand::RubberBandStretcher::OptionPhaseLaminar"
        OptionPhaseIndependent "RubberBand::RubberBandStretcher::OptionPhaseIndependent"
        OptionWindowStandard "RubberBand::RubberBandStretcher::OptionWindowStandard"
        OptionWindowShort "RubberBand::RubberBandStretcher::OptionWindowShort"
        OptionWindowLong "RubberBand::RubberBandStretcher::OptionWindowLong"
        OptionSmoothingOff "RubberBand::RubberBandStretcher::OptionSmoothingOff"
        OptionSmoothingOn "RubberBand::RubberBandStretcher::OptionSmoothingOn"
        OptionFormantShifted "RubberBand::RubberBandStretcher::OptionFormantShifted"
        OptionFormantPreserved "RubberBand::RubberBandStretcher::OptionFormantPreserved"
        OptionChannelsApart "RubberBand::RubberBandStretcher::OptionChannelsApart"
        OptionChannelsTogether "RubberBand::RubberBandStretcher::OptionChannelsTogether"

    cdef cppclass RubberBandStretcher:
        RubberBandStretcher(size_t sampleRate, size_t channels) nogil
        RubberBandStretcher(size_t sampleRate, size_t channels, int options) nogil
        RubberBandStretcher(size_t sampleRate, size_t channels, int options, double initialTimeRatio) nogil
        RubberBandStretcher(size_t sampleRate, size_t channels, int options, double initialTimeRatio, double initialPitchScale) nogil
        void reset() nogil
        void setTimeRatio(double ratio) nogil
        void setPitchScale(double scale) nogil
        size_t getLatency() nogil
        size_t getSamplesRequired() nogil
        void process(float **input, size_t samples, int final) nogil
        int available() nogil
        size_t retrieve(float **output, size_t samples) nogil

cdef extern from "portaudio.h" nogil:
    ctypedef void PaStream
    ctypedef int PaError
    enum:
        paNoError
    ctypedef unsigned long PaSampleFormat
    enum:
        paFloat32
        paNonInterleaved
    ctypedef unsigned long PaStreamCallbackFlags
    ctypedef double PaTime
    ctypedef struct PaStreamCallbackTimeInfo:
        PaTime inputBufferAdcTime
        PaTime currentTime
        PaTime outputBufferDacTime
    enum:
        paContinue
    ctypedef int PaStreamCallback(const void *input, void *output,
            unsigned long buffer_size, const PaStreamCallbackTimeInfo *timing,
            PaStreamCallbackFlags status, void *userdata)
    ctypedef struct PaStreamInfo:
        int structVersion
        PaTime inputLatency
        PaTime outputLatency
        double sampleRate

    PaError Pa_Initialize()
    PaError Pa_Terminate()
    const char *Pa_GetErrorText(PaError error)
    PaError Pa_OpenDefaultStream(PaStream **stream, int num_input, int num_output,
            PaSampleFormat format, double sample_rate, unsigned long buffer_size,
            PaStreamCallback *callback, void *userdata)
    PaError Pa_StartStream(PaStream *stream)
    PaError Pa_CloseStream(PaStream *stream)
    const PaStreamInfo *Pa_GetStreamInfo(PaStream *stream)
    PaTime Pa_GetStreamTime(PaStream *stream)

class AudioFileError(Exception):
    pass

cdef class AtomicInt:
    cdef vint val
    cdef void set(self, int v) nogil:
        __sync_synchronize()
        self.val = v
    cdef int get(self) nogil:
        cdef int t = self.val
        __sync_synchronize()
        return t

cdef long _src_cb(void *cb_data, float **data) nogil:
    return (<AudioFile>cb_data).src_read(data)

cdef class AudioFile:
    cdef:
        SNDFILE *fd
        SF_INFO info
        SRC_STATE *src

        float *buf
        int buf_size
        AtomicInt wptr
        AtomicInt rptr

        float *rbuf
        int rbuf_size

        long read_sample


        AtomicInt die
        AtomicInt first_time_full
        AtomicInt eof

        double src_ratio

        object thread

    def __init__(self, filename, target_rate, init_pos=0):
        self.die = AtomicInt()
        self.die.set(0)
        self.first_time_full = AtomicInt()
        self.first_time_full.set(0)
        self.info.format = 0
        self.eof = AtomicInt()
        self.eof.set(0)

        self.fd = sf_open(filename, SFM_READ, &self.info)
        if self.fd == NULL:
            raise AudioFileError("Failed to open file %s: %s" % (filename, sf_strerror(NULL)))

        init_pos = sf_seek(self.fd, <long>(init_pos * self.info.samplerate), 0);
        init_pos /= float(self.info.samplerate);

        self.src_ratio = <double>target_rate / <double>self.info.samplerate

        self.buf_size = target_rate * 10
        self.buf = <float *>malloc(self.info.channels  * self.buf_size * sizeof(float))

        self.rbuf_size = 2048
        self.rbuf = <float *>malloc(self.info.channels * self.rbuf_size * sizeof(float))

        self.wptr = AtomicInt()
        self.rptr = AtomicInt()
        self.wptr.set(0)
        self.rptr.set(0)

        self.read_sample = init_pos * target_rate

        cdef int error
        self.src = src_callback_new(_src_cb, SRC_SINC_FASTEST, self.info.channels, &error, <void *>self)
        if self.src == NULL:
            free(self.buf)
            self.buf = NULL
            free(self.rbuf)
            self.rbuf = NULL
            raise AudioFileError("Failed to init SRC (%s)" % src_strerror(error))

        self.thread = Thread(target = self.thread_func)
        self.thread.start()
        while not self.first_time_full.get() and not self.eof.get():
            time.sleep(0.1)

    cdef long src_read(self, float **data) nogil:
        data[0] = self.rbuf
        cdef long got = sf_readf_float(self.fd, self.rbuf, self.rbuf_size)
        return got

    def thread_func(self):
        cdef int buf_fill, buf_free, tail, got, wptr
        cdef float *p
        while not self.die.get():
            wptr = self.wptr.get()
            buf_fill = (wptr - self.rptr.get())
            if buf_fill < 0:
                buf_fill += self.buf_size
            buf_free = self.buf_size - 1 - buf_fill
            if buf_free == 0:
                self.first_time_full.set(1)
                time.sleep(0.1)
                continue
            tail = self.buf_size - wptr
            if tail < buf_free:
                buf_free = tail

            with nogil:
                got = src_callback_read(self.src, self.src_ratio, buf_free, &self.buf[wptr * self.info.channels])
            if not got:
                self.eof.set(1)
                return
            assert got <= buf_free
            wptr += got
            assert wptr <= self.buf_size
            if wptr == self.buf_size:
                wptr = 0
            self.wptr.set(wptr)

    cdef int read_pre(self, int samples, float **data) nogil:
        cdef int buf_fill, buf_free, tail, got, wptr, rptr

        rptr = self.rptr.get()
        buf_fill = (self.wptr.get() - rptr)
        if buf_fill < 0:
            buf_fill += self.buf_size
        tail = self.buf_size - rptr
        if samples > buf_fill:
            samples = buf_fill
        if samples > tail:
            samples = tail

        data[0] = &self.buf[rptr * self.info.channels]
        return samples

    cdef int read_post(self, int samples) nogil:
        cdef int rptr = self.rptr.get()
        rptr += samples
        if rptr >= self.buf_size:
            rptr -= self.buf_size
        self.rptr.set(rptr)
        self.read_sample += samples

    def close(self):
        if self.die.get():
            return
        self.die.set(1)
        self.thread.join()
        src_delete(self.src)
        sf_close(self.fd)
        free(self.rbuf)
        free(self.buf)

    @property
    def channels(self):
        return self.info.channels

    @property
    def frames(self):
        return self.info.frames

    @property
    def rate(self):
        return self.info.samplerate

    def __del__(self):
        self.close()

ctypedef struct TimingEntry:
    unsigned int backend_time
    long file_time

cdef class LockfreeQueue:
    cdef:
        AtomicInt w, r
        uint8_t *buf
        int size, count

    def __init__(self, size_t count, size_t element_size):
        self.size = element_size
        self.count = count
        self.w = AtomicInt()
        self.r = AtomicInt()
        self.w.set(0)
        self.r.set(0)
        self.buf = <uint8_t *>malloc(self.size * self.count)

    cdef int get(self, void *p) nogil:
        cdef int r = self.r.get()
        if self.w.get() == r:
            return 0
        memcpy(p, &self.buf[r * self.size], self.size)
        r += 1
        if r == self.count:
            r = 0
        self.r.set(r)
        return 1

    cdef int put(self, void *p) nogil:
        cdef int w = self.w.get()
        cdef int next_w = w + 1
        if next_w == self.count:
            next_w = 0
        if next_w == self.r.get():
            return 0
        memcpy(&self.buf[w * self.size], p, self.size)
        self.w.set(next_w)
        return 1

    def __del__(self):
        free(self.buf)

ctypedef enum State:
    STATE_IDLE
    STATE_PLAYING
    STATE_PAUSED

class AudioEngineError(Exception):
    pass

ctypedef enum AudioChannel:
    OUT_L
    OUT_R
    IN_MIC

cdef class AudioBackend:
    """Base class for audio backends. Default behavior is a "null" backend."""

    cdef:
        int (*user_process_callback)(unsigned int, void *) nogil
        void (*user_shutdown_callback)(void *) nogil
        void *user_callback_arg

    cdef void register_callbacks(self,
            int (*user_process_callback)(unsigned int, void *) nogil,
            void (*user_shutdown_callback)(void *) nogil,
            void *user_callback_arg):
        """Registers callbacks to be used for frame processing and on shutdown."""
        self.user_process_callback = user_process_callback
        self.user_shutdown_callback = user_shutdown_callback
        self.user_callback_arg = user_callback_arg

    cdef unsigned int latency(self) nogil:
        """Returns the end-to-end playback latency estimated by the backend.

        Measured in frames.
        """
        return 0

    cdef unsigned int sample_rate(self) nogil:
        """Returns the sample rate of the audio backend."""
        return 0

    cdef unsigned int current_frame_time(self) nogil:
        """Returns an approximate timestamp of the currently processing frame."""
        return 0

    cdef unsigned int last_frame_time(self) nogil:
        """Returns the timestamp of the last frame processed."""
        return 0

    cdef float *get_buffer(self, AudioChannel channel, unsigned int nframes) nogil:
        """Returns an audio buffer for the requested channel."""
        return NULL

    def activate(self):
        """Starts audio processing through the backend."""

    def shutdown(self):
        """Stops audio processing through the backend."""

cdef class JackBackend(AudioBackend):
    cdef:
        jack_client_t *client
        jack_port_t *in_mic
        jack_port_t *out_l
        jack_port_t *out_r
        int _sample_rate
        unsigned int _latency

    def __init__(self):
        self.client = jack_client_open("AudioEngine", JackNullOption, NULL)
        if self.client == NULL:
            raise AudioEngineError("Could not create JACK client")
        jack_set_process_callback(self.client, self.process_callback, <void *>self)
        jack_on_shutdown(self.client, self.shutdown_callback, <void *>self)

        self.in_mic = jack_port_register(self.client, "mic", JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0)
        self.out_l = jack_port_register(self.client, "l", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)
        self.out_r = jack_port_register(self.client, "r", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0)

        self._sample_rate = jack_get_sample_rate(self.client)

        cdef jack_latency_range_t r
        jack_port_get_latency_range(self.out_l, JackPlaybackLatency, &r)
        self._latency = (r.min + r.max) / 2

    @staticmethod
    cdef int process_callback(jack_nframes_t nframes, void *arg) nogil:
        return (<JackBackend>arg).user_process_callback(nframes, (<JackBackend>arg).user_callback_arg)

    @staticmethod
    cdef void shutdown_callback(void *arg) nogil:
        (<JackBackend>arg).user_shutdown_callback((<JackBackend>arg).user_callback_arg)

    cdef unsigned int latency(self) nogil:
        return self._latency

    cdef unsigned int sample_rate(self) nogil:
        return self._sample_rate

    cdef unsigned int current_frame_time(self) nogil:
        return jack_frame_time(self.client)

    cdef unsigned int last_frame_time(self) nogil:
        return jack_last_frame_time(self.client)

    cdef float *get_buffer(self, AudioChannel channel, unsigned int nframes) nogil:
        if channel == OUT_L:
            return <float *>jack_port_get_buffer(self.out_l, nframes)
        elif channel == OUT_R:
            return <float *>jack_port_get_buffer(self.out_r, nframes)
        elif channel == IN_MIC:
            return <float *>jack_port_get_buffer(self.in_mic, nframes)
        else:
            return NULL

    def activate(self):
        jack_activate(self.client)

        jack_connect(self.client, "system:capture_1", jack_port_name(self.in_mic))
        jack_connect(self.client, jack_port_name(self.out_l), "system:playback_1")
        jack_connect(self.client, jack_port_name(self.out_r), "system:playback_2")

    def shutdown(self):
        jack_client_close(self.client)

cdef double _monotonic_clock_secs() nogil:
    cdef timespec ts
    clock_gettime(CLOCK_MONOTONIC, &ts)
    return ts.tv_sec + (ts.tv_nsec / 1.0e9)

cdef class PortAudioBackend(AudioBackend):
    cdef:
        PaStream *stream

        int _sample_rate
        unsigned int _latency
        unsigned int _last_frame_time
        double _last_frame_ts

        float *out_l
        float *out_r
        float *in_mic

        float test

    def __init__(self):
        self._sample_rate = 48000  # Hardcoded for now...

        err = Pa_Initialize()
        if err != paNoError:
            raise AudioEngineError("Could not initialize PortAudio: %s" % Pa_GetErrorText(err))

        err = Pa_OpenDefaultStream(
                &self.stream, 1, 2, paFloat32 | paNonInterleaved, self._sample_rate,
                0, self.c_stream_callback, <void *>self)
        if err != paNoError:
            raise AudioEngineError("Could not open PortAudio stream: %s" % Pa_GetErrorText(err))

        info = Pa_GetStreamInfo(self.stream)
        self._latency = <unsigned int>(info.outputLatency * info.sampleRate)

    cdef unsigned int latency(self) nogil:
        return self._latency

    cdef unsigned int sample_rate(self) nogil:
        return self._sample_rate

    cdef unsigned int current_frame_time(self) nogil:
        return self._last_frame_time + <unsigned int>((_monotonic_clock_secs() - self._last_frame_ts) * self._sample_rate)

    cdef unsigned int last_frame_time(self) nogil:
        return self._last_frame_time

    cdef float *get_buffer(self, AudioChannel channel, unsigned int nframes) nogil:
        if channel == OUT_L:
            return self.out_l
        elif channel == OUT_R:
            return self.out_r
        elif channel == IN_MIC:
            return self.in_mic
        else:
            return NULL

    def activate(self):
        self._last_frame_time = 0
        self._last_frame_ts = _monotonic_clock_secs()
        self.test = 0
        err = Pa_StartStream(self.stream)
        if err != paNoError:
            raise AudioEngineError("Could not start PortAudio stream: %s" % Pa_GetErrorText(err))

    def shutdown(self):
        Pa_CloseStream(self.stream)
        Pa_Terminate()

    @staticmethod
    cdef int c_stream_callback(const void *input, void *output, unsigned long nframes,
            const PaStreamCallbackTimeInfo* timing, PaStreamCallbackFlags status,
            void *userdata) nogil:
        (<PortAudioBackend>userdata).stream_callback(input, output, nframes, timing, status)
        return paContinue

    cdef void stream_callback(self, const void *input, void *output, unsigned long nframes,
            const PaStreamCallbackTimeInfo* timing, PaStreamCallbackFlags status) nogil:
        self.in_mic = (<float **>input)[0]
        cdef float **output_chans = <float **>output
        self.out_l = output_chans[0]
        self.out_r = output_chans[1]

        self.user_process_callback(nframes, self.user_callback_arg)

        self._last_frame_ts = _monotonic_clock_secs()
        self._last_frame_time += nframes

cdef int _process_cb(unsigned int nframes, void *arg) nogil:
    return (<AudioEngine>arg).process(nframes)

cdef void _shutdown_cb(void *arg) nogil:
    puts("Audio backend shutdown called, dying rudely\n")
    _exit(1)

def get_audio_backend():
    backends = {
        "jack": JackBackend,
        "portaudio": PortAudioBackend,
    }
    return backends[os.environ.get("BLITZLOOP_AUDIO_BACKEND", "jack")]()

cdef class AudioEngine:
    cdef:
        AtomicInt state
        AtomicInt next_state

        AudioBackend audio_backend
        AudioFile cur_file

        int dead

        float volume
        float vocals
        float mic_volume
        float mic_feedback
        float mic_delay
        unsigned int _sample_rate

        float *rb_buf[2]
        float *delay_buf
        int delay_ptr, delay_max
        RubberBandStretcher *rb

        LockfreeQueue timing_queue
        object timing

        float speed, pitch, cur_speed, cur_pitch

    @property
    def sample_rate(self):
        return self._sample_rate

    def __init__(self):
        self.dead = False
        self.state = AtomicInt()
        self.next_state = AtomicInt()
        self.state.set(STATE_IDLE)
        self.next_state.set(STATE_IDLE)
        self.volume = 0.5
        self.mic_volume = 0.8
        self.mic_delay = 0.12
        self.mic_feedback = 0.3
        self.vocals = 1.0
        self.speed = self.cur_speed = 1.0
        self.pitch = self.cur_pitch = 1.0
        self.delay_ptr = 0;
        self.audio_backend = get_audio_backend()
        self.audio_backend.register_callbacks(_process_cb, _shutdown_cb, <void *>self)
        self._sample_rate = self.audio_backend.sample_rate()

        self.rb_buf[0] = <float *>malloc(self._sample_rate * sizeof(float))
        self.rb_buf[1] = <float *>malloc(self._sample_rate * sizeof(float))
        self.delay_max = self._sample_rate
        self.delay_buf = <float *>malloc(self.delay_max * sizeof(float))
        memset(self.delay_buf, 0, self.delay_max * sizeof(float))

        cdef int options = OptionProcessRealTime | OptionTransientsMixed | OptionChannelsTogether | OptionDetectorCompound
        self.rb = new RubberBandStretcher(self._sample_rate, 2, options)
        self.rb.setTimeRatio(self.cur_speed)
        self.rb.setPitchScale(self.cur_pitch)

        self.timing_queue = LockfreeQueue(128, sizeof(TimingEntry))
        self.timing = []

        self.audio_backend.activate()

    cdef int process(self, unsigned int nframes) nogil:
        cdef float *i_mic = self.audio_backend.get_buffer(IN_MIC, nframes)
        cdef float *o_l = self.audio_backend.get_buffer(OUT_L, nframes)
        cdef float *o_r = self.audio_backend.get_buffer(OUT_R, nframes)
        cdef float *f_data

        if self.state.get() != self.next_state.get():
            self.state.set(self.next_state.get())
            if self.state.get() == STATE_IDLE:
                self.rb.reset()

        memset(o_l, 0, sizeof(float) * nframes)
        memset(o_r, 0, sizeof(float) * nframes)

        cdef int r_id = 0
        cdef int channels
        cdef int got, want, left, block
        cdef int i
        cdef unsigned int nframes_left = nframes
        cdef float *o_p[2]
        cdef float *b_l
        cdef float *b_r
        cdef long file_pos = -1
        cdef TimingEntry timing, last_timing
        cdef unsigned int backend_time = self.audio_backend.last_frame_time()
        cdef int at_eof

        cdef float k_i, k_v

        last_timing.backend_time = 0
        last_timing.file_time = 0

        o_p[0] = o_l;
        o_p[1] = o_r;

        if self.speed != self.cur_speed:
            self.cur_speed = self.speed
            self.rb.setTimeRatio(self.cur_speed)
        if self.pitch != self.cur_pitch:
            self.cur_pitch = self.pitch
            self.rb.setPitchScale(self.cur_pitch)

        if self.state.get() == STATE_PLAYING:
            while nframes_left != 0:
                got = self.rb.available()
                if got > <int>nframes_left:
                    got = nframes_left
                got = self.rb.retrieve(o_p, got)
                nframes_left -= got
                for i from 0 <= i < got:
                    o_p[0][i] *= self.volume
                    o_p[1][i] *= self.volume
                o_p[0] += got
                o_p[1] += got
                backend_time += got

                if got == 0:
                    want = self.rb.getSamplesRequired()

                    channels = self.cur_file.info.channels
                    if channels > 1:
                        r_id = 1
                    vl_id = 0
                    vr_id = r_id
                    if channels >= 4:
                        vl_id = 2
                        vr_id = 3

                    b_l = self.rb_buf[0]
                    b_r = self.rb_buf[1]

                    left = want
                    at_eof = self.cur_file.eof.get()

                    for i in range(2):
                        if left == 0:
                            break
                        block = self.cur_file.read_pre(left, &f_data)
                        if i == 0:
                            file_pos = self.cur_file.read_sample
                        left -= block
                        k_v = self.vocals
                        k_i = 1 - self.vocals
                        for i from 0 <= i < block:
                            b_l[0] = k_i * f_data[0] + k_v * f_data[vl_id]
                            b_l += 1
                            b_r[0] = k_i * f_data[r_id] + k_v * f_data[vr_id]
                            b_r += 1
                            f_data += channels
                        self.cur_file.read_post(block)

                    if left == want and at_eof:
                        self.next_state.set(STATE_IDLE)
                        break

                    if file_pos != -1:
                        timing.backend_time = backend_time
                        timing.backend_time += self.audio_backend.latency()
                        timing.backend_time += self.rb.getLatency()
                        timing.file_time = file_pos
                        if timing.backend_time != last_timing.backend_time and timing.file_time != last_timing.file_time:
                            self.timing_queue.put(&timing)
                            last_timing = timing
                    self.rb.process(self.rb_buf, want - left, False)

        cdef int delay_samples = <int>(self.mic_delay * self._sample_rate)
        if delay_samples >= self.delay_max:
            delay_samples = self.delay_max - 1
        if delay_samples < 1:
            delay_samples = 1
        cdef float s
        cdef int p

        for i from 0 <= i < <int>nframes:
            p = (self.delay_ptr - delay_samples)
            if p < 0:
                p += self.delay_max
            s = self.delay_buf[p] * self.mic_feedback + i_mic[i]
            o_l[i] += s * self.mic_volume
            o_r[i] += s * self.mic_volume
            self.delay_buf[self.delay_ptr] = s
            self.delay_ptr += 1
            if self.delay_ptr >= self.delay_max:
                self.delay_ptr = 0

    def sync_state(self):
        while self.next_state.get() != self.state.get():
            time.sleep(0.05)

    def stop(self):
        self.sync_state()
        self.next_state.set(STATE_IDLE)

    def play(self, f):
        self.sync_state()
        if self.state.get() != STATE_IDLE:
            self.stop()
            self.sync_state()

        self.cur_file = f
        self.next_state.set(STATE_PLAYING)

    def shutdown(self):
        if self.dead:
            return
        self.stop()
        self.sync_state()
        self.audio_backend.shutdown()
        self.dead = True
        del self.rb
        free(self.rb_buf[0])
        free(self.rb_buf[1])

    def _current_time(self):
        return self.audio_backend.current_frame_time()

    def _get_timing(self):
        l = []
        cdef TimingEntry te
        while self.timing_queue.get(&te):
            l.append((te.backend_time, te.file_time))
        return l

    def song_time(self):
        if self.state.get() != STATE_PLAYING:
            self._get_timing()
            self.timing = []
            return None
        self.timing += self._get_timing()
        self.timing = self.timing[-2:]
        backend_t = self._current_time()
        if len(self.timing) != 2:
            return None

        backend_a, song_a = self.timing[0]
        backend_b, song_b = self.timing[1]

        if backend_a == backend_b or song_a == song_b:
            return None

        song_pos = song_a + ((backend_t - backend_a) / float(backend_b - backend_a)) * (song_b - song_a)
        song_pos /= self._sample_rate
        return song_pos

    def set_speed(self, speed):
        self.speed = speed

    def set_pitch(self, pitch):
        self.pitch = pitch

    def set_channel(self, channel, value):
        self.vocals = value

    def set_volume(self, value):
        self.volume = value

    def set_mic_volume(self, value):
        self.mic_volume = value

    def set_mic_delay(self, value):
        self.mic_delay = value

    def set_mic_feedback(self, value):
        self.mic_feedback = value

    def set_pause(self, pause):
        self.sync_state()
        if self.state.get() not in (STATE_PLAYING, STATE_PAUSED):
            return
        if pause and self.state.get() == STATE_PLAYING:
            self.next_state.set(STATE_PAUSED)
        elif not pause and self.state.get() == STATE_PAUSED:
            self.next_state.set(STATE_PLAYING)

    def is_playing(self):
        return self.state.get() != STATE_IDLE or self.next_state.get() != STATE_IDLE

    def __del__(self):
        self.shutdown()
