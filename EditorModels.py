#----------------------------------------------------------------------
# Name:        EditorModels.py                                         
# Purpose:     Model classes usually representing different types of   
#              source code                                             
#                                                                      
# Author:      Riaan Booysen                                           
#                                                                      
# Created:     1999                                                    
# RCS-ID:      $Id$                                   
# Copyright:   (c) 1999, 2000 Riaan Booysen                            
# Licence:     GPL                                                     
#----------------------------------------------------------------------

# Behind the screen
# beyond interpretation
# essence

""" The model classes represent different types of source code files,
    Different views can be connected to a model  """

# XXX form inheritance
# XXX Dynamically adding buttons to taskbar depending on the model and view

import moduleparse, string, os, sys, re, py_compile
from os import path
import relpath, pprint
from Companions import Companions
import Editor, Debugger, ErrorStack
from Views.DiffView import PythonSourceDiffView
from Views.AppViews import AppCompareView
import Preferences, Utils
from wxPython import wx 
from Utils import AddToolButtonBmpIS
from time import time, gmtime, strftime
from stat import *
from PrefsKeys import keyDefs

from wxPython.lib.dialogs import wxScrolledMessageDialog
import wxPython
from PhonyApp import wxProfilerPhonyApp
import profile

true = 1
false = 0

nl = chr(13)+chr(10)
init_ctrls = '_init_ctrls'
init_coll = '_init_coll_'
init_utils = '_init_utils'
init_props = '_init_props'
init_events = '_init_events'
defEnvPython = '#!/bin/env python\n'
defImport = 'from wxPython.wx import *\n\n'
defSig = '#Boa:%s:%s\n\n'

defCreateClass = '''def create(parent):
    return %s(parent)
\n'''
wid = '[A-Za-z0-9_, ]*'
srchWindowIds = '\[(?P<winids>[A-Za-z0-9_, ]*)\] = '+\
'map\(lambda %s: [wx]*NewId\(\), range\((?P<count>\d)\)\)'
defWindowIds = '''[%s] = map(lambda %s: wxNewId(), range(%d))\n'''

defClass = '''
class %s(%s):
    def '''+init_utils+'''(self): 
        pass

    def '''+init_ctrls+'''(self, prnt): 
        %s.__init__(%s)
        self.'''+init_utils+'''()
        
    def __init__(self, parent): 
        self.'''+init_ctrls+'''(parent)
'''

# This the closest I get to destroying partially created 
# frames without mucking up my indentation. 
# This doesn't not handle the case where the constructor itself fails
# Replace defClass with this in line 412 if you feel the need

defSafeClass = '''
class %s(%s):
    def '''+init_utils+'''(self): 
        pass

    def '''+init_ctrls+'''(self, prnt): 
        %s.__init__(%s)
        
    def __init__(self, parent): 
        self.'''+init_utils+'''()
        try: 
            self.'''+init_ctrls+'''(parent)

            # Your code
        except: 
            self.Destroy()
            import traceback
            traceback.print_exc()
            raise
'''

defApp = """import %s

modules = {'%s' : [1, 'Main frame of Application', '%s.py']}

class BoaApp(wxApp):
    def OnInit(self):
        self.main = %s.create(None)
        self.main.Show(true)
        self.SetTopWindow(self.main)
        return true

def main():
    application = BoaApp(0)
    application.MainLoop()

if __name__ == '__main__':
    main()"""

defInfoBlock = """#-----------------------------------------------------------------------------
# Name:        %s
# Purpose:     %s
#                
# Author:      %s
#                
# Created:     %s
# RCS-ID:      %s
# Copyright:   %s
# Licence:     %s
#-----------------------------------------------------------------------------
""" 
class EditorModel:
    defaultName = 'abstract'
    bitmap = 'None'
    imgIdx = -1
    closeBmp = 'Images/Editor/Close.bmp'
    objCnt = 0
    def __init__(self, name, data, editor, saved):
        self.active = false
        self.data = data
        self.savedAs = saved
        self.filename = name
        self.editor = editor
        
        self.views = {}
        self.modified = not saved
        self.viewsModified = []
        
        self.objCnt = self.objCnt + 1
    
    def __del__(self):
        self.objCnt = self.objCnt - 1
        print '__del__', self.__class__.__name__

    def destroy(self):
        print 'destroy', self.__class__.__name__
#        for i in self.views.values():
#            print sys.getrefcount(i)
        
        del self.views
        del self.viewsModified
        del self.editor        

    def addTools(self, toolbar):
        AddToolButtonBmpIS(self.editor, toolbar, self.closeBmp, 'Close', self.editor.OnClosePage)

    def addMenu(self, menu, wId, label, accls, code = ()):
        menu.Append(wId, label)
        if code:
            accls.append((code[0], code[1], wId),)
    
    def addMenus(self, menu):
        self.addMenu(menu, Editor.wxID_EDITORCLOSEPAGE, 'Close', (keyDefs['Close']))
        return []

    def reorderFollowingViewIdxs(self, idx):
##        print 'reorder', self.views.values 
        for view in self.views.values():
