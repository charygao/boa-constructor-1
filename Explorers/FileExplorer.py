#-----------------------------------------------------------------------------
# Name:        FileExplorer.py
# Purpose:
#
# Author:      Riaan Booysen
#
# Created:     2001/03/06
# RCS-ID:      $Id$
# Copyright:   (c) 2001
# Licence:     GPL
#-----------------------------------------------------------------------------
import string, os, time, stat

from wxPython.wx import *

import ExplorerNodes
import EditorModels, EditorHelper, Utils, Preferences

# XXX There might be a bug in the path code of Find in files

class FileSysCatNode(ExplorerNodes.CategoryNode):
#    protocol = 'config.file'
    defName = Preferences.explorerFileSysRootDefault[0]
    defaultStruct = Preferences.explorerFileSysRootDefault[1]
    def __init__(self, clipboard, config, parent, bookmarks):
        ExplorerNodes.CategoryNode.__init__(self, 'Filesystem', ('explorer', 'filesystem'),
              clipboard, config, parent)
        self.bookmarks = bookmarks

    def createParentNode(self):
        return self

    def createCatCompanion(self, catNode):
        comp = ExplorerNodes.CategoryStringCompanion(catNode.treename, self)
        return comp

    def createChildNode(self, entry, value):
        return NonCheckPyFolderNode(entry, value, self.clipboard,
              EditorHelper.imgFSDrive, self, self.bookmarks)

##    def newItem(self):
##        name = ExplorerNodes.CategoryNode.newItem()
##        self.entries[name] = copy.copy(self.defaultStruct)
##        self.updateConfig()
##        return name

    def renameItem(self, name, newName):
        if self.entries.has_key(newName):
            raise Exception, 'Name exists'
        self.entries[newName] = newName
        del self.entries[name]
        self.updateConfig()


(wxID_FSOPEN, wxID_FSTEST, wxID_FSNEW, wxID_FSNEWFOLDER, wxID_FSCVS,
 wxID_FSBOOKMARK, wxID_FSFILTERBOAMODULES, wxID_FSFILTERALLMODULES,
 wxID_FSFILTER, wxID_FSFILTERINTMODULES, wxID_FSFINDINFILES, wxID_FSFINDFILES,
) = map(lambda x: wxNewId(), range(12))

class FileSysController(ExplorerNodes.Controller, ExplorerNodes.ClipboardControllerMix):
    bookmarkBmp = 'Images/Shared/Bookmark.bmp'
    findBmp = 'Images/Shared/Find.bmp'
    def __init__(self, editor, list, cvsController = None):
        ExplorerNodes.Controller.__init__(self, editor)
        ExplorerNodes.ClipboardControllerMix.__init__(self)
        self.editor = editor

        self.list = list
        self.cvsController = cvsController
        self.menu = wxMenu()

#              (wxID_FSTEST, 'Test', self.OnTest),
        self.fileMenuDef = (
              (wxID_FSOPEN, 'Open', self.OnOpenItems, '-'),
              (-1, '-', None, '') ) +\
              self.clipMenuDef +\
            ( (-1, '-', None, ''),
              (wxID_FSFINDINFILES, 'Find', self.OnFindFSItem, self.findBmp),
              (wxID_FSBOOKMARK, 'Bookmark', self.OnBookmarkFSItem, self.bookmarkBmp),
        )
        self.setupMenu(self.menu, self.list, self.fileMenuDef)

        self.fileFilterMenuDef = (
              (wxID_FSFILTERBOAMODULES, '+Boa files', self.OnFilterFSItemBoa, '-'),
              (wxID_FSFILTERINTMODULES, '+Internal files', self.OnFilterFSItemInt, '-'),
              (wxID_FSFILTERALLMODULES, '+All files', self.OnFilterFSItemAll, '-'),
        )
        self.fileFilterMenu = wxMenu()
        self.setupMenu(self.fileFilterMenu, self.list, self.fileFilterMenuDef)

        # Check default option
        self.fileFilterMenu.Check(wxID_FSFILTERBOAMODULES, true)

        self.menu.AppendMenu(wxID_FSFILTER, 'Filter', self.fileFilterMenu)

        self.newMenu = wxMenu()
        self.setupMenu(self.newMenu, self.list, (
              (wxID_FSNEWFOLDER, 'Folder', self.OnNewFolderFSItems, '-'),
        ))
        self.menu.AppendMenu(wxID_FSNEW, 'New', self.newMenu)

        if cvsController:
            self.menu.AppendMenu(wxID_FSCVS, 'CVS', cvsController.fileCVSMenu)

        self.toolbarMenus = [self.fileMenuDef]

    def __del__(self):
        pass
