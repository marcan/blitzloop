# Overview
The suggested way to get Blitzloop running is to install it in a virtualenv and
use and your operating system's packet manager for libraries. If you want to do
things your own way, here's a nonexhaustive list of dependencies:

* Core:
   * Python 2.6 or 2.7
   * Cython
* Libs and headers (for _audio.pyx):
   * JACK
* Python modules/bindings:
   * PIL
   * bottle
   * ffms (optional, for record.py)
   * freetype-py
   * numpy
   * paste
   * pympv
   * pyopengl
* Libraries
   * libffms2
   * libfreetype
   * libjack
   * libmpv
   * librubberband

# Set up process

### Install the dependencies
On Debian, this should set you up:
```shell
sudo apt-get install libjack-jackd2-dev librubberband-dev libffms2-dev libfreetype6-dev libass-dev libgl1-mesa-dev libavfilter-dev
```

Under OSX, you need homebrew's python in addition to the libraries:
```shell
brew install python jack jpeg ffms2 rubberband libass freetype
```

### Set up python environment
```shell
BL_VENV=blitzloop-prod
mkvirtualenv ${BL_VENV}
pip install cython
```

Under OSX, you need some extra options to make sure python libs are able to find
homebrew shared libs:
```shell
PIP_FLAGS=(--global-option=build_ext --global-option=-I$(brew --prefix)/include --global-option=-L$(brew --prefix)/lib)
```

### Get libmpv
You need version 0.21.0 of `mpv` or higher.

Under OSX, run:
```shell
brew install mpv --with-rubberband --with-jack
```

If your package manager doesn't have a version which is recent enough, install
mpv from source:
```shell
cd ${BL_HOME}
mkdir mpv-dist
git clone https://github.com/mpv-player/mpv
cd mpv
./bootstrap.py
./waf --enable-libmpv-shared --prefix=${BL_HOME}/mpv-dist configure
./waf build
./waf install
```

### Get pympv.
```shell
pip install 'git+git://github.com/yacoob/pympv.git@HEAD' ${PIP_FLAGS}
```

### Install Blitzloop itself
```shell
pip install 'git+git://github.com/marcan/blitzloop.git@libmpv' ${PIP_FLAGS}
```

### Add songs.
```shell
cd ${BL_HOME}
ln -s /your/song/directory songs
```

# Sing!
TODO: fix this, as it's currently broken
```shell
pyenv activate ${BL_VENV}
cd ${BL_HOME}/app
export PYTHONPATH=$(echo `pwd`/build/lib.*)
LD_LIBRARY_PATH=../mpv-dist/lib python ./main.py -fs ../songs 1024 768
```

Visit port `10111` on your computer in a web browser, and sing!
