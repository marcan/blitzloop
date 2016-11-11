#!/usr/bin/env python
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    ext_modules=[
        Extension("_audio",
            ["_audio.pyx"],
            language="c",
            libraries=["jack"]
            )
    ],
    cmdclass={"build_ext": build_ext}
)
