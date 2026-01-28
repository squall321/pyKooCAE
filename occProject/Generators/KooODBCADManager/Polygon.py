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
import random

import numpy as np
import json
import math
from OCC.Core.gp import gp_Ax2, gp_Dir, gp_Circ, gp_Pnt, gp_Vec
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,    
)
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakePrism
)

class Vertex2D():
    def __init__(self,id,x,y,r=0):
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.r = r 
        self.shape = None

    def Vertex(self):
        vertex = []
        vertex.append(self.x)
        vertex.append(self.y)
        return vertex
    
    def Distance(self,vertex):
        distance = math.sqrt((self.x-vertex.x)**2 + (self.y-vertex.y)**2)
        #print("vertex : ",distance)
        return distance
    
    def SetRadius(self,r):
        self.r = r

    def SetCoord(self,x,y):
        self.x = float(x)
        self.y = float(y)

    def SerializeData(self):
        jsondata = {}
        jsondata['id'] = self.id
        jsondata['x'] = self.x
        jsondata['y'] = self.y
        jsondata['r'] = self.r
        return jsondata
    
    def GetVertexCoordinates(self, originX=0, originY=0, rotation = 0, mirror = False):        
        x = self.x
        y = self.y 
        #print(originX,originY,rotation,mirror)
        if rotation == 90:
            x = self.y
            y = -self.x
            if mirror:
                y = -y
        elif rotation == 180:
            x = -self.x
            y = -self.y
            if mirror:
                x = -x
        elif rotation == 270:
            x = -self.y
            y = self.x
            if mirror:
                y = -y
        else:
            if mirror:
                x = -x
        x = x + originX
        y = y + originY
        r = self.r        
        return [x,y,r]
    
    def Generate(self,originX=0,originY=0,originZ=0,rotation=0,mirror=False):
        [x,y,r] = self.GetVertexCoordinates(originX,originY,rotation,mirror)
        vBuilder = BRepBuilderAPI_MakeVertex(gp_Pnt(x,y,originZ))
        self.shape = vBuilder.Vertex()
        return self.shape
    
    def GenerateProjected(self,warpageFace, originX = 0, originY = 0, originZ = 0, rotation = 0, mirror = False):
        [x,y,r] = self.GetVertexCoordinates(originX,originY,rotation,mirror)
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        point_projection = GeomAPI_ProjectPointOnSurf(gp_Pnt(x,y,originZ),warpageFace)
        projectedPoint = point_projection.NearestPoint()
        vBuilder = BRepBuilderAPI_MakeVertex(projectedPoint)
        self.shape = vBuilder.Vertex()
        return self.shape

    def Print(self):
        print("Vertex: ",self.id,"(",self.x,",",self.y,")")
    
    
