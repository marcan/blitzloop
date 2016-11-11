# Linux:

```shell
pyenv virtualenv 2.7.12 bl
pyenv activate bl
pip install cython numpy freetype-py pyopengl bottle paste Pillow 3to2
pip install ffms
python setup.py build
[ mpv instructions with --prefix ]
[ pympv ]
python setup.py build_ext -I../mpv-dist/include -L../mpv-dist/lib
```



# OSX:
```shell
python setup.py build build_ext -I$(brew --prefix)/include -L$(brew --prefix)/lib
brew install jack jpeg ffms2 rubberband libass freetype
brew install mpv --with-rubberband --with-jack
```

# Running
pyenv activate bl
export PYTHONPATH=$(echo `pwd`/build/lib.*)
