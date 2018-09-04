#!/usr/bin/env python
import os
import sys

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
    Extension('blitzloop._glfw',
        ['blitzloop/_glfw.%s' % ext], libraries=['glfw']),
]
if USE_CYTHON:
    extensions=cythonize(extensions, force=True)

# res_files = []
# for dirpath, dirname, files in os.walk('blitzloop/res'):
#     for fn in files:
#         res_files.append(os.path.join(dirpath, fn))
# print res_files

if sys.version_info[0] >= 3:
    extra_requires = []
else:
    extra_requires = ['3to2']

setup(
        name='blitzloop',
        version='0.1',
        packages=find_packages(),
        ext_modules=extensions,
        entry_points={
            'console_scripts': [
                'blitzloop = blitzloop.main',
                'blitzloop-single = blitzloop.play',
            ]
        },
        setup_requires=extra_requires,
        install_requires=extra_requires + [
            'ConfigArgParse',
            'Pillow',
            'bottle',
            'freetype-py',
            'numpy',
            'paste',
            'pympv>=0.5.0',
            'pyopengl',
            'jaconv',
        ],
        include_package_data=True,
        zip_safe=False,
)
