# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in UniConvertor root directory.


import Tkinter, Ttk
from Tkinter import StringVar, IntVar
from Tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y
from Ttk import TFrame, TLabel

	
class ConvProgress:
		
		window=None
		parent=None
		callback=None
		icon=None
		
		def __init__ (self, parent, callback, icon):
			self.parent=parent
			self.callback=callback
			self.icon=icon
			
			self.window=Tkinter.Toplevel(parent)
			self.window.withdraw()
			self.window.title('Translation progress')
			self.window.transient(parent)
			self.window.group(parent)
			self.window.protocol('WM_DELETE_WINDOW', self.stub)
			self.window.tk.call('wm', 'iconbitmap', self.window, self.icon)
			
			self.win_panel=TFrame(self.window, borderwidth=10)
			self.win_panel.pack(side=TOP,fill=BOTH)
			
			top_panel=TFrame(self.win_panel)
			top_panel.pack(side=TOP,fill=X, pady=5)
			self.label1_reference = StringVar(self.window)
			self.label1=TLabel(top_panel, textvariable=self.label1_reference)
			self.label1.pack(side=LEFT)
			self.label1_reference.set('Start...')
			
			mid_panel=TFrame(self.win_panel)
			mid_panel.pack(side=TOP,fill=X)
			self.label2_reference = StringVar(self.window)
			self.label2=TLabel(mid_panel, textvariable=self.label2_reference)
			self.label2.pack(side=LEFT)	
			self.label2_reference.set('')					
			
			self.progress_reference = IntVar(self.window)
			self.progress_bar=Ttk.TProgressbar(self.win_panel, orient = 'horizontal',
										length = 450, variable=self.progress_reference)
			self.progress_bar.pack(side = TOP, anchor='w')
			self.progress_reference.set(10)		
			
			self.window.resizable(False,False)
			self.set_position()
			self.window.deiconify()

		def msg_receiver(self, msg1, msg2, val=0, mode='determinate'):
			self.label1_reference.set(msg1)
			self.label2_reference.set(msg2)
			self.progress_reference.set(val)
			self.window.update()		
		
		def run_dialog(self, *args):
			self.window.grab_set()
			self.callback()
			self.close()	
			
		def set_position(self):
			self.window.update()
			width = self.win_panel.winfo_reqwidth()
			height = self.win_panel.winfo_reqheight()
			posx = self.window.winfo_screenwidth()/2 - width/2
			posy = self.window.winfo_screenheight()/2 - height / 2
			self.window.geometry('%dx%d%+d%+d' % (width, height, posx, posy))
		
		def close(self):
			self.parent.grab_set()
			self.window.destroy()
		
		def stub(self):
			pass
			