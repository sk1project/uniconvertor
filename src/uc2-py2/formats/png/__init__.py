# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015 by Ihor E. Novikov
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

import cairo

from uc2.formats.fallback import im_loader
from uc2.formats.sk2.crenderer import CairoRenderer
from uc2.utils.fsutils import get_fileptr
from uc2.utils.mixutils import merge_cnf

PNG_ID = '\x89\x50\x4e\x47'


def png_loader(appdata, filename=None, fileptr=None, translate=True, cnf=None,
               **kw):
    return im_loader(appdata, filename, fileptr, translate, cnf, **kw)


def png_saver(sk2_doc, filename=None, fileptr=None, translate=True, cnf=None,
              **kw):
    cnf = merge_cnf(cnf, kw)
    if filename and not fileptr:
        fileptr = get_fileptr(filename, True)
    page = sk2_doc.methods.get_page()
    scale = abs(float(cnf.get('scale', 1.0))) or 1.0
    w, h = [scale * item for item in page.page_format[1]]
    trafo = (scale, 0, 0, -scale, w / 2.0, h / 2.0)

    canvas_matrix = cairo.Matrix(*trafo)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))
    ctx = cairo.Context(surface)
    ctx.set_matrix(canvas_matrix)
    
    antialias_flag = not cnf.get('antialiasing') in (False, 0)
    layers = sk2_doc.methods.get_visible_layers(page)
    rend = CairoRenderer(sk2_doc.cms)

    for item in layers:
        rend.antialias_flag = not any([not item.properties[3], not antialias_flag])
        rend.render(ctx, item.childs)

    surface.write_to_png(fileptr)
    fileptr.close()


def check_png(path):
    fileptr = get_fileptr(path)
    mstr = fileptr.read(len(PNG_ID))
    fileptr.close()
    return mstr == PNG_ID
