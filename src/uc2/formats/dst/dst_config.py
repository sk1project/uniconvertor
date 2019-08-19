# -*- coding: utf-8 -*-
#
#  Copyright (C) 2009-2019 by Maxim S. Barabash
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from uc2.utils.config import XmlConfigParser


class DST_Config(XmlConfigParser):
    filename = 'dst_config.xml'
    system_encoding = 'utf-8'
    thickness = 0.72

    # automatic_centering = True
    # delete_empty_stitches = True
    # delete_empty_jumps = True

    automatic_return_to_origin = True
    end_instruction = True
    optimize_number_of_stitches = False
    maximum_stitch_length = 12.1
    maximum_jump_length = 12.1

    borer_offset_x = 0.0
    borer_offset_y = 0.0

    empty_stitches_at_beginning = 0
    empty_jumps_at_beginning = 2

    create_edr_palette = True
