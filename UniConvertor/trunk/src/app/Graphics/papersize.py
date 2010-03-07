# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 2000 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
# Define some standard Papersizes
#
# This module exports the following variables:
#
# Papersize:
#
# A dictionary that maps the name of paper formats such as 'letter' or
# 'A4' to their widths and heights. The value of an entry is a tuple
# (width, height).
#
#
# PapersizesList:
#
# A list containing all sizes defined in Papersize. The list items are
# tuples of the form (name, width, height)
#
#
# All sizes are given in units of PostScript points (1/72 inch)
#

from app.Lib.units import m_to_pt, in_to_pt


# Compute the European paper sizes.
#
# While this is a cute approach, it also is less accurate than simply
# listing the papersizes because the standard defines the sizes in mm.
# I've left the code in here for entertainment and educational value
# :-).
#
# The definition is that A0 has an area of 1m^2 and its sides have a
# ratio of sqrt(2). A1 is A0 cut in half and so on. Therefore A0's
# height is 2**0.25 and its width 0.5**0.25 (both in meters)
def _european_sizes():
	sizes = []
	width = 0.5**0.25
	height = 2.0**0.25
	for i in range(8):
		sizes.append(('A' + `i`, width * m_to_pt, height * m_to_pt))
		width, height = height / 2, width
	return sizes[3:]

# The more accurate way to specify the european sizes, contributed by
# Martin Glaser:

_din_sizes = [
	('A0', 0.841 * m_to_pt, 1.189 * m_to_pt),
	('A1', 0.594 * m_to_pt, 0.841 * m_to_pt),
	('A2', 0.420 * m_to_pt, 0.594 * m_to_pt),
	('A3', 0.297 * m_to_pt, 0.420 * m_to_pt),
	('A4', 0.210 * m_to_pt, 0.297 * m_to_pt),
	('A5', 0.148 * m_to_pt, 0.210 * m_to_pt),
	('A6', 0.105 * m_to_pt, 0.148 * m_to_pt),
#    ('A7', 0.074 * m_to_pt, 0.105 * m_to_pt),
	('B1 (ISO)', 0.707 * m_to_pt, 1.0 * m_to_pt),
	('B4 (ISO)', 0.250 * m_to_pt, 0.353 * m_to_pt),
	('B5 (ISO)', 0.176 * m_to_pt, 0.250 * m_to_pt),
	('C3', 0.324 * m_to_pt, 0.458 * m_to_pt),
	('C4', 0.229 * m_to_pt, 0.324 * m_to_pt),
	('C5', 0.162 * m_to_pt, 0.229 * m_to_pt),
	('C6', 0.114 * m_to_pt, 0.162 * m_to_pt),
	('Visit card #1', 0.05 * m_to_pt, 0.09 * m_to_pt),
	('Visit card #2', 0.055 * m_to_pt, 0.085 * m_to_pt),
	('Envelope C6', 0.114 * m_to_pt, 0.162 * m_to_pt),
	('Envelope E65/DL', 0.110 * m_to_pt, 0.220 * m_to_pt),
	('Envelope C5', 0.162 * m_to_pt, 0.229 * m_to_pt),
	('Envelope C4', 0.229 * m_to_pt, 0.324 * m_to_pt),
	]



_american_sizes = [
	('Letter',		8.5  * in_to_pt, 11   * in_to_pt),
	('Half Letter',	5.5  * in_to_pt, 8.5   * in_to_pt),
	('Legal',		8.5  * in_to_pt, 14   * in_to_pt),
	('Executive',	7.25 * in_to_pt, 10.5 * in_to_pt)
	]


Papersize = {}
PapersizesList = _din_sizes + _american_sizes


for name, width, height in PapersizesList:
	Papersize[name] = (width, height)