#        self.newMenu.Destroy()
##        self.fileFilterMenu.Destroy()

    def destroy(self):
        ExplorerNodes.ClipboardControllerMix.destroy(self)
        self.fileFilterMenuDef = ()
        self.fileMenuDef = ()
        self.toolbarMenus = ()
        self.menu.Destroy()
#

##    def OnOpenFSItems(self, event):
##        if self.list.node:
##            nodes = self.getNodesForSelection(self.list.getMultiSelection())
##            for node in nodes:
##                if not node.isFolderish():
##                    node.open(self.editor)

    def OnNewFolderFSItems(self, event):
        if self.list.node:
            name = self.list.node.newFolder()
            self.list.refreshCurrent()
            self.list.selectItemNamed(name)
            self.list.EditLabel(self.list.selected)

    def OnBookmarkFSItem(self, event):
        if self.list.node:
            nodes = self.getNodesForSelection(self.list.getMultiSelection())
            for node in nodes:
                if node.isFolderish():
                    node.bookmarks.add(node.resourcepath)
                    self.editor.statusBar.setHint('Bookmarked %s'% node.resourcepath, 'Info')
                else:
                    self.editor.statusBar.setHint('Not a directory: %s'% node.resourcepath, 'Error')
                    

    def OnTest(self, event):
        print self.list.node.clipboard.globClip.currentClipboard

    def OnFilterFSItemBoa(self, event):
        self.groupCheckMenu(self.fileFilterMenu, self.fileFilterMenuDef,
              wxID_FSFILTERBOAMODULES, true)
        self.list.node.setFilter('BoaFiles')
        self.list.refreshCurrent()

    def OnFilterFSItemAll(self, event):
        self.groupCheckMenu(self.fileFilterMenu, self.fileFilterMenuDef,
              wxID_FSFILTERALLMODULES, true)
        self.list.node.setFilter('AllFiles')
        self.list.refreshCurrent()

    def OnFilterFSItemInt(self, event):
        self.groupCheckMenu(self.fileFilterMenu, self.fileFilterMenuDef,
              wxID_FSFILTERINTMODULES, true)
        self.list.node.setFilter('BoaInternalFiles')
        self.list.refreshCurrent()

    def OnFindFSItem(self, event):
        import Search
        dlg = wxTextEntryDialog(self.list, 'Enter text:',
          'Find in files', '')
        try:
            if dlg.ShowModal() == wxID_OK:
                res = Search.findInFiles(self.list, self.list.node.resourcepath,
                      dlg.GetValue(), filemask = self.list.node.getFilterExts(),
                      progressMsg = 'Search files...', joiner = os.sep)
                nd = self.list.node
                self.list.node = ResultsFolderNode('Results', nd.resourcepath, nd.clipboard, -1, nd, nd.bookmarks)
                #self.list.node.results = map(lambda r: r[1], res)
                self.list.node.results = res
                self.list.node.lastSearch = dlg.GetValue()
                self.list.refreshCurrent()
        finally:
            dlg.Destroy()

class FileSysExpClipboard(ExplorerNodes.ExplorerClipboard):
    def clipPaste_FileSysExpClipboard(self, node, nodes, mode):
        # XXX Delayed cut (delete on paste or move) should clear the clipboard
        # XXX or refresh clipboard with new paths and clear 'cut' mode
        for clipnode in nodes:
            if mode == 'cut':
                node.moveFileFrom(clipnode)
                self.clipNodes = []
            elif mode == 'copy':
                node.copyFileFrom(clipnode)

    clipPaste_DefaultClipboard = clipPaste_FileSysExpClipboard
    
    def _genericFSPaste(self, node, nodes, mode):
        for other in nodes:
            other.copyToFS(node)

    def clipPaste_ZopeEClip(self, node, nodes, mode):
        # XXX Pasting a cut from Zope does not delete the cut items from Zope
        for zopeNode in nodes:
            zopeNode.downloadToFS(os.path.join(node.resourcepath, zopeNode.name))

