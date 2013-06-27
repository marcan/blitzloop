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

import song
import texture_font
import numpy as np
import OpenGL.GL as gl
import OpenGL.GL.shaders as shaders
from contextlib import nested
from OpenGL.arrays import vbo
from util import map_from, map_to

vs_karaoke = """
#version 120

attribute vec3 border_color;
attribute vec3 fill_color;
attribute vec3 outline_color;
attribute vec3 border_color_on;
attribute vec3 fill_color_on;
attribute vec3 outline_color_on;

attribute float glyph_time;
attribute vec2 atom_time;
attribute vec2 line_time;
uniform float time;

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
	v_texcoord = gl_MultiTexCoord0.st;

	v_time = glyph_time;

	v_fill_color = fill_color;
	v_border_color = border_color;
	v_outline_color = outline_color;
	v_fill_color_on = fill_color_on;
	v_border_color_on = border_color_on;
	v_outline_color_on = outline_color_on;

	float line_start = line_time.x;
	float line_end = line_time.y;

	float fade_in = linstep(line_start, line_start + fade, time);
	float fade_out = linstep(line_end - fade, line_end, time);

	v_alpha = fade_in - fade_out;

	vec4 pos = gl_Vertex;

	float x_shift = 0.03;

	pos.x -= x_shift * smoothstep(0, 2, 1-fade_in);
	pos.x += x_shift * smoothstep(0, 2, fade_out);

	gl_Position = gl_ModelViewProjectionMatrix * pos;
}
"""

fs_karaoke = """
#version 120

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
	gl_FragColor.rgb /= a;
	gl_FragColor.a = a * v_alpha;
}
"""

class GlyphInstance(object):
	def __init__(self, glyph, x, y, style):
		self.glyph = glyph
		self.x = x
		self.y = y
		self.tx1 = self.tx2 = 0
		self.t1 = self.t2 = 0
		self.colors = style.colors
		self.colors_on = style.colors_on

	def set_timing(self, tx1, tx2, t1, t2):
		self.tx1 = tx1
		self.tx2 = tx2
		self.t1 = t1
		self.t2 = t2

	def __repr__(self):
		return "Gl(%.04f,%.04f)" % (self.x, self.y)

