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

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.GC import GC_MakeArcOfCircle
from KooCAEManager.KooNode import NodeManager
from KooCAEManager.KooElement import ElementManager
from OCC.Core.GeomAPI import (
    GeomAPI_PointsToBSplineSurface
)
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeShell,
    BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_Sewing
)
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeTorus,
    BRepPrimAPI_MakeWedge,
    BRepPrimAPI_MakeRevol,
    BRepPrimAPI_MakeHalfSpace,
    BRepPrimAPI_MakeRevolution,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeSweep,
    BRepPrimAPI_MakeOneAxis
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


from OCC.Core.TopoDS import topods
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX

from OCC.Core.BRepFill import(
BRepFill_Filling,
BRepFill_CurveConstraint,
)
import OCC.Core.GeomAbs as GeomAbs
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.TColgp import TColgp_Array2OfPnt
import math

from OCC.Core.BRep import BRep_Tool

class KooGeomVertex:

    def __init__(self,id=0,pnt = gp_Pnt(0,0,0)):
        self.id = id # int
        self.vertex = BRepBuilderAPI_MakeVertex(pnt).Vertex() # TopoDS_Vertex
        self.pnt = pnt # gp_Pnt
        self.node = None # KooNode
        self.hide = False # bool
        pass

    def SetPnt(self,pnt):
        self.pnt = pnt
        return self.Update()
    
    def SetVertex(self, v : TopoDS_Vertex):
        self.vertex = v 
        self.pnt = BRep_Tool.Pnt(v)
        
    def Update(self):
        self.vertex = BRepBuilderAPI_MakeVertex(self.pnt).Vertex()
        return self.vertex

    def GenerateNode(self,nodeMan):
        self.node = nodeMan.CreateNode(self.pnt.X,self.pnt.Y,self.pnt.Z)

    

class KooGeomEdge:
    def __init__(self,id=0,edge=None):
        self.id = id 
        self.vertices = [] 
        self.nodes = [] 
        self.elements = [] 
        self.type = None
        self.edge = edge
        self.hide = False
        pass

    def SetEdge(self, edge : TopoDS_Edge, vertices = [], type = None):
        self.edge = edge
        self.vertices = vertices
        if type is not None:
            self.type = type
    
    def Update(self):
        pass

    def FindNodesinEdge(self,nodeMan,tol=1.0e-6):
        for node in nodeMan.nodes:
            v = BRepBuilderAPI_MakeVertex(node.pnt).Vertex()
            extrema = BRepExtrema_DistShapeShape(v,self.edge)
            extrema.Perform()
            distance = extrema.Value()
            if distance < tol:
                self.nodes.append(node)
        return self.nodes

    def FindElementsinEdge(self,elemMan,tol=1.0e-6):
        for elem in elemMan.elements:
            isInside = True
            for node in elem.nodes:
                v = BRepBuilderAPI_MakeVertex(node.pnt).Vertex()
                extrema = BRepExtrema_DistShapeShape(v,self.edge)
                extrema.Perform()
                distance = extrema.Value()
                if distance >tol:
                    isInside = False
                    break
            if isInside:
                self.elements.append(elem)
        return self.elements
    
    def GetNVertices(self, n = 10):
        curve_adaptor = BRepAdaptor_Curve(self.edge)        
        umin, umax = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()        
        du = (umax-umin)/(n-1.0)
        paramList = [] 
        for i in range(n):
            paramList.append(umin+i*du)
        pntList = []
        for param in paramList:
            pnt = curve_adaptor.Value(param)
            pntList.append(pnt)
        return pntList



