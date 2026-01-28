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

from KooODBCADManager.Polygon import Polygon2D as Poly

# Open Cascade for Generating Solid
from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Circ, gp_Pnt, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing

from KooODBCADManager.WarpageSurface import WarpageSurface

class ArrayPCB():
    def __init__(self,id):
        self.id = id         
        self.unitpolygons = {}
        self.arraypolygons = {}
        self.holepolygons = {} 
        self.bridgepolygons = {}
        self.type = 'arraypcb'
        
        self.layup = [] 
        self.thickness = [] 
        self.materialFile = ""
        self.patternFeatures = {}        
        self.symbolfolder = []
        self.location = [0,0,0]
        self.rotation = 0 
        self.mirror = False
        self.warpageFile = None
        self.shape = []
        self.warpage = None
        
    def SetColor(self, r, g, b, a):
        self.color = [r, g, b, a]

    def SetLayup(self,layup):
        self.layup = layup

    def AddLayer(self,layer):
        self.layup.append(layer)
    
    def SetThickness(self,thickness):
        self.thickness = thickness
    def AddThickness(self,thickness):
        self.thickness.append(thickness)
    
    def AddLayerWithThickness(self,layer,thickness):
        self.layup.append(layer)
        self.thickness.append(thickness)
    
    def SetMaterialFile(self,materialFile):
        self.materialFile = materialFile
    
    def SetPatternFeatures(self,patternFeatures):
        self.patternFeatures = patternFeatures
    
    def SetSymbolsFolder(self,symbolfolder):
        self.symbolfolder = symbolfolder
    
    def SetLocation(self,location):
        self.location = location
    
    def SetRotation(self,rotation):
        self.rotation = rotation

    def GetWarpage(self):
        if self.warpageFile != None:
            self.warpage = WarpageSurface()
            self.warpage.SetWarpageUnit('MM')
            self.warpage.SetWarpageFile(self.warpageFile)
            self.warpage.ImportWarpage()
            self.warpage.RemoveEmptySpace()
            self.warpage.SmoothWarpage()
            bdBox = self.MappedBoundaryBox()
            xLength = bdBox[1] - bdBox[0]   
            yLength = bdBox[3] - bdBox[2]
            print("bdBox",bdBox)
            print(self.location[0],self.location[1],self.location[2])
            print(xLength,yLength)
            surface = self.warpage.MakeBSplineSurface(self.location[0]+bdBox[0],self.location[1]+bdBox[2],self.location[2],xLength,yLength)
            return surface
            #face = self.warpage.MakeBSplineSurfacefromBSplineCurves(self.location[0]+bdBox[0],self.location[1]+bdBox[2],self.location[2],xLength,yLength)
            #return face
        else:
            return None
    
    def SetMirror(self,mirror):
        self.mirror = mirror
    
    def SetWarpageFile(self,warpageFile):
        if warpageFile == "None":
            self.warpageFile = None
        else:
            self.warpageFile = warpageFile

    def AddUnitPolygons(self,polygons):
        self.unitpolygons = polygons

    def AddUnitPolygon(self,unitid,polygon):
        self.unitpolygons[unitid] = polygon
    
    def AddArrayPolygons(self,polygons):
        self.arraypolygons = polygons
    
    def AddArrayPolygon(self,arrayid,polygon):
        self.arraypolygons[arrayid] = polygon
    
    def AddHolePolygons(self,polygons):
        self.holepolygons = polygons

    def AddHolePolygon(self,holeid,polygon):
        self.holepolygons[holeid] = polygon
    
    def AddBridgePolygons(self,polygons):
        self.bridgepolygons = polygons
    
    def AddBridgePolygon(self,bridgeid,polygon):
        self.bridgepolygons[bridgeid] = polygon

    def BoundaryBox(self):
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]
        for aPoly in self.arraypolygons:
            curBoundaryBox = aPoly.BoundaryBox()
            boundaryBox[0] = min(boundaryBox[0],curBoundaryBox[0])
            boundaryBox[1] = max(boundaryBox[1],curBoundaryBox[1])
            boundaryBox[2] = min(boundaryBox[2],curBoundaryBox[2])
            boundaryBox[3] = max(boundaryBox[3],curBoundaryBox[3])
        return boundaryBox

    def TotalThickness(self):
        totalThickness = 0
        for aThickness in self.thickness:
            totalThickness += aThickness
        return totalThickness
    
    def MappedBoundaryBox(self):
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]
        for id in self.arraypolygons:            
            point2DList = self.arraypolygons[id].GetPolygonsCoordinates(self.location[0],self.location[1],self.rotation,self.mirror)            
            for aPoint in point2DList:
                aPointX = aPoint[0]
                aPointY = aPoint[1]
                boundaryBox[0] = min(boundaryBox[0],aPointX)
                boundaryBox[1] = max(boundaryBox[1],aPointX)
                boundaryBox[2] = min(boundaryBox[2],aPointY)
                boundaryBox[3] = max(boundaryBox[3],aPointY)
        return boundaryBox

    def GenerateSolidwithWarpage(self):
        warpageFace = self.GetWarpage()
        shapeListArray = {}
        shapeListUnit = {}
        shapeListHole = {}
        shapeListBridge = {}
        shapeArray = None
        thickness = self.TotalThickness()
        v = 0.0 
        print("Number of Array Polygon", len(self.arraypolygons))
        for id in self.arraypolygons:
            curV = self.arraypolygons[id].DiagonalLength()
            print("Diagonal Length : ", curV)
            if curV > v:                
                v = curV                
        for id in self.arraypolygons:
            print("Added Shape as Substract: ", id)
            curV = self.arraypolygons[id].DiagonalLength()
            print("curV : ", curV, " v : ", v)
            if curV <v:
                print("Substract Shape ID : ", id)
                shapeListArray[id] = self.arraypolygons[id].Generate(100.0*thickness,True,self.location[0], self.location[1], self.location[2]-thickness*50.0, self.rotation, self.mirror)
                #shapeListArray[id] = self.arraypolygons[id].GenerateSolidwithWarpage(thickness,True,self.location[0], self.location[1],self.location[2], self.rotation, self.mirror,warpageFace,0.01)
            else:
                print("Add Shape ID : ", id)
                shapeArray = self.arraypolygons[id].GenerateSolidwithWarpage(thickness,True,self.location[0], self.location[1],self.location[2], self.rotation, self.mirror,warpageFace,0.01)
            
        print("Number of Cut Geometry", len(shapeListArray))
        print("Number of Bridge Geometry", len(self.bridgepolygons))        
        for id in self.bridgepolygons:
            print("Bridge ID : ",id)
            curV = self.bridgepolygons[id].DiagonalLength()
            print("Diagonal Length : ", curV)
            bShape = self.bridgepolygons[id].GenerateSolidwithWarpage(thickness,True,self.location[0], self.location[1], self.location[2], self.rotation, self.mirror, warpageFace,0.001)
            shapeListBridge[id] = bShape
            print(bShape)
        print("Number of Unit Geometry", len(self.unitpolygons))
        for id in self.unitpolygons:
            print("Unit ID : ",id)
            curV = self.unitpolygons[id].DiagonalLength()
            print("Diagonal Length : ", curV)
            uShape =  self.unitpolygons[id].GenerateSolidwithWarpage(thickness,True,self.location[0], self.location[1], self.location[2], self.rotation, self.mirror, warpageFace,0.3)
            shapeListUnit[id] = uShape
            print(uShape)
        print("Number of Hole Geometry", len(self.holepolygons))
        for id in self.holepolygons:
            print("Hole ID : ",id)
            curV = self.holepolygons[id].DiagonalLength()
            print("Diagonal Length : ", curV)
            #self.holepolygons[id].Print()
            hShape = self.holepolygons[id].GenerateSolidwithWarpage(100.0*thickness,True,self.location[0], self.location[1], self.location[2]-50.0*thickness, self.rotation, self.mirror, warpageFace,0.2)
            hShape = self.holepolygons[id].Generate(100.0*thickness,True,self.location[0], self.location[1], self.location[2]-thickness*50.0, self.rotation, self.mirror)
            shapeListHole[id] = hShape
            print(hShape)
        
        # Generate Array
        for id in shapeListArray:
            print("Shape Cut by ", id)
            cut = BRepAlgoAPI_Cut(shapeArray,shapeListArray[id])                    
            cut.Build()
            shapeArray = cut.Shape()            

        

        shapeList = [] 
        #for id in shapeListBridge:
            #print("Shape Combine by ", id)
            #combine = BRepAlgoAPI_Fuse(shapeArray,shapeListBridge[id])
            #combine.Build()
            #shapeArray = combine.Shape()                    
            
           
        shapeList.append(shapeArray)
        #for id in shapeListArray:
