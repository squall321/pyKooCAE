import sys 
import os

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

import numpy as np
# Open Cascade for Generating Solid
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.BRepBuilderAPI import(
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

from KooODBCADManager.Polygon import Polygon2D, Edges2D, Vertex2D
from KooODBCADManager.Package import Package
from KooODBCADManager.PCB import PCB
from KooODBCADManager.Capacitor import Capacitor
from KooODBCADManager.PackageGenerator import PackageUserdefined


class Component():
    def __init__(self,id):
        self.id = id
        self.origin_x = 0.0
        self.origin_y = 0.0
        self.origin_z = 0.0 
        self.rotation = 0
        self.mirror = False
        self.color = [0.5,0.5,0.5,1.0]
        self.package_thickness = 0.1
        self.package_thickness_max = 0.1
        self.package_thickness_min = 0.1
        self.solderjoint_thickness = 0.03
        self.type = "None"
        self.value = ""
    
    def SetPackageThickness(self, thickness):
        self.package_thickness = thickness  
    
    def SetPackageThicknesswithMinMax(self, height, maxHeight, minHeight):
        self.package_thickness = height
        self.package_thickness_max = maxHeight
        self.package_thickness_min = minHeight

    def SetSolderJointThickness(self, thickness):
        self.solderjoint_thickness = thickness

    def SetOrigin(self, x,y,z=0.0):
        self.origin_x = x
        self.origin_y = y
        self.origin_z = z
    
    def SetRotation(self, rotation):
        self.rotation = int(rotation)

    def SetMirror(self, mirror):
        self.mirror = mirror


class PCBComponent(Component):

    def __init__(self,id,pcb):
        super(PCBComponent,self).__init__(id)
        self.pcb = pcb
        self.color = pcb.color
        self.type = "PCB"
        
    def BoundaryBox(self):        
        totalBoundaryBox = self.pcb.BoundaryBox()
        totalBoundaryBox[0] = totalBoundaryBox[0] + self.origin_x
        totalBoundaryBox[1] = totalBoundaryBox[1] + self.origin_x
        totalBoundaryBox[2] = totalBoundaryBox[2] + self.origin_y
        totalBoundaryBox[3] = totalBoundaryBox[3] + self.origin_y
        return totalBoundaryBox
    
class PackageComponent(Component):

    def __init__(self,id,pkg):
        super(PackageComponent,self).__init__(id)
        self.pkg : Package = pkg
        self.color = pkg.color
        self.type = "Package"
    
    def BoundaryBox(self):
        totalBoundaryBox = self.pkg.BoundaryBox()
        totalBoundaryBox[0] = totalBoundaryBox[0] + self.origin_x
        totalBoundaryBox[1] = totalBoundaryBox[1] + self.origin_x
        totalBoundaryBox[2] = totalBoundaryBox[2] + self.origin_y
        totalBoundaryBox[3] = totalBoundaryBox[3] + self.origin_y
        return totalBoundaryBox
    
    def GenerateTopShieldCan(self, pkgZLocation):
        pass
    def GenerateBottomShieldCan(self, pkgZLocation):
        pass

    def GenerateTop(self, pkgZLocation,detailPADS):        
        shapeList = [] 
        ith = 0
        detailBallMode = False 
        if self.pkg.name in detailPADS:
            detailBallMode = True
        elif "ALL" in detailPADS:
            detailBallMode = True
        if detailBallMode:
            for aPolygon in self.pkg.polygons:                
                #point2DList = aPolygon.GetPolygonsCoordinates(self.origin_x,self.origin_y,self.rotation,self.mirror)
                if aPolygon == None:
                    continue
                aPolygon : Polygon2D = aPolygon
                if ith == 0:                    
                    thickness = self.package_thickness
                    x = self.origin_x
                    y = self.origin_y
                    z = pkgZLocation + self.origin_z + self.solderjoint_thickness
                    rotation = self.rotation
                    mirror = self.mirror
                    if thickness == 0.0:
                        pass
                    else:
                        shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)
                        shapeList.append(shape)
                else:                    
                    thickness = self.solderjoint_thickness
                    x = self.origin_x
                    y = self.origin_y
                    z = pkgZLocation + self.origin_z
                    rotation = self.rotation
                    mirror = self.mirror
                    if thickness == 0.0:
                        pass
                    else:
                        shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)
                        shapeList.append(shape)
                    
                ith = ith + 1
        else:
            aPolygon = self.pkg.polygons[0]
            thickness = self.package_thickness
            x = self.origin_x
            y = self.origin_y
            z = pkgZLocation + self.origin_z
            rotation = self.rotation
            mirror = self.mirror            
            if aPolygon is not None:
                shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)
                if shape is not None:
                    shapeList.append(shape)            
        return shapeList

    def GenerateBottom(self, pkgZLocation, detailPADS):
        shapeList = [] 
        ith = 0
        detailBallMode = False
        if self.pkg.name in detailPADS:
            detailBallMode = True
        elif "ALL" in detailPADS:
            detailBallMode = True
        if detailBallMode:
            for aPolygon in self.pkg.polygons:
                if aPolygon == None:
                    continue
                aPolygon : Polygon2D = aPolygon
                if ith == 0:
                    ''''
                    point_list = []
                    for aPoint in point2DList:
                        x = aPoint[0]
                        y = aPoint[1]
                        z = pkgZLocation + self.origin_z - self.solderjoint_thickness - self.package_thickness
                        point_list.append(gp_Pnt(x,y,z))
                    pbuilder = BRepBuilderAPI_MakePolygon()
                    for aPoint in point_list:
                        pbuilder.Add(aPoint)
                    p = pbuilder.Wire()
                    face = BRepBuilderAPI_MakeFace(p,True).Face()
                    thick = self.package_thickness
                    prism = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
                    shapeList.append(prism.Shape())
                    '''
                    thickness = self.package_thickness
                    x = self.origin_x
                    y = self.origin_y
                    z = pkgZLocation + self.origin_z - self.solderjoint_thickness - thickness
                    rotation = self.rotation
                    mirror = not self.mirror
                    if thickness == 0.0:
                        pass
                    else:
                        shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)                
                        shapeList.append(shape)
                    
                else:
                    '''
                    for aPoint in point2DList:
                        x = aPoint[0]
                        y = aPoint[1]
                        z = pkgZLocation + self.origin_z - self.solderjoint_thickness
                        point_list.append(gp_Pnt(x,y,z))
                    pbuilder = BRepBuilderAPI_MakePolygon()
                    for aPoint in point_list:
                        pbuilder.Add(aPoint)
                    p = pbuilder.Wire()
                    face = BRepBuilderAPI_MakeFace(p,True).Face()
                    thick = self.solderjoint_thickness
                    prism = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,thick))
                    shapeList.append(prism.Shape())              
                    '''
                    thickness = self.solderjoint_thickness
                    x = self.origin_x
                    y = self.origin_y
                    z = pkgZLocation + self.origin_z - self.solderjoint_thickness
                    rotation = self.rotation
                    mirror = not self.mirror
                    if thickness == 0.0:
                        pass
                    else:
                        shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)
                        shapeList.append(shape)

                ith = ith + 1
        else:
            aPolygon : Polygon2D = self.pkg.polygons[0]

            thickness = self.package_thickness
            x = self.origin_x
            y = self.origin_y
            z = pkgZLocation + self.origin_z - thickness
            rotation = self.rotation
            mirror = not self.mirror
            if aPolygon is not None:
                shape = aPolygon.Generate(thickness,True,x,y,z,rotation,mirror)
                shapeList.append(shape)
        return shapeList
    
    def GenerateTopUserdefined(self, pkgZLocation, detailPKGFileName):
        curPath = os.getcwd()
        curFilePath = os.path.join(curPath,detailPKGFileName)
        print("Current Path : {curPath}".format(curPath=curFilePath))
        originX = self.origin_x
        originY = self.origin_y
        originZ = pkgZLocation + self.origin_z
        rotation = self.rotation
        mirror = self.mirror
        pkgUserdefined = PackageUserdefined(originX,originY,originZ,rotation,mirror,True)
        pkgUserdefined.outFileName = detailPKGFileName.replace(".txt",".step")
        pkgUserdefined.ImportPackage(curFilePath)
        shapeList = pkgUserdefined.GenerateShapeList()
        shapesTransformed = pkgUserdefined.TransformedShapeList()        
        return shapesTransformed

    def GenerateBottomUserdefined(self, pkgZLocation, detailPKGFileName):
        curPath = os.getcwd()
        curFilePath = os.path.join(curPath,detailPKGFileName)
        print("Current Path : {curPath}".format(curPath=curFilePath))
        originX = self.origin_x
        originY = self.origin_y
        originZ = pkgZLocation + self.origin_z
        rotation = self.rotation
        mirror = self.mirror
        pkgUserdefined = PackageUserdefined(originX,originY,originZ,rotation,mirror,False)
        pkgUserdefined.outFileName = detailPKGFileName.replace(".txt",".step")
        pkgUserdefined.ImportPackage(curFilePath)
        shapeList = pkgUserdefined.GenerateShapeList()
        shapesTransformed = pkgUserdefined.TransformedShapeList()        
        return shapesTransformed
    
    def ExportTopDetail(self, file, pkgZLocation, generateMesh = False):
        self.ExportDetail(file, pkgZLocation, True, generateMesh)
    
    def ExportBottomDetail(self, file, pkgZLocation, generateMesh = False):
        self.ExportDetail(file, pkgZLocation, False, generateMesh)    
    
    def ExportDetail(self,file, pkgZLocation, isTop, generateMesh = False):
        file.write("*Translation,{x},{y},{z}\n".format(x=self.origin_x,y=self.origin_y,z=pkgZLocation + self.origin_z))
        file.write("*Rotation,{rot}\n".format(rot=self.rotation))
        file.write("*Mirror,{mir}\n".format(mir=self.mirror))
        if isTop == True:
            file.write("*IsTop,True\n")        
        else:
            file.write("*IsTop,False\n")    
        
        ith = 0
        hasSolderShape = False
        for aPolygon in self.pkg.polygons:
            if aPolygon == None:
                continue
            aPolygon : Polygon2D = aPolygon
            if ith == 0:
                pass
            else:
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    hasSolderShape = True
                elif aPolygon.type == "RC":
                    pass 
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
                    print("Unknown Type")
                    exit()
            ith = ith + 1 
        
        if hasSolderShape == True:
            file.write("*Layer,SolderJointWarpage,SolderJointWarped\n")
        else:
            file.write("*Layer,PackageWarpage,Defined\n")
        file.write("Location,{x},{y},{z}\n".format(x=0,y=0,z=0.0))
        boundBox = self.BoundaryBox()
        xLength = boundBox[1] - boundBox[0]
        yLength = boundBox[3] - boundBox[2]
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,".3e"),yLength=format(yLength,".3e")))        
        file.write("Thickness,{thick}\n".format(thick=format(self.solderjoint_thickness,".3e")))
        
        if generateMesh == True:
            file.write("MeshGenerationType,Solid,Tetra\n")
            file.write("MeshPath,PackageMesh\n")
            file.write("MeshSizeInPlane,0.1\n")
            file.write("NumberofElementinThickness,5\n")
            file.write("MaterialID,1\n")
        if hasSolderShape == True:
            file.write("DetailSolder,True\n")
            
        file.write("MisalignmentAngle,0,0.0\n")
        file.write("SurfaceTension,480.0\n")
        ith = 0
        for aPolygon in self.pkg.polygons:
            if aPolygon == None:
                continue
            aPolygon : Polygon2D = aPolygon
            if ith == 0:
                pass
            else:
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    file.write("SMD,PIN{ith},{xbot},{ybot},{rbot},{xtop},{ytop},{rtop},{solderRadius},{topMaskThickness},{botMaskThickness},None\n".format(ith=ith,xbot=format(aVertex.x,".3e"),ybot=format(aVertex.y,".3e"),rbot=format(aVertex.r,".3e"),xtop=format(aVertex.x,".3e"),ytop=format(aVertex.y,".3e"),rtop=format(aVertex.r,".3e"),solderRadius=format(aVertex.r*1.5,".3e"),topMaskThickness=0.01,botMaskThickness=0.01))
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
                    print("Unknown Type")
                    exit()
            ith = ith + 1    
            
        file.write("*Layer,PackageWarpage,Defined\n")
        file.write("Location,{x},{y}\n".format(x=0,y=0))
        
        '''boundaryBox = self.BoundaryBox()
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,".3e"),yLength=format(yLength,".3e")))'''
        
        
        file.write("Thickness,{thick}\n".format(thick=format(self.package_thickness,".3e")))
        if generateMesh == True:
            file.write("MeshGenerationType,Solid,Hexa\n")
            file.write("MeshPath,PackageMesh\n")
            file.write("MeshSizeInPlane,0.1\n")
            file.write("NumberofElementinXDirection,20\n")
            file.write("NumberofElementinYDirection,20\n")
            file.write("NumberofElementinThickness,3\n")
        aPolygon = self.pkg.polygons[0]
        ith = 0 
        file.write("Part,Polynomial,Solid,1\n")
        for aVertex in aPolygon.vertices:
            if aVertex != None:
                x = aVertex.x
                y = aVertex.y
                
                if ith == 0:
                    file.write("OB {x} {y} I\n".format(x=format(x,".3e"),y=format(y,".3e")))
                else:
                    file.write("OS {x} {y}\n".format(x=format(x,".3e"),y=format(y,".3e")))                                
                    
                ith = ith + 1
        
        file.write("OE\n")        
    
        if generateMesh == True:
            file.write("MaterialID,2\n")
            file.write("*Material\n")
            file.write("Material.txt\n")
        file.write("*End")      
    
    def ExportTop(self, file, pkgZLocation, generateMesh = False):
        self.Export(file, pkgZLocation, True, generateMesh)
    
    def ExportBottom(self, file, pkgZLocation, generateMesh = False):
        self.Export(file, pkgZLocation, False, generateMesh)
    
    def Export(self,file, pkgZLocation, isTop = False, generateMesh = False):
        file.write("*Translation,{x},{y},{z}\n".format(x=self.origin_x,y=self.origin_y,z=pkgZLocation + self.origin_z))
        file.write("*Rotation,{rot}\n".format(rot=self.rotation))
        file.write("*Mirror,{mir}\n".format(mir=self.mirror))
        if isTop == True:
            file.write("*IsTop,True\n")        
        else:
            file.write("*IsTop,False\n")
        file.write("*Layer,SolderJoint\n")
        file.write("Location,{x},{y},{z}\n".format(x=0,y=0,z=0.0))
        boundaryBox = self.BoundaryBox()
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,".3e"),yLength=format(yLength,".3e")))
        file.write("Thickness,{thick}\n".format(thick=format(self.solderjoint_thickness,".3e")))
        if generateMesh == True:
            file.write("MeshGenerationType,Solid,Tetra\n")
            file.write("MeshPath,PackageMesh\n")
            file.write("MeshSizeInPlane,0.1\n")
            file.write("NumberofElementinThickness,5\n")
            file.write("MaterialID,1\n")
        #file.write("DetailSolder,True\n")
        file.write("MisalignmentAngle,0,0.0\n")
        file.write("SurfaceTension,480.0\n")
        ith = 0
        for aPolygon in self.pkg.polygons:
            if aPolygon == None:
                continue
            aPolygon : Polygon2D = aPolygon
            if ith == 0:
                pass
            else:                
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    file.write("Cylinder,{x},{y},{r}\n".format(x=format(aVertex.x,".3e"),y=format(aVertex.y,".3e"),r=format(aVertex.r,".3e")))
                elif aPolygon.type == "RC":
                    xmin = aVertex.x
                    ymin = aVertex.y
                    delX = aPolygon.vertices[2].x - xmin
                    delY = aPolygon.vertices[2].y - ymin
                    file.write("Box,{x},{y},{delX},{delY}\n".format(x=format(xmin,".3e"),y=format(ymin,".3e"),delX=format(delX,".3e"),delY=format(delY,".3e")))                                    
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
                    print("Unknown Type")
                    continue
            ith = ith + 1 
        file.write("*Layer,Package\n")
        file.write("Location,{x},{y}\n".format(x=0,y=0))
        aPolygon = self.pkg.polygons[0]
        boundaryBox = self.BoundaryBox()
        xmin = boundaryBox[0] - self.origin_x
        ymin = boundaryBox[2] - self.origin_y
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]


        file.write("Thickness,{thick}\n".format(thick=format(self.package_thickness,".3e")))
        file.write("Length,{xLength},{yLength}\n".format(xLength=format(xLength,".3e"),yLength=format(yLength,".3e")))
        if generateMesh == True:
            file.write("MeshGenerationType,Solid,Hexa\n")
            file.write("MeshPath,PackageMesh\n")
            file.write("MeshSizeInPlane,0.1\n")
            file.write("NumberofElementinXDirection,20\n")
            file.write("NumberofElementinYDirection,20\n")
            file.write("NumberofElementinThickness,3\n")
            file.write("MaterialID,2\n")
            file.write("*Material\n")
            file.write("Material.txt\n")
        file.write("*End")      
        pass
    
       

    '''def ExportBottom(self,file, pkgZLocation):
        self.ExportTop(file, pkgZLocation)
        file.write("*Layer,Package\n")
        file.write("Location,{x},{y},{z}\n".format(x=0,y=0,z= -pkgZLocation + self.origin_z - self.solderjoint_thickness - self.package_thickness))
        boundaryBox = self.BoundaryBox()
        xmin = boundaryBox[0] - self.origin_x
        ymin = boundaryBox[2] - self.origin_y
        xLength = boundaryBox[1] - boundaryBox[0]
        yLength = boundaryBox[3] - boundaryBox[2]
        file.write("Thickness,{thick}\n".format(thick=self.package_thickness))
        file.write("Box,{x},{y},{xLength},{yLength}\n".format(x=xmin,y=ymin,xLength=xLength,yLength=yLength))

        file.write("*Layer,SolderJoint\n")
        file.write("Location,{x},{y}\n".format(x=0,y=0))

        file.write("Length,{xLength},{yLength}\n".format(xLength=xLength,yLength=yLength))
        file.write("Thickness,{thick}\n".format(thick=self.solderjoint_thickness))
        ith = 0
        for aPolygon in self.pkg.polygons:
            if aPolygon == None:
                continue
            aPolygon : Polygon2D = aPolygon
            if ith == 0:
                pass
            else:                
                aVertex : Vertex2D = aPolygon.vertices[0]
                if aPolygon.type == "CR":
                    file.write("Circle,{x},{y},{r}\n".format(x=aVertex.x,y=aVertex.y,r=aVertex.r))
                elif aPolygon.type == "RC":
                    xmin = aVertex.x
                    ymin = aVertex.y
                    delX = aPolygon.vertices[2].x - xmin
                    delY = aPolygon.vertices[2].y - ymin
                    file.write("Box,{x},{y},{delX},{delY}\n".format(x=xmin,y=ymin,delX=delX,delY=delY))                                    
                else:
                    print("Unknown Type")
                    exit()

            ith = ith + 1 
            '''

class CapacitorComponent(PackageComponent):

    def __init__(self,id,pkg):
        super(CapacitorComponent,self).__init__(id,pkg)
        self.capacitor = Capacitor()
    

    #def SetCapacitor(self):
        #pkg.
        
