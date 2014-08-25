# -*- coding: utf-8 -*-

# Copyright (C) 2003-2010 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2002, 2003 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#	File system related functions used in various places...
#

import os, string, re, stat, system


# Return the value of the environment variable S if present, None
# otherwise. In Python 1.5 one might use os.environ.get(S) instead...
def getenv(s):
	if os.environ.has_key(s):
		return os.environ[s]
	return None

#Return directory list for provided path

def get_dirs(path='.'):
	list=[]
	if path:
		if os.path.isdir(path):
			try:
				names = os.listdir(path)
			except os.error:
				return []
		names.sort()
		for name in names:
			if os.path.isdir(os.path.join(path, name)):
				list.append(name)
		return list
	
def get_dirs_withpath(path='.'):
	list=[]
	names=[]
	if os.path.isdir(path):
		try:
			names = os.listdir(path)
		except os.error:
			return names
	names.sort()
	for name in names:
		if os.path.isdir(os.path.join(path, name)) and not name=='.svn':
			list.append(os.path.join(path, name))
	return list

#Return file list for provided path
def get_files(path='.', ext='*'):	
	list=[]
	if path:
		if os.path.isdir(path):
			try:
				names = os.listdir(path)
			except os.error:
				return []
		names.sort()
		for name in names:
			if not os.path.isdir(os.path.join(path, name)):
				if ext=='*':
					list.append(name)
				elif '.'+ext==name[-1*(len(ext)+1):]:
					list.append(name)				
	return list

#Return full file names list for provided path
def get_files_withpath(path='.', ext='*'):
	import glob
	list = glob.glob(os.path.join(path, "*."+ext))
	list.sort()
	result=[]
	for file in list:
		if os.path.isfile(file):
			result.append(file)
	return result

#Return recursive directories list for provided path
def get_dirs_tree(path='.'):
	tree=get_dirs_withpath(path)
	res=[]+tree
	for node in tree:
		subtree=get_dirs_tree(node)
		res+=subtree
	return res		
	
#Return recursive files list for provided path
def get_files_tree(path='.', ext='*'):
	tree=[]
	dirs=[path,]	
	dirs+=get_dirs_tree(path)
	for dir in dirs:
		list = get_files_withpath(dir,ext)
		list.sort()
		tree+=list
	return tree


class BackupError(Exception):
	"""
	The class represents BackupError exception.
	"""
	def __init__(self, errno, strerror, filename = ''):
		self.errno = errno
		self.strerror = strerror
		self.filename = filename

def make_backup(filename):
	"""
	The function makes a backup of FILENAME if it exists by renaming it to its
	backupname (suffix ~ is appended).
	
	On error throws BackupError exception.
	"""
	if os.path.isfile(filename):
		backupname = filename + '~'
		try:
			os.rename(filename, backupname)
		except os.error, value:
			raise BackupError(value[0], value[1], backupname)

def gethome():
	"""
	The function returns the user's home directory.
	"""
	return os.path.expanduser('~')
	
#
#	Filename manipulation
#

def commonbasedir(path1, path2):
	"""
	The functions return the longest common prefix of path1 and path2 that is a
	directory.
	"""
	if path1[-1] != os.sep:
		path1 = path1 + os.sep
	return os.path.split(os.path.commonprefix([path1, path2]))[0]


def relpath(path1, path2):
	"""
	The function returns the absolute path PATH2 as a path relative to the directory
	PATH1. PATH1 must be an absolute filename. If commonbasedir(PATH1,
	PATH2) is '/', return PATH2. Doesn't take symbolic links into
	account...
	"""
	if not os.path.isabs(path2):
		return path2
	basedir = commonbasedir(path1, path2)
	if basedir == os.sep:
		return path2
	path2 = path2[len(basedir) + 1 : ]
	curbase = path1
	while curbase != basedir:
		curbase = os.path.split(curbase)[0]
		path2 = os.pardir + os.sep + path2
	return path2


