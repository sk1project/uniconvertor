# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in UniConvertor root directory.


import Tkinter, Ttk, Tkconstants, tkFileDialog
from Tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y
from Ttk import TFrame, TButton, TLabel, TLabelframe, TCombobox, TEntry


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
		
		win_panel=TFrame(self.window, borderwidth=10)
		win_panel.pack(side=TOP, fill=Tkinter.BOTH, expand=1)
		
		#File selection
		file_panel=TFrame(win_panel)
		file_panel.pack(side = TOP, fill=X)
		
		label=TLabel(file_panel, text='File: ')
		label.pack(side = LEFT, padx=5)
		
		self.file_button=TButton(file_panel, text='...', command=self.openFile, width=0)
		self.file_button.pack(side=RIGHT,padx=1)
		
		self.file_entry=TEntry(file_panel, text='<None>', state='readonly')
		self.file_entry.pack(side=RIGHT, fill=X, expand=1)
				
		
		#Formats
		label=TLabel(win_panel, text=' Convert to: ')
		label.pack(side = TOP, padx=5)
		
		format_frame=TLabelframe(win_panel, labelwidget=label, borderwidth=2)
		format_frame.pack(side = TOP, fill=Tkinter.X, expand=1, pady=2)
		
		self.format_combo=TCombobox(format_frame, values=('1','2','3'), width=40, state='readonly')
		self.format_combo.pack(expand=1, padx=10, pady=10)		
		
		#Buttons
		button_panel=TFrame(win_panel)
		button_panel.pack(side=BOTTOM, fill=X, expand=1, pady=5)
		
		self.but_close=TButton(button_panel, text='Close', width=10, command=self.stub)
		self.but_close.pack(side=RIGHT)
		
		self.but_convert=TButton(button_panel, text='Convert', width=10, command=self.stub)
		self.but_convert.pack(side=RIGHT, padx=10)
		
		label=TLabel(button_panel, text='http://sk1project.org', state='disabled')
		label.pack(side = LEFT, anchor='sw')

	def openFile(self):
		self.file_opt = options = {}
		options['defaultextension'] = '' # couldn't figure out how this works
		options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
		options['initialdir'] = 'C:\\'
		options['initialfile'] = 'myfile.txt'
		options['parent'] = root
		options['title'] = 'This is a title'
		return tkFileDialog.askopenfile(mode='r')
	
	def main(self):
		self.window.mainloop()	
		
	def stub(self):
		pass