class KooGeomLine(KooGeomEdge):
    def __init__(self,id=0,vertex1=None,vertex2=None):
        super(KooGeomLine,self).__init__(id)
        self.type = "Line"
        self.edge = None
        self.vertices = [vertex1,vertex2]
        self.hide = False
        if vertex1 != None and vertex2 != None:
            self.SetLine(vertex1,vertex2)
        pass

    def SetLine(self,vertex1,vertex2):
        self.vertices = [vertex1,vertex2]
        self.Update()
    
    def Update(self):
        v1,v2 = self.vertices
        self.edge = BRepBuilderAPI_MakeEdge(v1.vertex,v2.vertex).Edge()
        return self.edge

    def GenerateNLines(self,nodeMan,elemMan,N=1):
        if self.edge != None:
            nodeList = []  
            p1 = self.vertices[0].pnt
            p2 = self.vertices[1].pnt   
            for i in range(N+1):
                if i == 0:
                    nodeList.append(self.vertices[0].node)
                    continue
                if i == N:
                    nodeList.append(self.vertices[1].node)
                    continue
                x = p1.X + (p2.X-p1.X)*i/N
                y = p1.Y + (p2.Y-p1.Y)*i/N
                z = p1.Z + (p2.Z-p1.Z)*i/N
                nodeList.append(nodeMan.CreateNode(x,y,z))
            elemList = [] 
            for i in range(len(nodeList)-1):
                elemList.append(elemMan.CreateLineLinearElement("Line",nodeList[i],nodeList[i+1]))
            self.elements = elemList
            return elemList
        return None   

class KooGeomArc(KooGeomEdge):
    def __init__(self,id=0, vstart=None,vend=None,vcenter=None,counterclockwise=True):
        super(KooGeomArc,self).__init__(id)
        self.type = "Arc"
        self.edge = None
        self.radius = 0.0        
        self.hide = False

        self.counterclockwise = counterclockwise
        if vstart != None and vcenter != None and vend != None:
            self.SetArc(vstart,vend,vcenter)            


    def SetArc(self,vstart,vend,vcenter):
        self.vertices = [vstart,vend,vcenter]
        self.Update()

    def Update(self):
        vstart,vend,vcenter = self.vertices
        vec1 = gp_Vec(vcenter.pnt,vstart.pnt)
        vec2 = gp_Vec(vcenter.pnt,vend.pnt)
        vec1.Normalize()
        vec2.Normalize()
        normal_direction = vec1.Crossed(vec2)
        if normal_direction.Magnitude() < 1.0e-6:
            normal_direction = gp_Vec(0,0,1)
        if self.counterclockwise:
            normal_direction.Reverse()
        self.radius = vcenter.pnt.Distance(vstart.pnt)
        coord = gp_Ax2(vcenter.pnt,gp_Dir(normal_direction))
        circle = gp_Circ(coord,self.radius)

        arc = GC_MakeArcOfCircle(circle,vstart.pnt,vend.pnt,self.counterclockwise)

        self.edge = BRepBuilderAPI_MakeEdge(arc.Value()).Edge()
        return self.edge
 
    
    def GenerateNLines(self,nodeMan,elemMan,N=1):
        if self.edge != None:
            nodeList = [] 
            curve = BRepAdaptor_Curve(self.edge)
            umin, umax = curve.FirstParameter(), curve.LastParameter()
            du = (umax-umin)/N
            for i in range(N+1):
                u = umin + du*i
                pnt = curve.Value(u)
                nodeList.append(nodeMan.CreateNode(pnt.X(),pnt.Y(),pnt.Z()))
            
            elemList = []
            for i in range(len(nodeList)-1):
                elemList.append(elemMan.CreateLineLinearElement("Line",nodeList[i],nodeList[i+1]))
            self.elements = elemList
            return elemList
        return None
   
    '''
    def GetNVertices(self, num = 10):
        from OCC.Core.GCPnts import GCPnts_UniformAbscissa

        curve = BRepAdaptor_Curve(self.edge)
        length = curve.LastParameter() - curve.FirstParameter()
        arc_length = num - 1 if num > 1 else 1  # ensure at least one segment
        spacing = length / arc_length

        algo = GCPnts_UniformAbscissa(curve, spacing, curve.FirstParameter(), curve.LastParameter())
        
        if not algo.IsDone():
            raise Exception("Discretization of curve failed")

        points = [curve.Value(algo.Parameter(i)) for i in range(1, algo.NbPoints() + 1)]
        return points
    '''