def find_in_path(paths, file):
	"""
	The function finds a file FILE in one of the directories listed in PATHS. If a file
	is found, return its full name, None otherwise.
	"""
	for path in paths:
		fullname = os.path.join(path, file)
		if os.path.isfile(fullname):
			return fullname

 
def find_files_in_path(paths, files):
	"""
	The function finds one of the files listed in FILES in one of the directories in
	PATHS. Return the name of the first one found, None if no file is
	found.
	"""
	for path in paths:
		for file in files:
			fullname = os.path.join(path, file)
			if os.path.isfile(fullname):
				return fullname


def create_directory(dir):
	"""
	The function creates directory dir and its parent dirs when necessary
	"""
	if os.path.isdir(dir):
		return

	parent, base = os.path.split(dir)
	create_directory(parent)
	os.mkdir(dir, 0777)
	
def get_system_fontdirs():
	"""
	The function detects system font directories according to detected 
	system type.
	"""
	if system.get_os_family()==system.LINUX:
		return ['/usr/share/fonts', os.path.join(gethome(),'.fonts')]
	if  system.get_os_family()==system.WINDOWS:
		try:
			import _winreg
		except ImportError:
			return [os.path.join(os.environ['WINDIR'], 'Fonts'),]
		else:
			k = _winreg.OpenKey(
				_winreg.HKEY_CURRENT_USER,
				r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
			)
			try:
				return [_winreg.QueryValueEx( k, "Fonts" )[0],]
			finally:
				_winreg.CloseKey( k )
	if system.get_os_family()==system.MACOSX:
		#FIXME: It's a stub. The paths should be more exact.
		return ['/',]


DIRECTORY_OBJECT=0
FILE_OBJECT=1
UNKNOWN_OBJECT=2

REGULAR_OBJECT=0
LINK_OBJECT=1

class FileObject:
	"""
	The class represents file system object in UNIX-like style ('all are files').
	"""
	type=FILE_OBJECT
	is_link=REGULAR_OBJECT
	is_hidden=0
	ext=''
	name=''
	basename=''
	
	def __init__(self,path):
		self.path=path
		if os.path.isdir(self.path):
			self.type=DIRECTORY_OBJECT
		elif os.path.isfile(self.path):
			self.type=FILE_OBJECT
		else:
			self.type=UNKNOWN_OBJECT
			
		if os.path.islink(self.path):
			self.is_link=LINK_OBJECT
			
		self.basename=os.path.basename(self.path)
		
		if not system.get_os_family()==system.WINDOWS:	
			if self.basename[0]=='.':
				self.is_hidden=1	
						
		if self.type:
			if self.is_hidden:
				self.ext=os.path.splitext(self.basename[1:])[1][1:]
				self.name=os.path.splitext(self.basename[1:])[0]
			else:		
				self.ext=os.path.splitext(self.basename)[1][1:]
				self.name=os.path.splitext(self.basename)[0]
		else:
			self.name=os.path.basename(self.path)
			
			
def get_file_objs(path):
	"""
	Scans provided path for directories and files.
	On success returns a list of file objects.
	On error returns None.
	"""
	if path[0]=='~':
		path=os.path.expanduser(path)
	if os.path.exists(path) and os.path.isdir(path):
		objs=[]
		try:
			paths = os.listdir(path)
		except os.error:
			return None
		paths.sort()
		for item in paths:
			objs.append(FileObject(os.path.join(path, item)))
		result=[]
		for obj in objs:
			if not obj.type: result.append(obj)		
		for obj in objs:
			if obj.type: result.append(obj)
		return result
	return None
	
	
	
def _test():
	files=get_file_objs("~")
	if files is None:
		print 'ERROR!'
	else:
		for file in files:
			if not file.is_hidden:
				print file.basename
	
		
if __name__ == '__main__':
    _test()
	
	