##            file.zopeConn.download(file.resourcepath+'/'+file.name,
##                  os.path.join(node.resourcepath, file.name))

    def clipPaste_FTPExpClipboard(self, node, nodes, mode):
        # XXX Pasting a cut from FTP does not delete the cut items from FTP
        for file in nodes:
            file.ftpConn.download(file.resourcepath,
                  os.path.join(node.resourcepath, file.name))

    clipPaste_SSHExpClipboard = _genericFSPaste
    clipPaste_ZipExpClipboard = _genericFSPaste
    clipPaste_DAVExpClipboard = _genericFSPaste

class PyFileNode(ExplorerNodes.ExplorerNode):
    protocol = 'file'
    filter = 'BoaFiles'
    lastSearch = ''
    subExplorerReg = {'file': [], 'folder': []}
    def __init__(self, name, resourcepath, clipboard, imgIdx, parent, 
          bookmarks = None, properties = {}):
        ExplorerNodes.ExplorerNode.__init__(self, name, resourcepath, clipboard,
              imgIdx, parent, properties or {})
        self.bookmarks = bookmarks
        self.exts = EditorHelper.extMap.keys() + ['.py']
        self.entries = []

        self.doCVS = true
        self.doZip = true
        self.allowedProtocols = ['*']        

    def destroy(self):
        self.entries = []

    def isDir(self):
        return os.path.isdir(self.resourcepath)

    def isFolderish(self):
        return self.isDir() or filter(lambda se, rp=self.resourcepath,
              ap=self.allowedProtocols : (ap == ['*'] or se[0].protocol in ap) and se[1](rp),
              self.subExplorerReg['file'])

    def createParentNode(self):
        parent = os.path.abspath(os.path.join(self.resourcepath, '..'))
        if parent[-2:] == '..':
            parent = parent[:-2]
        return PyFileNode(os.path.basename(parent), parent, self.clipboard,
                  EditorHelper.imgFolder, self, self.bookmarks)

    def createChildNode(self, file, filename = ''):
        if not filename:
            filename = os.path.join(self.resourcepath, file)

        ext = string.lower(os.path.splitext(filename)[1])
        # Files
        if (ext in self.exts) and os.path.isfile(filename):
            for other, otherIdFunc, imgIdx in self.subExplorerReg['file']:
                if '*' in self.allowedProtocols or \
                      other.protocol in self.allowedProtocols:
                    if otherIdFunc(filename):
                        return 'fol', other(file, filename, self.clipboard, 
                              imgIdx, self, self.bookmarks)
            return 'mod', PyFileNode(file, filename, self.clipboard,
              EditorModels.identifyFile(filename)[0].imgIdx, self, self.bookmarks,
              {'datetime': time.strftime('%a %b %d %H:%M:%S %Y',
                           time.gmtime(os.stat(filename)[stat.ST_MTIME]))})
        # Directories
        elif os.path.isdir(filename):
            for other, otherIdFunc, imgIdx in self.subExplorerReg['folder']:
                if '*' in self.allowedProtocols or \
                      other.protocol in self.allowedProtocols:
                    if otherIdFunc(filename):
                        return 'fol', other(file, filename, self.clipboard, 
                              imgIdx, self, self.bookmarks)
            return 'fol', PyFileNode(file, filename, self.clipboard,
                  EditorHelper.imgFolder, self, self.bookmarks)
        elif self.filter == 'AllFiles':
            return 'mod', PyFileNode(file, filename, self.clipboard,
              EditorHelper.imgUnknownFileModel, self, self.bookmarks)
        else:
            return '', None

    def openList(self):
        files = os.listdir(self.resourcepath)
        files.sort()
        entries = {'mod': [], 'fol': []}

        for file in files:
            tp, node = self.createChildNode(file)
            if node:
                entries[tp].append(node)

        self.entries = entries['fol'] + entries['mod']
        return self.entries
    
    def open(self, editor):
        apps = editor.getAppModules()
        for app in apps:
            mods = app.absModulesPaths()
            if self.resourcepath in mods:
                return editor.openOrGotoModule(self.resourcepath, app, self)

        return editor.openOrGotoModule(self.resourcepath, transport = self)

    def deleteItems(self, names):
        for name in names:
            path = os.path.join(self.resourcepath, name)
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)

    def renameItem(self, name, newName):
        oldfile = os.path.join(self.resourcepath, name)
        newfile = os.path.join(self.resourcepath, newName)
        os.rename(oldfile, newfile)

    def newFolder(self):
        name = Utils.getValidName(map(lambda n: n.name, self.entries), 'Folder')
        os.mkdir(os.path.join(self.resourcepath, name))
        return name

    def copyFileFrom(self, node):
        """ Copy node into self (only called for folders)"""
        import shutil
        if not node.isDir():
            if node.resourcepath == os.path.join(self.resourcepath, node.name):
                newNameBase = os.path.join(self.resourcepath, 'copy%s_of_'+node.name)
                num = ''
                while 1:
                    newName = newNameBase%num
                    if os.path.exists(newName):
                        try: num = str(int(num) + 1)
                        except: num = '2'
                    else:
                        shutil.copy(node.resourcepath, newName)
                        break
            else:
                shutil.copy(node.resourcepath, self.resourcepath)
