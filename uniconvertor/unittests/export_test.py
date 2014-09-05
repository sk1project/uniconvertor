#!/usr/bin/python

# -*- coding: utf-8 -*-

# Tests for export functionality

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

class TestExportFunctions(unittest.TestCase):

	def setUp(self):
		if os.path.exists(tmpdir): shutil.rmtree(tmpdir)
		os.makedirs(tmpdir)

	def test01_Export_SK1_file(self):
		if not conv('sk1', 'sk1'): self.fail()

	def test02_Export_SK_file(self):
		if not conv('sk1', 'sk'): self.fail()

	def test03_Export_SVG_file(self):
		if not conv('sk1', 'svg'): self.fail()

	def test04_Export_CGM_file(self):
		if not conv('sk1', 'cgm'): self.fail()

	def test05_Export_AI_file(self):
		if not conv('sk1', 'ai'): self.fail()

	def test06_Export_WMF_file(self):
		if not conv('sk1', 'wmf'): self.fail()

	def test07_Export_PLT_file(self):
		if not conv('sk1', 'plt'): self.fail()

	def test08_Export_PDF_file(self):
		if not conv('sk1', 'pdf'): self.fail()

	def test09_Export_PS_file(self):
		if not conv('sk1', 'ps'): self.fail()

	def tearDown(self):
		shutil.rmtree(tmpdir)

def get_suite():
	suite = unittest.TestSuite()
	suite.addTest(unittest.makeSuite(TestExportFunctions))
	return suite

def run_tests():
	print "\nUniConvertor export test suite\n" + "-"*60
	unittest.TextTestRunner(verbosity=2).run(get_suite())

if __name__ == '__main__':
	run_tests()