class KooGeomCircle(KooGeomEdge):
    def __init__(self, id=0, vCenter : KooGeomVertex = None, vEnd : KooGeomVertex = None):
        super(KooGeomCircle,self).__init__(id)
        self.type = "Circle"
        self.edge = None        
        self.hide = False
        if vCenter != None and vEnd != None:
            self.radius = vCenter.pnt.Distance(vEnd.pnt)
            self.SetCircle(vCenter,vEnd)
            self.vertices = [vCenter,vEnd]        
        else:
            self.radius = 0.0

    def SetCircle(self,vCenter,vEnd):
        self.vertices = [vCenter,vEnd]
        self.Update()
    
    def Update(self):
        vCenter,vEnd = self.vertices
        vec1 = gp_Vec(vCenter.pnt,vEnd.pnt)
        vec1.Normalize()
        normal_direction = gp_Vec(0,0,1)
        if normal_direction.IsParallel(vec1,1.0e-6):
            normal_direction = gp_Vec(1,0,0)
        coord = gp_Ax2(vCenter.pnt,gp_Dir(normal_direction))
        circle = gp_Circ(coord,self.radius)
        self.edge = BRepBuilderAPI_MakeEdge(circle).Edge()
        return self.edge

class KooGeomWire:
    def __init__(self,id=0,edges=[]):
        self.id = id
        self.edges = []
        self.wire = None 
        self.type = None
        self.hide = False
        if len(edges) != 0:
            self.SetEdges(edges)        
       

    def AddEdge(self,edge):
        self.edges.append(edge)
    
    def SetEdges(self, geomLineList):
        self.edges = geomLineList
        self.Update()
    
    def SetWire(self, wire : TopoDS_Wire, edges = []):
        self.wire = wire
        self.edges = edges
    
    def Update(self):
        wire_builder = BRepBuilderAPI_MakeWire()
        for geomEdge in self.edges:
            wire_builder.Add(geomEdge.edge)
        wire_builder.Build()
        self.wire = wire_builder.Wire()
        return self.wire

    def AddEdges(self, geomListList):
        for edge in geomListList:
            self.edges.append(edge)
    
    def ClearEdges(self):
        self.edges = []

class KooGeomPolyline(KooGeomWire):

    def __init__(self, id = 0,vlist = None):
        super(KooGeomPolyline,self).__init__(id)
        self.type = "Polyline"
        self.edges = [] 
        self.vertices = vlist
        self.SetPolyLine(vlist)
        self.hide = False
        pass

    def SetPolyLine(self, vertexList):
        for i in range(1,len(vertexList)):
            if i == len(vertexList)-1:
                geomline = KooGeomLine(i,vertexList[i],vertexList[0])
            else:
                geomline = KooGeomLine(i,vertexList[i],vertexList[i+1])
            self.edges.append(geomline)
        return self.Update()
       

class KooGeomFace:
    def __init__(self, id=0, wires = []):
        self.id = id  
        self.wire = None
        self.face = None
        if len(wires) != 0:
            self.wire = wires[0]
        self.wires = []
        for i in range(1,len(wires)):
            self.wires.append(wires[i])
        self.type = None
        self.hide = False
        if self.wire != None:
            self.Update()
        
    def SetWire(self, wire):
        self.wire = wire
        return self.Update()

    def SetFace(self,face : TopoDS_Face, wires = []):
        self.face = face
        if len(wires)>0:
            self.wire = wires[0]
            self.wires = wires
    def Update(self):
        curwire = self.wire.wire
        face_builder = BRepBuilderAPI_MakeFace(curwire)
        for wire in self.wires:
            face_builder.Add(wire.wire)
        face_builder.Build()
        self.face = face_builder.Face()
        return self.face
    
