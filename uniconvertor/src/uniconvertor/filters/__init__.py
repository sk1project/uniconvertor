# -*- coding: utf-8 -*-

# Copyright (C) 2003-2010 by Igor E. Novikov
# Copyright (C) 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

import sys, os

import re, imp
from string import join, split

from app.events.skexceptions import SketchError
from app.events.warn import warn_tb, warn, USER, INTERNAL, pdebug

from app import message_dir, Subscribe, config, const


def gettext(text):
	return text
def dgettext(domain, text):
	return text
def bindtextdomain(*args):
	pass
_ = gettext

# All plugins are loaded as modules in the _plugin_package_name package
# to keep the namespaces clean
_plugin_package_name = "app.filters"

import_dir = os.path.join(__path__[0], 'import')
export_dir = os.path.join(__path__[0], 'export')
parsing_dir = os.path.join(__path__[0], 'parsing')
preview_dir = os.path.join(__path__[0], 'preview')


def create_packages(package):
	"""
	Return the package's module and create it and it's parents if necessary
	"""
	names = split(package, '.')
	for i in range(1, len(names) + 1):
		name = join(names[:i], '.')
		if not sys.modules.has_key(name):
			module = imp.new_module(name)
			module.__path__ = []
			sys.modules[name] = module
	return sys.modules[name]

class ConfigInfo:

	module = None
	package = _plugin_package_name

	def __init__(self, module_name, dir, version = '1.0.0', unload = None,
					load_immediately = 0, standard_messages = 0):
		self.module_name = module_name
		self.dir = dir
		self.unload = unload
		self.load_immediately = load_immediately
		self.version = version
		self.plugin_list.append(self)
		self.standard_messages = standard_messages
		if not self.standard_messages:
			bindtextdomain(self.module_name, message_dir)

		if self.load_immediately:
			self.load_module()

	def load_module(self):
		if self.module is not None:
			return self.module
		try:
			file, filename, desc = imp.find_module(self.module_name, [self.dir])
		except:
			warn_tb(INTERNAL, 'Cannot find plugin module %s', self.module_name)
			return None
		try:
			try:
				create_packages(self.package)
				module_name = self.package + '.' + self.module_name
				self.module = imp.load_module(module_name, file, filename,
												desc)
			except:
				warn_tb(USER, _("Cannot load plugin module %s"),
						self.module_name)
				raise
		finally:
			if file is not None:
				file.close()
		self.module._ = self.nls_function()
		return self.module

	def UnloadPlugin(self):
		if self.unload:
			module_name = self.package + '.' + self.module_name
			try:
				module = sys.modules[module_name]
			except KeyError:
				# might happen if the module wasn't even loaded
				return
			self.module = None
			if type(self.unload) == type(""):
				getattr(module, self.unload)(module)
			else:
				name = module.__name__
				module.__dict__.clear()
				del sys.modules[name]

	def nls_function(self):
		if self.standard_messages:
			_ = gettext
		else:
			domain = self.module_name
			def _(text, domain = domain):
				#print domain, text
				result = dgettext(domain, text)
				#print '->', result
				return result
		return _

	def gettext(self, text):
		if self.standard_messages:
			return gettext(text)
		else:
			return dgettext(self.module_name, text)


NativeFormat = 'sK1'

import_plugins = []

class ImportInfo(ConfigInfo):

	plugin_list = import_plugins

	def __init__(self, module_name, dir, rx_magic, class_name, format_name,
					tk_file_type = (), version = '1.0.0', unload = None,
					load_immediately = 0, standard_messages = 0):
		ConfigInfo.__init__(self, module_name, dir, version = version,
							unload = unload,
							load_immediately = load_immediately,
							standard_messages = standard_messages)
		self.rx_magic = re.compile(rx_magic)
		self.class_name = class_name
		self.format_name = format_name
		self.tk_file_type = tk_file_type
		self.translate()

	def translate(self):
		name, ext = self.tk_file_type
		name = self.gettext(name)
		self.tk_file_type = name, ext

	def __call__(self, *args, **kw):
		try:
			module = self.load_module()
			if module is not None:
				return apply(getattr(module, self.class_name), args, kw)
		except:
			warn_tb(INTERNAL, 'When importing plugin %s', self.module_name)
			raise SketchError('Cannot load filter %(name)s.%(message)s'
								% {'name':self.module_name,
									'message':self.class_name})

	def UnloadPlugin(self):
		if config.preferences.unload_import_filters:
			ConfigInfo.UnloadPlugin(self)

