# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in UniConvertor root directory.


import os, sys, Tkinter, Ttk, Tkconstants, tkFileDialog, tkMessageBox
from Tkinter import StringVar, IntVar
from Tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y
from Ttk import TFrame, TButton, TLabel, TLabelframe, TCombobox, TEntry

from progressbar_dlg import ConvProgress


class UniConvw:
	
	file=None
	initialized=False
	stand_alone=False
	icon=None
	window=None
	
	def __init__(self, icon, options, filetypes, file=None):
		self.icon=icon
		self.options=options
		exit_message='Cancel'
		if not file is None:
			if os.path.isfile(file): self.file=file
		self.filetypes=filetypes
		
		self.window=Tkinter.Tk()
		self.window.title('UniConvertor')
#		self.window.tk.call('wm', 'iconbitmap', self.window, self.icon)
		
		self.win_panel=TFrame(self.window, borderwidth=10)
		self.win_panel.pack(side=TOP, fill=Tkinter.BOTH, expand=1)
		
		#File selection
		file_panel=TFrame(self.win_panel)
		
		label=TLabel(file_panel, text='File: ')
		label.pack(side = LEFT, padx=5)
		
		self.file_button=TButton(file_panel, text='...', command=self.openFile, width=0)
		self.file_button.pack(side=RIGHT,padx=1)
		
		self.file_reference = StringVar(self.window)
		self.file_reference.set('<None>')
		
		self.file_entry=TEntry(file_panel, text='<None>', state='readonly', textvariable=self.file_reference)
		self.file_entry.pack(side=RIGHT, fill=X, expand=1)
		
		if self.file is None:
			file_panel.pack(side = TOP, fill=X)
			self.stand_alone=True				
		
		#Formats
		label=TLabel(self.win_panel, text=' Convert to: ')
		label.pack(side = TOP, padx=5)
		
		format_frame=TLabelframe(self.win_panel, labelwidget=label, borderwidth=2)
		format_frame.pack(side = TOP, fill=Tkinter.X, expand=1, pady=2)
		
		formats=[]
		for item in self.options:
			formats.append(item[0])
			
		self.format_reference = StringVar(self.window)
		self.format_reference.set(self.options[1][0])
		
		self.format_combo=TCombobox(format_frame, values=formats, width=40, state='readonly', textvariable=self.format_reference)
		self.format_combo.pack(expand=1, padx=10, pady=10)		
		
		#Buttons
		button_panel=TFrame(self.win_panel)
		button_panel.pack(side=BOTTOM, fill=X, expand=1, pady=5)
		
		self.but_close=TButton(button_panel, text='Close', width=10, command=self.close)
		self.but_close.pack(side=RIGHT)
		
		self.but_convert=TButton(button_panel, text='Convert', width=10, command=self.convert)
		self.but_convert.pack(side=RIGHT, padx=10)
		if self.file is None: self.but_convert['state']='disabled'
			
		
		label=TLabel(button_panel, text='http://sk1project.org', state='disabled')
		label.pack(side = LEFT, anchor='sw')
		
		self.window.resizable(False,False)
		self.set_position()
		
	def convert(self):
		self.progress_dlg=ConvProgress(self.window, self.callback, self.icon)
		self.progress_dlg.run_dialog()
		if not self.stand_alone:
			self.close()
			
	def init_convertor(self):
		if not self.initialized:
			from uniconvertor import init_uniconv
			init_uniconv()
			self.initialized=True
			
	def get_format(self):
		format=self.format_reference.get()
		for item in self.options:
			if item[0]==format: format=item[1]
		return format
			
	def callback(self):
		self.init_convertor()
		self.send_msgs("Start", "UniConvertor is initialized",2)
		
		from app.io import load
		from sk1libs import filters
		import app, time
		
		app.receiver=self.progress_dlg.msg_receiver

		app.init_lib()
		
		self.send_msgs("Start", "Loading plugin configuration",3)
		filters.load_plugin_configuration()
		
		input_file=self.file
		output_file=self.file+'.'+ self.get_format()
		
		doc=None
		
		try:
			self.send_msgs("Start", "Parsing document file",5)
			doc = load.load_drawing(input_file)
			extension = os.path.splitext(output_file)[1]
			
			self.send_msgs("", "Parsing is completed",100)
			
			fileformat = filters.guess_export_plugin(extension)
			
			self.send_msgs("", "Saving translated file",50)
			if fileformat:				
				saver = filters.find_export_plugin(fileformat)
				saver(doc, output_file)
				self.send_msgs("", "Translated file is saved",100)
			else:
				self.msg_dialog('\nERROR: unrecognized extension %s\n' % extension)
		except Exception, value:
			self.msg_dialog("\nAn error occurred: " + str(value))
		finally:
			if not doc is None:
				doc.Destroy()
			return
		
	def msg_dialog(self, msg):
		self.progress_dlg.close()
		tkMessageBox.showwarning("UniConvertor",msg)

	def openFile(self):
		opt = {}
		ft=[]
		
		all_supported='All supported files - *.ai *.cdr *.svg *.wmf etc.'
		all_sup_ext=()
		for item in self.filetypes: all_sup_ext+=(item[1],)
		ft+=[(all_supported,all_sup_ext)]
		ft+=self.filetypes+[('All files - *.*', '.*')]
		
		opt['filetypes'] = ft
		opt['parent'] = self.window
		opt['title'] = 'Select a file for translation...'
		result=tkFileDialog.askopenfilename(**opt)
		if result and os.path.isfile(result):
			self.file_reference.set(result)
			self.file=result
			self.but_convert['state']='normal'
	
	def set_position(self):
		self.window.update()
		width = self.win_panel.winfo_width()
		height = self.win_panel.winfo_height()
		posx = self.window.winfo_screenwidth()/2 - width/2
		posy = self.window.winfo_screenheight()/2 - height / 2
		self.window.geometry('%dx%d%+d%+d' % (width, height, posx, posy))
		
	def send_msgs(self,msg1,msg2,val):
		self.progress_dlg.msg_receiver(msg1,msg2,val,'indeterminate')
	
	def main(self):
		self.window.mainloop()	
		
	def close(self):
		sys.exit(0)
		
	def stub(self):
		pass
	