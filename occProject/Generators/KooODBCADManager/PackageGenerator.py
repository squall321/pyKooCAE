import sys 
import os
import numpy as np
import re
from collections import Counter
from math import *
from scipy.spatial import KDTree
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

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf, gp_Ax1, gp_Pln
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_WIRE, TopAbs_FACE, TopAbs_SOLID, TopAbs_COMPOUND
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.TopLoc import TopLoc_Location

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

from OCC.Core.STEPControl import STEPControl_Reader

if __name__ == "__main__":
    path = os.path.join(os.getcwd(), "occProject\Generators")
    sys.path.append(path)
    
from KooCAEManager.KooNode import NodeManager, NodeSetManager, NodeSet, Node
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooContact import *
from KooCAEManager.KooSegment import *
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH, KooMeshManagerList
from KooCAEManager.KooPart import KooPartManager, KooPart, KooPartComposite
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooSection import *
from KooODBCADManager.PackageLayer import *
from KooODBCADManager.PackageWarpageLayer import *



class PackageUserdefined:

    def __init__(self,xOrigin=0.0,yOrigin=0.0,zOrigin=0.0,rotation = 0, mirror = False, isTop = True, totalThickness = 0.0,matMan : KooMaterialManager = None, secMan : KooSectionManager = None, nodeSetMan : NodeSetManager = None, bndMan : KooBoundaryNodeManager = None, loadMan : KooLoadManager = None, defineMan : KooDefineManager = None, contactMan : KooContactManager = None, segMan : KooSegmentSetManager = None):
        self.layerList = []
        self.outFileName = "output.txt"
        self.xOrigin = xOrigin
        self.yOrigin = yOrigin
        self.zOrigin = zOrigin
        self.rotation = rotation
        self.mirror = mirror
        self.isTop = isTop
        self.totalThickness = totalThickness
        self.partMan = None
        self.partPSIDtoPartID = {}
        self.partPIDtoLayerNum = {}
        
        self.sSetIDtoKey = {}
        self.sSetKeytoID = {}
        
        self.nSetIDtoKey = {}
        self.nSetKeytoID = {} 
         
        self.contactOptions = [] 
        self.loadOptions = [] 
        self.defineOptions = [] 
        self.boundaryOptions = [] 
        
        self.nastranAddScript = ""
        self.dynaAddScript = ""
        self.abaqusAddScript = ""
        self.ansysAddScript = ""
        
        
        if matMan != None:
            self.materialManager = matMan
        else:
            self.materialManager = KooMaterialManager()
        if secMan != None:
            self.sectionManager = secMan
        else:
            self.sectionManager = KooSectionManager()   
        if nodeSetMan != None:
            self.nodeSetManager = nodeSetMan
        else:
            self.nodeSetManager = NodeSetManager()
            
        if bndMan != None:
            self.boundaryNodeManager = bndMan
        else:
            self.boundaryNodeManager = KooBoundaryNodeManager()
        
        if loadMan != None:
            self.loadManager = loadMan
        else:
            self.loadManager = KooLoadManager()
        
        if defineMan != None:
            self.defineManager = defineMan
        else:
            self.defineManager = KooDefineManager()
            
        if contactMan != None:
            self.contactManager = contactMan
        else:
            self.contactManager = KooContactManager()
        
        if segMan != None:  
            self.segmentManager = segMan
        else:
            self.segmentManager = KooSegmentSetManager()
            
        
        self.nodeManager = None
        

        pass
    

    def AddPackageLayer(self,layer : PackageLayerDefined):
        self.layerList.append(layer)

    def ImportPackage(self, filePath):
        f = open(filePath, 'r')
        line = f.readline()        
        totalThickness = 0.0
        curZLoc = 0.0
        # read line by line
        psid = 0
        nsKey = 0
        ssKey = 0 
        
        
        
        while True:
            
            if not line: break
            #print(line)
            if line[0] == '#':
                line = f.readline()
                continue
            elif line[0] == '*':
                line = line.replace('\n','')
                svector = line.split(',')
                if svector[0] == "*End":
                    break
                elif svector[0] == "*Material":
                    line = f.readline()
                    matFileName = line.replace('\n','')
                    print("Material File Name : ",matFileName)
                    fileFolder = os.path.dirname(filePath)
                    matFilePath = os.path.join(fileFolder,matFileName)
                    self.materialManager.ImportMaterial(matFilePath)

                    line = f.readline()
                elif svector[0] == "*Translation":                
                    print("Change Translation from : ",self.xOrigin,self.yOrigin,self.zOrigin)
                    x = float(svector[1])
                    y = float(svector[2])
                    z = float(svector[3])
                    self.xOrigin = x
                    self.yOrigin = y
                    self.zOrigin = z
                    
                    print("to : ",x,y,z)
                    line = f.readline()
                elif svector[0] == "*Rotation":
                    print("Change Rotation from : ",self.rotation)
                    rotation = int(svector[1])
                    self.rotation = rotation
                    print("to : ",rotation)
                    line = f.readline()
                elif svector[0] == "*Mirror":
                    print("Change Mirror from : ",self.mirror)
                    if svector[1].lower() == 'true':
                        self.mirror = True
                    else:
                        self.mirror = False
                    print("to : ",self.mirror)
                    line = f.readline()
                elif svector[0] == "*IsTop":
                    print("Change IsTop from : ",self.isTop)
                    if svector[1].lower() == 'true':
                        self.isTop = True
                    else:
                        self.isTop = False
                    line = f.readline() 
                elif svector[0] == "*Layer":
                    layerGenMode = "Defined"
                    
                    if len(svector)  >= 3:
                        layerGenMode = svector[2]
                        if layerGenMode == "Warped":
                            layer = PackageWarpedLayer(svector[1]) 
                        elif layerGenMode == "Defined":
                            layer = PackageLayerDefined(svector[1])
                        elif layerGenMode == "SolderJointWarped":
                            layer = SolderJointsLayer(svector[1])    
                 
                    elif len(svector) == 2:
                        layer = PackageLayerDefined(svector[1],nSetMan = self.nodeSetManager)
                    else:
                        layer = PackageLayerDefined(nSetMan = self.nodeSetManager)
                    print("Layer Created")
                    layerMatID = -1
                    if layerGenMode == "SolderJointWarped":
                        while True:
                            line = f.readline()
                            if not line:break
                            line = line.replace('\n','')
                            svector = line.split(',')
                            if svector[0][0] == "*":
                                print("Layer End")
                                break
                            elif svector[0][0] == "#":
                                continue
                            elif svector[0] == "WarpageVariables":
                               
                                warpageVariables = [] 
                                warpageVariables.append(svector[1])
                                warpageVariables.append(float(svector[2])) # xloc
                                warpageVariables.append(float(svector[3])) # yloc
                                warpageVariables.append(float(svector[4])) # zloc
                                warpageVariables.append(float(svector[5])) # xleft
                                warpageVariables.append(float(svector[6])) # xright
                                warpageVariables.append(float(svector[7])) # ybottom
                                warpageVariables.append(float(svector[8])) # ytop
                                warpageVariables.append(svector[9]) # xmode
                                warpageVariables.append(float(svector[10])) # ymode
                                layer.SetWarpageVariables(warpageVariables)
                            elif svector[0] == "WarpageVariablesTop":
                                warpageVariablesTop = [] 
                                warpageVariablesTop.append(svector[1])
                                warpageVariablesTop.append(float(svector[2])) # xloc
                                warpageVariablesTop.append(float(svector[3])) # yloc    
                                warpageVariablesTop.append(float(svector[4])) # zloc
                                warpageVariablesTop.append(float(svector[5])) # xleft
                                warpageVariablesTop.append(float(svector[6])) # xright
                                warpageVariablesTop.append(float(svector[7])) # ybottom
                                warpageVariablesTop.append(float(svector[8])) # ytop
                                warpageVariablesTop.append(svector[9]) # xmode
                                warpageVariablesTop.append(float(svector[10])) # ymode
                                layer.SetWarpageVariablesTop(warpageVariablesTop)
                                    
                                
                            elif svector[0] == "Location":
                                x = float(svector[1])
                                y = float(svector[2])
                                if len(svector) >= 4:
                                    z = float(svector[3])      
                                    curZLoc = z                      
                                    layer.SetPositionPad(x,y,z)                                    
                                else:
                                    #z = totalThickness                                    
                                    layer.SetPositionPad(x,y,curZLoc)
                                print("Location:  ",x,y,z)
                            elif svector[0] == "LocationMisalignment":
                                x = float(svector[1])
                                y = float(svector[2])
                                x2 = float(svector[3])
                                y2 = float(svector[4])
                                if len(svector) >= 6:
                                    z = float(svector[5])
                                    curZLoc = z                                    
                                else:
                                    z = curZLoc
                                layer.SetPositionPad(x,y,z,x2,y2)
                                print("Location Misalignment:  ",x,y,z,x2,y2)
                                
                            elif svector[0] == "Length":
                                xLength = float(svector[1])
                                yLength = float(svector[2])
                                materialID = -1
                                if len(svector) >= 4:
                                    materialID = int(svector[3])
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                layer.SetLength(curpsid,xLength,yLength,materialID)
                                print("Length: ",xLength,yLength)
                            elif svector[0] == "MeshGenerationType":
                                meshGenerationType = svector[1].replace('\n','')
                                if len(svector) >= 3:
                                    meshType = svector[2].replace('\n','')
                                else:
                                    meshType = "Tetra"
                                layer.SetMeshGenerationType(meshGenerationType)
                                layer.SetMeshType(meshType)
                                print("MeshGenerationType: ",meshGenerationType)
                            elif svector[0] == "MeshPath":
                                meshPath = svector[1].replace('\n','')
                                layer.SetMeshPath(meshPath)
                                print("MeshPath: ",meshPath)
                            elif svector[0] == "MeshSizeInPlane":
                                meshSizeInPlane = float(svector[1])
                                layer.SetMeshSizeInPlane(meshSizeInPlane)
                                print("MeshSizeInPlane: ",meshSizeInPlane)
                            elif svector[0] == "NumberofElementinThickness":
                                numberofElementinThickness = int(svector[1])
                                layer.SetNumberofElementinThickness(numberofElementinThickness)
                                print("NumberofElementinThickness: ",numberofElementinThickness)
                            elif svector[0] == "ConformalBufferThickness":
                                conformalBufferThickness = float(svector[1])
                                layer.SetConformalBufferThickness(conformalBufferThickness)
                                print("ConformalBufferThickness: ", conformalBufferThickness)
                            elif svector[0] == "Thickness":
                                thickness = float(svector[1])
                                layer.SetThickness(thickness)
                                totalThickness += thickness
                                curZLoc += thickness
                                print("Thickness: ",thickness)
                            elif svector[0] == "MaterialID":
                                layerMatID = int(svector[1])
                            elif svector[0] == "DetailSolder":
                                if svector[1].lower() == "true":
                                    layer.SetDetailSolder(True)
                                else:
                                    layer.SetDetailSolder(False)
                            elif svector[0] == "MisalignmentAngle":
                                bottomAngle = float(svector[1])
                                topAngle = float(svector[2])
                                layer.SetRotationPad(bottomAngle,topAngle)
                            elif svector[0] == "SurfaceTension":
                                surfaceTension = float(svector[1])
                                layer.SetSurfaceTension(surfaceTension)
                            elif svector[0] == "Gravity":
                                gravity = float(svector[1])
                                layer.SetGravity(gravity)
                            elif svector[0] == "Density":
                                density = float(svector[1])
                                layer.SetSolderDensity(density)
                            elif svector[0] == "Force":
                                force = float(svector[1])
                                layer.SetForce(force)
                            elif svector[0] == "SMD":
                                modeType = "SMD"
                                name = svector[1]
                                bottomPadLocX = float(svector[2])
                                bottomPadLocY = float(svector[3])
                                bottomPadRadius = float(svector[4])
                                topPadLocX = float(svector[5])
                                topPadLocY = float(svector[6])
                                topPadRadius = float(svector[7])
                                solderRadius = float(svector[8])
                                topMaskThickness = float(svector[9])
                                bottomMaskThickness = float(svector[10])
                                if len(svector) > 11:
                                    detailMode = svector[11]
                                else:
                                    detailMode = "None"                                                                
                                materialID = layerMatID
                                if len(svector) >12:
                                    materialID = int(svector[12])
                                
                                layer.CreateSMDVariables(bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name, topMaskThickness, bottomMaskThickness,detailMode, materialID)   
                            elif svector[0] == "NSMD":
                                modeType = "NSMD"
                                name = svector[1]
                                bottomPadLocX = float(svector[2])
                                bottomPadLocY = float(svector[3])
                                bottomPadRadius = float(svector[4])
                                topPadLocX = float(svector[5])
                                topPadLocY = float(svector[6])
                                topPadRadius = float(svector[7])
                                solderRadius = float(svector[8])
                                topMaskThickness = float(svector[9])
                                bottomPadThickness = float(svector[10])
                                if len(svector) > 11:
                                    detailMode = svector[11]
                                else:
                                    detailMode = "None"
                                materialID = layerMatID
                                if len(svector) >12:
                                    materialID = int(svector[12])
                                layer.CreateNSMDVariables(bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name, topMaskThickness, bottomPadThickness, detailMode, materialID)
                                 
                    elif layerGenMode == "Warped":
                        while True:
                            line = f.readline()
                            if not line:break
                            line = line.replace('\n','')
                            svector = line.split(',')
                            if svector[0][0] == "*":
                                print("Layer End")
                                break
                            elif svector[0][0] == "#":
                                continue
                            elif svector[0] == "WarpageVariables":
                               
                                warpageVariables = [] 
                                warpageVariables.append(svector[1])
                                warpageVariables.append(float(svector[2])) # xloc
                                warpageVariables.append(float(svector[3])) # yloc
                                warpageVariables.append(float(svector[4])) # zloc
                                warpageVariables.append(float(svector[5])) # xleft
                                warpageVariables.append(float(svector[6])) # xright
                                warpageVariables.append(float(svector[7])) # ybottom
                                warpageVariables.append(float(svector[8])) # ytop
                                warpageVariables.append(svector[9]) # xmode
                                warpageVariables.append(float(svector[10])) # ymode
                                layer.SetWarpageVariables(warpageVariables)
                                
                                
                            elif svector[0] == "Location":
                                x = float(svector[1])
                                y = float(svector[2])
                                if len(svector) >= 4:
                                    z = float(svector[3])                            
                                    curZLoc = z
                                    layer.SetPosition(x,y,z)
                                else:
                                    z = curZLoc
                                    layer.SetPosition(x,y,curZLoc)
                                print("Location:  ",x,y,z)
                            elif svector[0] == "Length":
                                xLength = float(svector[1])
                                yLength = float(svector[2])
                                materialID = -1
                                if len(svector) >= 4:
                                    materialID = int(svector[3])
                                else:
                                    materialID = layerMatID
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                layer.SetLength(curpsid,xLength,yLength,materialID)
                                print("Length: ",xLength,yLength)
                            elif svector[0] == "MeshGenerationType":
                                meshGenerationType = svector[1].replace('\n','')
                                if len(svector) >= 3:
                                    meshType = svector[2].replace('\n','')  
                                else:
                                    meshType = "Tetra"
                                layer.SetMeshGenerationType(meshGenerationType)
                                layer.SetMeshType(meshType)
                                print("MeshGenerationType: ",meshGenerationType)    
                            elif svector[0] == "MeshPath":
                                meshPath = svector[1].replace('\n','')
                                layer.SetMeshPath(meshPath)
                                print("MeshPath: ",meshPath)
                            elif svector[0] == "MeshSizeInPlane":
                                meshSizeInPlane = float(svector[1])
                                layer.SetMeshSizeInPlane(meshSizeInPlane)
                                print("MeshSizeInPlane: ",meshSizeInPlane)
                            elif svector[0] == "NumberofElementinXDirection":
                                layer.SetNumberofElementinXDirection(int(svector[1])) 
                            elif svector[0] == "NumberofElementinYDirection":
                                layer.SetNumberofElementinYDirection(int(svector[1]))
                            elif svector[0] == "NumberofElementinThickness":
                                numberofElementinThickness = int(svector[1])
                                layer.SetNumberofElementinThickness(numberofElementinThickness)
                                print("NumberofElementinThickness: ",numberofElementinThickness)
                            elif svector[0] == "ConformalBufferThickness":
                                conformalBufferThickness = float(svector[1])
                                layer.SetConformalBufferThickness(conformalBufferThickness)
                                print("ConformalBufferThickness: ", conformalBufferThickness)
                            elif svector[0] == "MaterialID":
                                layerMatID = int(svector[1])
                            elif svector[0] == "Thickness":
                                thickness = float(svector[1])
                                layer.SetThickness(thickness)
                                totalThickness += thickness
                                curZLoc += thickness
                                print("Thickness: ",thickness)

                            elif svector[0] == "BoxWarpage":
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])
                                if len(svector) > 5:
                                    materialID = int(svector[5])
                                else:
                                    materialID = layerMatID
                                variables = ["BOX",x,y,xLength,yLength,materialID]
                                layer.AddVariables(variables)
                                
                            elif svector[0] == "CylinderWarpage":
                                x = float(svector[1])
                                y = float(svector[2])
                                r = float(svector[3])
                                if len(svector) >= 5:
                                    materialID = int(svector[4])
                                variables = ["CYLINDER",x,y,r,materialID]
                                layer.AddVariables(variables)
                                pass
                                
                    elif layerGenMode == "Defined":
                        while True:
                            line = f.readline()
                            if not line:break
                            line = line.replace('\n','')
                            svector = line.split(',')
                            if svector[0][0] == "*":
                                print("Layer End")
                                break
                            elif svector[0][0] == "#":
                                continue
                            elif svector[0][0] == "$":
                                continue
                            elif svector[0] == "Location":
                                x = float(svector[1])
                                y = float(svector[2])
                                if len(svector) >= 4:
                                    z = float(svector[3])   
                                    curZLoc = z                         
                                    layer.SetPosition(x,y,z)
                                else:
                                    z = curZLoc
                                    layer.SetPosition(x,y,z)
                                print("Location:  ",x,y,z)
                            elif svector[0] == "Length":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                xLength = float(svector[1])
                                yLength = float(svector[2])
                                materialID = -1
                                if len(svector) >= 4:
                                    materialID = int(svector[3])
                                layer.SetLength(curpsid,xLength,yLength,materialID)
                                print("Length: ",xLength,yLength)
                            elif svector[0] == "MeshGenerationType":
                                meshGenerationType = svector[1].replace('\n','')
                                if len(svector) >= 3:
                                    meshType = svector[2].replace('\n','')  
                                else:
                                    meshType = "Hexa"
                                layer.SetMeshGenerationType(meshGenerationType)
                                layer.SetMeshType(meshType)
                                print("MeshGenerationType: ",meshGenerationType)
                            elif svector[0] == "MeshPath":
                                meshPath = svector[1].replace('\n','')
                                layer.SetMeshPath(meshPath)
                                print("MeshPath: ",meshPath)                            
                            elif svector[0] == "MeshSizeInPlane":
                                meshSizeInPlane = float(svector[1])
                                layer.SetMeshSizeInPlane(meshSizeInPlane)
                                print("MeshSizeInPlane: ",meshSizeInPlane)
                            elif svector[0] == "NumberofElementinXDirection":
                                layer.SetNumberofElementinXDirection(int(svector[1])) 
                            elif svector[0] == "NumberofElementinYDirection":
                                layer.SetNumberofElementinYDirection(int(svector[1]))
                            elif svector[0] == "NumberofElementinThickness":
                                numberofElementinThickness = int(svector[1])
                                layer.SetNumberofElementinThickness(numberofElementinThickness)
                                print("NumberofElementinThickness: ",numberofElementinThickness)
                            elif svector[0] == "ConformalBufferThickness":
                                conformalBufferThickness = float(svector[1])
                                layer.SetConformalBufferThickness(conformalBufferThickness)
                                print("ConformalBufferThickness: ", conformalBufferThickness)
                            elif svector[0] == "Thickness":
                                thickness = float(svector[1])
                                layer.SetThickness(thickness)
                                totalThickness += thickness
                                curZLoc += thickness
                                print("Thickness: ",thickness)
                            elif svector[0] == "MaterialID":
                                layerMatID = int(svector[1])
                            elif "segmentset" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    if len(svectorsub) > 1:
                                        curssKey = int(svectorsub[1])
                                        ssKey = max(ssKey,curssKey)
                                    else:
                                        ssKey = ssKey + 1
                                        curssKey = ssKey
                                else:
                                    ssKey = ssKey + 1
                                    curssKey = ssKey
                                OptionLocation = svector[1]
                                SegmentSetName = svector[2]
                                SSID = svector[3]
                                SSID = str(curssKey) + svector[3]
                                tol = float(svector[4])
                                if len(svector)>5:
                                    da1 = float(svector[5])
                                else:
                                    da1 = 0.0
                                if len(svector)>6:
                                    da2 = float(svector[6])
                                else:
                                    da2 = 0.0
                                if len(svector)>7:
                                    da3 = float(svector[7])
                                else:
                                    da3 = 0.0
                                if len(svector)>8:
                                    da4 = float(svector[8])
                                else:
                                    da4 = 0.0
                                if len(svector)>9:
                                    solver = svector[9]
                                else:
                                    solver = "MECH"
                                if len(svector)>10:
                                    its = int(svector[10])
                                else:
                                    its = 0                                                                 
                                layer.AddSegmentSetOption(OptionLocation,SegmentSetName,SSID,tol,da1,da2,da3,da4,solver,its)
                                self.sSetIDtoKey[SSID] = curssKey                                
                            elif "nodeset" in svector[0].lower():
                                if len(svector) < 5:
                                    print("NodeSet Error")                                
                                    exit(0) 
                                    
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    if len(svectorsub) > 1:
                                        curnsKey = int(svectorsub[1])
                                        nsKey = max(nsKey,curnsKey)
                                    else:
                                        nsKey = nsKey + 1                                        
                                        curnsKey = nsKey
                                else:                                                                                                                    
                                    nsKey = nsKey + 1
                                    curnsKey = nsKey
                                OptionLocation = svector[1]
                                NodeSetName = svector[2]
                                NSID = svector[3]
                                NSID = str(curnsKey) + svector[3]
                                tol = float(svector[4])                                
                                layer.AddNodeSetOption(OptionLocation,NodeSetName,NSID,tol)
                                self.nSetIDtoKey[NSID] = curnsKey
                            
                            elif "stlfile" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                x = float(svector[1])
                                y = float(svector[2])
                                stlFileName = svector[3].replace('\n','')
                                if len(svector) > 4:
                                    svector[4] = svector[4].replace('\n','')
                                    scaleX = float(svector[4])
                                else:
                                    scaleX = 1.0
                                if len(svector) > 5:
                                    svector[5] = svector[5].replace('\n','')
                                    scaleY = float(svector[5])
                                else:
                                    scaleY = 1.0
                                if len(svector) > 6:
                                    svector[6] = svector[6].replace('\n','')
                                    scaleZ = float(svector[6])
                                else:
                                    scaleZ = 1.0
                                if len(svector) > 7:
                                    matID = int(svector[7])
                                else:
                                    matID = layerMatID
                                layer.AddSTLFileName(curpsid,x,y,stlFileName,scaleX,scaleY,scaleZ,matID)
                                print("STLFile: ",stlFileName)
                                
                            elif "stepfile" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                    
                                x = float(svector[1])
                                y = float(svector[2]) 
                                stepFileName = svector[3].replace('\n','')
                                if len(svector) > 4:
                                    svector[4] = svector[4].replace('\n','')
                                    scaleX = float(svector[4])
                                else:
                                    scaleX = 1.0
                                if len(svector) > 5:
                                    svector[5] = svector[5].replace('\n','')
                                    scaleY = float(svector[5])
                                else:
                                    scaleY = 1.0
                                if len(svector) > 6:
                                    svector[6] = svector[6].replace('\n','')
                                    scaleZ = float(svector[6])
                                else:
                                    scaleZ = 1.0
                                if len(svector) > 7:
                                    matID = int(svector[7])
                                else:
                                    matID = layerMatID
                                layer.AddStepFileName(curpsid,x,y,stepFileName,scaleX,scaleY,scaleZ,matID)
                                print("StepFile: ",stepFileName)
                            #elif svector[0] == "MSHFile":
                            elif "mshfile" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                        
                                x = float(svector[1])
                                y = float(svector[2])
                                mshFileName = svector[3].replace('\n','')
                                if len(svector) > 4:
                                    matID = int(svector[4])
                                else:
                                    matID = layerMatID
                                if len(svector) > 5:
                                    scaleX = float(svector[5])
                                else:
                                    scaleX = 1.0
                                if len(svector) > 6:
                                    scaleY = float(svector[6])
                                else:
                                    scaleY = 1.0
                                if len(svector) > 7:
                                    scaleZ = float(svector[7])
                                else:
                                    scaleZ = 1.0
                                    
                                layer.AddMSHFileName(curpsid,x,y,mshFileName,matID,scaleX,scaleY,scaleZ)
                                print("MSHFile: ",mshFileName)
                            #elif svector[0] == "DetailSolder":
                            elif "detailsolder" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                points = []
                                for i in range(3,len(svector),2):
                                    radius = float(svector[i])
                                    height = float(svector[i+1])
                                    points.append([radius,height])
                                if len(svector)%2 == 0:                                
                                    layer.AddDetailSolderShape(curpsid,x,y,points,layerMatID)
                                else:
                                    matID = int(svector[len(svector)-1])
                                    layer.AddDetailSolderShape(curpsid,x,y,points,matID)
                                print("DetailSolder: ",x,y,points)
                            elif "cylinder" in svector[0].lower():
                            #elif svector[0] == "Cylinder":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                r = float(svector[3])
                                if len(svector) >= 5:
                                    if "Shell" in svector[4]:
                                        layer.SetGeomGenerationType("Shell")
                                    else:
                                        layer.SetGeomGenerationType("Solid")

                                    if "Composite" in svector[4]:
                                        layer.SetGeomGenerationType("CompositeShell")
                                        line = f.readline()
                                        svector2 = line.split(",")
                                        compositeMatList = [] 
                                        compositeThicknessList = []
                                        compositeBList = []
                                        for ithLayer in range(0,len(svector2),3):
                                            ithLayerMatID = int(svector2[ithLayer])
                                            ithLayerThickness = float(svector2[ithLayer+1])
                                            ithLayerB = float(svector2[ithLayer+2])
                                            compositeMatList.append(ithLayerMatID)
                                            compositeThicknessList.append(ithLayerThickness)
                                            compositeBList.append(ithLayerB)

                                        layer.AddCylinder(curpsid,x,y,r,-1,compositeMatList,compositeThicknessList,compositeBList)

                                    elif len(svector) >= 6:
                                        matID = int(svector[5])
                                        layer.AddCylinder(curpsid,x,y,r,matID)
                                else:
                                    layer.AddCylinder(curpsid,x,y,r,layerMatID)

                                print("Cylinder: ",x,y,r)
                            #elif svector[0] == "CrackBox":
                            elif "crackbox" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])
                                if len(svector) >= 6:
                                    materialID = int(svector[5])
                                else:
                                    materialID = layerMatID
                                crackList = [] 
                                while True:
                                    line = f.readline()
                                    svector = line.split(",")
                                    if "endcrackbox" in svector[0].lower():
                                        break
                                    elif "vcrack" in svector[0].lower():
                                        originX = float(svector[1])
                                        originY = float(svector[2])
                                        angle = float(svector[3])
                                        width = float(svector[4])
                                        height = float(svector[5])
                                        length = float(svector[6])
                                        curCrack = ["VCrack",originX,originY,angle,width,height,length]
                                        crackList.append(curCrack)                                    
                                layer.AddBoxCrack(curpsid,x,y,xLength,yLength,crackList,materialID)        
                            #elif svector[0] == "Box":
                            elif "box" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])
                                if len(svector) > 5:
                                    if "Shell" in svector[5]:
                                        layer.SetGeomGenerationType("Shell")
                                    else:
                                        layer.SetGeomGenerationType("Solid")
                                    
                                    if "Composite" in svector[5]:
                                        if "Shell" in svector[5]:
                                            layer.SetGeomGenerationType("CompositeShell")                                    
                                            if len(svector) > 6:
                                                numLayer = int(svector[6])
                                            else:
                                                numLayer = 0 
                                            compositeMatList = [] 
                                            compositeThicknessList = []
                                            compositeBList = []
                                            if numLayer == 0:                                               
                                                line = f.readline()
                                                svector2 = line.split(",")
                                                
                                                for ithLayer in range(0,len(svector2),3):
                                                    ithLayerMatID = int(svector2[ithLayer])
                                                    ithLayerThickness = float(svector2[ithLayer+1])
                                                    ithLayerB = float(svector2[ithLayer+2])
                                                    compositeMatList.append(ithLayerMatID)
                                                    compositeThicknessList.append(ithLayerThickness)
                                                    compositeBList.append(ithLayerB)
                                            else:
                                                for ithLayer in range(numLayer):
                                                    line = f.readline()
                                                    svector2 = line.split(",")
                                                    ithLayerMatID = int(svector2[0])
                                                    ithLayerThickness = float(svector2[1])
                                                    ithLayerB = float(svector2[2])
                                                    compositeMatList.append(ithLayerMatID)
                                                    compositeThicknessList.append(ithLayerThickness)
                                                    compositeBList.append(ithLayerB)
                                            
                                            layer.AddBox(curpsid,x,y,xLength,yLength,-1,compositeMatList,compositeThicknessList,compositeBList)
                                            
                                        elif "Solid" in svector[5]:
                                            layer.SetGeomGenerationType("CompositeSolid")
                                            if len(svector) >6:
                                                numElematEachLayer = int(svector[6])
                                            else:
                                                numElematEachLayer = 3
                                            if len(svector)>7:
                                                numLayer = int(svector[7])
                                            else:
                                                numLayer = 0
                                            
                                            if numLayer == 0:
                                                line = f.readline()
                                                svector2 = line.split(",")
                                                compositeMatList = [] 
                                                compositeThicknessList = []
                                                compositeBList = []
                                                for ithLayer in range(0,len(svector2),3):
                                                    ithLayerMatID = int(svector2[ithLayer])
                                                    ithLayerThickness = float(svector2[ithLayer+1])
                                                    ithLayerB = float(svector2[ithLayer+2])
                                                    compositeMatList.append(ithLayerMatID)
                                                    compositeThicknessList.append(ithLayerThickness)
                                                    compositeBList.append(ithLayerB)
                                                layer.AddBox(curpsid,x,y,xLength,yLength,-1,compositeMatList,compositeThicknessList,compositeBList,numElematEachLayer)
                                            else:                                   
                                                compositeMatList = []
                                                compositeThicknessList = []
                                                compositeBList = []
                                                compositeOptionList = []
                                                compositeELFORMList = []
                                                compositeMeshRefinementSizeList = [] 
                                                compositeMeshRefinementLocationXList = [] 
                                                compositeMeshRefinementLocationYList = []
                                                compositeModeList = [] 

                                                for ii in range(numLayer):
                                                    line = f.readline()
                                                    svector2 = line.split(",")
                                                    ithLayerMatID = int(svector2[0])
                                                    ithLayerThickness = float(svector2[1])
                                                    ithLayerB = float(svector2[2])
                                                    compositeMatList.append(ithLayerMatID)
                                                    compositeThicknessList.append(ithLayerThickness)
                                                    compositeBList.append(ithLayerB)
                                                    if len(svector2) > 3:
                                                        if "/" in svector2[3]:
                                                            svector3 = svector2[3].split("/")
                                                            ithLayerEOSID = int(svector3[0])
                                                            if len(svector3) > 1:
                                                                ithLayerELFORM = int(svector3[1])
                                                            else:
                                                                ithLayerELFORM = 1
                                                        else:
                                                            ithLayerEOSID = int(svector2[3])
                                                            ithLayerELFORM = -99
                                                    else:
                                                        ithLayerEOSID = 0
                                                        ithLayerELFORM = -99 
                                                    compositeOptionList.append([ithLayerEOSID,ithLayerELFORM])                                                
                                                    if len(svector2) > 6:
                                                        meshSizeInside = float(svector2[4])
                                                        refineLocationX = float(svector2[5])
                                                        refineLocationY = float(svector2[6])
                                                    else:
                                                        meshSizeInside = 0 
                                                        refineLocationX = 0
                                                        refineLocationY = 0
                                                    if len(svector2) > 7:
                                                        mode = svector2[7]
                                                    else:
                                                        mode = "FEM"
                                                        # or "PERI"
                                                    compositeMeshRefinementSizeList.append(meshSizeInside)
                                                    compositeMeshRefinementLocationXList.append(refineLocationX)
                                                    compositeMeshRefinementLocationYList.append(refineLocationY)                                               
                                                    compositeModeList.append(mode)
                                                    

                                                layer.AddBox(curpsid,x,y,xLength,yLength,-1,compositeMatList,compositeThicknessList,compositeBList,numElematEachLayer,compositeOptionList,compositeMeshRefinementSizeList,compositeMeshRefinementLocationXList,compositeMeshRefinementLocationYList,compositeModeList)
                                                    
                                    
                                    elif len(svector) > 6: 
                                        materialID = int(svector[6])
                                        layer.AddBox(curpsid,x,y,xLength,yLength,materialID)                            
                                else:
                                    materialID = layerMatID
                                    layer.AddBox(curpsid,x,y,xLength,yLength,materialID)                            
                                print("Box: ",x,y,xLength,yLength)
                            elif "rectangletube" in svector[0].lower():
                            #elif svector[0] == "RectangleTube":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])
                                thickness = float(svector[5])                                                        
                                if len(svector) >= 7:
                                    if "Shell" in svector[6]:
                                        layer.SetGeomGenerationType("Shell")
                                    else:
                                        layer.SetGeomGenerationType("Solid")
                                    
                                    if "Composite" in svector[6]:
                                        layer.SetGeomGenerationType("CompositeShell")
                                        line = f.readline()
                                        svector2 = line.split(",")
                                        compositeMatList = [] 
                                        compositeThicknessList = []
                                        compositeBList = []
                                        for ithLayer in range(0,len(svector2),3):
                                            ithLayerMatID = int(svector2[ithLayer])
                                            ithLayerThickness = float(svector2[ithLayer+1])
                                            ithLayerB = float(svector2[ithLayer+2])
                                            compositeMatList.append(ithLayerMatID)
                                            compositeThicknessList.append(ithLayerThickness)
                                            compositeBList.append(ithLayerB)
                                        layer.AddRectangleTube(curpsid,x,y,xLength,yLength,thickness,-1,compositeMatList,compositeThicknessList,compositeBList)
                                    elif len(svector) >= 8:
                                        materialID = int(svector[7])
                                        layer.AddRectangleTube(curpsid,x,y,xLength,yLength,thickness,materialID)
                                    else:
                                        materialID = layerMatID
                                        layer.AddRectangleTube(curpsid,x,y,xLength,yLength,thickness,materialID)
                                else:
                                    materialID = layerMatID
                                    layer.AddRectangleTube(curpsid,x,y,xLength,yLength,thickness,materialID)
                            
                                print("RectangleTube: ",x,y,xLength,yLength,thickness)
                            elif "rectanglecirclecut" in svector[0].lower():
                            #elif svector[0] == "RectangleCircleCut":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])
                                circleX = float(svector[5])
                                circleY = float(svector[6])
                                circleRadius = float(svector[7])                                                        
                                if len(svector) >= 9:
                                    if "Shell" in svector[8]:
                                        layer.SetGeomGenerationType("Shell")
                                    else:
                                        layer.SetGeomGenerationType("Solid")
                                    if "Composite" in svector[8]:
                                        layer.SetGeomGenerationType("CompositeShell")
                                        line = f.readline()
                                        svector2 = line.split(",")
                                        compositeMatList = [] 
                                        compositeThicknessList = []
                                        compositeBList = []
                                        for ithLayer in range(0,len(svector2),3):
                                            ithLayerMatID = int(svector2[ithLayer])
                                            ithLayerThickness = float(svector2[ithLayer+1])
                                            ithLayerB = float(svector2[ithLayer+2])
                                            compositeMatList.append(ithLayerMatID)
                                            compositeThicknessList.append(ithLayerThickness)
                                            compositeBList.append(ithLayerB)
                                        layer.AddRectangleCircleCut(curpsid,x,y,xLength,yLength,circleX,circleY,circleRadius,-1,compositeMatList,compositeThicknessList,compositeBList)
                                    elif len(svector) >= 10:
                                        materialID = int(svector[9])
                                        layer.AddRectangleCircleCut(curpsid,x,y,xLength,yLength,circleX,circleY,circleRadius,materialID)
                                    else:
                                        materialID = layerMatID
                                        layer.AddRectangleCircleCut(curpsid,x,y,xLength,yLength,circleX,circleY,circleRadius,materialID)                                        
                                else:
                                    materialID = layerMatID
                                    layer.AddRectangleCircleCut(curpsid,x,y,xLength,yLength,circleX,circleY,circleRadius,materialID)
                            elif "rectanglefilletcut" in svector[0].lower():
                            #elif svector[0] == "RectangleFilletCut":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                x = float(svector[1])
                                y = float(svector[2])
                                xLength = float(svector[3])
                                yLength = float(svector[4])                               
                                cutList = []
                                while True:
                                    line = f.readline()
                                    svector2 = line.split(",")
                                    if svector2[0] == "EndRectangleFilletCut":
                                        break
                                    elif svector2[0] == "RFCFillet":
                                        posX_RFC = float(svector2[1])
                                        posY_RFC = float(svector2[2])
                                        lengthX_RFC = float(svector2[3])
                                        lengthY_RFC = float(svector2[4])
                                        radius_RFC = float(svector2[5])
                                        cutList.append(["RFCFillet",posX_RFC,posY_RFC,lengthX_RFC,lengthY_RFC,radius_RFC])
                                    elif svector2[0] == "RFCChamfer":
                                        posX_RFC = float(svector2[1])
                                        posY_RFC = float(svector2[2])
                                        lengthX_RFC = float(svector2[3])
                                        lengthY_RFC = float(svector2[4])
                                        distance_RFC = float(svector2[5])
                                        cutList.append(["RFCChamfer",posX_RFC,posY_RFC,lengthX_RFC,lengthY_RFC,distance_RFC])
                                if len(svector) >= 6:
                                    if "Shell" in svector[5]:
                                        layer.SetGeomGenerationType("Shell")
                                    else:
                                        layer.SetGeomGenerationType("Solid")                             
                                    if "Composite" in svector[5]:
                                        layer.SetGeomGenerationType("CompositeShell")
                                        line = f.readline()
                                        svector2 = line.split(",")
                                        compositeMatList = [] 
                                        compositeThicknessList = []
                                        compositeBList = []
                                        for ithLayer in range(0,len(svector2),3):
                                            ithLayerMatID = int(svector2[ithLayer])
                                            ithLayerThickness = float(svector2[ithLayer+1])
                                            ithLayerB = float(svector2[ithLayer+2])
                                            compositeMatList.append(ithLayerMatID)
                                            compositeThicknessList.append(ithLayerThickness)
                                            compositeBList.append(ithLayerB)
                                        layer.AddRectangleFilletCut(curpsid,x,y,xLength,yLength,cutList,-1,compositeMatList,compositeThicknessList,compositeBList)
                                    elif len(svector) >= 7:
                                        materialID = int(svector[6])
                                        layer.AddRectangleFilletCut(curpsid,x,y,xLength,yLength,cutList,materialID)
                                    else:
                                        materialID = layerMatID
                                        layer.AddRectangleFilletCut(curpsid,x,y,xLength,yLength,cutList,materialID)
                                else:
                                    materialID = layerMatID
                                    layer.AddRectangleFilletCut(curpsid,x,y,xLength,yLength,cutList,materialID)
                            elif "image" in svector[0].lower():                                    
                            #elif svector[0] == "Image":
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                                xLength = float(svector[1])
                                yLength = float(svector[2])
                                imageFileName = svector[3]
                                imageFileName = imageFileName.replace('\n','')                              
                                cutShapeOption = False
                                if len(svector) >= 5:                                
                                    if "True" in svector[4]:
                                        cutShapeOption = True
                                if len(svector) >= 6:
                                    materialID = int(svector[5])
                                else:
                                    materialID = layerMatID
                                layer.AddImage(curpsid, xLength,yLength,imageFileName,cutShapeOption,materialID)
                                print("Image: ",xLength,yLength,imageFileName)
                            elif "part" in svector[0].lower():
                                if "#" in svector[0]:
                                    svectorsub = svector[0].split("#")
                                    curpsid = int(svectorsub[1])
                                    psid = max(psid,curpsid)
                                else:
                                    psid = psid + 1
                                    curpsid = psid
                                    
                            #elif svector[0] == "Part":
                                if len(svector) >= 2:
                                    partType = svector[1]
                                    print("Part: ",partType)
                                    if "shieldcan" in partType.lower():
                                        xList = []
                                        yList = []
                                        line = f.readline()
                                        while True:
                                            svector2 = line.split(' ')
                                            if "OE" in svector2[0]:
                                                break
                                            else:
                                                xList.append(float(svector2[1]))
                                                yList.append(float(svector2[2]))
                                            line = f.readline()
                                        if "detail" in partType.lower():
                                            xListCut = []
                                            yListCut = []
                                           
                                            if "cut" in partType.lower():
                                                line = f.readline()
                                                while True:
                                                    svector2 = line.split(' ')
                                                
                                                    if "OE" in svector2[0]:
                                                        break
                                                    else:
                                                        xListCut.append(float(svector2[1]))
                                                        yListCut.append(float(svector2[2]))
                                                    line = f.readline()
                                            if len(svector) >= 3:
                                                if "Shell" in svector[2]:
                                                    layer.SetGeomGenerationType("Shell")
                                                else:
                                                    layer.SetGeomGenerationType("Solid")
                                                
                                                radius = float(svector[3])
                                                solidThickness = float(svector[4])
                                                padWidth = float(svector[5])
                                                offset = float(svector[6])
                                                if len(svector) >= 8:
                                                    matID = int(svector[7])
                                                else:
                                                    matID = layerMatID
                                                layer.AddShieldCan(curpsid,xList,yList,radius,solidThickness,padWidth,offset,xListCut,yListCut,matID, True)
                                        else:
                                            
                                            if len(svector) >= 3:
                                                if "Shell" in svector[2]:
                                                    layer.SetGeomGenerationType("Shell")
                                                else:
                                                    layer.SetGeomGenerationType("Solid")
                                                
                                                radius = float(svector[3])
                                                if len(svector) >= 6:
                                                
                                                    matID = int(svector[5])
                                                else:
                                                    matID = layerMatID
                                                
                                                if "Solid" in svector[2]:
                                                    solidThickness = float(svector[4])
                                                    layer.AddShieldCan(curpsid,xList,yList,radius,solidThickness,0.0,0.0,[],[],matID)
                                                else:
                                                    layer.AddShieldCan(curpsid,xList,yList,radius,0.0,0.0,0.0,[],[],matID)    
                                            else:
                                                matID = layerMatID
                                                layer.AddShieldCan(curpsid,xList,yList,0.0,0.0,0.0,0.0,[],[],matID)                                        
                                                
                                            
                                    elif "polynomialcut" in partType.lower():
                                        if "Shell" in svector[2]:
                                            layer.SetGeomGenerationType("Shell")
                                        else:
                                            layer.SetGeomGenerationType("Solid")
                                        numberofCut = int(svector[3])
                                        generateInternalOption = False
                                        if len(svector) > 4:
                                            if "True" in svector[4]:
                                                generateInternalOption = True                                                                      

                                        xList = [] 
                                        yList = [] 
                                        xCutMatrix = [] 
                                        yCutMatrix = []
                                        line = f.readline()
                                        while True:
                                            svector2 = line.split(' ')
                                            if "OE" in svector2[0]:
                                                break
                                            else:
                                                xList.append(float(svector2[1]))
                                                yList.append(float(svector2[2]))
                                            line = f.readline()
                                        for i in range(numberofCut):
                                            line = f.readline()
                                            xCutList = [] 
                                            yCutList = []
                                            while True:
                                                svector2 = line.split(' ')
                                                if "OE" in svector2[0]:
                                                    break
                                                else:
                                                    xCutList.append(float(svector2[1]))
                                                    yCutList.append(float(svector2[2]))
                                                line = f.readline()
                                            xCutMatrix.append(xCutList)
                                            yCutMatrix.append(yCutList)
                                        
                                        if len(svector) > 5:
                                            matID = int(svector[5])
                                        else:
                                            matID = layerMatID
                                        if len(svector) > 6:
                                            matCutID = int(svector[6])
                                        else:
                                            matCutID = matID

                                        if "Composite" in svector[2]:
                                            layer.SetGeomGenerationType("CompositeShell")
                                            line = f.readline()
                                            svector2 = line.split(",")
                                            compositeMatList = [] 
                                            compositeThicknessList = []
                                            compositeBList = [] 
                                            for ithLayer in range(0,len(svector2),3):
                                                ithLayerMatID = int(svector2[ithLayer])
                                                ithLayerThickness = float(svector2[ithLayer+1])
                                                ithLayerB = float(svector2[ithLayer+2])
                                                compositeMatList.append(ithLayerMatID)
                                                compositeThicknessList.append(ithLayerThickness)
                                                compositeBList.append(ithLayerB)
                                            layer.AddPolynomialCutPart(curpsid,xList,yList,xCutMatrix,yCutMatrix,generateInternalOption,matID,matCutID,compositeMatList,compositeThicknessList,compositeBList)
                                        else:
                                            layer.AddPolynomialCutPart(curpsid,xList,yList,xCutMatrix,yCutMatrix,generateInternalOption,matID,matCutID)

                                    elif "polynomialsweep" in partType.lower():
                                        if len(svector) >= 3:
                                            materialID = int(svector[2])
                                        else:
                                            materialID = layerMatID
                                        xListBottom = [] 
                                        yListBottom = []
                                        xListTop = []
                                        yListTop = []
                                        line = f.readline()
                                        while True:
                                            svector = line.split(' ')
                                            if "OE" in svector[0]:
                                                break
                                            else:
                                                xListBottom.append(float(svector[1]))
                                                yListBottom.append(float(svector[2]))
                                            line = f.readline()
                                        line = f.readline()
                                        while True:
                                            svector = line.split(' ')
                                            if "OE" in svector[0]:
                                                break
                                            else:
                                                xListTop.append(float(svector[1]))
                                                yListTop.append(float(svector[2]))
                                            line = f.readline()
                                        layer.AddPolynomialSweep(curpsid,xListBottom,yListBottom,xListTop,yListTop,materialID)
                                        
                                    elif "polynomial" in partType.lower():                                    
                                        xList = [] 
                                        yList = []
                                        line = f.readline()
                                        while True:
                                            svector2 = line.split(' ')
                                            if "OE" in svector2[0]:
                                                break
                                            else:
                                                xList.append(float(svector2[1]))
                                                yList.append(float(svector2[2]))
                                            line = f.readline()
                                        if len(svector) >= 3:
                                            if "Shell" in svector[2]:
                                                layer.SetGeomGenerationType("Shell")
                                            else:
                                                layer.SetGeomGenerationType("Solid")
                                            
                                            if "Composite" in svector[2]:
                                                layer.SetGeomGenerationType("CompositeShell")
                                                line = f.readline()
                                                svector2 = line.split(",")
                                                compositeMatList = [] 
                                                compositeThicknessList = []
                                                compositeBList = []
                                                for ithLayer in range(0,len(svector2),3):
                                                    ithLayerMatID = int(svector2[ithLayer])
                                                    ithLayerThickness = float(svector2[ithLayer+1])
                                                    ithLayerB = float(svector2[ithLayer+2])
                                                    compositeMatList.append(ithLayerMatID)
                                                    compositeThicknessList.append(ithLayerThickness)
                                                    compositeBList.append(ithLayerB)
                                                layer.AddPolynomialPart(curpsid, xList,yList,-1,compositeMatList,compositeThicknessList,compositeBList)
                                            elif len(svector) >= 4:
                                                matID = int(svector[3])
                                                layer.AddPolynomialPart(curpsid, xList,yList,matID)
                                        else:
                                            matID = layerMatID
                                            layer.AddPolynomialPart(curpsid, xList,yList,matID)                
                    self.layerList.append(layer)
                elif "*contact" in svector[0].lower():
                    while True:
                        line = f.readline()
                        if not line:break
                        line = line.replace('\n','')
                        svector = line.split(',')
                        if svector[0][0] == "*":                            
                            break          
                        elif svector[0][0] == "$":
                            continue
                        elif "tied" in svector[0].lower():
                            if len(svector) < 4: 
                                print("Error : TIED option is not enough")
                            contactType = svector[1]
                            tiedContact = {} 
                            if contactType.lower() == "part":
                                tiedContact["ContactType"] = "TIED_PART"
                                tiedContact["PartIDA"] = KooDynaInt(svector[2])
                                tiedContact["PartIDB"] = KooDynaInt(svector[3])
                                
                                self.contactOptions.append(tiedContact)
                                
                        elif "rbe2" in svector[0].lower():
                            if len(svector) < 4:
                                print("Error : RBE2 option is not enough")
                            AsideNodes = svector[1]
                            BsideNodes = svector[2]
                            nMinCon = int(svector[3])
                            tolerance = float(svector[4])
                            if len(svector) == 10:
                                cid = int(svector[5])
                                pnode = int(svector[6])
                                irpt = int(svector[7])
                                drflag = int(svector[8])
                                rrflag = int(svector[9])
                            else:
                                cid = 0     
                                pnode = 0
                                irpt = 2
                                drflag = 0  
                                rrflag = 0
                            rbe2OptionList = {}
                            rbe2OptionList["ContactType"] = "RBE2"
                            rbe2OptionList["AsideNodes"] = AsideNodes
                            rbe2OptionList["BsideNodes"] = BsideNodes
                            rbe2OptionList["nMinCon"] = nMinCon
                            rbe2OptionList["tolerance"] = tolerance
                            rbe2OptionList["cid"] = cid
                            rbe2OptionList["pnode"] = pnode
                            rbe2OptionList["irpt"] = irpt
                            rbe2OptionList["drflag"] = drflag
                            rbe2OptionList["rrflag"] = rrflag
                            
                            self.contactOptions.append(rbe2OptionList)
                            
                            
                        
                        
                    print("Contact End")
                elif "*boundary" in svector[0].lower(): 
                    while True:
                        line = f.readline()
                        if not line:break
                        line = line.replace('\n','')
                        svector = line.split(',')
                        if svector[0][0] == "*":
                            break
                        elif svector[0][0] == "$":
                            continue
                        elif "spcset" in svector[0].lower():
                            if len(svector) < 9:
                                print("Error : SPCSET option is not enough")
                            nsidList = svector[1].split('#')
                            cid = int(svector[2])
                            dofx = int(svector[3])
                            dofy = int(svector[4])
                            dofz = int(svector[5])
                            dofrx = int(svector[6])
                            dofry = int(svector[7])
                            dofrz = int(svector[8])
                            spcsetOptionList = {}
                            spcsetOptionList["BoundaryType"] = "BOUNDARY_SPC_SET"
                            spcsetOptionList["NSIDS"] = nsidList
                            spcsetOptionList["CID"] = cid
                            spcsetOptionList["DOFX"] = dofx
                            spcsetOptionList["DOFY"] = dofy
                            spcsetOptionList["DOFZ"] = dofz
                            spcsetOptionList["DOFRX"] = dofrx
                            spcsetOptionList["DOFRY"] = dofry
                            spcsetOptionList["DOFRZ"] = dofrz
                            self.boundaryOptions.append(spcsetOptionList)
                elif "*define" in svector[0].lower():
                    while True:
                        line = f.readline()
                        if not line:break
                        line = line.replace('\n','')
                        svector = line.split(',')
                        if svector[0][0] == "*":
                            break
                        elif svector[0][0] == "$":
                            continue                        
                        if len(svector) < 3:
                            print("Error : DEFINE option is not enough")
                        breakMode = False
                        if "curvefunction" in svector[0].lower():
                            LCID = int(svector[1])
                            SIDR = int(svector[2])
                            SFA = float(svector[3])
                            SFO = float(svector[4])
                            OFFA = float(svector[5])
                            OFFO = float(svector[6])
                            DATTYP = int(svector[7])
                            LCINT = int(svector[8])
                            variableMap = {}
                            baseVarName = ""
                            baseVarStart = 0.0
                            baseVarEnd = 0.0
                            baseVarStep = 0.0
                            OutputFunction = ""
                            while True:
                                line = f.readline()
                                if not line:break
                                line = line.replace('\n','')
                                svector = line.split(',')
                                if svector[0][0] == "*":
                                    breakMode = True        
                                    break
                                elif svector[0][0] == "$":
                                    continue
                                if len(svector) == 1:
                                    OutputFunction = svector[0]
                                    break
                                if len(svector) == 2:
                                    variableMap[svector[0]] = svector[1]
                                elif len(svector) == 4:
                                    baseVarName = svector[0]
                                    baseVarStart = float(svector[1])
                                    baseVarStep = float(svector[2])
                                    baseVarEnd = float(svector[3])
                                    
                            if baseVarEnd == 0.0 or len(OutputFunction) == 0:
                                 continue
                            curveOptionList = {}
                            curveOptionList["DefineType"] = "DEFINE_CURVE_FUNCTION"
                            curveOptionList["LCID"] = LCID
                            curveOptionList["SIDR"] = SIDR
                            curveOptionList["SFA"] = SFA
                            curveOptionList["SFO"] = SFO
                            curveOptionList["OFFA"] = OFFA
                            curveOptionList["OFFO"] = OFFO
                            curveOptionList["DATTYP"] = DATTYP
                            curveOptionList["LCINT"] = LCINT
                            curveOptionList["VariableMap"] = variableMap    
                            baseVars = [baseVarName,baseVarStart,baseVarStep,baseVarEnd]
                            curveOptionList["BaseVars"] = baseVars
                            curveOptionList["OutputFunction"] = OutputFunction
                            self.defineOptions.append(curveOptionList)  
                                  
                                
                            
                        elif "curve" in svector[0].lower():
                            if len(svector) < 9:
                                print("Error : Curve option is not enough")
                            LCID = int(svector[1])
                            SIDR = int(svector[2])
                            SFA = float(svector[3])
                            SFO = float(svector[4])
                            OFFA = float(svector[5])
                            OFFO = float(svector[6])
                            DATTYP = int(svector[7])
                            LCINT = int(svector[8])
                            A1List = []
                            O1List = []
                            while True:
                                line = f.readline()
                                if not line:break
                                line = line.replace('\n','')
                                svector = line.split(',')
                                if svector[0][0] == "*":
                                    breakMode = True        
                                    break  
                                if len(svector) != 2:
                                    break
                                elif svector[0][0] == "$":
                                    continue
                                                          
                                else:
                                    A1List.append(float(svector[0]))
                                    O1List.append(float(svector[1]))
                            curveOptionList = {}
                            curveOptionList["DefineType"] = "DEFINE_CURVE"
                            curveOptionList["LCID"] = LCID
                            curveOptionList["SIDR"] = SIDR
                            curveOptionList["SFA"] = SFA
                            curveOptionList["SFO"] = SFO
                            curveOptionList["OFFA"] = OFFA
                            curveOptionList["OFFO"] = OFFO
                            curveOptionList["DATTYP"] = DATTYP
                            curveOptionList["LCINT"] = LCINT
                            curveOptionList["A1List"] = A1List
                            curveOptionList["O1List"] = O1List
                            self.defineOptions.append(curveOptionList)
                        if breakMode:
                            break
                   
                elif "*load" in svector[0].lower():
                    while True:
                        line = f.readline()
                        if not line:break
                        line = line.replace('\n','')
                        svector = line.split(',')
                        if svector[0][0] == "*":
                            break
                        elif svector[0][0] == "$":
                            continue
                        if "segmentsnodedistributed" in svector[0].lower():
                            lid = int(svector[1])
                            ssid = svector[2].split('#')
                            fx = float(svector[3])
                            fy = float(svector[4])
                            fz = float(svector[5])
                            lcid = int(svector[6])
                            sf = float(svector[7])
                            cid = int(svector[8])
                            
                            loadOptionList = {}
                            loadOptionList["LoadType"] = "LOAD_SEGMENT_NODE_DISTRIBUTED"
                            loadOptionList["LID"] = lid
                            loadOptionList["SSID"] = ssid
                            loadOptionList["Fx"] = fx
                            loadOptionList["Fy"] = fy
                            loadOptionList["Fz"] = fz
                            loadOptionList["LCID"] = lcid
                            loadOptionList["SF"] = sf
                            loadOptionList["CID"] = cid     
                            self.loadOptions.append(loadOptionList)                                                                                     

                        elif "nodesetcenter" in svector[0].lower():
                            lid = int(svector[1])
                            nsid = int(svector[2])
                            fx = float(svector[3])
                            fy = float(svector[4])
                            fz = float(svector[5])
                            lcid = int(svector[6])
                            sf = float(svector[7])  
                            cid = int(svector[8])
                            
                            loadOptionList = {}
                            loadOptionList["LoadType"] = "LOAD_RBE_CENTER"
                            loadOptionList["NSID"] = nsid
                            loadOptionList["LID"] = lid
                            loadOptionList["Fx"] = fx
                            loadOptionList["Fy"] = fy
                            loadOptionList["Fz"] = fz
                            loadOptionList["LCID"] = lcid
                            loadOptionList["SF"] = sf
                            loadOptionList["CID"] = cid
                            self.loadOptions.append(loadOptionList)
                            
                        elif "forcesegmentset" in svector[0].lower():
                            lid = int(svector[1])
                            ssid = svector[2].split('#')
                            lcid = int(svector[3])
                            cid = int(svector[4])
                            Fx = float(svector[5])
                            Fy = float(svector[6])
                            Fz = float(svector[7])
                            loadOptionList = {}
                            loadOptionList["LoadType"] = "LOAD_FORCE_SEGMENT_SET"
                            loadOptionList["LID"] = lid
                            loadOptionList["SSID"] = ssid
                            loadOptionList["LCID"] = lcid
                            loadOptionList["CID"] = cid
                            loadOptionList["Fx"] = Fx
                            loadOptionList["Fy"] = Fy
                            loadOptionList["Fz"] = Fz
                            self.loadOptions.append(loadOptionList)
                        elif "segmentset" in svector[0].lower():
                            lid = int(svector[1])
                            ssid = svector[2].split('#')
                            lcid = int(svector[3])
                            sf = float(svector[4])
                            at = float(svector[5])
                            loadOptionList = {} 
                            loadOptionList["LoadType"] = "LOAD_SEGMENT_SET"
                            loadOptionList["LID"] = lid
                            loadOptionList["SSID"] = ssid
                            loadOptionList["LCID"] = lcid
                            loadOptionList["SF"] = sf
                            loadOptionList["AT"] = at
                            self.loadOptions.append(loadOptionList)                            
                elif "**addscript" in svector[0].lower():
                    addOpt = "LSDyna"                    
                    if len(svector) > 1:
                        addOpt = svector[1]
                    addScript = ""
                    while True:
                        line = f.readline()
                        if not line:break
                        line = line.replace('\n','')
                        if "**endscript" in line.lower():
                            break
                        elif line[0] == "$":
                            continue
                        addScript = addScript + line + "\n"
                    
                    if addOpt.lower() == "lsdyna":
                        self.dynaAddScript = addScript
                    elif addOpt.lower() == "abaqus":
                        self.abaqusAddScript = addScript
                    elif addOpt.lower() == "ansys":
                        self.ansysAddScript = addScript
                    elif addOpt.lower() == "nastran":
                        self.nastranAddScript = addScript
                    line = f.readline()
                    line = line.replace('\n','')
                        
                else:
                    print("Keyword Error : {0} is not supported".format(svector[0]))
                    exit(0)
                
            else:
                line = f.readline()



        f.close()
        pass


    def CreatePartsforPackage(self,partMan : KooPartManager = None):    
        if partMan == None:
            partMan : KooPartManager = KooPartManager()
        maxPartID = partMan.maxID
        partpsidtopidMap = {}
        partpidtolayernumMap = {}
        ith = 0 
        for layer in self.layerList:
            if type(layer) == SolderJointsLayer:
                layer : SolderJointsLayer = layer
                if layer.meshGenerationMode:
                    for warpedShape in layer.warpedShapeList:
                        curpid = maxPartID + warpedShape.meshManager.part.id 
                        partMan.AddPartfromKooPart(curpid,warpedShape.meshManager.part)
            elif type(layer) == PackageWarpedLayer:
                layer : PackageWarpedLayer = layer
                if layer.meshGenerationMode:
                    for warpedShape in layer.warpedShapeList:
                        curpid = maxPartID + warpedShape.meshManager.part.id 
                        partMan.AddPartfromKooPart(curpid,warpedShape.meshManager.part)
            elif type(layer) == PackageLayerDefined:
                layer : PackageLayerDefined = layer
                if layer.meshGenerationMode:
                    if layer.packageMesh != None:
                        curpid = maxPartID + layer.packageMesh.part.id
                        curpsid = layer.packageMeshpsid
                        partMan.AddPartfromKooPart(curpid,layer.packageMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                            
                    for i in range(len(layer.mshMeshList)):
                    #for mshMesh in layer.mshMeshList:
                        mshMesh : KooMeshManagerGMSH = layer.mshMeshList[i]
                        curpid = maxPartID + mshMesh.part.id
                        curpsid = layer.mshMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,mshMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.boxCrackMeshList)):
                    #for boxCrack in layer.boxCrackMeshList:
                        boxCrack : KooMeshManagerGMSH = layer.boxCrackMeshList[i]
                        curpid = maxPartID + boxCrack.part.id
                        curpsid = layer.boxCrackMeshpsidList[i]                        
                        partMan.AddPartfromKooPart(curpid,boxCrack.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.cylinderMeshList)):
                    # for cylinderMesh in layer.cylinderMeshList:
                        cylinderMesh : KooMeshManagerGMSH = layer.cylinderMeshList[i]
                        curpid = maxPartID + cylinderMesh.part.id
                        curpsid = layer.cylinderMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,cylinderMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.boxMeshList)):
                    #for boxMesh in layer.boxMeshList:
                        boxMesh : KooMeshManagerGMSH = layer.boxMeshList[i]
                        curpid = maxPartID + boxMesh.part.id
                        curpsid = layer.boxMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,boxMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.rectangleTubeMeshList)):
                    #for rectangleTubeMesh in layer.rectangleTubeMeshList:
                        rectangleTubeMesh : KooMeshManagerGMSH = layer.rectangleTubeMeshList[i]
                        curpid = maxPartID + rectangleTubeMesh.part.id
                        curpsid = layer.rectangleTubeMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,rectangleTubeMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.rectangleCircleCutMeshList)):
                    #for rectangleCircleCutMesh in layer.rectangleCircleCutMeshList:
                        rectangleCircleCutMesh : KooMeshManagerGMSH = layer.rectangleCircleCutMeshList[i]
                        curpid = maxPartID + rectangleCircleCutMesh.part.id
                        curpsid = layer.rectangleCircleCutMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,rectangleCircleCutMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.rectangleFilletCutMeshList)):
                    #for rectangleFilletCutMesh in layer.rectangleFilletCutMeshList:
                        rectangleFilletCutMesh : KooMeshManagerGMSH = layer.rectangleFilletCutMeshList[i]
                        curpid = maxPartID + rectangleFilletCutMesh.part.id
                        curpsid = layer.rectangleFilletCutMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,rectangleFilletCutMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.polynomialPartMeshList)):
                    #for detailShapes in layer.polynomialPartMeshList:
                        detailShapes : KooMeshManagerGMSH = layer.polynomialPartMeshList[i]
                        curpid = maxPartID + detailShapes.part.id
                        curpsid = layer.polynomialPartMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,detailShapes.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.polynomialCutPartMeshList)):
                    #for detailShapes in layer.polynomialCutPartMeshList:
                        detailShapes : KooMeshManagerGMSH = layer.polynomialCutPartMeshList[i]
                        curpid = maxPartID + detailShapes.part.id
                        curpsid = layer.polynomialCutPartMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,detailShapes.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.polynomialSweepMeshList)):
                    # for polynomialSweepShapes in layer.polynomialSweepMeshList:
                        polynomialSweepShapes : KooMeshManagerGMSH = layer.polynomialSweepMeshList[i]
                        curpid = maxPartID + polynomialSweepShapes.part.id  
                        curpsid = layer.polynomialSweepMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,polynomialSweepShapes.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.imageMeshList)):   
                    #for imageShapes in layer.imageMeshList:
                        imageShapes : KooMeshManagerGMSH = layer.imageMeshList[i]
                        curpid = maxPartID + imageShapes.part.id
                        curpsid = layer.imageMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,imageShapes.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.stlMeshList)):
                        stlMesh : KooMeshManagerGMSH = layer.stlMeshList[i]
                        curpid = maxPartID + stlMesh.part.id
                        curpsid = layer.stlFileMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid, stlMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith                        
                    for i in range(len(layer.stepMeshList)):
                    #for stepMesh in layer.stepMeshList:
                        stepMesh : KooMeshManagerGMSH = layer.stepMeshList[i]
                        curpid = maxPartID + stepMesh.part.id
                        curpsid = layer.stepFileMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,stepMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.shieldCanMeshList)):
                    #for shieldCanMesh in layer.shieldCanMeshList:
                        shieldCanMesh : KooMeshManagerGMSH = layer.shieldCanMeshList[i]
                        curpid = maxPartID + shieldCanMesh.part.id
                        curpsid = layer.shieldCanMeshpsidList[i]
                        partMan.AddPartfromKooPart(curpid,shieldCanMesh.part)
                        if curpsid not in partpsidtopidMap.keys():
                            partpsidtopidMap[curpsid] = [curpid]
                        else:
                            partpsidtopidMap[curpsid].append(curpid)
                        partpidtolayernumMap[curpid] = ith
                    for i in range(len(layer.conformalMeshList)):
                        conformalMesh : KooMeshManagerGMSH = layer.conformalMeshList[i]
                        curpid = maxPartID + conformalMesh.part.id
                        partMan.AddPartfromKooPart(curpid, conformalMesh.part)
                        partpidtolayernumMap[curpid] = ith
            maxPartID = partMan.maxID
            ith = ith + 1

        # Buffer mesh parts 등록
        for bufferMesh in self.bufferMeshList:
            curpid = maxPartID + bufferMesh.part.id
            partMan.AddPartfromKooPart(curpid, bufferMesh.part)
            maxPartID = partMan.maxID

        self.partMan = partMan
        self.partPSIDtoPartID = partpsidtopidMap
        
                    
        self.partPIDtoLayerNum = partpidtolayernumMap
        return partMan
    
    def CreateNodeSetsforPackage(self, partMan : KooPartManager = None):
        if partMan == None:
            partMan : KooPartManager = KooPartManager()
            self.CreatePartsforPackage(partMan)
        ith = 0 
        for layer in self.layerList:
            if type(layer) == SolderJointsLayer:
                pass
            elif type(layer) == PackageWarpedLayer:
                pass
            elif type(layer) == PackageLayerDefined:
                layer : PackageLayerDefined = layer 
                if layer.meshGenerationMode != None:
                    for nodeSetOption in layer.nodeSetOption:
                        curNodeSetOption = nodeSetOption
                        OptionLocation = curNodeSetOption[0]
                        NodeSetName = curNodeSetOption[1]
                        NSID = curNodeSetOption[2]
                        curKey = self.nSetIDtoKey[NSID]
                        tol = curNodeSetOption[3]
                        # count number of X in NSID
                        strNSID : str = NSID
                        numX = strNSID.count('X')
                        # make a list of X index
                        listX = ['X' for i in range(len(strNSID)) if strNSID[i] == 'X']
                        # make a string of X index
                        strX = ""
                        for i in listX:
                            strX += str(i)
                        
                        for partID in partMan.parts:
                            part : KooPart = partMan.parts[partID]
                            partID = part.id
                            if partID in self.partPIDtoLayerNum.keys():
                                if self.partPIDtoLayerNum[partID] != ith:
                                    continue
                            else:
                                continue
                            #part ID as numX digit
                            strPartID = str(partID)
                            while len(strPartID) < numX:
                                strPartID = "0"+strPartID
                                
                            #replace X with partID
                            newNSID = strNSID.replace(strX,strPartID)                                                                                          
                            newNSIDint = int(newNSID)
                            if curKey not in self.nSetKeytoID:
                                self.nSetKeytoID[curKey] = [newNSIDint]
                            else:
                                self.nSetKeytoID[curKey].append(newNSIDint)
                            name = NodeSetName
                                                                                    
                            if OptionLocation.lower() == "external":
                                nodes = part.elementManager.GetExternalNodes()
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
                            elif OptionLocation.lower() == "top":
                                nodes = part.elementManager.GetNodesOnLocation("top",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
                            elif OptionLocation.lower() == "bottom":
                                nodes = part.elementManager.GetNodesOnLocation("bottom",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
                            elif OptionLocation.lower() == "left":
                                nodes = part.elementManager.GetNodesOnLocation("left",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
                            elif OptionLocation.lower() == "right":
                                nodes = part.elementManager.GetNodesOnLocation("right",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
                            elif OptionLocation.lower() == "front":
                                nodes = part.elementManager.GetNodesOnLocation("front",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)                                
                            elif OptionLocation.lower() == "back":
                                nodes = part.elementManager.GetNodesOnLocation("back",tol)
                                part.nodeSetManager.CreateNodeSetwithNodesNodeSetID(newNSIDint, name, 0.0,0.0,0.0,0.0,"MECH",0,nodes)
            ith = ith + 1                            
            
    def CreateSegmentSetsforPackage(self, partMan : KooPartManager = None):
        if partMan == None:
            partMan : KooPartManager = KooPartManager()
            self.CreatePartsforPackage(partMan)
            
        ith = 0
        for layer in self.layerList:
            if type(layer) == SolderJointsLayer:
                pass
            elif type(layer) == PackageWarpedLayer:
                pass
            elif type(layer) == PackageLayerDefined:
                layer : PackageLayerDefined = layer
                if layer.meshGenerationMode != None:
                    for segmentSetOption in layer.segmentSetOption:
                        
                        curSegmentSetOption = segmentSetOption
                        OptionLocation = curSegmentSetOption[0]
                        SegmentSetName = curSegmentSetOption[1]
                        SSID = curSegmentSetOption[2]
                        curKey = self.sSetIDtoKey[SSID]
                        tol = curSegmentSetOption[3]
                        da1 = curSegmentSetOption[4]
                        da2 = curSegmentSetOption[5]
                        da3 = curSegmentSetOption[6]
                        da4 = curSegmentSetOption[7]
                        solvers = curSegmentSetOption[8]
                        its = curSegmentSetOption[9]

                            
                        # count number of X in SSID
                        strSSID : str = SSID
                        numX = strSSID.count('X')
                        # make a list of X index
                        listX = ['X' for i in range(len(strSSID)) if strSSID[i] == 'X']
                        # make a string of X index
                        strX = ""
                        for i in listX:
                            strX += str(i)
                            
                            
                        for partID in partMan.parts:
                            part : KooPart = partMan.parts[partID]
                            partID = part.id
                            if partID in self.partPIDtoLayerNum.keys():
                                if self.partPIDtoLayerNum[partID] != ith:
                                    continue
                            else:
                                continue
                            #part ID as numX digit
                            strPartID = str(partID)
                            while len(strPartID) < numX:
                                strPartID = "0"+strPartID
                            
                            #replace X with partID
                            newSSID = strSSID.replace(strX,strPartID)
                            newSSIDint = int(newSSID)
                            if curKey not in self.sSetKeytoID:
                                self.sSetKeytoID[curKey] = [newSSIDint]
                            else:
                                self.sSetKeytoID[curKey].append(newSSIDint)
                           
                            
                            boundaries = part.elementManager.GetBoundariesOnLocation(OptionLocation.lower(),tol)
                            if len(boundaries) > 0:
                                segmentSet = self.segmentManager.CreateSegmentSetwithID(newSSIDint,da1,da2,da3,da4,solvers,its)
                                for boundary in boundaries:
                                    if len(boundary) == 2:
                                        segmentSet.AddLineSegment(boundary[0],boundary[1])
                                    elif len(boundary) == 3:
                                        segmentSet.AddTrianagleSegment(boundary[0],boundary[1],boundary[2])
                                    elif len(boundary) == 4:
                                        segmentSet.AddQuadrangleSegment(boundary[0],boundary[1],boundary[2],boundary[3])
                                    
                            
                        
                        pass
                            
                           
            ith = ith + 1 
                
                
            
    def CreateLoad(self):
        for loadOption in self.loadOptions:
            if loadOption['LoadType'] == 'LOAD_SEGMENT_NODE_DISTRIBUTED':
                self.CreateLoadSegmentNodeDistributedforPackage(loadOption)
            elif loadOption["LoadType"] == "LOAD_RBE_CENTER":
                self.CreateLoadRBECenterforPackage(loadOption)
            elif loadOption["LoadType"] == "LOAD_FORCE_SEGMENT_SET":
                self.CreateLoadForceSegmentSetforPackage(loadOption)
            elif loadOption["LoadType"] == "LOAD_SEGMENT_SET":
                self.CreateLoadSegmentSetforPackage(loadOption)
            else:
                print("Error : Load Type is not supported")
                exit(0)
    
    def CreateLoadSegmentNodeDistributedforPackage(self, loadOption):   
        lid = loadOption["LID"]
        ssKeys = loadOption["SSID"]
        fx = loadOption["Fx"]
        fy = loadOption["Fy"]
        fz = loadOption["Fz"]
        lcid = loadOption["LCID"]
        sf = loadOption["SF"]
        cid = loadOption["CID"]
        
        totSegments = [] 
        for i in range(len(ssKeys)):
            ssKey = int(ssKeys[i])
            ssids = self.sSetKeytoID[ssKey]
            for ssid in ssids:
                segmentSet = self.segmentManager.segmentSetList[ssid]
                totSegments.extend(segmentSet.segments)
        
        nodeids = []
        for segment in totSegments:
            # remove duplicate segments
            segmentNodes = list(set(segment))
            nodeids.extend(segmentNodes)
        counts = Counter(b for b in nodeids)
        # counts to list 
        boundary_counts = counts.items()
        total_counts = 0
        for nodeid, count in boundary_counts:
            total_counts += count
            
                                                       
        name = "Load" + str(lid)
        if lcid == 0:
            defineCurve = self.defineManager.CreateDefineCurve("DefineCurveforLoad{0}".format(lid),SFA=1.0,SFO=1.0,OFFA=0.0,OFFO=0.0,DATTYP=0,LCINT=0,A1=[0.0,1.0], O1=[0.0,1.0])
            lcid = defineCurve.lcid
            
        for nodeid, count in boundary_counts:
            nid = nodeid
            Fx = fx * float(count) / float(total_counts)*sf
            Fy = fy * float(count) / float(total_counts)*sf
            Fz = fz * float(count) / float(total_counts)*sf
            name = "node{0}_Load"
            self.loadManager.CreateLoadNodalPoint(name,lcid,cid,Fx,Fy,Fz,nid)
            
            
        
    def CreateLoadRBECenterforPackage(self, loadOption):
        lid = loadOption["LID"]
        nskey = loadOption["NSID"]
        cid = loadOption["CID"]
        Fx = loadOption["Fx"]
        Fy = loadOption["Fy"]
        Fz = loadOption["Fz"]
        lcid = loadOption["LCID"]
        sf = loadOption["SF"]
        name = "nodeSetCenter{0}".format(lid)
        
        nsids = self.nSetKeytoID[nskey]
        nodes = [] 
        da1 = 0.0
        da2 = 0.0
        da3 = 0.0
        da4 = 0.0
        solver = "MECH"
        its = 0
        
        
        for nsid in nsids:
            nodeSet : NodeSet = self.nodeSetManager.nodeSets[nsid]
            da1 = nodeSet.da1
            da2 = nodeSet.da2
            da3 = nodeSet.da3
            da4 = nodeSet.da4
            solver = nodeSet.solver
            its = nodeSet.its
            
            nodes.extend(nodeSet.nodes.values())
            
        #node = self.nodeManager.CenterNode(nodeSet)
        node = self.nodeManager.CreateCenterNodefromNodeSet(nodeSet)
        nodes.append(node)
        newNodeSet = self.nodeSetManager.CreateNodeSetwithNodes(name,da1,da2,da3,da4,solver,its,nodes)
        
        constrained = self.partMan.CreateConstrainedNodalRigidBody(name,cid,node.id,1,0,0,newNodeSet)
        self.loadManager.CreateLoadNodalPoint(name,lcid,cid,Fx,Fy,Fz,node.id)
        self.partMan.CreatePointElement(node,100.0)
    
    def CreateLoadForceSegmentSetforPackage(self, loadOption):
        lid = loadOption["LID"]
        cid = loadOption["CID"]
        ssKeys = loadOption["SSID"]
        lcid = loadOption["LCID"]
        Fx = loadOption["Fx"]
        Fy = loadOption["Fy"]
        Fz = loadOption["Fz"]
        
        totSegments = [] 
        nodes = {}
        nodesArea = {}
        for i in range(len(ssKeys)):
            ssKey = int(ssKeys[i])
            ssids = self.sSetKeytoID[ssKey]
            for ssid in ssids:
                segmentSet = self.segmentManager.segmentSetList[ssid]
                totSegments.extend(segmentSet.segments)
    
        
        
        ''' for segment in totSegments:
            for id in segment:
                if id not in nodes.keys():
                    nodes[id] = self.nodeManager.nodes[id]
                    nodesArea[id] = 0.0
            area = self.nodeManager.GetQuadrangleArea(segment[0],segment[1],segment[2],segment[3])
            for id in segment:
                nodesArea[id] += area/4.0
        '''    
        name = "Load" + str(lid)
        if lcid == 0:
            defineCurve = self.defineManager.CreateDefineCurve("DefineCurveforLoad{0}".format(lid),SFA=1.0,SFO=1.0,OFFA=0.0,OFFO=0.0,DATTYP=0,LCINT=0,A1=[0.0,1.0], O1=[0.0,1.0])
            lcid = defineCurve.lcid
        
               
        self.loadManager.CreateLoadNodes(name, lcid, cid, Fx, Fy, Fz, totSegments, self.nodeManager)
        
            
        
    def CreateLoadSegmentSetforPackage(self, loadOption):
        lid = loadOption["LID"]
        name = "Load" + str(lid)
        ssKeys = loadOption["SSID"]
        lcid = loadOption["LCID"]
        sf = loadOption["SF"]
        at = loadOption["AT"]
        
        for i in range(len(ssKeys)):
            ssKey = int(ssKeys[i])
            ssids = self.sSetKeytoID[ssKey]            
            for ssid in ssids:
                curlid = str(lid) + str(ssid)
                curlid = int(curlid)                
                if ssid in self.segmentManager.segmentSetList.keys():
                    load = self.loadManager.CreateLoadSegmentSetwithID(curlid,name)
                    segmentSet = self.segmentManager.segmentSetList[ssid]
                    load.AddSegmentSet(segmentSet,lcid,sf,at)
                else:
                    print("Error : Segment Set ID {0} is not found".format(ssid))
                    exit(0)
            
        
        pass 
    
    def CreateBoundary(self):
        for boundaryOption in self.boundaryOptions:
            if boundaryOption["BoundaryType"] == "BOUNDARY_SPC_SET":
                self.CreateSPCSETforPackage(boundaryOption)
            else:
                print("Error : Boundary Type is not supported")
                exit(0)
                
    def CreateSPCSETforPackage(self, boundaryOption):
        nskeyList = boundaryOption["NSIDS"]
        cid = boundaryOption["CID"]
        dofx = boundaryOption["DOFX"]
        dofy = boundaryOption["DOFY"]
        dofz = boundaryOption["DOFZ"]
        dofrx = boundaryOption["DOFRX"]
        dofry = boundaryOption["DOFRY"]
        dofrz = boundaryOption["DOFRZ"]
        
        for nskey in nskeyList:
            nskey = int(nskey)
            if nskey in self.nSetKeytoID:
                nsids = self.nSetKeytoID[nskey]
                for nsid in nsids:
                    nset : NodeSet = self.nodeSetManager.nodeSets[nsid]
                    self.boundaryNodeManager.CreateBoundarySPCNodeSet(nset,cid,dofx,dofy,dofz,dofrx,dofry,dofrz,"SPCSET{0}".format(nset.name))
            
    def CreateDefine(self, partMan):
        for defineOption in self.defineOptions:
            if defineOption["DefineType"] == "DEFINE_CURVE_FUNCTION":
                self.CreateCurveFunctionforPackage(defineOption)
            elif defineOption["DefineType"] == "DEFINE_CURVE":
                self.CreateCurveforPackage(defineOption)
            else:
                print("Error : Define Type is not supported")
                exit(0)
                
    def CreateCurveFunctionforPackage(self, defineOption):
        LCID = defineOption["LCID"]
        SIDR = defineOption["SIDR"]
        SFA = defineOption["SFA"]
        SFO = defineOption["SFO"]
        OFFA = defineOption["OFFA"]
        OFFO = defineOption["OFFO"]
        DATTYP = defineOption["DATTYP"]
        LCINT = defineOption["LCINT"]
        variableMap = defineOption["VariableMap"]
        baseVars = defineOption["BaseVars"]
        OutputFunction = defineOption["OutputFunction"]
        
        baseVarName = baseVars[0]
        baseVarStart = baseVars[1]        
        baseVarStep = baseVars[2]
        baseVarEnd = baseVars[3]
        
        baseVarList = np.arange(baseVarStart,baseVarEnd+baseVarStep,baseVarStep).tolist()
        variables = re.findall(r'\{(.*?)\}', OutputFunction)
        A1List = []
        O1List = []
        for i in range(len(baseVarList)):
            curOutput = OutputFunction
            for variable in variables:
                if variable in variableMap.keys():
                    curOutput = curOutput.replace("{"+variable+"}",variableMap[variable])
            
            curOutput = curOutput.replace("{"+baseVarName+"}",str(baseVarList[i]))                
            value = eval(curOutput)
            A1List.append(baseVarList[i])
            O1List.append(value)
            print("A1: {0}, O1: {1}".format(baseVarList[i],value))

        self.defineManager.CreateDefineCurvewithID(LCID,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1List,O1List)
        
        

    def CreateCurveforPackage(self, defineOption):
        LCID = defineOption["LCID"]
        SIDR = defineOption["SIDR"]
        SFA = defineOption["SFA"]
        SFO = defineOption["SFO"]
        OFFA = defineOption["OFFA"]
        OFFO = defineOption["OFFO"]
        DATTYP = defineOption["DATTYP"]
        LCINT = defineOption["LCINT"]
        A1List = defineOption["A1List"]
        O1List = defineOption["O1List"]
        self.defineManager.CreateDefineCurvewithID(LCID,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1List,O1List)
        
                        
                                
    def CreateContact(self):
        for contactOption in self.contactOptions:
            if contactOption["ContactType"] == "RBE2":
                self.CreateRBE2ContactforPackage(contactOption)
            elif contactOption["ContactType"] == "TIED_PART":
                self.CreateTiedContactforPackage(contactOption)
            elif contactOption["ContactType"] == "NSettoNSet":
                self.CreateNodeSettoNodeSetContactforPackage(contactOption)
            else:
                print("Error : Contact Type is not supported")
                exit(0)
                
            
                
    def CreateTiedContactforPackage(self, contactOption):
        partIDA = contactOption["PartIDA"]
        partIDB = contactOption["PartIDB"]
        SSTYP = 3
        MSTYP = 3
        SBOXID = 0
        MBOXID = 0
        SPR = 0
        MPR = 0
        FS = 0.0
        FD = 0.0
        DC = 0.0
        VC = 0.0
        VDC = 0.0
        PENCHK = 0
        BT = 0.00
        DT = 1.00000E20
        SFS = ""
        SFM = ""
        SST = ""
        MST = ""
        SFST = ""
        SFMT = ""
        FSF = ""
        VSF = ""  
        if partIDA in self.partMan.parts:
            pass
        else:
            return
        
        if partIDB in self.partMan.parts:
            pass
        else: 
            return
            
        self.contactManager.CreateContactTiedSurfacetoSurfaceOffset(partIDA, partIDB, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
    
    def CreateNodeSettoNodeSetContactforPackage(self, contactOption):
        pass

    def CreateRBE2ContactforPackage(self, contactOption):
        AsideNodeSetKey = contactOption["AsideNodes"].split("#")
        BsideNodeSetKey = contactOption["BsideNodes"].split("#")
        nMinCon = contactOption["nMinCon"]
        tolerance = contactOption["tolerance"]
        cid = contactOption["cid"]
        pnode = contactOption["pnode"]
        irpt = contactOption["irpt"]
        drflag = contactOption["drflag"]
        rrflag = contactOption["rrflag"]
        
        ANodes = []
        BNodes = []
        for nodeKey in AsideNodeSetKey:
            nkey = int(nodeKey)
            if nkey in self.nSetKeytoID.keys():
                nsids = self.nSetKeytoID[nkey]
                for nsid in nsids:
                    nset : NodeSet = self.nodeSetManager.nodeSets[nsid]
                    for id in nset.nodes:
                        ANodes.append(nset.nodes[id])
                
        for nodeKey in BsideNodeSetKey:
            nkey = int(nodeKey)
            if nkey in self.nSetKeytoID.keys():
                nsids = self.nSetKeytoID[nkey]
                for nsid in nsids:
                    nset : NodeSet = self.nodeSetManager.nodeSets[nsid]
                    for id in nset.nodes:
                        BNodes.append(nset.nodes[id])
        
        Aoponent = []

        for i in range(len(ANodes)):
            Aoponent.append(None)
            
        BPoints = [(BNodes[i].x,BNodes[i].y,BNodes[i].z) for i in range(len(BNodes))]
        keytoid = [BNodes[i].id for i in range(len(BNodes))]
        tree = KDTree(BPoints)
        for i, NA in enumerate(ANodes):
            point = (NA.x,NA.y,NA.z)
            indices = tree.query_ball_point(point, tolerance)
            if len(indices) >= nMinCon:
                minDist = 1.0e99 
                for j in indices:
                    dist = NA.Distance(BNodes[j]) 
                    if dist < minDist:
                        minDist = dist
                        Aoponent[i] = BNodes[j]
        ''' 
        for i, NAid in enumerate(ANodes):
            NA = ANodes[i]
            minDist = 1.0e99
            
            for j in range(len(BNodes)):
                NB = BNodes[j]                
                dist = NA.Distance(NB)
                if dist < tolerance:
                    if dist < minDist:
                        minDist = dist
                        Aoponent[i] = BNodes[j]
        '''
        print("Num Aoponent: ",len(BNodes))
        
        nSetMan = self.nodeSetManager
        partMan = self.partMan
        for i in range(len(Aoponent)):
            if Aoponent[i] is not None:
                # remove APoponent in BNodes
                #print("Aoponent: ",Aoponent[i].id)
                curNodes = [ANodes[i],Aoponent[i]]
                nodeSet = nSetMan.CreateNodeSetwithNodes("RBENodeSet",0.0,0.0,0.0,0.0,"MECH",0,curNodes)
                partMan.CreateConstrainedNodalRigidBody("RBE2{0}to{1}".format(curNodes[0].id,curNodes[1].id),cid,pnode,irpt,drflag,rrflag,nodeSet)
                if Aoponent[i] in BNodes:
                    BNodes.remove(Aoponent[i])
        print("BNodes: ",len(BNodes))
        Boponent = []
        for i in range(len(BNodes)):
            Boponent.append(None)
        
        Apoints = [(ANodes[i].x,ANodes[i].y,ANodes[i].z) for i in range(len(ANodes))]
        keytoid = [ANodes[i].id for i in range(len(ANodes))]
        tree = KDTree(Apoints)
        for i, NB in enumerate(BNodes):
            point = (NB.x,NB.y,NB.z)
            indices = tree.query_ball_point(point, tolerance)
            if len(indices) >= nMinCon:
                minDist = 1.0e99 
                for j in indices:
                    dist = NB.Distance(ANodes[j]) 
                    if dist < minDist:
                        minDist = dist
                        Boponent[i] = ANodes[j]
        print("Num Boponent: ",len(Boponent))
        for i in range(len(Boponent)):
            if Boponent[i] is not None:
                curNodes = [Boponent[i],BNodes[i]]
                nodeSet = nSetMan.CreateNodeSetwithNodes("RBENodeSet",0.0,0.0,0.0,0.0,"MECH",0,curNodes)                
                partMan.CreateConstrainedNodalRigidBody("RBE2{0}to{1}".format(curNodes[0].id,curNodes[1].id),cid,pnode,irpt,drflag,rrflag,nodeSet)
                
                if Boponent[i] in ANodes:
                    ANodes.remove(Boponent[i])
        print("ANodes: ",len(ANodes))
                                
    def CombineNodeManager(self):
        self.nodeManager : NodeManager = NodeManager()
        for i in self.partMan.parts:
            part : KooPart = self.partMan.parts[i]
            self.nodeManager.AddNodesfromAnotherManager(part.nodeManager)
            # part의 node manager 통합 
            part.nodeManager = self.nodeManager
            part.elementManager.nodeManager = self.nodeManager

    def ExportNastranMesh(self, filePath, mode = "LinearStatic"):
        with open(filePath, 'w') as f:
            if mode == "LinearStatic":
                spcaddid = self.boundaryNodeManager.maxid + 1
                loadaddid = self.loadManager.maxid + 1
                f.write("INIT MASTER(S)\n")
                f.write("NASTRAN SYSTEM(442)=-1,SYSTEM(319)=1\n")
                f.write("ID FEMAP,FEMAP\n")
                f.write("SOL 101\n")
                f.write("CEND\n")
                f.write("  TITLE = KooAutomaticGenerator\n")
                f.write("  ECHO = NONE\n")
                f.write("  DISPLACEMENT(PLOT) = ALL\n")
                f.write("  STRESS(PLOT,CORNER) = ALL\n")
                f.write("  SPC = {spc}\n".format(spc=spcaddid))
                f.write("  LOAD = {load}\n".format(load=loadaddid))
                f.write("BEGIN BULK\n")
                f.write("PARAM,PRGPST,NO\n")
                f.write("PARAM,POST,-1\n")
                f.write("PARAM,OGEOM,NO\n")
                f.write("PARAM,AUTOSPC,YES\n")
                f.write("PARAM,K6ROT,100.\n")
                f.write("PARAM,GRDPNT,0\n")
                
            
            if self.nastranAddScript != "":
                f.write(self.nastranAddScript)
                
            if self.nodeManager == None:
                self.CombineNodeManager()
            
            addString = self.nodeManager.WritetoNastranKeyword(0)
            f.write(addString)  
            addString = self.materialManager.WritetoNastranKeyword(0)
            f.write(addString)
            maxelemID = 0
            for i in self.partMan.parts:
                part : KooPart = self.partMan.parts[i]
                addString = part.WritetoNastranPart()
                f.write(addString)                
                addString = part.WritetoNastranElements(0,0)
                f.write(addString)
                maxelemID = max(maxelemID,part.elementManager.maxID)
            for i in self.partMan.constrainedParts:
                part = self.partMan.constrainedParts[i]
                addString = part.WritetoNastranPart(maxelemID)
                f.write(addString)
            addString = self.boundaryNodeManager.WritetoNastranKeyword(0)
            f.write(addString)
            addString = self.loadManager.WritetoNastranKeyword(0,loadaddid)
            f.write(addString)
            
            ### write spcadd
            i = 1
            f.write("SPCADD  ")
            i = i + 1
            f.write(format(spcaddid,'>8d'))
            spcidList = self.boundaryNodeManager.boundaries.keys()
            for spcid in spcidList:
                f.write(format(spcid,'>8d'))
                i = i + 1
                if i % 9 == 0:
                    f.write("\n")
                    if i != len(spcidList)+1:
                        f.write("        ")
            if i % 9 != 0:
                f.write("\n")
            i = 1
            '''f.write("LOADADD ")
            i = i + 1
            f.write(format(loadaddid,'>8d'))
            i = i + 1
            f.write("     1.0")
            loadidList = self.loadManager.loads.keys()
            for loadid in loadidList:
                f.write("     1.0")
                i = i + 1
                f.write(format(loadid,'>8d'))
                i = i + 1
                
                if i % 9 == 0:
                    f.write("\n")
                    if i != len(loadidList)+1:
                        f.write("        ")
            if i % 9 != 0:
                f.write("\n")
            '''
            addString ="ENDDATA\n"
            f.write(addString)
                
            
            
    
    def ExportDynaMesh(self, filePath):            
        with open(filePath, 'w') as f:
            f.write("*KEYWORD\n")
            if self.dynaAddScript != "":
                f.write(self.dynaAddScript)
            #nnode = 0
            #nelem = 0
            if self.nodeManager == None:
                self.CombineNodeManager()
            # Buffer-layer 경계면 노드 merge (conformal 보장)
            if len(self.bufferMeshList) > 0:
                print("Merging boundary nodes for conformal buffer...")
                self.nodeManager.MergeNodes(1.0e-6)
            addString = self.nodeManager.WritetoDynaKeyword(0)
            f.write(addString)
                                                    
            for i in self.partMan.parts:
                part : KooPart = self.partMan.parts[i]
                addString = part.WritetoDynaPart()
                f.write(addString)
                #addString = part.WritetoDynaNodes(0)
                #f.write(addString)
                addString = part.WritetoDynaElements(0,0)
                f.write(addString)                
                #addString = part.WritetoDynaNodeSets(0)
                #f.write(addString)
                
                #nnode += part.nodeManager.NNode()
                #nelem += part.elementManager.NElement()
            addString = self.partMan.elementManager.WritetoDynaKeyword(0,0,0)
            f.write(addString)
            for i in self.partMan.constrainedParts:
                part = self.partMan.constrainedParts[i]
                addString = part.WritetoDynaPart()
                f.write(addString)
            addString = self.defineManager.WritetoDynaKeyword(0)
            f.write(addString)                            
            addString = self.nodeSetManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.segmentManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.materialManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.sectionManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.boundaryNodeManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.loadManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.contactManager.WritetoDynaKeyword(0)
            f.write(addString)
            
            f.write("*END")
            f.close()
        pass   

    def ExportAnsysAPDLMesh(self, filePath):
        with open(filePath, 'w') as f:
            f.write("/batch\n")
            f.write("/config,noeldb,1\n")
            f.write("*get,_wallstrt,active,,time,wall\n")
            f.write("/title,{0}\n".format("Package"))	        
            f.write("/com, -- - Data in consistent MKS units.See Solving Units in the help system for more information.\n")
            f.write("/units, MKS\n")
            f.write("/nopr\n")
            f.write("/wb, file, start              !signify a WB generated input file\n")
            f.write("/prep7\n")
            f.write("SHPP, OFF, , NOWARN\n")
            f.write("ncnv, 1, 1e9             !uMKS system, Increase DOF limit to 1e9\n")
            f.write("/nolist\n")
            f.write("etcon, set             !allow ANSYS to choose best KEYOP's for 180x elements\n")
            f.write("/com, *********** Nodes for the whole assembly ***********\n")
            if self.ansysAddScript != "":
                f.write(self.ansysAddScript)                

            for i in self.partMan.parts:
                part = self.partMan.parts[i]                
                addString = part.WritetoANSYSAPDLNodes(0)                
                f.write(addString)

                if type(part) == KooPart:
                    part : KooPart = part 
                    part.SetMaterialbyID(self.materialManager)
                    part.SetSectionbyID(self.sectionManager)
                    addString = part.WritetoAnsysAPDLShellElements(0,0)
                    f.write(addString)
                    addString = part.WritetoAnsysAPDLSolidElements(0,0)
                    f.write(addString)
                elif type(part) == KooPartComposite:
                    part : KooPartComposite = part
                    part.SetMaterialbyID(self.materialManager)
                    part.SetSectionbyID(self.sectionManager)
                    addString = part.WritetoAnsysAPDLShellElements(0,0)
                    f.write(addString)
                    pass            
                
            f.close()
    
    def ExportABAQUSPart(self, filePath):
        pass

    def ExportABAQUSMesh(self, filePath, partMode = False):        
        with open(filePath, 'w') as f:
            if self.abaqusAddScript != "":
                f.write(self.abaqusAddScript)
            if partMode == False:
                f.write("*Heading\n")
                f.write("Package\n")
                f.write("**\n")
                f.write("** PARTS\n")
                f.write("**\n")
            for i in self.partMan.parts:                
                part = self.partMan.parts[i]
                f.write("*Part,NAME={0}\n".format(part.name))
                if part.partType == "Part":
                    part : KooPart = part
                elif part.partType == "PartComposite":
                    part : KooPartComposite = part
                addString = part.WritetoABAQUSNodes(0)
                f.write(addString)        
                if type(part) == KooPart:
                    part.SetMaterialbyID(self.materialManager)
                    addString = part.WritetoABAQUSShellElements(0,0)        
                    f.write(addString)
                    addString = part.WritetoABAQUSSolidElements(0,0)
                    f.write(addString)
                elif type(part) == KooPartComposite:
                    addString = part.WritetoABAQUSShellElements(0,0)
                    f.write(addString)
                #addString = part.WritetoABAQUSElements(0,0)
                #f.write(addString)
                        
            f.write("*ORIENTATION,NAME=RECT1,DEFINITION=COORDINATES,SYSTEM=RECTANGULAR\n")
            f.write("1.0,0.0,0.0,0.0,1.0,0.0\n")
            f.write("0.0,0.0,0.0\n")

            
            if partMode == False: 
                f.write("*End Part\n")

    def ExportOBJMesh(self, filePath):
        with open(filePath, 'w') as f:
            addString = ""
            for i in self.partMan.parts:
                part = self.partMan.parts[i]
                addString += part.elementManager.GetExternalObjString()
                f.write(addString)
            f.close()

    def GenerateShapeList(self,maxNID=0,maxEID=0,maxPID=0,maxSID=0,maxMID=0, maxNSID=0 ):
        self.shapeList = []
        self.bufferMeshList = []
        i = 0

        meshGenerationMode = False        

        for layer in self.layerList:  
            i = i + 1

            layerith = i*10000
            if type(layer) == SolderJointsLayer:
                layer : SolderJointsLayer = layer
                if layer.meshGenerationMode:
                    layer.materialManager = self.materialManager
                    layer.sectionManager = self.sectionManager        
                    layer.nodesetManager = self.nodeSetManager
                layer.SetMaxIDs(maxNID,maxEID,maxPID,maxSID,maxMID,maxNSID)                
                layer.GenerateImportWarpageSurface()
                layer.GenerateImportWarpageSurface(1)
                layer.SetSolderJointObjects()
                shape = layer.GenerateSolderJoints()
                self.shapeList.extend(shape)
                if layer.meshGenerationMode:
                    meshGenerationMode = True
                    for shapeWarped in layer.warpedShapeList:
                        mesh = shapeWarped.meshManager
                        self.shapeList.append(mesh.shape)
                
                
                dh = layer.dh 
                #mindist = layer.minDistance
                #mintozero = layer.mintozero
                #zerotomax = layer.zerotomax
                
                topPointLists = layer.GetTopPointLists()
                
                for j in range(i,len(self.layerList)):
                    self.layerList[j].posZ += dh - layer.minZtop                    
                    #- layer.minDistance + layer.thickness - mintozero
                    self.layerList[j].SetRotation(layer.topRotate)
                    self.layerList[j].SetPosition(self.layerList[j].posX + layer.topX - layer.posX, self.layerList[j].posY + layer.topY - layer.posY, self.layerList[j].posZ)
                    if j == i:
                        if type(self.layerList[j]) == PackageWarpedLayer:
                            self.layerList[j].SetAdditionalTopPoints(topPointLists)
                    
                maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID = layer.GetMaxIDs()
            elif type(layer) == PackageWarpedLayer:
                layer : PackageWarpedLayer = layer
                layer.ith = layerith
                if layer.meshGenerationMode:
                    meshGenerationMode = True
                    layer.materialManager = self.materialManager
                    layer.sectionManager = self.sectionManager        
                    layer.nodesetManager = self.nodeSetManager
                layer.SetMaxIDs(maxNID,maxEID,maxPID,maxSID,maxMID,maxNSID)                
                layer.GenerateImportWarpageSurface()
                shape = layer.GenerateShapes()
                if layer.meshGenerationMode:
                    for shapeWarped in layer.warpedShapeList:
                        mesh = shapeWarped.meshManager
                        self.shapeList.append(mesh.shape)
                else:
                    if shape is not None:
                        self.shapeList.append(shape)
                '''dh = layer.dh
                for j in range(i,len(self.layerList)):
                    self.layerList[j].posZ += dh    '''                                    
                    
                maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID = layer.GetMaxIDs()
                
            elif type(layer) == PackageLayerDefined:
                layer : PackageLayerDefined = layer
                layer.ith = layerith
                if layer.meshGenerationMode:
                    layer.materialManager = self.materialManager
                    layer.sectionManager = self.sectionManager
                    layer.nodesetManager = self.nodeSetManager

                # ConformalHexa: 인접 층 실린더 footprint 전달
                if layer.meshType == "ConformalHexa":
                    adjCyls = []
                    layerIdx = self.layerList.index(layer)
                    # 이전 층 (아래)
                    if layerIdx > 0:
                        prevLayer = self.layerList[layerIdx - 1]
                        if type(prevLayer) == PackageLayerDefined and hasattr(prevLayer, 'cylinderList'):
                            for cyl in prevLayer.cylinderList:
                                adjCyls.append((cyl[0] + prevLayer.posX, cyl[1] + prevLayer.posY, cyl[2]))
                    # 다음 층 (위)
                    if layerIdx < len(self.layerList) - 1:
                        nextLayer = self.layerList[layerIdx + 1]
                        if type(nextLayer) == PackageLayerDefined and hasattr(nextLayer, 'cylinderList'):
                            for cyl in nextLayer.cylinderList:
                                adjCyls.append((cyl[0] + nextLayer.posX, cyl[1] + nextLayer.posY, cyl[2]))
                    layer.adjacentCylinderParams = adjCyls

                layer.SetMaxIDs(maxNID,maxEID,maxPID,maxSID,maxMID,maxNSID)
                layer.GenerateShape()  
                        
                if layer.meshGenerationMode:
                    meshGenerationMode = True
                    if layer.packageMesh != None:
                        self.shapeList.append(layer.packageMesh.shape)
                    for cylinderMesh in layer.cylinderMeshList:
                        self.shapeList.append(cylinderMesh.shape)
                    for boxMesh in layer.boxMeshList:
                        self.shapeList.append(boxMesh.shape)
                    for boxCrack in layer.boxCrackMeshList:
                        self.shapeList.append(boxCrack.shape)
                    for rectangleTubeMesh in layer.rectangleTubeMeshList:
                        self.shapeList.append(rectangleTubeMesh.shape)
                    for rectangleCircleCutMesh in layer.rectangleCircleCutMeshList:
                        self.shapeList.append(rectangleCircleCutMesh.shape)
                    for rectangleFilletCutMesh in layer.rectangleFilletCutMeshList:
                        self.shapeList.append(rectangleFilletCutMesh.shape)
                    for detailShapes in layer.polynomialPartMeshList:
                        self.shapeList.append(detailShapes.shape)
                    for detailShapes in layer.polynomialCutPartMeshList:
                        self.shapeList.append(detailShapes.shape)
                    for polynomialSweepMesh in layer.polynomialSweepMeshList:
                        self.shapeList.append(polynomialSweepMesh.shape)
                    for imageShapes in layer.imageMeshList:
                        self.shapeList.append(imageShapes.shape)
                    for stlShapes in layer.stlMeshList:
                        self.shapeList.append(stlShapes.shape)
                    for stepShapes in layer.stepMeshList:
                        self.shapeList.append(stepShapes.shape)
                    for mshShapes in layer.mshMeshList:
                        self.shapeList.append(mshShapes.shape)
                    for shieldcanShapes in layer.shieldCanMeshList:
                        self.shapeList.append(shieldcanShapes.shape)
                    for conformalMesh in layer.conformalMeshList:
                        if conformalMesh.shape is not None:
                            self.shapeList.append(conformalMesh.shape)

                else:
                    
                    if layer.shape != None:           
                        self.shapeList.append(layer.shape)
                    for detailShapes in layer.detailSolderShapeList:
                        self.shapeList.append(detailShapes)
                    for cylinderShapes in layer.cylinderShapeList:                                                
                        self.shapeList.append(cylinderShapes)
                    for boxShapes in layer.boxShapeList:
                        self.shapeList.append(boxShapes)
                    for boxCrackShapes in layer.boxCrackShapeList:
                        self.shapeList.append(boxCrackShapes)
                    for rectangleTubeShapes in layer.rectangleTubeShapeList:
                        self.shapeList.append(rectangleTubeShapes)
                    for rectangleCircleCutShapes in layer.rectangleCircleCutShapeList:
                        self.shapeList.append(rectangleCircleCutShapes)
                    for rectangleFilletCutShapes in layer.rectangleFilletCutShapeList:
                        self.shapeList.append(rectangleFilletCutShapes)
                    for imageShapes in layer.imageShapeList:
                        self.shapeList.append(imageShapes)
                    for detailShapes in layer.detailPolynomialPartShapeList:
                        self.shapeList.append(detailShapes)
                    for detailShapes in layer.detailPolynomialCutPartShapeList:
                        self.shapeList.append(detailShapes)
                    for polynomialSweepShapes in layer.polynomialSweepShapeList:
                        self.shapeList.append(polynomialSweepShapes)
                    for stlShapes in layer.stlShapeList:
                        self.shapeList.append(stlShapes)
                    for stepShapes in layer.stepShapeList:
                        self.shapeList.append(stepShapes)
                    for mshShapes in layer.mshShapeList:
                        self.shapeList.append(mshShapes)
                    for shieldCanShapes in layer.shieldCanShapeList:
                        self.shapeList.append(shieldCanShapes)

                maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID = layer.GetMaxIDs()

        # --- Tetra Buffer 생성 (ConformalHexa 모드) ---
        # 모든 ConformalHexa 층을 수집하고, 인접 쌍에서
        # 한쪽이라도 실린더/박스가 없는 사각형 층이면 buffer 생성
        allConformalLayers = []
        for layer in self.layerList:
            if type(layer) == PackageLayerDefined:
                if layer.meshType == "ConformalHexa":
                    allConformalLayers.append(layer)

        if len(allConformalLayers) > 1:
            for idx in range(len(allConformalLayers) - 1):
                bottomLayer = allConformalLayers[idx]
                topLayer = allConformalLayers[idx + 1]

                # 한쪽이라도 실린더/박스가 없는 순수 사각형이어야 buffer 생성
                bottomHasGeom = len(bottomLayer.cylinderList) > 0
                topHasGeom = len(topLayer.cylinderList) > 0
                if bottomHasGeom and topHasGeom:
                    print("Skipping buffer between '{0}' and '{1}': both have cylinders".format(
                        bottomLayer.name, topLayer.name))
                    continue

                # buffer 두께: 사각형 층의 conformalBufferThickness 사용
                if not bottomHasGeom and bottomLayer.conformalBufferThickness > 0:
                    bufferThickness = bottomLayer.conformalBufferThickness
                elif not topHasGeom and topLayer.conformalBufferThickness > 0:
                    bufferThickness = topLayer.conformalBufferThickness
                else:
                    # 둘 다 사각형이면 둘 중 큰 값 사용
                    bt = bottomLayer.conformalBufferThickness
                    tt = topLayer.conformalBufferThickness
                    bufferThickness = max(bt, tt)
                    if bufferThickness <= 0:
                        continue

                # Z 좌표: buffer는 사각형 층의 core 상/하면과 인접 층 사이
                # 아래층 상면 ~ 위층 하면 사이의 전체 gap을 tetra로 채움
                bottomTopZ = bottomLayer.posZ + bottomLayer.thickness
                topBottomZ = topLayer.posZ
                bufferThick = topBottomZ - bottomTopZ

                # conformalBufferThickness로 core가 줄어든 경우 gap이 생김
                if hasattr(bottomLayer, 'conformalCoreZ') and hasattr(bottomLayer, 'conformalCoreThickness'):
                    bottomTopZ = bottomLayer.conformalCoreZ + bottomLayer.conformalCoreThickness
                if hasattr(topLayer, 'conformalCoreZ'):
                    topBottomZ = topLayer.conformalCoreZ
                bufferThick = topBottomZ - bottomTopZ

                if bufferThick <= 0:
                    print("Warning: no gap between layer {0} and {1}, skipping buffer".format(
                        bottomLayer.name, topLayer.name))
                    continue

                print("Tetra Buffer: {0} -> {1}, thickness={2:.4f}".format(
                    bottomLayer.name, topLayer.name, bufferThick))

                bufferMeshManager = KooMeshManagerGMSH(
                    sectionMan=self.sectionManager,
                    materialMan=self.materialManager,
                    nodeSetMan=self.nodeSetManager
                )
                bufferMeshPath = bottomLayer.meshPath
                bufferMeshManager.SetPath(bufferMeshPath)
                bufferMeshManager.SetName("Buffer_{0}_{1}".format(bottomLayer.name, topLayer.name))

                # buffer가 정의된 층(사각형 층)의 전체 영역을 커버
                # bufferLayer: conformalBufferThickness가 정의된 층
                if not bottomHasGeom and bottomLayer.conformalBufferThickness > 0:
                    bufferLayer = bottomLayer
                else:
                    bufferLayer = topLayer

                bfLeftX = bufferLayer.posX - bufferLayer.xLength / 2.0
                bfLeftY = bufferLayer.posY - bufferLayer.yLength / 2.0
                bufferBox = (bfLeftX, bfLeftY,
                             bfLeftX + bufferLayer.xLength,
                             bfLeftY + bufferLayer.yLength)

                # 인접 층의 NodeManager에서 경계면 노드 직접 전달
                bottomNodeMan = bottomLayer.conformalMeshList[0].nodeMan if len(bottomLayer.conformalMeshList) > 0 else None
                topNodeMan = topLayer.conformalMeshList[0].nodeMan if len(topLayer.conformalMeshList) > 0 else None

                if bottomNodeMan is None or topNodeMan is None:
                    print("Warning: missing conformal mesh NodeManager, skipping buffer")
                    continue

                result = bufferMeshManager.mesh_tetra_buffer(
                    bottomNodeMan=bottomNodeMan,
                    topNodeMan=topNodeMan,
                    zBottom=bottomTopZ,
                    zTop=topBottomZ,
                    bufferBox=bufferBox,
                    maxNID=maxNID,
                    maxEID=maxEID
                )

                if result is not None:
                    maxNID, maxEID = bufferMeshManager.GetMaxIDs()
                    maxPID = maxPID + 1
                    bufferMeshManager.part.SetID(maxPID)
                    # shape=None (프로그래밍 방식이므로 STL 없음), shapeList에는 추가하지 않음
                    self.bufferMeshList.append(bufferMeshManager)
                    meshGenerationMode = True

        if meshGenerationMode:
            self.TransformedMeshShapeList()

        shapeList = self.TransformedShapeList()

        return shapeList
    
    def GetCombinedTransform(self):
        rotation = self.rotation
        mirror = self.mirror
        originX = self.xOrigin
        originY = self.yOrigin
        originZ = self.zOrigin
        totalThickness = self.totalThickness
        isTop = self.isTop
         
        R = gp_Trsf()
        R.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), -rotation*math.pi/180.0)

        M = gp_Trsf()
        if mirror:
            # 미러는 '로컬축' 기준.
            # 미러가 회전보다 먼저 적용되므로, 여기서는 '회전 전 축'을 사용해야 합니다.
            # "X 플립"을 원하면 YZ-평면(Dir(1,0,0)), "Y 플립"은 XZ-평면(Dir(0,1,0)).
            # 로직: 회전 후의 효과가 X/Y로 보이게 하려면 다음과 같이 고정하는 게 안전합니다.
            #   - mirrorX를 원하면 Dir(1,0,0), mirrorY면 Dir(0,1,0)
            # 질문 코드 패턴 유지: 90/270일 때는 '로컬X 플립'이 '글로벌Y 플립'처럼 보이게 하려면
            # 회전보다 먼저 적용이므로, 분기 없이 원하는 '로컬 플립'을 직접 지정하세요.
            M.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(1,0,0)))  # 예: X 좌표 부호 반전(= YZ-평면 대칭)

        B = gp_Trsf()
        if not isTop:
            # 보드 뒷면(바텀)을 위에서 내려다보는 뷰로 만들려면 Z-미러(= XY 평면 대칭)가 일반적
            B.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1)))

        T = gp_Trsf()
        if isTop:
            T.SetTranslation(gp_Vec(originX, originY, originZ))
        else:
            T.SetTranslation(gp_Vec(originX, originY, originZ - totalThickness))

        # 합성: 최종 적용 순서가 M → R → B → T 가 되도록 곱셈 순서 지정
        combined = T.Multiplied(B).Multiplied(R).Multiplied(M)
        return combined
    
    def TransformedShapeList(self):
        
        shapesTransformed = []
        combinedTrsf = self.GetCombinedTransform()
        for shape in self.shapeList:
            if shape != None:   
                if type(shape) == list:
                    for subshape in shape:
                        if subshape != None:
                            shapeTransformed = BRepBuilderAPI_Transform(subshape,combinedTrsf).Shape()
                            shapesTransformed.append(shapeTransformed)
                else:
                    shapeTransformed = BRepBuilderAPI_Transform(shape,combinedTrsf).Shape()
                    shapesTransformed.append(shapeTransformed)
        return shapesTransformed
        
        
    # 개발중 
    def TransformedMeshShapeList(self):   
        combinedTrsf = self.GetCombinedTransform() 
        isTop = self.isTop
        isYZPlaneMirrorMode = False
        isXZPlaneMirrorMode = False
        if self.rotation == 90 or self.rotation == 270:
            if self.mirror:
                isXZPlaneMirrorMode = True
        else:
            if self.mirror:
                isYZPlaneMirrorMode = True               
        
        for layer in self.layerList:
            if type(layer) == SolderJointsLayer:
                layer : SolderJointsLayer = layer
                if layer.meshGenerationMode:
                    for warpedShape in layer.warpedShapeList:
                        part = warpedShape.meshManager.part
                        nodes = part.elementManager.GetElementNodes()
                        for nid in nodes:
                            nodes[nid].Transform(combinedTrsf)
                        if isYZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityYZPlane()
                        if isXZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityXZPlane()
                        if isTop == False:
                            part.elementManager.SetMirrorConnectivityXYPlane()
                            
            elif type(layer) == PackageWarpedLayer:
                layer : PackageWarpedLayer = layer
                if layer.meshGenerationMode:
                    for warpedShape in layer.warpedShapeList:
                        part = warpedShape.meshManager.part
                        nodes = part.elementManager.GetElementNodes()
                        for nid in nodes:
                            nodes[nid].Transform(combinedTrsf)
                        if isYZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityYZPlane()
                        if isXZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityXZPlane()
                        if isTop == False:
                            part.elementManager.SetMirrorConnectivityXYPlane()
            elif type(layer) == PackageLayerDefined:
                layer : PackageLayerDefined = layer
                if layer.meshGenerationMode:
                    partList = []
                    if layer.packageMesh != None:
                        part = layer.packageMesh.part
                        partList.append(part)
                                                    
                    for i in range(len(layer.mshMeshList)):
                        part = layer.mshMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.boxCrackMeshList)):
                        part = layer.boxCrackMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.cylinderMeshList)):
                        part = layer.cylinderMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.boxMeshList)):
                        part = layer.boxMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.rectangleTubeMeshList)):
                        part = layer.rectangleTubeMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.rectangleCircleCutMeshList)):
                        part = layer.rectangleCircleCutMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.rectangleFilletCutMeshList)):
                        part = layer.rectangleFilletCutMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.polynomialPartMeshList)):
                        part = layer.polynomialPartMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.polynomialCutPartMeshList)):
                        part = layer.polynomialCutPartMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.polynomialSweepMeshList)):
                        part = layer.polynomialSweepMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.imageMeshList)):   
                        part = layer.imageMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.stlMeshList)):
                        part = layer.stlMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.stepMeshList)):
                        part = layer.stepMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.shieldCanMeshList)):
                        part = layer.shieldCanMeshList[i].part
                        partList.append(part)
                    for i in range(len(layer.conformalMeshList)):
                        part = layer.conformalMeshList[i].part
                        partList.append(part)

                    for i in range(len(partList)):
                        part = partList[i]
                        nodes = part.elementManager.GetElementNodes()
                        for nid in nodes:
                            nodes[nid].Transform(combinedTrsf)
                        if isYZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityYZPlane()
                        if isXZPlaneMirrorMode:
                            part.elementManager.SetMirrorConnectivityXZPlane()
                        if isTop == False:
                            part.elementManager.SetMirrorConnectivityXYPlane()

        # Buffer mesh도 transform 적용
        for bufferMesh in self.bufferMeshList:
            part = bufferMesh.part
            nodes = part.elementManager.GetElementNodes()
            for nid in nodes:
                nodes[nid].Transform(combinedTrsf)
            if isYZPlaneMirrorMode:
                part.elementManager.SetMirrorConnectivityYZPlane()
            if isXZPlaneMirrorMode:
                part.elementManager.SetMirrorConnectivityXZPlane()
            if isTop == False:
                part.elementManager.SetMirrorConnectivityXYPlane()

    def ExportPackage(self):

        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        for shape in self.shapeList:
            if type(shape) == list:
                for subshape in shape:
                    if subshape != None:
                        builder.Add(compound,subshape)
            elif shape != None:
                builder.Add(compound,shape)
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        print("Save Solder Joints to STEP File")
        step_writer = STEPControl_Writer()
        #for shape in self.shapeList:
        #    step_writer.Transfer(shape, STEPControl_AsIs)
        step_writer.Transfer(compound, STEPControl_AsIs)
        status = step_writer.Write(self.outFileName)
        #if status == 0:            
        print("Done.\n")
        #else:
        #print("Error: can't write file.\n")
        #pass

