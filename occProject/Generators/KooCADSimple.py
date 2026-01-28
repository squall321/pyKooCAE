import os
import sys
getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
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
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox
from PyQt5.QtGui import QMouseEvent

from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.gp import gp_Pnt
from OCC.Core.AIS import AIS_Point, AIS_Shape, AIS_Selection
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCC.Core.Aspect import Aspect_TOM_STAR
from OCC.Core.Quantity import Quantity_NOC_WHITE, Quantity_TOC_RGB
from OCC.Core.Prs3d import Prs3d_PointAspect
from OCC.Core.Aspect import Aspect_InteriorStyle
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCC.Core.Graphic3d import Graphic3d_NOM_CHROME
from OCC.Core.Graphic3d import Graphic3d_TMF_2d

from OCC.Core.Quantity import Quantity_Color
from KooCAEManager.KooCoordinate import KooGridPlane
from KooPolyLineGeneratorfromCellWidget import KooPolyLineGeneratorfromCellWidget
from KooBooleanOperatorWidget import KooBooleanOperatorWidget
from KooCAEManager.KooAISGeometryManager import KooAISGeometryManager

class KooPlaneModelViewer(qtViewer3d):
    
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parent = parent
        self.selectedPntTm2 = None
        self.selectedPntTm1 = None
        self.selectedPntT = None
        self.messageShape = None
        self.gridon = False
        self.gridPlane = KooGridPlane()
        self.gridPlane.Display(self)
        self.gridPlane.RemoveFromView(self)
        self.gridPlane.Display(self)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:               
            print("Left Button Pressed")
            return
        else:
            return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event : QMouseEvent):
        xLoc, yLoc = self._display.View.Convert(event.pos().x(), event.pos().y())
        xPos,yPos,zPos = self._display.View.At()
        xLoc = xLoc + xPos 
        yLoc = yLoc + yPos
        
        xLoc, yLoc = self.GetRoundPoint(xLoc,yLoc)
        if event.button() == QtCore.Qt.LeftButton:
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
            if event.type() == QMouseEvent.MouseButtonDblClick:
                self.selectedPntT = None
                self.selectedPntTm1 = None
                self.selectedPntTm2 = None
            else:
                self.selectedPntT = self.selectedPntTm1
                self.selectedPntTm1 = self.selectedPntTm2
                self.selectedPntTm2 = None 
            if self.parent != None: 
                self.parent.mouseReleaseEvent(event)
        else:
            return super().mouseReleaseEvent(event)
    def mouseDoubleClickEvent(self, event):
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
        
    def mouseMoveEvent(self, event):
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

    def wheelEvent(self, event):
        
        super().wheelEvent(event)
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


    

class KooCADPlaneModellingWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(KooCADPlaneModellingWindow, self).__init__(*args, **kwargs)
        #self.vnm2 = None
        #self.vnm1 = None
        #self.vn = None
        self.vList = [] #Vertex List
        self.eList = [] #Edge List
        self.PolyLineGeneratorfromCellWidget = None
        self.BooleanOperatorWidget = None
        self.setWindowTitle("KooCAD Plane Modeller")
        self.resize(800, 600)
        self.InitUI()
        self.viewer = KooPlaneModelViewer(self)
        self.viewer.SetBackgroundColor()
        #self.viewer.SetTopView()
        self.SetOrigin()
       # self.setCentralWidget(self.viewer)
        

        self.gridOnOff = False


        layout = QVBoxLayout()

        hLayoutTop = QHBoxLayout()
        self.OpenPolyLineGeneratorfromCellWidgetButton = QPushButton("PolyLine Generator")
        self.OpenBooleanOperatorButtonWidget = QPushButton("Boolean Operator")
        self.OpenPolyLineGeneratorfromCellWidgetButton.clicked.connect(self.OpenPolyLineGeneratorfromCellWidget)
        self.OpenBooleanOperatorButtonWidget.clicked.connect(self.OpenBooleanOperatorWidget)
        hLayoutTop.addWidget(self.OpenPolyLineGeneratorfromCellWidgetButton)
        hLayoutTop.addWidget(self.OpenBooleanOperatorButtonWidget)
        
        self.GroupBoxSelectMode = QGroupBox("Select Mode")
        self.GroupSelectModeLayout = QHBoxLayout()
        self.SelectVertexButton = QRadioButton("1 : Vertex")
        self.SelectEdgeButton = QRadioButton("2 : Edge")
        self.SelectFaceButton = QRadioButton("3 : Face")
        self.GroupSelectModeLayout.addWidget(self.SelectVertexButton)
        self.GroupSelectModeLayout.addWidget(self.SelectEdgeButton)
        self.GroupSelectModeLayout.addWidget(self.SelectFaceButton)
        self.GroupBoxSelectMode.setLayout(self.GroupSelectModeLayout)
    
     
        
        self.SelectVertexButton.setChecked(True)
        self.GroupBoxSelectMode.setMaximumHeight(50)
        layout.addLayout(hLayoutTop)
        layout.addWidget(self.GroupBoxSelectMode)
        layout.addWidget(self.viewer)
    
        
        hLayoutBottom = QHBoxLayout()
        self.checkbox = QCheckBox("Grid On")
        label = QLabel("Grid Size : ")
        self.gridsizeEdit = QLineEdit()
        self.gridsizeEdit.setText("10")
        
        self.SetOriginButton = QPushButton("Set Origin")
        self.checkbox.stateChanged.connect(self.checkbox_state_changed)
        self.SetOriginButton.clicked.connect(self.SetOrigin)
        
        hLayoutBottom.addWidget(self.checkbox)
        hLayoutBottom.addWidget(label)
        hLayoutBottom.addWidget(self.gridsizeEdit)
        hLayoutBottom.addWidget(self.SetOriginButton)
        layout.addLayout(hLayoutBottom)
        self.setLayout(layout)
       
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        ### Data Initialization 
        self.aisGeomMan = KooAISGeometryManager(self,self.viewer)

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
        else:
            self.PolyLineGeneratorfromCellWidget.show()
        self.dockWidget = QDockWidget("PolyLine Generator",self)
        self.dockWidget.setWidget(self.PolyLineGeneratorfromCellWidget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)

    def OpenBooleanOperatorWidget(self):
        if self.BooleanOperatorWidget == None:
            self.BooleanOperatorWidget = KooBooleanOperatorWidget(self.On_BooleanOperator_Update,self)
        else:
            self.BooleanOperatorWidget.show()
        
        self.dockWidget = QDockWidget("Boolean Operator",self)
        self.dockWidget.setWidget(self.BooleanOperatorWidget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)

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
                    edges = [] 
                    for value in edgeList.values():
                        edges.append(value)
                    print("Number of Edges",len(edges))
                    wire = self.aisGeomMan.FindWirefromEdges(edges)
                    face = self.aisGeomMan.FindFacefromWire(wire)
                    face.Display(self.viewer)


                    pass
        
        self.viewer._display.Context.UpdateCurrentViewer()       

        pass

    def On_BooleanOperator_Update(self):
        pass 

    def mouseReleaseEvent(self, event : QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            print("Left Button in main Window")
            self.GeneratebyClickView()
            if self.PolyLineGeneratorfromCellWidget != None:
                if self.PolyLineGeneratorfromCellWidget.isOpened:
                    pass
            return
        elif event.button() == QtCore.Qt.MiddleButton:
            pass
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
                
                if len(self.eList)>0:
                    print("Erase Edge")
                    #print(self.aisGeomMan.edges)
                    self.aisGeomMan.RemoveEdge(self.eList[len(self.eList)-1])
                    self.eList[len(self.eList)-1].Erase(self.viewer)
                    self.eList.pop()
                if len(self.vList)>0:
                    curVPos = len(self.vList)-1
                    vn = self.vList[curVPos]
                    self.aisGeomMan.RemoveVertex(vn)
                    vn.Erase(self.viewer)
                    self.vList.pop()
                #self.vn = self.vnm1
                #self.vnm1 = self.vnm2
                #self.vnm2 = None

            self.viewer._display.Context.UpdateCurrentViewer()       
            return

        return super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
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
        
        
    def GeneratebyClickView(self):
        curPoint = self.viewer.selectedPntT
        prevPoint = self.viewer.selectedPntTm1
        if curPoint == None:
            return
        if prevPoint == None:
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
    
        v1 = self.vList[0]
        if len(self.vList)>=2:
            if vn.pnt.Distance(v1.pnt) < 1.e-6:
                print("Generate Polygon")
                wire = self.aisGeomMan.CreateWirefromEdges(self.eList)
                face = self.aisGeomMan.CreateFacefromWire(wire)
                wire.Display(self.viewer)
                face.Display(self.viewer)
                self.vList = [] 
                self.eList = [] 
                #self.aisGeomMan.CreatePolygonfromVertices(self.vList)

        #self.aisGeomMan.Print()
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
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        geometry_menu = menu_bar.addMenu("&Geometry")

        file_menu.addAction(exit_action)

    
    def close(self):        
        super().close()
        
    



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KooCADPlaneModellingWindow()
    window.show()
    sys.exit(app.exec_())