##            print view.viewName
            if view.pageIdx > idx:
                view.pageIdx = view.pageIdx - 1

    def load(self, notify = true):
        """ Loads contents of data from file specified by self.filename. 
            Note: Load not really used currently objects are constructed
                  with their data as parameter """
        f = open(self.filename, 'r')
        self.data = f.read()
        f.close()
        self.modified = false
        self.saved = false
        self.update()
        if notify: self.notify()
    
    def save(self):
        """ Saves contents of data to file specified by self.filename. """
        if self.filename:
            try:
                f = open(self.filename, 'w')
            except IOError, message:
                dlg = wx.wxMessageDialog(self.editor, 'Could not save\n'+message.strerror,
                                      'Error', wx.wxOK | wx.wxICON_ERROR)
                try: dlg.ShowModal()
                finally: dlg.Destroy()
            else:
                f.write(self.data)
                f.close()
                self.modified = false
        else:
            raise 'No filename'
    
    def saveAs(self, filename):
        """ Saves contents of data to file specified by filename.
            Override this to catch name changes. """
        self.filename = filename
        self.save()
        self.savedAs = true
            
    def notify(self):
        """ Update all views connected to this model.
            This method must be called after changes were made to the model """
        for view in self.views.values():
            view.update()

    def update(self):
        """ Rebuild additional derived structure, called when data is changed """

    def refreshFromViews(self):
        for view in self.viewsModified:
            self.views[view].refreshModel()

class FolderModel(EditorModel):
    modelIdentifier = 'Folder'
    defaultName = 'folder'
    bitmap = 'Folder_s.bmp'
    imgIdx = 9

    def __init__(self, data, name, editor, filepath):
        EditorModel.__init__(self, name, data, editor, true)
        self.filepath = filepath

class SysPathFolderModel(FolderModel):
    modelIdentifier = 'SysPathFolder'
    defaultName = 'syspathfolder'
    bitmap = 'Folder_green.bmp'
    imgIdx = 10

class CVSEntry:
    def text(self):
        return 'cvs entry'
    def __repr__(self):
        return self.text()

class CVSDir(CVSEntry):
    def __init__(self, line = ''):
        self.imgIdx = 5
        if line:
##            self.name, self.filler1, self.filler2, self.filler3, self.filler4 = \
            self.name, self.revision, self.timestamp, self.options, self.tagdate = \
              string.split(line[2:], '/')
        else:
            self.name, self.revision, self.timestamp, self.options, self.tagdate = '', '', '', '', ''
##            self.name, self.filler1, self.filler2, self.filler3, self.filler4 = '', '', '', '', ''

    def text(self):
##        return string.join(('D', self.name, self.filler1, self.filler2, self.filler3, self.filler4), '/')
        return string.join(('D', self.name, self.revision, self.timestamp, self.options, self.tagdate), '/')

class CVSFile(CVSEntry):
    def __init__(self, line = '', filepath = ''):
        self.filepath = filepath
        self.missing = false
        if line:
            self.name, self.revision, self.timestamp, self.options, self.tagdate = \
              string.split(string.strip(line)[1:], '/')
        else:
            self.name, self.revision, self.timestamp, self.options, self.tagdate = '', '', '', '', ''
        self.imgIdx = 0
        if self.timestamp:
            filename = path.abspath(path.join(self.filepath, '..', self.name))
            if path.exists(filename):
                filets = strftime('%a %b %d %H:%M:%S %Y', gmtime(os.stat(filename)[ST_MTIME]))
                self.modified = self.timestamp != filets
            else:
                self.missing = true
                self.modified = false
        else:
            self.modified = false
        
        self.imgIdx = self.options == '-kb' or self.modified << 1 or self.missing << 2

    def text(self):
        return string.join(('D', self.name, self.revision, self.timestamp, self.options, self.tagdate), '/')

class CVSFolderModel(FolderModel):
    modelIdentifier = 'CVS Folder'
    defaultName = 'cvsfolder'
    bitmap = 'Folder_cyan_s.bmp'
    imgIdx = 11
    
    def __init__(self, data, name, editor, filepath):
        FolderModel.__init__(self, data, name, editor, filepath)
        self.readFiles()

    def readFile(self, filename):
        f = open(filename, 'r')
        try: return string.strip(f.read())
        finally: f.close()

    def readFiles(self):
        self.root = self.readFile(path.join(self.filepath, 'Root'))
        self.repository = self.readFile(path.join(self.filepath, 'Repository'))
        self.entries = []

        f = open(path.join(self.filepath, 'Entries'), 'r')
        dirpos = 0 
        try:
            txtEntries = f.readlines()
            for txtEntry in txtEntries:
                txtEntry = string.strip(txtEntry)
                if txtEntry:
                    if txtEntry == 'D':
                        pass
                        # maybe add all dirs?   
                    elif txtEntry[0] == 'D':
                        self.entries.insert(dirpos, CVSDir(txtEntry))  
                        dirpos = dirpos + 1
                    else:
                        try:
                            self.entries.append(CVSFile(txtEntry, self.filepath))  
                        except IOError: pass
        finally:
            f.close()
 

class ZopeDocumentModel(EditorModel):
    modelIdentifier = 'ZopeDocument'
    defaultName = 'zopedoc'
    bitmap = 'Package_s.bmp'
    imgIdx = 17

    saveBmp = 'Images/Editor/Save.bmp'

    def __init__(self, name, data, editor, saved, zopeConnection, zopeObject):
        EditorModel.__init__(self, name, data, editor, saved)
        self.zopeConn = zopeConnection
        self.zopeObj = zopeObject
        self.savedAs = true