class Edges2D():
    def __init__(self,id,vertices,type="Line"):
        self.id = id
        self.vertices = vertices
        self.type = type
        self.counterclockwise = True
        self.shape = None

    def ReverseOrder(self):
        self.vertices.reverse()

    def DistancefromEdge(self, edge):
        distance = 1.e99
        for i in range(len(self.vertices)):
            v1 = self.vertices[i]            
            for j in range(len(edge.vertices)):
                v2 = edge.vertices[j]                
                distance = min(v1.Distance(v2),distance)
        return distance        

    def AnglefromEdge(self, edge):
        vector1 = gp_Vec(self.vertices[1].x-self.vertices[0].x,self.vertices[1].y-self.vertices[0].y,0)
        vector2 = gp_Vec(edge.vertices[1].x-edge.vertices[0].x,edge.vertices[1].y-edge.vertices[0].y,0)
        angle = vector1.Angle(vector2)
        return angle
    
    def Length(self):
        length = 0
        for i in range(len(self.vertices)-1):
            v1 = self.vertices[i]
            v2 = self.vertices[i+1]
            length = length + math.sqrt((v1.x-v2.x)**2+(v1.y-v2.y)**2)
        return length

    def SetReverse(self):
        if self.type == "Line":
            v1 = self.vertices[0]
            v2 = self.vertices[1]
            self.vertices.clear()
            self.vertices.append(v2)
            self.vertices.append(v1)    
        if self.type == "Arc":
            v1 = self.vertices[0]
            v2 = self.vertices[1]
            v3 = self.vertices[2]
            self.vertices.clear()
            self.vertices.append(v2)
            self.vertices.append(v1) 
            self.vertices.append(v3)
            self.counterclockwise = not self.counterclockwise        
    
    def SetasLine(self,startVertex,endVertex):
        self.type = "Line"
        self.vertices = [] 
        self.vertices.append(startVertex)
        self.vertices.append(endVertex)

    def SetasArc(self,startVertex,endVertex,centerVertex):
        self.type = "Arc"
        self.vertices = []
        self.vertices.append(startVertex)
        self.vertices.append(endVertex) 
        self.vertices.append(centerVertex)  
    
    def SetasCircle(self, vertex):
        self.type = "Circle"
        self.vertices = []
        self.vertices.append(vertex)
        
    def AddVertex(self,newVertex):
        self.vertices.append(newVertex)

    def RemoveVertex(self,vertex):
        self.vertices.remove(vertex)

    def SerializeData(self):
        jsondata = {}
        jsondata['id'] = self.id
        jsondata['vertices'] = {}
        for aVertex in self.vertices:
            jsondata['vertices'][aVertex.id] = aVertex.SerializeData()
        jsondata['type'] = self.type
        return jsondata    
    def Generate(self,originX=0,originY=0,originZ=0,rotation=0,mirror=False):
        try:
            if self.type == "Line":
                v1 : Vertex2D = self.vertices[0]
                v2 : Vertex2D = self.vertices[1]
                v1 = v1.Generate(originX,originY,originZ,rotation,mirror)            
                v2 = v2.Generate(originX,originY,originZ,rotation,mirror)
                eBuilder = BRepBuilderAPI_MakeEdge(v1,v2)

            
                return eBuilder.Edge()
            if self.type == "Arc":
                v1 : Vertex2D = self.vertices[0]
                v2 : Vertex2D = self.vertices[1]
                v3 : Vertex2D = self.vertices[2]
                V1 = v1.Generate(originX,originY,originZ,rotation,mirror)
                [x1,y1,r1] = v1.GetVertexCoordinates(originX,originY,rotation,mirror)
                V2 = v2.Generate(originX,originY,originZ,rotation,mirror)
                [x2,y2,r2] = v2.GetVertexCoordinates(originX,originY,rotation,mirror)
                V3 = v3.Generate(originX,originY,originZ,rotation,mirror)
                [x3,y3,r3] = v3.GetVertexCoordinates(originX,originY,rotation,mirror)

                #print("Arc")
                #print(x1,",",y1)
                #print(x2,",",y2)
                #print(x3,",",y3)
                normal_vector = gp_Dir(0,0,1)
                if self.counterclockwise == False:
                    normal_vector = gp_Dir(0,0,-1)
                startp = gp_Pnt(x1,y1,originZ)
                endp = gp_Pnt(x2,y2,originZ) 
                centerp = gp_Pnt(x3,y3,originZ)
                radius = centerp.Distance(startp)          
                #print("radius :",radius)
                coordinate_system = gp_Ax2(centerp,normal_vector)

                eBuilder = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system,radius), startp,endp).Edge()
                return eBuilder
            if self.type == "Circle":
                v : Vertex2D = self.vertices[0]            
                [x,y,r] = v.GetVertexCoordinates(originX,originY,rotation,mirror)
                centerp = gp_Pnt(x,y,originZ)
                coordinate_system = gp_Ax2(centerp,gp_Dir(0,0,1))
                eBuilder = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system,r)).Edge()
                return eBuilder
        except:
            print("Error in Edge Generation", self.id)
            
            return None
        return None
    
    def GenerateProjected(self, warpageFace, originX = 0, originY = 0, originZ = 0, rotation = 0, mirror = False):
        if self.type == "Line":
            v1 = self.vertices[0]
            v2 = self.vertices[1]
            v1 : Vertex2D = v1.GenerateProjected(warpageFace,originX,originY,originZ,rotation,mirror)            
            v2 : Vertex2D = v2.GenerateProjected(warpageFace,originX,originY,originZ,rotation,mirror)
            eBuilder = BRepBuilderAPI_MakeEdge(v1,v2)
            return eBuilder.Edge()
        if self.type == "Arc":
            v1 : Vertex2D = self.vertices[0]
            v2 : Vertex2D = self.vertices[1]
            v3 : Vertex2D = self.vertices[2]
            V1 = v1.GenerateProjected(warpageFace,originX,originY,originZ,rotation,mirror)
            [x1,y1,r1] = v1.GetVertexCoordinates(originX,originY,rotation,mirror)
            V2 = v2.GenerateProjected(warpageFace,originX,originY,originZ,rotation,mirror)
            [x2,y2,r2] = v2.GetVertexCoordinates(originX,originY,rotation,mirror)
            V3 = v3.GenerateProjected(warpageFace,originX,originY,originZ,rotation,mirror)
            [x3,y3,r3] = v3.GetVertexCoordinates(originX,originY,rotation,mirror)

            #print("Arc")
            #print(x1,",",y1)
            #print(x2,",",y2)
            #print(x3,",",y3)
            normal_vector = gp_Dir(0,0,1)
            if self.counterclockwise == False:
                normal_vector = gp_Dir(0,0,-1)
            startp = gp_Pnt(x1,y1,originZ)
            endp = gp_Pnt(x2,y2,originZ) 
            centerp = gp_Pnt(x3,y3,originZ)
            radius = centerp.Distance(startp)          
            #print("radius :",radius)
            coordinate_system = gp_Ax2(centerp,normal_vector)

            eBuilder = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system,radius), startp,endp).Edge()
            return eBuilder
        return None
    
    def Print(self):
        print("Edge")
        for aVertex in self.vertices:
            aVertex.Print()
        print("type :",self.type)
        print("counterclockwise :",self.counterclockwise)

