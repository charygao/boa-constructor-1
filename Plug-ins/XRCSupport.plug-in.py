from wxPython.wx import *
from wxPython.xrc import *

from Companions import BaseCompanions

class XmlResourceDTC(BaseCompanions.UtilityDTC):
    handledConstrParams = ()
    def __init__(self, name, designer, objClass):
        BaseCompanions.UtilityDTC.__init__(self, name, designer, objClass)
        self.editors['FileMask'] = StrConstrPropEdit

##    def hideDesignTime(self):
##        return ['Handle']
    def constructor(self):
        return {'FileMask': 'filemask', 'Name': 'name'}
    def designTimeSource(self, position='wxDefaultPos', size='wxDefaultSize'):
        return {'filemask': "''"}
    def writeImports(self):
        return 'from wxPython.xrc import *'

    factoryDict = {'LoadPanel'  : 'XrcPanel'}
    def factory(self, method):
        return self.factoryDict.get(method, None)

from Companions import ContainerCompanions
import methodparse

class XrcPanelDTC(ContainerCompanions.PanelDTC):
    suppressWindowId = true
    def constructor(self):
        return {'Name': 'name'}

    def designTimeControl(self, position, size, args = None):
        """ Create and initialise a design-time control """
        if args:
            args['id'] = -1
            self.control = apply(self.ctrlClass, (), args)
        else:
            self.control = apply(self.ctrlClass, (), self.designTimeDefaults(position, size))

        self.initDesignTimeControl()
        return self.control

    def designTimeDefaults(self, position = wxDefaultPosition,
                                 size = wxDefaultSize):
        xrcObjs = self.designer.getObjectsOfClass(wxXmlResource)
        if not xrcObjs:
            raise 'No wxXmlResource objects found'
        # factory/LoadPage allows no positional info
        if not position: posx, posy = 0, 0
        else:            posx, posy = position.x, position.y
        return {'parent': self.parent, 'id': -1, 'pos': (posx, posy),
                'size': (200, 200)}

    xmlResource = ''
    def persistConstr(self, className, params):
        paramStrs = []
        for param in params.keys():
            paramStrs.append('%s = %s'%(param, params[param]))

        if not self.textConstr:
            xrcObjs = self.designer.getObjectsOfClass(wxXmlResource)
            names = xrcObjs.keys()
            if names:
                dlg = wxSingleChoiceDialog(self.designer, 'Select wxXmlResource to LoadPanel from',
                      'wxXmlResource.LoadPanel', names)
                try:
                    if dlg.ShowModal() == wxID_OK:
                        xrcObj = dlg.GetStringSelection()
                        self.xmlResource = string.split(xrcObj, '.')[1]
                    else:
                        raise 'Cancelled!'
                finally:
                    dlg.Destroy()
            else:
                raise 'No wxXmlResource objects found'
        else:
            self.xmlResource = self.textConstr.factory[0]

        self.textConstr = methodparse.ConstructorParse(
            'self.%s = self.%s.LoadPanel(%s)'%(self.name, self.xmlResource,
            string.join(paramStrs, ', ')))

        self.designer.addCtrlToObjectCollection(self.textConstr)

    def designTimeSource(self, position = 'wxDefaultPosition', size = 'wxDefaultSize'):
        return {'name':  `self.name`}


class XrcPanel(wxPanel):
    pass

import PaletteStore
PaletteStore.paletteLists['Utilities (Data)'].append(wxXmlResource)
PaletteStore.compInfo.update({wxXmlResource: ['wxXmlResource', XmlResourceDTC]})
PaletteStore.paletteLists['ContainersLayout'].append(XrcPanel)
PaletteStore.compInfo[XrcPanel] = ['XrcPanel', XrcPanelDTC]
