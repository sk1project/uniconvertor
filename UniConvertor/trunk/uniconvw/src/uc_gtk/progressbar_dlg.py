# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in UniConvertor root directory.

import pygtk, os
pygtk.require('2.0')
import gtk

class ConvProgress:
	
	callback=None
	msg1=''
	msg2=''
	val=0
	
	def __init__(self, callback,icon):
		self.callback=callback
		self.icon=icon
		
	def run_dialog(self, msg1, msg2, val=0.0):
		self.show()
		while gtk.events_pending():
			gtk.main_iteration()
		self.msg_receiver(msg1,msg2,val)
		self.callback()
		
	def msg_receiver(self, msg1, msg2, val=0.0):
		self.msg1=msg1
		self.msg2=msg2
		self.val=val
		self.label1.set_label(self.msg1)
		self.label2.set_label(self.msg2)
		self.progress.set_fraction(self.val/100.0)
		self.progress.text=str(int(self.val))+"%"
		while gtk.events_pending():
			gtk.main_iteration()
		
	def hide(self):	
		self.window.hide()
		self.msg_receiver('','',0)
		
	def show(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("Translation progress")
		self.window.set_icon_from_file(self.icon)
		self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		self.window.set_resizable(False)
		
		self.window.set_border_width(10)
		
		self.win_box = gtk.VBox(False, 5)
		self.window.add(self.win_box)
		
		#App label1
		self.label_box1 = gtk.HBox(False, 0)
		self.win_box.pack_start(self.label_box1, expand=False, fill=True, padding=0)
		
		self.label1=gtk.Label(self.msg1)
		self.label_box1.pack_start(self.label1, expand=False, fill=False, padding=0)
		
		#App label2
		self.label_box2 = gtk.HBox(False, 0)
		self.win_box.pack_start(self.label_box2, expand=False, fill=True, padding=0)
		
		self.label2=gtk.Label(self.msg2)
		self.label_box2.pack_start(self.label2, expand=False, fill=False, padding=0)
		
		#Progress
		self.progress_box = gtk.HBox(False, 0)
		self.win_box.pack_start(self.progress_box, expand=False, fill=True, padding=0)
		
		self.progress=gtk.ProgressBar()
		self.progress_box.pack_start(self.progress, expand=True, fill=True, padding=0)		
		self.progress.set_size_request(400, -1)
		
		self.progress.show()
		self.progress_box.show()
		self.label2.show()
		self.label1.show()
		self.label_box2.show()
		self.label_box1.show()
		self.win_box.show()
		self.window.show()


