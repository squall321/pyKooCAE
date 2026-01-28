from KooODBCADManager.Polygon import Polygon2D as Poly
from KooODBCADManager.Polygon import Vertex2D
import os.path
import json

class Package():
    def __init__(self,id,name):
        self.id = id
        self.name = name
        self.type='package'
        self.polygons = []
        self.max_pid = 0
        self.color = [0.5, 0.5, 0.5 ,1.0]

    def SetColor(self, r,g,b,a):
        self.color = [r,g,b,a]

    def AddPolygon(self, polygon):    
        self.polygons.append(polygon)
    
    def WritePackageJSON(self,path):
        fileName = "{name}.json".format(name=self.name)
        with open(os.path.join(path,fileName),'w') as stream:
            out = json.dumps(self.SerializeData(),indent='\t')
            stream.write(out)

    def SerializeData(self):
        jsonData = {}
        jsonData['id'] = self.id
        jsonData['name'] = self.name
        jsonData['color'] = [self.color[0],self.color[1],self.color[2],self.color[3]]
        jsonData['type'] = self.type
        jsonData['package']={}
        for aPolygon in self.polygons:
            jsonData['package'][aPolygon.id] = aPolygon.SerializeData()
        return jsonData
    
    def WritePackage(self,stream):
        if self.type == 'pcb':
            for aPolygon in self.polygons:
                stream.write("PRP BOARD_PLACEMENT_OUTLINE '' {flatVec}".format(flatVec=aPolygon.WritePolygonasConnectedVector(stream)))
        elif self.type == 'package':
            stream.write("# PKG {id}\n".format(id=self.id))
            stream.write("PKG {name}\n".format(name=self.name))
            for aPolygon in self.polygons:
                aPolygon.WritePolygon(stream)
    
    def GetPackagePolygonsCoordinates(self,originX=0, originY=0,rotation=0,mirror=False):
        polygonTramsformedList = []
        for aPolygon in self.polygons:
            aPolygonTransformed = [] 
            aPolygonTransformed.append(aPolygon.type)
            aPolygonTransformed.append(aPolygon.GetPolygonsCoordinates(originX,originY,rotation,mirror))
            polygonTramsformedList.append(aPolygonTransformed)
        return polygonTramsformedList

    def BoundaryBox(self):
        boundaryBox = [1.e99,-1.e99,1.e99,-1.e99]
        for aPoly in self.polygons:
            if aPoly != None:
                curBox = aPoly.BoundaryBox()
                boundaryBox[0] = min(boundaryBox[0],curBox[0])
                boundaryBox[1] = max(boundaryBox[1],curBox[1])
                boundaryBox[2] = min(boundaryBox[2],curBox[2])
                boundaryBox[3] = max(boundaryBox[3],curBox[3])
        return boundaryBox
    
    def ExportDetailPackage(self,file):
        file.write("*Layer,SolderJointWarpage,SolderJointWarped\n")
        file.write("Location,0,0,0\n")
        boundBox = self.BoundaryBox()
        xLength = boundBox[1] - boundBox[0]
        yLength = boundBox[3] - boundBox[2]
        
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,'.4e'),yLength=format(yLength,'.4e')))        
        file.write("Thickness,{thick}\n".format(thick=0.08))
        file.write("MeshGenerationType,Solid,Tetra\n")
        file.write("MeshPath,PackageMesh\n")
        file.write("MeshSizeInPlane,0.1\n")
        file.write("NumberofElementinThickness,5\n")
        file.write("MaterialID,1\n")
        file.write("DetailSolder,True\n")
        file.write("MisalignmentAngle,0,0.0\n")
        file.write("SurfaceTension,480.0\n")
        ith = 0 
        for aPolygon in self.polygons:
            if aPolygon == None:
                continue
            aPolygon : Poly = aPolygon
            if ith == 0:
                pass
            else:
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    solderRadius = aVertex.r * 1.5
                    topMaskThickness=0.01
                    botMaskThickness=0.01
                    
                    file.write("SMD,PIN{ith},{xbot},{ybot},{rbot},{xtop},{ytop},{rtop},{solderRadius},{topMaskThickness},{botMaskThickness},None\n".format(ith=ith,xbot=format(aVertex.x,".3e"),ybot=format(aVertex.y,".3e"),rbot=format(aVertex.r,".3e"),xtop=format(aVertex.x,".3e"),ytop=format(aVertex.y,".3e"),rtop=format(aVertex.r,".3e"),solderRadius=format(solderRadius,".3e"),topMaskThickness=format(topMaskThickness,".3e"),botMaskThickness=format(botMaskThickness,".3e")))
                elif aPolygon.type == "RC":
                    xmin = aVertex.x
                    ymin = aVertex.y
                    delX = aPolygon.vertices[2].x - xmin
                    delY = aPolygon.vertices[2].y - ymin
                    file.write("BoxWarpage,{x},{y},{delX},{delY}\n".format(x=format(xmin,".3e"),y=format(ymin,".3e"),delX=format(delX,".3e"),delY=format(delY,".3e")))
                elif aPolygon.type == "CT":
                    jth = 0
                    file.write("Part,Polynomial,Solid,1\n")
                    for aVertex in aPolygon.vertices:
                        if jth == 0:
                            file.write("OB {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                        elif jth == len(aPolygon.vertices) - 1:
                            file.write("OS {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                            file.write("OE\n")  
                        else:
                            file.write("OS {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                        jth = jth + 1
                else:
                    print("Unknown Polygon Type")
                    continue
            ith = ith + 1
        file.write("*Layer,PackageWarpage,Defined\n")
        file.write("Location,0,0\n")
        aPolygon = self.polygons[0]
        boundaryBox = self.BoundaryBox()
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,".3e"),yLength=format(yLength,".3e")))
        file.write("Thickness,{thick}\n".format(thick=0.5))
        file.write("MeshGenerationType,Solid,Hexa\n")
        file.write("MeshPath,PackageMesh\n")
        file.write("NumberofElementinXDirection,20\n")
        file.write("NumberofElementinYDirection,20\n")
        file.write("NumberofElementinThickness,3\n")
        file.write("MaterialID,2\n")
        file.write("*Material\n")
        file.write("Material.txt\n")
        file.write("*End")        
        
    
    def ExportPackage(self,file):
        file.write("*Layer,SolderJoint\n")
        file.write("Location,0,0,0\n")
        boundBox = self.BoundaryBox()
        xLength = boundBox[1] - boundBox[0]
        yLength = boundBox[3] - boundBox[2]
        file.write("Length,{xLength},{yLength}\n".format(xLength=xLength,yLength=yLength))
        file.write("Thickness,{thick}\n".format(thick=0.10))
        file.write("MeshGenerationType,Solid,Tetra\n")
        file.write("MeshPath,PackageMesh\n")
        file.write("MeshSizeInPlane,0.1\n")
        file.write("NumberofElementinThickness,5\n")
        file.write("MaterialID,1\n")
        file.write("SurfaceTension,480.0\n")
        ith = 0
        for aPolygon in self.polygons:
            if aPolygon == None:
                continue
            aPolygon : Poly = aPolygon
            if ith == 0:
                pass
            else:
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    file.write("Cylinder,{x},{y},{r}\n".format(x=aVertex.x,y=aVertex.y,r=aVertex.r))
                elif aPolygon.type == "RC":
                    xmin = aVertex.x
                    ymin = aVertex.y
                    delX = aPolygon.vertices[2].x - xmin
                    delY = aPolygon.vertices[2].y - ymin
                    file.write("Box,{x},{y},{delX},{delY}\n".format(x=xmin,y=ymin,delX=delX,delY=delY))
                elif aPolygon.type == "CT":
                    jth = 0
                    file.write("Part,Polynomial,Solid,1\n")
                    for aVertex in aPolygon.vertices:
                        if jth == 0:
                            file.write("OB {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                        elif jth == len(aPolygon.vertices) - 1:
                            file.write("OS {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                            file.write("OE\n")  
                        else:
                            file.write("OS {x} {y}\n".format(x=format(aVertex.x,".5e"),y=format(aVertex.y,".5e")))
                        jth = jth + 1
                else:
                    print("Unknown Polygon Type")
                    continue
            ith = ith + 1
        file.write("*Layer,Package\n")
        file.write("Location,0,0\n")
        aPolygon = self.polygons[0]
        boundaryBox = self.BoundaryBox()
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]
    
        file.write("Length,{xLength},{yLength}\n".format(xLength=xLength,yLength=yLength))
        file.write("Thickness,{thick}\n".format(thick=0.5))
        file.write("MeshGenerationType,Solid,Hexa\n")
        file.write("MeshPath,PackageMesh\n")
        file.write("NumberofElementinXDirection,20\n")
        file.write("NumberofElementinYDirection,20\n")
        file.write("NumberofElementinThickness,3\n")
        file.write("MaterialID,2\n")
        file.write("*Material\n")
        file.write("Material.txt\n")
        file.write("*End")        
