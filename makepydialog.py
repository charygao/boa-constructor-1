#Boa:Dialog:MakePyDialog

from wxPython.wx import *
from win32com.client import selecttlb, makepy
import traceback, types

def create(parent):
    return MakePyDialog(parent)

[wxID_MAKEPYDIALOGTYPELIBRARYLIST, wxID_MAKEPYDIALOGBFORDEMAND, wxID_MAKEPYDIALOGOK, wxID_MAKEPYDIALOGDIRECTSPECIFICATION, wxID_MAKEPYDIALOGCANCEL, wxID_MAKEPYDIALOG] = map(lambda _init_ctrls: wxNewId(), range(6))

class MakePyDialog(wxDialog):
    def _init_coll_typeLibraryList_Columns(self, parent):

        parent.InsertColumn(format = wxLIST_FORMAT_CENTRE, col = 0, heading = 'Library Name', width = 372)

    def _init_utils(self):
        pass

    def _init_ctrls(self, prnt):
        wxDialog.__init__(self, size = wxSize(420, 433), id = wxID_MAKEPYDIALOG, title = 'COM Library Generator', parent = prnt, name = 'MakePyDialog', style = wxDEFAULT_DIALOG_STYLE, pos = wxPoint(498, 119))
        self._init_utils()
        EVT_INIT_DIALOG(self, self.OnMakepydialogInitDialog)

        self.typeLibraryList = wxListCtrl(size = wxSize(376, 280), id = wxID_MAKEPYDIALOGTYPELIBRARYLIST, parent = self, name = 'typeLibraryList', validator = wxDefaultValidator, style = wxLC_NO_HEADER | wxLC_REPORT, pos = wxPoint(16, 40))
        self.typeLibraryList.SetToolTipString('List of the registered COM type libraries on your system')
        self._init_coll_typeLibraryList_Columns(self.typeLibraryList)
        EVT_LEFT_DCLICK(self.typeLibraryList, self.OnTypelibrarylistLeftDclick)

        self.OK = wxButton(label = 'Generate', id = wxID_MAKEPYDIALOGOK, parent = self, name = 'OK', size = wxSize(120, 35), style = 0, pos = wxPoint(136, 352))
        self.OK.SetToolTipString('Click to generate a wrapper for the selected library')
        EVT_BUTTON(self.OK, wxID_MAKEPYDIALOGOK, self.OnOkButton)

        self.Cancel = wxButton(label = 'Cancel', id = wxID_MAKEPYDIALOGCANCEL, parent = self, name = 'Cancel', size = wxSize(128, 35), style = 0, pos = wxPoint(264, 352))
        self.Cancel.SetToolTipString('Cancel wrapper generation')
        EVT_BUTTON(self.Cancel, wxID_MAKEPYDIALOGCANCEL, self.OnCancelButton)

        self.bForDemand = wxCheckBox(label = 'Generate Classes on Demand', id = wxID_MAKEPYDIALOGBFORDEMAND, parent = self, name = 'bForDemand', size = wxSize(248, 20), style = 0, pos = wxPoint(144, 328))
        self.bForDemand.SetToolTipString('Minimises amount of code generated by only wrapping used classes (recommended).  Clear to generate a single-file wrapper.')
        self.bForDemand.SetValue(true)

        self.directSpecification = wxTextCtrl(size = wxSize(376, 28), value = '', pos = wxPoint(16, 8), parent = self, name = 'directSpecification', style = 0, id = wxID_MAKEPYDIALOGDIRECTSPECIFICATION)
        self.directSpecification.SetToolTipString('Type text here to search for matching type libraries')
        EVT_TEXT(self.directSpecification, wxID_MAKEPYDIALOGDIRECTSPECIFICATION, self.OnDirectspecificationText)

    def __init__(self, parent):
        self._init_ctrls(parent)
        
        self.generatedFilename =''

    def OnTypelibrarylistLeftDclick(self, event):
        return self.OnOkButton( event )

    def OnOkButton(self, event):
        index = self.typeLibraryList.GetNextItem(-1,state=wxLIST_STATE_SELECTED  )
        # there could be multiple selected, should decide what to do then...
        if index != -1:
            self.generatedFilename = self.Generate( self.libraryList[index] )
            print 'generated to filename', self.generatedFilename
        return self.EndModal( wxID_OK )
