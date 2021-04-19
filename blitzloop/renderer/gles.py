#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2017 Hector Martin "marcan" <hector@marcansoft.com>
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

import numpy as np
import PIL

from OpenGL import arrays
from OpenGL.arrays import vbo

from blitzloop import texture_font
from blitzloop.util import map_from, map_to, get_opts
from blitzloop.matrix import Matrix

if get_opts().display in ("glut",):
    import OpenGL.GL as gl
    import OpenGL.GL.shaders as shaders
    import OpenGL.GLU as glu
else:
    import OpenGL.GLES2 as gl
    import OpenGL.GLES2.shaders as shaders
    glu = None


vs_karaoke = """
attribute vec4 coords;

attribute vec3 border_color;
attribute vec3 fill_color;
attribute vec3 outline_color;
attribute vec3 border_color_on;
attribute vec3 fill_color_on;
attribute vec3 outline_color_on;

attribute vec3 times;

uniform float time;
uniform mat4 transform;

varying vec2 v_texcoord;
varying vec3 v_border_color;
varying vec3 v_fill_color;
varying vec3 v_outline_color;
varying vec3 v_border_color_on;
varying vec3 v_fill_color_on;
varying vec3 v_outline_color_on;
varying float v_alpha;
varying float v_time;

float fade = 0.5;

float linstep(float min, float max, float v) {
    return clamp((v - min) / (max - min), 0.0, 1.0);
}

void main() {
    v_texcoord = coords.zw;

    v_time = times.x;

    v_fill_color = fill_color;
    v_border_color = border_color;
    v_outline_color = outline_color;
    v_fill_color_on = fill_color_on;
    v_border_color_on = border_color_on;
    v_outline_color_on = outline_color_on;

    float line_start = times.y;
    float line_end = times.z;

    float fade_in = linstep(line_start, line_start + fade, time);
    float fade_out = linstep(line_end - fade, line_end, time);

    v_alpha = fade_in - fade_out;

    vec4 pos = vec4(coords.x, coords.y, 0.0, 1.0);

    float x_shift = 0.03;

    pos.x -= x_shift * smoothstep(0.0, 2.0, 1.0 - fade_in);
    pos.x += x_shift * smoothstep(0.0, 2.0, fade_out);

    gl_Position = transform * pos;
}
"""

fs_karaoke = """
#ifdef GL_ES
precision highp float;
#endif

uniform float time;
uniform sampler2D tex;

varying vec2 v_texcoord;
varying vec3 v_border_color;
varying vec3 v_fill_color;
varying vec3 v_outline_color;
varying vec3 v_border_color_on;
varying vec3 v_fill_color_on;
varying vec3 v_outline_color_on;
varying float v_alpha;
varying float v_time;


void main() {
    vec4 texel = texture2D(tex, v_texcoord.st);
    float outline = texel.b;
    float border = texel.g;
    float fill = texel.r;

    vec3 outline_color, border_color, fill_color;
    if (v_time < time) {
        outline_color = v_outline_color_on;
        border_color = v_border_color_on;
        fill_color = v_fill_color_on;
    } else {
        outline_color = v_outline_color;
        border_color = v_border_color;
        fill_color = v_fill_color;
    }

    float a = (outline + border + fill);

    gl_FragColor.rgb = outline_color * outline;
    gl_FragColor.rgb += border_color * border;
    gl_FragColor.rgb += fill_color * fill;
    gl_FragColor.rgb *= v_alpha;
    gl_FragColor.a = a * v_alpha;
}
"""

vs_solid = """
attribute vec3 coord;

uniform vec4 color;
uniform mat4 transform;

varying vec4 v_color;

void main() {
    v_color = color;
    v_color.rgb *= color.a; // assume unpremultiplied color, premultiply

    vec4 pos = vec4(coord.x, coord.y, coord.z, 1.0);
    gl_Position = transform * pos;
}
"""

fs_solid = """
#ifdef GL_ES
precision highp float;
#endif

varying vec4 v_color;

void main() {
    gl_FragColor = v_color;
}
"""

vs_texture = """
attribute vec3 coord;

uniform vec4 color;
uniform mat4 textransform;
uniform mat4 transform;

varying vec2 v_texcoord;
varying vec4 v_color;

void main() {
    v_color = color;
    v_color.rgb *= color.a; // assume unpremultiplied color, premultiply

    vec4 pos = vec4(coord.x, coord.y, coord.z, 1.0);
    gl_Position = transform * pos;

    vec4 texcoord = textransform * pos;
    v_texcoord = texcoord.xy;
}
"""

fs_texture = """
#ifdef GL_ES
precision highp float;
#endif

uniform sampler2D tex;

varying vec2 v_texcoord;
varying vec4 v_color;

void main() {
    vec4 texel = texture2D(tex, v_texcoord.st);
    gl_FragColor = texel * v_color;
}
"""

