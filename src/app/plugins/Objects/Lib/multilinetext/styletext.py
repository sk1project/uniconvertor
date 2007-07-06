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


from ScrolledText import ScrolledText
from iterator import Style, StyletextError, Pool
from string import atoi, replace, split

class StyleText(ScrolledText):

	def __init__(self, master, **kw):
		apply(ScrolledText.__init__, (self, master), kw)

		self.pool = Pool(self)
		self.sorts = {}
		self.sorts_order = []

		self.clip_text = ''
		self.clip_styling = []

		# XXX force-mechanism should be moved to TextEditor
		self.style_force = []

		self._patch_tk()
		self.bind('<Control-c>', self.copyevent)
		self.bind('<Control-v>', self.pasteevent)

		self.bind('<Alt-p>', lambda e, s=self:s.pool.dump())
		self.bind('<Alt-t>', lambda e, s=self:s.tag_dump())
		self.bind('<Alt-m>', lambda e, s=self:s.mark_dump())
		self.bind('<Alt-g>', lambda e, s=self:s.styling_dump())
		self.bind('<Alt-s>', lambda e, s=self:s.print_current_style())
		self.bind('<Alt-f>', lambda e, s=self:s.fontify('1.0','end'))

	def _patch_tk(self):
		insert_tcl = self.register(self.insert)
		delete_tcl = self.register(self.delete)

		tclstr = """
		rename _w _old_w

		proc _w { command args } {
			if { $command == "insert" } {
				set ret [ eval "insert_tcl $args" ]
			} elseif {$command == "delete"} {
				set ret [ eval "delete_tcl $args" ]
			} else {
				set ret [ eval "_old_w $command $args" ]
			}
			return $ret
		}
		"""
		self._old_w = '.old'+self._w
		tclstr = replace(tclstr, '_old_w', self._old_w)
		tclstr = replace(tclstr, '_w', self._w)
		tclstr = replace(tclstr, 'insert_tcl', insert_tcl)
		tclstr = replace(tclstr, 'delete_tcl', delete_tcl)
		self.tk.eval(tclstr)

	def copyevent(self, event):
		range = self.tag_ranges('sel')
		if len(range) !=2:
			return
		self.clip_text = apply(self.get, range)
		self.clip_styling = apply(self.styling_get, range)

	def pasteevent(self, event):
		self.delselection()
		index = self.index('insert')
		self.insert(index, self.clip_text)
		self.styling_apply(index, self.clip_styling)

	def delselection(self):
		sel = self.tag_ranges('sel')
		if len(sel) == 2:
			apply(self.delete, sel)

	def register_sort(self, sortid, function, default):
		defaultstyle = apply(Style,(),{sortid : default})
		self.sorts[sortid] = (function, defaultstyle)
		self.sorts_order.insert(0, sortid)

	def print_current_style(self,event=None):
		print "_____ current style %s ______" % self.index('insert')
		for style in self.style_get('insert'):
			print self.index('insert'),"\t", style

	def mark_dump(self):
		list = []
		for name in self.mark_names():
			list.append((self.index(name), name))
		list.sort()


		print "============== mark dump ================="
		for pos, name in list:
