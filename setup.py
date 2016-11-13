#!/usr/bin/env python
import os

from setuptools import setup, find_packages
from setuptools.extension import Extension

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

ext = 'pyx' if USE_CYTHON else 'c'
extensions=[
    Extension('_audio', ['blitzloop/_audio.%s' % ext], libraries=['jack']),
]
if USE_CYTHON:
    extensions=cythonize(extensions)

setup(
        name='blitzloop',
        version='0.1',
        packages=find_packages(),
        ext_modules=extensions,
        entry_points={
            'console_scripts': [
                'blitzloop = blitzloop.main',
            ]
        },
        setup_requires=[
            '3to2',
        ],
        install_requires=[
            '3to2',
            'Pillow',
            'bottle',
            'ffms',
            'freetype-py',
            'numpy',
            'paste',
            'pympv',
            'pyopengl',
        ],
)
