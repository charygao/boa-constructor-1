#-----------------------------------------------------------------------------
# Name:        FrameCompanions.py
# Purpose:     
#
# Author:      Riaan Booysen
#
# Created:     2002
# RCS-ID:      $Id$
# Copyright:   (c) 2002
# Licence:     GPL
#-----------------------------------------------------------------------------
print 'importing Companions.FrameCompanions'

from wxPython.wx import *

from BaseCompanions import ContainerDTC

from Constructors import *
from EventCollections import *

from PropEdit.PropertyEditors import *
from PropEdit.Enumerations import *

from Preferences import wxDefaultFrameSize, wxDefaultFramePos

class BaseFrameDTC(ContainerDTC):
    def __init__(self, name, designer, frameCtrl):
        ContainerDTC.__init__(self, name, designer, None, None)
        self.control = frameCtrl

    def extraConstrProps(self):
        return {}

    def dontPersistProps(self):
        # Note this is a workaround for a problem on wxGTK where the size
        # passed to the frame constructor is actually means ClientSize on wxGTK.
        # By having this property always set, this overrides the frame size
        # and uses the same size on Win and Lin
        props = ContainerDTC.dontPersistProps(self)
        props.remove('ClientSize')
        return props

    def properties(self):
        props = ContainerDTC.properties(self)
        del props['Anchors']
        return props

    def hideDesignTime(self):
        hdt = ContainerDTC.hideDesignTime(self) + ['Label', 'Constraints']
        hdt.remove('Title')
        return hdt

    def generateWindowId(self):
        if self.designer:
            self.id = Utils.windowIdentifier(self.designer.GetName(), '')
        else: self.id = `wxNewId()`

    def events(self):
        return ContainerDTC.events(self) + ['FrameEvent']

    def SetName(self, oldValue, newValue):
        self.name = newValue
        self.designer.renameFrame(oldValue, newValue)

    def updatePosAndSize(self):
        ContainerDTC.updatePosAndSize(self)
        # Argh, this is needed so that ClientSize is up to date
        if self.textPropList:
            for prop in self.textPropList:
                if prop.prop_name == 'ClientSize':
                    size = self.control.GetClientSize()
                    prop.params = ['wxSize(%d, %d)' % (size.x, size.y)]


class FramesConstr(PropertyKeywordConstructor):
    def constructor(self):
        return {'Title': 'title', 'Position': 'pos', 'Size': 'size',
                'Style': 'style', 'Name': 'name'}

class FrameDTC(FramesConstr, BaseFrameDTC):
    #wxDocs = HelpCompanions.wxFrameDocs
    def __init__(self, name, designer, frameCtrl):
        BaseFrameDTC.__init__(self, name, designer, frameCtrl)

        self.editors.update({'StatusBar': StatusBarClassLinkPropEdit,
                             'MenuBar': MenuBarClassLinkPropEdit,
                             'ToolBar': ToolBarClassLinkPropEdit })
        self.triggers.update({'ToolBar': self.ChangeToolBar,
                              'StatusBar': self.ChangeStatusBar})
        self.windowStyles = ['wxDEFAULT_FRAME_STYLE', 'wxICONIZE',
              'wxMINIMIZE', 'wxMAXIMIZE', 'wxSTAY_ON_TOP', 'wxSYSTEM_MENU',
              'wxRESIZE_BORDER', 'wxTHICK_FRAME', 'wxFRAME_FLOAT_ON_PARENT',
              'wxFRAME_TOOL_WINDOW'] + self.windowStyles

    def designTimeSource(self):
        return {'title': `self.name`,
                'pos':   `wxDefaultFramePos`,
                'size':  `wxDefaultFrameSize`,
                'name':  `self.name`,
                'style': 'wxDEFAULT_FRAME_STYLE'}

    def dependentProps(self):
        return BaseFrameDTC.dependentProps(self) + \
          ['ToolBar', 'MenuBar', 'StatusBar']

    def notification(self, compn, action):
        BaseFrameDTC.notification(self, compn, action)
        if action == 'delete':
            # StatusBar
            sb = self.control.GetStatusBar()
            if sb and sb == compn.control:
                self.propRevertToDefault('StatusBar', 'SetStatusBar')
                self.control.SetStatusBar(None)

            # MenuBar
            # XXX MenuBar's have to be handled with care
            # XXX and can only be connected to a frame once
            # XXX Actually not even once!
            mb = self.control.GetMenuBar()
            if mb and `mb` == `compn.control`:
                if wxPlatform == '__WXGTK__':
                    raise 'May not delete a wxMenuBar, it would cause a segfault on wxGTK'
                self.propRevertToDefault('MenuBar', 'SetMenuBar')
                self.control.SetMenuBar(None)
                #if wxPlatform == '__WXGTK__':
                #    wxLogWarning('GTK only allows connecting the wxMenuBar once to the wxFrame')

            # ToolBar
            tb = self.control.GetToolBar()
            if tb and `tb` == `compn.control`:
                self.propRevertToDefault('ToolBar', 'SetToolBar')
                self.control.SetToolBar(None)

    def updatePosAndSize(self):
        # XXX Delete links to frame bars so client size is accurate
        self.control.SetToolBar(None)
        self.control.SetStatusBar(None)
        if wxPlatform != '__WXGTK__':
            self.control.SetMenuBar(None)

        BaseFrameDTC.updatePosAndSize(self)

    def ChangeToolBar(self, oldValue, newValue):
        if newValue:
            self.designer.connectToolBar(newValue)
        else:
            self.designer.disconnectToolBar(oldValue)

    def ChangeStatusBar(self, oldValue, newValue):
        pass
        # XXX Cannot refresh designer because statusbar not yet connected