#            if name[0] == '_':
				print pos,"\t", name

	def tag_dump(self):
		print "============== tag dump ==================="
		names = list(self.tag_names())
		out = []
		for tag in names:
			ranges = self.tag_ranges(tag)
			if len(ranges)>0:
				out.append((ranges, tag))
		out.sort()
		for ranges, tag in out:
			print tag,"\t\t", ranges

	def delete(self, index1, index2=None):
		index1 = self.index(index1)
		it = self.pool.iterator()
		self.tk.call(self._old_w, 'delete', index1, index2)

		# remove all tag changes which became obsolete.
		# Obsolete means, (1) the tag is at or after 'end' or (2) there
		# is another tag of the same sort at the same index position.
		it.before(index1)
		it.next()
		dict = {}
		while (not it.outofboundary) and self.compare(it, '==', index1):
			sort = it.current.sort
			if dict.has_key(sort):
				it.delete()
			else:
				dict[sort] = 1
				it.next()
		it.i = len(self.pool)-1
		it._update()
		while (not it.outofboundary) and self.compare(it, '>=', 'end'):
			it.delete()

	def insert(self, index, chars, *tagsnstyles):
		tags = []
		styles = self.style_force
		for arg in tagsnstyles:
			if type(arg).__name__ == 'string':
				tags = tags + arg
			elif hasattr(arg, 'is_Style'):
				styles.append(arg)
			else:
				raise StyletextError(
					"arguments should be tags and styles: %s" % arg)

		begin = self.index(index)
		self.tk.call((self._old_w, 'insert', index, chars) + tuple(tags))

		end = self.index('%s + %dc' % (begin, len(chars)))
		for style in styles:
			self.style_add(style, begin, end, supressfontify=1)
		self.fontify("%s linestart - 1 lines" % begin, "%s lineend" % end)
		self.style_force = []

	def style_get(self, index, sort = None):
		'''Returns the style of type sort at position index.

		If sort is not given, returns a complete list of all styles.
		'''
		it = self.pool.iterator()
		it.before(index)

		if sort is not None:
			# look for a style of type 'sort'
			if it.outofboundary:
				return self.sorts[sort][1]
			while not it.is_first() and not it.current.sort == sort:
				it.prev()
			if it.current.sort == sort:
				return it.current
			else:
				return self.sorts[sort][1]
		else:

			dict = {}
			if not it.outofboundary:
				dict[it.current.sort] = it.current
				while (not it.is_first()) and len(dict)<len(self.sorts):
					it.prev()
					if not dict.has_key(it.current.sort):
						dict[it.current.sort] = it.current
			# if incomplete: fill up with defaults
			for sort in self.sorts.keys():
				if not dict.has_key(sort):
					dict[sort] = self.sorts[sort][1]
			ret = []

			# keep the order as given in self.sorts.keys()
			for sort in self.sorts_order:
				ret.append(dict[sort])
			return ret

	def style_get_range(self, begin, end, sort=None):
		'''returns all styles between begin and end.

		If sort is given, only those of type sort are returned.
		'''
		styles = self.style_get(begin+'+1 chars')
		it = self.pool.iterator()
		it.before(begin+'+1 chars')
		while  not it.is_last():
			it.next()
			if self.compare(it.id,'>=', end):
				break
			try:
				i = styles.index(it.current)
			except:
				styles.append(it.current)
		return styles

	def style_removeall(self):
		for mark in self.mark_names():
			if mark[0] == '_':
				self.mark_unset(mark)
		self.pool = Pool(self)
		self.fontify('1.0','end')

	def styling_get(self, begin, end):
		it = self.pool.iterator()
		styles = self.style_get(begin+"+ 1 chars")
		styling = []
		for style in styles:
			styling.append((style, begin))
		it.before(begin)
		# need to replace befores when there a style at
		while 1:
			if it.i >= len(self.pool):
				break
			elif it.i >= 0:
				if self.compare(it, '>', end):
					break
				elif self.compare(it, '>', begin):
					style = it.current
					styling.append((style, self.index(it)))
			it.next()
		#
		end = self.index(end)
		styling.append((None, end))

		# relocate indizes
		ret = []
		bline, bchar = map(atoi, split(begin, '.'))
		for style, indexstr in styling:
			line, char = map(atoi, split(indexstr, '.'))
			if line == bline:
				char = char-bchar
			line = line-bline
			ret.append((style, line, char))

		return ret

	def styling_apply(self, index, styling):
		if styling is None or len(styling) == 0:
			return
		index = self.index(index)
		iline, ichar = map(atoi, split(index, '.'))
		it = self.pool.iterator()

		# determine end
		tmp, eline, echar = styling[-1]
		if eline == 0:
			echar = echar+ichar
		eline = eline+iline
		end = "%i.%i" % (eline, echar)

		i = 0
		for style, line, char in styling[:-1]:
			i = i+1
			if line == 0:
				char = char+ichar
			line = line+iline
			indexstr = "%i.%i" % (line, char)
			if i<4:
				self.style_add(style, index, end, supressfontify=1)
			else:
				# insert it
				it.insert_right(style, indexstr)
		self.fontify(index, end)


	def styling_dump(self):
		range = self.tag_ranges('sel')
		if len(range) != 2:
			return
		print apply(self.styling_get, range)

	def fontify(self, begin, end):
		for name in self.tag_names():
			if name[0]=='_':
				self.tag_remove(name, begin, end)

		styles = self.style_get(begin)
		dict = {}

		for style in styles:
			name = name+style._signature_
			dict[style.sort] = style.options

		it = self.pool.iterator()
		it.before(begin) # last style change before' begin'
		a = begin
		while self.compare(a,'<',end):
			if it.is_last():
				b = end
			else:
				it.next()
				b = it.id

			options = {}
			name = '_'+str(dict)
			self.tag_add(name,a, b)
			_dict = dict.copy()

			for sort in self.sorts_order:
				func = self.sorts[sort][0]
				apply(func, (options, _dict))

			self.tag_configure(name, options)

			if not it.outofboundary:
				dict[it.current.sort] = it.current.options
			a = b

	def style_add(self, style, begin, end, supressfontify=0):
		if self.compare(begin,'>=',end):
			return
		it = self.pool.iterator()

		# this is the simplest, definitly not the fastest solution
		ostyle_begin = self.style_get(begin, style.sort)
		ostyle_end = self.style_get(end+' +1 chars', style.sort)

		# delete all style changes of sort "style.sort" between "begin" and
		# "end"
		it.before(begin)
		it.next()
		while (not it.outofboundary) and  self.compare(it,'<=',end):
			if it.current.sort == style.sort:
				it.delete()
			else:
				it.next()
		if ostyle_begin != style:
			it.insert_left(style, begin)
		if ostyle_end != style:
			it.insert_right(ostyle_end, end)

		if not supressfontify:
			self.fontify(begin, end)

	# for older Tkinter version (those coming with Python 1.5.2) add
	# some missing Text methods
	def mark_next(self, index):
		"""Return the name of the next mark after INDEX."""
		return self.tk.call(self._w, 'mark', 'next', index) or None

	def mark_previous(self, index):
		"""Return the name of the previous mark before INDEX."""
		return self.tk.call(self._w, 'mark', 'previous', index) or None


