import os
import math
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
## QT Viewer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()
from OCC.Display.qtDisplay import qtViewer3d

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM

from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Check

from KooCAEManager.KooGeometry import (
    KooGeomVertex,
)
from KooCAEManager.KooAISGeometry import (
    KooAISGeomVertex,
    KooAISGeomEdge,
    KooAISGeomLine,
    KooAISGeomArc,
    KooAISGeomCircle,
    KooAISGeomWire,
    KooAISGeomFace,
    KooAISGeomCutFace,
    KooAISGeomShell,
    KooAISGeomSolid,
    KooAISGeomTextureBox    
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

from OCC.Core.TopExp import TopExp_Explorer

from OCC.Core.TopAbs import(
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_SOLID,
    TopAbs_SHELL,
    TopAbs_FACE,
    TopAbs_WIRE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
) 
from OCC.Core.GeomAbs import(    
    GeomAbs_Line,
    GeomAbs_Arc,
    GeomAbs_Circle,
    GeomAbs_BezierCurve,
    GeomAbs_BSplineCurve,    
) 

from OCC.Core.BRepAdaptor import BRepAdaptor_Curve

from OCC.Core.BRep import BRep_Tool

from KooCAEManager.KooGeometryManager import KooGeometryManager
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_Reader
from OCC.Core.STEPControl import STEPControl_AsIs

from OCC.Core.BRepLProp import BRepLProp_CLProps
from OCC.Core.BRepTools import breptools_UVBounds
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

class KooViewer(qtViewer3d):
    def __init__(self,parent=None):
        super(KooViewer,self).__init__(parent)
    

class KooAISGeometryManager(KooGeometryManager):
    def __init__(self,parent = None, viewer = None):
        super(KooAISGeometryManager,self).__init__()

        self.parent = parent
        if viewer == None:
            self.viewer = KooViewer(parent)
        else:
            self.viewer = viewer

    def SetViewer(self, viewer):
        self.viewer = viewer
    
    def CreateVertex(self,x,y,z):
        pnt = gp_Pnt(x,y,z)
        vertex = KooAISGeomVertex(0,pnt)
        return self.AddVertex(vertex)
    
    def AddVertex(self, v : KooAISGeomVertex):
        self.maxvertexid += 1
        v.id = self.maxvertexid
        self.vertices[self.maxvertexid] = v
        return v
    
    def AddVertexbyShape(self, vShape : TopoDS_Vertex):
        self.maxvertexid += 1
        v = KooAISGeomVertex(self.maxvertexid)
        v.SetVertex(vShape)
        return v
    
    def FindVertex(self,x,y,z,tol=1.e-6):
        for vertex in self.vertices.values():
            if vertex.pnt.Distance(gp_Pnt(x,y,z)) < tol:
                return vertex
        return self.CreateVertex(x,y,z)
    
    def FindVertexShape(self, v : TopoDS_Vertex,tol=1.e-6):
        p = BRep_Tool.Pnt(v)
        for vertex in self.vertices.values():
            if vertex.pnt.Distance(p) < tol:
                return vertex
        return self.AddVertexbyShape(v)
    
    def RemoveVertex(self,vertex, update = True):
        if vertex.id in self.vertices:
            if update == True:            
                self.vertices[vertex.id].Erase(self.viewer)
            del self.vertices[vertex.id]        

    def RemoveVertexbyID(self, vertexid, update = True):
        if vertexid in self.vertices:
            if update == True:            
                self.vertices[vertexid].Erase(self.viewer)
            del self.vertices[vertexid]                
    
    def AddEdge(self, e : KooAISGeomEdge):
        self.maxedgeid += 1
        e.id = self.maxedgeid
        self.edges[self.maxedgeid] = e
        return e
    
    def AddEdgebyShape(self, eShape : TopoDS_Edge, vList = []):
        self.maxedgeid += 1
        curve = BRepAdaptor_Curve(eShape)
        curve_type = curve.GetType()
        if len(vList) > 0:
            e = KooAISGeomEdge(self.maxedgeid)
            e.SetEdge(eShape, vList)
        elif curve_type == GeomAbs_Line:
            p1, p2 = self.GetVertexFromLine(eShape)
            v1 = self.CreateVertex(p1.X(),p1.Y(),p1.Z())
            v2 = self.CreateVertex(p2.X(),p2.Y(),p2.Z())
            e = KooAISGeomLine(self.maxedgeid, v1, v2)
        elif curve_type == GeomAbs_Circle:
            p1, p12, p2, pc = self.GetVertexFromCircle(eShape)
            if p1.Distance(p2) < 1.e-6:
                vc = self.CreateVertex(pc.X(),pc.Y(),pc.Z())
                ve = self.CreateVertex(p1.X(),p1.Y(),p1.Z())
                e = KooAISGeomCircle(self.maxedgeid, vc, ve)
            else:              
                # get p1, p12, p2 is counterclockwise or clockwise                
                px = gp_Pnt(pc.X()+1,pc.Y(),pc.Z())
                pz = gp_Pnt(pc.X(),pc.Y(),pc.Z()+1)
                #angle from x axis, in terms of 0 to 2pi                
                angle1 = gp_Vec(pc,p1).AngleWithRef(gp_Vec(pc,p12),gp_Vec(pc,pz))
                angle2 = gp_Vec(pc,p1).AngleWithRef(gp_Vec(pc,p2),gp_Vec(pc,pz))
                reversed = False
                if angle2*angle1 < 0:
                    reversed = True
                
                angle3 = angle2 - angle1 
                if angle3 < 0:
                    angle3 = 2*math.pi + angle3
                if angle3 > math.pi:
                    counterclockwise = True
                else:
                    counterclockwise = False
                '''if angle2 < 0:
                    counterclockwise = False
                else:
                    counterclockwise = True'''
                
                if reversed:
                    counterclockwise = not counterclockwise

                '''
                if angle1 < 0:
                    angle1 = 2*math.pi + angle1
                if angle2 < 0:
                    angle2 = 2*math.pi + angle2
                if angle12 < 0:
                    angle12 = 2*math.pi + angle12

                delAngle1to2 = angle2 - angle1
                delAngle1to12 = angle12 - angle1

                if delAngle1to2> 0 and delAngle1to12 > 0:
                    if abs(delAngle1to2) < abs(delAngle1to12):
                        counterclockwise = False
                    else:
                        counterclockwise = True
                elif delAngle1to2 < 0 and delAngle1to12 < 0:
                    if abs(delAngle1to2) < abs(delAngle1to12):
                        counterclockwise = True
                    else:
                        counterclockwise = False
                elif delAngle1to2 > 0 and delAngle1to12 < 0:
                    counterclockwise = False
                elif delAngle1to2 < 0 and delAngle1to12 > 0:
                    counterclockwise = False
                
                '''    

                '''
                angle1 = gp_Vec(pc,px).AngleWithRef(gp_Vec(pc,p1),gp_Vec(pc,p12))
                
                if angle1 > math.pi:
                    counterclockwise = True
                else:
                    counterclockwise = False
                '''
                v1 = self.CreateVertex(p1.X(),p1.Y(),p1.Z())
                v2 = self.CreateVertex(p2.X(),p2.Y(),p2.Z())
                vc = self.CreateVertex(pc.X(),pc.Y(),pc.Z())
                e = KooAISGeomArc(self.maxedgeid, v1, v2, vc, counterclockwise)
        else:
            e = None        
        self.edges[self.maxedgeid] = e
        return e
    
    def GetVertexFromLine(self, edge):
        if not isinstance(edge, TopoDS_Edge):
            return "Not an edge"
        
        curve_adaptor = BRepAdaptor_Curve(edge)
        if curve_adaptor.GetType() != GeomAbs_Line:
            return "Not a line"
        # if it is a line,         

        # Use a curve properties tool to get curve details at a mid parameter
        first, last = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()
        
        #mid_param = (first + last) / 2.0
        #curve_props = BRepLProp_CLProps(curve_adaptor, mid_param, 1, 1e-9)

        # pnt from first and last parameter
        pnt1 = curve_adaptor.Value(first)
        pnt2 = curve_adaptor.Value(last)
        
        print("First Point : ", pnt1.X(), pnt1.Y(), pnt1.Z())
        print("Last Point : ", pnt2.X(), pnt2.Y(), pnt2.Z())
        
        return pnt1, pnt2
        
    def GetVertexFromCircle(self,edge):
        
        if not isinstance(edge, TopoDS_Edge):
            return "Not an edge"
        
        curve_adaptor = BRepAdaptor_Curve(edge)
        if curve_adaptor.GetType() != GeomAbs_Circle:
            return "Not a circular arc"
        # if it is a circle not an arc,         

        # Use a curve properties tool to get curve details at a mid parameter
        first, last = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()
        
        center = (first + last) / 2.0      
        #mid_param = (first + last) / 2.0
        #curve_props = BRepLProp_CLProps(curve_adaptor, mid_param, 1, 1e-9)

        # pnt from first and last parameter
        pnt1 = curve_adaptor.Value(first)
        pnt12 = curve_adaptor.Value(center)
        pnt2 = curve_adaptor.Value(last)

        print("First Point : ", pnt1.X(), pnt1.Y(), pnt1.Z())
        print("Second Point : ", pnt12.X(), pnt12.Y(), pnt12.Z())
        print("Last Point : ", pnt2.X(), pnt2.Y(), pnt2.Z())

        # get center point of circle
        pntCenter = curve_adaptor.Circle().Location()
        print("Center Point : ", pntCenter.X(), pntCenter.Y(), pntCenter.Z())
        
        return pnt1, pnt12, pnt2, pntCenter
    
    def GetNVerticesfromEdge(self, edge, n = 10):
        if not isinstance(edge, TopoDS_Edge):
            return "Not an edge"
        
        curve_adaptor = BRepAdaptor_Curve(edge)

        # Use a curve properties tool to get curve details at a mid parameter
        first, last = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()
        
        paramList = [] 
        for i in range(n):
            param = first + (last - first) / (n-1) * i
            paramList.append(param)

        pntList = [] 
        for param in paramList:
            pnt = curve_adaptor.Value(param)
            pntList.append(pnt)
        return pntList        

    def RemoveEdge(self, edge : KooAISGeomEdge, update = True):
        if edge.id in self.edges:
            if update == True:            
                self.edges[edge.id].Erase(self.viewer)
            del self.edges[edge.id]

    def RemoveEdgebyID(self, edgeid, update = True):
        if edgeid in self.edges:
            if update == True:            
                self.edges[edgeid].Erase(self.viewer)
            del self.edges[edgeid]
    
    def CreateEdge(self, e):
        self.maxedgeid += 1
        edge = KooAISGeomEdge(self.maxedgeid, e)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def CreateLinefromVertices(self, v1, v2):
        self.maxedgeid += 1
        edge = KooAISGeomLine(self.maxedgeid, v1, v2)
        self.edges[self.maxedgeid] = edge
        #print("Create Line from Vertices")
        #print(edge)
        #print(self.edges)
        return edge
    
    def FindLinefromVertices(self, v1, v2):
        for edge in self.edges.values():
            if edge.type == "Line":
                if edge.vertices[0].id == v1.id and edge.vertices[1].id == v2.id:
                    return edge
                elif edge.vertices[0].id == v2.id and edge.vertices[1].id == v1.id:
                    return edge
        return self.CreateLinefromVertices(v1,v2)

    def CreateArcfromVertices(self, vstart, vend, vcenter, counterclockwise):
        self.maxedgeid += 1
        edge = KooAISGeomArc(self.maxedgeid, vstart, vend, vcenter, counterclockwise)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def FindArcfromVertices(self, vstart, vend, vcenter, counterclockwise):
        for edge in self.edges.values():
            if edge.type == "Arc":
                if edge.vertices[0].id == vstart.id and edge.vertices[1].id == vend.id and edge.vertices[2].id == vcenter.id and edge.counterclockwise == counterclockwise:
                    return edge
                elif edge.vertices[0].id == vend.id and edge.vertices[1].id == vstart.id and edge.vertices[2].id == vcenter.id and edge.counterclockwise == counterclockwise:
                    return edge
        return self.CreateArcfromVertices(vstart, vend, vcenter, counterclockwise)

    def CreateCirclefromVertices(self, vCenter, vEnd):
        self.maxedgeid += 1
        edge = KooAISGeomCircle(self.maxedgeid, vCenter, vEnd)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def FindCirclefromVertices(self, vCenter, vEnd):
        for edge in self.edges.values():
            if edge.type == "Circle":
                if edge.vertices[0].id == vCenter.id and edge.vertices[1].id == vEnd.id:
                    return edge
                elif edge.vertices[0].id == vEnd.id and edge.vertices[1].id == vCenter.id:
                    return edge
        return self.CreateCirclefromVertices(vCenter, vEnd)
    
    def FindEdgeShape(self, e : TopoDS_Edge, vList = []):
        for edge in self.edges.values():
            if edge.edge.IsSame(e):
                return edge
        return self.AddEdgebyShape(e,vList)

    def CreateWirefromEdges(self, edges):
        self.maxwireid += 1
        wire = KooAISGeomWire(self.maxwireid, edges)
        self.wires[self.maxwireid] = wire
        return wire 
    
    def AddWirebyShape(self, w : TopoDS_Wire, edges = []):
        self.maxwireid += 1
        wire = KooAISGeomWire(self.maxwireid)
        wire.SetWire(w,edges)
        self.wires[self.maxwireid] = wire
        return wire 

    def RemoveWire(self, wire : KooAISGeomWire, update = True):
        if wire.id in self.wires:
            if update == True:            
                self.wires[wire.id].Erase(self.viewer)
            del self.wires[wire.id]

    def RemoveWirebyID(self, wireid, update = True):
        if wireid in self.wires:
            if update == True:            
                self.wires[wireid].Erase(self.viewer)
            del self.wires[wireid]
    
    def FindWirefromEdges(self, edges):
        for wire in self.wires.values():
            if len(wire.edges) != len(edges):
                continue
            isSame = True
            for i in range(len(wire.edges)):
                if wire.edges[i].id != edges[i].id:
                    isSame = False
                    break
            if isSame:
                return wire
        return self.CreateWirefromEdges(edges)
    
    def FindWireShape(self, w : TopoDS_Wire, edges = []):
        for wire in self.wires.values():
            if wire.wire.IsSame(w):
                return wire
        return self.AddWirebyShape(w,edges)
    
    '''
    def CreatePollinefromVertices(self, vertices):
        self.maxwireid += 1
        wire = KooAISGeomPolyline(self.maxwireid, vertices)
        self.wires[self.maxwireid] = wire
        for edge in wire.edges:
            self.AddEdge(edge)
    '''

    def CreateFacefromWire(self, wire):
        self.maxfaceid += 1
        wires = [wire]
        face = KooAISGeomFace(self.maxfaceid, wires)
        face.SetColorbyID()
        self.faces[self.maxfaceid] = face
        return face
    
    def CreateFacefromWires(self, wires):
        self.maxfaceid += 1
        face = KooAISGeomFace(self.maxfaceid, wires)
        face.SetColorbyID()
        self.faces[self.maxfaceid] = face
        return face
    
    def AddFace(self, f : KooAISGeomFace):
        self.maxfaceid += 1
        f.id = self.maxfaceid
        f.SetColorbyID()

        self.faces[self.maxfaceid] = f
        
        return f
    
    def AddFacebyShape(self, f : TopoDS_Face, wires = []):
        self.maxfaceid += 1
        face = KooAISGeomFace(self.maxfaceid)
        face.SetFace(f,wires)
        self.faces[self.maxfaceid] = face
        return face
        
    def RemoveFace(self, face : KooAISGeomFace, update = True):
        if face.id in self.faces:
            if update == True:            
                self.faces[face.id].Erase(self.viewer)
            del self.faces[face.id]

    def HideFacebyID(self, faceid, update = True):
        if faceid in self.faces:
            if update == True:            
                self.faces[faceid].SetHide(self.viewer,True,update)

    def RemoveFacebyID(self, faceid, update = True):
        if faceid in self.faces:
            if update == True:            
                self.faces[faceid].Erase(self.viewer)
            del self.faces[faceid]

    def RemoveFacewithSubGeometries(self, face : KooAISGeomFace):
        for wire in face.wires:
            for edge in wire.edges:
                for vertex in edge.vertices:
                    self.RemoveVertex(vertex)
                self.RemoveEdge(edge)
            self.RemoveWire(wire)
        
        if face.wire is not None:
            wire = face.wire
            for edge in wire.edges:
                for vertex in edge.vertices:
                    self.RemoveVertex(vertex)
                self.RemoveEdge(edge)
            self.RemoveWire(wire)
        self.RemoveFace(face)

    
    def FindFace(self, s: TopoDS_Face):
        for face in self.faces.values():   
            if type(face.face) == TopoDS_Face:      
                if s.IsPartner(face.trShape):
                    return face
            elif type(face.face) == TopoDS_Compound:
                topexp = TopExp_Explorer(face.face,TopAbs_FACE)
                while topexp.More():
                    if s.IsPartner(topexp.Current()):
                        return face
                    topexp.Next()            
        return None
    
    
    def FindFacefromWire(self, wire):
        for face in self.faces.values():
            if face.wire.id == wire.id:
                return face
        return self.CreateFacefromWire(wire)        
    
    def FindFaceShape(self, f : TopoDS_Face, wires = []):
        for face in self.faces.values():
            if face.face.IsSame(f):
                return face
        return self.AddFacebyShape(f,wires)
    
    ### Cut Face
    def CreateCutFace(self, baseFace, toolFace):
        self.maxfaceid += 1
        face = KooAISGeomCutFace(self.maxfaceid, baseFace, toolFace)
        face.SetColorbyID()
        self.CreateSubGeometriesforFace(face)
        self.faces[self.maxfaceid] = face
        return face
    
    def CreateSubGeometriesforFace(self, face):
        topodsFace = face.face
        wire_explorer = TopExp_Explorer(topodsFace,TopAbs_WIRE)
        wires = []
        while wire_explorer.More():
            wire = wire_explorer.Current()
            edge_explorer = TopExp_Explorer(wire,TopAbs_EDGE)
            edges = []
            while edge_explorer.More():
                edge = edge_explorer.Current()
                '''vList = []
                vertex_explorer = TopExp_Explorer(edge,TopAbs_VERTEX)
                while vertex_explorer.More():
                    vertex = vertex_explorer.Current()
                    vList.append(self.FindVertexShape(vertex))
                    vertex_explorer.Next()'''
                # distinguish whether edge is circle or arc or line                                                  
                edges.append(edge)
                edge_explorer.Next()            
            edgesTopods = self.RearrangeEdges(edges)
            edges = []
            for edge in edgesTopods:                
                curEdge = self.AddEdgebyShape(edge)
                edges.append(curEdge)                
                curEdge.Display(self.viewer)
                

            wires.append(self.AddWirebyShape(wire,edges))
            wire_explorer.Next()
        for wire in wires:
            wire.Display(self.viewer)
        face.wires = wires        
    ### Shell 

    def RearrangeEdges(self, topodsedges):
        if len(topodsedges) == 0:
            return None
        edges = []
        edge = topodsedges[0]
        curve_adaptor = BRepAdaptor_Curve(edge)
        first, last = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()
        pnt1 = curve_adaptor.Value(first)
        pnt2 = curve_adaptor.Value(last)

        edges.append(edge)
        topodsedges.remove(edge)
        
        while len(topodsedges) > 0:
            for i in range(len(topodsedges)):
                edge = topodsedges[i]
                curve_adaptor = BRepAdaptor_Curve(edge)
                first, last = curve_adaptor.FirstParameter(), curve_adaptor.LastParameter()
                pnt3 = curve_adaptor.Value(first)
                pnt4 = curve_adaptor.Value(last)
                if pnt2.Distance(pnt3) < 1.e-6:
                    edges.append(edge)
                    topodsedges.remove(edge)
                    pnt2 = pnt4
                    break
                elif pnt2.Distance(pnt4) < 1.e-6:
                    #change direction 
                    edges.append(edge.Reversed())                   
                    topodsedges.remove(edge)
                    pnt2 = pnt3
                    break

        return edges

    def CreateShellfromFaces(self, faces):
        self.maxshellid += 1
        shell = KooAISGeomShell(self.maxshellid, faces)
        self.shells[self.maxshellid] = shell
        return shell
    
    def AddShellbyShape(self, s : TopoDS_Shell, faces = []):
        self.maxshellid += 1
        shell = KooAISGeomShell(self.maxshellid)
        shell.SetShell(s,faces)
        self.shells[self.maxshellid] = shell
        return shell

    def RemoveShell(self, shell : KooAISGeomShell, update = True):
        if shell.id in self.shells:
            if update == True:            
                self.shells[shell.id].Erase(self.viewer)
            del self.shells[shell.id]
    
    def RemoveShellbyID(self, shellid, update = True):
        if shellid in self.shells:
            if update == True:            
                self.shells[shellid].Erase(self.viewer)
            del self.shells[shellid]
    
    def FindShellShape(self, s : TopoDS_Shell, faces = []):
        for shell in self.shells.values():
            if s.IsSame(shell.shell):
                return shell
        return self.AddShellbyShape(s,faces)
    
    def CreateSolidfromShell(self, shell):
        self.maxsolidid += 1
        solid = KooAISGeomSolid(self.maxsolidid, shell)
        self.solids[self.maxsolidid] = solid
        return solid
    
    def AddSolidbyShape(self, s : TopoDS_Solid, shell = None):
        self.maxsolidid += 1
        solid = KooAISGeomSolid(self.maxsolidid)        
        solid.SetSolid(s,shell)
        
        self.solids[self.maxsolidid] = solid
        return solid
    
    def RemoveSolid(self, solid : KooAISGeomSolid, update = True):
        if solid.id in self.solids:
            if update == True:            
                self.solids[solid.id].Erase(self.viewer)
            del self.solids[solid.id]
    
    def HideSolidbyID(self, solidid, update = True):
        if solidid in self.solids:
            if update == True:
            #Erase if exists            
                self.solids[solidid].SetHide(self.viewer,True,update)

    def RemoveSolidbyID(self, solidid, update = True):
        if solidid in self.solids:
            if update == True:
            #Erase if exists            
                self.solids[solidid].Erase(self.viewer)
            del self.solids[solidid]

    def FindSolid(self, s: TopoDS_Solid):
        for solid in self.solids.values():            
            #check = BRepAlgoAPI_Check(solid.solid,s)
            #if check:
            #    return solid        
            if s.IsPartner(solid.trShape):
            #if s.IsSame(solid.trShape):
                return solid
            


        return None
    
    def FindSolidShape(self, s : TopoDS_Solid, shell = None):
        for solid in self.solids.values():
            if s.IsSame(solid.solid):
                return solid
        return self.AddSolidbyShape(s,shell)
    
    def FindCompound(self, s : TopoDS_Compound):
        for face in self.faces.values():
            if s.IsPartner(face.trShape):
                return face
        for solid in self.solids.values():
            if s.IsPartner(solid.trShape):
                return solid
        return None

    def CreateTextureBox(self, texture, x, y, z, dx, dy, dz):
        self.maxtextureboxid += 1
        texturebox = KooAISGeomTextureBox(self.maxtextureboxid, texture, x, y, z, dx, dy, dz)
        if texturebox.texture == None:
            return None
        
        texturebox.Update()
        self.textureboxes[self.maxtextureboxid] = texturebox
        return texturebox

    def AddTextureBox(self, t : KooAISGeomTextureBox):
        self.maxtextureboxid += 1
        t.id = self.maxtextureboxid
        self.textureboxes[self.maxtextureboxid] = t
        return t

    def RemoveTextureBox(self, texturebox : KooAISGeomTextureBox, update = True):
        if texturebox.id in self.textureboxes:
            if update == True:            
                self.textureboxes[texturebox.id].Erase(self.viewer)
            del self.textureboxes[texturebox.id]
        
    def HideTextureBoxbyID(self, textureboxid, update = True):
        if textureboxid in self.textureboxes:
            if update == True:            
                self.textureboxes[textureboxid].SetHide(self.viewer,True,update)
    
    def RemoveTextureBoxbyID(self, textureboxid, update = True):
        if textureboxid in self.textureboxes:
            if update == True:            
                self.textureboxes[textureboxid].Erase(self.viewer)
            del self.textureboxes[textureboxid]
    
    def SetParentWindow(self, parent):
        self.viewer = KooViewer(parent)

    def Display(self, update = False, trsf : gp_Trsf = None):
        print("Number of Vertices : ", len(self.vertices))
        print("Number of Edges : ", len(self.edges))
        print("Number of Wires : ", len(self.wires))
        print("Number of Faces : ", len(self.faces))
        print("Number of Shells : ", len(self.shells))
        print("Number of Solids : ", len(self.solids))
        self.DisplayVertex(update,trsf)        
        self.DisplayEdge(update,trsf)
        self.DisplayWire(update,trsf)
        self.DisplayFace(update,trsf)
        self.DisplayShell(update,trsf)
        self.DisplaySolid(update,trsf)
        self.DisplayTextureBox(update,trsf)
    
    def DisplayVertex(self,update=False, trsf : gp_Trsf = None):
        for i in self.vertices:
            self.vertices[i].Display(self.viewer,update,trsf)
        
    def DisplayEdge(self,update=False, trsf : gp_Trsf = None):
        for i in self.edges:
            self.edges[i].Display(self.viewer,update,trsf)
    
    def DisplayWire(self,update=False, trsf : gp_Trsf = None):
        for i in self.wires:
            self.wires[i].Display(self.viewer,update,trsf)

    def DisplayFace(self,update=False, trsf : gp_Trsf = None):
        for i in self.faces:
            self.faces[i].Display(self.viewer,update,trsf)

    def DisplayShell(self,update=False, trsf : gp_Trsf = None):
        for i in self.shells:
            self.shells[i].Display(self.viewer,update,trsf)

    def DisplaySolid(self,update=False, trsf : gp_Trsf = None):
        for i in self.solids:
            self.solids[i].Display(self.viewer,update,trsf)            
    
    def DisplayTextureBox(self,update=False, trsf : gp_Trsf = None):
        for i in self.textureboxes:
            self.textureboxes[i].Display(self.viewer,update,trsf)

    def SetTransparencyAll(self, transparency):
        for i in self.vertices:
            self.vertices[i].SetTransparency(transparency)
        for i in self.edges:
            self.edges[i].SetTransparency(transparency)
        for i in self.wires:
            self.wires[i].SetTransparency(transparency)
        for i in self.faces:
            self.faces[i].SetTransparency(transparency)
        for i in self.shells:
            self.shells[i].SetTransparency(transparency)
        for i in self.solids:
            self.solids[i].SetTransparency(transparency)
        for i in self.textureboxes:
            self.textureboxes[i].SetTransparency(transparency)
            

    
    def RemoveAll(self):
        self.EraseAll()
        super().RemoveAll()

    def RemoveGeometry(self, topoShape):
        if type(topoShape) == TopoDS_Solid:
            solid = self.FindSolidShape(topoShape)
            self.RemoveSolid(solid)
        elif type(topoShape) == TopoDS_Shell:
            shell = self.FindShellShape(topoShape)
            self.RemoveShell(shell)
        elif type(topoShape) == TopoDS_Face:
            face = self.FindFaceShape(topoShape)
            self.RemoveFace(face)
        elif type(topoShape) == TopoDS_Wire:
            wire = self.FindWireShape(topoShape)
            self.RemoveWire(wire)
        elif type(topoShape) == TopoDS_Edge:
            edge = self.FindEdgeShape(topoShape)
            self.RemoveEdge(edge)
        elif type(topoShape) == TopoDS_Vertex:
            vertex = self.FindVertexShape(topoShape)
            self.RemoveVertex(vertex)
        else:
            pass
        

    def EraseAll(self):
        self.EraseVertex()
        self.EraseEdge()
        self.EraseWire()
        self.EraseFace()
        self.EraseShell()
        self.EraseSolid()
        self.EraseTextureBox()
    
    def EraseVertex(self):
        for i in self.vertices:
            self.vertices[i].Erase(self.viewer)
    
    def EraseEdge(self):
        for i in self.edges:
            self.edges[i].Erase(self.viewer)

    def EraseWire(self):
        for i in self.wires:
            self.wires[i].Erase(self.viewer)
    
    def EraseFace(self):
        for i in self.faces:
            self.faces[i].Erase(self.viewer)
    
    def EraseShell(self):
        for i in self.shells:
            self.shells[i].Erase(self.viewer)
    
    def EraseSolid(self):
        for i in self.solids:
            self.solids[i].Erase(self.viewer)
    
    def EraseTextureBox(self):
        for i in self.textureboxes:
            self.textureboxes[i].Erase(self.viewer)


    def CreateGeometryfromShape(self, shape):
        vertexList = self.FindTopoDSVertices(shape)
        aisGeomVertexList = [] 
        aisGeomEdgeList = [] 
        aisGeomWireList = []
        aisGeomFaceList = []
        aisGeomShellList = []
        aisGeomSolidList = []
        numobjects = 0
        print("Create Geometry from Shape")
        for v in vertexList:
            aisGeomVertex = self.FindVertexShape(v)
            aisGeomVertexList.append(aisGeomVertex)
            numobjects += 1
        print("Find Vertex Shape Done :",numobjects)
        if shape.ShapeType() == TopAbs_EDGE:
            edge = self.FindEdgeShape()
            return edge
        else:
            numobjects = 0 
            edgeList = self.FindTopoDSEdges(shape)
            for edge in edgeList:
                vListinEdge = self.FindTopoDSVertices(edge)
                curAISGeomVList = [] 
                for v in vListinEdge:
                    for aisGeomVertex in aisGeomVertexList:
                        if aisGeomVertex.vertex.IsSame(v):
                            curAISGeomVList.append(aisGeomVertex)
                numobjects += 1
                aisGeomEdge = self.FindEdgeShape(edge,curAISGeomVList)
                aisGeomEdgeList.append(aisGeomEdge)
        print("Find Edge Shape Done:",numobjects)
        if shape.ShapeType() == TopAbs_WIRE:
            wire = self.FindWireShape(shape,aisGeomEdgeList)
            return wire
        else:
            numobjects = 0 
            wireList = self.FindTopoDSWires(shape)
            for wire in wireList:
                eListinWire = self.FindTopoDSEdges(wire)
                curAISGeomEList = [] 
                for e in eListinWire:
                    for aisGeomEdge in aisGeomEdgeList:
                        if aisGeomEdge.edge.IsSame(e):
                            curAISGeomEList.append(aisGeomEdge)
                numobjects += 1
                aisGeomWire = self.FindWireShape(wire,curAISGeomEList)
                aisGeomWireList.append(aisGeomWire)
        print("Find Wire Shape Done:",numobjects)
        if shape.ShapeType() == TopAbs_FACE:
            face = self.FindFaceShape(shape,aisGeomWireList)
            return face
        else:
            faceList = self.FindTopoDSFaces(shape)
            numobjects = 0 
            for face in faceList:
                wListinFace = self.FindTopoDSWires(face)
                curAISGeomWList = []
                for w in wListinFace:
                    for aisGeomWire in aisGeomWireList:
                        if aisGeomWire.wire.IsSame(w):
                            curAISGeomWList.append(aisGeomWire)
                numobjects += 1
                aisGeomFace = self.FindFaceShape(face,curAISGeomWList)
                aisGeomFaceList.append(aisGeomFace)
        print("Find Face Shape Done:",numobjects)
        if shape.ShapeType() == TopAbs_SHELL:
            shell = self.FindShellShape(shape,aisGeomFaceList)
            return shell
        else:
            numobjects = 0 
            shellList = self.FindTopoDSShells(shape)
            for shell in shellList:
                fListinShell = self.FindTopoDSFaces(shell)
                curAISGeomFList = [] 
                for faceinShell in fListinShell:
                    for aisGeomface in aisGeomFaceList:
                        if aisGeomface.face.IsSame(faceinShell):
                            curAISGeomFList.append(aisGeomface)
                numobjects += 1
                aisGeomShell = self.FindShellShape(shell,curAISGeomFList)
                aisGeomShellList.append(aisGeomShell)
        print("Find Shell Shape Done:",numobjects)
        aisGeomSolidList = [] 
        numobjects = 0 
        for aisGeomShell in aisGeomShellList:
            aisGeomSolid = self.FindSolidShape(shape,aisGeomShell)
            aisGeomSolidList.append(aisGeomSolid)
            numobjects += 1
        
        print("Find Solid Shape Done:",numobjects)
        
        if shape.ShapeType() == TopAbs_SOLID:
            print("Solid Shape Done")
            return aisGeomSolidList[0]
        else:
            print("Find Solid Shape Done")
            return aisGeomSolidList

    def CopyfromKooGeomManager(self,geomMan):
        self.RemoveAll()
        for i in geomMan.vertices:
            self.vertices[i] = geomMan.vertices[i]
        for i in geomMan.edges:
            self.edges[i] = geomMan.edges[i]
        for i in geomMan.wires:
            self.wires[i] = geomMan.wires[i]
        for i in geomMan.faces:
            self.faces[i] = geomMan.faces[i]
        for i in geomMan.shells:
            self.shells[i] = geomMan.shells[i]
        for i in geomMan.solids:
            self.solids[i] = geomMan.solids[i]
        for i in geomMan.textureboxes:
            self.textureboxes[i] = geomMan.textureboxes[i]

        self.maxvertexid = geomMan.maxvertexid
        self.maxedgeid = geomMan.maxedgeid
        self.maxwireid = geomMan.maxwireid
        self.maxfaceid = geomMan.maxfaceid
        self.maxshellid = geomMan.maxshellid
        self.maxsolidid = geomMan.maxsolidid
        self.maxtextureboxid = geomMan.maxtextureboxid

        self.Display()

    def ImportStepFile(self, filePath):
        solidLists = [] 
        step_reader = STEPControl_Reader()

        from OCC.Extend.DataExchange import read_step_file

        shapes = read_step_file(filePath)
        shapes = self.FindTopoDSSolids(shapes)
        for shape in shapes:
            print("Imported :",  shape)
            solid = self.FindSolidShape(shape)    
            solidLists.append(solid)
            print("Solid ID:", solid.id)
        #for shape in shapes:
        #self.CreateGeometryfromShape(shapes)
        #step_reader.ReadFile(filePath)                
        #step_reader.TransferRoot(1)
        #shape = step_reader.Shape()
        #self.CreateGeometryfromShape(shape) 
        return solidLists
    
    def ExportStepFileSolid(self, filePath):
        step_writer = STEPControl_Writer()
        for i in self.solids:
            step_writer.Transfer(self.solids[i].solid,STEPControl_AsIs)
        print("Write Step File : ",filePath)
        status = step_writer.Write(filePath)

        
        print("Write Status : ",status)
        if status == 0:
            print("Write Success")
        else:
            pass

    def ExportStepFile(self, filePath):
        step_writer = STEPControl_Writer()
        
        for i in self.vertices:
            step_writer.Transfer(self.vertices[i].vertex,TopAbs_VERTEX)
        for i in self.edges:
            step_writer.Transfer(self.edges[i].edge,TopAbs_EDGE)
        for i in self.wires:
            step_writer.Transfer(self.wires[i].wire,TopAbs_WIRE)
        for i in self.faces:
            step_writer.Transfer(self.faces[i].face,TopAbs_FACE)
        for i in self.shells:
            step_writer.Transfer(self.shells[i].shell,TopAbs_SHELL)
        for i in self.solids:
            step_writer.Transfer(self.solids[i].solid,TopAbs_SOLID)

        status = step_writer.Write(filePath)
        print("Write Status : ",status)
        if status == 0:
            print("Write Success")
        else:
            pass

    def PrintStatistics(self):
        print("Number of Vertices : ", len(self.vertices))
        print("Number of Edges : ", len(self.edges))
        print("Number of Wires : ", len(self.wires))
        print("Number of Faces : ", len(self.faces))
        print("Number of Shells : ", len(self.shells))
        print("Number of Solids : ", len(self.solids))




           


    
        
    
    
        