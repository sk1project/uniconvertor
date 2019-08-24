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

from uc2.formats.dst import dst_model, dst_const
from uc2 import _, uc2const, sk2const, cms, libgeom
from uc2.formats.dst.dst_const import MM_TO_DST
import math


class EmbroideryMachine(object):
    max_distance = dst_const.MAX_DISTANCE
    max_stitch_length = dst_const.MAX_DISTANCE
    max_jump_length = dst_const.MAX_DISTANCE
    optimize_number_of_stitches = False
    x = 0
    y = 0
    borer_offset_x = 0
    borer_offset_y = 0
    stitch_count = 0
    extents_left = 0
    extents_top = 0
    extents_right = 0
    extents_bottom = 0
    command_color_change = 0

    def __init__(self, dst_doc):
        self.dst_doc = dst_doc
        self.dst_mt = dst_doc.model
        self.header = dst_model.DstHeader()
        self.dst_mt.childs.append(self.header)

    def append_stitch(self, cmd):
        self.stitch_count += 1
        self.dst_mt.childs.append(cmd)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.extents_left = min(self.extents_left, self.x)
        self.extents_right = max(self.extents_right, self.x)
        self.extents_top = min(self.extents_top, self.y)
        self.extents_bottom = max(self.extents_bottom, self.y)

    def jump_to(self, x, y):
        max_distance = min(self.max_distance, self.max_jump_length)
        if not self.optimize_number_of_stitches:
            distance = libgeom.distance((self.x, self.y), (x, y))
            number_pieces = math.ceil(distance / max_distance) or 1.0
            max_distance = distance / number_pieces
        self._to(x, y, dst_const.CMD_JUMP, max_distance)

    def stitch_to(self, x, y):
        max_distance = min(self.max_distance, self.max_stitch_length)
        if not self.optimize_number_of_stitches:
            distance = libgeom.distance((self.x, self.y), (x, y))
            number_pieces = math.ceil(distance / max_distance) or 1.0
            max_distance = distance / number_pieces
        self._to(x, y, dst_const.CMD_STITCH, max_distance)

    def stitch_from(self, x, y):
        max_distance = min(self.max_distance, self.max_stitch_length)
        current_point = (self.x, self.y)
        end_point = (x, y)
        distance = libgeom.distance((self.x, self.y), end_point)
        if distance > max_distance:
            coef = (distance - max_distance / 2.0) / distance
            start_x, start_y = libgeom.midpoint(current_point, end_point, coef)
            self.jump_to(start_x, start_y)
        self.stitch_to(x, y)

    def chang_color(self):
        self.command_color_change += 1
        cmd = dst_model.DstCmd()
        cmd.cid = dst_const.CMD_CHANGE_COLOR
        self.append_stitch(cmd)

    def trim(self):
        sign_x = -1 if self.x > 0 else 1
        self.jump_to(self.x + 3 * sign_x, self.y)
        self.jump_to(self.x - 2 * sign_x, self.y)
        self.jump_to(self.x - 1 * sign_x, self.y)

    def stop(self):
        cmd = dst_model.DstCmd()
        cmd.cid = dst_const.CMD_STOP
        self.append_stitch(cmd)

    def end(self):
        cmd = dst_model.DstCmd()
        cmd.cid = dst_const.DATA_TERMINATOR
        self.dst_mt.childs.append(cmd)

    def _to(self, x, y, cid, max_distance):
        end_point = (x, y)
        while True:
            current_point = (self.x, self.y)
            distance = libgeom.distance(current_point, end_point)

            if distance > 0:
                coef = min(distance, max_distance) / distance
                x, y = libgeom.midpoint(current_point, end_point, coef)

            cmd = dst_model.DstCmd()
            cmd.cid = cid  # TODO: if long stitch used dst_const.CMD_JUMP
            cmd.dx = int(x) - self.x
            cmd.dy = int(y) - self.y

            self.append_stitch(cmd)
            self.move(cmd.dx, cmd.dy)
            if distance <= max_distance:
                break


