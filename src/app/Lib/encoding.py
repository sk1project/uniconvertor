# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

import operator, string

notdef = '.notdef'

iso_latin_1 = (notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, 'space', 'exclam',
		'quotedbl', 'numbersign', 'dollar', 'percent',
		'ampersand', 'quoteright', 'parenleft', 'parenright',
		'asterisk', 'plus', 'comma', 'minus', 'period', 'slash',
		'zero', 'one', 'two', 'three', 'four', 'five', 'six',
		'seven', 'eight', 'nine', 'colon', 'semicolon', 'less',
		'equal', 'greater', 'question', 'at', 'A', 'B', 'C', 'D',
		'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
		'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
		'bracketleft', 'backslash', 'bracketright',
		'asciicircum', 'underscore', 'quoteleft', 'a', 'b', 'c',
		'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
		'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
		'z', 'braceleft', 'bar', 'braceright', 'asciitilde',
		notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, 'dotlessi', 'grave', 'acute',
		'circumflex', 'tilde', 'macron', 'breve', 'dotaccent',
		'dieresis', notdef, 'ring', 'cedilla', notdef,
		'hungarumlaut', 'ogonek', 'caron', 'space', 'exclamdown',
		'cent', 'sterling', 'currency', 'yen', 'brokenbar',
		'section', 'dieresis', 'copyright', 'ordfeminine',
		'guillemotleft', 'logicalnot', 'hyphen', 'registered',
		'macron', 'degree', 'plusminus', 'twosuperior',
		'threesuperior', 'acute', 'mu', 'paragraph',
		'periodcentered', 'cedilla', 'onesuperior',
		'ordmasculine', 'guillemotright', 'onequarter',
		'onehalf', 'threequarters', 'questiondown', 'Agrave',
		'Aacute', 'Acircumflex', 'Atilde', 'Adieresis', 'Aring',
		'AE', 'Ccedilla', 'Egrave', 'Eacute', 'Ecircumflex',
		'Edieresis', 'Igrave', 'Iacute', 'Icircumflex',
		'Idieresis', 'Eth', 'Ntilde', 'Ograve', 'Oacute',
		'Ocircumflex', 'Otilde', 'Odieresis', 'multiply',
		'Oslash', 'Ugrave', 'Uacute', 'Ucircumflex', 'Udieresis',
		'Yacute', 'Thorn', 'germandbls', 'agrave', 'aacute',
		'acircumflex', 'atilde', 'adieresis', 'aring', 'ae',
		'ccedilla', 'egrave', 'eacute', 'ecircumflex',
		'edieresis', 'igrave', 'iacute', 'icircumflex',
		'idieresis', 'eth', 'ntilde', 'ograve', 'oacute',
		'ocircumflex', 'otilde', 'odieresis', 'divide', 'oslash',
		'ugrave', 'uacute', 'ucircumflex', 'udieresis', 'yacute',
		'thorn', 'ydieresis')


adobe_standard = (notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, 'space', 'exclam', 'quotedbl',
		'numbersign', 'dollar', 'percent', 'ampersand',
		'quoteright', 'parenleft', 'parenright', 'asterisk',
		'plus', 'comma', 'hyphen', 'period', 'slash', 'zero',
		'one', 'two', 'three', 'four', 'five', 'six', 'seven',
		'eight', 'nine', 'colon', 'semicolon', 'less',
		'equal', 'greater', 'question', 'at', 'A', 'B', 'C',
		'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
		'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
		'Z', 'bracketleft', 'backslash', 'bracketright',
		'asciicircum', 'underscore', 'quoteleft', 'a', 'b',
		'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
		'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
		'y', 'z', 'braceleft', 'bar', 'braceright',
		'asciitilde', notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, 'exclamdown',
		'cent', 'sterling', 'fraction', 'yen', 'florin',
		'section', 'currency', 'quotesingle', 'quotedblleft',
		'guillemotleft', 'guilsinglleft', 'guilsinglright',
		'fi', 'fl', notdef, 'endash', 'dagger', 'daggerdbl',
		'periodcentered', notdef, 'paragraph', 'bullet',
		'quotesinglbase', 'quotedblbase', 'quotedblright',
		'guillemotright', 'ellipsis', 'perthousand', notdef,
		'questiondown', notdef, 'grave', 'acute',
		'circumflex', 'tilde', 'macron', 'breve', 'dotaccent',
		'dieresis', notdef, 'ring', 'cedilla', notdef,
		'hungarumlaut', 'ogonek', 'caron', 'emdash', notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, notdef, notdef, notdef,
		notdef, notdef, notdef, 'AE', notdef, 'ordfeminine',
		notdef, notdef, notdef, notdef, 'Lslash', 'Oslash',
		'OE', 'ordmasculine', notdef, notdef, notdef, notdef,
		notdef, 'ae', notdef, notdef, notdef, 'dotlessi',
		notdef, notdef, 'lslash', 'oslash', 'oe',
		'germandbls', notdef, notdef, notdef, notdef)

class Reencoder:

	def __init__(self, source, dest, notdef = None):
		self.source = source
		self.dest = dest
		if notdef is None:
			try:
				notdef = list(self.source).index('.notdef')
			except:
				notdef = 0
		self.notdef = notdef
		self.build_mapping()

	def build_mapping(self):
		dest = self.dest; source = self.source; notdef = self.notdef
		dict = {}
		length = len(dest)
		map(operator.setitem, [dict] * length, dest, range(length))
		dict[notdef] = self.notdef
		mapping = range(256)
		for i in mapping:
			if source[i] != dest[i]:
				if source[i] == notdef:
					mapping[i] = notdef
				else:
					mapping[i] = dict.get(source[i], notdef)
		if mapping == range(256):
			self.mapping = ''
		else:
			self.mapping = string.join(map(chr, mapping), '')

	def __call__(self, text):
		if self.mapping:
			return string.translate(text, self.mapping)
		else:
			return text
