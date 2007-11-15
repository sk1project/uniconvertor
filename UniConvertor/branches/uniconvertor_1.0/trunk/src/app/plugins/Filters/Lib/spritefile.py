"""
    spritefile.py

    Read a Sprite file and store the contents in an instance of a Sprite
    file class.

    (C) David Boddie 2001-2

    This module may be freely distributed and modified.
"""

# History
#
# 0.10 (Fri 24th August 2001)
#
# First version to allow the drawfile.py module to access sprites.
#
# 0.11 (Tue 09th October 2001)
#
# Started sprite writing support.
#
# 0.12 (Sun 17th February 2002)
#
# Modified the maximum number of dots per inch for sprites with a mode
# number.

version = '0.12 (Sun 17th February 2002)'

import struct

def str2num(size, s):
    """Convert the integer in the string s which has to contain size bytes.

    Allowed sizes are 1, 2 and 4.  1-byte and 2-byte integers as
    unsigned and 4-byte integers as signed.  All numbers were
    little-endian.
    """
    formats = ("<B", "<H", None, "<i")
    format = formats[size - 1]
    if format is None:
        raise ValueError("Size must be one of 1, 2, or 4")
    return struct.unpack(format, s)[0]


class spritefile_error(Exception):

    pass

scale8  = 255.0/15.0        # scaling factor for 8 bits per pixel colour
                            # components
#scale8  = 254.0/16.0       # scaling factor for 8 bits per pixel colour
                            # components
scale16 = 255.0/31.0        # scaling factor for 16 bits per pixel colour
                            # components

