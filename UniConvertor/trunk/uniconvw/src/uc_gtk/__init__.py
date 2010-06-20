# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in UniConvertor root directory.

import pygtk, os
pygtk.require('2.0')
import gtk

from progressbar_dlg import ConvProgress

class UniConvw:
	
	file=None
	initialized=False
	stand_alone=False
	icon=None
	
	def __init__(self, icon, options, filetypes, file=None):
		self.icon=icon
		self.options=options
		exit_message=' '+'Cancel'+' '
		if not file is None:
			if os.path.isfile(file): self.file=file
		self.filetypes=filetypes		
		
		#Window creation
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("UniConvertor")
		self.window.set_icon_from_file(icon)
		self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		self.window.set_resizable(False)
		
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)	
		self.window.set_border_width(10)
		
		self.win_box = gtk.VBox(False, 5)
		self.window.add(self.win_box)
		
		self.buttonConvert = gtk.Button(" Convert ")
		
		#Optional file selection
		if self.file is None:
			self.stand_alone=True
			exit_message='  '+'Exit'+'  '
			self.buttonConvert.set_sensitive(False)
			
			self.file_hbox = gtk.HBox(False, 5)
			self.win_box.add(self.file_hbox)
			
			
			self.dialog = gtk.FileChooserDialog("Select a file for translation...",
						None,
						gtk.FILE_CHOOSER_ACTION_OPEN,
						(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
							gtk.STOCK_OPEN, gtk.RESPONSE_OK))
			self.dialog.set_default_response(gtk.RESPONSE_OK)
			
			for item in filetypes:
				filter = gtk.FileFilter()
				filter.set_name(item[0])
				filter.add_pattern(item[1])
				self.dialog.add_filter(filter)
			
			self.filechooserbutton = gtk.FileChooserButton(self.dialog)
			self.filechooserbutton.set_current_folder('/home/igor')
			self.filechooserbutton.connect("file-set", self.file_changed)
			self.file_hbox.pack_end(self.filechooserbutton, expand=True, fill=True, padding=0)
			
			self.file_label=gtk.Label("File:")
			self.file_hbox.pack_end(self.file_label, expand=False, fill=False, padding=0)
			
			self.file_label.show()
			self.file_hbox.show()
			self.filechooserbutton.show()
		
		#ComboBox creation
		self.frame=gtk.Frame(" Convert to: ")
		self.win_box.add(self.frame)
		
		self.cb_vbox = gtk.VBox(False, 5)
		self.frame.add(self.cb_vbox)
		
		self.cb_hbox = gtk.HBox(False, 5)
		self.cb_vbox.pack_start(self.cb_hbox, expand=False, fill=True, padding=10)
		
		self.combo=gtk.combo_box_new_text()
		for item in self.options:
			self.combo.append_text(item[0])
		self.combo.set_active(1)
		self.cb_hbox.pack_start(self.combo, expand=False, fill=True, padding=10)
		
		#Buttons
		self.buttons_box = gtk.HBox(False, 10)
		self.win_box.add(self.buttons_box)
		
		self.buttonExit = gtk.Button(exit_message)
		self.buttonExit.connect_object("clicked", gtk.Widget.destroy, self.window)
		self.buttons_box.pack_end(self.buttonExit, expand=False, fill=False, padding=0)

		
		self.buttonConvert.connect("clicked", self.convert)
		self.buttons_box.pack_end(self.buttonConvert, expand=False, fill=False, padding=0)
		
		#App label
		self.label_box = gtk.VBox(False, 0)
		self.buttons_box.pack_start(self.label_box, expand=False, fill=True, padding=0)
		
		self.link=gtk.Label("http://sk1project.org")
		self.link.set_sensitive(False)
		self.label_box.pack_end(self.link, expand=False, fill=False, padding=0)		
		
			

		self.link.show()
		self.label_box.show()
		self.combo.show()
		self.buttonExit.show()
		self.buttonConvert.show()
		self.buttons_box.show()
		self.cb_hbox.show()
		self.cb_vbox.show()
		self.frame.show()
		self.win_box.show()
		self.window.show()

		
	def init_convertor(self):
		if not self.initialized:
			from uniconvertor import init_uniconv
			init_uniconv()
			self.initialized=True	
		
	def file_changed(self, *args):
		file=self.dialog.get_filename()
		if os.path.isfile(file):
			self.file=file
			self.buttonConvert.set_sensitive(True)
		
	def convert(self, *args):
		self.progress_dlg=ConvProgress(self.callback, self.icon)
		self.progress_dlg.run_dialog("Start", "UniConvertor initialization")
		while gtk.events_pending():
			gtk.main_iteration()
		self.progress_dlg.window.destroy()
		if not self.stand_alone:
			self.destroy()
		
	def callback(self):
		self.init_convertor()
		while gtk.events_pending():
			gtk.main_iteration()
		self.progress_dlg.msg_receiver("Start", "UniConvertor is initialized",0.02)
		
		from app.io import load
		from sk1libs import filters
		import app
		
		app.receiver=self.progress_dlg.msg_receiver

		app.init_lib()
		
		self.progress_dlg.msg_receiver("Start", "Loading plugin configuration",0.03)
		filters.load_plugin_configuration()
		
		input_file=self.file
		output_file=self.file+'.'+self.options[self.combo.get_active()][1]
		
		doc=None
		
		try:
			while gtk.events_pending():
				gtk.main_iteration()
			self.progress_dlg.msg_receiver("Start", "Parsing document file",0.05)
			doc = load.load_drawing(input_file)
			extension = os.path.splitext(output_file)[1]
			
			while gtk.events_pending():
				gtk.main_iteration()				
			self.progress_dlg.msg_receiver("", "Parsing is completed",1.0)
			
			fileformat = filters.guess_export_plugin(extension)
			
			while gtk.events_pending():
				gtk.main_iteration()
				
			self.progress_dlg.msg_receiver("", "Saving translated file",0.5)
			if fileformat:
				
				saver = filters.find_export_plugin(fileformat)
				saver(doc, output_file)
				while gtk.events_pending():
					gtk.main_iteration()				
				self.progress_dlg.msg_receiver("", "Translated file is saved",1.0)
			else:
				self.msg_dialog('\nERROR: unrecognized extension %s\n' % extension, gtk.MESSAGE_WARNING)
		except Exception, value:
			self.msg_dialog("\nAn error occurred: " + str(value), gtk.MESSAGE_WARNING)
		finally:
			if not doc is None:
				doc.Destroy()
			return
				
	def msg_dialog(self,text, dlg_type=gtk.MESSAGE_WARNING):
		while gtk.events_pending():
			gtk.main_iteration()
		self.progress_dlg.window.destroy()
		dlg=gtk.MessageDialog(self.window, 
						flags=gtk.DIALOG_MODAL, 
						type=dlg_type, 
						buttons=gtk.BUTTONS_OK, 
						message_format=text)
		dlg.set_title('UniConvertor')
		dlg.connect("response", lambda d, r: d.destroy())
		dlg.run()

	def delete_event(self, widget, event, data=None):
		return False

	def destroy(self, *args):
		gtk.main_quit()
	
	def main(self):
		gtk.main()