##        return wxDialog.OnOK( self, event )

    def OnCancelButton(self, event):
        return self.EndModal( wxID_CANCEL )
    def Generate( self, typeLibrary):
        '''Generate wrapper for a given type library'''
        progress = Progress( self )

        try:
            makepy.GenerateFromTypeLibSpec(
                typeLibrary, None,
                bForDemand = 1,
                bBuildHidden = 1,
                progressInstance = progress,
            )
            filename =progress.filename
            progress.Destroy()
        except Exception, error:
            traceback.print_exc()
            errorMessage = wxMessageDialog( self, str(error), "Generation Failure!", style=wxOK )
            progress.Destroy()
            errorMessage.ShowModal()
            errorMessage.Destroy()
            return None
        return filename

    def OnDirectspecificationText(self, event):
        '''Set focus to any matching item while typing'''
        text = self.directSpecification.GetValue()
        if text:
            items = self.SearchList( text )
            if items:
                for index in range(self.typeLibraryList.GetItemCount()):
                    self.typeLibraryList.SetItemState( index, 0, wxLIST_STATE_SELECTED )
                for (index,item) in items:
                    self.typeLibraryList.SetItemState( index, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED )
                self.typeLibraryList.EnsureVisible( items[0][0] )
        event.Skip()


    def SearchList( self, text ):
        '''Attempt to find the specified text in the list
        of DLL names, classID, and descriptions.'''
        import re
        finder = re.compile( text, re.IGNORECASE )
        items = []
        wxBeginBusyCursor()
        try:
            for attribute in ('desc', 'clsid','dll',):
                for index in range(len( self.libraryList)):
                    librarySpecification = self.libraryList[index]
                    try:
                        value = getattr( librarySpecification, attribute)
                        if value and type(value) == types.StringType:
                            if finder.search( value ):
                                items.append( (index, librarySpecification))
                    except Exception, error:
                        pass
##                    print error, librarySpecification, attribute, repr(getattr( librarySpecification, attribute))
        finally:
            wxEndBusyCursor()
        return items

    def OnMakepydialogInitDialog(self, event):
        '''Initialisation of the dialog starts up a
        process of loading the type library definitions.'''
        wxBeginBusyCursor()
        try:
            self.libraryList = libraryList = selecttlb.EnumTlbs()
            libraryList.sort()
            for index in range(len( libraryList)):
                librarySpecification = libraryList[index]
                self.typeLibraryList.InsertStringItem(
                    index,
                    librarySpecification.desc
                )
        finally:
            wxEndBusyCursor()

class Progress(wxProgressDialog):
    verboseLevel = 1
    filename = ""
    def __init__(self, parent):
        wxProgressDialog.__init__(
            self, "MakePy Progress",
            "Generating type library wrappers",
            parent=parent, style = wxPD_AUTO_HIDE | wxPD_APP_MODAL,
        )
    def Close(self, event=None):
        pass
    def Starting( self, description=None ):
        pass
    def Finished(self):
        pass
    def SetDescription(self, desc, maxticks = None):
        self.Update( newmsg = desc )
    def Tick(self, desc = None):
        pass
    def VerboseProgress(self, desc, verboseLevel = 2):
        if self.verboseLevel >= verboseLevel:
            self.SetDescription(desc)

    def LogBeginGenerate(self, filename):
        self.VerboseProgress("Generating to %s" % filename, 1)
        self.filename = filename

    def LogWarning(self, desc):
        self.VerboseProgress("WARNING: " + desc, 1)

if __name__ == "__main__":
    class DemoFrame( wxFrame ):
        def __init__(self, parent):
            wxFrame.__init__(self, parent, 2400, "File entry with browse", size=(500,150) )
            dialog = MakePyDialog( self )
            dialog.ShowModal( )
            dialog.Destroy()

    class DemoApp(wxApp):
        def OnInit(self):
            wxImage_AddHandler(wxJPEGHandler())
            wxImage_AddHandler(wxPNGHandler())
            wxImage_AddHandler(wxGIFHandler())
            frame = DemoFrame(NULL)
            frame.Show(true)
            self.SetTopWindow(frame)
            return true
    def test( ):
        app = DemoApp(0)
        app.MainLoop()
    print 'Creating dialog'
    test( )