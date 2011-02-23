# -*- coding: utf-8 -*-

# System related utilities for multiplatform issues

# Copyright (c) 2010 by Igor E.Novikov
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Library General Public
#License as published by the Free Software Foundation; either
#version 2 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Library General Public License for more details.
#
#You should have received a copy of the GNU Library General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import platform, os, string, re, stat

WINDOWS = 'Windows'
LINUX = 'Linux'
MACOSX = 'Darwin'
GENERIC = 'generic'

def get_os_family():
	"""
	Detects OS type and returns module predefined platform name.
	The function is used for all platform dependent issues.
	"""
	name = platform.system()
	if name == LINUX:
		return LINUX
	elif name == WINDOWS:
		return WINDOWS
	elif name == MACOSX:
		return MACOSX
	else:
		return GENERIC
	

p32bit = '32bit'
p64bit = '64bit'
p128bit = '128bit'
pxxbit = 'unknown'
	
def get_os_arch():
	"""
	Detects OS architecture and returns module predefined architecture type.
	"""
	arch,bin = platform.architecture()
	if arch == p32bit:
		return p32bit
	elif arch == p64bit:
		return p64bit
	elif arch == p128bit:
		return p128bit
	else:
		return pxxbit
	
#Supported OS'es:
WinXP = 'XP'
WinVista = 'Vista'#???
Win7 = 'Win7'#???
WinOther = 'WinOther'

Ubuntu = 'Ubuntu'
Mint = 'LinuxMint'
Mandriva = 'mandrake'
Fedora = 'fedora'
Suse = 'SuSE'
LinuxOther = 'LinuxOther'

Leopard = '10.5'
SnowLeopard = '10.6'
MacOther = 'MacOther'

Unix = 'unix'

def get_os_name():
	"""
	Detects OS name and returns module predefined constant.
	"""
	if get_os_family() == WINDOWS:
		if platform.release() == WinXP:
			return WinXP
		elif platform.release() == WinVista:
			return WinVista
		elif platform.release() == Win7:
			return Win7
		else:
			return WinOther
		
	elif get_os_family() == LINUX:
		if not (platform.platform()).find(Ubuntu) == -1:
			return Ubuntu
		elif not (platform.platform()).find(Mint) == -1:
			return Mint
		elif not (platform.platform()).find(Mandriva) == -1:
			return Mandriva
		elif not (platform.platform()).find(Fedora) == -1:
			return Fedora
		elif not (platform.platform()).find(Suse) == -1:
			return Suse
		else:
			return LinuxOther
		
	elif get_os_family() == MACOSX:
		if not ((platform.mac_ver())[0]).find(Leopard) == -1:
			return Leopard
		elif not ((platform.mac_ver())[0]).find(SnowLeopard) == -1:
			return SnowLeopard
		else:
			return MacOther
		
	else:
		return Unix
	
	
# Return the value of the environment variable S if present, None
# otherwise. In Python 1.5 one might use os.environ.get(S) instead...
def getenv(s):
	if os.environ.has_key(s):
		return os.environ[s]
	return None


# Return the current local date and time as a string. The optional
# parameter format is used as the format parameter of time.strftime and
# defaults to '%c'.
# Currently this is used for the CreationTime comment in a PostScript
# file.
def current_date(format = '%c'):
	import time
	return time.strftime(format, time.localtime(time.time()))

# Return the pwd entry for the current user in the format of
# pwd.getpwuid.
def get_pwd():
	import pwd
	user = getenv("USER") or getenv("LOGNAME")
	if not user:
		return pwd.getpwuid(os.getuid())
	else:
		return pwd.getpwnam(user)


# Return the real user name (the gecos field of passwd)
def get_real_username():
	try:
		return get_pwd()[4]
	except:
		return None

# Return the hostname
def gethostname():
	name = getenv('HOSTNAME')
	if not name:
		try:
			import socket
			name = socket.gethostname()
		except:
			pass
	return name
