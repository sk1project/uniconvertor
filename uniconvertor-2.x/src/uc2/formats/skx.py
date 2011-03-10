# -*- coding: utf-8 -*-
#
#	Copyright (C) 2011 by Igor E. Novikov
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import zipfile
from zipfile import ZipFile

import xml.sax
from xml.sax.xmlreader import InputSource
from xml.sax import handler

from uc2 import _
from uc2.sk1doc import model
from uc2 import sk1doc
from uc2.utils import fs

from abstract import AbstractLoader, AbstractSaver


IDENT = '\t'

def encode_quotes(line):
	result = line.replace('"', '&quot;')
	result = result.replace("'", "&#039;")
	return result

def decode_quotes(line):
	result = line.replace('&quot;', '"')
	result = result.replace("&#039;", "'")
	return result

def escape_quote(line):
	return line.replace("'", "\\'")



class SKX_Loader(AbstractLoader):
	name = 'SKX_Loader'
	options = {}
	model = None

	def __init__(self):
		AbstractLoader.__init__(self)

	def load(self, presenter, path):
		self.presenter = presenter
		self.path = path

		if not zipfile.is_zipfile(self.path):
			raise IOError(2, _('It seems the file is not SKX file'))

		self._extract_content()
		self._build_model()
		return self.model

	def _extract_content(self):
		skx = ZipFile(self.path, 'r')
		try:
			fl = skx.namelist()
		except:
			errtype, value, traceback = sys.exc_info()
			raise IOError(errtype, _('It seems the SKX file is corrupted') + \
									'\n' + value, traceback)
		if not 'mimetype' in fl or not skx.read('mimetype') == sk1doc.DOC_MIME:
			raise IOError(2, _('The file is corrupted or not SKX file'))

		filelist = []
		for item in fl:
			if item == 'mimetype' or item[-1] == '/':
				continue
			filelist.append(item)

		for item in filelist:
			source = skx.read(item)
			dest = open(os.path.join(self.presenter.doc_dir, item), 'wb')
			dest.write(source)
			dest.close()

	def _build_model(self):
		content_handler = XMLDocReader(self.presenter)
		error_handler = ErrorHandler()
		entity_resolver = EntityResolver()
		dtd_handler = DTDHandler()
		try:
			filename = os.path.join(self.presenter.doc_dir, 'content.xml')
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
		self.model = content_handler.model


class XMLDocReader(handler.ContentHandler):

	def __init__(self, presenter):
		self.model = None
		self.presenter = presenter
		self.parent_stack = []

	def startElement(self, name, attrs):
		if name == 'Content':
			self.parent_stack[-1][1] = True
		else:
			cid = int(attrs._attrs['cid'])
			obj = model.CID_TO_CLASS[cid](self.presenter.config)
			for item in attrs._attrs.keys():
				line = 'self.value=' + attrs._attrs[item]
				code = compile(line, '<string>', 'exec')
				exec code
				obj.__dict__[item] = self.value
				
			if self.parent_stack:
				parent = self.parent_stack[-1][0]
				if self.parent_stack[-1][1]:
					sk1doc.add_child(parent, obj)
				else:
					if model.CID_TO_PROPNAME.has_key(cid):
						parent.__dict__[model.CID_TO_PROPNAME[cid]] = obj
			else:
				self.model = obj

			self.parent_stack.append([obj, False])

	def endElement(self, name):
		if name == 'Content':
			self.parent_stack[-1][1] = False
		else:
			self.parent_stack = self.parent_stack[:-1]

	def characters(self, data):
		pass


class ErrorHandler(handler.ErrorHandler): pass
class EntityResolver(handler.EntityResolver): pass
class DTDHandler(handler.DTDHandler): pass


