# Overview
The suggested way to get Blitzloop running is to install it in a virtualenv and
use and your operating system's packet manager for libraries. If you want to do
things your own way, here's a nonexhaustive list of dependencies:

* Core:
   * Python 3
   * Cython
* Libs and headers (for _audio.pyx):
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

# Set up process

### Install the dependencies
On Debian, this should set you up:
```shell
sudo apt-get install libjack-jackd2-dev librubberband-dev libffms2-dev libfreetype6-dev libass-dev libgl1-mesa-dev libavfilter-dev python3-dev
```

Under OSX, you need homebrew's python in addition to the libraries:
```shell
brew install python3 jack jpeg ffms2 rubberband libass freetype
```

Under Gentoo, this should work:
```shell
emerge -av --noreplace virtual/jack media-libs/ffmpegsource media-libs/freetype media-libs/libass media-libs/rubberband
```

### Set up python environment
```shell
BL_VENV=blitzloop-prod
mkvirtualenv --python=$(which python3) ${BL_VENV}
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

On Linux, If your package manager doesn't have a version which is recent enough,
install mpv from source to `/usr/local`:
```shell
git clone https://github.com/mpv-player/mpv
cd mpv
./bootstrap.py
./waf --enable-libmpv-shared configure
./waf build
./waf install
```

On Gentoo Linux, make sure you have the `libmpv` USE flag set, and build mpv:
```shell
sudo euse -p media-video/mpv libmpv
sudo emerge -av media-video/mpv
```
If you're running stable (`arch`, not `~arch`) then you need to add
`media-video/mpv` to `/etc/portage/package.keywords`; as of this writing,
version 0.21.0 or newer is not keyworded stable.

### Install Blitzloop itself
```shell
pip install 'git+git://github.com/marcan/blitzloop.git@HEAD' ${PIP_FLAGS}
```

Note: Non-empty `PIP_FLAGS` disables usage of wheels in pip, and makes the whole
process slower. You might save time running this command twice, once without
`PIP_FLAGS` to install all dependencies from wheels, and once with `PIP_FLAGS`
to finish the installation - it's only blitzloop itself that needs these flags.

### Add songs.
Stories tell about ancient caches of existing blitzloop songs. Find one, or make
your own songs. By default, blitzloop expects songs in `~/.blitzloop/songs`.

### Sing!
```shell
workon ${BL_VENV}
blitzloop -fs ${path_to_your_songs} 1024 768
```

Visit port `10111` on your computer in a web browser, and sing!
