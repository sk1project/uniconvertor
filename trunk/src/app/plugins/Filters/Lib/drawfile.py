"""
    drawfile.py

    Read a Drawfile and store the elements in an instance
    of a Drawfile class

    (C) David Boddie 2001-2

    This module may be freely distributed and modified. 
"""

# Version history:
#
# 0.10 (Fri 24th August 2001)
#
# Initial release version.
#
# 0.11 (Fri 24th August 2001)
#
# Modified tagged objects so that they contain any extra data which may be
# present.
#
# 0.12 (Wed 29th August 2001)
#
# Changed paragraph handling in text areas.
#
# 0.13 (Sat 20th October 2001)
#
# Changed error to a class derived from exceptions.Exception.
#
# 0.131 (Sat 26th January 2002)
#
# Tidied up some formatting errors caused by mixing tabs and spaces.

import spritefile, os, string
import struct

version = '0.13 (Sat 20th October 2001)'

try:
    import cStringIO
    StringIO = cStringIO
except ImportError:
    import StringIO

class drawfile_error(Exception):

    pass

units_per_inch = 180*256
units_per_point = 640

# Compatibility with future versions of Python with different division
# semantics:
points_per_inch = int(units_per_inch/units_per_point)

class drawfile_object:

    def __init__(self, data = None):

        if data != None:

            self.input(data)

        else:

            self.new()

    def number(self, size, n):
    
        # Little endian writing
    
        s = ""
    
        while size > 0:
            i = n % 256
            s = s + chr(i)
#           n = n / 256
            n = n >> 8
            size = size - 1
    
        return s

    def str2num(self, size, s):
        return spritefile.str2num(size, s)

    def decode_double(self, s):
        """Return a floating point number from an IEEE double encoded in a
        string"""

        # Information on decoding from the gnu-fixed library for gcc

        word1 = self.str2num(4, s[0:4])
        word2 = self.str2num(4, s[4:8])

        sign = word1 >> 31
        exponent = ((word1 >> 20) & 0x7ff) - 1023

        fraction = long((word1 & 0x000fffff) | 0x100000) << 32
        fraction = fraction | long(word2)

        if exponent > 0:

            value = float(fraction << exponent) / float(1L << 52)

        elif exponent == 0:

            value = float(fraction) / float(1L << 52)

        else:
            value = float(fraction >> -exponent) / float(1L << 52)

        if sign == 1:
            return -value
        else:
            return value


    def encode_double(self, f):

        l = long(f)


class font_table(drawfile_object):

    def new(self):

        self.font_table = {}

    def input(self, data):
        """input(self, data)
        Decodes a raw font table object from a Draw file and stores it
        internally as a dictionary of font numbers and names.
        """
        at = 0
        l = len(data)

        self.font_table = {}

        while at < l:

            number = ord(data[at])

            if number == 0:     # at the end of the object
                return

            name = ''
            at = at + 1
            while ord(data[at]) != 0 and at < l:

                c = ord(data[at])
                if c > 32 and c != 127:
                    name = name + data[at]
                at = at + 1

            at = at + 1

            if name == '':      # at the end of the object
                return

            self.font_table[number] = name

#           if (at % 4) > 0: at = at + 4 - (at % 4)

    def output(self):
        """output(self)
        Returns the internal dictionary of font numbers and names as raw
        data to be written to a Draw file.
        """

        data = ''

        for key in self.font_table.keys():

            # Font number
            data = data + chr(key)
            # Font name
            data = data + self.font_table[key] + '\000'

        # Pad with zeros
        pad = len(data) % 4
        data = data + ((4-pad) % 4)*'\000'

        data = self.number(4, 0) + self.number(4, len(data) + 8) + data

        return data