##    def addTools(self, toolbar):
##        EditorModel.addTools(self, toolbar)
##
##    def addMenu(self, menu, label, meth, accls, code):
##        newId = NewId()
##        menu.Append(newId, label)
##        EVT_MENU(self.editor, newId, meth)
##        accls.append((code[0], code[1], newId),)
    

    def addTools(self, toolbar):
        EditorModel.addTools(self, toolbar)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveBmp, 'Save', self.editor.OnSave)
        
    def addMenus(self, menu):
        accls = EditorModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORSAVE, 'Save', accls, (keyDefs['Save']))
        return accls

    def load(self, notify = true):
        self.data = self.zopeConn.load(self.zopeObj)
        self.modified = false
        self.saved = false
        self.update()
        if notify: self.notify()
    
    def save(self):
        """ Saves contents of data to file specified by self.filename. """
        if self.filename:
            self.zopeConn.save(self.zopeObj, self.data)
            self.modified = false
        else:
            raise 'No filename'
    
    def saveAs(self, filename):
        """ Saves contents of data to file specified by filename.
            Override this to catch name changes. """

        raise 'Save as not supported'
            
            
class PackageModel(EditorModel):
    """ Must be constructed in a valid path, name being filename, actual
        name will be derived from path """
        
    modelIdentifier = 'Package'
    defaultName = 'package'
    bitmap = 'Package_s.bmp'
    imgIdx = 7
    pckgIdnt = '__init__.py'
    ext = '.py'

    saveBmp = 'Images/Editor/Save.bmp'
    saveAsBmp = 'Images/Editor/SaveAs.bmp'

    def __init__(self, data, name, editor, saved):
        EditorModel.__init__(self, name, data, editor, saved)
        self.packagePath, dummy = path.split(self.filename)
        dummy, self.packageName = path.split(self.packagePath)
        self.savedAs = true
        self.modified = false
    
    def addTools(self, toolbar):
        EditorModel.addTools(self, toolbar)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveBmp, 'Save', self.editor.OnSave)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveAsBmp, 'Save as...', self.editor.OnSaveAs)

    def addMenus(self, menu):
        accls = EditorModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORSAVE, 'Save', accls, (keyDefs['Save']))
        self.addMenu(menu, Editor.wxID_EDITORSAVEAS, 'Save as...', accls, (keyDefs['SaveAs']))
        return accls

    def openPackage(self, name):
        self.editor.openModule(path.join(self.packagePath, name, self.pckgIdnt))
    
    def openFile(self, name):
        self.editor.openModule(path.join(self.packagePath, name + self.ext))
    
    def generateFileList(self):
        """ Generate a list of modules and packages in the package path """
        files = os.listdir(self.packagePath)
        packages = []
        modules = []
        for file in files:
            filename = path.join(self.packagePath, file)
            mod, ext = path.splitext(file)
            if file == self.pckgIdnt: continue
            elif (ext == self.ext) and path.isfile(filename):
                modules.append((mod, identifyFile(filename)[0]))
            elif path.isdir(filename) and \
              path.exists(path.join(filename, self.pckgIdnt)):
                packages.append((file, PackageModel))
        
        return packages + modules
                
class ModuleModel(EditorModel):

    modelIdentifier = 'Module'
    defaultName = 'module'
    bitmap = 'Module_s.bmp'
    imgIdx = 6
    ext = '.py'

    saveBmp = 'Images/Editor/Save.bmp'
    saveAsBmp = 'Images/Editor/SaveAs.bmp'

    def __init__(self, data, name, editor, saved, app = None):
        EditorModel.__init__(self, name, data, editor, saved)
        self.moduleName = path.split(self.filename)[1]
        self.app = app
        self.debugger = None
        if data: self.update()

    def destroy(self):
        EditorModel.destroy(self)
        del self.app
        del self.debugger
        
    def addTools(self, toolbar):
        EditorModel.addTools(self, toolbar)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveBmp, 'Save', self.editor.OnSave)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveAsBmp, 'Save as...', self.editor.OnSaveAs)
        
    # This is a comment
    def addMenus(self, menu):
        accls = EditorModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORSAVE, 'Save', accls, (keyDefs['Save']))
        self.addMenu(menu, Editor.wxID_EDITORSAVEAS, 'Save as...', accls, (keyDefs['SaveAs']))
        menu.Append(-1, '-')
        self.addMenu(menu, Editor.wxID_EDITORSWITCHAPP, 'Switch to app', accls, (keyDefs['SwitchToApp']))
        self.addMenu(menu, Editor.wxID_EDITORDIFF, 'Diff modules...', accls, ())
        return accls

    def new(self):
        self.data = ''
        self.savedAs = false
        self.modified = true
        self.update()
        self.notify()

    def load(self, notify = true):
        EditorModel.load(self, false)
        self.update()
        if notify: self.notify()
        
    def initModule(self):
        t1 = time()
        self.module = moduleparse.Module(self.moduleName, string.split(self.data, '\012'))
        t2 = time()
