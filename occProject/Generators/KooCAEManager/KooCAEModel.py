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

from OCC.Core.gp import gp_Pnt, gp_Trsf
#from OCC.Core.AIS import AIS_Manipulator

from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex
)

from OCC.Core.TopoDS import (
    TopoDS_Vertex,
)

import math
from OCC.Core.gp import gp_Ax1, gp_Dir, gp_Trsf, gp_Vec
from KooCAEManager.KooAISBoundaryManager import KooAISBoundaryManager
from KooCAEManager.KooAISBoundary import (
    KooBoundary,
    KooAISBoundaryDisplacement,
)
from KooCAEManager.KooBoundary import (
    KooBoundaryDisplacement,
)

from KooCAEManager.KooAISGeometryManager import KooAISGeometryManager
from KooCAEManager.KooAISGeometry import KooAISManipulator
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH, KooMeshManager
from KooCAEManager.KooAISGeometry import (
    KooAISGeomVertex,
    KooAISGeomEdge,
    KooAISGeomWire,
    KooAISGeomFace,
    KooAISGeomShell,
    KooAISGeomSolid,
    KooAISGeomArc,
    KooAISGeomBSplineFace,
    KooAISGeomFillingFace,
    KooAISGeomLine,
    KooAISGeomPrism
)
from KooCAEManager.KooGeometry import (
    KooGeomVertex,
    KooGeomEdge,
    KooGeomWire,
    KooGeomFace,
    KooGeomShell,
    KooGeomSolid,
    KooGeomArc,
    KooGeomLine,
    KooGeomBSplineFace,
    KooGeomFillingFace,
    KooGeomPolyline,
    KooGeomPrism
)
from PyQt5.QtGui import QStandardItem
import KooCADPlaneModellingWindow as KooCADPlaneModellingWindow
import KooCADStackModellingWindow as KooCADStackModellingWindow

class QKooCAEModel(QStandardItem):
    def __init__(self, parent, viewer):
        self.name = "" 
        super(QKooCAEModel, self).__init__(self.name)                
        pass

class QKooBoundaryItem(QStandardItem):
    def __init__(self, name, boundary, parent, viewer = None):
        self.name = name
        super(QKooBoundaryItem, self).__init__(name)
        self.boundary = boundary
        self.viewer = viewer
        self.Parent = parent 
    
    def GetBoundary(self):
        return self.boundary

    def Erase(self, update = False):
        self.boundary.SetHide(self.viewer, True, update)
    
    def Show(self, update = False):
        self.Erase(update)
        self.Display(update)
    
    def Display(self, update = False):
        self.boundary.SetHide(self.viewer, False, update)        

class QKooMeshItem(QStandardItem):
    def __init__(self, parent, viewer = None):
        super(QKooMeshItem, self).__init__("Mesh")
        self.mesh = KooMeshManagerGMSH()
        self.Parent = parent
        self.viewer = viewer
        self.meshSizeMin = 1
        self.meshSizeMax = 1
        self.meshDimension = 3

    def SetPath(self, path):
        self.mesh.SetPath(path)
    
    def SetFileName(self, name):
        self.mesh.SetName(name)

    def SetMeshSize(self,mean):
        self.meshSizeMin = mean
        self.meshSizeMax = mean
    
    def SetMeshSizeMinMax(self, minValue, maxValue):
        self.meshSizeMin = minValue
        self.meshSizeMax = maxValue
    
    def GetMeshManager(self):
        return self.mesh

    def GenerateMesh(self, geom):
        self.EraseMesh()
        if type(geom) == KooAISGeomFace or type(geom) == KooGeomFace:
            self.meshDimension = 2
            if geom.face != None:
                self.mesh.mesh_shape(geom.face, self.meshSizeMin, self.meshSizeMax, self.meshDimension) 
        elif type(geom) == KooAISGeomSolid or type(geom) == KooGeomSolid:
            self.meshDimension = 3 
            if geom.solid != None:
                self.mesh.mesh_shape(geom.solid, self.meshSizeMin, self.meshSizeMax, self.meshDimension)
        self.DisplayMesh()    
    
    def EraseMesh(self):
        self.mesh.Erase(self.viewer)
    
    def ShowMesh(self, update = False):
        self.EraseMesh()
        self.DisplayMesh(update)

    def DisplayMesh(self,update = False):        
        trsf = self.Parent.Parent.GetTransformationMultiplied()
        self.mesh.Display(self.viewer,update,trsf)
    
    pass                        

