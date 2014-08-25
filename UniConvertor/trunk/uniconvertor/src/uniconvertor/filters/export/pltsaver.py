# -*- coding: utf-8 -*-

# Copyright (C) 2009 by Barabash Maxim
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
#type = Export
#tk_file_type = ("HPGL Plotter file", '.plt')
#extensions = '.plt'
format_name = 'PLT'
#unload = 1
###End

__version__='0.1'


from app import CreatePath, PolyBezier
from app import Bezier, EmptyPattern, Point, Polar, Trafo

from math import pi, cos, sin

degrees = pi / 180.0

plt_options={
				'max_steps_across':'',
				'max_steps_down':'',
				'per_inch':'1016',
				'first_command':'IN',
				'final_command':'PU',
				'move_command':'PU',
				'draw_command':'PD',
				'XY_separator':',',
				'coordinate_separator':',',
				'command_terminator':';',
				'page_feed_command':'',
				'page_terminator_command':'',
				'name': 'Generic Cutter HPGL',
				'output': ''
			}
			

command={
			'rotation':'no',
			'mirror':'no',
			'remove_empty_lines':'no',
			'origin':'no'
}


########### PLS

# Fault Tolerance for flattening Beziers.
# If you find the curves not smooth enough, lower this value.
EPS=0.5

def rndtoint(num):
	return int(round(num))

def cr(P1, P2):
	return P1.x * P2.y - P1.y * P2.x

def FlattenPath(P0, P1, P2, P3):

	P4=(P0 + P1) / 2
	P5=(P1 + P2) / 2
	P6=(P2 + P3) / 2
	P7=(P4 + P5) / 2
	P8=(P5 + P6) / 2
	P9=(P7 + P8) / 2

	B=P3 - P0
	S=P9 - P0
	C1=P1 - P0
	C2=P2 - P3

	# I couldn't find an example of a flattening algorithm so I came up
	# with the following criteria for deciding to stop the approximation
	# or to continue.

	# if either control vector is larger than the base vector continue
	if abs(C1) > abs(B) or abs(C2) > abs(B):
		return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)

	# otherwise if the base is smaller than half the fault tolerance stop.
	elif abs(B) < EPS / 2:
		return (P9, P3)
	else:

		# if neither of the above applies, check for the following conditions.
		# if one of them is true continue the approximation otherwise stop
		#
		# The first constrol vector goes too far before the base
		# The seconde control vector goes too far behind the base
		# Both control vectors lie on either side of the base.
		# The midpoint is too far from base.

		N=B.normalized()
		if ((C1 * N) < -EPS or (C2 * N) > EPS or cr(C1,B)*cr(C2,B) < 0
			or abs(cr(N,S)) > EPS):
			return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)
		else:
			return (P9, P3)


class PLTSaver:

	def __init__(self, file, pathname, options=None):
		self.file=file
		self.pathname=pathname
		self.options={}
		self.options.update(plt_options)
		self.options.update(command)
		self.options.update(options)


	def write_headers(self):
		self.file.write(self.options['first_command']+self.options['command_terminator'])

	def write_terminator(self):
		self.file.write(self.options['final_command']+self.options['command_terminator'])

	def putpolyrec(self, seq):
		self.file.write(self.options['move_command']+str(seq[0])+','+str(seq[1])+self.options['command_terminator'])
		l=len(seq)
		i=2
		while i < l:
			self.file.write(self.options['draw_command']+str(seq[i])+','+str(seq[i+1])+self.options['command_terminator'])
			i=2 + i

	def PathToSeq(self, Path):
		parlst=()
		p0=Point(0,0)
		for i in range(Path.len):
			type, control, p, cont=Path.Segment(i)
			if type==Bezier:
				p1, p2=control
				tmplst=FlattenPath(p0, p1, p2, p)
				for tp in tmplst:
					parlst=parlst + tuple(self.trafo(tp))
			else:
				parlst=parlst + tuple(self.trafo(p))
			p0=p
		return parlst

	def PolyBezier(self, Paths, Properties):
		line_pattern=Properties.line_pattern
		path=Paths[0]
		if line_pattern is EmptyPattern and self.options['remove_empty_lines']=='yes':
			pass
		else:
			for path in Paths:
				lst=self.PathToSeq(path)
				self.putpolyrec(map(rndtoint , lst))

	def close(self):
		self.file.close()

	def SaveObjects(self, Objects):
		for object in Objects:
			if object.is_Compound:
				self.SaveObjects(object.GetObjects())
			elif object.is_Bezier or object.is_Rectangle or object.is_Ellipse:
				self.PolyBezier(object.Paths(), object.Properties())
			elif object.is_SimpleText:
				obj=object.AsBezier()
				self.PolyBezier(obj.Paths(), obj.Properties())

	def SaveLayers(self, Layers):
		for layer in Layers:
			if not layer.is_SpecialLayer and layer.Printable():
				self.SaveObjects(layer.GetObjects())

	def SaveDocument(self, doc):
		left, bottom, right, top=doc.PageRect()
		inch=int(self.options['per_inch'])
		sc=inch / 72.0
		
		self.trafo=Trafo(sc, 0, 0, sc, 0, bottom*sc)
		self.Scale=sc
		self.inch=inch
		self.extend=map(rndtoint, tuple(self.trafo(left,bottom))
									+ tuple(self.trafo(right,top)))

		# Header
		self.write_headers()
		self.SaveLayers(doc.Layers())
		self.write_terminator()
		#end

def save(document, file, filename, options={}):
	saver=PLTSaver(file, filename, options)
	saver.SaveDocument(document)
	saver.close()
	
######## END PLS