class KooGeomCutFace(KooGeomFace):
    def __init__(self, id=0, baseFace = None, toolFace = None):
        super(KooGeomCutFace,self).__init__(id)
        self.type = "CutFace"
        self.baseFace = baseFace
        self.toolFace = toolFace
        self.face = None
        self.hide = False
        if baseFace != None and toolFace != None:
            self.Update()
    
    def SetBaseFace(self, baseFace):
        self.baseFace = baseFace
        return self.Update()

    def SetToolFace(self, toolFace):
        self.toolFace = toolFace
        return self.Update()
    
    def Update(self):
        baseFace = self.baseFace.face
        toolFace = self.toolFace.face
        cut = BRepAlgoAPI_Cut(baseFace,toolFace)
        cut.Build()
        if cut.HasErrors():
            return None
        result = cut.Shape()
        self.face = result
        
        '''
        # wires from the result
        explorer = TopExp_Explorer(result, TopAbs_WIRE)
        while explorer.More():
            wire = topods.Wire(explorer.Current())
            self.wires.append(KooGeomWire)            
            explorer.Next()
        '''

        return self.face


    


class KooGeomFillingFace(KooGeomFace):
    def __init__(self, id=0, wire = None, pnts = []):
        super(KooGeomFillingFace,self).__init__(id,wire)
        self.type = "FillingFace"
        self.face = None

        # Filling parameters
        self.Degree = 3
        self.NbPtsOnCur = 15
        self.NbIter = 2
        self.Anisotropie = False
        self.Tol2d = 0.00001
        self.Tol3d = 0.0001
        self.TolAng = 0.01
        self.TolCurv = 0.1
        self.MaxDeg = 8
        self.MaxSegments = 9
        if len(pnts) > 0:
            self.SetPnts()

        if wire != None:
            self.Update()

    def SetWire(self, wire):
        self.wire = wire
        return self.Update()

    def SetPnts(self, pnts):
        self.pnts = pnts

    def Update(self):
        filling = BRepFill_Filling(self.Degree,self.NbPtsOnCur,self.NbIter,self.Anisotropie,self.Tol2d,self.Tol3d,self.TolAng,self.TolCurv,self.MaxDeg,self.MaxSegments)
        for edge in self.wire.edges:
            filling.Add(edge.edge,GeomAbs.GeomAbs_C0)
        for pnt in self.pnts:
            filling.Add(pnt)
        filling.Build()
        surface = filling.Face()
        while surface.IsNull():
            self.Tol2d *=1.5
            self.Tol3d *=1.5
            filling = BRepFill_Filling(self.Degree,self.NbPtsOnCur,self.NbIter,self.Anisotropie,self.Tol2d,self.Tol3d,self.TolAng,self.TolCurv,self.MaxDeg,self.MaxSegments)
            for edge in self.wire.edges:
                filling.Add(edge.edge,GeomAbs.GeomAbs_C0)
            filling.Build()
            surface = filling.Face()
        self.face = surface
        return surface
            
class KooGeomBSplineFace(KooGeomFace):
    def __init__(self,id=0,pointsMatrix = None):
        super(KooGeomBSplineFace,self).__init__(id)
        self.type = "BSplineFace"
        self.pointsMatrix = pointsMatrix
        self.face = None
        # B Spline Surface Option 
        self.DegMin = 3
        self.DegMax = 8
        self.Continuity = GeomAbs.GeomAbs_C2
        self.Tol3D = 0.001
        self.TolSurfacetoFace = 0.000001
    
    def SetFacefrom2DPoints(self, pointsMatrix):
        self.pointsMatrix = pointsMatrix
        return self.Update()
    
    def Update(self):
        pointsMatrix = self.pointsMatrix
        control_points = TColgp_Array2OfPnt(1,len(pointsMatrix),1,len(pointsMatrix[0]))
        for i in range(len(pointsMatrix)):
            for j in range(len(pointsMatrix[0])):
                control_points.SetValue(i+1,j+1,pointsMatrix[i][j])
        surface_builder = GeomAPI_PointsToBSplineSurface(control_points,self.DegMin,self.DegMax,self.Continuity,self.Tol3D)
        while surface_builder.IsDone() == False:
            self.Tol3D *= 1.5
            surface_builder = GeomAPI_PointsToBSplineSurface(control_points,self.DegMin,self.DegMax,self.Continuity,self.Tol3D)
        surface = surface_builder.Surface()
        face_builder = BRepBuilderAPI_MakeFace(surface,self.TolSurfacetoFace)
        face_builder.Build()
        while face_builder.IsDone() == False:
            self.TolSurfacetoFace *= 1.5
            face_builder = BRepBuilderAPI_MakeFace(surface,self.TolSurfacetoFace)
            face_builder.Build()

        self.face = face_builder.Face()

        return self.face


