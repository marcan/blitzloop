#!/usr/bin/env python
import os

# TODO: Handle Cython missing at setup time.
#
from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize

extensions=[
    Extension(
        '_audio',
        ['blitzloop/_audio.pyx'],
        language='c',
        libraries=['jack']
    ),
]

setup(
        name='blitzloop',
        version='0.1',
        packages=find_packages(),
        ext_modules=cythonize(extensions),
        entry_points={
            'console_scripts': [
                'blitzloop = blitzloop.main',
            ]
        },
        setup_requires=[
            'Cython',
            '3to2',
        ],
        install_requires=[
            '3to2',
            'Cython',
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
