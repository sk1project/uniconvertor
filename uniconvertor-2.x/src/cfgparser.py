# -*- coding: utf-8 -*-

# Copyright (C) 2011 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

from uc2 import events

import os, sys, types

from xml.sax import handler
		
class XmlConfigParser:
	
	"""
	Represents parent class for application config.
	"""

	def __setattr__(self, attr, value):
		if not hasattr(self, attr) or getattr(self, attr) != value:
			self.__dict__[attr] = value
			events.emit(events.CONFIG_MODIFIED, attr, value)
			
	def load(self, filename=None):
		import xml.sax
		from xml.sax.xmlreader import InputSource
		
		content_handler = XMLPrefReader(pref=self)
		error_handler = ErrorHandler()
		entity_resolver = EntityResolver()
		dtd_handler = DTDHandler()
		try:
			input = open(filename, "r")
			input_source = InputSource()
			input_source.setByteStream(input)
			xml_reader = xml.sax.make_parser()
			xml_reader.setContentHandler(content_handler)
			xml_reader.setErrorHandler(error_handler)
			xml_reader.setEntityResolver(entity_resolver)
			xml_reader.setDTDHandler(dtd_handler)
			xml_reader.parse(input_source)
			input.close
		except:
			pass

	def save(self, filename=None):
		if len(self.__dict__) == 0 or filename == None:
			return
		from xml.sax.saxutils import XMLGenerator

		try:
			file = open(filename, 'w')
		except (IOError, os.error), value:
			sys.stderr('cannot write preferences into %s: %s' % (`filename`, value[1]))
			return
	
		writer = XMLGenerator(out=file, encoding=self.system_encoding)
		print '=========\n encoding', self.system_encoding
		writer.startDocument()	
		defaults = XmlConfigParser.__dict__
		items = self.__dict__.items()
		items.sort()
		writer.startElement('preferences', {})
		writer.characters('\n')
		for key, value in items:
			if defaults.has_key(key) and defaults[key] == value:
				continue
			writer.characters('	')
			writer.startElement('%s' % key, {})
			print type(value)
			if not type(value) == types.UnicodeType:
				value = '%s' % `value`
			
			print 'WRITTEN:', value
			writer.characters(value)
				
			writer.endElement('%s' % key)
			writer.characters('\n')
		writer.endElement('preferences')
		writer.endDocument()
		file.close
		
class XMLPrefReader(handler.ContentHandler):
	"""Handler for xml file reading"""
	def __init__(self, pref=None):
		self.key = None
		self.value = None
		self.pref = pref

	def startElement(self, name, attrs):
		self.key = name

	def endElement(self, name):
		if name != 'preferences':
			try:
				if self.is_int(self.value):
					self.value = int(self.value)
				elif self.is_float(self.value):
					self.value = float(self.value)									
				self.pref.__dict__[self.key] = self.value
			except Exception:
				print sys.exc_info()[0]


	def characters(self, data):
		self.value = data
		
	def is_int(self, value):
		res = True
		for letter in value:
			if not letter in '0123456789':
				res = False
				break
		return res
	
	def is_float(self, value):
		res = True
		for letter in value:
			if not letter in '.,0123456789':
				res = False
				break
		return res

class ErrorHandler(handler.ErrorHandler): pass
class EntityResolver(handler.EntityResolver): pass
class DTDHandler(handler.DTDHandler): pass