EventCategories['DialogEvent'] = (EVT_INIT_DIALOG,)
class DialogDTC(FramesConstr, BaseFrameDTC):
    #wxDocs = HelpCompanions.wxDialogDocs
    def __init__(self, name, designer, frameCtrl):
        BaseFrameDTC.__init__(self, name, designer, frameCtrl)
        self.windowStyles = ['wxDIALOG_MODAL', 'wxDIALOG_MODELESS',
              'wxCAPTION', 'wxDEFAULT_DIALOG_STYLE', 'wxRESIZE_BORDER',
              'wxTHICK_FRAME', 'wxSTAY_ON_TOP', 'wxNO_3D', 'wxDIALOG_NO_PARENT']\
              + self.windowStyles

    def hideDesignTime(self):
        # Because the Designer is actually a wxFrame pretending to be a
        # wxDialog, introspection will pick up wxFrame spesific properties
        # which must be supressed
        return BaseFrameDTC.hideDesignTime(self) + ['ToolBar', 'MenuBar',
              'StatusBar', 'Icon']

    def designTimeSource(self):
        return {'title': `self.name`,
                'pos':   `wxDefaultFramePos`,
                'size':  `wxDefaultFrameSize`,
                'name':  `self.name`,
                'style': 'wxDEFAULT_DIALOG_STYLE'}

    def events(self):
        return BaseFrameDTC.events(self) + ['DialogEvent']

class MiniFrameDTC(FramesConstr, FrameDTC):
    #wxDocs = HelpCompanions.wxMiniFrameDocs
    def __init__(self, name, designer, frameCtrl):
        FrameDTC.__init__(self, name, designer, frameCtrl)
        self.windowStyles.extend(['wxTINY_CAPTION_HORIZ', 'wxTINY_CAPTION_VERT'])

class MDIParentFrameDTC(FramesConstr, FrameDTC):
    #wxDocs = HelpCompanions.wxMDIParentFrameDocs
    def designTimeSource(self):
        dts = FrameDTC.designTimeSource(self)
        dts.update({'style': 'wxDEFAULT_FRAME_STYLE | wxVSCROLL | wxHSCROLL'})
        return dts

class MDIChildFrameDTC(FramesConstr, FrameDTC):
    #wxDocs = HelpCompanions.wxMDIChildFrameDocs
    pass

class PopupWindowDTC(ContainerDTC):
    suppressWindowId = true
    def __init__(self, name, designer, frameCtrl):
        ContainerDTC.__init__(self, name, designer, None, None)
        self.control = frameCtrl
        self.editors['Flags'] = FlagsConstrPropEdit
        # XXX should rather be enumerated
        self.windowStyles = ['wxSIMPLE_BORDER', 'wxDOUBLE_BORDER',
                             'wxSUNKEN_BORDER', 'wxRAISED_BORDER',
                             'wxSTATIC_BORDER', 'wxNO_BORDER']
    def properties(self):
        props = ContainerDTC.properties(self)
        del props['Anchors']
        return props

    def constructor(self):
        return {'Flags': 'flags'}

    def designTimeSource(self):
        return {'flags': 'wxSIMPLE_BORDER'}

    def hideDesignTime(self):
        return ContainerDTC.hideDesignTime(self) + ['ToolBar', 'MenuBar',
              'StatusBar', 'Icon', 'Anchors', 'Constraints', 'Label']

    def SetName(self, oldValue, newValue):
        self.name = newValue
        self.designer.renameFrame(oldValue, newValue)

EventCategories['PanelEvent'] = (EVT_SYS_COLOUR_CHANGED,)

class FramePanelDTC(WindowConstr, BaseFrameDTC):
    #wxDocs = HelpCompanions.wxPanelDocs
    suppressWindowId = false
    def __init__(self, name, designer, frameCtrl):
        BaseFrameDTC.__init__(self, name, designer, frameCtrl)

        self.editors['DefaultItem'] = ButtonClassLinkPropEdit
        self.windowStyles.insert(0, 'wxTAB_TRAVERSAL')

    def hideDesignTime(self):
        return BaseFrameDTC.hideDesignTime(self) + ['ToolBar', 'MenuBar',
              'StatusBar', 'Icon', 'Title', 'Anchors']

    def designTimeSource(self, position = 'wxDefaultPosition', size = 'wxDefaultSize'):
        return {'pos':   position,
                'size': self.getDefCtrlSize(),
                'style': 'wxTAB_TRAVERSAL',
                'name':  `self.name`}

    def events(self):
        # skip frame events
        return ContainerDTC.events(self) + ['PanelEvent']

    def dependentProps(self):
        return BaseFrameDTC.dependentProps(self) + ['DefaultItem']

class wxFramePanel(wxPanel): pass

#-------------------------------------------------------------------------------
import PaletteStore

PaletteStore.compInfo.update({wxApp: ['wxApp', None],
    wxFrame: ['wxFrame', FrameDTC],
    wxDialog: ['wxDialog', DialogDTC],
    wxMiniFrame: ['wxMiniFrame', MiniFrameDTC],
    wxMDIParentFrame: ['wxMDIParentFrame', MDIParentFrameDTC],
    wxMDIChildFrame: ['wxMDIChildFrame', MDIChildFrameDTC],
    wxPopupWindow: ['wxPopupWindow', PopupWindowDTC],
    wxPopupTransientWindow: ['wxPopupTransientWindow', PopupWindowDTC],
    wxFramePanel: ['wxFramePanel', FramePanelDTC],
})