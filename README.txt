Dependencies:

 Core:
  Python 2.6 or 2.7
  Cython

 Libs and headers (for _audio.pyx):
  JACK
  libsndfile
  libsamplerate
  librubberband

 Python modules/bindings:
  numpy
  ffms
  freetype-py
  pyopengl
  bottle
  paste
  PIL

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
	libsndfile-dev \
	libsamplerate-dev \
	librubberband-dev \
	libffms2-dev \
	libfreetype6-dev
$ sudo easy_install freetype-py 3to2
(ffms doesn't work with easy_install for some reason)
$ wget https://bitbucket.org/spirit/ffms/downloads/ffms-0.3a2.tar.bz2
$ tar xvzf ffms-0.3a2.tar.bz2
$ cd ffms-0.3a2
$ sudo python2 setup.py install

Then build the _audio module:
$ python setup.py build
$ export PYTHONPATH=$(echo `pwd`/build/lib.*)

Note: libsndfile doesn't support mp3 (but does support most everything else).
TODO: switch to ffmpegsource.

Audio may be 1-track (mono), 2-track (stereo), 4-track (dual stereo, without
and with vocals)

0) Start up JACK server and make sure it works

1) Test audio playback:
$ python audiotest.py <file.flac>

2) Test graphics (you'll need them for the steptool):
$ python graphics.py
You should see a red triangle. <esc> to exit.

2) Time BPM:
$ python timetool.py <file.flac>
Hit <enter> each beat. Press ctrl-c to exit when done. [Timing] section will
be printed to stdout. Only one constant BPM is supported for now.

3) Write song file. If you're reading this you probably already have an
example. Do not include @: timing lines in the lyrics section

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
$ python play.py [-fs] <songfile.txt> [speed] [pitch]
It'll hang at the end of a song. Ctrl-\ is your friend. Edit the
window size in the python script. It should match your fullscreen resolution
anyway, otherwise the fonts will be rendered at the wrong resolution because
it doesn't check the real window size before prerendering (not ideal). Yes
this will be fixed too.

8) Run the full app
$ python main.py -fs <songs directory> 1024 768