class SK2_to_DST_Translator(object):
    sk2_doc = None
    sk2_mtds = None
    dst_doc = None
    trafo = None
    palette = None
    processor = None

    def translate(self, sk2_doc, dst_doc):
        cfg = dst_doc.config
        origin_x = - int(MM_TO_DST * cfg.borer_offset_x)
        origin_y = - int(MM_TO_DST * cfg.borer_offset_y)

        processor = EmbroideryMachine(dst_doc)
        processor.x = origin_x
        processor.y = origin_y
        processor.max_stitch_length = MM_TO_DST * cfg.maximum_stitch_length
        processor.max_jump_length = MM_TO_DST * cfg.maximum_jump_length
        self.processor = processor
        self.sk2_doc = sk2_doc
        self.sk2_mtds = sk2_doc.methods
        self.dst_doc = dst_doc
        self.trafo = [] + dst_const.SK2_to_DST_TRAFO
        self.palette = []

        header = dst_model.DstHeader()
        self.dst_doc.model.childs = [header]

        page = self.sk2_mtds.get_page()
        self.translate_page(page)

        if cfg.automatic_return_to_origin:
            self.processor.jump_to(origin_x, origin_y)

        self.processor.stop()
        if cfg.end_instruction:
            self.processor.end()

        self.translate_bg_color()

        metadata = self.metadata()
        header.metadata.update(metadata)
        dst_doc.palette = self.palette

    def metadata(self):
        metadata = dict()
        metadata['LA'] = 'Name'
        metadata['ST'] = int(self.processor.stitch_count)
        metadata['CO'] = int(self.processor.command_color_change)
        metadata['+X'] = int(abs(self.processor.extents_right))
        metadata['-X'] = int(abs(self.processor.extents_left))
        metadata['+Y'] = int(abs(self.processor.extents_bottom))
        metadata['-Y'] = int(abs(self.processor.extents_top))
        metadata['AX'] = int(self.processor.x)
        metadata['AY'] = int(self.processor.y)
        metadata['MX'] = 0
        metadata['MY'] = 0
        metadata['PD'] = b'******'
        return metadata

    def translate_page(self, page):
        cfg = self.dst_doc.config
        # Empty jumps at Start for Sync
        for _i in range(0, cfg.empty_jumps_at_beginning or 0):
            self.processor.jump_to(0, 0)

        # Empty stitches at Start for Sync
        for _i in range(0, cfg.empty_stitches_at_beginning or 0):
            self.processor.stitch_to(0, 0)

        for layer in page.childs:
            if self.sk2_mtds.is_layer_visible(layer):
                self.translate_objs(layer.childs)

    def translate_bg_color(self):
        desktop_bg = self.sk2_mtds.get_desktop_bg()
        hex_color = cms.rgb_to_hexcolor(desktop_bg)
        self.palette.append(hex_color)

    def translate_objs(self, objs):
        for obj in objs:
            if obj.is_primitive:
                self.translate_primitive(obj)
            elif obj.is_group:
                self.translate_group(obj)

    def translate_group(self, obj):
        self.translate_objs(obj.childs)

    def translate_primitive(self, obj):
        curve = obj.to_curve()
        if curve.is_group:
            self.translate_group(curve)
            return
        curve.update()
        trafo = libgeom.multiply_trafo(curve.trafo, self.trafo)
        paths = libgeom.apply_trafo_to_paths(curve.paths, trafo)
        paths = libgeom.flat_paths(paths)
        self.translate_paths(obj.style, paths)

    def translate_paths(self, style, paths):
        if style[1]:
            self.translate_stroke(style, paths)

    def translate_stroke(self, style, paths):
        clr = self.sk2_doc.cms.get_rgb_color(style[1][2])
        hex_color = cms.rgb_to_hexcolor(clr[1])
        if not self.palette:
            self.palette.append(hex_color)

        if self.is_color_changed(hex_color):
            self.palette.append(hex_color)
            self.processor.chang_color()

        for path in paths:
            start_point = path[0]
            points = path[1]
            self.processor.stitch_from(start_point[0], start_point[1])

            for point in points:
                self.processor.stitch_to(point[0], point[1])
            self.processor.trim()

    def is_color_changed(self, hex_color):
        return not (self.palette and self.palette[-1] == hex_color)
