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
#type=Import
#class_name='PLTLoader'
#rx_magic='^IN|^PA|^PU|^PD|^PR|^PS|^\\x20?\\x1B\\x2E|^\\x20?\\x03\\x3b'
#tk_file_type=('PLT - HPGL Plotter file', ('.plt', '.hgl'))
#format_name='PLT'
#unload=1
#standard_messages=1
###End

#
#       Import Filter for HPGL Plotter files
#



import sys, os, string

from types import StringType, TupleType
from app import _, CreatePath, Style, SolidPattern, StandardColors

from app.events.warn import INTERNAL, pdebug, warn_tb
from app.io.load import GenericLoader, SketchLoadError
from app.conf.const import ArcArc, JoinRound, CapRound
from math import sqrt, atan2, cos, sin, pi, hypot
import app

plu=1016.0/72.0
def_width_pen = 0.85 # 0.3 mm
degrees = pi / 180.0

colors = {
		'0': StandardColors.white,
		'1': StandardColors.black,
		'2': StandardColors.blue,
		'3': StandardColors.red,
		'4': StandardColors.green,
		'5': StandardColors.magenta,
		'6': StandardColors.yellow,
		'7': StandardColors.cyan,
		'8': StandardColors.darkgray,
		}

class PLTLoader(GenericLoader):

	functions={		"IN": 'initialize',
					"SP": 'select_pen',
					"PD": 'pen_down',
					"PU": 'pen_up',
					"PA": 'plot_absolute',
					"PR": 'plot_relative',
					"PW": 'pen_sizes',
					#"PT": 'pen_metric', 
					#"PL": 'pen_plu',
					"LT": 'linetype',
					"AA": 'arc_absolute',
					"AR": 'arc_relative',
					"CI": 'circle_plot',
					}

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file=file
		self.initialize()

	def get_position(self, x, y, absolute = None):
		if absolute is None:
			absolute = self.absolute
		
		if x == '' is not None:
			x = self.cur_x
		else:
			x = float(x) / plu
			if absolute == 0:
				x += self.cur_x
			
		if y == '' is not None:
			y = self.cur_y
		else:
			y = float(y) / plu
			if absolute == 0:
				y += self.cur_y
		
		return x,y

	def bezier(self):
		if self.path.len > 1:
			if self.path.Node(0) == self.path.Node(-1):
				self.path.load_close(1)
			self.prop_stack.AddStyle(self.curstyle.Duplicate())
			GenericLoader.bezier(self, paths=(self.path,))
		self.path=CreatePath()


	def arc_absolute(self, x, y, qc, qd = 5):
		x, y = self.get_position(x, y, 1)
		self.arc(x, y, qc, qd)

	def arc_relative(self, x, y, qc, qd = 5):
		x, y = self.get_position(x, y, 0)
		self.arc(x, y, qc, qd)
	
	def arc(self, x, y, qc, qd = 5):
		qc = float(qc) * degrees
		x2 = self.cur_x - x
		y2 = self.cur_y - y
		
		r = hypot(x2, y2)
		
		if qc < 0:
			end_angle = atan2(y2, x2) 
			angle = start_angle = end_angle + qc
		else:
			start_angle = atan2(y2, x2)
			angle = end_angle = start_angle + qc
			
		self.cur_x = (x + r * cos(angle))
		self.cur_y = (y + r * sin(angle))
		if self.draw==1:
			self.pen_up()
			self.pen_down()
			self.prop_stack.AddStyle(self.curstyle.Duplicate())
			apply(self.ellipse, (r, 0, 0, r, x, y, start_angle, end_angle, ArcArc))


	def circle_plot(self, r, qd = 5):
		x, y = self.cur_x, self.cur_y
		r = float(r) / plu
		#self.bezier()
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		apply(self.ellipse, (r, 0, 0, r, x, y))


	def move(self, x,y):
		if self.draw==1:
			self.path.AppendLine(x, y)
		else:
			self.bezier()
			self.path.AppendLine(x, y)
		self.cur_x=x
		self.cur_y=y

	def pen_down(self,x='',y=''):
		self.draw=1
		if x !='' is not None:
			x,y=self.get_position(x,y)
			self.move(x,y)

	def pen_up(self,x='',y=''):
		self.draw=0
		x,y=self.get_position(x,y)
		self.move(x,y)

	def plot_absolute(self,x='',y=''):
		self.absolute=1
		if x !='' is not None:
			x,y=self.get_position(x,y)
			self.move(x,y)

	def plot_relative(self,x='',y=''):
		self.absolute=0
		if x !='' is not None:
			x,y=self.get_position(x,y)
			self.move(x,y)

	def initialize(self):
		self.curstyle=Style()
		self.curstyle.line_join = JoinRound
		self.curstyle.line_cap = CapRound
		self.cur_x=0.0
		self.cur_y=0.0
		self.draw=0
		self.absolute=1
		self.path=CreatePath()
		self.curpen = None
		self.penwidth = {}
		self.select_pen()

	def select_pen(self, pen = '1'):
		if not pen in colors:
			pen = '1'
		if not pen in self.penwidth:
			width = def_width_pen
		else:
			width = self.penwidth[pen]
		if not self.curpen == pen:
			if self.draw == 1:
				self.pen_up()
				self.pen_down()
			patern = SolidPattern(colors[pen])
			self.curstyle.line_pattern = patern
			self.curstyle.line_width = width
			self.curpen = pen

	def linetype(self, n = '0', p = '10', q = ''):
		n = abs(int(n))
		#p = float(p)
		p = 20
		dash = [[],
				[0, p],
				[p*0.5, p*0.5],
				[p*0.7, p*0.3],
				[p*0.8, p*0.1, p*0.1, 0],
				[p*0.7, p*0.1, p*0.1, p*0.1],
				[p*0.5, p*0.1, p*0.1, p*0.1, p*0.2, 0],
				[p*0.7, p*0.1, 0, p*0.1, 0, p*0.1],
				[p*0.5, p*0.1, 0, p*0.1, p*0.1, p*0.1, p*0.1, 0],
				[p,p],
				[p,p],
				[p,p],
				]
		self.curstyle.line_dashes = dash[n]
		

	def pen_sizes(self, width, pen = None):
		if pen is None:
			pen = self.curpen
		self.penwidth[pen] = float(width) * 72 / 25.4
		self.curpen = None
		self.select_pen(pen)


	def get_compiled(self):
		funclist={}
		for char, name in self.functions.items():
			method=getattr(self, name)
			argc=method.im_func.func_code.co_argcount - 1
			funclist[char]=(method, argc)
		return funclist

	def interpret(self):
		import shlex
		
		def is_number(a):
			try:
				i=float(a)
			except ValueError:
				return 0
			return 1
		
		file = self.file
		if type(file) == StringType:
			file = open(file, 'r')
		file.seek(0)
		readline = file.readline
		fileinfo=os.stat(self.filename)
		totalsize=fileinfo[6]
		
		lexer=shlex.shlex(file)
		lexer.debug=0
		lexer.wordchars=lexer.wordchars + ".-+"
		lexer.whitespace=lexer.whitespace + ';,'
		
		keyword=None
		args=[]
		
		parsed=0
		parsed_interval=totalsize/99+1
		while 1:
			
			interval_count=file.tell()/parsed_interval
			if interval_count > parsed:
				parsed+=10 # 10% progress
				app.updateInfo(inf2 = '%u' % parsed + _('% of file is parsed...'), inf3 = parsed)
			
			token=lexer.get_token()
			if not token:
				# run last command
				self.run(keyword,args)
				# pun up
				self.run('PU',[])
				# END INTERPRETATION
				app.updateInfo(inf2=_('Parsing is finished'),inf3=100)
				break
			
			if keyword and is_number(token):
				args.append(token)
			else:
				self.run(keyword,args)
				keyword=token[0:2]
				args=[]
				if token[2:]:
					lexer.push_token(token[2:])

	def run(self,keyword,args):
		if keyword is None:
			return
		unknown_operator=(None, None)
		funclist=self.funclist
		if keyword is not None:
			method, argc=funclist.get(keyword, unknown_operator)
			if method is not None:
				#print method.__name__, args
				try:
					if len(args):
						i=0
						while i<len(args):
							apply(method, args[i:argc+i])
							i+=argc
					else:
						method()
				except:
					warn_tb(INTERNAL, 'PLTLoader: error')



	def Load(self):
		self.funclist=self.get_compiled()
		self.document()
		self.layer(name=_("PLT_objects"))
		self.interpret()
		self.end_all()
		self.object.load_Completed()
		return self.object

