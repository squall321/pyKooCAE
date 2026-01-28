from __future__ import annotations
import math
import numpy as np 
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
from io import StringIO

from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from scipy.spatial import KDTree
from KooCAEManager.KooOperator import *
class Node:
    __slots__ = ('id','x','y','z','tc','rc','elems',
                'coordinate','displacement','velocity','acceleration',
                'rotation','rotationVelocity','rotationAcceleration')
    def __init__(self,id=0):
        self.id = id
        self.x = 0
        self.y = 0
        self.z = 0
        self.tc = 0
        self.rc = 0
        self.elems = {}

        self.coordinate = []

        self.displacement = []
        self.velocity = []
        self.acceleration = []

        self.rotation = []
        self.rotationVelocity = []
        self.rotationAcceleration = []
        
    def Translate(self, dx, dy, dz):
        self.x = self.x + dx
        self.y = self.y + dy
        self.z = self.z + dz
        
    def Rotate(self, angle=90, axis = (0,0,1), center = (0,0,0)):
        trsf = gp_Trsf()
        trsf.SetRotation(gp_Ax1(gp_Pnt(center[0], center[1], center[2]), gp_Dir(axis[0], axis[1], axis[2])), math.radians(angle))
        pnt = gp_Pnt(self.x, self.y, self.z)
        pnt.Transform(trsf)
        self.x = pnt.X()
        self.y = pnt.Y()
        self.z = pnt.Z()
        
    def Transform(self, trsf : gp_Trsf):
        if trsf is not None:
            pnt = gp_Pnt(self.x, self.y, self.z)
            pnt.Transform(trsf)
            self.x = pnt.X()
            self.y = pnt.Y()
            self.z = pnt.Z()
        
    def GetXYZ(self):
        return (self.x, self.y, self.z)
    
    def Distance(self, node):
        return math.sqrt((self.x - node.x)**2 + (self.y - node.y)**2 + (self.z - node.z)**2)

    def DistancefromPoint(self, x, y, z):
        return math.sqrt((self.x - x)**2 + (self.y - y)**2 + (self.z - z)**2)

    def SetTimeSize(self,size):
        self.displacement = np.zeros((size,3), dtype=np.float32)
        self.velocity = np.zeros((size,3), dtype=np.float32)
        self.acceleration = np.zeros((size,3), dtype=np.float32)
        
        self.rotation = np.zeros((size,3), dtype=np.float32)
        self.rotationVelocity = np.zeros((size,3), dtype=np.float32)
        self.rotationAcceleration = np.zeros((size,3), dtype=np.float32)
    
    def LaplacianSmoothingZ(self):    
        newZ = 0.0
        num = 0.0
        for eid in self.elems:
            elem = self.elems[eid]
            for node in elem.nodes:
                if node.id != self.id:
                    newZ = newZ + node.z
                    num = num + 1.0
        if num > 0.0:
            self.z = newZ / num                   
    
    def ZAxisSmoothingZPrev(self, zDir, w=1.4):
        newD = 0.0
        num = 0.0
        
        for eid in self.elems:
            elem = self.elems[eid]
            for node in elem.nodes:
                if node.id != self.id:
                    disp = np.array([node.x-self.x, node.y-self.y, node.z-self.z])
                    newD += np.dot(disp, zDir)                                   
                    num = num + 1.0
        if num > 0.0:
            newD = newD / num
        new_p = np.array([self.x, self.y, self.z]) + newD * zDir
                
        self.x = (1.0-w)*self.x + w*new_p[0]
        self.y = (1.0-w)*self.y + w*new_p[1]
        self.z = (1.0-w)*self.z + w*new_p[2]
        
    def ZAxisSmoothingZ(self, zDir, w=1.4):
        # 1. 주변 노드 unique set 수집
        neighbor_nodes = set()
        for eid in self.elems:
            elem = self.elems[eid]
            for node in elem.nodes:
                if node.id != self.id:
                    neighbor_nodes.add(node)

        # 2. displacement 평균 계산
        newD = 0.0
        num = 0.0
        for node in neighbor_nodes:
            dx = node.x - self.x
            dy = node.y - self.y
            dz = node.z - self.z

            dot = dx * zDir[0] + dy * zDir[1] + dz * zDir[2]
            newD += dot
            num += 1.0

        if num > 0.0:
            newD /= num

        # 3. 위치 업데이트
        self.x += w * newD * zDir[0]
        self.y += w * newD * zDir[1]
        self.z += w * newD * zDir[2]
        
            
    def LaplacianSmoothing(self):
        newX = 0.0
        newY = 0.0
        newZ = 0.0
        num = 0.0
        for eid in self.elems:
            elem = self.elems[eid]
            for node in elem.nodes:
                
                if node.id != self.id:
                    newX = newX + node.x
                    newY = newY + node.y
                    newZ = newZ + node.z
                    num = num + 1.0
        if num > 0.0:
            self.x = newX / num
            self.y = newY / num
            self.z = newZ / num                   
        

    def SetXYZ(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z     
        
    def Transform(self, trsf : gp_Trsf):
        if trsf is not None:
            pnt = gp_Pnt(self.x, self.y, self.z)
            pnt.Transform(trsf)
            self.x = pnt.X()
            self.y = pnt.Y()
            self.z = pnt.Z()            
    
    def AddDisplacement(self, dispx,dispy,dispz):
        newDisp = [dispx, dispy, dispz]
        self.displacement.append(newDisp)
    
    def SetDisplacement(self, i, dispx, dispy, dispz):
        self.displacement[i][0] = dispx
        self.displacement[i][1] = dispy
        self.displacement[i][2] = dispz
        
    def GetDisplacementSize(self):
        return len(self.displacement)
        
    def GetDisplacement(self, ithStep):
        if len(self.displacement) > ithStep:
            curDisp = self.displacement[ithStep]
        else:
            curDisp = [0,0,0]
        return curDisp
    
    def GetTotalDisplacement(self,ithStep):
        if len(self.displacement) > ithStep:
            curDisp = self.displacement[ithStep]
        else:
            curDisp = [0,0,0]                    
        return math.sqrt(curDisp[0]**2 + curDisp[1]**2 + curDisp[2]**2)
    
    def GetDisplacementX(self, ithStep): 
        if len(self.displacement) > ithStep:
            curDisp = self.displacement[ithStep]
        else:
            curDisp = [0,0,0]
        return curDisp[0]
    
    def GetDisplacementY(self, ithStep):
        if len(self.displacement) > ithStep:
            curDisp = self.displacement[ithStep]
        else:
            curDisp = [0,0,0]
        return curDisp[1]
    
    def GetDisplacementZ(self, ithStep):
        if len(self.displacement) > ithStep:
            curDisp = self.displacement[ithStep]
        else:
            curDisp = [0,0,0]            
        return curDisp[2]

    def GetMaxDisplacement(self):
        maxDisp = -1.0e99
        maxith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = math.sqrt(disp[0]**2 + disp[1]**2 + disp[2]**2)
            if absDisp > maxDisp:
                maxDisp = absDisp
                maxith = ith
            ith = ith + 1        
        return maxith, maxDisp
    
    def GetMaxDisplacementX(self):
        maxDisp = -1.0e99
        maxith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[0]
            if absDisp > maxDisp:
                maxDisp = absDisp
                maxith = ith
            ith = ith + 1        
        return maxith, maxDisp

    def GetMaxDisplacementY(self):
        maxDisp = -1.0e99
        maxith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[1]
            if absDisp > maxDisp:
                maxDisp = absDisp
                maxith = ith
            ith = ith + 1        
        return maxith, maxDisp
    
    def GetMaxDisplacementZ(self):
        maxDisp = -1.0e99
        maxith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[2]
            if absDisp > maxDisp:
                maxDisp = absDisp
                maxith = ith
            ith = ith + 1        
        return maxith, maxDisp  
    
    def GetMinDisplacement(self):
        minDisp = 1.0e99
        minith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = math.sqrt(disp[0]**2 + disp[1]**2 + disp[2]**2)
            if absDisp < minDisp:
                minDisp = absDisp
                minith = ith
            ith = ith + 1        
        return minith, minDisp
    
    def GetMinDisplacementX(self):
        minDisp = 1.0e99
        minith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[0]
            if absDisp < minDisp:
                minDisp = absDisp
                minith = ith
            ith = ith + 1        
        return minith, minDisp
    
    def GetMinDisplacementY(self):
        minDisp = 1.0e99
        minith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[1]
            if absDisp < minDisp:
                minDisp = absDisp
                minith = ith
            ith = ith + 1        
        return minith, minDisp
    
    def GetMinDisplacementZ(self):
        minDisp = 1.0e99
        minith = -1
        ith = 0

        for disp in self.displacement:
            absDisp = disp[2]
            if absDisp < minDisp:
                minDisp = absDisp
                minith = ith
            ith = ith + 1        
        return minith, minDisp
        
    def AddVelocity(self, velx,vely,velz):
        newVel = [velx, vely, velz]
        self.velocity.append(newVel)
    
    def SetVelocity(self, i, velx, vely, velz):
        self.velocity[i] = [velx, vely, velz]

    def GetMaxVelocity(self):
        maxVel = -1.0e99
        maxith = -1
        ith = 0

        for vel in self.velocity:
            absVel = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
            if absVel > maxVel:
                maxVel = absVel
                maxith = ith
            ith = ith + 1        
        return maxith, maxVel

    def GetMaxVelocityX(self):
        maxVel = -1.0e99
        maxith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[0]
            if absVel > maxVel:
                maxVel = absVel
                maxith = ith
            ith = ith + 1        
        return maxith, maxVel

    def GetMaxVelocityY(self):
        maxVel = -1.0e99
        maxith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[1]
            if absVel > maxVel:
                maxVel = absVel
                maxith = ith
            ith = ith + 1        
        return maxith, maxVel
    
    def GetMaxVelocityZ(self):
        maxVel = -1.0e99
        maxith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[2]
            if absVel > maxVel:
                maxVel = absVel
                maxith = ith
            ith = ith + 1        
        return maxith, maxVel   
    
    def GetMinVelocity(self):
        minVel = 1.0e99
        minith = -1
        ith = 0

        for vel in self.velocity:
            absVel = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
            if absVel < minVel:
                minVel = absVel
                minith = ith
            ith = ith + 1        
        return minith, minVel
    
    def GetMinVelocityX(self):
        minVel = 1.0e99
        minith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[0]
            if absVel < minVel:
                minVel = absVel
                minith = ith
            ith = ith + 1        
        return minith, minVel
    
    def GetMinVelocityY(self):  
        minVel = 1.0e99
        minith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[1]
            if absVel < minVel:
                minVel = absVel
                minith = ith
            ith = ith + 1        
        return minith, minVel
    
    def GetMinVelocityZ(self):
        minVel = 1.0e99
        minith = -1
        ith = 0

        for vel in self.velocity:
            absVel = vel[2]
            if absVel < minVel:
                minVel = absVel
                minith = ith
            ith = ith + 1        
        return minith, minVel
        
    def AddAcceleration(self, accx,accy,accz):
        newAcc = [accx, accy, accz]
        self.acceleration.append(newAcc)
    
    def SetAcceleration(self, i, accx, accy, accz): 
        self.acceleration[i] = [accx, accy, accz]

    def GetMaxAcceleration(self):
        maxAcc = -1.0e99
        maxith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = math.sqrt(acc[0]**2 + acc[1]**2 + acc[2]**2)
            if absAcc > maxAcc:
                maxAcc = absAcc
                maxith = ith
            ith = ith + 1        
        return maxith, maxAcc

    def GetMaxAccelerationX(self):
        maxAcc = -1.0e99
        maxith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[0]
            if absAcc > maxAcc:
                maxAcc = absAcc
                maxith = ith
            ith = ith + 1        
        return maxith, maxAcc
    
    def GetMaxAccelerationY(self):
        maxAcc = -1.0e99
        maxith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[1]
            if absAcc > maxAcc:
                maxAcc = absAcc
                maxith = ith
            ith = ith + 1        
        return maxith, maxAcc
    
    def GetMaxAccelerationZ(self):
        maxAcc = -1.0e99
        maxith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[2]
            if absAcc > maxAcc:
                maxAcc = absAcc
                maxith = ith
            ith = ith + 1        
        return maxith, maxAcc
    
    def GetMinAcceleration(self):
        minAcc = 1.0e99
        minith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = math.sqrt(acc[0]**2 + acc[1]**2 + acc[2]**2)
            if absAcc < minAcc:
                minAcc = absAcc
                minith = ith
            ith = ith + 1        
        return minith, minAcc
    
    def GetMinAccelerationX(self):
        minAcc = 1.0e99
        minith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[0]
            if absAcc < minAcc:
                minAcc = absAcc
                minith = ith
            ith = ith + 1        
        return minith, minAcc
    
    def GetMinAccelerationY(self):
        minAcc = 1.0e99
        minith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[1]
            if absAcc < minAcc:
                minAcc = absAcc
                minith = ith
            ith = ith + 1        
        return minith, minAcc
    
    def GetMinAccelerationZ(self):
        minAcc = 1.0e99
        minith = -1
        ith = 0

        for acc in self.acceleration:
            absAcc = acc[2]
            if absAcc < minAcc:
                minAcc = absAcc
                minith = ith
            ith = ith + 1        
        return minith, minAcc
    
    def AddCoordinate(self, coordX, coordY, coordZ):
        newCoord = [coordX, coordY, coordZ]
        self.coordinate.append(newCoord)
    
    def AddRotation(self, rotx,roty,rotz):
        newRot = [rotx, roty, rotz]
        self.rotation.append(newRot)
    
    def AddRotationVelocity(self, rotVelx,rotVely,rotVelz):
        newRotVel = [rotVelx, rotVely, rotVelz]
        self.rotationVelocity.append(newRotVel)
    
    def AddRotationAcceleration(self, rotAccx,rotAccy,rotAccz):
        newRotAcc = [rotAccx, rotAccy, rotAccz]
        self.rotationAcceleration.append(newRotAcc)
    
    def SetConstraint(self,tc,rc):
        self.tc = tc
        self.rc = rc

    def SetID(self,id):
        self.id = id

    def SetElementAdjacency(self,elem):
        self.elems[elem.id] = elem
    
    def RemoveElementAdjacency(self,elem):
        self.elems.pop(elem.id)
    
    def Write(self, stream ,split = " "):
        stream.write("{id}{split}{x}{split}{y}{split}{z}{split}\n".format(id = self.id,split=split,x=self.x,y=self.y,z=self.z))

    def Print(self):
        print(self.id,self.x,self.y,self.z)

class NodeSetListGenerate:
    def __init__(self, name="NODESET_LIST_GENERATE", sid = 0):
        self.setKeyword = "SET_NODE_LIST_GENERATE"
        self.nodeidPairs = []
        self.name = name
        self.sid = sid
        self.da1 = 0.0
        self.da2 = 0.0  
        self.da3 = 0.0
        self.da4 = 0.0
        self.solver = "MECH"
        self.its = 0
        
    def SetDynaOption(self, setKeyword="SET_NODE_LIST_GENERATE", da1=0.0,da2=0.0,da3=0.0,da4=0.0,solver="MECH",its=0):
        self.setKeyword = setKeyword
        self.da1 = da1
        self.da2 = da2
        self.da3 = da3
        self.da4 = da4
        self.solver = solver
        self.its = its
    
    def AddNodePair(self, nodeid1, nodeid2):
        self.nodeidPairs.append([nodeid1, nodeid2])
    
    def WritetoDynaKeyword(self, startID):        
        keyword = "*SET_NODE_LIST_GENERATE\n"
        keyword += "$$     NID       da1       da2       da3       da4    SOLVER       ITS\n"
        sid = format(self.sid+startID,">10")
        da1 = format(self.da1,">10.4e")
        da2 = format(self.da2,">10.4e")
        da3 = format(self.da3,">10.4e")
        da4 = format(self.da4,">10.4e")
        solver = format(self.solver,">10")  
        its = format(self.its,">10")
        keyword += f"{sid}{da1}{da2}{da3}{da4}{solver}{its}\n"
        i = 0 
        keyword += "$$   BiBEG     BiEND   Bi+1BEG   Bi+1END   Bi+2BEG   Bi+2END   Bi+3BEG   Bi+3END\n"
        for pair in self.nodeidPairs:
            i = i + 1
            nodeid1 = format(pair[0],">10")
            nodeid2 = format(pair[1],">10")            
            keyword += f"{nodeid1}{nodeid2}"
            if i % 4 == 0:
                keyword += "\n"        
        if i % 4 != 0:
            keyword += "\n"
        
        return keyword
            

class NodeSet:
    def __init__(self, name="NODESET",sid=0):
        self.setKeyword = "SET_NODE"
        self.nodes = {}
        self.name = name
        self.sid = sid
        self.da1 = 0.0
        self.da2 = 0.0
        self.da3 = 0.0
        self.da4 = 0.0
        self.solver = "MECH"
        self.its = 0
        
    def SetDynaOption(self, setKeyword="SET_NODE", da1=0.0,da2=0.0,da3=0.0,da4=0.0,solver="MECH",its=0):
        self.setKeyword = setKeyword
        self.da1 = da1
        self.da2 = da2
        self.da3 = da3
        self.da4 = da4
        self.solver = solver
        self.its = its
    
    def AddNodesfromDict(self, nodes):
        for key in nodes:
            self.nodes[key] = nodes[key]
    
    def AddNodes(self, nodes):
        for node in nodes:
            self.nodes[node.id] = node
    
    def AddNode(self, node):
        self.nodes[node.id] = node
        
    def RemoveNode(self, node):
        self.nodes.pop(node.id)    
    
    def Clear(self):
        self.nodes.clear()
        
    def WritetoDynaKeyword(self, startID):
        if self.setKeyword == "SET_NODE_LIST_TITLE":
            keyword = "*SET_NODE_LIST_TITLE\n"
            keyword += "$$ Name\n"
            keyword += "{name}\n".format(name=self.name)
        elif self.setKeyword == "SET_NODE_LIST":
            keyword = "*{setKeyword}\n".format(setKeyword=self.setKeyword)
        else:
            keyword = "*{setKeyword}\n".format(setKeyword=self.setKeyword)
        keyword += "$$     NID       da1       da2       da3       da4    SOLVER       ITS\n"
        sid = format(self.sid+startID,">10")
        da1 = format(self.da1,">10.4e")
        da2 = format(self.da2,">10.4e")
        da3 = format(self.da3,">10.4e")
        da4 = format(self.da4,">10.4e")
        solver = format(self.solver,">10")
        its = format(self.its,">10")
        keyword += f"{sid}{da1}{da2}{da3}{da4}{solver}{its}\n"                    
        
        keyword += "$$    NIDi    NIDi+1    NIDi+2    NIDi+3    NIDi+4    NIDi+5    NIDi+6    NIDi+7\n"        
        
        if self.setKeyword == "SET_NODE_LIST_TITLE" or self.setKeyword == "SET_NODE_LIST" or self.setKeyword == "SET_NODE" or self.setKeyword == "SET_NODE_TITLE":
            i = 0 
            for key in self.nodes:
                node = self.nodes[key]
                nodeid = format(node.id,">10")
                keyword += f"{nodeid}"                
                i = i + 1
                if i != 1 and i % 8 == 0:
                    keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        if self.setKeyword == "SET_NODE_LIST_TITLE":
            stream.write("*SET_NODE_LIST_TITLE\n")
            stream.write("$$ Name\n")
            stream.write("{name}\n".format(name=self.name))
        elif self.setKeyword == "SET_NODE_LIST":
            stream.write("*{setKeyword}\n".format(setKeyword=self.setKeyword))
        else:
            stream.write("*{setKeyword}\n".format(setKeyword=self.setKeyword))
        stream.write("$$     NID       da1       da2       da3       da4    SOLVER       ITS\n")
        sid = format(self.sid+startID,">10")
        da1 = format(self.da1,">10.4e")
        da2 = format(self.da2,">10.4e")
        da3 = format(self.da3,">10.4e")
        da4 = format(self.da4,">10.4e")
        solver = format(self.solver,">10")
        its = format(self.its,">10")
        stream.write(f"{sid}{da1}{da2}{da3}{da4}{solver}{its}\n")
        stream.write("$$    NIDi    NIDi+1    NIDi+2    NIDi+3    NIDi+4    NIDi+5    NIDi+6    NIDi+7\n")
        
        if self.setKeyword == "SET_NODE_LIST_TITLE" or self.setKeyword == "SET_NODE_LIST" or self.setKeyword == "SET_NODE" or self.setKeyword == "SET_NODE_TITLE":
            i = 0 
            for key in self.nodes:
                node = self.nodes[key]
                nodeid = format(node.id,">10")
                stream.write(f"{nodeid}")                
                i = i + 1
                if i != 1 and i % 8 == 0:
                    stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")
            
        
class NodeManager:
    def __init__(self):
        self.nodes = {} 
        self.maxID = 0 
        self.name = "NODEMAN"
        self.time = []
    
    def ApplyTransformfromThreePoints(self, P, Q, node_ids=None, inverse = False):
        """
        P, Q: (3,3) - row마다 한 점 [p1; p2; p3], [q1; q2; q3]
        반환: R(3x3), t(3,)
        """
        R, t = self.estimate_rigid_transform_from_3pts(P, Q)
        self.apply_transform(R, t, node_ids, inverse)

    def estimate_rigid_transform_from_3pts(self, P, Q):
        """
        P, Q: (3,3) - row마다 한 점 [p1; p2; p3], [q1; q2; q3]
        반환: R(3x3), t(3,)
        """
        P = np.asarray(P, dtype=float)
        Q = np.asarray(Q, dtype=float)
        assert P.shape == (3,3) and Q.shape == (3,3)

        p_centroid = P.mean(axis=0)
        q_centroid = Q.mean(axis=0)
        Pc = P - p_centroid
        Qc = Q - q_centroid

        # H = Pc^T Qc
        H = Pc.T @ Qc
        U, S, Vt = np.linalg.svd(H)
        V = Vt.T
        R = V @ np.diag([1, 1, np.linalg.det(V @ U.T)]) @ U.T  # reflection fix
        t = q_centroid - R @ p_centroid
        return R, t

    def apply_transform(self, R, t, node_ids=None, inverse=False):
        """
        R: (3,3) 회전, t: (3,) 이동
        node_ids: 변환할 노드 id 서브셋(생략 시 전체)
        inverse=True면 원래 자세로 환원: x = R^T (x' - t)
        """
        nodes = self.nodes
        if node_ids is None:
            # dict values를 바로 돌면 순서가 불확정이므로, 키 리스트를 잡아둡니다.
            keys = list(nodes.keys())
        else:
            keys = list(node_ids)

        n = len(keys)
        if n == 0:
            return

        # 1) 좌표를 연속 배열로 모으기 (파이썬 루프는 '읽기'만)
        X = np.empty((n, 3), dtype=np.float64)
        get = nodes.__getitem__  # 로컬 바인딩(미세 최적화)
        for i, k in enumerate(keys):
            nd = get(k)
            X[i, 0] = nd.x
            X[i, 1] = nd.y
            X[i, 2] = nd.z

        # 2) 벡터화 변환 (한 번에)
        if inverse:
            # x = R^T (x' - t)
            # in-place로 메모리 재사용
            np.subtract(X, t, out=X)
            X[:] = X @ R
        else:
            # x' = R x + t
            X[:] = X @ R.T
            np.add(X, t, out=X)

        # 3) 결과를 객체에 되돌리기 (파이썬 루프은 '쓰기'만)
        for i, k in enumerate(keys):
            nd = nodes[k]
            xi, yi, zi = X[i]
            nd.x, nd.y, nd.z = xi, yi, zi
    
   
        
    def OffsetID(self, offset):
        for key in self.nodes:
            node = self.nodes[key]
            node.id += offset
        self.maxID += offset

    def OverwritefromNodeManager(self, nodeManager : NodeManager):
        for key, value in nodeManager.nodes.items():
            self.nodes[key] = value
        self.maxID = max(nodeManager.maxID, self.maxID)

        self.name = self.name + "_" + nodeManager.name
        if len(nodeManager.time) > 0:
            self.time = nodeManager.time

    def GetTriangleArea(self, nid1, nid2, nid3):
        n1 = self.nodes[nid1]
        n2 = self.nodes[nid2]
        n3 = self.nodes[nid3]
        x1 = n1.x
        y1 = n1.y
        z1 = n1.z
        x2 = n2.x
        y2 = n2.y
        z2 = n2.z
        x3 = n3.x
        y3 = n3.y
        z3 = n3.z
        
        v1 = [x2-x1, y2-y1, z2-z1]
        v2 = [x3-x1, y3-y1, z3-z1]
        area = 0.5 * math.sqrt((v1[1]*v2[2] - v1[2]*v2[1])**2 + (v1[2]*v2[0] - v1[0]*v2[2])**2 + (v1[0]*v2[1] - v1[1]*v2[0])**2)                   
        return area
    
    def GetQuadrangleArea(self, nid1, nid2, nid3, nid4):
        tri1 = self.GetTriangleArea(nid1, nid2, nid3)
        tri2 = self.GetTriangleArea(nid1, nid3, nid4)
        return tri1 + tri2
        
    def AddTime(self, time):
        self.time.append(time)

    def SetName(self, name):
        self.name = name

    def SetMaxID(self,maxID):
        self.maxID = maxID
        
    def Transform(self, trsf : gp_Trsf):
        for key in self.nodes:
            n : Node = self.nodes[key]
            n.Transform(trsf)
            
    def MoveNodes(self, dx, dy, dz):
        for key in self.nodes:
            n : Node = self.nodes[key]
            n.SetXYZ(n.x + dx, n.y + dy, n.z + dz)
    
    def Scaling(self, dx, dy, dz):
        minx = 1e99
        miny = 1e99
        minz = 1e99
        maxx = -1e99
        maxy = -1e99
        maxz = -1e99
        for key in self.nodes:
            node = self.nodes[key]
            if node.x < minx:
                minx = node.x
            if node.y < miny:
                miny = node.y
            if node.z < minz:
                minz = node.z
            if node.x > maxx:
                maxx = node.x
            if node.y > maxy:
                maxy = node.y
            if node.z > maxz:
                maxz = node.z
        centerx = 0.5*(minx+maxx)
        centery = 0.5*(miny+maxy)
        centerz = 0.5*(minz+maxz)
        for key in self.nodes:
            node = self.nodes[key]
            #node.x = centerx + dx*(node.x-centerx)
            #node.y = centery + dy*(node.y-centery)
            #node.z = centerz + dz*(node.z-centerz)
            node.x = dx*(node.x)
            node.y = dy*(node.y)
            node.z = dz*(node.z)
    
    def GetDisplacement(self, ithStep):
        nnode = self.NNode()
        disp = np.empty((nnode,3), dtype=np.float32)
        for key in self.nodes:
            n : Node = self.nodes[key]
            disp[key] = n.GetDisplacement(ithStep)
        return disp
    
    def GetTotalDisplacement(self, ithStep):
        nnode = self.NNode()
        disp = np.empty(nnode, dtype=np.float32)
        i = 0 
        for key in self.nodes:
            n : Node = self.nodes[key]
            disp[i] = n.GetTotalDisplacement(ithStep)
            i = i + 1
        return disp
    
    def GetDisplacementX(self, ithStep):
        nnode = self.NNode()
        disp = np.empty((nnode,1), dtype=np.float32)
        i = 0 
        for key in self.nodes:
            n : Node = self.nodes[key]
            disp[i] = n.GetDisplacementX(ithStep)
            i = i + 1
        return disp
    
    def GetDisplacementY(self, ithStep):
        nnode = self.NNode()
        disp = np.empty((nnode,1), dtype=np.float32)
        i = 0
        for key in self.nodes:
            n : Node = self.nodes[key]
            disp[i] = n.GetDisplacementY(ithStep)
            i = i + 1
        return disp
    
    def GetDisplacementZ(self, ithStep):
        nnode = self.NNode()
        disp = np.empty((nnode,1), dtype=np.float32)
        i = 0
        for key in self.nodes:
            n : Node = self.nodes[key]
            disp[i] = n.GetDisplacementZ(ithStep)
            i = i + 1
        return disp  
    
    def GetNodesXRange(self, xmin, xmax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.x > xmin and n.x < xmax:
                nodes[key] = n
        return nodes
    
    def GetNodesYRange(self, ymin, ymax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.y > ymin and n.y < ymax:
                nodes[key] = n
        return nodes
    
    def GetNodesZRange(self, zmin, zmax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.z > zmin and n.z < zmax:
                nodes[key] = n
        return nodes

    def GetNodesXRangeYRange(self, xmin, xmax, ymin, ymax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.x > xmin and n.x < xmax and n.y > ymin and n.y < ymax:
                nodes[key] = n
        return nodes
    
    def GetNodesXRangeZRange(self, xmin, xmax, zmin, zmax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.x > xmin and n.x < xmax and n.z > zmin and n.z < zmax:
                nodes[key] = n
        return nodes
    
    def GetNodesYRangeZRange(self, ymin, ymax, zmin, zmax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.y > ymin and n.y < ymax and n.z > zmin and n.z < zmax:
                nodes[key] = n
        return nodes
    
    def GetNodesXRangeYRangeZRange(self, xmin, xmax, ymin, ymax, zmin, zmax):
        nodes = {}
        for key in self.nodes:
            n : Node = self.nodes[key]
            if n.x > xmin and n.x < xmax and n.y > ymin and n.y < ymax and n.z > zmin and n.z < zmax:
                nodes[key] = n
        return nodes

    def NNode(self):
        return len(self.nodes)

    def MaxDisplacement(self):
        maxNode = None
        maxDisp = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMaxDisplacement()
            if curDisp > maxDisp:
                maxDisp = curDisp
                maxNode = n
                maxith = ith
        return maxNode, maxDisp, maxith
    
    def MaxDisplacementX(self):
        maxNode = None
        maxDisp = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMaxDisplacementX()
            if curDisp > maxDisp:
                maxDisp = curDisp
                maxNode = n
                maxith = ith
        return maxNode, maxDisp, maxith
    
    def MaxDisplacementY(self):
        maxNode = None
        maxDisp = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMaxDisplacementY()
            if curDisp > maxDisp:
                maxDisp = curDisp
                maxNode = n
                maxith = ith
        return maxNode, maxDisp, maxith
    
    def MaxDisplacementZ(self):
        maxNode = None
        maxDisp = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMaxDisplacementZ()
            if curDisp > maxDisp:
                maxDisp = curDisp
                maxNode = n
                maxith = ith
        return maxNode, maxDisp, maxith
    
    def MinDisplacement(self):
        minNode = None
        minDisp = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMinDisplacement()
            if curDisp < minDisp:
                minDisp = curDisp
                minNode = n
                minith = ith
        return minNode, minDisp, minith
    
    def MinDisplacementX(self):
        minNode = None
        minDisp = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMinDisplacementX()
            if curDisp < minDisp:
                minDisp = curDisp
                minNode = n
                minith = ith
        return minNode, minDisp, minith
    
    def MinDisplacementY(self):
        minNode = None
        minDisp = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMinDisplacementY()
            if curDisp < minDisp:
                minDisp = curDisp
                minNode = n
                minith = ith
        return minNode, minDisp, minith
    
    def MinDisplacementZ(self):
        minNode = None
        minDisp = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curDisp = n.GetMinDisplacementZ()
            if curDisp < minDisp:
                minDisp = curDisp
                minNode = n
                minith = ith
        return minNode, minDisp, minith
    
    def MaxVelocity(self):
        maxNode = None
        maxVel = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMaxVelocity()
            if curVel > maxVel:
                maxVel = curVel
                maxNode = n
                maxith = ith
        return maxNode, maxVel, maxith

    def MaxVelocityX(self):
        maxNode = None
        maxVel = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMaxVelocityX()
            if curVel > maxVel:
                maxVel = curVel
                maxNode = n
                maxith = ith
        return maxNode, maxVel, maxith
    
    def MaxVelocityY(self):
        maxNode = None
        maxVel = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMaxVelocityY()
            if curVel > maxVel:
                maxVel = curVel
                maxNode = n
                maxith = ith
        return maxNode, maxVel, maxith
    
    def MaxVelocityZ(self):
        maxNode = None
        maxVel = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMaxVelocityZ()
            if curVel > maxVel:
                maxVel = curVel
                maxNode = n
                maxith = ith
        return maxNode, maxVel, maxith
    
    def MinVelocity(self):
        minNode = None
        minVel = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMinVelocity()
            if curVel < minVel:
                minVel = curVel
                minNode = n
                minith = ith
        return minNode, minVel, minith
    
    def MinVelocityX(self):
        minNode = None
        minVel = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMinVelocityX()
            if curVel < minVel:
                minVel = curVel
                minNode = n
                minith = ith
        return minNode, minVel, minith
    
    def MinVelocityY(self):
        minNode = None
        minVel = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMinVelocityY()
            if curVel < minVel:
                minVel = curVel
                minNode = n
                minith = ith
        return minNode, minVel, minith
    
    def MinVelocityZ(self):
        minNode = None
        minVel = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curVel = n.GetMinVelocityZ()
            if curVel < minVel:
                minVel = curVel
                minNode = n
                minith = ith
        return minNode, minVel, minith
    
    def MaxAcceleration(self):
        maxNode = None
        maxAcc = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMaxAcceleration()
            if curAcc > maxAcc:
                maxAcc = curAcc
                maxNode = n
                maxith = ith
        return maxNode, maxAcc, maxith
    
    def MaxAccelerationX(self):
        maxNode = None
        maxAcc = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMaxAccelerationX()
            if curAcc > maxAcc:
                maxAcc = curAcc
                maxNode = n
                maxith = ith
        return maxNode, maxAcc, maxith
    
    def MaxAccelerationY(self):
        maxNode = None
        maxAcc = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMaxAccelerationY()
            if curAcc > maxAcc:
                maxAcc = curAcc
                maxNode = n
                maxith = ith
        return maxNode, maxAcc, maxith
    
    def MaxAccelerationZ(self):
        maxNode = None
        maxAcc = -1.0e99
        maxith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMaxAccelerationZ()
            if curAcc > maxAcc:
                maxAcc = curAcc
                maxNode = n
                maxith = ith
        return maxNode, maxAcc, maxith
    
    def MinAcceleration(self):
        minNode = None
        minAcc = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMinAcceleration()
            if curAcc < minAcc:
                minAcc = curAcc
                minNode = n
                minith = ith
        return minNode, minAcc, minith
    
    def MinAccelerationX(self):
        minNode = None
        minAcc = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMinAccelerationX()
            if curAcc < minAcc:
                minAcc = curAcc
                minNode = n
                minith = ith
        return minNode, minAcc, minith
    
    def MinAccelerationY(self):
        minNode = None
        minAcc = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMinAccelerationY()
            if curAcc < minAcc:
                minAcc = curAcc
                minNode = n
                minith = ith
        return minNode, minAcc, minith
    
    def MinAccelerationZ(self):
        minNode = None
        minAcc = 1.0e99
        minith = -1
        for key in self.nodes:
            n : Node = self.nodes[key]
            ith, curAcc = n.GetMinAccelerationZ()
            if curAcc < minAcc:
                minAcc = curAcc
                minNode = n
                minith = ith
        return minNode, minAcc, minith    

    def AddNodesfromDynaAdvanced(self, dynaNodes):
        # Precompute attributes for nodes to minimize redundant method calls
        import time 
        start = time.time()
        add_node = self.AddNodewithID
        set_constraint = lambda node, tc, rc: node.SetConstraint(tc, rc)

        for node in dynaNodes:
            curid = int(node[0])
            x, y, z = node[1], node[2], node[3]
            tc, rc = node[4], node[5]
            
            # Create node and set attributes efficiently
            newNode = add_node(curid, x, y, z)
            set_constraint(newNode, tc, rc)
        end = time.time()
        print("AddNodesfromDynaAdvanced",end-start)
        return self.maxID
    
    def AddNodesfromDyna(self, dynaNodes):
        import time 
        start = time.time()
        for node in dynaNodes:
            curid = int(node[0])
            x = node[1]
            y = node[2]
            z = node[3]
            tc = node[4]
            rc = node[5]
            newNode = self.AddNodewithID(curid,x,y,z)
            newNode.SetConstraint(tc,rc)
        end = time.time()
        print("AddNodesfromDyna",end-start)
        return self.maxID
               
    def AddNodesfromMSH(self, mshNodes,maxNID = 0):
        for node in mshNodes['entities']:
            node_tags = node['node_tags']
            coordinates = node['coordinates']
            for i in range(len(node_tags)):
                curid = node_tags[i] + maxNID
                x,y,z = coordinates[i]
                self.AddNodewithID(curid,x,y,z)
            pass
        
    def AddNodesfromMSHwithoutBoundary(self, mshNodes, maxNID = 0, boundaryNodes = {}, tol = 1.0e-8):
        
        # 1. boundaryNodes를 좌표 배열로 변환
        boundary_coords = np.array([[node.x, node.y, node.z] for node in boundaryNodes.values()])
        kdtree = KDTree(boundary_coords)
        nodekeytoid = {}        
        # 2. 노드 반복 처리
        for node in mshNodes['entities']:
            node_tags = node['node_tags']
            coordinates = node['coordinates']
            for i in range(len(node_tags)):
                curid = node_tags[i] + maxNID
                x, y, z = coordinates[i]

                # KDTree를 이용하여 tol 이내 거리의 노드가 있는지 확인
                indices = kdtree.query_ball_point([x, y, z], tol)

                if len(indices) == 0:  # 근처에 경계 노드가 없다면
                    # 경계 노드가 없을 때만 노드 추가
                    self.AddNodewithID(curid, x, y, z)
                    nodekeytoid[curid] = curid
                else:
                    # 근처에 경계 노드가 있다면, 가장 가까운 노드의 ID를 찾음
                    closest_index = indices[0]  # 가장 가까운 인덱스                    
                    closest_node_id = list(boundaryNodes.keys())[closest_index]  # ID 찾기
                    nodekeytoid[curid] = closest_node_id  # 경계 노드 ID 저장
        return nodekeytoid
            
                    

    def CreateNode(self,x,y,z):
        self.maxID += 1
        node = Node(self.maxID)
        node.SetXYZ(x,y,z)
        self.AddNode(node)
        return node
    
    def CreateNodefromNode(self,node):
        self.maxID += 1
        node.SetID(self.maxID)
        self.AddNode(node)
        return node
    
    def CreateNodefromGivenID(self,id,x,y,z):
        self.maxID = max(self.maxID,id)
        node = Node(id)
        node.SetXYZ(x,y,z)
        self.AddNode(node)
        return node
    
    def CenterNode(self, nodeSet):
        nodes = nodeSet.nodes
        x = 0.0
        y = 0.0
        z = 0.0
        for key in nodes:
            n : Node = nodes[key]
            x += n.x
            y += n.y
            z += n.z
        x /= len(nodes)
        y /= len(nodes)
        z /= len(nodes)
        dist = 1.0e99
        optKey  = 0
        for key in nodes:
            n : Node = nodes[key]
            if dist > (n.x - x)**2 + (n.y - y)**2 + (n.z - z)**2:
                dist = (n.x - x)**2 + (n.y - y)**2 + (n.z - z)**2
                optKey = key
        return nodes[optKey]
    
    def CreateCenterNodefromNodeSet(self,nodeSet):
        nodes = nodeSet.nodes
        x = 0.0
        y = 0.0
        z = 0.0
        for key in nodes:
            n : Node = nodes[key]
            x += n.x
            y += n.y
            z += n.z
        x /= len(nodes)
        y /= len(nodes)
        z /= len(nodes)
        return self.CreateNode(x,y,z)
    

    def AddNode(self, node):
        # Directly compare without using max function
        if node.id > self.maxID:
            self.maxID = node.id
        self.nodes[node.id] = node
        
    def AddNodes(self , nodes):
        for nid in nodes:
            self.nodes[nid] = nodes[nid]
            if nid > self.maxID:
                self.maxID = nid
    
    def AddNodeList(self, nodes):
        for node in nodes:
            self.nodes[node.id] = node
            if node.id > self.maxID:
                self.maxID = node.id
    
    def AddNodewithID(self, id, x, y, z):
        # Directly create and add the node in one step
        node = Node(id)
        node.SetXYZ(x, y, z)
        # Inline AddNode to avoid additional function call
        if id > self.maxID:
            self.maxID = id
        self.nodes[id] = node
        return node
            
    def FindNode(self,node, tol=1.e-6):
        for key in self.nodes:
            distance = (self.nodes[key].x - node.x)**2 + (self.nodes[key].y - node.y)**2 + (self.nodes[key].z - node.z)**2
            if math.sqrt(distance) < tol:
                return self.nodes[key]
        return self.CreateNodefromNode(node)
    
    def FindNodefromID(self,id):
        if id in self.nodes:
            return self.nodes[id]
        else:
            return None
    
    def FindNodesfromIDs(self,ids):
        nodes = []
        for id in ids:
            if id in self.nodes:
                nodes.append(self.nodes[id])
        return nodes

    def FindSubNodeDictfromIDs(self, ids):
        nodes = {} 
        for id in ids:
            if id in self.nodes:
                nodes[id] = self.nodes[id]
        return nodes
    
    def FindNodefromCoordinate(self, x,y,z, tol=1.e-6):
        node = Node()
        node.SetXYZ(x,y,z)
        return self.FindNode(node,tol)
    
    def Write(self, stream ,split = " "):
        stream.write("*NODE\n")
        for key in self.nodes:
            self.nodes[key].Write(stream,split)

    def Print(self):
        print("Node")
        for key in self.nodes:
            self.nodes[key].Print()        

    def GetNode(self,id):
        if id in self.nodes:
            return self.nodes[id]
        else:
            return None
    
    def ShiftID(self,shift):
        maxID = 0
        for key in self.nodes:
            self.nodes[key].SetID(self.nodes[key].id + shift)
            maxID = max(maxID,self.nodes[key].id)
        self.maxID = maxID

    def CombineNodesfromManager(self,nodeMan):
        for key in nodeMan.nodes:
            self.CreateNodefromNode(nodeMan.nodes[key])
    
    def RemoveNode(self,node):
        if node.id in self.nodes:
            del self.nodes[node.id]
            return True
        else:
            return False
        
    def RemoveComplementaryNodes(self, nodes):
        complementaryNodes = {}
        for key in self.nodes:
            if key not in nodes:
                complementaryNodes[key] = self.nodes[key]                
        self.nodes = nodes
        return complementaryNodes
    
    def RemoveNodesExceptNodes(self,nodes = {}, nodesExcept= {}):
        for id in nodes:
            if id in self.nodes and id not in nodesExcept:
                del self.nodes[id]
        return True
    
    def RemoveNodes(self, nodes = {}):
        for id in nodes:
            if id in self.nodes:
                del self.nodes[id]
        return True            

    def RemoveNodeList(self, nodes):
        for node in nodes:
            if node.id in self.nodes:
                del self.nodes[node.id]
        return True
        
    def RemoveNodefromID(self,id):
        if id in self.nodes:
            del self.nodes[id]
            return True
        else:
            return False
    
    def ReorderNodeID(self,startid=1):
        newNodes = {}
        id = startid
        for key in self.nodes:
            newNodes[id] = self.nodes[key]
            self.nodes[key].SetID(id)
            id += 1
        self.nodes = newNodes

    def GetNodalCoordinates(self):
        nnode = len(self.nodes)
        nodalCoordinates = np.zeros((nnode,3))
        idtokey = {}    
        curKey = 0
        for key in self.nodes:
            nodalCoordinates[curKey,0] = self.nodes[key].x
            nodalCoordinates[curKey,1] = self.nodes[key].y
            nodalCoordinates[curKey,2] = self.nodes[key].z
            idtokey[self.nodes[key].id] = curKey
            curKey += 1
        return idtokey, nodalCoordinates

    def GetDeformedCoordinates(self, option, ithStep):
        nnode = self.NNode()        
        deformedCoordinates = np.empty((nnode,3), dtype=np.float32)
        idtokey = {}
        curKey = 0
        if option == "ut":
            for key in self.nodes:
                n : Node = self.nodes[key]
                deformedCoordinates[curKey,0] = n.x + n.displacement[ithStep][0]
                deformedCoordinates[curKey,1] = n.y + n.displacement[ithStep][1]
                deformedCoordinates[curKey,2] = n.z + n.displacement[ithStep][2]                    
                idtokey[n.id] = curKey            
                curKey += 1
            
        return idtokey, deformedCoordinates


    def GetNodalCoordinatesOriginal(self):
        nodalCoordinates = np.array([]).astype(np.float64)
        idtokey = {}
        curKey = 0 
        for key in self.nodes:
            nodalCoordinates = np.append(nodalCoordinates,[self.nodes[key].x,self.nodes[key].y,self.nodes[key].z])
            idtokey[self.nodes[key].id] = curKey
            curKey += 1
        return idtokey, nodalCoordinates    
    
    def WritetoNastranStream(self, stream, startID):
        star8digit = "*       "
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            id = format(id_fixed, ">16")
            CP = format(0, ">16")
            x = format(node.x, ">16.9e")
            y = format(node.y, ">16.9e")
            z = format(node.z, ">16.9e")
            CD = format(0, ">16")
            stream.write("GRID*   ")
            stream.write(id)
            stream.write(CP)
            stream.write(x)
            stream.write(y)
            stream.write("\n")
            stream.write(star8digit)
            stream.write(z)
            stream.write(CD)
            stream.write("\n")                        
    
    def WritetoNastranKeyword(self, startID):
        keywords = ""
        star8digit = "*       "
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            id = format(id_fixed, ">16")
            CP = format(0, ">16")            
            
            
            x = format(node.x, ">16.9e")
            #x = x.replace("e+0", "e+").replace("e-0", "e-")
            #x = " " + x
            '''if node.x >0:
                x = " " + x
            elif node.x == 0:
                x = "0.000000"'''
            y = format(node.y, ">16.9e")
            #y = y.replace("e+0", "e+").replace("e-0", "e-")
            #y = " " + y
            '''if node.y >0:
                y = " " + y
            elif node.y == 0:
                y = "0.000000"'''
            z = format(node.z, ">16.9e")
            #z = z.replace("e+0", "e+").replace("e-0", "e-")
            #z = " " + z
            '''if node.z >0:
                z = " " + z
            elif node.z == 0:
                z = "0.000000"'''

            '''x = x.replace("e","")
            y = y.replace("e","")
            z = z.replace("e","")'''
            
            CD = format(0, ">16")
            keywords += "GRID*   "
            keywords += id 
            keywords += CP
            keywords += x
            keywords += y
            keywords += "\n"
            keywords += star8digit
            keywords += z
            keywords += CD
            keywords += "\n"
        return keywords
    
    def WritetoDynaKeyword(self, startID):
        keywords = "*NODE\n"
        keywords += "$$   NID               X               Y               Z      TC      RC\n"
        numNodes = len(self.nodes)
        i = 0 
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            x = format(node.x, ">16.8e")
            y = format(node.y, ">16.8e")
            z = format(node.z, ">16.8e")
            tc = format(node.tc, ">8")
            rc = format(node.rc, ">8")
            formatStr = f"{str(id_fixed):>8}{x}{y}{z}{tc}{rc}\n"
            keywords += formatStr
            i = i + 1
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*NODE\n$$   NID               X               Y               Z      TC      RC\n")
        
        lines = [f"{node.id + startID:>8}{node.x:>16.8e}{node.y:>16.8e}"
                f"{node.z:>16.8e}{node.tc:>8}{node.rc:>8}\n" 
                for node in self.nodes.values()]
        
        stream.write(''.join(lines))
         
    def WriteStreamDynaKeywordPrev(self, stream, startID):
        stream.write("*NODE\n")
        stream.write("$$   NID               X               Y               Z      TC      RC\n")
        numNodes = len(self.nodes)
        i = 0 
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            x = format(node.x, ">16.8e")
            y = format(node.y, ">16.8e")
            z = format(node.z, ">16.8e")
            tc = format(node.tc, ">8")
            rc = format(node.rc, ">8")
            formatStr = f"{str(id_fixed):>8}{x}{y}{z}{tc}{rc}\n"
            stream.write(formatStr)
            i = i + 1
        
    def WriteStreamABAQUSKeyword(self, stream, startID):
        stream.write("*NODE, NSET={name}\n".format(name=self.name))
        numNodes = len(self.nodes)
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            x = node.x
            y = node.y
            z = node.z

            formatStr = "{id},{x},{y},{z}\n".format(id=id_fixed,x=x,y=y,z=z)
            stream.write(formatStr)
    
    def WritetoABAQUSKeyword(self, startID):
        keywords = "*NODE, NSET={name}\n".format(name=self.name)
        numNodes = len(self.nodes)
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            x = node.x
            y = node.y
            z = node.z

            formatStr = "{id},{x},{y},{z}\n".format(id=id_fixed,x=x,y=y,z=z)
            keywords += formatStr
        return keywords    
    
    def WritetoANSYSAPDLKeyword(self, startID):
        keywords = ""
        numNodes = len(self.nodes)
        for key in self.nodes:
            node = self.nodes[key]
            id_fixed = node.id + startID
            x = node.x
            y = node.y
            z = node.z

            formatStr = "N,{id},{x},{y},{z},0,0,0\n".format(id=id_fixed,x=x,y=y,z=z)
            keywords += formatStr
        return keywords
    
    def AddNodesfromAnotherManager(self, nodeMan):
        nodeMan : NodeManager = nodeMan
        for key in nodeMan.nodes:
            #self.AddNodewithID(nodeMan.nodes[key].id,nodeMan.nodes[key].x,nodeMan.nodes[key].y,nodeMan.nodes[key].z)
            if key in self.nodes:
                print("Node ID : ",key," is already exist")
                exit(0)
            self.AddNode(nodeMan.nodes[key])            
    
    def SplitNodes(self):
        newNodes = {} 
        previdList = [] 
        for id in self.nodes:
            previdList.append(id)
        for id in previdList:
            node : Node = self.nodes[id]
            elems = node.elems
            for eid in elems: 
                elem = elems[eid]
                i = 0
                for innode in elem.nodes:
                    if innode.id == node.id:
                        newNode = self.CreateNode(innode.x,innode.y,innode.z)
                        newNode.SetElementAdjacency(elems[eid])
                        newNodes[newNode.id] = newNode
                        elem.nodes[i] = newNode
                    i = i+1
        return newNodes
            
    
    def MergeGivenNodes(self, nodes, tol = 1.0e-8):
        # nodes : dict = nodes
        points = [(node.x, node.y, node.z) for node in nodes.values()]
        keytoid = [node.id for node in nodes.values()]                
        tree = KDTree(points)
        removedKey = {}
        ii = 0
        ith = 0 
        for key, node in nodes.items():
            if key in removedKey:
                continue
            point = (node.x, node.y, node.z)
            indices = tree.query_ball_point(point, tol**0.5)
            for idx in indices:
                node2 = nodes[keytoid[idx]]
                if node.id != node2.id and node2.id not in removedKey:
                    for ii in node2.elems:           
                        for jj, innode in enumerate(node2.elems[ii].nodes):
                            if innode.id == node2.id:
                                node2.elems[ii].nodes[jj] = node
                                node.SetElementAdjacency(node2.elems[ii])
                                removedKey[node2.id] = node2
            ith = ith + 1
            if ith % 1000 == 0:
                print("{ii} th node is checked".format(ii=ith))        
        print("{ii} th node is checked".format(ii=ith))        
        for key in removedKey:
            #print("Node ID : ",key," is removed")
            self.RemoveNode(removedKey[key])
        print("Merging is done")
    
    def MergeNodes(self, tol = 1.0e-8):
        
        # 노드 리스트에서 좌표 추출
        points = [(node.x, node.y, node.z) for node in self.nodes.values()]
        keytoid = [node.id for node in self.nodes.values()]
        # KD-트리 생성
        tree = KDTree(points)
        removedKey = {}
        ith = 0
        for key, node in self.nodes.items():
            if key in removedKey:
                continue
            # 현재 노드의 좌표
            point = (node.x, node.y, node.z)
            # tol 거리 이내의 노드 찾기 (자기 자신 포함)
            indices = tree.query_ball_point(point, tol**0.5)
            #print(indices)
            for idx in indices:
                node2 = self.nodes[keytoid[idx]]
                #print(str(node2.id) + " is removed if it is same as " + str(node.id))
                if node.id != node2.id and node2.id not in removedKey:
                    #print(str(node2.id) + " is removed")
                    #print(node2.elems)
                    for ii in node2.elems:           
                        #print(str(ii) + " th element is checked")             
                        for jj, innode in enumerate(node2.elems[ii].nodes):
                            #print(str(innode.id) + "and" + str(node2.id) + "is checked")
                            if innode.id == node2.id:
                                node2.elems[ii].nodes[jj] = node
                                node.SetElementAdjacency(node2.elems[ii])
                                removedKey[node2.id] = node2
                                #print("Node ID : ",node2.id," is removed")
            ith = ith + 1
            if ith % 1000 == 0:
                print("{ii} th node is checked".format(ii=ith))        
        print("{ii} th node is checked".format(ii=ith))        
        for key in removedKey:
            #print("Node ID : ",key," is removed")
            self.RemoveNode(removedKey[key])
        print("Merging is done")            
       
    def GetBoundingBox(self):
        self.boundingBox = [1.0e99,1.0e99,1.0e99,-1.0e99,-1.0e99,-1.0e99]
        for key in self.nodes:
            if self.nodes[key].x < self.boundingBox[0]:
                self.boundingBox[0] = self.nodes[key].x
            if self.nodes[key].y < self.boundingBox[1]:
                self.boundingBox[1] = self.nodes[key].y
            if self.nodes[key].z < self.boundingBox[2]:
                self.boundingBox[2] = self.nodes[key].z
            if self.nodes[key].x > self.boundingBox[3]:
                self.boundingBox[3] = self.nodes[key].x
            if self.nodes[key].y > self.boundingBox[4]:
                self.boundingBox[4] = self.nodes[key].y
            if self.nodes[key].z > self.boundingBox[5]:
                self.boundingBox[5] = self.nodes[key].z
        return self.boundingBox
    
    def RelocationNodes(self, delX, delY, delZ, scaleX, scaleY, scaleZ):
        boundingBox = self.GetBoundingBox()        
        
        curCenterX = (boundingBox[3] + boundingBox[0]) / 2.0
        curCenterY = (boundingBox[4] + boundingBox[1]) / 2.0
        curCenterZ = (boundingBox[5] + boundingBox[2]) / 2.0
        
        xCenterNew = curCenterX + delX
        yCenterNew = curCenterY + delY
        zCenterNew = curCenterZ + delZ
        for key in self.nodes:
            self.nodes[key].x = (self.nodes[key].x - curCenterX) * scaleX + xCenterNew
            self.nodes[key].y = (self.nodes[key].y - curCenterY) * scaleY + yCenterNew
            self.nodes[key].z = (self.nodes[key].z - curCenterZ) * scaleZ + zCenterNew
    
    def FindClosestNodefromPoint(self, x, y, z):
        closest_node = None
        min_distance = float("inf")

        for node in self.nodes.values():
            distance = node.DistancefromPoint(x, y, z)
            if distance < min_distance:
                min_distance = distance
                closest_node = node

        return closest_node

    def FindClosestNode(self, target_node):
        if not self.nodes:
            return None

        closest_node = None
        min_distance = float("inf")
        
        for node in self.nodes.values():
            distance = node.DistancefromPoint(target_node.x, target_node.y, target_node.z)
            if distance < min_distance:
                min_distance = distance
                closest_node = node

        return closest_node
    
    def FindFarthestNodefromPoint(self, x, y, z):
        farthest_node = None
        max_distance = float("-inf")

        for node in self.nodes.values():
            distance = node.DistanceToPoint(x, y, z)
            if distance > max_distance:
                max_distance = distance
                farthest_node = node

        return farthest_node

    def FindFarthestNodes(self, direction):
        if not self.nodes:
            return None, None
        
        # 모든 노드 좌표를 한 번에 배열로 변환
        node_ids = list(self.nodes.keys())
        coordinates = np.array([[self.nodes[nid].x, self.nodes[nid].y, self.nodes[nid].z] 
                            for nid in node_ids])
        
        # 벡터화된 내적 계산
        dot_products = np.dot(coordinates, direction)
        
        # 최소/최대 인덱스 찾기
        min_idx = np.argmin(dot_products)
        max_idx = np.argmax(dot_products)
        
        return self.nodes[node_ids[min_idx]], self.nodes[node_ids[max_idx]]
                            

if __name__ == "__main__":
    nodeMan = NodeManager()
    node1 = nodeMan.CreateNode(0,0,0)
    node2 = nodeMan.CreateNode(1,0,0)
    node3 = nodeMan.CreateNode(1,1,0)
    node4 = nodeMan.CreateNode(0,1,0)
    node5 = Node()
    node5.SetXYZ(0,0,1)
    node5 = nodeMan.FindNode(node5)
    node6 = nodeMan.FindNodefromCoordinate(1,0,1)
    node7 = nodeMan.FindNodefromCoordinate(1,1,0)
    node8 = nodeMan.FindNodefromCoordinate(0,1,0)

    print("Print from Node Manager")
    nodeMan.Print()
    print("Print from Node")
    node1.Print()
    node2.Print()
    node3.Print()
    node4.Print()
    node5.Print()
    node6.Print()
    node7.Print()
    node8.Print()

    print("Print from Node Manager after remove nodes")
    nodeMan.RemoveNode(node1)
    nodeMan.RemoveNodefromID(2)
    print(nodeMan.RemoveNodefromID(2))
    nodeMan.Print()

    file = open("test.txt","w")
    nodeMan.Write(file)
    file.close()

class NodeSetManager:
    def __init__(self, nodeManager = None):
        self.nodeSets = {}
        self.nodeManager = nodeManager
        self.maxID = 0
        self.name = "NODESET"
        
    def OffsetID(self, offsetNSID):
        self.maxID += offsetNSID
        for key in self.nodeSets:
            nodeSet = self.nodeSets[key]
            nodeSet.sid += offsetNSID

    def OverwritefromNodeSetManager(self, nodeSetManager : NodeSetManager):
        for nsid, nodeSet in nodeSetManager.nodeSets.items():
            self.nodeSets[nsid] = nodeSet
        self.maxID = max(self.maxID, nodeSetManager.maxID)
        self.name = self.name + "_" + nodeSetManager.name

    def RemoveNodesExceptNodes(self,nodes = {}, nodesExcept= {}):
        delnsidList = []
        for nsid in self.nodeSets:
            curNodes = self.nodeSets[nsid].nodes
            remNodes = {}
            for id in curNodes:
                if id in nodes and id not in nodesExcept:
                    remNodes[id] = curNodes[id]
            for id in remNodes:
                del curNodes[id]
            if len(curNodes) == 0:
                delnsidList.append(nsid)

        for nsid in delnsidList:
            del self.nodeSets[nsid]
        return delnsidList
    
    def SetMaxID(self, maxID):
        self.maxID = maxID
        
    def FindMaxNSID(self):
        return self.maxID
    
    def CreateNodeSet(self, name):        
        self.maxID += 1
        nodeSet = NodeSet(name, self.maxID)
        nodeSet.setKeyword = "SET_NODE_LIST"
        self.AddNodeSet(nodeSet)
        
        return nodeSet
    
    def CreateNodeSetwithNodes(self, name, da1, da2, da3, da4, solver, its, nodes):
        self.maxID += 1
        nodeSet = NodeSet(name, self.maxID)
        nodeSet.SetDynaOption("SET_NODE_LIST", da1, da2, da3, da4, solver, its)
        nodeSet.AddNodes(nodes)
        return self.AddNodeSet(nodeSet)    
        
        
    def CreateNodeSetwithNodesNodeSetID(self, nsid, name, da1, da2, da3, da4, solver, its, nodes):
        nodeSet = NodeSet(name, nsid)
        nodeSet.SetDynaOption("SET_NODE_LIST", da1, da2, da3, da4, solver, its)
        nodeSet.AddNodes(nodes)
        return self.AddNodeSet(nodeSet)
    
    def CreateNodeSetListGenerate(self, name):
        self.maxID += 1
        nodeSet = NodeSetListGenerate(name, self.maxID)        
        return self.AddNodeSet(nodeSet)
    
    def CreateNodeSetListGeneratewithPairs(self, name, da1, da2, da3, da4, solver, its, nodeidPairs):
        self.maxID += 1
        nodeSet = NodeSetListGenerate(name, self.maxID)
        nodeSet.SetDynaOption("SET_NODE_LIST", da1, da2, da3, da4, solver, its)
        for pair in nodeidPairs:
            nodeSet.AddNodePair(pair[0],pair[1])
        return self.AddNodeSet(nodeSet)
            

    def AddNodeSet(self, nodeSet):
        self.nodeSets[nodeSet.sid] = nodeSet
        self.maxID = max(self.maxID, nodeSet.sid)
        return nodeSet
        
    def RemoveNodeSet(self, nodeSet):
        if nodeSet.sid in self.nodeSets:
            del self.nodeSets[nodeSet.sid]
            return True
        else:
            return False

    def RemoveNodeSetfromID(self, sid):
        if sid in self.nodeSets:
            del self.nodeSets[sid]
            return True
        else:
            return False

    def WritetoDynaKeyword(self, startID):
        keywords = ""
        for key in self.nodeSets:
            nodeSet = self.nodeSets[key]
            keywords += nodeSet.WritetoDynaKeyword(startID)
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for key in self.nodeSets:
            nodeSet = self.nodeSets[key]
            nodeSet.WriteStreamDynaKeyword(stream,startID)
        
    def AddNodeSetfromDyna(self, dynaSetNodes, nodeManager : NodeManager = None):
        if nodeManager is None:
            nodeManager = self.nodeManager
        for i in range(len(dynaSetNodes)):
            parameters = dynaSetNodes[i]
            curKeyword = parameters[0]

            if curKeyword == "*SET_NODE_LIST":
                
                setNodesOption = parameters[1]
                nsid = int(setNodesOption[0])
                name = "SetNode" + str(nsid)
                if len(setNodesOption[1].strip()) > 0:
                    da1 = float(setNodesOption[1])
                else:
                    da1 = 0.0
                if len(setNodesOption[2].strip()) > 0:
                    da2 = float(setNodesOption[2])
                else:
                    da2 = 0.0
                if len(setNodesOption[3].strip()) > 0:
                    da3 = float(setNodesOption[3])
                else:
                    da3 = 0.0
                if len(setNodesOption[4].strip()) > 0:
                    da4 = float(setNodesOption[4])
                else:
                    da4 = 0.0
                solver = setNodesOption[5]
                if len(setNodesOption[6].strip()) > 0:
                    its = int(setNodesOption[6])
                else:
                    its = 0
                    
                nodeids = parameters[2]
                # nodeids to int list but it has '' in the list, so remove it
                
                nodeids = [KooDynaInt(nodeid) for nodeid in nodeids]
                # remove 0 in the list
                nodeids = [nodeid for nodeid in nodeids if nodeid != 0]
                nodes = nodeManager.FindNodesfromIDs(nodeids)
                self.CreateNodeSetwithNodesNodeSetID(nsid, name, da1, da2, da3, da4, solver, its, nodes)
                
            elif curKeyword == "*SET_NODE_LIST_TITLE":
                name = parameters[1]
                setNodesOption = parameters[2]
                nsid = int(setNodesOption[0])
                if len(setNodesOption[1].strip()) > 0:
                    da1 = float(setNodesOption[1])
                else:
                    da1 = 0.0
                if len(setNodesOption[2].strip()) > 0:
                    da2 = float(setNodesOption[2])
                else:
                    da2 = 0.0
                if len(setNodesOption[3].strip()) > 0:
                    da3 = float(setNodesOption[3])
                else:
                    da3 = 0.0
                if len(setNodesOption[4].strip()) > 0:
                    da4 = float(setNodesOption[4])
                else:
                    da4 = 0.0
                solver = setNodesOption[5]
                if len(setNodesOption[6].strip()) > 0:
                    its = int(setNodesOption[6])
                else:
                    its = 0
                nodeids = parameters[3]
                nodeids = [int(nodeid) if nodeid.strip() != '' else 0 for nodeid in nodeids]
                nodeids = [nodeid for nodeid in nodeids if nodeid != 0]
                
                nodes = nodeManager.FindNodesfromIDs(nodeids)
                self.CreateNodeSetwithNodesNodeSetID(nsid, name, da1, da2, da3, da4, solver, its, nodes)
            elif curKeyword == "*SET_NODE_LIST_GENERATE":
                setNodesOption = parameters[1]
                nsid = int(setNodesOption[0])
                name = "SetNodeListGenerate" + str(nsid)
                if len(setNodesOption[1].strip()) > 0:
                    da1 = float(setNodesOption[1])
                else:
                    da1 = 0.0
                if len(setNodesOption[2].strip()) > 0:
                    da2 = float(setNodesOption[2])
                else:
                    da2 = 0.0
                if len(setNodesOption[3].strip()) > 0:
                    da3 = float(setNodesOption[3])
                else:
                    da3 = 0.0
                if len(setNodesOption[4].strip()) > 0:
                    da4 = float(setNodesOption[4])
                else:
                    da4 = 0.0
                solver = setNodesOption[5]
                if len(setNodesOption[6].strip()) > 0:
                    its = int(setNodesOption[6])
                else:
                    its = 0
                nodeidPairs = []
                for i in range(2, len(parameters)):
                    curParam = parameters[i]
                    if len(curParam[0].strip()) > 0:
                        start = int(curParam[0])
                    else:
                        start = 0
                    if len(curParam[1].strip()) > 0:
                        end = int(curParam[1])                        
                    else:
                        end = 0
                    if start != 0 and end != 0:
                        nodeidPairs.append([start,end])
                    if len(curParam[2].strip()) > 0:
                        start = int(curParam[2])
                    else:
                        start = 0
                    if len(curParam[3].strip()) > 0:
                        end = int(curParam[3])
                    else:
                        end = 0                        
                    if start != 0 and end != 0:
                        nodeidPairs.append([start,end])
                    if len(curParam[4].strip()) > 0:
                        start = int(curParam[4])
                    else:
                        start = 0
                    if len(curParam[5].strip()) > 0:
                        end = int(curParam[5])
                    else:
                        end = 0
                    if start != 0 and end != 0:
                        nodeidPairs.append([start,end])
                    if len(curParam[6].strip()) > 0:
                        start = int(curParam[6])
                    else:
                        start = 0
                    if len(curParam[7].strip()) > 0:
                        end = int(curParam[7])
                    else:
                        end = 0
                    if start != 0 and end != 0:
                        nodeidPairs.append([start,end])
                        
                self.CreateNodeSetListGeneratewithPairs(name, da1, da2, da3, da4, solver, its, nodeidPairs)
           
                
            