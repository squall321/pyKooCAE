from __future__ import annotations
import sys
import os
import numpy as np
from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooSection import *
from KooCAEManager.KooOperator import *
#from KooCAEManager.KooMeshManagerGMSH import *
from OCC.Core.BRepTools import breptools_Write
from scipy.ndimage import binary_dilation

from KooCAEManager.KooWarpage import *


def get_nodes(nodeManager, nids):
    """Helper function to find nodes from node IDs."""
    return [nodeManager.FindNodefromID(nid) for nid in nids]

class KooConstraintPart():
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.type = "None"
    
    def SetID(self, id):
        self.id = id
    
    def SetName(self, name):
        self.name = name
        
    def SetPartProperty(self, id, name):
        self.id = id
        self.name = name
        self.type = "None"
    
class KooConstrainedNodalRigidBodyPart(KooConstraintPart):
    def __init__(self, id = 0, name =""):
        super(KooConstrainedNodalRigidBodyPart,self).__init__(id,name)
        self.type = "ConstrainedNodalRigidBody"
        
        self.cid = 0
        self.nodeSet = None 
        self.pnode = 0 
        self.iprt = 0 
        self.drflag = 0 
        self.rrflag = 0         
    
    def CreateConstrainedOptions(self, cid, pnode, iprt, drflag, rrflag):
        self.cid = cid
        self.pnode = pnode
        self.iprt = iprt
        self.drflag = drflag
        self.rrflag = rrflag
        
    def CreateConstrainedOptionswithNodeSet(self, cid, nodeSet, pnode, iprt, drflag, rrflag):
        self.cid = cid
        self.nodeSet = nodeSet
        self.pnode = pnode
        self.iprt = iprt
        self.drflag = drflag
        self.rrflag = rrflag
    
    def AddDependentNode(self, node : Node, nodeSetManager : NodeSetManager):
        if self.nodeSet is None: 
            self.nodeSet = nodeSetManager.CreateNodeSet("NodeSetforConstrainedNodalRigidBody")        
        self.nodeSet.AddNode(node)        
        
    def AddDependentNodes(self, nodes, nodeSetManager : NodeSetManager):
        if self.nodeSet is None: 
            self.nodeSet = nodeSetManager.CreateNodeSet("NodeSetforConstrainedNodalRigidBody")
        self.nodeSet.AddNodes(nodes)
        
    def WritetoNastranPart(self,maxelemID):
        keywords = "RBE2    "        
        
        idstr = format(self.id+maxelemID,">8")
        keywords += f"{idstr}"
        count = 1
        nodes = self.nodeSet.nodes
        nodes = list(nodes.values())
        independentNode = nodes[0]
        
        nidstr = format(independentNode.id,">8")
        keywords += f"{nidstr}"
        count = count + 1
        
        dof = ""
        if self.drflag == 0:
            dof += "123"
        elif self.drflag == -1:
            dof += "23"
        elif self.drflag == -2:
            dof += "13"
        elif self.drflag == -3:
            dof += "12" 
        elif self.drflag == -4:
            dof += "3"
        elif self.drflag == -5:
            dof += "1"
        elif self.drflag == -6:
            dof += "2"
        elif self.drflag == -7:
            dof += ""
            
        if self.rrflag == 0:
            dof += "456"
        
        dofstr = format(dof,">8")
        keywords += f"{dofstr}"
        count = count + 1
        
        for i in range(1,len(nodes)):
            node = nodes[i]
            nidstr = format(node.id,">8")
            keywords += f"{nidstr}"
            count = count + 1
            if count % 8 == 0:
                keywords += "+\n"
                keywords += "+       "                        
        
        keywords += "\n"
        return keywords
        

    def WritetoDynaPart(self):
        keywords = "*CONSTRAINED_NODAL_RIGID_BODY\n"
        keywords += "$#     PID       CID      NSID     PNODE      IPRT    DRFLAG    RRFLAG\n"
        
        pidstr = format(self.id,">10")
        cidstr = format(self.cid,">10")
        nsidstr = format(self.nodeSet.sid,">10")
        pnodestr = format(self.pnode,">10")
        iprtstr = format(self.iprt,">10")
        drflagstr = format(self.drflag,">10")
        rrflagstr = format(self.rrflag,">10")
        
        keywords += f"{pidstr}{cidstr}{nsidstr}{pnodestr}{iprtstr}{drflagstr}{rrflagstr}\n"
        return keywords
        
    def WriteStreamDynaPart(self, stream):
        stream.write("*CONSTRAINED_NODAL_RIGID_BODY\n")
        stream.write("$#     PID       CID      NSID     PNODE      IPRT    DRFLAG    RRFLAG\n")
        pidstr = format(self.id,">10")
        cidstr = format(self.cid,">10")
        nsidstr = format(self.nodeSet.sid,">10")
        pnodestr = format(self.pnode,">10")
        iprtstr = format(self.iprt,">10")
        drflagstr = format(self.drflag,">10")
        rrflagstr = format(self.rrflag,">10")
        stream.write(f"{pidstr}{cidstr}{nsidstr}{pnodestr}{iprtstr}{drflagstr}{rrflagstr}\n")        
        
            
        


