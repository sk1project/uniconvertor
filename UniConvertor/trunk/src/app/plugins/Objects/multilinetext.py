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


###Sketch Config
#type = PluginCompound
#class_name = 'MultilineText'
#menu_text = 'Multiline Text'
#standard_messages = 1
#custom_dialog = 'MultilineTextDlg'
###End

(''"Multiline Text")

import Tkinter
from Tkconstants import *
from Tkinter import StringVar, Entry, Label, Button, Frame, Text, END, \
	BOTH, LEFT, TOP, X, W, GROOVE, Frame, Label, StringVar, Radiobutton

import os
from string import split, rstrip
from types import StringType
from math import ceil


from app.conf import const
from app import Scale, TrafoPlugin, SimpleText, Translation, Identity, \
	GetFont, StandardColors, SolidPattern, UndoAfter, _
from app.UI.sketchdlg import SketchPanel

from Lib.multilinetext.TextEditor import TextEditor, FONTS, Style, \
		raw2styling, styling2raw
from Lib.multilinetext.chunker import Chunker



class MultilineText(TrafoPlugin):

	class_name = 'MultilineText'
	has_edit_mode       = 0
	is_Text             = 0
	is_SimpleText       = 0
	is_curve            = 0
	is_clip             = 0
	has_font            = 0
	has_fill            = 0
	has_line            = 0
	is_Group            = 1

	Ungroup = TrafoPlugin.GetObjects


	def __init__(self, text = '', styling = [],
					trafo = None, loading = 0, duplicate = None):
		self.objects = []
		TrafoPlugin.__init__(self, trafo = trafo, duplicate = duplicate)

		if duplicate is not None:
			self.text = duplicate.text
			self.styling = duplicate.styling[:]
		else:
			self.text = text
			if loading: # XXX a bit ugly 
				raw = styling
				styling = raw2styling(raw)
			self.styling = styling
		if not loading:
			self.recompute()

	def recompute(self):
		chunker = Chunker(rstrip(self.text), self.styling, '\t')

		objects = []
		options = {}
		x = 0
		y = 0
		maxy = 0
		line = []
		while not chunker.eof():
			text, styles =  chunker.get()

			family = styles['family'].options
			color = styles['color'].options
			fill = SolidPattern(getattr(StandardColors, color))
			# XXX should be done in advance


			size = styles['size'].options
			bold = styles['bold'].options
			italic = styles['italic'].options

			if bold and italic:
				attr = 'Bold Italic'
			elif bold:
				attr = 'Bold'
			elif italic:
				attr = 'Italic'
			else:
				attr = 'Roman'

			supersub = styles['supersub'].options
			if len(text)>0:
				height = 1.2*size # XXX is that ok ?
				if maxy<height:
					maxy = height

				if supersub != 'normal':
					if supersub == 'superscript':
						offset = size*0.5
					else:
						offset = -size*0.15
					size = 0.5*size
				else:
					offset = 0
				textObj = SimpleText(Translation(x,offset), text)
				objects.append(textObj)
				line.append(textObj)

				psfont = FONTS.ps(family=family, attr=attr)
				font = GetFont(psfont)

				textObj.SetProperties(font=font, font_size=size, 
					fill_pattern=fill)

				left, bottom, right, top = textObj.coord_rect
				width = right-left

			else:
				width = 0

			reason = chunker.reason()
			if reason == '\n' or chunker.eof():
				if width > 0:
					y = y-maxy
				else:
					y = y-size
				maxy = 0
				x = 0
				for obj in line:
					obj.Transform(self.trafo(Translation(0, y)))
				line = []
			elif reason == '\t':
				x = x+width+size
				#
				# XXX this is very provisional
				x = ceil(x/50.)*50.
			else:
				x = x+width

		# XXX this is a problem: what happens, if the MultilineText onbject
		#           is empty  ??
		#~ if len(objects)>0:
		self.set_objects(objects)

	def SetParameters(self, params):
		return TrafoPlugin.SetParameters(self, params)

	def Transform(self, trafo):
		return self.set_transformation(trafo(self.trafo))

	def Text(self):
		return self.text

	def Styling(self):
		return self.styling

	def SaveToFile(self, file):
		raw = styling2raw(self.styling)
		TrafoPlugin.SaveToFile(self, file, self.text, raw, self.trafo.coeff())

	def AsBezier(self):
		return self.objects[0].AsBezier()

	def Paths(self):
		return self.objects[0].Paths()


class MultilineTextDlg(SketchPanel):

	title = _("Multiline Text")
	class_name = "MultilineTextPanel"
	receivers = SketchPanel.receivers[:]

	def __init__(self, master, main_window, doc):
		SketchPanel.__init__(self, master, main_window, doc,
								name = 'multilinetxtdlg')

	receivers.append((const.SELECTION, 'Update'))
	def Update(self):
		"""
		This method is used as a callback and
		is automatically called when the selection changes
		"""
		# get selection
		selections = self.document.SelectedObjects()
		if len(selections) == 1:
			selected = selections[0]
			if selected.is_Plugin and selected.class_name == 'MultilineText':
				self.set_text(selected.text)
				self.set_styling(selected.styling)
				return
		self.set_text('')
		self.set_styling([])

	def init_from_doc(self):
		"""
		Called whenever the document changes and from __init__
		"""
		self.Update()

	def build_dlg(self):
		top = self.top
		self.text = ''

		text_field = TextEditor(top,
			background = 'white',
			width = 40,
			height = 20)
		text_field.pack(fill = BOTH, expand = 1)

		text_field.button_apply.configure(command=self.apply)
		text_field.warn = self.report_error
		self.text_field = text_field

	def report_error(self, title, message):
		app = self.main_window.application
		app.MessageBox(title = title,
						message = message,
						icon = 'warning')


	def get_text(self):
		tk = self.master.tk
		return tk.utf8_to_latin1(self.text_field.get('1.0', 'end')[:-1])

	def get_styling(self):
		return self.text_field.styling_get('1.0', 'end')

	def set_text(self, text):
		self.text_field.delete('1.0', 'end')
		self.text_field.insert('end', text)

	def set_styling(self, styling):
		if len(styling) == 0:
			self.text_field.style_removeall()
		else:
			self.text_field.styling_apply('1.0', styling)

	def apply(self):
		text = self.get_text()
		styling = self.get_styling()
		doc = self.document
		selections = doc.SelectedObjects()
		if len(selections) == 1:
			selected = selections[0]
			if selected.is_Plugin and selected.class_name =='MultilineText':
				doc.BeginTransaction(_("Set MultilineText Parameters"))
				try:
					try:
						params = {}
						params["text"] = text
						params["styling"] = styling
						doc.AddUndo(selected.SetParameters(params))
					except:
						doc.AbortTransaction()
				finally:
					doc.EndTransaction()
				return
		object = MultilineText(text, styling)
		self.main_window.PlaceObject(object)