class text(drawfile_object):

    def new(self):

        self.x1 = self.y1 = self.x2 = self.y2 = 0.0
        self.foreground = [0, 0, 0, 0]
        self.background = [0xff, 0xff, 0xff, 0xff]
        self.size = [0, 0]
        self.baseline = [0, 0]
        self.style = 0
        self.text = ''

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

        data = args[4]
        l = len(data)

        if len(args) == 6:

            # Transformed text
            self.transform = (
                self.str2num(4, data[0:4]), self.str2num(4, data[4:8]),
                self.str2num(4, data[8:12]), self.str2num(4, data[12:16]),
                self.str2num(4, data[16:20]), self.str2num(4, data[20:24]) )

            self.font_flags = self.str2num(4, data[24:28])

            data = data[28:]

        # Standard text information
        self.foreground = [self.str2num(1, data[0]),
                           self.str2num(1, data[1]),
                           self.str2num(1, data[2]),
                           self.str2num(1, data[3])]

        self.background = [self.str2num(1, data[4]),
                           self.str2num(1, data[5]),
                           self.str2num(1, data[6]),
                           self.str2num(1, data[7])]

        self.style = self.str2num(4, data[8:12])
        self.size = [self.str2num(4, data[12:16]),
                     self.str2num(4, data[16:20])]
        self.baseline = [self.str2num(4, data[20:24]),
                         self.str2num(4, data[24:28])]

        at = 28
        while (data[at] != '\000') and (at < l):
            at = at + 1

        self.text = data[28:at]

    def output(self):

        pad = (len(self.text)+1) % 4
        if pad != 0: pad = 4 - pad 

        data = self.number(4, 1) + \
            self.number(4, len(self.text) + 1 + pad + 24 + 28) + \
            self.number(4, self.x1) + \
            self.number(4, self.y1) + \
            self.number(4, self.x2) + \
            self.number(4, self.y2) + \
            self.number(1, self.foreground[0]) + \
            self.number(1, self.foreground[1]) + \
            self.number(1, self.foreground[2]) + \
            self.number(1, self.foreground[3]) + \
            self.number(1, self.background[0]) + \
            self.number(1, self.background[1]) + \
            self.number(1, self.background[2]) + \
            self.number(1, self.background[3]) + \
            self.number(4, self.style) + \
            self.number(4, self.size[0]) + \
            self.number(4, self.size[1]) + \
            self.number(4, self.baseline[0]) + \
            self.number(4, self.baseline[1]) + \
            self.text + '\000'

        data = data + pad*'\000'

        return data


