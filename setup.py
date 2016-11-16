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
    Extension('blitzloop._audio',
        ['blitzloop/_audio.%s' % ext], libraries=['jack']),
]
if USE_CYTHON:
    extensions=cythonize(extensions)

# res_files = []
# for dirpath, dirname, files in os.walk('blitzloop/res'):
#     for fn in files:
#         res_files.append(os.path.join(dirpath, fn))
# print res_files

setup(
        name='blitzloop',
        version='0.1.1',
        packages=find_packages(),
        ext_modules=extensions,
        entry_points={
            'console_scripts': [
                'blitzloop = blitzloop.main',
                'blitzloop-single = blitzloop.play',
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
        include_package_data=True,
        zip_safe=False,
)