class spritefile:

    def __init__(self, file = None):

        # Constants
        self.HEADER = 60

        # Mode information dictionary (log2bpp, x scale, y scale)
        self.mode_info = {
                    0: (0, 1, 2), 1: (1, 2, 2), 2: (2, 3, 2), 3: (1, 1, 2),
                    4: (0, 2, 2), 5: (1, 3, 2), 6: (1, 2, 2), 7: (2, 2, 2),
                    8: (1, 1, 2), 9: (2, 2, 2), 10: (3, 3, 2), 11: (1, 1, 2),
                    12: (2, 1, 2), 13: (3, 2, 2), 14: (2, 1, 2), 15: (3, 1, 2),
                    16: (2, 1, 2), 17: (2, 1, 2), 18: (0, 1, 1), 19: (1, 1, 1),
                    20: (2, 1, 1), 21: (3, 1, 1), 22: (2, 0, 1), 23: (0, 1, 1),
                    24: (3, 1, 2), 25: (0, 1, 1), 26: (1, 1, 1), 27: (2, 1, 1),
                    28: (3, 1, 1), 29: (0, 1, 1), 30: (1, 1, 1), 31: (2, 1, 1),
                    32: (3, 1, 1), 33: (0, 1, 2), 34: (1, 1, 2), 35: (2, 1, 2),
                    36: (3, 1, 2), 37: (0, 1, 2), 38: (1, 1, 2), 39: (2, 1, 2),
                    40: (3, 1, 2), 41: (0, 1, 2), 42: (1, 1, 2), 43: (2, 1, 2),
                    44: (0, 1, 2), 45: (1, 1, 2), 46: (2, 1, 2), 47: (3, 2, 2),
                    48: (2, 2, 1), 49: (3, 2, 1)
                }

        #self.palette16 = {
        #           0:  (0xff, 0xff, 0xff), 1 : (0xdd, 0xdd, 0xdd),
        #           2:  (0xbb, 0xbb, 0xbb), 3 : (0x99, 0x99, 0x99),
        #           4:  (0x77, 0x77, 0x77), 5 : (0x55, 0x55, 0x55),
        #           6:  (0x33, 0x33, 0x33), 7 : (0x00, 0x00, 0x00),
        #           8:  (0x00, 0x44, 0x99), 9 : (0xee, 0xee, 0x00),
        #           10: (0x00, 0xcc, 0x00), 11: (0xdd, 0x00, 0x00),
        #           12: (0xee, 0xee, 0xbb), 13: (0x55, 0x88, 0x00),
        #           14: (0xff, 0xbb, 0x00), 15: (0x00, 0xbb, 0xff)
        #       }
        #
        #self.palette4 = {
        #           0: (0xff, 0xff, 0xff), 1: (0xbb, 0xbb, 0xbb),
        #           2: (0x77, 0x77, 0x77), 3: (0x00, 0x00, 0x00)
        #       }

        self.palette16 = [
                    (0xff, 0xff, 0xff), (0xdd, 0xdd, 0xdd),
                    (0xbb, 0xbb, 0xbb), (0x99, 0x99, 0x99),
                    (0x77, 0x77, 0x77), (0x55, 0x55, 0x55),
                    (0x33, 0x33, 0x33), (0x00, 0x00, 0x00),
                    (0x00, 0x44, 0x99), (0xee, 0xee, 0x00),
                    (0x00, 0xcc, 0x00), (0xdd, 0x00, 0x00),
                    (0xee, 0xee, 0xbb), (0x55, 0x88, 0x00),
                    (0xff, 0xbb, 0x00), (0x00, 0xbb, 0xff)
                ]

        self.palette4 = [
                    (0xff, 0xff, 0xff), (0xbb, 0xbb, 0xbb),
                    (0x77, 0x77, 0x77), (0x00, 0x00, 0x00)
                ]

        if file != None:
            self.read(file)
        else:
            self.new()

    def new(self):

        self.sprites = {}

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
        return str2num(size, s)

    def sprite2rgb(self, file, width, height, h_words, first_bit_used, bpp,
                   palette):

        # Convert sprite to RGB values

        if palette != []:
            has_palette = 1
        else:
            has_palette = 0

        rgb = ''
        ptr = file.tell()*8         # bit offset

        for j in range(0, height):

            row = ''
            row_ptr = ptr + first_bit_used      # bit offset into the image

            for i in range(0, width):

                file.seek(row_ptr >> 3, 0)

                # Conversion depends on bpp value
                if bpp == 32:

                    red = ord(file.read(1))
                    green = ord(file.read(1))
                    blue = ord(file.read(1))
                    row_ptr = row_ptr + 32

                elif bpp == 16:

                    value = self.str2num(2, file.read(2))
                    red   = int( (value & 0x1f) * scale16 )
                    green = int( ((value >> 5) & 0x1f) * scale16 )
                    blue  = int( ((value >> 10) & 0x1f) * scale16 )
                    row_ptr = row_ptr + 16

                elif bpp == 8:

                    if has_palette == 0:

                        # Standard VIDC 256 colours
                        value = ord(file.read(1))
                        red   = ((value & 0x10) >> 1) | (value & 7)
                        green = ((value & 0x40) >> 3) | \
                                ((value & 0x20) >> 3) | (value & 3)
                        blue  = ((value & 0x80) >> 4) | \
                                ((value & 8) >> 1) | (value & 3)
                        red   = int( red * scale8 )
                        green = int( green * scale8 )
                        blue  = int( blue * scale8 )
                    else:
                        # 256 entry palette
                        value = ord(file.read(1))
                        red, green, blue = palette[value][0]

                    row_ptr = row_ptr + 8

                elif bpp == 4:

                    value = ( ord(file.read(1)) >> (row_ptr % 8) ) & 0xf

                    if has_palette == 0:

                        # Standard 16 desktop colours
                        # Look up the value in the standard palette
                        red, green, blue = self.palette16[value]
                    else:
                                                # 16 entry palette
                        red, green, blue = palette[value][0]

                    row_ptr = row_ptr + 4

                elif bpp == 2:

                    value = (ord(file.read(1)) >> (row_ptr % 8) ) & 0x3

                    if has_palette == 0:

                        # Greyscales
                        red, green, blue = self.palette4[value]
                    else:
                                                # 4 entry palette
                        red, green, blue = palette[value][0]

                    row_ptr = row_ptr + 2

                elif bpp == 1:

                    value = (ord(file.read(1)) >> (row_ptr % 8) ) & 1

                    if has_palette == 0:

                        # Black and white
                        red = green = blue = (255*(1-value))
                    else:
                                                # 2 entry palette
                        red, green, blue = palette[value][0]

                    row_ptr = row_ptr + 1

                row = row + chr(red) + chr(green) + chr(blue)

            rgb = rgb + row
            ptr = ptr + (h_words * 32)

        return rgb


    def mask2byte(self, file, width, height, bpp):

        mask = ''

        ptr = file.tell()*8         # bit offset
        image_ptr = 0

        if bpp == 32 or bpp == 16:

            bpp = 1

        # Colour depths below 16 bpp have the same number of bpp in the mask
        bits = bpp * width

        row_size = bits >> 5        # number of words
        if bits % 32 != 0:
            row_size = row_size + 1


        for j in range(0, height):

            row = ''
            row_ptr = ptr           # bit offset into the image

            for i in range(0, width):

                file.seek(row_ptr >> 3, 0)

                # Conversion depends on bpp value
                if bpp == 32:

                    value = (ord(file.read(1)) >> (row_ptr % 8)) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                elif bpp == 16:

                    value = (ord(file.read(1)) >> (row_ptr % 8)) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                elif bpp == 8:

                    value = ord(file.read(1))
                    row_ptr = row_ptr + 8

                elif bpp == 4:

                    value = ( ord(file.read(1)) >> (row_ptr % 8) ) & 0xf
                    value = value | (value << 4)
                    row_ptr = row_ptr + 4

                elif bpp == 2:

                    value = ( ord(file.read(1)) >> (row_ptr % 8) ) & 0x3
                    if value == 3:
                        value = 0xff
                    row_ptr = row_ptr + 2

                elif bpp == 1:

                    # Black and white
                    value = (ord(file.read(1)) >> (row_ptr % 8) ) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                row = row + chr(value)

            mask = mask + row
            ptr = ptr + (row_size * 32)

        return mask


    def mask2rgba(self, file, width, height, bpp, image):

        rgba = ''

        ptr = file.tell()*8         # bit offset
        image_ptr = 0

        if bpp == 32 or bpp == 16:

            bpp = 1

        # Colour depths below 16 bpp have the same number of bpp in the mask
        bits = bpp * width

        row_size = bits >> 5        # number of words
        if bits % 32 != 0:
            row_size = row_size + 1


        for j in range(0, height):

            row = ''
            row_ptr = ptr           # bit offset into the image

            for i in range(0, width):

                file.seek(row_ptr >> 3, 0)

                # Conversion depends on bpp value
                if bpp == 32:

                    value = (ord(file.read(1)) >> (row_ptr % 8)) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                elif bpp == 16:

                    value = (ord(file.read(1)) >> (row_ptr % 8)) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                elif bpp == 8:

                    value = ord(file.read(1))
                    row_ptr = row_ptr + 8

                elif bpp == 4:

                    value = ( ord(file.read(1)) >> (row_ptr % 8) ) & 0xf
                    value = value | (value << 4)
                    row_ptr = row_ptr + 4

                elif bpp == 2:

                    value = ( ord(file.read(1)) >> (row_ptr % 8) ) & 0x3
                    if value == 3:
                        value = 0xff
                    row_ptr = row_ptr + 2

                elif bpp == 1:

                    # Black and white
                    value = (ord(file.read(1)) >> (row_ptr % 8) ) & 1
                    value = value * 0xff
                    row_ptr = row_ptr + 1

                row = row + image[image_ptr:image_ptr+3] + chr(value)
                image_ptr = image_ptr + 3

            rgba = rgba + row
            ptr = ptr + (row_size * 32)

        return rgba


    def read_details(self, file, offset):

        # Go to start of this sprite
        file.seek(offset, 0)

        next = self.str2num(4, file.read(4))

        # We will return a data dictionary
        data = {}

        n = file.read(12)
        name = ''
        for i in n:
            if ord(i)>32:
                name = name + i
            else:
                break

        h_words = self.str2num(4, file.read(4)) + 1
        v_lines = self.str2num(4, file.read(4)) + 1

        data['h_words'] = h_words
        data['v_lines'] = v_lines

        first_bit_used = self.str2num(4, file.read(4))
        last_bit_used   = self.str2num(4, file.read(4))

        data['first bit'] = first_bit_used
        data['last bit'] = last_bit_used

        image_ptr = offset + self.str2num(4, file.read(4))
        mask_ptr  = offset + self.str2num(4, file.read(4))

        mode = self.str2num(4, file.read(4))

        bpp = (mode >> 27)

        if bpp == 0:
        
            mode = mode & 0x3f

            # Information on commonly used modes
            if self.mode_info.has_key(mode):

                log2bpp, xscale, yscale = self.mode_info[mode]
                #xdpi = int(180/xscale)      # was 90
                #ydpi = int(180/yscale)      # was 90
                xdpi = int(90/xscale)        # Old modes have a maximum of
                ydpi = int(90/yscale)        # 90 dots per inch.
                bpp = 1 << log2bpp
            else:
                raise spritefile_error, 'Unknown mode number.'

        else:
            if bpp == 1:
                log2bpp = 0
            elif bpp == 2:
                log2bpp = 1
            elif bpp == 3:
                bpp = 4
                log2bpp = 2
            elif bpp == 4:
                bpp = 8
                log2bpp = 3
            elif bpp == 5:
                bpp = 16
                log2bpp = 4
            elif bpp == 6:
                bpp = 32
                log2bpp = 5
            else:
                return

            xdpi = ((mode >> 1) & 0x1fff)
            ydpi = ((mode >> 14) & 0x1fff)

        data['bpp'] = bpp
        data['log2bpp'] = log2bpp
        data['dpi x'] = xdpi
        data['dpi y'] = ydpi

        has_palette = 0

        palette = []

        # Read palette, if present, putting the values into a list
        while file.tell() < image_ptr:

            file.seek(1,1)      # skip a byte
            # First entry (red, green, blue)
            entry1 = (ord(file.read(1)), ord(file.read(1)), ord(file.read(1)))
            file.seek(1,1)      # skip a byte
            # Second entry (red, green, blue)
            entry2 = (ord(file.read(1)), ord(file.read(1)), ord(file.read(1)))
            palette.append( ( entry1, entry2 ) )

        if palette != []:

            if bpp == 8 and len(palette) < 256:

                if len(palette) == 16:

                    # Each four pairs of entries describes the variation
                    # in a particular colour: 0-3, 4-7, 8-11, 12-15
                    # These sixteen colours describe the rest of the 256
                    # colours.

                    for j in range(16, 256, 16):

                        for i in range(0, 16):

                            entry1, entry2 = palette[i]

                            # Generate new colours using the palette
                            # supplied for the first 16 colours
                            red   = (((j + i) & 0x10) >> 1) | (entry1[0] >> 4)
                            green = (((j + i) & 0x40) >> 3) | \
                                    (((j + i) & 0x20) >> 3) | (entry1[1] >> 4)
                            blue  = (((j + i) & 0x80) >> 4) | (entry1[2] >> 4)
                            red   = int( red * scale8 )
                            green = int( green * scale8 )
                            blue  = int( blue * scale8 )

                            # Append new entries
                            palette.append(
                                ( (red, green, blue), (red, green, blue) ) )

                elif len(palette) == 64:

                    for j in range(64, 256, 64):

                        for i in range(0, 64):

                            entry1, entry2 = palette[i]

                            red   = (((j + i) & 0x10) >> 1) | (entry1[0] >> 4)
                            green = (((j + i) & 0x40) >> 3) | \
                                    (((j + i) & 0x20) >> 3) | (entry1[1] >> 4)
                            blue  = (((j + i) & 0x80) >> 4) | (entry1[2] >> 4)
                            red   = int( red * scale8 )
                            green = int( green * scale8 )
                            blue  = int( blue * scale8 )

                            # Append new entries
                            palette.append(
                                ( (red, green, blue), (red, green, blue) ) )

                data['palette'] = palette
            else:
                data['palette'] = palette

        width = (h_words * (32 >> log2bpp)) - (first_bit_used >> log2bpp) - \
                ((31-last_bit_used) >> log2bpp)
        height = v_lines

        data['width'] = width
        data['height'] = height

        # Obtain image data
        file.seek(image_ptr, 0)

        data['image'] = self.sprite2rgb(file, width, height, h_words,
                                        first_bit_used, bpp, palette)
        data['mode'] = 'RGB'

        # Obtain mask data
        if mask_ptr != image_ptr:

            file.seek(mask_ptr, 0)

            data['image'] = self.mask2rgba(file, width, height, bpp,
                                           data['image'])
            data['mode'] = 'RGBA'

        return name, data, next

    def read(self, file):

        file.seek(0,2)
        size = file.tell()
        file.seek(0,0)

        # Examine the sprites
        number = self.str2num(4, file.read(4))
        offset = self.str2num(4, file.read(4)) - 4
        free   = self.str2num(4, file.read(4)) - 4

        self.sprites = {}

        while (offset < free):

            name, data, next = self.read_details(file, offset)

            self.sprites[name] = data
            offset = offset + next


    def rgb2sprite(self, name):

        data = self.sprites[name]

        # Number of bits per pixel in the original sprite
        bpp = data['bpp']

        # If the sprite didn't have a palette then use a standard one
        if data.has_key('palette'):

            # Explicitly defined palette
            has_palette = 1
            palette = data['palette']

        else:
            # Standard palette - invert the built in palette
            if bpp == 4:

                palette = self.palette4

            elif bpp == 2:

                palette = self.palette2

            else:
                palette = []

            # There is no explicitly defined palette
            has_palette = 0

        # Image data
        image = data['image']

        # Storage mode: RGB or RGBA
        mode = data['mode']

        # Sprite and mask strings
        sprite = ''
        mask = ''

        # If there was either a palette specified or a standard one used
        # then create an inverse.
        if palette != []:

            # Create inverse palette dictionary
            inverse = {}

            for i in range(0, len(palette)):

                inverse[palette[i]] = i

        # Write the image data to the sprite and mask
        ptr = 0

        for j in range(0, data['height']):

            sprite_word = 0
            mask_word = 0
            sprite_ptr = 0
            mask_ptr = 0

            for i in range(0, data['width']):

                # Read the red, green and blue components
                r = ord(image[ptr])
                g = ord(image[ptr + 1])
                b = ord(image[ptr + 2])

                if mode == 'RGBA':

                    a = image[ptr + 3]
                    ptr = ptr + 4
                else:
                    # No alpha component
                    ptr = ptr + 3

                # Write the pixels to the sprite and mask
                if bpp == 32:

                    # Store the components in the sprite word
                    sprite_word = r | (g << 8) | (b << 24)
                    sprite_ptr = 32

                    # Store mask data if relevant
                    if mode == 'RGBA':

                        mask_word = mask_word | ((a == 255) << mask_ptr)
                        mask_ptr = mask_ptr + 1

                elif bpp == 16:

                    # Convert the components to the relevant form
                    half_word = int(r/scale16) | \
                            (int(g/scale16) << 5) | \
                            (int(b/scale16) << 10)

                    sprite_word = sprite_word | (half_word << sprite_ptr)
                    sprite_ptr = sprite_ptr + 16

                    # Store mask data if relevant
                    if mode == 'RGBA':

                        mask_word = mask_word | ((a == 255) << mask_ptr)
                        mask_ptr = mask_ptr + 1

                elif bpp == 8:

                    # If there is a palette then look up the colour index
                    # in the inverse palette dictionary
                    if palette != []:

                        index = inverse[(r, g, b)]
                    else:
                        # Standard palette
                        red = int(r/scale8)
                        green = int(g/scale8)
                        blue = int(b/scale8)

                        index = ((red & 0x8) << 1) | (red & 0x4) | \
                                ((green & 0x8) << 3) | ((green & 0x4) << 3) | \
                                ((blue & 0x8) << 4) | ((blue & 0x4) << 1) | \
                                int((red + green + blue) / 15.0)

                    # Store the contents in the sprite word
                    sprite_word = sprite_word | (index << sprite_ptr)
                    sprite_ptr = sprite_ptr + 8

                    # Store mask data
                    if mode == 'RGBA':

                        if a != 0xff:
                            a = 0

                        mask_word = mask_word | (a << mask_ptr)
                        mask_ptr = mask_ptr + 8

                elif bpp == 4:

                    # Look up bit state in inverse palette
                    index = inverse[(r, g, b)]

                    # Store the contents in the sprite word
                    sprite_word = sprite_word | (index << sprite_ptr)
                    sprite_ptr = sprite_ptr + 4

                    # Store mask data
                    if mode == 'RGBA':

                        if a == 0xff:
                            a = 0xf
                        else:
                            a = 0

                        mask_word = mask_word | (a << mask_ptr)
                        mask_ptr = mask_ptr + 4

                elif bpp == 2:

                    # Look up bit state in inverse palette
                    index = inverse[(r, g, b)]

                    # Store the contents in the sprite word
                    sprite_word = sprite_word | (index << sprite_ptr)
                    sprite_ptr = sprite_ptr + 2

                    # Store mask data
                    if mode == 'RGBA':

                        if a == 0xff:
                            a = 0x3
                        else:
                            a = 0

                        mask_word = mask_word | (a << mask_ptr)
                        mask_ptr = mask_ptr + 2

                elif bpp == 1:

                    if palette != []:

                        # Look up bit state in inverse palette
                        bit = inverse[(r, g, b)]
                    else:
                        # Use red component
                        bit = (bit == 255)

                    # Append bit to byte
                    sprite_word = sprite_word | (bit << sprite_ptr)
                    sprite_ptr = sprite_ptr + 1

                    # Determine mask bit if present
                    if mode == 'RGBA':

                        mask_word = mask_word | ((a == 255) << mask_ptr)
                        mask_ptr = mask_ptr + 1

                # Write the sprite word to the sprite string if the word is
                # full
                if sprite_ptr == 32:

                    # End of word, so reset offset,
                    sprite_ptr = 0
                    # store the word in the sprite string
                    sprite = sprite + self.number(4, sprite_word)
                    # and reset the byte
                    sprite_word = 0

                # Do the same for the mask
                if mask_ptr == 32:

                    mask_ptr = 0
                    mask = mask + self.number(4, mask_word)
                    mask_word = 0

            # Write any remaining sprite data to the sprite string
            if sprite_ptr > 0:

                # store the word in the sprite string
                sprite = sprite + self.number(4, sprite_word)

            # Do the same for the mask
            if mask_ptr > 0:

                mask = mask + self.number(4, mask_word)

        # Determine the actual number of words used per line of
        # the sprite

        width = int( (data['width'] * bpp)/32 )
        excess = (data['width'] % (32/bpp)) != 0

        self.sprites[name]['h_words'] = width + excess
        self.sprites[name]['v_lines'] = data['height']

        if has_palette == 1:

            # Convert the palette into a string
            palette_string = ''

            for (r1, g1, b1), (r2, g2, b2) in palette:

                word = r1 | (g1 << 8) | (b1 << 16)
                palette_string = palette_string + self.number(4, word)
                word = r2 | (g2 << 8) | (b2 << 16)
                palette_string = palette_string + self.number(4, word)

            # Return sprite, mask and palette strings
            return sprite, mask, palette_string
        else:
            return sprite, mask, ''


    def write_details(self, name):

        # The details of the sprite
        data = self.sprites[name]

        # Using the bits per pixel of the image, convert the
        # RGB or RGBA image to an appropriate pixel format.
        sprite, mask, palette = self.rgb2sprite(name)

        # Write the sprite header minus the offset to the next sprite
        header = name[:12] + (12 - len(name))*'\0' + \
             self.number(4, data['h_words'] - 1) + \
             self.number(4, data['v_lines'] - 1) + \
             self.number(4, data['first bit']) + \
             self.number(4, data['last bit']) + \
             self.number(4, 16 + len(palette))

        if mask != '':

            # Offset to mask
            header = header + \
            self.number(4, 12 + len(palette) + len(sprite))
        else:
            # Point to sprite instead
            header = header + \
            self.number(4, 12 + len(palette) )

        # Determine the screen mode from the bpp, xdpi and ydpi
        if data['bpp'] == 1:
            log2bpp = 0
        elif data['bpp'] == 2:
            log2bpp = 1
        elif data['bpp'] == 4:
            log2bpp = 2
        elif data['bpp'] == 8:
            log2bpp = 3
        elif data['bpp'] == 16:
            log2bpp = 4
        elif data['bpp'] == 32:
            log2bpp = 5
        else:
            raise spritefile_error, \
                  'Invalid number of bits per pixel in sprite.'

        mode = (log2bpp << 27) | (int(180/data['dpi x'] << 1)) | \
               (int(180/data['dpi y']) << 14)

        header = header + self.number(4, mode)

        # Write the next sprite offset for this sprite
        # the sprite header + palette + sprite + mask
        file.write(
            self.number(
                4, len(header) + len(palette) + len(sprite) + len(mask) ) )

        # Write the sprite header
        file.write(header)

        # Write the palette
        file.write(palette)

        # Write the image data
        file.write(sprite)

        # Write the mask
        file.write(mask)

        # Return the amount of data written to the file
        return len(header) + len(palette) + len(sprite) + len(mask)


    def write(self, file):

        # Count the sprites in the area
        number = len(self.sprites.keys())
        file.write(self.number(4, number))

        # Put the sprites in the standard place
        offset = 16
        file.write(self.number(4, offset))

        # The free space offset points to after all the sprites
        # so we need to know how much space they take up.

        # Record the position of the free space pointer in the
        # file.
        free_ptr = file.tell()
        # Put a zero word in as a placeholder
        file.write(self.number(4, 0))

        # The offset will start after the number, first sprite offset
        # and free space offset with an additional word added for when
        # the sprite file is imported into a sprite area.
        free = 16

        # Write the sprites to the file
        for name in self.sprites.keys():

            free = free + self.write_details(name)

        # Fill in free space pointer
        file.seek(free_ptr, 0)
        file.write(self.number(free))
