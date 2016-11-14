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

import OpenGL.GL as gl
import freetype as ft
import math
import numpy as np
import sys


#  TextureAtlas is based on examples/texture_font.py from freetype-py
#  FreeType high-level python API - Copyright 2011 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
class TextureAtlas(object):
    '''
    Group multiple small data regions into a larger texture.

    The algorithm is based on the article by Jukka Jylänki : "A Thousand Ways
    to Pack the Bin - A Practical Approach to Two-Dimensional Rectangle Bin
    Packing", February 27, 2010. More precisely, this is an implementation of
    the Skyline Bottom-Left algorithm based on C++ sources provided by Jukka
    Jylänki at: http://clb.demon.fi/files/RectangleBinPack/

    Example usage:
    --------------

    atlas = TextureAtlas(512,512,3)
    region = atlas.get_region(20,20)
    ...
    atlas.set_region(region, data)
    '''

    def __init__(self, width=2048, height=2048, depth=1):
        '''
        Initialize a new atlas of given size.

        Parameters
        ----------

        width : int
            Width of the underlying texture

        height : int
            Height of the underlying texture

        depth : 1 to 4
            Depth of the underlying texture
        '''
        self.width = int(math.pow(2, int(math.log(width, 2) + 0.5)))
        self.height = int(math.pow(2, int(math.log(height, 2) + 0.5)))
        self.depth = depth
        self.nodes = [ (0,0,self.width), ]
        self.data = np.zeros((self.height, self.width, self.depth), dtype=np.ubyte)
        self.texid = None
        self.used = 0
        self._dirty = True

    def upload(self):
        '''
        Upload atlas data into video memory.
        '''

        if not self._dirty:
            return

        if self.texid is None:
            self.texid = gl.glGenTextures(1)

        FORMATS = {
            1: (1, gl.GL_ALPHA),
            2: (2, gl.GL_LUMINANCE_ALPHA),
            3: (3, gl.GL_RGB),
            4: (4, gl.GL_RGBA),
        }
        ifmt, fmt = FORMATS[self.depth]
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP )
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP )
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
        gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )
        #gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST )
        #gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST )
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, ifmt,
                        self.width, self.height, 0,
                        fmt, gl.GL_UNSIGNED_BYTE, self.data)

        self._dirty = False

    def set_region(self, region, data):
        '''
        Set a given region width provided data.

        Parameters
        ----------

        region : (int,int,int,int)
            an allocated region (x,y,width,height)

        data : numpy array
            data to be copied into given region
        '''

        x, y, width, height = region
        self.data[y:y+height,x:x+width, :] = data
        self._dirty = True

    def get_region(self, width, height):
        '''
        Get a free region of given size and allocate it

        Parameters
        ----------

        width : int
            Width of region to allocate

        height : int
            Height of region to allocate

        Return
        ------
            A newly allocated region as (x,y,width,height) or None
        '''

        best_height = sys.maxsize
        best_index = None
        best_width = sys.maxsize
        region = 0, 0, width, height

        for i in range(len(self.nodes)):
            y = self.fit(i, width, height)
            if y is not None:
                node = self.nodes[i]
                if (y+height < best_height or
                    (y+height == best_height and node[2] < best_width)):
                    best_height = y+height
                    best_index = i
                    best_width = node[2]
                    region = node[0], y, width, height

        if best_index is None:
            return None

        node = region[0], region[1]+height, width
        self.nodes.insert(best_index, node)

        i = best_index+1
        while i < len(self.nodes):
            node = self.nodes[i]
            prev_node = self.nodes[i-1]
            if node[0] < prev_node[0]+prev_node[2]:
                shrink = prev_node[0]+prev_node[2] - node[0]
                x,y,w = self.nodes[i]
                self.nodes[i] = x+shrink, y, w-shrink
                if self.nodes[i][2] <= 0:
                    del self.nodes[i]
                    i -= 1
                else:
                    break
            else:
                break
            i += 1

        self.merge()
        self.used += width*height
        return region

    def fit(self, index, width, height):
        '''
        Test if region (width,height) fit into self.nodes[index]

        Parameters
        ----------

        index : int
            Index of the internal node to be tested

        width : int
            Width or the region to be tested

        height : int
            Height or the region to be tested

        '''

        node = self.nodes[index]
        x,y = node[0], node[1]
        width_left = width

        if x+width > self.width:
            return None

        i = index
        while width_left > 0:
            node = self.nodes[i]
            y = max(y, node[1])
            if y+height > self.height:
                return None
            width_left -= node[2]
            i += 1
        return y

    def merge(self):
        '''
        Merge nodes
        '''

        i = 0
        while i < len(self.nodes)-1:
            node = self.nodes[i]
            next_node = self.nodes[i+1]
            if node[1] == next_node[1]:
                self.nodes[i] = node[0], node[1], node[2]+next_node[2]
                del self.nodes[i+1]
            else:
                i += 1

    def __del__(self):
        if self.texid is not None:
            gl.glDeleteTextures(self.texid)

def bitmap_to_numpy(bitmap, dtype=np.uint8):
    pitch = bitmap.pitch
    width = bitmap.width
    buf = bitmap.buffer
    arr = np.array(buf,dtype=dtype).reshape(bitmap.rows, bitmap.pitch)
    if pitch != width:
        return arr[:,:width]
    else:
        return arr

