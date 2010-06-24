"""Wrapper functions for Tile widgets

Original Tkinter library is modified for sK1 distribution by
Igor Novikov (C) 2006, 2007, 2008 

This library is covered by GNU Library General Public License.
For more info see COPYRIGHTS file in sK1 root directory.
"""

__version__ = "$Revision: 0.1.0.0 $"

import sys
import _tkinter 
tkinter = _tkinter 
TclError = _tkinter.TclError
from types import *
from Tkconstants import *
import Tkinter


wantobjects = 1

TkVersion = float(_tkinter.TK_VERSION)
TclVersion = float(_tkinter.TCL_VERSION)

READABLE = _tkinter.READABLE
WRITABLE = _tkinter.WRITABLE
EXCEPTION = _tkinter.EXCEPTION

try: _tkinter.createfilehandler
except AttributeError: _tkinter.createfilehandler = None
try: _tkinter.deletefilehandler
except AttributeError: _tkinter.deletefilehandler = None


def _flatten(tuple):
	"""Internal function."""
	res = ()
	for item in tuple:
		if type(item) in (TupleType, ListType):
			res = res + _flatten(item)
		elif item is not None:
			res = res + (item,)
	return res

try: _flatten = _tkinter._flatten
except AttributeError: pass

def _cnfmerge(cnfs):
	"""Internal function."""
	if type(cnfs) is DictionaryType:
		return cnfs
	elif type(cnfs) in (NoneType, StringType):
		return cnfs
	else:
		cnf = {}
		for c in _flatten(cnfs):
			try:
				cnf.update(c)
			except (AttributeError, TypeError), msg:
				print "_cnfmerge: fallback due to:", msg
				for k, v in c.items():
					cnf[k] = v
		return cnf

try: _cnfmerge = _tkinter._cnfmerge
except AttributeError: pass

class TScrollbar(Tkinter.Widget):
	"""Scrollbar widget which displays a slider at a certain position."""
	def __init__(self, master=None, cnf={}, **kw):
		self.scroll_offset = 0.05
		"""Construct a scrollbar widget with the parent MASTER.

		Valid resource names: activebackground, activerelief,
		background, bd, bg, borderwidth, command, cursor,
		elementborderwidth, highlightbackground,
		highlightcolor, highlightthickness, jump, orient,
		relief, repeatdelay, repeatinterval, takefocus,
		troughcolor, width."""
		Tkinter.Widget.__init__(self, master, 'ttk::scrollbar', cnf, kw)
		self.bind("<Button-4>", self.scroll_up)
		self.bind("<Button-5>", self.scroll_down)
	def activate(self, index):
		"""Display the element at INDEX with activebackground and activerelief.
		INDEX can be "arrow1","slider" or "arrow2"."""
		self.tk.call(self._w, 'activate', index)
	def delta(self, deltax, deltay):
		"""Return the fractional change of the scrollbar setting if it
		would be moved by DELTAX or DELTAY pixels."""
		return getdouble(
			self.tk.call(self._w, 'delta', deltax, deltay))
	def fraction(self, x, y):
		"""Return the fractional value which corresponds to a slider
		position of X,Y."""
		return getdouble(self.tk.call(self._w, 'fraction', x, y))
	def identify(self, x, y):
		"""Return the element under position X,Y as one of
		"arrow1","slider","arrow2" or ""."""
		return self.tk.call(self._w, 'identify', x, y)
	def get(self):
		"""Return the current fractional values (upper and lower end)
		of the slider position."""
		return self._getdoubles(self.tk.call(self._w, 'get'))
	def set(self, *args):
		"""Set the fractional values of the slider position (upper and
		lower ends as value between 0 and 1)."""
		self.tk.call((self._w, 'set') + args)
	def scroll_up(self,*args):
		top,down=self.get()
		offset=0
		if top > self.scroll_offset:
			top-=self.scroll_offset
			down-=self.scroll_offset
			offset=-self.scroll_offset
		else:
			top=0
			down-=top
			offset-=top
		self.set(top,down)
		if self['command'] is not None:
			self.tk.call(self['command'],'moveto',top)
	def scroll_down(self,*args):
		top,down=self.get()
		offset=0
		if 1-down > self.scroll_offset:
			top+=self.scroll_offset
			down+=self.scroll_offset
			offset=self.scroll_offset
		else:
			top+=1-down
			down=1.0
			offset=1-down
		self.set(top,down)
		if self['command'] is not None:
			self.tk.call(self['command'],'moveto',top)