##                names = map(lambda n: n.name, self.entries)
##                dir, name = os.path.split(self.resourcepath)
##                name, ext = os.path.splitext(name)
##                name = Util.getValidName(names, name, ext)
##                shutil.copy(node.resourcepath, name)
##            else:
##            shutil.copy(node.resourcepath, self.resourcepath)
        else:
            shutil.copytree(node.resourcepath, os.path.join(self.resourcepath, node.name))

    def moveFileFrom(self, node):
        # Moving into directory being moved should not be allowed
        sp = os.path.normpath(node.resourcepath)
        dp = os.path.normpath(self.resourcepath)
        if dp[:len(sp)] == sp:
            raise Exception('Cannot move into itself')

        self.copyFileFrom(node)
        if not node.isFolderish():
            os.remove(node.resourcepath)
        else:
            import shutil
            shutil.rmtree(node.resourcepath)

    def setFilter(self, filter):
        self.__class__.filter = filter

    def getFilterExts(self):
        if self.filter == 'BoaFiles':
            return self.exts + ['.py']
        if self.filter == 'BoaInternalFiles':
            return self.exts
        if self.filter == 'AllFiles':
            return ('.*',)

    def load(self, mode='rb'):
        try:
            return open(self.resourcepath, mode).read()
        except IOError, error:
            raise ExplorerNodes.TransportLoadError(error, self.resourcepath)

    def save(self, filename, data, mode='wb'):
        # XXX Maybe IOError should be translated to ExplorerSaveError or something
        if self.resourcepath != filename:
            self.resourcepath = filename
            self.name = os.path.basename(self.resourcepath)
        try:
            open(self.resourcepath, mode).write(data)
        except IOError, error:
            raise ExplorerNodes.TransportSaveError(error, self.resourcepath)

##        try:
##            f = open(self.resourcepath, mode)
##        except IOError, message:
##            dlg = wx.wxMessageDialog(None, 'Could not save\n'+message.strerror,
##                                  'Error', wx.wxOK | wx.wxICON_ERROR)
##            try: dlg.ShowModal()
##            finally: dlg.Destroy()
##        else:
##            f.write(data)
##            f.close()

def isPackage(filename):
    return os.path.exists(os.path.join(filename, EditorModels.PackageModel.pckgIdnt))    

# Register Packages as a File Explorer sub type
PyFileNode.subExplorerReg['folder'].append( 
      (PyFileNode, isPackage, EditorHelper.imgPackageModel),
)

class ResultsFolderNode(PyFileNode):
    results = []
    def openList(self):
        self.parentOpensChildren = true
        self.results.sort()
        self.results.reverse()
        entries = []

        for occrs, filename in self.results:
            tp, node = self.createChildNode('(%d) %s'%(occrs, filename),
                  os.path.join(self.resourcepath, filename))
            if node:
                entries.append(node)

        self.entries = entries
        return self.entries

    def openParent(self, editor):
        editor.explorer.tree.SelectItem(editor.explorer.tree.GetSelection())
        return true

    def open(self, node, editor):
        mod = node.open(editor)
        if mod.views.has_key('Source'):
            mod.views['Source'].doFind(self.lastSearch)
            mod.views['Source'].doNextMatch()
        return mod

    def getTitle(self):
        return 'Find results for %s in %s' % (self.lastSearch, self.resourcepath)



class NonCheckPyFolderNode(PyFileNode):
    def isFolderish(self):
        return true
 