if __name__=='__main__':
	from Tkinter import *
	tk = Tk()
	text = StyleText(tk, background='white')
	text.pack(fill=BOTH, expand=1)
	text.insert(END,'01234567890abcdefghijkl\n')
	text.insert(END,'01234567890abcdefghijkl\n')
	text.insert(END,'01234567890abcdefghijkl\n')

	import sys
	sys.path.append('/usr/lib/sketch-0.6.12/')
	from app.Graphics import font

	class font_families:
		def __init__(self):
			self.family_to_fonts = font.make_family_to_fonts()
			self.families = self.family_to_fonts.keys()
			self.families.sort()

		def xlfd(self, **kw):
			fonts = self.family_to_fonts[kw['family']]
			for name in fonts:
				family, attrs, xlfd_start, encoding = font.fontmap[name]
				if attrs == kw['attr']:
					return font.xlfd_template % \
										(xlfd_start, kw['size'], encoding)

			kw['attr'] = 'Roman'
			return apply(self.xlfd, (), kw)

		def ps(self, **kw):
			props = {}
			props.update(DEFAULT)
			props.update(kw)

			fonts = self.family_to_fonts[props['family']]
			for name in fonts:
				family, attrs, xlfd_start, encoding = font.fontmap[name]
				if attrs == props['attr']:
					return name
			return ''

	font.read_font_dirs()
	FONTS = font_families()

	def FamilySort(tagoptions, dict):
		return tagoptions

	def AttrSort(tagoptions, dict):
		return tagoptions

	def SizeSort(tagoptions, dict):
		xfont = apply(FONTS.xlfd, (), dict)
		tagoptions['font'] = xfont
		return tagoptions

	text.register_sort('family', FamilySort, 'Times' )
	text.register_sort('attr', AttrSort, 'Roman')
	text.register_sort('size', SizeSort, 12)
	
	
	text.style_add(Style(size=24),'1.5','2.13')
	text.pool.dump()
	text.style_add(Style(size=72),'1.4','2.14')
	text.pool.dump()

	raw_input()
