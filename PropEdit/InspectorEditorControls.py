#----------------------------------------------------------------------
# Name:        InspectorEditorControls.py
# Purpose:     
#
# Author:      Riaan Booysen
#
# Created:     1999
# RCS-ID:      $Id$
# Copyright:   (c) 1999, 2000 Riaan Booysen
# Licence:     GPL
#----------------------------------------------------------------------

from wxPython.wx import *
import Preferences
from os import path

class InspectorEditorControl:
    """ Interface for controls that edit values in the Inspector 
        values are stored in the native type of the control       """

    def __init__(self, propEditor, value):
        self.propEditor = propEditor
        self.editorCtrl = None
        self.wID = NewId()
        self.value = value

    def createControl(self):
        if self.editorCtrl: self.editorCtrl.SetFocus()
    
    def destroyControl(self):
        if self.editorCtrl:
     	    self.editorCtrl.Destroy()
     	    self.editorCtrl = None
                    
    def getValue(self):
        pass
    
    def setValue(self, value):
        pass

    # default sizing for controls that span the entire value width
    def setWidth(self, width):
        if self.editorCtrl:
	    height = self.editorCtrl.GetSize().y
	    self.editorCtrl.SetSize(wxSize(width -1, height))

    def setIdx(self, idx):
        if self.editorCtrl: self.editorCtrl.SetPosition(wxPoint(-2, idx*Preferences.oiLineHeight -2))

class BevelIEC(InspectorEditorControl):
    def destroyControl(self):
        if self.bevelTop:
            self.bevelTop.Destroy()
            self.bevelTop = None
            self.bevelBottom.Destroy()
        InspectorEditorControl.destroyControl(self)
        
    def createControl(self, parent, idx, sizeX):
        self.bevelTop = wxPanel(parent, -1, wxPoint(0, idx*Preferences.oiLineHeight -1), wxSize(sizeX, 1))
        self.bevelTop.SetBackgroundColour(wxBLACK)
        self.bevelBottom = wxPanel(parent, -1, wxPoint(0, (idx + 1)*Preferences.oiLineHeight -1), wxSize(sizeX, 1))
        self.bevelBottom.SetBackgroundColour(wxWHITE)
        
    def setWidth(self, width):
        if self.bevelTop:
            self.bevelTop.SetSize(wxSize(width, 1))
            self.bevelBottom.SetSize(wxSize(width, 1))

    def setIdx(self, idx):
        if self.bevelTop:
            self.bevelTop.SetPosition(wxPoint(-2, idx*Preferences.oiLineHeight -1))
            self.bevelBottom.SetPosition(wxPoint(-2, (idx +1)*Preferences.oiLineHeight -1))
#        InspectorEditorControl.setIdx(self, idx)        
        
class TextCtrlIEC(InspectorEditorControl):
    def createControl(self, parent, value, idx, sizeX):
        self.editorCtrl = wxTextCtrl(parent, self.wID, self.propEditor.valueToIECValue(), #self.propEditor.getDisplayValue(), 
         wxPoint(-2, idx*Preferences.oiLineHeight -2), wxSize(sizeX, Preferences.oiLineHeight+3))
        InspectorEditorControl.createControl(self); 
    def getValue(self):
        if self.editorCtrl:
            self.value = self.editorCtrl.GetValue()
        return self.value
        
    def setValue(self, value):
        self.value = value
        if self.editorCtrl:
            self.editorCtrl.SetValue(value)
        
class ChoiceIEC(InspectorEditorControl):
    def createControl(self, parent, idx, sizeX):
        self.editorCtrl = wxChoice(parent, self.wID, 
         wxPoint(-2, idx*Preferences.oiLineHeight -1), wxSize(sizeX, Preferences.oiLineHeight+3),
         self.propEditor.getValues())
        InspectorEditorControl.createControl(self); 
    def getValue(self):
        if self.editorCtrl:
            return self.editorCtrl.GetStringSelection()
    def setValue(self, value):
        if self.editorCtrl:
            self.editorCtrl.SetStringSelection(value)

class ComboIEC(InspectorEditorControl):
    def createControl(self, parent, idx, sizeX):
        self.editorCtrl = wxComboBox(parent, self.wID, self.value,
         wxPoint(-2, idx*Preferences.oiLineHeight -1), wxSize(sizeX, Preferences.oiLineHeight+3),
         self.propEditor.getValues())
        InspectorEditorControl.createControl(self); 
    def getValue(self):
        if self.editorCtrl:
            return self.editorCtrl.GetStringSelection()
    def setValue(self, value):
        if self.editorCtrl:
            self.editorCtrl.SetSelection(self.editorCtrl.FindString(value))

class ButtonIEC(BevelIEC):
    def createControl(self, parent, idx, sizeX, editMeth):
       # XXX use image store
	bmp = wxBitmap(path.join(Preferences.pyPath, 'Images', 'Shared', 'ellipsis.bmp'), wxBITMAP_TYPE_BMP)
        self.editorCtrl = wxBitmapButton(parent, self.wID, bmp, 
          wxPoint(sizeX -18 - 3, idx*Preferences.oiLineHeight +1), 
          wxSize(18, Preferences.oiLineHeight-2))
       	EVT_BUTTON(self.editorCtrl, self.wID, editMeth)
       	BevelIEC.createControl(self, parent, idx, sizeX)

    def setWidth(self, width):
        if self.editorCtrl:
            self.editorCtrl.SetDimensions(width - 18 - 3, self.editorCtrl.GetPosition().y, 
              18, Preferences.oiLineHeight-2)

       	BevelIEC.setWidth(self, width)

    def setIdx(self, idx):
        if self.editorCtrl:
            self.editorCtrl.SetDimensions(self.editorCtrl.GetPosition().x, 
              idx*Preferences.oiLineHeight +1, 18, Preferences.oiLineHeight-2)
##            self.editorCtrl.SetPosition(wxPoint(self.editorCtrl.GetPosition().x, idx*Inspector.oiLineHeight +1))
##	    ## XX why set width, fix
##	    self.editorCtrl.SetSize(wxSize(18, Inspector.oiLineHeight-2))
       	BevelIEC.setIdx(self, idx)
          
          
          
          
          
          
      