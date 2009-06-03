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
#rx_magic='^IN|^PA|^PU|^PD|^PR|^PS'
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
from app import _, CreatePath, Style

from app.events.warn import INTERNAL, pdebug, warn_tb
from app.io.load import GenericLoader, SketchLoadError
import app

plu=1016.0/72.0


class PLTLoader(GenericLoader):

	functions={"PD": 'pen_down',
					"PU": 'pen_up',
					"PA": 'plot_absolute',
					"PR": 'plot_relative',
					"IN": 'initialize'
					#"SP": 'select_pen',
					#"LT": 'linetype',
					#"PT": 'pen_metric', 
					#"PL": 'pen_plu', 
					#"SP": 'set_pen'
					}

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file=file
		self.initialize()

	def get_position(self,x,y):
		if x=='' is not None:
			x=self.cur_x
		else:
			x=float(x)/plu
		if y=='' is not None:
			y=self.cur_y
		else:
			y=float(y)/plu
		if self.absolute==0:
			x=x+self.cur_x
			y=y+self.cur_y
		return x,y

	def bezier(self):
		if self.path.len > 1:
			GenericLoader.bezier(self, paths=(self.path,))
		self.path=CreatePath()

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
		if self.draw==1:
			self.bezier()
		self.draw=0
		if x !='' is not None:
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
		self.cur_x=0.0
		self.cur_y=0.0
		self.draw=0
		self.absolute=1
		self.path=CreatePath()


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
				app.updateInfo(inf2='%u'%parsed+'% of file is parsed...',inf3=parsed)
			
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

