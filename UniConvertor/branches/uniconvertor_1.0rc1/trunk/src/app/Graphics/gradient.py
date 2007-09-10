# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#
#	color gradient classes
#

from blend import Blend, MismatchError

class Gradient:

	def __init__(self, duplicate = None):
		pass

	def ColorAt(self, pos):
		pass

	def Duplicate(self):
		return self.__class__(duplicate = self)


class MultiGradient(Gradient):

	def __init__(self, colors = (), duplicate = None):
		if duplicate is not None:
			self.colors = duplicate.colors[:]
		else:
			if len(colors) < 2:
				raise ValueError, 'at least 2 colors required'
			self.colors = colors

	def StartColor(self):
		return self.colors[0][-1]

	def SetStartColor(self, color):
		undo = (self.SetStartColor, self.colors[0][-1])
		self.colors[0] = (0, color)
		return undo

	def EndColor(self):
		return self.colors[-1][-1]

	def SetEndColor(self, color):
		undo = (self.SetEndColor, self.colors[-1][-1])
		self.colors[-1] = (1, color)
		return undo

	def ColorAt(self, pos):
		colors = self.colors
		for i in range(len(colors) - 1):
			if colors[i][0] <= pos and colors[i + 1][0] >= pos:
				break
		else:
			return self.EndColor()
		start_pos, start_color = colors[i]
		if i < len(colors) - 1:
			end_pos, end_color = colors[i + 1]
		else:
			return start_color
		return Blend(end_color, start_color,
						(pos - start_pos) / float(end_pos - start_pos))

	def Sample(self, num):
		colors = self.colors
		max = num - 1.0
		pos1, color1 = colors[0]
		pos2, color2 = colors[1]
		diff = float(pos2 - pos1)
		cur = 1
		result = []
		blend = color1.Blend
		for i in range(num):
			frac = i / max
			while frac > pos2:
				pos1 = pos2; color1 = color2
				cur = cur + 1
				pos2, color2 = colors[cur]
				diff = float(pos2 - pos1)
				blend = color1.Blend
			frac = (frac - pos1) / diff
			result.append(blend(color2, 1 - frac, frac))
		return result

	def Colors(self):
		return self.colors

	def SetColors(self):
		undo = (self.SetColors, self.colors)
		self.colors = colors
		return undo

	def Blend(self, other, frac1, frac2):
		if type(other) == type(self.colors[0][-1]):
			# blend a gradient with a single color
			sc = self.colors
			c = []
			for i in range(len(sc)):
				p1, c1 = sc[i]
				c.append((p1, c1.Blend(other, frac1, frac2)))
			return self.__class__(c)
		elif other.__class__ == self.__class__:
			# blend two MultiGradient instances
			# XXX: improve this...
			length = min(len(self.colors), len(other.colors))
			sc = self.colors[:length - 1]
			sc.append(self.colors[-1])
			oc = other.colors[:length - 1]
			oc.append(other.colors[-1])
			c = []
			for i in range(length):
				p1, c1 = sc[i]
				p2, c2 = oc[i]
				c.append((frac1 * p1 + frac2 * p2,
							Blend(c1, c2, frac1, frac2)))
			return self.__class__(c)
		else:
			raise MismatchError

	def SaveToFile(self, file):
		file.Gradient(self.colors)


# convenience function for the most common gradient type
def CreateSimpleGradient(start, end):
	return MultiGradient([(0, start), (1, end)])

