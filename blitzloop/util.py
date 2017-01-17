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

import os
import sys
import configargparse


RESDIR = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'res')
CFG = {
        'fontdir': os.path.join(RESDIR, 'fonts'),
        'gfxdir': os.path.join(RESDIR, 'gfx'),
        'webdir': os.path.join(RESDIR, 'web'),
}

def init_argparser():
    configargparse.init_argument_parser(
            default_config_files=['/etc/blitzloop/cfg', '~/.blitzloop/cfg'])
    parser = configargparse.get_argument_parser()
    parser.add_argument(
        '--fullscreen', default=False, action='store_true',
        help='run blitzloop fullscreen')
    parser.add_argument(
        '--display', default="glut",
        help='Choose a display backend')
    parser.add_argument(
        '--mpv-ao', default="jack",
        help='Audio output driver for libmpv')
    parser.add_argument(
        '--mpv-vo', default="opengl-cb",
        help='Video output driver for libmpv')
    parser.add_argument(
        '--fps', default="60", type=int,
        help='Display FPS (required for correct video sync)')
    parser.add_argument(
        '--mpv-options', default="",
        help='Additional options for libmpv (space separated opt=val)')

def get_argparser():
    return configargparse.get_argument_parser()

_opts = None
def get_opts():
    global _opts
    if _opts is None:
        _opts, unknown = get_argparser().parse_known_args()
    return _opts

def get_res_path(t, fp):
    return os.path.join(CFG[t], fp)

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


init_argparser()
