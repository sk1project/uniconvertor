#
#  inspect_beziers - examine bezier polygons
#                    Tamito KAJIYAMA <26 March 2000>
# Copyright (C) 2000 by Tamito KAJIYAMA
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from app import Bezier, Line, ContAngle, ContSmooth, ContSymmetrical

from Tkinter import *

class Viewer(Toplevel):
    type_names = {Line: "Line", Bezier: "Bezier"}
    cont_names = {ContAngle: "ContAngle",
                  ContSmooth: "ContSmooth",
                  ContSymmetrical: "ContSymmetrical"}
    def __init__(self, context):
        Toplevel.__init__(self, context.application.root)
        self.title("Inspect Beziers")
        self.document = context.document
        frame = Frame(self)
        frame.pack(side=BOTTOM, fill=X)
	button = Button(frame, text="Update", command=self.update)
	button.pack(side=LEFT)
	button = Button(frame, text="Dismiss", command=self.destroy)
	button.pack(side=RIGHT)
        sb = Scrollbar(self)
        sb.pack(side=RIGHT, fill=Y)
        self.text = Text(self, width=85, height=25, yscrollcommand=sb.set)
        self.text.pack(side=LEFT, fill=BOTH, expand=1)
        sb.config(command=self.text.yview)
        self.update()
    def update(self):
        self.text.delete("1.0", END)
        n = 0
        for obj in self.document.SelectedObjects():
            if not obj.is_Bezier:
                continue
            self.text.insert(END, "Bezier #%d\n" % (n + 1))
            paths = obj.Paths()
            for i in range(len(paths)):
                self.text.insert(END, "  path #%d\n" % (i + 1))
                for j in range(paths[i].len):
                    s = apply(self.format_segment, paths[i].Segment(j))
                    self.text.insert(END, "    #%d %s\n" % ((j + 1), s))
            self.text.insert(END, "\n")
            n = n + 1
        if n == 0:
            self.text.insert(END, "No bezier polygons selected.")
    def format_segment(self, type, controls, point, cont):
        if type == Line:
            controls = ""
        elif controls:
            controls = " ((%.2f, %.2f), (%.2f, %.2f))" % \
                       (controls[0].x, controls[0].y,
                        controls[1].x, controls[1].y)
        else:
            controls = " ()"
        point = " (%.2f, %.2f) " % (point.x, point.y)
        type = self.type_names[type]
        cont = self.cont_names[cont]
        return type + controls + point + cont

import app.Scripting
app.Scripting.AddFunction('inspect_beziers', 'Inspect Beziers', Viewer,
                             script_type=app.Scripting.AdvancedScript)
