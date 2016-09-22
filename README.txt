Dependencies:

 Core:
  Python 2.6 or 2.7
  Cython

 Libs and headers (for _audio.pyx):
  JACK

 Python modules/bindings:
  numpy
  ffms (only for record.py)
  freetype-py
  pyopengl
  bottle
  paste
  PIL
  pympv

On Debian:
$ sudo apt-get install \
	cython \
	python-numpy \
	python-opengl \
	python-pip \
	python-bottle \
	python-paste \
	python-imaging \
	libjack-jackd2-dev \
	librubberband-dev \
	libffms2-dev \
	libfreetype6-dev
$ sudo easy_install freetype-py 3to2

Then build the _audio module:
$ python setup.py build
$ export PYTHONPATH=$(echo `pwd`/build/lib.*)

You currently need version 0.21.0 of libmpv, which comes with mpv, plus
updated bindings. 0.21.0 is not released as of this writing, so use git master:

$ git clone https://github.com/mpv-player/mpv
$ cd mpv
$ ./bootstrap.py
$ ./waf --enable-libmpv-shared configure
$ ./waf build
$ ./waf install
$ cd ..
$ git clone https://github.com/marcan/pympv
$ cd pympv
$ python setup.py install

If you want to use record.py to render to video, you need ffms:
$ wget https://bitbucket.org/spirit/ffms/downloads/ffms-0.3a2.tar.bz2
$ tar xvf ffms-0.3a2.tar.bz2
$ cd ffms-0.3a2
$ sudo python2 setup.py install

Audio may be 1-track (mono), 2-track (stereo), 4-track (dual stereo, without
and with vocals)

0) Start up JACK server and make sure it works

1) Test audio system (mic echo effect):
$ python audiotest.py <file.flac>

2) Test graphics (you'll need them for the steptool):
$ python graphics.py
You should see a red triangle. <esc> to exit.

2) Write song file. If you're reading this you probably already have an
example. Do not include @: timing lines in the lyrics section

3) Time BPM:
$ python timetool.py <songfile.txt>
Hit <enter> each beat. Press ctrl-c to exit when done. [Timing] section will
be printed to stdout. Only one constant BPM is supported for now.

4) Test the layout. Fonts are hardcoded for now.
$ python layout.py <songfile.txt>

5) Time the lyrics.
$ python steptool.py <songfile.txt> <quantization> [audio speed]
Hit <space> for each step (atom), and <enter> to terminate the last step of
each compound (lyrics line in the song file). If you don't press <enter> then
the last step will last until the first step of the next compound (i.e. the last
and first steps are adjacent).

"quantization" is the denominator used for rounding to beats. 1 means full
beats, 2 half beats, etc.

You need to hit space one extra time at the end of the file to force it to
write out the result (to <songfile>.new). Hit it a bunch of times just in
case. The program will not exit either way. Ctrl-\ it. Yes, this is made
of fail and will be fixed at some point.

You can add an extra argument to control the audio speed, as a time multiple.
That is, 2 means half speed, 0.5 means double speed (why oh why would you do
that?).

6) Edit the songfile and fix everything you screwed up while timing it.

7) Sing.
$ python play.py [-fs] <songfile.txt> [start position] [variant]

8) Run the full app
$ python main.py -fs <songs directory> 1024 768

Resolution doesn't really matter for fullscreen mode, but must be specified
anyway.