class KooPart():
    def __init__(self, nodeManager = None, elementManater = None, material = None, section = None, nodeSetManager = None):
        self.id = 0
        self.name = ""
        self.secid = 0
        self.mid = 0
        self.eosid = 0 
        self.hgid = 0
        self.grav = 0
        self.adpopt = 0
        self.tmid = 0
        self.partType = "Part"
        self.nodeManager : NodeManager = nodeManager
        self.elementManager : ElementManager = elementManater
        self.nodeSetManager : NodeSetManager = nodeSetManager
        self.modelType = "FEM"
        self.boundaryNodes = {}
        self.warpageTop : KooWarpage = None
        self.warpageBottom : KooWarpage = None
        
        if nodeManager is None:
            self.nodeManager = NodeManager()

        if elementManater is None:
            self.elementManager = ElementManager(self.nodeManager)
        
        if nodeSetManager is None:
            self.nodeSetManager = NodeSetManager(self.nodeManager)

        if material is not None:
            self.material : KooMaterial = material
            self.mid = material.id
        else:
            self.material : KooMaterial = None

        if section is not None:
            self.section : KooSection = section
            self.secid = section.id
        else:
            self.section : KooSection = None
            
        self.tempBrepFileName = "temp.brep"
        self.tempStlFileName = "temp.stl"
        self.tempGeoFileName = "temp.geo"
        self.tempMshFileName = "temp.msh"
        self.path = os.getcwd()
        
        self.SetPath(self.path)
        self.meshAlgoOption = "auto"
        from KooCAEManager.KooMeshImporter import KooMSHImporter
        self.mshImporter : KooMSHImporter = KooMSHImporter(self.nodeManager, self.elementManager)
        
    @staticmethod
    def _find_linux_gmsh(basePath=None):
        """리눅스에서 gmsh 경로를 찾는다. /opt → Library fallback → which gmsh"""
        candidates = [
            "/opt/gmsh-4.14.1-Linux64/bin/gmsh",
        ]
        if basePath is not None:
            for i in range(5):
                prefix = os.path.join(basePath, *(['..'] * i))
                candidates.append(os.path.join(prefix, "Library", "gmsh-4.14.1-Linux64", "bin", "gmsh"))
        else:
            candidates.append(os.path.join(".", "Library", "gmsh-4.14.1-Linux64", "bin", "gmsh"))
        for c in candidates:
            if os.path.exists(c):
                return c
        import shutil
        found = shutil.which("gmsh")
        if found:
            return found
        print("gmsh not found")
        sys.exit()

    def SetPath(self, path):
        self.path = path
        if sys.platform.startswith("win"):
            # find gmsh.exe in the path
            winCandidates = [
                os.path.join(path, ".\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                os.path.join(path, "..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                os.path.join(path, "..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                os.path.join(path, "..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                os.path.join(path, "..\\..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
            ]
            for c in winCandidates:
                if os.path.exists(c):
                    self.gmshPath = c
                    return
            print("gmsh.exe not found")
            sys.exit()
        else:
            self.gmshPath = self._find_linux_gmsh(path)

    def Translate(self, dx, dy, dz):
        nodes = self.elementManager.GetElementNodes()
        for nid in nodes:
            node : Node = nodes[nid]
            node.Translate(dx, dy, dz)
            
    def Rotate(self, angle = 90, axis = (0,0,1), center = (0,0,0)):
        trsf = gp_Trsf()
        trsf.SetRotation(gp_Ax1(gp_Pnt(center[0], center[1], center[2]), gp_Dir(axis[0], axis[1], axis[2])), math.radians(angle))
        nodes = self.elementManager.GetElementNodes()
        for nid in nodes:
            node : Node = nodes[nid]
            node.Rotate(trsf)
    
    def WarpZdirectionPartfromTopBottom(self, warpageFileTop, warpageFileBottom, xLoc, yLoc, zLoc, xLength, yLength, unitScale, amplitudeTop, amplitudeBottom, globalzMin, globalzMax, addedNodes):
        if xLength == 0.0 and yLength == 0.0:
            xmin, xmax, ymin, ymax, zmin, zmax = self.elementManager.GetBoundaryBox()
            xLoc = xmin
            yLoc = ymin
            zLoc = zmin
            xLength = xmax - xmin
            yLength = ymax - ymin
        else:
            xmin = xLoc
            xmax = xLoc + xLength
            ymin = yLoc
            ymax = yLoc + yLength
            _,_,_,_, zmin, zmax = self.elementManager.GetBoundaryBox()
        if globalzMin == 0.0 and globalzMax == 0.0:
            globalzMin = zmin
            globalzMax = zmax        
        self.warpageTop = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFileTop)
        self.warpageBottom = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFileBottom)
        self.warpageTop.SetWarpageUnit(unitScale)
        self.warpageBottom.SetWarpageUnit(unitScale)
        
        nodes = self.elementManager.GetElementNodes()
        xArray = np.zeros(len(nodes))
        yArray = np.zeros(len(nodes))
        zArrayTop = np.zeros(len(nodes))
        zArrayBottom = np.zeros(len(nodes))
        nidArray = np.zeros(len(nodes), dtype=int)
        i = 0
        for nid in nodes:
            node : Node = nodes[nid]
            if node.x < xmin or node.x > xmax or node.y < ymin or node.y > ymax:
                continue
            xArray[i] = node.x
            yArray[i] = node.y
            zArrayTop[i] = node.z
            zArrayBottom[i] = node.z
            nidArray[i] = nid
            i += 1
        self.warpageTop.GenerateZInterpolator()
        self.warpageBottom.GenerateZInterpolator()
        zAddArrayTop = self.warpageTop.GetZList(xArray, yArray)
        zAddArrayBottom = self.warpageBottom.GetZList(xArray, yArray)
        newAddedNodes = {}
        for i in range(len(nidArray)):
            nid = nidArray[i]
            if nid == 0:
                continue
            if nid in addedNodes:
                continue
            else:
                newAddedNodes[nid] = nid
            node : Node = nodes[nid]
            curPosZRatio = (node.z - globalzMin) / (globalzMax - globalzMin)
            node.z = node.z + amplitudeTop * zAddArrayTop[i] * curPosZRatio + amplitudeBottom * zAddArrayBottom[i] * (1 - curPosZRatio)
        return newAddedNodes
        
           
    def WarpZdirectionPart(self, warpageFile, xLoc, yLoc, zLoc, xLength = 0.0, yLength = 0.0, unit = "mm", amp = 1.0, addedNodes = {}):
        if xLength == 0.0 and yLength == 0.0:
            xmin, xmax, ymin, ymax, zmin, zmax = self.elementManager.GetBoundaryBox()
            xLoc = xmin
            yLoc = ymin
            zLoc = zmin
            xLength = xmax - xmin
            yLength = ymax - ymin
        else:
            xmin = xLoc
            xmax = xLoc + xLength
            ymin = yLoc
            ymax = yLoc + yLength
            _,_,_,_, zmin, zmax = self.elementManager.GetBoundaryBox()
             
        self.warpageTop = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFile)
        self.warpageTop.SetWarpageUnit(unit)
        
        nodes = self.elementManager.GetElementNodes()
        xArray = np.zeros(len(nodes))
        yArray = np.zeros(len(nodes))
        zArray = np.zeros(len(nodes))
        nidArray = np.zeros(len(nodes), dtype=int)
        i = 0
        for nid in nodes:
            node : Node = nodes[nid]
            if node.x < xmin or node.x > xmax or node.y < ymin or node.y > ymax:
                continue
            xArray[i] = node.x
            yArray[i] = node.y
            zArray[i] = node.z
            nidArray[i] = nid
            i += 1
        self.warpageTop.GenerateZInterpolator()
        zAddArray = self.warpageTop.GetZList(xArray, yArray)
        newAddedNodes = {} 
        for i in range(len(nidArray)):
            nid = nidArray[i]
            if nid == 0:
                continue
            if nid in addedNodes:
                continue
            else:
                newAddedNodes[nid] = nid
            node : Node = nodes[nid]
            node.z = node.z + amp*zAddArray[i] 
        return newAddedNodes
    
    def WarpZdirectionParttoInitialStress(self, warpageFileTop, xLoc, yLoc, zLoc, xLength, yLength, unitScale, amplitudeTop, addThickness):
        if xLength == 0.0 and yLength == 0.0:
            xmin, xmax, ymin, ymax, zmin, zmax = self.elementManager.GetBoundaryBox()
            xLoc = xmin
            yLoc = ymin
            zLoc = zmin
            xLength = xmax - xmin
            yLength = ymax - ymin
        else:
            xmin = xLoc
            xmax = xLoc + xLength
            ymin = yLoc
            ymax = yLoc + yLength
            _,_,_,_, zmin, zmax = self.elementManager.GetBoundaryBox()
        
        centerZ = (zmin + zmax) / 2.0
        self.warpageTop = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFileTop)
        self.warpageTop.SetWarpageUnit(unitScale)
        
        nodes = self.elementManager.GetElementNodes()
        xArray = np.zeros(len(nodes))
        yArray = np.zeros(len(nodes))
        zArray = np.zeros(len(nodes))
        nidArray = np.zeros(len(nodes), dtype=int)
        i = 0
        for nid in nodes:
            node : Node = nodes[nid]
            if node.x < xmin or node.x > xmax or node.y < ymin or node.y > ymax:
                continue
            xArray[i] = node.x
            yArray[i] = node.y
            zArray[i] = node.z
            nidArray[i] = nid
            i += 1
        self.warpageTop.GenerateZInterpolator()
        zAddArray = self.warpageTop.GetZList(xArray, yArray)
                
        zDict = {} 
        for i in range(len(nidArray)):
            nid = nidArray[i]
            if nid == 0:
                continue
            node : Node = nodes[nid]
            zDict[nid] = addThickness*(node.z - zmin)/(zmax - zmin)
            #amplitudeTop*zAddArray[i] + 
            node.AddDisplacement(0.0,0.0, zDict[nid])
        
        xArrayElement = np.zeros(len(self.elementManager.elements))
        yArrayElement = np.zeros(len(self.elementManager.elements))
        
        i = 0
        
        for eid in self.elementManager.elements:
            element : Element = self.elementManager.elements[eid]
            if element.type.lower() == "tetra4" or element.type.lower() == "hexa8":
                element : SolidElement = element
                centerPoint = element.GetCenterPoint()
                if centerPoint[0] < xmin or centerPoint[0] > xmax or centerPoint[1] < ymin or centerPoint[1] > ymax:
                    continue
                xArrayElement[i] = centerPoint[0]
                yArrayElement[i] = centerPoint[1]
                i = i + 1
        self.warpageTop.GenerateCurvatureInterpolator(amplitudeTop)
        dw2dx2, dw2dy2, dw2dxy = self.warpageTop.GetCurvatureList(xArrayElement, yArrayElement)
        
                
            
        E = self.material.GetE()
        nu = self.material.GetNu()
        EIDList = []
        S11List = [] 
        S22List = []
        S33List = []
        S12List = []
        S13List = []
        S23List = []        
        i = 0 

        boundaryElements = self.elementManager.GetBoundaryElements()
        for eid in self.elementManager.elements:
            element : Element = self.elementManager.elements[eid]
            if element.type.lower() == "tetra4" or element.type.lower() == "hexa8":
                element : SolidElement = element
                edw2dx2 = dw2dx2[i]
                edw2dy2 = dw2dy2[i]
                edw2dxy = dw2dxy[i]
                solidStressTensor = element.GetStressfromDisplacement(E, nu, -1)
                stressTensor = element.GetStressfromDisplacementandCurvatureXYPlane(E,nu, edw2dx2, edw2dy2, edw2dxy, centerZ,-1)
                stressTensor = -stressTensor  # sign change for initial stress
                if eid in boundaryElements:
                    #if boundaryElements[eid] == 1:
                    #    stressTensor = 0.5 * stressTensor
                    if boundaryElements[eid] > 2:
                        stressTensor = 0.5 * stressTensor
                EIDList.append(eid)
                S11List.append([stressTensor[0][0]])
                S22List.append([stressTensor[1][1]])
                S33List.append([stressTensor[2][2]])
                S12List.append([stressTensor[0][1]])
                S13List.append([stressTensor[0][2]])  
                S23List.append([stressTensor[1][2]])
                i = i + 1
            else:
                continue
            
        return EIDList, S11List, S22List, S33List, S12List, S13List, S23List
    
    def WarpZdirectionPartfromTopBottomtoInitialStress(self, warpageFileTop, warpageFileBottom, xLoc, yLoc, zLoc, xLength, yLength, unitScale, amplitudeTop, amplitudeBottom, zmin, zmax, addThickness):
        if xLength == 0.0 and yLength == 0.0:
            xmin, xmax, ymin, ymax, zmin, zmax = self.elementManager.GetBoundaryBox()
            xLoc = xmin
            yLoc = ymin
            zLoc = zmin
            xLength = xmax - xmin
            yLength = ymax - ymin
        else:
            xmin = xLoc
            xmax = xLoc + xLength
            ymin = yLoc
            ymax = yLoc + yLength
            _,_,_,_, zmin, zmax = self.elementManager.GetBoundaryBox()
        
        centerZ = (zmin + zmax) / 2.0
        self.warpageTop = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFileTop) 
        self.warpageBottom = KooWarpage(xLoc, yLoc, xLength, yLength, warpageFileBottom)
        self.warpageTop.SetWarpageUnit(unitScale)
        self.warpageBottom.SetWarpageUnit(unitScale)
        
        nodes = self.elementManager.GetElementNodes()
        xArray = np.zeros(len(nodes))
        yArray = np.zeros(len(nodes))
        zArrayTop = np.zeros(len(nodes))
        zArrayBottom = np.zeros(len(nodes))
        nidArray = np.zeros(len(nodes), dtype=int)
        i = 0
        for nid in nodes:
            node : Node = nodes[nid]
            if node.x < xmin or node.x > xmax or node.y < ymin or node.y > ymax:
                continue
            xArray[i] = node.x
            yArray[i] = node.y
            zArrayTop[i] = node.z
            zArrayBottom[i] = node.z
            nidArray[i] = nid
            i += 1
        self.warpageTop.GenerateZInterpolator()
        self.warpageBottom.GenerateZInterpolator()
        zAddArrayTop = self.warpageTop.GetZList(xArray, yArray)
        zAddArrayBottom = self.warpageBottom.GetZList(xArray, yArray)
        
        zDict = {}
        for i in range(len(nidArray)):
            nid = nidArray[i]
            if nid == 0:
                continue
            node : Node = nodes[nid]
            zDict[nid] = addThickness*(node.z - zmin)/(zmax - zmin)
            node.AddDisplacement(0.0,0.0, zDict[nid])
        
        xArrayElement = np.zeros(len(self.elementManager.elements))
        yArrayElement = np.zeros(len(self.elementManager.elements))
        
        i = 0
        for eid in self.elementManager.elements:
            element : Element = self.elementManager.elements[eid]
            if element.type.lower() == "tetra4" or element.type.lower() == "hexa8":
                element : SolidElement = element
                centerPoint = element.GetCenterPoint()
                if centerPoint[0] < xmin or centerPoint[0] > xmax or centerPoint[1] < ymin or centerPoint[1] > ymax:
                    continue
                xArrayElement[i] = centerPoint[0]
                yArrayElement[i] = centerPoint[1]
                i = i + 1
        self.warpageTop.GenerateCurvatureInterpolator(amplitudeTop)
        self.warpageBottom.GenerateCurvatureInterpolator(amplitudeBottom)
        dw2dx2Top, dw2dy2Top, dw2dxyTop = self.warpageTop.GetCurvatureList(xArrayElement, yArrayElement)
        dw2dx2Bottom, dw2dy2Bottom, dw2dxyBottom = self.warpageBottom.GetCurvatureList(xArrayElement, yArrayElement)
        
        E = self.material.GetE()
        nu = self.material.GetNu()
        EIDList = []
        S11List = []
        S22List = []
        S33List = []
        S12List = []
        S13List = []
        S23List = []
        i = 0
        boundaryElements = self.elementManager.GetBoundaryElements()
        for eid in self.elementManager.elements:
            element : Element = self.elementManager.elements[eid]
            if element.type.lower() == "tetra4" or element.type.lower() == "hexa8":
                element : SolidElement = element
                edw2dx2Top = dw2dx2Top[i]
                edw2dy2Top = dw2dy2Top[i]
                edw2dxyTop = dw2dxyTop[i]
                edw2dx2Bottom = dw2dx2Bottom[i]
                edw2dy2Bottom = dw2dy2Bottom[i]
                edw2dxyBottom = dw2dxyBottom[i]
   
                stressTensor = element.GetStressfromDisplacementandTopBottomCurvatureXYPlane(E, nu, edw2dx2Top, edw2dy2Top, edw2dxyTop, edw2dx2Bottom, edw2dy2Bottom, edw2dxyBottom, zmin, zmax, -1)
                stressTensor = -stressTensor  # sign change for initial stress
                if eid in boundaryElements:
                    if boundaryElements[eid] > 2:
                        stressTensor = 0.5 * stressTensor
                EIDList.append(eid)
                S11List.append([stressTensor[0][0]])
                S22List.append([stressTensor[1][1]])
                S33List.append([stressTensor[2][2]])
                S12List.append([stressTensor[0][1]])
                S13List.append([stressTensor[0][2]])
                S23List.append([stressTensor[1][2]])
                i = i + 1
            else:
                continue
        return EIDList, S11List, S22List, S33List, S12List, S13List, S23List 
    
    def LengthVariationbyTolerance(self, ex, ey, ez):
        E = self.material.GetE()
        nu = self.material.GetNu()
        EIDList = []
        S11List = []
        S22List = []
        S33List = []
        S12List = []
        S13List = []
        S23List = []
        i = 0
        #boundaryElements = self.elementManager.GetBoundaryElements()
        for eid in self.elementManager.elements:
            element : SolidElement = self.elementManager.elements[eid]            
            stressTensor = element.GetStressWithDirectionalExpansion(E, nu, ex, ey, ez, True)
            stressTensor = -stressTensor
            #if eid in boundaryElements:
            #    if boundaryElements[eid] > 2:
            #        stressTensor = 0.5 * stressTensor
            EIDList.append(eid)
            S11List.append([stressTensor[0][0]])
            S22List.append([stressTensor[1][1]])
            S33List.append([stressTensor[2][2]])
            S12List.append([stressTensor[0][1]])
            S13List.append([stressTensor[0][2]])
            S23List.append([stressTensor[1][2]])
            i = i + 1

        return EIDList, S11List, S22List, S33List, S12List, S13List, S23List

    def LaplacianSmoothingwithoutExceptedNodes(self, exceptedNodes, niter = 1):
        totalNodes = {} 
        for element in self.elementManager.elements.values():
            for node in element.nodes:
                totalNodes[node.id] = node
        for nid in exceptedNodes:
            if nid in totalNodes:
                del totalNodes[nid]
            
        for i in range(niter):
            for node in totalNodes.values():
                node.LaplacianSmoothingZ()
                
    def ZAxisSmoothingwithoutExceptedNodes(self, exceptedNodes, niter = 1, zDir = [0,0,1]):
        zDirArray = np.array(zDir)
        totalNodes = {} 
        for element in self.elementManager.elements.values():
            for node in element.nodes:
                totalNodes[node.id] = node
        for nid in exceptedNodes:
            if nid in totalNodes:
                del totalNodes[nid]
        
        for i in range(niter):
            for node in totalNodes.values():
                node.ZAxisSmoothingZ(zDirArray)
    
    def ZAxisSmoothingwithNodesandExceptedNodes(self,nodes, exceptedNodes, niter = 1, zDir = [0,0,1]):        
        zDirArray = np.array(zDir)
        for nid in exceptedNodes:
            if nid in nodes:
                del nodes[nid]
        for i in range(niter):
            for node in nodes.values():
                node.ZAxisSmoothingZ(zDirArray)
        

    def SetMaterial(self, material : KooMaterial):
        self.material = material
        self.mid = material.id

    def SetMaterialbyID(self, materialManager : KooMaterialManager, id=0):
        if id == 0:
            self.material = materialManager.FindMaterialfromID(self.mid)
        else:
            self.material = materialManager.FindMaterialfromID(id)
            self.mid = id
    
    def SetSection(self, section : KooSection):
        self.section = section
        self.secid = section.id        

    def SetSectionbyID(self, sectionManager : KooSectionManager, id=0):
        if id == 0:
            self.section = sectionManager.FindSectionfromID(self.secid)
        else:
            self.section = sectionManager.FindSectionfromID(id)
            self.secid = id
    
    def GetCenterX(self):
        x = 0
        n = 0
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                n += 1
                x += node.x
        if n == 0:
            return 0
        else:
            return x / n
        
    def GetCenterY(self):
        y = 0
        n = 0
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                n += 1
                y += node.y
        if n == 0:
            return 0
        else:
            return y / n        

    def GetCenterZ(self):
        z = 0
        n = 0
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                n += 1
                z += node.z
        if n == 0:
            return 0
        else:
            return z / n
        
        
    def MorphwithBox(self, loc, boxLength, xDir, zDir, distance, mode, effectRadius, angle = 360.0):
        
        if angle == 360.0:            
            boundaryNodes = self.boundaryNodes
        else:
            boundaryNodes = self.elementManager.GetBoundaryNodesWithVectorwithAngle(zDir,angle)
        if len(boundaryNodes) == 0:
            boundaryNodes = self.SetBoundaryNodes()
        # array with size of boundaryNodes
        boundaryNodePoints = np.zeros((len(boundaryNodes), 3))
        
        for i, nodeid in enumerate(boundaryNodes):
            node = boundaryNodes[nodeid]
            boundaryNodePoints[i][0] = node.x
            boundaryNodePoints[i][1] = node.y
            boundaryNodePoints[i][2] = node.z
        
        yDir = np.cross(zDir, xDir)
        yDir = yDir / np.linalg.norm(yDir)
                
        xLength = boxLength[0]
        yLength = boxLength[1]
        
        p1 = [loc[0] + xDir[0] * xLength / 2.0 + yDir[0] * yLength / 2.0, loc[1] + xDir[1] * xLength / 2.0 + yDir[1] * yLength / 2.0, loc[2] + xDir[2] * xLength / 2.0 + yDir[2] * yLength / 2.0]
        p2 = [loc[0] + xDir[0] * xLength / 2.0 - yDir[0] * yLength / 2.0, loc[1] + xDir[1] * xLength / 2.0 - yDir[1] * yLength / 2.0, loc[2] + xDir[2] * xLength / 2.0 - yDir[2] * yLength / 2.0]
        p3 = [loc[0] - xDir[0] * xLength / 2.0 - yDir[0] * yLength / 2.0, loc[1] - xDir[1] * xLength / 2.0 - yDir[1] * yLength / 2.0, loc[2] - xDir[2] * xLength / 2.0 - yDir[2] * yLength / 2.0]
        p4 = [loc[0] - xDir[0] * xLength / 2.0 + yDir[0] * yLength / 2.0, loc[1] - xDir[1] * xLength / 2.0 + yDir[1] * yLength / 2.0, loc[2] - xDir[2] * xLength / 2.0 + yDir[2] * yLength / 2.0]
        
        polygon3D = np.array([p1, p2, p3, p4])
                            
        direction = zDir
        
        inplaneDistances = distance_from_prism_edge(boundaryNodePoints, polygon3D, direction)
        #inplaneDistances = elliptical_distance_from_box(boundaryNodePoints, polygon3D, xDir, yDir, boxLength, effectRadius)

        print(max(inplaneDistances), min(inplaneDistances),effectRadius)
        if mode == "Pull":
            distance = -distance                            
            
      
        for i, nodeid in enumerate(boundaryNodes):
            node = boundaryNodes[nodeid]
            inDistance = inplaneDistances[i]

            if 0 <= inDistance < effectRadius:
                factor = math.cos((math.pi / 2.0) * (inDistance / effectRadius))
                
                if factor < 0.0:
                    factor = 0.0
                curLength = distance * factor
               
                node.x += direction[0] * curLength
                node.y += direction[1] * curLength
                node.z += direction[2] * curLength
               
        
        if angle == 360.0:
            self.LaplacianSmoothingwithoutExceptedNodes(boundaryNodes,2)
        else:
            #for bid in self.elementManager.GetExternalNodes():
            #    boundaryNodes[bid.id] = self.nodeManager.nodes[bid.id]
            #invZdir = np.array([-zDir[0], -zDir[1], -zDir[2]])
            #addBoundaryNodes = self.elementManager.GetBoundaryNodesWithVectorwithAngle(invZdir,angle)
            #for bid in addBoundaryNodes:
            #    boundaryNodes[bid] = addBoundaryNodes[bid]
            #boundaryNodes.update(addBoundaryNodes)
            boundaryNodes = self.SetBoundaryNodes()
            #self.LaplacianSmoothingwithoutExceptedNodes(boundaryNodes,2)
            #self.ZAxisSmoothingwithoutExceptedNodes(boundaryNodes,7,zDir)
            xmin = loc[0] - xLength / 2.0 - effectRadius
            xmax = loc[0] + xLength / 2.0 + effectRadius
            ymin = loc[1] - yLength / 2.0 - effectRadius
            ymax = loc[1] + yLength / 2.0 + effectRadius
            nodes = self.GetNodesinXYBox(xmin, ymin, xmax, ymax)

            self.ZAxisSmoothingwithNodesandExceptedNodes(nodes, boundaryNodes, 7, zDir)
            
    def GetNodesinXYBox(self, xmin, ymin, xmax, ymax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.x >= xmin and node.x <= xmax and node.y >= ymin and node.y <= ymax:
                    nodes[node.id] = node
        return nodes

    def SetBoundaryNodes(self):
        # faces 추출        
        nodes = self.nodeManager.nodes        
        self.boundaryNodes = {}
        boundary = self.elementManager.GetExternalTriBoundary()
        for i in range(len(boundary)):
            face = boundary[i]
            for j in range(len(face)):
                self.boundaryNodes[face[j]] = nodes[face[j]]            
        return self.boundaryNodes

    def GetPartDimension(self):
        num1D = 0
        num2D = 0
        num3D = 0
        for element in self.elementManager.elements.values():
            element : Element = element
            if element.type == "BEAM2":
                num1D += 1
            elif element.type == "TRI3" or element.type == "QUAD4":
                num2D += 1
            elif element.type == "TETRA4" or element.type == "HEXA8" or element.type == "PENTA6":
                num3D += 1
        if num3D > 0:
            return 3
        elif num2D > 0:
            return 2
        else:
            return 1

    def GetShellSegmentList(self):
        nodes = []
        for element in self.elementManager.elements.values():
            element : Element = element
            locNodes = [] 
            if element.type == "TRI3":
                locNodes = [element.nodes[0], element.nodes[1], element.nodes[2], element.nodes[2]]
            elif element.type == "QUAD4":
                locNodes = [element.nodes[0], element.nodes[1], element.nodes[2], element.nodes[3]]
            #extend nodes 
            for node in locNodes:
                nodes.append(node)
        
        return nodes


    def GetNodesonPart(self):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                nodes[node.id] = node
        return nodes

    def GetNodesXRange(self, xMin, xMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.x >= xMin and node.x <= xMax:
                    nodes[node.id] = node
        return nodes

    def GetNodesYRange(self, yMin, yMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.y >= yMin and node.y <= yMax:
                    nodes[node.id] = node
        return nodes

    def GetNodesZRange(self, zMin, zMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.z >= zMin and node.z <= zMax:
                    nodes[node.id] = node
        return nodes     

    def GetNodesXRangeYRange(self, xMin, xMax, yMin, yMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.x >= xMin and node.x <= xMax and node.y >= yMin and node.y <= yMax:
                    nodes[node.id] = node
        return nodes

    def GetNodesXRangeZRange(self, xMin, xMax, zMin, zMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.x >= xMin and node.x <= xMax and node.z >= zMin and node.z <= zMax:
                    nodes[node.id] = node
        return nodes

    def GetNodesYRangeZRange(self, yMin, yMax, zMin, zMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.y >= yMin and node.y <= yMax and node.z >= zMin and node.z <= zMax:
                    nodes[node.id] = node
        return nodes

    def GetNodesXRangeYRangeZRange(self, xMin, xMax, yMin, yMax, zMin, zMax):
        nodes = {}
        for element in self.elementManager.elements.values():
            element : Element = element
            for node in element.nodes:
                node : Node = node
                if node.x >= xMin and node.x <= xMax and node.y >= yMin and node.y <= yMax and node.z >= zMin and node.z <= zMax:
                    nodes[node.id] = node
        return nodes                  
    
    def SetAsPeridynamics(self):
        self.nodeManager.SplitNodes()
        self.modelType = "PERI"
         
    def SetModelTypebySection(self, secManager : KooSectionManager):
        curSection = secManager.FindSectionfromID(self.secid)        
        if curSection is None:
            self.modelType = "FEM"
        
        if type(curSection) == KooSectionSolidPeri:
            self.modelType = "PERI"
        else:
            self.modelType = "FEM"

    def NElement(self):
        return self.elementManager.NElement()

    def SetID(self, id):
        self.id = id
        self.elementManager.SetID(id)
    
    def SetName(self, name):
        self.name = name

    def SetPID(self, id):
        self.id = id 
    
    def SetSectionID(self, id):
        self.secid = id
    
    def SetMaterialID(self, id):
        self.mid = id
    
    def SetEOSID(self, id):
        self.eosid = id            
        
    def SetPartProperty(self, id, name, secid, mid, eosid, hgid, grav, adpopt, tmid):
        self.id = id
        self.name = name 
        self.secid = secid
        self.mid = mid
        self.eosid = eosid 
        self.hgid = hgid
        self.grav = grav
        self.adpopt = adpopt
        self.tmid = tmid

    def AddLineLinearElement(self, eid, n1, n2, rt1, rr1, rt2, rr2, local):
        self.elementManager.AddLineLinearElement(eid,n1,n2,rt1,rr1,rt2,rr2, local)
    
    def AddLineQuadraticElement(self, eid, n1, n2, n3, rt1, rr1, rt2, rr2, local):
        self.elementManager.AddLineQuadraticElement(eid,n1,n2,n3,rt1,rr1,rt2,rr2, local)

    def AddTriangleLinearElement(self, eid, n1, n2, n3):
        self.elementManager.AddTriangleLinearElement(eid,n1,n2,n3)
    
    def AddTriangleLinearElementThetaBeta(self,eid,n1,n2,n3,theta1,theta2,theta3,theta4,beta):
        e = self.elementManager.AddTriangleLinearElement(eid,n1,n2,n3)
        e.SetThetaBeta4(theta1,theta2,theta3,theta4,beta)
    
    def AddTriangleQuadraticElement(self, eid, n1, n2, n3, n4, n5, n6):
        self.elementManager.AddTriangleQuadraticElement(eid,n1,n2,n3,n4,n5,n6)
    
    def AddTriangleQuadraticElementThetaBeta(self,eid,n1,n2,n3,n4,n5,n6,theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8,beta):
        e = self.elementManager.AddTriangleQuadraticElement(eid,n1,n2,n3,n4,n5,n6)
        e.SetThetaBeta8(theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8,beta)

    def AddQuadrangleLinearElement(self, eid, n1, n2, n3, n4):
        self.elementManager.AddQuadrangleLinearElement(eid,n1,n2,n3,n4)
    
    def AddQuadrangleLinearElementThetaBeta(self,eid,n1,n2,n3,n4,theta1,theta2,theta3,theta4,beta):
        e = self.elementManager.AddQuadrangleLinearElement(eid,n1,n2,n3,n4)
        e.SetThetaBeta4(theta1,theta2,theta3,theta4,beta)

    def AddQuadrangleQuadraticElement(self, eid, n1, n2, n3, n4, n5, n6, n7, n8):
        self.elementManager.AddQuadrangleQuadraticElement(eid,n1,n2,n3,n4,n5,n6,n7,n8)
    
    def AddQuadrangleQuadraticElementThetaBeta(self,eid,n1,n2,n3,n4,n5,n6,n7,n8,theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8,beta):
        e = self.elementManager.AddQuadrangleQuadraticElement(eid,n1,n2,n3,n4,n5,n6,n7,n8)
        e.SetThetaBeta8(theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8,beta)
            
    def AddTetrahedronLinearElement(self, eid, n1, n2, n3, n4):
        self.elementManager.AddTetrahedronLinearElement(eid,n1,n2,n3,n4)
    
    def AddTetrahedronQuadraticElement(self, eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10):
        self.elementManager.AddTetrahedronQuadraticElement(eid,n1,n2,n3,n4,n5,n6,n7,n8,n9,n10)
        
    def AddPentahedronLinearElement(self, eid, n1, n2, n3, n4, n5, n6):
        self.elementManager.AddPentahedronLinearElement(eid,n1,n2,n3,n4,n5,n6)
    
    def AddHexahedronLinearElement(self, eid, n1, n2, n3, n4, n5, n6, n7, n8):
        self.elementManager.AddHexahedronLinearElement(eid,n1,n2,n3,n4,n5,n6,n7,n8)
    
    def AddHexahedronQuadraticElement(self, eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16, n17, n18, n19, n20):
        self.elementManager.AddHexahedronQuadraticElement(eid,n1,n2,n3,n4,n5,n6,n7,n8,n9,n10,n11,n12,n13,n14,n15,n16,n17,n18,n19,n20)

    def WritetoNastranPart(self):
        curString = ""
        dim = self.GetPartDimension()
        if dim == 3:
            curString += "PSOLID  "
            curString += f"{self.id:>8}"
            curString += f"{self.mid:>8}"
            # coordinate
            curString += "       0"
            curString += "\n"
        return curString

    def WritetoDynaPart(self,startPID = 0):
        curString = "*PART\n"
        curString += f"{self.name}\n"        
        
        curString += "$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID\n"
        formatString = f"{str(self.id + startPID):>10}{str(self.secid):>10}{str(self.mid):>10}{str(self.eosid):>10}{str(self.hgid):>10}{str(self.grav):>10}{str(self.adpopt):>10}{str(self.tmid):>10}\n"
        curString += formatString        
        return curString
    
    def WriteStreamDynaPart(self, stream, startPID = 0):
        stream.write("*PART\n")
        stream.write(f"{self.name}\n")
        stream.write("$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID\n")
        formatString = f"{str(self.id + startPID):>10}{str(self.secid):>10}{str(self.mid):>10}{str(self.eosid):>10}{str(self.hgid):>10}{str(self.grav):>10}{str(self.adpopt):>10}{str(self.tmid):>10}\n"
        stream.write(formatString)        
    
    def WritetoNasranNodes(self, startNID):
        return self.nodeManager.WritetoNastranKeyword(startNID)

    def WritetoDynaNodes(self, startNID):
        return self.nodeManager.WritetoDynaKeyword(startNID)
    
    def WritetoDynaNodeSets(self, startNSID):
        return self.nodeSetManager.WritetoDynaKeyword(startNSID)        

    def WritetoABAQUSNodes(self, startNID):
        return self.nodeManager.WritetoABAQUSKeyword(startNID)
    
    def WritetoABAQUSStreamNodes(self, stream, startNID):
        self.nodeManager.WriteStreamABAQUSKeyword(stream, startNID)
    
    def WritetoANSYSAPDLNodes(self, startNID):
        return self.nodeManager.WritetoANSYSAPDLKeyword(startNID)
    
    def WritetoNastranStreamElements(self, stream, startNID, startEID):
        self.elementManager.WritetoNastranStream(stream, self.id, startNID, startEID)
       
    def WritetoNastranElements(self, startNID, startEID):
        return self.elementManager.WritetoNastranKeyword(self.id, startNID, startEID)
    
    def WritetoNastranShellElements(self, startNID, startEID):
        return self.elementManager.WritetoNastranKeywordFace(self.id, startNID, startEID)
    
    def WritetoNastranSolidElements(self, startNID, startEID):
        return self.elementManager.WritetoNastranKeywordSolid(self.id, startNID, startEID)    
    
    def WritetoDynaElements(self, startNID, startEID):
        return self.elementManager.WritetoDynaKeyword(self.id, startNID, startEID)

    def WritetoDynaBeamElements(self, startNID, startEID):
        return self.elementManager.WritetoDynaKeywordLine(self.id, startNID, startEID)

    def WritetoDynaShellElements(self, startNID, startEID):        
        return self.elementManager.WritetoDynaKeywordFace(self.id, startNID, startEID)    

    def WritetoDynaSolidElements(self, startNID, startEID):
        return self.elementManager.WritetoDynaKeywordSolid(self.id, startNID, startEID)
      
    def WriteStreamDynaElements(self, stream, startNID, startEID):
        self.elementManager.WriteStreamDynaKeyword(stream, self.id, startNID, startEID)
    
    def WriteStreamDynaBeamElements(self, stream, startNID, startEID):
        self.elementManager.WriteStreamDynaKeywordLine(stream, self.id, startNID, startEID)
    
    def WriteStreamDynaShellElements(self, stream, startNID, startEID):
        self.elementManager.WriteStreamDynaKeywordFace(stream, self.id, startNID, startEID)
    
    def WriteStreamDynaSolidElements(self, stream, startNID, startEID):
        self.elementManager.WriteStreamDynaKeywordSolid(stream, self.id, startNID, startEID)
              
    def WritetoAnsysAPDLPointElements(self, startNID, startEID):
        if self.elementManager.GetNumberofPointElements() >0:
            ansysString = ""
            ansysString += "ET,{pid},mass21\n".format(self.id)
            ansysString += "KEYOPT,{pid},3,0\n".format(self.id)
            ansysString += self.elementManager.WritetoAnsysAPDLPoint(self.id, startNID, startEID)
        return 
    
    def WritetoAnsysAPDLShellElements(self, startNID, startEID):
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
        self.section : KooSectionShell = self.section
        ansysString = "" 
        if self.elementManager.GetNumberofLinearFaceElements() >0:            
            ansysString += "ET,{pid},SHELL181\n".format(pid = self.id)
            #ansysString += "KEYOPT,8,1\n"
            ansysString += self.section.GenerateAnsysAPDLKeyword(mid)
            ansysString += "type,{pid}\n".format(pid = self.id)            
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += "secnum,{pid}\n".format(pid = self.id)            
            ansysString += self.elementManager.WritetoAnsysAPDLFaceLinear(self.id, startNID, startEID)
        if self.elementManager.GetNumberofQuadraticFaceElements() >0:
            ansysString += "ET,{pid},SHELL281\n".format(pid = self.id)
            #ansysString += "KEYOPT,8,1\n"
            ansysString += self.section.GenerateAnsysAPDLKeyword(mid)
            ansysString += "type,{pid}\n".format(pid = self.id)
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += "secnum,{pid}\n".format(pid = self.id)            
            ansysString += self.elementManager.WritetoAnsysAPDLFaceQuadratic(self.id, startNID, startEID)
        return ansysString
    
    def WritetoABAQUSStreamElements(self, stream, startNID, startEID, materialManager : KooMaterialManager = None):
        if materialManager is not None:
            self.SetMaterialbyID(materialManager)
        self.WritetoABAQUSStreamShellElements(stream, startNID, startEID)
        self.WritetoABAQUSStreamSolidElements(stream, startNID, startEID)
    
    def WritetoABAQUSShellElements(self, startNID, startEID):
        abaqusString = ""
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
        if self.elementManager.GetNumberofTri3Elements() >0:            
            abaqusString += self.elementManager.WritetoABAQUSTri3(self.id, startNID, startEID)
            elesetName = "PART_Tri3_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
            abaqusString += "{thickness}\n".format(thickness = self.section.T1)
        if self.elementManager.GetNumberofTri6Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSTri6(self.id, startNID, startEID)
            elesetName = "PART_Tri6_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
            abaqusString += "{thickness}\n".format(thickness = self.section.T1)            
        if self.elementManager.GetNumberofQuad4Elements() >0:            
            abaqusString += self.elementManager.WritetoABAQUSQuad4(self.id, startNID, startEID)
            elesetName = "PART_Quad4_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
            abaqusString += "{thickness}\n".format(thickness = self.section.T1)            
        if self.elementManager.GetNumberofQuad8Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSQuad8(self.id, startNID, startEID)            
            elesetName = "PART_Quad8_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
            abaqusString += "{thickness}\n".format(thickness = self.section.T1)            
        return abaqusString
    
    def WritetoABAQUSStreamShellElements(self, stream, startNID, startEID):
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
        
        if self.elementManager.GetNumberofTri3Elements() >0:
            self.elementManager.WritetoABAQUSStreamTri3(stream, self.id, startNID, startEID)
            elesetName = "PART_Tri3_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
            stream.write("{thickness}\n".format(thickness = self.section.T1))
        if self.elementManager.GetNumberofTri6Elements() >0:
            self.elementManager.WritetoABAQUSStreamTri6(stream, self.id, startNID, startEID)
            elesetName = "PART_Tri6_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
            stream.write("{thickness}\n".format(thickness = self.section.T1))
        if self.elementManager.GetNumberofQuad4Elements() >0:
            self.elementManager.WritetoABAQUSStreamQuad4(stream, self.id, startNID, startEID)
            elesetName = "PART_Quad4_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
            stream.write("{thickness}\n".format(thickness = self.section.T1))
        if self.elementManager.GetNumberofQuad8Elements() >0:
            self.elementManager.WritetoABAQUSStreamQuad8(stream, self.id, startNID, startEID)
            elesetName = "PART_Quad8_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
            stream.write("{thickness}\n".format(thickness = self.section.T1))                        
    
    def WritetoAnsysAPDLSolidElements(self, startNID, startEID):
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
        ansysString = ""
        if self.elementManager.GetNumberofHexa8Elements() >0:
            ansysString += "ET,{pid},SOLID185\n".format(pid = self.id)
            ansysString += "type,{pid}\n".format(pid = self.id)
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += self.elementManager.WritetoAnsysAPDLSolidHexa8(self.id, startNID, startEID)
        if self.elementManager.GetNumberofHexa20Elements() >0:
            ansysString += "ET,{pid},SOLID186\n".format(pid = self.id)
            ansysString += "type,{pid}\n".format(pid = self.id)
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += self.elementManager.WritetoAnsysAPDLSolidHexa20(self.id, startNID, startEID)
        if self.elementManager.GetNumberofTetra4Elements() >0:
            ansysString += "ET,{pid},SOLID285\n".format(pid = self.id)
            ansysString += "type,{pid}\n".format(pid = self.id)
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += self.elementManager.WritetoAnsysAPDLSolidTetra4(self.id, startNID, startEID)
        if self.elementManager.GetNumberofTetra10Elements() >0:
            ansysString += "ET,{pid},SOLID187\n".format(pid = self.id)
            ansysString += "type,{pid}\n".format(pid = self.id)
            ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += self.elementManager.WritetoAnsysAPDLSolidTetra10(self.id, startNID, startEID)
        return ansysString        

    def WritetoABAQUSSolidElements(self, startNID, startEID):
        abaqusString = ""
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
            
        if self.elementManager.GetNumberofHexa8Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSHexa8(self.id, startNID, startEID)
            elesetName = "PART_Hexa8_{pid}".format(pid = self.id)
            abaqusString += "*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
        if self.elementManager.GetNumberofHexa20Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSHexa20(self.id, startNID, startEID)
            elesetName = "PART_Hexa20_{pid}".format(pid = self.id)
            abaqusString += "*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)            
        if self.elementManager.GetNumberofTetra4Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSTetra4(self.id, startNID, startEID)
            elesetName = "PART_Tetra4_{pid}".format(pid = self.id)
            abaqusString += "*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
        if self.elementManager.GetNumberofTetra10Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSTetra10(self.id, startNID, startEID)
            elesetName = "PART_Tetra10_{pid}".format(pid = self.id)
            abaqusString += "*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid)
        return abaqusString
    
    def WritetoABAQUSStreamSolidElements(self, stream, startNID, startEID):
        if self.material is None:
            mid = 1
        else:
            mid = self.material.id
        if self.elementManager.GetNumberofHexa8Elements() >0:
            self.elementManager.WritetoABAQUSStreamHexa8(stream, self.id, startNID, startEID)
            elesetName = "PART_Hexa8_{pid}".format(pid = self.id)
            stream.write("*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
        if self.elementManager.GetNumberofHexa20Elements() >0:
            self.elementManager.WritetoABAQUSStreamHexa20(stream, self.id, startNID, startEID)
            elesetName = "PART_Hexa20_{pid}".format(pid = self.id)
            stream.write("*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
        if self.elementManager.GetNumberofTetra4Elements() >0:
            self.elementManager.WritetoABAQUSStreamTetra4(stream, self.id, startNID, startEID)
            elesetName = "PART_Tetra4_{pid}".format(pid = self.id)
            stream.write("*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))
        if self.elementManager.GetNumberofTetra10Elements() >0:
            self.elementManager.WritetoABAQUSStreamTetra10(stream, self.id, startNID, startEID)
            elesetName = "PART_Tetra10_{pid}".format(pid = self.id)
            stream.write("*Solid Section, elset={setname}, material={mid}\n".format(setname = elesetName, mid = mid))                                
        
    def WritetoABAQUSElements(self, startNID, startEID):
        abaqusString = "" 
        if self.elementManager.GetNumberofHexa8Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSHexa8(self.id, startNID, startEID)
        if self.elementManager.GetNumberofHexa20Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSHexa20(self.id, startNID, startEID)
        if self.elementManager.GetNumberofPenta6Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSPenta6(self.id, startNID, startEID)
        if self.elementManager.GetNumberofTetra4Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSTetra4(self.id, startNID, startEID)
        if self.elementManager.GetNumberofTetra10Elements() >0:
            abaqusString += self.elementManager.WritetoABAQUSTetra10(self.id, startNID, startEID)
        return abaqusString
    
    '''def WritetoABAQUSStreamElements(self, stream, startID, startEID):
        self.WritetoABAQUSStreamSolidElements(stream, startID, startEID)
        self.WritetoABAQUSStreamShellElements(stream, startID, startEID)'''
        
    def ImportMSHFile(self, fileName, dim = 3):
        mshFilePath = os.path.join(self.path, fileName)
        self.mshImporter.import_msh_file(mshFilePath)
        self.mshImporter.UpdateManager(0,0,dim)
        
    def GenerateTetraMeshfromShapes(self, shapes, meshSizeMin, meshSizeMax, dim = 3):
        for sid in shapes:
            shape = shapes[sid]
            self.GenerateTetraMeshfromShape(shape, meshSizeMin, meshSizeMax, dim)

    def GenerateTetraMeshfromShape(self, shape, meshSizeMin, meshSizeMax, dim = 3):
        inputFilePath = self.path
        curdir = inputFilePath
        inputFilePath = os.path.join(curdir, self.tempBrepFileName)
        breptools_Write(shape, inputFilePath)
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;

        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        """
        geoFilePath = os.path.join(curdir, self.tempGeoFileName)
        gmsh_geo_file = open(geoFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        
        gmshFilePath = os.path.join(curdir, self.tempMshFileName)
        
        command = self.gmshPath + "  -setnumber General.Verbosity 0  \"" + geoFilePath + "\" -" + str(dim) + " -algo " + self.meshAlgoOption + " -o \"" + gmshFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)
        if gmsh_success == 0 and os.path.isfile(gmshFilePath):
            
            self.mshImporter.import_msh_file(gmshFilePath)
            self.mshImporter.UpdateManager(0,0,dim)
        
        if os.path.isfile(inputFilePath):
            os.remove(inputFilePath)
        if os.path.isfile(geoFilePath):
            os.remove(geoFilePath)
        if os.path.isfile(gmshFilePath):
            os.remove(gmshFilePath)                           
    
    def quad_to_triangles(quad):
        return [quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]    
    
    def ray_intersects_triangle(self,orig, dir, v0, v1, v2, epsilon = 1e-8):
        edge1 = v1 - v0
        edge2 = v2 - v0
        h = np.cross(dir, edge2)
        a = np.dot(edge1, h)
        if a > -epsilon and a < epsilon:
            return False
        f = 1.0 / a
        s = orig - v0
        u = f * np.dot(s, h)
        if u < 0.0 or u > 1.0:
            return False
        q = np.cross(s, edge1)
        v = f * np.dot(dir, q)
        if v < 0.0 or u + v > 1.0:
            return False
        t = f * np.dot(edge2, q)
        if t > epsilon:
            return True
        else:
            return False
    def is_point_inside_polyhedron(self, point, poly_faces, exclude_face=None):
        count = 0 
        ray_dir = np.random.rand(3)
        ray_dir /= np.linalg.norm(ray_dir)  # Normalize the ray direction
        

        for face in poly_faces:
            tris = []
            if len(face) == 3:
                tris.append(face)
            elif len(face) == 4:
                tris.extend(self.quad_to_triangles(face))
            for tri in tris:
                if exclude_face is not None and set(map(tuple, tri)) == set(map(tuple, exclude_face)):
                    continue
                if self.ray_intersects_triangle(point, ray_dir, *tri):
                    count += 1
        return count % 2 == 1  # Odd count means inside, even means outside 
    
    def DistancefromPoints(self, points = []):
        node_segments = self.elementManager.GetExternalNodeCoordinates()
        distanceList = []
        for point in points:
            point = np.array(point)
            
            for nodesegment in node_segments:
                planePt1 = nodesegment[0]
                planePt2 = nodesegment[1]
                planePt3 = nodesegment[2]
                # calculate distance point from plane from three points
                v1 = planePt2 - planePt1
                v2 = planePt3 - planePt1
                normal = np.cross(v1, v2)
                normal = normal / np.linalg.norm(normal)
                d = np.dot(normal, planePt1)
                distance = np.abs(np.dot(normal, point) - d) / np.linalg.norm(normal)
                distanceList.append(distance)
                #print("Distance from point to plane: ", distance)
                #print("Plane normal: ", normal)
                #print("Plane point: ", planePt1)
                #print("Point: ", point)
                #print("Distance: ", distance)
        return distanceList                
    
    def CheckPointsInsidePart(self, points = []):
        
        node_segments = self.elementManager.GetExternalNodeCoordinates()
        
        locationList = [] 
        for point in points:
            point = np.array(point)
            inside = self.is_point_inside_polyhedron(point, node_segments)
            if not inside:
                locationList.append(False)
            else:
                locationList.append(True)
        return locationList
    
    def CheckIntersectionandT(self, v0, a, v1, v2, v3):
        d1 = v2 - v1 
        d2 = v3 - v1
        rhs = v0 - v1
        a = np.array(a)
        
        M = np.column_stack((d1, d2, -a))
        try:
            sol = np.linalg.solve(M, rhs)
            u, v, t = sol
                
            inside = (u >=0) and (v >= 0) and (u + v <= 1)
            return inside, t
        except np.linalg.LinAlgError:
            return False, None
        
            
    def GetRayDistance(self, point, rayVector):
        node_segments = self.elementManager.GetExternalNodeCoordinates() 
        globalisInside = False 
        globalt = 0.0
        for nodesegment in node_segments:
            planePt1 = nodesegment[0]
            planePt2 = nodesegment[1]
            planePt3 = nodesegment[2]
            
            isInside, t = self.CheckIntersectionandT(point, rayVector, planePt1, planePt2, planePt3)
            if isInside:
                globalisInside = True
                globalt = t
                break
        
        if globalisInside:
            return globalt
        else:
            return None
        
    def CheckinsideValidArea(self, mask, xlim, ylim, plane = "XY"):
        # mask는 2D numpy array, xlim과 ylim은 각각 x축과 y축의 범위
        # plane은 "XY", "XZ", "YZ" 중 하나로 설정
        # mask의 값이 1인 부분이 유효한 영역으로 간주
        # mask의 값이 0인 부분이 하나라도 있으면 False 반환
        # mask의 값이 1인 부분이 모두 유효한 영역에 포함되면 True 반환
        
        nodes = self.elementManager.GetElementNodes()
        H, W = mask.shape
        node_mask = np.zeros_like(mask, dtype=bool)
        if plane == "XY":
            for nid in nodes:
                x = nodes[nid].x
                y = nodes[nid].y                
                xi = int((x - xlim[0]) / (xlim[1] - xlim[0]) * W)
                yi = int((y - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= xi < W and 0 <= yi < H:
                    node_mask[yi, xi] = True
        elif plane == "XZ":
            for nid in nodes:
                x = nodes[nid].x
                z = nodes[nid].z                
                xi = int((x - xlim[0]) / (xlim[1] - xlim[0]) * W)
                zi = int((z - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= xi < W and 0 <= zi < H:
                    node_mask[zi, xi] = True                    
        elif plane == "YZ":
            for nid in nodes:
                y = nodes[nid].y
                z = nodes[nid].z                
                yi = int((y - xlim[0]) / (xlim[1] - xlim[0]) * W)
                zi = int((z - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= yi < W and 0 <= zi < H:
                    node_mask[zi, yi] = True
        
        for i in range(H):
            for j in range(W):
                if node_mask[i][j] == True and mask[i][j] == 0:
                    return False
                
        return True
        
    def FastMaskDilationfromNodes(self, mask, xlim, ylim, dilation=1, plane = "XY", mode = "include"):
        nodes = self.elementManager.GetElementNodes()
        H, W = mask.shape
        node_mask = np.zeros_like(mask, dtype=bool)
        if plane == "XY":
            for nid in nodes:
                x = nodes[nid].x
                y = nodes[nid].y                
                xi = int((x - xlim[0]) / (xlim[1] - xlim[0]) * W)
                yi = int((y - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= xi < W and 0 <= yi < H:
                    node_mask[yi, xi] = True
        elif plane == "XZ":
            for nid in nodes:
                x = nodes[nid].x
                z = nodes[nid].z                
                xi = int((x - xlim[0]) / (xlim[1] - xlim[0]) * W)
                zi = int((z - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= xi < W and 0 <= zi < H:
                    node_mask[zi, xi] = True
        elif plane == "YZ":
            for nid in nodes:
                y = nodes[nid].y
                z = nodes[nid].z                
                yi = int((y - xlim[0]) / (xlim[1] - xlim[0]) * W)
                zi = int((z - ylim[0]) / (ylim[1] - ylim[0]) * H)
                if 0 <= yi < W and 0 <= zi < H:
                    node_mask[zi, yi] = True

        # dilation: 노드가 영향을 미치는 영역
        structure = np.ones((2 * dilation + 1, 2 * dilation + 1), dtype=bool)
        dilated = binary_dilation(node_mask, structure=structure)

        if mode == "include":
            # 무조건 영향을 받은 부분은 1로 설정
            modified_mask = mask.copy()
            modified_mask[dilated] = 1
            return modified_mask

        elif mode == "exclude":
            # 기존 값이 1인 곳만 대상으로, 노드 근처인 곳만 0으로 덮어씀
            modified_mask = mask.copy()
            affected = dilated & (mask == 1)
            modified_mask[affected] = 0
            return modified_mask

        else:
            raise ValueError("mode must be 'include' or 'exclude'")
                
          
        

class KooPartComposite(KooPart):
    def __init__(self, nodeManager = None, elementManager = None, nodeSetManager = None, contact = False, tshell = False):
        super(KooPartComposite, self).__init__(nodeManager, elementManager, None, None, nodeSetManager)        
        self.elform = -16
        self.shrf = 0
        self.nloc = 0
        self.marea = 0
        self.hgid = 0
        self.adpopt = 0
        self.thshel = 0
        self.partType = "PartComposite"
        self.midi = []
        self.thicki = []
        self.bi = []
        self.tmidi = []
        self.plyidi = []
        self.shrfaci = []
        self.contact = contact
        self.tshell = tshell 
    
    def SetTShellMode(self, tshell = True):
        self.tshell = tshell

    def SetPartCompositeProperty(self, id, name, elform, shrf, nloc, marea, hgid, adpopt, thshel):
        self.id = id
        self.name = name
        self.elform = elform
        self.shrf = shrf
        self.nloc = nloc
        self.marea = marea
        self.hgid = hgid
        self.adpopt = adpopt
        self.thshel = thshel

    def AddLayer(self, midi, thicki, bi="", tmidi="", plyidi="", shrfaci=""):
        self.midi.append(midi)
        self.thicki.append(thicki)
        
        self.bi.append(bi)
        self.tmidi.append(tmidi)
        if plyidi !="":
            self.plyidi.append(plyidi)
        if shrfaci !="":
            self.shrfaci.append(shrfaci)

    def SetLaminates(self, midiList,thickiList,biList = [],tmidiList = [], plyidiList = [], shrfaciList = []):
        self.midi = midiList
        self.thicki = thickiList
        self.bi = biList        
        if len(biList) == 0:
            for i in range(len(midiList)):
                self.bi.append("0.0")
        self.tmidi = tmidiList
        if len(tmidiList) == 0:
            for i in range(len(midiList)):
                self.tmidi.append("")

        
        self.plyidi = plyidiList
        self.shrfaci = shrfaciList
              
    def GetTensileModulus(self, materialManager : KooMaterialManager):
        totalThickness = 0.0 
        sumE = 0.0
        for i in range(len(self.midi)):
            mid = self.midi[i]
            mat = materialManager.GetMaterialbyID(mid)
            thickness = self.thicki[i]
            totalThickness += thickness
            sumE += mat.GetE() * thickness            
        if totalThickness > 0:
            E = sumE / totalThickness
        else:
            E = 0
        return E
    
    def GetAveragePoissionRatio(self, materialManager : KooMaterialManager):
        totalThickness = 0.0 
        sumPR = 0.0
        for i in range(len(self.midi)):
            mid = self.midi[i]
            mat = materialManager.GetMaterialbyID(mid)
            thickness = self.thicki[i]
            totalThickness += thickness
            sumPR += mat.GetNu() * thickness
        if totalThickness > 0:
            PR = sumPR / totalThickness
        else:
            PR = 0
        return PR
            
    def GetAverageDensity(self, materialManager : KooMaterialManager):
        totalThickness = 0.0 
        sumDensity = 0.0
        for i in range(len(self.midi)):
            mid = self.midi[i]
            mat = materialManager.GetMaterialbyID(mid)
            thickness = self.thicki[i]
            totalThickness += thickness
            sumDensity += mat.GetDensity() * thickness
        if totalThickness > 0:
            density = sumDensity / totalThickness
        else:
            density = 0
        return density

    def GetTotalThickness(self):
        totalThickness = 0.0
        for i in range(len(self.thicki)):
            totalThickness += self.thicki[i]
        return totalThickness
    
    def WritetoDynaPart(self, startPID = 0):
        curString = "*PART_COMPOSITE"
        if self.tshell == True:
            curString += "_TSHELL"
        if len(self.plyidi) > 0: 
            curString += "_LONG"
        curString += "\n"
        curString += f"{self.name}\n"        
        
        if self.tshell == False:
            curString += "$$     PID    ELFORM      SHRF      NLOC     MAREA      HGID    ADPOPT    THSHEL\n"
            formatString = f"{str(self.id + startPID):>10}{str(self.elform):>10}{str(self.shrf):>10}{str(self.nloc):>10}{str(self.marea):>10}{str(self.hgid):>10}{str(self.adpopt):>10}{str(self.thshel):>10}\n"
        else:
            curString += "$$     PID    ELFORM      SHRF                          HGID              THSHEL\n"
            empty = ""
            formatString = f"{str(self.id + startPID):>10}{str(self.elform):>10}{str(self.shrf):>10}{empty:>10}{empty:>10}{str(self.hgid):>10}{empty:>10}{str(self.thshel):>10}\n"
        curString += formatString        
        if len(self.plyidi) > 0: 
            curString += "$$    MIDI    THICKI        BI     TMIDI    PLYIDI   SHRFACI\n"
            for i in range(len(self.midi)):
                formatString = f"{str(self.midi[i]):>10}{str(self.thicki[i]):>10}{str(self.bi[i]):>10}{str(self.tmidi[i]):>10}{str(self.plyidi[i]):>10}{str(self.shrfaci[i]):>10}\n"
                curString += formatString        
        else:
            curString += "$$    MIDi    THICKi        Bi     TMIDi    MIDi+1  THICKi+1      Bi+1   TMIDi+1\n"
            for i in range(len(self.midi)):
                formatString = f"{str(self.midi[i]):>10}{str(self.thicki[i]):>10}{str(self.bi[i]):>10}{str(self.tmidi[i]):>10}"                
                curString += formatString
                if i % 2 == 1 or i == len(self.midi) - 1:
                    curString += "\n"                    

        return curString
    
    def WriteStreamDynaPart(self, stream, startPID = 0):
        stream.write("*PART_COMPOSITE")
        if self.tshell == True:
            stream.write("_TSHELL")
        if len(self.plyidi) > 0: 
            stream.write("_LONG")
        stream.write("\n")
        stream.write(f"{self.name}\n")
        if self.tshell == False:
            stream.write("$$     PID    ELFORM      SHRF      NLOC     MAREA      HGID    ADPOPT    THSHEL\n")
            formatString = f"{str(self.id + startPID):>10}{str(self.elform):>10}{str(self.shrf):>10}{str(self.nloc):>10}{str(self.marea):>10}{str(self.hgid):>10}{str(self.adpopt):>10}{str(self.thshel):>10}\n"
            stream.write(formatString)
        else:
            stream.write("$$     PID    ELFORM      SHRF                          HGID              THSHEL\n")
            empty = ""
            formatString = f"{str(self.id + startPID):>10}{str(self.elform):>10}{str(self.shrf):>10}{empty:>10}{empty:>10}{str(self.hgid):>10}{empty:>10}{str(self.thshel):>10}\n"
            stream.write(formatString)
        if len(self.plyidi) > 0:
            stream.write("$$    MIDI    THICKI        BI     TMIDI    PLYIDI   SHRFACI\n")
            for i in range(len(self.midi)):
                formatString = f"{str(self.midi[i]):>10}{self.thicki[i]:>10.3e}{str(self.bi[i]):>10}{str(self.tmidi[i]):>10}{str(self.plyidi[i]):>10}{str(self.shrfaci[i]):>10}\n"                                
                stream.write(formatString)
        else:
            stream.write("$$    MIDi    THICKi        Bi     TMIDi    MIDi+1  THICKi+1      Bi+1   TMIDi+1\n")
            for i in range(len(self.midi)):
                formatString = f"{str(self.midi[i]):>10}{self.thicki[i]:>10.3e}{str(self.bi[i]):>10}{str(self.tmidi[i]):>10}"                
                stream.write(formatString)
                if i % 2 == 1 or i == len(self.midi) - 1:
                    stream.write("\n")
    
    def WritetoAnsysAPDLShellElements(self, startNID, startEID):        
        self.section : KooSectionShell = self.section
        ansysString = "" 
        if self.elementManager.GetNumberofLinearFaceElements() >0:
            
            ansysString += "ET,{pid},SHELL181\n".format(pid=self.id)
            #ansysString += "KEYOPT,8,1\n"
            ansysString += "sectype,{sid}, SHELL,, SECTION_{sid}\n".format(sid = self.secid)
            for i in range(len(self.midi)):
                ansysString += "secdata,{thick},{mid},{bi},3\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])
            ansysString += "secoffset,MID\n"
            ansysString += "seccontrol,,,,,,,\n"                            
            ansysString += "type,{pid}\n".format(pid=self.id)            
            #ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += "secnum,{pid}\n".format(pid=self.id)            
            ansysString += self.elementManager.WritetoAnsysAPDLFaceLinear(self.id, startNID, startEID)
        if self.elementManager.GetNumberofQuadraticFaceElements() >0:
            ansysString += "ET,{pid},SHELL281\n".format(pid=self.id)
            #ansysString += "KEYOPT,8,1\n"
            ansysString += "sectype,{sid}, SHELL,, SECTION_{sid}\n".format(sid = self.secid)
            for i in range(len(self.midi)):
                ansysString += "secdata,{thick},{mid},{bi},3\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])
            ansysString += "secoffset,MID\n"
            ansysString += "seccontrol,,,,,,,\n"                            
            ansysString += "type,{pid}\n".format(pid=self.id)
            #ansysString += "mat,{mid}\n".format(mid = mid)
            ansysString += "secnum,{pid}\n".format(pid=self.id)            
            ansysString += self.elementManager.WritetoAnsysAPDLFaceQuadratic(self.id, startNID, startEID)
        return ansysString

    def WritetoABAQUSShellElements(self, startNID, startEID):        
        abaqusString = ""   
        if self.elementManager.GetNumberofTri3Elements() > 0:
            abaqusString += self.elementManager.WritetoABAQUSTri3(self.id, startNID, startEID)
            elesetName = "PART_Tri3_{pid}".format(pid = self.id)
            abaqusString += "*Orientation, name=Ori_{eleset}\n".format(eleset = elesetName)

            abaqusString += "*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName)
            for i in range(len(self.midi)):                
                abaqusString += "{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])                
        if self.elementManager.GetNumberofTri6Elements() > 0:
            abaqusString += self.elementManager.WritetoABAQUSTri6(self.id, startNID, startEID)
            elesetName = "PART_Tri6_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName)
            for i in range(len(self.midi)):                
                abaqusString += "{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])
        if self.elementManager.GetNumberofQuad4Elements() > 0:
            abaqusString += self.elementManager.WritetoABAQUSQuad4(self.id, startNID, startEID)
            elesetName = "PART_Quad4_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName)
            for i in range(len(self.midi)):                
                abaqusString += "{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])
        if self.elementManager.GetNumberofQuad8Elements() > 0:
            abaqusString += self.elementManager.WritetoABAQUSQuad8(self.id, startNID, startEID)
            elesetName = "PART_Quad8_{pid}".format(pid = self.id)
            abaqusString += "*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName)
            for i in range(len(self.midi)):                
                abaqusString += "{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i])
        self.section : KooSectionShell = self.section        
        return abaqusString
    
    def WritetoABAQUSStreamShellElements(self, stream, startNID, startEID, materialManager : KooMaterialManager = None):
        if materialManager is not None:
            pass 
        
        self.WritetoABAQUSStreamShellElements(stream, startNID, startEID)
    
    def WritetoABAQUSStreamShellElements(self, stream, startNID, startEID):        
        if self.elementManager.GetNumberofTri3Elements() > 0:
            self.elementManager.WritetoABAQUSStreamTri3(stream,self.id, startNID, startEID)
            elesetName = "PART_Tri3_{pid}".format(pid = self.id)
            stream.write("*Orientation, name=Ori_{eleset}\n".format(eleset = elesetName))
            stream.write("*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName))
            for i in range(len(self.midi)):                
                stream.write("{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i]))
        if self.elementManager.GetNumberofTri6Elements() > 0:
            self.elementManager.WritetoABAQUSStreamTri6(stream,self.id, startNID, startEID)
            elesetName = "PART_Tri6_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName))
            for i in range(len(self.midi)):                
                stream.write("{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i]))
        if self.elementManager.GetNumberofQuad4Elements() > 0:
            self.elementManager.WritetoABAQUSStreamQuad4(stream,self.id, startNID, startEID)
            elesetName = "PART_Quad4_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName))
            for i in range(len(self.midi)):                
                stream.write("{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i]))
        if self.elementManager.GetNumberofQuad8Elements() > 0:
            self.elementManager.WritetoABAQUSStreamQuad8(stream,self.id, startNID, startEID)
            elesetName = "PART_Quad8_{pid}".format(pid = self.id)
            stream.write("*Shell Section, elset={eleset}, composite, orientation=Ori_{eleset}, layup=CompositeLayup_{eleset}\n".format(eleset = elesetName))
            for i in range(len(self.midi)):                
                stream.write("{thick},3,{mid},{bi},Ply{mid}\n".format(thick = self.thicki[i], mid = self.midi[i], bi = self.bi[i]))
    
import trimesh
    
class KooSTLPart(KooPart):
    def __init__(self, nodeManager = None, elementManager = None, material = None, section = None, nodeSetManager = None, stlFilePath = ""):
        super(KooSTLPart, self).__init__(nodeManager, elementManager, material, section, nodeSetManager)                
        self.partType = "PartSTL"
        
        self.vertices = None 
        self.faces = None
        self.stl_file_path = stlFilePath
        if stlFilePath != "":
            self.name = os.path.basename(stlFilePath)                        
        if len(self.nodeManager.nodes) != 0 and len(self.elementManager.elements) != 0:
            self.ExtractSurfaceMesh()
            
        from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH
        self.meshManager = KooMeshManagerGMSH(self.nodeManager, self.elementManager)
        self.meshManager.SetName("STLMeshManager")
        self.meshManager.SetPath(os.getcwd())
        
    
    def ImportSTL(self, stlFilePath):
        self.stl_file_path = stlFilePath
        
        if not os.path.exists(stlFilePath):
            raise FileNotFoundError(f"STL file not found: {stlFilePath}")
        
        mesh = trimesh.load_mesh(stlFilePath)
        self.vertices = mesh.vertices
        self.faces = mesh.faces
    
    def ExportSTL(self, stlFilePath = "", subStr = "", scale = 1.0):
        
        stlOutPath = stlFilePath
        if ".stl" in stlOutPath:
            stlOutPath = stlOutPath.replace(".stl", subStr + ".stl")
            
        if self.vertices is None or self.faces is None:
            raise ValueError("No mesh data available. Please import an STL file first.")
        
        vertices = self.vertices * scale
       
        mesh = trimesh.Trimesh(vertices=vertices, faces=self.faces)
        mesh.export(stlOutPath)#, file_type='stl')
        self.stl_file_path = stlOutPath
        
        return True                        
   
    def ExtractSurfaceMesh(self):
        nodes = self.nodeManager.nodes        
        elements = self.elementManager.elements
        
        nodekeytoid = {}
        nodeidtokey = {}
        ith = 0

        
        for nodeid in nodes:
            nodekeytoid[ith] = nodeid
            nodeidtokey[nodeid] = ith
            ith = ith + 1
            
            
        # id 순서대로 [x, y, z] 추출
        sorted_ids = sorted(nodekeytoid.keys())
        vertices = np.array([[nodes[nodekeytoid[i]].x, nodes[nodekeytoid[i]].y, nodes[nodekeytoid[i]].z] for i in sorted_ids])
                
            
        # faces 추출        
        self.boundaryNodes = {}
        boundary = self.elementManager.GetExternalTriBoundary()
        boundarywithkey = {}
        for i in range(len(boundary)):
            face = boundary[i]
            facekey = []
            for j in range(len(face)):
                facekey.append(nodeidtokey[face[j]])
                self.boundaryNodes[face[j]] = nodes[face[j]]
            facekey = tuple(facekey)
            boundarywithkey[i] = facekey
                           
                           
        # dict values to array        
        faces = np.array(list(boundarywithkey.values()))

        self.faces = faces
        self.vertices = vertices
        self.verticeskeytonodeid = nodekeytoid
        
        print("Extracted surface mesh from 3D part")
    
    def GenerateSolidMeshfromSurfaceMesh(self, meshSizeMin, meshSizeMax):        
        self.meshManager.mesh_shape_from_stl_without_surface_nodes(self.stl_file_path, self.boundaryNodes, self, meshSizeMin, meshSizeMax)
        
            
    
class PartSet:
    def __init__(self, psid, da1 = 0.0, da2 = 0.0, da3 = 0.0, da4 = 0.0, solver="MECH", pids = None, name = ""):
        self.psid = psid
        self.da1 = da1
        self.da2 = da2
        self.da3 = da3
        self.da4 = da4
        self.solver = solver
        self.pids = pids if pids is not None else []
        self.name = name 
    
    def AddPart(self, pid):
        self.pids.append(pid)
        
    def WritetoDynaKeyword(self):
        if len(self.name) == 0 or self.name == "":
            keyword = ""
            keyword += "*SET_PART_LIST\n"
            keyword += format(self.psid,">10")
            keyword += format(self.da1,">10") 
            keyword += format(self.da2,">10")
            keyword += format(self.da3,">10")
            keyword += format(self.da4,">10")
            keyword += format(self.solver,">10")
            keyword += "\n"
            i = 0 
            for pid in self.pids:
                keyword += format(pid,">10")
                i = i + 1
                if i % 8 == 0:
                    keyword += "\n"
            if i % 8 != 0:
                keyword += "\n"
        else:
            keyword = ""
            keyword += "*SET_PART_LIST_TITLE\n"
            
            keyword += format(self.name,">80")
            keyword += "\n"
            keyword += format(self.psid,">10")
            keyword += format(self.da1,">10")
            keyword += format(self.da2,">10")
            keyword += format(self.da3,">10")
            keyword += format(self.da4,">10")
            keyword += format(self.solver,">10")
            keyword += "\n"
            i = 0 
            for pid in self.pids:
                keyword += format(pid,">10")
                i = i + 1
                if i % 8 == 0:
                    keyword += "\n"
            if i % 8 != 0:
                keyword += "\n"
            
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        if len(self.name) == 0 or self.name == "":
            stream.write("*SET_PART_LIST\n")
            stream.write(format(self.psid,">10"))
            stream.write(format(self.da1,">10")) 
            stream.write(format(self.da2,">10"))
            stream.write(format(self.da3,">10"))
            stream.write(format(self.da4,">10"))
            stream.write(format(self.solver,">10"))
            stream.write("\n")
            i = 0 
            for pid in self.pids:
                stream.write(format(pid,">10"))
                i = i + 1
                if i % 8 == 0:
                    stream.write("\n")
            if i % 8 != 0:
                stream.write("\n")
        else:
            stream.write("*SET_PART_LIST_TITLE\n")            
            stream.write(format(self.name,">80"))
            stream.write("\n")
            stream.write(format(self.psid,">10"))
            stream.write(format(self.da1,">10"))
            stream.write(format(self.da2,">10"))
            stream.write(format(self.da3,">10"))
            stream.write(format(self.da4,">10"))
            stream.write(format(self.solver,">10"))
            stream.write("\n")
            i = 0 
            for pid in self.pids:
                stream.write(format(pid,">10"))
                i = i + 1
                if i % 8 == 0:
                    stream.write("\n")
            if i % 8 != 0:
                stream.write("\n")
        

class KooPartManager():
    
    def __init__(self, nodeManager = None, elementManager = None):
        self.maxID = 0
        self.parts = {}
        self.partsRigid = {}

        self.maxSID = 0
        self.partSets = {}

        self.constrainedParts = {}

        # === IGA 관련 속성 ===
        self.igaParts = {}           # {iga_pid: KooIGAPart}
        self.igaIncludes = []        # ['file1.k', 'file2.k', ...]
        self.maxIGAID = 0            # IGA ID 자동 할당용

        if nodeManager is None:
            self.nodeManager : NodeManager = NodeManager()
        else:
            self.nodeManager = nodeManager
        if elementManager is None:
            self.elementManager : ElementManager = ElementManager(self.nodeManager)
        else:
            self.elementManager = elementManager
            
    def UpdatePartGraph(self):
        pidtonamegraph = {} 
        for key, part in self.parts.items():
            pid = part.id
            name = part.name.strip()
            pidtonamegraph[pid] = name
        
        return pidtonamegraph           
                  
    def OffsetID(self, offsetPID, offsetPSID, offsetEID, offsetNID=-1):
        for key in self.parts:
            part = self.parts[key]
            part.id += offsetPID            
        for key in self.partsRigid:
            partRigid = self.partsRigid[key]
            partRigid.id += offsetPID
        for key in self.constrainedParts:
            constrainedPart = self.constrainedParts[key]
            constrainedPart.id += offsetPID
        self.maxID += offsetPID
        self.maxSID += offsetPSID
        for key in self.partSets:
            partSet = self.partSets[key]
            partSet.id += offsetPSID
        if self.nodeManager is not None:
            if offsetNID >0:
                self.nodeManager.OffsetID(offsetNID)
        if self.elementManager is not None:
            self.elementManager.OffsetID(offsetEID)

    def OverwritefromPartManager(self, partManager : KooPartManager):
        self.maxID = max(self.maxID, partManager.maxID)
        for key, value in partManager.parts.items():
            self.parts[key] = value
        for key, value in partManager.partsRigid.items():
            self.partsRigid[key] = value
        self.maxSID = max(self.maxSID, partManager.maxSID)
        for key, value in partManager.partSets.items():
            self.partSets[key] = value
        
        for key, value in partManager.constrainedParts.items():
            self.constrainedParts[key] = value
        
        if partManager.nodeManager is not None:
            self.nodeManager.OverwritefromNodeManager(partManager.nodeManager)
        if partManager.elementManager is not None:
            self.elementManager.OverwritefromElementManager(partManager.elementManager)

    def CreatePartSet(self, da1 = 0.0, da2 = 0.0, da3 = 0.0, da4 = 0.0, solver="MECH", pids = None, name=""):
        self.maxSID = self.maxSID + 1
        if name == "":
            name = "PartSet_{psid}".format(psid = self.maxSID)
        partSet = PartSet(self.maxSID, da1, da2, da3, da4, solver, pids, name)
        self.partSets[self.maxSID] = partSet
        return partSet
        
    def CreatePartSetwithID(self, psid, da1 = 0.0, da2 = 0.0, da3 = 0.0, da4 = 0.0, solver="MECH", pids = None, name = ""):
        self.maxSID = max(self.maxSID, psid)
        if name == "":
            name = "PartSet_{psid}".format(psid = psid)
        partSet = PartSet(psid, da1, da2, da3, da4, solver, pids, name)
        self.partSets[psid] = partSet
        return partSet
    

    def CreateConstrainedNodalRigidBody(self, name, cid, pnode, iprt, drflag, rrflag, nodeSet):
        self.maxID = self.maxID + 1
        constrainedPart = KooConstrainedNodalRigidBodyPart(self.maxID, name)
        constrainedPart.CreateConstrainedOptionswithNodeSet(cid, nodeSet, pnode, iprt, drflag, rrflag)                
        self.constrainedParts[self.maxID] = constrainedPart
        return constrainedPart

    def CreatePointElement(self, node, mass):        
        maxeid = self.FindMaxEID()
        self.maxID = max(self.maxID, maxeid) + 1
        return self.elementManager.AddPointElement(self.maxID, node, mass)


    def FindMaxEID(self):
        maxEID = 0
        for part in self.parts.values():
            elemManager : ElementManager = part.elementManager            
            maxEID = max(maxEID, elemManager.maxID)
        maxEID = max(maxEID, self.elementManager.maxID)
        return maxEID

    def FindElementfromID(self, id):
        for part in self.parts.values():
            element : Element = part.elementManager.FindElementfromID(id)
            if element is not None:
                return element
        return None
    
    def AddSolidPart(self, nodeManager : NodeManager, elementManager : ElementManager, section : KooSection, material : KooMaterial):
        self.maxID = self.maxID + 1
        
        newPart = KooPart(nodeManager, elementManager)        
        newPart.SetID(self.maxID)
        newPart.SetSection(section)
        newPart.SetMaterial(material)
        self.AddPart(newPart)
        return newPart

    def CreatePart(self, id, name = "", secid = 0, mid = 0, eosid = 0, hgid = 0, grav = 0, adpopt = 0, tmid = 0, nodeManager = None, elementManager = None):
        if id in self.parts:
            print("Part ID already exists")
            return None
        else:
            newPart = KooPart(nodeManager, elementManager)
            newPart.SetPartProperty(id, name, secid, mid, eosid, hgid, grav, adpopt, tmid)
            self.AddPart(newPart)
            self.maxID = max(self.maxID, id)
            return newPart
    
    def CreatePartfromKooPart(self, part : KooPart):
        self.maxID = self.maxID + 1
        #part = KooPart(part.nodeManager, part.elementManager)        
        part.SetPartProperty(self.maxID, part.name, part.secid, part.mid, part.eosid, part.hgid, part.grav, part.adpopt, part.tmid)
        self.AddPart(part)
        return part
    
    def CreateSTLPartfromKooPart(self, part : KooPart):
        self.maxID = self.maxID + 1 
        
        part = KooSTLPart(part.nodeManager, part.elementManager, part.material, part.section, part.nodeSetManager)
        part.SetPartProperty(self.maxID, part.name, part.secid, part.mid, part.eosid, part.hgid, part.grav, part.adpopt, part.tmid)
        self.AddPart(part)
        return part

    def AddPartfromKooPart(self, id, part : KooPart):
        if id in self.parts:
            print("Part ID already exists")
            return None
        else:
            part.SetID(id)
            self.AddPart(part)

        return part
    
    def AddSTLPartfromKooPart(self, id):
        if id in self.parts:
            part = self.parts[id]
            newPart = KooSTLPart(part.nodeManager, part.elementManager, part.material, part.section, part.nodeSetManager)
            newPart.SetPartProperty(id, part.name, part.secid, part.mid, part.eosid, part.hgid, part.grav, part.adpopt, part.tmid)
            self.AddPart(newPart)
            return newPart
        else:
            print("Part ID does not exist")
            return None
    
    def AddIndependentNode(self, x,y,z):
        maxnid = 0
        for part in self.parts.values():
            part : KooPart = part
            maxnid = max(maxnid, part.nodeManager.maxID)
        maxnid = max(maxnid, self.nodeManager.maxID)
        maxnid = maxnid + 1
        node : Node = self.nodeManager.AddNodewithID(maxnid,x,y,z)
        for part in self.parts.values():
            part : KooPart = part
            part.nodeManager.SetMaxID(maxnid)
        
        return node
        
    def CreatePartComposite(self, id, name = "", elform=0, shrf=0, nloc=0, marea=0, hgid=0, adpopt=0, thshel=0, nodeManager = None, elementManager = None):
        if id in self.parts:
            print("Part ID already exists")
            return None
        else:
            newPart = KooPartComposite(nodeManager, elementManager)
            newPart.SetPartCompositeProperty(id,name, elform, shrf, nloc, marea, hgid, adpopt, thshel)
            self.AddPart(newPart)
            return newPart

    
    def AddPart(self, part : KooPart):
        if part.id in self.parts:
            self.parts[part.id] = part
        else:
            self.parts[part.id] = part
            self.maxID = max(self.maxID, part.id)
            return part
    
    def RemovePart(self, id):
        if id in self.parts:
            del self.parts[id]
        else:
            print("Part ID does not exist")        
            
    def RemoveConstrainedPart(self, id):
        if id in self.constrainedParts:
            del self.constrainedParts[id]
        else:
            print("Part Constrained ID does not exist")            

    def AddMassElementsfromDyna(self, parametersMass, mode = "MASS"):
        # parametersMass = [블록][행][컬럼]  (블록 하나의 *ELEMENT_MASS 아래 여러 행 가능)
        for block in parametersMass:
            for parameters in block:
                if parameters is None or len(parameters) < 4:
                    continue
                try:
                    eid = int(parameters[0])
                    nid = int(parameters[1])
                    mass = float(parameters[2])
                    pid = int(parameters[3])
                except (ValueError, IndexError):
                    continue

                # part lookup: parts / partsRigid / constrainedParts 모두 확인
                target_part = None
                if pid in self.parts:
                    target_part = self.parts[pid]
                elif pid in self.partsRigid:
                    target_part = self.partsRigid[pid]
                elif pid in self.constrainedParts:
                    target_part = self.constrainedParts[pid]

                if target_part is not None and hasattr(target_part, 'elementManager'):
                    if mode == "MASS":
                        node = target_part.nodeManager.FindNodefromID(nid)
                        if node is None:
                            # part에 없으면 글로벌 nodeManager에서 재탐색
                            node = self.nodeManager.FindNodefromID(nid)
                        if node is None:
                            print(f"[WARNING] *ELEMENT_MASS eid={eid} nid={nid} 노드 미발견 — 스킵")
                            continue
                        pe = target_part.elementManager.AddPointElement(eid, node, mass)
                    else:  # MASS_NODE_SET
                        pe = target_part.elementManager.AddPointElement(eid, nid, mass)
                    if pe is not None:
                        pe.pid = pid
                else:
                    # 루트 elementManager 폴백 — 원본 pid 보존 (write 시 pid=0 방지)
                    if mode == "MASS":
                        node = self.nodeManager.FindNodefromID(nid)
                        if node is None:
                            print(f"[WARNING] *ELEMENT_MASS eid={eid} nid={nid} 노드 미발견 — 스킵")
                            continue
                        pe = self.elementManager.AddPointElement(eid, node, mass)
                    else:
                        pe = self.elementManager.AddPointElement(eid, nid, mass)
                    if pe is not None:
                        pe.pid = pid
                
    
    def AddBeamElementsfromDyna(self, parametersBeam):
        for i in range(len(parametersBeam)):
            parameters = parametersBeam[i]
            for j in range(len(parameters)):
                parameter = parameters[j] 
                eid = int(parameter[0])
                pid = int(parameter[1])
                # integer
                try:
                    testValue = int(parameter[4])
                    nids = parameter[2:5]
                except:
                    nids = parameter[2:4]
                    
                # nids to integer list 
                nids = [int(i) for i in nids]
                rt1 = parameter[5]
                rr1 = parameter[6]
                rt2 = parameter[7]
                rr2 = parameter[8]
                local = parameter[9]
                if pid in self.parts:
                    part : KooPart = self.parts[pid]
                    if len(nids)<3 or nids[2] == 0:
                        n1 = part.nodeManager.FindNodefromID(nids[0])
                        n2 = part.nodeManager.FindNodefromID(nids[1])
                        part.AddLineLinearElement(eid, n1, n2, rt1, rr1, rt2, rr2, local)
                    else:
                        n1 = part.nodeManager.FindNodefromID(nids[0])
                        n2 = part.nodeManager.FindNodefromID(nids[1])
                        n3 = part.nodeManager.FindNodefromID(nids[2])

                        part.AddLineQuadraticElement(eid, n1, n2, n3, rt1, rr1, rt2, rr2, local)
                    

    def AddShellElementsfromDyna(self, parametersShell):
        for i in range(len(parametersShell)):
            parameters = parametersShell[i]
            mode = 1
            if len(parameters) > 2:
                length1 = len(parameters[0])
                length2 = len(parameters[1])
                if length1 == length2:
                    mode = 1
                else:
                    mode = 2
                    if len(parameters) > 3:
                        length3 = len(parameters[2])
                        if length1 == length3:
                            mode = 2
                        else:
                            mode = 3 
            else:
                mode = 1
            if mode == 1:
                for j in range(len(parameters)):
                    parameter = parameters[j] 
                    eid = int(parameter[0])
                    pid = int(parameter[1])
                    # integer
                    nids = parameter[2:]
                    # nids to integer list 
                    nids = [int(i) for i in nids]
                    if pid in self.parts:
                        part : KooPart = self.parts[pid]
                        if len(nids) == 3 or nids[3] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            part.AddTriangleLinearElement(eid, n1, n2, n3)
                        elif len(nids) == 4 or nids[4] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            part.AddQuadrangleLinearElement(eid, n1, n2, n3, n4)
                        elif len(nids) == 6 or nids[6] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            part.AddTriangleQuadraticElement(eid, n1, n2, n3, n4, n5, n6)
                        elif len(nids) == 8:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            part.AddQuadrangleQuadraticElement(eid, n1, n2, n3, n4, n5, n6, n7, n8)
            elif mode == 2:
                for i in range(0,len(parameters),2):
                    parameter1 = parameters[i]
                    parameter2 = parameters[i+1]
                    eid = int(parameter1[0])
                    pid = int(parameter1[1])
                    # integer
                    nids = parameter1[2:]
                    # nids to integer list
                    nids = [int(i) for i in nids]
                    # floats
                    thickness = parameter2[0:-1]                    
                    beta = parameter2[4]

                    if pid in self.parts:
                        part : KooPart = self.parts[pid]
                        if len(nids) == 3 or nids[3] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            part.AddTriangleLinearElementThetaBeta(eid, n1, n2, n3, thickness[0], thickness[1], thickness[2], thickness[3], beta)
                        elif len(nids) == 4 or nids[4] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            part.AddQuadrangleLinearElementThetaBeta(eid, n1, n2, n3, n4, thickness[0], thickness[1], thickness[2], thickness[3], beta)
            elif mode == 3:
                for i in range(0,len(parameters),3):
                    parameter1 = parameters[i]
                    parameter2 = parameters[i+1]
                    parameter3 = parameters[i+2]
                    eid = int(parameter1[0])
                    pid = int(parameter1[1])
                    # integer
                    nids = parameter1[2:]
                    # nids to integer list
                    nids = [int(i) for i in nids]
                    # floats
                    thickness = parameter2[0:-1]                    
                    beta = parameter2[4]
                    # parameter3 has 4 theta values
                    theta = parameter3

                    if pid in self.parts:
                        part : KooPart = self.parts[pid]
                        if len(nids) == 6 or nids[6] == 0:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            part.AddTriangleQuadraticElementThetaBeta(eid, n1, n2, n3, n4, n5, n6, theta[0], theta[1], theta[2], theta[3], theta[4], theta[5], theta[6], theta[7], beta)
                        elif len(nids) == 8:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            part.AddQuadrangleQuadraticElementThetaBeta(eid, n1, n2, n3, n4, n5, n6, n7, n8, theta[0], theta[1], theta[2], theta[3], theta[4], theta[5], theta[6], theta[7], beta)

    def AddSolidElementsfromDynaAdvanced(self, parametersSolid):
        for i in range(len(parametersSolid)):
                parameters = parametersSolid[i]
                mode = 1
                if len(parameters) > 2:
                    length1 = len(parameters[0])
                    length2 = len(parameters[1])
                    if length1 == length2:
                        mode = 1
                        if len(parameters) > 3:
                            length3 = len(parameters[2])
                            if length1 == length3:
                                mode = 1
                            else:
                                mode = 3
                    else:
                        mode = 2
                else:
                    mode = 1

                if mode == 1:
                    for j in range(len(parameters)):
                        parameter = parameters[j]
                        eid = int(parameter[0])
                        pid = int(parameter[1])
                        nids = [KooDynaInt(i) for i in parameter[2:]]

                        if pid in self.parts:
                            part = self.parts[pid]
                            if len(nids) == 4 or nids[4] == 0 or nids[4] == nids[3]:
                                nodes = get_nodes(part.nodeManager, nids[:4])
                                part.AddTetrahedronLinearElement(eid, *nodes)
                            elif len(nids) == 6 or nids[6] == 0 or nids[6] == nids[5]:
                                nodes = get_nodes(part.nodeManager, nids[:6])
                                part.AddPentahedronLinearElement(eid, *nodes)
                            elif len(nids) == 8:
                                nodes = get_nodes(part.nodeManager, nids[:8])
                                part.AddHexahedronLinearElement(eid, *nodes)

                elif mode == 2:
                    for i in range(0, len(parameters), 2):
                        parameter1 = parameters[i]
                        parameter2 = parameters[i + 1]
                        eid = int(parameter1[0])
                        pid = int(parameter1[1])
                        nids = [KooDynaInt(i, 0) for i in parameter2]

                        if pid in self.parts:
                            part = self.parts[pid]
                            if len(nids) == 4 or nids[4] == 0 or nids[4] == nids[3]:
                                nodes = get_nodes(part.nodeManager, nids[:4])
                                part.AddTetrahedronLinearElement(eid, *nodes)
                            elif len(nids) == 6 or nids[6] == 0 or nids[6] == nids[5]:
                                nodes = get_nodes(part.nodeManager, nids[:6])
                                part.AddPentahedronLinearElement(eid, *nodes)                                
                            elif len(nids) == 8 or nids[8] == 0 or nids[8] == nids[7]:
                                nodes = get_nodes(part.nodeManager, nids[:8])
                                part.AddHexahedronLinearElement(eid, *nodes)
                            elif len(nids) == 10:
                                nodes = get_nodes(part.nodeManager, nids[:10])
                                part.AddTetrahedronQuadraticElement(eid, *nodes)

                elif mode == 3:
                    for i in range(0, len(parameters), 3):
                        parameter1 = parameters[i]
                        parameter2 = parameters[i + 1]
                        parameter3 = parameters[i + 2]
                        eid = int(parameter1[0])
                        pid = int(parameter1[1])
                        nids = [int(i) for i in parameter2 + parameter3]

                        if pid in self.parts:
                            part = self.parts[pid]
                            if len(nids) == 20:
                                nodes = get_nodes(part.nodeManager, nids[:20])
                                part.AddHexahedronQuadraticElement(eid, *nodes)
                                
                                
    
    def AddSolidElementsfromDyna(self, parametersSolid):
        for i in range(len(parametersSolid)):
            parameters = parametersSolid[i]
            mode = 1
            if len(parameters) > 2:
                length1 = len(parameters[0])
                length2 = len(parameters[1])
                if length1 == length2:
                    mode = 1
                    if len(parameters) > 3:
                        length3 = len(parameters[2])
                        if length1 == length3:
                            mode = 1
                        else:
                            mode = 3
                else:
                    mode = 2
            else:
                mode = 1
            if mode == 1:
                for j in range(len(parameters)):
                    parameter = parameters[j] 
                    eid = int(parameter[0])
                    pid = int(parameter[1])
                    # integer
                    nids = parameter[2:]
                    # nids to integer list 
                    nids = [KooDynaInt(i) for i in nids]
                    if pid in self.parts:
                        part = self.parts[pid]
                        if len(nids) == 4 or nids[4] == 0 or nids[4] == nids[3]:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            part.AddTetrahedronLinearElement(eid, n1, n2, n3, n4)
                        elif len(nids) == 6 or nids[6] == 0 or nids[6] == nids[5]:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            part.AddPentahedronLinearElement(eid, n1, n2, n3, n4, n5, n6)
                        elif len(nids) == 8:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            part.AddHexahedronLinearElement(eid, n1, n2, n3, n4, n5, n6, n7, n8)
            elif mode == 2: 
                ## TODO: Add Solid Element for Quadratic            
                for i in range(0,len(parameters),2):
                    parameter1 = parameters[i]
                    parameter2 = parameters[i+1]
                    eid = int(parameter1[0])
                    if eid == 951:
                        pass
                    pid = int(parameter1[1])
                    # integer
                    nids = parameter2
                    # nids to integer list
                    nids = [KooDynaInt(i,0) for i in nids]
                    if pid in self.parts:
                        part : KooPart = self.parts[pid]
                        if len(nids) == 4 or nids[4] == 0 or nids[4] == nids[3]:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            part.AddTetrahedronLinearElement(eid, n1, n2, n3, n4)
                        elif len(nids) == 6 or nids[6] == 0 or nids[6] == nids[5]:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            part.AddPentahedronLinearElement(eid, n1, n2, n3, n4, n5, n6)
                        elif len(nids) == 8 or nids[8] == 0 or nids[8] == nids[7]:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            part.AddHexahedronLinearElement(eid, n1, n2, n3, n4, n5, n6, n7, n8)                    
                        elif len(nids) == 10:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            n9 = part.nodeManager.FindNodefromID(nids[8])
                            n10 = part.nodeManager.FindNodefromID(nids[9])
                            part.AddTetrahedronQuadraticElement(eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10)
            elif mode == 3:
                for i in range(0,len(parameters),3):
                    parameter1 = parameters[i]
                    parameter2 = parameters[i+1]
                    parameter3 = parameters[i+2]
                    eid = int(parameter1[0])
                    pid = int(parameter1[1])
                    # integer
                    nids1 = parameter2
                    nids2 = parameter3
                    nids = nids1 + nids2                    
                    nids = [int(i) for i in nids]
                    if pid in self.parts:
                        part : KooPart = self.parts[pid]
                        if len(nids) == 20:
                            n1 = part.nodeManager.FindNodefromID(nids[0])
                            n2 = part.nodeManager.FindNodefromID(nids[1])
                            n3 = part.nodeManager.FindNodefromID(nids[2])
                            n4 = part.nodeManager.FindNodefromID(nids[3])
                            n5 = part.nodeManager.FindNodefromID(nids[4])
                            n6 = part.nodeManager.FindNodefromID(nids[5])
                            n7 = part.nodeManager.FindNodefromID(nids[6])
                            n8 = part.nodeManager.FindNodefromID(nids[7])
                            n9 = part.nodeManager.FindNodefromID(nids[8])
                            n10 = part.nodeManager.FindNodefromID(nids[9])
                            n11 = part.nodeManager.FindNodefromID(nids[10])
                            n12 = part.nodeManager.FindNodefromID(nids[11])
                            n13 = part.nodeManager.FindNodefromID(nids[12])
                            n14 = part.nodeManager.FindNodefromID(nids[13])
                            n15 = part.nodeManager.FindNodefromID(nids[14])
                            n16 = part.nodeManager.FindNodefromID(nids[15])
                            n17 = part.nodeManager.FindNodefromID(nids[16])
                            n18 = part.nodeManager.FindNodefromID(nids[17])
                            n19 = part.nodeManager.FindNodefromID(nids[18])
                            n20 = part.nodeManager.FindNodefromID(nids[19])
                            part.AddHexahedronQuadraticElement(eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16, n17, n18, n19, n20)

                pass
            
    def AddPartfromDyna(self, partKeyword):
        if "*PART_COMPOSITE" in partKeyword[0]:
            name = partKeyword[1][0]
            firstLine = partKeyword[2]
            pid = KooDynaInt(firstLine[0])
            elform = KooDynaInt(firstLine[1])
            shrf = KooDynaFloat(firstLine[2])
            nloc = KooDynaFloat(firstLine[3])
            marea = KooDynaFloat(firstLine[4])
            hgid = KooDynaInt(firstLine[5])
            adpopt = KooDynaInt(firstLine[6])
            thshel = KooDynaInt(firstLine[7])
            
                
            if pid in self.parts:
                nodeMan = self.parts[pid].nodeManager
                elemMan = self.parts[pid].elementManager
                self.RemovePart(pid)
            else:
                nodeMan = None
                elemMan = None
            
            part = self.CreatePartComposite(pid, name, elform, shrf, nloc, marea, hgid, adpopt, thshel, nodeMan, elemMan)
            if "_LONG" in partKeyword[0]:
                for k in range(3, len(partKeyword)):
                    midi = KooDynaInt(partKeyword[k][0])
                    thicki = KooDynaFloat(partKeyword[k][1])
                    bi = KooDynaFloat(partKeyword[k][2])
                    tmidi = KooDynaInt(partKeyword[k][3])
                    plyidi = KooDynaInt(partKeyword[k][4])
                    shafaci = KooDynaFloat(partKeyword[k][5])
                    part.AddLayer(midi, thicki, bi, tmidi, plyidi, shafaci)
            else:
                
                for k in range(3, len(partKeyword)):
                    midi = KooDynaInt(partKeyword[k][0])
                    thki = KooDynaFloat(partKeyword[k][1])
                    bi = KooDynaFloat(partKeyword[k][2])
                    midti = KooDynaInt(partKeyword[k][3])
                    midip1 = KooDynaInt(partKeyword[k][4])
                    thkip1 = KooDynaFloat(partKeyword[k][5])
                    bip1 = KooDynaFloat(partKeyword[k][6])
                    midtip1 = KooDynaInt(partKeyword[k][7])
            
                    part.AddLayer(midi,thki,bi,midti)
                    if midip1 != 0 and thkip1 != 0.0:
                        part.AddLayer(midip1,thkip1,bip1,midtip1)
            if "_TSHELL" in partKeyword[0]:
                part.SetTShellMode(True)
            return part
        return None                    
            
    def AddPartSetfromDyna(self, partSetKeyword):
        if partSetKeyword[0] == "*SET_PART" or partSetKeyword[0] == "*SET_PART_LIST":
            optionKeyword = partSetKeyword[1] 
            psid = KooDynaInt(optionKeyword[0])
            da1 = KooDynaFloat(optionKeyword[1])
            da2 = KooDynaFloat(optionKeyword[2])
            da3 = KooDynaFloat(optionKeyword[3])
            da4 = KooDynaFloat(optionKeyword[4])
            solver = KooDynaString(optionKeyword[5],'MECH')
            pids = []
            for i in range(2,len(partSetKeyword)):
                for j in range(len(partSetKeyword[i])):
                    value = KooDynaInt(partSetKeyword[i][j],None)
                    if value is not None:
                        pids.append(value)                
            partSet = self.CreatePartSetwithID(psid, da1, da2, da3, da4, solver, pids)
        if partSetKeyword[0] == "*SET_PART_LIST_TITLE":
            name = partSetKeyword[1][0]
            optionKeyword = partSetKeyword[2] 
            psid = KooDynaInt(optionKeyword[0])
            da1 = KooDynaFloat(optionKeyword[1])
            da2 = KooDynaFloat(optionKeyword[2])
            da3 = KooDynaFloat(optionKeyword[3])
            da4 = KooDynaFloat(optionKeyword[4])
            solver = KooDynaString(optionKeyword[5],'MECH')
            pids = []
            for i in range(3,len(partSetKeyword)):
                for j in range(len(partSetKeyword[i])):
                    value = KooDynaInt(partSetKeyword[i][j],None)
                    if value is not None:
                        pids.append(value)                
            partSet = self.CreatePartSetwithID(psid, da1, da2, da3, da4, solver, pids, name)
    
    def MoveElementsfromRigidPartstoPart(self, exceptPIDs = {}, offsetid = 0):
        maxPIDOffset = self.maxID + offsetid
        for rigidPart in self.partsRigid.values():
            curPID = rigidPart.id - maxPIDOffset
            if curPID in exceptPIDs:
                continue            
            if curPID in self.parts:
                part = self.parts[curPID]
                part.elementManager.AddElementsfromElementManager(rigidPart.elementManager)
                rigidPart.elementManager.RemoveAllElements()
                
    def ChangetoRigidPartNotinSphere(self, center, radius, exceptPIDs = {}):
        locx = center[0]
        locy = center[1]
        locz = center[2]
        
        for part in self.parts.values():
            if part.id in exceptPIDs:
                continue
            if part.id in self.partsRigid:
                partRigid = self.partsRigid[part.id]
            else:
                continue
            if part.elementManager.IsOverlappingwithSphere(locx, locy, locz, radius) == False:
                elems = part.elementManager.elements
                partRigid.elementManager.AddElements(elems)
                part.elementManager.RemoveAllElements()
                
    def ChangeConstrainedNodalRigidBodytoBeam(self, cnrbIDs, newPart : KooPart):        
        nodeMan = newPart.nodeManager
        elemMan = newPart.elementManager
        for id in cnrbIDs:
            if id in self.constrainedParts:
                part : KooConstrainedNodalRigidBodyPart  = self.constrainedParts[id]                 
                nodeset : NodeSet = part.nodeSet
                centerX = 0.0
                centerY = 0.0
                centerZ = 0.0
                numNodes = len(nodeset.nodes)
                for nid in nodeset.nodes:
                    n =nodeset[nid]
                    centerX += n.x
                    centerY += n.y
                    centerZ += n.z
                centerX /= numNodes
                centerY /= numNodes 
                centerZ /= numNodes
                
                n1 = nodeMan.CreateNode(centerX, centerY, centerZ)
                for nid in nodeset.nodes:
                    n2 = nodeset.nodes[nid]                    
                    elemMan.CreateLineLinearElement(n1, n2)
        
        for id in cnrbIDs:
            #remove id in self.constrainedParts[id]
            if id in self.constrainedParts:
                del self.constrainedParts[id]
                    
                
                
                
                
                
    def ChangetoRigidElementsOutsideofSphere(self, center, radius, exceptPIDs = {}):
        locx = center[0]
        locy = center[1]
        locz = center[2]
        
        for part in self.parts.values():
            if part.id in exceptPIDs:
                continue
            if part.id in self.partsRigid:
                partRigid = self.partsRigid[part.id]
            else:
                continue
            outerElems, boundaryElems, innerElems = part.elementManager.GetOuterandBoundaryandInnerElement(locx, locy, locz, radius)
            part.elementManager.RemoveAllElements()
            partRigid.elementManager.RemoveAllElements()
            partRigid.elementManager.AddElements(outerElems)
            part.elementManager.AddElements(boundaryElems)
            part.elementManager.AddElements(innerElems)
            
            
            
                
                
    
    def GenerateRigidPartforAll(self, materialMan : KooMaterialManager, sectionMan : KooSectionManager, offsetid = 0):
        rigidMat = materialMan.rigidMaterials
        allMat = materialMan.materials
        
        maxid = self.maxID + offsetid        
        
        for part in self.parts.values():
            if type(part) == KooPartComposite:
                part : KooPartComposite = part
                if part.id in self.partsRigid:
                    continue
                else:
                    rho = part.GetAverageDensity(materialMan)
                    nu = part.GetAveragePoissionRatio(materialMan)
                    E = part.GetTensileModulus(materialMan)
                    newRigidMat = materialMan.CreateRigidMaterial("RIGID_" + str(part.id), rho, nu, E)
                    
                    if part.tshell:
                        section = sectionMan.CreateSolidSection("RIGID_" + str(part.id))
                    else:
                        thickness = part.GetTotalThickness()
                        section = sectionMan.CreateShellSection("RIGID_" + str(part.id), thickness)
                                             
                    newPart = KooPart(part.nodeManager, None, newRigidMat, section, part.nodeSetManager)                    
                    newPart.SetID(maxid + part.id)                    
                    self.partsRigid[part.id] = newPart                    
                    
            else:
                part : KooPart = part
                if part.id in self.partsRigid:
                    continue
                else:
                    curRigidMat = rigidMat[part.material.id]
                    newPart = KooPart(part.nodeManager, None, curRigidMat, part.section, part.nodeSetManager)
                    newPart.SetID(maxid + part.id)
                    newPart.SetMaterial(curRigidMat)
                    self.partsRigid[part.id] = newPart

    def RemoveAllRigidPart(self):
        self.partsRigid = {}        
        
    
    def UpdateMaterial(self, materialMan : KooMaterialManager):
        for part in self.parts.values():
            if type(part) == KooPartComposite:
                part : KooPartComposite = part
            else:
                mid = part.material.id 
                if mid in materialMan.materials:
                    newMat = materialMan.materials[mid]
                    part.SetMaterial(newMat)
                
    def WritetoDynaKeyword(self, startPID = 0, startNID = 0, startEID = 0):
        keyword = ""
        for i in self.parts:
            part = self.parts[i]
            keyword += part.WritetoDynaPart(startPID)
            if len(part.elementManager.elements) >0:
                
                keyword += part.WritetoDynaElements(startNID, startEID)
        
        for i in self.partsRigid:
            part = self.partsRigid[i]
            keyword += part.WritetoDynaPart(startPID)
            if len(part.elementManager.elements) >0:                
                keyword += part.WritetoDynaElements(startNID, startEID)
        
        for i in self.partSets:
            partSet = self.partSets[i]
            keyword += partSet.WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPID = 0, startNID = 0, startEID = 0):
        for i in self.parts:
            part = self.parts[i]            
            part.WriteStreamDynaPart(stream, startPID)
            if len(part.elementManager.elements) >0:
                
                part.WriteStreamDynaElements(stream, startNID, startEID)
                
        for i in self.partsRigid:
            part = self.partsRigid[i]
            part.WriteStreamDynaPart(stream, startPID)
            if len(part.elementManager.elements) >0:
                part.WriteStreamDynaElements(stream, startNID, startEID)
        
        for i in self.partSets:
            partSet = self.partSets[i]
            partSet.WriteStreamDynaKeyword(stream)

    # ========================================================================
    # IGA Part 관련 메서드
    # ========================================================================

    def CreateIGAPart(self, source_pid, materialManager, sectionManager, options):
        """
        IGA 파트 생성 - Material, Section ID 자동 할당

        Args:
            source_pid: 원본 FEM Part ID
            materialManager: KooMaterialManager 인스턴스
            sectionManager: KooSectionManager 인스턴스
            options: IGA 옵션 딕셔너리
                - 'iga_id': IGA Part ID (옵션, 없으면 자동 할당)
                - 'output_file': 출력 파일명 (필수)
                - 그 외 KooIGAPart에서 사용하는 옵션들

        Returns:
            KooIGAPart 인스턴스

        Example:
            iga_part = partManager.CreateIGAPart(
                source_pid=5,
                materialManager=matManager,
                sectionManager=secManager,
                options={
                    'iga_id': 100,
                    'output_file': 'iga_part.k'
                }
            )
        """
        from KooCAEManager.KooIGAPart import KooIGAPart

        # 원본 파트 확인
        if source_pid not in self.parts:
            raise ValueError(f"Source part {source_pid} not found")

        source_part = self.parts[source_pid]

        # === 1. IGA Part ID (사용자 지정 또는 자동) ===
        iga_pid = options.get('iga_id')
        if iga_pid is None:
            self.maxIGAID += 1
            iga_pid = self.maxIGAID
            options['iga_id'] = iga_pid

        # PID 중복 검사
        if iga_pid in self.parts or iga_pid in self.igaParts:
            raise ValueError(f"IGA Part ID {iga_pid} already exists")

        # === 2. Material 복제 (MaterialManager가 자동 ID 할당) ===
        if source_part.mid not in materialManager.materials:
            raise ValueError(f"Source part material ID {source_part.mid} not found in MaterialManager")

        source_material = materialManager.materials[source_part.mid]

        new_material = materialManager.CloneMaterial(
            source_material,
            name_suffix='_IGA'
        )
        material_id = new_material.id

        # === 3. Section 생성 (SectionManager가 자동 ID 할당) ===
        ir = options.get('integration_rule', 0)

        new_section = sectionManager.CreateIGASection(
            name=f'IGA_Section_{iga_pid}',
            ir=ir
        )
        section_id = new_section.id

        # === 4. IGA Part 생성 ===
        iga_part = KooIGAPart(
            source_part=source_part,
            pid=iga_pid,
            mid=material_id,
            secid=section_id,
            options=options
        )

        # === 5. Manager에 등록 ===
        self.igaParts[iga_pid] = iga_part
        self.maxIGAID = max(self.maxIGAID, iga_pid)

        # Include 파일 경로 저장
        if iga_part.output_file not in self.igaIncludes:
            self.igaIncludes.append(iga_part.output_file)

        return iga_part

    def CreateIGAPartWithAutoID(self, source_pid, materialManager, sectionManager, options):
        """
        IGA ID를 자동 할당하여 IGA 파트 생성

        Args:
            source_pid: 원본 FEM Part ID
            materialManager: KooMaterialManager 인스턴스
            sectionManager: KooSectionManager 인스턴스
            options: IGA 옵션 (iga_id 없어도 됨)

        Returns:
            KooIGAPart 인스턴스
        """
        # iga_id가 없으면 자동 할당
        if 'iga_id' not in options or options['iga_id'] is None:
            self.maxIGAID += 1
            options['iga_id'] = self.maxIGAID

        # output_file이 없으면 자동 생성
        if 'output_file' not in options:
            options['output_file'] = f'iga_part_{source_pid}_id{options["iga_id"]}.k'

        return self.CreateIGAPart(source_pid, materialManager, sectionManager, options)

    def WriteAllIGAFiles(self, output_dir='.'):
        """
        모든 IGA 파트를 파일로 출력

        Args:
            output_dir: 출력 디렉토리 (default: 현재 디렉토리)

        Returns:
            생성된 파일 경로 리스트
        """
        import os

        created_files = []

        for iga_id, iga_part in self.igaParts.items():
            # 출력 경로 조정
            if output_dir != '.':
                original_file = iga_part.output_file
                filename = os.path.basename(original_file)
                iga_part.output_file = os.path.join(output_dir, filename)

            # 파일 생성
            file_path = iga_part.WriteToFile()
            created_files.append(file_path)

            print(f"IGA Part {iga_id} written to: {file_path}")

        return created_files

    def WriteIGAIncludes(self, stream, relative_path=True):
        """
        모든 IGA Include 문을 메인 파일에 출력

        Args:
            stream: 파일 스트림
            relative_path: True이면 상대경로, False이면 절대경로

        Example:
            with open('main.k', 'w') as f:
                partManager.WriteStreamDynaKeyword(f)
                partManager.WriteIGAIncludes(f)
        """
        if len(self.igaParts) == 0:
            return

        stream.write("$\n")
        stream.write("$--- IGA Part Includes ---\n")
        stream.write("$\n")

        for iga_part in self.igaParts.values():
            include_str = iga_part.GenerateInclude(relative_path)
            stream.write(include_str)

    def RemoveIGAPart(self, iga_id):
        """
        IGA 파트 제거

        Args:
            iga_id: 제거할 IGA Part ID
        """
        if iga_id in self.igaParts:
            iga_part = self.igaParts[iga_id]

            # Include 리스트에서도 제거
            if iga_part.output_file in self.igaIncludes:
                self.igaIncludes.remove(iga_part.output_file)

            del self.igaParts[iga_id]
            print(f"IGA Part {iga_id} removed")
        else:
            print(f"IGA Part {iga_id} not found")

    def GetIGAPartsBySourcePID(self, source_pid):
        """
        특정 원본 파트로부터 생성된 IGA 파트들 찾기

        Args:
            source_pid: 원본 FEM Part ID

        Returns:
            List[KooIGAPart]
        """
        result = []
        for iga_part in self.igaParts.values():
            if iga_part.source_part.id == source_pid:
                result.append(iga_part)
        return result