class QKooGeometryItem(QStandardItem):
    def __init__(self, geom, parent, viewer = None):
        self.name = geom.name
        super(QKooGeometryItem, self).__init__(self.name)
        self.id = geom.id        
        self.geom = geom
        self.viewer = viewer
        self.meshItem = None 
        self.Parent = parent
        self.meshSize = 1.0
            
    def GetGeometry(self):
        return self.geom   

    def SetMeshSize(self,mean):
        self.meshSize = mean     
    
    def GenerateMesh(self,directoryPath = ""):
        self.EraseGeom()

        if self.meshItem == None:            
            self.meshItem = QKooMeshItem(self,self.viewer)
            modelName = self.Parent.name
            geomName = self.name 
            if directoryPath == "":
                directoryPath = os.getcwd()
            directoryPath = directoryPath.replace("/","\\") 
            fullPath = directoryPath + "\\" + modelName + "\\" + geomName
            if not os.path.exists(fullPath):
                os.makedirs(fullPath)
            self.meshItem.SetFileName(geomName)
            self.meshItem.SetPath(fullPath)
            self.appendRow(self.meshItem)    
        self.meshItem.SetMeshSize(self.meshSize)
        self.meshItem.GenerateMesh(self.geom)                    

    def EraseMeshItem(self):
        if self.meshItem != None:
            self.meshItem.EraseMesh()
            self.meshItem = None

    def EraseGeom(self, update = False):
        self.geom.SetHide(self.viewer, True,update)
        #self.geom.Erase(self.viewer, update)
    
    def ShowGeom(self, update = False):
        self.EraseGeom(update)
        self.DisplayGeom(update)
       

    def DisplayGeom(self,update = False):
        self.geom.SetHide(self.viewer,False,update)
        #self.geom.Display(self.viewer,update)    
        pass
             
class QSketchItem(QStandardItem):
    def __init__(self, name, parent = None, viewer = None):
        super(QSketchItem, self).__init__(name)
        self.ais_geometry_manager = KooAISGeometryManager(parent.Parent, viewer)
        self.modellingWindow = None        
        self.Parent = parent
        self.viewer = viewer
        self.name = name
        self.ais_geometry_manager_list = []
        self.ais_geometry_manager_list.append(self.ais_geometry_manager)
        #self.DisplayWindow()

    def DisplayWindow(self):
        '''if self.modellingWindow:
            self.modellingWindow.show()
        else:          

            #self.modellingWindow = KooCADPlaneModellingWindow.KooCADPlaneModellingWindow()        
            self.modellingWindow = KooCADStackModellingWindow.KooCADStackModellingWindow()
            self.modellingWindow.SetAISGeometryManager(self.ais_geometry_manager)
            self.ais_geometry_manager.Display(True)
            self.modellingWindow.SetParent(self)
            self.modellingWindow.show()'''
            
        if self.modellingWindow:
            
            #self.modellingWindow.close()
            self.modellingWindow.setParent(None)
            self.modellingWindow.deleteLater()           
            self.modellingWindow = None 

        #self.modellingWindow = KooCADPlaneModellingWindow.KooCADPlaneModellingWindow()        
        self.modellingWindow = KooCADStackModellingWindow.KooCADStackModellingWindow()
        #self.modellingWindow.SetAISGeometryManager(self.ais_geometry_manager)        
        if len(self.ais_geometry_manager_list)>0:
            self.modellingWindow.add_models(self.ais_geometry_manager_list)
        self.modellingWindow.SetAISGeometryManagerfromIndex(0)
        self.ais_geometry_manager.Display(True)
        self.modellingWindow.SetParent(self)
        
        self.modellingWindow.show()

    def AddFacesfromSketch(self,aisMan : KooAISGeometryManager):
        print("Update Sketch")
        #parentItem : QKooCAEItem = self.Parent
        #parentItem.RemoveAllItems()
        faces = self.ais_geometry_manager.faces

        addedFaces = [] 
        for i in faces:
            addedFaces.append(aisMan.AddFace(faces[i]))

        caeModel : KooCAEModel = self.Parent.data
        caeModel.Display()         
        #parentItem.UpdateItem()       
        return addedFaces
    
         



class QKooManipulatorItem(QStandardItem):
    def __init__(self, name, manipulator):
        super(QKooManipulatorItem, self).__init__(name)
        self.name = name
        self.manipulator = manipulator

