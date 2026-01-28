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


from KooODBCADManager.WarpageSurface import WarpageSurface
from KooODBCADManager.WarpageSolderJoint import SolderMaskedDefined, NonSolderMaskedDefined

from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
from OCC.Core.BRep import BRep_Tool_PolygonOnTriangulation
from OCC.Core.BRepFill import BRepFill_Filling
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
import random
import multiprocessing

from KooODBCADManager.PackageLayer import PackageLayer

from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH, KooMeshManagerList
from KooCAEManager.KooNode import NodeManager, Node
from KooCAEManager.KooElement import ElementManager
from KooCAEManager.KooPart import KooPartManager, KooPart, KooPartComposite
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooNode import NodeSetManager
from KooCAEManager.KooSection import *

class PackageWarpedLayer(PackageLayer):
    def __init__(self, name = "", x = 0.0, y = 0.0, z=0.0, xLength = -1.0, yLength = -1.0, thickness = 1.0, secMan : KooSectionManager = None, matMan : KooMaterialManager = None, nSetMan : NodeSetManager = None):
        super(PackageWarpedLayer,self).__init__(name, x, y, z, xLength, yLength, thickness, secMan, matMan, nSetMan)
        
        self.variablesList = []
        self.shapesWarped = []
        self.warpageVariableList = [] 
        self.warpageVariableListTop = []
        self.warpageSurface = WarpageSurface()
        self.warpageSurfaceTop = WarpageSurface()
        self.bsplineSurface = None
        self.bsplineSurfaceTop = None
        
        self.meshGenerationMode = False
        self.additionalPointLists = [] 
        
        self.warpedShapeList = []
        self.dh = 0.0 
        self.shape = None
        pass

    
    def SetAdditionalTopPoints(self, pointLists):
        self.additionalPointLists.extend(pointLists)
        
    def AddVariables(self, variables, warpageVariableList = None, warpageVariableListTop = None):
        self.variablesList.append(variables)
        if warpageVariableList is not None:
            self.warpageVariableList = warpageVariableList
        if warpageVariableListTop is not None:
            self.warpageVariableListTop = warpageVariableListTop
    
    def SetWarpageVariables(self, warpageVariableList):
        self.warpageVariableList = warpageVariableList
        
    def SetWarpageVariablesTop(self, warpageVariableListTop):
        self.warpageVariableListTop = warpageVariableListTop
    
    def SetWarpageSurface(self, warpedSurface):
        self.warpageSurface = warpedSurface
        
    def SetWarpageSurfaceTop(self, warpedSurface):
        self.warpageSurfaceTop = warpedSurface
    
    def SetBSplineSurface(self, bsplineSurface):
        self.bsplineSurface = bsplineSurface
    
    def SetBSplineSurfaceTop(self, bsplineSurface):
        self.bsplineSurfaceTop = bsplineSurface
    
    def GenerateImportWarpageSurface(self, Option=0, warpageVariableList = None):
        if Option == 0:
            warpageVariableList = self.warpageVariableList
        elif Option == 1:
            if len(self.warpageVariableListTop) == 0:
                warpageVariableList = self.warpageVariableList
            else:
                warpageVariableList = self.warpageVariableListTop
        else:
            pass
        if len(warpageVariableList) < 9:
            print("No Warpage File")
            return None
        fileName = warpageVariableList[0]
        locX = warpageVariableList[1]
        locY = warpageVariableList[2]
        locZ = warpageVariableList[3]
        bdBox = [warpageVariableList[4], warpageVariableList[5], warpageVariableList[6], warpageVariableList[7]]
        unit = warpageVariableList[8]
        if len(warpageVariableList) > 9:
            amplification = warpageVariableList[9]
        else:
            amplification = 1.0
        return self.ImportWarpageSurface(fileName, locX, locY, locZ, bdBox, unit, amplification, Option)
        
    
    def ImportWarpageSurface(self, filename, locX, locY, locZ, bdBox, unit='MM', amplification=1.0, Option = 0):
        warpageSurface = WarpageSurface()
        warpageSurface.SetWarpageUnit(unit)
        warpageSurface.SetWarpageFile(filename)
        warpageSurface.ImportWarpage(None, amplification)
        warpageSurface.RemoveEmptySpace()
        warpageSurface.SmoothWarpage()
        if Option == 0:
            self.warpageSurface = warpageSurface
        elif Option == 1:
            self.warpageSurfaceTop = warpageSurface
        else:
            pass
        xLength = bdBox[1] - bdBox[0]
        yLength = bdBox[3] - bdBox[2]
        print("Generate BSpline Surface")   
        bsplineSurface = warpageSurface.MakeBSplineSurface(locX + bdBox[0], locY + bdBox[2], locZ, xLength, yLength)
        if Option == 0:
            self.bsplineSurface = bsplineSurface
        elif Option == 1:
            self.bsplineSurfaceTop = bsplineSurface
        else:
            pass
        print("Generate BSpline Surface Done")
        return self.bsplineSurface
    
    def generate_random_points_inside_polygon(self, polygon, num_points):
        points = []
        
        min_x = min(p.X() for p in polygon)
        max_x = max(p.X() for p in polygon)
        min_y = min(p.Y() for p in polygon)
        max_y = max(p.Y() for p in polygon)
        z = polygon[0].Z()
        
        option = 1
        option = 2
        if option == 1:
            newPoints = self.generate_rectangular_points(min_x, max_x, min_y, max_y, 5,5)
            for p in newPoints:
                if self.is_point_inside_polygon(p, polygon):
                    pnt = gp_Pnt(p[0],p[1],z)
                    points.append(pnt)
        elif option == 2:
            while len(points) < num_points:
                point = self.generate_random_point(min_x, max_x, min_y, max_y)
                if self.is_point_inside_polygon(point, polygon):
                    pnt = gp_Pnt(point[0],point[1],z)
                    points.append(pnt)
        '''print("Additional points generated")
        for p in points:
            print(p.X(), p.Y(), p.Z())'''
        return points
    
    def generate_random_point(self, min_x, max_x, min_y, max_y):
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        return x, y

    def generate_rectangular_points(self, min_x, max_x, min_y, max_y, num_point_x, num_point_y):
        points = [] 
        x_step = (max_x - min_x)/num_point_x
        y_step = (max_y - min_y)/num_point_y
        for i in range(num_point_x):
            for j in range(num_point_y):
                x = min_x + i*x_step
                y = min_y + j*y_step
                points.append((x,y))
        return points

    def is_point_inside_polygon(self, point, polygon):
        x, y = point
        n = len(polygon)
        inside = False
        p1x = polygon[0].X()
        p1y = polygon[0].Y()
        for i in range(n+1):
            p2x = polygon[i % n].X()
            p2y = polygon[i % n].Y()
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def ProjectPointOnWarpageSurface(self, point_list, warpageFace):
        pointsProjected = []
        for i in range(len(point_list)):
            point_projection = GeomAPI_ProjectPointOnSurf(point_list[i], warpageFace)
            projected_point = point_projection.NearestPoint()
            projected_point = gp_Pnt(projected_point.X(), projected_point.Y(), projected_point.Z() + point_list[i].Z())
            pointsProjected.append(projected_point)
        return pointsProjected
    
    def GenerateProjectedSurfacebyPointListandWarpageSurface(self,point_list,warpageFace, additional_points = []):
        pbuilder = BRepBuilderAPI_MakePolygon()
        pointsProjected = [] 
        additionalPointsProjected = []         
        
        for i in range(len(point_list)):            
            point_projection = GeomAPI_ProjectPointOnSurf(point_list[i], warpageFace)            
            projected_point = point_projection.NearestPoint()
            projected_point = gp_Pnt(projected_point.X(), projected_point.Y(), projected_point.Z() + point_list[i].Z())            
            print(i,projected_point.X(),projected_point.Y(),projected_point.Z())
            pbuilder.Add(projected_point)
            pointsProjected.append(projected_point)    
            #print(i,pointsProjected[i].X(),pointsProjected[i].Y(),pointsProjected[i].Z())
        
        for i in range(len(additional_points)):
            point_projection = GeomAPI_ProjectPointOnSurf(additional_points[i], warpageFace)
            projected_point = point_projection.NearestPoint()
            projected_point = gp_Pnt(projected_point.X(), projected_point.Y(), projected_point.Z() + additional_points[i].Z())
            additionalPointsProjected.append(projected_point)
        
        
        # Create a BRepFill_Filling object
        filling = BRepFill_Filling()
        # Add the points to the filling object
        edges = []
        
        print("Edge Generating...")
        for i in range(len(pointsProjected) - 1):
            #print(i,len(pointsProjected) - 1)
            #print(pointsProjected[i].X(),pointsProjected[i].Y(),pointsProjected[i].Z()) 
            #print(pointsProjected[i+1].X(),pointsProjected[i+1].Y(),pointsProjected[i+1].Z())   
            
            edge = BRepBuilderAPI_MakeEdge(pointsProjected[i], pointsProjected[i + 1])            
            edges.append(edge.Edge())
        print("Edge Generating...Done")  
        import OCC.Core.GeomAbs as GeomAbs
        # Create a BRepFill_Filling object and perform the filling operation

        filling = BRepFill_Filling(3,15,2,False,0.00001,0.0001,0.01,0.1,4,20)
        for edge in edges:
            #filling.Add(edge,GeomAbs.GeomAbs_C0)
            filling.Add(edge,GeomAbs.GeomAbs_C0)

        if len(additionalPointsProjected) > 0:
            for pnt in additionalPointsProjected:
                filling.Add(pnt)
        filling.Build()
        
        surface = filling.Face()
        criteria = 0.0001
        while surface.IsNull():
            #filling = BRepFill_Filling(3,15,2,False,criteria,criteria,0.1,0.1,20,20)
            filling = BRepFill_Filling(3, 15, 10, False, criteria, criteria, 0.1, 0.1, 10, 30)
            for edge in edges:
                filling.Add(edge,GeomAbs.GeomAbs_C0)

            if len(additionalPointsProjected) > 0:
                for pnt in additionalPointsProjected:
                    filling.Add(pnt)
            filling.Build()
            
            surface = filling.Face()
            criteria = criteria *1.1
            print("Current Criteria :", criteria)
        print("Face Generating...Done")        
        return surface
    
    def PrismfromPoints(self, point_list, thickness = 0.0):        
        if self.bsplineSurface is None:
            self.bsplineSurface = self.GenerateImportWarpageSurface()
            if self.bsplineSurface is None:
                print("Generate BSpline Surface is None")
                polygon = BRepBuilderAPI_MakePolygon()
                for p in point_list:
                    polygon.Add(p)
                polygon.Close()
                polygon.Build()
                surface = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
           
        if self.bsplineSurface is not None:                
            num_additional_points = 200  # Number of additional points to generate                                    
                                    
            additional_points = self.generate_random_points_inside_polygon(point_list, num_additional_points)        
            print("Additional Points")
            for i in range(len(additional_points)):
                print(additional_points[i].X(),additional_points[i].Y(),additional_points[i].Z())
            '''if len(self.additionalPointLists) > 0:
                additional_points = []
                for i in range(len(self.additionalPointLists)):
                    pt = self.additionalPointLists[i]
                    additional_points.append(gp_Pnt(pt.X(),pt.Y(),0.0))
                #additional_points.extend(self.additionalPointLists)
                print("New Additional Points")
                for i in range(len(additional_points)):
                    print(additional_points[i].X(),additional_points[i].Y(),additional_points[i].Z())
                for i in range(0,len(point_list)-1):
                    pi = point_list[i]
                    pi1 = point_list[i+1]
                    n = 5
                    for j in range(1,n):
                        p = gp_Pnt(pi.X() + (pi1.X() - pi.X()) * j/n, pi.Y() + (pi1.Y() - pi.Y()) * j/n, pi.Z() + (pi1.Z() - pi.Z()) * j/n)
                        additional_points.append(p)'''
                                    
                        
            surface = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list,self.bsplineSurface,additional_points)
            
        else:
            pass
        if thickness == 0.0:
            thickness = self.thickness
        sweep_direction = gp_Vec(0,0,thickness)
        prism = BRepPrimAPI_MakePrism(surface, sweep_direction).Shape()
        # prism transformation to z direction
        #trsf = gp_Trsf()
        #trsf.SetTranslation(gp_Vec(0,0,self.posZ))
        #prism = BRepBuilderAPI_Transform(prism, trsf).Shape()
        #prism = self.Transformation(prism)        
        return prism
    
    def GetTransformation(self):
        trsf = gp_Trsf()
        trsf2 = gp_Trsf()
        
        trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), math.pi*self.rotate/180.0)
        trsf2.SetTranslation(gp_Vec(self.posX, self.posY, self.posZ))
        trsf.Multiply(trsf2)
        return trsf    
    
    def Transformation(self, shape,trsf = None):
        if trsf is None:
            trsf = self.GetTransformation()
        
        shape = BRepBuilderAPI_Transform(shape, trsf).Shape()
        return shape
    
    def GenerateBoxWarped(self, variables):
        box = BoxWarped(sectionMan=self.sectionManager, materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
        box.SetMaxIDs(self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID)
        box.SetVariables(variables)
        point_list = box.Generate()
        shape = self.PrismfromPoints(point_list)
        shape = self.Transformation(shape)
        if self.meshGenerationMode == True:
            meshType = self.meshType
            meshSize = self.meshSizeInPlane
            numElemX = self.numberofElementinX
            numElemY = self.numberofElementinY
            numElemZ = self.numberofElementinThickness
            meshPath = self.meshPath
            bottomSurface = self.GenerateImportWarpageSurface(0)
            topSurface = self.GenerateImportWarpageSurface(1)
            thickness = self.thickness
            name = self.name
            #box.SetMaxIDs(self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID)
            posZ = self.posZ
            trsf = self.GetTransformation()
            if numElemX == 0 or numElemY == 0:
                box.GenerateMesh(trsf,posZ, name, thickness, meshPath, meshType, meshSize, numElemZ, bottomSurface, topSurface)
            else:
                box.GenerateStructuredMesh(trsf,posZ, name, thickness, meshPath, meshType, numElemX, numElemY, numElemZ, bottomSurface, topSurface)
                
        self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID = box.GetMaxIDs()
        self.warpedShapeList.append(box)    
        return shape    
    
    def GenerateCylinderWarped(self, variables):
        cylinder = CylinderWarped(sectionMan=self.sectionManager, materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
        cylinder.SetMaxIDs(self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID)
        cylinder.SetVariables(variables)
        point_list = cylinder.Generate()
        shape = self.PrismfromPoints(point_list)
        shape = self.Transformation(shape)

        if self.meshGenerationMode == True:
            meshType = self.meshType
            meshSize = self.meshSizeInPlane
            numElemZ = self.numberofElementinThickness
            meshPath = self.meshPath
            bottomSurface = self.GenerateImportWarpageSurface(0)
            topSurface = self.GenerateImportWarpageSurface(1)
            thickness = self.thickness
            name = self.name
            #cylinder.SetMaxIDs(self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID)
            trsf = self.GetTransformation()
            posZ = self.posZ
            cylinder.GenerateMesh(trsf,posZ, name, thickness, meshPath, meshType, meshSize, numElemZ, bottomSurface, topSurface)        
        
        self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID = cylinder.GetMaxIDs()
        self.warpedShapeList.append(cylinder)    
        return shape
    
    def GenerateShapes(self):
        self.shapesWarped = []
        for i in range(len(self.variablesList)):
            variables = self.variablesList[i]
            if variables[0] == "BOX":
                shape = self.GenerateBoxWarped(variables)                
                self.shapesWarped.append(shape)
            elif variables[0] == "CYLINDER":
                shape = self.GenerateCylinderWarped(variables)
                self.shapesWarped.append(shape)
        
        '''bottomSurface = self.GenerateImportWarpageSurface(0)
        
        geom_bottom_surface = bottomSurface#BRep_Tool.Surface(bottomSurface)
                
        self.xmin = 1.0e99
        self.ymin = 1.0e99
        self.xmax = -1.0e99
        self.ymax = -1.0e99
        for obj in self.warpedShapeList:
            self.xmin = min(self.xmin, obj.xmin)    
            self.ymin = min(self.ymin, obj.ymin)
            self.xmax = max(self.xmax, obj.xmax)
            self.ymax = max(self.ymax, obj.ymax)
        
        if self.xLength > 0 and self.yLength > 0:
            self.xmin = min(self.maxNID, self.posX - self.xLength/2)
            self.ymin = min(self.maxNID, self.posY - self.yLength/2)
            self.xmax = max(self.maxNID, self.posX + self.xLength/2)
            self.ymax = max(self.maxNID, self.posY + self.yLength/2)
        zMax = -1.0e99
        zMin = 1.0e99
        zAvg = 0.0
        num = 0.0
        for i in range(10):
            for j in range(10):
                curX = self.xmin + (self.xmax - self.xmin) * i/10
                curY = self.ymin + (self.ymax - self.ymin) * j/10
                pnt = gp_Pnt(curX,curY,0.0)
                point_projection = GeomAPI_ProjectPointOnSurf(pnt, geom_bottom_surface)
                projected_point = point_projection.NearestPoint()
                projected_point = gp_Pnt(projected_point.X(), projected_point.Y(), projected_point.Z())
                num = num + 1
                zAvg = zAvg + projected_point.Z()
                zMax = max(zMax, projected_point.Z())
                zMin = min(zMin, projected_point.Z())
        zAvg = zAvg/num
        zAvg = (zMax + zMin)/2
        
        
        for warpedShape in self.warpedShapeList:
            warpedShape.meshManager.nodeMan.MoveNodes(0.0,0.0,-zAvg)
        '''    
            
        
        if self.xLength >0 and self.yLength > 0:
            box = BoxWarped()
            variables = [] 
            variables.append("BOX")
            variables.append(self.posX)
            variables.append(self.posY)
            variables.append(self.xLength)
            variables.append(self.yLength)
            variables.append(self.packageMeshMatID)
            
            box.SetVariables(variables)
            point_list = box.Generate()
            shape = self.PrismfromPoints(point_list)
            shape = self.Transformation(shape)
            
            initShape = shape 
            cut = BRepAlgoAPI_Cut()
            L1 = TopTools_ListOfShape()
            L1.Append(initShape)
            L2 = TopTools_ListOfShape()
            i = 0 
            for i in range(len(self.shapesWarped)):
                L2.Append(self.shapesWarped[i])
                i = i + 1
            curShape = initShape
            if i > 0:     
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.00000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                    self.shapesWarped.append(initShape)
                else:
                    print("Cut Success")
                    self.shapesWarped.append(cut.Shape())
                    curShape = cut.Shape()
                        
            else:
                self.shapesWarped.append(initShape)
            
            if self.meshGenerationMode == True:
                meshType  = self.meshType
                meshSize = self.meshSizeInPlane
                meshPath = self.meshPath
                box.meshManager.SetPath(meshPath)
                box.meshManager.SetName("WarpedShape_{0}".format(self.name))
                if self.packageMeshMatID != -1:
                    box.meshManager.part.SetMaterialID(self.packageMeshMatID)

                box.meshManager.ExportStepFile("WarpedShape_{0}.step".format(self.name),curShape)
                box.meshManager.mesh_shape(curShape, meshSize*0.5, meshSize, 3, None, self.maxNID, self.maxEID, 0, "")
                self.maxNID, self.maxEID = box.meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                box.meshManager.part.SetID(self.maxPID)
                self.warpedShapeList.append(box)
                
                
            
        
        return self.shapesWarped
      
class WarpedShape():          
    def __init__(self, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        self.meshManager = KooMeshManagerGMSH(nodeMan=nodeMan, elementMan=elementMan, partMan=partMan,sectionMan=sectionMan, materialMan=materialMan, nodeSetMan=nodeSetMan, part=part)         
        self.maxNID = 0
        self.maxEID = 0 
        self.maxPID = 0 
        self.maxMID = 0 
        self.maxSID = 0     
        self.maxNSID = 0
        self.matID = -1
        
        self.xmin = 1.0e99
        self.ymin = 1.0e99
        self.xmax = -1.0e99
        self.ymax = -1.0e99
        
        pass 
    
    def SetMaxIDs(self, maxNID, maxEID, maxPID, maxMID, maxSID, maxNSID):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID
        self.maxMID = maxMID
        self.maxSID = maxSID
        self.maxNSID = maxNSID
        
    def GetMaxIDs(self):
        return self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID
    
    def GenerateStructuredMesh(self, trsf,posZ, name, thickness, meshPath, meshType, numElemX, numElemY, numElemZ, bottomSurface,topSurface):
        mid = self.matID
        trsfBottom = gp_Trsf()
        trsfTop = gp_Trsf()
        trsfBottom.Multiply(trsf)
        trsfTop.Multiply(trsf)
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(0,0,thickness))
        trsfTop.Multiply(trsf)
        
        if topSurface == None:
            geom_top_surface = None
        else:
            face_builder = BRepBuilderAPI_MakeFace(topSurface, 1e-6)
            face = face_builder.Face()    
            topSurface = BRepBuilderAPI_Transform(face, trsfTop).Shape()
            topSurface = BRepBuilderAPI_Transform(topSurface, trsf).Shape()
            geom_top_surface = BRep_Tool.Surface(topSurface)
        
        if bottomSurface == None:
            geom_bottom_surface = None
        else:              
            face_builder = BRepBuilderAPI_MakeFace(bottomSurface, 1e-6)
            face = face_builder.Face()
            bottomSurface = BRepBuilderAPI_Transform(face, trsfBottom).Shape()            
            geom_bottom_surface = BRep_Tool.Surface(bottomSurface)
        
        
        point_list = self.Generate()
        point_list_transformed = [] 
        for i in range(0,4):
            p = point_list[i]
            p = p.Transformed(trsfBottom)
            point_list_transformed.append(p)
        for i in range(0,4):
            p = point_list[i]
            p = p.Transformed(trsfTop)
            point_list_transformed.append(p)
            
        
        self.xmin = 1.0e99
        self.ymin = 1.0e99
        self.xmax = -1.0e99
        self.ymax = -1.0e99
        pt_list = [] 
        for i in range(len(point_list_transformed)):
            pnt = point_list_transformed[i]            
            if pnt.X() < self.xmin:
                self.xmin = pnt.X()
            if pnt.X() > self.xmax:
                self.xmax = pnt.X()
            if pnt.Y() < self.ymin:
                self.ymin = pnt.Y()
            if pnt.Y() > self.ymax:
                self.ymax = pnt.Y()
            pt_list.append(pnt) 
          
            
        
        self.meshManager.SetPath(meshPath)
                        
        self.meshManager.SetName("WarpedShape_{0}".format(name))
        if mid != -1:
            self.meshManager.part.SetMaterialID(mid)
                
        tol = thickness*0.1/numElemZ
        self.meshManager.GenerateStructuredMeshbyNumberofElement(pt_list, numElemX, numElemY, numElemZ, self.maxNID, self.maxEID)
        
            
        botNodes = self.meshManager.part.GetNodesZRange(posZ-tol/2,posZ+tol/2)            
        topNodes = self.meshManager.part.GetNodesZRange(posZ+thickness-tol/2,posZ+thickness+tol/2)
        
        for nid in botNodes:
            node = botNodes[nid]
            pnt : gp_Pnt = gp_Pnt(node.x,node.y,node.z)                                       
            if geom_bottom_surface is not None:
                point_projection = GeomAPI_ProjectPointOnSurf(pnt, geom_bottom_surface)            
                projected_point = point_projection.NearestPoint()                
            else:
                projected_point = pnt
            node.SetXYZ(projected_point.X(),projected_point.Y(),projected_point.Z())
        
        for nid in topNodes:
            node = topNodes[nid]
            pnt : gp_Pnt = gp_Pnt(node.x,node.y,node.z)                                       
            if geom_top_surface is not None:
                point_projection = GeomAPI_ProjectPointOnSurf(pnt, geom_top_surface)            
                projected_point = point_projection.NearestPoint()
            else:
                projected_point = pnt
            node.SetXYZ(projected_point.X(),projected_point.Y(),projected_point.Z())
           
        nodes = botNodes 
        nodes.update(topNodes) 
        
        self.meshManager.part.LaplacianSmoothingwithoutExceptedNodes(nodes,10)
        self.maxNID, self.maxEID = self.meshManager.GetMaxIDs()
        self.maxPID = self.maxPID + 1
        self.meshManager.part.SetID(self.maxPID)        
        
    def GenerateMesh(self,trsf,posZ, name, thickness, meshPath, meshType, meshSize, numElemZ, bottomSurface,topSurface):
        mid = self.matID
        trsfBottom = gp_Trsf()
        trsfTop = gp_Trsf()
        trsfBottom.Multiply(trsf)
        trsfTop.Multiply(trsf)
        trsfThickness = gp_Trsf()
        trsfThickness.SetTranslation(gp_Vec(0,0,thickness))
        
        if topSurface == None:
            geom_top_surface = None
        else:
            face_builder = BRepBuilderAPI_MakeFace(topSurface, 1e-6)
            face = face_builder.Face()
            
            topSurface = BRepBuilderAPI_Transform(face, trsfTop).Shape()
            topSurface = BRepBuilderAPI_Transform(topSurface, trsfThickness).Shape()
            geom_top_surface = BRep_Tool.Surface(topSurface)
        if bottomSurface == None:
            geom_bottom_surface = None       
        else:                 
            face_builder = BRepBuilderAPI_MakeFace(bottomSurface, 1e-6)
            face = face_builder.Face()
            bottomSurface = BRepBuilderAPI_Transform(face, trsfBottom).Shape()
            geom_bottom_surface = BRep_Tool.Surface(bottomSurface)
        
        
        point_list = self.Generate()
        point_list_transformed = []
        for p in point_list:
            #print("Original :",p.X(),p.Y(),p.Z())    
            p = p.Transformed(trsfBottom)
            #print("Transformed :",p.X(),p.Y(),p.Z())
            point_list_transformed.append(p)
        polygon = BRepBuilderAPI_MakePolygon()
        for p in point_list_transformed:
            polygon.Add(p)
        polygon.Close()
        polygon.Build()
        surface = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
        self.meshManager.SetPath(meshPath)
                           
        self.meshManager.SetName("WarpedShape_{0}".format(name))
        if mid != -1:
            self.meshManager.part.SetMaterialID(mid)
                
        tol = thickness*0.1/numElemZ
        if meshType.lower() == "hexa":
            self.meshManager.mesh_shape_extrude_3D(surface,meshSize,numElemZ,[0,0,1],11,self.maxNID,self.maxEID)
        else:
            prism = BRepPrimAPI_MakePrism(surface, gp_Vec(0,0,thickness)).Shape()
            
            self.meshManager.mesh_shape(prism,meshSize,meshSize,3,None,self.maxNID,self.maxEID)            
        
            
        botNodes = self.meshManager.part.GetNodesZRange(posZ-tol/2,posZ+tol/2)            
        topNodes = self.meshManager.part.GetNodesZRange(posZ+thickness-tol/2,posZ+thickness+tol/2)
        self.xmin = 1.0e99
        self.ymin = 1.0e99
        self.xmax = -1.0e99
        self.ymax = -1.0e99
        
        for nid in botNodes:
            node = botNodes[nid]
            pnt : gp_Pnt = gp_Pnt(node.x,node.y,node.z)                                       
            #print("Original :",pnt.X(),pnt.Y(),pnt.Z())            
            if geom_bottom_surface is not None:
                point_projection = GeomAPI_ProjectPointOnSurf(pnt, geom_bottom_surface)            
                projected_point = point_projection.NearestPoint()                
            else:
                projected_point = pnt
            
            node.SetXYZ(projected_point.X(),projected_point.Y(),projected_point.Z())
            #print("Projected :",projected_point.X(),projected_point.Y(),projected_point.Z())
            if projected_point.X() < self.xmin:
                self.xmin = projected_point.X()
            if projected_point.X() > self.xmax:
                self.xmax = projected_point.X()
            if projected_point.Y() < self.ymin:
                self.ymin = projected_point.Y()
            if projected_point.Y() > self.ymax:
                self.ymax = projected_point.Y()
                
        for nid in topNodes:
            node = topNodes[nid]
            pnt : gp_Pnt = gp_Pnt(node.x,node.y,node.z)                                       
            if geom_top_surface is not None:
                point_projection = GeomAPI_ProjectPointOnSurf(pnt, geom_top_surface)            
                projected_point = point_projection.NearestPoint()                
            else:
                projected_point = pnt
            node.SetXYZ(projected_point.X(),projected_point.Y(),projected_point.Z())
            if projected_point.X() < self.xmin:
                self.xmin = projected_point.X()
            if projected_point.X() > self.xmax:
                self.xmax = projected_point.X()
            if projected_point.Y() < self.ymin:
                self.ymin = projected_point.Y()
            if projected_point.Y() > self.ymax:
                self.ymax = projected_point.Y()                
           
        #externalNodes = self.meshManager.part.elementManager.GetExternalNodes()
        # combine dictionary
        nodes = botNodes 
        nodes.update(topNodes) 
        self.maxNID, self.maxEID = self.meshManager.GetMaxIDs()
        self.maxPID = self.maxPID + 1
        self.meshManager.part.SetID(self.maxPID)     
        #exnodesDict = {}
        #for node in externalNodes:
        #    exnodesDict[node.id] = node
        #nodes.update(exnodesDict)
        
        
        self.meshManager.part.LaplacianSmoothingwithoutExceptedNodes(nodes,10)
        
        
            
            
    
class BoxWarped(WarpedShape):
    def __init__(self,  nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        super(BoxWarped,self).__init__(nodeMan=nodeMan, elementMan=elementMan, partMan=partMan, sectionMan=sectionMan, materialMan=materialMan, nodeSetMan=nodeSetMan, part=part)
        self.variables = []      
        self.thickness = 0.0
        pass    
    
    def SetVariables(self, variables):
        self.variables = variables
        self.matID = self.variables[5]
    
    def Generate(self, tol = 0.3):
        locx = self.variables[1]
        locy = self.variables[2]
        xLength = self.variables[3]
        yLength = self.variables[4]
        '''matID = self.variables[4]
        compMatIDList = self.variables[5]
        compThicknessList = self.variables[6]
        compBList = self.variables[7]
        numElemforEachLayer = self.variables[8]
        compositeEOSList = self.variables[9]
        compositeMeshrefinementSizeLlist = self.variables[10]
        compositeMeshrefinementLocationXList = self.variables[11]
        compositeMeshrefinementLocationYList = self.variables[12]
        compositeModeList = self.variables[13]
        '''
        
        x = locx# + self.posX
        y = locy# + self.posY
        z = 0
        point_list = [] 
        size = 5
        for i in range(size):
            curX = x + xLength/2.0 * i / size
            curY = y
            point = gp_Pnt(curX, curY, z)
            point_list.append(point)
        
        for i in range(size):
            curX = x + xLength/2.0
            curY = y + i * yLength/2.0 / size
            point = gp_Pnt(curX, curY, z)
            point_list.append(point)
            
        for i in range(size):
            curX = x + xLength/2.0 * (size - i) / size
            curY = y + yLength/2.0
            point = gp_Pnt(curX, curY, z)
            point_list.append(point)
            
        for i in range(size):
            curX = x - xLength/2.0
            curY = y + yLength/2.0 * (size - i) / size
            point = gp_Pnt(curX, curY, z)
            point_list.append(point) 
            
        #point_list.append(gp_Pnt(x, y, z))
        
        #point_list.append(gp_Pnt(x + xLength, y, z))
        #point_list.append(gp_Pnt(x + xLength, y + yLength, z))
        #point_list.append(gp_Pnt(x, y + yLength, z))
        point_list.append(gp_Pnt(x, y, z))
        
        '''point_list.append(gp_Pnt(x - xLength/2, y - yLength/2, z))
        point_list.append(gp_Pnt(x + xLength/2, y - yLength/2, z))
        point_list.append(gp_Pnt(x + xLength/2, y + yLength/2, z))
        point_list.append(gp_Pnt(x - xLength/2, y + yLength/2, z))
        point_list.append(gp_Pnt(x - xLength/2, y - yLength/2, z))   '''            
        return point_list
    
    
        
        
        

class CylinderWarped(WarpedShape):
    def __init__(self, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        super(CylinderWarped,self).__init__(nodeMan=nodeMan, elementMan=elementMan, partMan=partMan, sectionMan=sectionMan, materialMan=materialMan, nodeSetMan=nodeSetMan, part=part)
        self.variables = []
        self.thickness = 0.0
        pass
    
    def SetVariables(self, variables):
        self.variables = variables
        self.matID = self.variables[4]
    
    def Generate(self):
        locX = self.variables[1]
        locY = self.variables[2]
        radius = self.variables[3]
        '''matID = self.variables[3]
        compMatIDList = self.variables[4]
        compThicknessList = self.variables[5]
        compBList = self.variables[6]'''
        
        x = locX
        y = locY

        point_list = []
        for i in range(10):
            curX = x + radius * math.cos(i * math.pi / 5.0)
            curY = y + radius * math.sin(i * math.pi / 5.0) 
            point = gp_Pnt(curX, curY, 0.0)
            point_list.append(point)
        point_list.append(point_list[0])
        return point_list
    
class SolderJointsLayer(PackageWarpedLayer):
    def __init__(self, name = "", x = 0.0, y = 0.0, z=0.0, xLength = -1.0, yLength = -1.0, thickness = 1.0, secMan : KooSectionManager = None, matMan : KooMaterialManager = None, nSetMan : NodeSetManager = None): 
        super(SolderJointsLayer,self).__init__(name, x, y, z, xLength, yLength, thickness, secMan, matMan, nSetMan)
        self.solderVariableList = []
        self.solderJointList = []
        self.bottomRotate = 0.0
        self.topRotate = 0.0
        '''
        self.S_TENSION = 4.800
        self.SOLDER_DENSITY = 0.0009
        self.GRAVITY = 9810
        '''
        self.S_TENSION = 4.8*1000.0
        self.SOLDER_DENSITY = 0.0090*1000.0
        self.GRAVITY = 0.009810
        self.FORCE = 1.0
        self.VOLUME = 0.0
        self.detailMode = False
        self.topX = x 
        self.topY = y
        self.dh = 0.0      
        
        self.warpedShapeList = []
        
    
    def SolidfromPointstoPoints(self, point_list_bottom, point_list_top, thickness = 0.0):
        noWarpageMode = False
        if self.bsplineSurface is None:
            self.bsplineSurface = self.GenerateImportWarpageSurface()
            if self.bsplineSurface is None:
                print("Generate BSpline Surface is None")
                polygon = BRepBuilderAPI_MakePolygon()
                for p in point_list_bottom:
                    polygon.Add(p)
                polygon.Close()
                polygon.Build()
                surfaceBottom = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
                noWarpageMode = True
        if self.bsplineSurface is not None:
            num_additional_points = 200  # Number of additional points to generate
            additional_points = self.generate_random_points_inside_polygon(point_list_bottom, num_additional_points)
            
            
            if len(self.additionalPointLists) > 0:
                #additional_points = []
                for i in range(len(self.additionalPointLists)):
                    pt = self.additionalPointLists[i]
                    additional_points.append(gp_Pnt(pt.X(),pt.Y(),0.0))
                for i in range(0,len(point_list_bottom)-1):
                    pi = point_list_bottom[i]
                    pi1 = point_list_bottom[i+1]
                    n = 5
                    for j in range(1,n):
                        p = gp_Pnt(pi.X() + (pi1.X() - pi.X()) * j/n, pi.Y() + (pi1.Y() - pi.Y()) * j/n, pi.Z() + (pi1.Z() - pi.Z()) * j/n)
                        additional_points.append(p)
            
            
            surfaceBottom = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list_bottom,self.bsplineSurface,additional_points)
            noWarpageMode = False
        else:
            pass
        
        if thickness == 0.0:
            thickness = self.thickness + self.dh
            
        if self.bsplineSurfaceTop is None:
            self.bsplineSurfaceTop = self.GenerateImportWarpageSurface(1)
            if self.bsplineSurfaceTop is None:
                print("Generate BSpline Surface is None")
                polygon = BRepBuilderAPI_MakePolygon()
                for p in point_list_top:                    
                    polygon.Add(p)
                polygon.Close()
                polygon.Build()
                surfaceTop = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
                noWarpageMode = True
        if self.bsplineSurfaceTop is not None:
            num_additional_points = 200        
            additional_points = self.generate_random_points_inside_polygon(point_list_top, num_additional_points)            
            surfaceTop = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list_top,self.bsplineSurfaceTop,additional_points)
            noWarpageMode = False
        else:
            pass
        
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(0,0,thickness))
        surfaceTop = BRepBuilderAPI_Transform(surfaceTop, trsf).Shape()
                      
        if surfaceTop is None or surfaceBottom is None:
            return None
        
        if noWarpageMode == True:
            offset_shape_builder = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builder.PerformByJoin(surfaceTop, -thickness*0.01,1.e-6)
            offset_surface1 = offset_shape_builder.Shape()
            #offset_shape_builder = BRepOffsetAPI_MakeOffsetShape()
            #trsf = gp_Trsf()
            #trsf.SetTranslation(gp_Vec(0,0,-0.01))
            #offset_surface1 = BRepBuilderAPI_Transform(offset_surface1, trsf).Shape()        
            offset_shape_builder2 = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builder2.PerformByJoin(surfaceBottom, thickness*0.01,1.e-6)
            offset_surface2 = offset_shape_builder2.Shape()
        else:
            offset_shape_builder = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builder.PerformByJoin(surfaceTop, thickness*0.05,1.e-6)
            offset_surface1 = offset_shape_builder.Shape()
            #offset_shape_builder = BRepOffsetAPI_MakeOffsetShape()
            #trsf = gp_Trsf()
            #trsf.SetTranslation(gp_Vec(0,0,-0.01))
            #offset_surface1 = BRepBuilderAPI_Transform(offset_surface1, trsf).Shape()        
            offset_shape_builder2 = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builder2.PerformByJoin(surfaceBottom, -thickness*0.05,1.e-6)
            offset_surface2 = offset_shape_builder2.Shape()
            #offset_shape_builder2 = BRepOffsetAPI_MakeOffsetShape()
            #offset_surface2 = BRepBuilderAPI_Transform(offset_surface2, trsf).Shape()        
        
        
        surfaceTop = offset_surface1
        surfaceBottom = offset_surface2        
        
        
        
        explorerTop = TopExp_Explorer(surfaceTop, TopAbs_WIRE)
        explorerBottom = TopExp_Explorer(surfaceBottom, TopAbs_WIRE)
        wiresTop = []
        wiresBottom = []
        while explorerTop.More():
            wire = topods_Wire(explorerTop.Current())
            wiresTop.append(wire)
            explorerTop.Next()
        while explorerBottom.More():
            wire = topods_Wire(explorerBottom.Current())
            wiresBottom.append(wire)
            explorerBottom.Next()
            
        loft = BRepOffsetAPI_ThruSections(True)
        for wire in wiresTop:
            loft.AddWire(wire)
        for wire in wiresBottom:
            loft.AddWire(wire)
        
        loft.Build()
        shape = loft.Shape()
        return shape
        
        '''
        shell_builder = brepfill_Shell(wiresTop[0],wiresBottom[0])
        solid_builder = BRepBuilderAPI_MakeSolid()
        solid_builder.Add(surfaceTop)
        solid_builder.Add(surfaceBottom)
        solid_builder.Add(shell_builder)
        solid_builder.Build()        
        return solid_builder.Shape()
        '''
               
            
        
        
            
            
    
        
    def GetTransformationPad(self, isTop = True, thickness = 0.0):
        
        if isTop == True:
            trsf = gp_Trsf()
            trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), math.pi*self.topRotate/180.0)
            trsf2 = gp_Trsf()            
            trsf2.SetTranslation(gp_Vec(self.topX, self.topY, self.posZ + thickness))
            trsf.Multiply(trsf2)
        else:
            trsf = gp_Trsf()
            trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), math.pi*self.bottomRotate/180.0)
            trsf2 = gp_Trsf()
            trsf2.SetTranslation(gp_Vec(self.posX, self.posY, self.posZ + thickness))
            trsf.Multiply(trsf2)                        
        
        return trsf            
        
    def SetRotationPad(self, bottomRotate, topRotate):
        self.bottomRotate = bottomRotate
        self.topRotate = topRotate
        
    def SetPositionPad(self, x, y, z, x2 = 0.0, y2 = 0.0):
        self.posX = x
        self.posY = y
        self.posZ = z
        self.topX = x2 + x
        self.topY = y2 + x
    
    def SetSurfaceTension(self, tension):
        self.S_TENSION = tension
    
    def SetSolderDensity(self, density):
        self.SOLDER_DENSITY = density
    
    def SetGravity(self, gravity):
        self.GRAVITY = gravity
    
        
    def SetForce(self, force):
        self.FORCE = force      
    
    def SetDetailSolder(self, detailMode):
        self.detailMode = detailMode
        
    def CreateSMDVariables(self, bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name = "",topMaskThickness=0.0,bottomMaskThickness=0.0, detailMode = True, materialID = -1):
        variables = []
        variables.append("SMD")
        variables.append(bottomPadLocX)
        variables.append(bottomPadLocY)
        variables.append(bottomPadRadius)
        variables.append(topPadLocX)
        variables.append(topPadLocY)
        variables.append(topPadRadius)
        variables.append(solderRadius)
        #variables.append(solderHeight)
        variables.append(name)
        variables.append(topMaskThickness)
        variables.append(bottomMaskThickness)
        variables.append(detailMode)
        variables.append(materialID)
        self.solderVariableList.append(variables)
        return variables

    def CreateNSMDVariables(self, bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name = "",topMaskThickness=0.0,bottomPadThickness=0.0,detailMode = True, materialID = -1):
        variables = [] 
        variables.append("NSMD")
        variables.append(bottomPadLocX)
        variables.append(bottomPadLocY)
        variables.append(bottomPadRadius)
        variables.append(topPadLocX)
        variables.append(topPadLocY)
        variables.append(topPadRadius)
        variables.append(solderRadius)
        #variables.append(solderHeight)
        variables.append(name)
        variables.append(topMaskThickness)
        variables.append(bottomPadThickness)
        variables.append(detailMode)
        variables.append(materialID)
        self.solderVariableList.append(variables)
        return variables
                
    def AddSolderVariables(self, variables):
        self.solderVariableList.append(variables)
    
    def SetSolderJointObjects(self):
        topPadPt1s = []
        topPadPt2s = []
        topPadPtCs = []
        
        botPadPt1s = []
        botPadPt2s = []
        botPadPtCs = []
        solderVolumes = [] 
        names = []
        topMaskThickness = {}
        bottomMaskThickness = {}
        bottomPadThickness = {}       
        i = 0 
        self.minDistance = self.thickness
        materialIDList = []
        detailModeList = [] 
        for solderVariables in self.solderVariableList:
            solderType = solderVariables[0]
            if solderType == "SMD":
                bottomPadLocX = solderVariables[1]
                bottomPadLocY = solderVariables[2]
                bottomPadRadius = solderVariables[3]
                topPadLocX = solderVariables[4]
                topPadLocY = solderVariables[5]
                topPadRadius = solderVariables[6]
                solderRadius = solderVariables[7]
                #solderHeight = solderVariables[8]
                tpt1 = gp_Pnt(topPadLocX + topPadRadius, topPadLocY, 0)
                tpt2 = gp_Pnt(topPadLocX, topPadLocY + topPadRadius, 0)
                tptc = gp_Pnt(topPadLocX, topPadLocY, 0)
                bpt1 = gp_Pnt(bottomPadLocX + bottomPadRadius, bottomPadLocY, 0)
                bpt2 = gp_Pnt(bottomPadLocX, bottomPadLocY + bottomPadRadius, 0)
                bptc = gp_Pnt(bottomPadLocX, bottomPadLocY, 0)
                topPadPt1s.append(tpt1)
                topPadPt2s.append(tpt2)
                topPadPtCs.append(tptc)
                botPadPt1s.append(bpt1)
                botPadPt2s.append(bpt2)
                botPadPtCs.append(bptc)
                #topPadLocZs.append(self.posZ + solderHeight)
                #bottomPadLocZs.append(self.posZ)
                solderVolume = math.pi * solderRadius * solderRadius * self.thickness
                solderVolumes.append(solderVolume)                
                name = solderVariables[8]
                if len(name) == 0:
                    name = "SMD" + str(i)
                names.append(name)
                topMaskThickness[i] = solderVariables[9]
                bottomMaskThickness[i] = solderVariables[10]
                if len(solderVariables) > 11:
                    if solderVariables[11].lower() == "true":
                        detailModeList.append(True)
                    elif solderVariables[11].lower() == "none":
                        detailModeList.append(self.detailMode)
                    else:
                        detailModeList.append(False)
                else:
                    detailModeList.append(self.detailMode)
                
                materialIDList.append(solderVariables[12])                
                i = i + 1 
            elif solderType == "NSMD":
                bottomPadLocX = solderVariables[1]
                bottomPadLocY = solderVariables[2]
                bottomPadRadius = solderVariables[3]
                topPadLocX = solderVariables[4]
                topPadLocY = solderVariables[5]
                topPadRadius = solderVariables[6]
                solderRadius = solderVariables[7]
                #solderHeight = solderVariables[8]
                tpt1 = gp_Pnt(topPadLocX + topPadRadius, topPadLocY, 0)
                tpt2 = gp_Pnt(topPadLocX, topPadLocY + topPadRadius, 0)
                tptc = gp_Pnt(topPadLocX, topPadLocY, 0)
                bpt1 = gp_Pnt(bottomPadLocX + bottomPadRadius, bottomPadLocY, 0)
                bpt2 = gp_Pnt(bottomPadLocX, bottomPadLocY + bottomPadRadius, 0)
                bptc = gp_Pnt(bottomPadLocX, bottomPadLocY, 0)
                topPadPt1s.append(tpt1)
                topPadPt2s.append(tpt2)
                topPadPtCs.append(tptc)
                botPadPt1s.append(bpt1)
                botPadPt2s.append(bpt2)
                botPadPtCs.append(bptc)
                #topPadLocZs.append(self.posZ + solderHeight)
                #bottomPadLocZs.append(self.posZ)
                solderVolume = math.pi * solderRadius * solderRadius * self.thickness
                solderVolumes.append(solderVolume)
                
                name = solderVariables[8]
                if len(name) == 0:
                    name = "NSMD" + str(i)
                names.append(name)
                topMaskThickness[i] = solderVariables[9]
                bottomPadThickness[i] = solderVariables[10]
                if len(solderVariables) > 11:
                    if solderVariables[11].lower() == "true":
                        detailModeList.append(True)
                    elif solderVariables[11].lower() == "none":
                        detailModeList.append(self.detailMode)
                    else:
                        detailModeList.append(False)
                else:
                    detailModeList.append(self.detailMode)
                materialIDList.append(solderVariables[12])
                i = i + 1 
        
        self.minith = 0
        if self.bsplineSurface is None:
            topPadPt1sWarpage = topPadPt1s
            topPadPt2sWarpage = topPadPt2s
            topPadPtCsWarpage = topPadPtCs
            botPadPt1sWarpage = botPadPt1s
            botPadPt2sWarpage = botPadPt2s
            botPadPtCsWarpage = botPadPtCs
            self.minZtop = 0.0
            
        else:
            if self.bsplineSurfaceTop is None:
                topPadPt1sWarpage = self.ProjectPointOnWarpageSurface(topPadPt1s, self.bsplineSurface)
                topPadPt2sWarpage = self.ProjectPointOnWarpageSurface(topPadPt2s, self.bsplineSurface)
                topPadPtCsWarpage = self.ProjectPointOnWarpageSurface(topPadPtCs, self.bsplineSurface)
            else:
                topPadPt1sWarpage = self.ProjectPointOnWarpageSurface(topPadPt1s, self.bsplineSurfaceTop)
                topPadPt2sWarpage = self.ProjectPointOnWarpageSurface(topPadPt2s, self.bsplineSurfaceTop)
                topPadPtCsWarpage = self.ProjectPointOnWarpageSurface(topPadPtCs, self.bsplineSurfaceTop)
            botPadPt1sWarpage = self.ProjectPointOnWarpageSurface(botPadPt1s, self.bsplineSurface)
            botPadPt2sWarpage = self.ProjectPointOnWarpageSurface(botPadPt2s, self.bsplineSurface)
            botPadPtCsWarpage = self.ProjectPointOnWarpageSurface(botPadPtCs, self.bsplineSurface)
            minDistance = 1.0e99
            mintozero = 0.0
            zerotomax = 0.0
            minZTop = 1.0e99
            maxZBot = -1.0e99
            minZBot = 1.0e99
            
            for i in range(len(topPadPtCsWarpage)): 
                minZTop = min(minZTop, topPadPtCsWarpage[i].Z())
                maxZBot = max(maxZBot, botPadPtCsWarpage[i].Z())            
                minZBot = min(minZBot, botPadPtCsWarpage[i].Z())
            
            for i in range(len(topPadPtCsWarpage)): 
                topPadPt1sWarpage[i].SetZ(topPadPt1sWarpage[i].Z() - minZTop)
                topPadPt2sWarpage[i].SetZ(topPadPt2sWarpage[i].Z() - minZTop)
                topPadPtCsWarpage[i].SetZ(topPadPtCsWarpage[i].Z() - minZTop)
                botPadPt1sWarpage[i].SetZ(botPadPt1sWarpage[i].Z() )
                botPadPt2sWarpage[i].SetZ(botPadPt2sWarpage[i].Z() )
                botPadPtCsWarpage[i].SetZ(botPadPtCsWarpage[i].Z() )
            
            for i in range(len(topPadPtCsWarpage)):
                distance = self.thickness + topPadPt1sWarpage[i].Z() - botPadPt1sWarpage[i].Z()
                if distance < minDistance:
                    minDistance = distance
                    
            if minDistance < 0.0:
                for i in range(len(topPadPtCsWarpage)): 
                    topPadPt1sWarpage[i].SetZ(topPadPt1sWarpage[i].Z() - minDistance)
                    topPadPt2sWarpage[i].SetZ(topPadPt2sWarpage[i].Z() - minDistance)
                    topPadPtCsWarpage[i].SetZ(topPadPtCsWarpage[i].Z() - minDistance)
                    botPadPt1sWarpage[i].SetZ(botPadPt1sWarpage[i].Z() - minDistance)
                    botPadPt2sWarpage[i].SetZ(botPadPt2sWarpage[i].Z() - minDistance)
                    botPadPtCsWarpage[i].SetZ(botPadPtCsWarpage[i].Z() - minDistance)
                
                        
            minDistance = 1.0e99
            for i in range(len(topPadPt1sWarpage)):
                distance = self.thickness + topPadPt1sWarpage[i].Z() - botPadPt1sWarpage[i].Z()
                if distance < minDistance:
                    self.minith = i
                    minDistance = min(minDistance, distance)
                    mintozero = -botPadPt1sWarpage[i].Z()
                    zerotomax = self.thickness + topPadPt1sWarpage[i].Z()
                    
                print("Distance",distance)
            
            self.minZtop = minZTop
            self.mintozero = mintozero
            self.zerotomax = zerotomax
            self.minDistance = minDistance
            self.topPtList = []             
                
            
        topTrsf = self.GetTransformationPad(True, self.thickness)        
        bottomTrsf = self.GetTransformationPad(False)
        for i in range(len(topPadPt1sWarpage)):
            #print("TopPadPt1sWarpage",topPadPt1sWarpage[i].X(),topPadPt1sWarpage[i].Y(),topPadPt1sWarpage[i].Z())
            topPadPt1sWarpage[i].Transform(topTrsf)
            #print("TopPadPt1sWarpage",topPadPt1sWarpage[i].X(),topPadPt1sWarpage[i].Y(),topPadPt1sWarpage[i].Z())
            topPadPt2sWarpage[i].Transform(topTrsf)
            topPadPtCsWarpage[i].Transform(topTrsf)
            botPadPt1sWarpage[i].Transform(bottomTrsf)
            botPadPt2sWarpage[i].Transform(bottomTrsf)
            botPadPtCsWarpage[i].Transform(bottomTrsf)            
      
        '''
        for i in range(len(topPadPt1sWarpage)):
            topPadPt1sWarpage[i].SetZ(topPadPt1sWarpage[i].Z() + topPadLocZs[i])
            topPadPt2sWarpage[i].SetZ(topPadPt2sWarpage[i].Z() + topPadLocZs[i])
            topPadPtCsWarpage[i].SetZ(topPadPtCsWarpage[i].Z() + topPadLocZs[i])
            botPadPt1sWarpage[i].SetZ(botPadPt1sWarpage[i].Z() + bottomPadLocZs[i])
            botPadPt2sWarpage[i].SetZ(botPadPt2sWarpage[i].Z() + bottomPadLocZs[i])
            botPadPtCsWarpage[i].SetZ(botPadPtCsWarpage[i].Z() + bottomPadLocZs[i])
        '''
        for i in range(len(topPadPt1sWarpage)):
            solderType = self.solderVariableList[i][0]
            materialID = materialIDList[i]
            if solderType == "SMD":
                solderVolume = solderVolumes[i]
                name = names[i]
                solderJoint = SolderMaskedDefined(name, sectionMan=self.sectionManager, materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                solderJoint.SetMaterialID(materialID)
                if detailModeList[i] == True:
                    solderJoint.SetDetailMode(True)
                botPadPt1 = botPadPt1sWarpage[i]
                botPadPt2 = botPadPt2sWarpage[i]
                botPadPtC = botPadPtCsWarpage[i]
                topPadPt1 = topPadPt1sWarpage[i]
                topPadPt2 = topPadPt2sWarpage[i]
                topPadPtC = topPadPtCsWarpage[i]
                
                topMaskT = topMaskThickness[i]
                bottomMaskT = bottomMaskThickness[i]
                
                solderJoint.SetBottomfromTwoPointsandCenter(botPadPt1, botPadPt2, botPadPtC)
                solderJoint.SetTopfromTwoPointsandCenter(topPadPt1, topPadPt2, topPadPtC)
                solderJoint.SetMaskThicknessTopBottom(bottomMaskT, topMaskT)
                solderJoint.SetSurfaceTension(self.S_TENSION)
                solderJoint.SetSolderDensity(self.SOLDER_DENSITY)                
                solderJoint.SetGravity(self.GRAVITY)
                solderJoint.SetVolume(solderVolume)
                self.solderJointList.append(solderJoint)
            elif solderType == "NSMD":
                solderVolume = solderVolumes[i]
                name = names[i]
                solderJoint = NonSolderMaskedDefined(name, sectionMan=self.sectionManager, materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
                solderJoint.SetMaterialID(materialID)
                if detailModeList[i] == True:
                    solderJoint.SetDetailMode(True)
                botPadPt1 = botPadPt1sWarpage[i]
                botPadPt2 = botPadPt2sWarpage[i]
                botPadPtC = botPadPtCsWarpage[i]
                topPadPt1 = topPadPt1sWarpage[i]
                topPadPt2 = topPadPt2sWarpage[i]
                topPadPtC = topPadPtCsWarpage[i]
                
                topMaskT = topMaskThickness[i]
                bottomPadT = bottomPadThickness[i]
                solderJoint.SetBottomfromTwoPointsandCenter(botPadPt1, botPadPt2, botPadPtC)
                solderJoint.SetTopfromTwoPointsandCenter(topPadPt1, topPadPt2, topPadPtC)
                solderJoint.SetPadThicknessBottom(bottomPadT)
                solderJoint.SetMaskThicknessTop(topMaskT)
                solderJoint.SetSurfaceTension(self.S_TENSION)
                solderJoint.SetSolderDensity(self.SOLDER_DENSITY)
                solderJoint.SetGravity(self.GRAVITY)
                solderJoint.SetVolume(solderVolume)
                self.solderJointList.append(solderJoint)
                
    def GenerateSolder(self, ith, q):
        if ith >= len(self.solderJointList):
            return
        solderJoint = self.solderJointList[ith]
        if solderJoint.solderType == "SMD":
            solderJoint : SolderMaskedDefined = solderJoint
            solderJoint.UpdateScript()
            solder = solderJoint.MakeSolder()
        elif solderJoint.solderType == "NSMD":
            solderJoint : NonSolderMaskedDefined = solderJoint
            solderJoint.UpdateScript()
            solder = solderJoint.MakeSolder()
        q.put(solder)   
    
    def GetTopPointLists(self):
        topPointLists = []
        for solderJoint in self.solderJointList:
            if solderJoint.solderType == "SMD":
                solderJoint : SolderMaskedDefined = solderJoint
            elif solderJoint.solderType == "NSMD":
                solderJoint : NonSolderMaskedDefined = solderJoint
            topPointLists.extend(solderJoint.topPointLists)
        return topPointLists

    def GetBottomPointLists(self):
        bottomPointLists = []
        for solderJoint in self.solderJointList:
            if solderJoint.solderType == "SMD":
                solderJoint : SolderMaskedDefined = solderJoint
            elif solderJoint.solderType == "NSMD":
                solderJoint : NonSolderMaskedDefined = solderJoint
            bottomPointLists.extend(solderJoint.bottomPointLists)
        return bottomPointLists
    
            
    def GenerateSolderJoints(self):
        shapeList = [] 
        # thread start for each solder joint
        mode = "Thread"
        mode = "Single"

        if mode == "Thread":
            processes = [] 
            results = [] 
            result_queue = multiprocessing.Queue()
            for i in range(0,len(self.solderJointList),8):
                for j in range(i, i+8):
                    if j >= len(self.solderJointList):
                        break
                    p = multiprocessing.Process(target=self.GenerateSolder, args=(j, result_queue))
                    processes.append(p)
                    p.start()
                for p in processes:
                    p.join()
                while not result_queue.empty():
                    results.append(result_queue.get())
            for result in results:
                shapeList.append(result)
        else:
            firstSolderJoint = self.solderJointList[self.minith]
            
            if firstSolderJoint.solderType == "SMD":
                firstSolderJoint : SolderMaskedDefined = firstSolderJoint
            elif firstSolderJoint.solderType == "NSMD":
                firstSolderJoint : NonSolderMaskedDefined = firstSolderJoint
            firstSolderJoint.SetScriptforHeight(self.FORCE, self.minDistance)                
            if self.minDistance > 0:
                dh = firstSolderJoint.GetHeightDifference()
            else:
                dh = firstSolderJoint.GetHeightDifference()
            #dh += + self.thickness - self.minDistance
        
                            
            for solderJoint in self.solderJointList:
                if solderJoint.solderType == "SMD":
                    solderJoint : SolderMaskedDefined = solderJoint
                elif solderJoint.solderType == "NSMD":
                    solderJoint : NonSolderMaskedDefined = solderJoint
                curH = dh 
                if solderJoint.isNonWet(curH):
                    solderJoint.UpdateBottomBallScript()
                    if len(solderJoint.script) > 0:
                        solder = solderJoint.MakeSolder()
                        if solder is not None:
                            shapeList.append(solder)
                    solderJoint.UpdateTopBallScript(curH)
                    if len(solderJoint.script) > 0:
                        solder = solderJoint.MakeSolder()
                        if solder is not None:
                            shapeList.append(solder)
                else:
                    solderJoint.UpdateScript(curH)                
                    if len(solderJoint.script) > 0:
                        solder = solderJoint.MakeSolder()
                        if solder is not None:
                            shapeList.append(solder)
                if self.meshGenerationMode == True:
                    meshSize = self.meshSizeInPlane
                    meshPath = self.meshPath                     
                    solderJoint.SetMaxIDs(self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID)
                    solderJoint.GenerateMesh(meshSize, meshPath)          
                    self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID = solderJoint.GetMaxIDs()
                self.warpedShapeList.append(solderJoint)
        
                      
        for i in range(len(shapeList)):
            self.shapesWarped.append(shapeList[i])           
        self.dh = dh
        
        
        if self.xLength >0 and self.yLength > 0:
            box = BoxWarped(sectionMan=self.sectionManager, materialMan=self.materialManager, nodeSetMan=self.nodesetManager)
            variables = [] 
            variables.append("BOX")
            variables.append(self.posX)
            variables.append(self.posY)
            variables.append(self.xLength)
            variables.append(self.yLength)
            variables.append(self.packageMeshMatID)
            box.SetVariables(variables)
            point_list = box.Generate()
                                    
            point_list_top = []
            trsf = self.GetTransformationPad(True)
            for p in point_list:                
                point_list_top.append(p.Transformed(trsf))
                
            trsf = self.GetTransformationPad(False)
            for p in point_list:
                p.Transform(trsf)
                
            
            #shape = self.PrismfromPoints(point_list,self.thickness + self.dh)       
            shape = self.SolidfromPointstoPoints(point_list,point_list_top)
            #shape = self.Transformation(shape)
            
            initShape = shape                         
            
            cut = BRepAlgoAPI_Cut()
            L1 = TopTools_ListOfShape()
            L1.Append(initShape)
            L2 = TopTools_ListOfShape()
            i = 0 
            for i in range(len(shapeList)):
               
                L2.Append(shapeList[i])
                i = i + 1
               
            curShape = initShape
           
            if i > 0:     
                cut.SetArguments(L1)
                cut.SetTools(L2)
                cut.SetRunParallel(True)
                cut.SetFuzzyValue(0.00000000001)
                cut.Build()
                if cut.Shape() == None:
                    print("Cut Failed")
                    self.shapesWarped.append(initShape)
                else:
                    print("Cut Success")
                    self.shapesWarped.append(cut.Shape())
                    curShape = cut.Shape()
            else:
                self.shapesWarped.append(initShape)
                        
            if self.meshGenerationMode == True:
                meshType  = self.meshType
                meshSize = self.meshSizeInPlane
                meshPath = self.meshPath
                box.meshManager.SetPath(meshPath)
                box.meshManager.SetName("WarpedShape_{0}".format(self.name))
                if self.packageMeshMatID != -1:
                    box.meshManager.part.SetMaterialID(self.packageMeshMatID)
                
                box.meshManager.mesh_shape(curShape, meshSize, meshSize, 3, None, self.maxNID, self.maxEID, 0, "")
                self.maxNID, self.maxEID = box.meshManager.GetMaxIDs()
                self.maxPID = self.maxPID + 1
                box.meshManager.part.SetID(self.maxPID)
                self.warpedShapeList.append(box)
                 
            
                       
                    
                    
        
        return self.shapesWarped
                
            
                
            
'''     
class PackagePolynomialWarped(PackageWarpedLayer):
    def __init__(self):
        super(PackagePolynomialWarped,self).__init__()
        pass
    
    def Generate(self):
        print("Generate PackagePolynomialWarped")
        k = self.GenerateImportWarpageSurface()
        
        
        pass
    
'''  

    
    
        
        
    