#----------------------------------------------------------------------------------------------------------------------------------------	
class TFrame(Tkinter.Widget):
	"""Frame widget which may contain other widgets and can have a 3D border."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a frame widget with the parent MASTER.

		Valid resource names: background, bd, bg, borderwidth, class,
		colormap, container, cursor, height, highlightbackground,
		highlightcolor, highlightthickness, relief, takefocus, visual, width."""
		cnf = _cnfmerge((cnf, kw))
		extra = ()
		if cnf.has_key('class_'):
			extra = ('-class', cnf['class_'])
			del cnf['class_']
		elif cnf.has_key('class'):
			extra = ('-class', cnf['class'])
			del cnf['class']
		Tkinter.Widget.__init__(self, master, 'ttk::frame', cnf, {}, extra)
#----------------------------------------------------------------------------------------------------------------------------------------	
class TLabelframe(Tkinter.Widget):
	"""TLabelFrame widget which may contain other widgets."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a frame widget with the parent MASTER.

		Valid resource names: background, bd, bg, borderwidth, class,
		colormap, container, cursor, height, highlightbackground,
		highlightcolor, highlightthickness, relief, takefocus, visual, width."""
		cnf = _cnfmerge((cnf, kw))
		extra = ()
		if cnf.has_key('class_'):
			extra = ('-class', cnf['class_'])
			del cnf['class_']
		elif cnf.has_key('class'):
			extra = ('-class', cnf['class'])
			del cnf['class']
		Tkinter.Widget.__init__(self, master, 'ttk::labelframe', cnf, {}, extra)
#--------------------------------------------------------------------------------------------------	
class TMenubutton(Tkinter.Widget):
	"""Menubutton widget, obsolete since Tk8.0."""
	def __init__(self, master=None, cnf={}, **kw):
		Tkinter.Widget.__init__(self, master, 'ttk::menubutton', cnf, kw)
#--------------------------------------------------------------------------------------------------	
class TLabel(Tkinter.Widget):
	"""Label widget which can display text and bitmaps."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a label widget with the parent MASTER.

		STANDARD OPTIONS

			activebackground, activeforeground, anchor,
			background, bitmap, borderwidth, cursor,
			disabledforeground, font, foreground,
			highlightbackground, highlightcolor,
			highlightthickness, image, justify,
			padx, pady, relief, takefocus, text,
			textvariable, underline, wraplength

		WIDGET-SPECIFIC OPTIONS

			height, state, width

		"""
		Tkinter.Widget.__init__(self, master, 'ttk::label', cnf, kw)
#--------------------------------------------------------------------------------------------------	
class TCheckbutton(Tkinter.Widget):
	"""Checkbutton widget which is either in on- or off-state."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a checkbutton widget with the parent MASTER.

		Valid resource names: activebackground, activeforeground, anchor,
		background, bd, bg, bitmap, borderwidth, command, cursor,
		disabledforeground, fg, font, foreground, height,
		highlightbackground, highlightcolor, highlightthickness, image,
		indicatoron, justify, offvalue, onvalue, padx, pady, relief,
		selectcolor, selectimage, state, takefocus, text, textvariable,
		underline, variable, width, wraplength."""
		Tkinter.Widget.__init__(self, master, 'ttk::checkbutton', cnf, kw)
	def deselect(self):
		"""Put the button in off-state."""
		self.tk.call(self._w, 'deselect')
	def flash(self):
		"""Flash the button."""
		self.tk.call(self._w, 'flash')
	def invoke(self):
		"""Toggle the button and invoke a command if given as resource."""
		return self.tk.call(self._w, 'invoke')
	def select(self):
		"""Put the button in on-state."""
		self.tk.call(self._w, 'select')
	def toggle(self):
		"""Toggle the button."""
		self.tk.call(self._w, 'toggle')
