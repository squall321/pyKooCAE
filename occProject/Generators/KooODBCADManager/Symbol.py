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

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.gp import gp_Vec, gp_Pnt, gp_Elips
from OCC.Core.gp import gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.gp import gp_Vec
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

class BasicSymbol():
    def __init__(self, name):
        self.name = name
        self.type = None
        self.valueList = [] 

    def SetName(self, name):
        self.name = name 
    
    def SetSymbol(self, type, unit):
        self.name = type 
        #type is string and check include "Round", "Rectangle", "Line" partially
        if "rect" in type.lower():
            type = type.lower().replace("rect", "")
            mode = 0 
            if "r" in type:
                type = type.replace("r", "")   
                mode = 1
            elif "c" in type:
                type = type.replace("c", "")   
                mode = 2
            
            if mode == 0:
                self.type = "Rectangle"
            elif mode == 1:
                self.type = "RoundedRectangle"
            elif mode == 2:
                self.type = "ChemferedRectangle"
            type = type.split("x")
            if mode == 0:
                self.valueList = [unit*float(type[0]), unit*float(type[1])]
            else:
                if len(type) == 3:
                    self.valueList = [unit*float(type[0]), unit*float(type[1]), unit*float(type[2]), "1234"]
                elif len(type) == 4:
                    self.valueList = [unit*float(type[0]), unit*float(type[1]), unit*float(type[2]), type[3]]
                    
        
        elif "oval" in type.lower():
            type = type.lower().replace("oval", "")
            self.type = "Oval"
            
            type = type.split("x")            
            self.valueList = [unit*float(type[0]), unit*float(type[1])]
                
        elif "donut_s" in type.lower():
            type = type.lower().replace("donut_s", "")
            self.type = "Donut_Square"
            type = type.split("x")
            self.valueList = [unit*float(type[0]), unit*float(type[1])]
        elif "donut_r" in type.lower() or "donut_r" in type.lower():
            type = type.lower().replace("donut_r", "")
            self.type = "Donut_Round"
            type = type.split("x")
            self.valueList = [unit*float(type[0]), unit*float(type[1])] 
        elif "s" in type.lower():
            type = type.lower().replace("s", "")
            self.type = "Square"
            self.valueList = [unit*float(type)]        
        # x is not included in type        
        elif "r" in type.lower():
            type = type.lower().replace("r", "")
            self.type = "Round"
            self.valueList = [unit*float(type)]        
        else:
            self.type = None


    def IsPointInsideofSymbol(self, originX, originY, pointXList : list, pointYList : list):
        if self.type == "Round":
            if len(pointXList) == 1:
                delx = originX - pointXList[0]
                dely = originY - pointYList[0]
                length = (delx**2 + dely**2)**0.5
                if length <= self.valueList[0]/2.0:
                    return True
                else:
                    return False
            elif len(pointXList) == 2:
                xs = pointXList[0]
                xe = pointXList[1]
                ys = pointYList[0]
                ye = pointYList[1]
                length = ((xs-xe)**2 + (ys-ye)**2)**0.5
                VACx = xe - xs
                VACy = ye - ys
                costheta = 0.0
                sintheta = -1.0
                VA1x = self.valueList[0] / length *(VACx*costheta - VACy*sintheta)
                VA1y = self.valueList[0] / length *(VACx*sintheta + VACy*costheta)

                P1x = xs + VA1x
                P1y = ys + VA1y

                P2x = P1x + VACx
                P2y = P1y + VACy

                P3x = P2x - 2*VA1x
                P3y = P2y - 2*VA1y
                
                P4x = P3x - VACx
                P4y = P3y - VACy
                xGeom = []
                yGeom = [] 
                xGeom.append(P1x)
                xGeom.append(P2x)
                xGeom.append(P3x)
                xGeom.append(P4x)
                yGeom.append(P1y)
                yGeom.append(P2y)
                yGeom.append(P3y)
                yGeom.append(P4y)

                if self.IsInsideList(originX, originY, xGeom, yGeom):
                    return True
                if self.IsInside(originX, originY, pointXList[0], pointYList[0]):
                    return True
                if self.IsInside(originX, originY, pointXList[1], pointYList[1]):
                    return True
                else:
                    return False
                
        else:            
            if self.IsInsideList(originX, originY, pointXList, pointYList):
                return True
            else:
                return False
    
    def IsInsideList(self, originX, originY, pointXList : list, pointYList : list):
        crosses = 0 
        if type(pointXList[0]) == list:
            # 다중 폴리곤 처리
            for i in range(len(pointXList)):
                n = len(pointXList[i])
                for j in range(n):
                    y1 = pointYList[i][j]
                    y2 = pointYList[i][(j + 1) % n]
                    if (y1 > originY) != (y2 > originY):  # 서로 다른 쪽에 있을 때
                        x1 = pointXList[i][j]
                        x2 = pointXList[i][(j + 1) % n]
                        atX = (x2 - x1) * (originY - y1) / (y2 - y1) + x1
                        if originX < atX:
                            crosses += 1
        else:
            # 단일 폴리곤 처리
            n = len(pointXList)
            for i in range(n):
                j = (i + 1) % n
                y1 = pointYList[i]
                y2 = pointYList[j]
                if (y1 > originY) != (y2 > originY):  # 서로 다른 쪽에 있을 때
                    x1 = pointXList[i]
                    x2 = pointXList[j]
                    atX = (x2 - x1) * (originY - y1) / (y2 - y1) + x1
                    if originX < atX:
                        crosses += 1
        return crosses % 2 == 1                    

    def IsInside(self, originX, originY, pointX : float, pointY : float):        
        if self.type == "Rectangle" or self.type == "RoundedRectangle" or self.type == "ChemferedRectangle":
            xmin = originX - self.valueList[0]/2.0
            xmax = originX + self.valueList[0]/2.0
            ymin = originY - self.valueList[1]/2.0
            ymax = originY + self.valueList[1]/2.0
            if pointX > xmax or pointX < xmin:
                return False
            if pointY > ymax or pointY < ymin:
                return False
            return True
        elif self.type == "Oval":
            delX = pointX - originX
            delY = pointY - originY
            if delX**2/self.valueList[0]**2 + delY**2/self.valueList[1]**2 <= 1.0:
                return True
            else:
                return False
        elif self.type == "Square":
            xmin = originX - self.valueList[0]/2.0
            xmax = originX + self.valueList[0]/2.0
            ymin = originY - self.valueList[0]/2.0
            ymax = originY + self.valueList[0]/2.0
            if pointX > xmax or pointX < xmin:
                return False
            if pointY > ymax or pointY < ymin:
                return False
            return True
        elif self.type == "Round":
            delX = pointX - originX
            delY = pointY - originY
            length = (delX**2 + delY**2)**0.5
            if length > self.valueList[0]/2.0:
                return False
            else:
                return True
        elif self.type == "Donut_Round":
            print("Not implemented yet")
        elif self.type == "Donut_Square":
            print("Not implemented yet")
        else:
            print("Not implemented yet")
            return -1

    def IsBasicSymbol(self, type):
        svector = type.split(' ')
        if svector[0].lower() == "r":
            return True
        if svector[0].lower() == "rect":
            return True
        if svector[0].lower() == "oval":
            return True
        if svector[0].lower() == "s":
            return True        
        else:
            return False
    
    def GetMinMax(self):
        if self.type == "Round":
            xmin = -self.valueList[0]/2.0
            xmax = self.valueList[0]/2.0
            ymin = -self.valueList[0]/2.0
            ymax = self.valueList[0]/2.0

        elif self.type == "Rectangle":
            xmin = -self.valueList[0]/2.0
            xmax = self.valueList[0]/2.0
            ymin = -self.valueList[1]/2.0
            ymax = self.valueList[1]/2.0
        elif self.type == "Line":
            xmin = -self.valueList[0]/2.0
            xmax = self.valueList[0]/2.0
            ymin = -self.valueList[0]/2.0
            ymax = self.valueList[0]/2.0
        elif self.type == "Oval":
            xmin = -self.valueList[0]/2.0
            xmax = self.valueList[0]/2.0
            ymin = -self.valueList[1]/2.0
            ymax = self.valueList[1]/2.0
        else:
            xmin = 0.0
            ymin = 0.0
            xmax = 0.0
            ymax = 0.0 
        return xmin, ymin, xmax, ymax
    
    
    def GetShapeBasic(self, xLoc, yLoc, zLoc, thickness):
        shapeList = [] 
        xmin = 1.0e99
        ymin = 1.0e99
        xmax = -1.0e99
        ymax = -1.0e99
        
        if self.type == "Round":
            # Make a circle
            radius = self.valueList[0]/2.0
            xmin = xLoc - radius
            xmax = xLoc + radius
            ymin = yLoc - radius
            ymax = yLoc + radius
                        
            center = gp_Pnt(xLoc, yLoc, zLoc)
            normal = gp_Dir(0, 0, 1)
            
            circle_geom = gp_Circ(gp_Ax2(center, normal), radius)            
            circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
            circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
            circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(circle_face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)
            
        elif self.type == "Square":    
            xSize = self.valueList[0]/2.0
            ySize = self.valueList[0]/2.0
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            
            p1 = gp_Pnt(xLoc - xSize, yLoc - ySize, zLoc)
            p2 = gp_Pnt(xLoc + xSize, yLoc - ySize, zLoc)
            p3 = gp_Pnt(xLoc + xSize, yLoc + ySize, zLoc)
            p4 = gp_Pnt(xLoc - xSize, yLoc + ySize, zLoc)
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
            edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
            wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3, edge4).Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()
            vec = gp_Vec(0,0,thickness)
            prism_shape = BRepPrimAPI_MakePrism(face, vec)
            prism_shape.Build()
            shape = prism_shape.Shape()
            shapeList.append(shape)
            
        elif self.type == "Rectangle":
            xSize = self.valueList[0]/2.0
            ySize = self.valueList[1]/2.0
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            
            p1 = gp_Pnt(xLoc - xSize, yLoc - ySize, zLoc)
            p2 = gp_Pnt(xLoc + xSize, yLoc - ySize, zLoc)
            p3 = gp_Pnt(xLoc + xSize, yLoc + ySize, zLoc)
            p4 = gp_Pnt(xLoc - xSize, yLoc + ySize, zLoc)
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
            edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
            wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3, edge4).Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()
            vec = gp_Vec(0,0,thickness)
            prism_shape = BRepPrimAPI_MakePrism(face, vec)
            prism_shape.Build()
            shape = prism_shape.Shape()
            shapeList.append(shape)
        elif self.type == "RoundedRectangle":
            xSize = self.valueList[0]/2.0
            ySize = self.valueList[1]/2.0
            radius = self.valueList[2]
            radiuslocation = self.valueList[3]
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            xminpradius = xLoc - xSize + radius
            xmaxpradius = xLoc + xSize - radius
            yminpradius = yLoc - ySize + radius
            ymaxpradius = yLoc + ySize - radius
            
            edgeList = [] 
            normal_vector = gp_Dir(0, 0, 1)
            if "1" in radiuslocation:
                p0 = gp_Pnt(xmax,ymaxpradius,zLoc)
                p1 = gp_Pnt(xmaxpradius,ymaxpradius,zLoc)
                p2 = gp_Pnt(xmaxpradius,ymax,zLoc)
                coordinate_system = gp_Ax2(p1, normal_vector)
                arc1 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius), p0, p2)
            else:
                p0 = gp_Pnt(xmax, ymax, zLoc)
                p2 = gp_Pnt(xmax, ymax, zLoc)
                arc1 = None 
            if arc1 is not None:
                edgeList.append(arc1.Edge())
            
            if "2" in radiuslocation:
                p3 = gp_Pnt(xminpradius, ymax, zLoc)
                p4 = gp_Pnt(xminpradius, ymaxpradius, zLoc)
                p5 = gp_Pnt(xmin, ymaxpradius, zLoc)
                coordinate_system = gp_Ax2(p4,normal_vector)                
                arc2 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p3,p5)
                
            else:
                p3 = gp_Pnt(xmin, ymax, zLoc)
                p5 = gp_Pnt(xmin, ymax, zLoc)
                arc2 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p2,p3).Edge())
            if arc2 is not None:
                edgeList.append(arc2.Edge())
                            
            if "3" in radiuslocation:
                p6 = gp_Pnt(xmin, yminpradius, zLoc)
                p7 = gp_Pnt(xminpradius, yminpradius, zLoc)
                p8 = gp_Pnt(xminpradius, ymin, zLoc)                
                coordinate_system = gp_Ax2(p7,normal_vector)
                arc3 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p6,p8)    
            else:
                p6 = gp_Pnt(xmin, ymin, zLoc)
                p8 = gp_Pnt(xmin, ymin, zLoc)
                arc3 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p5,p6).Edge())
            if arc3 is not None:
                edgeList.append(arc3.Edge())
            
            
            if "4" in radiuslocation:
                p9 = gp_Pnt(xmaxpradius, ymin, zLoc)
                p10 = gp_Pnt(xmaxpradius, yminpradius, zLoc)
                p11 = gp_Pnt(xmax, yminpradius, zLoc)
                coordinate_system = gp_Ax2(p10,normal_vector)
                arc4 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p9,p11)                
            else:
                p9 = gp_Pnt(xmax, ymin, zLoc)
                p11 = gp_Pnt(xmax, ymin, zLoc)
                arc4 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p8,p9).Edge())
            if arc4 is not None:
                edgeList.append(arc4.Edge())                
            edgeList.append(BRepBuilderAPI_MakeEdge(p11,p0).Edge())
            
            wire = BRepBuilderAPI_MakeWire()
            for edge in edgeList:
                wire.Add(edge)
            face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
            vec = gp_Vec(0,0,thickness)
            prismShape = BRepPrimAPI_MakePrism(face,vec)
            prismShape.Build()
            shape = prismShape.Shape()
            shapeList.append(shape)
            pass
        elif self.type == "Oval":
            r1 = self.valueList[0]/2.0
            r2 = self.valueList[1]/2.0
            if r1>r2: 
                major_r1 = r1
                major_r2 = r2
                xdir = gp_Dir(1,0,0)
            else:
                major_r1 = r2
                major_r2 = r1
                xdir = gp_Dir(0,1,0)
            
            center_point = gp_Pnt(xLoc, yLoc, zLoc)
            major_axis = gp_Dir(0,0,1)
            axis2_placement = gp_Ax2(center_point, major_axis, xdir)
            
            ellipse_geom = gp_Elips(axis2_placement, major_r1, major_r2)
            ellipse_edge = BRepBuilderAPI_MakeEdge(ellipse_geom).Edge()
            ellipse_wire = BRepBuilderAPI_MakeWire(ellipse_edge).Wire()
            ellipse_face = BRepBuilderAPI_MakeFace(ellipse_wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(ellipse_face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)
        elif self.type == "ChemferedRectangle":
            xSize = self.valueList[0]/2.0
            ySize = self.valueList[1]/2.0
            radius = self.valueList[2]
            radiuslocation = self.valueList[3]
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            xminpradius = xLoc - xSize + radius
            xmaxpradius = xLoc + xSize - radius
            yminpradius = yLoc - ySize + radius
            ymaxpradius = yLoc + ySize - radius
            edgeList = []
            if "1" in radiuslocation:
                p0 = gp_Pnt(xmax, ymaxpradius, zLoc)
                p1 = gp_Pnt(xmaxpradius, ymax, zLoc)
                edge1 = BRepBuilderAPI_MakeEdge(p0, p1).Edge()
            else:
                p0 = gp_Pnt(xmax, ymax, zLoc)
                p1 = gp_Pnt(xmax, ymax, zLoc)
                edge1 = None
            if edge1 is not None:
                edgeList.append(edge1)
            
            if "2" in radiuslocation:
                p2 = gp_Pnt(xminpradius, ymax, zLoc)
                p3 = gp_Pnt(xmin, ymaxpradius, zLoc)
                edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            else:
                p2 = gp_Pnt(xmin, ymax, zLoc)
                p3 = gp_Pnt(xmin, ymax, zLoc)
                edge2 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
            if edge2 is not None:
                edgeList.append(edge2)
                
            if "3" in radiuslocation:
                p4 = gp_Pnt(xmin, yminpradius, zLoc)
                p5 = gp_Pnt(xminpradius, ymin, zLoc)
                edge3 = BRepBuilderAPI_MakeEdge(p4, p5).Edge()
            else:
                p4 = gp_Pnt(xmin, ymin, zLoc)
                p5 = gp_Pnt(xmin, ymin, zLoc)
                edge3 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p3, p4).Edge())
            if edge3 is not None:
                edgeList.append(edge3)
            
            if "4" in radiuslocation:
                p6 = gp_Pnt(xmaxpradius, ymin, zLoc)
                p7 = gp_Pnt(xmax, yminpradius, zLoc)
                edge4 = BRepBuilderAPI_MakeEdge(p6, p7).Edge()
            else:
                p6 = gp_Pnt(xmax, ymin, zLoc)
                p7 = gp_Pnt(xmax, ymin, zLoc)
                edge4 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p5, p6).Edge())
            if edge4 is not None:
                edgeList.append(edge4)
            edgeList.append(BRepBuilderAPI_MakeEdge(p7, p0).Edge())
            
            wire = BRepBuilderAPI_MakeWire()
            for edge in edgeList:
                wire.Add(edge)
            face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
            vec = gp_Vec(0,0,thickness)
            prismShape = BRepPrimAPI_MakePrism(face,vec)
            prismShape.Build()
            shape = prismShape.Shape()
            shapeList.append(shape)                                      
            pass
        else:
            print("Not implemented yet")
            return -1
    
        return shapeList
            

