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
from uc2.formats.pes import pes_const, pes_colors
from uc2.formats.sk2 import sk2_model
from uc2 import _, uc2const, sk2const
from uc2.libgeom.trafo import apply_trafo_to_point

from uc2.formats.dst.dst_to_sk2 import EmbroideryMachine


class PEC_to_SK2_Translator(object):
    sk2_doc = None
    sk2_mtds = None
    processor = None
    layer = None
    config = None

    def translate(self, dst_doc, sk2_doc):
        cfg = dst_doc.config
        self.config = cfg
        processor = EmbroideryMachine(self)
        # processor.automatic_thread_cut = pes_const.MM_TO_PES * cfg.automatic_thread_cut
        # processor.delete_empty_stitches = cfg.delete_empty_stitches
        self.processor = processor
        self.sk2_doc = sk2_doc
        self.sk2_mtds = sk2_doc.methods
        self.walk(dst_doc.model.childs)
        # self.translate_desktop_bg()
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
            pes_const.PES_to_SK2_TRAFO
        )
        size = (width or 25.0, height or 25.0)
        orient = uc2const.PORTRAIT
        if width > height:
            orient = uc2const.LANDSCAPE
        page = self.sk2_mtds.get_page()
        self.sk2_mtds.set_page_format(page, [_('Custom size'), size, orient])
        self.sk2_mtds.set_doc_origin(sk2const.DOC_ORIGIN_CENTER)

    def walk(self, command_list):
        processor = self.processor
        for cmd in command_list:
            if cmd.cid == pes_const.CMD_STITCH:
                processor.stitch_to(cmd.dx, cmd.dy)
            elif cmd.cid == pes_const.CMD_JUMP:
                processor.jump_to(cmd.dx, cmd.dy)
            elif cmd.cid == pes_const.CMD_TRIM:
                processor.trim(cmd.dx, cmd.dy)
            elif cmd.cid == pes_const.CMD_CHANGE_COLOR:
                processor.change_color(cmd.dx, cmd.dy)
                self.handle_change_color(cmd)
            elif cmd.cid == pes_const.PEC_HEADER:
                self.handle_pec_header(cmd)
            elif cmd.cid == pes_const.PEC_BODY:
                self.walk(cmd.childs)
            elif cmd.cid == pes_const.CMD_END:
                processor.stop(cmd.dx, cmd.dy)

    def handle_pec_header(self, rec):
        metainfo = [b'', b'', b'', b'']
        metainfo[3] = b64encode(rec.chunk.split(pes_const.DATA_TERMINATOR)[0])
        self.sk2_mtds.set_doc_metainfo(metainfo)

        colors = []
        for idx in rec.index_colors:
            try:
                color = pes_colors.DEFAULT_COLORS[idx-1]
            except (IndexError, KeyError):
                color = pes_colors.REPLACEMENT_COLOR
            colors.append(color)

        self.processor.colors = colors
        self.handle_change_color()

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
                trafo=[] + pes_const.PES_to_SK2_TRAFO
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
        width = abs(self.config.thickness * uc2const.mm_to_pt)
        return [rule, width, color, dash, cap_style, join_style, miter_limit,
                behind_flag, scalable_flag, markers]