class path(drawfile_object):

    join = ['mitred', 'round', 'bevelled']                  # 0, 1, 2
    end_cap = ['butt', 'round', 'square', 'triangular']     # 0, 4, 8, 12
    start_cap = ['butt', 'round', 'square', 'triangular']   # 0, 16, 32, 48
    winding = ['non-zero', 'even-odd']                      # 0, 64
    dashed = ['missing', 'present']                         # 0, 128
    tag = ['end', '', 'move', '', '', 'close', 'bezier', '', 'draw']  

    def new(self):

        self.x1 = self.y1 = self.x2 = self.y2 = 0.0
        self.outline = [0, 0, 0, 0]
        self.fill = [0xff, 0xff, 0xff, 0xff]
        self.width = 0
        self.style = {'join': 'mitred', 'end cap': 'butt', 'start cap': 'butt',
                      'winding rule': 'even-odd', 'dash pattern': 'missing',
                      'triangle cap width': 16, 'triangle cap length': 16}

        self.path = []

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

        data = args[4]
        l = len(data)

        self.fill = [self.str2num(1,data[0]), self.str2num(1,data[1]),
                     self.str2num(1,data[2]), self.str2num(1,data[3])]
        self.outline = [self.str2num(1,data[4]), self.str2num(1,data[5]),
                        self.str2num(1,data[6]), self.str2num(1,data[7])]
        self.width = self.str2num(4, data[8:12])
        style = self.str2num(4, data[12:16])

        self.style = {}
        try:
            self.style['join'] = self.join[style & 3]
        except:
            self.style['join'] = 'mitred'
        try:
            self.style['end cap'] = self.end_cap[(style >> 2) & 3]
        except:
            self.style['end cap'] = 'butt'
        try:
            self.style['start cap'] = self.start_cap[(style >> 4) & 3]
        except:
            self.style['end cap'] = 'butt'
        try:
            self.style['winding rule'] = self.winding[(style >> 6) & 1]
        except:
            self.style['winding rule'] = 'even-odd'
        try:
            self.style['dash pattern'] = self.dashed[(style >> 7) & 1]
        except:
            self.style['dash pattern'] = 'missing'

        self.style['triangle cap width'] = (style >> 16) & 255
        self.style['triangle cap length'] = (style >> 24) & 255

        if self.style['dash pattern'] == 'present':

            # Read the dash pattern
            self.pattern = [self.str2num(4, data[16:20])]
            number = self.str2num(4, data[20:24])
            self.pattern.append(number)

            at = 24
            for i in range(number):

                self.pattern.append(self.str2num(4, data[at:at+4]))
                at = at + 4

        else:
            at = 16

        # Read the path elements

        self.path = []
        while at < l:

            tag = self.str2num(4, data[at:at+4])

            if tag == 0:
                self.path.append(['end'])
                at = at + 4
            elif tag == 2:
                self.path.append(
                    ('move',
                     (self.str2num(4, data[at+4:at+8]),
                      self.str2num(4, data[at+8:at+12]) ) ) )
                at = at + 12
            elif tag == 5:
                self.path.append(['close'])
                at = at + 4
            elif tag == 6:
                self.path.append(
                    ('bezier',
                     (self.str2num(4, data[at+4:at+8]),
                      self.str2num(4, data[at+8:at+12]) ),
                     (self.str2num(4, data[at+12:at+16]),
                      self.str2num(4, data[at+16:at+20]) ),
                     (self.str2num(4, data[at+20:at+24]),
                      self.str2num(4, data[at+24:at+28]) ) ) )
                at = at + 28
            elif tag == 8:
                self.path.append(
                    ('draw',
                     (self.str2num(4, data[at+4:at+8]),
                      self.str2num(4, data[at+8:at+12]) ) ) )
                at = at + 12
            else:
                raise drawfile_error, 'Unknown path segment found (%s)' % \
                      hex(tag)


    def output(self):

        # Write the colours and width
        data = self.number(1,self.fill[0]) + \
            self.number(1,self.fill[1]) + \
            self.number(1,self.fill[2]) + \
            self.number(1,self.fill[3]) + \
            self.number(1,self.outline[0]) + \
            self.number(1,self.outline[1]) + \
            self.number(1,self.outline[2]) + \
            self.number(1,self.outline[3]) + \
            self.number(4,self.width)

        if hasattr(self, 'pattern'):
            self.style['dash pattern'] == 'present'

        # Write the path style
        style = self.join.index(self.style['join']) | \
            (self.end_cap.index(self.style['end cap']) << 2) | \
            (self.start_cap.index(self.style['start cap']) << 4) | \
            (self.winding.index(self.style['winding rule']) << 6) | \
            (self.dashed.index(self.style['dash pattern']) << 7) | \
            (self.style['triangle cap width'] << 16) | \
            (self.style['triangle cap length'] << 24)

        data = data + self.number(4, style)

        if hasattr(self, 'pattern'):

            for n in self.pattern:

                data = data + self.number(4, n)

        # Write the path segments to the string
        for item in self.path:

            tag = item[0]
            data = data + self.number(4, self.tag.index(tag))
            for x, y in item[1:]:

                self.x1 = min(self.x1, x)
                self.y1 = min(self.y1, y)
                self.x2 = max(self.x2, x)
                self.y2 = max(self.y2, y)
                data = data + self.number(4, x) + self.number(4, y)

        # The last segment must be an end segment
        if tag != 'end':
            data = data + self.number(4, 0)

        # Write the header
        data = self.number(4, 2) + \
            self.number(4, len(data) + 24) + \
            self.number(4, self.x1) + \
            self.number(4, self.y1) + \
            self.number(4, self.x2) + \
            self.number(4, self.y2) + data

        return data


class sprite(drawfile_object):

    def new(self):

        self.sprite = {}

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

        data = args[4]

        if len(args) == 6:

            # Transformed sprite
            self.transform = (
                self.str2num(4, data[0:4]), self.str2num(4, data[4:8]),
                self.str2num(4, data[8:12]), self.str2num(4, data[12:16]),
                self.str2num(4, data[16:20]), self.str2num(4, data[20:24]) )
            data = data[24:]

        # Construct a reasonable sprite block from the data supplied
        # One sprite and offset to sprite 
        sprdata = self.number(4, 1) + \
               self.number(4, 0x10)

        free = self.str2num(4, data[0:4]) + 0x10
        sprdata = sprdata + self.number(4, free) + data

        # Create a spritefile object
        sprites = spritefile.spritefile(StringIO.StringIO(sprdata))

        # Use the first, and only, sprite
        self.name = sprites.sprites.keys()[0]
        self.sprite = sprites.sprites[self.name]

    def output(self):

        # Create a new spritefile object
        sprites = spritefile.spritefile()
        # Add the sprite
        sprites.sprites[self.name] = self.sprite
        # Write the sprite to an output stream
        stream = StringIO.StringIO()
        sprites.write(stream)

        # Return the text string stored in the stream
        return StringIO.StringIO.read()