class QKooCAEItem(QStandardItem):

    def __init__(self,text, parent,viewer):
        super(QKooCAEItem, self).__init__(text)
        self.name = text
        self.data : KooCAEModel = KooCAEModel(parent,viewer)
        self.Parent = parent
        self.manipulatorItem = QKooManipulatorItem("Manipulator", self.data.manipulator)        
        self.appendRow(self.manipulatorItem)        
        self.manipulatorItem.data = self.data
        #self.manipulatorIndex = self.manipulatorItem.index()

        self.sketchItem = QSketchItem("Sketch",self,viewer)
        self.appendRow(self.sketchItem)
        
        self.geomItem = QStandardItem("Geometry")        

        self.vertexItem = QStandardItem("Vertex")
        self.edgeItem = QStandardItem("Edge")
        self.wireItem = QStandardItem("Wire")        
        self.faceItem = QStandardItem("Face")        
        self.shellItem = QStandardItem("Shell")
        self.solidItem = QStandardItem("Solid")
        self.appendRow(self.geomItem)
        self.geomItem.appendRow(self.vertexItem)
        self.geomItem.appendRow(self.edgeItem)
        self.geomItem.appendRow(self.wireItem)
        self.geomItem.appendRow(self.faceItem)
        self.geomItem.appendRow(self.shellItem)
        self.geomItem.appendRow(self.solidItem)

        self.boundaryItem = QStandardItem("Boundary")
        
        self.appendRow(self.boundaryItem)
        


      
        
        '''        
        self.appendRow(self.vertexItem)
        self.appendRow(self.edgeItem)
        self.appendRow(self.wireItem)
        self.appendRow(self.faceItem)
        self.appendRow(self.shellItem)
        self.appendRow(self.solidItem)        
        '''

        self.data.SetTreeViewItem(self)
    
    def ImportStepFile(self, filePath):
        # Data load
        #self.RemoveAllItems()
        solids = self.data.ImportStepFile(filePath)
        #self.UpdateItem()    
        for solid in solids:
            solidItem = QKooGeometryItem(solid,self,self.data.viewer)
            self.solidItem.appendRow(solidItem)

    def RemoveAllItems(self):
        #Child Item of self.vertexItem is QStandardItem
        for i in range(self.vertexItem.rowCount()):
            self.vertexItem.removeRow(0)
        for i in range(self.edgeItem.rowCount()):
            self.edgeItem.removeRow(0)
        for i in range(self.wireItem.rowCount()):
            self.wireItem.removeRow(0)
        for i in range(self.faceItem.rowCount()):
            self.faceItem.removeRow(0)
        for i in range(self.shellItem.rowCount()):
            self.shellItem.removeRow(0)
        for i in range(self.solidItem.rowCount()):
            self.solidItem.removeRow(0)        
        for i in range(self.boundaryItem.rowCount()):
            self.boundaryItem.removeRow(0)

    def UpdateItem(self):
        self.vertexItem.clearData()
        self.edgeItem.clearData()
        self.wireItem.clearData()
        self.faceItem.clearData()
        self.shellItem.clearData()
        self.solidItem.clearData()

        self.boundaryItem.clearData()

        self.vertexItem.setText("Vertex")
        self.edgeItem.setText("Edge")
        self.wireItem.setText("Wire")
        self.faceItem.setText("Face")
        self.shellItem.setText("Shell")
        self.solidItem.setText("Solid")

        self.boundaryItem.setText("Boundary")

        #self.data.ais_geometry_manager.vertices is Dictionary
        for i in self.data.ais_geometry_manager.vertices:
            vertex = self.data.ais_geometry_manager.vertices[i]
            vertexItem = QKooGeometryItem(vertex,self,self.data.viewer)
            self.vertexItem.appendRow(vertexItem)
        for i in self.data.ais_geometry_manager.edges:
            edge = self.data.ais_geometry_manager.edges[i]
            edgeItem = QKooGeometryItem(edge,self,self.data.viewer)
            self.edgeItem.appendRow(edgeItem)
        for i in self.data.ais_geometry_manager.wires:
            wire = self.data.ais_geometry_manager.wires[i]
            wireItem = QKooGeometryItem(wire,self,self.data.viewer)
            self.wireItem.appendRow(wireItem)        
        for i in self.data.ais_geometry_manager.faces:
            face = self.data.ais_geometry_manager.faces[i]
            faceItem = QKooGeometryItem(face,self,self.data.viewer)
            self.faceItem.appendRow(faceItem)
        for i in self.data.ais_geometry_manager.shells:
            shell = self.data.ais_geometry_manager.shells[i]
            shellItem = QKooGeometryItem(shell,self,self.data.viewer)
            self.shellItem.appendRow(shellItem)
        for i in self.data.ais_geometry_manager.solids:
            solid = self.data.ais_geometry_manager.solids[i]
            solidItem = QKooGeometryItem(solid,self,self.data.viewer)
            self.solidItem.appendRow(solidItem)

        for i in self.data.ais_boundary_manager.boundaryDict:
            boundary = self.data.ais_boundary_manager.boundaryDict[i]
            if boundary.btype == "Displacement":
                boundaryItem = QKooBoundaryItem("Displacement{bid}".format(bid=i),boundary,self,self.data.viewer)
                self.boundaryItem.appendRow(boundaryItem)                

    def AddFacesfromSketch(self):
        faces = self.sketchItem.AddFacesfromSketch(self.data.ais_geometry_manager)
        for face in faces:
            faceItem = QKooGeometryItem(face,self,self.data.viewer)
            self.faceItem.appendRow(faceItem)



    def AddBoundaryDisplacement(self, shapeList, timeList = [] , dispList = [] ):
        boundary = self.data.AddBoundaryDisplacement(shapeList, timeList, dispList)
        boundaryItem = QKooBoundaryItem("Displacement{bid}".format(bid=boundary.bid),boundary,self,self.data.viewer)
        self.boundaryItem.appendRow(boundaryItem)

    def ShowAll(self):
        self.data.ShowAll()
    
    def EraseAll(self):
        self.data.EraseAll()

    def Erase(self):        
        self.data.Erase()

    def Display(self, update = False):
        self.data.Display(update)

    def ExportStepFile(self, filePath):
        self.data.ExportStepFile(filePath)
    
    def ExportStepFileSolid(self, filePath):
        self.data.ExportStepFileSolid(filePath)
        
    def GetTransformationMultiplied(self):
        return self.data.GetTransformationMultiplied()    

            

