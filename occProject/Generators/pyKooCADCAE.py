import sys
import threading
import os

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
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QMenuBar, QAction, QFileDialog, QTreeView, QMessageBox
from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QAbstractItemView, qApp, QCheckBox, QDockWidget
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox, QShortcut
from PyQt5.QtGui import QMouseEvent, QKeySequence, QCursor, QWheelEvent, QStandardItemModel, QStandardItem
from PyQt5.QtCore import QItemSelectionModel, QModelIndex


from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

from OCC.Display.qtDisplay import qtViewer3d
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Circ, gp_Trsf
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

from OCC.Core.BRep import BRep_Tool
import OCC.Core.BRepAdaptor as BRepAdaptor
import OCC.Core.TopExp as TopExp
import OCC.Core.BRepGProp as BRepGProp


from KooPolyLineGeneratorfromCellWidget import KooPolyLineGeneratorfromCellWidget
from KooBooleanOperatorWidget import KooBooleanOperatorWidget
from KooCAEManager.KooCoordinate import KooGridPlane, KooViewCube, KooAxis3D
from KooCAEManager.KooAISGeometryManager import KooAISGeometryManager
from KooCAEManager.KooAISGeometry import (
    KooAISManipulator,
    KooAISGeomFace,
    KooAISGeomSolid
)

from KooCAEManager.KooAISBoundaryManager import KooAISBoundaryManager
from KooCAEManager.KooAISBoundary import (
    KooAISBoundaryDisplacement,
)

from KooCAEManager.KooAISPreviewManager import KooAISPreviewManager

from KooPopupDialog import AnglePopupDialog, PositiveNegativeSelectDialog

from KooCADCAEView import KooCADCAEView
from KooPropertyWidget import (
    KooPropertyWidget,
    KooFaceGeometryWidget,
    KooSolidGeometryWidget,
    KooManipulatorWidget
)

