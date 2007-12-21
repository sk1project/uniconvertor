# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#	Extract character outlines from Type1 font files...
#

import sys
from cStringIO import StringIO
from types import StringType

from string import atoi, split, find, strip

import streamfilter

from app import Point
from app._type1 import decode, hexdecode
from app.pstokenize import PSTokenizer, OPERATOR, NAME, INT, END

def read_type1_file(filename):
	data = StringIO()
	file = open(filename, 'rb')
	head = file.read(6)
	if head[:2] == '%!':
		line = file.readline()
		while line:
			line = file.readline()
			pos = find(line, 'eexec')
			if pos >= 0:
				data.write(line[:pos + 5] + '\n')
				line = line[pos + 5:]
				break
			data.write(line)

		try:
			buf = line + file.read(200)
			buf, extra = hexdecode(buf)
			buf, r = decode(buf, 55665)
			data.write(buf[4:])
			buf = extra + file.read(200)
			while buf:
				buf, extra = hexdecode(buf)
				buf, r = decode(buf, r)
				data.write(buf)
				buf = extra + file.read(200)
		except:
			pass
	else:
		while 1:
			if ord(head[0]) != 128:
				raise TypeError, 'not a pfb file'
			data_type = ord(head[1])
			if data_type == 3:
				# EOF
				break

			data_length = ord(head[2]) + 256 * ord(head[3]) \
							+ 65536 * ord(head[4]) + 16777216 * ord(head[5])
			if data_type == 1: # ASCII
				data.write(file.read(data_length))
			elif data_type == 2: #Binary
				# decode and discard the first 4 bytes
				buf = file.read(4)
				if len(buf) < 4:
					raise IOError, "insufficient data"
				buf, r = decode(buf, 55665)
				data_length = data_length - 4
				if data_length < 0:
					raise IOError, "invalid data"
				while data_length:
					buf = file.read(min(1000, data_length))
					if not buf:
						raise IOError, "insufficient data"
					buf, r = decode(buf, r)
					data.write(buf)
					data_length = data_length - len(buf)
			else:
				raise RuntimeError, "Invalid data type"
			head = file.read(6)


	data = data.getvalue()
	return data

def parse_type1_file(data):
	subrs = char_strings = None
	tokenizer = PSTokenizer(data)
	next = tokenizer.next
	
	while 1:
		token, value = next()
		if token == NAME:
			if value == 'Subrs':
				token, value = next()
				if token == INT:
					subrs = read_subrs(tokenizer, value)
			elif value == 'CharStrings':
				char_strings = read_char_strings(tokenizer)
				if subrs is not None:
					break
		elif token == END:
			break

	return subrs, char_strings


def read_subrs(tokenizer, num):
	subrs = [''] * num
	next = tokenizer.next
	read = tokenizer.read
	
	while not subrs[-1]:
		token, value = next()
		if token == OPERATOR and value == 'dup':
			token, index = next()
			token, length = next()
			next() # discard RD operator
			read(1) # discard space character
			data = read(length)
			subrs[index] = decode(data)[0][4:] 
		elif token == END:
			break
	return subrs


def read_char_strings(tokenizer):
	char_strings = {}
	next = tokenizer.next
	read = tokenizer.read

	while 1:
		token, value = next()
		if token == NAME:
			token, length = next()
			next() # discard RD operator
			read(1) # discard space character
			data = read(length)
			char_strings[value] = decode(data)[0][4:]
		elif token == END or (token == OPERATOR and value == 'end'):
			break

	return char_strings

class SubrReturn(Exception):
	pass