#            shapeList.append(shapeListArray[id])            
        
        print("shapeListUnit Size : ",len(shapeListUnit))
        for id in shapeListUnit:
            aShape = shapeListUnit[id]
            print(aShape)
            for id2 in shapeListHole:
                print("Shape Cut by ", id2)
                cut = BRepAlgoAPI_Cut(aShape,shapeListHole[id2])                    
                cut.Build()
                aShape = cut.Shape()
            
            shapeList.append(aShape)
        print("shapeListHole Size : ",len(shapeListHole))
        print("shapeListBridge Size : ",len(shapeListBridge))
        for id in shapeListBridge:
            aShape = shapeListBridge[id]
            print(aShape)
            shapeList.append(aShape)
            
        #shapeList.append(warpageFace)
        return shapeList

    def Generate(self):        
        shapeListArray = {}         
        shapeListUnit = {}
        shapeListHole = {}    
        shapeListBridge = {}
        shapeArray = None
        thickness = self.TotalThickness()
        v = 0.0             
        print("Number of Array Polygon",len(self.arraypolygons))
        for id in self.arraypolygons:                        
            curV = self.arraypolygons[id].DiagonalLength()
            print("Diagonal Length : ",curV)
            if curV > v:                
                v = curV
                shapeArray = self.arraypolygons[id].Generate(thickness,True,self.location[0],self.location[1],self.location[2],self.rotation,self.mirror)
        for id in self.arraypolygons:
            print("Added Shape as Substract: ",id)
            curV = self.arraypolygons[id].DiagonalLength()
            print("curV : ",curV, " v : ",v)
            if curV < v:                                
                shapeListArray[id] = self.arraypolygons[id].Generate(thickness,True,self.location[0],self.location[1],self.location[2],self.rotation,self.mirror)

        print("Number of Cut Geometry :", len(shapeListArray))
        for id in self.bridgepolygons:
            shapeListBridge[id] = self.bridgepolygons[id].Generate(thickness,True,self.location[0],self.location[1],self.location[2],self.rotation,self.mirror)            
        
        for id in self.unitpolygons:
            shapeListUnit[id] = self.unitpolygons[id].Generate(thickness,True,self.location[0],self.location[1],self.location[2],self.rotation,self.mirror)            
        for id in self.holepolygons:
            shapeListHole[id] = self.holepolygons[id].Generate(thickness,True,self.location[0],self.location[1],self.location[2],self.rotation,self.mirror)
                
        # Generate Array
        for id in shapeListArray:
            print("Shape Cut by ", id)
            cut = BRepAlgoAPI_Cut(shapeArray,shapeListArray[id])                    
            cut.Build()
            shapeArray = cut.Shape()            
        for id in shapeListBridge:
            print("Shape Combine by ", id)
            combine = BRepAlgoAPI_Fuse(shapeArray,shapeListBridge[id])
            combine.Build()
            shapeArray = combine.Shape()                    
        
        shapeList = [] 
        shapeList.append(shapeArray)
        for id in shapeListUnit:
            aShape = shapeListUnit[id]
            for id2 in shapeListHole:
                print("Shape Cut by ", id2)
                cut = BRepAlgoAPI_Cut(aShape,shapeListHole[id2])                    
                cut.Build()
                aShape = cut.Shape()
            shapeList.append(aShape)
        return shapeList

    