class OutlinedGlyph(object):
    def __init__(self, font, charcode):
        self.font = font
        self.face = font.face

        self.face.load_char(charcode, ft.FT_LOAD_DEFAULT | ft.FT_LOAD_NO_BITMAP)

        fill = self.get_glyph()
        border = self.get_glyph(self.font.style.border_width)
        outline = self.get_glyph(self.font.style.border_width + self.font.style.outline_width)

        (top, left, width, height), (fill, border, outline) = self.get_bitmaps(fill, border, outline)

        outline = outline - border
        border = border - fill

        stack = np.dstack((fill, border, outline))
        self.data = np.clip(stack * 255.0, 0, 255).astype(np.uint8)
        self.top = top / self.font.hres
        self.left = left / self.font.hres
        self.pwidth = width
        self.pheight = height
        self.width = width / self.font.hres
        self.height = height / self.font.hres
        self.bot = self.top - self.height
        self.right = self.left + self.width
        self.dy = self.font.ft2screen(self.face.glyph.advance.y)
        self.dx = self.font.ft2screen(self.face.glyph.advance.x)

    def get_glyph(self, stroke=None):
        glyph = self.face.glyph.get_glyph()
        if stroke is not None:
            stroke_width = int(stroke * 64 * self.font.hres / 330)
            stroker = ft.Stroker()
            stroker.set(stroke_width, ft.FT_STROKER_LINECAP_ROUND, ft.FT_STROKER_LINEJOIN_ROUND, 0)
            # StrokeBorder is not wrapped in freetype-py.Glyph...
            error = ft.FT_Glyph_StrokeBorder(ft.byref(glyph._FT_Glyph), stroker._FT_Stroker, 0, 0)
            if error:
                raise ft.FT_Exception(error)
        blyph = glyph.to_bitmap(ft.FT_RENDER_MODE_NORMAL, ft.Vector(0,0))
        blyph.glyph = glyph # keep a reference, otherwise it blows up
        return blyph

        #bitmap = f_glyph.bitmap
        #top, left = f_glyph.bitmap_top, f_glyph.bitmap_left
        #f_width, f_height = f_bitmap.width, f_bitmap.rows
        #f_data = bitmap_to_numpy(f_bitmap)/255.0
        #glyph = self.face.glyph
        #bitmap = f_glyph.bitmap
        #f_top, f_left, = f_glyph.bitmap_top, f_glyph.bitmap_left
        #f_width, f_height = f_bitmap.width, f_bitmap.rows
        #f_data = bitmap_to_numpy(f_bitmap)/255.0

    def get_bitmaps(self, *glyphs):
        corners = []
        for glyph in glyphs:
            corners.append((glyph.top, glyph.left,
                glyph.top - glyph.bitmap.rows,
                glyph.left + glyph.bitmap.width))
        corners = list(zip(*corners))
        top, left, bot, right = max(corners[0]), min(corners[1]), min(corners[2]), max(corners[3])

        width = right - left
        height = top - bot

        bitmaps = []
        for glyph in glyphs:
            expanded = np.zeros((height,width), dtype=np.float)
            dx = glyph.left - left
            dy = top - glyph.top
            data = bitmap_to_numpy(glyph.bitmap, np.float) / 255.0
            expanded[dy:dy+glyph.bitmap.rows, dx:dx+glyph.bitmap.width] = data
            bitmaps.append(expanded)

        return (top, left, width, height), bitmaps

class TextureFont(object):
    def __init__(self, hres, atlas, filename, size, style, glyphclass=OutlinedGlyph):
        self.hres = hres
        self.atlas = atlas
        assert atlas.depth == 3
        self.filename = filename
        self.size = size
        self.style = style
        self.glyphs = {}
        self.glyphclass = glyphclass
        self.face = ft.Face(self.filename)
        self.face.set_char_size(int(self.size * 64), hres=int(self.hres / 4), vres=int(self.hres / 4))
        self._dirty = True
        metrics = self.face.size
        self.ascender = self.ft2screen(metrics.ascender)
        self.descender = self.ft2screen(metrics.descender)
        self.height = self.ft2screen(metrics.height)
        self.linegap = self.height - self.ascender + self.descender
        self.depth = atlas.depth

    def ft2screen(self, c):
        return int((c + 32) / 64) / float(self.hres)

    def get_glyph(self, charcode):
        if charcode in self.glyphs:
            return self.glyphs[charcode]

        glyph = self.glyphclass(self, charcode)
        region = self.atlas.get_region(glyph.pwidth+2, glyph.pheight+2)
        if region is None:
            raise Exception("Atlas is full")
        x, y, w, h = region
        x += 1
        y += 1
        w -= 2
        h -= 2
        self.atlas.set_region((x, y, w, h), glyph.data)
        glyph.tex_top = y / float(self.atlas.height)
        glyph.tex_bot = glyph.tex_top + (h / float(self.atlas.width))
        glyph.tex_left = x / float(self.atlas.height)
        glyph.tex_right = glyph.tex_left + (w / float(self.atlas.width))
        self.glyphs[charcode] = glyph
        self._dirty = True
        return glyph

    def get_kerning(self, prev, cur):
        kern = self.face.get_kerning(prev, cur)
        return self.ft2screen(kern.x), self.ft2screen(kern.x)