class group(drawfile_object):

    def new(self):

        self.name = ''
        self.x1 = self.y1 = self.x2 = self.y2 = 0.0
        self.objects = ''

    def input(self, data):

        self.x1 = data[0]
        self.y1 = data[1]
        self.x2 = data[2]
        self.y2 = data[3]
        self.name = data[4]
        self.objects = data[5]

    def output(self):

        data = ''

        for obj in self.objects:

            data = data + obj.output()
            self.x1 = min(obj.x1, self.x1)
            self.y1 = min(obj.y1, self.y1)
            self.x2 = max(obj.x2, self.x2)
            self.y2 = max(obj.y2, self.y2)

        if len(self.name) < 12:
            self.name = self.name + (12-len(self.name))*' '

        data = self.name + data

        data = self.number(4,6) + \
            self.number(4,len(data)+24) + \
            self.number(4,self.x1) + \
            self.number(4,self.y1) + \
            self.number(4,self.x2) + \
            self.number(4,self.y2) + data

        return data


class tagged(drawfile_object):

    def new(self):

        self.id = ''
        self.object = []

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]
        self.id = args[4]

        self.object = args[5]   # there is only one object passed
        self.data = args[6]

    def output(self):
        """output(self)
        Returns the tag ID and objects as data to be written to a Draw file.
        """

        data = self.id
        data = data + self.objects.output() # get the object contained
                                            # to output itself
        data = data + self.data             # add extra data

        data = self.number(4,7) + \
            self.number(4,len(data)+24) + \
            self.number(4,self.x1) + \
            self.number(4,self.y1) + \
            self.number(4,self.x2) + \
            self.number(4,self.y2) + data

        return data


class text_area(drawfile_object):

    def new(self):

        self.columns = []
        self.text = ''

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

        data = args[4]

        self.columns = []

        l = len(data)
        i = 0
        while i < l:

            n = self.str2num(4, data[i:i+4])

            if n == 0:
                i = i + 4
                break

            if n != 10:
                raise drawfile_error, 'Not a text column object.'

            length = self.str2num(4, data[i+4:i+8])

            if length != 24:
                raise drawfile_error, 'Text column object has invalid length.'

            self.columns.append(
                column(
                    ( self.str2num(4, data[i+8:i+12]),
                      self.str2num(4, data[i+12:i+16]),
                      self.str2num(4, data[i+16:i+20]),
                      self.str2num(4, data[i+20:i+24]) ) ) )
            i = i + 24

        # Skip reserved words
        i = i + 8

        # Initial colours
        self.foreground = (ord(data[i+1]), ord(data[i+2]), ord(data[i+3]))
        self.background = (ord(data[i+5]), ord(data[i+6]), ord(data[i+7]))

        i = i + 8

        # Read text
        self.text = ''
        while i < l:

            if ord(data[i]) != 0:
                self.text = self.text + data[i]
            i = i + 1

        # Parse the text, creating tuples containing command and value
        # information.
        self.align = 'L'                # current alignment
