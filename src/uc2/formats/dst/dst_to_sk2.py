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

from base64 import b64encode
from uc2.formats.dst import dst_const
from uc2.formats.dst import dst_colors
from uc2.formats.sk2 import sk2_model
from uc2 import _, uc2const, sk2const, libgeom
from uc2.formats.dst.dst_const import MM_TO_DST

from uc2.libgeom.trafo import apply_trafo_to_point


class EmbroideryMachine(object):
    automatic_thread_cut = 0
    jumps_on_thread_cut = 0
    delete_empty_stitches = False
    delete_empty_jumps = False
    colors = None
    current_color_index = 0
    x = 0
    y = 0
    extents_left = 0
    extents_top = 0
    extents_right = 0
    extents_bottom = 0
    jump_count = 0
    stitch_count = 0
    color_change_count = 0
    trim_count = 0

    def __init__(self, methods):
        self.methods = methods
        self.colors = []
        self.stitch_list = []

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.extents_left = min(self.extents_left, self.x)
        self.extents_right = max(self.extents_right, self.x)
        self.extents_top = min(self.extents_top, self.y)
        self.extents_bottom = max(self.extents_bottom, self.y)

    def get_current_color(self):
        try:
            color = self.colors[self.current_color_index]
        except (IndexError, KeyError):
            color = dst_colors.REPLACEMENT_COLOR
        return color

    def change_color(self, dx, dy):
        self.move(dx, dy)
        self.methods.end_stitch()
        self.color_change_count += 1
        self.current_color_index += 1

    def stop(self, dx, dy):
        self.move(dx, dy)
        self.methods.end_stitch()

    def trim(self, dx, dy):
        self.trim_count += 1
        self.move(dx, dy)
        self.methods.end_stitch()

    def jump_to(self, dx, dy):
        self.jump_count += 1
        if self.delete_empty_jumps and not dx and not dy:
            return
        self.move(dx, dy)
        self.methods.end_stitch()

    def stitch_to(self, dx, dy):
        self.stitch_count += 1
        if self.delete_empty_stitches and not dx and not dy:
            return
        if self.automatic_thread_cut and self.stitch_list:
            last_stitch = self.stitch_list[-1]
            distance = libgeom.distance(last_stitch, (self.x, self.y))
            if distance >= self.automatic_thread_cut:
                self.methods.end_stitch()
        self.move(dx, dy)
        self.stitch_list.append([self.x, self.y])

    def sequin_eject(self, dx, dy):
        self.move(dx, dy)


class DST_to_SK2_Translator(object):
    dst_doc = None
    sk2_doc = None
    sk2_mtds = None
    processor = None
    layer = None

    def translate(self, dst_doc, sk2_doc):
        cfg = dst_doc.config
        processor = EmbroideryMachine(self)
        processor.automatic_thread_cut = MM_TO_DST * cfg.automatic_thread_cut
        processor.delete_empty_stitches = cfg.delete_empty_stitches
        processor.colors = dst_doc.colors or dst_colors.DEFAULT_COLORS

        self.processor = processor
        self.dst_doc = dst_doc
        self.sk2_doc = sk2_doc
        self.sk2_mtds = sk2_doc.methods
        self.handle_change_color()
        self.walk(dst_doc.model.childs)
        self.translate_desktop_bg()
        self.translate_page()
        sk2_doc.model.do_update()

    def translate_desktop_bg(self):
        if len(self.processor.colors) - 1 > self.processor.color_change_count:
            color = self.processor.colors[-1]
            desktop_bg = self.sk2_doc.cms.get_rgb_color(color)[1]
            self.sk2_mtds.set_desktop_bg(desktop_bg)

    def translate_page(self):
        processor = self.processor
        height = max(abs(processor.extents_top), abs(processor.extents_bottom))
        width = max(abs(processor.extents_right), abs(processor.extents_left))
        width, height = apply_trafo_to_point(
            (width * 2, height * 2),
            dst_const.DST_to_SK2_TRAFO
        )
        size = (width or 25.0, height or 25.0)
        orient = uc2const.PORTRAIT
        if width > height:
            orient = uc2const.LANDSCAPE
        page = self.sk2_mtds.get_page()
        self.sk2_mtds.set_page_format(page, [_('Custom size'), size, orient])
        self.sk2_mtds.set_doc_origin(sk2const.DOC_ORIGIN_CENTER)

    def walk(self, command_list):
        sequin_mode = False
        processor = self.processor
        for cmd in command_list:
            if cmd.cid == dst_const.CMD_STITCH:
                processor.stitch_to(cmd.dx, cmd.dy)
            elif cmd.cid == dst_const.CMD_JUMP:
                if sequin_mode:
                    # XXX: didn't check it
                    processor.sequin_eject(cmd.dx, cmd.dy)
                else:
                    processor.jump_to(cmd.dx, cmd.dy)
            elif cmd.cid == dst_const.CMD_CHANGE_COLOR:
                processor.change_color(cmd.dx, cmd.dy)
                self.handle_change_color(cmd)
            elif cmd.cid == dst_const.CMD_SEQUIN_MODE:
                # XXX: didn't check it
                processor.sequin_eject(cmd.dx, cmd.dy)
                sequin_mode = not sequin_mode
            elif cmd.cid == dst_const.DST_HEADER:
                self.handle_doc_metainfo(cmd)
            elif cmd.cid == dst_const.CMD_STOP:
                processor.stop(cmd.dx, cmd.dy)
            else:
                processor.move(cmd.dx, cmd.dy)

    def handle_doc_metainfo(self, rec):
        metainfo = [b'', b'', b'', b'']
        metainfo[3] = b64encode(rec.chunk.split(dst_const.DATA_TERMINATOR)[0])
        self.sk2_mtds.set_doc_metainfo(metainfo)

    def handle_change_color(self, _rec=None):
        page = self.sk2_mtds.get_page()
        if self.layer is None:
            self.layer = self.sk2_mtds.get_layer(page)
        else:
            self.layer = self.sk2_mtds.add_layer(page)
        color = self.processor.get_current_color()
        self.layer.name = color[3]

    def end_stitch(self):
        if len(self.processor.stitch_list) > 1:
            methods = self.sk2_doc.methods
            path = self.processor.stitch_list
            curve = sk2_model.Curve(
                self.sk2_doc.config,
                parent=None,
                style=self.get_style(),
                paths=[[path[0], path[1:], sk2const.CURVE_OPENED]],
                trafo=[] + dst_const.DST_to_SK2_TRAFO
            )
            methods.append_object(curve, self.layer)
            self.processor.stitch_list = []

    def get_style(self):
        fill = []
        text_style = []
        stroke = self.get_stroke()
        return [fill, stroke, text_style, []]

    def get_stroke(self):
        cap_style = sk2const.CAP_ROUND
        join_style = sk2const.JOIN_ROUND
        rule = sk2const.STROKE_MIDDLE
        dash = []
        miter_limit = 4.0
        behind_flag = 0
        scalable_flag = 0
        markers = [[], []]
        color = self.processor.get_current_color()
        width = abs(self.dst_doc.config.thickness * uc2const.mm_to_pt)
        return [rule, width, color, dash, cap_style, join_style, miter_limit,
                behind_flag, scalable_flag, markers]