class DisplayLine(object):
	def __init__(self, display):
		self.display = display
		self.glyphs = []
		self.text = u""
		self.px = 0
		self.py = 0
		self.x = 0.0
		self.y = 0.0
		self._start_t = None
		self._end_t = None
		self.start = None
		self.end = None
		self.fade_in_time = self.fade_out_time = 1

		self.descender = 0
		self.ascender = 0

		self.want_row = None

	def copy(self):
		l = DisplayLine(self.display)
		l.text = self.text
		l.glyphs = list(self.glyphs)
		l.px = self.px
		l.py = self.py
		l.x = self.x
		l.y = self.y
		l._start_t = self._start_t
		l._end_t = self._end_t
		l.start = self.start
		l.end = self.end
		l.ascender = self.ascender
		l.descender = self.descender

		l.want_row = self.want_row
		return l

	@property
	def width(self):
		return self.px
	
	@property
	def height(self):
		return self.ascender - self.descender

	@property
	def lim_start(self):
		return self._start_t - self.fade_in_time

	@property
	def lim_end(self):
		return self._end_t + self.fade_in_time

	def add(self, molecule, get_atom_time, style, font, ruby_font):
		# append a space if we are joining with a previous molecule
		space_char = molecule.SPACE
		if self.glyphs:
			glyph = font.get_glyph(space_char)
			self.px += glyph.dx
			self.py += glyph.dy
			self.text += space_char
		prev_char = None
		step = 0

		new_ascender = font.ascender
		if ruby_font:
			new_ascender += ruby_font.ascender - ruby_font.descender
		self.ascender = max(self.ascender, new_ascender)
		self.descender = min(self.descender, font.descender)

		# add the molecule's atoms
		for atom in molecule.atoms:
			atom_x, atom_y = self.px, self.py
			edge_px = None
			glyphs = []
			# add the atom's base text as glyphs
			for i,c in enumerate(atom.text):
				if atom.particle_edge is not None and i == atom.particle_edge:
					edge_px = self.px
				self.text += c
				glyph = font.get_glyph(c)
				gi = GlyphInstance(glyph, self.px, self.py, style)
				if prev_char is not None:
					kx, ky = font.get_kerning(prev_char, c)
					self.px += kx
					self.py += ky
				glyphs.append(gi)
				self.px += glyph.dx
				self.py += glyph.dy
				prev_char = c
			# assign the timing map for the atom's glyphs
			# atom_x (left) -> atom start time
			# self.px (right) -> atom end time
			for glyph in glyphs:
				start, end = get_atom_time(step, atom.steps)
				if self._start_t is None:
					self._start_t = start
				else:
					self._start_t = min(start, self._start_t)
				if self._end_t is None:
					self._end_t = end
				else:
					self._end_t = max(end, self._end_t)
				glyph.set_timing(atom_x, self.px, start, end)
			self.glyphs += glyphs
			# if the atom has subatomic particles (ruby text)
			if atom.particles is not None:
				# ruby pen. we will adjust X later when centering over atom.
				ruby_px = 0
				ruby_py = self.display.round_coord(atom_y + font.ascender - ruby_font.descender)
				ruby_prev_char = None
				ruby_glyphs = []
				par_step = step
				# add the particles
				for particle in atom.particles:
					par_glyphs = []
					particle_x = ruby_px
					# add the characters in the particle
					for c in particle.text:
						glyph = ruby_font.get_glyph(c)
						gi = GlyphInstance(glyph, ruby_px, ruby_py, style)
						if ruby_prev_char is not None:
							kx, ky = ruby_font.get_kerning(ruby_prev_char, c)
							ruby_px += kx
							ruby_py += ky
						par_glyphs.append(gi)
						ruby_px += glyph.dx
						ruby_py += glyph.dy
						ruby_prev_char = c
					for glyph in par_glyphs:
						start, end = get_atom_time(par_step, particle.steps)
						glyph.set_timing(particle_x, ruby_px, start, end)
					par_step += particle.steps
					ruby_glyphs += par_glyphs
				# center the ruby text over the atom
				if edge_px is not None:
					atom_width = edge_px - atom_x
				else:
					atom_width = self.px - atom_x
				dx = self.display.round_coord(atom_x + (atom_width - ruby_px) / 2.0)
				for glyph in ruby_glyphs:
					glyph.tx1 += dx
					glyph.tx2 += dx
					glyph.x += dx
					self.glyphs.append(glyph)
			step += atom.steps

		self.start = self.lim_start
		self.end = self.lim_end

	def build(self):
		vbodata = []
		idxdata = []
		for i,g in enumerate(self.glyphs):
			tleft = map_to(map_from(g.x + g.glyph.left, g.tx1, g.tx2), g.t1, g.t2)
			tright = map_to(map_from(g.x + g.glyph.right, g.tx1, g.tx2), g.t1, g.t2)
			const_vbodata = list(i/255.0 for i in sum(g.colors + g.colors_on, ()))
			const_vbodata += (g.t1, g.t2, self.start, self.end)
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
		self.count = len(self.glyphs)

	def draw(self, renderer):
		with nested(self.vbo, self.ibo):
			gl.glPushMatrix()
			x = self.display.round_coord(self.x)
			y = self.display.round_coord(self.y)
			gl.glTranslate(x, y, 0)

			gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
			gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
			renderer.enable_attribs()

			stride = 27*4
			off = 0
			gl.glVertexPointer(2, gl.GL_FLOAT, stride, self.vbo + off)
			off += 2*4
			gl.glTexCoordPointer(2, gl.GL_FLOAT, stride, self.vbo + off)
			off += 2*4
			off += renderer.attrib_pointer("glyph_time", stride, off, self.vbo)
			off += renderer.attrib_pointer("fill_color", stride, off, self.vbo)
			off += renderer.attrib_pointer("border_color", stride, off, self.vbo)
			off += renderer.attrib_pointer("outline_color", stride, off, self.vbo)
			off += renderer.attrib_pointer("fill_color_on", stride, off, self.vbo)
			off += renderer.attrib_pointer("border_color_on", stride, off, self.vbo)
			off += renderer.attrib_pointer("outline_color_on", stride, off, self.vbo)
			off += renderer.attrib_pointer("atom_time", stride, off, self.vbo)
			off += renderer.attrib_pointer("line_time", stride, off, self.vbo)
			assert off == stride

			gl.glDrawElements(gl.GL_TRIANGLES, 6*self.count, gl.GL_UNSIGNED_SHORT, self.ibo)

			gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
			gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
			renderer.disable_attribs()
			gl.glPopMatrix()

	def __unicode__(self):
		return u"DisplayLine<[%s]>" % self.text