#       self.baseline = object.y2       # current baseline
#       self.horizontal = object.x1     # current cursor position
        self.linespacing = 0.0          # line spacing for next line
        self.paragraph = 10.0           # spacing before this paragraph
        self.columns_number = len(self.columns)    # number of columns to use
        self.in_column = 1              # the current column
        self.left_margin = 1.0          # left and
        self.right_margin = 1.0         # right margins
        self.font_table = {}            # font and size dictionary
        self.font_name = ''
        self.font_size = 0.0
        self.font_width = 0.0
        self.current = ''               # text buffer

        # Write the commands and their arguments to a list for later processing
        self.commands = []

        # Each line/paragraph will contain the following keys:
        # text              the textual content
        # left margin
        # right margin
        # paragraph

        i = 0
        while i < len(self.text):

            if self.text[i] == '\\':

                command, args, next = self.read_escape(i+1)

                # Add command to the list
                self.commands.append((command, args))

            else:
                # In text: add it to the buffer
                next = string.find(self.text, '\\', i)

                if next == -1: next = len(self.text)

                lines = string.split(self.text[i:next], '\n')

                # Examine all but the last line

                # Paragraph counter
                n_paragraphs = 0

                for line in lines[:-1]:

                    if line == '':

                        # Empty line: new paragraph
                        n_paragraphs = n_paragraphs + 1

                    else:
                        # If the preceding elements were paragraph
                        # breaks then add them all except one, with a
                        # minimum of one
                        if n_paragraphs > 0:
                            for j in range(max(n_paragraphs-1, 1)):
                                self.commands.append(('para', ''))

                        n_paragraphs = 0

                        # Substitute spaces for tabs
                        line = string.expandtabs(line, 1)
                        words = string.split(line, ' ')

                        # Examine the words on this line
                        for word in words:

                            # Add word (assuming that a space follows)
                            self.commands.append(('text', (word, ' ')))

                # If the preceding elements were paragraph
                # breaks then add them all except one, with a
                # minimum of one
                if n_paragraphs > 0:
                    for j in range(max(n_paragraphs-1, 1)):
                        self.commands.append(('para', ''))

                        # The last line doesn't end with a newline character so we
                        # can't have a paragraph break

                if lines[-1] != '':

                    # Substitute spaces for tabs
                    line = string.expandtabs(lines[-1], 1)
                    words = string.split(line, ' ')

                    # Examine all but the last word
                    for word in words[:-1]:

                        # Add word (assuming that a space follows)
                        self.commands.append(('text', (word, ' ')))

                    if words[-1] != '':

                        # Add word without following space
                        self.commands.append(('text', (words[-1], '')))


            # Go to next command
            i = next


    def read_escape(self, i):

        command = self.text[i]

        # Special case: the newline character is itself a command
        if command != '\n' and command != '-' and command != '\\':
            next = self.skip_whitespace(i + 1)
        else:
            next = i + 1

        if command == '!':

            args, next = self.read_value(next, ['/', '\n'])

        elif command == 'A':

            args = self.text[next]
            if args not in 'LRCD':
                raise drawfile_error, \
                      'Unknown alignment character '+self.align + \
                      ' in text area at '+hex(i)

            if self.text[next+1] == '/':
                next = next + 2
            else:
                next = next + 1

        elif command == 'B':

            value1, next = self.read_value(next, [' '])
            next = self.skip_whitespace(next)
            value2, next = self.read_value(next, [' '])
            next = self.skip_whitespace(next)
            value3, next = self.read_value(next, ['\n', '/'])

            try:
                value1, value2, value3 = int(value1), int(value2), int(value3)
            except ValueError:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)

            if value1 < 0 or value1 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)
            if value2 < 0 or value2 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)
            if value3 < 0 or value3 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)

            args = (value1, value2, value3)

        elif command == 'C':

            value1, next = self.read_value(next, [' '])
            next = self.skip_whitespace(next)
            value2, next = self.read_value(next, [' '])
            next = self.skip_whitespace(next)
            value3, next = self.read_value(next, ['\n', '/'])

            try:
                value1, value2, value3 = int(value1), int(value2), int(value3)
            except ValueError:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)

            if value1 < 0 or value1 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)
            if value2 < 0 or value2 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)
            if value3 < 0 or value3 > 255:
                raise drawfile_error, 'Invalid colour in text area at '+hex(i)

            args = (value1, value2, value3)

        elif command == 'D':

            args, next = self.read_value(next, ['/', '\n'])
            try:
                args = int(args)
            except ValueError:
                raise drawfile_error, \
                      'Invalid number of columns in text area at '+hex(i)

        elif command == 'F':

            digits, next = self.read_number(next)

            try:
                digits = int(digits)
            except ValueError:
                raise drawfile_error, \
                      'Invalid font number in text area at '+hex(i)

            next = self.skip_whitespace(next)
            name, next = self.read_value(next, [' '])

            next = self.skip_whitespace(next)
            value2, next = self.read_value(next, [' ', '/', '\n'])

            if self.text[next] == ' ':
                value3, next = self.read_value(next, ['\n', '/'])
            else:
                value3 = value2

            try:
                value2, value3 = int(value2), int(value3)
            except ValueError:
                raise drawfile_error, \
                      'Invalid font size in text area at '+hex(i)

            self.font_table[digits] = (name, value2, value3)

            args = (digits, name, value2, value3)

        elif command == 'L':

            args, next = self.read_value(next, ['/', '\n'])
            try:
                args = int(args)
            except ValueError:
                raise drawfile_error, \
                      'Invalid leading value in text area at '+hex(i)

        elif command == 'M':

            value1, next = self.read_value(next, [' '])
            next = self.skip_whitespace(next)
            value2, next = self.read_value(next, ['/', '\n'])

            try:
                value1, value2 = int(value1), int(value2)
            except ValueError:
                raise drawfile_error, \
                      'Invalid margins in text area at '+hex(i)

            if value1 <= 0.0 or value2 <= 0.0:
                raise drawfile_error, \
                      'Invalid margins in text area at '+hex(i)

            args = (value1, value2)

        elif command == 'P':

            args, next = self.read_value(next, ['/', '\n'])

            try:
                args = int(args)
            except ValueError:
                raise drawfile_error, \
                      'Invalid leading value in text area at '+hex(i)

        elif command == 'U':

            if self.text[next] != '.':
                value1, next = self.read_value(next, [' '])
                next = self.skip_whitespace(next)
                value2, next = self.read_value(next, ['/', '\n'])

                try:
                    value1, value2 = int(value1), int(value2)
                except ValueError:
                    raise drawfile_error, \
                          'Invalid value in text area at '+hex(i)

                args = (value1, value2)
            else:
                next = next + 1
                args = '.'

        elif command == 'V':

            args = self.text[next]
            if self.text[next+1] == '/':
                next = next + 2
            else:
                next = next + 1
            try:
                args = int(args)
            except ValueError:
                raise drawfile_error, 'Invalid value in text area at '+hex(i)

        elif command == '-':

            args = ''

        elif command == '\n':

            command = 'newl'
            args = ''

        elif command == '\\':

            commands = 'text'
            args = ('\\', '')

        elif command == ';':

            args, next = self.read_value(next, ['\n'])

        elif command not in string.digits:

            # Unknown
            raise drawfile_error, \
                  'Unknown command '+command+' in text area at '+hex(i)
        else:
            # Digits
            value, next = self.read_number(next)

            # The command was actually the first digit
            value = command+value

            try:
                value = int(value)
            except ValueError:
                raise drawfile_error, \
                      'Font number was not an integer in text area at '+hex(i)

            if self.text[next] == '/':
                next = next + 1

            try:
                font_name, font_size, font_width = self.font_table[value]
            except KeyError:
                raise drawfile_error, 'Font not found in text area at '+hex(i)

            command = 'font'
            args = value

        return command, args, next


    def skip_whitespace(self, i):

        while self.text[i] in string.whitespace:
            i = i + 1

        return i


    def read_value(self, i, endings):

        ends = []
        for ch in endings:

            end = string.find(self.text, ch, i)
            if end != -1:
                ends.append(end)

        if ends == []:
            return self.text[i:], len(self.text)

        return self.text[i:min(ends)], min(ends) + 1


    def read_number(self, i):

        value = ''
        while self.text[i] in '0123456789':

            value = value + self.text[i]
            i = i + 1

        return value, i


    def output(self):

        data = ''

        for c in self.columns:

            data = data + c.output()

        data = data + self.number(4, 0) + \
                self.number(4, 0) + \
                self.number(4, 0) + \
                self.number(4, self.foreground) + \
                self.number(4, self.background) + \
                self.text + '\000'

        excess = len(data) % 4
        if excess != 0:
            data = data + ((4 - excess)*'\000')

        data = self.number(4,9) + \
            self.number(4,len(data)+24) + \
            self.number(4,self.x1) + \
            self.number(4,self.y1) + \
            self.number(4,self.x2) + \
            self.number(4,self.y2) + data

        return data