#        print 'parse', t2 - t1
        
    def refreshFromModule(self):
        """ Must call this method to apply changes were made to module object. """
        self.data = string.join(self.module.source, '\012')#os.linesep)
        self.notify()
    
    def renameClass(self, oldname, newname):
        pass
    
    def update(self):
        EditorModel.update(self)
        self.initModule()

    def checkError(self, err, str):    
        err.parse()
        if len(err.error):
            model = self.editor.openOrGotoModule(err.stack[0].file, self.app)
##            print 'erpos', err.error[2]
            model.views['Source'].focus()
            model.views['Source'].SetFocus()
            model.views['Source'].gotoLine(err.stack[0].lineNo - 1, err.error[2])
            model.views['Source'].setStepPos(err.stack[0].lineNo - 1)
            self.editor.statusBar.setHint('%s: %s'% (err.error[0], err.error[1]))
        else:
            self.editor.statusBar.setHint('%s %s successfully.' %\
              (str, path.basename(self.filename)))

    def run(self, args = ''):
        """ Excecute the current saved image of the application. """
        if self.savedAs:
            cwd = path.abspath(os.getcwd())
            os.chdir(path.dirname(self.filename))
            oldErr = sys.stderr
            sys.stderr = ErrorStack.ErrorParser()
            try:
                cmd = '"%s" %s %s'%(sys.executable, path.basename(self.filename), args)
                print 'executing', cmd, args
                try:
                    wx.wxExecute(cmd, true)
                except:
                    raise                    
                self.checkError(sys.stderr, 'Ran')
            finally:
                sys.stderr = oldErr
                os.chdir(cwd)

    def runAsScript(self):
        execfile(self.filename)
    
    def compile(self):
        if self.savedAs:
            try:
                oldErr = sys.stderr
                sys.stderr = ErrorStack.ErrorParser()
                try:
                    py_compile.compile(self.filename)
                except:
                    print 'Compile Exception!'
                    raise
                self.checkError(sys.stderr, 'Compiled')
            finally:
                sys.stderr = oldErr

    def cyclops(self):
        """ Excecute the current saved image of the application. """
        if self.savedAs:
            cwd = path.abspath(os.getcwd())
            os.chdir(path.dirname(self.filename))
            page = ''
            try:
                name = path.basename(self.filename)

                # excecute Cyclops in Python with module as parameter
                command = '"%s" "%s" "%s"'%(sys.executable, 
                  Preferences.toPyPath('RunCyclops.py'), name)
                wx.wxExecute(command, true)

                # read report that Cyclops generated
                f = open(name[:-3]+'.cycles', 'r')
                page = f.read()
                f.close()
            finally:
                os.chdir(cwd)
                return page
        else:
            wxLogWarning('Save before running Cyclops')
            raise 'Not saved yet!' 

    def debug(self):
        if self.savedAs:
            if self.editor.debugger:
                self.editor.debugger.Show(true)
            else:
                self.editor.debugger = Debugger.DebuggerFrame(self)
                self.editor.debugger.Show(true)  
                self.editor.debugger.debug_file(self.editor.debugger.filename)
    
    def profile(self):
        if self.savedAs:
            cwd = path.abspath(os.getcwd())
            os.chdir(path.dirname(self.filename))

            tmpApp = wxPython.wx.wxApp
            wxProfilerPhonyApp.realApp = self.editor.app
            wxPython.wx.wxApp = wxProfilerPhonyApp
            try:
                prof = profile.Profile()
	        try:
		    prof = prof.run('execfile("%s")'% path.basename(self.filename))
	        except SystemExit:
		    pass
                prof.create_stats()
                return prof.stats     

            finally:
                wxPython.wx.wxApp = tmpApp
                del wxProfilerPhonyApp.realApp
                os.chdir(cwd)
        

    def addModuleInfo(self, prefs):
        # XXX Check that module doesn't already have an info block

        dollar = '$' # has to be obscured from CVS :)
        prefs['Name'] = self.moduleName
        prefs['Created'] = strftime('%Y/%d/%m', gmtime(time()))
        prefs['RCS-ID'] = '%sId: %s %s' % (dollar, self.moduleName , dollar)

        self.data = defInfoBlock % (prefs['Name'], prefs['Purpose'], prefs['Author'],
          prefs['Created'], prefs['RCS-ID'], prefs['Copyright'], prefs['Licence']) + self.data
        self.modified = true
        self.update()
        self.notify()

    def saveAs(self, filename):
        oldFilename = self.filename  
        EditorModel.saveAs(self, filename)
        if self.app: 
            self.app.moduleSaveAsNotify(self, oldFilename, filename)
        self.moduleName = path.basename(filename)
        self.notify()

    def diff(self, filename):
        tbName = 'Diff with : '+filename
        if not self.views.has_key(tbName):
            resultView = self.editor.addNewView(tbName, PythonSourceDiffView)
        else:
            resultView = self.views[tbName]
            
        resultView.tabName = tbName
        resultView.diffWith = filename
        resultView.refresh()
        resultView.focus()
                
