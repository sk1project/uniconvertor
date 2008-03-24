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


from styletext import StyleText, Style
import Tkinter
from Tkconstants import *
from tkFileDialog import asksaveasfilename, asksaveasfilename, \
		askopenfilename
from app.Graphics import font
from app import _

from cPickle import loads, dumps
import os


def raw2styling(raw):
	styling = []
	for l, line, char in raw:
		if l == 0:
			style = None
		else:
			style = apply(Style, [], {l[0] : l[1]})
		styling.append((style, line, char))
	return styling
	
def styling2raw(styling):
	raw_styling = []
	for style, line, char in styling:
		if style is not None:
			l = (style.sort, style.options)
		else:
			l = 0
		raw_styling.append((l, line, char))
	return raw_styling
	
	
	
st_signature = '## styletext '
def load_text(name):
	file = open(name, 'r')
	s = file.read()
	file.close()
	styling = []
	len_sig = len(st_signature)

	if s[:len_sig] == st_signature:
		text, raw = loads(s[len_sig:])
		styling = raw2styling(raw)
	else:
		# assume plain text otherwise
		text = s
	return text, styling

def save_text(name, text, styling=[]):
	file = open(name, 'w')
	if name[-3:] == '.st':
		raw = styling2raw(styling)
		s = st_signature + dumps((text, raw))
	else:
		s = text

	file.write(s)
	file.close()


class font_families:
	def __init__(self):
		self.family_to_fonts = font.make_family_to_fonts()
		self.families = self.family_to_fonts.keys()
		self.families.sort()

	def xlfd(self, **kw):
		fonts = self.family_to_fonts[kw['family']]
		list = [kw['attr'], 'Roman']
		for attr in list:
			for name in fonts:
				family, attrs, xlfd_start, encoding = font.fontmap[name]
				if attrs == attr:
					return font.xlfd_template % (xlfd_start, kw['size'],
													encoding)

	def ps(self, **kw):
		family = kw['family']
		fonts = self.family_to_fonts[family]
		list = [kw['attr'], 'Roman']
		for attr in list:
			for name in fonts:
				family, attrs, xlfd_start, encoding = font.fontmap[name]
				if attrs == attr:
					return name
		return ''

font.read_font_dirs()
FONTS = font_families()
std_sizes = (8, 9, 10, 12, 14, 18, 24, 36, 48, 72)



