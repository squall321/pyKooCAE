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
from KooCAEManager.KooGeometry import (
    KooGeomVertex,
    KooGeomEdge,
    KooGeomLine,
    KooGeomArc,
    KooGeomCircle,
    KooGeomWire,
    KooGeomPolyline,
    KooGeomFace,
    KooGeomCutFace,
    KooGeomShell, 
    KooGeomSolid,
    KooGeomTextureBox
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

from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_Sewing
)

from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_Reader


class KooGeometryManager():

    def __init__(self):
        self.maxvertexid = 0
        self.maxedgeid = 0 
        self.maxwireid = 0 
        self.maxfaceid = 0 
        self.maxshellid = 0
        self.maxsolidid = 0 
        self.maxtextureboxid = 0

        self.vertices = {}
        self.edges = {} 
        self.wires = {}
        self.faces = {}
        self.shells = {}
        self.solids = {} 
        self.textureboxes = {}
    
    ### Vertex

    def CreateVertex(self,x,y,z):
        pnt = gp_Pnt(x,y,z)
        vertex = KooGeomVertex(0,pnt)
        return self.AddVertex(vertex)
    
    def AddVertex(self, v : KooGeomVertex):
        self.maxvertexid += 1 
        v.id = self.maxvertexid
        self.vertices[self.maxvertexid] = v
        return v

    def AddVertexbyShape(self, vShape : TopoDS_Vertex):
        self.maxvertexid += 1
        v = KooGeomVertex(self.maxvertexid)
        v.SetVertex(vShape)        
        return v
        

    def FindVertex(self,x,y,z,tol=1.e-6):
        for vertex in self.vertices.values():
            if vertex.pnt.Distance(gp_Pnt(x,y,z)) < tol:
                return vertex
        return self.CreateVertex(x,y,z)
    
    def FindClosestVertex(self,x,y,z):
        vertex = None 
        minDist = 1.e10
        for v in self.vertices.values():
            dist = v.pnt.Distance(gp_Pnt(x,y,z))
            if dist < minDist:
                minDist = dist
                vertex = v
        return minDist, vertex
    
    def FindVertexShape(self, v : TopoDS_Vertex, tol=1.e-6):
        p = BRep_Tool.Pnt(v)   
        for vertex in self.vertices.values():
            if vertex.pnt.Distance(p)<tol:
                return vertex
        return self.AddVertexbyShape(v)    
    
    def RemoveVertex(self,vertex):
        del self.vertices[vertex.id]
    
    def RemoveVertexbyID(self,vertexid):
        del self.vertices[vertexid]

    ### Edge
    
    def AddEdge(self, e : KooGeomEdge):
        self.maxedgeid += 1 
        e.id = self.maxedgeid
        self.edges[self.maxedgeid] = e   
        return e
    
    def AddEdgebyShape(self, e : TopoDS_Edge, vList = []):
        self.maxedgeid += 1
        edge = KooGeomEdge(self.maxedgeid)
        edge.SetEdge(e,vList)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def RemoveEdge(self, edge : KooGeomEdge):
        print("Remove Edge")
        print(edge)
        print("id",edge.id)
        print(self.edges)
        del self.edges[edge.id]

    def RemoveEdgebyID(self, edgeid):
        del self.edges[edgeid]
    
    def CreateEdge(self, e):
        self.maxedgeid += 1
        edge = KooGeomEdge(self.maxedgeid,e)
        self.edges[self.maxedgeid] = edge
        return edge

    def CreateLinefromVertices(self,v1,v2):
        self.maxedgeid += 1 
        edge = KooGeomLine(self.maxedgeid,v1,v2)
        self.edges[self.maxedgeid] = edge
        return edge 
    
    def FindLinefromVertices(self, v1,v2):
        for edge in self.edges.values():
            if edge.type == "Line":
                if edge.vertices[0].id == v1.id and edge.vertices[1].id == v2.id:
                    return edge
                elif edge.vertices[0].id == v2.id and edge.vertices[1].id == v1.id:
                    return edge
        return self.CreateLinefromVertices(v1,v2)

    def CreateArcfromVertices(self,vstart,vend,vcenter,counterclockwise):
        self.maxedgeid += 1 
        edge = KooGeomArc(self.maxedgeid,vstart,vend,vcenter,counterclockwise)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def FindArcfromVertices(self,vstart,vend,vcenter,counterclockwise):
        for edge in self.edges.values():
            if edge.type == "Arc":
                if edge.vertices[0].id == vstart.id and edge.vertices[1].id == vend.id and edge.vertices[2].id == vcenter.id and edge.counterclockwise == counterclockwise:
                    return edge
                elif edge.vertices[0].id == vend.id and edge.vertices[1].id == vend.id and edge.vertices[2].id == vcenter.id and edge.counterclockwise == counterclockwise:
                    return edge
        return self.CreateArcfromVertices(vstart,vend,vcenter,counterclockwise)

    def FindEdgeShape(self, e : TopoDS_Edge, vList = []):
        for edge in self.edges.values():
            if e.IsSame(edge.edge):
                return edge
        return self.AddEdgebyShape(e,vList)

    def CreateCirclefromVertices(self,vCenter, vEnd):
        self.maxedgeid += 1
        edge = KooGeomCircle(self.maxedgeid,vCenter,vEnd)
        self.edges[self.maxedgeid] = edge
        return edge
    
    def FindCirclefromVertices(self,vCenter, vEnd):
        for edge in self.edges.values():
            if edge.type == "Circle":
                if edge.vertices[0].id == vCenter.id and edge.vertices[1].id == vEnd.id:
                    return edge
                elif edge.vertices[0].id == vEnd.id and edge.vertices[1].id == vCenter.id:
                    return edge
        return self.CreateCirclefromVertices(vCenter,vEnd)

    ### Wire

    def CreateWirefromEdges(self,edges):
        self.maxwireid += 1
        wire = KooGeomWire(self.maxwireid,edges)
        self.wires[self.maxwireid] = wire
        return wire
    
    def AddWirebyShape(self, w : TopoDS_Wire, edges = []):
        self.maxwireid += 1
        wire = KooGeomWire(self.maxwireid)
        wire.SetWire(w,edges)
        self.wires[self.maxwireid] = wire
        return wire
    
    def RemoveWire(self, wire : KooGeomWire):
        print("Remove Wire")
        print(wire)
        print("id ",wire.id)
        print(self.wires)
        del self.wires[wire.id]        

    def RemoveWirebyID(self, wireid):
        del self.wires[wireid]

    def FindWirefromEdges(self,edges):
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
            if w.IsSame(wire.wire):
                return wire
        return self.AddWirebyShape(w,edges)

    def CreatePolylinefromVertices(self,vertices):
        self.maxwireid += 1
        wire = KooGeomPolyline(self.maxwireid,vertices)
        self.wires[self.maxwireid] = wire

        for edge in wire.edges:
            self.AddEdge(edge)
    
    ### Face

    def CreateFacefromWire(self, wire):
        self.maxfaceid += 1
        wires = [wire]
        face = KooGeomFace(self.maxfaceid,wires)
        self.faces[self.maxfaceid] = face
        return face
    
    def CreateFacefromWires(self, wires):
        self.maxfaceid += 1
        face = KooGeomFace(self.maxfaceid,wires)
        self.faces[self.maxfaceid] = face
        return face
    
    def AddFacebyShape(self, f : TopoDS_Face, wires = []):
        self.maxfaceid += 1
        face = KooGeomFace(self.maxfaceid)
        face.SetFace(f,wires)
        self.faces[self.maxfaceid] = face
        return face
    
    def RemoveFace(self, face : KooGeomFace):
        print("Remove Face")
        print(face)
        print("id ",face.id)
        print(self.faces)
        del self.faces[face.id]
    
    def RemoveFacebyID(self, faceid):
        del self.faces[faceid]

    def RemoveFacewithSubGeometries(self, face : KooGeomFace):
        for wire in face.wires:
            for edge in wire.edges:
                for vertex in edge.vertices:
                    self.RemoveVertex(vertex)
                self.RemoveEdge(edge)
            self.RemoveWire(wire)
        wire = face.wire
        for edge in wire.edges:
            for vertex in edge.vertices:
                self.RemoveVertex(vertex)
            self.RemoveEdge(edge)
        self.RemoveWire(wire)
        self.RemoveFace(face)


    def FindFacefromWire(self, wire):
        for face in self.faces.values():
            if face.wire.id == wire.id:
                return face
        return self.CreateFacefromWire(wire)    
    
    def FindFaceShape(self, f : TopoDS_Face, wires = []):
        for face in self.faces.values():
            if f.IsSame(face.face):
                return face
        return self.AddFacebyShape(f,wires)
    
    ### Cut Face
    def CreateCutFace(self, baseFace, toolFace):
        self.maxfaceid += 1
        face = KooGeomCutFace(self.maxfaceid,baseFace,toolFace)
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
                vList = []
                vertex_explorer = TopExp_Explorer(edge,TopAbs_VERTEX)
                while vertex_explorer.More():
                    vertex = vertex_explorer.Current()
                    vList.append(self.FindVertexShape(vertex))
                    vertex_explorer.Next()
                edges.append(self.AddEdgebyShape(edge,vList))
                edge_explorer.Next()
            wires.append(self.AddWirebyShape(wire,edges))
            wire_explorer.Next()
            
    ### Shell

    def CreateShellfromFaces(self, faces):
        self.maxshellid += 1
        shell = KooGeomShell(self.maxshellid,faces)
        self.shells[self.maxshellid] = shell
        return shell

    def AddShellbyShape(self, s : TopoDS_Shell, faces = []):
        self.maxshellid += 1
        shell = KooGeomShell(self.maxshellid)
        shell.SetShell(s,faces)
        self.shells[self.maxshellid] = shell
        return shell
    
    def RemoveShell(self, shell : KooGeomShell):
        print("Remove Shell")
        print(shell)
        print("id ",shell.id)
        print(self.shells)
        del self.shells[shell.id]

    def RemoveShellbyID(self, shellid):
        del self.shells[shellid]
    
    def FindShellShape(self, s : TopoDS_Shell, faces = []):
        for shell in self.shells.values():
            if s.IsSame(shell.shell):
                return shell
        return self.AddShellbyShape(s,faces)
    
    def CreateSolidfromShell(self, shell):
        self.maxsolidid += 1
        solid = KooGeomSolid(self.maxsolidid,shell)
        self.solids[self.maxsolidid] = solid
        return solid
    
    def AddSolidbyShape(self, s : TopoDS_Solid, shell = None):
        self.maxsolidid += 1
        solid = KooGeomSolid(self.maxsolidid)
        solid.SetSolid(s,shell)
        self.solids[self.maxsolidid] = solid
        return solid
    
    def RemoveSolid(self, solid : KooGeomSolid):
        print("Remove Solid")
        print(solid)
        print("id ",solid.id)
        print(self.solids)
        del self.solids[solid.id]
    
    def RemoveSolidbyID(self, solidid):
        del self.solids[solidid]

    # texture box 
    def CreateTextureBox(self,texturePath, xPos, yPos, zPos, xSize, ySize, zSize):
        self.maxtextureboxid += 1
        textureBox = KooGeomTextureBox(self.maxtextureboxid,texturePath, xPos, yPos, zPos, xSize, ySize, zSize)
        textureBox.Update()
        self.textureboxes[self.maxtextureboxid] = textureBox
        return textureBox

    def RemoveTextureBox(self, textureBox : KooGeomTextureBox):
        print("Remove Texture Box")
        print(textureBox)
        print("id ",textureBox.id)
        print(self.textureboxes)
        del self.textureboxes[textureBox.id]
    
    def RemoveTextureBoxbyID(self, textureBoxid):
        del self.textureboxes[textureBoxid]
    
    def FindSolidShape(self, s : TopoDS_Solid, shell = None):
        for solid in self.solids.values():
            if s.IsSame(solid.solid):
                print("Solid already exists")
                return solid
        return self.AddSolidbyShape(s,shell)
    
    def FindTopoDSVertices(self, shape):
        vertex_explorer = TopExp_Explorer(shape,TopAbs_VERTEX)
        vertices = []
        while vertex_explorer.More():
            vertex = vertex_explorer.Current()
            vertices.append(vertex)
            vertex_explorer.Next()
        return vertices
    
    def FindTopoDSEdges(self, shape):
        edge_explorer = TopExp_Explorer(shape,TopAbs_EDGE)
        edges = []
        while edge_explorer.More():
            edge = edge_explorer.Current()
            edges.append(edge)
            edge_explorer.Next()
        return edges
    
    def FindTopoDSWires(self, shape):
        wire_explorer = TopExp_Explorer(shape,TopAbs_WIRE)
        wires = []
        while wire_explorer.More():
            wire = wire_explorer.Current()
            wires.append(wire)
            wire_explorer.Next()
        return wires
    
    def FindTopoDSFaces(self, shape):
        face_explorer = TopExp_Explorer(shape,TopAbs_FACE)
        faces = []
        while face_explorer.More():
            face = face_explorer.Current()
            faces.append(face)
            face_explorer.Next()
        return faces
    
    def FindTopoDSShells(self, shape):
        shell_explorer = TopExp_Explorer(shape,TopAbs_SHELL)
        shells = []
        while shell_explorer.More():
            shell = shell_explorer.Current()
            shells.append(shell)
            shell_explorer.Next()
        return shells
    
    def FindTopoDSSolids(self, shape):
        solid_explorer = TopExp_Explorer(shape,TopAbs_SOLID)
        solids = []
        while solid_explorer.More():
            solid = solid_explorer.Current()
            solids.append(solid)
            solid_explorer.Next()
        return solids

    def CreateGeometryfromShape(self,shape):
        vertexList = self.FindTopoDSVertices(shape)
        geomVertexList = [] 
        geomEdgeList = [] 
        geomWireList = [] 
        geomFaceList = []
        geomShellList = []
        geomSolidList = []        
        for vertex in vertexList:
            geomVertex = self.FindVertexShape(vertex)
            geomVertexList.append(geomVertex)
        if shape.ShapeType() == TopAbs_EDGE:
            edge = self.FindEdgeShape(shape,geomVertexList)
            return edge
        else:
            edgeList = self.FindTopoDSEdges(shape)
            for edge in edgeList:
                vListinEdge = self.FindTopoDSVertices(edge)
                curGeomVList = []
                for vertexinEdge in vListinEdge: 
                    for geomVertex in geomVertexList:
                        if geomVertex.vertex.IsSame(vertexinEdge):
                            curGeomVList.append(geomVertex)
                geomEdge = self.FindEdgeShape(edge,curGeomVList)
                geomEdgeList.append(geomEdge)
        if shape.ShapeType() == TopAbs_WIRE:
            wire = self.FindWireShape(shape,geomEdgeList)
            return wire
        else:
            wireList = self.FindTopoDSWires(shape)
            for wire in wireList:
                eListinWire = self.FindTopoDSEdges(wire)
                curGeomEList = []
                for edgeinWire in eListinWire:
                    for geomEdge in geomEdgeList:
                        if geomEdge.edge.IsSame(edgeinWire):
                            curGeomEList.append(geomEdge)
                geomWire = self.FindWireShape(wire,curGeomEList)
                geomWireList.append(geomWire)
        if shape.ShapeType() == TopAbs_FACE:
            face = self.FindFaceShape(shape,geomWireList)
            return face
        else:
            faceList = self.FindTopoDSFaces(shape)
            for face in faceList:
                wListinFace = self.FindTopoDSWires(face)
                curGeomWList = []
                for wireinFace in wListinFace:
                    for geomWire in geomWireList:
                        if geomWire.wire.IsSame(wireinFace):
                            curGeomWList.append(geomWire)
                geomFace = self.FindFaceShape(face,curGeomWList)
                geomFaceList.append(geomFace)
        if shape.ShapeType() == TopAbs_SHELL:
            shell = self.FindShellShape(shape,geomFaceList)
            return shell
        else:
            shellList = self.FindTopoDSShells(shape)
            for shell in shellList:
                fListinShell = self.FindTopoDSFaces(shell)
                curGeomFList = []
                for faceinShell in fListinShell:
                    for geomFace in geomFaceList:
                        if geomFace.face.IsSame(faceinShell):
                            curGeomFList.append(geomFace)
                geomShell = self.FindShellShape(shell,curGeomFList)
                geomShellList.append(geomShell)
        
        geomSolidList = [] 
        for geomShell in geomShellList:
            solid = self.FindSolidShape(shape,geomShell)
            geomSolidList.append(solid)
        if shape.ShapeType() == TopAbs_SOLID:
            return geomSolidList[0]
        else:
            return geomSolidList
  

    '''
    def CreateGeometryfromShape(self,shape):
        if shape.ShapeType() == TopAbs_SOLID:
            pass
        elif shape.ShapeType() == TopAbs_SHELL:
            pass
        elif shape.ShapeType() == TopAbs_FACE:
            pass
        elif shape.ShapeType() == TopAbs_WIRE:
            pass
        elif shape.ShapeType() == TopAbs_EDGE:
            pass
        elif shape.ShapeType() == TopAbs_VERTEX:
            pass
        pass
    '''
    
    '''
    def CommonFacetoFace(self,face1,face2):
        f1 = face1.face
        f2 = face2.face
    '''   

    def Print(self):
        print("Vertices:",len(self.vertices))
        print("Edges:",len(self.edges))
        print("Wires:",len(self.wires))
        print("Faces:",len(self.faces))
        print("Solids:",len(self.solids))

    def RemoveAll(self):
        self.vertices.clear()
        self.edges.clear()
        self.wires.clear()
        self.faces.clear()
        self.shells.clear()
        self.solids.clear()        
        self.textureboxes.clear()

        self.maxvertexid = 0
        self.maxedgeid = 0 
        self.maxwireid = 0 
        self.maxfaceid = 0 
        self.maxshellid = 0
        self.maxsolidid = 0 
        self.maxtextureboxid = 0




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

    def ImportStepFile(self, filePath):
        step_reader = STEPControl_Reader()

        from OCC.Extend.DataExchange import read_step_file

        shapes = read_step_file(filePath)
        shapes = self.FindTopoDSSolids(shapes)
        for shape in shapes:
            self.FindSolidShape(shape)
        
        #for shape in shapes:
        #self.CreateGeometryfromShape(shapes)
        #step_reader.ReadFile(filePath)                
        #step_reader.TransferRoot(1)
        #shape = step_reader.Shape()
        #self.CreateGeometryfromShape(shape)  

    def ExportStepFileSolid(self, filePath):
        step_writer = STEPControl_Writer()
        for i in self.solids:
            step_writer.Transfer(self.solids[i].solid,TopAbs_SOLID)
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

