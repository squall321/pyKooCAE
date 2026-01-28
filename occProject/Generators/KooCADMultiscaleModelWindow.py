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

#import QItemSelectionModel
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QAbstractItemView, qApp, QCheckBox, QDockWidget
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox, QShortcut
from PyQt5.QtWidgets import QTreeView, QMenu, QFileDialog
from PyQt5.QtGui import QMouseEvent, QKeySequence, QCursor, QStandardItemModel, QStandardItem

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
from OCC.Core.Graphic3d import Graphic3d_NOM_CHROME
from OCC.Core.Graphic3d import Graphic3d_TMF_2d

from OCC.Core.Quantity import Quantity_Color
from KooPolyLineGeneratorfromCellWidget import KooPolyLineGeneratorfromCellWidget
from KooBooleanOperatorWidget import (
    KooCutOperatorWidget,
    KooBooleanOperatorWidget
)
from KooCAEManager.KooCoordinate import KooGridPlane
from KooCAEManager.KooAISGeometry import (
    KooAISGeomVertex,
    KooAISGeomEdge,
    KooAISGeomFace,
    KooAISGeomCutFace,
    KooAISGeomTextureBox
)
from KooCAEManager.KooAISGeometryManager import KooAISGeometryManager
from KooCAEManager.KooAISPreviewManager import KooAISPreviewManager

from KooPopupDialog import AnglePopupDialog, RadiusPopupDialog, PositiveNegativeSelectDialog
from KooImportImageDialog import ImportImageDialog


class QKooAISGeometryManagerItem(QStandardItem):
    def __init__(self, name,id, aisGeomMan : KooAISGeometryManager):
        super(QKooAISGeometryManagerItem, self).__init__(name)
        self.aisGeomMan : KooAISGeometryManager = aisGeomMan
        self.id = id

class KooStackModelViewer(qtViewer3d):
    
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.previewPnt = None
        self.selectedPntTm3 = None
        self.selectedPntTm2 = None
        self.selectedPntTm1 = None
        self.selectedPntT = None
        self.messageShape = None
        self.gridon = False
        # Set ambient light
        from OCC.Core.Graphic3d import Graphic3d_Vec4
        ambient_color = Graphic3d_Vec4(1.0, 1.0, 1.0, 1.0)  # White color, full intensity
        from OCC.Core.Aspect import Aspect_GradientFillMethod
        
        self.gridPlane = KooGridPlane()
        self.gridPlane.Display(self)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.Display(self)
        self.selectMode = 0
        self.generateOption = 0

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:               
            print("Left Button Pressed")
            return super().mousePressEvent(event)
        else:
            return super().mousePressEvent(event)
    
    def mouseReleaseEventGenerateMode(self, event : QMouseEvent):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos,yPos,zPos = self._display.View.At()
        xLoc = xLoc + xPos 
        yLoc = yLoc + yPos
        
        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        if event.button() == QtCore.Qt.LeftButton:
            self.selectedPntTm3 = self.selectedPntTm2
            self.selectedPntTm2 = self.selectedPntTm1
            self.selectedPntTm1 = self.selectedPntT
            self.selectedPntT = gp_Pnt(xLoc,yLoc,0)
           
            print("Left Button released")
            if self.selectedPntTm2 != None:                
                print("Xn-2 : ",self.selectedPntTm2.X(), "Yn-2 : ",self.selectedPntTm2.Y())
            if self.selectedPntTm1 != None:
                print("Xn-1 : ",self.selectedPntTm1.X(), "Yn-1 : ",self.selectedPntTm1.Y())
            if self.selectedPntT != None:
                print("Xn : ",self.selectedPntT.X(), "Yn : ",self.selectedPntT.Y())
            if self.parent != None: 
                self.parent.mouseReleaseEvent(event)
            return
        elif event.button() == QtCore.Qt.RightButton:
            self.selectedPntT = self.selectedPntTm1
            self.selectedPntTm1 = self.selectedPntTm2
            self.selectedPntTm2 = self.selectedPntTm3
            self.selectedPntTm3 = None
            
            if self.parent != None: 
                self.parent.mouseReleaseEvent(event)
        else:
            return super().mouseReleaseEvent(event)

    def mouseReleaseEventVertexmode(self, event : QMouseEvent):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        xLoc, yLoc = self.GetRoundPoint(xLoc, yLoc)
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button released in Vertex mode")
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
            return 
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button released in Vertex mode")
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
            return
        else:
            return super().mouseReleaseEvent(event)        

    def mouseReleaseEventEdgeMode(self, event : QMouseEvent):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        xLoc, yLoc = self.GetRoundPoint(xLoc, yLoc)
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button released in Edge mode")
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
            return 
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button released in Edge mode")
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
            return
        else:
            return super().mouseReleaseEvent(event)        

    def mouseReleaseEventFaceMode(self, event : QMouseEvent):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        xLoc, yLoc = self.GetRoundPoint(xLoc, yLoc)
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button released in Face mode")
            super().mouseReleaseEvent(event)
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
             
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button released in Face mode")
            super().mouseReleaseEvent(event)
            if self.parent != None:
                self.parent.mouseReleaseEvent(event)
            return
        else:
            return super().mouseReleaseEvent(event)   

    def mouseReleaseEvent(self, event : QMouseEvent):
        if self.selectMode == 0:
            self.mouseReleaseEventGenerateMode(event)
        elif self.selectMode == 1:
            self.mouseReleaseEventVertexmode(event)
        elif self.selectMode == 2:
            self.mouseReleaseEventEdgeMode(event)
        elif self.selectMode == 3:
            self.mouseReleaseEventFaceMode(event)
        else:
            return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEventGenerateMode(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Double Clicked")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        else:
            return super().mouseDoubleClickEvent(event)

    def mouseDoubleClickEventVertexmode(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Double Clicked in Vertex mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in Vertex mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        else:
            return super().mouseDoubleClickEvent(event)

    def mouseDoubleClickEventEdgeMode(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Double Clicked in Edge mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in Edge mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        else:
            return super().mouseDoubleClickEvent(event)

    def mouseDoubleClickEventFaceMode(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Double Clicked in Face mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in Face mode")
            if self.parent != None:
                self.parent.mouseDoubleClickEvent(event)
            return
        else:
            return super().mouseDoubleClickEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        if self.selectMode == 0:
            self.mouseDoubleClickEventGenerateMode(event)
        elif self.selectMode == 1:
            self.mouseDoubleClickEventVertexmode(event)
        elif self.selectMode == 2:
            self.mouseDoubleClickEventEdgeMode(event)
        elif self.selectMode == 3:
            self.mouseDoubleClickEventFaceMode(event)
        return super().mouseDoubleClickEvent(event)

    def mouseMoveEventGenerateMode(self, event : QMouseEvent):   
        self.on_paint(event)
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        #Get Window Size
        #xSize,ySize = self._display.View.Size()
        xPos,yPos,zPos = self._display.View.At()
        xLoc = xLoc + xPos 
        yLoc = yLoc + yPos
        zLoc = zPos
        #help(self._display.View)
        #Get View Size
        #print(xLoc,yLoc,xLoc/xSize,yLoc/ySize)

        if self.messageShape != None:
            self.messageShape.Erase()
        
        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        self.messageShape = self._display.DisplayMessage(gp_Pnt(xLoc,yLoc,0),"x : {xloc}, y : {yloc}".format(xloc=xLoc,yloc=yLoc),height=20)
        #print(self.messageShape)
        if event.buttons() & Qt.LeftButton:    
            #print("Left Button")
            return
        if event.buttons() & Qt.MiddleButton:
            super().mouseMoveEvent(event)
            xSize, ySize = self._display.View.Size()
            screenSize = min(xSize,ySize)
            self.gridPlane.RemoveFromView(self)
            self.gridPlane.SetGridCenter(xPos,yPos)
            #print(xPos,yPos)
            self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
            self.gridPlane.Display(self)
            #print("Wheel Button")
            return
        else:
            return super().mouseMoveEvent(event)

    def mouseMoveEventVertexmode(self, event : QMouseEvent):
        self.on_paint(event)
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        zLoc = zPos
        if self.messageShape != None:
            self.messageShape.Erase()

        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        self.messageShape = self._display.DisplayMessage(gp_Pnt(xLoc,yLoc,0),"x : {xloc}, y : {yloc}".format(xloc=xLoc,yloc=yLoc),height=20)
        if event.buttons() & Qt.LeftButton:
            print("Left Button in Vertex Mode")
           # super().mouseMoveEvent(event)
            return
        if event.buttons() & Qt.MiddleButton:
            print("Middle Button in Vertex Mode")
            super().mouseMoveEvent(event)
            xSize, ySize = self._display.View.Size()
            screenSize = min(xSize,ySize)
            self.gridPlane.RemoveFromView(self)
            self.gridPlane.SetGridCenter(xPos,yPos)
            self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
            self.gridPlane.Display(self)
            return
        else:
            return super().mouseMoveEvent(event)


    def mouseMoveEventEdgeMode(self, event : QMouseEvent):
        self.on_paint(event)
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        zLoc = zPos
        if self.messageShape != None:
            self.messageShape.Erase()

        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        self.messageShape = self._display.DisplayMessage(gp_Pnt(xLoc,yLoc,0),"x : {xloc}, y : {yloc}".format(xloc=xLoc,yloc=yLoc),height=20)
        if event.buttons() & Qt.LeftButton:
            print("Left Button in Edge Mode")
            #super().mouseMoveEvent(event)
            return
        if event.buttons() & Qt.MiddleButton:
            print("Middle Button in Edge Mode")
            super().mouseMoveEvent(event)
            xSize, ySize = self._display.View.Size()
            screenSize = min(xSize,ySize)
            self.gridPlane.RemoveFromView(self)
            self.gridPlane.SetGridCenter(xPos,yPos)
            self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
            self.gridPlane.Display(self)
            return
        else:
            return super().mouseMoveEvent(event)

    def mouseMoveEventFaceMode(self, event : QMouseEvent):
        self.on_paint(event)
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        zLoc = zPos
        if self.messageShape != None:
            self.messageShape.Erase()

        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        self.messageShape = self._display.DisplayMessage(gp_Pnt(xLoc,yLoc,0),"x : {xloc}, y : {yloc}".format(xloc=xLoc,yloc=yLoc),height=20)
        if event.buttons() & Qt.LeftButton:
            print("Left Button in Face Mode")
           # super().mouseMoveEvent(event)
            return
        if event.buttons() & Qt.MiddleButton:
            print("Middle Button in Face Mode")
            super().mouseMoveEvent(event)
            xSize, ySize = self._display.View.Size()
            screenSize = min(xSize,ySize)
            self.gridPlane.RemoveFromView(self)
            self.gridPlane.SetGridCenter(xPos,yPos)
            self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
            self.gridPlane.Display(self)
            return
        else:
            return super().mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        self.PreviewMoveEvent(event)
        if self.selectMode == 0:
            self.mouseMoveEventGenerateMode(event)
        elif self.selectMode == 1:
            self.mouseMoveEventVertexmode(event)
        elif self.selectMode == 2:
            self.mouseMoveEventEdgeMode(event)
        elif self.selectMode == 3:
            self.mouseMoveEventFaceMode(event)
        else:
            return super().mouseMoveEvent(event)

    
    def PreviewMoveEvent(self, event):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos, yPos, zPos = self._display.View.At()
        xLoc = xLoc + xPos
        yLoc = yLoc + yPos
        xLoc, yLoc = self.GetRoundPoint(xLoc, yLoc)
        self.previewPnt = gp_Pnt(xLoc, yLoc, 0)
        #print("X : ", xLoc, "Y : ", yLoc)
        if self.selectMode == 0:
            if self.parent != None: 
                self.parent.PreviewMoveEvent(event)
        elif self.selectMode == 1:
            if self.parent != None: 
                self.parent.PreviewMoveEvent(event)
        elif self.selectMode == 2:
            if self.parent != None: 
                self.parent.PreviewMoveEvent(event)

    def wheelEventGenerateMode(self, event):
        xPos,yPos,zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize,ySize)
        screenSize = min(xSize,ySize)

        #if event.angleDelta().y() > 0:
            #print("Zoom In")
        #else:
            #print("Zoom Out")
        #print('Screen Size : ',screenSize)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.SetGridCenter(xPos,yPos)
        self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
        
        #print(self.gridPlane.axisLength)
        self.gridPlane.Display(self)

    def wheelEventVertexmode(self, event):
        xPos, yPos, zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize, ySize)
        screenSize = min(xSize, ySize)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.SetGridCenter(xPos, yPos)
        self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
        self.gridPlane.Display(self)

    def wheelEventEdgeMode(self, event):
        xPos, yPos, zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize, ySize)
        screenSize = min(xSize, ySize)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.SetGridCenter(xPos, yPos)
        self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
        self.gridPlane.Display(self)

    def wheelEventFaceMode(self, event):
        xPos, yPos, zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize, ySize)
        screenSize = min(xSize, ySize)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.SetGridCenter(xPos, yPos)
        self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
        self.gridPlane.Display(self)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if self.selectMode == 0:
            self.wheelEventGenerateMode(event)
        elif self.selectMode == 1:
            self.wheelEventVertexmode(event)
        elif self.selectMode == 2:
            self.wheelEventEdgeMode(event)
        elif self.selectMode == 3:
            self.wheelEventFaceMode(event) 

    def GetRoundPoint(self, xLoc, yLoc):
        if self.gridon:
            xLoc, yLoc = self.gridPlane.GetNearGridPoint(xLoc,yLoc)
        else:
            gridsize = self.parent.GetGridSize()
            curDeci = abs(round(math.log10(gridsize)))+3

            if gridsize > 0:
                xLoc = round(int(xLoc/gridsize)*self.parent.GetGridSize(),curDeci)
                yLoc = round(int(yLoc/gridsize)*self.parent.GetGridSize(),curDeci)
        return xLoc, yLoc
    
    def UpdateGrid(self):
        xPos,yPos,zPos = self._display.View.At()
        xSize, ySize = self._display.View.Size()
        print(xSize,ySize)
        screenSize = min(xSize,ySize)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.SetGridCenter(xPos,yPos)
        self.gridPlane.SetAxisLengthfromScreenSize(screenSize)
        
        #print(self.gridPlane.axisLength)
        self.gridPlane.Display(self)

    def on_paint(self, event):
        super().paintEvent(event)
        if not self._inited:
            self.InitDriver()  
        self._display.Context.UpdateCurrentViewer()

    def SetBackgroundColor(self, color=Quantity_Color(1.0,1.0,1.0, Quantity_TOC_RGB)):
        self._display.View.SetBackgroundColor(color)
 
    def SetTopView(self):
        # Set the view as a top view from Z-axis
        self._display.View_Top()
    

class KooCADStackModellingWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(KooCADStackModellingWindow, self).__init__(*args, **kwargs)
        #self.vnm2 = None
        #self.vnm1 = None
        #self.vn = None
        self.setAngle = 0.0
        
        self.multiscaleOption = {}
        self.multiscaleOption["Activate"] = False
        self.multiscaleOption["BoundingBox"] = []
        self.vList = [] #Vertex List
        self.eList = [] #Edge List
        self.PolyLineGeneratorfromCellWidget = None
        self.BooleanOperatorWidget = None
        self.CutOperatorWidget = None
        self.dockWidgetCutOperWidget = None
        self.setWindowTitle("KooCAD Stack Modeller")
        self.resize(800, 600)
        self.InitUI()
        self.viewer = KooStackModelViewer(self)
        self.viewer.SetBackgroundColor()
        #self.viewer.SetTopView()
        self.SetOrigin()
       # self.setCentralWidget(self.viewer)
        
        self.previewer = KooAISPreviewManager(self, self.viewer)
        self.importImageDialog = ImportImageDialog(self)

        self.gridOnOff = False
        self.Parent = None

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Layer'])

        self.dataViewTree = QTreeView()
        self.dataViewTree.setModel(self.model)
        # fix the column width of dataViewTree
    
        self.selection_model = self.dataViewTree.selectionModel()
        self.selection_model.selectionChanged.connect(self.on_selection_changed)
        
        layout = QHBoxLayout()
        layout.addWidget(self.dataViewTree)
        self.dataViewTree.setColumnWidth(0, 100)
        self.dataViewTree.setMaximumWidth(100)
        self.dataViewTree.setMinimumWidth(100)
        self.dataViewTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dataViewTree.customContextMenuRequested.connect(self.show_context_menu_tree)

        vlayout = QVBoxLayout()

        hLayoutTop = QHBoxLayout()
        self.OpenPolyLineGeneratorfromCellWidgetButton = QPushButton("PolyLine Generator")
        self.OpenBooleanOperatorButtonWidget = QPushButton("Boolean Operator")
        self.CutOperatorButtonWidget = QPushButton("Cut")
        self.OpenPolyLineGeneratorfromCellWidgetButton.clicked.connect(self.OpenPolyLineGeneratorfromCellWidget)
        self.OpenBooleanOperatorButtonWidget.clicked.connect(self.OpenBooleanOperatorWidget)
        self.CutOperatorButtonWidget.clicked.connect(self.OpenCutOperatorWidget)
        hLayoutTop.addWidget(self.OpenPolyLineGeneratorfromCellWidgetButton)
        hLayoutTop.addWidget(self.OpenBooleanOperatorButtonWidget)
        hLayoutTop.addWidget(self.CutOperatorButtonWidget)
        
        self.InitializeSelection = QPushButton("Init Select")
        self.InitializeSelection.clicked.connect(self.InitSelect)
       

        self.GroupBoxSelectMode = QGroupBox("Select Mode")
        self.GroupSelectModeLayout = QHBoxLayout()
        self.SelectCreateButton = QRadioButton("1 : Generate")
        self.SelectVertexButton = QRadioButton("2 : Vertex")
        self.SelectEdgeButton = QRadioButton("3 : Edge")
        self.SelectFaceButton = QRadioButton("4 : Face")
        self.SelectCreateButton.clicked.connect(self.SelectCreateButtonClicked)
        self.SelectVertexButton.clicked.connect(self.SelectVertexButtonClicked)
        self.SelectEdgeButton.clicked.connect(self.SelectEdgeButtonClicked)
        self.SelectFaceButton.clicked.connect(self.SelectFaceButtonClicked)
        self.GroupSelectModeLayout.addWidget(self.SelectCreateButton)
        self.GroupSelectModeLayout.addWidget(self.SelectVertexButton)
        self.GroupSelectModeLayout.addWidget(self.SelectEdgeButton)
        self.GroupSelectModeLayout.addWidget(self.SelectFaceButton)
        self.GroupBoxSelectMode.setLayout(self.GroupSelectModeLayout)

        self.GroupBoxGenerateOption = QGroupBox("Generate Option")
        self.GroupGenerateOptionLayout = QHBoxLayout()
        self.GenerateOptionLineButton = QRadioButton("Q : Line")
        self.GenerateOptionArcButton = QRadioButton("W : Arc")
        self.GenerateOptionBoxButton = QRadioButton("E : Box")
        self.GenerateOptionCircleButton = QRadioButton("R : Circle")
        self.GenerateOptionLineButton.clicked.connect(self.GenerateOptionLineButtonClicked)
        self.GenerateOptionArcButton.clicked.connect(self.GenerateOptionArcButtonClicked)
        self.GenerateOptionBoxButton.clicked.connect(self.GenerateOptionBoxButtonClicked)
        self.GenerateOptionCircleButton.clicked.connect(self.GenerateOptionCircleButtonClicked)
        self.GroupGenerateOptionLayout.addWidget(self.GenerateOptionLineButton)
        self.GroupGenerateOptionLayout.addWidget(self.GenerateOptionArcButton)
        self.GroupGenerateOptionLayout.addWidget(self.GenerateOptionBoxButton)
        self.GroupGenerateOptionLayout.addWidget(self.GenerateOptionCircleButton)
        self.GroupBoxGenerateOption.setLayout(self.GroupGenerateOptionLayout)


        
        self.SelectCreateButton.setChecked(True)
        self.GenerateOptionLineButton.setChecked(True)
        self.GroupBoxSelectMode.setMaximumHeight(50)
        self.GroupBoxGenerateOption.setMaximumHeight(50)
        vlayout.addLayout(hLayoutTop)
        hlayoutOption = QHBoxLayout()
        hlayoutOption.addWidget(self.InitializeSelection)
        hlayoutOption.addWidget(self.GroupBoxSelectMode)
        hlayoutOption.addWidget(self.GroupBoxGenerateOption)
        vlayout.addLayout(hlayoutOption)
        #layout.addWidget(self.GroupBoxSelectMode)
        vlayout.addWidget(self.viewer)
    
        
        hLayoutBottom = QHBoxLayout()
        self.checkbox = QCheckBox("Grid On")
        
        label = QLabel("Grid Size : ")
        self.gridsizeEdit = QLineEdit()
        self.gridsizeEdit.setText("10")
        
        self.SetOriginButton = QPushButton("Set Origin")
        self.checkbox.stateChanged.connect(self.checkbox_state_changed)
        self.checkbox.setChecked(True)
        self.checkbox_state_changed(2)
        
        self.SetOriginButton.clicked.connect(self.SetOrigin)
        
        hLayoutBottom.addWidget(self.checkbox)
        hLayoutBottom.addWidget(label)
        hLayoutBottom.addWidget(self.gridsizeEdit)
        hLayoutBottom.addWidget(self.SetOriginButton)
        vlayout.addLayout(hLayoutBottom)
        layout.addLayout(vlayout)
        self.setLayout(layout)
       
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Create a shortcut for a specific key
        shortcutSelectModeGenerate = QShortcut(QKeySequence("1"), self)
        shortcutSelectModeVertex = QShortcut(QKeySequence("2"), self)
        shortcutSelectModeEdge = QShortcut(QKeySequence("3"), self)
        shortcutSelectModeFace = QShortcut(QKeySequence("4"), self)

        shortcutSelectModeGenerate.activated.connect(self.SelectCreateButtonClicked)
        shortcutSelectModeVertex.activated.connect(self.SelectVertexButtonClicked)
        shortcutSelectModeEdge.activated.connect(self.SelectEdgeButtonClicked)
        shortcutSelectModeFace.activated.connect(self.SelectFaceButtonClicked)

        shortcutGenerateOptionLine = QShortcut(QKeySequence("Q"), self)
        shortcutGenerateOptionArc = QShortcut(QKeySequence("W"), self)
        shortcutGenerateOptionBox = QShortcut(QKeySequence("E"), self)
        shortcutGenerateOptionCircle = QShortcut(QKeySequence("R"), self)

        shortcutGenerateOptionLine.activated.connect(self.GenerateOptionLineButtonClicked)
        shortcutGenerateOptionArc.activated.connect(self.GenerateOptionArcButtonClicked)
        shortcutGenerateOptionBox.activated.connect(self.GenerateOptionBoxButtonClicked)
        shortcutGenerateOptionCircle.activated.connect(self.GenerateOptionCircleButtonClicked)


        ### Data Initialization 
        
        if __name__ == "__main__":
            self.aisGeomMan = KooAISGeometryManager(self,self.viewer)
            self.curItem = None
            self.maxLayer = 0
            self.add_model("Layer 1", self.aisGeomMan)
            self.maxLayer += 1
        else:
            self.maxLayer = 0
        
        
        self.ResetView()
        # select first item
        index = self.model.index(0, 0)
        self.dataViewTree.selectionModel().select(index, QItemSelectionModel.Select)
        self.on_selection_changed(self.dataViewTree.selectionModel().selection(),self.dataViewTree.selectionModel().selection())



    def InitSelect(self):
        self.SelectCreateButtonClicked()
        self.GenerateOptionLineButtonClicked()
        self.viewer.selectedPntT = None
        self.viewer.selectedPntTm1 = None
        self.viewer.selectedPntTm2 = None
        self.viewer.selectedPntTm3 = None
        self.vList = [] 
        self.vList = [] 

        
    def SetAISGeometryManager(self, aisGeomMan : KooAISGeometryManager):        
        self.aisGeomMan = None
        self.aisGeomMan = aisGeomMan
        aisGeomMan.SetViewer(self.viewer)

    def SetAISGeometryManagerfromIndex(self, index):
        parentItem = self.model.invisibleRootItem()
        item = parentItem.child(index)        
        self.aisGeomMan = item.aisGeomMan
        self.aisGeomMan.SetViewer(self.viewer)

    def SelectCreateButtonClicked(self):

        if self.CutOperatorWidget is not None and self.CutOperatorWidget.isVisible():
            self.SelectFaceButtonClicked()
            return
        self.SelectCreateButton.setChecked(True)
        self.SelectVertexButton.setChecked(False)
        self.SelectEdgeButton.setChecked(False)
        self.SelectFaceButton.setChecked(False)
        self.viewer.selectMode = 0 
        
        self.viewer._display.SetSelectionMode(None)

    def SelectVertexButtonClicked(self):
        if self.CutOperatorWidget is not None and self.CutOperatorWidget.isVisible():
            self.SelectFaceButtonClicked()
            return
        self.SelectCreateButton.setChecked(False)
        self.SelectVertexButton.setChecked(True)
        self.SelectEdgeButton.setChecked(False)
        self.SelectFaceButton.setChecked(False)
        self.viewer.selectMode = 1

        self.viewer._display.SetSelectionModeVertex()

    def SelectEdgeButtonClicked(self):
        if self.CutOperatorWidget is not None and self.CutOperatorWidget.isVisible():
            self.SelectFaceButtonClicked()
            return
        self.SelectCreateButton.setChecked(False)
        self.SelectVertexButton.setChecked(False)
        self.SelectEdgeButton.setChecked(True)
        self.SelectFaceButton.setChecked(False)
        self.viewer.selectMode = 2

        self.viewer._display.SetSelectionModeEdge()

    def SelectFaceButtonClicked(self):        
        self.SelectCreateButton.setChecked(False)
        self.SelectVertexButton.setChecked(False)
        self.SelectEdgeButton.setChecked(False)
        self.SelectFaceButton.setChecked(True)
        self.viewer.selectMode = 3

        self.viewer._display.SetSelectionModeFace()

    def GenerateOptionLineButtonClicked(self):
        self.GenerateOptionLineButton.setChecked(True)
        self.GenerateOptionArcButton.setChecked(False)
        self.GenerateOptionBoxButton.setChecked(False)
        self.GenerateOptionCircleButton.setChecked(False)
        self.viewer.generateOption = 0

    def GenerateOptionArcButtonClicked(self):
        self.GenerateOptionLineButton.setChecked(False)
        self.GenerateOptionArcButton.setChecked(True)
        self.GenerateOptionBoxButton.setChecked(False)
        self.GenerateOptionCircleButton.setChecked(False)
        self.viewer.generateOption = 1

    def GenerateOptionBoxButtonClicked(self):
        self.GenerateOptionLineButton.setChecked(False)
        self.GenerateOptionArcButton.setChecked(False)
        self.GenerateOptionBoxButton.setChecked(True)
        self.GenerateOptionCircleButton.setChecked(False)
        self.viewer.generateOption = 2
        self.viewer.selectedPntTm2 = None
        self.viewer.selectedPntTm1 = None
        self.vList = []
        self.eList = []

    def GenerateOptionCircleButtonClicked(self):
        self.GenerateOptionLineButton.setChecked(False)
        self.GenerateOptionArcButton.setChecked(False)
        self.GenerateOptionBoxButton.setChecked(False)
        self.GenerateOptionCircleButton.setChecked(True)
        self.viewer.generateOption = 3
        self.viewer.selectedPntTm2 = None
        self.viewer.selectedPntTm1 = None 
        self.vList = []
        self.eList = []

    def GetGridSize(self):
        svalue = self.gridsizeEdit.text()
        #if svalue is float
         
        if svalue.replace('.','',1).isdigit():
            value = float(svalue) 
            if value <= 0:
                value = 1.e-8
        else:
            value = 1.e-8
        return value     

    def OpenPolyLineGeneratorfromCellWidget(self):
        if self.PolyLineGeneratorfromCellWidget == None:
            self.PolyLineGeneratorfromCellWidget = KooPolyLineGeneratorfromCellWidget(self.On_PolyLineGeneratorfromCellWidget_Update,self)
        
        if self.PolyLineGeneratorfromCellWidget.isVisible() == False:
            self.PolyLineGeneratorfromCellWidget.show()
            self.dockWidgetPolyGenCellWidget = QDockWidget("PolyLine Generator",self)
            self.dockWidgetPolyGenCellWidget.setWidget(self.PolyLineGeneratorfromCellWidget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidgetPolyGenCellWidget)

    def OpenBooleanOperatorWidget(self):
        if self.BooleanOperatorWidget == None:
            self.BooleanOperatorWidget = KooBooleanOperatorWidget(self.On_BooleanOperator_Update,self)
        
        if self.BooleanOperatorWidget.isVisible() == False:
            self.BooleanOperatorWidget.show()
            self.dockWidgetBoolOperWidget = QDockWidget("Boolean Operator",self)
            self.dockWidgetBoolOperWidget.setWidget(self.BooleanOperatorWidget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidgetBoolOperWidget)

    def OpenCutOperatorWidget(self):
        if self.CutOperatorWidget == None:
            self.CutOperatorWidget = KooCutOperatorWidget(self.On_CutOperator_Update,self)

        if self.CutOperatorWidget.isVisible() == False:            
            self.CutOperatorWidget = KooCutOperatorWidget(self.On_CutOperator_Update,self)
            self.SelectFaceButtonClicked()
            self.CutOperatorWidget.show()

            if self.dockWidgetCutOperWidget is not None:                           
                self.dockWidgetCutOperWidget.setWidget(None)
                self.removeDockWidget(self.dockWidgetCutOperWidget)

            if self.curItem is not None:
                parent_item = self.model.invisibleRootItem()
                self.ResetView()
                for row in range(parent_item.rowCount()):
                    item = parent_item.child(row)
                    if item.index() == self.curItem.index():
                        curItem : QKooAISGeometryManagerItem = item
                        curItem.aisGeomMan.SetTransparencyAll(0.0)
                        curItem.aisGeomMan.Display()
                self.viewer._display.Context.UpdateCurrentViewer()


            self.dockWidgetCutOperWidget = QDockWidget("Cut Operator",self)
            self.dockWidgetCutOperWidget.setWidget(self.CutOperatorWidget)        
            self.dockWidgetCutOperWidget.closeEvent = self.CutOperatorWidget.closeEvent
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidgetCutOperWidget)
            

    def On_PolyLineGeneratorfromCellWidget_Update(self):
        groups = self.PolyLineGeneratorfromCellWidget.edgeGroups
        groupid = 0
        for group in groups:
            groupid += 1
            if len(group) > 1:
                edge0 = group[0]
                edgeLast = group[len(group)-1] 
                x1, y1 = edge0[1],edge0[2]
                x2, y2 = edge0[3],edge0[4]
                x3, y3 = edgeLast[1],edgeLast[2]
                x4, y4 = edgeLast[3],edgeLast[4] 
                isClosed = False
                if x1 == x3 and y1 == y3:
                    isClosed = True
                    pass
                elif x2 == x3 and y2 == y3:
                    isClosed = True
                    pass
                elif x1 == x4 and y1 == y4:
                    isClosed = True
                    pass
                elif x2 == x4 and y2 == y4:
                    isClosed = True
                    pass
                if isClosed == True:
                    print(groupid,"th group is closed")
                    vertexList = {}
                    edgeList = {}
                    for edge in group:
                        if edge[0] == "Line":
                            x1, y1 = edge[1],edge[2]
                            x2, y2 = edge[3],edge[4]
                            v1 = self.aisGeomMan.FindVertex(x1,y1,0.0)
                            v2 = self.aisGeomMan.FindVertex(x2,y2,0.0)
                            e = self.aisGeomMan.FindLinefromVertices(v1,v2)
                            vertexList[v1.id] = v1
                            vertexList[v2.id] = v2
                            edgeList[e.id] = e
                        elif edge[0] == "Arc":
                            x1, y1 = edge[1],edge[2]
                            x2, y2 = edge[3],edge[4]
                            x3, y3 = edge[5],edge[6]
                            v1 = self.aisGeomMan.FindVertex(x1,y1,0.0)
                            v2 = self.aisGeomMan.FindVertex(x2,y2,0.0)
                            v3 = self.aisGeomMan.FindVertex(x3,y3,0.0)
                            counterClockWise = True
                            if edge[7] == 1:
                                counterClockWise = False
                            e = self.aisGeomMan.FindArcfromVertices(v1,v2,v3,counterClockWise)
                            vertexList[v1.id] = v1
                            vertexList[v2.id] = v2
                            vertexList[v3.id] = v3
                            edgeList[e.id] = e
                    for vertex in vertexList.values():
                        vertex.Display(self.viewer)
                    edges = [] 
                    for value in edgeList.values():
                        edges.append(value)
                        value.Display(self.viewer)
                    print("Number of Edges",len(edges))
                    wire = self.aisGeomMan.FindWirefromEdges(edges)
                    face = self.aisGeomMan.FindFacefromWire(wire)
                    
                    face.Display(self.viewer)


                    pass
        
        self.viewer._display.Context.UpdateCurrentViewer()       

        pass

    def On_BooleanOperator_Update(self):
        pass 
    
    def On_CutOperator_Update(self,eventType = "None"):
        self.SelectCreateButtonClicked()
        
                
        if self.CutOperatorWidget.CutOperationMode == True:
            faceMain = self.CutOperatorWidget.selectedMainFace
            faceTool = self.CutOperatorWidget.selectedToolFace
            if faceMain is not None and faceTool is not None:
                #faceMain.Display(self.viewer)
                #faceTool.Display(self.viewer)
                faceMainFace = faceMain.face
                faceToolFace = faceTool.face
                '''
                from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
                cut = BRepAlgoAPI_Cut(faceMainFace,faceToolFace)
                cut.Build()
                result = cut.Shape()
                self.viewer._display.DisplayShape(result)
                '''
                self.aisGeomMan.RemoveFacewithSubGeometries(faceMain)
                self.aisGeomMan.RemoveFacewithSubGeometries(faceTool)
                
                cutFace = self.aisGeomMan.CreateCutFace(faceMain,faceTool)
                cutFace.Display(self.viewer)
                
                

                self.CutOperatorWidget.selectedMainFace = cutFace
                self.CutOperatorWidget.selectedToolFace = None
                self.CutOperatorWidget.CutOperationMode = False
        
        if eventType == "Close":
            if self.curItem is not None:
                parent_item = self.model.invisibleRootItem()
                self.ResetView()
                for row in range(parent_item.rowCount()):
                    item = parent_item.child(row)
                    if item.index() == self.curItem.index():
                        curItem : QKooAISGeometryManagerItem = item
                        curItem.aisGeomMan.SetTransparencyAll(0.0)
                        curItem.aisGeomMan.Display()
                    else:
                        curItem : QKooAISGeometryManagerItem = item
                        curItem.aisGeomMan.SetTransparencyAll(0.5)
                        curItem.aisGeomMan.Display()  

       
        self.viewer._display.Context.UpdateCurrentViewer()

    def PreviewMoveEvent(self, event : QMouseEvent):
        prevPnt = self.viewer.previewPnt
        Pnt = self.viewer.selectedPntT
        Pntm1 = self.viewer.selectedPntTm1
        
        Pntm2 = self.viewer.selectedPntTm2
        self.previewer.ClearAll()
        #print("Line Preview is activated")
        if self.GenerateOptionLineButton.isChecked():
            if Pnt != None:
                if Pnt.Distance(prevPnt) < 1.e-6:
                    pass
                else:
                    e = BRepBuilderAPI_MakeEdge(Pnt,prevPnt).Edge()
                    self.previewer.AddEdge(e)
            pass
        elif self.GenerateOptionArcButton.isChecked():
            if Pnt != None and Pntm1 != None:
                startPnt = Pntm1
                centerPnt = Pnt
                minAngle, endPnt = self.FindClosestPntfromonCircle(prevPnt,centerPnt,startPnt)
                if startPnt.Distance(endPnt) < 1.e-6:
                    return
                xStartPnt = startPnt.X() - centerPnt.X()
                yStartPnt = startPnt.Y() - centerPnt.Y()
                xEndPnt = endPnt.X() - centerPnt.X()
                yEndPnt = endPnt.Y() - centerPnt.Y()
                angleStartPnt = math.atan2(yStartPnt,xStartPnt)
                angleStartPnt = math.degrees(angleStartPnt)
                angleEndPnt = math.atan2(yEndPnt,xEndPnt)
                angleEndPnt = math.degrees(angleEndPnt)
                if angleStartPnt < 0.0:
                    angleStartPnt += 360.0
                
                while angleEndPnt < angleStartPnt:
                    angleEndPnt += 360.0

                counterClockwise = False
                print(angleStartPnt,angleEndPnt)
                if angleEndPnt-angleStartPnt > 180.0:
                    counterClockwise = True
                else:
                    counterClockwise = False

                self.setAngle = minAngle - angleStartPnt
                if self.setAngle < 0.0:
                    self.setAngle += 360.0
                normal_direction = gp_Vec(0.0,0.0,1.0)
                self.radius = centerPnt.Distance(startPnt)
                coord = gp_Ax2(centerPnt,gp_Dir(normal_direction))
                circle = gp_Circ(coord,self.radius)
                if counterClockwise == True:
                    arc = GC_MakeArcOfCircle(circle,endPnt,startPnt,True)
                else:
                    arc = GC_MakeArcOfCircle(circle,startPnt,endPnt,True)
                    
                e = BRepBuilderAPI_MakeEdge(arc.Value()).Edge()
                self.previewer.AddEdge(e) 

                '''
                startPnt = Pntm1
                centerPnt = Pnt
                minAngle, endPnt = self.FindClosestPntfromonCircle(prevPnt,centerPnt,startPnt)
                if startPnt.Distance(endPnt) < 1.e-6:
                    return
                print("startPnt :",startPnt.X(),startPnt.Y())
                print("centerPnt :",centerPnt.X(),centerPnt.Y())
                print("endPnt :",endPnt.X(),endPnt.Y())
                xStartPnt = startPnt.X() - centerPnt.X()
                yStartPnt = startPnt.Y() - centerPnt.Y()
                angleStartPnt = math.atan2(yStartPnt,xStartPnt)
                angleStartPnt = math.degrees(angleStartPnt)
                if angleStartPnt < 0.0:
                    angleStartPnt += 360.0
                print("Min Angle :",minAngle)
                print("Angle Start Pnt :",angleStartPnt)
                self.setAngle = minAngle - angleStartPnt
                if self.setAngle < 0.0:
                    self.setAngle += 360.0                
                normal_direction = gp_Vec(0.0,0.0,1.0)
                self.radius = centerPnt.Distance(startPnt)
                
                coord = gp_Ax2(centerPnt,gp_Dir(normal_direction))
                circle = gp_Circ(coord,self.radius)

                arc = GC_MakeArcOfCircle(circle,startPnt,endPnt,True)
                e = BRepBuilderAPI_MakeEdge(arc.Value()).Edge()
                self.previewer.AddEdge(e)   
                '''
            pass
        elif self.GenerateOptionBoxButton.isChecked():
            if Pnt != None:
                firstPnt = Pnt 
                secondPnt = prevPnt
                if secondPnt.Distance(firstPnt) < 1.e-6:
                    return

                x1, y1 = firstPnt.X(), firstPnt.Y()
                x2, y2 = secondPnt.X(), secondPnt.Y()

                if x1 < x2:
                    xMin = x1
                    xMax = x2
                else:
                    xMin = x2
                    xMax = x1
                if y1 < y2:
                    yMin = y1
                    yMax = y2
                else:
                    yMin = y2
                    yMax = y1

                if yMin == yMax:
                    yMin = 0.99999*yMax
                if xMin == xMax:
                    xMin = 0.99999*xMax
                
                p1 = gp_Pnt(xMin,yMin,0.0)
                p2 = gp_Pnt(xMax,yMin,0.0)
                p3 = gp_Pnt(xMax,yMax,0.0)
                p4 = gp_Pnt(xMin,yMax,0.0)
                e1 = BRepBuilderAPI_MakeEdge(p1,p2).Edge()
                e2 = BRepBuilderAPI_MakeEdge(p2,p3).Edge()
                e3 = BRepBuilderAPI_MakeEdge(p3,p4).Edge()
                e4 = BRepBuilderAPI_MakeEdge(p4,p1).Edge()
                self.previewer.AddEdge(e1)
                self.previewer.AddEdge(e2)
                self.previewer.AddEdge(e3)
                self.previewer.AddEdge(e4)
                
               
            pass
        elif self.GenerateOptionCircleButton.isChecked():
            if Pnt != None:
                centerPnt = Pnt
                endPnt = prevPnt
                normal_vector = gp_Dir(0,0,1.0)
                coord = gp_Ax2(centerPnt,normal_vector)

                radius = centerPnt.Distance(endPnt)
                circle = gp_Circ(coord,radius)
                edge = BRepBuilderAPI_MakeEdge(circle).Edge()
                self.previewer.AddEdge(edge)
            
            pass

    def FindClosestPntfromonCircle(self, Pnt : gp_Pnt, centerPnt : gp_Pnt, startPnt : gp_Pnt,division = 72):
        radius = centerPnt.Distance(startPnt)
        x0, y0, z0 = centerPnt.X(), centerPnt.Y(), centerPnt.Z()
        xc, yc, zc = 0.0, 0.0, 0.0
        xp, yp, zp = Pnt.X(), Pnt.Y(), Pnt.Z()
        minDistance = 1.e99
        cloestPnt = gp_Pnt(xp,yp,zp)
        minAngle = 0.0
        for i in range(0,division):
           angle = float(360.0/division*i)
           xc = x0 + radius * math.cos(math.radians(angle))
           yc = y0 + radius * math.sin(math.radians(angle))
           zc = z0
           curDistance = math.sqrt((xc - xp)**2 + (yc - yp)**2 + (zc - zp)**2)
           if curDistance < minDistance:
               minDistance = curDistance
               cloestPnt = gp_Pnt(xc,yc,zc)
               minAngle = angle
               print(minAngle)
              
        
        return minAngle, cloestPnt


    def mouseReleaseEventSelectGenerate(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                print("Control + Left Button in main Window")
                self.GenerateLinebyControlClickView()
                return
            elif modifiers == QtCore.Qt.ShiftModifier:
                print("Shift + Left Button in main Window")
            elif modifiers == QtCore.Qt.AltModifier:
                print("Alt + Left Button in main Window")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
                print("Control + Shift + Left Button in main Window")
            elif modifiers == (Qt.ControlModifier | Qt.AltModifier):
                print("Control + Alt + Left Button in main Window")
            elif modifiers == (Qt.ShiftModifier | Qt.AltModifier):
                print("Shift + Alt + Left Button in main Window")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier):
                print("Control + Shift + Alt + Left Button in main Window")
            else:
                print("Left Button in main Window")
                if self.GenerateOptionLineButton.isChecked():
                    self.GenerateLinebyClickView()
                elif self.GenerateOptionArcButton.isChecked():
                    self.GenerateArcbyClickView()
                elif self.GenerateOptionBoxButton.isChecked():
                    self.GenerateBoxbyClickView()
                elif self.GenerateOptionCircleButton.isChecked():
                    self.GenerateCirclebyClickView()

                if self.PolyLineGeneratorfromCellWidget != None:
                    if self.PolyLineGeneratorfromCellWidget.isOpened:
                        pass
                return
        elif event.button() == QtCore.Qt.MiddleButton:
            return
        elif event.button() == QtCore.Qt.RightButton:
            if event.type() == QMouseEvent.MouseButtonDblClick:
                #self.vnm2 = None
                #self.vnm1 = None
                #self.vn = None
                print("Double Click in main Window")
                self.vList = [] 
                self.eList = [] #Edge List
            else:
                print("Right Button in main Window")
                
                
                curType = "Line"
                if len(self.eList)>0:
                    print("Erase Edge")
                    #print(self.aisGeomMan.edges)
                    self.aisGeomMan.RemoveEdge(self.eList[len(self.eList)-1])
                    if self.eList[len(self.eList)-1].type == "Arc":
                        curType = "Arc"
                        self.vList.pop()
                        self.viewer.selectedPntT = self.vList[len(self.vList)-2].pnt
                        
                        #self.viewer.selectedPntT = self.viewer.selectedPntTm1
                        #self.viewer.selectedPntTm1 = self.viewer.selectedPntTm2
                        #self.viewer.selectedPntTm2 = self.viewer.selectedPntTm3
                    self.eList[len(self.eList)-1].Erase(self.viewer)
                    self.eList.pop()
                if len(self.vList)>0:
                    #curVPos = len(self.vList)-1
                    #vn = self.vList[curVPos]
                    #self.aisGeomMan.RemoveVertex(vn)
                    #vn.Erase(self.viewer)
                    self.vList.pop()
                #self.vn = self.vnm1
                #self.vnm1 = self.vnm2
                #self.vnm2 = None

            self.viewer._display.Context.UpdateCurrentViewer()       
            return
        return super().mouseReleaseEvent(event)
    def mouseReleaseEventSelectVertex(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                print("Control + Left Button in main Window with Vertex Mode")
            elif modifiers == QtCore.Qt.ShiftModifier:
                print("Shift + Left Button in main Window with Vertex Mode")
            elif modifiers == QtCore.Qt.AltModifier:
                print("Alt + Left Button in main Window with Vertex Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
                print("Control + Shift + Left Button in main Window with Vertex Mode")
            elif modifiers == (Qt.ControlModifier | Qt.AltModifier):
                print("Control + Alt + Left Button in main Window with Vertex Mode")
            elif modifiers == (Qt.ShiftModifier | Qt.AltModifier):
                print("Shift + Alt + Left Button in main Window with Vertex Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier):
                print("Control + Shift + Alt + Left Button in main Window with Vertex Mode")
            else:       
                print("Left Button in main Window with Vertex Mode")
                self.viewer._display.Context.UpdateCurrentViewer()
                return
        elif event.button() == QtCore.Qt.MiddleButton:
            print("Middle Button in main Window with Vertex Mode")
            self.viewer._display.Context.UpdateCurrentViewer()
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button in main Window with Vertex Mode")
            self.viewer._display.Context.UpdateCurrentViewer()
            return        
        return super().mouseReleaseEvent(event)
    
    def mouseReleaseEventSelectEdge(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                print("Control + Left Button in main Window with Edge Mode")
            elif modifiers == QtCore.Qt.ShiftModifier:
                print("Shift + Left Button in main Window with Edge Mode")
            elif modifiers == QtCore.Qt.AltModifier:
                print("Alt + Left Button in main Window with Edge Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
                print("Control + Shift + Left Button in main Window with Edge Mode")
            elif modifiers == (Qt.ControlModifier | Qt.AltModifier):
                print("Control + Alt + Left Button in main Window with Edge Mode")
            elif modifiers == (Qt.ShiftModifier | Qt.AltModifier):
                print("Shift + Alt + Left Button in main Window with Edge Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier):
                print("Control + Shift + Alt + Left Button in main Window with Edge Mode")
            else:
                print("Left Button in main Window with Edge Mode")
                self.viewer._display.Context.UpdateCurrentViewer()
                return
        elif event.button() == QtCore.Qt.MiddleButton:
            print("Middle Button in main Window with Edge Mode")
            self.viewer._display.Context.UpdateCurrentViewer()
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button in main Window with Edge Mode")
            self.viewer._display.Context.UpdateCurrentViewer()
            return        
        return super().mouseReleaseEvent(event)
    
    def mouseReleaseEventSelectFace(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                print("Control + Left Button in main Window with Face Mode")
            elif modifiers == QtCore.Qt.ShiftModifier:
                print("Shift + Left Button in main Window with Face Mode")
            elif modifiers == QtCore.Qt.AltModifier:
                print("Alt + Left Button in main Window with Face Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
                print("Control + Shift + Left Button in main Window with Face Mode")
            elif modifiers == (Qt.ControlModifier | Qt.AltModifier):
                print("Control + Alt + Left Button in main Window with Face Mode")
            elif modifiers == (Qt.ShiftModifier | Qt.AltModifier):
                print("Shift + Alt + Left Button in main Window with Face Mode")
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier):
                print("Control + Shift + Alt + Left Button in main Window with Face Mode")
            else:
                print("Left Button in main Window with Face Mode")
                if len(self.viewer._display.selected_shapes)>0:
                    face = self.viewer._display.selected_shapes[0]
                    face2 = self.aisGeomMan.FindFace(face)
                    if face2 == None:
                        face2 = self.aisGeomMan.FindCompound(face)
                    face = face2
                    if face is not None:
                        if self.CutOperatorWidget is not None and self.CutOperatorWidget.isVisible():
                            self.CutOperatorWidget.AddFace(face)                        
                
            
        elif event.button() == QtCore.Qt.MiddleButton:
            print("Middle Button in main Window with Face Mode")
            self.viewer._display.Context.UpdateCurrentViewer()
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button in main Window with Face Mode")
            for shape in self.viewer._display.selected_shapes:
                face = self.aisGeomMan.FindFace(shape)
                if face is not None:
                    wire = face.wire
                    for edge in wire.edges:
                        for vertex in edge.vertices:
                            self.aisGeomMan.RemoveVertex(vertex)
                        self.aisGeomMan.RemoveEdge(edge) 
                    self.aisGeomMan.RemoveWire(wire)      
                    self.aisGeomMan.RemoveFace(face)
            self.viewer._display.Context.UpdateCurrentViewer()
            return
        return super().mouseReleaseEvent(event)
    
    def mouseReleaseEvent(self, event : QMouseEvent) -> None:
        
        if self.SelectCreateButton.isChecked():
            self.mouseReleaseEventSelectGenerate(event)
        elif self.SelectVertexButton.isChecked():
            self.mouseReleaseEventSelectVertex(event)
        elif self.SelectEdgeButton.isChecked():
            self.mouseReleaseEventSelectEdge(event)
        elif self.SelectFaceButton.isChecked():
            self.mouseReleaseEventSelectFace(event)
        else:
            return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEventSelectGenerate(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Double Clicked in main Window")
            if len(self.eList)>0:
                wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
                wire.Display(self.viewer)
                self.vList = [] 
                self.eList = [] 
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in main Window")
            return
        else:
            return super().mouseDoubleClickEvent(event)
        
    def mouseDoubleClickEventSelectVertex(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Double Clicked in main Window with Vertex Mode")
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in main Window with Vertex Mode")
            return
        else:
            return super().mouseDoubleClickEvent(event)

    def mouseDoubleClickEventSelectEdge(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Double Clicked in main Window with Edge Mode")
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in main Window with Edge Mode")
            return
        else:
            return super().mouseDoubleClickEvent(event)
    def mouseDoubleClickEventSelectFace(self, event : QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button Double Clicked in main Window with Face Mode")
            return
        elif event.button() == QtCore.Qt.RightButton:
            print("Right Button Double Clicked in main Window with Face Mode")
            return
        else:
            return super().mouseDoubleClickEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.SelectCreateButton.isChecked():
            self.mouseDoubleClickEventSelectGenerate(event)
        elif self.SelectVertexButton.isChecked():
            self.mouseDoubleClickEventSelectVertex(event)
        elif self.SelectEdgeButton.isChecked():
            self.mouseDoubleClickEventSelectEdge(event)
        elif self.SelectFaceButton.isChecked():
            self.mouseDoubleClickEventSelectFace(event)
        return super().mouseDoubleClickEvent(event)  

    def FindClosestVertexwithGrid(self, x, y):
        gridLength = self.viewer.gridPlane.axisLength/self.viewer.gridPlane.gridSize
        minDist, vertex = self.aisGeomMan.FindClosestVertex(x, y,0.0)
        print(gridLength)
        print(minDist,vertex)
        if minDist < gridLength:
            return vertex
        else:
            return None

    def GenerateLinebyControlClickView(self):
        curPoint = self.viewer.selectedPntT
        prevPoint = self.viewer.selectedPntTm1
        print(curPoint)
        print(prevPoint)
        if curPoint == None:
            return
        vertex = self.FindClosestVertexwithGrid(curPoint.X(), curPoint.Y())

        print(vertex)
        if vertex == None:
            return
        if len(self.vList) == 0:
            self.vList.append(vertex)
            self.viewer.selectedPntT = vertex.pnt
            print("Test Zero Reached")
            return
        print("Test Reached1")
        print(len(self.vList))
        print(len(self.eList))
        for i in range(0,len(self.vList)):
            print(self.vList[i].pnt.X(), self.vList[i].pnt.Y(), self.vList[i].pnt.Z())
        for i in range(1,len(self.vList)):            
            if self.vList[i].pnt.Distance(vertex.pnt) < 1.e-6:
                return
        print("Test Reached2")
        if prevPoint == None:
            pass
        else:
            if curPoint.Distance(prevPoint) < 1.e-6:
                return
        self.viewer.selectedPntT = vertex.pnt
        vn = vertex
        self.vList.append(vn)
        if len(self.vList) >=2:
            vnm1 = self.vList[len(self.vList)-2]
            if vnm1.pnt.Distance(curPoint) < 1.e-6:
                return
        print("Test Reached3")

        if len(self.vList) == 1:
            return
        else:
            if vnm1.pnt.Distance(vn.pnt) < 1.e-6:
                return
            en = self.aisGeomMan.CreateLinefromVertices(vnm1,vn)
            self.eList.append(en)
            en.Display(self.viewer)
            v1 = self.vList[0]
            if vn.pnt.Distance(v1.pnt) <1.e-6:
                print("Generate Polygon")
                wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
                face = self.aisGeomMan.CreateFacefromWire(wire)
                wire.Display(self.viewer)
                face.Display(self.viewer)
                self.vList = []
                self.eList = []
                self.viewer.selectedPntT = None
                self.viewer.selectedPntTm1 = None
                self.viewer.selectedPntTm2 = None

        self.viewer._display.Context.UpdateCurrentViewer()
    def GenerateFace(self):
        v1 = self.vList[0]
        vn = self.vList[len(self.vList)-1]
        if len(self.vList)>=2:
            if vn.pnt.Distance(v1.pnt) < 1.e-6:
                print("Generate Polygon")
                wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
                face = self.aisGeomMan.CreateFacefromWire(wire)
                wire.Display(self.viewer)
                face.Display(self.viewer)
                self.vList = [] 
                self.eList = [] 
                self.viewer.selectedPntT = None
                self.viewer.selectedPntTm1 = None
                self.viewer.selectedPntTm2 = None

                #self.aisGeomMan.CreatePolygonfromVertices(self.vList)
    def GenerateFacefromBox(self):
        wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
        face = self.aisGeomMan.CreateFacefromWire(wire)
        wire.Display(self.viewer)
        face.Display(self.viewer)
        self.vList = []
        self.eList = []
        self.viewer.selectedPntT = None
        self.viewer.selectedPntTm1 = None
        self.viewer.selectedPntTm2 = None

        
    def GenerateFacefromCircle(self):
        wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
        face = self.aisGeomMan.CreateFacefromWire(wire)
        wire.Display(self.viewer)
        face.Display(self.viewer)
        self.vList = []
        self.eList = []
        self.viewer.selectedPntT = None
        self.viewer.selectedPntTm1 = None
        self.viewer.selectedPntTm2 = None


    def GenerateLinebyClickView(self):
        curPoint = self.viewer.selectedPntT
        prevPoint = self.viewer.selectedPntTm1
        if curPoint == None:
            return
      
        if prevPoint != None:
            if curPoint.Distance(prevPoint) < 1.e-6:
                return 
        
        #self.vnm2 = self.vnm1
        #self.vnm1 = self.vn
        #self.vn = self.aisGeomMan.CreateVertex(curPoint.X(),curPoint.Y(), curPoint.Z())
        if len(self.vList) != 0:
            vnm1 = self.vList[len(self.vList)-1]
            if vnm1.pnt.Distance(curPoint) < 1.e-6:
                return
        vn = self.aisGeomMan.CreateVertex(curPoint.X(),curPoint.Y(), curPoint.Z())
        self.vList.append(vn)
        vn.Display(self.viewer)
        if len(self.vList)>=2:
            
            en = self.aisGeomMan.CreateLinefromVertices(vnm1,vn)
            self.eList.append(en)
            en.Display(self.viewer)         
            self.viewer.selectedPntTm1 = None
    
        self.GenerateFace()
        self.viewer._display.Context.UpdateCurrentViewer()

    def GenerateArcbyClickView(self):
        pntT = self.viewer.selectedPntT
        pntTm1 = self.viewer.selectedPntTm1
        pntTm2 = self.viewer.selectedPntTm2
        if pntT == None:
            return
        if pntT != None:
            print("PntT",pntT.X(),pntT.Y(),pntT.Z())
        if pntTm1 != None:
            print("PntTm1",pntTm1.X(),pntTm1.Y(),pntTm1.Z())
        if pntTm2 != None:
            print("PntTm2",pntTm2.X(),pntTm2.Y(),pntTm2.Z())
        if pntTm1 == None or pntTm2 == None:
            if pntTm1 != None:
                if pntTm1.Distance(pntT)<1.e-6:
                    self.viewer.selectedPntT = self.viewer.selectedPntTm1
                    self.viewer.selectedPntTm1 = None
                    
                    return
            vn = self.aisGeomMan.CreateVertex(pntT.X(),pntT.Y(), pntT.Z())
            self.vList.append(vn)
            vn.Display(self.viewer)
        elif pntTm2 != None:
            
            startPnt = pntTm2
            centerPnt = pntTm1
            angle = self.setAngle
            
            edit_popup = AnglePopupDialog(self,angle)
            edit_popup.move(QCursor.pos())

            result = edit_popup.exec_()

            if result == QDialog.Accepted:
                angle = edit_popup.input_field.text()
                doubleAngle = float(angle)
                radius = startPnt.Distance(centerPnt)
                costheta = (startPnt.X()-centerPnt.X())/radius
                sintheta = (startPnt.Y()-centerPnt.Y())/radius
                theta = math.atan2(sintheta,costheta)
                theta = theta + math.radians(doubleAngle)
                endPnt = gp_Pnt(centerPnt.X()+radius*math.cos(theta),centerPnt.Y()+radius*math.sin(theta),0)
                vn = self.aisGeomMan.CreateVertex(endPnt.X(),endPnt.Y(), endPnt.Z())
                self.vList.append(vn)
                pns_popup = PositiveNegativeSelectDialog(self,doubleAngle)
                pns_popup.move(QCursor.pos())
                resultpns = pns_popup.exec_()
                counterclockwise = True
                
                
              
                if resultpns == QDialog.Accepted:
                    counterclockwise = False
                elif resultpns == QDialog.Rejected:
                    counterclockwise = True
                
                print("Start Pnt",startPnt.X(),startPnt.Y())
                print("Center Pnt",centerPnt.X(),centerPnt.Y())
                print("End Pnt",endPnt.X(),endPnt.Y())
                im2 = len(self.vList)-3
                im1 = len(self.vList)-2
                i = len(self.vList)-1
                en = self.aisGeomMan.CreateArcfromVertices(self.vList[im2],self.vList[i],self.vList[im1],counterclockwise)
                self.eList.append(en)
                en.Display(self.viewer) 
                self.viewer.selectedPntT = endPnt
                self.viewer.selectedPntTm1 = None
                self.viewer.selectedPntTm2 = None    
                self.GenerateFace()    
            pass
        self.viewer._display.Context.UpdateCurrentViewer()

    def GenerateBoxbyClickView(self):
        curPoint = self.viewer.selectedPntT
        prevPoint = self.viewer.selectedPntTm1
        if curPoint == None:
            return
        if prevPoint != None:
            if curPoint.Distance(prevPoint) < 1.e-6:
                return
        
        if len(self.vList) != 0:
            vnm1 = self.vList[len(self.vList)-1]
            if vnm1.pnt.Distance(curPoint) < 1.e-6:
                return
        
        vn = self.aisGeomMan.CreateVertex(curPoint.X(),curPoint.Y(), curPoint.Z())
        self.vList.append(vn)
        vn.Display(self.viewer)
        if len(self.vList) == 2:
            v1 = self.vList[0]
            v2 = self.vList[1]
            x1, y1 = v1.pnt.X(), v1.pnt.Y()
            x2, y2 = v2.pnt.X(), v2.pnt.Y()

            if x1 < x2:
                xMin = x1
                xMax = x2
            else:
                xMin = x2
                xMax = x1
            if y1 < y2:
                yMin = y1
                yMax = y2
            else:
                yMin = y2
                yMax = y1

            if yMin == yMax:
                yMin = 0.99999*yMax
            if xMin == xMax:
                xMin = 0.99999*xMax
            
            p1 = gp_Pnt(xMin,yMin,0.0)
            p2 = gp_Pnt(xMax,yMin,0.0)
            p3 = gp_Pnt(xMax,yMax,0.0)
            p4 = gp_Pnt(xMin,yMax,0.0)
            v1 = self.aisGeomMan.CreateVertex(p1.X(),p1.Y(),p1.Z())
            v2 = self.aisGeomMan.CreateVertex(p2.X(),p2.Y(),p2.Z())
            v3 = self.aisGeomMan.CreateVertex(p3.X(),p3.Y(),p3.Z())
            v4 = self.aisGeomMan.CreateVertex(p4.X(),p4.Y(),p4.Z())
            v1.Display(self.viewer)
            v2.Display(self.viewer)
            v3.Display(self.viewer)
            v4.Display(self.viewer)
            e1 = self.aisGeomMan.CreateLinefromVertices(v1,v2)
            e2 = self.aisGeomMan.CreateLinefromVertices(v2,v3)
            e3 = self.aisGeomMan.CreateLinefromVertices(v3,v4)
            e4 = self.aisGeomMan.CreateLinefromVertices(v4,v1)
            e1.Display(self.viewer)
            e2.Display(self.viewer)
            e3.Display(self.viewer)
            e4.Display(self.viewer)
            self.eList.append(e1)
            self.eList.append(e2)
            self.eList.append(e3)
            self.eList.append(e4)
            self.GenerateFacefromBox()
            
            if self.multiscaleOption["Activate"] == True:
                boxMinMaxBox = [xMin, yMin, xMax, yMax]
                self.multiscaleOption["BoundingBox"].append(boxMinMaxBox)
        

        pass

    def GenerateCirclebyClickView(self):
        curPoint = self.viewer.selectedPntT
        prevPoint = self.viewer.selectedPntTm1
        if curPoint == None:
            return
        if prevPoint != None:
            if curPoint.Distance(prevPoint) < 1.e-6:
                return
        if len(self.vList) != 0:
            vnm1 = self.vList[len(self.vList)-1]
            if vnm1.pnt.Distance(curPoint) < 1.e-6:
                return
        
        vn = self.aisGeomMan.CreateVertex(curPoint.X(),curPoint.Y(), curPoint.Z())
        self.vList.append(vn)
        vn.Display(self.viewer)
        if len(self.vList) == 2:

            radius = self.vList[0].pnt.Distance(self.vList[1].pnt)

            edit_popup = RadiusPopupDialog(self,radius)
            edit_popup.move(QCursor.pos())

            result = edit_popup.exec_()
            if result == QDialog.Accepted:
                radius = edit_popup.input_field.text()
                radius = float(radius)
                self.vList[1].pnt = gp_Pnt(self.vList[0].pnt.X()+radius,self.vList[0].pnt.Y(),self.vList[0].pnt.Z())
                    
                en = self.aisGeomMan.CreateCirclefromVertices(self.vList[0],self.vList[1])
                self.eList.append(en)
                self.GenerateFacefromCircle()            
            else:
                self.viewer.selectedPntT = None
                self.viewer.selectedPntTm1 = None   
                self.vList = []
            pass

        self.viewer._display.Context.UpdateCurrentViewer()

    def SetOrigin(self):
        print("Set Origin")
        #self.viewer._display.Pan(0,0)
        self.viewer._display.ResetView()
        self.viewer.SetTopView()
     #   self.viewer._display.ZoomArea(-100,-100,100,100)
        self.viewer._display.ZoomFactor(0.5)
        self.viewer.UpdateGrid()
        self.viewer._display.Context.UpdateCurrentViewer()
       # self.viewer._display.FitAll()
       #
        pass
    def checkbox_state_changed(self, state):
        if state == 2:  # Qt.Checked
            print("Checkbox is checked")
            self.viewer.gridon = True
        else:
            print("Checkbox is unchecked")
            self.viewer.gridon = False
    
    def InitUI(self):
        
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        geometry_menu = menu_bar.addMenu("&Geometry")
        view_menu = menu_bar.addMenu("&View")
        
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.New)
        file_menu.addAction(new_action)

        import_sub_menu = file_menu.addMenu("Import")
        import_image_action = QAction("Image", self)
        import_odb_menu = import_sub_menu.addMenu("ODB")
        import_sub_menu.addAction(import_image_action)
        import_image_action.triggered.connect(self.ImportImage)

        import_odb_external_geometry_action = QAction("External Geometry", self)
        import_odb_menu.addAction(import_odb_external_geometry_action)
        import_odb_external_geometry_action.triggered.connect(self.ImportODBExternalGeometry)
        

        export_sub_menu = file_menu.addMenu("Export")
        export_multiscale_model_action = QAction("Multiscale Model", self)
        export_package_automation_action = QAction("Package Automation", self)
        export_sub_menu.addAction(export_multiscale_model_action)
        export_sub_menu.addAction(export_package_automation_action) 
        export_multiscale_model_action.triggered.connect(self.ExportMultiscaleModel)
        export_package_automation_action.triggered.connect(self.ExportPackageAutomation)   
         
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        data_view_action = QAction("Data View", self)
        data_view_action.triggered.connect(self.OpenDataViewTreeWidget)
        view_menu.addAction(data_view_action)

    
    def SetParent(self, parent):
        self.Parent = parent
    
    def close(self):        
        super().close()

    def New(self):
        print("New")        
        
        parent_item = self.model.invisibleRootItem()
        # clear all layers from parent_item
        for row in range(parent_item.rowCount()):
           
            parent_item.removeRow(0)    
            
        
        self.dataViewTree.reset()
        self.maxLayer = 0       
        self.aisGeomMan = KooAISGeometryManager(self, self.viewer)
        self.add_model("Layer 1", self.aisGeomMan)        
        self.maxLayer = 1
        self.ResetView()


    def ResetView(self):
        self.viewer._display.EraseAll()
        self.viewer._display.Context.UpdateCurrentViewer()
        self.viewer._display.FitAll()
        self.viewer._display.Context.UpdateCurrentViewer()
        self.viewer._display.ResetView()
        self.viewer._display.Context.UpdateCurrentViewer()
        self.SetOrigin()

    def ImportODBExternalGeometry(self):
        # import odb file (*.zip)
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getOpenFileName(
            self, "Import ODB External Geometry", "", "Zip Files (*.zip)"
            )
        if file_path:
            self.ImportODBExternalGeometryFile(file_path)
    
    def ImportODBExternalGeometryFile(self, file_path):
        from KooODBCADManager.Layer import PrintedCircuitBoard
        
        pcb = PrintedCircuitBoard()
        xPatternList, yPatternList, _, _, nameList = pcb.ImportODBZipExternalGeometry(file_path)
        vMat = []        
        for i in range(len(xPatternList)):
            vList = []
            for j in range(len(xPatternList[i])):
                x = xPatternList[i][j]
                y = yPatternList[i][j]
                vList.append(self.aisGeomMan.CreateVertex(x, y, 0.0))
            vMat.append(vList)
        
        for i in range(len(vMat)):
            vList = vMat[i]
            for j in range(len(vList)-1):
                v1 = vList[j]
                v2 = vList[j+1]
                en = self.aisGeomMan.CreateLinefromVertices(v1, v2)        
                en.Display(self.viewer)
                
        self.multiscaleOption["ODBFileName"] = file_path
        self.multiscaleOption["Activate"] = True
        self.multiscaleOption["NameList"] = nameList
        self.viewer._display.Context.UpdateCurrentViewer()
         
    def ImportImage(self):
        
        parent_item = self.model.invisibleRootItem()
        layerNameList = [] 
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            layerNameList.append(item.text())
        
        # if it is shown, close it
        if hasattr(self, 'importImageDialog'):
            self.importImageDialog.close()
        self.importImageDialog.SetNumLayers(layerNameList)
        self.importImageDialog.show()
        pass

    def ImportTextureBox(self, layerNameList, filePathList, XSizeList, YSizeList):
        parent_item = self.model.invisibleRootItem()
        if len(layerNameList) > parent_item.rowCount():
            for i in range(len(layerNameList)-parent_item.rowCount()):
                self.AddLayer()
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            if item.text() in layerNameList:
                index = layerNameList.index(item.text())
                filePath = filePathList[index]
                XSize = XSizeList[index]
                YSize = YSizeList[index]
                ZSize = 10.0
                xLoc = -XSize/2.0
                yLoc = -YSize/2.0
                zLoc = -100.0
                self.aisGeomMan : KooAISGeometryManager = item.aisGeomMan
                curTexture : KooAISGeomTextureBox = self.aisGeomMan.CreateTextureBox(filePath, xLoc, yLoc, zLoc, XSize, YSize, ZSize)
                if curTexture != None:
                    curTexture.Display(self.viewer)
        
        # update viewer
        self.viewer._display.Context.UpdateCurrentViewer()
        pass

    def ExportMultiscaleModel(self):
        if self.multiscaleOption["Activate"] == False:
            return
        
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getSaveFileName(
            self, "Export Multiscale Model", "", "Text Files (*.txt)"
            )
        if file_path:
            
            from KooLayerDialog import LayerInputDialog
            layerDialog = LayerInputDialog(self, self.multiscaleOption["NameList"])
            layerDialog.SetFilePath(file_path)
            if layerDialog.exec_():
                pass
            
            
            
    def ExportMultiscaleModelFile(self, data):
        file_path = data["filepath"]
        thicknessList = data["thicknesslist"]
        smthickness = data["smThickness"]
        spthickness = data["spThickness"]
        if self.multiscaleOption["Activate"] == False:
            return
        boxList = self.multiscaleOption["BoundingBox"]
        file_path = file_path.replace(".txt","")
        for i in range(len(boxList)):
            curFilePath = file_path + "_" + str(i+1) + ".txt"
            with open(curFilePath, 'w') as file:
                file.write("*ODB\n")
                file.write("ODBFile,")
                file.write(self.multiscaleOption["ODBFileName"] + "\n")
                file.write("ZLocation,0.0000\n")
                file.write("Thickness")
                for j in range(len(thicknessList)):
                    file.write("," + str(thicknessList[j])) 
                file.write("\n")
                if smthickness != 0.0:
                    file.write("ThicknessSolderMask," + str(smthickness) + "\n")
                if spthickness != 0.0:
                    file.write("ThicknessSolderPaste," + str(spthickness) + "\n")                
                file.write("BoundaryBox")
                for j in range(len(boxList[i])):
                    file.write("," + str(0.001*boxList[i][j]))
                file.write("\n")
                file.write("MinimumSize,0.0\n")
                file.write("DetailPAD,ALL\n")
                file.write("ExportPackage,True,PackageMesh\n")
                file.write("*End")
                
                

    def ExportPackageAutomation(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getSaveFileName(
            self, "Export Package Automation", "", "Text Files (*.txt)"
            )
        if file_path:
            self.ExportPackageAutomationFile(file_path)
        
 
    def ExportPackageAutomationFile(self, file_path):
        with open(file_path, 'w') as file: 
            parent_item = self.model.invisibleRootItem()
            j = 0
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)

                file.write("*Layer," + item.text() + "\n")
                if j == 0:
                    file.write("Location,0.0,0.0,0.0\n")
                else:
                    file.write("Location,0.0,0.0\n")
                
                file.write("Thickness,10.0\n")
                
                aisGeomMan : KooAISGeometryManager = item.aisGeomMan
                faces = aisGeomMan.faces
                for i in faces:
                    face = faces[i]
                    if type(face) == KooAISGeomFace:                        
                        if len(face.wire.edges) == 1:
                            face.wire.edges[0].WriteODB(file)
                        else:
                            file.write("Part,Polynomial\n")                    
                            face.WriteODB(file)
                    if type(face) == KooAISGeomCutFace:
                        numCut = len(face.wires)-1
                        file.write("Part,PolynomialCut,Solid," + str(numCut) + "\n")
                        face.WriteODB(file)
                j += 1



    def exit(self):
        super().exit()

    def OpenDataViewTreeWidget(self):

        self.dockWidgetDataView = QDockWidget("Data View",self)
        self.dockWidgetDataView.setWidget(self.dataViewTree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidgetDataView)
    
    def add_model(self, objName, aisMan : KooAISGeometryManager):
        parent_item = self.model.invisibleRootItem()

        object_item = QKooAISGeometryManagerItem(objName,self.maxLayer, aisMan)
        parent_item.appendRow(object_item)
        
    def add_models(self, aisManList):
        self.maxLayer = 0        
        for aisMan in aisManList:            
            name = "Layer " + str(self.maxLayer+1)
            self.add_model(name, aisMan)
            self.maxLayer = self.maxLayer + 1
        
        self.SetAISGeometryManager(aisManList[0])

    def on_selection_changed(self, selected, deselected):
        print("Selection Changed")
        parent_item = self.model.invisibleRootItem()
        self.ResetView()
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            if item.index() in selected.indexes():
                print("Selected Item")
                print(item.text())                
                curItem : QKooAISGeometryManagerItem = item
                self.curItem = curItem
                self.aisGeomMan = curItem.aisGeomMan                
                self.aisGeomMan.SetTransparencyAll(0.0)
                self.aisGeomMan.Display()
            else:
                curItem : QKooAISGeometryManagerItem = item

                curItem.aisGeomMan.SetTransparencyAll(0.5)
                curItem.aisGeomMan.Display()    
                
        if self.CutOperatorWidget is not None and self.CutOperatorWidget.isVisible():
            self.dockWidgetCutOperWidget.hide()
            self.CutOperatorWidget.forceClose()
        self.viewer._display.Context.UpdateCurrentViewer()
        print(deselected)
        pass

    def show_context_menu_tree(self, position):
        selected_indexes = self.dataViewTree.selectedIndexes()
        if selected_indexes:
            print("Selected Indexes")
            print(selected_indexes)
            menu = QMenu()
            add_action = QAction('Add',self)
            clear_action = QAction('Clear',self)
            remove_action = QAction('Remove',self)
            add_action.triggered.connect(self.AddLayer)
            clear_action.triggered.connect(self.ClearLayer)
            remove_action.triggered.connect(self.RemoveLayer)
            menu.addAction(add_action)
            menu.addAction(clear_action)
            menu.addAction(remove_action)
            self.selectedIndexes = selected_indexes
            menu.exec(self.dataViewTree.viewport().mapToGlobal(position))

    def AddLayer(self):
        print("Add Layer")
        aisGeomMan = KooAISGeometryManager(self, self.viewer)        
        self.add_model("Layer " + str(self.maxLayer+1), aisGeomMan)
        self.maxLayer = self.maxLayer + 1
    
    def ClearLayer(self):
        print("Clear Layer")
        parent_item = self.model.invisibleRootItem()
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            if item.index() in self.selectedIndexes:
                print("Selected Item")
                print(item.text())                
                self.aisGeomMan : KooAISGeometryManager = item.aisGeomMan
                self.aisGeomMan.RemoveAll()
                self.ResetView()
                break
        

    def RemoveLayer(self):
        print("Remove Layer")
        parent_item = self.model.invisibleRootItem()
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            if item.index() in self.selectedIndexes:
                print("Selected Item")
                print(item.text())                

                parent_item.removeRow(row)
                self.ResetView()
                # select first item
                index = self.model.index(0, 0)
                self.dataViewTree.selectionModel().select(index, QItemSelectionModel.Select)
                self.on_selection_changed(self.dataViewTree.selectionModel().selection(),self.dataViewTree.selectionModel().selection())
                break


    # when program is terminated
    def closeEvent(self, event):
        faces =  self.aisGeomMan.faces
        print("KooCADStackModellingWindow is deleted")
        if self.Parent is None:
            print("Face Lists")
            for i in faces:                
                print(faces[i].id)
        if self.Parent is not None:
            
            self.Parent.ais_geometry_manager_list = [] 
            for row in range(self.model.rowCount()):
                ais_geom = self.model.item(row)
                ais_geom_man = ais_geom.aisGeomMan
                self.Parent.ais_geometry_manager_list.append(ais_geom_man)
            
            pass
            #self.Parent.UpdateSketch(faces)
        pass
        
    
    



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KooCADStackModellingWindow()
    window.show()
    #window3 = KooCADStackModellingWindow()
    #window3.show()
    sys.exit(app.exec_())
