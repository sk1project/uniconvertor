# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 2000 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


# A simple parser for PostScript files that conform to the Document
# Structuring Conventions (DSC).
#
# In its current form this is mainly intended for parsing EPS files and
# extract the information necessary for Sketch (BoundingBox and resource
# dependencies)
#

import re, string
from string import split, strip, atof

import streamfilter

try:
	from app.events.warn import warn, INTERNAL
except ImportError:
	def warn(*args):
		pass
	INTERNAL = None

# match a line containing a DSC-comment.
rx_dsccomment = re.compile('^%%([a-zA-Z+]+):?')

# match the beginning of an EPS file.
rx_eps_magic = re.compile('^%!.*EPSF')

endcommentchars = string.maketrans('','')[33:127]
ATEND = '(atend)'


class DSCError(Exception):
	pass


#
# Class EpsInfo
#
# The instance variables of this class are the key/value pairs extracted
# from the header comments of an EPS file.
#
# BoundingBox:
#
#	The bounding box of the document as a 4-tuple of floats. The DSC
#	say that the BoundingBox should be given in UINTs but since some
#	programs (incorrectly) use floats here we also use float here.
#
# DocumentNeededResources:
#
#	A dictionary describing the resources needed by the document.
#	The information is stored in the *keys* of the dictionary.
#
#	A key has the form (TYPE, VALUE) where TYPE is a string giving
#	the resource type (such as 'font') and value is a string
#	describing the resource (such as 'Times-Roman')
#
# DocumentSuppliedResources:
#
#	The resources supplied by the document in the same format as
#	DocumentNeededResources.
#
# atend:
#
#	True, if any comment in the header had a value of `(atend)'.
#	(Used internally by the parsing functions)

class EpsInfo:

	def __init__(self):
		self.DocumentSuppliedResources = {}
		self.DocumentNeededResources   = {}
		self.BoundingBox = None
		self.atend = 0

	def NeedResources(self, type, resources):
		for res in resources:
			self.DocumentNeededResources[(type, res)] = 1

	def SupplyResources(self, type, resources):
		for res in resources:
			self.DocumentSuppliedResources[(type, res)] = 1

	def print_info(self):
		# print the contents of self in a readable manner. (for debugging)
		print 'BoundingBox:\t%s' % `self.BoundingBox`
		print 'DocumentNeededResources: [',
		for res in self.DocumentNeededResources.keys():
			print res,
		print ']'
		print 'DocumentSuppliedResources: [',
		for res in self.DocumentSuppliedResources.keys():
			print res,
		print ']'

		for key, value in self.__dict__.items():
			if key not in ('BoundingBox', 'DocumentNeededResources',
							'DocumentSuppliedResources', 'atend'):
				print '%s\t%s' % (key, value)

def IsEpsFileStart(data):
	# return true if data might be the beginning of an Encapsulated
	# PostScript file.
	return rx_eps_magic.match(data)


def parse_header(file, info):
	# Parse the header section of FILE and store the information found
	# in the INFO object which is assumed to be an instance of EpsInfo.
	#
	# This works for the %%Trailer section as well so that parsing the
	# beginning (until %%EndComments) and end (from %%Trailer) if
	# necessary with the same INFO object should get all information
	# available.
	line = file.readline()
	last_key = ''
	while line:
		match = rx_dsccomment.match(line)
		if match:
			key = match.group(1)
			value = strip(line[match.end(0):])
			if key == 'EndComments' or key == 'EOF':
				break

			if key == '+':
				key = last_key
			else:
				last_key = ''

			if key == 'BoundingBox':
				if value != ATEND:
					# the bounding box should be given in UINTs
					# but may also (incorrectly) be float.
					info.BoundingBox = tuple(map(atof, split(value)))
				else:
					info.atend = 1
			elif key == 'DocumentNeededResources':
				if value != ATEND:
					if value:
						[type, value] = split(value, None, 1)
						if type == 'font':
							info.NeedResources(type, split(value))
						else:
							# XXX: might occasionally be interesting for the
							# user
							warn(INTERNAL, 'needed resource %s %s ignored',
									type, value)
				else:
					info.atend = 1
			elif key == 'DocumentNeededFonts':
				if value != ATEND:
					info.NeedResources('font', split(value))
				else:
					info.atend = 1
			elif key == 'DocumentSuppliedResources':
				if value != ATEND:
					if value:
						[type, value] = split(value, None, 1)
						if type == 'font':
							info.NeedResources(type, split(value))
						else:
							# XXX: might occasionally be interesting for the
							# user
							warn(INTERNAL, 'supplied resource %s %s ignored',
									type, value)
				else:
					info.atend = 1
			else:
				setattr(info, key, value)
			#
			last_key = key
		else:
			# the header comments end at a line not beginning with %X,
			# where X is a printable character not in SPACE, TAB, NL
			# XXX: It is probably wrong to do this in the %%Trailer
			if line[0] != '%':
				break
			if len(line) == 1 or line[1] not in endcommentchars:
				break
		line = file.readline()

def skip_to_comment(file, comment):
	# Read lines from FILE until a line with a DSC comment COMMENT is
	# found. Handles (it should at least) (binary) data and embedded
	# documents correctly (i.e. isn't confused by embedded documents
	# containing COMMENT as well, if they are enclosed in
	# Begin/EndDocument comments).
	#
	# The file is positioned right after the line containing the
	# comment. Raise a DSCError if the comment is not found
	line = file.readline()
	while line:
		match = rx_dsccomment.match(line)
		if match:
			key = match.group(1)
			if key == comment:
				return
			elif key == 'BeginDocument':
				# skip embedded document
				skip_to_comment(file, 'EndDocument')
			elif key == 'BeginData':
				value = split(strip(line[match.end(0):]))
				lines = 0
				if len(value) >= 1:
					count = atoi(value)
					if len(value) == 3:
						lines = value[2] == 'Lines'
				else:
					# should never happen in a conforming document...
					count = 0
				if count > 0:
					if lines:
						for i in range(count):
							file.readline()
					else:
						blocksize = 4000
						while count:
							if count > blocksize:
								count = count - len(file.read(blocksize))
							else:
								count = count - len(file.read(count))
		line = file.readline()

	else:
		raise DSCError('DSC-Comment %s not found' % comment)



def parse_eps_file(filename):
	# Extract information from the EPS file FILENAME. Return an instance
	# of EpsInfo with the appropriate parameters. Raise a DSCError, if
	# the file is not an EPS file.
	file = streamfilter.LineDecode(open(filename, 'r'))
	line = file.readline()
	info = EpsInfo()

	if IsEpsFileStart(line):
		parse_header(file, info)
		if info.atend:
			skip_to_comment(file, 'Trailer')
			parse_header(file, info)
	else:
		raise DSCError('%s is not an EPS file' % filename)

	file.close()

	return info



#
#
#

if __name__ == '__main__':
	import sys
	file = open(sys.argv[1], 'r')
	info = EpsInfo()

	parse_header(file, info)
	if info.atend:
		skip_to_comment(file, 'Trailer')
		parse_header(file, info)

	file.close()

	info.print_info()
