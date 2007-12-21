# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998 by Bernhard Herzog
#
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

# dashes for sketch

import os

from app import config, _
from app.events.warn import warn_tb, USER
from app.io.loadres import read_resource_file

std_dashes = None

def StandardDashes():
	global std_dashes
	if std_dashes is None:
		filename = os.path.join(config.std_res_dir, config.preferences.dashes)
		try:
			std_dashes = []
			read_resource_file(filename, '##Sketch Dashes 0',
								_("%s is not dashes file"),
								{'dashes': std_dashes.append})
		except:
			warn_tb(USER, _("Error trying to read dashes from %s\n"
							"Using builtin defaults"), filename)
			std_dashes = [(), (5, 5)]
	return std_dashes