import socket

def get_ip_address():
    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Connect to a remote server (doesn't matter which)
        sock.connect(("8.8.8.8", 80))
        # Retrieve the local IP address
        ip_address = sock.getsockname()[0]
    except socket.error:
        ip_address = None
    finally:
        # Close the socket
        sock.close()

    return ip_address

import requests
import json
from datetime import datetime

def get_current_time(url):
    try:
        # Send an HTTP GET request to the specified URL
        response = requests.get(url)
        # Extract the current time from the response
        data = json.loads(response.text)
        #{"year":2023,"month":7,"day":11,"hour":12,"minute":46,"seconds":53,"milliSeconds":490,"dateTime":"2023-07-11T12:46:53.4904705","date":"07/11/2023","time":"12:46","timeZone":"Asia/Seoul","dayOfWeek":"Tuesday","dstActive":false}

        current_time = datetime(data["year"],data["month"],data["day"],data["hour"],data["minute"],data["seconds"],data["milliSeconds"])
        #current_time = datetime.strptime(response.text, "%Y-%m-%d %H:%M:%S")
        return current_time
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
        return None
    


if __name__ == '__main__':

    
    # List of registered IP addresses
    registered_ips = ["219.250.247.155","222.234.112.125", "219.250.247.168", "10.252.34.71", "10.252.32.210", "10.252.33.107", "58.124.52.240", "10.252.32.33"]

    # Get the current IP address
    ip = get_ip_address()

    # Check if the current IP is in the registered list
    if ip in registered_ips:
        print("Access granted. IP address:", ip)
        # Continue running the application
    else:
        print("Access denied. IP address:", ip)
        exit(0)
        # Terminate the application or perform any desired action
  

    
    # Specify the URL of the website that provides the current time
    time_website_url = "https://www.timeapi.io/api/Time/current/zone?timeZone=Asia/Seoul"

    # Specify the threshold date for termination
    threshold_date = datetime(2025, 12, 1)

    # Call the function to get the current time from the website
    current_time = get_current_time(time_website_url)

    # Check if the current time was successfully retrieved
    if current_time is not None:
        print("Current time:", current_time)
        print("License Limit Date:",threshold_date)

        # Compare the current time with the threshold date
        if current_time > threshold_date:
            print("Terminating the application. Threshold date exceeded.")
            # Terminate the application or perform any other desired action
            exit(0)
        else:
            print("Threshold date not exceeded. Continuing with the application.")
            # Continue running the application
    else:
        exit(0)
    
    if len(sys.argv)<2:
        #print("Usage: PackageGenerator.exe [input file path] [output file path]")
        #sys.exit(0)
        sys.argv.clear() 
        sys.argv.append("PackageGenerator")
        #sys.argv.append("PackageInfo.txt")
        #sys.argv.append("PackageInfoDetail.txt")
        #sys.argv.append("PackageInfoold.txt")
        #sys.argv.append("PackageInfoSimple.txt")
        #sys.argv.append("PackageInfo_PolynomialPart.txt")
        #sys.argv.append("PackageInfo_PolynomialCutPart.txt")
        sys.argv.append("PackageInfo_ImagePart.txt")
        #sys.argv.append("PackageInfo_PolynomialCutPartMesh.txt")
        #sys.argv.append("PackageInfoCylinderMesh.txt")
        
        #sys.argv.append("layer1ContourInfo.txt")
        

        sys.argv.append("PackageOut.stp")
    
    inputFilePath = sys.argv[1]    
    
    
    #get current directory 
    currentDirectory = os.getcwd()
    #input file to path 
    inputFilePath = os.path.join(currentDirectory,inputFilePath)

    
    print("inputFilePath: ",inputFilePath)     
    if os.path.exists(inputFilePath):
        print("File exists.")
    else:
        print("File does not exist.")
    xOrigin = 30.0
    yOrigin = 0.0 
    zOrigin = 5.0
    package = PackageUserdefined(xOrigin,yOrigin,zOrigin,90,True)
    if len(sys.argv)>=3:        
        outputFilePath = sys.argv[2]
        print("outputFilePath: ",outputFilePath)
        package.outFileName = outputFilePath
    package.outFileName = os.path.join(currentDirectory,package.outFileName)

    print("Import Package")
    package.ImportPackage(inputFilePath)
    
    shapes = package.GenerateShapeList()
    
    shapesTransformed = [] 
    shapesTransformed = package.TransformedShapeList()  
  
        
    print("Shape Generated")
    print("Export Package")
    package.ExportPackage()
    print("Package Exported")
    print("Display Package")
    i = 0
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:
        # 정상 GUI 모드
        from OCC.Display.SimpleGui import init_display
        display, start_display, add_menu, add_function_to_menu = init_display()
    
        for shape in shapes:
            if shape != None:
                display.DisplayShape(shape,update=False)    
            i = i + 1
            #print("Shape " + str(i) + " Displayed")
        '''        
        for shape in shapesTransformed:
            if shape != None:
                display.DisplayShape(shape,update=False)    
            i = i + 1
            #print("Shape " + str(i) + " Displayed")
        '''
        display.FitAll()

        # Top view 
        display.GetView().SetProj(0,0,10)
        start_display()

    


    