class TextModel(EditorModel):

    modelIdentifier = 'Text'
    defaultName = 'text'
    bitmap = 'Text_s.bmp'
    imgIdx = 8
    ext = '.txt'

    saveBmp = 'Images/Editor/Save.bmp'
    saveAsBmp = 'Images/Editor/SaveAs.bmp'

    def __init__(self, data, name, editor, saved):
        EditorModel.__init__(self, name, data, editor, saved)
        if data: self.update()
        
    def addTools(self, toolbar):
        EditorModel.addTools(self, toolbar)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveBmp, 'Save', self.editor.OnSave)
        AddToolButtonBmpIS(self.editor, toolbar, self.saveAsBmp, 'Save as...', self.editor.OnSaveAs)

    def addMenus(self, menu):
        accls = EditorModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORSAVE, 'Save', accls, (keyDefs['Save']))
        self.addMenu(menu, Editor.wxID_EDITORSAVEAS, 'Save as...', accls, (keyDefs['SaveAs']))
        return accls

    def new(self):
        self.data = ''
        self.savedAs = false
        self.modified = true
        self.update()
        self.notify()

    def load(self, notify = true):
        EditorModel.load(self, false)
        self.update()
        if notify: self.notify()
                

class ClassModel(ModuleModel):
    """ Represents access to 1 maintained main class in the module.
        This class is identified by the 3rd header entry  #Boa:Model:Class """
    def __init__(self, data, name, main, editor, saved, app = None):
        self.main = main
        self.mainConstr = None
        ModuleModel.__init__(self, data, name, editor, saved, app)
    
    def renameMain(self, oldName, newName):
        self.module.renameClass(oldName, newName)
        self.main = newName

        header = string.split(string.strip(self.module.source[0]), ':')
        if (len(header) == 3) and (header[0] == '#Boa'):
            self.module.source[0] = string.join((header[0], header[1], newName), ':')

class ObjectCollection:
    def __init__(self):#, creators = [], properties = [], events = [], collections = []):
##        print 'ObjectCollection created' 
        self.creators = []
        self.properties = []
        self.events = []
        self.collections = []
        self.initialisers = []
        self.finalisers = []
        
        self.creatorByName = {}
        self.propertiesByName = {}
        self.eventsByName = {}
        self.collectionsByName = {}

    def setup(self, creators, properties, events, collections, initialisers, finalisers):
##        print 'ObjectCollection setup', id(self.creators), id(creators)
        self.creators = creators
        self.properties = properties
        self.events = events
        self.collections = collections
        self.initialisers = initialisers
        self.finalisers = finalisers

    def removeReference(self, name, method):
        i = 0
        while i < len(self.collections):
            if self.collections[i].method == method:
                del self.collections[i]
            else:
                i = i + 1

        if self.collectionsByName.has_key(name):
            namedColls = self.collectionsByName[name]
            
            i = 0
            while i < len(namedColls):
                if namedColls[i].method == method:
                    del namedColls[i]
                else:
                    i = i + 1

        i = 0
        while i < len(self.properties):
            prop = self.properties[i]
            if len(prop.params) and prop.params[0][5:len(method) +5] == method:
                del self.properties[i]
            else:
                i = i + 1

        i = 0
        if self.propertiesByName.has_key(name):
            props = self.propertiesByName[name]
            while i < len(props):
                prop = props[i]
                if len(prop.params) and prop.params[0][5:len(method) +5] == method:
                    del props[i]
                else:
                    i = i + 1
            
    def deleteCtrl(self, name):
        for list in (self.creators, self.properties, self.events):
            i = 0
            while i < len(list):
                if list[i].comp_name == name:
                    del list[i]
                else:
                    i = i + 1

    def setupList(self, list):
        dict = {}
        for item in list:
            if not dict.has_key(item.comp_name):
                dict[item.comp_name] = []
            dict[item.comp_name].append(item)
        return dict
        
    def indexOnCtrlName(self):
        self.creatorByName = self.setupList(self.creators)
        self.propertiesByName = self.setupList(self.properties)
        self.eventsByName = self.setupList(self.events)
        self.collectionsByName = self.setupList(self.collections)

    def __repr__(self):
        return '<ObjectCollection instance: %s,\n %s,\n %s,\n %s,\n %s,\n %s,\n %s,\n %s,>'%\
          (`self.creators`, `self.properties`, `self.collections`, `self.events`, 
           `self.creatorByName`, `self.propertiesByName`, 
           `self.collectionsByName`, `self.eventsByName`)

class BaseFrameModel(ClassModel):
    modelIdentifier = 'Frames'
    companion = Companions.DesignTimeCompanion
    designerBmp = 'Images/Shared/Designer.bmp'
    def __init__(self, data, name, main, editor, saved, app = None):
        ClassModel.__init__(self, data, name, main, editor, saved, app)
        self.designerTool = None

    def addTools(self, toolbar):
        ClassModel.addTools(self, toolbar)
        toolbar.AddSeparator()
        AddToolButtonBmpIS(self.editor, toolbar, self.designerBmp, 'Frame Designer', self.editor.OnDesigner)

    def addMenus(self, menu):
        accls = ClassModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORDESIGNER, 'Frame Designer', accls, (keyDefs['Designer']))
        return accls

    def renameMain(self, oldName, newName):
        ClassModel.renameMain(self, oldName, newName)
        self.module.replaceFunctionBody('create', ['    return %s(parent)'%newName, ''])

    def renameCtrl(self, oldName, newName):
        # Currently DesignerView maintains ctrls
        pass
        
    def new(self, params):
        paramLst = []
        for param in params.keys():
            paramLst.append('%s = %s'%(param, params[param]))
        paramStr = 'self, ' + string.join(paramLst, ', ')
        
        self.data = (defSig + defImport + defCreateClass + defWindowIds + \
          defClass) % (self.modelIdentifier, self.main, self.main, 
          Utils.windowIdentifier(self.main, ''), init_ctrls, 1, self.main, 
          self.defaultName, self.defaultName, paramStr)
        
        self.savedAs = false
        self.modified = true
        self.initModule()