#--------------------------------------------------------------------------------------------------		
class TRadiobutton(Tkinter.Widget):
	"""Radiobutton widget which shows only one of several buttons in on-state."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a radiobutton widget with the parent MASTER.

		Valid resource names: activebackground, activeforeground, anchor,
		background, bd, bg, bitmap, borderwidth, command, cursor,
		disabledforeground, fg, font, foreground, height,
		highlightbackground, highlightcolor, highlightthickness, image,
		indicatoron, justify, padx, pady, relief, selectcolor, selectimage,
		state, takefocus, text, textvariable, underline, value, variable,
		width, wraplength."""
		Tkinter.Widget.__init__(self, master, 'ttk::radiobutton', cnf, kw)
	def deselect(self):
		"""Put the button in off-state."""

		self.tk.call(self._w, 'deselect')
	def flash(self):
		"""Flash the button."""
		self.tk.call(self._w, 'flash')
	def invoke(self):
		"""Toggle the button and invoke a command if given as resource."""
		return self.tk.call(self._w, 'invoke')
	def select(self):
		"""Put the button in on-state."""
		self.tk.call(self._w, 'select')
#--------------------------------------------------------------------------------------------------			
class TEntry(Tkinter.Widget):
	"""Entry widget which allows to display simple text."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct an entry widget with the parent MASTER.
		
		Valid resource names: background, bd, bg, borderwidth, cursor,
		exportselection, fg, font, foreground, highlightbackground,
		highlightcolor, highlightthickness, insertbackground,
		insertborderwidth, insertofftime, insertontime, insertwidth,
		invalidcommand, invcmd, justify, relief, selectbackground,
		selectborderwidth, selectforeground, show, state, takefocus,
		textvariable, validate, validatecommand, vcmd, width,
		xscrollcommand."""
		kw['cursor']='xterm'
		Tkinter.Widget.__init__(self, master, 'ttk::entry', cnf, kw)
	def delete(self, first, last=None):
		"""Delete text from FIRST to LAST (not included)."""
		self.tk.call(self._w, 'delete', first, last)
	def get(self):
		"""Return the text."""
		return self.tk.call(self._w, 'get')
	def icursor(self, index):
		"""Insert cursor at INDEX."""
		self.tk.call(self._w, 'icursor', index)
	def index(self, index):
		"""Return position of cursor."""
		return getint(self.tk.call(
			self._w, 'index', index))
	def insert(self, index, string):
		"""Insert STRING at INDEX."""
		self.tk.call(self._w, 'insert', index, string)
	def scan_mark(self, x):
		"""Remember the current X, Y coordinates."""
		self.tk.call(self._w, 'scan', 'mark', x)
	def scan_dragto(self, x):
		"""Adjust the view of the canvas to 10 times the
		difference between X and Y and the coordinates given in
		scan_mark."""
		self.tk.call(self._w, 'scan', 'dragto', x)
	def selection_adjust(self, index):
		"""Adjust the end of the selection near the cursor to INDEX."""
		self.tk.call(self._w, 'selection', 'adjust', index)
	select_adjust = selection_adjust
	def selection_clear(self):
		"""Clear the selection if it is in this widget."""
		self.tk.call(self._w, 'selection', 'clear')
	select_clear = selection_clear
	def selection_from(self, index):
		"""Set the fixed end of a selection to INDEX."""
		self.tk.call(self._w, 'selection', 'from', index)
	select_from = selection_from
	def selection_present(self):
		"""Return whether the widget has the selection."""
		return self.tk.getboolean(
			self.tk.call(self._w, 'selection', 'present'))
	select_present = selection_present
	def selection_range(self, start, end):
		"""Set the selection from START to END (not included)."""
		self.tk.call(self._w, 'selection', 'range', start, end)
	select_range = selection_range
	def selection_to(self, index):
		"""Set the variable end of a selection to INDEX."""
		self.tk.call(self._w, 'selection', 'to', index)
	select_to = selection_to
	def xview(self, index):
		"""Query and change horizontal position of the view."""
		self.tk.call(self._w, 'xview', index)
	def xview_moveto(self, fraction):
		"""Adjust the view in the window so that FRACTION of the
		total width of the entry is off-screen to the left."""
		self.tk.call(self._w, 'xview', 'moveto', fraction)
	def xview_scroll(self, number, what):
		"""Shift the x-view according to NUMBER which is measured in "units" or "pages" (WHAT)."""
		self.tk.call(self._w, 'xview', 'scroll', number, what)
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
class TButton(Tkinter.Widget):
	"""Button widget."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a button widget with the parent MASTER.

		STANDARD OPTIONS

			activebackground, activeforeground, anchor,
			background, bitmap, borderwidth, cursor,
			disabledforeground, font, foreground
			highlightbackground, highlightcolor,
			highlightthickness, image, justify,
			padx, pady, relief, repeatdelay,
			repeatinterval, takefocus, text,
			textvariable, underline, wraplength

		WIDGET-SPECIFIC OPTIONS

			command, compound, default, height,
			overrelief, state, width
		"""
		Tkinter.Widget.__init__(self, master, 'ttk::button', cnf, kw)

	def tkButtonEnter(self, *dummy):
		self.tk.call('tkButtonEnter', self._w)

	def tkButtonLeave(self, *dummy):
		self.tk.call('tkButtonLeave', self._w)

	def tkButtonDown(self, *dummy):
		self.tk.call('tkButtonDown', self._w)

	def tkButtonUp(self, *dummy):
		self.tk.call('tkButtonUp', self._w)

	def tkButtonInvoke(self, *dummy):
		self.tk.call('tkButtonInvoke', self._w)

	def flash(self):
		"""Flash the button.

		This is accomplished by redisplaying
		the button several times, alternating between active and
		normal colors. At the end of the flash the button is left
		in the same normal/active state as when the command was
		invoked. This command is ignored if the button's state is
		disabled.
		"""
		self.tk.call(self._w, 'flash')

	def invoke(self):
		"""Invoke the command associated with the button.

		The return value is the return value from the command,
		or an empty string if there is no command associated with
		the button. This command is ignored if the button's state
		is disabled.
		"""
		return self.tk.call(self._w, 'invoke')
	
	def state(self, state):
		return self.tk.call(self, 'state', state)
	
