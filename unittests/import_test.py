#!/usr/bin/python

# -*- coding: utf-8 -*-

# Tests for import functionality

# Copyright (c) 2014 by Igor E.Novikov
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

import os, unittest, shutil

from uniconvertor import convert

tmpdir = 'result'
datadir = 'import_data'

def conv(ext_in, ext_out):
	input_file = os.path.join(datadir, 'probe.' + ext_in)
	output_file = os.path.join(tmpdir, 'probe.' + ext_out)
	try:
		convert(input_file, output_file)
	except:
		return False
	if not os.path.exists(output_file) or not os.path.getsize(output_file):
		return False
	return True

class TestImportFunctions(unittest.TestCase):

	def setUp(self):
		if os.path.exists(tmpdir): shutil.rmtree(tmpdir)
		os.makedirs(tmpdir)

	def test01_Open_SK1_file(self):
		if not conv('sk1', 'sk1'): self.fail()

	def test02_Open_SK_file(self):
		if not conv('sk', 'sk1'): self.fail()

	def test03_Open_SVG_file(self):
		if not conv('svg', 'sk1'): self.fail()

	def test04_Open_CGM_file(self):
		if not conv('cgm', 'sk1'): self.fail()

	def test05_Open_AI_file(self):
		if not conv('ai', 'sk1'): self.fail()

	def test06_Open_WMF_file(self):
		if not conv('wmf', 'sk1'): self.fail()

	def test07_Open_PLT_file(self):
		if not conv('plt', 'sk1'): self.fail()

	def test08_Open_CDR_file(self):
		if not conv('cdr', 'sk1'): self.fail()

	def test08_Open_CMX_file(self):
		if not conv('cmx', 'sk1'): self.fail()

	def tearDown(self):
		shutil.rmtree(tmpdir)

def get_suite():
	suite = unittest.TestSuite()
	suite.addTest(unittest.makeSuite(TestImportFunctions))
	return suite

def run_tests():
	print "\nUniConvertor import test suite\n" + "-"*60
	unittest.TextTestRunner(verbosity=2).run(get_suite())

if __name__ == '__main__':
	run_tests()
