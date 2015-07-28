#!/usr/bin/python

# -*- coding: utf-8 -*-

# cms - small package which provides binding to LittleCMS library.

# Copyright (c) 2009 by Igor E.Novikov
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from time import sleep
import cms_test, import_test, export_test

cms_test.run_tests()
sleep(1)
import_test.run_tests()
sleep(1)
export_test.run_tests()