class TextEditor(StyleText):
	def __init__(self, parent=None, **kw):
		self.top = parent
		apply(StyleText.__init__, (self, parent), kw)

		self.register_sort('family', self.FamilySort, 'Times' )
		self.register_sort('bold', self.BoldSort, 0)
		self.register_sort('italic', self.ItalicSort, 0)
		self.register_sort('size', self.SizeSort, 12)
		self.register_sort('color', self.ColorSort, 'black' )
		self.register_sort('supersub', self.SupersubSort, 'normal' )
		self.plain_options = {'size':14, 'color':'black'}

		bar = Tkinter.Frame(parent)
		self._make_menu()

		self.bind('<ButtonRelease-1>', lambda e, s=self: s.Update())
		self.bind('<KeyRelease>', lambda e, s=self: s.Update())

		rightFrame = Tkinter.Frame(bar)
		self.button_apply = Tkinter.Button(rightFrame, text='apply')
		self.button_apply.pack()
		rightFrame.pack(side='right')
		bar.pack(side = 'top', fill = 'x')

	def _make_menu(self):
		# make menu button
		menu = Tkinter.Menu(self)
		menu.file = Tkinter.Menu(menu)

		menu.file.add_command(label='Load', command=self.load)
		menu.file.add_command(label='Save', command=self.saveas)
		menu.file.add_command(label='Insert', command=self.insert_file)


		menu.options = Tkinter.Menu(menu)
		self._plainmode_state = Tkinter.IntVar()
		menu.options.add_checkbutton(label='Plain mode', \
			variable = self._plainmode_state,
			command = lambda s=self: s.fontify('1.0', 'end'))

		menu.family = Tkinter.Menu(menu)
		for f in FONTS.families:
			menu.family.add_command(label=f,
				command=lambda s=self, f=f: s.change_family(f))

		menu.size = Tkinter.Menu(menu)
		for f in std_sizes:
			menu.size.add_command(label=f,
				command=lambda s=self, f=f: s.change_size(f))

		menu.color = Tkinter.Menu(menu)
		for f in ('black', 'darkgray', 'gray', 'lightgray', 'blue', 'cyan',
					'green', 'magenta', 'red', 'yellow', 'white'):
			menu.color.add_command(label=f, \
				command=lambda s=self, f=f: s.change_color(f),
				background = f)

		# definition of the menu one level up...
		menu.add_cascade(
			label='File',
			menu=menu.file)
		menu.add_cascade(
			label='Options',
			menu=menu.options)

		menu.add_separator()

		menu.add_cascade(
			label='Font Family',
			menu=menu.family)

		menu.add_cascade(
			label='Size',
			menu=menu.size)

		menu.add_cascade(
			label='Color',
			menu=menu.color)

		self._bold_state = Tkinter.IntVar()
		self._italic_state = Tkinter.IntVar()

		menu.add_checkbutton(label=_('Bold'), \
								variable=self._bold_state,
								command=lambda s=self, i=self._bold_state: \
										s.change_bold(i.get())
							)
		menu.add_checkbutton(label=_("Italic"),
								variable=self._italic_state,
								command=lambda s=self, i=self._italic_state: \
										s.change_italic(i.get())
							)

		self._subscript_state = Tkinter.IntVar()
		self._superscript_state = Tkinter.IntVar()

		menu.add_checkbutton(label=_("Subscript"), \
			variable=self._subscript_state,
			command=lambda s=self, i=self._subscript_state: \
					s.change_subscript(i.get())
			)
		menu.add_checkbutton(label=_("Superscript"), \
			variable=self._superscript_state,
			command=lambda s=self, i=self._superscript_state: \
					s.change_superscript(i.get())
			)

		self.menu = menu
		self.bind('<Button-3>',
					lambda e, s=self: s.menu.tk_popup(e.x_root, e.y_root))
						
	def warn(self, title, message):
		# This will be overridden
		pass
		
	def _update_menu(self):
		styles = self.style_get('insert')
		dict = {}
		for style in styles:
			dict[style.sort] = style.options

		self.menu.entryconfigure(4, label=dict['family'])
		self.menu.entryconfigure(5, label=dict['size'])
		self.menu.entryconfigure(6, foreground=dict['color'])
		supersub = dict['supersub']
		self._superscript_state.set(supersub=='superscript')
		self._subscript_state.set(supersub=='subscript')

		self._bold_state.set(dict['bold'])
		self._italic_state.set(dict['italic'])

	def Update(self):
		self._update_menu()

	def ColorSort(self, tagoptions, alloptions):
		if not self._plainmode_state.get():
			tagoptions['foreground'] = alloptions['color']
		else:
			tagoptions['foreground'] = self.plain_options['color']

	
	def SupersubSort(self, tagoptions, alloptions):
		if self._plainmode_state.get():
			size = self.plain_options['size']
		else:
			size = alloptions['size']

		option = alloptions['supersub']
		if option == 'subscript':
			alloptions['size'] = size * 0.5
			tagoptions['offset'] = -size * 0.2
		elif option == 'superscript':
			alloptions['size'] = size * 0.5
			tagoptions['offset'] = size * 0.6

	def FamilySort(self, tagoptions, alloptions):
		pass
	
	def ItalicSort(self, tagoptions, alloptions):
		pass
	
	def BoldSort(self, tagoptions, alloptions):
		pass
	
	def SizeSort(self, tagoptions, alloptions):
		dict = {}
		if not self._plainmode_state.get():
			dict['size'] = int(round(alloptions['size']))
		else:
			dict['size'] = self.plain_options['size']

		dict['family'] = alloptions['family']
		bold = alloptions['bold']
		italic = alloptions['italic']
		if bold and italic:
			dict['attr'] = 'Bold Italic'
		elif bold:
			dict['attr'] = 'Bold'
		elif italic:
			dict['attr'] = 'Italic'
		else:
			dict['attr'] = 'Roman'

		xfont = apply(FONTS.xlfd, (), dict)
		tagoptions['font'] = xfont


	def change_set(self, style):
		range = self.tag_ranges('sel')
		if len(range) == 2:
			apply(self.style_add,(style,)+self.tag_ranges('sel'))
		else:
			self.style_force.append(style)
		self.Update()

	def change_bold(self, state):
		style = Style(bold=state)
		self.change_set(style)

	def change_subscript(self, state):
		if state:
			self._superscript_state.set(0)
			style = Style(supersub='subscript')
		else:
			style = Style(supersub='normal')
		self.change_set(style)


	def change_superscript(self, state):
		if state:
			self._subscript_state.set(0)
			style = Style(supersub='superscript')
		else:
			style = Style(supersub='normal')
		self.change_set(style)

	def change_italic(self, state):
		style = Style(italic=state)
		self.change_set(style)

	def change_family(self, family):
		style = Style(family=family)
		self.change_set(style)

	def change_size(self, size):
		style = Style(size=size)
		self.change_set(style)

	def change_color(self, color):
		style = Style(color=color)
		self.change_set(style)

	def load(self, event=None):
		name = askopenfilename( \
			filetypes=[(_("styletext files"), "*.st"), \
						(_("all files"), "*")])
		if name:
			try:
				text, styling = load_text(name) 
			except Exception, value:
				self.warn( 
					title = _("Load File"),
					message = _("Cannot load %(filename)s:\n"
								"%(message)s") \
					% {'filename':`os.path.split(name)[1]`,
						'message':value})
				return
			index = '1.0'
			self.style_removeall()
			self.delete('1.0', 'end')
			self.insert(index, text)
			self.styling_apply(index, styling)

	def saveas(self, event=None):
		name = asksaveasfilename( \
			filetypes=[(_("styletext files"), "*.st"), \
						(_("all files"), "*")])
		if name:
			text = self.get('1.0', 'end')
			styling = self.styling_get('1.0', 'end')
			try:
				save_text(name, text, styling)
			except IOError, value:
				self.warn( 
					title = _("Save File"),
					message = _("Cannot Save %(filename)s:\n"
								"%(message)s") \
					% {'filename':`os.path.split(name)[1]`,
						'message':value})

	def insert_file(self, event=None):
		name = askopenfilename( \
			filetypes=[(_("styletext files"), "*.st"), \
						(_("all files"), "*")])
		if name:
			try:
				text, styling = load_text(name) 
			except Exception, value:
				self.warn( 
					title = _("Insert File"),
					message = _("Cannot insert %(filename)s:\n"
								"%(message)s") \
					% {'filename':`os.path.split(name)[1]`,
						'message':value})
				return
			
			index = self.index('insert')
			self.insert(index, text)
			self.styling_apply(index, styling)
	


