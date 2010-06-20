# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 1999, 2000, 2002 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


import os, sys, string

path_separator='/'
if os.name=='nt':
	path_separator='\\'

_pkgdir = __path__[0]

temp=string.split(_pkgdir,path_separator)
temp.remove(temp[-1])
_parentdir=string.join(temp,path_separator)

sKVersion = string.strip(open(os.path.join(_pkgdir, 'VERSION')).read())

for _dir in ('modules', 'Base'):
	__path__.insert(0, os.path.join(_pkgdir, _dir))

dir = os.path.join(_parentdir, 'app')
dir = os.path.join(dir, 'modules')
if os.path.isdir(dir):
	sys.path.insert(1, dir)

message_dir = os.path.join(sys.path[0], 'Resources')
message_dir = os.path.join(message_dir, 'Messages')
try:
	from intl import gettext, dgettext, bindtextdomain
	import intl, locale
	try:
		locale.setlocale(locale.LC_ALL, "")
	except:
		# if we can't set the locale we might not be able to get
		# properly translated messages
		print "Can't set locale." \
				" Please check your LANG and LC_* environment variables"
	intl.textdomain("sketch")
	bindtextdomain("sketch", message_dir)
except ImportError:
	def gettext(text):
		return text
	def dgettext(domain, text):
		return text
	def bindtextdomain(*args):
		pass
_ = gettext



####Info variables for progress
info1=None
info2=None
info3=None
info_win=None
#######################################

from conf import const

from _sketch import Point, Polar, PointType
NullPoint = Point(0, 0)

from conf.configurator import Configurator
config = Configurator(base_dir=_parentdir)

from managers.colormanager import ColorManager
colormanager=ColorManager()


from _sketch import Rect, PointsToRect, UnionRects, IntersectRects, EmptyRect, InfinityRect, RectType
UnitRect = Rect(0, 0, 1, 1)

from _sketch import Trafo, Scale, Translation, Rotation, SingularMatrix, TrafoType
Identity = Trafo(1, 0, 0, 1, 0, 0)
IdentityMatrix = Identity.matrix()

from _sketch import CreatePath, RectanglePath, RoundedRectanglePath, approx_arc, CreateFontMetric, SKCache, TransformRectangle
from _sketch import ContAngle, ContSmooth, ContSymmetrical, SelNone, SelNodes, SelSegmentFirst, SelSegmentLast, Bezier, Line

# import config
# config.init_directories(_parentdir)


from events.skexceptions import *
from events.undo import Undo, UndoList, CreateListUndo, CreateMultiUndo, UndoAfter, UndoRedo, NullUndo
from events.connector import Connect, Disconnect, Issue, RemovePublisher, Subscribe, Publisher, QueueingPublisher

receiver=None

def updateInfo(inf1='',inf2='',inf3=0):
	if not receiver is None:
		receiver(inf1,inf2,inf3)


command_classes = []

def RegisterCommands(aclass):
	for cmd in aclass.commands:
		cmd.SetClass(aclass)
	command_classes.append(aclass)


# from Graphics.base import GraphicsObject, Primitive

from Graphics.arrow import StandardArrows, Arrow
from Graphics.properties import Style, FillStyle, EmptyFillStyle, LineStyle, EmptyLineStyle, PropertyStack, EmptyProperties

from Graphics.blend import MismatchError, Blend, BlendTrafo
from Graphics.blendgroup import BlendGroup, CreateBlendGroup, BlendInterpolation

from Graphics.color import CreateRGBColor, XRGBColor, CreateCMYKColor, StandardColors, ParseSKColor
from Graphics.compound import Compound, EditableCompound
from Graphics.dashes import StandardDashes

from Graphics.document import EditDocument, SelectionMode, EditMode
Document = EditDocument

from sk1libs.ft2engine import GetFont
from Graphics.gradient import MultiGradient, CreateSimpleGradient
from Graphics.graphics import SimpleGC, GraphicsDevice, InvertingDevice, HitTestDevice

from Graphics.group import Group
from Graphics.guide import GuideLine
from Graphics.image import Image, load_image, ImageData
from Graphics.layer import Layer, GuideLayer, GridLayer

from Graphics.maskgroup import MaskGroup

from Graphics.pattern import EmptyPattern, SolidPattern, HatchingPattern, LinearGradient, RadialGradient, ConicalGradient, ImageTilePattern

from Graphics.plugobj import PluginCompound, TrafoPlugin

from Graphics.rectangle import Rectangle, RectangleCreator
from Graphics.ellipse import Ellipse, EllipseCreator
from Graphics.bezier import PolyBezier, PolyBezierCreator, PolyLineCreator, CombineBeziers, CreatePath, ContAngle, ContSmooth, ContSymmetrical

from Graphics.psdevice import PostScriptDevice


from Graphics.text import SimpleText, SimpleTextCreator, PathText


def init_lib():
	from sk1libs import filters
# 	config.load_user_preferences()
	Issue(None, const.INITIALIZE)

def init_ui():
	pass

def init_modules_from_widget(root):
	pass
