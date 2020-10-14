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
import os.path
import sys
import configargparse


RESDIR = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'res')
CFG = {
        'fontdir': os.path.join(RESDIR, 'fonts'),
        'gfxdir': os.path.join(RESDIR, 'gfx'),
        'webdir': os.path.join(RESDIR, 'web'),
}

def init_argparser():
    config_home = os.getenv('XDG_CONFIG_HOME', '~/.config')
    home = os.path.expanduser('~')
    if config_home.startswith(home):
        config_home = '~' + config_home[len(home):]
    config_file = os.path.join(config_home, 'blitzloop', 'blitzloop.conf')
    configargparse.init_argument_parser(
            default_config_files=['/etc/blitzloop/blitzloop.conf', config_file])
    parser = configargparse.get_argument_parser()
    parser.add_argument(
        '--fullscreen', default=False, action='store_true',
        help='run blitzloop fullscreen')
    parser.add_argument(
        '--display', default="glut",
        help='Choose a display backend')
    parser.add_argument(
        '--mpv-audio-device', default="jack",
        help='Audio output driver and device for libmpv')
    parser.add_argument(
        '--mpv-ao', default=None,
        help='Audio output driver for libmpv (deprecated, use --mpv-audio-device)')
    parser.add_argument(
        '--mpv-options', default="",
        help='Additional options for libmpv (space separated opt=val)')
    parser.add_argument(
        '--mpv-msg-level', default=None,
        help='Message level for mpv')
    parser.add_argument(
        '--mpv-vo', default="opengl-cb",
        help='Video output driver for libmpv')
    parser.add_argument(
        '--mpv-hwdec', default=None,
        help='Hardware decoding mode for libmpv (try --mpv-hwdec=vaapi)')
    parser.add_argument(
        '--mpv-visualizer', default="[aid1]asplit=2[ao][a1]; [a1]volume=volume=%(volume)f * 3.0,showcqt=bar_v=8:count=1:basefreq=120:csp=bt709:s=128x72:axis=0:fps=60:sono_h=0:bar_g=3:cscheme=0.5|1|0|0|0.5|1,format=pix_fmts=rgb24,split[c1][c2]; [c2]vflip,hflip[c3]; [c1][c3]blend=all_mode=addition[vo]",
        help='Visualizer filter for no-video songs')
    parser.add_argument(
        '--fps', default="60", type=int,
        help='Display FPS (required for correct video sync)')
    parser.add_argument(
        '--instant', default=False, action='store_true',
        help='use instant syllable display instead of scrolling')

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
