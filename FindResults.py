#-----------------------------------------------------------------------------
# Name:        FindResults.py
# Purpose:     
#
# Author:      Tim Hochberg
#
# Created:     2001/29/08
# RCS-ID:      $Id$
# Copyright:   (c) 2001 Tim Hochberg,
#              but substantially derived from code (c) by Riaan Booysen
# Licence:     GPL
#-----------------------------------------------------------------------------


from os import path
from wxPython.wx import *
from Views.EditorViews import ListCtrlView, ClosableViewMix

class FindResults(ListCtrlView, ClosableViewMix):
    gotoLineBmp = 'Images/Editor/GotoLine.bmp'
    viewName = 'Find Results'
    
    def __init__(self, parent, model):
        ClosableViewMix.__init__(self, 'find results')
        ListCtrlView.__init__(self, parent, model, wxLC_REPORT,
          ( ('Goto match', self.OnGoto, self.gotoLineBmp, ()),
          ) + self.closingActionItems, 0)

        self.InsertColumn(0, 'Module', width = 100)
        self.InsertColumn(1, 'Line no', wxLIST_FORMAT_CENTRE, 40)
        self.InsertColumn(2, 'Col', wxLIST_FORMAT_CENTRE, 40)
        self.InsertColumn(3, 'Text', width = 550)

        self.results = {}
        self.listResultIdxs = []
        self.tabName = 'Results'
        self.findPattern = ''
        self.active = true
        self.model = model

    def refreshCtrl(self):
        ListCtrlView.refreshCtrl(self)
        i = 0
        self.listResultIdxs = []
        for mod in self.results.keys():
            for result in self.results[mod]:
                self.listResultIdxs.append((mod, result))
                i = self.addReportItems(i, (path.basename(mod), `result[0]`,
                  `result[1]`, string.strip(result[2])) )

        self.model.editor.statusBar.setHint('%d matches of "%s".'%(i, self.findPattern))

        self.pastelise()

    def OnGoto(self, event):
        if self.selected >= 0:
            modName = self.listResultIdxs[self.selected][0]
            if modName != self.model.filename:
                model, controller = self.model.editor.openOrGotoModule(modName)
            else:
                model = self.model
            srcView = model.views['Source']
            srcView.focus()
            foundInfo = self.listResultIdxs[self.selected][1]
            srcView.lastSearchPattern = self.findPattern
            srcView.lastSearchResults = self.results[modName]
            try:
                srcView.lastMatchPosition = self.results[modName].index(foundInfo)
            except:
                srcView.lastMatchPosition = 0
                print 'foundInfo not found'
            srcView.selectSection(foundInfo[0]-1, foundInfo[1]-1, self.findPattern)

    def OnRerun(self, event):
        pass
    
   