from typing import List
    
class Symbol(BasicSymbol):
    def __init__(self, name = None, xPosListList = None, yPosListList = None, xPosCutListList = None, yPosCutListList = None):

        super(Symbol, self).__init__(name)
        self.PCenterList: List[Point] = []
        self.LStartList: List[Point] = []
        self.LEndList: List[Point] = []

        self.AStartList: List[Point] = []
        self.AEndList: List[Point] = [] 
        self.ACenterList: List[Point] = []

        self.xPosListList = [] 
        self.yPosListList = [] 
        self.xPosCutListList = []
        self.yPosCutListList = []
        self.clockwiseList = []
        self.symbolIDList = [] 
        self.polarityList = [] 

        self.symbolMap = {} 
        if xPosListList != None and yPosListList != None:
            self.SetPosVector(xPosListList, yPosListList)
        if xPosCutListList != None and yPosCutListList != None:
            self.SetPosCutVector(xPosCutListList, yPosCutListList)

    def SetPosVector(self, xPosListList, yPosListList):
        self.xPosListList.clear()        
        self.yPosListList.clear()

        #xPostList is 2D list 
        for xPosList in xPosListList:
            newXPosList = []
            for xPos in xPosList:
                newXPosList.append(xPos)
            self.xPosListList.append(newXPosList)
        
        for yPosList in yPosListList:
            newYPosList = []
            for yPos in yPosList:
                newYPosList.append(yPos)
            self.yPosListList.append(newYPosList)
            
    def SetPosCutVector(self, xPosCutListList, yPosCutListList):
        self.xPosCutListList.clear()        
        self.yPosCutListList.clear()

        #xPostList is 2D list 
        for xPosCutList in xPosCutListList:
            newXPosCutList = []
            for xPos in xPosCutList:
                newXPosCutList.append(xPos)
            self.xPosCutListList.append(newXPosCutList)
        
        for yPosCutList in yPosCutListList:
            newYPosCutList = []
            for yPos in yPosCutList:
                newYPosCutList.append(yPos)
            self.yPosCutListList.append(newYPosCutList)
    
    def ImportSymbolsfromLines(self, lines, udMap):
        unit = 1.0         
        curPolarity = 1.0            
        # read file
        for i in range(len(lines)):            
            
            # read line
            line = lines[i]
            # Process the current line
            #print(line.strip())  # Print the line after removing leading/trailing whitespace

            string_vector = line.split(' ')
            firstString = string_vector[0]
            firstChar = firstString[0]

            if firstChar == "U":
                if "INCH" in line:
                    unit = unit *25.4
                elif "MM" in line:
                    unit = unit *1.0
            elif firstChar == "$":
                symbolName = string_vector[1]
                symbolcurId = int(string_vector[0].replace("$", ""))
                # udMap is dictionary with symbolName, Symbol object 
                # I want to find symbolName in udMap
                if symbolName in udMap:
                    aSymbol = udMap[symbolName]
                else:
                    aSymbol = Symbol(symbolName)
                    curunit = unit*0.001
                    aSymbol.SetSymbol(symbolName, curunit)
                self.symbolMap.update({symbolcurId : aSymbol})
            elif firstChar == "P":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                xi = unit* float(string_vector[1])
                yi = unit* float(string_vector[2])
                symid = int(string_vector[3])
                xList = [] 
                yList = [] 
                xList.append(xi)
                yList.append(yi)
                self.xPosListList.append(xList)
                self.yPosListList.append(yList)
                self.symbolIDList.append(symid)
                self.polarityList.append(curPolarity)

            elif firstChar == "L":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                xi = unit* float(string_vector[1])
                yi = unit* float(string_vector[2])
                xf = unit* float(string_vector[3])
                yf = unit* float(string_vector[4])
                symid = int(string_vector[5])
                xList = []
                yList = []
                xList.append(xi)
                xList.append(xf)
                yList.append(yi)
                yList.append(yf)
                self.xPosListList.append(xList)
                self.yPosListList.append(yList)
                self.symbolIDList.append(symid)
                self.polarityList.append(curPolarity)
                
            elif firstChar == "A":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                xi = unit* float(string_vector[1])
                yi = unit* float(string_vector[2])
                xf = unit* float(string_vector[3])
                yf = unit* float(string_vector[4])
                xc = unit* float(string_vector[5])
                yc = unit* float(string_vector[6])
                symid = int(string_vector[7])
                xList = []
                yList = []
                xList.append(xi)
                xList.append(xf)
                yList.append(yi)
                yList.append(yf)
                xList.append(xc)
                yList.append(yc)
                self.xPosListList.append(xList)
                self.yPosListList.append(yList)
                self.symbolIDList.append(symid)
                self.polarityList.append(curPolarity)
            elif firstChar == "S":
                if "N" in line:
                    curPolarity = 0 
                else:
                    curPolarity = 1
            elif "OB" in line:
                
                xStart = unit* float(string_vector[1])
                yStart = unit* float(string_vector[2])
                if "I" in string_vector[3]:
                    cutXposMode = 0
                else:
                    cutXposMode = 1
                #xList = [] 
                #yList = [] 
                #self.polarityList.append(curPolarity)
                #xList.append(unit* float(string_vector[1]))
                #yList.append(unit* float(string_vector[2]))
                xMat = []
                yMat = []
                clockwise = []
                for j in range(i+1, len(lines)):
                    line = lines[j]
                    if "OE" in line:
                        break
                    line = line.replace("\n", "")
                    string_vector = line.split(' ')
                    if "OS" in line:
                        xEnd = unit* float(string_vector[1])
                        yEnd = unit* float(string_vector[2])
                        xList = [xStart, xEnd]
                        yList = [yStart, yEnd]
                        xMat.append(xList)
                        yMat.append(yList)
                        clockwise.append(None)
                        xStart = xEnd
                        yStart = yEnd
                        
                    elif "OC" in line:
                        xEnd = unit* float(string_vector[1])
                        yEnd = unit* float(string_vector[2])
                        xCenter = unit* float(string_vector[3])
                        yCenter = unit* float(string_vector[4])
                        cw = string_vector[5]
                        if cw.lower() == "y":
                            clockwise.append(1)
                        else:
                            clockwise.append(0)
                        
                        xList = [xStart, xEnd, xCenter]
                        yList = [yStart, yEnd, yCenter]
                        xMat.append(xList)
                        yMat.append(yList)
                        xStart = xEnd
                        yStart = yEnd
                
                if cutXposMode == 0:
                    self.xPosListList.append(xMat)
                    self.yPosListList.append(yMat)
                    self.clockwiseList.append(clockwise)
                    self.polarityList.append(curPolarity)    
                    self.symbolIDList.append(-1)
                else:
                    self.xPosCutListList.append(xMat)
                    self.yPosCutListList.append(yMat)
                    
                
            
    
    def ImportSymbols(self,fileName, udMap):
        unit = 1.0 
        
    
        # read file
        with open(fileName, 'r') as file:
            print("Importing Symbols")
            curPolarity = 1.0 
            # read line
            line = file.readline()
            while line:                                    
                # Process the current line
                print(line.strip())  # Print the line after removing leading/trailing whitespace

                string_vector = line.split(' ')
                firstString = string_vector[0]
                firstChar = firstString[0]

                if firstChar == "U":
                    if "INCH" in line:
                        unit = unit *25.4
                    elif "MM" in line:
                        unit = unit *1.0
                elif firstChar == "$":
                    symbolName = string_vector[1]
                    symbolcurId = int(string_vector[0].replace("$", ""))
                    # udMap is dictionary with symbolName, Symbol object 
                    # I want to find symbolName in udMap
                    if udMap.has_key(symbolName) == False:
                        aSymbol = Symbol(symbolName)
                        curunit = unit*0.001
                        aSymbol.SetSymbol(symbolName, curunit)
                    else:
                        aSymbol = udMap[symbolName]
                    self.symbolMap.update({symbolcurId : aSymbol})
                elif firstChar == "P":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    xi = unit* float(string_vector[1])
                    yi = unit* float(string_vector[2])
                    symid = int(string_vector[3])
                    xList = [] 
                    yList = [] 
                    xList.append(xi)
                    yList.append(yi)
                    self.xPosListList.append(xList)
                    self.yPosListList.append(yList)
                    self.symbolIDList.append(symid)
                    self.polarityList.append(curPolarity)

                elif firstChar == "L":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    xi = unit* float(string_vector[1])
                    yi = unit* float(string_vector[2])
                    xf = unit* float(string_vector[3])
                    yf = unit* float(string_vector[4])
                    symid = int(string_vector[5])
                    xList = []
                    yList = []
                    xList.append(xi)
                    xList.append(xf)
                    yList.append(yi)
                    yList.append(yf)
                    self.xPosListList.append(xList)
                    self.yPosListList.append(yList)
                    self.symbolIDList.append(symid)
                    self.polarityList.append(curPolarity)
                    
                elif firstChar == "A":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    xi = unit* float(string_vector[1])
                    yi = unit* float(string_vector[2])
                    xf = unit* float(string_vector[3])
                    yf = unit* float(string_vector[4])
                    xc = unit* float(string_vector[5])
                    yc = unit* float(string_vector[6])
                    symid = int(string_vector[5])
                    xList = []
                    yList = []
                    xList.append(xi)
                    xList.append(xf)
                    yList.append(yi)
                    yList.append(yf)
                    xList.append(xc)
                    yList.append(yc)
                    self.xPosListList.append(xList)
                    self.yPosListList.append(yList)
                    self.symbolIDList.append(symid)
                    self.polarityList.append(curPolarity)
                elif firstChar == "S":
                    if "N" in line:
                        curPolarity = 0 
                    else:
                        curPolarity = 1
                elif "OB" in line:
                    
                    xStart = unit* float(string_vector[1])
                    yStart = unit* float(string_vector[2])
                    if "I" in string_vector[3]:
                        cutXposMode = 0
                    else:
                        cutXposMode = 1
                    xMat = []
                    yMat = []
                    clockwise = []
                    while True:
                        line = file.readline()
                        if "OE" in line:
                            break
                        line = line.replace("\n", "")
                        string_vector = line.split(' ')
                        if "OS" in line:
                            xEnd = unit* float(string_vector[1])
                            yEnd = unit* float(string_vector[2])
                            xList = [xStart, xEnd]
                            yList = [yStart, yEnd]
                            xMat.append(xList)
                            yMat.append(yList)
                            clockwise.append(None)
                           
                            xStart = xEnd
                            yStart = yEnd
                        elif "OC" in line:
                            xEnd = unit* float(string_vector[1])
                            yEnd = unit* float(string_vector[2])
                            xCenter = unit* float(string_vector[3])
                            yCenter = unit* float(string_vector[4])
                            cw = string_vector[5]
                            if cw.lower() == "y":
                                clockwise.append(1)
                            else:
                                clockwise.append(0)
                            
                            xList = [xStart, xEnd, xCenter]
                            yList = [yStart, yEnd, yCenter]
                            xMat.append(xList)
                            yMat.append(yList)
                            xStart = xEnd
                            yStart = yEnd
                
                    if cutXposMode == 0:
                        self.xPosListList.append(xMat)
                        self.yPosListList.append(yMat)
                        self.clockwiseList.append(clockwise)
                        self.polarityList.append(curPolarity)    
                        self.symbolIDList.append(-1)
                    else:
                        self.xPosCutListList.append(xMat)
                        self.yPosCutListList.append(yMat)

                # Read the next line
                line = file.readline()                
    
    def GetMinMax(self):
        xmin = 1.e99
        ymin = 1.e99
        xmax = -1.e99
        ymax = -1.e99

        if len(self.xPosListList) == 0:
            return super().GetMinMax()
        
        for i in range(len(self.xPosListList)):
            for j in range(len(self.xPosListList[i])):
                if type(self.xPosListList[i][j]) == list:
                    for k in range(len(self.xPosListList[i][j])):
                        xmin = min(xmin, self.xPosListList[i][j][k])
                        xmax = max(xmax, self.xPosListList[i][j][k])
                        ymin = min(ymin, self.yPosListList[i][j][k])
                        ymax = max(ymax, self.yPosListList[i][j][k])
                else:
                    xmin = min(xmin, self.xPosListList[i][j])
                    xmax = max(xmax, self.xPosListList[i][j])
                    ymin = min(ymin, self.yPosListList[i][j])
                    ymax = max(ymax, self.yPosListList[i][j])
        return xmin, ymin, xmax, ymax
    
    def IsInsideList(self, originX, originY, pointXList: list, pointYList: list):
        return super().IsInsideList(originX, originY, pointXList, pointYList)
    
    def IsInside(self, originX, originY, pointX: float, pointY: float):
        if self.type == None:
            for i in range(len(self.symbolIDList)):
                if self.symbolIDList[i] == -1:
                    if self.IsInsideList(originX-pointX, originY-pointY, self.xPosListList[i], self.yPosListList[i]):
                        return True
                elif self.symbolMap.has_key(self.symbolIDList[i]):
                    aSymbol = self.symbolMap[self.symbolIDList[i]]
                    
                    if aSymbol.IsInside(originX, originY, pointX, pointY):
                        return True
        else:
            return super().IsInside(originX, originY, pointX, pointY)
        return False
    
    def GetShape(self, xLoc, yLoc, zLoc, thickness):
        
        shapeList = []
        for i in range(len(self.symbolIDList)):
            xPosList = self.xPosListList[i]
            yPosList = self.yPosListList[i]
            polygon_builder = BRepBuilderAPI_MakePolygon()
            if self.type is not None and self.type.lower() == "round":
                radius = self.valueList[0]/2.0  
                # Make a circle
                center = gp_Pnt(xLoc, yLoc, zLoc)
                normal = gp_Dir(0, 0, 1)
                
                circle_geom = gp_Circ(gp_Ax2(center, normal), radius)            
                circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
                circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
                circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
                vec = gp_Vec(0,0,thickness)
                cylinder_shape = BRepPrimAPI_MakePrism(circle_face,vec)
                cylinder_shape.Build()
                shape = cylinder_shape.Shape()
                shapeList.append(shape)
                 
            if self.symbolIDList[i] == -1:
                try:
                    for j in range(len(xPosList)):
                        polygon_builder.Add(gp_Pnt(xLoc + xPosList[j][0], yLoc + yPosList[j][0], zLoc))
                    wire = polygon_builder.Wire()
                    face = BRepBuilderAPI_MakeFace(wire).Face()
                    vec = gp_Vec(0,0,thickness)
                    prism = BRepPrimAPI_MakePrism(face,vec)
                    shape = prism.Shape()
                    # Check volume: negative means inverted face normals (CW winding)
                    props = GProp_GProps()
                    brepgprop.VolumeProperties(shape, props)
                    if props.Mass() < 0:
                        face.Reverse()
                        prism = BRepPrimAPI_MakePrism(face,vec)
                        shape = prism.Shape()
                    shapeList.append(shape)
                except:
                    print("Error in GetShape")
                    pass
            else:
                aSymbol = self.symbolMap[self.symbolIDList[i]]
                if aSymbol == None:
                    print("Error in GetShape")
                    continue
                else:
                    subShapeList = aSymbol.GetShapeBasic(xLoc, yLoc, zLoc, thickness)
                    if subShapeList == None:
                        print("Error in GetShape")
                        continue
                    if len(subShapeList) == 0:
                        print("Error in GetShape")
                        continue
                    shapeList.extend(subShapeList)
        
        
        for i in range(len(self.xPosCutListList)):
            xPosList = self.xPosCutListList[i]
            yPosList = self.yPosCutListList[i]
            polygon_builder = BRepBuilderAPI_MakePolygon()
            try:
                for j in range(len(xPosList)):
                    polygon_builder.Add(gp_Pnt(xLoc + xPosList[j][0], yLoc + yPosList[j][0], zLoc))
                wire = polygon_builder.Wire()
                face = BRepBuilderAPI_MakeFace(wire).Face()
                vec = gp_Vec(0,0,thickness)
                cutshape = BRepPrimAPI_MakePrism(face,vec).Shape()
                for i in range(len(shapeList)):
                    curShape = shapeList[i]
                    curShape = BRepAlgoAPI_Cut(curShape, cutshape).Shape()
                    if curShape is not None:
                        shapeList[i] = curShape           
            except:
                print("Error in GetShape")
                pass 
        return shapeList
    
        


                    

        








        
        