class column(drawfile_object):

    def new(self):

        pass

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

    def output(self):

        data = self.number(4,10) + \
            self.number(4,24) + \
            self.number(4,self.x1) + \
            self.number(4,self.y1) + \
            self.number(4,self.x2) + \
            self.number(4,self.y2)

        return data


class options(drawfile_object):

    def new(self):

        self.options = {}

    def input(self, data):

        # Ignore the empty bounding box
        data = data[16:]

        self.options = {}

        self.options['paper size'] = 'A%i' % \
                                     ((self.str2num(4, data[0:4]) >> 8) - 1)

        paper = self.str2num(4, data[4:8])

        if (paper & 1) != 0:

            self.options['show limits'] = 'on'
        else:
            self.options['show limits'] = 'off'

        if (paper & 0x10) != 0:

            self.options['paper limits'] = 'landscape'
        else:
            self.options['paper limits'] = 'portrait'

        if (paper & 0x100) != 0:

            self.options['printer limits'] = 'default'
        else:
            self.options['printer limits'] = 'unknown'

        self.options['grid spacing'] = self.decode_double(data[8:16])
        self.options['grid subdivisions'] = self.str2num(4, data[16:20])

        if self.str2num(4, data[20:24]) == 0:

            self.options['grid type'] = 'rectangular'
        else:
            self.options['grid type'] = 'isometric'

        if self.str2num(4, data[24:28]) == 0:

            self.options['grid auto adjustment'] = 'off'
        else:
            self.options['grid auto adjustment'] = 'on'

        if self.str2num(4, data[28:32]) == 0:

            self.options['grid shown'] = 'off'
        else:
            self.options['grid shown'] = 'on'

        if self.str2num(4, data[32:36]) == 0:

            self.options['grid locking'] = 'off'
        else:
            self.options['grid locking'] = 'on'

        if self.str2num(4, data[36:40]) == 0:

            self.options['grid units'] = 'in'
        else:
            self.options['grid units'] = 'cm'

        zoom_mult = self.str2num(4, data[40:44])
        if zoom_mult > 8:
            zoom_mult = 8
        if zoom_mult < 1:
            zoom_mult = 1

        zoom_div = self.str2num(4, data[44:48])
        if zoom_div > 8:
            zoom_div = 8
        if zoom_div < 1:
            zoom_div = 1

        self.options['zoom'] = (zoom_mult, zoom_div)

        if self.str2num(4, data[48:52]) == 0:

            self.options['zoom locking'] = 'off'
        else:
            self.options['zoom locking'] = 'on'

        if self.str2num(4, data[52:56]) == 0:

            self.options['toolbox'] = 'off'
        else:
            self.options['toolbox'] = 'on'

        tool = self.str2num(4, data[56:60])
        if tool == 1:
            self.options['tool'] = 'line'
        elif tool == 2:
            self.options['tool'] = 'closed line'
        elif tool == 4:
            self.options['tool'] = 'curve'
        elif tool == 8:
            self.options['tool'] = 'closed curve'
        elif tool == 16:
            self.options['tool'] = 'rectangle'
        elif tool == 32:
            self.options['tool'] = 'ellipse'
        elif tool == 64:
            self.options['tool'] = 'text'
        elif tool == 128:
            self.options['tool'] = 'select'
        else:
            self.options['tool'] = 'unknown'

        self.options['undo buffer size'] = self.str2num(4, data[60:64])