class SongLayout(object):
	def __init__(self, song_obj, variant, renderer):
		self.song = song_obj
		self.variant = song_obj.variants[variant]
		self.renderer = renderer

		self.margin = 0.07
		self.rowspacing = 0.01
		self.wrapwidth = 1.0 - self.margin * 2
		self.pre_line = 1.0
		self.post_line = 1.0

		self.lines = {}
		self.fonts = {}

		self._merge_lines()
		self._layout_lines(self.lines[song.TagInfo.BOTTOM], False)
		self._layout_lines(self.lines[song.TagInfo.TOP], True)
		self._build_lines()
		self.renderer.atlas.upload()

	def _get_font(self, style, ruby=False):
		font = style.font if not ruby else style.ruby_font
		size = style.size if not ruby else style.ruby_size
		ident = (font, size, style.border_width, style.outline_width)
		if ident in self.fonts:
			return self.fonts[ident]
		else:
			fontfile = self.song.get_font_path(font)
			font = texture_font.TextureFont(self.renderer.display.width, self.renderer.atlas, fontfile, size, style)
			self.fonts[ident] = font
			return font

	def _merge_lines(self):
		edges = {
			song.TagInfo.TOP: [],
			song.TagInfo.BOTTOM: []
		}
		for compound in self.song.compounds:
			for tag, molecule in compound.items():
				if tag in self.variant.tags:
					tag_info = self.variant.tags[tag]
					edges[tag_info.edge].append((compound.get_atom_time, tag_info, molecule))

		for edge, molecules in edges.items():
			lines = []
			line = None
			for get_atom_time, tag_info, molecule in molecules:
				font = self._get_font(tag_info.style, False)
				if molecule.has_ruby:
					ruby_font = self._get_font(tag_info.style, True)
				else:
					ruby_font = None
				if molecule.break_before or line is None:
					line = DisplayLine(self.renderer.display)
					line.add(molecule, get_atom_time, tag_info.style, font, ruby_font)
					lines.append(line)
					if molecule.row is not None:
						line.want_row = molecule.row
				else:
					tmp = line.copy()
					tmp.add(molecule, get_atom_time, tag_info.style, font, ruby_font)
					if tmp.px > self.wrapwidth:
						line = DisplayLine(self.renderer.display)
						line.add(molecule, get_atom_time, tag_info.style, font, ruby_font)
						lines.append(line)
					else:
						lines[-1] = line = tmp
				if molecule.break_after:
					line = None

			self.lines[edge] = lines

	def _build_lines(self):
		for lines in self.lines.values():
			for dl in lines:
				dl.build()

	def _layout_lines(self, lines, top=False):
		if not lines:
			return
		rows = [[] for i in range(10)]
		lines.sort(key = lambda x: x.start)

		def sortrow(rowid):
			rows[rowid].sort(key = lambda x: x.start)

		def collides(l, rowid):
			c = []
			for l2 in rows[rowid][::-1]:
				if l.start >= l2.end:
					return c
				elif l.end <= l2.start:
					continue
				else:
					c.append(l2)
			else:
				return c

		def canmoveup(l, limit=1):
			if l.row >= limit:
				return False
			for l2 in collides(l, l.row + 1):
				if not canmoveup(l2, limit):
					return False
			return True

		def moveup(l, limit=1):
			assert l.row < limit
			for l2 in collides(l, l.row + 1):
				moveup(l2, limit)
			rows[l.row].remove(l)
			sortrow(l.row)
			l.row += 1
			assert not collides(l, l.row)
			rows[l.row].append(l)
			sortrow(l.row)

		def canmovetop(l):
			return True

		def movetop(l):
				if l.row == 0:
					# FIXME: this can cause another line to violate the
					# "no jumping ahead" rule. meh.
					for row in range(len(rows)):
						if collides(l, row):
							need_row = row + 1
				else:
					need_row = l.row - 1
					for l2 in collides(l, need_row):
						movetop(l2)
				rows[l.row].remove(l)
				sortrow(l.row)
				l.row = need_row
				rows[l.row].append(l)
				sortrow(l.row)

		if not top:
			for i, l in enumerate(lines):
				if l.want_row and not collides(l, l.want_row):
					l.row = l.want_row
					rows[l.want_row].append(l)
				elif not collides(l, 1):
					l.row = 1
					rows[1].append(l)
				elif not collides(l, 0):
					l.row = 0
					rows[0].append(l)
				else:
					need_row = 2
					while collides(l, need_row):
						need_row += 1
					for want_row in (lines[i-1].row,):
						if canmoveup(rows[want_row][-1], need_row):
							moveup(rows[want_row][-1], need_row)
							l.row = want_row
							rows[want_row].append(l)
							break
					else:
						l.row = need_row
						rows[need_row].append(l)
		else:
			for i, l in enumerate(lines):
				for row in range(len(rows)):
					if not collides(l, row):
						need_row = row
						break
				if i == 0 or need_row <= (lines[i-1].row + 1):
					l.row = need_row
					rows[need_row].append(l)
				else:
					for want_row in (lines[i-1].row, lines[i-1].row + 1):
						if canmovetop(rows[want_row][-1]):
							movetop(rows[want_row][-1])
							l.row = want_row
							rows[want_row].append(l)
							break
					else:
						l.row = need_row
						rows[need_row].append(l)

		max_ascender = max(l.ascender for l in lines)
		min_descender = min(l.descender for l in lines)
		row_height = max_ascender - min_descender + self.rowspacing

		lastrow = 1 if top else -1
		max_end = 0
		prev_l = None
		for i, l in enumerate(lines):
			next_l = lines[i+1] if i < len(lines)-1 else None
			if not top:
				if l.row == 0:
					l.x = self.margin + (self.wrapwidth - l.width) # right
				elif (l.start > max_end or l.row > lastrow) and (max_end > l.end or (next_l and next_l.start < l.end)):
					l.x = self.margin # left
				else:
					l.x = self.margin + (self.wrapwidth - l.width) / 2.0 # center
			else:
				if (l.start > max_end or l.row < lastrow) and (max_end > l.end or (next_l and next_l.start < l.end)):
					l.x = self.margin # left
				elif l.row >= 1 and not (next_l and next_l.row > l.row) and (max_end > l.end or (next_l and next_l.start < l.end)):
					l.x = self.margin + (self.wrapwidth - l.width) # right
				else:
					l.x = self.margin + (self.wrapwidth - l.width) / 2.0 # center
			if max_end > l.start and prev_l:
				l.start = max(min(l.start,prev_l.lim_start), l.start - 5)
				prev_in_row = rows[l.row].index(l) - 1
				if prev_in_row >= 0:
					l.start = max(l.start, rows[l.row][prev_in_row].end)
			max_end = max(max_end, l.end)
			lastrow = l.row
			if not top:
				l.y = self.margin - min_descender + row_height * l.row
			else:
				l.y = self.renderer.display.top - self.margin - max_ascender - row_height * l.row
			prev_l = l

	def _layout_lines_top(self, lines):
		if not lines:
			return

	def draw(self, t, renderer):
		for edge, lines in self.lines.items():
			for l in lines:
				if l.start <= t <= l.end:
					l.draw(renderer)