#        self.readComponents()
        self.notify()
    
    def identifyCollectionMethods(self):
        results = []
        if self.module.classes.has_key(self.main):
            main = self.module.classes[self.main]
            for meth in main.methods.keys():
                if len(meth) > len('_init_') and meth[:6] == '_init_':
                    results.append(meth)
        return results
    
    def allObjects(self):
        views = ['Data', 'Designer']
        
        order = []
        objs = {}
        
        for view in views:
            order.extend(self.views[view].objectOrder)
            objs.update(self.views[view].objects)
        
        return order, objs

    def getInitialiser(self, clss, coll):
        if coll.has_key(clss):
            return coll[clss]
        else:
            return []

    def readComponents(self):
        from methodparse import *
        self.objectCollections = {}
        if self.module.classes.has_key(self.main):
            main = self.module.classes[self.main]
            for oc in self.identifyCollectionMethods(): 
                codeSpan = main.methods[oc]
                codeBody = self.module.source[codeSpan.start : codeSpan.end]
                if len(oc) > len('_init_coll_') and oc[:11] == '_init_coll_':
                    try:
                        res = Utils.split_seq(codeBody, '')
                        inits, body, fins = res[:3]
                    except ValueError:
                        raise 'Collection body '+oc+' not in init, body, fin form'
                    
                    allInitialisers = parseMixedBody([CollectionItemInitParse, 
                      EventParse], body)
                    creators = self.getInitialiser(CollectionItemInitParse, allInitialisers)
                    collectionInits = []
                    properties = []
                    events = self.getInitialiser(EventParse, allInitialisers)
                else:
                    inits = []
                    fins = []
                    
                    if oc[:11] == '_init_ctrls' and \
                      string.strip(codeBody[1]) == 'self._init_utils()':
                        del codeBody[1]
                        
                    allInitialisers = parseMixedBody([ConstructorParse, 
                      EventParse, CollectionInitParse, PropertyParse], codeBody)
                    
                    creators = self.getInitialiser(ConstructorParse, allInitialisers)
                    if creators and oc == init_ctrls:
                        self.mainConstr = creators[0]
                    collectionInits = self.getInitialiser(CollectionInitParse, allInitialisers)
                    properties = self.getInitialiser(PropertyParse, allInitialisers)
                    events = self.getInitialiser(EventParse, allInitialisers)
    
                self.objectCollections[oc] = ObjectCollection()
                self.objectCollections[oc].setup(creators, properties, events, 
                  collectionInits, inits, fins)

    def removeWindowIds(self, colMeth):
        # find windowids in source
        winIdIdx = -1
        reWinIds = re.compile(srchWindowIds % colMeth)
        for idx in range(len(self.module.source)):
            match = reWinIds.match(self.module.source[idx])
            if match:
                del self.module.source[idx]
                del self.module.source[idx]
                self.module.renumber(-2, idx)
                break

    def writeWindowIds(self, colMeth, companions):
        # To integrate efficiently with Designer.SaveCtrls this method
        # modifies module.source but doesn't refresh anything
        
        # find windowids in source
        winIdIdx = -1
        reWinIds = re.compile(srchWindowIds % colMeth)
        for idx in range(len(self.module.source)):
            match = reWinIds.match(self.module.source[idx])
            if match:
                winIdIdx = idx
                break
        # build window id list
        lst = []
        for comp in companions:
            if winIdIdx == -1:
                comp.updateWindowIds()
            comp.addIds(lst)
	
        if winIdIdx == -1:
            if lst:
                # No window id definitions could be found add one above class def
                insPt = self.module.classes[self.main].block.start - 1
                self.module.source[insPt:insPt] = \
                  [string.strip(defWindowIds % (string.join(lst, ', '), colMeth, 
                  len(lst))), '']
                self.module.renumber(2, insPt)
        else:
	    # Update window ids
	    self.module.source[idx] = \
	      string.strip(defWindowIds % (string.join(lst, ', '), colMeth, len(lst)))
	    
    def update(self):
        ClassModel.update(self)
#        self.readComponents()
            
class FrameModel(BaseFrameModel):
    modelIdentifier = 'Frame'
    defaultName = 'wxFrame'
    bitmap = 'wxFrame_s.bmp'
    imgIdx = 1
    companion = Companions.FrameDTC

class DialogModel(BaseFrameModel):
    modelIdentifier = 'Dialog'
    defaultName = 'wxDialog'
    bitmap = 'wxDialog_s.bmp'
    imgIdx = 2
    companion = Companions.DialogDTC

class MiniFrameModel(BaseFrameModel):
    modelIdentifier = 'MiniFrame'
    defaultName = 'wxMiniFrame'
    bitmap = 'wxMiniFrame_s.bmp'
    imgIdx = 3
    companion = Companions.MiniFrameDTC

