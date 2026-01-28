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

from PyQt5 import QtGui
import math

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QAbstractItemView, qApp, QCheckBox, QDockWidget
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox, QShortcut
from PyQt5.QtGui import QMouseEvent, QKeySequence, QCursor

from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.GC import GC_MakeArcOfCircle

from OCC.Core.AIS import AIS_Point, AIS_Shape, AIS_Selection
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCC.Core.Aspect import Aspect_TOM_STAR
from OCC.Core.Quantity import Quantity_NOC_WHITE, Quantity_TOC_RGB
from OCC.Core.Prs3d import Prs3d_PointAspect
from OCC.Core.Aspect import Aspect_InteriorStyle
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeEdge
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
from OCC.Core.TopAbs import (
    TopAbs_FACE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
    TopAbs_SHELL,
    TopAbs_SOLID,
)
from OCC.Core.Graphic3d import Graphic3d_NOM_CHROME
from OCC.Core.Graphic3d import Graphic3d_TMF_2d

from OCC.Core.Quantity import Quantity_Color
from KooPolyLineGeneratorfromCellWidget import KooPolyLineGeneratorfromCellWidget
from KooBooleanOperatorWidget import KooBooleanOperatorWidget
from KooCAEManager.KooCoordinate import KooGridPlane
from KooCAEManager.KooAISGeometryManager import KooAISGeometryManager
from KooCAEManager.KooAISPreviewManager import KooAISPreviewManager

from KooPopupDialog import AnglePopupDialog, PositiveNegativeSelectDialog


class KooCADCAEView(qtViewer3d):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.screenSize = 1000.0        

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Clicked")
            if self.parent != None:
                self.parent.mousePressEvent(event)
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Clicked")
            if self.parent != None:
                self.parent.mousePressEvent(event)                                
                if self._display.selected_shapes != []:
                    firstShape = self._display.selected_shapes[0]
                    if type(firstShape) == TopoDS_Solid:                            
                        self.parent.PopupViewerMenuSolid(event)
                    elif type(firstShape) == TopoDS_Face:
                        self.parent.PopupViewerMenuFace(event)
                    elif type(firstShape) == TopoDS_Edge:
                        self.parent.PopupViewerMenuEdge(event)
                    elif type(firstShape) == TopoDS_Vertex:
                        self.parent.PopupViewerMenuVertex(event)
                else:
                    self.parent.PopupViewerMenu(event)
        elif event.button() == QtCore.Qt.MidButton:
            print("Middle Button Clicked")
            if self.parent != None:
                self.parent.mousePressEvent(event)
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Released")
            for shape in self._display.selected_shapes:
                print(shape)
        if self.parent != None:
            self.parent.mouseReleaseEvent(event)

        return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event : QMouseEvent):
        if self.parent != None:
            self.parent.mouseDoubleClickEvent(event)

        return super().mouseDoubleClickEvent(event)
    
    def mouseMoveEvent(self, event : QMouseEvent):
        if self.parent != None:
            self.parent.mouseMoveEvent(event)
        return super().mouseMoveEvent(event)
    
    def wheelEvent(self, event : QMouseEvent):

        xPos, yPos, zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize, ySize)
        self.screenSize = min(xSize, ySize)
        if self.parent != None:
            self.parent.wheelEvent(event)
        return super().wheelEvent(event)

    def SetBackgroundColor(self, color=Quantity_Color(0.8,0.8,0.8, Quantity_TOC_RGB)):
        self._display.View.SetBackgroundColor(color)
 
    