class RenderedLine(object):
    def __init__(self, line):
        self.line = line
        self.display = line.display

    def build(self):
        vbodata = []
        idxdata = []
        for i,g in enumerate(self.line.glyphs):
            if get_opts().instant:
                tleft = tright = g.t1
            else:
                tleft = map_to(map_from(g.x + g.glyph.left, g.tx1, g.tx2), g.t1, g.t2)
                tright = map_to(map_from(g.x + g.glyph.right, g.tx1, g.tx2), g.t1, g.t2)
            const_vbodata = [self.line.start, self.line.end]
            const_vbodata += list(i/255.0 for i in sum(g.colors + g.colors_on, ()))
            vbodata.append(
                [g.x + g.glyph.left, g.y + g.glyph.bot,
                g.glyph.tex_left, g.glyph.tex_bot,
                tleft] + const_vbodata)
            vbodata.append(
                [g.x + g.glyph.left, g.y + g.glyph.top,
                g.glyph.tex_left, g.glyph.tex_top,
                tleft] + const_vbodata)
            vbodata.append(
                [g.x + g.glyph.right, g.y + g.glyph.top,
                g.glyph.tex_right, g.glyph.tex_top,
                tright] + const_vbodata)
            vbodata.append(
                [g.x + g.glyph.right, g.y + g.glyph.bot,
                g.glyph.tex_right, g.glyph.tex_bot,
                tright] + const_vbodata)
            idxdata += (i*4, i*4+1, i*4+2, i*4+2, i*4+3, i*4)
        self.vbo = vbo.VBO(np.asarray(vbodata, np.float32), gl.GL_STATIC_DRAW, gl.GL_ARRAY_BUFFER)
        self.ibo = vbo.VBO(np.asarray(idxdata, np.uint16), gl.GL_STATIC_DRAW, gl.GL_ELEMENT_ARRAY_BUFFER)
        self.count = len(self.line.glyphs)

    def draw(self, renderer):
        with self.vbo, self.ibo:
            self.display.matrix.push()
            x = self.display.round_coord(self.line.x)
            y = self.display.round_coord(self.line.y)
            self.display.matrix.translate(x, y)
            self.display.commit_matrix(renderer.l_transform)

            stride = 25*4
            off = 0
            off += renderer.attrib_pointer("coords", stride, off, self.vbo)
            off += renderer.attrib_pointer("times", stride, off, self.vbo)
            off += renderer.attrib_pointer("fill_color", stride, off, self.vbo)
            off += renderer.attrib_pointer("border_color", stride, off, self.vbo)
            off += renderer.attrib_pointer("outline_color", stride, off, self.vbo)
            off += renderer.attrib_pointer("fill_color_on", stride, off, self.vbo)
            off += renderer.attrib_pointer("border_color_on", stride, off, self.vbo)
            off += renderer.attrib_pointer("outline_color_on", stride, off, self.vbo)
            assert off == stride

            gl.glDrawElements(gl.GL_TRIANGLES, 6*self.count, gl.GL_UNSIGNED_SHORT, self.ibo)

            self.display.matrix.pop()

_current_renderer = None

class BaseRenderer(object):
    TYPE_LEN = {
        gl.GL_FLOAT: 4
    }
    def __init__(self, display):
        self.display = display
        self.shader = shaders.compileProgram(
            shaders.compileShader(self.VS, gl.GL_VERTEX_SHADER),
            shaders.compileShader(self.FS, gl.GL_FRAGMENT_SHADER),
        )
        for i in self.UNIFORMS:
            setattr(self, "l_" + i, gl.glGetUniformLocation(self.shader, i))
        self.attrib_loc = {i: gl.glGetAttribLocation(self.shader, i) for i in self.ATTRIBUTES}

    def attrib_pointer(self, attrib, stride, offset, vbo):
        size, data_type = self.ATTRIBUTES[attrib]
        loc = self.attrib_loc[attrib]
        if loc >= 0:
            gl.glVertexAttribPointer(loc, size, data_type, gl.GL_FALSE, stride, vbo + offset)
        return self.TYPE_LEN[data_type] * size

    def enable_attribs(self):
        for i in self.attrib_loc.values():
            if i >= 0:
                gl.glEnableVertexAttribArray(i)

    def disable_attribs(self):
        for i in self.attrib_loc.values():
            if i >= 0:
                gl.glDisableVertexAttribArray(i)

    def activate(self):
        global _current_renderer
        if _current_renderer is not self:
            if _current_renderer is not None:
                _current_renderer.cleanup()
            self.setup()
            _current_renderer = self

    def setup(self):
        pass
    def cleanup(self):
        pass