export_plugins = []
export_formats = {}

class ExportInfo(ConfigInfo):

	plugin_list = export_plugins

	def __init__(self, module_name, dir, format_name, tk_file_type = (),
					extensions = (), version = '1.0.0', unload = None,
					load_immediately = 0, standard_messages = 0):
		ConfigInfo.__init__(self, module_name, dir, version = version,
							unload = unload,
							load_immediately = load_immediately,
							standard_messages = standard_messages)
		self.format_name = format_name
		self.tk_file_type = tk_file_type
		if type(extensions) != type(()):
			extensions = (extensions,)
		self.extensions = extensions
		export_formats[format_name] = self

	def translate(self):
		name, ext = self.tk_file_type
		name = self.gettext(name)
		self.tk_file_type = name, ext

	def __call__(self, document, filename, file = None, options = None):
		if options is None:
			options = {}
		try:
			module = self.load_module()
		except:
			warn_tb(INTERNAL, 'When importing plugin %s', self.module_name)
			raise SketchError(_("Cannot load filter %(name)s")
								% {'name':self.module_name})
		if file is None:
			file = open(filename, 'wb')
			close = 1
		else:
			close = 0
		if module is not None:
			module.save(document, file, filename, options)
		if close:
			file.close()
		if self.format_name == NativeFormat:
			document.ClearEdited()
		self.UnloadPlugin()

	def UnloadPlugin(self):
		if config.preferences.unload_import_filters:
			ConfigInfo.UnloadPlugin(self)

object_plugins = {}
compound_plugins = []
class PluginCompoundInfo(ConfigInfo):

	plugin_list = compound_plugins

	def __init__(self, module_name, dir, class_name, menu_text, factory = '',
					version = '1.0.0', parameters = (), uses_selection = 0,
					custom_dialog = '', load_immediately = 0,
					standard_messages = 0):
		ConfigInfo.__init__(self, module_name, dir, version = version,
							load_immediately = load_immediately,
							standard_messages = standard_messages)
		self.class_name = class_name
		self.factory = factory
		self.menu_text = menu_text
		self.parameters = parameters
		self.uses_selection = uses_selection
		self.custom_dialog = custom_dialog
		object_plugins[class_name] = self
		self.translate()

	def translate(self):
		gettext = self.gettext
		self.menu_text = gettext(self.menu_text)
		parameters = []
		for parameter in self.parameters:
			parameters.append(parameter[:-1] + (gettext(parameter[-1]),))
		self.parameters = parameters

	def load_module_attr(self, attr):
		try:
			module = self.load_module()
			if module is not None:
				return getattr(module, attr)
		except:
			warn_tb(INTERNAL, 'When importing plugin %s', self.module_name)
			raise SketchError(_("Cannot load plugin %(name)s.%(attr)s")
								% {'name':self.module_name, 'attr':attr})

	def Constructor(self):
		return self.load_module_attr(self.class_name)

	def CallFactory(self, *args, **kw):
		if self.factory:
			attr = self.factory
		else:
			attr = self.class_name
		return apply(self.load_module_attr(attr), args, kw)

	__call__ = CallFactory

	def HasParameters(self):
		return len(self.parameters)

	def UsesSelection(self):
		return self.uses_selection

	def HasCustomDialog(self):
		return self.custom_dialog

	def CreateCustomDialog(self, root, mainwindow, document):
		dialog = self.load_module_attr(self.custom_dialog)
		return dialog(root, mainwindow, document)

def find_object_plugin(name):
	return object_plugins.get(name)



parsing_plugins = []

