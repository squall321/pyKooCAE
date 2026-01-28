import sys 
import os
import cv2
import numpy as np
import math

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

from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf, gp_Ax1, gp_Pln
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_WIRE, TopAbs_FACE, TopAbs_SOLID, TopAbs_COMPOUND
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepFill import BRepFill_Filling
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeSolid
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell,BRepOffsetAPI_MakeOffsetShape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.Law import Law_Linear, Law_Constant
from OCC.Core.BRepFill import brepfill_Shell
from OCC.Core.TopoDS import TopoDS_Shell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.ChFi2d import ChFi2d_AnaFilletAlgo, ChFi2d_ChamferAPI, ChFi2d_Builder
from OCC.Extend.ShapeFactory import make_wire

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment


from OCC.Core.STEPControl import STEPControl_Reader

from shapely.geometry import Polygon
from KooCAEManager.KooNode import NodeManager, NodeSetManager

if __name__ == "__main__":
    '''
    # package import from Absolute Path
    curPath = os.getcwd() 
    curPath = os.path.join(curPath, "occProject\Generators")
    os.add_dll_directory(curPath)
    # parent directory 
    #parentPath = os.path.abspath(os.path.join(curPath, os.pardir))
    sys.path.append(os.path.dirname(os.path.abspath(curPath)))
    from occProject.Generators.KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH
    '''
else:
    from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH, KooMeshManagerList
    from KooCAEManager.KooPart import KooPartManager, KooPart, KooPartComposite
    from KooCAEManager.KooMaterial import *
    from KooCAEManager.KooSection import *
    

class PackageLayer:
    def __init__(self, name = "", x=0.0, y=0.0, z=0.0, xLength=-1.0, yLength=-1.0, thickness=1.0, secMan : KooSectionManager = None, matMan : KooMaterialManager = None, nSetMan : NodeSetManager = None):
        
        #### geometry properties
        self.name = name
        self.posX = x
        self.posY = y
        self.posZ = z
        self.xLength = xLength
        self.yLength = yLength
        self.thickness = thickness
        self.packageMeshpsid = -1
        self.packageMeshMatID = -1
        self.rotate = 0.0                
        
        #### mesh properties
        self.meshGenerationMode = False
        self.meshPath = os.getcwd()
        self.meshSizeInPlane = 1.0
        self.numberofElementinX = 0 
        self.numberofElementinY = 0 
        self.numberofElementinThickness = 1
        self.meshGenerationType = "Solid"
        self.geomGenerationType = "Solid"
        self.meshType = "Hexa"
        self.maxNID = 0
        self.maxEID = 0 
        self.maxPID = 0 
        self.maxMID = 0 
        self.maxSID = 0     
        self.maxNSID = 0
        ## NodeSet Generation Option
        self.nodeSetOption = []
        ## SegmentSet Generation Option
        self.segmentSetOption = []
        ## TiedContact by NodeSet        
        if secMan is None:
            self.sectionManager = KooSectionManager()
        else:
            self.sectionManager = secMan
        if matMan is None:
            self.materialManager = KooMaterialManager()
        else:
            self.materialManager = matMan
        if nSetMan is None:
            self.nodesetManager = NodeSetManager()
        else:
            self.nodesetManager = nSetMan
            
    def AddNodeSetOption(self, optionLoc, name, nsid, tol):
        self.nodeSetOption.append([optionLoc, name, nsid, tol])
        pass   
    
    def AddSegmentSetOption(self, optionLoc, name, sid, tol,da1=0.0,da2=0.0,da3=0.0,da4=0.0,solver="MECH",its=0):
        self.segmentSetOption.append([optionLoc, name, sid, tol,da1,da2,da3,da4,solver,its])
        pass
    
        
    def SetPosition(self,x,y,z):
        self.posX = x
        self.posY = y
        self.posZ = z
        pass

    def SetLength(self,curpsid,x,y,matID = -1):
        self.packageMeshpsid = curpsid
        self.xLength = x
        self.yLength = y
        self.packageMeshMatID = matID
        pass
    
    def SetRotation(self,angle):
        self.rotate = angle
        pass
    
    def SetThickness(self,thickness):
        self.thickness = thickness
        pass
    
    def GetMaxIDs(self):
        return self.maxNID, self.maxEID, self.maxPID, self.maxSID, self.maxMID, self.maxNSID

    def SetMaxIDs(self,maxNID,maxEID,maxPID,maxSID=0, maxMID=0,maxNSID=0):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID
        self.maxSID = maxSID
        self.maxMID = maxMID
        self.maxNSID = maxNSID
    
    def SetMeshPath(self,meshPath):
        self.meshGenerationMode = True
        self.meshPath = os.getcwd() + "\\" + meshPath
        pass

    def SetMeshGenerationType(self,meshGenerationType):
        self.meshGenerationMode = True
        self.meshGenerationType = meshGenerationType
        pass    

    def SetGeomGenerationType(self,geomGenerationType):
        self.geomGenerationType = geomGenerationType

    def SetMeshType(self,meshType):
        self.meshGenerationMode = True
        self.meshType = meshType
        pass

    def SetMeshSizeInPlane(self,meshSizeInPlane):
        self.meshGenerationMode = True
        self.meshSizeInPlane = meshSizeInPlane
        pass

    def SetNumberofElementinXDirection(self, numXDir):
        self.numberofElementinX = numXDir
    
    def SetNumberofElementinYDirection(self, numYDir):
        self.numberofElementinY = numYDir

    def SetNumberofElementinThickness(self,numberofElementinThickness):
        self.meshGenerationMode = True
        self.numberofElementinThickness = numberofElementinThickness
        pass