class KooCAEModel:

    def __init__(self, parent, viewer):
        self.ais_geometry_manager = KooAISGeometryManager(parent, viewer)                
        self.ais_boundary_manager = KooAISBoundaryManager(parent, viewer)
        self.viewer = viewer
        self.manipulator = KooAISManipulator()
        self.aisManipulator = None 
        self.refVertex = BRepBuilderAPI_MakeVertex(gp_Pnt(0,0,0)).Vertex()
        self.aisRefVertex = viewer._display.DisplayShape(self.refVertex, update=False)
        self.manipulator.Attach(self.aisRefVertex[0])
        self.manipulator.SetSize(75.0)
        self.treeViewItem = None
        self.Parent = parent

    def AddBoundaryDisplacement(self, shapeList, timeList = [] , dispList = [] ):
        
        boundary = KooAISBoundaryDisplacement(0,shapeList, timeList, dispList)
        self.ais_boundary_manager.AddBoundary(boundary)        
        trsfMultiplied = self.GetTransformationMultiplied()                                     
        boundary.Display(self.viewer, False, trsfMultiplied)                 
        return boundary

    def SetTreeViewItem(self, item):
        self.treeViewItem = item

    def GetPosition(self):
        return self.manipulator.Position()
    
    def AddTransformation(self, trsf):
        ax2 = self.manipulator.Position()
        ax2.Transform(trsf)
        self.manipulator.SetPosition(ax2)

    def SetTransformation(self, trsf):
        self.viewer._display.Context.Erase(self.manipulator, False)
        #self.manipulator = KooAISManipulator()     
        #self.manipulator.Attach(self.aisRefVertex[0])
        self.manipulator.Attach(self.aisRefVertex[0])
        
        self.AddTransformation(trsf)    
        self.Erase()
        self.Display()

    def GetTrsf(self):
        maniPos = self.GetPosition()
        trsX = self.manipulator.locationX
        trsY = self.manipulator.locationY
        trsZ = self.manipulator.locationZ
        rotX = self.manipulator.rotationX
        rotY = self.manipulator.rotationY
        rotZ = self.manipulator.rotationZ
        
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
        return trsf


    def ShowAll(self):   
        self.SetTransformation(self.GetTrsf())                
       

    def EraseAll(self):
        self.viewer._display.Context.Erase(self.manipulator, False)
        self.viewer._display.Context.Erase(self.aisRefVertex[0], False)
        self.Erase()

    def Erase(self):
        self.ais_geometry_manager.EraseAll()
        self.ais_boundary_manager.EraseAll()


    def RemoveGeometry(self, geom):
        self.ais_geometry_manager.RemoveGeometry(geom)    

    def GetTransformationMultiplied(self):
        pnt = self.manipulator.Position().Location()
        #print("Pnt,",pnt.X(),pnt.Y(),pnt.Z())
        trsf = self.manipulator.Transformation()
        trsfTranslate = gp_Trsf()
        trsfTranslate.SetTranslation(gp_Pnt(0,0,0), gp_Pnt(pnt.X(),pnt.Y(),pnt.Z()))
        trsfMultiplied = trsfTranslate.Multiplied(trsf)
        return trsfMultiplied

    def Display(self, update = False):        
        trsfMultiplied = self.GetTransformationMultiplied()                                     
        self.ais_geometry_manager.Display(update,trsfMultiplied)
        self.ais_boundary_manager.Display(update,trsfMultiplied)
        

    def ImportStepFile(self, filePath):
        return self.ais_geometry_manager.ImportStepFile(filePath)

    def ExportStepFile(self, filePath):
        self.ais_geometry_manager.ExportStepFile(filePath)

    def ExportStepFileSolid(self, filePath):
        self.ais_geometry_manager.ExportStepFileSolid(filePath)

