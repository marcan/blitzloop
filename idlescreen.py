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

import time, math
import OpenGL.GL as gl
import OpenGL.GLU as glu
import PIL

class ImageTexture(object):
	def __init__(self, img_file):
		self.image = PIL.Image.open(img_file).convert("RGBA")
		self.texid = gl.glGenTextures(1)

		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_NEAREST);
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP);
		gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP);

		glu.gluBuild2DMipmaps(gl.GL_TEXTURE_2D, 4, self.width, self.height, gl.GL_RGBA,
				      gl.GL_UNSIGNED_BYTE, self.image.tostring())

	@property
	def width(self):
		return self.image.size[0]

	@property
	def height(self):
		return self.image.size[1]

	@property
	def aspect(self):
		return self.width / float(self.height)
	
	def __del__(self):
		gl.glDeleteTextures(self.texid)
	
	def draw(self, x=0, y=0, width=1, height=None, brightness=1.0):
		if height is None:
			height = width / self.aspect

		gl.glEnable(gl.GL_BLEND)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA);
		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D, self.texid)
		gl.glEnable(gl.GL_TEXTURE_2D)
		gl.glBegin(gl.GL_TRIANGLE_STRIP)
		gl.glColor4f(brightness, brightness, brightness,1)
		gl.glTexCoord2f(0, 1)
		gl.glVertex2f(x, y)
		gl.glTexCoord2f(1, 1)
		gl.glVertex2f(x+width, y)
		gl.glTexCoord2f(0, 0)
		gl.glVertex2f(x, y+height)
		gl.glTexCoord2f(1, 0)
		gl.glVertex2f(x+width, y+height)
		gl.glEnd()
		gl.glDisable(gl.GL_TEXTURE_2D)
		

class IdleScreen(object):
	def __init__(self, display):
		self.display = display
		self.logo = ImageTexture("logo.png")
		self.tablet = ImageTexture("tablet.png")
		self.hand = ImageTexture("hand.png")
		self.reset()

	def reset(self):
		self.fade = 0
		self.st = time.time()
		self.closing = False

	def close(self):
		self.closing = True

	def __iter__(self):
		return self

	def next(self):
		t = time.time() - self.st
		self.display.set_aspect(4.0/3.0)
		if self.closing:
			self.fade -= 0.015
			if self.fade < 0:
				raise StopIteration()
		elif self.fade < 1:
			self.fade = min(1, self.fade + 0.015)
		
		gl.glClearColor(1, 1, 1, 1)
		gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
		self.logo.draw(y=(1 / self.display.aspect) - (1 / self.logo.aspect))
		self.tablet.draw(x=0.4, y=0.12, width=0.2)
		d = math.sin(t / 0.5 * math.pi) * 0.02
		self.hand.draw(x=0.5 - 0.6 * d, y=0.03 + d, width=0.1)

		self.display.set_aspect(None)
		gl.glBegin(gl.GL_TRIANGLE_STRIP)
		gl.glColor4f(0, 0, 0, 1-self.fade)
		gl.glVertex2f(0, 0)
		gl.glVertex2f(0, 1)
		gl.glVertex2f(1, 0)
		gl.glVertex2f(1, 1)
		gl.glEnd()
		
