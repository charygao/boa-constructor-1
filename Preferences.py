#----------------------------------------------------------------------
# Name:        Preferences.py
# Purpose:     Global settings
#
# Author:      Riaan Booysen
#
# Created:     1999
# RCS-ID:      $Id$
# Copyright:   (c) 1999, 2000 Riaan Booysen
# Licence:     GPL
#----------------------------------------------------------------------
import os, sys
from os import path

print 'importing wxPython...'
from wxPython import wx

from ImageStore import ImageStore, ZippedImageStore

#-Window sizes------------------------------------------------------------------
wx_screenWidthPerc = 1.0
if wx.wxPlatform == '__WXMSW__':
    wx_screenHeightPerc = 0.94
else:
    wx_screenHeightPerc = 0.87

w32_screenHeightOffset = 20
try:
    import win32api, win32con
except ImportError:
    # thnx Mike Fletcher
    screenWidth = int(wx.wxSystemSettings_GetSystemMetric(wx.wxSYS_SCREEN_X) * wx_screenWidthPerc)
    screenHeight = int(wx.wxSystemSettings_GetSystemMetric(wx.wxSYS_SCREEN_Y) * wx_screenHeightPerc)
else:
    screenWidth = win32api.GetSystemMetrics(win32con.SM_CXFULLSCREEN)
    screenHeight = win32api.GetSystemMetrics(win32con.SM_CYFULLSCREEN) + w32_screenHeightOffset

if wx.wxPlatform == '__WXMSW__':
    from PrefsMSW import *
    wxDefaultFramePos = wx.wxDefaultPosition
    wxDefaultFrameSize = wx.wxDefaultSize
elif wx.wxPlatform == '__WXGTK__':
    from PrefsGTK import *
    wxDefaultFramePos = (screenWidth / 4, screenHeight / 4)
    wxDefaultFrameSize = (screenWidth / 2, screenHeight / 2)

inspWidth = screenWidth * (1/3.75) - windowManagerSide * 2
edWidth = screenWidth - inspWidth + 1 - windowManagerSide * 4

bottomHeight = screenHeight - paletteHeight

#-Miscellaneous-----------------------------------------------------------------

# Should toolbars have flat buttons
flatTools = wx.wxTB_FLAT # 0

# Alternating background colours used in ListCtrls
pastels = 1
pastelMedium = wx.wxColour(235, 246, 255)
pastelLight = wx.wxColour(255, 255, 240)

# Replace the standard file dialog with Boa's own dialog
useBoaFileDlg = 1

# Colour used to display uninitialised window space.
# A control must be placed in this space before valid code can be generated
undefinedWindowCol = wx.wxColour(128, 0, 0)

# Info that will be filled into the comment block. (Edit->Add module info)
# Also used by setup.py
staticInfoPrefs = { 'Purpose':   '',
                    'Author':    '<Your name>',
                    'Copyright': '(c) <Your copyright>',
                    'Licence':   '<Your licence>',
                    'Email':     '<Your email>',
                  }

# Should modules be added to the application if it is the active Model when
# a module is created from the palette
autoAddToApplication = 1

# Load images from image archive or files
useImageArchive = 0

# Draw grid in designer
drawDesignerGridForSubWindows = 1
# Grid draw method: 'lines', 'dots', 'grid', NYI: 'bitmap'
drawGridMethod = 'grid'

# Flag for turning on special checking for european keyboard characters by
# checking for certain codes while ctrl alt is held.
handleSpecialEuropeanKeys = 0

# Auto correct indentation and EOL characters on load, save and refresh
# This only works for Python 2.0 and up
autoReindent = 1

#-Inspector---------------------------------------------------------------------

# Display properties for which source will be generated in Bold
showModifiedProps = 1
# Inspector row height
oiLineHeight = 18
# Default Inspector Names (1st coloumn) width
oiNamesWidth = 100
inspNotebookFlags = 0 #32
##inspPageNames = {'Constr': 'Constructor',
##                 'Props': 'Properties',
##                 'Evts': 'Events',
##                 'Objs': 'Objects'}

#Smaller version if you don't have have high enough res
inspPageNames = {'Constr': 'Constr',
                 'Props': 'Props',
                 'Evts': 'Evts',
                 'Objs': 'Objs'}

#---Other-----------------------------------------------------------------------

pyPath = path.abspath(path.join(os.getcwd(), sys.path[0]))
if useImageArchive:
    IS = ZippedImageStore(pyPath, 'Images.archive')
else:
    IS = ImageStore(pyPath)

def toPyPath(filename):
    return path.join(pyPath, filename)

def toWxDocsPath(filename):
    return path.join(wxWinDocsPath, filename)

if useBoaFileDlg:
    import FileDlg
    wxFileDialog = FileDlg.wxBoaFileDialog
    del FileDlg
else:
    wxFileDialog = wx.wxFileDialog