class jpeg(drawfile_object):

    def new(self):

        self.image = ''
        self.transform = []

        # Data with unknown meaning
        self.unknown = ''

    def input(self, args):

        self.x1 = args[0]
        self.y1 = args[1]
        self.x2 = args[2]
        self.y2 = args[3]

        data = args[4]

        self.unknown = data[:8]

        self.dpi_x = self.str2num(4, data[8:12])
        self.dpi_y = self.str2num(4, data[12:16])

        self.transform = [ self.str2num(4, data[16:20]),
                           self.str2num(4, data[20:24]),
                           self.str2num(4, data[24:28]),
                           self.str2num(4, data[28:32]),
                           self.str2num(4, data[32:36]),
                           self.str2num(4, data[36:40])    ]
        length = self.str2num(4, data[40:44])

        self.image = data[44:44+length]

    def output(self):

        data = ''
        data = data + self.unknown + \
                  self.number(4, self.dpi_x) + \
                  self.number(4, self.dpi_y)

        for value in self.transform:
            data = data + self.number(4, value)

        data = data + self.number(4, len(self.image)) + self.image

        return data


class unknown(drawfile_object):

    def new(self):

        raise drawfile_error, 'Cannot create an unspecified unknown object.'

    def input(self, data):

        self.type = data[0]
        self.length = data[1]
        self.x1 = data[2]
        self.y1 = data[3]
        self.x2 = data[4]
        self.y2 = data[5]
        self.data = data[6]

    def output(self):

        return self.number(4,self.type) + \
               self.number(4,self.length) + \
               self.number(4,self.x1) + \
               self.number(4,self.y1) + \
               self.number(4,self.x2) + \
               self.number(4,self.y2) + \
               self.data


class drawfile:

    def __init__(self, file = None):

        if file != None:
            self.read(file)
        else:
            self.new()

    def new(self):

        self.version = {'major': 201, 'minor': 0}
        self.creator = 'drawfile.py '
        self.objects = []

        self.x1 = 0x7fffffff
        self.y1 = 0x7fffffff

        # Note: self.x2 and self.y2 used to be initialized to
        # 0x80000000.  In Python 2.4 the meaning of that literal has
        # changed to be always positive instead of being negative on 32
        # bit platforms.  To avoid problems with that the constants have
        # been replaced with the decimal version of the interpretation
        # of 0x80000000 on 32 bit machines.  It's not clear whether that
        # really is the right solution.  The intention of the value
        # might have been something like -sys.maxint - 1 instead.
        self.x2 = -2147483648
        self.y2 = -2147483648

    def number(self, size, n):
    
        # Little endian writing
    
        s = ""
    
        while size > 0:
            i = n % 256
            s = s + chr(i)
