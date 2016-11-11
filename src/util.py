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


RESDIR = 'res'
CFG = {
        'fontdir': os.path.join(RESDIR, 'fonts'),
        'gfxdir': os.path.join(RESDIR, 'gfx'),
}

def get_res_path(t, fp):
    return os.path.join(CFG[t], fp)

def get_resfont_path(fp):
    return get_res_path('fontdir', fp)

def get_resgfx_path(fp):
    return get_res_path('gfxdir', fp)

def map_from(x, min, max):
    return (x-min) / (max-min)

def map_to(x, min, max):
    return min + x * (max - min)
