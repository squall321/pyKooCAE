
import os

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
import sys
if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path
## QT Viewer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()
from OCC.Display.qtDisplay import qtViewer3d

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM

from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Check

from KooCAEManager.KooGeometry import (
    KooGeomVertex,
)
from KooCAEManager.KooAISGeometry import (
    KooAISGeomVertex,
    KooAISGeomEdge,
    KooAISGeomLine,
    KooAISGeomArc,
    KooAISGeomWire,
    KooAISGeomFace,
    KooAISGeomShell,
    KooAISGeomSolid,
)

from KooCAEManager.KooAISBoundary import (
    KooAISBoundaryDisplacement,
)

from OCC.Core.TopoDS import (
    TopoDS_Vertex,
    TopoDS_Edge,
    TopoDS_Wire,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Solid,
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Shell,
    )
from OCC.Core.TopAbs import(
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_SOLID,
    TopAbs_SHELL,
    TopAbs_FACE,
    TopAbs_WIRE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
) 
from OCC.Core.BRep import BRep_Tool

from KooCAEManager.KooGeometryManager import KooGeometryManager
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_Reader
from OCC.Core.STEPControl import STEPControl_AsIs

from KooCAEManager.KooAISGeometryManager import KooViewer
from KooCAEManager.KooBoundaryManager import KooBoundaryManager

class KooAISBoundaryManager(KooBoundaryManager):
    def __init__(self, parent = None, viewer = None):
        super(KooAISBoundaryManager,self).__init__()
        self.parent = parent
        if viewer == None:
            self.viewer = KooViewer(parent)
        else:
            self.viewer = viewer
    
    def AddBoundary(self, boundary):
        self.maxboundaryid += 1
        boundary.bid = self.maxboundaryid
        self.boundaryDict[self.maxboundaryid] = boundary
        if type(boundary) == KooAISBoundaryDisplacement:
            self.boundaryDispList.append(boundary)
        return boundary 

    def RemoveBoundary(self, bid, update = True):
        boundary = self.boundaryDict[bid]
        if update == True:
            boundary.Erase(self.viewer, update)
        if type(boundary) == KooAISBoundaryDisplacement:

            self.boundaryDispList.remove(boundary)
            
        del self.boundaryDict[bid]
        
    def SetParentWindow(self, parent):
        self.viewer = KooViewer(parent)

    def Display(self, update = False, trsf : gp_Trsf = None):

        self.DisplayDispBoundary(update, trsf)
    
    def DisplayDispBoundary(self, update = False, trsf : gp_Trsf = None):
        for boundary in self.boundaryDispList:
            boundary.Display(self.viewer, update, trsf)
    
    def RemoveAll(self):
        self.EraseAll()
        super().RemoveAll()
    
    def EraseAll(self, update = False):
        self.EraseAllDispBoundary(update)
    
    def EraseAllDispBoundary(self, update = False):
        for boundary in self.boundaryDispList:
            boundary.Erase(self.viewer, update)

    
