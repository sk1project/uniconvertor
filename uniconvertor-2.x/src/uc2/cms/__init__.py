# -*- coding: utf-8 -*-
#
#	Copyright (C) 2011 by Igor E. Novikov
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import libcms


def rgb_to_hexcolor(color):
	"""
	Converts list of RGB float values to hex color string.
	For example: [1.0, 0.0, 1.0] => #ff00ff
	"""
	r, g, b = color
	return '#%02x%02x%02x' % (int(255 * r), int(255 * g), int(255 * b))

def rgba_to_hexcolor(color):
	"""
	Converts list of RGBA float values to hex color string.
	For example: [1.0, 0.0, 1.0, 1.0] => #ff00ffff
	"""
	r, g, b, a = color
	return '#%02x%02x%02x%02x' % (int(255 * r), int(255 * g),
								int(255 * b), int(65535 * a))

def hexcolor_to_rgb(hexcolor):
	"""
	Converts hex color string as a list of float values.
	For example: #ff00ff => [1.0, 0.0, 1.0]
	"""
	r = int(hexcolor[1:3], 0x10) / 255.0
	g = int(hexcolor[3:5], 0x10) / 255.0
	b = int(hexcolor[5:], 0x10) / 255.0
	return [r, g, b]

def cmyk_to_rgb(color):
	"""
	Converts list of CMYK values to RGB.
	"""
	c, m, y, k = color
	r = round(1.0 - min(1.0, c + k), 3)
	g = round(1.0 - min(1.0, m + k), 3)
	b = round(1.0 - min(1.0, y + k), 3)
	return [r, g, b]

def rgb_to_cmyk(color):
	"""
	Converts list of RGB values to CMYK.
	"""
	r, g, b = color
	c = 1.0 - r
	m = 1.0 - g
	y = 1.0 - b
	k = min(c, m, y)
	return [c - k, m - k, y - k, k]

class Color:
	type = []
	value = []
	name = ''

	def __init__(self, val=[libcms.TYPE_RGB_8, [0, 0, 0], 'Black']):
		self.type, self.value, self.name = val

class ColorManager:

	use_cms = False
	qcolor_cache = {}
	qcolor_creator = None

	def __init__(self, creator=None):
		self.qcolor_cache = {}
		self.qcolor_creator = creator

	def get_cairo_color(self, color):
		if color.type == libcms.TYPE_RGB_8:
			return [] + color.value
		if color.type == libcms.TYPE_CMYK_8:
			return cmyk_to_rgb(color.value)

	def get_qcolor(self, color):
		if self.qcolor_cache.has_key(color):
			return self.qcolor_cache[color]
		if color.type == libcms.TYPE_RGB_8:
			hex = rgb_to_hexcolor(color.value)
			qcolor = self.qcolor_creator(hex)
			self.qcolor_cache[color] = qcolor
			return qcolor
		if color.type == libcms.TYPE_CMYK_8:
			data = cmyk_to_rgb(color.value)
			hex = rgb_to_hexcolor(data)
			qcolor = self.qcolor_creator(hex)
			self.qcolor_cache[color] = qcolor
			return qcolor