class CharStringInterpreter:

	commands = {}

	def __init__(self, subrs):
		self.subrs = subrs
		self.reset()

	def print_path(self):
		for closed, path in self.paths:
			if closed:
				print 'closed:'
			else:
				print 'open:'
			for part in path:
				print part

	def reset(self):
		self.stack = []
		self.ps_stack = []
		self.paths = ()
		self.path = []
		self.closed = 0
		self.in_flex = 0
		self.flex = []
		self.cur = Point(0, 0)

	def execute(self, cs):
		stack = self.stack
		cs = map(ord, cs)
		try:
			while cs:
				code = cs[0]; del cs[0]
				if code >= 32:
					if code <= 246:
						stack.append(code - 139)
					elif code <= 250:
						stack.append((code - 247) * 256 + cs[0] + 108)
						del cs[0]
					elif code <= 254:
						stack.append(-(code - 251) * 256 - cs[0] - 108)
						del cs[0]
					else:
						stack.append(cs[0] * 0x01000000 + cs[1] * 0x10000
										+ cs[2] * 0x100 + cs[3])
						del cs[:4]
				else:
					if code == 12:
						code = 32 + cs[0]
						del cs[0]
					cmd = self.commands[code]
					if cmd:
						cmd(self)
		except SubrReturn:
			return

	def new_path(self):
		if self.path:
			self.paths = self.paths + ((self.closed, self.path),)
			self.path = []
			self.closed = 0

	def flush_stack(self, *rest):
		del self.stack[:]

	commands[32 + 0] = flush_stack	# dotsection
	commands[1]	     = flush_stack	# hstem
	commands[32 + 2] = flush_stack	# hstem3
	commands[3]	     = flush_stack	# vstem
	commands[32 + 1] = flush_stack	# vstem3

	def pop(self, n):
		result = self.stack[-n:]
		del self.stack[-n:]
		if n == 1:
			return result[0]
		return result

	def pop_all(self):
		result = self.stack[:]
		del self.stack[:]
		if len(result) == 1:
			return result[0]
		return result

	def endchar(self):
		self.new_path()
		self.flush_stack()
	commands[14] = endchar

	def hsbw(self):
		# horizontal sidebearing and width
		sbx, wx = self.pop_all()
		self.cur = Point(sbx, 0)
	commands[13] = hsbw

	def seac(self):
		# standard encoding accented character
		asb, adx, ady, bchar, achar = self.pop_all()
	commands[32 + 6] = seac

	def sbw(self):
		# sidebearing and width
		sbx, sby, wx, wy = self.pop_all()
		self.cur = Point(sbx, sby)
	commands[32 + 7] = sbw

	def closepath(self):
		self.pop_all()
		self.closed = 1
	commands[9] = closepath

	def rlineto(self):
		dx, dy = self.pop_all()
		self.cur = self.cur + Point(dx, dy)
		self.path.append(tuple(self.cur))
	commands[5] = rlineto

	def hlineto(self):
		dx = self.pop_all()
		self.cur = self.cur + Point(dx, 0)
		self.path.append(tuple(self.cur))
	commands[6] = hlineto

	def vlineto(self):
		dy = self.pop_all()
		self.cur = self.cur + Point(0, dy)
		self.path.append(tuple(self.cur))
	commands[7] = vlineto

	def rmoveto(self):
		dx, dy = self.pop_all()
		self.cur = self.cur + Point(dx, dy)
		if self.in_flex:
			self.flex.append(self.cur)
		else:
			self.new_path()
			self.path.append(tuple(self.cur))
	commands[21] = rmoveto

	def hmoveto(self):
		dx = self.pop_all()
		self.cur = self.cur + Point(dx, 0)
		self.new_path()
		self.path.append(tuple(self.cur))
	commands[22] = hmoveto

	def vmoveto(self):
		dy = self.pop_all()
		self.cur = self.cur + Point(0, dy)
		self.new_path()
		self.path.append(tuple(self.cur))
	commands[4] = vmoveto

	def rrcurveto(self):
		dx1, dy1, dx2, dy2, dx3, dy3 = self.pop_all()
		d1 = self.cur + Point(dx1, dy1)
		d2 = d1 + Point(dx2, dy2)
		d3 = d2 + Point(dx3, dy3)
		self.cur = d3
		self.path.append(tuple(d1) +tuple(d2) + tuple(d3))
	commands[8] = rrcurveto

	def hvcurveto(self):
		dx1, dx2, dy2, dy3 = self.pop_all()
		d1 = self.cur + Point(dx1, 0)
		d2 = d1 + Point(dx2, dy2)
		d3 = d2 + Point(0, dy3)
		self.cur = d3
		self.path.append(tuple(d1) + tuple(d2) + tuple(d3))
	commands[31] = hvcurveto

	def vhcurveto(self):
		dy1, dx2, dy2, dx3 = self.pop_all()
		d1 = self.cur + Point(0, dy1)
		d2 = d1 + Point(dx2, dy2)
		d3 = d2 + Point(dx3, 0)
		self.cur = d3
		self.path.append(tuple(d1) + tuple(d2) + tuple(d3))
	commands[30] = vhcurveto

	def start_flex(self):
		print 'start_flex'
		self.in_flex = 1
		self.flex = []

	def end_flex(self):
		print 'end_flex'
		size, x, y = self.pop_all()
		d1, d2, d3 = self.flex[1:4]
		self.path.append(tuple(d1) + tuple(d2) + tuple(d3))
		d1, d2, d3 = self.flex[4:7]
		self.path.append(tuple(d1) + tuple(d2) + tuple(d3))

	def div(self):
		num1, num2 = self.pop(2)
		self.stack.append(float(num1) / num2)
	commands[32 + 12] = div

	def callothersubr(self):
		n, sn = self.pop(2)
		if n:
			self.ps_stack = self.pop(n)
		if sn == 3:
			self.ps_stack = [3]
	commands[32 + 16] = callothersubr

	def callsubr(self):
		num = self.pop(1)
		if num == 0:
			self.end_flex()
		elif num == 1:
			self.start_flex()
		elif 2 <= num <= 3:
			return
		self.execute(self.subrs[num])
	commands[10] = callsubr

	def pop_ps(self):
		value = self.ps_stack[-1]
		del self.ps_stack[-1]
		self.stack.append(value)
	commands[32 + 17] = pop_ps

	def subr_return(self):
		raise SubrReturn
	commands[11] = subr_return

	def setcurrentpoint(self):
		x, y = self.pop_all()
		self.cur = Point(x, y)
	commands[32 + 33] = setcurrentpoint