#----------------------------------------------------------------------------------------------------------------------------------------	
class TCombobox(Tkinter.Widget):
	"""OptionMenu which allows the user to select a value from a menu."""
	def __init__(self, master, **kwargs):
		"""Construct an optionmenu widget with the parent MASTER, with
		the resource textvariable set to VARIABLE, the initially selected
		value VALUE, the other menu values VALUES and an additional
		keyword argument command."""
		Tkinter.Widget.__init__(self, master, "ttk::combobox", kwargs)
		self.widgetName = 'ttk_Combobox'
		#menu = self.__menu = Menu(self, name="menu", tearoff=0)
		#self.menuname = menu._w
		# 'command' is the only supported keyword
		#callback = kwargs.get('postcommand')
		#if kwargs.has_key('postcommand'):
			#del kwargs['postcommand']
		#if kwargs:
			#raise TclError, 'unknown option -'+kwargs.keys()[0]
		#menu.add_command(label=value,
				 #command=_setit(variable, value, callback))
		#for v in values:
			#menu.add_command(label=v,
					 #command=_setit(variable, v, callback))
		#self["menu"] = menu

	#def __getitem__(self, name):
		#if name == 'menu':
			#return self.__menu
		#return Widget.__getitem__(self, name)

	def destroy(self):
		"""Destroy this widget and the associated menu."""
		Tkinter.Widget.destroy(self)
		#self.__menu = None