class MDIParentModel(BaseFrameModel):
    modelIdentifier = 'MDIParent'
    defaultName = 'wxMDIParentFrame'
    bitmap = 'wxMDIParentFrame_s.bmp'
    imgIdx = 4
    companion = Companions.MDIParentFrameDTC

class MDIChildModel(BaseFrameModel):
    modelIdentifier = 'MDIChild'
    defaultName = 'wxMDIChildFrame'
    bitmap = 'wxMDIChildFrame_s.bmp'
    imgIdx = 5
    companion = Companions.MDIChildFrameDTC
    
# XXX Autocreated frames w/ corresponding imports
# XXX Paths
# XXX module references to app mut be cleared on closure

class AppModel(ClassModel):
    modelIdentifier = 'App'
    defaultName = 'wxApp'
    bitmap = 'wxApp_s.bmp'
    imgIdx = 0
    def __init__(self, data, name, main, editor, saved):
        self.moduleModels = {}
        ClassModel.__init__(self, data, name, main, editor, saved, self)
        if data:
            self.update()
            self.notify()

    def addMenus(self, menu):
        accls = ClassModel.addMenus(self, menu)
        self.addMenu(menu, Editor.wxID_EDITORCMPAPPS, 'Compare apps...', accls, ())
        return accls
        
    def convertToUnixPath(self, filename):
        # Don't convert absolute windows paths, will stay illegal until saved
        if path.splitdrive(filename)[0] != '':
            return filename
        else:
            return string.join(string.split(filename, '\\'), '/')

    def saveAs(self, filename):
        for mod in self.modules.keys():
            self.modules[mod][2] = self.convertToUnixPath(\
              relpath.relpath(path.dirname(filename), 
              self.normaliseModuleRelativeToApp(self.modules[mod][2])))

        self.writeModules()    
        
        ClassModel.saveAs(self, filename)
        
        self.notify()
    
##    def modulePathChange(self, oldFilename, newFilename):
##        # self.modules have already been renamed, use newFilename
##        key = path.splitext(path.basename(newFilename))[0]
##        self.modules[key][2] = relpath.relpath(path.dirname(self.filename), newFilename)
##
##        self.writeModules()    

    def renameMain(self, oldName, newName):
        ClassModel.renameMain(self, oldName, newName)
        self.module.replaceFunctionBody('main', 
          ['    application = %s(0)'%newName, '    application.MainLoop()', ''])

    def new(self, mainModule):
        self.data = (defSig + defEnvPython + defImport + defApp) \
          %(self.modelIdentifier, 'BoaApp', mainModule, mainModule,
            mainModule, mainModule)
        self.saved = false
        self.modified = true
        self.update()
        self.notify()
    
    def findImports(self):
        impPos = string.find(self.data, defImport)
        impPos = string.find(self.data, 'import', impPos + 1)
        
        # XXX Add if not found
        if impPos == -1: raise 'Module import list not found in application'
        impEnd = string.find(self.data, '\012', impPos + len('import') +1) + 1
        if impEnd == -1: raise 'Module import list not terminated'
        return impPos + len('import'), impEnd        

    def findModules(self):
        modStr = 'modules ='
        modPos = string.find(self.data, modStr)
        if modPos == -1:
            raise 'Module list not found in application'
        modEnd = string.find(self.data, '}', modPos + len(modStr) +1) + 1
        if modEnd == -1: raise 'Module list not terminated properly'
        return modPos + len(modStr), modEnd
            
    def idModel(self, name):
        absPath = self.normaliseModuleRelativeToApp(self.modules[name][2])
        if path.exists(absPath):
            self.moduleModels[name], main = identifyFile(absPath)
        else:
            if self.editor.modules.has_key(absPath):
                self.moduleModels[name], main = identifySource( \
                  self.editor.modules[absPath].model.module.source)
            elif self.editor.modules.has_key(path.basename(absPath)):
                self.moduleModels[name], main = identifySource( \
                  self.editor.modules[path.basename(absPath)].model.module.source)
            else:
                print 'could not find unsaved module', absPath, self.editor.modules

    def readModules(self):
	modS, modE = self.findModules()
        try:
            self.modules = eval(self.data[modS:modE])
        except: raise 'Module list not a valid dictionary'
        
        for mod in self.modules.keys():
            self.idModel(mod)
        
    def readImports(self):
	impS, impE = self.findImports()
        try:
            self.imports = string.split(self.data[impS:impE], ', ')
        except: raise 'Module import list not a comma delimited list'

    def writeModules(self, notify = true):
	modS, modE = self.findModules()
        self.data = self.data[:modS]+`self.modules`+self.data[modE:]

        self.modified = true
        self.editor.updateTitle()
        self.editor.updateModulePage(self)
        
        if notify: self.notify()

    def writeImports(self, notify = true):
	impS, impE = self.findImports()
        self.data = self.data[:impS]+string.join(self.imports, ', ')+ \
          self.data[impE:]
        if notify: self.notify()

    def viewAddModule(self):
        # XXX Don't really want to access editor
        fn = self.editor.openFileDlg()
        if fn:
            self.addModule(fn, '')
        
    def addModule(self, filename, descr):
        name, ext = path.splitext(path.basename(filename))
        if self.modules.has_key(name): raise 'Module exists in application'
        if self.savedAs:
            relative = relpath.relpath(path.dirname(self.filename), filename)
        else:
            relative = filename
        self.modules[name] = [0, descr, self.convertToUnixPath(relative)]

        self.idModel(name)

        self.writeModules()

    def removeModule(self, name):
        if not self.modules.has_key(name): raise 'No such module in application'
        del self.modules[name]
        self.writeModules()
    
    def editModule(self, oldname, newname, main, descr):
        if oldname != newname:
            del self.modules[oldname]
        self.modules[newname] = (main, descr)
        self.writeModules()

    def moduleFilename(self, name):
        if not self.modules.has_key(name): raise 'No such module in application: '+name
        if self.savedAs:
            if path.isabs(self.modules[name][2]):
                absPath = self.modules[name][2]
            else:
                absPath = path.normpath(path.join(path.dirname(self.filename), 
                  self.modules[name][2]))
        else:
            absPath = name + ModuleModel.ext
        return absPath

    def moduleSaveAsNotify(self, module, oldFilename, newFilename):
        if module != self:
            newName, ext = path.splitext(path.basename(newFilename))
            oldName = path.splitext(path.basename(oldFilename))[0]
 
            if not self.modules.has_key(oldName): raise 'Module does not exists in application'

            if self.savedAs:
                relative = relpath.relpath(path.dirname(self.filename), newFilename)
            else:
                relative = newFilename

            if newName != oldName:
                self.modules[newName] = self.modules[oldName]
                del self.modules[oldName]
            self.modules[newName][2] = self.convertToUnixPath(relative)

            self.writeModules()

    def openModule(self, name):
        absPath = self.moduleFilename(name)
        
        module = self.editor.openOrGotoModule(absPath, self)
        
        return module
        
    def readPaths(self):
        pass

    def normaliseModuleRelativeToApp(self, relFilename):
        if not self.savedAs:
            return path.normpath(path.join(Preferences.pyPath, relFilename))
        else:
            return path.normpath(path.join(path.dirname(self.filename), relFilename))
        
    def buildImportRelationshipDict(self, modules = None):
        relationships = {}
        
        if modules is None:
            modules = self.modules.keys()
            
        tot = len(modules)
        self.editor.statusBar.progress.SetRange(tot)
        prog = 0
        for moduleName in modules:
            self.editor.statusBar.progress.SetValue(prog)
            prog = prog + 1
            self.editor.statusBar.setHint('Parsing '+moduleName+'...')
            module = self.modules[moduleName]
            try: f = open(self.normaliseModuleRelativeToApp(module[2]))
            except IOError: 
                print "couldn't load", module[2]
                continue
            else:
                data = f.read()
                f.close()
                model = ModuleModel(data, module[2], self.editor, 1)
                relationships[moduleName] = model.module#.imports
        self.editor.statusBar.progress.SetValue(0)
        self.editor.statusBar.setHint('')
        return relationships
    
    def showImportsView(self):
        # XXX Should be more generic
        self.editor.showImportsView()
    
    def compareApp(self, filename):
        tbName = 'App. Compare : '+filename
        if not self.views.has_key(tbName):
            resultView = self.editor.addNewView(tbName, AppCompareView)
        else:
            resultView = self.views[tbName]
            
        resultView.tabName = tbName
        resultView.compareTo = filename
        resultView.refresh()
        resultView.focus()
                    
    def update(self):
        ClassModel.update(self)
        self.readModules()
        self.readPaths()