#
# read_outlines(FILENAME)
#
# Return the outlines of the glyphs in the Type1 font stored in the file
# FILENAME as a tuple (CHAR_STRINGS, INTERPRETER). CHAR_STRINGS is a
# dictionary mapping glyph names to strings containing the outline
# description, INTERPRETER is an instance of CharStringInterpreter
# initialized with the appropriate Subrs.
def read_outlines(filename):
	data = read_type1_file(filename)
	data = streamfilter.StringDecode(data, None)
	subrs, char_strings = parse_type1_file(data)
	interpreter = CharStringInterpreter(subrs)
	return char_strings, interpreter






def embed_type1_file(fontfile, outfile):
	if type(fontfile) == StringType:
		file = open(filename, 'rb')
	else:
		file = fontfile
	head = file.read(6)
	if head[:2] == '%!':
		# PFA
		outfile.write(head)
		data = file.read(4000)
		while data:
			outfile.write(data)
			data = file.read(4000)
	else:
		# Probably PFB
		while 1: # loop over all chunks
			if ord(head[0]) != 128:
				raise TypeError, 'not a pfb file'
			data_type = ord(head[1])
			if data_type == 3:
				# EOF
				break

			data_length = ord(head[2]) + 256 * ord(head[3]) \
							+ 65536 * ord(head[4]) + 16777216 * ord(head[5])
			if data_type == 1: # ASCII
				outfile.write(file.read(data_length))
			elif data_type == 2: #Binary
				# Hex encode data
				encoder = streamfilter.HexEncode(outfile)
				while data_length:
					if data_length > 4000:
						length = 4000
					else:
						length = data_length
					data = file.read(length)
					encoder.write(data)
					data_length = data_length - length
				encoder.close()
			head = file.read(6)


#
#	some test functions...
#

def test():
	filename = sys.argv[1]
	data = read_type1_file(filename)
	data = streamfilter.StringDecode(data, None)
	subrs, char_strings = parse_type1_file(data)
	items = char_strings.items()
	items.sort()
	interpreter = CharStringInterpreter(subrs)
	for name, code in items:
		print name, `code`
		interpreter.execute(code)
		interpreter.print_path()
		interpreter.reset()

if __name__ == '__main__':
	test()