#----------------------------------------------------------------------------------------------------------------------------------------	
class LabelFrame(Tkinter.Widget):
	"""Frame widget which may contain other widgets and can have a 3D border."""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a frame widget with the parent MASTER.

		Valid resource names: background, bd, bg, borderwidth, class,
		colormap, container, cursor, height, highlightbackground,
		highlightcolor, highlightthickness, relief, takefocus, visual, width."""
		cnf = _cnfmerge((cnf, kw))
		extra = ()
		if cnf.has_key('class_'):
			extra = ('-class', cnf['class_'])
			del cnf['class_']
		elif cnf.has_key('class'):
			extra = ('-class', cnf['class'])
			del cnf['class']
		Tkinter.Widget.__init__(self, master, 'labelframe', cnf, {}, extra)
		
#----------------------------------------------------------------------------------------------------------------------------------------	
class TProgressbar(Tkinter.Widget):
	"""ttk::progressbar - Provide progress feedback"""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a frame widget with the parent MASTER.
			STANDARD OPTIONS:
			class, cursor, style, takefocus
			
			WIDGET-SPECIFIC OPTIONS: 
			orient, length, mode, maximum, value, variable, phase
			"""
		cnf = _cnfmerge((cnf, kw))
		extra = ()
		if cnf.has_key('class_'):
			extra = ('-class', cnf['class_'])
			del cnf['class_']
		elif cnf.has_key('class'):
			extra = ('-class', cnf['class'])
			del cnf['class']
		Tkinter.Widget.__init__(self, master, 'ttk::progressbar', cnf, {}, extra)
		
	def start(self, interval=50):
		"""Begin autoincrement mode: schedules a recurring timer event that 
		calls step every interval milliseconds. If omitted, interval defaults 
		to 50 milliseconds (20 steps/second)."""
		self.tk.call(self._w, 'start', interval)
		
	def stop(self):
		"""Stop autoincrement mode: cancels any recurring timer event initiated 
		by pathName start."""
		self.tk.call(self._w, 'stop')
		
	def step(self, amount=1.0):
		"""Increments the -value by amount. amount defaults to 1.0 if omitted."""
		self.tk.call(self._w, 'step', amount)
		
	def destroy(self):
		"""Destroy this widget and the associated menu."""
		self.stop()
		Tkinter.Widget.destroy(self)
		
#----------------------------------------------------------------------------------------------------------------------------------------	
class TNotebook(Tkinter.Widget):
	"""ttk::notebook - Multi-paned container widget"""
	def __init__(self, master=None, cnf={}, **kw):
		"""Construct a frame widget with the parent MASTER.
			STANDARD OPTIONS:
			class, cursor, style, takefocus
			
			WIDGET-SPECIFIC OPTIONS: 
			height, padding, width
			
			TAB OPTIONS:
			state, sticky, padding, text, image, compound, underline
			"""
		cnf = _cnfmerge((cnf, kw))
		extra = ()
		if cnf.has_key('class_'):
			extra = ('-class', cnf['class_'])
			del cnf['class_']
		elif cnf.has_key('class'):
			extra = ('-class', cnf['class'])
			del cnf['class']
		Tkinter.Widget.__init__(self, master, 'ttk::notebook', cnf, {}, extra)
		
	def add(self, window, cnf={}, **kw):
		"""Adds a new tab to the notebook. See TAB OPTIONS for the list of 
		available options. If window is currently managed by the notebook 
		but hidden, it is restored to its previous position."""
		self.tk.call((self._w, 'add', window) + self._options(cnf, kw))
				
	def forget(self, tabid):
		"""Removes the tab specified by tabid, unmaps and unmanages the 
		associated window."""
		self.tk.call(self._w, 'forget', tabid)
		
	def hide(self, tabid):
		"""Hides the tab specified by tabid. The tab will not be displayed, 
		but the associated window remains managed by the notebook and its 
		configuration remembered. Hidden tabs may be restored with the add 
		command."""
		self.tk.call(self._w, 'hide', tabid)
		
	def index(self, tabid):
		"""Returns the numeric index of the tab specified by tabid, or the 
		total number of tabs if tabid is the string 'end'."""
		self.tk.call(self._w, 'index', tabid)
		
	def insert(self, pos, window, cnf={}, **kw):
		"""Inserts a pane at the specified position. pos is either the string 
		end, an integer index, or the name of a managed subwindow. If subwindow 
		is already managed by the notebook, moves it to the specified position. 
		See TAB OPTIONS for the list of available options."""
		self.tk.call(self._w, 'insert', pos, window._w, cnf, kw)

	def select(self, tabid):
		"""Selects the specified tab. The associated slave window will be 
		displayed, and the previously-selected window (if different) is unmapped. 
		If tabid is omitted, returns the widget name of the currently selected 
		pane."""
		self.tk.call(self._w, 'select', tabid)
		
	