# model registry: add to this dict to register a Model
modelReg = {AppModel.modelIdentifier: AppModel, 
            FrameModel.modelIdentifier: FrameModel,
            DialogModel.modelIdentifier: DialogModel,
            MiniFrameModel.modelIdentifier: MiniFrameModel,
            MDIParentModel.modelIdentifier: MDIParentModel,
            MDIChildModel.modelIdentifier: MDIChildModel,
            ModuleModel.modelIdentifier: ModuleModel,
            TextModel.modelIdentifier: TextModel,
            PackageModel.modelIdentifier: PackageModel}

def identifyHeader(headerStr):
    header = string.split(headerStr, ':')
    if len(header) and (header[0] == '#Boa') and modelReg.has_key(header[1]):
        return modelReg[header[1]], header[2]
    return ModuleModel, ''
    
def identifyFile(filename):
    """ Return appropriate model for given source file.
        Assumes header will be part of the first continious comment block """
    f = open(filename)
    try:
        dummy, name = path.split(filename)
        if name == '__init__.py':
            return PackageModel, ''
        dummy, ext = path.splitext(filename)
        if ext == '.txt':
            return TextModel, ''
        while 1:
            line = f.readline()
            if not line: break
            line = string.strip(line)
            if line:
                if line[0] != '#':
                    return ModuleModel, ''
                
                headerInfo = identifyHeader(line)
                
                if headerInfo[0] != ModuleModel:
                    return headerInfo
        return ModuleModel, ''
    finally:
        f.close()

def identifySource(source):
    """ Return appropriate model for given source.
        The logic is a copy paste from above func """
    for line in source:
        if line:
            if line[0] != '#':
                return ModuleModel, ''
            
            headerInfo = identifyHeader(string.strip(line))
            
            if headerInfo[0] != ModuleModel:
                return headerInfo
        else:
            return ModuleModel, ''
            
            
            
            
            
            
            
            
            
            
            
       