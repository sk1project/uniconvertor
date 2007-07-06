# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999 by Bernhard Herzog
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

from app.events.warn import warn_tb, USER
import app

from wrapper import DocumentWrapper


class Context:

	def __init__(self):
		self.application = app.main.application
		self.main_window = self.application.main_window
		self.document = self.main_window.document

class Script:

	def __init__(self, name, title, function, args = (), kwargs = None,
					sensitive = None):
		self.name = name
		self.title = title
		self.function = function
		self.args = args
		self.kwargs = kwargs
		self.sensitive = sensitive

	def Title(self):
		return self.title

	def execute(self, context, *args, **kw):
		document = context.main_window.document
		apply(document.BeginTransaction, args, kw)
		try:
			try:
				kw = self.kwargs
				if kw is None:
					kw = {}
				apply(self.function, (context,) + self.args, kw)
			except:
				warn_tb(USER, 'Error in user script "%s"', self.name)
				document.AbortTransaction()
		finally:
			document.EndTransaction()


class SafeScript(Script):

	def Execute(self):
		context = Context()
		context.document = DocumentWrapper(context.document)
		self.execute(context, self.Title())


#class SelectionScript(Script):
#
#    def Execute(self):
#        self.execute(Context(), clear_selection_rect = 0)

class AdvancedScript(Script):

	def Execute(self):
		self.execute(Context(), self.Title())
