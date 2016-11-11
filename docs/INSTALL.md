# Overview
The suggested way to get Blitzloop running is to use [pyenv] for python deps
management and your operating system's packet manager for libraries. If you want
to do things your own way, here's a nonexhaustive list of dependencies:

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

### Get blitzloop
```shell
BL_HOME=$(pwd)
git clone https://github.com/marcan/blitzloop.git app
cd app
git checkout libmpv
```

### Get the dependencies
On Debian, this should set you up:
```shell
sudo apt-get install libjack-jackd2-dev librubberband-dev libffms2-dev libfreetype6-dev libass-dev libgl1-mesa-dev libavfilter-dev
```

Under OSX, try this:
```shell
brew install jack jpeg ffms2 rubberband libass freetype
```

### Set up python environment
```shell
BL_PYENV=blitzloop-prod
pyenv virtualenv ${BL_PYENV}
pyenv activate ${BL_PYENV}
pip install cython numpy freetype-py pyopengl bottle paste Pillow 3to2 ffms
```

### Get libmpv.
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
cd ${BL_HOME}
git clone https://github.com/marcan/pympv
cd pympv
```

Linux:
```shell
python setup.py install build_ext -I../mpv-dist/include -L../mpv-dist/lib
```

OSX:
```shell
python setup.py install build_ext -I$(brew --prefix)/include -L$(brew --prefix)/lib

```


### Build Blitzloop's binary module
```shell
cd ${BL_HOME}/app
python setup.py build
```

On OSX, you need to point the build process to homebrew libraries:
```shell
python setup.py build build_ext -I$(brew --prefix)/include -L$(brew --prefix)/lib
```

### (OSX only) Link the homebrew libraries
Since El Capitan, you can no longer use `DYLD_*` variables to point an
application to shared libraries it should use [without significant fiddling with
your operating system][csrutil]. As a result you need to make sure Blitzloop is
able to find all of the libraries it needs.
```shell
cd ${BL_HOME}/app
for lib in freetype; do ln -s $(brew --prefix)/lib/lib${lib}.dylib; done
```

### Add songs.
```shell
cd ${BL_HOME}
ln -s /your/song/directory songs
```

# Running Blitzloop
```shell
pyenv activate ${BL_PYENV}
cd ${BL_HOME}/app
export PYTHONPATH=$(echo `pwd`/build/lib.*)
python ./main.py -fs songs 1024 768
```

Visit port `10111` on your computer in a web browser, and sing!

[pyenv]: https://github.com/yyuu/pyenv
[csrutil]: https://derflounder.wordpress.com/2015/10/01/system-integrity-protection-adding-another-layer-to-apples-security-model/