# PCB, package, capacitor and etc
class Polygon2D():
    def __init__(self,id,type="CR"):
        self.id = id
        self.vertices = [] 
        self.edges = [] 
        self.name = "None"
        self.type = type
        self.shape = None

    def AddVertex(self,newVertex):
        self.vertices.append(newVertex)
    
    def AddVertices(self,newVertices):
        for vertex in newVertices:
            self.vertices.append(vertex)
    
    def AddLine(self, e):
        v1 = e.vertices[0]
        v2 = e.vertices[1]
        v1Check = False
        v2Check = False
        for aVertex in self.vertices:
            if aVertex.id == v1.id:
                v1Check = True
            if aVertex.id == v2.id:
                v2Check = True
        if v1Check == False:
            self.vertices.append(v1)
        if v2Check == False:
            self.vertices.append(v2)
        self.edges.append(e)
    def AddArc(self, e):
        v1 = e.vertices[0]
        v2 = e.vertices[1]
        v3 = e.vertices[2]
        v1Check = False
        v2Check = False
        v3Check = False
        for aVertex in self.vertices:
            if aVertex.id == v1.id:
                v1Check = True
            if aVertex.id == v2.id:
                v2Check = True
            if aVertex.id == v3.id:
                v3Check = True
        if v1Check == False:
            self.vertices.append(v1)
        if v2Check == False:
            self.vertices.append(v2)
        if v3Check == False:
            self.vertices.append(v3)
        self.edges.append(e)
    
    def AddLines(self,e):
        for edge in e:
            self.AddLine(edge)

    def AddEdge(self,newEdge):        
        self.edges.append(newEdge)
    
    def AddEdges(self,newEdges):
        for edge in newEdges:
            self.edges.append(edge)

    def WritePolygonasConnectedVector(self,stream):
        for aVertex in self.vertices:
            stream.write("{x} {y} ".format(x=aVertex.x,y=aVertex.y))

    def SerializeData(self):
        jsondata = {}
        jsondata['id'] = self.id
        jsondata['name'] = self.name
        jsondata['type'] = self.type
        jsondata['vertices'] = {}
        for aVertex in self.vertices:
            jsondata['vertices'][aVertex.id] = aVertex.SerializeData()
        jsondata['edges'] = {}
        for aEdge in self.edges:
            jsondata['edges'][aEdge.id] = aEdge.SerializeData()            
        return jsondata
    
    def WritePolygon(self, stream):
        if self.type == 'RC':
            xmin = self.vertices[0].x
            ymin = self.vertices[0].y
            delX = self.vertices[2].x - xmin 
            delY = self.vertices[2].y - ymin
            stream.write("RC,{xmin},{ymin},{width},{height}\n".format(xmin=xmin,ymin=ymin,width=delX,height=delY))
        elif self.type == 'CR':
            aVertex = self.vertices[0]
            stream.write("CR,{x},{y},{r}\n".format(x=aVertex.x,y=aVertex.y,r=aVertex.r))
        elif self.type == 'CT':
            stream.write("CT\n")
            i = 0
            for aVertex in self.vertices:
                if i == 0:
                    stream.write("OB,{x},{y}\n".format(x=aVertex.x,y=aVertex.y))
                elif i == len(self.vertices)-1:
                    stream.write("OS,{x},{y}\n".format(x=aVertex.x,y=aVertex.y))
                    stream.write("OE\n")
                else:
                    stream.write("OS,{x},{y}\n".format(x=aVertex.x,y=aVertex.y))
            stream.write("CE\n")

    def GetPolygonsCoordinateswithoutArc(self, originX=0, originY=0, rotation = 0, mirror = False):
        polygonList = [] 
        for aEdge in self.edges:
            aVertex = aEdge.vertices[0]
            x = aVertex.x
            y = aVertex.y 
            if rotation == 90:
                x = aVertex.y
                y = -aVertex.x
                
                if mirror:
                    y = -y
                    
            elif rotation == 180:
                x = -aVertex.x
                y = -aVertex.y
                if mirror:
                    x = -x
            elif rotation == 270:
                x = -aVertex.y
                y = aVertex.x
                if mirror:
                    y = -y
            else:
                if mirror:
                    x = -x
            x = x + originX
            y = y + originY
            r = aVertex.r
            #print('x,y',x,y)
            polygonList.append([x,y,r])            
        return polygonList




    def GetPolygonsCoordinates(self, originX=0, originY=0, rotation = 0, mirror = False):
        polygonList = []
        
        for aVertex in self.vertices:
            x = aVertex.x
            y = aVertex.y 
            if rotation == 90:
                x = aVertex.y
                y = -aVertex.x
                
                if mirror:
                    y = -y
                    
            elif rotation == 180:
                x = -aVertex.x
                y = -aVertex.y
                if mirror:
                    x = -x
            elif rotation == 270:
                x = -aVertex.y
                y = aVertex.x
                if mirror:
                    y = -y
            else:
                if mirror:
                    x = -x
            x = x + originX
            y = y + originY
            r = aVertex.r
            polygonList.append([x,y,r])
        return polygonList
    
    def BoundaryBox(self):
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]
        for aVertex in self.vertices:
            x = aVertex.x
            y = aVertex.y
            boundaryBox[0] = min(x,boundaryBox[0])
            boundaryBox[1] = max(x,boundaryBox[1])
            boundaryBox[2] = min(y,boundaryBox[2])
            boundaryBox[3] = max(y,boundaryBox[3])
        return boundaryBox
    
    def DiagonalLength(self):
        bdBox = self.BoundaryBox()
        return math.sqrt((bdBox[1]-bdBox[0])**2+(bdBox[3]-bdBox[2])**2)
    
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
            #print('x1,y1',x1,y1,'x2,y2',x2,y2,'l1',l1)
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
    
    def GenerateProjectedSurfacebyPointListandWarpageSurface2(self,point_list,warpageFace, additional_points = []):
        pbuilder = BRepBuilderAPI_MakePolygon()
        pointsProjected = [] 
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCC.Core.GeomAPI import GeomAPI_IntSS, GeomAPI_IntCS
        from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Lin
        from OCC.Core.Geom import Geom_Line


        from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
        for i in range(len(point_list)):          
            line = gp_Lin(gp_Pnt(point_list[i].X(), point_list[i].Y(), point_list[i].Z()), gp_Dir(0,0,1))  # Replace with your line parameters
            line = Geom_Line(line)
            intersection = GeomAPI_IntCS(line, warpageFace)
            #intersection.Perform()
  
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
        filling = BRepFill_Filling(3,15,2,False,0.01,0.01,0.1,0.1,8,9)
        for edge in edges:
            filling.Add(edge,GeomAbs.GeomAbs_C0)

        if len(additional_points) > 0:
            for pnt in additional_points:
                filling.Add(pnt)
        filling.Build()
        print("Face Generating...Done")        
        surface = filling.Face()
        return surface

    def GenerateProjectedSurfacebyPointListandWarpageSurface(self,point_list,warpageFace, additional_points = []):
        pbuilder = BRepBuilderAPI_MakePolygon()
        pointsProjected = [] 
        additionalPointsProjected = [] 
        from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
        from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
        from OCC.Core.BRep import BRep_Tool_PolygonOnTriangulation
        
        for i in range(len(point_list)):            
            point_projection = GeomAPI_ProjectPointOnSurf(point_list[i], warpageFace)            
            projected_point = point_projection.NearestPoint()            
            #print(i,projected_point.X(),projected_point.Y(),projected_point.Z())
            pbuilder.Add(projected_point)
            pointsProjected.append(projected_point)    
            print(i,pointsProjected[i].X(),pointsProjected[i].Y(),pointsProjected[i].Z())
        
        for i in range(len(additional_points)):
            point_projection = GeomAPI_ProjectPointOnSurf(additional_points[i], warpageFace)
            projected_point = point_projection.NearestPoint()
            additionalPointsProjected.append(projected_point)
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
        if len(additionalPointsProjected) > 0:
            for pnt in additionalPointsProjected:
                filling.Add(pnt)
        filling.Build()
        print("Face Generating...Done")        
        surface = filling.Face()
        criteria = 0.0001
        while surface.IsNull():
            filling = BRepFill_Filling(3,15,2,False,criteria,criteria,0.1,0.1,20,20)
            for edge in edges:
                filling.Add(edge,GeomAbs.GeomAbs_C0)
            if len(additionalPointsProjected) > 0:
                for pnt in additionalPointsProjected:
                    filling.Add(pnt)
            filling.Build()
            print("Face Generating...Done")        
            surface = filling.Face()
            criteria = criteria *1.1

        '''
        filling = BRepFill_Filling(3,15,2,False,0.1,0.1,0.1,0.1,8,9)
        for edge in edges:
            filling.Add(edge,GeomAbs.GeomAbs_C0)
        filling.Build()
        print("Face Generating...Done")        
        surface = filling.Face()
        criteria = 0.2
        while surface.IsNull():
            filling = BRepFill_Filling(3,15,2,False,0.1,criteria,0.1,0.1,8,9)
            for edge in edges:
                filling.Add(edge,GeomAbs.GeomAbs_C0)
            filling.Build()
            print("Face Generating...Done")        
            surface = filling.Face()
            criteria = criteria + 0.1

        '''



        
        return surface
    
    def GenerateSolidwithWarpage(self, thickness,upper, originX = 0, originY = 0, originZ = 0, rotation = 0, mirror = False, warpageFace = None,tol=0.3):
        if warpageFace == None: 
            return self.Generate()
        surface = self.GenerateSurfacewithWarpage(originX, originY, originZ, rotation, mirror, warpageFace,tol)
        if surface == None:
            return None
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
        from OCC.Core.gp import gp_Vec 
        print("Generating Solid")
        print("Thickness",thickness)
        sweep_direction = gp_Vec(0,0,thickness)
        if upper == False:
            sweep_direction = gp_Vec(0,0,-thickness)
        print("Direction Vector",sweep_direction.X(),sweep_direction.Y(),sweep_direction.Z())
        print("Surface Type",surface)
        prism_builder = BRepPrimAPI_MakePrism(surface, sweep_direction)
        print("Building Solid...")
        prism_builder.Build()
        print("Generating Solid...Done")
        return prism_builder.Shape()
    
    
    def GenerateSurfacewithWarpage(self,originX = 0, originY = 0, originZ = 0, rotation = 0, mirror = False, warpageFace=None,tol=0.3):
        if warpageFace == None:
            return None
        
        shapeList = [] 
        #point2DList = self.GetPolygonsCoordinates(originX,originY,rotation,mirror)
        point2DList = self.GetPolygonsCoordinateswithoutArc(originX,originY,rotation,mirror)
        point2DList = self.ReducePolygonsCoordinates(point2DList,tol)
        ii = 0
        point_list = [] 
        #print('point2DList',point2DList)
        #print('Number of points',len(point2DList))
        for aPoint in point2DList:
            aPointX = aPoint[0]
            aPointY = aPoint[1] 
            aPointZ = originZ
            #print('i=',ii,'aPointX,aPointY,aPointZ',aPointX,aPointY,aPointZ)
            #ii = ii + 1
            point_list.append(gp_Pnt(aPointX,aPointY,aPointZ))
        
        num_additional_points = 20  # Number of additional points to generate
        additional_points = self.generate_random_points_inside_polygon(point_list, num_additional_points)        
        #surface = self.GenerateProjectedSurfacebyPointListandWarpageSurface(additional_points,warpageFace)
        surface = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list,warpageFace,additional_points)
        #surface = self.GenerateProjectedSurfacebyPointListandWarpageSurface(point_list,warpageFace)
        return surface


    def ReducedWire(self,edgeList, originX=0,originY=0,originZ=0,rotation=0,mirror=False, tol = 0.2):
        
        conservedEdgeList = []
        newEdgeList = [] 
        for edge in edgeList:        
            e = edge
            if e.Length() < tol:
                newEdgeList.append(e)
            else:
                conservedEdgeList.append(edge)

        if len(newEdgeList) == 0:
            return conservedEdgeList   
        
        modifiedEdgeGroupList = []
        newGroup = [] 
        i = 0
        while len(newEdgeList) > 0:        
            e1 = newEdgeList[i]
            newGroup.append(e1)
            newEdgeList.remove(e1)            
            newEdge = True
            while newEdge == True:
                newEdge = False
                size = len(newEdgeList)
                for j in range(size):
                    if j>=size:
                        break
                    e2 = newEdgeList[j]
                    distance = e2.DistancefromEdge(e1)
                    #print("distance",distance)
                    if distance < 0.001:                        
                        if e2.vertices[1].id == e1.vertices[1].id:
                            e2.SetReverse()
                        newGroup.append(e2)
                        newEdgeList.remove(e2)
                        
                        newEdge = True
                        e1 = e2
                        j=0 
                        size = len(newEdgeList)
            modifiedEdgeGroupList.append(newGroup)
            newGroup = []               

        newEdgeList = conservedEdgeList         
        for edgeGroup in modifiedEdgeGroupList:
            pointList = [] 
            for i in range(len(edgeGroup)):
                pointList.append(edgeGroup[i].vertices[0])
            pointList.append(edgeGroup[len(edgeGroup)-1].vertices[1])

            newPointList = []
            if len(pointList) < 4:
                for i in range(0,len(pointList)-1):
                    v1 = pointList[i]
                    v2 = pointList[i+1]
                    newEdge = Edges2D(0,[v1,v2],"Line")
                    newEdgeList.append(newEdge)
            else:
                for i in range(0,len(pointList)-1,max(1,int((len(pointList)-1)/4))):
                    newPointList.append(pointList[i])
                for i in range(0,len(newPointList)-1):
                    v1 = newPointList[i]
                    v2 = newPointList[i+1]
                    newEdge = Edges2D(0,[v1,v2],"Line")
                    newEdgeList.append(newEdge)
                
            


        '''
        for edgeGroup in modifiedEdgeGroupList:
            if len(edgeGroup) == 1:
                newEdgeList.append(edgeGroup[0])
            else:
                triangleEdgeList = [] 
                elseEdgeList = [] 
                triangleEdgeList.append(edgeGroup[0])
                centerp = None 
                for j in range(len(edgeGroup)-1):
                    e1 = edgeGroup[j]
                    e2 = edgeGroup[j+1]          
                    v1 = e1.vertices[0]
                    v2 = e1.vertices[1]
                    v3 = e2.vertices[1]
                    P1x = v1.x
                    P1y = v1.y
                    P2x = v2.x
                    P2y = v2.y
                    P3x = v3.x
                    P3y = v3.y                        
                    D21x = P2x-P1x
                    D21y = P2y-P1y
                    D31x = P3x-P1x
                    D31y = P3y-P1y

                    F2 = 1/2*(D21x**2+D21y**2)
                    F3 = 1/2*(D31x**2+D31y**2)

                    M23xy = D21x*D31y-D21y*D31x                                               

                    F23x = F2*D31x-F3*D21x
                    F23y = F2*D31y-F3*D21y

                    Cx = P1x+(M23xy*F23y)/(M23xy**2)
                    Cy = P1y+(-M23xy*F23x)/(M23xy**2)
                    print(Cx,Cy,0.0)
                    if j == 0:                        
                        # v1,v2,v3 make arc. I want to find center point of arc
                        centerp = gp_Pnt(Cx,Cy,0)
                    else:
                        curp = gp_Pnt(Cx,Cy,0)
                        if curp.Distance(centerp) < 0.001:                            
                            triangleEdgeList.append(e2)                            
                        else:                            
                            elseEdgeList.append(e2)
                
                if len(elseEdgeList)>0:
                    for k in range(len(elseEdgeList)):
                        triangleEdgeList.append(elseEdgeList[k])

                v1 = triangleEdgeList[0].vertices[0]
                v2 = triangleEdgeList[0].vertices[1]
                v3 = triangleEdgeList[len(triangleEdgeList)-1].vertices[1]
                #arc from x1,y1 to x3,y3

                newEdge = Edges2D(0,[v1,v2,v3],"Arc")
                newEdgeList.append(newEdge)
                print("triangleEdgeList")
                for k in range(len(triangleEdgeList)):
                    
                    print(triangleEdgeList[k].vertices[0].x,triangleEdgeList[k].vertices[0].y)
                print(triangleEdgeList[k].vertices[1].x,triangleEdgeList[k].vertices[1].y)                    
                print("\n")
                print("\n")


        '''          

                    

  
           
        # order 
        reorderedEdgeList = [] 
        while len(newEdgeList) >0:
            e1 = newEdgeList[0]
            reorderedEdgeList.append(e1)
            newEdgeList.remove(e1)
            newEdge = True
            while newEdge == True:
                newEdge = False
                for j in range(len(newEdgeList)):
                    if j>= len(newEdgeList):
                        break
                    e2 = newEdgeList[j]
                    if e2.DistancefromEdge(e1) < 0.000001:                        
                        if e2.vertices[1].id == e1.vertices[1].id:
                            e2.SetReverse()
                        reorderedEdgeList.append(e2)
                        newEdgeList.remove(e2)
                        
                        newEdge = True
                        e1 = e2
                        j = 0


        v1 = reorderedEdgeList[len(reorderedEdgeList)-1].vertices[1]
        v2 = reorderedEdgeList[0].vertices[0]
        if v1.Distance(v2) > 0.000001:                    
            newEdge = Edges2D(0,[v1,v2],"Line")
            reorderedEdgeList.append(newEdge)
        for edge in reorderedEdgeList:
            v1 = edge.vertices[0]
            v2 = edge.vertices[1]
            print("v1",v1.x,v1.y," ","v2",v2.x,v2.y," ")
            if len(edge.vertices) == 3:
                v3 = edge.vertices[2]
                print("v3",v3.x,v3.y," ")   
        return reorderedEdgeList
    
    def Generate(self,thickness,upper, originX=0,originY=0,originZ=0,rotation=0,mirror=False):
        wire_builder = BRepBuilderAPI_MakeWire()
        
        mode = "CURRENT"

        #mode = "EXPERIMENTAL2"
        if mode == "CURRENT":
            edgeList = [] 
            for edge in self.edges:
                e = edge.Generate(originX,originY,originZ,rotation,mirror)                                
                if e == None:
                    return None
                wire_builder.Add(e)   
                    
        elif mode == "EXPERIMENTAL":
            
            edgeList = [] 
            for edge in self.edges:            
                edgeList.append(edge)
            edgeList = self.ReducedWire(edgeList,originX,originY,originZ,rotation,mirror)
            for edge in edgeList:            
                e = edge.Generate(originX,originY,originZ,rotation,mirror)
                #print(e)
                wire_builder.Add(e)            
        elif mode == "EXPERIMENTAL2":
            point2DList = self.GetPolygonsCoordinateswithoutArc(originX,originY,rotation,mirror)
            point2DList = self.ReducePolygonsCoordinates(point2DList,0.2)
            for i in range(len(point2DList)-1):
                p1 = point2DList[i]
                v1 = Vertex2D(0,p1[0],p1[1],0)
                p2 = point2DList[i+1]
                v2 = Vertex2D(0,p2[0],p2[1],0)
                e = Edges2D(0,[v1,v2],"Line")                
                wire_builder.Add(e.Generate(originX,originY,originZ,rotation,mirror))                

        wire = wire_builder.Wire()
        face_builder = BRepBuilderAPI_MakeFace(wire,True)
        face_builder.Build()
        if upper == True:
            prism_builder = BRepPrimAPI_MakePrism(face_builder.Face(),gp_Vec(0,0,thickness))
        else:
            prism_builder = BRepPrimAPI_MakePrism(face_builder.Face(),gp_Vec(0,0,-thickness))

        self.shape = prism_builder.Shape()          
                
        return self.shape 
    
    def Print(self):
        print("Polygon")
        for edge in self.edges:
            edge.Print()


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


    def generate_random_points_inside_polygon(self, polygon, num_points):
        points = []
        
        min_x = min(p.X() for p in polygon)
        max_x = max(p.X() for p in polygon)
        min_y = min(p.Y() for p in polygon)
        max_y = max(p.Y() for p in polygon)
        z = polygon[0].Z()
        
        option = 2
        option = 1
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
        print("Additional points generated")
        for p in points:
            print(p.X(), p.Y(), p.Z())
        return points
    
    def MinDistance(self, v11, v12, v21, v22):
        d1 = v11.Distance(v21)
        d2 = v11.Distance(v22)
        d3 = v12.Distance(v21)
        d4 = v12.Distance(v22)
        return min(d1,d2,d3,d4)

    def ReshapeHolePolygonstoShell(self):
        longestPoints = [] 
        longestPoints2 = [] 
        longestPoints3 = [] 
        longestPoints4 = [] 
        maxlength = 0.0
        maxLength2 = 0.0
        maxLength3 = 0.0
        maxLength4 = 0.0
        for i in range(len(self.vertices)-1):
            v1 : Vertex2D = self.vertices[i]
            v2 : Vertex2D = self.vertices[i+1]            
            length = v1.Distance(v2)
            if length > maxLength4:
                maxLength4 = length                 
                longestPoints4 = [i,v1,v2]
                if length > maxLength3:
                    maxLength4 = maxLength3
                    longestPoints4 = longestPoints3
                    maxLength3 = length
                    longestPoints3 = [i,v1,v2]
                    if length > maxLength2:
                        maxLength3 = maxLength2
                        longestPoints3 = longestPoints2
                        maxLength2 = length
                        longestPoints2 = [i,v1,v2]
                        if length > maxlength:
                            maxLength2 = maxlength
                            longestPoints2 = longestPoints
                            maxlength = length
                            longestPoints = [i,v1,v2]
        l2 = self.MinDistance(longestPoints[1],longestPoints[2],longestPoints2[1],longestPoints2[2])
        l3 = self.MinDistance(longestPoints[1],longestPoints[2],longestPoints3[1],longestPoints3[2])
        l4 = self.MinDistance(longestPoints[1],longestPoints[2],longestPoints4[1],longestPoints4[2])
        longestPair = [] 
        if l2 < l3 and l2 < l4:
            longestPair = longestPoints2
        elif l3 < l2 and l3 < l4:
            longestPair = longestPoints3
        else:
            longestPair = longestPoints4
        ith = 0
        if longestPoints[1].x <longestPoints[2].x:
            ith = longestPoints[0]
        else:
            ith = longestPoints[0]+1
        jth = 0
        if longestPair[1].x <longestPair[2].x:
            jth = longestPair[0]
        else:
            jth = longestPair[0]+1

        if ith > jth:
            temp = ith
            ith = jth
            jth = temp

        vertexList1 = [] 
        vertexList2 = []
        if ith == 0:
            pass
        else:
            for i in range(ith,len(self.vertices)):
                if i >= ith and i <= jth:
                    vertexList1.append(self.vertices[i])

            for i in range(ith-1,-1,-1):
                vertexList2.append(self.vertices[i])
            for i in range(len(self.vertices)-1,jth,-1):
                vertexList2.append(self.vertices[i])

            # averaging all pair points 
            vertexList = []
            initV = vertexList1[0]
            for i in range(int(len(vertexList1)/2)):
                v1 = vertexList1[i]
                v2 = vertexList1[len(vertexList1)-1-i]
                vavg = Vertex2D(0,(v1.x+v2.x)/2,(v1.y+v2.y)/2,0)
                vertexList.append(vavg)
                if i == int(len(vertexList1)/2)-1:                    
                    initV = vavg

            vertexList.reverse()
            for i in range(int(len(vertexList2)/2)):
                v1 = vertexList2[i]
                v2 = vertexList2[len(vertexList2)-1-i]
                vavg = Vertex2D(0,(v1.x+v2.x)/2,(v1.y+v2.y)/2,0)
                vertexList.append(vavg)            
            vertexList.append(initV)
            edges = [] 
            for i in range(len(vertexList)-1):
                v1 = vertexList[i]
                v2 = vertexList[i+1]
                newEdge = Edges2D(0,[v1,v2])
                edges.append(newEdge)
            self.vertices = vertexList
            self.edges = edges




        

        

        



    

    