class KooGeomShell:
    def __init__(self, id=0, faces=[]):
        self.id = id 
        self.shell = None
        self.faces = faces
        self.type = None
        self.hide = False
        if len(self.faces) > 0:
            self.shell = self.Update()
        
    def AddFace(self, face):
        self.faces.append(face)
    
    def SetFaces(self, faceList):
        self.faces = faceList
        return self.Update()
    
    def SetShell(self, shell : TopoDS_Shell,faces = []):
        self.shell = shell 
        self.faces = faces
    
    def Update(self):
        sewing = BRepBuilderAPI_Sewing()
        for face in self.faces:
            sewing.Add(face.face)
        sewing.Perform()
        shell = sewing.SewedShape()
        self.shell = shell
        return shell

        #face_builder = BRepBuilderAPI_MakeShell()
        #for face in self.faces:
        #    face_builder.Add(face.face)
        #face_builder.Build()
        #self.shell = face_builder.Shell()
        #return self.shell
    
    def AddFaces(self, faceList):
        for face in faceList:
            self.faces.append(face)
    
    def ClearEdges(self):
        self.faces = [] 

class KooGeomSolid:
    def __init__(self, id=0, shell = None):
        self.id = id
        self.solid = None
        self.shell = shell
        self.type = None
        self.hide = False
    
    def SetShell(self, shell):
        self.shell = shell
        return self.Update()
    
    def SetSolid(self, solid :TopoDS_Solid, shell = None):
        self.solid = solid 
        self.shells = shell
    
    def Update(self):
        self.solid = BRepBuilderAPI_MakeSolid(self.shell.shell).Solid()
        return self.solid

class KooGeomPrism(KooGeomSolid):
    def __init__(self, id=0, baseGeomFace = None, direction = gp_Vec(0,0,1), thickness = 1.0):
        super(KooGeomPrism,self).__init__(id)
        self.type = "Prism"
        self.baseGeomFace = baseGeomFace
        self.thickness = thickness 
        self.direction = direction.Multiplied(thickness)
        self.solid = None
        self.hide = False
        
    def SetBaseFace(self, geomFace):
        self.baseGeomFace = geomFace
        return self.baseGeomFace
    
    def SetDirection(self, x, y, z):
        self.direction = gp_Vec(x,y,z)
        return self.direction
    
    def SetDirectionbyTwoPoint(self,x1,y1,z1,x2,y2,z2):
        self.direction = gp_Vec(x2-x1,y2-y1,z2-z1)
        return self.direction
    
    def Update(self):
        face = self.baseGeomFace.face
        direction = self.direction
        shape_builder = BRepPrimAPI_MakePrism(face,direction)
        shape_builder.Build()
        self.solid = shape_builder.Shape()
        return self.solid    

class KooGeomTextureBox():
    def __init__(self, id, textureImagePath,xPos,yPos,zPos, width, height, depth):
        self.id = id
        self.textureImagePath = textureImagePath
        self.xPos = xPos
        self.yPos = yPos
        self.zPos = zPos        
        self.width = width
        self.height = height
        self.depth = depth
        self.solid = None
        self.hide = False
    
    def Update(self):
        pnt : gp_Pnt = gp_Pnt(self.xPos,self.yPos,self.zPos)
        box = BRepPrimAPI_MakeBox(pnt,self.width,self.height,self.depth)
        self.solid = box.Shape()
        return self.solid



