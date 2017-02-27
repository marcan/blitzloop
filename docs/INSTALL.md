# Overview
The suggested way to get Blitzloop running is to install it in a virtualenv and
use and your operating system's package manager for libraries. If you want to
do things your own way, here's a nonexhaustive list of dependencies:

* Core:
   * Python 3
* Libs and headers (for \_audio.pyx):
   * JACK
* Python modules/bindings:
   * Pillow
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

# Installation

## General instructions

First, install the required OS dependencies:

* Python 3
* JACK
* ffms
* freetype
* OpenGL

Next, install libmpv. You need mpv built with librubberband support. This will
pull in additional dependencies. If your platform has version 0.21.0 or later
with rubberband compiled in, you may use that. Otherwise, compile it from
source:

```shell
git clone https://github.com/mpv-player/mpv
cd mpv
./bootstrap.py
./waf --enable-libmpv-shared configure
./waf build
sudo ./waf install
```

Finally, make a virtualenv and install BlitzLoop:

```shell
python3 -m venv blitz
source blitz/bin/activate
pip install 'git+git://github.com/marcan/blitzloop.git'
```

## Platform specific guides

Please report back any missing dependencies you may encounter while following
these guides.

### Arch Linux

These instructions have been tested on Arch Linux ARM (e.g. Raspberry Pi).

```shell
sudo pacman -S --needed gcc jack ffms2 freetype2 mpv
# Optionally use distro Python packages to save time with pip
sudo pacman -S --needed numpy python-pillow python-freetype python-numpy python-opengl
python -m venv blitz
source blitz/bin/activate
pip install 'git+git://github.com/marcan/blitzloop.git'
```

### Debian

NOTE: not tested recently, please report back feedback and any problems/missing
deps.

```shell
sudo apt-get install libjack-jackd2-dev librubberband-dev libffms2-dev libfreetype6-dev libgl1-mesa-dev libavfilter-dev python3-dev
git clone https://github.com/mpv-player/mpv
cd mpv
./bootstrap.py
./waf --enable-libmpv-shared configure
./waf build
sudo ./waf install
python3 -m venv blitz
source blitz/bin/activate
pip install 'git+git://github.com/marcan/blitzloop.git'
```

### Gentoo Linux
Under Gentoo, this should work (note: `euse` is in gentoolkit):

```shell
sudo euse -p media-video/mpv libmpv rubberband
sudo emerge -avN --noreplace virtual/jack media-libs/ffmpegsource media-libs/freetype media-video/mpv
python3 -m venv blitz
source blitz/bin/activate
pip install 'git+git://github.com/marcan/blitzloop.git'
```

### macOS

```shell
brew install python3 jack jpeg ffms2 rubberband libass freetype
brew install mpv --with-rubberband --with-jack
PIP_FLAGS=(--global-option=build_ext --global-option=-I$(brew --prefix)/include --global-option=-L$(brew --prefix)/lib)
python3 -m venv blitz
source blitz/bin/activate
pip install 'git+git://github.com/marcan/blitzloop.git' ${PIP_FLAGS}
```

Note: Non-empty `PIP_FLAGS` disables usage of wheels in pip, and makes the whole
process slower. You might save time running this command twice, once without
`PIP_FLAGS` to install all dependencies from wheels, and once with `PIP_FLAGS`
to finish the installation - it's only blitzloop itself that needs these flags.

# Usage

## Add songs
Stories tell about ancient caches of existing blitzloop songs. Find one, or make
your own songs. By default, blitzloop expects songs in
`$XDG_DATA_HOME/blitzloop/songs` (generally `~/.local/share/blitzloop/songs`).

### Sing!
```shell
source blitz/bin/activate
blitzloop -fs
```

Visit port `10111` on your computer in a web browser, and sing!
