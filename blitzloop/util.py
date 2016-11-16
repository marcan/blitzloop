#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Hector Martin "marcan" <hector@marcansoft.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import configparser
import os
import sys


RESDIR = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'res')
RESDIRS = {
        'fontdir': os.path.join(RESDIR, 'fonts'),
        'gfxdir': os.path.join(RESDIR, 'gfx'),
        'webdir': os.path.join(RESDIR, 'web'),
}
CONFIG = configparser.ConfigParser(
        interpolation=None,
        defaults={
            'songdir': os.path.expanduser('~/.blitzloop/songs'),
            'port': '10111',
            'fullscreen': 'False',
            'width': '1024',
            'height': '768',
})
try:
    CONFIG.read_file(open(os.path.expanduser('~/.blitzloop/cfg')))
except FileNotFoundError:
    CONFIG['blitzloop'] = {}

def get_cfg():
    return CONFIG['blitzloop']

def get_cfg_bool(k):
    return C

def get_res_path(t, fp):
    return os.path.join(RESDIRS[t], fp)

def get_resfont_path(fp):
    return get_res_path('fontdir', fp)

def get_resgfx_path(fp):
    return get_res_path('gfxdir', fp)

def get_webres_path(fp):
    return get_res_path('webdir', fp)

def map_from(x, min, max):
    return (x-min) / (max-min)

def map_to(x, min, max):
    return min + x * (max - min)