class ParsingInfo(ConfigInfo):

	plugin_list = parsing_plugins

	def __init__(self, module_name, dir, rx_magic, class_name, format_name,
					tk_file_type = (), version = '1.0.0', unload = None,
					load_immediately = 0, standard_messages = 0):
		ConfigInfo.__init__(self, module_name, dir, version = version,
							unload = unload,
							load_immediately = load_immediately,
							standard_messages = standard_messages)
		self.rx_magic = re.compile(rx_magic)
		self.class_name = class_name
		self.format_name = format_name
		self.tk_file_type = tk_file_type
		self.translate()

	def translate(self):
		name, ext = self.tk_file_type
		name = self.gettext(name)
		self.tk_file_type = name, ext

	def __call__(self, *args, **kw):
		try:
			module = self.load_module()
			if module is not None:
				return apply(getattr(module, self.class_name), args, kw)
		except:
			warn_tb(INTERNAL, 'When analysing plugin %s', self.module_name)
			raise SketchError('Cannot load filter %(name)s.%(message)s'
								% {'name':self.module_name,
									'message':self.class_name})

	def UnloadPlugin(self):
		ConfigInfo.UnloadPlugin(self)



config_types = {'Import': ImportInfo,
				'Export': ExportInfo,
				'Parsing': ParsingInfo,
				'PluginCompound': PluginCompoundInfo
				}


def extract_cfg(file):
	rx_start = re.compile('^###Sketch[ \t]+Config')
	rx_end = re.compile('^###End')
	file = open(file, 'r')
	cfg = []
	for line in file.readlines():
		if rx_end.match(line):
			break
		elif cfg or rx_start.match(line):
			if line[0] == '#':
				line = line[1:]
			if line[-2] == '\\':
				line = line[:-2]
			cfg.append(line)
	return join(cfg, '')



def _search_dir(dir, recurse, package = _plugin_package_name):
	try:
		files = os.listdir(dir)
	except os.error, value:
		warn(USER, _("Cannot list directory %(filename)s\n%(message)s"),
				filename = dir, message = value[1])
		return
	for file in files:
		filename = os.path.join(dir, file)
		if os.path.isdir(filename):
			if file == "Lib":
				# A Lib directory on the plugin path. It's assumed to
				# hold library files for some plugin. Append it to the
				# current package's .Lib package's __path__ so that it's
				# modules can be imported by prefixing their names with
				# Lib.
				lib_pkg = create_packages(package + '.Lib')
				lib_pkg.__path__.append(filename)
			elif recurse:
				# an ordinary directory and we should recurse into it to
				# find more modules, so do that.
				_search_dir(filename, recurse - 1, package + '.' + file)
		elif filename[-3:] == '.py':
			try:
				module_name = os.path.splitext(os.path.basename(filename))[0]
				vars = {'_':_}	# hack
				cfg = extract_cfg(filename)
				exec cfg in config_types, vars
				infoclass = vars.get('type')
				if infoclass is None:
					warn(USER, _("No plugin-type information in %(filename)s"),
							filename = filename)
				else:
					del vars['type']
					del vars['_']
					info = apply(infoclass, (module_name, dir), vars)
					info.package = package
			except:
				warn_tb(INTERNAL, 'In config file %s', filename)
				warn(USER, _("can't read configuration information from "
								"%(filename)s"),
						filename =	 filename)
				


def find_export_plugin(name):
	return export_formats.get(name)

def guess_export_plugin(extension):
	for plugin in export_plugins:
		if extension in plugin.extensions:
			return plugin.format_name
	return ''

def load_plugin_configuration(): #path):
	if __debug__:
		import time
		start = time.clock()
	path = [import_dir, export_dir, parsing_dir]#, preview_dir]
	for dir in path:
		# XXX unix specific
		if len(dir) >= 2 and dir[-1] == '/':
			if dir[-2] == '/':
				recurse = -1
			else:
				recurse = 1
		else:
			recurse = 0
		_search_dir(dir, recurse)
	if __debug__:
		pdebug('timing', 'time to scan cfg files: %g', time.clock()-start)
	# rearrange import plugins to ensure that native format is first
	for loader in import_plugins:
		if loader.format_name == NativeFormat:
			import_plugins.remove(loader)
			import_plugins.insert(0, loader)


Subscribe(const.INITIALIZE, load_plugin_configuration)