from KooCAEManager.KooCAEModel import (
    KooCAEModel,
    QKooCAEItem,
    QKooGeometryItem,
    QKooBoundaryItem,
    QKooManipulatorItem
)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100,100,1280,720)
        
        self.model = None
        self.tree_view = None
        self.property_manipulator_widget : KooManipulatorWidget = None
        self.property_face_widget : KooFaceGeometryWidget = None
        self.property_solid_widget : KooSolidGeometryWidget = None
        self.focusedData = None
        self.data = {} 
        self.fixedName = {}

        # Create a menu bar
        menu_bar = self.menuBar()

        # Create a all menu
        self.file_menu = menu_bar.addMenu('File')
        geometry_menu = menu_bar.addMenu('Geometry')
        mesh_menu = menu_bar.addMenu('Mesh')
        boundary_menu = menu_bar.addMenu('Boundary')
        solver_menu = menu_bar.addMenu('Solver')
        post_menu = menu_bar.addMenu('Post')
        view_menu = menu_bar.addMenu('View')



        ################ File Menu ################
        # Create actions for File menu
        new_action = QAction('New', self)
        exit_action = QAction('Exit', self)

        # Add actions to File menu
        self.file_menu.addAction(new_action)
        open_sub_menu = self.file_menu.addMenu('Open')
        save_sub_menu = self.file_menu.addMenu('Save')
        self.file_menu.addAction(exit_action)

        open_iges_action = QAction('IGES', self)
        open_step_action = QAction('STEP', self)
        open_sub_menu.addAction(open_iges_action)
        open_sub_menu.addAction(open_step_action)

        save_iges_action = QAction('IGES', self)
        save_step_action = QAction('STEP', self)
        save_sub_menu.addAction(save_iges_action)
        save_sub_menu.addAction(save_step_action)
    
        # Connect the New action to a function
        open_iges_action.triggered.connect(self.open_iges_file)
        open_step_action.triggered.connect(self.open_step_file)
        save_iges_action.triggered.connect(self.save_iges_file)
        save_step_action.triggered.connect(self.save_step_file)
        # Connect the Exit action to a function

        exit_action.triggered.connect(self.close)

        ################ Geometry Menu ################

        ################ Mesh Menu ################

        ################ Boundary Menu ################

        ################ Solver Menu ################

        ################ Post Menu ################

        ################ View Menu ################
        # Create actions for View menu
        data_View_action = QAction('Data View', self)
        # Add actions to View menu
        view_menu.addAction(data_View_action)
        # Connect the Data View action to a function
        data_View_action.triggered.connect(self.OpenDataViewTreeWidget)

        # 0 All, 1 Vertex, 2 Edge, 3 Face, 4 Solid
        self.popupSelectMode = 0
        self .setWindowTitle('Koo CAD/CAE')


        ################ Define Variables of Widgets ################
        self.model = None 



        ########## MainLayout

        layout = QVBoxLayout()
        self.viewer = KooCADCAEView(self)
        self.view_cube = KooViewCube()
        self.view_cube.Display(self.viewer)
        layout.addWidget(self.viewer)        

        layoutBottomOption = QHBoxLayout()
        # left alignment of QHBoxLayout
        layoutBottomOption.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.SetSelectModeNoneButton = QPushButton("None")
        self.SetSelectModeVertexButton = QPushButton("Vertex")
        self.SetSelectModeEdgeButton = QPushButton("Edge")
        self.SetSelectModeFaceButton = QPushButton("Face")
        self.SetSelectModeSolidButton = QPushButton("Solid")
        # Edit which is including texts 
        self.InputFolderPathEditButton = QLineEdit()

        self.SetInputFolderPathButton = QPushButton("...")
        
        self.SetSelectModeNoneButton.setFixedWidth(60)
        self.SetSelectModeVertexButton.setFixedWidth(60)
        self.SetSelectModeEdgeButton.setFixedWidth(60)
        self.SetSelectModeFaceButton.setFixedWidth(60)
        self.SetSelectModeSolidButton.setFixedWidth(60)
        self.InputFolderPathEditButton.setFixedWidth(400)
        self.SetInputFolderPathButton.setFixedWidth(30)
        
        self.SetSelectModeNoneButton.clicked.connect(self.SetSelectModeNone)
        self.SetSelectModeVertexButton.clicked.connect(self.SetSelectModeVertex)
        self.SetSelectModeEdgeButton.clicked.connect(self.SetSelectModeEdge)
        self.SetSelectModeFaceButton.clicked.connect(self.SetSelectModeFace)
        self.SetSelectModeSolidButton.clicked.connect(self.SetSelectModeSolid)
        self.SetInputFolderPathButton.clicked.connect(self.SetInputFolder)
        #self.InputFilePathEditButton.returnPressed.connect(self.SetInputFile)
        layoutBottomOption.addWidget(self.SetSelectModeNoneButton)
        layoutBottomOption.addWidget(self.SetSelectModeVertexButton)
        layoutBottomOption.addWidget(self.SetSelectModeEdgeButton)
        layoutBottomOption.addWidget(self.SetSelectModeFaceButton)
        layoutBottomOption.addWidget(self.SetSelectModeSolidButton)
        layoutBottomOption.addWidget(self.InputFolderPathEditButton)
        layoutBottomOption.addWidget(self.SetInputFolderPathButton)
        layout.addLayout(layoutBottomOption)
        self.setLayout(layout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.viewer.SetBackgroundColor()
        self.globalAxis = KooAxis3D()
        self.globalAxis.DisplayAxis(self.viewer,True)

        shortcutOptionDelete = QShortcut(QKeySequence(Qt.Key_Delete), self)
        shortcutOptionDelete.activated.connect(self.remove_geometry_selected)


        self.OpenDataViewTreeWidget()

        self.Load_Tutorial()

    def remove_geometry_selected(self):
        print("Remove Geometry")
        for shape in self.viewer._display.selected_shapes:            
            if type(shape) == TopoDS_Face:
                for i in self.data:
                    faceItems = self.data[i].faceItem
                    aisMan :KooAISGeometryManager = self.data[i].data.ais_geometry_manager
                    aisMan.PrintStatistics()
                    face = aisMan.FindFace(shape)
                    if face is None:
                        continue
                    if faceItems.hasChildren():
                        for row in range(faceItems.rowCount()):
                            faceItem = faceItems.child(row)
                            if faceItem.id == face.id:
                                print("Remove Face ",face.id)
                                aisMan.RemoveFacebyID(faceItem.id)
                                if faceItem.hasChildren():
                                    meshItem = faceItem.meshItem 
                                    if meshItem is not None:
                                        faceItem.EraseMeshItem()
                                self.data[i].faceItem.removeRow(faceItem.row())
                                
                                break
            elif type(shape) == TopoDS_Solid:
                for i in self.data:
                    solidItems = self.data[i].solidItem
                    aisMan = self.data[i].data.ais_geometry_manager
                    aisMan.PrintStatistics()
                    solid = aisMan.FindSolid(shape)                    
                    if solid is None:
                        continue
                    if solidItems.hasChildren():
                        for row in range(solidItems.rowCount()):
                            solidItem = solidItems.child(row)
                            if solidItem.id == solid.id:
                                print("Remove Solid ",solid.id)
                                aisMan.RemoveSolidbyID(solidItem.id)
                                if solidItem.hasChildren():
                                    meshItem = solidItem.meshItem
                                    if meshItem is not None:
                                        solidItem.EraseMeshItem()
                                self.data[i].solidItem.removeRow(solidItem.row())
                                
                                break 
                                
        self.viewer._display.Context.UpdateCurrentViewer()                            

                    

    def SetSelectModeNone(self):
         
        self.viewer._display.SetSelectionMode(None)
        self.view_cube.Hide(self.viewer)
        self.view_cube.Display(self.viewer)

    def SetSelectModeVertex(self):
        self.viewer._display.SetSelectionModeVertex()

    def SetSelectModeEdge(self):
        self.viewer._display.SetSelectionModeEdge()

    def SetSelectModeFace(self):
        self.viewer._display.SetSelectionModeFace()

    def SetSelectModeSolid(self):
        self.viewer._display.SetSelectionMode(TopAbs_SOLID)

    def SetInputFolderbyString(self, folder_path):
        self.InputFolderPathEditButton.setText(folder_path)

    def SetInputFolder(self):
        file_Dialog = QFileDialog(self)
        # get open folder name 
        folder_path = file_Dialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            print("Selected folder", folder_path)
            self.SetInputFolderbyString(folder_path)            
            self.ShowMessageforExporttoAlltoDirectory()
            self.InitializeDataViewTreeWidget()

    def open_iges_file(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getOpenFileName(
            self,'Open IGES Files', '', 'IGES Files (*.igs *.iges)'
        ) 
        if file_path:
            print("Selected file", file_path)
        
    def open_step_file(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getOpenFileName(
            self,'Open STEP Files', '', 'STEP Files (*.stp *.step)'
        )
        if file_path:
            print("Selected file", file_path)
        
    def save_iges_file(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getSaveFileName(
            self,'Save IGES Files', '', 'IGES Files (*.igs *.iges)'
        )
        if file_path:
            print("Selected file", file_path)

    def save_step_file(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getSaveFileName(
            self,'Save STEP Files', '', 'STEP Files (*.stp *.step)'
        )
        if file_path:
            print("Selected file", file_path)

    def InitializeDataViewTreeWidget(self):
        self.removeDockWidget(self.dockWidget)
        self.viewer._display.Context.RemoveAll(True)

        self.view_cube = KooViewCube()
        self.view_cube.Display(self.viewer)
        self.model = None
        self.tree_view = None
        self.property_manipulator_widget = None
        self.property_face_widget = None
        self.property_solid_widget = None
        self.focusedData = None
        self.data = {} 
        self.fixedName = {}
        self.OpenDataViewTreeWidget()

    def OpenDataViewTreeWidget(self):

        if self.model == None:
            # Create the tree model
            self.model = QStandardItemModel()
            self.model.setHorizontalHeaderLabels(['Objects'])
            self.model.dataChanged.connect(self.on_data_tree_changed)

            # Create the tree view
            self.tree_view = QTreeView()
            self.tree_view.setModel(self.model)
            self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tree_view.customContextMenuRequested.connect(self.show_context_menu_tree)

            # Set the selection mode to single selection 
            self.selection_model = self.tree_view.selectionModel()
            self.selection_model.selectionChanged.connect(self.on_tree_selection_changed)

            # Create some sample data 
            ########################################
            '''
            self.add_object('Point', 'Point A')
            self.add_object('Point', 'Point B')
            self.add_object('Edge', 'Edge 1')
            self.add_object('Edge', 'Edge 2')
            self.add_object('Face', 'Face 1')
            self.add_object('Face', 'Face 2')
            '''
        self.dockWidget = QDockWidget('Data View', self)
        self.dockWidget.setWidget(self.tree_view)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockWidget)


    def add_object(self, obj_type, obj_name):
        parent_item = self.model.invisibleRootItem()

        # Find the parent item based on object type
        for row in range(parent_item.rowCount()):
            if parent_item.child(row, 0).text() == obj_type:
                parent_item = parent_item.child(row)
                break
        else:
            # If the parent item doesn't exist, create it
            parent_item = QStandardItem(obj_type)
            self.model.appendRow(parent_item)

        # Add the object as a child item
        object_item = QStandardItem(obj_name)
        parent_item.appendRow(object_item)
        #object_item.index()
        #object_item.appendColumn([QStandardItem('1'), QStandardItem('2')])


    def on_tree_selection_changed(self, selected, deselected):
        # Get the selected item's index 
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            print('Selected index:',index)
            item = self.model.itemFromIndex(index)
            print('Selected item:', item.text())
            
            if type(item) == QKooGeometryItem:                
                geom = item.GetGeometry()
                self.viewer._display.selected_shapes.clear()
                if type(geom) == KooAISGeomFace:
                    self.viewer._display.selected_shapes.append(geom.face)
                    geom.aisShape[0].SetHilightMode(1)
                    self.viewer._display.Context.SetSelected(geom.aisShape[0],True)
                if type(geom) == KooAISGeomSolid:    
                    self.viewer._display.selected_shapes.append(geom.solid)
                    #geom.aisShape[0].SetSelected(True)
                    geom.aisShape[0].SetHilightMode(1)
                    self.viewer._display.Context.SetSelected(geom.aisShape[0],True)
                    
                    
                self.viewer._display.Context.UpdateCurrentViewer()
            elif type(item) == QKooBoundaryItem:
                boundary = item.GetBoundary()
                self.viewer._display.selected_shapes.clear()
                if type(boundary) == KooAISBoundaryDisplacement:
                    for shape in boundary.shapeList:
                        self.viewer._display.selected_shapes.append(shape)
                    for aisshape in boundary.aisShape:
                        aisshape[0].SetHilightMode(1)
                        self.viewer._display.Context.SetSelected(aisshape[0],True)
                self.viewer._display.Context.UpdateCurrentViewer()
                # select in the view 
            elif type(item) == QKooManipulatorItem:
                
                if self.property_manipulator_widget != None:    

                    #self.property_manipulator_widget.close()
                    #print("set manipulator")
                    #self.CreatePropertyManipulator()
                    self.property_manipulator_widget.SetManipulator(item)
                    #self.OpenPropertyManipulator()

                
                '''
                ## Find Manipulator
                curManipulator = None
                curIndex = None
                for index in self.data:
                    print("check indexes")
                    print(self.data[index].manipulatorItem.index(), index)
                   
                    if self.data[index].manipulatorItem.index() == index:
                        curManipulator = self.data[index].manipulatorItem 
                        curIndex = index
                #print(curManipulator)
                if curIndex:
                    if self.property_manipulator_widget != None:
                        self.property_manipulator_widget.SetManipulator(item)
                '''
            
          
                


    def on_data_tree_changed(self):
        print('Object name changed to {x}'.format(x=self.model.itemFromIndex(self.tree_view.currentIndex()).text()))
        # Find the parent item based on object type
        isFixed = False
        for index, name in self.fixedName.items():
            print(index, self.tree_view.currentIndex())
            if index == self.tree_view.currentIndex():
                self.model.itemFromIndex(index).setText(name)
                isFixed = True
                break
        if isFixed == False:
            if self.model.itemFromIndex(self.tree_view.currentIndex()).text() == "Model":
                i = len(self.data)
                self.model.itemFromIndex(self.tree_view.currentIndex()).setText("Model {i}".format(i=i))
            
    def add_boundary_displacement(self):

        selected_indexes = self.tree_view.selectedIndexes()

        if selected_indexes:
            selected_indexes = selected_indexes[0]

            for i in self.data:
                curCAEItem : QKooCAEItem = self.data[i]
                
                if selected_indexes == curCAEItem.boundaryItem.index():
                    shapes = self.viewer._display.selected_shapes                    
                    if shapes != []:                        
                        curType = shapes[0]
                        shapeList = [] 
                        shapeList.append(shapes[0])
                        
                        for j in range(1,len(shapes)):
                            if type(curType) == type(shapes[j]):
                                shapeList.append(shapes[j])
                        
                        curCAEItem.AddBoundaryDisplacement(shapeList)                        
                        
                    pass
        #curCAEItem.RemoveAllItems()
        #curCAEItem.UpdateItem()
        self.viewer._display.Context.UpdateCurrentViewer()
            
    def add_model(self):
        parent_item = self.model.invisibleRootItem()

        # Find the parent item based on object type
        for row in range(parent_item.rowCount()):
            if parent_item.child(row, 0).text() == "Model":
                parent_item = parent_item.child(row)
                break 
        else:
            # If the parent item doesn't exist, create it
            parent_item = QStandardItem("Model")
            self.model.appendRow(parent_item)
            self.fixedName[parent_item.index()] = "Model"

        # Add the object as a child item
        curNumberofModel = len(self.data)
        object_item = QKooCAEItem("New_Model_{i}".format(i=curNumberofModel+1),self,self.viewer)
        parent_item.appendRow(object_item)
        self.data[object_item.index()] = object_item

        if self.viewer._display.selected_shapes != []:
            shape = self.viewer._display.selected_shapes[0]
            x,y,z = self.FindCenterofShape(shape)
            xVec, yVec, zVec = self.FindCoordinateVectors(shape)
            # Calculate the rotation angles for each axis (X, Y, Z)
            angle_x = math.atan2(xVec.Crossed(gp_Vec(1, 0, 0)).Magnitude(), xVec.Dot(gp_Vec(1, 0, 0)))
            angle_y = math.atan2(yVec.Crossed(gp_Vec(0, 1, 0)).Magnitude(), yVec.Dot(gp_Vec(0, 1, 0)))
            angle_z = math.atan2(zVec.Crossed(gp_Vec(0, 0, 1)).Magnitude(), zVec.Dot(gp_Vec(0, 0, 1)))

            # Convert angles from radians to degrees
            angle_x_deg = math.degrees(angle_x)
            angle_y_deg = math.degrees(angle_y)
            angle_z_deg = math.degrees(angle_z)
            print(object_item.manipulatorItem.data)

            if self.property_manipulator_widget is None:
                self.CreatePropertyManipulator()                

            self.property_manipulator_widget.data = object_item.manipulatorItem.data 
            self.property_manipulator_widget.manipulatorLocationX = x 
            self.property_manipulator_widget.manipulatorLocationY = y
            self.property_manipulator_widget.manipulatorLocationZ = z  
            self.property_manipulator_widget.manipulatorRotationX = angle_x_deg
            self.property_manipulator_widget.manipulatorRotationY = angle_y_deg
            self.property_manipulator_widget.manipulatorRotationZ = angle_z_deg
            
            self.On_PropertyManipulator_Update()
                
            print(shape)
          

        self.viewer._display.Context.UpdateCurrentViewer()
        pass

    def show_model(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_indexes = selected_indexes[0]
            if selected_indexes in self.data:
                self.data[selected_indexes].ShowAll()
            else:
                print("Search in the data")
                for i in self.data:
                    faceItems = self.data[i].faceItem
                    solidItems = self.data[i].solidItem
                    aisMan : KooAISGeometryManager = self.data[i].data.ais_geometry_manager

                    if faceItems.hasChildren():
                        for row in range(faceItems.rowCount()):
                            faceItem = faceItems.child(row)
                            if selected_indexes == faceItem.index():
                                faceItem.ShowGeom()
                                pass
                            if faceItem.hasChildren():
                                meshItem = faceItem.meshItem
                                if meshItem is not None:
                                    if selected_indexes == meshItem.index():
                                        meshItem.ShowMesh()
                                        pass
                    if solidItems.hasChildren():
                        for row in range(solidItems.rowCount()):
                            solidItem = solidItems.child(row)
                            if selected_indexes == solidItem.index():
                                solidItem.ShowGeom()
                                pass
                            if solidItem.hasChildren():
                                meshItem = solidItem.meshItem
                                if meshItem is not None:
                                    if selected_indexes == meshItem.index():
                                        meshItem.ShowMesh()
                                        pass


        self.viewer._display.Context.UpdateCurrentViewer()

    def import_model(self):
        self.import_step()
        
    def export_model(self):
        self.export_step()
        
    def import_step(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getOpenFileName(
            self, "Open STEP Files", "", "STEP Files (*.stp *.step)"
        )
        if file_path:            
            print("Selected file", file_path)           
            if self.focusedData != None:
                self.focusedData.Erase()
                self.focusedData.ImportStepFile(file_path)
                self.focusedData.Display(False)
                self.viewer._display.Context.UpdateCurrentViewer()

    def export_step(self):
        file_Dialog  = QFileDialog(self)
        file_path, _ = file_Dialog.getSaveFileName(
            self, "Save STEP Files", "", "STEP Files (*.stp *.step)"
        )
        if file_path:
            print("Selected file", file_path)
            if self.focusedData != None:
                self.focusedData.Erase()
                self.focusedData.ExportStepFileSolid(file_path)
                self.focusedData.Display(False)
                self.viewer._display.Context.UpdateCurrentViewer()

                
    def hide_model(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            if selected_index in self.data:
                self.data[selected_index].EraseAll()                
            # Mesh selected
            # hide 만들어야함 
            else:
                print("Search in the data")
                for i in self.data:
                    faceItems = self.data[i].faceItem 
                    solidItems = self.data[i].solidItem
                    aisMan : KooAISGeometryManager = self.data[i].data.ais_geometry_manager
                    print(aisMan)
                    if faceItems.hasChildren():
                        print("Face has children")
                        for row in range(faceItems.rowCount()):
                            faceItem = faceItems.child(row)
                            if selected_index == faceItem.index():                                
                                aisMan.HideFacebyID(faceItem.id)
                                pass
                            if faceItem.hasChildren():
                                meshItem = faceItem.meshItem
                                if meshItem is not None:
                                    if selected_index == meshItem.index():
                                        meshItem.EraseMesh() 
                                        pass 
                    if solidItems.hasChildren():
                        print("Solid has children")
                        for row in range(solidItems.rowCount()):
                            solidItem = solidItems.child(row)
                            if selected_index == solidItem.index():
                                aisMan.HideSolidbyID(solidItem.id)
                                pass
                            if solidItem.hasChildren():
                                meshItem = solidItem.meshItem
                                if meshItem is not None:
                                    if selected_index == meshItem.index():
                                        meshItem.EraseMesh()
                                        pass


                    
        self.viewer._display.Context.UpdateCurrentViewer()
                                        
                      

    def Load_Tutorial(self):
        self.add_model()        
        curFolder = os.getcwd()
        curPath = os.path.join(curFolder,"PCB_0.stp")
        # if exist, import the file
        if os.path.exists(curPath):
            for i in self.data:
                self.tree_view.setCurrentIndex(i)
                self.data[i].ImportStepFile(curPath)
                self.data[i].Display(True)
        self.InputFolderPathEditButton.setText(os.path.join(curFolder,"Example/Model"))
            
        if self.property_manipulator_widget is None:
            self.CreatePropertyManipulator()                
        self.On_PropertyManipulator_Update()
        
        
            

    def remove_item_selected_tree(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            # Get the top-level selected index
            selected_index = selected_indexes[0]
            item = self.model.itemFromIndex(selected_index)
    
            if selected_index in self.data:
                self.data[selected_index].EraseAll()
                del self.data[selected_index]
            else:
                print("Search in the data")
                for i in self.data:
                    faceItems = self.data[i].faceItem
                    solidItems = self.data[i].solidItem                    
                    boundaryItems = self.data[i].boundaryItem
                    aisMan : KooAISGeometryManager = self.data[i].data.ais_geometry_manager
                    aisbdMan : KooAISBoundaryManager = self.data[i].data.ais_boundary_manager
                    print(aisMan)
                    if faceItems.hasChildren():
                        print("Face has children")
                        for row in range(faceItems.rowCount()):
                            faceItem = faceItems.child(row)
                            if selected_index == faceItem.index():
                                print("Remove Face")
                                aisMan.RemoveFacebyID(faceItem.id)
                                faceItem.EraseMeshItem()
                                pass
                            if faceItem.hasChildren():
                                print("Face has mesh")
                                meshItem = faceItem.meshItem
                                if meshItem is not None:
                                    if selected_index == meshItem.index():
                                        print("Remove Mesh")
                                        faceItem.EraseMeshItem()
                    if solidItems.hasChildren():
                        print("Solid has children")
                        for row in range(solidItems.rowCount()):
                            solidItem = solidItems.child(row)
                            print(solidItem.text(), solidItem.index(), selected_index)
                            if selected_index == solidItem.index():
                                #aisMan.RemoveEdge                                
                                print("Remove Solid ")
                                aisMan.RemoveSolidbyID(solidItem.id)
                                solidItem.EraseMeshItem()
                                pass
                            if solidItem.hasChildren():
                                print("Solid has mesh")                                
                                meshItem = solidItem.meshItem
                                if meshItem is not None:
                                    if selected_index == meshItem.index():
                                        print("Remove Mesh")
                                        solidItem.EraseMeshItem()                    
                    if boundaryItems.hasChildren():
                        print("Boundary has children")
                        for row in range(boundaryItems.rowCount()):
                            boundaryItem : QKooBoundaryItem = boundaryItems.child(row)
                            if selected_index == boundaryItem.index():
                                print("Remove Boundary")
                                aisbdMan.RemoveBoundary(boundaryItem.boundary.bid)
                                pass
                    

            parent = item.parent()
            if parent:
                parent.removeRow(item.row())
            else:
                self.model.removeRow(item.row())
                        
        
            self.viewer._display.Context.UpdateCurrentViewer()
    
    def generate_mesh(self):
        selected_indexes = self.tree_view.selectedIndexes()

        if selected_indexes:
            selected_indexes = selected_indexes[0]
            if selected_indexes in self.data:
                pass
            else:
                for i in self.data:
                    aisMan : KooAISGeometryManager = self.data[i].data.ais_geometry_manager
                    faceItems = self.data[i].faceItem
                    solidItems = self.data[i].solidItem
                    for j in range(faceItems.rowCount()):
                        faceItem: QKooGeometryItem = faceItems.child(j)
                        if faceItem.index() == selected_indexes:
                            inputFilePath = self.InputFolderPathEditButton.text()
                            faceItem.GenerateMesh(inputFilePath)
                            self.viewer._display.Context.UpdateCurrentViewer()
                    for j in range(solidItems.rowCount()):
                        solidItem : QKooGeometryItem = solidItems.child(j)
                        if solidItem.index() == selected_indexes:                            
                            inputFilePath = self.InputFolderPathEditButton.text()
                            solidItem.GenerateMesh(inputFilePath)
                            self.viewer._display.Context.UpdateCurrentViewer()
        pass
    def start_mesh_generate(self):
        thread = threading.Thread(target=self.generate_mesh)
        thread.start()

    def show_context_menu_tree(self, position):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            # Get the top-level selected index
            selected_index = selected_indexes[0]
            item = self.model.itemFromIndex(selected_index)
            if item.text() == "Model":
                menu = QMenu(self)
                add_model_action = QAction('Add Model',self)
                #remove_action = QAction('Remove',self)
                add_model_action.triggered.connect(self.add_model)
                #remove_action.triggered.connect(self.remove_item_selected_tree)
                menu.addAction(add_model_action)
                #menu.addAction(remove_action)
                menu.exec_(self.tree_view.viewport().mapToGlobal(position))
            elif item.text() == "Manipulator":
                ## Find Manipulator
                curManipulator = None
                curIndex = None
                print("Manipulfator is selected")
                for index in self.data:
                    print("check indexes")
                    print(self.data[index].manipulatorItem.index(), selected_index)
                   
                    if self.data[index].manipulatorItem.index() == selected_index:
                        curManipulator = self.data[index].manipulatorItem 
                        curIndex = index
                #print(curManipulator)
                if curIndex:
                    menu = QMenu(self)
                    property_action = QAction('Property',self)
                    property_action.triggered.connect(self.OpenPropertyManipulator)
                    print("Property Widget will be created")
                    self.CreatePropertyManipulator()                    
                    if self.property_manipulator_widget != None:
                        #self.property_manipulator_widget.SetManipulator(self.data[curIndex].data.manipulator)                        
                        print("Property Widget will be updated")
                        self.property_manipulator_widget.SetManipulator(item)
                    menu.addAction(property_action)
                    menu.exec_(self.tree_view.viewport().mapToGlobal(position))
            elif item.text() == "Sketch":
                print("Sketch is selected")
                curIndex = None
                for index in self.data:
                    print("check indexes")
                    print(self.data[index].sketchItem.index(), selected_index)

                    if self.data[index].sketchItem.index() == selected_index:
                        curSketch = self.data[index].sketchItem 
                        curIndex = index                        
                if curIndex:
                    menu = QMenu(self)
                    edit_action = QAction('Edit',self)                     
                    face_action = QAction('Face',self)
                    solid_action = QAction('Solid',self)
                    edit_action.triggered.connect(self.EditSketch)
                    face_action.triggered.connect(self.AddFacefromSketch)

                    menu.addAction(edit_action)
                    menu.addAction(face_action)
                    menu.addAction(solid_action)
                    menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                    

                        
            elif selected_index in self.data:
                self.focusedData = self.data[selected_index]
                menu = QMenu(self)                
                show_model_action = QAction('Show',self)
                import_model_action = QAction('Import',self)
                export_model_action = QAction('Export',self)
                hide_model_action = QAction('Hide',self)
                remove_action = QAction('Remove',self)
                show_model_action.triggered.connect(self.show_model)
                import_model_action.triggered.connect(self.import_model)
                export_model_action.triggered.connect(self.export_model)
                hide_model_action.triggered.connect(self.hide_model)
                remove_action.triggered.connect(self.remove_item_selected_tree)
                menu.addAction(remove_action)
                menu.addAction(import_model_action)
                menu.addAction(export_model_action)
                menu.addAction(show_model_action)
                menu.addAction(hide_model_action)
                menu.exec_(self.tree_view.viewport().mapToGlobal(position))
            else:
                ############# Face 기하형상을 선택하는 경우 
                for i in self.data:
                    faceItems = self.data[i].faceItem 
                    if faceItems.hasChildren():
                        for row in range(faceItems.rowCount()):
                            faceItem = faceItems.child(row)
                            if faceItem == None:
                                continue
                            if faceItem is not None:
                                if selected_index == faceItem.index():
                                    menu = QMenu(self)
                                    remove_action = QAction('Remove',self)
                                    generate_action = QAction('Generate',self)                                    
                                    show_action = QAction('Show',self)
                                    hide_action = QAction('Hide',self)                                

                                    property_action = QAction('Property',self)

                                    self.CreatePropertyFace()
                                    if self.property_face_widget != None:
                                        print("Property Widget will be updated")
                                        self.property_face_widget.SetFaceItem(faceItem)                                    


                                    remove_action.triggered.connect(self.remove_item_selected_tree)
                                    #generate_action.triggered.connect(self.generate_mesh)
                                    generate_action.triggered.connect(self.start_mesh_generate)
                                    show_action.triggered.connect(self.show_model)
                                    hide_action.triggered.connect(self.hide_model)
                                    property_action.triggered.connect(self.OpenPropertyFace)

                                    menu.addAction(remove_action)
                                    menu.addAction(generate_action)
                                    menu.addAction(show_action)
                                    menu.addAction(hide_action)
                                    menu.addAction(property_action)
                                    menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                                if faceItem.meshItem is not None:
                                    if selected_index == faceItem.meshItem.index():
                                        menu = QMenu(self)
                                        remove_action = QAction('Remove',self)
                                        show_action = QAction('Show',self)
                                        hide_action = QAction('Hide',self)
                                        remove_action.triggered.connect(self.remove_item_selected_tree)
                                        show_action.triggered.connect(self.show_model)
                                        hide_action.triggered.connect(self.hide_model)

                                        menu.addAction(remove_action)
                                        menu.addAction(show_action)
                                        menu.addAction(hide_action)
                                        menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                            
                                    '''
                                    display_model_action = QAction('Display',self)
                                    import_model_action = QAction('Import',self)
                                    hide_model_action = QAction('Hide',self)
                                    
                                    display_model_action.triggered.connect(self.display_model)
                                    import_model_action.triggered.connect(self.import_model)
                                    hide_model_action.triggered.connect(self.hide_model)
                                    
                                    
                                    menu.addAction(import_model_action)
                                    menu.addAction(display_model_action)
                                    menu.addAction(hide_model_action)
                                    '''
                                
                        
                    pass
                ############# Solid 기하형상을 선택하는 경우 
                for i in self.data:
                    solidItems = self.data[i].solidItem
                    if solidItems.hasChildren():
                        for row in range(solidItems.rowCount()):
                            solidItem = solidItems.child(row)
                            if solidItem == None:
                                continue                           
                            if solidItem is not None:
                                if selected_index == solidItem.index():
                                    menu = QMenu(self)
                                    remove_action = QAction('Remove',self)
                                    generate_action = QAction('Generate',self)
                                    property_action = QAction('Property',self)
                                    show_action = QAction('Show',self)
                                    hide_action = QAction('Hide',self)
                                     
                                    self.CreatePropertySolid()
                                    if self.property_solid_widget != None:
                                        print("Property Widget will be updated")
                                        self.property_solid_widget.SetSolidItem(solidItem)
                                                                            

                                    remove_action.triggered.connect(self.remove_item_selected_tree)
                                    #generate_action.triggered.connect(self.generate_mesh)
                                    generate_action.triggered.connect(self.start_mesh_generate)
                                    property_action.triggered.connect(self.OpenPropertySolid)
                                    show_action.triggered.connect(self.show_model)
                                    hide_action.triggered.connect(self.hide_model)

                                    menu.addAction(remove_action)
                                    menu.addAction(generate_action)
                                    menu.addAction(show_action)
                                    menu.addAction(hide_action)
                                    menu.addAction(property_action)

                                   
                                    menu.exec_(self.tree_view.viewport().mapToGlobal(position))                                                        
                                if solidItem.meshItem is not None:
                                    if selected_index == solidItem.meshItem.index():
                                        menu = QMenu(self)
                                        remove_action = QAction('Remove',self)
                                        show_action = QAction('Show',self)
                                        hide_action = QAction('Hide',self)                                        
                                        remove_action.triggered.connect(self.remove_item_selected_tree)
                                        show_action.triggered.connect(self.show_model)
                                        hide_action.triggered.connect(self.hide_model)

                                        menu.addAction(remove_action)
                                        menu.addAction(show_action)
                                        menu.addAction(hide_action)

                                        menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                            
                        
                    pass
                
                for i in self.data:
                    boundaryItem = self.data[i].boundaryItem
                    if boundaryItem is not None:
                        if selected_index == boundaryItem.index():
                            menu = QMenu(self)
                            add_displacement_action = QAction('Displacement',self)
                            add_displacement_action.triggered.connect(self.add_boundary_displacement)
                            menu.addAction(add_displacement_action)
                            menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                        else:
                            for row in range(boundaryItem.rowCount()):
                                boundaryDisplacementItem = boundaryItem.child(row)
                                if boundaryDisplacementItem is not None:
                                    if selected_index == boundaryDisplacementItem.index():
                                        menu = QMenu(self)
                                        remove_action = QAction('Remove',self)
                                        remove_action.triggered.connect(self.remove_item_selected_tree)
                                        menu.addAction(remove_action)
                                        menu.exec_(self.tree_view.viewport().mapToGlobal(position))
                                        pass




            
        else:
            menu = QMenu(self)
            add_model_action = QAction('Add Model',self)
            add_model_action.triggered.connect(self.add_model)
            menu.addAction(add_model_action)
            menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def CreatePropertyFace(self):
        print("CreatePropertyFace")
        self.property_face_widget = KooFaceGeometryWidget(self.On_PropertyFace_Update,self,"Face")
        self.property_face_widget.hide()

    def CreatePropertySolid(self):
        print("CreatePropertySolid")
        self.property_solid_widget = KooSolidGeometryWidget(self.On_PropertySolid_Update,self,"Solid")
        self.property_solid_widget.hide()        
    
    def CreatePropertyManipulator(self):
        print("CreatePropertyManipulator")
        #if self.property_manipulator_widget == None:
        self.property_manipulator_widget = KooManipulatorWidget(self.On_PropertyManipulator_Update,self,"Manipulator")
        self.property_manipulator_widget.hide()
        #else:
        #    self.property_manipulator_widget.show()        

    def OpenPropertyFace(self):
        self.property_face_widget.show()
        self.dockWidgetPropertyFace = QDockWidget("Face Property", self)
        self.dockWidgetPropertyFace.setWidget(self.property_face_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockWidgetPropertyFace)

    def OpenPropertySolid(self):
        self.property_solid_widget.show()
        self.dockWidgetPropertySolid = QDockWidget("Solid Property", self)
        self.dockWidgetPropertySolid.setWidget(self.property_solid_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockWidgetPropertySolid)
        

    def OpenPropertyManipulator(self):            
        self.property_manipulator_widget.show()
        self.dockWidgetPropertyManipulator = QDockWidget("Manipulator Property", self)
        self.dockWidgetPropertyManipulator.setWidget(self.property_manipulator_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockWidgetPropertyManipulator)

    def EditSketch(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            # Get the top-level selected index
            selected_index = selected_indexes[0]
            item = self.model.itemFromIndex(selected_index)
            if item.text() == "Sketch":
                print("Sketch is selected")
                for index in self.data:
                    print("check indexes")
                    if self.data[index].sketchItem.index() == selected_index:
                        curSketch = self.data[index].sketchItem
                        curSketch.DisplayWindow()

    def AddFacefromSketch(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if selected_indexes:
            selected_index = selected_indexes[0]
            item = self.model.itemFromIndex(selected_index)
            if item.text() == "Sketch":
                print("Sketch is selected")
                for index in self.data:
                    print("check indexes")
                    if self.data[index].sketchItem.index() == selected_index:
                        self.data[index].AddFacesfromSketch()
                        #curSketch = self.data[index].sketchItem
                        #curSketch.AddFacesfromSketch(self.data[index].data.ais_geometry_manager)
                        self.viewer._display.Context.UpdateCurrentViewer()                            
    
    def On_PropertyFace_Update(self):
        pass

    def On_PropertySolid_Update(self):
        #if self.property_solid_widget is not None:
        #    selectedData = self.property_solid_widget.data
        pass

    def On_PropertyManipulator_Update(self):
        if self.property_manipulator_widget is not None:            
            selectedData = self.property_manipulator_widget.data

            if selectedData != None:
                print("Manipulator is updated!")
                trsX = self.property_manipulator_widget.manipulatorLocationX
                trsY = self.property_manipulator_widget.manipulatorLocationY
                trsZ = self.property_manipulator_widget.manipulatorLocationZ
                rotX = self.property_manipulator_widget.manipulatorRotationX
                rotY = self.property_manipulator_widget.manipulatorRotationY
                rotZ = self.property_manipulator_widget.manipulatorRotationZ
               
                axX = gp_Ax1(gp_Pnt(0.0,0.0,0.0),gp_Dir(1.0,0.0,0.0))
                axY = gp_Ax1(gp_Pnt(0.0,0.0,0.0),gp_Dir(0.0,1.0,0.0))
                axZ = gp_Ax1(gp_Pnt(0.0,0.0,0.0),gp_Dir(0.0,0.0,1.0))
                
                trsf1 = gp_Trsf()
                trsf1.SetRotation(axX,math.radians(rotX)) 
                axX.Transform(trsf1)
                axY.Transform(trsf1)
                axZ.Transform(trsf1)
                trsf2 = gp_Trsf()
                trsf2.SetRotation(axY,math.radians(rotY))
                axX.Transform(trsf2)
                axY.Transform(trsf2)
                axZ.Transform(trsf2)
                trsf3 = gp_Trsf()
                trsf3.SetRotation(axZ,math.radians(rotZ))
                trsf = trsf1.Multiplied(trsf2)
                trsf = trsf.Multiplied(trsf3)
                trsf4 = gp_Trsf()
                trsf4.SetTranslation(gp_Vec(trsX,trsY,trsZ))
                trsf = trsf4.Multiplied(trsf)
              
                selectedData.SetTransformation(trsf)                
                selectedData.manipulator.locationX = trsX
                selectedData.manipulator.locationY = trsY
                selectedData.manipulator.locationZ = trsZ
                selectedData.manipulator.rotationX = rotX
                selectedData.manipulator.rotationY = rotY
                selectedData.manipulator.rotationZ = rotZ
                # Save the current view before calling UpdateCurrentViewer()
                self.viewer._display.Context.UpdateCurrentViewer()                

              #  selectedData.Display(True)
                
        
        pass

    def ShowMessageforExporttoAlltoDirectory(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Export to All to Directory")
        message_box.setText("Export:")
        message_box.setInformativeText("Do you want to export to all to directory?")
        message_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        message_box.setDefaultButton(QMessageBox.StandardButton.No)
        message_box.buttonClicked.connect(self.ExporttoAlltoDirectory)
        choice = message_box.exec()
        if choice == message_box.Yes:
            print("Yes")
        elif choice == message_box.No:
            print("No")

    def ExporttoAlltoDirectory(self):
        curPath =  self.InputFolderPathEditButton.text()
        

            
        pass

    # Popup menu when geometries are not selected 
    def PopupViewerMenu(self, event : QMouseEvent):
        self.popupSelectMode = 0 
        menu = QMenu(self)
        addMenu = QMenu("Add")
        menu.addMenu(addMenu)        
        add_model_action = QAction('Model',self)        
        add_model_action.triggered.connect(self.add_model)
        

        addMenu.addAction(add_model_action)
        
        menu.exec_(event.globalPos())
        pass

    def PopupViewerMenuSolid(self, event : QMouseEvent):
        self.popupSelectMode = 4
        menu = QMenu(self)
        addMenu = QMenu("Add")
        menu.addMenu(addMenu)        
        add_model_action = QAction('Model',self)
        add_model_action.triggered.connect(self.add_model)

        addMenu.addAction(add_model_action)
        menu.exec_(event.globalPos())
        pass
    
    # Popup menu when face is selected
    def PopupViewerMenuFace(self, event : QMouseEvent):
        self.popupSelectMode = 3 
        menu = QMenu(self)
        addMenu = QMenu("Add")        
        menu.addMenu(addMenu)        
        add_model_action = QAction('Model',self)
        add_model_action.triggered.connect(self.add_model)
        addMenu.addAction(add_model_action)
        '''
        add_boundary_menu = QMenu("Boundary")                
        addMenu.addMenu(add_boundary_menu)    
        add_boundary_displacement_action = QAction('Displacement',self)        
        add_boundary_displacement_action.triggered.connect(self.add_boundary_displacement)        
        add_boundary_menu.addAction(add_boundary_displacement_action)
        '''
        menu.exec_(event.globalPos())
        pass

    def PopupViewerMenuEdge(self, event : QMouseEvent):
        self.popupSelectMode = 2
        menu = QMenu(self)
        addMenu = QMenu("Add")        
        menu.addMenu(addMenu)        
        add_model_action = QAction('Model',self)
        add_model_action.triggered.connect(self.add_model)
        addMenu.addAction(add_model_action)

        menu.exec_(event.globalPos())
        pass

    def PopupViewerMenuVertex(self, event : QMouseEvent):
        self.popupSelectMode = 1
        menu = QMenu(self)
        addMenu = QMenu("Add")        
        menu.addMenu(addMenu)        
        add_model_action = QAction('Model',self)
        add_model_action.triggered.connect(self.add_model)
        addMenu.addAction(add_model_action)

        menu.exec_(event.globalPos())
        pass
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:  
        self.on_pressed_mouse_position = a0.pos()
          
        pnt = self.viewer._display.View.Camera().Eye()
        camera_direction = self.viewer._display.View.Camera().Direction()

        print("Eye:",pnt.X(), pnt.Y(), pnt.Z())
        print("Camera Direction:", camera_direction.X(), camera_direction.Y(), camera_direction.Z())

        for i in self.data:
            curCAEItem : QKooCAEItem =self.data[i]
            manipulator : KooAISManipulator = curCAEItem.data.manipulator
            print(i)
            # -1 unselected 
            # 0 x axis 
            # 1 y axis
            # 2 z axis
            print(manipulator.ActiveAxisIndex())            
            # 1 axis 
            # 2 rotation 
            # 3 vertex
            # 4 plane
            print(manipulator.ActiveMode())

        return super().mousePressEvent(a0)
    
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        return super().mouseReleaseEvent(a0)

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        return super().mouseDoubleClickEvent(a0)
    
    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        return super().mouseMoveEvent(a0)
    
    def wheelEvent(self, a0: QWheelEvent) -> None:

        self.globalAxis.RemoveFromView(self.viewer)
        self.globalAxis.DisplayAxis(self.viewer,False,self.viewer.screenSize)
        self.viewer._display.Context.UpdateCurrentViewer()

        return super().wheelEvent(a0)
    
    def FindCenterofShape(self, shape):
        
        if shape.ShapeType() == TopAbs_VERTEX:
            vertex = BRep_Tool.Pnt(shape)
            return [vertex.X(), vertex.Y(), vertex.Z()]
        
        elif shape.ShapeType() == TopAbs_EDGE:
            curve = BRepAdaptor.BRepAdaptor_Curve(shape)
            umin, umax = curve.FirstParameter(), curve.LastParameter()
            u = (umin + umax) / 2
            center_point = gp_Pnt()
            curve.D0(u, center_point)
            return [center_point.X(), center_point.Y(), center_point.Z()]
        
        elif shape.ShapeType() == TopAbs_FACE:
            surface = BRepAdaptor.BRepAdaptor_Surface(shape)
            u_center = (surface.FirstUParameter() + surface.LastUParameter()) / 2
            v_center = (surface.FirstVParameter() + surface.LastVParameter()) / 2
            center_point = gp_Pnt()
            surface.D0(u_center, v_center, center_point)
            return [center_point.X(), center_point.Y(), center_point.Z()]
        
        elif shape.ShapeType() == TopAbs_SOLID:
            face_iterator = TopExp.TopExp_Explorer(shape, TopAbs_FACE)
            sum_center_point = gp_Pnt(0,0,0)
            num_faces = 0 
            while face_iterator.More():
                num_faces += 1
                face = face_iterator.Current()
                surface = BRepAdaptor.BRepAdaptor_Surface(face)
                u_center = (surface.FirstUParameter() + surface.LastUParameter()) / 2.0
                v_center = (surface.FirstVParameter() + surface.LastVParameter()) / 2.0
                center_point = gp_Pnt()
                surface.D0(u_center, v_center, center_point)

                sum_center_point.SetX(sum_center_point.X() + center_point.X())
                sum_center_point.SetY(sum_center_point.Y() + center_point.Y())
                sum_center_point.SetZ(sum_center_point.Z() + center_point.Z())                

                face_iterator.Next()                

            sum_center_point.SetX(sum_center_point.X() / num_faces)
            sum_center_point.SetY(sum_center_point.Y() / num_faces)
            sum_center_point.SetZ(sum_center_point.Z() / num_faces)
            return [sum_center_point.X(), sum_center_point.Y(), sum_center_point.Z()]
        return None
    
    def FindCoordinateVectors(self,shape):
        
        if shape.ShapeType() == TopAbs_VERTEX:
            xVec = gp_Vec(1,0,0)
            yVec = gp_Vec(0,1,0)
            zVec = gp_Vec(0,0,1)
            return [xVec, yVec, zVec]
        
        elif shape.ShapeType() == TopAbs_EDGE:
            curve = BRepAdaptor.BRepAdaptor_Curve(shape)
            # Get the start and end points of the curve
            start_point = curve.Value(curve.FirstParameter())
            end_point = curve.Value(curve.LastParameter())
            xVec = gp_Vec(start_point, end_point)
            xVec.Normalize()
            testVector = gp_Vec(0,0,1.0)
            if abs(xVec.Dot(testVector)) < 1.0e-10:
                testVector = gp_Vec(0,1.0,0)
            yVec = xVec.Crossed(testVector)
            yVec.Normalize()
            zVec = xVec.Crossed(yVec)
            zVec.Normalize()
            return [xVec, yVec, zVec]

        elif shape.ShapeType() == TopAbs_FACE:
            #surface = BRepAdaptor.BRepAdaptor_Surface(shape)
            zVec = gp_Vec()
            centerPoint = gp_Pnt()
            gprop = BRepGProp.BRepGProp_Face(shape)
            gprop.Normal(0.5,0.5,centerPoint,zVec)
            print("Z Vector,",zVec.X(),zVec.Y(),zVec.Z())   
            zVec.Normalize()
            tmpVec = gp_Vec()
            tmpPnt = gp_Pnt()
            gprop.Normal(0.499,0.5,tmpPnt,tmpVec)
            tmpVec.SetCoord(tmpPnt.X()-centerPoint.X(),tmpPnt.Y()-centerPoint.Y(),tmpPnt.Z()-centerPoint.Z())
            yVec = zVec.Crossed(tmpVec)
            yVec.Normalize()

            print("Y Vector,",yVec.X(),yVec.Y(),yVec.Z())
            
            xVec = yVec.Crossed(zVec)
            xVec.Normalize()
            print("X Vector,",xVec.X(),xVec.Y(),xVec.Z())
            return [xVec, yVec, zVec]        

        
        elif shape.ShapeType() == TopAbs_SOLID:
            xVec = gp_Vec(1,0,0)    
            yVec = gp_Vec(0,1,0)
            zVec = gp_Vec(0,0,1)
            return [xVec, yVec, zVec]
        return None



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())