#           n = n / 256
            n = n >> 8
            size = size - 1
    
        return s


    def str2num(self, size, s):
        return spritefile.str2num(size, s)


    def read_group(self, f):

        start = f.tell() - 4

        l = self.str2num(4, f.read(4))
        x1 = self.str2num(4, f.read(4))
        y1 = self.str2num(4, f.read(4))
        x2 = self.str2num(4, f.read(4))
        y2 = self.str2num(4, f.read(4))

        name = f.read(12)

        objects = []

        while f.tell() < (start + l):

            object = self.read_object(f)
            if object == '':
                break
            objects.append(object)

        return (6, l, x1, y1, x2, y2, name, objects)


    def read_object(self, f):

        # Read object number
        s = f.read(4)

        if not s:
            return ''

        t = self.str2num(4, s)

        if t == 0:

            # Font table object
            l = self.str2num(4, f.read(4))
#           return (t, l, f.read(l-8))
            return font_table(f.read(l-8))

        elif t == 1:

            # Text object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

            return text((x1, y1, x2, y2, f.read(l-24)))

        elif t == 2:

            # Path object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

            return path((x1, y1, x2, y2, f.read(l-24)))

        elif t == 5:

            # Sprite object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

            return sprite((x1, y1, x2, y2, f.read(l-24)))

        elif t == 6:

            # Group object
#           return self.read_group(f)
            return group(self.read_group(f)[2:])

        elif t == 7:

            # Tagged object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))
            id = f.read(4)

            begin = f.tell()
            object = self.read_object(f)
            length = f.tell() - begin
            data = f.read(l-28-length)

            return tagged((x1, y1, x2, y2, id, object, data))

        elif t == 9:

            # Text area object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

            return text_area((x1, y1, x2, y2, f.read(l-24)))

        elif t == 11:

            # Options object
            l = self.str2num(4, f.read(4))

            return options(f.read(l-8))

        elif t == 12:

            # Transformed text object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))
            return text((x1, y1, x2, y2, f.read(l-24), 1))

        elif t == 13:

            # Tranformed sprite object
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

            return sprite((x1, y1, x2, y2, f.read(l-24), 1))

        elif t == 16:

            # JPEG image
            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))
            return jpeg((x1, y1, x2, y2, f.read(l-24)))

        else:

            l = self.str2num(4, f.read(4))
            x1 = self.str2num(4, f.read(4))
            y1 = self.str2num(4, f.read(4))
            x2 = self.str2num(4, f.read(4))
            y2 = self.str2num(4, f.read(4))

#           return (t, l, x1, y1, x2, y2, f.read(l-24))
            return unknown((t, l, x1, y1, x2, y2, f.read(l-24)))


    def read(self, file):

        self.version = {}
        self.creator = ''
        self.objects = []

        file.seek(0, 0)

        if file.read(4) != 'Draw':
            raise drawfile_error, 'Not a Draw file'

        self.version['major'] = self.str2num(4, file.read(4))
        self.version['minor'] = self.str2num(4, file.read(4))

        self.creator = file.read(12)

        self.x1 = self.str2num(4, file.read(4))
        self.y1 = self.str2num(4, file.read(4))
        self.x2 = self.str2num(4, file.read(4))
        self.y2 = self.str2num(4, file.read(4))

        objects = []

        while 1:

            object = self.read_object(file)
            if object == '':
                break
            objects.append(object)

        self.objects = objects


    def write_objects(self, file, objects):

        for object in objects:

            file.write(object.output())
#           # Write the object type and length and bounding box
#           # if there is one
#           for i in range(0,len(object)-1):
#               file.write(self.number(4, object[i]))
#
#           if object[0] == 6:
#               # Group object
#               self.write_objects(file, object[-1])
#           else:
#               file.write(object[-1])


    def write(self, file):

        # Write file header
        file.write('Draw')
        
        # Write version stamps
        file.write(self.number(4, self.version['major']))
        file.write(self.number(4, self.version['minor']))

        # Write creator information
        file.write(self.creator[:12])
        
        # Write bounding box
        file.write(self.number(4, self.x1))
        file.write(self.number(4, self.y1))
        file.write(self.number(4, self.x2))
        file.write(self.number(4, self.y2))

        self.write_objects(file, self.objects)