class SKX_Saver(AbstractSaver):
	name = 'SKX_Saver'
	file = None
	options = {}
	ident = 0
	content = []

	def __init__(self):
		AbstractSaver.__init__(self)

	def save(self, presenter, path):
		self.presenter = presenter
		self.path = path
		self.content = []
		self._save_content()
		self._write_manifest()
		self._pack_content()

	def _save_content(self):
		content_xml = os.path.join(self.presenter.doc_dir, 'content.xml')
		try:
			self.file = open(content_xml, 'wb')
		except:
			errtype, value, traceback = sys.exc_info()
			raise IOError(errtype,
						_('Cannot open %s file for writing') % (content_xml) + \
						'\n' + value, traceback)

		doc = self.presenter.model
		self._start()
		self._write_tree(doc)
		self._finish()

	def _start(self):
		config = self.presenter.config
		ln = '<?xml version="1.0" encoding="%s"?>\n' % (config.system_encoding)
		self.file.write(ln)

	def _write_tree(self, item):
		tag = model.CID_TO_TAGNAME[item.cid]
		params = self._get_params(item)
		self._open_tag(tag, params, item.childs)
		if item.childs:
			self.ident += 1
			self.file.write('%s<Content>\n' % (self.ident * IDENT))
			self.ident += 1
			for child in item.childs:
				self._write_tree(child)
			self.ident -= 1
			self.file.write('%s</Content>\n' % (self.ident * IDENT))
			self.ident -= 1
			self._close_tag(tag)

	def _get_params(self, child):
		result = []
		props = child.__dict__
		items = props.keys()
		items.sort()
		for item in ['cid', 'childs', 'parent', 'config']:
			if item in items:
				items.remove(item)
		items = ['cid'] + items
		for item in items:
			item_str = props[item].__str__()
			if isinstance(props[item], str):
				item_str = "'%s'" % (escape_quote(item_str))
			result.append((item, encode_quotes(item_str)))
		return result

	def _open_tag(self, tag, params, len):
		self.file.write('%s<%s ' % (self.ident * IDENT, tag))
		for item in params:
			param, value = item
			self.file.write('\n%s %s="%s"' % (self.ident * IDENT, param, value))
		if len:
			self.file.write('>\n')
		else:
			self.file.write(' />\n')

	def _close_tag(self, tag):
		self.file.write('%s</%s>\n' % (self.ident * IDENT, tag))

	def _finish(self):
		self.file.close()

	def _write_manifest(self):
		xml = os.path.join(self.presenter.doc_dir, 'META-INF', 'manifest.xml')
		try:
			self.file = open(xml, 'wb')
		except:
			errtype, value, traceback = sys.exc_info()
			raise IOError(errtype,
						_('Cannot open %s file for writing') % (xml) +
						'\n' + value, traceback)
		self._start()
		self.file.write('<manifest>\n')
		self._write_manifest_entries()
		self.file.write('</manifest>\n')
		self._finish()

	def _write_manifest_entries(self):
		content = []

		for path in sk1doc.DOC_STRUCTURE:
			pt = os.path.join(self.presenter.doc_dir, path)
			self.content.append((pt, path + '/'))
			files = fs.get_files(os.path.join(self.presenter.doc_dir, path))
			for file in files:
				filetype = ''
				if os.path.splitext(file)[1] == '.xml':
					filetype = 'text/xml'
				if not path == 'META-INF':
					content.append((filetype, path + '/' + file))
				pt = os.path.join(self.presenter.doc_dir, path, file)
				self.content.append((pt, path + '/' + file))
			if not path == 'META-INF':
				content.append(('', path + '/'))

		pt = os.path.join(self.presenter.doc_dir, 'content.xml')
		self.content.append((pt, 'content.xml'))
		pt = os.path.join(self.presenter.doc_dir, 'mimetype')
		self.content.append((pt, 'mimetype'))

		main = [(sk1doc.DOC_MIME, '/')]
		main += [('text/xml', 'content.xml')]
		content = main + content

		for item in content:
			tp, pt = item
			ln = '\t<file-entry media-type="%s" full-path="%s"/>\n' % (tp, pt)
			self.file.write(ln)


	def _pack_content(self):
		skx = ZipFile(self.presenter.doc_file, 'w')
		for item in self.content:
			path, filename = item
			filename = filename.encode('ascii')
			skx.write(path, filename, zipfile.ZIP_DEFLATED)
		skx.close()