class KaraokeRenderer(BaseRenderer):
    UNIFORMS = [
        "tex", "time", "transform",
    ]
    ATTRIBUTES = {
        "coords": (4, gl.GL_FLOAT),
        "times": (3, gl.GL_FLOAT),
        "border_color": (3, gl.GL_FLOAT),
        "fill_color": (3, gl.GL_FLOAT),
        "outline_color": (3, gl.GL_FLOAT),
        "border_color_on": (3, gl.GL_FLOAT),
        "fill_color_on": (3, gl.GL_FLOAT),
        "outline_color_on": (3, gl.GL_FLOAT),
    }
    FS = fs_karaoke
    VS = vs_karaoke
    def __init__(self, display):
        BaseRenderer.__init__(self, display)
        self.atlas = texture_font.TextureAtlas(depth=3)

    def setup(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas.texid)
        gl.glUseProgram(self.shader)
        gl.glUniform1i(self.l_tex, 0)
        self.enable_attribs()

    def draw(self, time, layout):
        self.activate()
        gl.glUniform1f(self.l_time, time)
        layout.draw(time, self)

    def cleanup(self):
        self.disable_attribs()
        gl.glUseProgram(0)

    def reset(self):
        self.atlas = texture_font.TextureAtlas(depth=3)

class SolidRenderer(BaseRenderer):
    UNIFORMS = [
        "color", "transform",
    ]
    ATTRIBUTES = {
        "coord": (3, gl.GL_FLOAT),
    }
    VS = vs_solid
    FS = fs_solid

    def __init__(self, display):
        BaseRenderer.__init__(self, display)

        vbodata = [[0., 0., 0.],
                   [1., 0., 0.],
                   [1., 1., 0.],
                   [0., 1., 0.]]

        self.vbo = vbo.VBO(np.asarray(vbodata, np.float32), gl.GL_STATIC_DRAW, gl.GL_ARRAY_BUFFER)

    def setup(self):
        gl.glUseProgram(self.shader)
        self.vbo.bind()
        self.enable_attribs()
        stride = 3*4
        off = 0
        off += self.attrib_pointer("coord", stride, off, self.vbo)
        assert off == stride

    def draw(self, pos, size, color):
        self.activate()
        self.display.matrix.push()
        self.display.matrix.translate(*pos)
        self.display.matrix.scale(*size)
        self.display.commit_matrix(self.l_transform)
        gl.glUniform4f(self.l_color, *color)
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)
        self.display.matrix.pop()

    def cleanup(self):
        self.disable_attribs()
        self.vbo.unbind()
        gl.glUseProgram(0)

class TextureRenderer(SolidRenderer):
    UNIFORMS = [
        "tex", "color", "transform", "textransform"
    ]
    VS = vs_texture
    FS = fs_texture

    def __init__(self, display):
        SolidRenderer.__init__(self, display)
        self.tmatrix = Matrix()

    def setup(self):
        SolidRenderer.setup(self)
        gl.glUniform1i(self.l_tex, 0)

    def draw(self, pos, size, tpos, tsize, color):
        self.activate()
        self.tmatrix.reset()
        self.tmatrix.translate(*tpos)
        self.tmatrix.scale(*tsize)
        gl.glUniformMatrix4fv(self.l_textransform, 1, False, self.tmatrix.m)
        SolidRenderer.draw(self, pos, size, color)

class ImageTexture(object):
    def __init__(self, img_file, texture_renderer):
        self.renderer = texture_renderer
        self.image = PIL.Image.open(img_file).convert("RGBA")

        self.tw = 1
        while self.tw < self.width:
            self.tw *= 2
        self.th = 1
        while self.th < self.height:
            self.th *= 2

        self.teximage = PIL.Image.new("RGBA", (self.tw, self.th), (0, 0, 0, 0))
        self.teximage.paste(self.image, (0,0), self.image)
        self.teximage = self.teximage.convert("RGBa") # premultiply alpha

        self.texid = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        try:
            blob = self.teximage.tobytes()
        except AttributeError:
            blob = self.teximage.tostring()

        if glu is not None:
            glu.gluBuild2DMipmaps(gl.GL_TEXTURE_2D, 4, self.tw, self.th,
                gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, blob)
        else:
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.tw, self.th,
                            0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, blob)
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    @property
    def width(self):
        return self.image.size[0]

    @property
    def height(self):
        return self.image.size[1]

    @property
    def aspect(self):
        return self.width / self.height

    def __del__(self):
        tex = arrays.GLintArray.asArray([self.texid])
        gl.glDeleteTextures(1, tex)

    def draw(self, x=0, y=0, width=1, height=None, alpha=1.0):
        if height is None:
            height = width / self.aspect

        color = (1., 1., 1., alpha)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)

        self.renderer.draw((x, y), (width, height), (0, self.height / self.th),
                           (self.width / self.tw, -self.height / self.th), color)

def cleanup():
    global _current_renderer
    if _current_renderer is not None:
        _current_renderer.cleanup()
        _current_renderer = None

def clear(r, g, b, a):
    gl.glClearColor(r, g, b, a)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
