# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#	Constants...
#

#
#	Types of handles
#

# physical
# for rect handles: filled == handle_id & 1


Handle_OpenRect		= 0
Handle_FilledRect	= 1
Handle_SmallOpenRect	= 2
Handle_SmallFilledRect	= 3

Handle_OpenCircle	= 4
Handle_FilledCircle	= 5
Handle_SmallOpenCircle	= 6
Handle_SmallFilledCircle = 7

Handle_SmallOpenRectList = 8

Handle_Line		= 9
Handle_Pixmap		= 10
Handle_Caret		= 11
Handle_PathText         = 12

# logical	XXX should these be moved to config.py?
Handle			= Handle_FilledRect
HandleNode		= Handle_OpenRect
HandleSelectedNode	= Handle_FilledRect
HandleControlPoint	= Handle_SmallFilledRect
HandleLine		= Handle_Line
HandleCurvePoint        = Handle_FilledCircle

#
#
#

# The corners of the unit rectangle
corners = [(0, 0), (1, 0), (1, 1), (0, 1)]


#
#	Standard channel names
#

# common
CHANGED = 'CHANGED'
DOCUMENT = 'DOCUMENT'
MODE = 'MODE'
SELECTION = 'SELECTION'

# dialogs
CLOSED = 'CLOSED'

# TKExt
COMMAND = 'COMMAND'
# also uses SELECTION

# APPLICATION
CLIPBOARD = 'CLIPBOARD'
ADD_TO_SPECIAL_MENU = 'ADD_TO_SPECIAL_MENU'

# Global
INITIALIZE = 'INITIALIZE'
APP_INITIALIZED = 'APP_INITIALIZED'
INIT_READLINE = 'INIT_READLINE'
MOVING = 0

# CANVAS
STATE = 'STATE'
UNDO = 'UNDO'
VIEW = 'VIEW'
POSITION = 'POSITION'
CURRENTINFO = 'CURRENTINFO'

# DOCUMENT
EDITED = 'EDITED'
GRID = 'GRID'
LAYER = 'LAYER'
LAYER_STATE = 'LAYER_STATE';	LAYER_ORDER = 'LAYER_ORDER'
LAYER_COLOR = 'LAYER_COLOR';	LAYER_ACTIVE = 'LAYER_ACTIVE'
LAYOUT = 'LAYOUT'
REDRAW = 'REDRAW'
STYLE = 'STYLE'
UNDO = 'UNDO'
GUIDE_LINES = 'GUIDE_LINES'
PAGE = 'PAGE'

# graphics object
#TRANSFORMED = 'TRANSFORMED'

# command
UPDATE = 'update'

# palette
COLOR1 = 'color1'
COLOR2 = 'color2'

# Drop types
DROP_COLOR = 'COLOR'


#
#       Scripting Access
#

SCRIPT_UNDO = 'SCRIPT_UNDO'
SCRIPT_GET = 'SCRIPT_GET'
SCRIPT_OBJECT = 'SCRIPT_OBJECT'
SCRIPT_OBJECTLIST = 'SCRIPT_OBJECTLIST'

#
#	constants for selections
#

# the same as in curveobject.c
SelectSet = 0
SelectAdd = 1
SelectSubtract = 2
SelectSubobjects = 3
SelectDrag = 4

SelectGuide = 5

# Arc modes. bezier_obj.approx_arc uses these
ArcArc = 0
ArcChord = 1
ArcPieSlice = 2

#
#	X specific stuff
#

#from app.X11 import X

ShiftMask = (1<<0)
LockMask = (1<<1)
ControlMask = (1<<2)
Mod1Mask = (1<<3)
Mod2Mask = (1<<4)
Mod3Mask = (1<<5)
Mod4Mask = (1<<6)
Mod5Mask = (1<<7)

#ShiftMask = X.ShiftMask
#LockMask = X.LockMask
#ControlMask = X.ControlMask
#Mod1Mask = X.Mod1Mask
#Mod2Mask = X.Mod2Mask
#Mod3Mask = X.Mod3Mask
#Mod4Mask = X.Mod4Mask
#Mod5Mask = X.Mod5Mask
MetaMask = Mod1Mask

#Button1Mask = X.Button1Mask
#Button2Mask = X.Button2Mask
#Button3Mask = X.Button3Mask
#Button4Mask = X.Button4Mask
#Button5Mask = X.Button5Mask

Button1Mask            = (1<<8)
Button2Mask            = (1<<9)
Button3Mask            = (1<<10)
Button4Mask            = (1<<11)
Button5Mask            = (1<<12)
AllButtonsMask = Button1Mask | Button2Mask | Button3Mask

#Button1 = X.Button1
#Button2 = X.Button2
#Button3 = X.Button3
#Button4 = X.Button4
#Button5 = X.Button5

#ContextButton	= Button3
#ContextButtonMask = Button3Mask

AllowedModifierMask = ShiftMask | ControlMask | MetaMask
ConstraintMask = ControlMask
AlternateMask = ShiftMask

LineSolid = 0
LineOnOffDash = 1
LineDoubleDash = 2

#AddSelectionMask = ShiftMask
#SubtractSelectionMask = MetaMask

#SubobjectSelectionMask = ControlMask 

##
##	Line Styles
##

#JoinMiter	= X.JoinMiter
#JoinRound	= X.JoinRound
#JoinBevel	= X.JoinBevel
#CapButt		= X.CapButt
#CapRound	= X.CapRound
#CapProjecting	= X.CapProjecting

JoinMiter	= 0
JoinRound	= 1
JoinBevel	= 2
CapButt	= 1
CapRound	= 2
CapProjecting = 3

# cursors

CurStd		= 'top_left_arrow'
CurStd1		= 'top_left_arrow'
CurHandle	= 'crosshair'
CurTurn		= 'exchange'
CurPick		= 'hand2'
CurCreate	= 'crosshair'#'pencil'
CurPlace	= 'crosshair'
CurDragColor	= 'spraycan'
CurHGuide       = 'sb_v_double_arrow'
CurVGuide       = 'sb_h_double_arrow'
CurZoom		= 'plus'	# is replaced by bitmap specification in
CurUp ='based_arrow_up'
CurUpDown = 'sb_v_double_arrow'
CurDown ='based_arrow_down'
CurEdit = 'left_ptr'#'xterm'

# unused as yet
CurHelp		= 'question_arrow'
CurWait		= 'watch'
CurMove		= 'top_left_arrow'#'fleur'

#
# Text Alignment
#
ALIGN_BASE = 0
ALIGN_CENTER = 1
ALIGN_TOP = 2
ALIGN_BOTTOM = 3

ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2