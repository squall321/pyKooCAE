from KooODBCADManager.Polygon import Polygon2D as Poly
from KooODBCADManager.Polygon import Vertex2D
from KooODBCADManager.Polygon import Edges2D

class PolygonManager2D():
    def __init__(self):
        self.vertices = {}
        self.edges = {} 
        self.polygons = {} 
        self.max_vid = 0 
        self.max_eid = 0
        self.max_pid = 0 
    
    def CreateVertex(self,x,y,r=0):
        self.max_vid += 1
        return Vertex2D(self.max_vid,x,y,r)
    
    def CreateNewVertices(self,vertices):        
        for v in vertices:
            self.CreateVertices(v.x,v.y,v.r)                
    
    def CreateLine(self, v1, v2):
        self.max_eid += 1
        newEdge = Edges2D(self.max_eid,[v1,v2])
        self.AddEdge(newEdge)
        return newEdge
    
    def CreateCircle(self,vertices):
        self.max_eid += 1
        newEdge = Edges2D(self.max_eid,vertices,"Circle")
        edges = [] 
        edges.append(newEdge)
        return edges

    
    def CreateLines(self,vertices):
        edges = []
        size = len(vertices)
        for i in range(0,size-1):
            v1 = vertices[i]
            v2 = vertices[i+1]
            newEdge = self.CreateLine(v1,v2)
            edges.append(newEdge)
        return edges
    
    def CreateNewEdge(self,edge):
        self.max_eid += 1
        newEdge = Edges2D(self.max_eid,edge.vertices,edge.type)
        newEdge.counterclockwise = edge.counterclockwise
        self.AddEdge(newEdge)
    
    def CreateNewEdges(self,edges):
        for e in edges:            
            self.CreateNewEdges(e)
    
    def CreateArc(self,v1, v2, v3, clk=True):
        self.max_eid += 1
        newEdge = Edges2D(self.max_eid,[v1,v2,v3],"Arc")
        newEdge.counterclockwise = clk        
        self.AddEdge(newEdge)
        return newEdge
    
    def CreatePolygon(self,vertices,type,edges=None):
        self.max_pid += 1        
        newPolygon = Poly(self.max_pid,type)
        newPolygon.AddVertices(vertices)
        if type == "CR":
            edges = self.CreateCircle(vertices)
        elif edges == None:
            edges = self.CreateLines(vertices)
        newPolygon.AddEdges(edges)
        
        self.AddPolygon(newPolygon)
        return newPolygon
    
    def AddVertex(self, vertex):
        self.vertices[vertex.id] = vertex
        self.max_vid = max(self.max_vid,vertex.id)       

    def AddEdge(self, edge):
        self.edges[edge.id] = edge
        self.max_eid = max(self.max_eid,edge.id) 
    
    def AddPolygon(self, polygon):
        self.polygons[polygon.id] = polygon
        self.max_pid = max(self.max_pid,polygon.id)        

    def FindVertex(self, x, y):
        for v in self.vertices.values():
            if v.x == x and v.y == y:
                return v
        return self.CreateVertex(x,y)
    

    
    def CreateTriangle(self,v1,v2,v3):
        self.max_pid += 1
        newPolygon = Poly(self.max_pid)
        newPolygon.AddVertex(v1)
        newPolygon.AddVertex(v2)
        newPolygon.AddVertex(v3)        
        edges = self.CreateLines([v1,v2,v3,v1])
        newPolygon.AddLines(edges)
        self.AddPolygon(newPolygon)
        return newPolygon
    
    def CreateQuadrangle(self,v1,v2,v3,v4):
        self.max_pid += 1
        newPolygon = Poly(self.max_pid)
        newPolygon.AddVertex(v1)
        newPolygon.AddVertex(v2)
        newPolygon.AddVertex(v3)
        newPolygon.AddVertex(v4)
        edges = self.CreateLines([v1,v2,v3,v4,v1])
        newPolygon.AddLines(edges)        
        self.AddPolygon(newPolygon)
        return newPolygon
    
    def CreatePolygonfromFlattenVector(self, svector):
        vertices = []
        size = len(svector)
        for i in range(0,size,2):
            x = float(svector[i])*0.0393701
            y = float(svector[i+1])*0.0393701
            newVertex = self.CreateVertex(x,y)    
            vertices.append(newVertex)
        vertices.append(vertices[0])
        edges = self.CreateLines(vertices)        
        aPolygon = self.CreatePolygon(vertices,'Flat')
        aPolygon.AddLines(edges)
        return aPolygon
 