def test1():
	tk = Tkinter.Tk()
	text = TextEditor(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	text.insert(END,'1\n2\n3\n4\n5\n')
	text.fontify('1.0','end')
	text.style_add(Style(size=24), '2.0','3.0')
	text.style_add(Style(size=36), '4.0','5.0')
	text.fontify('1.0','end')
	text.bind('<Control-l>', text.load)
	text.bind('<Control-s>', text.saveas)
	text.bind('<Control-i>', text.insert_file)

	raw_input()

def waste():
	global text
	print "profiling"
	for i in range(1000):
		text.insert('250.10', "x")

def test2():
	#
	# profiling
	tk = Tkinter.Tk()
	global text
	text = TextEditor(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	n = 500
	print "n =", n
	for i in range(n):
#        print i
		text.insert(END, '1234567890abcdefghij\n')
		text.style_add(Style(sizesort, size=24), 'end -5 chars',
						'end -3 chars')
		text.style_add(Style(familysort, family="Helvetica"), 'end -5 chars',
						'end -3 chars')
		text.style_add(Style(attrsort, attr="Italic"), 'end -5 chars',
						'end -3 chars')

	from profile import run
	run("waste()")

def test3():
	tk = Tkinter.Tk()
	text = TextEditor(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.style_add(Style(size = 24), '1.0','4.0')
	text.style_add(Style(size = 24), '2.0','3.0')
	text.pool.dump()

def test4():
	tk = Tkinter.Tk()
	text = TextEditor(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.style_add(Style(size = 24), '2.0','3.0')
	text.style_add(Style(size = 24), '1.0','4.0')
	text.pool.dump()


def test5():
	tk = Tkinter.Tk()
	text = TextEditor(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.insert(END,'1234567890\n')
	text.style_add(Style(size = 24), '1.0','3.0')
	text.style_add(Style(size = 24), '2.0','4.0')
	text.pool.dump()

if __name__=='__main__':
	import sys
	sys.path.append('/usr/lib/sketch-0.6.12/')
	# 
	test1()
	
	#
	#~ for test in (test3, test4, test5):
		#~ print "\n", test.__name__
		#~ apply(test)
