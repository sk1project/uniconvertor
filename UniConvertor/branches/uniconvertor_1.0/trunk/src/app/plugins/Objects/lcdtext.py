# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA


###Sketch Config
#type = PluginCompound
#class_name = 'LCDText'
#menu_text = 'LCD Text'
#parameters = (\
#    ('text', 'text', '0', None, 'Text'), \
#    ('size', 'length', 10.0, (0.0, None), 'Size'))
#standard_messages = 1
###End

(''"LCD Text")
(''"Text")
(''"Size")

from app import Scale, TrafoPlugin, PolyBezier, CreatePath


segments = ((( 0, 18), (10, 18), ( 8, 16), ( 2, 16), ( 0, 18)),
			(( 0, 18), ( 2, 16), ( 2, 10), ( 0,	 9), ( 0, 18)),
			((10, 18), (10,  9), ( 8, 10), ( 8, 16), (10, 18)),
			(( 0,  9), ( 2, 10), ( 8, 10), (10,	 9), ( 8,  8), (2, 8), (0, 9)),
			(( 0,  9), ( 2,  8), ( 2,  2), ( 0,	 0), ( 0,  9)),
			((10,  9), (10,  0), ( 8,  2), ( 8,	 8), (10,  9)),
			(( 0,  0), ( 2,  2), ( 8,  2), (10,	 0), ( 0,  0)))

chardefs = (('0DO', (0, 1, 2, 4, 5, 6)),
			('1Il', (2, 5)),
			('2Zz', (0, 2, 3, 4, 6)),
			('3', (0, 2, 3, 5, 6)),
			('4', (1, 2, 3, 5)),
			('5Ss', (0, 1, 3, 5, 6)),
			('6G', (0, 1, 3, 4, 5, 6)),
			('7', (0, 2, 5)),
			('8BQ', (0, 1, 2, 3, 4, 5, 6)),
			('9gq', (0, 1, 2, 3, 5, 6)),
			('AR', (0, 1, 2, 3, 4, 5)),
			('C([{', (0, 1, 4, 6)),
			('E', (0, 1, 3, 4, 6)),
			('Ff', (0, 1, 3, 4)),
			('HKMNWXkmwx', (1, 2, 3, 4, 5)),
			('J', (2, 4, 5, 6)),
			('L', (1, 4, 6)),
			('Pp', (0, 1, 2, 3, 4)),
			('T', (0, 1, 4)),
			('UV', (1, 2, 4, 5, 6)),
			('Yy', (1, 2, 3, 4)),
			('b', (1, 3, 4, 5, 6)),
			('c', (3, 4, 6)),
			('d', (2, 3, 4, 5, 6)),
			('e', (0, 1, 2, 3, 4, 6)),
			('h', (1, 3, 4, 5)),
			('i', (5,)),
			('j', (5, 6)),
			('n', (3, 4, 5)),
			('oa', (3, 4, 5, 6)),
			('r', (3, 4)),
			('t', (1, 3, 4, 6)),
			('uv', (4, 5, 6)),
			("'", (2,)),
			("`", (1,)),
			('"', (1, 2)),
			('-', (3,)),
			(' ', ()),
			('_', (6,)),
			(')]}', (0, 2, 5, 6)),
			(',', (4,)),
			('?', (0, 2, 3, 4)),
			)

char_segs = {}
for chars, segs in chardefs:
	for char in chars:
		char_segs[char] = segs



char_width = 11
char_scale = 18

class LCDText(TrafoPlugin):

	class_name = 'LCDText'
	is_curve = 1

	def __init__(self, text = '0', size = 12.0, trafo = None, loading = 0,
					duplicate = None):
		TrafoPlugin.__init__(self, trafo = trafo, duplicate = duplicate)
		if duplicate is not None:
			self.text = duplicate.text
			self.size = duplicate.size
		else:
			self.text = text
			self.size = size
		if not loading:
			self.recompute()

	def recompute(self):
		paths = []
		trafo = self.trafo(Scale(self.size / float(char_scale)))
		width = 0
		for char in self.text:
			segs = char_segs.get(char)
			if segs is not None:
				for seg in segs:
					path = CreatePath()
					map(path.AppendLine, segments[seg])
					path.ClosePath()
					path.Translate(width, 0)
					path.Transform(trafo)
					paths.append(path)
				width = width + char_width

		paths = tuple(paths)
		if self.objects:
			self.objects[0].SetPaths(paths)
		else:
			self.set_objects([PolyBezier(paths)])

	def Text(self):
		return self.text

	def Size(self):
		return self.size

	def SaveToFile(self, file):
		TrafoPlugin.SaveToFile(self, file, self.text, self.size,
								self.trafo.coeff())

	def Info(self):
		return _("LCD Text: `%(text)s', size %(size)g") % self.__dict__

	def AsBezier(self):
		return self.objects[0].AsBezier()

	def Paths(self):
		return self.objects[0].Paths()

