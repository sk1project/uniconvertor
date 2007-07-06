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



from StringIO import StringIO
from re import compile, search

EOF = 'eof'
STYLECHANGE = 'stylechange'

class Chunker:

	def __init__(self, text, styling, sep=()):
		self.styling = styling
		self.text = text
		self.styles = {}
		self.next_styles = {}

		self.i = 0
		self.line = 0
		self.col = 0
		self.pos = 0
		self.next_pos = -1
		self.len = len(text)

		sepstr = ''
		sep = ('\n',)+tuple(sep)
		for s in sep:
			sepstr = sepstr+s
		self.sep_r = compile('[%s]' % sepstr)

	def eof(self):
		return self.pos >= self.len

	def reason(self):
		'''
		Gives the reason for the last break.

		Returns either the separation char if there was one, otherwise
		"eof" or "stylechange"
		'''
		if self.pos >= self.len:
			return EOF
		elif self.pos == self.next_pos+1:
			return self.text[self.next_pos]
		else:
			return STYLECHANGE

	def get(self):
		ret = ''
		opos = self.pos
		while self.pos == opos:
			style, line, col = self.styling[self.i]

			# need to find the next sep ?
			if self.pos >= self.next_pos:
				if self.text[self.next_pos] == '\n':
					self.line = self.line+1
					self.col = 0
				match = self.sep_r.search(self.text, self.next_pos+1)
				if match is None:
					self.next_pos = self.len
				else:
					self.next_pos = match.start(0)

			# need to adjust i ?
			while (self.i<len(self.styling)-1) and \
				((self.line>line) or (self.line==line and self.col>=col)):
					self.i = self.i+1
					self.styles[style.sort] = style
					style, line, col = self.styling[self.i]

			plus = 0
			if self.pos>=self.len:
				return

			elif self.i >=len(self.styling)-1:
				plus = self.next_pos - self.pos

			elif self.line<line:
				plus = self.next_pos - self.pos

			elif self.line == line:
				plus = min(col-self.col, self.next_pos-self.pos)

			ret = self.text[self.pos: self.pos+plus]
			if self.pos+plus == self.next_pos:
				plus = plus+1

			self.col = self.col+plus
			self.pos = self.pos+plus

		return ret, self.styles



if __name__ == '__main__':
	from iterator import Style
	styling = (
		(Style(sorta=1), 0, 0),
		(Style(sortb=8), 0, 0),
		(Style(sortc=9), 0, 0),
		(Style(sortb=1), 3, 2),
		(Style(sorta=2), 3, 11),
		(Style(sorta=3), 4, 0),
		(None, 2,0),
	)

	text = '''\n\nA234567890\nB234567890\nC234567890\tX123''' \
		'''45\tY12345\t\n\t\n'''

	chunker = Chunker(text, styling, '\t')
	while not chunker.eof():
		print ">",repr(chunker.get()), "eof = ",chunker.eof(),  \
			"\t reason = ", repr(chunker.reason())
