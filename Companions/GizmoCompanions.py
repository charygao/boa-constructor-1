#-----------------------------------------------------------------------------
# Name:        GizmoCompanions.py
# Purpose:
#
# Author:      Riaan Booysen
#
# Created:     2002
# RCS-ID:      $Id$
# Copyright:   (c) 2002 - 2004
# Licence:     GPL
#-----------------------------------------------------------------------------
print 'importing Companions.GizmoCompanion'

from wxPython.wx import *

import Preferences, Utils

import BaseCompanions, Companions, ContainerCompanions

import EventCollections, Constructors
from PropEdit import PropertyEditors
import PaletteStore

#-------------------------------------------------------------------------------
from wxPython.gizmos import *

class GizmoDTCMix:
    def writeImports(self):
        return 'from wxPython.gizmos import *'

EventCollections.EventCategories['DynamicSashEvent'] = (EVT_DYNAMIC_SASH_SPLIT, EVT_DYNAMIC_SASH_UNIFY)
EventCollections.commandCategories.append('DynamicSashEvent')

# Derives from Window instead of Container because children must be added in
# the OnSplit event, not at design-time (crashes if children not added in event)
class DynamicSashWindowDTC(GizmoDTCMix, Constructors.WindowConstr, BaseCompanions.WindowDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        BaseCompanions.WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wxDS_MANAGE_SCROLLBARS', 'wxDS_DRAG_CORNER'] + self.windowStyles
        self.ctrlDisabled = true

    def designTimeSource(self, position = 'wxDefaultPosition', size = 'wxDefaultSize'):
        return {'pos':   position,
                'size':  'wxSize(100, 100)',
                'style': 'wxCLIP_CHILDREN',
                'name':  `self.name`}

    def events(self):
        return BaseCompanions.WindowDTC.events(self) + ['DynamicSashEvent']

    def writeImports(self):
        return '\n'.join( (BaseCompanions.WindowDTC.writeImports(self), 
                           GizmoDTCMix.writeImports(self)) )

PaletteStore.paletteLists['ContainersLayout'].append(wxDynamicSashWindow)
PaletteStore.compInfo[wxDynamicSashWindow] = ['wxDynamicSashWindow', DynamicSashWindowDTC]

#-------------------------------------------------------------------------------

LEDNumberCtrlAlignment = [wxLED_ALIGN_LEFT, wxLED_ALIGN_RIGHT,
                          wxLED_ALIGN_CENTER, wxLED_ALIGN_MASK, wxLED_DRAW_FADED]
LEDNumberCtrlAlignmentNames = {'wxLED_ALIGN_LEFT': wxLED_ALIGN_LEFT,
                               'wxLED_ALIGN_RIGHT': wxLED_ALIGN_RIGHT,
                               'wxLED_ALIGN_CENTER': wxLED_ALIGN_CENTER,
                               'wxLED_ALIGN_MASK': wxLED_ALIGN_MASK,
                               'wxLED_DRAW_FADED': wxLED_DRAW_FADED}

class LEDNumberCtrlDTC(GizmoDTCMix, BaseCompanions.WindowDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        BaseCompanions.WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors.update({'Alignment'   : PropertyEditors.EnumPropEdit,
                             'DrawFaded' : PropertyEditors.BoolPropEdit})
        self.windowStyles = ['wxLED_ALIGN_LEFT', 'wxLED_ALIGN_RIGHT',
                             'wxLED_ALIGN_CENTER', 'wxLED_ALIGN_MASK',
                             'wxLED_DRAW_FADED'] + self.windowStyles
        self.options['Alignment'] = LEDNumberCtrlAlignment
        self.names['Alignment'] = LEDNumberCtrlAlignmentNames

    def constructor(self):
        return {'Position': 'pos', 'Size': 'size', 'Style': 'style'}

    def designTimeSource(self, position = 'wxDefaultPosition', size = 'wxDefaultSize'):
        return {'pos':   position,
                'size':  'wxSize(%d, %d)'%(Preferences.dsDefaultControlSize.x,
                                           Preferences.dsDefaultControlSize.y),
                'style': 'wxLED_ALIGN_LEFT'}

    def writeImports(self):
        return '\n'.join( (BaseCompanions.WindowDTC.writeImports(self), 
                           GizmoDTCMix.writeImports(self)) )

PaletteStore.paletteLists['BasicControls'].append(wxLEDNumberCtrl)
PaletteStore.compInfo[wxLEDNumberCtrl] = ['wxLEDNumberCtrl', LEDNumberCtrlDTC]


#-------------------------------------------------------------------------------

class EditableListBoxDTC(GizmoDTCMix, ContainerCompanions.PanelDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        ContainerCompanions.PanelDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors['Strings'] = PropertyEditors.BITPropEditor
        self.ctrlDisabled = true
        self.compositeCtrl = true

    def constructor(self):
        return {'Label': 'label', 'Position': 'pos', 'Size': 'size', 'Name': 'name'}

    def designTimeSource(self, position = 'wxDefaultPosition', size = 'wxDefaultSize'):
        return {'label': `self.name`,
                'pos':   position,
                'size':  self.getDefCtrlSize(),
                'name': `self.name`}

    def writeImports(self):
        return '\n'.join( (ContainerCompanions.PanelDTC.writeImports(self), 
                           GizmoDTCMix.writeImports(self)) )

PaletteStore.paletteLists['ListControls'].append(wxEditableListBox)
PaletteStore.compInfo[wxEditableListBox] = ['wxEditableListBox', EditableListBoxDTC]

#-------------------------------------------------------------------------------

import ListCompanions

class TreeListCtrlDTC(GizmoDTCMix, ListCompanions.TreeCtrlDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        ListCompanions.TreeCtrlDTC.__init__(self, name, designer, parent, ctrlClass)
        ImgLstPropEdit = PropertyEditors.ImageListClassLinkPropEdit
        self.editors.update({'Columns':           TreeListColumnsColPropEdit,
                             'ButtonsImageList':  ImgLstPropEdit,
                             'StateImageList':    ImgLstPropEdit,
                            })
        self.subCompanions['Columns'] = TreeListCtrlColumnsCDTC
        self.ctrlDisabled = true
        self.compositeCtrl = true

    def properties(self):
        props = ListCompanions.TreeCtrlDTC.properties(self)
        props['Columns'] =  ('NoneRoute', None, None)
        return props

    def hideDesignTime(self):
        hdt = ListCompanions.TreeCtrlDTC.hideDesignTime(self)
        hdt.remove('StateImageList')
        return hdt

    def dependentProps(self):
        return ListCompanions.TreeCtrlDTC.dependentProps(self) + ['ButtonsImageList']

    def writeImports(self):
        return ListCompanions.TreeCtrlDTC.writeImports(self) + '\n' +\
               GizmoDTCMix.writeImports(self)

    def designTimeSource(self, position='wxDefaultPosition', size='wxDefaultSize'):
        return ListCompanions.TreeCtrlDTC.designTimeSource(self, position, 
                                                           self.getDefCtrlSize())
    def defaultAction(self):
        self.designer.inspector.props.getNameValue('Columns').propEditor.edit(None)

class TreeListColumnsColPropEdit(PropertyEditors.CollectionPropEdit): pass

class TreeListCtrlColumnsCDTC(BaseCompanions.CollectionDTC):
    propName = 'Columns'
    displayProp = 'text'
    indexProp = '(None)'
    insertionMethod = 'AddColumn'
    deletionMethod = 'RemoveColumn'

    def __init__(self, name, designer, parentCompanion, ctrl):
        BaseCompanions.CollectionDTC.__init__(self, name, designer, parentCompanion, ctrl)
        self.editors = {'Text': PropertyEditors.StrConstrPropEdit}

    def constructor(self):
        return {'Text': 'text'}

    def properties(self):
        props = BaseCompanions.CollectionDTC.properties(self)
        props.update({'Text':  ('IndexRoute', wxTreeListCtrl.GetColumnText, 
                                              wxTreeListCtrl.SetColumnText)})
        return props

    def designTimeSource(self, wId, method=None):
        return {'text': `'%s%d'%(self.propName, wId)`}

    def moveItem(self, idx, dir):
        newIdx = BaseCompanions.CollectionDTC.moveItem(self, idx, dir)
        if newIdx != idx:
            txt = self.control.GetColumnText(idx)
            self.control.RemoveColumn(idx)
            self.control.InsertColumn(newIdx, txt)
        return newIdx

try:
    PaletteStore.paletteLists['ListControls'].append(wxTreeListCtrl)
    PaletteStore.compInfo[wxTreeListCtrl] = ['wxTreeListCtrl', TreeListCtrlDTC]
except NameError:
    # pre 2.4.1.2
    pass
