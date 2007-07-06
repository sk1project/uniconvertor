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

class StyletextError(Exception):
	pass
	
	
class Style:

	is_Style = 1

	def __init__(self, **kw):
		if len(kw) != 1:
			raise StyletextError(
				"Style should be called with exactly one parameter "
				"eg. Style(size=3): %s" % kw)
		self.sort = kw.keys()[0]
		self.options = kw.values()[0]
		self._signature_ = str(kw)

	def __cmp__ (self, other):
		if not hasattr(other, 'is_Style'):
			raise StyletextError(
				"can't compare styles to non-style objects: %s" %
				other)
		s1 = self._signature_
		s2 = other._signature_
		return cmp(s1,s2)

class Id:

	def __init__(self):
		self.next_id = -1

	def new_id(self):
		self.next_id = self.next_id+1
		return '_'+str(self.next_id)

class Pool(Id):

	def __init__(self, text_inst=None):
		self.keys = []
		self.signatures = []
		self.dict = {}
		self.Text = text_inst

		Id.__init__(self)

	def __len__(self):
		return len(self.keys)

	def __getitem__(self, key):
		i = self.keys.index(key)
		sig = self.signatures[i]
		return self.dict[sig]

	def __setitem__(self, key, value):
		# XXX inconistency: keys should be created solely by pool
		try:
			i = self.keys.index(key)
			sig = value._signature_
		except:
			self.keys.append(key)
			sig = value._signature_
			self.signatures.append(sig)
		self.dict[sig] = value

	def __delitem__(self, key):
		i = self.keys.index(key)
		del self.keys[i]
		sig = self.signatures[i]
		del self.signatures[i]
		try:
			i = self.signatures.index(sig)
		except:
			del self.dict[sig]

	def dump(self):
		out = []
		print "______________ POOL DUMP __________"
		for i in range(len(self.keys)):
			sig = self.signatures[i]
			id = self.keys[i]
			if self.Text is not None:
				index = self.Text.index(id)
			else: index = ""
			out.append((index,  id, self.dict[sig]))
		for index, id, style in out:
			print index,"\t", id,"\t", style
		print "# of keys = ", len(self.keys)
		print "# of signatures = ", len(self.signatures)

	class Iterator:

		def __init__(self, pool):
			self.pool = pool
			self.i = -1
			self._update()

		def __repr__(self):
			return "Iterator of %s" % repr(self.pool)

		def __str__(self):
			if self.i<0:
				index = "1.0"
			elif self.i>=len(self.pool):
				index = "end"
			else:
				index = self.id
			return str(index)

		def _update(self):
			if self.i >= len(self.pool) or self.i <0:
				self.outofboundary = 1
				self.current = None
				self.id = None
			else:
				self.outofboundary = 0
				self.id = self.pool.keys[self.i]
				sig = self.pool.signatures[self.i]
				self.current = self.pool.dict[sig]

		def next(self):
			if self.i<len(self.pool):
				self.i = self.i+1
				self._update()
			return self.current

		def prev(self):
			if self.i>=0:
				self.i = self.i-1
				self._update()
			return self.current

		def insert_left(self, style, index=None):
			'''inserts stlye before index or if it is not given, after 
			current id'''
			texti = self._textinst()

			if index is None:
				index = self.current
				if index is None:
					raise StyletextError(
							"Can't insert at index: %s" % index)
			it = self.pool.iterator()
			it.before(index)
			it.next()
			it.align_left()

			# case 1: there is no mark before index
			if it.outofboundary:
				i = it.i

			# case 2: there is already a mark at index
			elif texti.compare(it, '==', index):
				it.align_left()
				i = it.i

			# case 3: there is no mark at index, but after index
			else:
				i = it.i
			sig = style._signature_
			id = self.pool.new_id()
			texti.mark_set(id, index)
			texti.mark_gravity(id, 'right')
			self.pool.keys.insert(i, id)
			self.pool.signatures.insert(i, sig)
			self.pool.dict[sig] = style
			self.i = i

			return self._update()

		def insert_right(self, style, index=None):
			'''inserts stlye after index or if it is not given, 
			after current id'''
			texti = self._textinst()

			if index is None:
				index = self.current
				if index is None:
					raise StyletextError(
							"Can't insert at index '%s'" % index)

			it = self.pool.iterator()
			it.after(index)
			it.align_right()

			# case 1: there is no mark at or after index
			if it.outofboundary:
				i = it.i

			# case 2: there is already a mark at index
			elif texti.compare(it, '==', index):
				it.align_right()
				i = it.i+1

			# case 3: there is no mark at index, but after index
			else:
				i = it.i

			sig = style._signature_
			id = self.pool.new_id()
			texti.mark_set(id, index)
			texti.mark_gravity(id, 'right')
			self.pool.keys.insert(i, id)
			self.pool.signatures.insert(i, sig)
			self.pool.dict[sig] = style
			self.i = i
			return self._update()

		def delete(self):
			texti = self._textinst()
			del self.pool.keys[self.i]
			del self.pool.signatures[self.i]
			texti.mark_unset(self.id)
			if self.i>len(self.pool):
				self.i = self.i-1
			self._update()

		def _textinst(self):
			'''Returns pools assigned text instance, error if no Text is
			assigned'''
			if self.pool.Text is None:
				raise StyletextError("pool has no 'text' instance")
			return self.pool.Text

		def guess(self, indexOrId):
			'''finds a style mark which is before indexOrId. Not Necessarily
			the nearest one.
			'''
			if len(self.pool) == 0:
				return  self._update()

			texti = self._textinst()

			# start with a good guess
			index = indexOrId
			while 1:
				mark = texti.mark_previous(index)
				#print "mark = ",mark
				if mark is None or type(mark)=='None':
					# there is no mark before indexorid then
					self.i = -1
					return  self._update()
				if mark[0] == '_':
					id = mark
					break
				index = mark
			i = self.pool.keys.index(id)
			self.i = i
			return self._update()


		def after(self, indexOrId):
			'''finds last stylemark which is at index or, if there is none, 
			the next one'''
			if len(self.pool) == 0:
				return self._update()
			texti = self._textinst()
			it = self.pool.iterator()

			# start with a good guess
			it.guess(indexOrId)
			if it.i<0:
				it.next()

			i = it.i

			# fine tuning
			while texti.compare(self.pool.keys[i],'<', indexOrId):
				i = i+1
				if i>=len(self.pool):
					break
			self.i = i

		def before(self, indexOrId):
			'''finds last style mark which is before indexOrId
			# XXX inconsistent to Tk: previous = next mark bevor or at index

			'''
			if len(self.pool) == 0:
				return  self._update()

			texti = self._textinst()
			it = self.pool.iterator()

			# start with a good guess
			it.guess(indexOrId)
			while (not it.outofboundary) and (texti.compare(it,'>=', \
					indexOrId)):
				it.prev()

			if it.outofboundary:
				self.i = it.i
				return self._update()

			i = it.i
			# now fine tuning
			oi = i
			while texti.compare(self.pool.keys[i], '<',indexOrId):
				#~ print i, "<", texti.index(indexOrId)
				oi = i
				i = i+1
				if i>=len(self.pool):
					break

			# now oi  is at the last stylemark which is before indexOrId
			self.i = oi
			return self._update()

		def set(self, id):
			self.i = self.pool.keys.index(id)
			self._update()
			return current

		def align_left(self):
			if self.outofboundary:
				return self.current
			ids = self.pool.keys
			compare = self._textinst().compare
			i = self.i

			while i>0 and i<len(self.pool) and compare(ids[i-1],'==',ids[i]):
				i = i-1
			self.i = i
			self._update()
			return self.current


		def align_right(self):
			if self.outofboundary:
				return self.current
			ids = self.pool.keys
			compare = self._textinst().compare
			i = self.i
			while i<len(ids)-1 and compare(ids[i],'==',ids[i+1]):
				i = i+1
			self.i = i
			self._update()
			return self.current

		def is_first(self):
			return self.i == 0

		def is_last(self):
			return self.i == len(self.pool)-1

	def iterator(self):
		return Pool.Iterator(pool=self)


if __name__=='__main__':
	from Tkinter import *
	tk = Tk()
	text = Text(tk)
	text.pack()
	for i in range(5):
		text.insert('end', '0123456789\n')
	pool = Pool(text)
	s1 = Style(q=1)
	s2 = Style(w=1)
	s3 = Style(w=1)
	if s2 == s3: print "error"
	if s2 != s3: print "error"
		
	i = pool.iterator()
	i.insert_left(Style(color = "blue"),'1.0')
	i.insert_left(Style(color = "red"),'2.0')
	i.insert_left(Style(color = "green"),'3.0')
	i.insert_left(Style(color = "black"),'1.0')
	i.insert_right(Style(color = "grey"),'1.0')

	pool.dump()
	i.after("1.0")
	print "after 1.0: ",i,i.i
	
	i.after("2.0")
	print "after 2.0: ",i,i.i