class PackageLayerDefined(PackageLayer):
    def __init__(self,name="",x=0.0,y=0.0,z=0.0,xLength=-1.0,yLength=-1.0,thickness=1.0, secMan : KooSectionManager = None, matMan : KooMaterialManager = None, nSetMan : NodeSetManager = None):
        super(PackageLayerDefined,self).__init__(name,x,y,z,xLength,yLength,thickness,secMan,matMan,nSetMan)

        self.cylinderpsidList = []
        self.boxpsidList = []
        self.boxCrackpsidList = [] 
        self.rectangleTubepsidList = []
        self.rectangleCircleCutpsidList = []
        self.rectangleFilletCutpsidList = []
        self.imagepsidList = []
        self.stlFilepsidList = []
        self.stepFilepsidList = []
        self.mshpsidList = []
        self.detailSolderpsidList = []
        self.polynomialPartpsidList = []
        self.polynomialCutPartpsidList = []
        self.polynomialSweeppsidList = []
        self.shieldCanpsidList = []
        
        self.cylinderMeshpsidList = []
        self.boxMeshpsidList = []
        self.boxCrackMeshpsidList = []
        self.rectangleTubeMeshpsidList = []
        self.rectangleCircleCutMeshpsidList = []
        self.rectangleFilletCutMeshpsidList = []
        self.imageMeshpsidList = []
        self.stlFileMeshpsidList = []
        self.stepFileMeshpsidList = []
        self.mshMeshpsidList = []
        self.detailSolderMeshpsidList = []
        self.polynomialPartMeshpsidList = []
        self.polynomialCutPartMeshpsidList = []
        self.polynomialSweepMeshpsidList = []
        self.shieldCanMeshpsidList = []

        self.cylinderList = []         
        self.boxList = []        
        self.boxCrackList = []
        self.rectangleTubeList = []         
        self.rectangleCircleCutList = []
        self.rectangleFilletCutList = []
        self.imageList = []
        self.stlFileList = []
        self.stepFileList = []
        self.mshFileList = [] 
        self.detailSolderList = [] 
        self.polynomialPartList = []
        self.polynomialCutPartList = [] 
        self.polynomialSweepList = []
        self.shieldCanList = []

        self.cylinderShapeList = []        
        self.boxShapeList = []        
        self.boxCrackShapeList = []
        self.rectangleTubeShapeList = []
        self.rectangleCircleCutShapeList = []
        self.rectangleFilletCutShapeList = [] 
        self.imageShapeList = [] 
        self.stlShapeList = []
        self.stepShapeList = []
        self.mshShapeList = []
        self.detailSolderShapeList = []             
        self.detailPolynomialPartShapeList = [] 
        self.detailPolynomialCutPartShapeList = []
        self.polynomialSweepShapeList = []
        self.shieldCanShapeList = [] 

        self.cylinderMeshList = [] 
        self.boxMeshList = []
        self.boxCrackMeshList = []
        self.rectangleTubeMeshList = []
        self.rectangleCircleCutMeshList = []
        self.rectangleFilletCutMeshList = []
        self.imageMeshList = []   
        self.stlMeshList = []
        self.stepMeshList = []
        self.mshMeshList = []                     
        self.detailSolderMeshList = []
        self.polynomialPartMeshList = []
        self.polynomialCutPartMeshList = []
        self.polynomialSweepMeshList = []     
        self.shieldCanMeshList = []   
        self.packageMesh = None

        self.cylinderMeshMatIDList = [] 
        self.boxMeshMatIDList = []
        self.boxCrackMeshMatIDList = []
        self.rectangleTubeMeshMatIDList = []
        self.rectangleCircleCutMeshMatIDList = []
        self.rectangleFilletCutMeshMatIDList = []
        self.imageMeshMatIDList = []
        self.detailSolderMeshMatIDList = []
        self.polynomialPartMeshMatIDList = []
        self.polynomialCutPartMeshMatIDList = []
        self.polynomialSweepMeshMatIDList = []
        self.shieldCanMeshMatIDList = []
                        
        self.shape = None 

        self.ith = 1                 
    
    def AddCylinder(self,curpsid, x,y,r,matID=-1,compMatIDList = [], compThicknessList = [], compBList = []):
        self.cylinderpsidList.append(curpsid)
        self.cylinderList.append([x,y,r,matID,compMatIDList,compThicknessList,compBList])
        pass
    
    def AddBox(self,curpsid, x,y,xLength,yLength,matID=-1,compMatIDList = [], compThicknessList = [], compBList = [], numElemforEachLayer = -1, compositeOptionList = [], compositeMeshrefinementSizeLlist = [], compositeMeshrefinementLocationXList = [], compositeMehrefinementLocationYList = [], compositeModeList=[]):
        self.boxpsidList.append(curpsid)
        self.boxList.append([x,y,xLength,yLength,matID,compMatIDList,compThicknessList, compBList, numElemforEachLayer, compositeOptionList, compositeMeshrefinementSizeLlist, compositeMeshrefinementLocationXList, compositeMehrefinementLocationYList,compositeModeList])
        pass

    def AddBoxCrack(self,curpsid,x,y,xLength,yLength,crackList,matID=-1):
        self.boxCrackpsidList.append(curpsid)
        self.boxCrackList.append([x,y,xLength,yLength,crackList,matID])
        pass

    def AddRectangleTube(self, curpsid, x, y, xLength, yLength, thickness, matID=-1,compMatIDList = [], compThicknessList = [], compBList = []):
        self.rectangleTubepsidList.append(curpsid)
        self.rectangleTubeList.append([x,y,xLength,yLength,thickness,matID,compMatIDList,compThicknessList,compBList])
        pass

    def AddRectangleCircleCut(self,curpsid, x, y, xLength, yLength, cutX, cutY, cutR, matID=-1,compMatIDList = [], compThicknessList = [], compBList = []):
        self.rectangleCircleCutpsidList.append(curpsid)
        self.rectangleCircleCutList.append([x,y,xLength,yLength,cutX,cutY,cutR,matID,compMatIDList,compThicknessList, compBList])
        pass

    def AddRectangleFilletCut(self, curpsid, x, y, xLength, yLength, cutList, matID=-1,compMatIDList = [], compThicknessList = [], compBList = []):
        self.rectangleFilletCutpsidList.append(curpsid)
        self.rectangleFilletCutList.append([x,y,xLength,yLength,cutList,matID,compMatIDList,compThicknessList, compBList])
        pass

    def AddImage(self, curpsid, xLength, yLength, imageFileName,cutShapeOption,matID=-1):
        self.imagepsidList.append(curpsid)
        self.imageList.append([xLength,yLength,imageFileName,cutShapeOption,matID])
        pass
    
    def AddSTLFileName(self,curpsid, x, y, stlFileName, scaleX=1.0, scaleY=1.0, scaleZ=1.0, matID=-1):
        self.stlFilepsidList.append(curpsid)
        self.stlFileList.append([x,y,stlFileName,scaleX,scaleY,scaleZ,matID])
        
    def AddStepFileName(self,curpsid, x, y, stepFileName, scaleX=1.0, scaleY=1.0, scaleZ=1.0, matID=-1):
        self.stepFilepsidList.append(curpsid)
        self.stepFileList.append([x,y,stepFileName,scaleX,scaleY,scaleZ,matID])
    
    def AddMSHFileName(self,curpsid, x, y, mshFileName, matID=-1, scaleX=1.0, scaleY=1.0, scaleZ=1.0):
        self.mshpsidList.append(curpsid)
        self.mshFileList.append([x,y,mshFileName,matID,scaleX,scaleY,scaleZ])
    
    def AddDetailSolderShape(self, curpsid, x,y,points,matID=-1):
        self.detailSolderpsidList.append(curpsid)
        self.detailSolderList.append([x,y,points,matID])
        pass

    def AddPolynomialPart(self, curpsid, xList, yList, matID=-1,compMatIDList = [], compThicknessList = [], compBList = []):
        self.polynomialPartpsidList.append(curpsid)
        self.polynomialPartList.append([xList,yList,matID,compMatIDList,compThicknessList, compBList])
        pass

    def AddPolynomialCutPart(self, curpsid, xList, yList, xCutMatrix, yCutMatrix,generateInternalOption,matID=-1,matCutID = -1, compMatIDList = [], compThicknessList = [], compBList = []):
        self.polynomialCutPartpsidList.append(curpsid)
        self.polynomialCutPartList.append([xList,yList,xCutMatrix,yCutMatrix,generateInternalOption,matID,matCutID,compMatIDList,compThicknessList, compBList])
        pass

    def AddPolynomialSweep(self, curpsid, xBottomList, yBottomList, xTopList, yTopList, matID=-1):
        self.polynomialSweeppsidList.append(curpsid)
        self.polynomialSweepList.append([xBottomList,yBottomList,xTopList,yTopList,matID])
        pass

    def AddShieldCan(self, curpsid, xList, yList, radius,solidThickness,padWidth,offset, xListCut,yListCut, matID=-1, detailMode = False):
        self.shieldCanpsidList.append(curpsid)
        self.shieldCanList.append([xList,yList,radius,solidThickness, padWidth, offset, xListCut, yListCut, matID, detailMode])
        pass

    def GenerateCylinderShapes(self):
        self.cylinderShapeList = [] 
        curi = 0 
        for cylinder in self.cylinderList:
            curpsid = self.cylinderpsidList[curi]
            curi = curi + 1
            x = cylinder[0] + self.posX
            y = cylinder[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            r = cylinder[2]
            thickness = self.thickness

            matID = cylinder[3]

            center = gp_Pnt(x,y,z)
            normal = gp_Dir(0,0,1)
            circle_geom = gp_Circ(gp_Ax2(center,normal),r)
            circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
            circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
            circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
            if self.meshGenerationMode and self.meshType != "Tetra":
                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(self.meshPath)
                meshManager.SetName("{0}_CylinderMesh{1}".format(self.name,self.ith))
                
                self.ith += 1
                if self.meshType == "Hexa":
                    meshManager.mesh_shape_extrude_3D(circle_face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],11,self.maxNID,self.maxEID)
                #elif self.meshType == "Tetra":
                #    meshManager.mesh_shape_extrude_3D(circle_face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],2,self.maxNID,self.maxEID)
                elif self.meshType == "Quad":
                    meshManager.mesh_shape_quad_2D(circle_face,self.meshSizeInPlane,self.maxNID,self.maxEID,self.thickness)
                elif self.meshType == "Tri":
                    meshManager.mesh_shape_tri_2D(circle_face,self.meshSizeInPlane,self.maxNID,self.maxEID,self.thickness)
                if self.meshType != "Tetra":
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialbyID(self.materialManager,matID)

                
                
            cylinder_shape = BRepPrimAPI_MakePrism(circle_face,gp_Vec(0,0,thickness)).Shape()
            self.cylinderShapeList.append(cylinder_shape)
            if self.meshGenerationMode:                
                if  self.meshType == "Tetra":
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.mesh_shape(cylinder_shape,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialbyID(self.materialManager,matID)
                self.cylinderMeshList.append(meshManager)
                self.cylinderMeshpsidList.append(curpsid)

    def GenerateSTLShape(self):
        self.stlShapeList = []
        curi = 0 
        for stl in self.stlFileList:
            curpsid = self.stlFilepsidList[curi]
            curi = curi + 1
            x = stl[0] + self.posX
            y = stl[1] + self.posY
            z = self.posZ
            stlFileName = stl[2]
            scaleX = stl[3]
            scaleY = stl[4]
            scaleZ = stl[5]
            matID = stl[6]
            meshsize = self.meshSizeInPlane
            meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
            meshManager.SetPath(os.getcwd())    
            curname = stlFileName.replace(".stl","")
            meshManager.SetName("{0}_STLMesh{1}".format(curname,curi))
            if self.meshGenerationMode:
                meshManager.mesh_shape_from_stl(stlFileName,meshsize,10.0*meshsize,10, self.maxNID, self.maxEID) 
                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                meshManager.part.SetID(self.maxPID)
                if matID != -1:
                    meshManager.part.SetMaterialID(matID)
                self.stlMeshList.append(meshManager)
                self.stlFileMeshpsidList.append(curpsid)
                meshManager.part.elementManager.Scaling(scaleX,scaleY,scaleZ) 
                meshManager.part.elementManager.Translate(stl[0],stl[1],0)      

    def GenerateStepShape(self):
        self.stepShapeList = []
        curi = 0 
        for step in self.stepFileList:
            curpsid = self.stepFilepsidList[curi]
            curi = curi + 1
            x = step[0] + self.posX
            y = step[1] + self.posY
            z = self.posZ
            delX = step[3]
            delY = step[4]
            delZ = step[5]
            stepFileName = step[2]
            matID = step[6]
            
            # step reader
            step_reader = STEPControl_Reader()
            step_reader.ReadFile(stepFileName)
            step_reader.TransferRoots()
            num_shapes = step_reader.NbShapes()
            # transform by x, y, z and scale as delX, delY, delZ
            '''moveTrsf = gp_Trsf()
            scaleTrsf = gp_Trsf()
            
            moveTrsf.SetTranslation(gp_Vec(x,y,z))
            
            print("scaling transformation is only for isotropic scaling") 
                
            # SetValues 사용하여 개별 축 방향으로 스케일링 설정
            scaleTrsf.SetValues(
            delX, 0, 0, 0,
            0, delY, 0, 0,
            0, 0, delZ, 0
            )  
            #apply scale and then move 
            trsf = gp_Trsf()
            trsf.Multiply(moveTrsf)
            trsf.Multiply(scaleTrsf)'''
            for i in range(1, num_shapes + 1):
                shape = step_reader.Shape(i)
                #shape = BRepBuilderAPI_Transform(shape,trsf).Shape()
                self.stepShapeList.append(shape)
                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(os.getcwd())
                curname = stepFileName.replace(".step","")
                curname = curname.replace(".stp","")
                meshManager.SetName("{0}_STPMesh{1}".format(curname,i))
                
                if self.meshGenerationMode:
                    meshManager.mesh_shape(shape,self.meshSizeInPlane, self.meshSizeInPlane, 3, None, self.maxNID, self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.stepMeshList.append(meshManager)
                    self.stepFileMeshpsidList.append(curpsid)
                    meshManager.part.elementManager.Scaling(delX,delY,delZ) 
                    meshManager.part.elementManager.Translate(step[0],step[1],0)   
                    
                pass
                                            
                

    def GenerateGMSHShape(self):
        self.mshShapeList = [] 
        curi = 0 
        for msh in self.mshFileList:
            curpsid = self.mshpsidList[curi]
            curi = curi + 1
            delX = msh[0] + self.posX
            delY = msh[1] + self.posY
            delZ = self.posZ
            mshFileName = msh[2]
            matID = msh[3]
            scaleX = msh[4]
            scaleY = msh[5]
            scaleZ = msh[6]
            meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
            meshManager.SetPath(os.getcwd())
            meshManager.SetName("{0}_MSHMesh{1}".format(self.name,self.ith))
            shape = meshManager.ImportMSHFile(mshFileName,self.maxNID,self.maxEID,delX,delY,delZ,scaleX,scaleY,scaleZ)
            
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(matID)
            
            self.mshShapeList.append(shape)
            self.mshMeshList.append(meshManager)
            self.mshMeshpsidList.append(curpsid)
            
            
            
            
            print("mshFileName",mshFileName)
        pass

    def GenerateBoxShape(self):
        self.boxShapeList = [] 
        curi = 0 
        for box in self.boxList:
            curpsid = self.boxpsidList[curi]
            curi = curi + 1
            x = box[0] + self.posX
            y = box[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            xLength = box[2]
            yLength = box[3]
            matID = box[4]
            thickness = self.thickness            
            rectangle_box_wire = BRepBuilderAPI_MakePolygon()
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_face = BRepBuilderAPI_MakeFace(rectangle_box_wire.Wire()).Face()
            if len(box[11])>0:
                numElemforEachLayer = box[8]
                meshSizeBig = self.meshSizeInPlane
                compMatIDList = box[5]
                compThicknessList = box[6]
                compBList = box[7]
                compOptionList = box[9]
                compMeshrefinementSizeList = box[10]
                compMeshrefinementLocationXList = box[11]
                compMeshrefinementLocationYList = box[12]
                compModeList = box[13]
                for i in range(len(compThicknessList)):
                    curThickness = compThicknessList[i]
                    box_shape = BRepPrimAPI_MakeBox(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z),xLength,yLength,curThickness).Shape()
                    self.boxShapeList.append(box_shape)
                    z = z + curThickness
                z = self.posZ
                if self.meshGenerationMode:
                    for i in range(len(compThicknessList)):
                        curMatID = compMatIDList[i]
                        curThickness = compThicknessList[i]
                        curB = compBList[i]
                        curOption = compOptionList[i]
                        if len(curOption) > 0:
                            curEOS = curOption[0]
                        else:
                            curEOS = 0
                        if len(curOption) > 1:
                            curELFORM = curOption[1]
                        else:
                            curELFORM = -99
                            
                        curMeshSizeSmall = compMeshrefinementSizeList[i]
                        curMeshLocationX = compMeshrefinementLocationXList[i]
                        curMeshLocationY = compMeshrefinementLocationYList[i]
                        curMode = compModeList[i]
                        
                        pt1 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z)
                        pt2 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z)
                        pt3 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z)
                        pt4 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z)
                        ptList = [pt1,pt2,pt3,pt4]

                        meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                        meshManager.SetPath(self.meshPath)
                        meshManager.SetName("{0}_BoxMesh{1}_{2}".format(self.name,self.ith,i))
                        if curMeshSizeSmall == 0.0:
                            curMeshSizeSmall = meshSizeBig
                        meshManager.mesh_shape_extrude_3D_polygon_refine(ptList,curThickness,numElemforEachLayer, meshSizeBig, curMeshSizeSmall, curMeshLocationX, curMeshLocationY, self.maxNID, self.maxEID, curMode)
                        if curEOS != 0:
                            meshManager.part.SetEOSID(curEOS)
                        if "FEM" in curMode: 
                            if curELFORM != -99:
                                meshManager.section.SetElform(curELFORM)
                        if "PERI" in curMode or "Peridynamics" in curMode:
                            meshManager.part.SetAsPeridynamics()                            
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        meshManager.part.SetMaterialID(curMatID)
                        
                        
                        self.boxMeshList.append(meshManager)
                        self.boxMeshpsidList.append(curpsid)    
                        z = z + curThickness
                self.ith += 1

            elif box[8] != -1:
                numElemforEachLayer = box[8]
                meshSize = self.meshSizeInPlane
                pt1 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z)
                pt2 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z)
                pt3 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z)
                pt4 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z)
                pt5 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z+thickness)
                pt6 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z+thickness)
                pt7 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z+thickness)
                pt8 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z+thickness)
                ptList = [pt1,pt2,pt3,pt4,pt5,pt6,pt7,pt8]
                compMatIDList = box[5]
                compThicknessList = box[6]
                compBList = box[7]
                compEOSList = box[9]
                for i in range(len(compThicknessList)):
                    curThickness = compThicknessList[i]
                    box_shape = BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),xLength,yLength,curThickness).Shape()
                    self.boxShapeList.append(box_shape)
                    z = z + curThickness   
                z = self.posZ 
                if self.meshGenerationMode:
                    meshManagerList : KooMeshManagerList = KooMeshManagerList()     
                    meshManagerList.SetPath(self.meshPath)
                    meshManagerList.SetName("{0}_BoxMesh{1}".format(self.name,self.ith))
                    
                    meshManagerList.GenerateStructuredMesh(ptList, meshSize, numElemforEachLayer, compThicknessList, compMatIDList, compEOSList, self.maxNID, self.maxEID, self.maxPID, self.sectionManager, self.nodesetManager)
                    self.maxNID, self.maxEID = meshManagerList.GetMaxIDs()
                    for meshManager in meshManagerList.meshManagerList:
                        self.boxMeshList.append(meshManager)
                        self.boxMeshpsidList.append(curpsid)
                    self.ith += 1
            elif box[8] != -1:
                numElemforEachLayer = box[8]
                meshSize = self.meshSizeInPlane
                pt1 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z)
                pt2 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z)
                pt3 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z)
                pt4 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z)
                pt5 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z+thickness)
                pt6 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z+thickness)
                pt7 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z+thickness)
                pt8 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z+thickness)
                
                #ptList = [pt1,pt2,pt3,pt4,pt5,pt6,pt7,pt8]
                compMatIDList = box[5]
                compThicknessList = box[6]
                compBList = box[7]
                numComp = len(compThicknessList)
                for i in range(len(compThicknessList)):
                    curThickness = compThicknessList[i]
                    box_shape = BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),xLength,yLength,curThickness).Shape()
                    self.boxShapeList.append(box_shape)
                    z = z + curThickness    
                z = self.posZ
                if self.meshGenerationMode:
                    for i in range(numComp):
                        #interpolation between pt1 and pt5
                        curPt1 : gp_Pnt = gp_Pnt((pt1.X()*(numComp-i) + pt5.X()*i)/numComp, (pt1.Y()*(numComp-i) + pt5.Y()*i)/numComp, (pt1.Z()*(numComp-i) + pt5.Z()*i)/numComp)
                        curPt2 : gp_Pnt = gp_Pnt((pt2.X()*(numComp-i) + pt6.X()*i)/numComp, (pt2.Y()*(numComp-i) + pt6.Y()*i)/numComp, (pt2.Z()*(numComp-i) + pt6.Z()*i)/numComp)
                        curPt3 : gp_Pnt = gp_Pnt((pt3.X()*(numComp-i) + pt7.X()*i)/numComp, (pt3.Y()*(numComp-i) + pt7.Y()*i)/numComp, (pt3.Z()*(numComp-i) + pt7.Z()*i)/numComp)
                        curPt4 : gp_Pnt = gp_Pnt((pt4.X()*(numComp-i) + pt8.X()*i)/numComp, (pt4.Y()*(numComp-i) + pt8.Y()*i)/numComp, (pt4.Z()*(numComp-i) + pt8.Z()*i)/numComp)
                        curPt5 : gp_Pnt = gp_Pnt((pt1.X()*(numComp-i-1) + pt5.X()*(i+1))/(numComp), (pt1.Y()*(numComp-i-1) + pt5.Y()*(i+1))/(numComp), (pt1.Z()*(numComp-i-1) + pt5.Z()*(i+1))/(numComp)) 
                        curPt6 : gp_Pnt = gp_Pnt((pt2.X()*(numComp-i-1) + pt6.X()*(i+1))/(numComp), (pt2.Y()*(numComp-i-1) + pt6.Y()*(i+1))/(numComp), (pt2.Z()*(numComp-i-1) + pt6.Z()*(i+1))/(numComp))
                        curPt7 : gp_Pnt = gp_Pnt((pt3.X()*(numComp-i-1) + pt7.X()*(i+1))/(numComp), (pt3.Y()*(numComp-i-1) + pt7.Y()*(i+1))/(numComp), (pt3.Z()*(numComp-i-1) + pt7.Z()*(i+1))/(numComp))
                        curPt8 : gp_Pnt = gp_Pnt((pt4.X()*(numComp-i-1) + pt8.X()*(i+1))/(numComp), (pt4.Y()*(numComp-i-1) + pt8.Y()*(i+1))/(numComp), (pt4.Z()*(numComp-i-1) + pt8.Z()*(i+1))/(numComp))
                        curPtList = [curPt1,curPt2,curPt3,curPt4,curPt5,curPt6,curPt7,curPt8]
                        meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                        meshManager.SetPath(self.meshPath)
                        meshManager.SetName("{0}_BoxMesh{1}_{2}".format(self.name,self.ith,i))                        
                        if self.numberofElementinX != 0 and self.numberofElementinY != 0:
                            meshManager.GenerateStructuredMeshbyNumberofElement(curPtList, self.numberofElementinX, self.numberofElementinY, numElemforEachLayer, self.maxNID, self.maxEID)
                        else:
                            meshManager.GenerateStructuredMesh(curPtList, meshSize, numElemforEachLayer, self.maxNID, self.maxEID)
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)
                        self.boxMeshList.append(meshManager)
                        self.boxMeshpsidList.append(curpsid)
                self.ith += 1

            else:
                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_BoxMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    #meshManager.mesh_shape_extrude_3D(rectangle_face,self.meshSizeInPlane,self.numberofElementinThickness)
                    if self.meshType == "Hexa":
                        
                        if self.numberofElementinX != 0 and self.numberofElementinY != 0:
                            pt1 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z)
                            pt2 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z)
                            pt3 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z)
                            pt4 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z)
                            pt5 = gp_Pnt(x-xLength/2.0,y-yLength/2.0,z+thickness)
                            pt6 = gp_Pnt(x+xLength/2.0,y-yLength/2.0,z+thickness)
                            pt7 = gp_Pnt(x+xLength/2.0,y+yLength/2.0,z+thickness)
                            pt8 = gp_Pnt(x-xLength/2.0,y+yLength/2.0,z+thickness)
                            ptList = [pt1,pt2,pt3,pt4,pt5,pt6,pt7,pt8]
                            meshManager.GenerateStructuredMeshbyNumberofElement(ptList,self.numberofElementinX, self.numberofElementinY, self.numberofElementinThickness, self.maxNID, self.maxEID)
                            
                            pass
                        else:
                            meshManager.mesh_shape_extrude_3D(rectangle_face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],11,self.maxNID,self.maxEID)                
                    elif self.meshType == "Quad":
                        meshManager.mesh_shape_quad_2D(rectangle_face,self.meshSizeInPlane,self.maxNID,self.maxEID,self.thickness)
                    elif self.meshType == "Tri":
                        meshManager.mesh_shape_tri_2D(rectangle_face,self.meshSizeInPlane,self.maxNID,self.maxEID,self.thickness)                
                    
                    if self.meshType != "Tetra":
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        if len(box) > 5:
                            if len(box[5]) > 0:
                                compMatIDList = box[5]
                                if len(box) > 6:
                                    compThicknessList = box[6]                    
                                    if len(box) > 7:
                                        compBList = box[7]
                                    else:
                                        compBList = []
                                    meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)

                box_shape = BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),xLength,yLength,thickness).Shape()
                if "Shell" in self.geomGenerationType:
                    self.boxShapeList.append(rectangle_face)
                else:
                    self.boxShapeList.append(box_shape)

                if self.meshGenerationMode:
                    if self.meshType == "Tetra":
                        meshManager.mesh_shape(box_shape,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)
                    self.boxMeshList.append(meshManager)
                    self.boxMeshpsidList.append(curpsid)

    def GenerateBoxCrackShape(self):
        self.boxCrackShapeList = []
        i = 0 
        for boxCrack in self.boxCrackList:
            curpsid = self.boxCrackpsidList[i]
            i = i + 1
            x = boxCrack[0] + self.posX
            y = boxCrack[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            xLength = boxCrack[2]
            yLength = boxCrack[3]
            thickness = self.thickness
            crackList = boxCrack[4]
            matID = boxCrack[5]
            rectangle_box_wire = BRepBuilderAPI_MakePolygon()
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_face = BRepBuilderAPI_MakeFace(rectangle_box_wire.Wire()).Face()
            box_shape = BRepPrimAPI_MakePrism(rectangle_face,gp_Vec(0,0,thickness)).Shape()

            cutShapeList = []
            L1 = TopTools_ListOfShape()
            L1.Append(box_shape)
            L2 = TopTools_ListOfShape()
            for crack in crackList:
                if crack[0] == "VCrack":
                    crackOriginX = crack[1]
                    crackOriginY = crack[2]
                    crackAngle = crack[3]
                    crackWidth = crack[4]
                    crackHeight = crack[5]
                    crackLength = crack[6]

                    crackRadianAngle = crackAngle*np.pi/180.0
                    crackLengthDirection = gp_Vec(np.cos(crackRadianAngle),np.sin(crackRadianAngle),0)
                    crackWidthDirection = gp_Vec(-np.sin(crackRadianAngle),np.cos(crackRadianAngle),0)
                    x1 = self.posX + crackOriginX - crackLength/2.0*crackLengthDirection.X()
                    y1 = self.posY + crackOriginY - crackLength/2.0*crackLengthDirection.Y()
                    z1 = z - crackHeight + thickness
                    x2 = x1 + crackWidth/2.0*crackWidthDirection.X()
                    y2 = y1 + crackWidth/2.0*crackWidthDirection.Y()
                    z2 = z + thickness
                    x3 = x1 - crackWidth/2.0*crackWidthDirection.X()
                    y3 = y1 - crackWidth/2.0*crackWidthDirection.Y()
                    z3 = z + thickness
                    crackWire = BRepBuilderAPI_MakePolygon()
                    crackWire.Add(gp_Pnt(x1,y1,z1))
                    crackWire.Add(gp_Pnt(x2,y2,z2))
                    crackWire.Add(gp_Pnt(x3,y3,z3))
                    crackWire.Add(gp_Pnt(x1,y1,z1))
                    crackFace = BRepBuilderAPI_MakeFace(crackWire.Wire()).Face()
                    crackSolid = BRepPrimAPI_MakePrism(crackFace,crackLengthDirection*crackLength).Shape()
                    cutShapeList.append(crackSolid)
                    L2.Append(crackSolid)
            cut = BRepAlgoAPI_Cut()
            cut.SetArguments(L1)
            cut.SetTools(L2)
            cut.SetRunParallel(True)
            cut.SetFuzzyValue(0.0000001)
            cut.Build()
            if cut.Shape() == None:
                print("Cut Failed")
            else:
                print("Cut Success")
                shape = cut.Shape()
            
            self.boxCrackShapeList.append(shape)
            if self.meshGenerationMode:
                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(self.meshPath)
                meshManager.SetName("{0}_BoxCrackMesh{1}".format(self.name,self.ith))
                self.ith += 1
                meshAlgo="auto"
                meshManager.mesh_shape(shape,self.meshSizeInPlane*0.05,self.meshSizeInPlane,3,meshAlgo,self.maxNID,self.maxEID)
                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                meshManager.part.SetID(self.maxPID)
                if matID != -1:
                    meshManager.part.SetMaterialID(matID)
                self.boxCrackMeshList.append(meshManager)
                self.boxCrackMeshpsidList.append(curpsid)

    def GenerateRectangleTubeShape(self):
        self.rectangleTubeShapeList = [] 
        curi = 0 
        for rectangleTube in self.rectangleTubeList:   
            curpsid = self.rectangleTubepsidList[curi]
            curi = curi + 1
            x = rectangleTube[0] + self.posX
            y = rectangleTube[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            xLength = rectangleTube[2]
            yLength = rectangleTube[3]
            thickness = rectangleTube[4]
            matID = rectangleTube[5]

            if self.geomGenerationType == "Solid": 
                rectangleTube_wire = BRepBuilderAPI_MakePolygon()
                rectangleTube_wire.Add(gp_Pnt(x-xLength/2.0-thickness/2.0,y-yLength/2.0-thickness/2.0,z))
                rectangleTube_wire.Add(gp_Pnt(x+xLength/2.0+thickness/2.0,y-yLength/2.0-thickness/2.0,z))
                rectangleTube_wire.Add(gp_Pnt(x+xLength/2.0+thickness/2.0,y+yLength/2.0+thickness/2.0,z))
                rectangleTube_wire.Add(gp_Pnt(x-xLength/2.0-thickness/2.0,y+yLength/2.0+thickness/2.0,z))
                rectangleTube_wire.Add(gp_Pnt(x-xLength/2.0-thickness/2.0,y-yLength/2.0-thickness/2.0,z))
                rectangleTube_face = BRepBuilderAPI_MakeFace(rectangleTube_wire.Wire()).Face()
                rectangleTube_inner_wire = BRepBuilderAPI_MakePolygon()
                rectangleTube_inner_wire.Add(gp_Pnt(x-xLength/2.0+thickness,y-yLength/2.0+thickness,z))
                rectangleTube_inner_wire.Add(gp_Pnt(x+xLength/2.0-thickness,y-yLength/2.0+thickness,z))
                rectangleTube_inner_wire.Add(gp_Pnt(x+xLength/2.0-thickness,y+yLength/2.0-thickness,z))
                rectangleTube_inner_wire.Add(gp_Pnt(x-xLength/2.0+thickness,y+yLength/2.0-thickness,z))
                rectangleTube_inner_wire.Add(gp_Pnt(x-xLength/2.0+thickness,y-yLength/2.0+thickness,z))
                rectangleTube_inner_face = BRepBuilderAPI_MakeFace(rectangleTube_inner_wire.Wire()).Face()
                rectangleTube_face = BRepAlgoAPI_Cut(rectangleTube_face,rectangleTube_inner_face).Shape()
                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManage, nodeSetMan=self.nodesetManagerr)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleTubeMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    #meshManager.mesh_shape_extrude_3D(rectangleTube_face,self.meshSizeInPlane,self.numberofElementinThickness)
                    if self.meshType == "Hexa":
                        meshManager.mesh_shape_extrude_3D(rectangleTube_face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],11,self.maxNID,self.maxEID)                
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)
                        self.rectangleTubeMeshList.append(meshManager)
                        self.rectangleTubeMeshpsidList.append(curpsid)
                rectangleTube_shape = BRepPrimAPI_MakePrism(rectangleTube_face,gp_Vec(0,0,self.thickness)).Shape()
                self.rectangleTubeShapeList.append(rectangleTube_shape)
                if self.meshGenerationMode:
                    if self.meshType == "Tetra":
                        meshManager.mesh_shape(rectangleTube_shape,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)
                        self.rectangleTubeMeshList.append(meshManager)
                        self.rectangleTubeMeshpsidList.append(curpsid)
            else:
                points = [gp_Pnt(x-xLength/2.0,y-yLength/2.0,z),gp_Pnt(x+xLength/2.0,y-yLength/2.0,z),gp_Pnt(x+xLength/2.0,y+yLength/2.0,z),gp_Pnt(x-xLength/2.0,y+yLength/2.0,z),gp_Pnt(x-xLength/2.0,y-yLength/2.0,z)]
                polygon = BRepBuilderAPI_MakePolygon()
                for point in points:
                    polygon.Add(point)
                wire = polygon.Wire()
                direction = BRepBuilderAPI_MakeEdge(gp_Pnt(x,y,z),gp_Pnt(x,y,z+self.thickness)).Edge()
                directionWire = BRepBuilderAPI_MakeWire(direction).Wire()
                pipe_shell_maker = BRepOffsetAPI_MakePipeShell(directionWire)
                law_f = Law_Constant()
                law_f.Set(1.0,1.0,1.0)
                pipe_shell_maker.SetLaw(wire, law_f, False, True)
                shape = pipe_shell_maker.Shape()


                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleTubeMesh{1}".format(self.name,self.ith))
                    self.ith += 1                    
                    meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,2,None,self.maxNID,self.maxEID,thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()

                    if len(rectangleTube) > 6:
                        if len(rectangleTube[6]) > 0:
                            compMatIDList = rectangleTube[6]
                            if len(rectangleTube) > 7:
                                compThicknessList = rectangleTube[7]
                                if len(rectangleTube) > 8:
                                    compBList = rectangleTube[8]
                                else:
                                    compBList = []
                                meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.rectangleTubeMeshList.append(meshManager)  
                    self.rectangleTubeMeshpsidList.append(curpsid)                  
                self.rectangleTubeShapeList.append(shape)

    def GenerateRectangleCircleCutShape(self):
        self.rectangleCircleCutShapeList = []
        curi = 0
        for rectangleCircleCut in self.rectangleCircleCutList:
            curpsid = self.rectangleCircleCutpsidList[curi]
            curi = curi + 1
            x = rectangleCircleCut[0] + self.posX
            y = rectangleCircleCut[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            xLength = rectangleCircleCut[2]
            yLength = rectangleCircleCut[3]
            circleCenterX = rectangleCircleCut[4]
            circleCenterY = rectangleCircleCut[5]
            circleRadius = rectangleCircleCut[6]
            matID = rectangleCircleCut[7]
            
            rectangleCircleCut = BRepBuilderAPI_MakePolygon()
            rectangleCircleCut.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangleCircleCut.Add(gp_Pnt(x+xLength/2.0,y-yLength/2.0,z))
            rectangleCircleCut.Add(gp_Pnt(x+xLength/2.0,y+yLength/2.0,z))
            rectangleCircleCut.Add(gp_Pnt(x-xLength/2.0,y+yLength/2.0,z))
            rectangleCircleCut.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangleCircleCut_face = BRepBuilderAPI_MakeFace(rectangleCircleCut.Wire()).Face()
            normal_vector = gp_Dir(0,0,1)
            circle_geom = gp_Circ(gp_Ax2(gp_Pnt(circleCenterX,circleCenterY,z),normal_vector),circleRadius)
            circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
            circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
            circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
            rectangleCircleCut_face = BRepAlgoAPI_Cut(rectangleCircleCut_face,circle_face).Shape()
                        
            if self.geomGenerationType == "Solid":
                rectangleCircleCut_solid = BRepPrimAPI_MakePrism(rectangleCircleCut_face,gp_Vec(0,0,self.thickness)).Shape()
                self.rectangleCircleCutShapeList.append(rectangleCircleCut_solid)
            else:
                self.rectangleCircleCutShapeList.append(rectangleCircleCut_face)

            if self.meshGenerationMode:
                if self.geomGenerationType == "Solid":
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleCircleCutMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    if self.meshType == "Hexa": 
                        meshManager.mesh_shape_extrude_3D(rectangleCircleCut_solid,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],11,self.maxNID,self.maxEID)
                    else:
                        meshManager.mesh_shape(rectangleCircleCut_solid,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.rectangleCircleCutMeshList.append(meshManager)
                    self.rectangleCircleCutMeshpsidList.append(curpsid)
                elif self.geomGenerationType == "Shell":
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleCircleCutMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    meshManager.mesh_shape(rectangleCircleCut_face,self.meshSizeInPlane,self.meshSizeInPlane,2,None,self.maxNID,self.maxEID,self.thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1                    
                    if len(rectangleCircleCut) > 8:
                        if len(rectangleCircleCut[8]) > 0:
                            compMatIDList = rectangleCircleCut[8]
                            if len(rectangleCircleCut) > 9:
                                compThicknessList = rectangleCircleCut[9]
                                if len(rectangleCircleCut) > 10:
                                    compBList = rectangleCircleCut[10]
                                else:
                                    compBList = []
                                meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.rectangleCircleCutMeshList.append(meshManager)
                    self.rectangleCircleCutMeshpsidList.append(curpsid)

    def GenerateRectangleFilletCutShape(self):
        self.rectangleFilletCutShapeList = [] 
        curi = 0
        for rectangleFilletCut in self.rectangleFilletCutList:
            curpsid = self.rectangleFilletCutpsidList[curi]
            curi = curi + 1
            x = rectangleFilletCut[0] + self.posX
            y = rectangleFilletCut[1] + self.posY
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            xLength = rectangleFilletCut[2]
            yLength = rectangleFilletCut[3]            
            thickness = self.thickness
            rectangle_box_wire = BRepBuilderAPI_MakePolygon()
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y-yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x+xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y+yLength/2.0,z))
            rectangle_box_wire.Add(gp_Pnt(x-xLength/2.0,y-yLength/2.0,z))
            rectangle_face = BRepBuilderAPI_MakeFace(rectangle_box_wire.Wire()).Face()

            cutFaceList = []                       

            cutList = rectangleFilletCut[4]
            matID = rectangleFilletCut[5]
            for i in range(len(cutList)):
                curCutType = cutList[i][0]                                
                curCutX = cutList[i][1] + self.posX
                curCutY = cutList[i][2] + self.posY
                offset = 0.5
                curCutZ = z-offset
                
                curCutXLength = cutList[i][3]
                curCutYLength = cutList[i][4]                
                curCutR = cutList[i][5]
                pt1 = gp_Pnt(curCutX-curCutXLength/2.0,curCutY-curCutYLength/2.0,curCutZ)
                pt2 = gp_Pnt(curCutX+curCutXLength/2.0,curCutY-curCutYLength/2.0,curCutZ)
                pt3 = gp_Pnt(curCutX+curCutXLength/2.0,curCutY+curCutYLength/2.0,curCutZ)
                pt4 = gp_Pnt(curCutX-curCutXLength/2.0,curCutY+curCutYLength/2.0,curCutZ)
                ed1 = BRepBuilderAPI_MakeEdge(pt1,pt2).Edge()
                ed2 = BRepBuilderAPI_MakeEdge(pt2,pt3).Edge()
                ed3 = BRepBuilderAPI_MakeEdge(pt3,pt4).Edge()
                ed4 = BRepBuilderAPI_MakeEdge(pt4,pt1).Edge()

                if curCutType == "RFCFillet":
                    
                    f1 = ChFi2d_AnaFilletAlgo()
                    f1.Init(ed1,ed2,gp_Pln(gp_Pnt(0,0,z-offset),gp_Dir(0,0,1)))
                    f1.Perform(curCutR)
                    fillet2d1 = f1.Result(ed1,ed2)
                    f2 = ChFi2d_AnaFilletAlgo()
                    f2.Init(ed2,ed3,gp_Pln(gp_Pnt(0,0,z-offset),gp_Dir(0,0,1)))
                    f2.Perform(curCutR)
                    fillet2d2 = f2.Result(ed2,ed3)
                    f3 = ChFi2d_AnaFilletAlgo()
                    f3.Init(ed3,ed4,gp_Pln(gp_Pnt(0,0,z-offset),gp_Dir(0,0,1)))
                    f3.Perform(curCutR)
                    fillet2d3 = f3.Result(ed3,ed4)
                    f4 = ChFi2d_AnaFilletAlgo()
                    f4.Init(ed4,ed1,gp_Pln(gp_Pnt(0,0,z-offset),gp_Dir(0,0,1)))
                    f4.Perform(curCutR)
                    fillet2d4 = f4.Result(ed4,ed1)

                    w = make_wire([ed1,fillet2d1,ed2,fillet2d2,ed3,fillet2d3,ed4,fillet2d4,ed1])
                    cut_rect_face = BRepBuilderAPI_MakeFace(w).Face()
                    cutFaceList.append(cut_rect_face)
                elif curCutType == "RFCChamfer":
                    #chamfer = ChFi2d_ChamferAPI()
                    pt1 = gp_Pnt(curCutX-curCutXLength/2.0+curCutR,curCutY-curCutYLength/2.0,curCutZ)
                    pt2 = gp_Pnt(curCutX+curCutXLength/2.0-curCutR,curCutY-curCutYLength/2.0,curCutZ)
                    pt3 = gp_Pnt(curCutX+curCutXLength/2.0,curCutY-curCutYLength/2.0+curCutR,curCutZ)
                    pt4 = gp_Pnt(curCutX+curCutXLength/2.0,curCutY+curCutYLength/2.0-curCutR,curCutZ)
                    pt5 = gp_Pnt(curCutX+curCutXLength/2.0-curCutR,curCutY+curCutYLength/2.0,curCutZ)
                    pt6 = gp_Pnt(curCutX-curCutXLength/2.0+curCutR,curCutY+curCutYLength/2.0,curCutZ)
                    pt7 = gp_Pnt(curCutX-curCutXLength/2.0,curCutY+curCutYLength/2.0-curCutR,curCutZ)
                    pt8 = gp_Pnt(curCutX-curCutXLength/2.0,curCutY-curCutYLength/2.0+curCutR,curCutZ)
                    ed1 = BRepBuilderAPI_MakeEdge(pt1,pt2).Edge()
                    ed2 = BRepBuilderAPI_MakeEdge(pt2,pt3).Edge()
                    ed3 = BRepBuilderAPI_MakeEdge(pt3,pt4).Edge()
                    ed4 = BRepBuilderAPI_MakeEdge(pt4,pt5).Edge()
                    ed5 = BRepBuilderAPI_MakeEdge(pt5,pt6).Edge()
                    ed6 = BRepBuilderAPI_MakeEdge(pt6,pt7).Edge()
                    ed7 = BRepBuilderAPI_MakeEdge(pt7,pt8).Edge()
                    ed8 = BRepBuilderAPI_MakeEdge(pt8,pt1).Edge()
                    w = make_wire([ed1,ed2,ed3,ed4,ed5,ed6,ed7,ed8,ed1])
                    cut_rect_face = BRepBuilderAPI_MakeFace(w).Face()
                    cutFaceList.append(cut_rect_face)




                
                '''
                if curCutType == "RFCFillet":
                    fill = BRepFilletAPI_MakeFillet(cut_rect_face)
                    for e in TopologyExplorer(cut_rect_face).edges():
                        fill.Add(curCutR,e)
                    fill.Build()
                    cutFaceList.append(fill.Shape())
                    
                elif curCutType == "RFCChamfer":
                    chamfer = BRepFilletAPI_MakeChamfer(cut_rect_face)
                    for e in TopologyExplorer(cut_rect_face).edges():
                        chamfer.Add(curCutR,e)
                    cutFaceList.append(chamfer.Shape())
                '''

            if self.geomGenerationType == "Solid":
                rectSolid = BRepPrimAPI_MakePrism(rectangle_face,gp_Vec(0,0,thickness)).Shape()
                #cutShapeList = []
                L1 = TopTools_ListOfShape()
                L1.Append(rectSolid)
                L2 = TopTools_ListOfShape()
                for cutFace in cutFaceList:
                    curSolid = BRepPrimAPI_MakePrism(cutFace,gp_Vec(0,0,thickness+offset*2.0)).Shape()
                    L2.Append(curSolid)
                    #cutShapeList.append(curSolid)
                cut = BRepAlgoAPI_Cut()
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.0000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                else:
                    print("Cut Success")
                    shape = cut.Shape()
                self.rectangleFilletCutShapeList.append(shape)                
                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleFilletCutMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    if self.meshType == "Hexa":
                        L1 = TopTools_ListOfShape()
                        L1.Append(rectangle_face)
                        L2 = TopTools_ListOfShape()
                        for cutFace in cutFaceList:
                            L2.Append(cutFace)
                        cut = BRepAlgoAPI_Cut()
                        cut.SetArguments(L1)
                        cut.SetTools(L2)
                        cut.SetRunParallel(True)
                        cut.SetFuzzyValue(0.0000001)
                        cut.Build()
                        if cut.Shape() == None:
                            print("Cut Failed")
                        else:
                            print("Cut Success")
                            shape = cut.Shape()
                        meshManager.mesh_shape_extrude_3D(shape,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],11,self.maxNID,self.maxEID)
                    elif self.meshType == "Tetra":
                        meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.rectangleFilletCutMeshList.append(meshManager)
                    self.rectangleFilletCutMeshpsidList.append(curpsid)
            elif "Shell" in self.geomGenerationType:
                L1 = TopTools_ListOfShape()
                L1.Append(rectangle_face)
                L2 = TopTools_ListOfShape()
                for cutFace in cutFaceList:
                    solid = BRepPrimAPI_MakePrism(cutFace,gp_Vec(0,0,offset*2.0)).Shape()
                    L2.Append(solid)
                cut = BRepAlgoAPI_Cut()
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.0000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                else:
                    print("Cut Success")
                    shape = cut.Shape()
                self.rectangleFilletCutShapeList.append(shape)
                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_RectangleFilletCutMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    if self.meshType == "Quad":
                        meshManager.mesh_shape_quad_2D(shape,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    else:
                        meshManager.mesh_shape_tri_2D(shape,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    if len(rectangleFilletCut) > 6:
                        if len(rectangleFilletCut[6]) > 0:
                            compMatIDList = rectangleFilletCut[6]
                            if len(rectangleFilletCut) > 7:
                                compThicknessList = rectangleFilletCut[7]
                                if len(rectangleFilletCut) > 8:
                                    compBList = rectangleFilletCut[8]
                                else:
                                    compBList = []
                                meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.rectangleFilletCutMeshList.append(meshManager)
                    self.rectangleFilletCutMeshpsidList.append(curpsid)
                               

    def GenerateImageShape(self):
        self.imageShapeList = [] 
        curi = 0 
        for imageData in self.imageList:
            curpsid = self.imagepsidList[curi]
            curi = curi + 1
            xLength = imageData[0]
            yLength = imageData[1]
            imageFileName = imageData[2]            
            cutShapeOption = imageData[3]
            matID = imageData[4]
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0

            image = cv2.imread(imageFileName)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = [contour for i, contour in enumerate(contours) if hierarchy[0][i][3] != -1]
            contour_img = np.zeros_like(image)
            cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
            xMatrix = []
            yMatrix = []
            print("Contour Length : ",len(contours))
            for i, contour in enumerate(contours):
                pointList = contour.tolist()
                xList = [point[0][0] for point in pointList]
                yList = [point[0][1] for point in pointList]
                xMatrix.append(xList)
                yMatrix.append(yList)

            point3DList = []
            pointCut3DMatrix = []
            for i in range(len(xMatrix)):
                xList = xMatrix[i]
                yList = yMatrix[i]
                if i == 0:
                    xmin = min(xList)
                    xmax = max(xList)
                    ymin = min(yList)
                    ymax = max(yList)
                    xLengthModified = xLength/(xmax - xmin)
                    yLengthModified = yLength/(ymax - ymin)
                    for j in range(len(xList)):
                        x = xLengthModified*xList[j] + self.posX
                        # 3 digit
                        y = yLengthModified*yList[j] + self.posY                        

                        point3DList.append(gp_Pnt(x,y,z))
                    x = xLengthModified*xList[0] + self.posX
                    y = yLengthModified*yList[0] + self.posY                    
                    point3DList.append(gp_Pnt(x,y,z))
                    if self.meshGenerationMode:
                        point3DList = self.ReducePoint3DbyMinimumMeshSize(point3DList,self.meshSizeInPlane*0.4)
                else:
                    pointCut3DList = [] 
                    for j in range(len(xList)):
                        x = xLengthModified*xList[j] + self.posX
                        y = yLengthModified*yList[j] + self.posY                        
                        x = round(x,4)
                        y = round(y,4)
                        z = round(z,4)
                        pointCut3DList.append(gp_Pnt(x,y,z))
                    x = xLengthModified*xList[0] + self.posX
                    y = yLengthModified*yList[0] + self.posY                   
                    pointCut3DList.append(gp_Pnt(x,y,z))
                    if self.meshGenerationMode:
                        pointCut3DList = self.ReducePoint3DbyMinimumMeshSize(pointCut3DList,self.meshSizeInPlane*0.4)
                    pointCut3DMatrix.append(pointCut3DList)
            pbuilder = BRepBuilderAPI_MakePolygon()
            for point in point3DList:
                pbuilder.Add(point)
            p = pbuilder.Wire()
            fbuilder = BRepBuilderAPI_MakeFace(p,True)
            face = fbuilder.Face()
        
            thick = self.thickness
            pbuilder = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
            shape = pbuilder.Shape()   
                                
            if len(pointCut3DMatrix) == 0:
                self.imageShapeList.append(shape)
                if self.meshGenerationMode:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_ImageMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    #meshManager.mesh_shape_extrude_3D(shape,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness])
                    if self.meshType == "Hexa":
                        meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 11,self.maxNID,self.maxEID)
                    elif self.meshType == "Tetra":
                        meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                    elif self.meshType == "Quad":
                        meshManager.mesh_shape_quad_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    elif self.meshType == "Tri":
                        meshManager.mesh_shape_tri_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.imageMeshList.append(meshManager)
                    self.imageMeshpsidList.append(curpsid)
                   
            else:
                L1 = TopTools_ListOfShape()
                L1.Append(shape)
                L2 = TopTools_ListOfShape()
                cutShapeList = []
                curFaceList = []
                for i in range(len(pointCut3DMatrix)):
                    pbuilder = BRepBuilderAPI_MakePolygon()
                    for point in pointCut3DMatrix[i]:
                        pbuilder.Add(point)
                    p = pbuilder.Wire()
                    fbuilder = BRepBuilderAPI_MakeFace(p,True)
                    thick = self.thickness
                    curFaceList.append(fbuilder.Face())
                    pbuilder = BRepPrimAPI_MakePrism(fbuilder.Face(),gp_Vec(0,0,thick))
                    shapeCut = pbuilder.Shape()
                    cutShapeList.append(shapeCut)
                    L2.Append(shapeCut)
                cut = BRepAlgoAPI_Cut()
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.0000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                else:
                    print("Cut Success")   
                    shape = cut.Shape()                
                
                self.imageShapeList.append(shape)
                if cutShapeOption:
                    for cutShape in cutShapeList:                    
                        self.imageShapeList.append(cutShape)

                if self.meshGenerationMode:
                    L1 = TopTools_ListOfShape()
                    L1.Append(face)
                    L2 = TopTools_ListOfShape()
                    for cutFace in curFaceList:
                        L2.Append(cutFace)
                    cut = BRepAlgoAPI_Cut()
                    cut.SetArguments(L1)
                    cut.SetTools(L2)
                    cut.SetRunParallel(True)
                    cut.SetFuzzyValue(0.0000001)
                    cut.Build()
                    if cut.Shape() == None:
                        print("Cut Failed")
                    else:
                        print("Cut Success")
                        face = cut.Shape()
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_ImageMesh{1}".format(self.name,self.ith))
                    self.ith += 1                    
                    #meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness])
                    if self.meshType == "Hexa":
                        meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 11,self.maxNID,self.maxEID)
                    elif self.meshType == "Tetra":
                        meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 2, self.maxNID, self.maxEID)
                    elif self.meshType == "Quad":
                        meshManager.mesh_shape_quad_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    elif self.meshType == "Tri":
                        meshManager.mesh_shape_tri_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.imageMeshList.append(meshManager)
                    self.imageMeshpsidList.append(curpsid)
            
                    if cutShapeOption:
                        if self.meshType == "Tetra":
                            for cutShape in cutShapeList:
                                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                                meshManager.SetPath(self.meshPath)
                                meshManager.SetName("{0}_ImageMesh{1}".format(self.name,self.ith))
                                self.ith += 1
                                meshManager.mesh_shape(cutShape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                                self.maxPID = self.maxPID + 1
                                meshManager.part.SetID(self.maxPID)
                                if matID != -1:
                                    meshManager.part.SetMaterialID(matID)
                                self.imageMeshList.append(meshManager)
                                self.imageMeshpsidList.append(curpsid)  
                        else:
                            for cutFace in curFaceList:
                                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                                meshManager.SetPath(self.meshPath)
                                meshManager.SetName("{0}_ImageMesh{1}".format(self.name,self.ith))
                                self.ith += 1
                                #meshManager.mesh_shape_extrude_3D(cutFace,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness])
                                if self.meshType == "Hexa":
                                    meshManager.mesh_shape_extrude_3D(cutFace,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 11,self.maxNID,self.maxEID)
                                elif self.meshType == "Quad":
                                    meshManager.mesh_shape_quad_2D(cutFace,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                                elif self.meshType == "Tri":
                                    meshManager.mesh_shape_tri_2D(cutFace,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                                
                                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                                self.maxPID = self.maxPID + 1
                                meshManager.part.SetID(self.maxPID)
                                if matID != -1:
                                    meshManager.part.SetMaterialID(matID)
                                self.imageMeshList.append(meshManager)
                                self.imageMeshpsidList.append(curpsid)
                    

            


    def GenerateDetailSolderShapes(self):
        self.detailSolderShapeList = []
        for detailSolder in self.detailSolderList:
            x = detailSolder[0] + self.posX
            y = detailSolder[1] + self.posY
            z = self.posZ
            
            points = detailSolder[2]
            matID = detailSolder[3]
            wires = [] 
            for radius, height in points:
                circle = gp_Circ(gp_Ax2(gp_Pnt(x,y,z+height*self.thickness), gp_Dir(0, 0, 1)), radius)
                circle_edge = BRepBuilderAPI_MakeEdge(circle).Edge()
                circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
                wires.append(circle_wire)
            loft = BRepOffsetAPI_ThruSections(True)
            for wire in wires:
                loft.AddWire(wire)
            loft.Build()
            shape = loft.Shape()
            self.detailSolderShapeList.append(shape)
            if self.meshGenerationMode:
                meshManager = meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(self.meshPath)
                meshManager.SetName("{0}_DetailSolderMesh{1}".format(self.name,len(self.detailSolderShapeList)))
                meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                meshManager.part.SetID(self.maxPID)
                if matID != -1:
                    meshManager.part.SetMaterialID(matID)
                self.detailSolderMeshList.append(meshManager)

    def ReducePoint3DbyMinimumMeshSize(self,point3DList,minimumMeshSize):
        newPointList = [] 
        for i in range(len(point3DList)):
            newPointList.append(point3DList[i])

        while True:
            numRemoved = 0
            for i in range(1,len(newPointList)-1):
                
                if i >= len(newPointList)-1:
                    break    
                pointPrev : gp_Pnt = newPointList[i-1]
                point : gp_Pnt = newPointList[i]
                pointNext : gp_Pnt = newPointList[i+1]
                d1 = pointPrev.Distance(point)
                d2 = point.Distance(pointNext)
                #print(d1,d2)
                if d1 < minimumMeshSize and d2 < minimumMeshSize:
                    newPointList.pop(i)
                   
                    i = 0
                    numRemoved += 1
                else:
                    pass#print("Keep",i)
            print("Number of Removed : ",numRemoved)
            if numRemoved == 0:
                break
            numRemoved = 0
        return newPointList
    
    def GeneratePolynomialPartShapes(self):
        self.detailPolynomialPartShapeList = []
        curi = 0 
        for polynomialPart in self.polynomialPartList:
            curpsid = self.polynomialPartpsidList[curi]
            curi = curi + 1
            xList = polynomialPart[0]
            yList = polynomialPart[1]
            matID = polynomialPart[2]
            if len(xList) != len(yList):
                print("Polynomial Part Error")
                continue
            point3DList = [] 
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            for i in range(len(xList)):
                x = xList[i] + self.posX
                y = yList[i] + self.posY
                
                point3DList.append(gp_Pnt(x,y,z))
            
            if self.meshGenerationMode:
                point3DList = self.ReducePoint3DbyMinimumMeshSize(point3DList,self.meshSizeInPlane*0.4)
            
            pbuilder = BRepBuilderAPI_MakePolygon()
            for point in point3DList:
                pbuilder.Add(point)
            p = pbuilder.Wire()
            fbuilder = BRepBuilderAPI_MakeFace(p,True)
            face = fbuilder.Face()
            if self.meshGenerationMode:
                if self.meshType == "Tetra":
                    pass
                else:
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_PolynomialPartMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    #meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness])
                    if self.meshType == "Hexa":
                        meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 11,self.maxNID,self.maxEID)
                    elif self.meshType == "Tetra":
                        meshManager.mesh_shape_extrude_3D(face,self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],2, self.maxNID, self.maxEID)
                    elif self.meshType == "Quad":
                        meshManager.mesh_shape_quad_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    elif self.meshType == "Tri":
                        meshManager.mesh_shape_tri_2D(face,self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    if "Shell" in self.geomGenerationType:
                        if len(polynomialPart) > 3:
                            if len(polynomialPart[3]) > 0:
                                compMatIDList = polynomialPart[3]
                                if len(polynomialPart) > 4:
                                    compThicknessList = polynomialPart[4]
                                    if len(polynomialPart) > 5:
                                        compBList = polynomialPart[5]
                                    else:
                                        compBList = []
                                    meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.polynomialPartMeshList.append(meshManager)
                    self.polynomialPartMeshpsidList.append(curpsid)

            thick = self.thickness
            pbuilder = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
            shape = pbuilder.Shape()               
            if self.geomGenerationType == "Solid":
                self.detailPolynomialPartShapeList.append(shape)
            elif "Shell" in self.geomGenerationType:
                self.detailPolynomialPartShapeList.append(face)

            if self.meshGenerationMode:
                if self.meshType == "Tetra":
                    meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.polynomialPartMeshList.append(meshManager)
                    self.polynomialPartMeshpsidList.append(curpsid)

    def GeneratePolynomialCutPartShapes(self):
        self.detailPolynomialCutPartShapeList = []
        curi = 0
        for polynomialCutPart in self.polynomialCutPartList:
            curpsid = self.polynomialCutPartpsidList[curi]
            curi = curi + 1
            xList = polynomialCutPart[0]
            yList = polynomialCutPart[1]
            xCutMatrix = polynomialCutPart[2]
            yCutMatrix = polynomialCutPart[3]
            generateInternalOption = polynomialCutPart[4]
            matID = polynomialCutPart[5]
            if len(polynomialCutPart) > 6:
                matCutID = polynomialCutPart[6]
            else:
                matCutID = matID
            
            if len(xList) != len(yList):
                print("Polynomial Part Error")
                continue
            if len(xCutMatrix) != len(yCutMatrix):
                print("Polynomial Part Error")
                continue
           
            point3DList = [] 
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0

            for i in range(len(xList)):
                x = xList[i] + self.posX
                y = yList[i] + self.posY
                
                point3DList.append(gp_Pnt(x,y,z))
            if self.meshGenerationMode:
                point3DList = self.ReducePoint3DbyMinimumMeshSize(point3DList,self.meshSizeInPlane*0.4)
            pointCut3DMatrix = [] 
            for i in range(len(xCutMatrix)):
                pointCut3DList = []
                for j in range(len(xCutMatrix[i])):
                    x = xCutMatrix[i][j] + self.posX
                    y = yCutMatrix[i][j] + self.posY
                    
                    pointCut3DList.append(gp_Pnt(x,y,z))
                if self.meshGenerationMode:
                    pointCut3DList = self.ReducePoint3DbyMinimumMeshSize(pointCut3DList,self.meshSizeInPlane*0.4)
                pointCut3DMatrix.append(pointCut3DList)
            
            pbuilder = BRepBuilderAPI_MakePolygon()
            for point in point3DList:
                pbuilder.Add(point)
            p = pbuilder.Wire()
            fbuilder = BRepBuilderAPI_MakeFace(p,True)
            face = fbuilder.Face()
            cutFaceList = [] 
            for i in range(len(pointCut3DMatrix)):
                pbuilder = BRepBuilderAPI_MakePolygon()
                for point in pointCut3DMatrix[i]:
                    pbuilder.Add(point)
                p = pbuilder.Wire()
                fbuilder = BRepBuilderAPI_MakeFace(p,True)
                cutFaceList.append(fbuilder.Face())
            
            if self.meshGenerationMode:
                L1 = TopTools_ListOfShape()
                L1.Append(face)
                L2 = TopTools_ListOfShape()
                for cutFace in cutFaceList:
                    L2.Append(cutFace)
                cut = BRepAlgoAPI_Cut()
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.0000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                else:
                    print("Cut Success")
                    if self.meshType == "Tetra":
                        pass
                    else:
                        meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                        meshManager.SetPath(self.meshPath)
                        meshManager.SetName("{0}_PolynomialCutPartMesh{0}".format(self.name,self.ith))
                        self.ith += 1
                        #meshManager.mesh_shape_extrude_3D(cut.Shape(),self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness])
                        if self.meshType == "Hexa":
                            meshManager.mesh_shape_extrude_3D(cut.Shape(),self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness], 11,self.maxNID,self.maxEID)
                        elif self.meshType == "Tetra":
                            meshManager.mesh_shape_extrude_3D(cut.Shape(),self.meshSizeInPlane,self.numberofElementinThickness, [0, 0, self.thickness],2, self.maxNID, self.maxEID)
                        elif self.meshType == "Quad":
                            meshManager.mesh_shape_quad_2D(cut.Shape(),self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)
                        elif self.meshType == "Tri":
                            meshManager.mesh_shape_tri_2D(cut.Shape(),self.meshSizeInPlane, self.maxNID, self.maxEID, self.thickness)

                        self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                        self.maxPID = self.maxPID + 1
                        if "Shell" in self.geomGenerationType:
                            if len(polynomialCutPart) > 7:
                                if len(polynomialCutPart[7]) > 0:
                                    compMatIDList = polynomialCutPart[7]
                                    if len(polynomialCutPart) > 8:
                                        compThicknessList = polynomialCutPart[8]
                                        if len(polynomialCutPart) > 9:
                                            compBList = polynomialCutPart[9]
                                        else:
                                            compBList = []
                                        meshManager.SetPartasComposite(compMatIDList,compThicknessList,compBList)

                        meshManager.part.SetID(self.maxPID)
                        if matID != -1:
                            meshManager.part.SetMaterialID(matID)
                        self.polynomialCutPartMeshList.append(meshManager)
                        self.polynomialCutPartMeshpsidList.append(curpsid)
                pass
            

            thick = self.thickness
            pbuilder = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
            shape = pbuilder.Shape()
            L1 = TopTools_ListOfShape()
            L1.Append(shape)
            L2 = TopTools_ListOfShape()            
            cutShapeList = [] 
            for i in range(len(pointCut3DMatrix)):
                pbuilder = BRepBuilderAPI_MakePolygon()
                for point in pointCut3DMatrix[i]:
                    pbuilder.Add(point)
                p = pbuilder.Wire()
                fbuilder = BRepBuilderAPI_MakeFace(p,True)
                face = fbuilder.Face()
                thick = self.thickness
                pbuilder = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
                shapeCut = pbuilder.Shape()
                cutShapeList.append(shapeCut)
                L2.Append(shapeCut)
            cut = BRepAlgoAPI_Cut()
            cut.SetArguments(L1)
            cut.SetTools(L2)
            cut.SetRunParallel(True)
            cut.SetFuzzyValue(0.0000001)
            cut.Build()
            if cut.Shape() == None:
                print("Cut Failed")                
            else:
                print("Cut Success")
                shape = cut.Shape()                            
            if self.meshGenerationMode:
                if self.meshType == "Tetra":                    
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_PolynomialCutPartMesh{1}".format(self.name,self.ith))
                    self.ith += 1
                    meshManager.mesh_shape(shape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.polynomialCutPartMeshList.append(meshManager)
                    self.polynomialCutPartMeshpsidList.append(curpsid)
            if self.geomGenerationType == "Solid":
                self.detailPolynomialCutPartShapeList.append(shape)
            elif "Shell" in self.geomGenerationType:
                self.detailPolynomialCutPartShapeList.append(face)
            if generateInternalOption == True:
                if self.geomGenerationType == "Solid":
                    for cutShape in cutShapeList:
                        self.detailPolynomialCutPartShapeList.append(cutShape)                    
                elif "Shell" in self.geomGenerationType:
                    for cutFace in cutFaceList:
                        self.detailPolynomialCutPartShapeList.append(cutFace)
                if self.meshGenerationMode:
                    if self.meshType == "Tetra":                        
                        for cutShape in cutShapeList:
                            meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                            meshManager.SetPath(self.meshPath)
                            meshManager.SetName("{0}_PolynomialCutPartMesh{1}".format(self.name,self.ith))
                            self.ith += 1
                            meshManager.mesh_shape(cutShape,self.meshSizeInPlane,self.meshSizeInPlane,3, None,self.maxNID,self.maxEID)
                            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                            self.maxPID = self.maxPID + 1
                            meshManager.part.SetID(self.maxPID)
                            if matCutID != -1:
                                meshManager.part.SetMaterialID(matCutID)
                            self.polynomialCutPartMeshList.append(meshManager)
                            self.polynomialCutPartMeshpsidList.append(curpsid)
    
    def GeneratePolynomialSweepShape(self):
        self.polynomialSweepShapeList = []
        curi = 0 
        for polynomialSweep in self.polynomialSweepList:
            curpsid = self.polynomialSweeppsidList[curi]
            curi = curi + 1
            xBottomList = polynomialSweep[0]
            yBottomList = polynomialSweep[1]
            xTopList = polynomialSweep[2]
            yTopList = polynomialSweep[3]
            matID = polynomialSweep[4]
            if len(xBottomList) != len(yBottomList):
                print("Polynomial Sweep Error")
                continue
            if len(xTopList) != len(yTopList):
                print("Polynomial Sweep Error")
                continue
            if len(xTopList) != len(xBottomList):
                print("Polynomial Sweep Error")
                continue
            point3DBottomList = []
            point3DTopList = []
            z = self.posZ
            if self.meshGenerationMode:
                if self.meshType == "Quad" or self.meshType == "Tri":
                    z = z + self.thickness/2.0
            for i in range(len(xBottomList)):
                x = xBottomList[i] + self.posX
                y = yBottomList[i] + self.posY
                
                point3DBottomList.append(gp_Pnt(x,y,z))
                x = xTopList[i] + self.posX
                y = yTopList[i] + self.posY
                zt = z + self.thickness
                point3DTopList.append(gp_Pnt(x,y,zt))
            '''if self.meshGenerationMode:
                point3DBottomList = self.ReducePoint3DbyMinimumMeshSize(point3DBottomList,self.meshSizeInPlane*0.4)
                point3DTopList = self.ReducePoint3DbyMinimumMeshSize(point3DTopList,self.meshSizeInPlane*0.4)'''
            edgeTopList = []
            edgeBottomList = []
            length = len(point3DBottomList)
            for i in range(length-1):
                edgeTop = BRepBuilderAPI_MakeEdge(point3DTopList[i],point3DTopList[i+1]).Edge()
                edgeTopList.append(edgeTop)
                edgeBottom = BRepBuilderAPI_MakeEdge(point3DBottomList[i],point3DBottomList[i+1]).Edge()
                edgeBottomList.append(edgeBottom)
            wireTop = BRepBuilderAPI_MakeWire()
            wireBottom = BRepBuilderAPI_MakeWire()
            for edge in edgeTopList:
                wireTop.Add(edge)
            for edge in edgeBottomList:
                wireBottom.Add(edge)
            sewing = BRepBuilderAPI_Sewing()

            faceTop = BRepBuilderAPI_MakeFace(wireTop.Wire()).Face()
            faceBottom = BRepBuilderAPI_MakeFace(wireBottom.Wire()).Face()
            
            sewing.Add(faceTop)
            sewing.Add(faceBottom)

            for i in range(length-1):
                edgeBottom = edgeBottomList[i]
                edgeTop = edgeTopList[i]
                pnt1 = point3DBottomList[i]
                pnt2 = point3DBottomList[i+1]
                pnt3 = point3DTopList[i+1]
                pnt4 = point3DTopList[i]
                edgeRight = BRepBuilderAPI_MakeEdge(pnt2,pnt3).Edge()
                edgeLeft = BRepBuilderAPI_MakeEdge(pnt4,pnt1).Edge()
                wire = BRepBuilderAPI_MakeWire()
                wire.Add(edgeBottom)
                wire.Add(edgeRight)
                wire.Add(edgeTop)
                wire.Add(edgeLeft)
                face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
                sewing.Add(face)
            sewing.Perform()
            shape = sewing.SewedShape()
            solid = BRepBuilderAPI_MakeSolid(shape).Solid()

            #shell_builder = brepfill_Shell(wireTop.Wire(),wireBottom.Wire())    
            #solid_builder = BRepBuilderAPI_MakeSolid()
            #solid_builder.Add(shell_builder)

            '''offset_face_top = BRepOffsetAPI_MakeOffsetShape()
            offset_face_top.PerformByJoin(faceTop,0.001,1.e-6)
            shellTop = offset_face_top.Shape()
            offset_face_top = BRepOffsetAPI_MakeOffsetShape()
            offset_face_top.PerformByJoin(shellTop,-0.001,1.e-6)
            shellTop = offset_face_top.Shape()
            offset_face_bottom = BRepOffsetAPI_MakeOffsetShape()
            offset_face_bottom.PerformByJoin(faceBottom,0.001,1.e-6)
            shellBottom = offset_face_bottom.Shape()
            offset_face_bottom = BRepOffsetAPI_MakeOffsetShape()
            offset_face_bottom.PerformByJoin(shellBottom,-0.001,1.e-6)
            shellBottom = offset_face_bottom.Shape()
            solid_builder.Add(shellTop)
            solid_builder.Add(shellBottom)
            solid_builder.Build()
            shape = solid_builder.Shape()'''
            self.polynomialSweepShapeList.append(solid)

            if self.meshGenerationMode:
                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(self.meshPath)
                meshManager.SetName("{0}_PolynomialSweepMesh{1}".format(self.name,self.ith))
                self.ith += 1
                meshManager.mesh_shape(solid,self.meshSizeInPlane,self.meshSizeInPlane,3,"front3d",self.maxNID,self.maxEID)
                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                meshManager.part.SetID(self.maxPID)
                if matID != -1:
                    meshManager.part.SetMaterialID(matID)
                self.polynomialSweepMeshList.append(meshManager)
                self.polynomialSweepMeshpsidList.append(curpsid)
        pass
    
   
    def make_wire_from_points(self, points):
        """
        Create a Polygon Wire from a list of points
        """
        
        # Create a TColgp_Array1OfPnt to store the points
        gpPntList = []
        for i, point in enumerate(points):
            gpPntList.append(gp_Pnt(*point))
        
        edges = []
        for i in range(len(gpPntList)-1):
            edge = BRepBuilderAPI_MakeEdge(gpPntList[i], gpPntList[i+1]).Edge()
            edges.append(edge)
        polygon = BRepBuilderAPI_MakePolygon()
        for point in gpPntList:
            polygon.Add(point)

        wire = polygon.Wire()
        return wire

    def make_offset_curve(self, wire, distance):
        """
        Create an offset curve from an wire
        """
        # Create an offset curve from the edge
        # edge is not closed 
        
        offset = BRepOffsetAPI_MakeOffset(wire)
        offset.Perform(distance,0)
        offset.Build()
        return offset.Shape()

    def get_edges_from_compound(self, compound):
        """
        Get all edges from a compound
        """
        # Create an explorer to iterate over the edges
        explorer = TopExp_Explorer(compound, TopAbs_EDGE)
        edges = []
        while explorer.More():
            edge = topods.Edge(explorer.Current())
            edges.append(edge)
            explorer.Next()
        return edges
    
    def get_face_from_points(self, pointsOuter):
        """
        Get the face from a list of points
        """
        wire = self.make_wire_from_points(pointsOuter)
        face = BRepBuilderAPI_MakeFace(wire).Face()
        return face
    
    def get_face_from_points_and_cut_points(self, pointsOuter, pointsInner):
        """
        Get the face from a list of points
        """
        wireOuter = self.make_wire_from_points(pointsOuter)
        faceOuter = BRepBuilderAPI_MakeFace(wireOuter).Face()
        wireInner = self.make_wire_from_points(pointsInner)
        faceInner = BRepBuilderAPI_MakeFace(wireInner).Face()
        
        cut = BRepAlgoAPI_Cut(faceOuter, faceInner)
        cut.Build()
        face = cut.Shape()        
        return face
    
    def get_faces_between_closed_two_wire_points(self, pointsOuter, pointsInner):
        faces = [] 
        for i in range(len(pointsOuter)):
            ip1 = i + 1 
            if ip1 == len(pointsOuter):
                ip1 = 0
            p1 = gp_Pnt(*pointsOuter[i])
            p2 = gp_Pnt(*pointsOuter[ip1])
            p3 = gp_Pnt(*pointsInner[ip1])
            p4 = gp_Pnt(*pointsInner[i])
            face = self.create_face(p1, p2, p3, p4)
            faces.append(face)
        return faces
    
    def create_bspline_from_points(self, points):
        array = TColgp_Array1OfPnt(1, len(points))
        for i, point in enumerate(points):
            array.SetValue(i + 1, gp_Pnt(*point))
        return GeomAPI_PointsToBSpline(array).Curve()
    
    def extract_points_from_arc(self, arc, num_points):
        points = []
        u_start = arc.FirstParameter()  # Start parameter of the curve
        u_end = arc.LastParameter()    # End parameter of the curve
        u_step = (u_end - u_start) / (num_points - 1)

        for i in range(num_points):
            u = u_start + i * u_step
            point = gp_Pnt()  # Create a gp_Pnt to hold the result
            arc.D0(u, point)  # Evaluate the point on the curve at parameter u
            points.append((point.X(), point.Y(), point.Z()))
            
        return points
 
    def get_arc_faces_between_closed_wire_points(self, pointsA, pointsCenter,pointsB):
        faces = [] 
        num_points = 3  # Number of points to extract

        for i in range(len(pointsA)-1):
            print(i)
            ip1 = i + 1
            if ip1 == len(pointsA)-1:
                ip1 = 0
            if i == 0:
                p1 = gp_Pnt(*pointsA[i])      
                p3 = gp_Pnt(*pointsB[i])
                p5 = gp_Pnt(*pointsCenter[i])
                vec1 = gp_Vec(p5,p1)
                vec2 = gp_Vec(p5,p3)
                vec1.Normalize()
                vec2.Normalize()
                normal_12 = vec1.Crossed(vec2)
                if normal_12.Magnitude() < 1.0e-10:
                    normal_12 = gp_Vec(0,0,1)
                self.radius12 = p5.Distance(p1)
                coord12 = gp_Ax2(p5, gp_Dir(normal_12))            
                circle12 = gp_Circ(coord12, self.radius12)
                arc1 = GC_MakeArcOfCircle(circle12, p1, p3, False).Value()
                arc1_points = self.extract_points_from_arc(arc1, num_points)
                arc1_points[-1] = [p1.X(),p1.Y(),p1.Z()]
                arc1_points[0] = [p3.X(),p3.Y(),p3.Z()]           
                bspline = self.create_bspline_from_points(arc1_points)
                arc1 = bspline
            else:
                arc1 = arc2
                        
            p2 = gp_Pnt(*pointsA[ip1])
            p4 = gp_Pnt(*pointsB[ip1])
            p6 = gp_Pnt(*pointsCenter[ip1])
            vec3 = gp_Vec(p6,p4)
            vec4 = gp_Vec(p6,p2)
            vec3.Normalize()
            vec4.Normalize()           
            normal_34 = vec3.Crossed(vec4)
            if normal_34.Magnitude() < 1.0e-10:
                normal_34 = gp_Vec(0,0,1)
            self.radius34 = p6.Distance(p4)
            coord34 = gp_Ax2(p6, gp_Dir(normal_34))
            circle34 = gp_Circ(coord34, self.radius34)
            arc2 = GC_MakeArcOfCircle(circle34, p4, p2, False).Value()
            arc2_points = self.extract_points_from_arc(arc2, num_points)
            arc2_points[-1] = [p4.X(),p4.Y(),p4.Z()]
            arc2_points[0] = [p2.X(),p2.Y(),p2.Z()]
            bspline2 = self.create_bspline_from_points(arc2_points)
            arc2 = bspline2

            
            edge1 = BRepBuilderAPI_MakeEdge(arc1).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(arc2).Edge()
            
            sweep = BRepOffsetAPI_ThruSections(False, False, 0.00000000000001)
            sweep.SetSmoothing(False)
            wire_maker = BRepBuilderAPI_MakeWire()
            wire_maker.Add(edge1)
            wire_maker2 = BRepBuilderAPI_MakeWire()
            wire_maker2.Add(edge2)
            # 곡선 추가
            sweep.AddWire(wire_maker.Wire())
            sweep.AddWire(wire_maker2.Wire())
            # 스윕 곡면 생성
            sweep.Build()
            face = sweep.Shape()
            
            faces.append(face)
        return faces
    
    def get_arc_faces_between_closed_wire_points_prev(self, pointsA, pointsCenter,pointsB):
        faces = [] 
        for i in range(len(pointsA)-1):
            print(i)
            ip1 = i + 1
            if ip1 == len(pointsA)-1:
                ip1 = 0
            p1 = gp_Pnt(*pointsA[i])      
            p3 = gp_Pnt(*pointsB[i])
            p5 = gp_Pnt(*pointsCenter[i])
            
            p2 = gp_Pnt(*pointsA[ip1])
            p4 = gp_Pnt(*pointsB[ip1])
            p6 = gp_Pnt(*pointsCenter[ip1])
            
            print("p1 = gp_Pnt(",p1.X(),",",p1.Y(),",",p1.Z(),")")
            print("p2 = gp_Pnt(",p2.X(),",",p2.Y(),",",p2.Z(),")")
            print("p3 = gp_Pnt(",p3.X(),",",p3.Y(),",",p3.Z(),")")
            print("p4 = gp_Pnt(",p4.X(),",",p4.Y(),",",p4.Z(),")")
            print("p5 = gp_Pnt(",p5.X(),",",p5.Y(),",",p5.Z(),")")
            print("p6 = gp_Pnt(",p6.X(),",",p6.Y(),",",p6.Z(),")")
            
            vec1 = gp_Vec(p5,p1)
            vec2 = gp_Vec(p5,p3)
            
            vec3 = gp_Vec(p6,p4)
            vec4 = gp_Vec(p6,p2)
            
            
            vec1.Normalize()
            vec2.Normalize()
            vec3.Normalize()
            vec4.Normalize()
            print("vec1 : ",vec1.X(),vec1.Y(),vec1.Z())
            print("vec2 : ",vec2.X(),vec2.Y(),vec2.Z())
            print("vec3 : ",vec3.X(),vec3.Y(),vec3.Z())
            print("vec4 : ",vec4.X(),vec4.Y(),vec4.Z())
            
            
            normal_12 = vec1.Crossed(vec2)
            normal_34 = vec3.Crossed(vec4)
            if normal_12.Magnitude() < 1.0e-10:
                normal_12 = gp_Vec(0,0,1)
            if normal_34.Magnitude() < 1.0e-10:
                normal_34 = gp_Vec(0,0,1)
                
            print("normal_12 : ",normal_12.X(),normal_12.Y(),normal_12.Z())
            print("normal_34 : ",normal_34.X(),normal_34.Y(),normal_34.Z())
            self.radius12 = p5.Distance(p1)
            self.radius34 = p6.Distance(p4)
            
            coord12 = gp_Ax2(p5, gp_Dir(normal_12))
            coord34 = gp_Ax2(p6, gp_Dir(normal_34))
            
            circle12 = gp_Circ(coord12, self.radius12)
            circle34 = gp_Circ(coord34, self.radius34)
            
            arc1 = GC_MakeArcOfCircle(circle12, p1, p3, False).Value()
            arc2 = GC_MakeArcOfCircle(circle34, p4, p2, False).Value()
            
            num_points = 3  # Number of points to extract
            arc1_points = self.extract_points_from_arc(arc1, num_points)
            arc2_points = self.extract_points_from_arc(arc2, num_points)
            arc1_points[-1] = [p1.X(),p1.Y(),p1.Z()]
            arc1_points[0] = [p3.X(),p3.Y(),p3.Z()]
            arc2_points[-1] = [p4.X(),p4.Y(),p4.Z()]
            arc2_points[0] = [p2.X(),p2.Y(),p2.Z()]
            
            bspline = self.create_bspline_from_points(arc1_points)
            bspline2 = self.create_bspline_from_points(arc2_points)
            arc1 = bspline
            arc2 = bspline2

            
            mode = 1
            if mode == 2:
                arc1 = GC_MakeArcOfCircle(circle12, p1, p3, False).Value()
                arc2 = GC_MakeArcOfCircle(circle34, p2, p4, False).Value()
                edge_arc1 = BRepBuilderAPI_MakeEdge(arc1).Edge()
                edge_arc2 = BRepBuilderAPI_MakeEdge(arc2).Edge()
                
                line1 = GC_MakeSegment(p1, p2).Value()
                line2 = GC_MakeSegment(p3, p4).Value()

                edge_line1 = BRepBuilderAPI_MakeEdge(line1).Edge()
                edge_line2 = BRepBuilderAPI_MakeEdge(line2).Edge()
                
                # Create the surface using BRepOffsetAPI_MakeFilling
                filling = BRepOffsetAPI_MakeFilling()
                filling.Add(edge_arc1,0)
                filling.Add(edge_line1,0)
                filling.Add(edge_arc2,0)
                filling.Add(edge_line2,0)
                try:
                    filling.Build()
                    face = filling.Shape()
                except:
                    pass
                
                
            if mode == 1:
                edge1 = BRepBuilderAPI_MakeEdge(arc1).Edge()
                edge2 = BRepBuilderAPI_MakeEdge(arc2).Edge()
                
                sweep = BRepOffsetAPI_ThruSections(False, False, 0.00000000000001)
                sweep.SetSmoothing(False)
                wire_maker = BRepBuilderAPI_MakeWire()
                wire_maker.Add(edge1)
                wire_maker2 = BRepBuilderAPI_MakeWire()
                wire_maker2.Add(edge2)
                # 곡선 추가
                sweep.AddWire(wire_maker.Wire())
                sweep.AddWire(wire_maker2.Wire())
                # 스윕 곡면 생성
                sweep.Build()
                face = sweep.Shape()
                
            faces.append(face)
        return faces
            
    def get_points_from_edge(self, edge):
        """
        Get the points from an edge
        """
        # Get the curve from the edge
        curve = BRep_Tool.Curve(edge, TopLoc_Location())
        adaptor = BRepAdaptor_Curve(edge)
        # Get the points from the curve
        points = []
        point = adaptor.Value(adaptor.FirstParameter())
        points.append((point.X(), point.Y(), point.Z()))
        point = adaptor.Value(adaptor.LastParameter())
        points.append((point.X(), point.Y(), point.Z()))
        return points
    
    def get_points_from_wire(self, wire):
        """
        Get the points from a wire
        """
        # Get the edges from the wire
        edges = self.get_edges_from_compound(wire)
        points = []
        for edge in edges:
            points.extend(self.get_points_from_edge(edge))
        
        points_reduced = []
        points_reduced.append(points[0])
        for i in range(len(points)-1):
            pt1 = points[i]
            pt2 = points[i+1]
            length = math.sqrt((pt2[0]-pt1[0])**2 + (pt2[1]-pt1[1])**2 + (pt2[2]-pt1[2])**2)
            if length < 1.0e-10:
                pass
            else:
                points_reduced.append(pt2)
                
                
            
        return points_reduced

    def make_close_curve(self, points, distance):
        """
        Create a closed offset curve from a list of points
        """
            # Create an edge from the points
        wire = self.make_wire_from_points(points)
        # Create an offset curve from the edge
        offset = self.make_offset_curve(wire, distance)
        offsetEdges= [] 
        offsetEdges.extend(self.get_edges_from_compound(offset))
        # Get the points from the edges
        edgeList = []
        #edge from wire
        
        #edgeList.append(wire)
        # wire from offsetEdges
        wire = BRepBuilderAPI_MakeWire()
        for edge in offsetEdges:
            wire.Add(edge)
        return wire.Wire()
        
    def create_face(self,p1, p2, p3, p4):
        polygon = BRepBuilderAPI_MakePolygon()
        polygon.Add(p1)
        polygon.Add(p2)
        polygon.Add(p3)
        polygon.Add(p4)
        polygon.Close()
        return BRepBuilderAPI_MakeFace(polygon.Wire()).Face()

    def ramer_douglas_peucker(self, points, epsilon):
        """
        Ramer-Douglas-Peucker 알고리즘으로 점의 수를 줄입니다.
        
        :param points: [[x1, y1], [x2, y2], ...] 형태의 점 리스트 (2D 좌표)
        :param epsilon: 허용 오차 (값이 작을수록 더 많은 점이 유지됨)
        :return: 줄어든 점 리스트
        """
        if len(points) < 3:
            return points

        # 시작점과 끝점을 연결하는 직선에서 가장 먼 점을 찾음
        start, end = points[0], points[-1]
        line = np.array(end) - np.array(start)
        max_dist = 0
        index = 0
        
        for i in range(1, len(points) - 1):
            # 점에서 직선까지의 거리 계산
            point = np.array(points[i])
            dist = np.linalg.norm(np.cross(line, point - start)) / np.linalg.norm(line)
            if dist > max_dist:
                max_dist = dist
                index = i

        # 최대 거리 점이 허용 오차보다 크면 해당 점을 기준으로 분할
        if max_dist > epsilon:
            left = self.ramer_douglas_peucker(points[:index + 1], epsilon)
            right = self.ramer_douglas_peucker(points[index:], epsilon)
            return left[:-1] + right
        else:
            # 시작점과 끝점만 유지
            return [start, end]
        
    def GenerateShieldCanShape(self):
        self.shieldCanShapeList = [] 
        curi = 0
        for shieldCan in self.shieldCanList:
            curpsid = self.shieldCanpsidList[curi]
            curi = curi + 1
            xList = shieldCan[0]
            yList = shieldCan[1]
            radius = shieldCan[2]
            solidThickness = shieldCan[3]
            thickness = self.thickness
            padWidth = shieldCan[4]
            offset = shieldCan[5]
            xListCut = shieldCan[6]
            yListCut = shieldCan[7]
           
            matID = shieldCan[8]
            detailMode = shieldCan[9]
            if len(xList) != len(yList):
                print("Shield Can Error")
                continue
           
            if detailMode == True:
                points = [] 
                for i in range(len(xList)):
                    x = xList[i]
                    y = yList[i]
                    points.append([x,y])
                    
                points.pop()
                epsilon = 0.2
                points = self.ramer_douglas_peucker(points, epsilon)
                
                # points의 배열 중간에 있는 값부터 시작해서 points의 끝까지 입력 후 points의 처음부터 중간값 바로 전까지를 추가한 new_points 생성
                points = points[len(points)//2:] + points[:len(points)//2-1]
                points = self.ramer_douglas_peucker(points, epsilon)
                 
                polygon_shape = Polygon(points)
                offset_polygon_shape = polygon_shape.buffer(0.1, resolution=1)
                offset_polygon_coords = np.array(offset_polygon_shape.exterior.coords)
                
                point3DList = [] 
                for i in range(len(offset_polygon_coords)):
                    x = offset_polygon_coords[i][0] + self.posX
                    y = offset_polygon_coords[i][1] + self.posY
                    point3DList.append([x,y,self.posZ +solidThickness/2.0])
                                
                wireOutBottom = self.make_close_curve(point3DList,-0.1-offset)
                wireInBottom = self.make_close_curve(point3DList,-0.1-offset-padWidth)
                for i in range(len(point3DList)):
                    point3DList[i][2] += thickness -radius
                wireInTop = self.make_close_curve(point3DList,-0.1-offset-padWidth)
                wireTopRadiusCenter = self.make_close_curve(point3DList,-0.1-offset-padWidth-radius)
                for i in range(len(point3DList)):
                    point3DList[i][2] += radius
                wireTop = self.make_close_curve(point3DList,-0.1-offset-padWidth-radius)
                point3D_ListCut = []
                for i in range(len(xListCut)):
                    x = xListCut[i] + self.posX
                    y = yListCut[i] + self.posY
                    point3D_ListCut.append([x,y,self.posZ + solidThickness/2.0 + thickness])
                
                
                pointsOutBottom = self.get_points_from_wire(wireOutBottom)
                pointsInBottom = self.get_points_from_wire(wireInBottom)
                pointsInTop = self.get_points_from_wire(wireInTop)
                pointsTopRadiusCenter = self.get_points_from_wire(wireTopRadiusCenter)
                pointsTop = self.get_points_from_wire(wireTop)
                
                faces1 = self.get_faces_between_closed_two_wire_points(pointsOutBottom,pointsInBottom)
                faces2 = self.get_faces_between_closed_two_wire_points(pointsInBottom,pointsInTop)
                
                '''wireA = wireInTop
                wireB = wireTop

                thru_sections = BRepOffsetAPI_ThruSections()
                thru_sections.AddWire(wireA)
                thru_sections.AddWire(wireB)
                thru_sections.Build()'''

                #face3 = thru_sections.Shape()
                faces3 = self.get_arc_faces_between_closed_wire_points(pointsInTop,pointsTopRadiusCenter, pointsTop)
                #faces3 = [face3]
                curShapes = []
                for face in faces1:
                    curShapes.append(face)
                for face in faces2:
                    curShapes.append(face)
                for face in faces3:
                    curShapes.append(face)      
                #combine curshapes to TopoDS_Compound
                compound = TopoDS_Compound()
                builder = BRep_Builder()
                builder.MakeCompound(compound)
                for shape in curShapes:
                    builder.Add(compound,shape)
                    
                if len(xListCut) == 0:
                    face4 = self.get_face_from_points(pointsTop)   
                    curShapes.append(face4)  
                    builder.Add(compound,face4)
                else:
                    face4 = self.get_face_from_points_and_cut_points(pointsTop,point3D_ListCut)
                    curShapes.append(face4)
                    builder.Add(compound,face4)
                
                self.shieldCanShapeList.append(compound)
 
                    
                if self.meshGenerationMode:
                    curMatID = matID
                    curMeshSizeSmall = self.meshSizeInPlane
                    curMeshSizeLarge = self.meshSizeInPlane
                    
                    meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                    meshManager.SetPath(self.meshPath)
                    meshManager.SetName("{0}_ShieldCanMesh{1}".format(self.name,self.ith))
                    meshManager.mesh_shape_quad_2D(compound,curMeshSizeSmall, self.maxNID, self.maxEID, solidThickness, "", 5)
                    self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                    self.maxPID = self.maxPID + 1
                    meshManager.part.SetID(self.maxPID)
                    if matID != -1:
                        meshManager.part.SetMaterialID(matID)
                    self.shieldCanMeshList.append(meshManager)
                    self.shieldCanMeshpsidList.append(curpsid)
            
                    
                '''

                polygon_shape2 = Polygon(offset_polygon_coords)
                curOffset = offset+0.1
                offset_polygon_shape2 = polygon_shape2.buffer(-curOffset, resolution=1)
                offset_polygon_coords = np.array(offset_polygon_shape2.exterior.coords)

                polygon_shape3 = Polygon(offset_polygon_coords)
                offset_outer_pad_shape = polygon_shape3.buffer(padWidth, resolution=1)
                offset_outer_pad_coords = np.array(offset_outer_pad_shape.exterior.coords)  
                
                polygon_shape4 = Polygon(offset_polygon_coords)
                offset_top_inner_shape = polygon_shape4.buffer(-radius, resolution=1)
                offset_top_inner_coords = np.array(offset_top_inner_shape.exterior.coords)
                
                point_3D_List_Outer_Pad = [] 
                point_3D_List_Bottom_Wall = []
                point_3D_List_Top_Wall = [] 
                point_3D_List_Top_Wall_Center_Circle = [] 
                point_3D_List_Top_Wall_Inner = [] 
                
                for i in range(len(offset_outer_pad_coords)):
                    x = offset_outer_pad_coords[i][0] + self.posX
                    y = offset_outer_pad_coords[i][1] + self.posY
                    point_3D_List_Outer_Pad.append([x,y,self.posZ])
                
                for i in range(len(offset_polygon_coords)):
                    x = offset_polygon_coords[i][0] + self.posX
                    y = offset_polygon_coords[i][1] + self.posY
                    point_3D_List_Bottom_Wall.append([x,y,self.posZ])
                    point_3D_List_Top_Wall.append([x,y,self.posZ+thickness-radius])
                
                for i in range(len(offset_top_inner_coords)):
                    x = offset_top_inner_coords[i][0] + self.posX
                    y = offset_top_inner_coords[i][1] + self.posY
                    point_3D_List_Top_Wall_Center_Circle.append([x,y,self.posZ+thickness-radius])
                    point_3D_List_Top_Wall_Inner.append([x,y,self.posZ+thickness])
                '''
                
              
                
            else:
                point3DList = []
                for i in range(len(xList)):
                    x = xList[i] + self.posX
                    y = yList[i] + self.posY
                    point3DList.append([x,y,self.posZ])
                
                
                if self.geomGenerationType == "Solid":
                    solidThickness = shieldCan[3]
                    wireOutBottom = self.make_close_curve(point3DList,radius + solidThickness)
                    wireInBottom = self.make_close_curve(point3DList,radius + solidThickness*0.001)
                    

                
                    #self.shieldCanShapeList.append(solidsubst)
                    for i in range(len(point3DList)):
                        point3DList[i][2] += thickness -solidThickness/2.0
                    wirebottom = self.make_close_curve(point3DList,radius*0.01)
                    for i in range(len(point3DList)):
                        point3DList[i][2] += solidThickness
                    wiretop = self.make_close_curve(point3DList,radius*0.01)
                    
                    for i in range(len(point3DList)):
                        point3DList[i][2] -= radius + solidThickness/2.0 
                    wireInTop = self.make_close_curve(point3DList,radius)
                    wireOutTop = self.make_close_curve(point3DList,radius+solidThickness)            
                                        
                    facebottom = BRepBuilderAPI_MakeFace(wirebottom).Face()                
                    solidbottom = BRepPrimAPI_MakePrism(facebottom, gp_Vec(0,0,solidThickness)).Shape()
                    #self.shieldCanShapeList.append(solidbottom)
                    points_bottom = self.get_points_from_wire(wirebottom)
                    points_top = self.get_points_from_wire(wiretop)
                    points_outtop = self.get_points_from_wire(wireOutTop)
                    points_intop = self.get_points_from_wire(wireInTop) 
                    
                    points_outbottom = self.get_points_from_wire(wireOutBottom)
                    points_inbottom = self.get_points_from_wire(wireInBottom)
                    
                    wireOutTop = self.make_wire_from_points(points_outtop)
                    wireInTop = self.make_wire_from_points(points_intop)
                    wireOutBottom = self.make_wire_from_points(points_outbottom)
                    wireInBottom = self.make_wire_from_points(points_inbottom)
                    for i in range(len(points_inbottom)):
                        ip1 = i + 1
                        if ip1 == len(points_inbottom):
                            ip1 = 0
                        p1 = gp_Pnt(*points_inbottom[i])
                        p2 = gp_Pnt(*points_inbottom[ip1])
                        p3 = gp_Pnt(*points_outbottom[ip1])
                        p4 = gp_Pnt(*points_outbottom[i])
                        p5 = gp_Pnt(*points_intop[i])
                        p6 = gp_Pnt(*points_intop[ip1])
                        p7 = gp_Pnt(*points_outtop[ip1])
                        p8 = gp_Pnt(*points_outtop[i])
                        face1 = self.create_face(p1, p4, p3, p2)  # Bottom
                        face2 = self.create_face(p5, p6, p7, p8)  # Top
                        face3 = self.create_face(p1, p2, p6, p5)  # Front
                        face4 = self.create_face(p2, p3, p7, p6)  # Right
                        face5 = self.create_face(p3, p4, p8, p7)  # Back
                        face6 = self.create_face(p4, p1, p5, p8)  # Left
                        # Create a solid connecting 8 points which are the corners of hexahedron
                        sewing = BRepBuilderAPI_Sewing()
                        sewing.Add(face1)
                        sewing.Add(face2)
                        sewing.Add(face3)
                        sewing.Add(face4)
                        sewing.Add(face5)
                        sewing.Add(face6)
                        sewing.Perform()
                        shell = sewing.SewedShape()  
                        solid_maker = BRepBuilderAPI_MakeSolid()
                        solid_maker.Add(shell)
                        solid = solid_maker.Solid()
                        self.shieldCanShapeList.append(solid)
                        
                    '''wireOutTop = self.make_wire_from_points(points_outtop)
                    wireInTop = self.make_wire_from_points(points_intop)
                    faceOut = BRepBuilderAPI_MakeFace(wireOutTop).Face()
                    faceIn = BRepBuilderAPI_MakeFace(wireInTop).Face() 
                    solidout = BRepPrimAPI_MakePrism(faceOut, gp_Vec(0,0,-thickness+radius)).Shape()
                    solidin = BRepPrimAPI_MakePrism(faceIn, gp_Vec(0,0,-thickness+radius)).Shape()               
                    solidsubst = BRepAlgoAPI_Cut(solidout,solidin).Shape()'''
                    
                    for i in range(len(points_bottom)):
                        ip1 = i + 1
                        if ip1 == len(points_bottom):
                            ip1 = 0
                        p1 = gp_Pnt(*points_bottom[i])
                        p2 = gp_Pnt(*points_bottom[ip1])
                        p3 = gp_Pnt(*points_top[ip1])
                        p4 = gp_Pnt(*points_top[i])
                    

                        p5 = gp_Pnt(*points_intop[i])
                        p6 = gp_Pnt(*points_intop[ip1])
                        p7 = gp_Pnt(*points_outtop[ip1])
                        p8 = gp_Pnt(*points_outtop[i])
                    
                        face1 = self.create_face(p1, p4, p3, p2)  # Bottom
                        face2 = self.create_face(p5, p6, p7, p8)  # Top
                        face3 = self.create_face(p1, p2, p6, p5)  # Front
                        face4 = self.create_face(p2, p3, p7, p6)  # Right
                        face5 = self.create_face(p3, p4, p8, p7)  # Back
                        face6 = self.create_face(p4, p1, p5, p8)  # Left
                        # Create a solid connecting 8 points which are the corners of hexahedron
                        sewing = BRepBuilderAPI_Sewing()
                        sewing.Add(face1)
                        sewing.Add(face2)
                        sewing.Add(face3)
                        sewing.Add(face4)
                        sewing.Add(face5)
                        sewing.Add(face6)
                        sewing.Perform()
                        shell = sewing.SewedShape()  
                        solid_maker = BRepBuilderAPI_MakeSolid()
                        solid_maker.Add(shell)
                        solid = solid_maker.Solid()
                        self.shieldCanShapeList.append(solid)
                    '''
                    # connecting wirein to wirebottom and connecting wireout to wiretop
                    section_maker = BRepOffsetAPI_ThruSections(False)
                    section_maker.AddWire(wirebottom)
                    section_maker.AddWire(wireInTop)
                    section_maker.Build()

                    # Get the resulting shape
                    insideShape = section_maker.Shape()
                    section_maker_out = BRepOffsetAPI_ThruSections(False)
                    section_maker_out.AddWire(wiretop)
                    section_maker_out.AddWire(wireOutTop)
                    section_maker_out.Build()
                    inface = section_maker.Shape()
                    outface = section_maker_out.Shape()
                    #self.shieldCanShapeList.append(inface)    
                    #self.shieldCanShapeList.append(outface)                     
                    '''
                        
                    '''
                    section_maker = BRepOffsetAPI_ThruSections(True)
                    section_maker.AddWire(wirebottom)
                    section_maker.AddWire(wiretop)
                    section_maker.AddWire(wireOutTop)
                    section_maker.AddWire(wireInTop)
                    section_maker.AddWire(wirebottom)
                    section_maker.Build()
                    resulting_shape = section_maker.Shape()
                    #self.shieldCanShapeList.append(resulting_shape)   
                    '''
                    #combine solidbottom, solidsubst, resulting_shape
                    self.shieldCanShapeList.append(solidbottom)
                    #self.shieldCanShapeList.append(solidsubst)
                    # remove duplicated volume
                    '''
                    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
                    cut = BRepAlgoAPI_Cut(resulting_shape,solidbottom).Shape()
                    cut = BRepAlgoAPI_Cut(cut,solidsubst).Shape()
                    self.shieldCanShapeList.append(cut) 
                    '''
                
                
                else:
                    for i in range(len(point3DList)):
                        point3DList[i][2] += thickness-radius
                    
                    wire = self.make_close_curve(point3DList,radius)
                    pointsWall = self.get_points_from_wire(wire)
                    wire = self.make_wire_from_points(pointsWall)
                    #extrude edge to z-direction and make face
                    prism = BRepPrimAPI_MakePrism(wire,gp_Vec(0,0,-thickness-radius))
                    shape = prism.Shape()
                    self.shieldCanShapeList.append(shape)
                    
                    for i in range(len(point3DList)):
                        point3DList[i][2] += radius
                    wire2 = self.make_close_curve(point3DList,radius/100.0)
                    pointsTop = self.get_points_from_wire(wire2)
                    wire2 = self.make_wire_from_points(pointsTop) 
                    face2 = BRepBuilderAPI_MakeFace(wire2).Face()
                    
                    self.shieldCanShapeList.append(face2)
                    
                    for i in range(len(pointsWall)):
                        ip1 = i + 1
                        if ip1 == len(pointsWall):
                            ip1 = 0
                        p1 = gp_Pnt(*pointsWall[i])
                        p2 = gp_Pnt(*pointsWall[ip1])
                        p3 = gp_Pnt(*pointsTop[ip1])
                        p4 = gp_Pnt(*pointsTop[i])
                        face1 = self.create_face(p1, p4, p3, p2)
                        self.shieldCanShapeList.append(face1)
                    
                        
                    '''wire = self.make_close_curve(point3DList,-radius/100.0)
                    
                    #extrude edge to z-direction and make face
                    prism = BRepPrimAPI_MakePrism(wire,gp_Vec(0,0,thickness-radius))
                    shape = prism.Shape()
                    self.shieldCanShapeList.append(shape)
                    for i in range(len(point3DList)):
                        point3DList[i][2] += thickness
                    
                    
                    wire2 = self.make_close_curve(point3DList,-radius)
                    point3DListModified = self.get_points_from_wire(wire2)
                    point3DListModified_reduced = []
                    point3DListModified_reduced.append(point3DListModified[0])

                    for i in range(len(point3DListModified)):
                        if i == len(point3DListModified)-1:
                            ip1 = 0
                        else:
                            ip1 = i+1
                        x1 = point3DListModified[i][0]
                        y1 = point3DListModified[i][1]
                        x2 = point3DListModified[ip1][0]
                        y2 = point3DListModified[ip1][1]
                        d = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                        if d < 1.0*radius:
                            pass
                        else:
                            point3DListModified_reduced.append(point3DListModified[ip1])
                    wire2 = self.make_wire_from_points(point3DListModified_reduced)
                            
                        
                    
                    for i in range(len(point3DList)):
                        point3DList[i][2] -= radius
                    wire1 = self.make_wire_from_points(point3DList)
                    #wire1 = self.make_close_curve(point3DList,-radius/100.0)

                    face2 = BRepBuilderAPI_MakeFace(wire2).Face()
                    
            
                    self.shieldCanShapeList.append(face2)
                    
                    # Create a face connecting the two wires using BRepOffsetAPI_ThruSections
                    section_maker = BRepOffsetAPI_ThruSections(True)
                    section_maker.AddWire(wire1)
                    section_maker.AddWire(wire2)
                    section_maker.Build()

                    # Get the resulting shape
                    resulting_shape = section_maker.Shape()
                    self.shieldCanShapeList.append(resulting_shape)
                    '''
                    '''from OCC.Core.GCPnts import GCPnts_AbscissaPoint

                    wire_explorer = TopExp_Explorer(resulting_shape, TopAbs_WIRE)
                    newWireList = []
                    min_edge_length = radius/5.0
                    while wire_explorer.More():
                        wire = topods.Wire(wire_explorer.Current())
                        newWireList.append(wire)
                        wire_explorer.Next()
                        
                    # Create a face from the wire
                    #from OCC.Core.ShapeAnalysis import ShapeAnalysis_Wire
                    #from OCC.Core.ShapeFix import ShapeFix_Wire
                    for wire in newWireList:
                        face = BRepBuilderAPI_MakeFace(wire)
                        
                        self.shieldCanShapeList.append(face.Face())
                    '''

                    '''from OCC.Core.BOPAlgo import BOPAlgo_Splitter
                    from OCC.Core.GCPnts import GCPnts_AbscissaPoint
                    # Splitter to split edges
                    splitter = BOPAlgo_Splitter()
                    splitter.AddArgument(resulting_shape)
                    min_edge_length = 0.5

                    # Explore edges and check their lengths
                    edge_explorer = TopExp_Explorer(resulting_shape, TopAbs_EDGE)
                    while edge_explorer.More():
                        edge = topods.Edge(edge_explorer.Current())
                        curve, first, last = BRep_Tool.Curve(edge)
                        #geom_curve to adaptor3d_curve
                        adp_curve = BRepAdaptor_Curve(edge)
                        length = GCPnts_AbscissaPoint().Length(adp_curve, first, last)
                        if length < min_edge_length:
                            splitter.AddArgument(edge)  # Add short edges to the splitter
                        edge_explorer.Next()

                    # Perform the split operation
                    splitter.Perform()
                    result_shape = splitter.Shape()
                    self.shieldCanShapeList.append(result_shape)
                    '''

                self.ith += 1  
                
                
            
            

    def GenerateShape(self):
        print("Generate Shape of PackageLayerDefined")                        
        self.GenerateRectangleTubeShape()
        print("Rectangle Tube Shape Generated")        
        self.GenerateRectangleCircleCutShape()
        print("Rectangle Circle Cut Shape Generated")        
        self.GenerateRectangleFilletCutShape()
        print("Rectangle Fillet Cut Shape Generated")        
        self.GenerateBoxCrackShape()
        print("Box Crack Shape Generated")
        self.GeneratePolynomialCutPartShapes()
        print("Polynomial Cut Part Shape Generated")        
        self.GeneratePolynomialPartShapes()
        print("Polynomial Part Shape Generated")        
        self.GeneratePolynomialSweepShape()
        print("Polynomial Sweep Shape Generated")        
        self.GenerateDetailSolderShapes()
        print("Detail Solder Shape Generated")
        #print("Generate Shape of PackageLayer")                
        self.GenerateImageShape()
        print("Image shape generated")
        self.GenerateCylinderShapes()
        print("Cylinder shape generated")
        self.GenerateBoxShape()
        print("Box shape generated")
        self.GenerateShieldCanShape()
        print("Shield Can shape generated")
        self.GenerateSTLShape()
        print("STL shape generated")
        self.GenerateStepShape()
        print("Step shape generated")
        self.GenerateGMSHShape()
        print("GMSH shape generated")
        self.shape = None

        if self.xLength>0 and self.yLength>0:
            # Package MainBody 
            leftBottomX = self.posX - self.xLength/2
            leftBottomY = self.posY - self.yLength/2
            leftBottomZ = self.posZ        
            self.shape = BRepPrimAPI_MakeBox(gp_Pnt(leftBottomX,leftBottomY,leftBottomZ),self.xLength,self.yLength,self.thickness).Shape()
            print("Main Body Generated") 
            initShape = self.shape
            cut = BRepAlgoAPI_Cut()
            L1 = TopTools_ListOfShape()
            L1.Append(self.shape)
            L2 = TopTools_ListOfShape()
            i = 0 

            for rectangleTube_shape in self.rectangleTubeShapeList:
                L2.Append(rectangleTube_shape)
                i += 1
                print("Rectangle Tube Shape " + str(i) + " Appended")
            
            for rectangleCircleCut_shape in self.rectangleCircleCutShapeList:
                L2.Append(rectangleCircleCut_shape)
                i += 1
                print("Rectangle Circle Cut Shape " + str(i) + " Appended")                
            
            for rectangleFilletCut_shape in self.rectangleFilletCutShapeList:
                L2.Append(rectangleFilletCut_shape)
                i += 1
                print("Rectangle Fillet Cut Shape " + str(i) + " Appended")

            for box_crack_shape in self.boxCrackShapeList:
                L2.Append(box_crack_shape)
                i += 1
                print("Box Crack Shape " + str(i) + " Appended")

            for detail_shape in self.detailPolynomialCutPartShapeList:
                L2.Append(detail_shape)
                i += 1
                print("Detail Polynomial Cut Part Shape " + str(i) + " Appended")
            
            for detail_shape in self.detailPolynomialPartShapeList:
                L2.Append(detail_shape)
                i += 1
                print("Detail Polynomial Part Shape " + str(i) + " Appended")            
            
            for polynomial_sweep_shape in self.polynomialSweepShapeList:
                L2.Append(polynomial_sweep_shape)
                i += 1
                print("Polynomial Sweep Shape " + str(i) + " Appended")

            for detail_shape in self.detailSolderShapeList:
                L2.Append(detail_shape)
                i += 1
                print("Detail Solder Shape " + str(i) + " Appended")
            
            for image_shape in self.imageShapeList:
                L2.Append(image_shape)
                i += 1
                print("Image Shape " + str(i) + " Appended")
                
            for cylinder_shape in self.cylinderShapeList:
                L2.Append(cylinder_shape)
                i += 1
                print("Cylinder Shape " + str(i) + " Appended")
            for box_shape in self.boxShapeList:
                L2.Append(box_shape)
                i += 1
                print("Box Shape " + str(i) + " Appended")
            for shieldCan_shape in self.shieldCanShapeList:
                L2.Append(shieldCan_shape)
                i += 1
                print("Shield Can Shape " + str(i) + " Appended")  
            for stl_shape in self.stlShapeList:
                L2.Append(stl_shape)
                i += 1
                print("STL Shape " + str(i) + " Appended")
            for step_shape in self.stepShapeList:
                L2.Append(step_shape)
                i += 1
                print("Step Shape " + str(i) + " Appended")       
            for msh_shape in self.mshShapeList:
                L2.Append(msh_shape)
                i += 1
                print("GMSH Shape " + str(i) + " Appended")
            if i>0:
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.0000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                    self.shape = initShape
                else:
                    print("Cut Success")
                    self.shape = cut.Shape()
            if self.meshGenerationMode:
                meshManager = KooMeshManagerGMSH(sectionMan=self.sectionManager,materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                meshManager.SetPath(self.meshPath)
                meshManager.SetName("{0}_PackageMesh".format(self.name))
                meshManager.mesh_shape(self.shape,self.meshSizeInPlane,self.meshSizeInPlane,3,None,self.maxNID,self.maxEID)
                self.maxNID, self.maxEID = meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                meshManager.part.SetID(self.maxPID)
                if self.packageMeshMatID != -1:
                    meshManager.part.SetMaterialID(self.packageMeshMatID)

                self.packageMesh = meshManager
            
        return self.shape
