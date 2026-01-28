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
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.BRepBuilderAPI import(
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

from KooODBCADManager.WarpageSurface import WarpageSurface

class PCB():
    def __init__(self,id):
        self.id = id
        self.polygons = []
        #polgonType = Poly
        #self.polygons = self.polygons + [polgonType()]*0
        self.color = [0.5,0.5,0.5,1.0]
        self.type = 'pcb'
        self.layup = []
        self.thickness = [] 
        self.materialFile = ""
        self.patternFeatures = {}
        self.symbolfolder = [] 
        self.location = [0,0,0] 
        self.rotation = 0
        self.warpageFile = None
        self.mirror = False
        self.shape = []
        self.warpage = None
    
    def SetColor(self,r,g,b,a):
        self.color = [r,g,b,a]
    
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
    
    def SetWarpageFile(self,warpageFile):
        if warpageFile == "None":
            self.warpageFile = None
        else:
            self.warpageFile = warpageFile

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

    def AddPolygon(self,polygon):
        self.polygons.append(polygon)
    
    def WritePCB(self,stream):
        stream.write("PRP BOARD_PLACEMENT_OUTLINE '' ")
        for aPoly in self.polygons:
            aPoly.WritePolygonasConnectedVector(stream)
             
    def BoundaryBox(self):
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]
        for aPoly in self.polygons:
            curBoundaryBox = aPoly.BoundaryBox()
            boundaryBox[0] = min(boundaryBox[0],curBoundaryBox[0])
            boundaryBox[1] = max(boundaryBox[1],curBoundaryBox[1])
            boundaryBox[2] = min(boundaryBox[2],curBoundaryBox[2])
            boundaryBox[3] = max(boundaryBox[3],curBoundaryBox[3])
        return boundaryBox
    
    def TotalThickness(self):
        totalThickness = 0
        for aThickness in self.thickness:
            totalThickness = totalThickness + aThickness
        return totalThickness
    def MappedBoundaryBox(self):         
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]        
        for aPoly in self.polygons:
            point2DList = aPoly.GetPolygonsCoordinates(self.location[0],self.location[1],self.rotation,self.mirror)            
            for aPoint in point2DList:
                aPointX = aPoint[0]
                aPointY = aPoint[1]
                boundaryBox[0] = min(boundaryBox[0],aPointX)   
                boundaryBox[1] = max(boundaryBox[1],aPointX)
                boundaryBox[2] = min(boundaryBox[2],aPointY)
                boundaryBox[3] = max(boundaryBox[3],aPointY)
        return boundaryBox                

    def GenerateSolidwithSurface(self):
        from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
        from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
        from OCC.Core.GeomLProp import GeomLProp_SLProps
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_WIRE
        from OCC.Core.BRepFill import brepfill_Shell

        surfaceList = self.GenerateSurfacewithWarpage() 
        thickness = self.TotalThickness()
        solidList = [] 
        # Create the face from the B-spline surface
        for face in surfaceList:   
            
            from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
            from OCC.Core.gp import gp_Vec

            # Assuming you have a surface called 'surface' that you want to sweep
            # and a vector representing the direction and distance of the sweep called 'sweep_vector'

            # Define the sweep direction as a gp_Dir object
            sweep_direction = gp_Vec(0,0,thickness)

            # Create the prism by sweeping the surface along the direction vector
            prism_builder = BRepPrimAPI_MakePrism(face, sweep_direction)
            prism_builder.Build()

            # Get the resulting solid
            solidList.append(prism_builder.Shape())
            
                 
            #face_builder = BRepBuilderAPI_MakeFace], 1e-6)
            #face = face_builder.Face()
            #surface_adaptor = BRepAdaptor_Surface(face)
            #props = GeomLProp_SLProps(surface, surface_adaptor.FirstUParameter(), surface_adaptor.FirstVParameter(), 1, 1e-6)
            #surface_area_vector = props.Normal() 
            '''           
            offset_shape_builderA = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builderB = BRepOffsetAPI_MakeOffsetShape()
            offset_shape_builderA.PerformByJoin(face, thickness/2.0,1.e-6)
            offset_shape_builderB.PerformByJoin(face, -thickness/2.0,1.e-6)
            offset_surfaceA = offset_shape_builderA.Shape()
            offset_surfaceB = offset_shape_builderB.Shape()
            explorerA = TopExp_Explorer(offset_surfaceA, TopAbs_WIRE)            
            # Iterate over the wires in the shape and extract them
            wiresA = []            
            ii = 0            
            while explorerA.More():
                wire = explorerA.Current()
                wiresA.append(wire)
                explorerA.Next()
                print(wire)
                ii = ii + 1
            jj = 0 
            wiresB = [] 
            explorerB = TopExp_Explorer(offset_surfaceB, TopAbs_WIRE)
            while explorerB.More():
                wire = explorerB.Current()
                wiresB.append(wire)
                explorerB.Next()
                print(wire)
                jj = jj + 1
            print(ii,jj)
            shell_builder = brepfill_Shell(wiresA[0],wiresB[0])
            '''
            '''
            from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
            # Create a shell by adding the surfaces to a BRepBuilderAPI_MakeSolid object
            sewing = BRepBuilderAPI_Sewing()
            # Add the shapes to the sewing algorithm
            sewing.Add(offset_surfaceA)
            sewing.Add(offset_surfaceB)
            sewing.Add(shell_builder)            

            # Perform the sewing operation
            sewing.Perform()
            result_shape = sewing.SewedShape()
            solid = result_shape

            '''
            '''
            solid_builder = BRepBuilderAPI_MakeSolid()
            solid_builder.Add(offset_surfaceA)
            solid_builder.Add(offset_surfaceB)  
            solid_builder.Add(shell_builder)
            solid_builder.Build()
            solid = solid_builder.Solid()            
            
            solidList.append(solid)
            '''
            
        return solidList
    
    def ReducePolygonsCoordinates(self,point2DList,tol=0.3):
        import math
        newPoint2DList = [] 
        newPoint2DList.append(point2DList[0])
        size = len(point2DList)-1
        im1 = 0 
        for i in range(size):
            x1 = point2DList[im1][0]
            y1 = point2DList[im1][1]
            x2 = point2DList[i+1][0]
            y2 = point2DList[i+1][1]
            l1 = math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
            print('x1,y1',x1,y1,'x2,y2',x2,y2,'l1',l1)
            if l1 < tol:  
                continue
            else:
                im1 = i+1
                newPoint2DList.append(point2DList[i+1])
        x1 = newPoint2DList[len(newPoint2DList)-1][0]
        y1 = newPoint2DList[len(newPoint2DList)-1][1]
        x2 = newPoint2DList[0][0]
        y2 = newPoint2DList[0][1]
        l1 = math.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
        if l1 != 0:
            newPoint2DList.append(newPoint2DList[0])
        return newPoint2DList
            


                
    def GenerateSurfacewithWarpage(self):
        warpageFace = self.GetWarpage()
        print(warpageFace)
        if warpageFace == None:
            return self.Generate()
        shapelist = [] 
        for aPoly in self.polygons:
            '''
            point2DList = aPoly.GetPolygonsCoordinates(self.location[0],self.location[1],self.rotation,self.mirror)
            point2DList = self.ReducePolygonsCoordinates(point2DList)
            ii = 0
            point_list = []             
            print('point2DList',point2DList)
            print('Number of point', len(point2DList))
            for aPoint in point2DList:
                aPointX = aPoint[0]
                aPointY = aPoint[1]
                aPointZ = self.location[2]                                
                #print("i=",ii,"aPointX",aPointX,"aPointY",aPointY,"aPointZ",aPointZ)
                ii = ii + 1
                point_list.append(gp_Pnt(aPointX,aPointY,aPointZ))
            surface = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list,warpageFace)
            '''
            surface = aPoly.GenerateSurfacewithWarpage(self.location[0],self.location[1],self.location[2],self.rotation,self.mirror,warpageFace)
            shapelist.append(surface)
        return shapelist

    def GenerateProjectedSurfacebyPointListandWarpageSurface(self,point_list,warpageFace):
        pbuilder = BRepBuilderAPI_MakePolygon()
        pointsProjected = [] 
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCC.Core.GeomAPI import GeomAPI_IntSS
        from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Lin


        from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
        for i in range(len(point_list)):          
            line = gp_Lin(gp_Pnt(point_list[i].X(), point_list[i].Y(), point_list[i].Z()), gp_Dir(0,0,1))  # Replace with your line parameters
            intersection = GeomAPI_IntSS(line, warpageFace)
            intersection.Perform()
  
            #point_projection = GeomAPI_ProjectPointOnSurf(point_list[i], warpageFace)                        
            #projected_point = point_projection.NearestPoint()            
            if intersection.IsDone():
                projected_point = intersection.Point(1)
                print(i,projected_point.X(),projected_point.Y(),projected_point.Z())
                pbuilder.Add(projected_point)
                pointsProjected.append(projected_point)
         
        from OCC.Core.BRepFill import BRepFill_Filling
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        
        # Create a BRepFill_Filling object
        filling = BRepFill_Filling()
        # Add the points to the filling object
        edges = []
        
        print("Edge Generating...")
        for i in range(len(pointsProjected) - 1):
            print(i,len(pointsProjected) - 1)
            print(pointsProjected[i].X(),pointsProjected[i].Y(),pointsProjected[i].Z()) 
            print(pointsProjected[i+1].X(),pointsProjected[i+1].Y(),pointsProjected[i+1].Z())   
            
            edge = BRepBuilderAPI_MakeEdge(pointsProjected[i], pointsProjected[i + 1])            
            edges.append(edge.Edge())
        print("Edge Generating...Done")  
        import OCC.Core.GeomAbs as GeomAbs
        # Create a BRepFill_Filling object and perform the filling operation
        filling = BRepFill_Filling(3,15,2,False,0.1,0.1,0.1,0.1,8,9)
        for edge in edges:
            filling.Add(edge,GeomAbs.GeomAbs_C0)
        filling.Build()
        print("Face Generating...Done")        
        surface = filling.Face()
        return surface

    def GenerateProjectedSurfacebyPointListandWarpageSurface2(self,point_list,warpageFace):
        pbuilder = BRepBuilderAPI_MakePolygon()
        pointsProjected = [] 
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
        for i in range(len(point_list)):            
            point_projection = GeomAPI_ProjectPointOnSurf(point_list[i], warpageFace)                        
            projected_point = point_projection.NearestPoint()            
            print(i,projected_point.X(),projected_point.Y(),projected_point.Z())
            pbuilder.Add(projected_point)
            pointsProjected.append(projected_point)
         
        from OCC.Core.BRepFill import BRepFill_Filling
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        
        # Create a BRepFill_Filling object
        filling = BRepFill_Filling()
        # Add the points to the filling object
        edges = []
        
        print("Edge Generating...")
        for i in range(len(pointsProjected) - 1):
            print(i,len(pointsProjected) - 1)
            print(pointsProjected[i].X(),pointsProjected[i].Y(),pointsProjected[i].Z()) 
            print(pointsProjected[i+1].X(),pointsProjected[i+1].Y(),pointsProjected[i+1].Z())   
            
            edge = BRepBuilderAPI_MakeEdge(pointsProjected[i], pointsProjected[i + 1])            
            edges.append(edge.Edge())
        print("Edge Generating...Done")  
        import OCC.Core.GeomAbs as GeomAbs
        # Create a BRepFill_Filling object and perform the filling operation
        filling = BRepFill_Filling(3,15,2,False,0.1,0.1,0.1,0.1,8,9)
        for edge in edges:
            filling.Add(edge,GeomAbs.GeomAbs_C0)
        filling.Build()
        print("Face Generating...Done")        
        surface = filling.Face()
        return surface
    


    def Generate(self):
        
        point_list = []         
        shapeList = []  
        for aPoly in self.polygons:
            #print("Current location : ",self.location[0],self.location[1],self.location[2])
            #print("Current rotation : ",self.rotation)
            #print("Current mirror : ",self.mirror)
            point2DList = aPoly.GetPolygonsCoordinates(self.location[0],self.location[1],self.rotation,self.mirror)
            for aPoint in point2DList:
                aPointX = aPoint[0]
                aPointY = aPoint[1]
                aPointZ = self.location[2]
                point_list.append(gp_Pnt(aPointX,aPointY,aPointZ))                
            pbuilder = BRepBuilderAPI_MakePolygon()
            for point in point_list:
                pbuilder.Add(point)
            p = pbuilder.Wire()
            fbuilder = BRepBuilderAPI_MakeFace(p,True)
            face = fbuilder.Face()
            thick = self.TotalThickness()
            pbuilder = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
            solid = pbuilder.Shape()
            shapeList.append(solid)
        self.shape = shapeList
        return shapeList