class Renderer(object):
	UNIFORMS = [
		"tex", "time"
	]
	ATTRIBUTES = {
		"glyph_time": (1, gl.GL_FLOAT),
		"atom_time": (2, gl.GL_FLOAT),
		"line_time": (2, gl.GL_FLOAT),
		"border_color": (3, gl.GL_FLOAT),
		"fill_color": (3, gl.GL_FLOAT),
		"outline_color": (3, gl.GL_FLOAT),
		"border_color_on": (3, gl.GL_FLOAT),
		"fill_color_on": (3, gl.GL_FLOAT),
		"outline_color_on": (3, gl.GL_FLOAT),
	}
	TYPE_LEN = {
		gl.GL_FLOAT: 4
	}
	def __init__(self, display):
		self.display = display
		self.shader = shaders.compileProgram(
			shaders.compileShader(vs_karaoke, gl.GL_VERTEX_SHADER),
			shaders.compileShader(fs_karaoke, gl.GL_FRAGMENT_SHADER),
		)
		for i in self.UNIFORMS:
			setattr(self, "l_" + i, gl.glGetUniformLocation(self.shader, i))
		self.attrib_loc = {i: gl.glGetAttribLocation(self.shader, i) for i in self.ATTRIBUTES}
		self.atlas = texture_font.TextureAtlas(depth=3)

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

	def draw(self, time, layout):
		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas.texid)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		gl.glEnable(gl.GL_BLEND)
		with self.shader:
			gl.glUniform1i(self.l_tex, 0)
			gl.glUniform1f(self.l_time, time)
			layout.draw(time, self)

	def reset(self):
		self.atlas = texture_font.TextureAtlas(depth=3)

if __name__ == "__main__":
	import sys, song, graphics
	s = song.Song(sys.argv[1])
	display = graphics.Display(1280,720)
	renderer = Renderer(display)
	layout = SongLayout(s, s.variants.keys()[-1], renderer)
	def render():
		song_time = 1
		while True:
			gl.glClearColor(0, 0.3, 0, 1)
			gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
			gl.glLoadIdentity()
			renderer.draw(song_time, layout)
			song_time += 1/70.0
			yield None
	display.set_render_gen(render)
	display.main_loop()
