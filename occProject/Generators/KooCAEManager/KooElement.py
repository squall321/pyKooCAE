from __future__ import annotations
import math
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression

from collections import defaultdict, deque

from collections import Counter
from KooCAEManager.KooNode import Node, NodeManager
from KooCAEManager.KooOperator import *


def _format_mass8(value: float) -> str:
    """*ELEMENT_MASS 8자리 고정폭 포맷.
    기본: 8.2e (예: 1.23e+05). 음수/3자리 지수로 8자를 넘으면
    mantissa 자릿수를 줄여 8자 안에 맞춘다.
    """
    s = format(value, "8.2e")
    if len(s) <= 8:
        return s
    s = format(value, ".1e")
    if len(s) <= 8:
        return s
    # 극단값: 지수만 표기
    s = format(value, ".0e")
    return s[:8]


class Element:
    def __init__(self,id=0):
        self.id = id
        self.type = ""
        self.nodes = []
        self.boundaries = [] 
        #self.time = []
    
    def RemapNodes(self, nodes):
        for i in range(len(self.nodes)):
            if self.nodes[i].id in nodes:
                self.nodes[i] = nodes[self.nodes[i].id]

    def Connectivity(self):
        connectivity = []
        for n in self.nodes:
            connectivity.append(n.id)
        return connectivity
        
    def GetCenterPoint(self):
        x = 0.0
        y = 0.0
        z = 0.0
        for n in self.nodes:        
            x += n.x
            y += n.y
            z += n.z
        x /= len(self.nodes)
        y /= len(self.nodes)
        z /= len(self.nodes)
        return (x,y,z)

    def SetID(self,id):
        self.id = id

    def SetType(self,type):
        self.type = type
    
    def SetBoundaries(self):
        self.boundaries = []
    
    def GetBoundaries(self):
        if len(self.boundaries) == 0:
            self.SetBoundaries()
        return self.boundaries
    
    def AddNode(self,node : Node):
        if node is not None:
            self.nodes.append(node)        
            node.SetElementAdjacency(self)

    #def AddTime(self, current_time):
    #    self.time.append(current_time)
    
    def RemoveNode(self, location=0):
        if location < len(self.nodes):
            self.nodes[location].RemoveElementAdjacency(self)
            self.nodes.pop(location)

    def ClearNodes(self):
        self.nodes.clear()
    
    def SetElementAdjacencyforNodes(self):
        for node in self.nodes:
            node.SetElementAdjacency(self)
    
    def Print(self):
        print(self.id,self.type)
    
    def Write(self,stream,split=" "):
        stream.write("{id}{split}{type}".format(id=self.id,split=split,type=self.type))
    
    def CreateIsotropicConstitutiveEquation(self, E, nu):
        return None
    
    def GreenLagrange(self, F):
        """
        Compute the Green-Lagrange strain tensor from the deformation gradient F.
        """
        E = 0.5 * (F.T @ F - np.eye(F.shape[0]))
        return E
    
    def toVoigt(self, E):
        """
        Convert the Green-Lagrange strain tensor to Voigt notation.
        """
        return np.array([E[0,0], E[1,1], E[2,2], 2*E[0,1], 2*E[1,2], 2*E[0,2]])
        
    def fromVoigt(self, Sv):
        """
        Convert from Voigt notation to the full 3x3 tensor.
        """
        return np.array([
            [Sv[0], Sv[3]/2, Sv[5]/2],
            [Sv[3]/2, Sv[1], Sv[4]/2],
            [Sv[5]/2, Sv[4]/2, Sv[2]]
        ])
        
    def ComputeF(self, X, u, dN_dX):
        """
        Compute the deformation gradient F from the nodal coordinates X, displacements u, and shape function gradients dN_dX.
        """
        F = np.eye(X.shape[1])
        for a in range(X.shape[0]):
            F += np.outer(u[a], dN_dX[a])
        return F
    
    def GetXMatrix(self):
        X = np.array([[node.x, node.y, node.z] for node in self.nodes])
        return X
    
    def GetUMatrix(self, timestep = -1):
        nsize = len(self.nodes)
        u = np.zeros((nsize, 3), dtype=np.float32)
        if timestep >= 0:
            for i in range(nsize):
                disp = self.nodes[i].GetDisplacement(timestep)
                u[i, 0] = disp[0]
                u[i, 1] = disp[1]
                u[i, 2] = disp[2]
        else:
            maxSize = self.nodes[0].GetDisplacementSize() - 1
            for i in range(nsize):
                disp = self.nodes[i].GetDisplacement(maxSize)
                u[i, 0] = disp[0]
                u[i, 1] = disp[1]
                u[i, 2] = disp[2]
        return u
        
class PointElement(Element):
    def __init__(self,id,nodes = None, massElemType= None):
        super(PointElement,self).__init__(id)
        self.nodes = nodes
        self.mass = 0.0
        self.massX = 0.0
        self.massY = 0.0
        self.massZ = 0.0
        # 루트 elementManager에 저장될 때 원본 PID 보존 (0이면 caller의 pid 사용)
        self.pid = 0

        if massElemType != None:
            if nodes != None:
                self.SetElementAdjacencyforNodes()
                self.SetType("POINT")
        else:
            self.SetType("POINT_NSET")
            self.nsid = nodes

    def SetNodesPoint(self, node1): 
        if type(node1) == int:
            self.nsid = node1            
            self.SetType("POINT_NSET")
        else:
            self.nodes = [] 
            self.AddNode(node1)
            self.SetType("POINT")

    def SetMass(self,mass):
        self.mass = mass
        self.massX = mass
        self.massY = mass
        self.massZ = mass
    
    def SetMassXYZ(self,massX,massY,massZ):
        self.massX = massX
        self.massY = massY
        self.massZ = massZ  
    
    def SettimeSize(self, size):
        pass      
    

class LineElement(Element):
    def __init__(self,id,nodes = None):
        super(LineElement,self).__init__(id)
        self.nodes = nodes
        self.boundaries = [] 
        self.constraints = []
        self.local = 2
        
        self.resultant = []
        self.plasticStrain = []         
        #self.stress = {}
        #self.plasticStrain = {}
        if nodes != None:
            self.SetElementAdjacencyforNodes()
            self.SetBoundaries()
            if len(nodes) == 2:
                self.SetType("LINE2")
            elif len(nodes) == 3:
                self.SetType("LINE3")

    def GetNumIntegrationPoints(self):
        return 1

    def AddResultant(self, axial, shear_s, shear_t, moment_s, moment_t, torsion, pleps):
        resultant = [axial, shear_s, shear_t, moment_s, moment_t, torsion, pleps]
        self.resultant.append(resultant)
    
    def AddPlasticStrain(self, plasticstrain):
        self.plasticStrain.append(plasticstrain)
        
    def SetTimeSize(self, size):
        self.resultant = np.zeros((size,6), dtype=np.float32)
        self.plasticStrain = np.zeros((size,1), dtype=np.float32)
            
    def GetNumSteps(self):
        if len(self.resultant) > 0:
            # first stress, but index is unknown
            return len(self.resultant)
        else:
            return 0
      
    def SetNodesLinear(self,node1,node2):
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)  
        self.SetType("LINE2")
        self.SetBoundaries()

    def SetNodesQuadratic(self,node1,node2,node3):
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.SetType("LINE3")
        self.SetBoundaries()

    def SetConstraints(self,rt1,rr1,rt2,rr2):
        self.constraints = [rt1,rr1,rt2,rr2]
    
    def SetCoordinate(self,local):
        self.local = local

    def SetBoundaries(self):
        self.boundaries = []
        if self.type == "LINE2":
            self.boundaries.append([self.nodes[0]])
            self.boundaries.append([self.nodes[1]])
        elif self.type == "LINE3":
            self.boundaries.append([self.nodes[0]])
            self.boundaries.append([self.nodes[2]])
        return self.boundaries
    
    def GetBoundaries(self):
        if len(self.boundaries) == 0:
            self.SetBoundaries()
        return self.boundaries

    def Print(self):
        if self.type == "LINE2":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id)
        elif self.type == "LINE3":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id)

    def Write(self,stream,split=" "):
        if self.type == "LINE2":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id))
        elif self.type == "LINE3":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id))

class FaceElement(Element):
    def __init__(self,id,nodes=[], theta = None, beta = None):
        super(FaceElement,self).__init__(id)
        self.nodes = nodes 
        self.boundaries = []
        self.theta = theta
        self.beta = beta

        self.stress = {}
        self.plasticStrain = {}
        self.yieldFunction = {}
        if len(nodes) != 0:
            self.SetElementAdjacencyforNodes()
            self.SetBoundaries()
            if len(nodes) == 3:
                self.SetType("TRI3")
            elif len(nodes) == 6:
                self.SetType("TRI6")
            elif len(nodes) == 4:
                self.SetType("QUAD4")
            elif len(nodes) == 8:
                self.SetType("QUAD8")
                
        
    def GetNumIntegrationPoints(self):
        if len(self.stress) > 0:
            return len(self.stress)
        if self.type == "TRI3":
            return 1
        elif self.type == "TRI6":
            return 3
        elif self.type == "QUAD4":
            return 4
        elif self.type == "QUAD8":
            return 9
        
    def SetMirrorConnectivityXYPlane(self):
        if self.type == "TRI3":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            self.nodes = [n1,n3,n2]
        elif self.type == "TRI6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n1,n3,n2,n6,n5,n4]
        elif self.type == "QUAD4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n1,n4,n3,n2]
        elif self.type == "QUAD8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n1,n4,n3,n2,n8,n7,n6,n5]

    def SetMirrorConnectivityYZPlane(self):
        if self.type == "TRI3":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            self.nodes = [n2,n1,n3]
        elif self.type == "TRI6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n2,n1,n3,n5,n4,n6]
        elif self.type == "QUAD4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n2,n1,n4,n3]
        elif self.type == "QUAD8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n2,n1,n4,n3,n6,n5,n8,n7]          

    def SetMirrorConnectivityXZPlane(self):
        if self.type == "TRI3":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            self.nodes = [n3,n2,n1]
        elif self.type == "TRI6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n3,n2,n1,n6,n5,n4]
        elif self.type == "QUAD4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n4,n3,n2,n1]
        elif self.type == "QUAD8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n4,n3,n2,n1,n8,n7,n6,n5]
            

    def GetNumSteps(self):
        if len(self.stress) > 0:
            # first stress, but index is unknown
            firstStress = self.stress[list(self.stress.keys())[0]]
            return len(firstStress)
        else:
            return 0    
        
    def SetTimeSize(self, size, iptsize = 3):
        for i in range(iptsize):
            self.stress[i] = np.zeros((size,6), dtype=np.float32)
            self.plasticStrain[i] = np.zeros((size,1), dtype=np.float32)
            self.yieldFunction[i] = np.zeros((size,1), dtype=np.float32)
    
    def GetCauchyStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]
            stressTensor = np.array([[sigxx,sigxy,sigzx],[sigxy,sigyy,sigyz],[sigzx,sigyz,sigzz]])
            return stress
        else:
            return None
        
    def GetCauchyStressXX(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            return sigxx
        else:
            return None
    
    def GetCauchyStressYY(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigyy = stress[1]
            return sigyy
        else:
            return None
    
    def GetCauchyStressXY(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxy = stress[3]
            return sigxy
        else:
            return None
        
    def GetVonMisesStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]
            sigm = np.sqrt(0.5*((sigxx-sigyy)**2 + (sigyy-sigzz)**2 + (sigzz-sigxx)**2 + 6*(sigxy**2 + sigyz**2 + sigzx**2)))
            return sigm
        else:
            return None

    def GetPrincipalStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]

            stressTensor = np.array([[sigxx,sigxy,sigzx],[sigxy,sigyy,sigyz],[sigzx,sigyz,sigzz]])
            eigvals, eigvecs = np.linalg.eig(stressTensor)
            sig1 = eigvals[0]
            sig2 = eigvals[1]
            sig3 = eigvals[2]
            return sig1, sig2, sig3
        else:
            return None

    def GetHydrostaticStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigh = (sigxx + sigyy + sigzz)/3
            return sigh
        else:
            return None    

    def GetPlasticStrain(self, ipt, ithStep):
        plasticStrainHistory = self.plasticStrain.get(ipt,[])
        if len(plasticStrainHistory) > ithStep:
            plasticStrain = plasticStrainHistory[ithStep]
            return plasticStrain
        else:
            return None
    
    def AddStressTensorandVonMisesandYieldFunction(self,ipt,sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,vonMisesStress,yieldfunction):
        stress = [sigxx, sigyy, sigzz, sigxy, sigyz, sigzx]
        stressHistory = self.stress.get(ipt,[])
        stressHistory.append(stress)
        self.stress[ipt] = stressHistory
        yieldFunctionHistory = self.yieldFunction.get(ipt,[])
        yieldFunctionHistory.append(yieldfunction)
        self.yieldFunction[ipt] = yieldFunctionHistory

    def AddStressTensorandPlasticStrain(self,ipt,sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,plasticstrain):
        stress = [sigxx, sigyy, sigzz, sigxy, sigyz, sigzx]
        stressHistory = self.stress.get(ipt,[])
        stressHistory.append(stress)
        self.stress[ipt] = stressHistory
        plasticStrainHistory = self.plasticStrain.get(ipt,[])
        plasticStrainHistory.append(plasticstrain)
        self.plasticStrain[ipt] = plasticStrainHistory
        
    def SetStressTensorandPlasticStrain(self, ipt, timestep, sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,plasticstrain):
        stressHistory = self.stress.get(ipt,[])
        plasticHistory = self.plasticStrain.get(ipt,[])
        stressHistory[timestep] = [sigxx,sigyy,sigzz,sigxy,sigyz,sigzx]
        plasticHistory[timestep][0] = plasticstrain
        
    def SetNodesTri3(self,node1,node2,node3):
        self.SetType("TRI3")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)

    def SetNodesTri6(self,node1,node2,node3,node4,node5,node6):
        self.SetType("TRI6")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)

    def SetNodesQuad4(self,node1,node2,node3,node4):
        self.SetType("QUAD4")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
    
    def SetNodesQuad8(self,node1,node2,node3,node4,node5,node6,node7,node8):
        self.SetType("QUAD8")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)
        self.AddNode(node7)
        self.AddNode(node8)

    def SetThetaBeta4(self,theta1,theta2,theta3,theta4,beta):
        self.theta = [theta1,theta2,theta3,theta4]
        self.beta = beta 
    
    def SetThetaBeta8(self,theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8,beta):
        self.theta = [theta1,theta2,theta3,theta4,theta5,theta6,theta7,theta8]
        self.beta = beta

    def SetBoundaries(self):
        self.boundaries = []
        if self.type == "TRI3":
            boundaryA = []
            boundaryB = [] 
            boundaryC = []

      
            boundaryA.append(self.nodes[0].id)
            boundaryA.append(self.nodes[1].id)
            boundaryB.append(self.nodes[1].id)
            boundaryB.append(self.nodes[2].id)
            boundaryC.append(self.nodes[2].id)
            boundaryC.append(self.nodes[0].id)
            self.boundaries.append(boundaryA) 
            self.boundaries.append(boundaryB)
            self.boundaries.append(boundaryC)
        elif self.type == "QUAD4":
            boundaryA = []
            boundaryB = []
            boundaryC = []
            boundaryD = []
            boundaryA.append(self.nodes[0].id)
            boundaryA.append(self.nodes[1].id)
            boundaryB.append(self.nodes[1].id)
            boundaryB.append(self.nodes[2].id)
            boundaryC.append(self.nodes[2].id)
            boundaryC.append(self.nodes[3].id)
            boundaryD.append(self.nodes[3].id)
            boundaryD.append(self.nodes[0].id)
            self.boundaries.append(boundaryA)
            self.boundaries.append(boundaryB)
            self.boundaries.append(boundaryC)
            self.boundaries.append(boundaryD)
        return self.boundaries
    
    def GetBoundaries(self):
        if len(self.boundaries) == 0:
            self.SetBoundaries()
        return self.boundaries

    def Print(self):
        if self.type == "TRI3":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id)
        elif self.type == "TRI6":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id)
        elif self.type == "QUAD4":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id)
        elif self.type == "QUAD8":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id,self.nodes[6].id,self.nodes[7].id)
        
    
    def Write(self,stream,split=" "):
        if self.type == "TRI3":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id))
        elif self.type == "TRI6":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}{split}{node7}{split}{node8}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[2].id,node5=self.nodes[3].id,node6=self.nodes[4].id,node7=self.nodes[5].id,node8=self.nodes[5].id))
        elif self.type == "QUAD4":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id))
        elif self.type == "QUAD8":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}{split}{node7}{split}{node8}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id,node5=self.nodes[4].id,node6=self.nodes[5].id,node7=self.nodes[6].id,node8=self.nodes[7].id))

    def GenerateAnsysAPDLKeyword(self):
        keywordString = ""
        if self.type == "TRI3":
            keywordString += "En,{eid},{n1},{n2},{n3},{n3}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id)
        elif self.type == "TRI6":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n3},{n3}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id)
        elif self.type == "QUAD4":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id)
        elif self.type == "QUAD8":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id,n7=self.nodes[6].id,n8=self.nodes[7].id)
        return keywordString

    def CreateIsotropicConstitutiveEquation(self, E, nu):
        # Plane Stress condition for 2D elements    
        C = E / (1 - nu**2) * np.array([
            [1, nu, 0],
            [nu, 1, 0],
            [0, 0, (1 - nu)/2]
        ])
        return C
    
    def CreatePlaneStrainConstitutiveEquation(self, E, nu):
        # Plane Strain condition for 2D elements
        C = E / ((1 + nu) * (1 - 2 * nu)) * np.array([
            [1 - nu, nu, 0],    
            [nu, 1 - nu, 0],
            [0, 0, (1 - 2 * nu)/2]
        ])

        return C
    
    def GradShape(self):
        if self.type == "TRI3":
            X = [[self.nodes[0].x, self.nodes[0].y, self.nodes[0].z],
                 [self.nodes[1].x, self.nodes[1].y, self.nodes[1].z],
                 [self.nodes[2].x, self.nodes[2].y, self.nodes[2].z]]
            v1 = X[1] - X[0]
            v2 = X[2] - X[0]
            normal = np.cross(v1, v2)
            e1 = v1 / np.linalg.norm(v1)
            e3 = normal / np.linalg.norm(normal)
            e2 = np.cross(e3, e1)
            R = np.vstack([e1, e2, e3])  # 3x3
            
            # Local 2D coordinates (3x2)
            X_local = (R @ (X - X[0]).T).T[:, :2]
            x1, x2, x3 = X_local
            A = 0.5 * np.linalg.det(np.array([[1, *x1], [1, *x2], [1, *x3]]))
            b = np.array([
                [x2[1] - x3[1], x3[1] - x1[1], x1[1] - x2[1]],
                [x3[0] - x2[0], x1[0] - x3[0], x2[0] - x1[0]]
            ]) / (2 * A)
            
            dN_local = b.T  # (3x2)
            dN_global = (R[:2, :].T @ dN_local.T).T  # (3x3)
            return dN_global
        elif self.type == "QUAD4":
            X = [[self.nodes[0].x, self.nodes[0].y, self.nodes[0].z],
                 [self.nodes[1].x, self.nodes[1].y, self.nodes[1].z],
                 [self.nodes[2].x, self.nodes[2].y, self.nodes[2].z],
                 [self.nodes[3].x, self.nodes[3].y, self.nodes[3].z]]
            v1 = X[1] - X[0]
            v2 = X[3] - X[0]
            normal = np.cross(v1, v2)
            e1 = v1 / np.linalg.norm(v1)
            e3 = normal / np.linalg.norm(normal)
            e2 = np.cross(e3, e1)
            R = np.vstack([e1, e2, e3])  # 3x3

            X_local = (R @ (X - X[0]).T).T[:, :2]
            dN_dxi = np.array([
                [-0.25, -0.25],
                [ 0.25, -0.25],
                [ 0.25,  0.25],
                [-0.25,  0.25]
            ])

            J = dN_dxi.T @ X_local  # 2x2
            dN_local = np.linalg.solve(J.T, dN_dxi.T).T  # 4x2
            dN_global = (R[:2, :].T @ dN_local.T).T  # 4x3
            return dN_global
        else:
            raise NotImplementedError("GradShape is not implemented for this element type: {}".format(self.type))
    
    
    def GetStressfromDisplacement(self, E, nu, timestep = -1):
        nsize = len(self.nodes)
        X = self.GetXMatrix()
        U = self.GetUMatrix(timestep)
        dN = self.GradShape()
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        C = self.CreateIsotropicConstitutiveEquation(E, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        return S
    
    def GetStressfromReverseDisplacement(self, E, nu, timestep = -1):
        '''
        deformed configuration is state without stress
        undeformed configuration is state with stress
        '''
        nsize = len(self.nodes)
        Xorigin = self.GetXMatrix() 
        Uorigin = self.GetUMatrix(timestep)
        X = Xorigin + Uorigin
        U = -Uorigin
        dN = self.GradShape()
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        C = self.CreateIsotropicConstitutiveEquation(E, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        return S
        
        
                
class SolidElement(Element):
    def __init__(self,id,nodes=[]):
        super(SolidElement,self).__init__(id)
        self.nodes = nodes
        self.boundaries = []

        self.stress = {}
        self.plasticStrain = {}
        self.yieldFunction = {}
        if len(self.nodes) != 0:
            self.SetElementAdjacencyforNodes()
            self.SetBoundaries()
            if len(self.nodes) == 4:
                self.SetType("TETRA4")
            elif len(self.nodes) == 10:
                self.SetType("TETRA10")
            elif len(self.nodes) == 6:
                self.SetType("PENTA6")
            elif len(self.nodes) == 8:
                self.SetType("HEXA8")
            elif len(self.nodes) == 20:
                self.SetType("HEXA20")        
        
    def FixConnectivityHexa8withNeighborElement(self, neighborElement):
        if self.type != "HEXA8" or neighborElement.type != "HEXA8":
            return
        boundaryNodes = self.GetBoundaries()
        neighborElementBoundaries = neighborElement.GetBoundaries()
        neighborElementPosition = -1
        neighborElementPositionOpposite = -1        
        elemFaceidtoNeighborFaceid = {}
        opposite_face = {0:5, 1:3, 2:4, 3:1, 4:2, 5:0}

        for i in range(len(boundaryNodes)):
            boundary = boundaryNodes[i]
            for j in range(len(neighborElementBoundaries)):
                neighborBoundary = neighborElementBoundaries[j]                                
                if set(sorted(boundary)) == set(sorted(neighborBoundary)):                    
                    neighborElementPosition = j
                    nej = j                     
                    jopposite = opposite_face[j]
                    iopposite = opposite_face[i]
                    neighborElementPositionOpposite = jopposite
                    elemFaceidtoNeighborFaceid[i] = jopposite
                    elemFaceidtoNeighborFaceid[iopposite] = j
        
                        
        if neighborElementPosition == -1:
            print("Error: No matching boundary found between the elements.")
            return
        
        
        for i in range(len(boundaryNodes)):
            boundary = boundaryNodes[i]
            if i in elemFaceidtoNeighborFaceid.keys():
                continue
            for j in range(len(neighborElementBoundaries)):
                if j in elemFaceidtoNeighborFaceid.values():
                    continue
                neighborBoundary = neighborElementBoundaries[j]                
                # two boundary share 2 same nodes 
                nodeList = list(set(sorted(boundary)) & set(sorted(neighborBoundary)))
                if len(nodeList) == 2:
                    elemFaceidtoNeighborFaceid[i] = j 
        
        
        neighborFaceidtoElemFaceid = {}
        for elemFaceid, neighborFaceid in elemFaceidtoNeighborFaceid.items():            
            neighborFaceidtoElemFaceid[neighborFaceid] = elemFaceid
        # change connectivity of the element    
        nids = [-1,-1,-1,-1,-1,-1,-1,-1]
        for i in range(len(self.nodes)):
            nid = self.nodes[i].id 
            
            if nid in boundaryNodes[neighborFaceidtoElemFaceid[0]]:
                if nid in boundaryNodes[neighborFaceidtoElemFaceid[1]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[4]]:
                        nids[0] = nid
                    elif nid in boundaryNodes[neighborFaceidtoElemFaceid[2]]:
                        nids[1] = nid
                elif nid in boundaryNodes[neighborFaceidtoElemFaceid[2]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[3]]:
                        nids[2] = nid
                elif nid in boundaryNodes[neighborFaceidtoElemFaceid[3]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[4]]:
                        nids[3] = nid
            elif nid in boundaryNodes[neighborFaceidtoElemFaceid[5]]:
                if nid in boundaryNodes[neighborFaceidtoElemFaceid[1]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[4]]:
                        nids[4] = nid
                    elif nid in boundaryNodes[neighborFaceidtoElemFaceid[2]]:
                        nids[5] = nid
                elif nid in boundaryNodes[neighborFaceidtoElemFaceid[2]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[3]]:
                        nids[6] = nid
                elif nid in boundaryNodes[neighborFaceidtoElemFaceid[3]]:
                    if nid in boundaryNodes[neighborFaceidtoElemFaceid[4]]:
                        nids[7] = nid
        tmpNodes = {} 
        for i in range(len(self.nodes)):
            nid = self.nodes[i].id 
            if nid in nids:
                tmpNodes[nid] = self.nodes[i]
                
        self.nodes = []                 
        for nid in nids:
            self.nodes.append(tmpNodes[nid])
        
        self.SetBoundaries()
        return 
        
    
    def SetMirrorConnectivityXYPlaneNew(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n1,n3,n2,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n1,n3,n2,n4,n7,n6,n5,n8,n9,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n1,n3,n2,n4,n6,n5]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n5,n8,n7,n6,n1,n4,n3,n2]
        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n5, n6, n7, n8, n1, n2, n3, n4, n13, n14, n15, n16, n9, n10, n11, n12, n20, n19, n18, n17]            
                             
    
    def SetMirrorConnectivityXYPlane(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n1,n3,n2,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n1,n3,n2,n4,n7,n6,n5,n8,n9,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n1,n3,n2,n4,n6,n5]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n1,n4,n3,n2,n5,n8,n7,n6]
        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n1,n4,n3,n2,n5,n8,n7,n6,n9,n12,n11,n10,n13,n16,n15,n14,n20,n19,n18,n17]
    
    def SetMirrorConnectivityYZPlaneNew(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n2,n1,n3,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n2,n1,n3,n4,n6,n5,n7,n9,n8,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n2,n1,n3,n5,n4,n6]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n4, n1, n2, n3, n8, n5, n6, n7]


            #[n2,n1,n4,n3,n6,n5,n8,n7]
        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n4, n1, n2, n3, n8, n5, n6, n7, n12, n9, n10, n11, n16, n13, n14, n15, n18, n17, n20, n19]


            #[n4, n3, n2, n1, n8, n7, n6, n5, n12, n11, n10, n9, n16, n15, n14, n13, n18, n17, n20, n19]
            
            #[n2,n1,n4,n3,n6,n5,n8,n7,n10,n9,n12,n11,n14,n13,n16,n15,n18,n17,n20,n19]
    
    def SetMirrorConnectivityYZPlane(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n2,n1,n3,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n2,n1,n3,n4,n6,n5,n7,n9,n8,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n2,n1,n3,n5,n4,n6]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n2,n1,n4,n3,n6,n5,n8,n7]
        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n2,n1,n4,n3,n6,n5,n8,n7,n10,n9,n12,n11,n14,n13,n16,n15,n18,n17,n20,n19]
    
    def SetMirrorConnectivityXZPlaneNew(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n1,n3,n2,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n1,n3,n2,n4,n7,n6,n5,n8,n9,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n4,n5,n6,n1,n2,n3]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n4, n3, n2, n1, n8, n7, n6, n5]

        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n4, n3, n2, n1, n8, n7, n6, n5, n12, n11, n10, n9, n16, n15, n14, n13, n19, n18, n20, n17]

       
    def SetMirrorConnectivityXZPlane(self):
        if self.type == "TETRA4":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            self.nodes = [n1,n3,n2,n4]
        elif self.type == "TETRA10":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            self.nodes = [n1,n3,n2,n4,n7,n6,n5,n8,n9,n10]
        elif self.type == "PENTA6":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            self.nodes = [n4,n5,n6,n1,n2,n3]
        elif self.type == "HEXA8":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            self.nodes = [n1,n4,n3,n2,n5,n8,n7,n6]
        elif self.type == "HEXA20":
            n1 = self.nodes[0]
            n2 = self.nodes[1]
            n3 = self.nodes[2]
            n4 = self.nodes[3]
            n5 = self.nodes[4]
            n6 = self.nodes[5]
            n7 = self.nodes[6]
            n8 = self.nodes[7]
            n9 = self.nodes[8]
            n10 = self.nodes[9]
            n11 = self.nodes[10]
            n12 = self.nodes[11]
            n13 = self.nodes[12]
            n14 = self.nodes[13]
            n15 = self.nodes[14]
            n16 = self.nodes[15]
            n17 = self.nodes[16]
            n18 = self.nodes[17]
            n19 = self.nodes[18]
            n20 = self.nodes[19]
            self.nodes = [n1,n4,n3,n2,n5,n8,n7,n6,n12,n11,n10,n9,n16,n15,n14,n13,n17,n20,n19,n18]
                          
    def SetTimeSize(self, size):
        self.stress[0] = np.zeros((size,6), dtype=np.float32)
        self.plasticStrain[0] = np.zeros((size,1), dtype=np.float32)
        self.yieldFunction[0] = np.zeros((size,1), dtype=np.float32)
            
    
    def GetNumIntegrationPoints(self):
        if len(self.stress) > 0:
            return len(self.stress)
        return 1

    def GetNumSteps(self):
        if len(self.stress) > 0:
            # first stress, but index is unknown
            firstStress = self.stress[list(self.stress.keys())[0]]
            return len(firstStress)
        else:
            return 0    
    
    def GetCauchyStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]
            stressTensor = np.array([[sigxx,sigxy,sigzx],[sigxy,sigyy,sigyz],[sigzx,sigyz,sigzz]])
            return stress
        else:
            return None
        
    def GetCauchyStressXX(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            return sigxx
        else:
            return None
        
    def GetCauchyStressYY(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigyy = stress[1]
            return sigyy
        else:
            return None
        
    def GetCauchyStressZZ(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigzz = stress[2]
            return sigzz
        else:
            return None
        
    def GetCauchyStressXY(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxy = stress[3]
            return sigxy
        else:
            return None
        
    def GetCauchyStressYZ(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigyz = stress[4]
            return sigyz
        else:
            return None
        
    def GetCauchyStressZX(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigzx = stress[5]
            return sigzx
        else:
            return None       
        
    def GetVonMisesStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]
            sigm = np.sqrt(0.5*((sigxx-sigyy)**2 + (sigyy-sigzz)**2 + (sigzz-sigxx)**2 + 6*(sigxy**2 + sigyz**2 + sigzx**2)))
            return sigm
        else:
            return None

    def GetPrincipalStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigxy = stress[3]
            sigyz = stress[4]
            sigzx = stress[5]

            stressTensor = np.array([[sigxx,sigxy,sigzx],[sigxy,sigyy,sigyz],[sigzx,sigyz,sigzz]])
            eigvals, eigvecs = np.linalg.eig(stressTensor)
            sig1 = eigvals[0]
            sig2 = eigvals[1]
            sig3 = eigvals[2]
            return sig1, sig2, sig3
        else:
            return None

    def GetHydrostaticStress(self, ipt, ithStep):
        stressHistory = self.stress.get(ipt,[])
        if len(stressHistory) > ithStep:
            stress = stressHistory[ithStep]
            sigxx = stress[0]
            sigyy = stress[1]
            sigzz = stress[2]
            sigh = (sigxx + sigyy + sigzz)/3
            return sigh
        else:
            return None    

    def GetPlasticStrain(self, ipt, ithStep):
        plasticStrainHistory = self.plasticStrain.get(ipt,[])
        if len(plasticStrainHistory) > ithStep:
            plasticStrain = plasticStrainHistory[ithStep]
            return plasticStrain
        else:
            return None
    
    def AddStressTensorandVonMisesandYieldFunction(self,ipt,sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,vonMisesStress,yieldfunction):
        stress = [sigxx, sigyy, sigzz, sigxy, sigyz, sigzx]
        stressHistory = self.stress.get(ipt,[])
        stressHistory.append(stress)
        self.stress[ipt] = stressHistory
        yieldFunctionHistory = self.yieldFunction.get(ipt,[])
        yieldFunctionHistory.append(yieldfunction)
        self.yieldFunction[ipt] = yieldFunctionHistory

    def AddStressTensorandPlasticStrain(self,ipt,sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,plasticstrain):
        stress = [sigxx, sigyy, sigzz, sigxy, sigyz, sigzx]
        stressHistory = self.stress.get(ipt,[])
        stressHistory.append(stress)
        self.stress[ipt] = stressHistory
        plasticStrainHistory = self.plasticStrain.get(ipt,[])
        plasticStrainHistory.append(plasticstrain)
        self.plasticStrain[ipt] = plasticStrainHistory
        
    def SetStressTensorandPlasticStrain(self, ipt, timestep, sigxx,sigyy,sigzz,sigxy,sigyz,sigzx,plasticstrain):
        stressHistory = self.stress.get(ipt,[])
        plasticHistory = self.plasticStrain.get(ipt,[])
        stressHistory[timestep] = [sigxx,sigyy,sigzz,sigxy,sigyz,sigzx]
        plasticHistory[timestep][0] = plasticstrain

    def SetNodesTetra4(self,node1,node2,node3,node4):
        self.SetType("TETRA4")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
    
    def SetNodesPenta6(self,node1,node2,node3,node4,node5,node6):
        self.SetType("PENTA6")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)
    
    def SetNodesTetra10(self,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10):
        self.SetType("TETRA10")
        self.nodes = [] 
        self.AddNode(node1) 
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)
        self.AddNode(node7)
        self.AddNode(node8)
        self.AddNode(node9)
        self.AddNode(node10)
    
    def SetNodesHexa8(self,node1,node2,node3,node4,node5,node6,node7,node8):
        self.SetType("HEXA8")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)
        self.AddNode(node7)
        self.AddNode(node8)
    
    def SetNodesHexa20(self,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15,node16,node17,node18,node19,node20):
        self.SetType("HEXA20")
        self.nodes = [] 
        self.AddNode(node1)
        self.AddNode(node2)
        self.AddNode(node3)
        self.AddNode(node4)
        self.AddNode(node5)
        self.AddNode(node6)
        self.AddNode(node7)
        self.AddNode(node8)
        self.AddNode(node9)
        self.AddNode(node10)
        self.AddNode(node11)
        self.AddNode(node12)
        self.AddNode(node13)
        self.AddNode(node14)
        self.AddNode(node15)
        self.AddNode(node16)
        self.AddNode(node17)
        self.AddNode(node18)
        self.AddNode(node19)
        self.AddNode(node20)

    def SetBoundaries(self):
        self.boundaries = [] 
        if self.type == "TETRA4":
            boundary1 = []
            boundary2 = []
            boundary3 = []
            boundary4 = []
            boundary1.append(self.nodes[0].id)
            boundary1.append(self.nodes[2].id)
            boundary1.append(self.nodes[1].id)
            boundary2.append(self.nodes[0].id)
            boundary2.append(self.nodes[1].id)
            boundary2.append(self.nodes[3].id)
            boundary3.append(self.nodes[1].id)
            boundary3.append(self.nodes[2].id)
            boundary3.append(self.nodes[3].id)
            boundary4.append(self.nodes[2].id)
            boundary4.append(self.nodes[0].id)
            boundary4.append(self.nodes[3].id)
            self.boundaries.append(boundary1)
            self.boundaries.append(boundary2)
            self.boundaries.append(boundary3)
            self.boundaries.append(boundary4)
        elif self.type == "PENTA6":
            boundary1 = []
            boundary2 = []
            boundary3 = []
            boundary4 = []
            boundary5 = []
            boundary6 = []
            boundary1.append(self.nodes[0].id)
            boundary1.append(self.nodes[1].id)
            boundary1.append(self.nodes[2].id)
            boundary2.append(self.nodes[3].id)
            boundary2.append(self.nodes[4].id)
            boundary2.append(self.nodes[5].id)
            boundary3.append(self.nodes[0].id)
            boundary3.append(self.nodes[1].id)
            boundary3.append(self.nodes[4].id)
            boundary3.append(self.nodes[3].id)
            boundary4.append(self.nodes[1].id)
            boundary4.append(self.nodes[2].id)
            boundary4.append(self.nodes[5].id)
            boundary4.append(self.nodes[4].id)
            boundary5.append(self.nodes[2].id)
            boundary5.append(self.nodes[0].id)
            boundary5.append(self.nodes[3].id)
            boundary5.append(self.nodes[5].id)
            
            self.boundaries.append(boundary1)
            self.boundaries.append(boundary2)
            self.boundaries.append(boundary3)
            self.boundaries.append(boundary4)
            self.boundaries.append(boundary5)
        elif self.type == "HEXA8":
            boundary1 = []
            boundary2 = []
            boundary3 = []
            boundary4 = []
            boundary5 = []
            boundary6 = []
            boundary1.append(self.nodes[0].id)
            boundary1.append(self.nodes[3].id)
            boundary1.append(self.nodes[2].id)
            boundary1.append(self.nodes[1].id)

            boundary2.append(self.nodes[0].id)
            boundary2.append(self.nodes[1].id)
            boundary2.append(self.nodes[5].id)
            boundary2.append(self.nodes[4].id)

            boundary3.append(self.nodes[1].id)
            boundary3.append(self.nodes[2].id)
            boundary3.append(self.nodes[6].id)
            boundary3.append(self.nodes[5].id)

            boundary4.append(self.nodes[2].id)
            boundary4.append(self.nodes[3].id)
            boundary4.append(self.nodes[7].id)
            boundary4.append(self.nodes[6].id)
            
            boundary5.append(self.nodes[3].id)
            boundary5.append(self.nodes[0].id)
            boundary5.append(self.nodes[4].id)
            boundary5.append(self.nodes[7].id)

            boundary6.append(self.nodes[4].id)
            boundary6.append(self.nodes[5].id)
            boundary6.append(self.nodes[6].id)
            boundary6.append(self.nodes[7].id)

            self.boundaries.append(boundary1)
            self.boundaries.append(boundary2)
            self.boundaries.append(boundary3)
            self.boundaries.append(boundary4)
            self.boundaries.append(boundary5)
            self.boundaries.append(boundary6)
    
    def GetBoundaries(self):
        if len(self.boundaries) == 0:
            self.SetBoundaries()
        return self.boundaries

    def Print(self):
        if self.type == "TETRA4":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id)
        elif self.type == "PENTA6":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id)
        elif self.type == "HEXA8":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id,self.nodes[6].id,self.nodes[7].id)
        elif self.type == "TETRA10":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id,self.nodes[6].id,self.nodes[7].id,self.nodes[8].id,self.nodes[9].id)
        elif self.type == "HEXA20":
            print(self.id,self.type,self.nodes[0].id,self.nodes[1].id,self.nodes[2].id,self.nodes[3].id,self.nodes[4].id,self.nodes[5].id,self.nodes[6].id,self.nodes[7].id,self.nodes[8].id,self.nodes[9].id,self.nodes[10].id,self.nodes[11].id,self.nodes[12].id,self.nodes[13].id,self.nodes[14].id,self.nodes[15].id,self.nodes[16].id,self.nodes[17].id,self.nodes[18].id,self.nodes[19].id)
    
    def Write(self,stream,split=" "):
        if self.type == "TETRA4":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id))        
        elif self.type == "PENTA6":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id,node5=self.nodes[4].id,node6=self.nodes[5].id))
        elif self.type == "HEXA8":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}{split}{node7}{split}{node8}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id,node5=self.nodes[4].id,node6=self.nodes[5].id,node7=self.nodes[6].id,node8=self.nodes[7].id))
        elif self.type == "TETRA10":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}{split}{node7}{split}{node8}{split}{node9}{split}{node10}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id,node5=self.nodes[4].id,node6=self.nodes[5].id,node7=self.nodes[6].id,node8=self.nodes[7].id,node9=self.nodes[8].id,node10=self.nodes[9].id))
        elif self.type == "HEXA20":
            stream.write("{id}{split}{type}{split}{node1}{split}{node2}{split}{node3}{split}{node4}{split}{node5}{split}{node6}{split}{node7}{split}{node8}{split}{node9}{split}{node10}{split}{node11}{split}{node12}{split}{node13}{split}{node14}{split}{node15}{split}{node16}{split}{node17}{split}{node18}{split}{node19}{split}{node20}".format(id=self.id,split=split,type=self.type,node1=self.nodes[0].id,node2=self.nodes[1].id,node3=self.nodes[2].id,node4=self.nodes[3].id,node5=self.nodes[4].id,node6=self.nodes[5].id,node7=self.nodes[6].id,node8=self.nodes[7].id,node9=self.nodes[8].id,node10=self.nodes[9].id,node11=self.nodes[10].id,node12=self.nodes[11].id,node13=self.nodes[12].id,node14=self.nodes[13].id,node15=self.nodes[14].id,node16=self.nodes[15].id,node17=self.nodes[16].id,node18=self.nodes[17].id,node19=self.nodes[18].id,node20=self.nodes[19].id))

    def GenerateAnsysAPDLKeyword(self):
        keywordString = ""
        if self.type == "TETRA4":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id)            
        elif self.type == "PENTA6":
            keywordString += "En,{eid},{n1},{n2},{n3},{n3},{n4},{n5},{n6},{n6}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id)
        elif self.type == "HEXA8":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id,n7=self.nodes[6].id,n8=self.nodes[7].id)
        elif self.type == "TETRA10":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id,n7=self.nodes[6].id,n8=self.nodes[7].id,n9=self.nodes[8].id,n10=self.nodes[9].id)
        elif self.type == "HEXA20":
            keywordString += "En,{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10},{n11},{n12},{n13},{n14},{n15},{n16},{n17},{n18},{n19},{n20}\n".format(eid=self.id,n1=self.nodes[0].id,n2=self.nodes[1].id,n3=self.nodes[2].id,n4=self.nodes[3].id,n5=self.nodes[4].id,n6=self.nodes[5].id,n7=self.nodes[6].id,n8=self.nodes[7].id,n9=self.nodes[8].id,n10=self.nodes[9].id,n11=self.nodes[10].id,n12=self.nodes[11].id,n13=self.nodes[12].id,n14=self.nodes[13].id,n15=self.nodes[14].id,n16=self.nodes[15].id,n17=self.nodes[16].id,n18=self.nodes[17].id,n19=self.nodes[18].id,n20=self.nodes[19].id)
        return keywordString
    
    def CreateIsotropicConstitutiveEquation(self, E, nu):
        lam = E * nu / ((1 + nu) * (1 - 2 * nu))
        mu = E / (2 * (1 + nu))
        C = np.array(
            [[lam + 2 * mu, lam, lam, 0, 0, 0],
             [lam, lam + 2 * mu, lam, 0, 0, 0],
             [lam, lam, lam + 2 * mu, 0, 0, 0],
             [0, 0, 0, mu, 0, 0],
             [0, 0, 0, 0, mu, 0],
             [0, 0, 0, 0, 0, mu]]
        )
        return C
        
    def GradShape(self, X = None):
        if self.type == "TETRA4":
            x0, y0, z0 = X[0]
            x1, y1, z1 = X[1]
            x2, y2, z2 = X[2]
            x3, y3, z3 = X[3]

            J = np.array([
                [x1 - x0, x2 - x0, x3 - x0],
                [y1 - y0, y2 - y0, y3 - y0],
                [z1 - z0, z2 - z0, z3 - z0]
            ])
            detJ = np.linalg.det(J)
            if abs(detJ) < 1e-12:
                raise ValueError("Jacobian is singular or nearly zero.")

            invJ = np.linalg.inv(J)
            # Reference shape function gradients
            dN_dxi = np.array([
                [-1, -1, -1],
                [1,  0,  0],
                [0,  1,  0],
                [0,  0,  1]
            ])
            return dN_dxi @ invJ.T  # shape: (4,3)
        elif self.type == "HEXA8":
            xi = eta = zeta = 0  # 중심점 (0,0,0)

            dN_dxi = 0.125 * np.array([
                [-(1 - eta)*(1 - zeta), -(1 - xi)*(1 - zeta), -(1 - xi)*(1 - eta)],
                [ (1 - eta)*(1 - zeta), -(1 + xi)*(1 - zeta), -(1 + xi)*(1 - eta)],
                [ (1 + eta)*(1 - zeta),  (1 + xi)*(1 - zeta), -(1 + xi)*(1 + eta)],
                [-(1 + eta)*(1 - zeta),  (1 - xi)*(1 - zeta), -(1 - xi)*(1 + eta)],
                [-(1 - eta)*(1 + zeta), -(1 - xi)*(1 + zeta),  (1 - xi)*(1 - eta)],
                [ (1 - eta)*(1 + zeta), -(1 + xi)*(1 + zeta),  (1 + xi)*(1 - eta)],
                [ (1 + eta)*(1 + zeta),  (1 + xi)*(1 + zeta),  (1 + xi)*(1 + eta)],
                [-(1 + eta)*(1 + zeta),  (1 - xi)*(1 + zeta),  (1 - xi)*(1 + eta)],
            ])
            # dN_dxi shape: (8, 3)

            J = dN_dxi.T @ X
            invJ = np.linalg.inv(J)
            dN_dX = dN_dxi @ invJ.T
            return dN_dX
        else:
            raise NotImplementedError("Gradient of shape functions not implemented for element type: {}".format(self.type))
    
    def GetStressfromDisplacementandTopBottomCurvatureXYPlane(self, modulus, nu, d2w_dx2_top, d2w_dy2_top, d2w_dxdy_top, d2w_dx2_bottom, d2w_dy2_bottom, d2w_dxdy_bottom, minZ, maxZ, timestep = -1):
        nsize = len(self.nodes)
        X = self.GetXMatrix()
        U = self.GetUMatrix(timestep)
        dN = self.GradShape(X)
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        curZ = np.mean([node.z for node in self.nodes])
        curZValue = (curZ - minZ) / (maxZ - minZ)  # Normalized curvature value
        curd2w_dx2 = d2w_dx2_top * curZValue + d2w_dx2_bottom * (1 - curZValue)
        curd2w_dy2 = d2w_dy2_top * curZValue + d2w_dy2_bottom * (1 - curZValue)
        curd2w_dxdy = d2w_dxdy_top * curZValue + d2w_dxdy_bottom * (1 - curZValue)
        
        E[0, 0] += - curd2w_dx2 * (curZ - (minZ + maxZ) / 2)
        E[1, 1] += - curd2w_dy2 * (curZ - (minZ + maxZ) / 2)
        E[0, 1] += - curd2w_dxdy * (curZ - (minZ + maxZ) / 2)
        E[1, 0] += - curd2w_dxdy * (curZ - (minZ + maxZ) / 2)
        C = self.CreateIsotropicConstitutiveEquation(modulus, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        return S        
        
    def GetStressfromDisplacementandCurvatureXYPlane(self, modulus, nu, d2w_dx2, d2w_dy2, d2w_dxdy, centerZ,  timestep = -1):
        nsize = len(self.nodes)
        X = self.GetXMatrix()
        U = self.GetUMatrix(timestep)
        dN = self.GradShape(X)
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        curZ = np.mean([node.z for node in self.nodes])
        E[0, 0] += - d2w_dx2 * (curZ - centerZ)
        E[1, 1] += - d2w_dy2 * (curZ - centerZ)
        E[0, 1] += - d2w_dxdy * (curZ - centerZ)
        E[1, 0] += - d2w_dxdy * (curZ - centerZ)
        #print(curZ, centerZ)
        #print(E)
        C = self.CreateIsotropicConstitutiveEquation(modulus, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        #print(S)
        return S     
    
    def GetStressWithDirectionalExpansion(self, modulus, nu,
                                      ex, ey, ez,
                                      large_strain=True):
        """
        ex, ey, ez : 방향별 '자유 팽창' 변형률 (ΔL/L). thermal이면 αΔT 값을 그대로 넣음.
        large_strain=True : Green-Lagrange에 맞춰 ε + 0.5ε^2 보정 사용 (확대 변형 고려)
        mode : "3D" | "plane_stress" | "plane_strain"
        """        
        

        # 2) 방향별 '고유변형(팽창)' 텐서 구성
        if large_strain:
            # Green-Lagrange로 변환: 0.5(λ^2-1) ≈ ε + 0.5 ε^2 (λ=1+ε)
            #ex_GL = ex + 0.5 * ex * ex
            #ey_GL = ey + 0.5 * ey * ey
            #ez_GL = ez + 0.5 * ez * ez
            ex_GL = math.log(1 + ex)
            ey_GL = math.log(1 + ey)
            ez_GL = math.log(1 + ez)
        else:
            ex_GL, ey_GL, ez_GL = ex, ey, ez

        E_exp = np.array([[ex_GL, 0.0,   0.0],
                        [0.0,   ey_GL, 0.0],
                        [0.0,   0.0,   ez_GL]])

        # 5) 등방성 구성방정식으로 응력 계산
        C = self.CreateIsotropicConstitutiveEquation(modulus, nu)  # 6x6
        S = self.fromVoigt(C @ self.toVoigt(E_exp))               # 3x3 대칭 응력

        return S      
    
    def GetStressfromDisplacement(self, modulus, nu, timestep = -1):
        nsize = len(self.nodes)
        X = self.GetXMatrix()
        U = self.GetUMatrix(timestep)
        dN = self.GradShape(X)
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        C = self.CreateIsotropicConstitutiveEquation(modulus, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        return S
    
    def GetStressfromReverseDisplacement(self, modulus, nu, timestep = -1):
        '''
        deformed configuration is state without stress
        undeformed configuration is state with stress
        '''
        nsize = len(self.nodes)
        Xorigin = self.GetXMatrix() 
        Uorigin = self.GetUMatrix(timestep)
        X = Xorigin + Uorigin
        U = -Uorigin
        dN = self.GradShape(X)
        F = self.ComputeF(X, U, dN)
        E = self.GreenLagrange(F)
        C = self.CreateIsotropicConstitutiveEquation(modulus, nu)
        S = self.fromVoigt(C @ self.toVoigt(E))
        return S
    
class ShellSet:
    def __init__(self, sid, name, da1, da2, da3, da4, elemList = []):
        self.sid = sid
        self.name = name
        self.da1 = da1
        self.da2 = da2
        self.da3 = da3
        self.da4 = da4
        self.elemList = elemList
        
    def AddElement(self,element):
        self.elemList.append(element)
        
    def RemoveElements(self):
        self.elemList = []
    
    def WritetoDynaKeyword(self, startEID):
        keywordString = ""
        keywordString += "*SET_SHELL_TITLE\n"
        keywordString += format(self.name,  '>80')
        keywordString += "\n"   
        keywordString += format(self.sid,  '>10')
        keywordString += format(self.da1,  '>10')
        keywordString += format(self.da2,  '>10')
        keywordString += format(self.da3,  '>10')
        keywordString += format(self.da4,  '>10')
        keywordString += "\n"
        j = 0 
        for i in range(0,len(self.elemList)):
            j = j + 1            
            keywordString += format(self.elemList[i].id + startEID,  '>10')
            if j == 8:
                keywordString += "\n"
                j = 0
        if j != 0:
            keywordString += "\n"
        return keywordString
    
    def WriteStreamDynaKeyword(self, stream, startEID):
        stream.write("*SET_SHELL_TITLE\n")
        stream.write(format(self.name,  '>80'))
        stream.write("\n")
        stream.write(format(self.sid,  '>10'))
        stream.write(format(self.da1,  '>10'))
        stream.write(format(self.da2,  '>10'))
        stream.write(format(self.da3,  '>10'))
        stream.write(format(self.da4,  '>10'))
        stream.write("\n")
        j = 0
        for i in range(0,len(self.elemList)):
            j = j + 1
            stream.write(format(self.elemList[i].id + startEID,  '>10'))
            if j == 8:
                stream.write("\n")
                j = 0
        if j != 0:
            stream.write("\n")
        
            
class SolidSet:
    def __init__(self, sid,name = "", solver = "MECH", elemList =[]):
        self.sid = sid
        if name == "":
            self.name = "SolidSet{sid}".format(sid=sid)
        else:
            self.name = name
        self.solver = solver
        self.elemList = elemList
    
    def AddElement(self,element):
        self.elemList.append(element)
        
    def RemoveElements(self):
        self.elemList = []
    
    def WritetoDynaKeyword(self, startEID):
        print("SolidSet WritetoDynaKeyword")
        keywordString = ""
        keywordString += "*SET_SOLID_TITLE\n"
        keywordString += format(self.name,  '>80')
        keywordString += "\n"
        keywordString += format(self.sid,  '>10')
        keywordString += format(self.solver, '>10')
        keywordString += "\n"
        j = 0 
        for i in range(0,len(self.elemList)):
            j = j + 1            
            keywordString += format(self.elemList[i] + startEID,  '>10')
            if j == 8:
                keywordString += "\n"
                j = 0
        if j != 0:
            keywordString += "\n"
        return keywordString
    
    def WriteStreamDynaKeyword(self, stream, startEID):
        stream.write("*SET_SOLID_TITLE\n")
        stream.write(format(self.name,  '>80'))
        stream.write("\n")
        stream.write(format(self.sid,  '>10'))
        stream.write(format(self.solver, '>10'))
        stream.write("\n")
        j = 0
        for i in range(0,len(self.elemList)):
            j = j + 1
            stream.write(format(self.elemList[i] + startEID,  '>10'))
            if j == 8:
                stream.write("\n")
                j = 0
        if j != 0:
            stream.write("\n")
            
class ElementManager:
        
    def __init__(self,nodeManager = None, id=0):
        self.elementManagerID = id
        self.maxID = 0         
        self.elements = {}
        self.sets = {} 
        self.time = []
        
        self.maxSID = 0 
        self.elementsSet = {}
        
        self.TShellMode = False

        self.nodeManager = nodeManager 
        if self.nodeManager == None:
            self.nodeManager = NodeManager()               
        self.boundaryNodes = {}
    
    def OffsetID(self, offsetEID, offsetSID):
        for key in self.elements:
            element = self.elements[key]
            element.id += offsetEID
        for key in self.sets:
            elemSet = self.sets[key]
            elemSet.sid += offsetSID
            for i in range(len(elemSet.elemList)):
                elemSet.elemList[i] += offsetEID
        self.maxID += offsetEID
        self.maxSID += offsetSID

    def OverwritefromElementManager(self, elementManager : ElementManager, overwriteNode = False):
        self.maxID = max(self.maxID, elementManager.maxID)
        for key, value in elementManager.elements.items():
            self.elements[key] = value
        for key, value in elementManager.sets.items():
            self.sets[key] = value
        if len(elementManager.time) > 0:
            for key, value in elementManager.time.items():
                self.time[key] = value
        self.maxSID = max(self.maxSID, elementManager.maxSID)
        for key, value in elementManager.elementsSet.items():
            self.elementsSet[key] = value
        self.TShellMode = elementManager.TShellMode        
        if overwriteNode == True:
            self.nodeManager.OverwritefromNodeManager(elementManager.nodeManager)

    def SplitNodes(self, nodes):
        newNodeIDs = {}
        for id, node in nodes.items():
            newNodes = self.nodeManager.CreateNode(node.x, node.y, node.z)
            newNodeIDs[id] = newNodes 

        self.Remap(newNodeIDs)

    def Remap(self, nodes):
        for key, element in self.elements.items():
            element.RemapNodes(nodes)

    def Translate(self, dx, dy, dz):
        nodes = {}
        for key in self.elements:
            element = self.elements[key]
            for node in element.nodes:
                nodes[node.id] = node
        for key in nodes:
            node = nodes[key]
            node.Translate(dx,dy,dz)
    
    def Scaling(self, dx, dy, dz):
        nodes = {}
        for key in self.elements:
            element = self.elements[key]
            for node in element.nodes:
                nodes[node.id] = node
        #min max bounding box
        minx = 1e99
        miny = 1e99
        minz = 1e99
        maxx = -1e99
        maxy = -1e99
        maxz = -1e99
        for key in nodes:
            node = nodes[key]
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
        for key in nodes:
            node = nodes[key]
            #node.x = centerx + dx*(node.x-centerx)
            #node.y = centery + dy*(node.y-centery)
            #node.z = centerz + dz*(node.z-centerz)
            node.x = dx*(node.x)
            node.y = dy*(node.y)
            node.z = dz*(node.z)
            
    def SetMirrorConnectivityXYPlane(self):
        for key in self.elements:
            element = self.elements[key]
            if type(element) == FaceElement:
                element.SetMirrorConnectivityXYPlane()
            if type(element) == SolidElement:
                element.SetMirrorConnectivityXYPlane()
    def SetMirrorConnectivityYZPlane(self):
        for key in self.elements:
            element = self.elements[key]
            if type(element) == FaceElement:
                element.SetMirrorConnectivityYZPlane()
            if type(element) == SolidElement:
                element.SetMirrorConnectivityYZPlane() 
                   
    def SetMirrorConnectivityXZPlane(self):
        for key in self.elements:
            element = self.elements[key]
            if type(element) == FaceElement:
                element.SetMirrorConnectivityXZPlane()
            if type(element) == SolidElement:
                element.SetMirrorConnectivityXZPlane()
    def SetTShellMode(self,mode):
        self.TShellMode = mode
    
    def GetMaxID(self):
        return self.maxID
    
    def SetMaxID(self, id):
        self.maxID = id
            
    def CreateShellSet(self,name="",da1=0.0,da2=0.0,da3=0.0,da4=0.0, elemList=[]):
        self.maxSID += 1
        shellSet = ShellSet(self.maxSID,name,da1,da2,da3,da4,elemList)
        self.sets[self.maxSID] = shellSet
        return shellSet

    def CreateShellSetwithID(self, id, name = "", da1=0.0,da2=0.0,da3=0.0,da4=0.0, elemList=[]):
        self.maxSID = max(self.maxSID,id)
        shellSet = ShellSet(id,name,da1,da2,da3,da4,elemList)
        self.sets[id] = shellSet
        return shellSet
    
    def CreateSolidSet(self,name="",solver="MECH", elemList=[]):
        self.maxSID += 1
        solidSet = SolidSet(self.maxSID,name,solver,elemList)
        self.sets[self.maxSID] = solidSet
        return solidSet
    
    def CreateSolidSetwithID(self, id, name = "", solver = "MECH", elemList=[]):
        self.maxSID = max(self.maxSID,id)
        solidSet = SolidSet(id,name,solver,elemList)
        self.sets[id] = solidSet
        return solidSet
    
    def GetNumIntegrationPoints(self):
        firstElement = self.elements[list(self.elements.keys())[0]]
        return firstElement.GetNumIntegrationPoints()
    
    def AddTime(self,time):
        self.time.append(time)
    
    def SetTimeSize(self):
        size = len(self.time)
        for key in self.elements:
            element = self.elements[key]
            element.SetTimeSize(size)
    
    def NElement(self):
        return len(self.elements)

    def FindElementfromID(self,id):
        element = self.elements.get(id,None)
        return element
    
    def SetID(self,id):
        self.elementManagerID = id
    
    def GetCauchyStress(self,elementID, ipt, ithStep):
        element = self.FindElementfromID(elementID)
        if element != None:
            return element.GetCauchyStress(ipt,ithStep)
        else:
            return None


    def GetVonMisesStress(self, elementID, ipt, ithStep):
        element = self.FindElementfromID(elementID)
        if element != None:
            if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                return None
            else:
                return element.GetVonMisesStress(ipt,ithStep)
        else:
            return None
    
    def GetMaximumVonMisesStress(self):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        stress = 0 
                    else:
                        stress = element.GetVonMisesStress(ipt,ithStep)
                    if stress > maxStress:
                        maxStress = stress
        return maxStress
    
    def GetMinimumVonMisesStress(self):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        stress = 0
                    else:
                        stress = element.GetVonMisesStress(ipt,ithStep)
                    if stress < minStress:
                        minStress = stress
        return minStress

    def GetMaximumVonMisesStressTimeStep(self, ithStep):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                stress = element.GetVonMisesStress(ipt,ithStep)
                if stress > maxStress:
                    maxStress = stress
        return maxStress

    def GetMinimumVonMisesStressTimeStep(self, ithStep):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                stress = element.GetVonMisesStress(ipt,ithStep)
                if stress < minStress:
                    minStress = stress
        return minStress    
        
    def GetPrincipalStress(self, elementID, ipt, ithStep):
        element = self.FindElementfromID(elementID)
        if element != None:
            return element.GetPrincipalStress(ipt,ithStep)
        else:
            return None
    
    def GetMaximumPrincipalStress(self):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        pass
                    else:
                        ps1, ps2, ps3 = element.GetPrincipalStress(ipt,ithStep)
                        if ps1 > maxStress:
                            maxStress = ps1
                        if ps2 > maxStress:
                            maxStress = ps2
                        if ps3 > maxStress:
                            maxStress = ps3
        return maxStress

    def GetMinimumPrincipalStress(self):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        pass
                    else:
                        ps1, ps2, ps3 = element.GetPrincipalStress(ipt,ithStep)
                        if ps1 < minStress:
                            minStress = ps1
                        if ps2 < minStress:
                            minStress = ps2
                        if ps3 < minStress:
                            minStress = ps3
        return minStress
    
    def GetMaximumPrincipalStressTimeStep(self, ithStep):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                ps1, ps2, ps3 = element.GetPrincipalStress(ipt,ithStep)
                if ps1 > maxStress:
                    maxStress = ps1
                if ps2 > maxStress:
                    maxStress = ps2
                if ps3 > maxStress:
                    maxStress = ps3
        return maxStress

    def GetMinimumPrincipalStressTimeStep(self, ithStep):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                ps1, ps2, ps3 = element.GetPrincipalStress(ipt,ithStep)
                if ps1 < minStress:
                    minStress = ps1
                if ps2 < minStress:
                    minStress = ps2
                if ps3 < minStress:
                    minStress = ps3
                
        return minStress
        
    def GetHydrostaticStress(self, elementID, ipt, ithStep):
        element = self.FindElementfromID(elementID)
        if element != None:
            return element.GetHydrostaticStress(ipt,ithStep)
        else:
            return None    
        
    def GetMaximumHydrostaticStress(self):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        pass
                    else:
                        stress = element.GetHydrostaticStress(ipt,ithStep)
                        if stress > maxStress:
                            maxStress = stress
        return maxStress
    
    def GetMinimumHydrostaticStress(self):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                for ithStep in range(0,element.GetNumSteps()):
                    if element.type == "LINE2" or element.type == "LINE3" or element.type == "POINT":
                        # stress 계산 필요 
                        pass
                    else:
                        stress = element.GetHydrostaticStress(ipt,ithStep)
                        if stress < minStress:
                            minStress = stress
        return minStress
    
    def GetMaximumHydrostaticStressTimeStep(self, ithStep):
        maxStress = 0
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                stress = element.GetHydrostaticStress(ipt,ithStep)
                if stress > maxStress:
                    maxStress = stress
        return maxStress
    
    def GetMinimumHydrostaticStressTimeStep(self, ithStep):
        minStress = 1e99
        for key in self.elements:
            element = self.elements[key]
            for ipt in range(1,element.GetNumIntegrationPoints()+1):
                stress = element.GetHydrostaticStress(ipt,ithStep)
                if stress < minStress:
                    minStress = stress
        return minStress        

    def GetElementConnectivities(self,idtokey):
        elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "POINT":
                elementConnectivities = np.append(elementConnectivities,[1,idtokey[element.nodes[0].id]])
            elif element.type == "LINE2":
                elementConnectivities = np.append(elementConnectivities,[2,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id]])
            elif element.type == "LINE3":
                elementConnectivities = np.append(elementConnectivities,[3,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id]])
            elif element.type == "TRI3":
                elementConnectivities = np.append(elementConnectivities,[3,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id]])
            elif element.type == "TRI6":
                elementConnectivities = np.append(elementConnectivities,[6,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id],idtokey[element.nodes[4].id],idtokey[element.nodes[5].id]])
            elif element.type == "QUAD4":
                elementConnectivities = np.append(elementConnectivities,[4,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id]])            
            elif element.type == "QUAD8":
                elementConnectivities = np.append(elementConnectivities,[8,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id],idtokey[element.nodes[4].id],idtokey[element.nodes[5].id],idtokey[element.nodes[6].id],idtokey[element.nodes[7].id]])                 
            elif element.type == "TETRA4":
                elementConnectivities = np.append(elementConnectivities,[4,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id]])
            elif element.type == "PENTA6":
                elementConnectivities = np.append(elementConnectivities,[6,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id],idtokey[element.nodes[4].id],idtokey[element.nodes[5].id]])
            elif element.type == "HEXA8":
                elementConnectivities = np.append(elementConnectivities,[8,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id],idtokey[element.nodes[4].id],idtokey[element.nodes[5].id],idtokey[element.nodes[6].id],idtokey[element.nodes[7].id]])
        #size of elementConnectivities        
        return elementConnectivities

    def GetPointConnectivities(self,idtokey):
        nPointelem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "POINT":
                nPointelem += 1
        elementConnectivities = np.empty((nPointelem, 3), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "POINT":
                elementConnectivities[i,0] = 1
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                i += 1
        return elementConnectivities

        '''elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "POINT":
                elementConnectivities = np.append(elementConnectivities,[1,idtokey[element.nodes[0].id]])
        return elementConnectivities'''    

    def GetLine2Connectivities(self,idtokey):
        nLine2elem = 0  
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE2":
                nLine2elem += 1
        elementConnectivities = np.empty((nLine2elem, 4), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE2":
                elementConnectivities[i,0] = 2
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                i += 1
        return elementConnectivities
        '''elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE2":
                elementConnectivities = np.append(elementConnectivities,[2,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id]])
        return elementConnectivities'''

    def GetLine3Connectivities(self,idtokey):
        nLine3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE3":
                nLine3elem += 1
        elementConnectivities = np.empty((nLine3elem, 4), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE3":
                elementConnectivities[i,0] = 3
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                i += 1
        '''elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE3":
                elementConnectivities = np.append(elementConnectivities,[3,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id]])
        return elementConnectivities'''
        return elementConnectivities
    
    def GetTri3VonMisesStresses(self, ipt, ithStep):
        nTri3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                nTri3elem += 1
        elementVonMisesStress = np.empty((nTri3elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress

    def GetTri3StressXX(self, ipt, ithStep):
        nTri3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                nTri3elem += 1
        elementStressXX = np.empty((nTri3elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetTri3StressYY(self, ipt, ithStep):
        nTri3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                nTri3elem += 1
        elementStressYY = np.empty((nTri3elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY       
    
    def GetTri3StressXY(self, ipt, ithStep):
        nTri3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                nTri3elem += 1
        elementStressXY = np.empty((nTri3elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY    

    def GetTri3Connectivities(self,idtokey):
        nTri3elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                nTri3elem += 1
        elementConnectivities = np.empty((nTri3elem, 4), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                elementConnectivities[i,0] = 3
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                i += 1
        return elementConnectivities
        '''elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                elementConnectivities = np.append(elementConnectivities,[3,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id]])
        return elementConnectivities'''
    
    def GetTri6Connectivities(self,idtokey):
        nTri6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI6":
                nTri6elem += 1
        elementConnectivities = np.empty((nTri6elem, 7), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI6":
                elementConnectivities[i,0] = 6
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                i += 1
        return elementConnectivities
    
    def GetQuad4VonMisesStresses(self, ipt, ithStep):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementVonMisesStress = np.empty((nQuad4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress
    
    def GetQuad4StressXX(self, ipt, ithStep):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementStressXX = np.empty((nQuad4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetQuad4StressYY(self, ipt, ithStep):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementStressYY = np.empty((nQuad4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetQuad4StressXY(self, ipt, ithStep):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementStressXY = np.empty((nQuad4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY

    def GetQuad4ConnectivitieswithVonMisesStress(self,idtokey, ipt, ithStep):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementConnectivities = np.empty((nQuad4elem, 5), dtype=np.int32)
        elementVonMisesStress = np.empty((nQuad4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "QUAD4":
                elementConnectivities[i,0] = 4
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementConnectivities, elementVonMisesStress

    def GetQuad4Connectivities(self,idtokey):
        nQuad4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                nQuad4elem += 1
        elementConnectivities = np.empty((nQuad4elem, 5), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementConnectivities[i,0] = 4
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                i += 1
        return elementConnectivities

        '''
        elementConnectivities = np.array([]).astype(np.int32)
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                elementConnectivities = np.append(elementConnectivities,[4,idtokey[element.nodes[0].id],idtokey[element.nodes[1].id],idtokey[element.nodes[2].id],idtokey[element.nodes[3].id]])
        return elementConnectivities
        '''
    def GetQuad8Connectivities(self, idtokey):
        nQuad8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD8":
                nQuad8elem += 1
        elementConnectivities = np.empty((nQuad8elem, 9), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD8":
                elementConnectivities[i,0] = 8
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                elementConnectivities[i,7] = idtokey[element.nodes[6].id]
                elementConnectivities[i,8] = idtokey[element.nodes[7].id]
                i += 1
        return elementConnectivities
    '''
    def GetTetra4Connectivities(self,idtokey):        
        elementConnectivities = np.empty((0, 5), dtype=np.int32)

        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":                
                nid1 = idtokey[element.nodes[0].id]
                nid2 = idtokey[element.nodes[1].id]
                nid3 = idtokey[element.nodes[2].id]
                nid4 = idtokey[element.nodes[3].id]
                elementConnectivities = np.append(elementConnectivities, np.array([[4,nid1,nid2,nid3,nid4]]), axis=0)

        return elementConnectivities
    '''
    def GetTetra4VonMisesStresses(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementVonMisesStress = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress
    
    def GetTetra4StressXX(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressXX = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetTetra4StressYY(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressYY = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetTetra4StressZZ(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressZZ = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressZZ[i,0] = element.GetCauchyStressZZ(ipt,ithStep)
                i += 1
        return elementStressZZ
    
    def GetTetra4StressXY(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressXY = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY
    
    def GetTetra4StressYZ(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressYZ = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressYZ[i,0] = element.GetCauchyStressYZ(ipt,ithStep)
                i += 1
        return elementStressYZ
    
    def GetTetra4StressXZ(self, ipt, ithStep):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementStressXZ = np.empty((nTetra4elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementStressXZ[i,0] = element.GetCauchyStressXZ(ipt,ithStep)
                i += 1
        return elementStressXZ
       
    def GetTetra4Connectivities(self,idtokey):
        nTetra4elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                nTetra4elem += 1
        elementConnectivities = np.empty((nTetra4elem, 5), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                elementConnectivities[i,0] = 4
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                i += 1
        return elementConnectivities
    
    def GetPenta6VonMisesStresses(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementVonMisesStress = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress
    
    def GetPenta6StressXX(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressXX = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetPenta6StressYY(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressYY = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetPenta6StressZZ(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressZZ = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressZZ[i,0] = element.GetCauchyStressZZ(ipt,ithStep)
                i += 1
        return elementStressZZ
    
    def GetPenta6StressXY(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressXY = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY
    
    def GetPenta6StressYZ(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressYZ = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressYZ[i,0] = element.GetCauchyStressYZ(ipt,ithStep)
                i += 1
        return elementStressYZ
    
    def GetPenta6StressXZ(self, ipt, ithStep):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementStressXZ = np.empty((nPenta6elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementStressXZ[i,0] = element.GetCauchyStressXZ(ipt,ithStep)
                i += 1
        return elementStressXZ
            
    def GetPenta6Connectivities(self,idtokey):
        nPenta6elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                nPenta6elem += 1
        elementConnectivities = np.empty((nPenta6elem, 7), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                elementConnectivities[i,0] = 6
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                i += 1
        return elementConnectivities    

    def GetTetra10VonMisesStresses(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementVonMisesStress = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress
    
    def GetTetra10StressXX(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressXX = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetTetra10StressYY(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressYY = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetTetra10StressZZ(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressZZ = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressZZ[i,0] = element.GetCauchyStressZZ(ipt,ithStep)
                i += 1
        return elementStressZZ
    
    def GetTetra10StressXY(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressXY = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY
    
    def GetTetra10StressYZ(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressYZ = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressYZ[i,0] = element.GetCauchyStressYZ(ipt,ithStep)
                i += 1
        return elementStressYZ
    
    def GetTetra10StressXZ(self, ipt, ithStep):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementStressXZ = np.empty((nTetra10elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementStressXZ[i,0] = element.GetCauchyStressXZ(ipt,ithStep)
                i += 1
        return elementStressXZ
            
    def GetTetra10Connectivities(self,idtokey):
        nTetra10elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                nTetra10elem += 1
        elementConnectivities = np.empty((nTetra10elem, 11), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                elementConnectivities[i,0] = 10
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                elementConnectivities[i,7] = idtokey[element.nodes[6].id]
                elementConnectivities[i,8] = idtokey[element.nodes[7].id]
                elementConnectivities[i,9] = idtokey[element.nodes[8].id]
                elementConnectivities[i,10] = idtokey[element.nodes[9].id]
                i += 1
        return elementConnectivities

    def GetHexa8VonMisesStresses(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementVonMisesStress = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress

    def GetHexa8StressXX(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressXX = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetHexa8StressYY(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressYY = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetHexa8StressZZ(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressZZ = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressZZ[i,0] = element.GetCauchyStressZZ(ipt,ithStep)
                i += 1
        return elementStressZZ
    
    def GetHexa8StressXY(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressXY = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY
    
    def GetHexa8StressYZ(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressYZ = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressYZ[i,0] = element.GetCauchyStressYZ(ipt,ithStep)
                i += 1
        return elementStressYZ
    
    def GetHexa8StressXZ(self, ipt, ithStep):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementStressXZ = np.empty((nHexa8elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementStressXZ[i,0] = element.GetCauchyStressXZ(ipt,ithStep)
                i += 1
        return elementStressXZ
        
    def GetHexa8Connectivities(self,idtokey):
        nHexa8elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                nHexa8elem += 1
        elementConnectivities = np.empty((nHexa8elem, 9), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                elementConnectivities[i,0] = 8
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                elementConnectivities[i,7] = idtokey[element.nodes[6].id]
                elementConnectivities[i,8] = idtokey[element.nodes[7].id]
                i += 1
                
        return elementConnectivities    

    def GetHexa20VonMisesStresses(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementVonMisesStress = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementVonMisesStress[i,0] = element.GetVonMisesStress(ipt,ithStep)
                i += 1
        return elementVonMisesStress

    def GetHexa20StressXX(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressXX = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressXX[i,0] = element.GetCauchyStressXX(ipt,ithStep)
                i += 1
        return elementStressXX
    
    def GetHexa20StressYY(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressYY = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressYY[i,0] = element.GetCauchyStressYY(ipt,ithStep)
                i += 1
        return elementStressYY
    
    def GetHexa20StressZZ(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressZZ = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressZZ[i,0] = element.GetCauchyStressZZ(ipt,ithStep)
                i += 1
        return elementStressZZ
    
    def GetHexa20StressXY(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressXY = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressXY[i,0] = element.GetCauchyStressXY(ipt,ithStep)
                i += 1
        return elementStressXY
    
    def GetHexa20StressYZ(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressYZ = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressYZ[i,0] = element.GetCauchyStressYZ(ipt,ithStep)
                i += 1
        return elementStressYZ
    
    def GetHexa20StressXZ(self, ipt, ithStep):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementStressXZ = np.empty((nHexa20elem, 1), dtype=np.float32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementStressXZ[i,0] = element.GetCauchyStressXZ(ipt,ithStep)
                i += 1
        return elementStressXZ        
    
    def GetHexa20Connectivities(self,idtokey):
        nHexa20elem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                nHexa20elem += 1
        elementConnectivities = np.empty((nHexa20elem, 21), dtype=np.int32)
        i = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                elementConnectivities[i,0] = 20
                elementConnectivities[i,1] = idtokey[element.nodes[0].id]
                elementConnectivities[i,2] = idtokey[element.nodes[1].id]
                elementConnectivities[i,3] = idtokey[element.nodes[2].id]
                elementConnectivities[i,4] = idtokey[element.nodes[3].id]
                elementConnectivities[i,5] = idtokey[element.nodes[4].id]
                elementConnectivities[i,6] = idtokey[element.nodes[5].id]
                elementConnectivities[i,7] = idtokey[element.nodes[6].id]
                elementConnectivities[i,8] = idtokey[element.nodes[7].id]
                elementConnectivities[i,9] = idtokey[element.nodes[8].id]
                elementConnectivities[i,10] = idtokey[element.nodes[9].id]
                elementConnectivities[i,11] = idtokey[element.nodes[10].id]
                elementConnectivities[i,12] = idtokey[element.nodes[11].id]
                elementConnectivities[i,13] = idtokey[element.nodes[12].id]
                elementConnectivities[i,14] = idtokey[element.nodes[13].id]
                elementConnectivities[i,15] = idtokey[element.nodes[14].id]
                elementConnectivities[i,16] = idtokey[element.nodes[15].id]
                elementConnectivities[i,17] = idtokey[element.nodes[16].id]
                elementConnectivities[i,18] = idtokey[element.nodes[17].id]
                elementConnectivities[i,19] = idtokey[element.nodes[18].id]
                elementConnectivities[i,20] = idtokey[element.nodes[19].id]
                i += 1
        return elementConnectivities
    
    def AddElementsfromElementManager(self, elementManager):
        elements = elementManager.elements
        self.AddElements(elements)
    
    def AddElementsfromMSH(self,mshElements, maxNID, maxEID, dim=-1, nodekeytoid = None):
        numElem = 0
        for elementSet in mshElements['entities']:
            curDim = elementSet['entityDim']
            elementList = elementSet['elements']
            for element in elementList:                
                elementTag = element['elementTag']
                nodeTags = element['nodeTags']
                nodes = [] 
                for nodeTag in nodeTags:
                    if nodekeytoid is not None:
                        nodes.append(self.nodeManager.FindNodefromID(nodekeytoid[nodeTag+maxNID]))
                    else:
                        nodes.append(self.nodeManager.FindNodefromID(nodeTag+maxNID))
                if curDim == 0:
                    if dim != 0 and dim != -1:
                        continue                    
                    if len(nodes) == 1:
                        #self.CreatePointElement(nodes[0], maxEID)
                        self.AddPointElement(elementTag+maxEID,nodes[0])
                        numElem += 1
                elif curDim == 1:
                    if dim != 1 and dim != -1:
                        continue                    
                    if len(nodes) == 2:
                        #self.CreateLineLinearElement(nodes[0],nodes[1],maxEID)
                        self.AddLineLinearElement(elementTag+maxEID,nodes[0],nodes[1])
                        numElem += 1
                    elif len(nodes) == 3:
                        #self.CreateLineQuadraticElement(nodes[0],nodes[1],nodes[2],maxEID) 
                        self.AddLineQuadraticElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2])
                        numElem += 1
                elif curDim == 2:
                    if dim != 2 and dim != -1:
                        continue                    
                    if len(nodes) == 3:
                        #self.CreateTriangleLinearElement(nodes[0],nodes[1],nodes[2],maxEID)
                        self.AddTriangleLinearElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2])
                        numElem += 1
                    elif len(nodes) == 4:
                        #self.CreateQuadrangleLinearElement(nodes[0],nodes[1],nodes[2],nodes[3],maxEID)
                        self.AddQuadrangleLinearElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2],nodes[3])
                        numElem += 1
                elif curDim == 3:
                    if dim != 3 and dim != -1:
                        continue                    
                    if len(nodes) == 4:
                        #self.CreateTetrahedronLinearElement(nodes[0],nodes[1],nodes[2],nodes[3],maxEID)
                        self.AddTetrahedronLinearElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2],nodes[3])
                        numElem += 1
                    elif len(nodes) == 6:
                        #self.CreatePentahedronLinearElement(nodes[0],nodes[1],nodes[2],nodes[3],nodes[4],nodes[5],maxEID)
                        self.AddPentahedronLinearElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2],nodes[3],nodes[4],nodes[5])
                        numElem += 1
                    elif len(nodes) == 8:
                        #self.CreateHexahedronLinearElement(nodes[0],nodes[1],nodes[2],nodes[3],nodes[4],nodes[5],nodes[6],nodes[7],maxEID)
                        self.AddHexahedronLinearElement(elementTag+maxEID,nodes[0],nodes[1],nodes[2],nodes[3],nodes[4],nodes[5],nodes[6],nodes[7])
                        numElem += 1
            print("Number of Elements: ",numElem) 
            numElem = numElem + 1

    def CreatePointElement(self,node1,mass = 0.0): 
        self.maxID = self.maxID + 1
        element = PointElement(self.maxID)
        element.SetNodesPoint(node1)
        element.SetMass(mass)
        self.AddElement(element)        
        return element
    
    def AddPointElement(self, id, node1,mass = 0.0):
        element = PointElement(id)
        element.SetNodesPoint(node1)
        element.SetMass(mass)
        self.AddElement(element)
        return element

    def CreateLineLinearElement(self,node1,node2,rt1=0,rr1=0,rt2=0,rr2=0,local=2):
        self.maxID = self.maxID + 1
        element = LineElement(self.maxID)
        element.SetNodesLinear(node1,node2)
        element.SetConstraints(rt1,rr1,rt2,rr2)
        element.SetCoordinate(local)
        self.AddElement(element)
        return element

    def AddLineLinearElement(self, id, node1, node2,rt1=0,rr1=0,rt2=0,rr2=0,local=2):
        element = LineElement(id)
        element.SetNodesLinear(node1,node2)
        element.SetConstraints(rt1,rr1,rt2,rr2)
        element.SetCoordinate(local)
        self.AddElement(element)
        return element
    
    def CreateLineQuadraticElement(self,node1,node2,node3,rt1=0,rr1=0,rt2=0,rr2=0,local=2):
        self.maxID = self.maxID + 1
        element = LineElement(self.maxID)
        element.SetNodesQuadratic(node1,node2,node3)
        element.SetConstraints(rt1,rr1,rt2,rr2)
        element.SetCoordinate(local)
        self.AddElement(element)
        return element

    def AddLineQuadraticElement(self, id, node1, node2, node3,rt1=0,rr1=0,rt2=0,rr2=0,local=2):
        element = LineElement(id)
        element.SetNodesQuadratic(node1,node2,node3)
        element.SetConstraints(rt1,rr1,rt2,rr2)
        element.SetCoordinate(local)
        self.AddElement(element)
        return element
    
    def CreateTriangleLinearElement(self,node1,node2,node3):
        self.maxID = self.maxID + 1
        element = FaceElement(self.maxID)
        element.SetNodesTri3(node1,node2,node3)
        self.AddElement(element)
        return element
    
    def AddTriangleLinearElement(self, id, node1, node2, node3):
        element = FaceElement(id)
        element.SetNodesTri3(node1,node2,node3)
        self.AddElement(element)
        return element
    
    def CreateTriangleQuadraticElement(self,node1,node2,node3,node4,node5,node6):
        self.maxID = self.maxID + 1
        element = FaceElement(self.maxID)
        element.SetNodesTri6(node1,node2,node3,node4,node5,node6)
        self.AddElement(element)
        return element    
    
    def AddTriangleQuadraticElement(self, id, node1, node2, node3, node4, node5, node6):
        element = FaceElement(id)
        element.SetNodesTri6(node1,node2,node3,node4,node5,node6)
        self.AddElement(element)
        return element

    def CreateQuadrangleLinearElement(self,node1,node2,node3,node4):
        self.maxID = self.maxID + 1
        element = FaceElement(self.maxID)
        element.SetNodesQuad4(node1,node2,node3,node4)
        self.AddElement(element)
        return element    
    
    def AddQuadrangleLinearElement(self, id, node1, node2, node3, node4):
        element = FaceElement(id)
        element.SetNodesQuad4(node1,node2,node3,node4)
        self.AddElement(element)
        return element
    
    def CreateQuadrangleQuadraticElement(self,node1,node2,node3,node4,node5,node6,node7,node8):
        self.maxID = self.maxID + 1
        element = FaceElement(self.maxID)
        element.SetNodesQuad8(node1,node2,node3,node4,node5,node6,node7,node8)
        self.AddElement(element)
        return element
    
    def AddQuadrangleQuadraticElement(self, id, node1, node2, node3, node4, node5, node6, node7, node8):
        element = FaceElement(id)
        element.SetNodesQuad8(node1,node2,node3,node4,node5,node6,node7,node8)
        self.AddElement(element)
        return element    

    def CreatePentahedronLinearElement(self,node1,node2,node3,node4,node5,node6):
        self.maxID = self.maxID + 1
        element = SolidElement(self.maxID)
        element.SetNodesPenta6(node1,node2,node3,node4,node5,node6)
        self.AddElement(element)
        return element

    def AddPentahedronLinearElement(self, id, node1, node2, node3, node4, node5, node6):
        element = SolidElement(id)
        element.SetNodesPenta6(node1,node2,node3,node4,node5,node6)
        self.AddElement(element)
        return element
        
    def CreateTetrahedronLinearElement(self,node1,node2,node3,node4):
        self.maxID = self.maxID + 1
        element = SolidElement(self.maxID)
        element.SetNodesTetra4(node1,node2,node3,node4)
        self.AddElement(element)
        return element

    def AddTetrahedronLinearElement(self, id, node1, node2, node3, node4):
        element = SolidElement(id)
        element.SetNodesTetra4(node1,node2,node3,node4)
        self.AddElement(element)
        return element

    def CreateTetrahedronQuadraticElement(self,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10):
        self.maxID = self.maxID + 1
        element = SolidElement(self.maxID)
        element.SetNodesTetra10(node1,node2,node3,node4,node5,node6,node7,node8,node9,node10)
        self.AddElement(element)
        return element

    def AddTetrahedronQuadraticElement(self, id, node1, node2, node3, node4, node5, node6, node7, node8, node9, node10):
        element = SolidElement(id)
        element.SetNodesTetra10(node1,node2,node3,node4,node5,node6,node7,node8,node9,node10)
        self.AddElement(element)
        return element

    def CreateHexahedronLinearElement(self,node1,node2,node3,node4,node5,node6,node7,node8):
        self.maxID = self.maxID + 1
        element = SolidElement(self.maxID)
        element.SetNodesHexa8(node1,node2,node3,node4,node5,node6,node7,node8)
        self.AddElement(element)
        return element
    
    def AddHexahedronLinearElement(self, id, node1, node2, node3, node4, node5, node6, node7, node8):
        element = SolidElement(id)
        element.SetNodesHexa8(node1,node2,node3,node4,node5,node6,node7,node8)
        self.AddElement(element)
        return element
    
    def CreateHexahedronQuadraticElement(self,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15,node16,node17,node18,node19,node20):
        self.maxID = self.maxID + 1
        element = SolidElement(self.maxID)
        element.SetNodesHexa20(node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15,node16,node17,node18,node19,node20)
        self.AddElement(element)
        return element

    def AddHexahedronQuadraticElement(self, id, node1, node2, node3, node4, node5, node6, node7, node8, node9, node10, node11, node12, node13, node14, node15, node16, node17, node18, node19, node20):
        element = SolidElement(id)
        element.SetNodesHexa20(node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15,node16,node17,node18,node19,node20)
        self.AddElement(element)
        return element
    
    def CreateElementsfromSegments(self, sharedNodes,segments):
        for segment in segments:
            if len(segment) == 2:
                if segment[0] not in sharedNodes or segment[1] not in sharedNodes:
                    continue
                node1 = self.nodeManager.nodes[segment[0]]
                node2 = self.nodeManager.nodes[segment[1]]
                self.CreateLineLinearElement(node1, node2)
            elif len(segment) == 3:
                if segment[0] not in sharedNodes or segment[1] not in sharedNodes or segment[2] not in sharedNodes:
                    continue
                node1 = self.nodeManager.nodes[segment[0]]
                node2 = self.nodeManager.nodes[segment[1]]
                node3 = self.nodeManager.nodes[segment[2]]
                self.CreateTriangleLinearElement(node1, node2, node3)
            elif len(segment) == 4:
                if segment[0] not in sharedNodes or segment[1] not in sharedNodes or segment[2] not in sharedNodes or segment[3] not in sharedNodes:
                    continue
                node1 = self.nodeManager.nodes[segment[0]]
                node2 = self.nodeManager.nodes[segment[1]]
                node3 = self.nodeManager.nodes[segment[2]]
                node4 = self.nodeManager.nodes[segment[3]]
                self.CreateQuadrangleLinearElement(node1, node2, node3, node4)

    def AddElement(self,element):
        self.elements[element.id] = element
        if element.id > self.maxID:
            self.maxID = element.id
    
    def AddElements(self, elements):
        for eid in elements:
            self.elements[eid] = elements[eid]
            self.maxID = max(self.maxID, eid)
        
    def AddElementsfromList(self,elements):
        for element in elements:
            self.AddElement(element)

    def RemoveAllElements(self):
        self.elements.clear()       
        self.maxID = 0
        
    def RemoveSetElements(self, elements):        
        removedSet = {}
        for i in self.sets:
            newElemList = [] 
            elemList = self.sets[i].elemList
            for eid in elemList:
                if eid in elements:
                    pass
                else:
                    newElemList.append(eid)
            if len(newElemList) == 0:
                removedSet[i] = i               
            else:
                self.sets[i].elemList = newElemList
        for key in removedSet:
            del self.sets[key]
                   
                    
    
    def RemoveAllSetElements(self):
        for aSet in self.sets:
            aSet.RemoveElements()            

    def RemoveElement(self,element):
        if element.id in self.elements:
            del self.elements[element.id]
    
    def RemoveElements(self, elements):
        for eid in elements:
            if eid in self.elements:
                del self.elements[eid]

    def GetElement(self,id):
        if id in self.elements:
            return self.elements[id]
        else:
            return None
        
    def GetNumberofLinearSolidElements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4" or element.type == "HEXA8" or element.type == "PENTA6":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofQuadraticSolidElements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10" or element.type == "HEXA20":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofTetra4Elements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA4":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofTetra10Elements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TETRA10":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofPenta6Elements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "PENTA6":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofHexa8Elements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA8":
                numSolidElem += 1
        return numSolidElem
    
    def GetNumberofHexa20Elements(self):
        numSolidElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "HEXA20":
                numSolidElem += 1
        return numSolidElem
        
    def GetNumberofLinearFaceElements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3" or element.type == "QUAD4":
                numFaceElem += 1
        return numFaceElem
    
    def GetNumberofTri3Elements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI3":
                numFaceElem += 1
        return numFaceElem
    
    def GetNumberofTri6Elements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI6":
                numFaceElem += 1
        return numFaceElem
    
    def GetNumberofQuad4Elements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD4":
                numFaceElem += 1
        return numFaceElem
    
    def GetNumberofQuad8Elements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "QUAD8":
                numFaceElem += 1
        return numFaceElem
    
        
    def GetNumberofQuadraticFaceElements(self):
        numFaceElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "TRI6" or element.type == "QUAD8":
                numFaceElem += 1
        return numFaceElem
    
    def GetNumberofLinearLineElements(self):
        numLineElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE2":
                numLineElem += 1
        return numLineElem
    
    def GetNumberofQuadraticLineElements(self):
        numLineElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "LINE3":
                numLineElem += 1
        return numLineElem

    def GetNumberofPointElements(self):
        numPointElem = 0
        for key in self.elements:
            element = self.elements[key]
            if element.type == "POINT":
                numPointElem += 1
            elif element.type == "POINT_NSET":
                numPointElem += 1
        return numPointElem
    
    def WritetoNastranStream(self, stream, pid, startNID, startEID):
        self.WritetoNastranStreamSolid(stream, pid, startNID, startEID)
        self.WritetoNastranStreamFace(stream, pid, startNID, startEID)
        self.WritetoNastranStreamLine(stream, pid, startNID, startEID)
        self.WritetoNastranStreamPoint(stream, pid, startNID, startEID)
    
    def WritetoNastranStreamSolid(self, stream, pid, startNID, startEID):
        if self.GetNumberofLinearSolidElements() > 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA4":
                    stream.write("CTETRA  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id+startNID):>8}{str(element.nodes[1].id+startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}\n")                    
                elif element.type == "PENTA6":
                    stream.write("CPENTA  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n")
                elif element.type == "HEXA8":
                    stream.write("CHEXA   ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n")
                    stream.write("+       ")
                    stream.write(f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n")                    
        if self.GetNumberofQuadraticSolidElements() > 0:
            for key in self.elements:
                element : SolidElement = self.elements[key] 
                if element.type == "TETRA10":
                    stream.write("CTETRA  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n")
                    stream.write("+       ")
                    stream.write(f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n")                    
                elif element.type == "HEXA20":
                    stream.write("CHEXA   ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n")
                    stream.write("+       ")
                    stream.write(f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}{str(element.nodes[10].id + startNID):>8}{str(element.nodes[11].id + startNID):>8}{str(element.nodes[12].id + startNID):>8}{str(element.nodes[13].id + startNID):>8}+\n")
                    stream.write("+       ")
                    stream.write(f"{str(element.nodes[14].id + startNID):>8}{str(element.nodes[15].id + startNID):>8}{str(element.nodes[16].id + startNID):>8}{str(element.nodes[17].id + startNID):>8}{str(element.nodes[18].id + startNID):>8}{str(element.nodes[19].id + startNID):>8}\n")                    

    
    def WritetoNastranStreamFace(self, stream, pid, startNID, startEID):
        if self.GetNumberofLinearFaceElements() > 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI3":
                    stream.write("CTRIA3  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}\n")                    
                elif element.type == "QUAD4":
                    stream.write("CQUAD4  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}\n")                    
                    
        if self.GetNumberofQuadraticFaceElements() > 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI6":
                    stream.write("CTRIA6  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n")                    
                elif element.type == "QUAD8":
                    stream.write("CQUAD8  ")
                    stream.write(f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n")
                    stream.write("+       ")
                    stream.write(f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n")                                                
    
    def WritetoNastranStreamLine(self, stream, pid, startNID, startEID):
        pass
    
    def WritetoNastranStreamPoint(self, stream, pid, startNID, startEID):
        pass
    
    def WritetoNastranKeyword(self, pid, startNID, startEID):
        nasString = ""
        nasString += self.WritetoNastranKeywordSolid(pid,startNID,startEID)
        nasString += self.WritetoNastranKeywordFace(pid,startNID,startEID)
        nasString += self.WritetoNastranKeywordLine(pid,startNID,startEID)
        nasString += self.WritetoNastranKeywordPoint(pid,startNID,startEID)
        return nasString
    
    def WritetoNastranKeywordSolid(self, pid, startNID, startEID):
        nasString = ""
        if self.GetNumberofLinearSolidElements() > 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA4":
                    formatString = "CTETRA  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id+startNID):>8}{str(element.nodes[1].id+startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}\n"
                    nasString += formatString
                elif element.type == "PENTA6":
                    formatString = "CPENTA  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n"
                    nasString += formatString
                elif element.type == "HEXA8":
                    formatString = "CHEXA   "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n"                    
                    formatString += "+       "
                    formatString += f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                    nasString += formatString
        if self.GetNumberofQuadraticSolidElements() > 0:
            for key in self.elements:
                element : SolidElement = self.elements[key] 
                if element.type == "TETRA10":
                    formatString = "CTETRA  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n"
                    formatString += "+       "
                    formatString += f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n"
                    nasString += formatString
                elif element.type == "HEXA20":
                    formatString = "CHEXA   "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n"
                    formatString += "+       "
                    formatString += f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}{str(element.nodes[10].id + startNID):>8}{str(element.nodes[11].id + startNID):>8}{str(element.nodes[12].id + startNID):>8}{str(element.nodes[13].id + startNID):>8}+\n"
                    formatString += "+       "
                    formatString += f"{str(element.nodes[14].id + startNID):>8}{str(element.nodes[15].id + startNID):>8}{str(element.nodes[16].id + startNID):>8}{str(element.nodes[17].id + startNID):>8}{str(element.nodes[18].id + startNID):>8}{str(element.nodes[19].id + startNID):>8}\n" 
                    nasString += formatString
        return nasString
    
    def WritetoNastranKeywordFace(self, pid, startNID, startEID):
        nasString = ""       
        if self.GetNumberofLinearFaceElements() > 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI3":
                    formatString = "CTRIA3  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}\n"
                    nasString += formatString
                elif element.type == "QUAD4":
                    formatString = "CQUAD4  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}\n"                    
                    nasString += formatString
                    
        if self.GetNumberofQuadraticFaceElements() > 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI6":
                    formatString = "CTRIA6  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n"
                    nasString += formatString
                elif element.type == "QUAD8":
                    formatString = "CQUAD8  "
                    formatString += f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}+\n"
                    formatString += "+       "
                    formatString += f"{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                    nasString += formatString
                    
        return nasString
                    
                
    
    def WritetoNastranKeywordLine(self, pid, startNID, startEID):
        nasString = ""       
        return nasString
    
    def WritetoNastranKeywordPoint(self, pid, startNID, startEID):
        nasString = ""  
        return nasString     
    
    def AddSetsfromDyna(self, dynaSets):
        if dynaSets[0] == "*SET_SHELL" or dynaSets[0] == "*SET_SHELL_LIST":
            firstline = dynaSets[1]
            sid = KooDynaInt(firstline[0])
            da1 = KooDynaFloat(firstline[1])
            da2 = KooDynaFloat(firstline[2])
            da3 = KooDynaFloat(firstline[3])
            da4 = KooDynaFloat(firstline[4])
            elemList = [] 
            for i in range(2, len(dynaSets)):
                for j in range(0, len(dynaSets[i])):
                    eid = KooDynaInt(dynaSets[i][j])
                    elemList.append(eid)
            name = "SET_SHELL_" + str(sid)
            aSet = self.CreateShellSetwithID(sid, name, da1, da2, da3, da4, elemList)
        if dynaSets[0] == "*SET_SHELL_TITLE":
            firstLine = dynaSets[1]
            name = firstLine[0]
            secondLine = dynaSets[2]
            sid = KooDynaInt(secondLine[0])
            da1 = KooDynaFloat(secondLine[1])
            da2 = KooDynaFloat(secondLine[2])
            da3 = KooDynaFloat(secondLine[3])
            da4 = KooDynaFloat(secondLine[4])
            elemList = []
            for i in range(3, len(dynaSets)):
                for j in range(0, len(dynaSets[i])):
                    eid = KooDynaInt(dynaSets[i][j])
                    elemList.append(eid)
            aSet = self.CreateShellSetwithID(sid, name, da1, da2, da3, da4, elemList)
        if dynaSets[0] == "*SET_SOLID":
            firstLine = dynaSets[1]
            sid = KooDynaInt(firstLine[0])
            solver = firstLine[1]
            elemList = []
            for i in range(2, len(dynaSets)):
                for j in range(0, len(dynaSets[i])):
                    eid = KooDynaInt(dynaSets[i][j])
                    elemList.append(eid)
            name = "SET_SOLID_" + str(sid)
            aSet = self.CreateSolidSetwithID(sid, name, solver, elemList)
        if dynaSets[0] == "*SET_SOLID_TITLE":
            firstLine = dynaSets[1]
            name = firstLine[0]
            secondLine = dynaSets[2]
            sid = KooDynaInt(secondLine[0])
            solver = secondLine[1]
            elemList = []
            for i in range(3, len(dynaSets)):
                for j in range(0, len(dynaSets[i])):
                    eid = KooDynaInt(dynaSets[i][j])
                    elemList.append(eid)
            aSet = self.CreateSolidSetwithID(sid, name, solver, elemList)
            print("Solid Set Created")
            
            
        
    def WritetoDynaKeyword(self, pid, startNID,startEID):
        dynaString = ""
        dynaString += self.WritetoDynaKeywordSolid(pid,startNID,startEID)
        dynaString += self.WritetoDynaKeywordFace(pid,startNID,startEID)
        dynaString += self.WritetoDynaKeywordLine(pid,startNID,startEID)
        dynaString += self.WritetoDynaKeywordPoint(pid,startNID,startEID)
               
        for aSetID in self.sets:
            aSet = self.sets[aSetID]
            dynaString += aSet.WritetoDynaKeyword(startEID)
        return dynaString
    
    def WriteStreamDynaKeyword(self, stream, pid, startNID, startEID):
        self.WriteStreamDynaKeywordSolid(stream, pid, startNID, startEID)
        self.WriteStreamDynaKeywordFace(stream, pid, startNID, startEID)
        self.WriteStreamDynaKeywordLine(stream, pid, startNID, startEID)
        self.WriteStreamDynaKeywordPoint(stream, pid, startNID, startEID)
        
        for aSetID in self.sets:
            aSet = self.sets[aSetID]
            aSet.WriteStreamDynaKeyword(stream, startEID)


    def WritetoDynaKeywordSolid(self, pid, startNID, startEID):
        dynaString = ""
        if self.GetNumberofLinearSolidElements() > 0:
            if self.TShellMode == True:
                dynaString += "*ELEMENT_TSHELL\n"
            else:
                dynaString += "*ELEMENT_SOLID\n"
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA4":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id+startNID):>8}{str(element.nodes[1].id+startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}\n"
                    dynaString += formatString
                elif element.type == "PENTA6":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n"
                    dynaString += formatString
                elif element.type == "HEXA8":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                    dynaString += formatString
        if self.GetNumberofQuadraticSolidElements() > 0:
            dynaString += "*ELEMENT_SOLID\n"       
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA10":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}\n"
                    formatString += f"{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n"
                    dynaString += formatString
                elif element.type == "HEXA20":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}\n"
                    formatString += f"{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n"
                    formatString += f"{str(element.nodes[10].id + startNID):>8}{str(element.nodes[11].id + startNID):>8}{str(element.nodes[12].id + startNID):>8}{str(element.nodes[13].id + startNID):>8}{str(element.nodes[14].id + startNID):>8}{str(element.nodes[15].id + startNID):>8}{str(element.nodes[16].id + startNID):>8}{str(element.nodes[17].id + startNID):>8}{str(element.nodes[18].id + startNID):>8}{str(element.nodes[19].id + startNID):>8}\n"
                    dynaString += formatString
        return dynaString
    
    def WriteStreamDynaKeywordSolid(self, stream, pid, startNID, startEID):
        if self.GetNumberofLinearSolidElements() > 0:
            if self.TShellMode == True:
                stream.write("*ELEMENT_TSHELL\n")
            else:
                stream.write("*ELEMENT_SOLID\n")
            try:
                for key in self.elements:
                    element : SolidElement = self.elements[key]
                    if element.type == "TETRA4":
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id+startNID):>8}{str(element.nodes[1].id+startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}{str(element.nodes[3].id+startNID):>8}\n"
                        stream.write(formatString)
                    elif element.type == "PENTA6":
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}\n"
                        stream.write(formatString)
                    elif element.type == "HEXA8":
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                        stream.write(formatString)
            except:
                pass
        if self.GetNumberofQuadraticSolidElements() > 0:
            stream.write("*ELEMENT_SOLID\n")       
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA10":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}\n"
                    stream.write(formatString)
                    formatString = f"{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n"
                    stream.write(formatString)
                elif element.type == "HEXA20":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}\n"
                    stream.write(formatString)
                    formatString = f"{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}{str(element.nodes[8].id + startNID):>8}{str(element.nodes[9].id + startNID):>8}\n"
                    stream.write(formatString)
                    formatString = f"{str(element.nodes[10].id + startNID):>8}{str(element.nodes[11].id + startNID):>8}{str(element.nodes[12].id + startNID):>8}{str(element.nodes[13].id + startNID):>8}{str(element.nodes[14].id + startNID):>8}{str(element.nodes[15].id + startNID):>8}{str(element.nodes[16].id + startNID):>8}{str(element.nodes[17].id + startNID):>8}{str(element.nodes[18].id + startNID):>8}{str(element.nodes[19].id + startNID):>8}\n"
                    stream.write(formatString)
                    
    def WritetoDynaKeywordFace(self, pid, startNID, startEID):
        dynaString = ""         
        if self.GetNumberofLinearFaceElements() > 0:
            dynaString += "*ELEMENT_SHELL\n"
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI3":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(0):>8}{str(0):>8}{str(0):>8}{str(0):>8}\n"
                    dynaString += formatString
                elif element.type == "QUAD4":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(0):>8}{str(0):>8}{str(0):>8}{str(0):>8}\n"
                    dynaString += formatString
        
        if self.GetNumberofQuadraticFaceElements() > 0:
            dynaString += "*ELEMENT_SHELL\n"
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI6":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(0):>8}{str(0):>8}\n"
                    dynaString += formatString
                elif element.type == "QUAD8":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                    dynaString += formatString
        return dynaString
    
    def WriteStreamDynaKeywordFace(self, stream, pid, startNID, startEID):
        if self.GetNumberofLinearFaceElements() > 0:
            stream.write("*ELEMENT_SHELL\n")
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI3":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[2].id+startNID):>8}{str(0):>8}{str(0):>8}{str(0):>8}{str(0):>8}\n"
                    stream.write(formatString)
                elif element.type == "QUAD4":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(0):>8}{str(0):>8}{str(0):>8}{str(0):>8}\n"
                    stream.write(formatString)
        
        if self.GetNumberofQuadraticFaceElements() > 0:
            stream.write("*ELEMENT_SHELL\n")
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI6":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(0):>8}{str(0):>8}\n"
                    stream.write(formatString)
                elif element.type == "QUAD8":
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.nodes[3].id + startNID):>8}{str(element.nodes[4].id + startNID):>8}{str(element.nodes[5].id + startNID):>8}{str(element.nodes[6].id + startNID):>8}{str(element.nodes[7].id + startNID):>8}\n"
                    stream.write(formatString)

    def WritetoDynaKeywordLine(self, pid, startNID, startEID):
        dynaString = ""
        if self.GetNumberofLinearLineElements() > 0:
            dynaString += "*ELEMENT_BEAM\n"
            for key in self.elements:
                element : LineElement = self.elements[key]
                if element.type == "LINE2":
                    nullStr = "        "
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{nullStr}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    dynaString += formatString                    
        if self.GetNumberofQuadraticLineElements() > 0:
            dynaString += "*ELEMENT_BEAM\n"
            for key in self.elements:
                element : LineElement = self.elements[key]
                if element.type == "LINE3":
                    if element.nodes[2] == 0:
                        nullStr = "        "
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{nullStr}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    else:
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    dynaString += formatString
        return dynaString

    def WriteStreamDynaKeywordLine(self, stream, pid, startNID, startEID):
        if self.GetNumberofLinearLineElements() > 0:
            stream.write("*ELEMENT_BEAM\n")             
            for key in self.elements:
                element : LineElement = self.elements[key]
                if element.type == "LINE2":
                    nullStr = "        "
                    formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{nullStr}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    stream.write(formatString)
        if self.GetNumberofQuadraticLineElements() > 0:
            stream.write("*ELEMENT_BEAM\n")
            for key in self.elements:
                element : LineElement = self.elements[key]
                if element.type == "LINE3":
                    if element.nodes[2].id == 0:
                        nullStr = "        "
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{nullStr}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    else:
                        formatString = f"{str(element.id + startEID):>8}{str(pid):>8}{str(element.nodes[0].id + startNID):>8}{str(element.nodes[1].id + startNID):>8}{str(element.nodes[2].id + startNID):>8}{str(element.constraints[0]):>8}{str(element.constraints[1]):>8}{str(element.constraints[2]):>8}{str(element.constraints[3]):>8}{str(element.local):>8}\n"
                    stream.write(formatString)
    
    def WritetoDynaKeywordPoint(self, pid, startNID, startEID):
        dynaString = ""
        if self.GetNumberofPointElements() > 0:
            i = 0
            for key in self.elements:
                element : PointElement = self.elements[key]
                if element.type == "POINT":
                    # mass characters exponent has 8 characters
                    i = i + 1
                    if i == 1:
                        dynaString += "*ELEMENT_MASS\n"
                    massStr = _format_mass8(element.mass)
                    ePid = getattr(element, "pid", 0) or pid
                    formatString = f"{str(element.id + startEID):>8}{str(element.nodes[0].id + startNID):>8}{massStr:>8}{str(ePid):>8}\n"
                    dynaString += formatString
            i = 0
            for key in self.elements:
                element : PointElement = self.elements[key]
                if element.type == "POINT_NSET":
                    i = i + 1
                    if i == 1:
                        dynaString += "*ELEMENT_MASS_NODE_SET\n"
                    massStr = _format_mass8(element.mass)
                    ePid = getattr(element, "pid", 0) or pid
                    formatString = f"{str(element.id + startEID):>8}{str(element.nsid):>8}{massStr:>8}{str(ePid):>8}\n"
                    dynaString += formatString
        return dynaString

    def WriteStreamDynaKeywordPoint(self, stream, pid, startNID, startEID):
        if self.GetNumberofPointElements() > 0:
            i = 0
            for key in self.elements:
                element : PointElement = self.elements[key]
                if element.type == "POINT":
                    i = i + 1
                    if i == 1:
                        stream.write("*ELEMENT_MASS\n")
                    massStr = _format_mass8(element.mass)
                    ePid = getattr(element, "pid", 0) or pid
                    formatString = f"{str(element.id + startEID):>8}{str(element.nodes[0].id + startNID):>8}{massStr:>8}{str(ePid):>8}\n"
                    stream.write(formatString)
            i = 0
            for key in self.elements:
                element : PointElement = self.elements[key]
                if element.type == "POINT_NSET":
                    i = i + 1
                    if i == 1:
                        stream.write("*ELEMENT_MASS_NODE_SET\n")
                    massStr = _format_mass8(element.mass)
                    ePid = getattr(element, "pid", 0) or pid
                    formatString = f"{str(element.id + startEID):>8}{str(element.nsid):>8}{massStr:>8}{str(ePid):>8}\n"
                    stream.write(formatString)
                    
            
                    
    def WritetoAnsysAPDL(self, pid, startNID, startEID):
        ansysString = ""
        ansysString += self.WritetoAnsysAPDLSolidHexa20(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLSolidHexa8(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLSolidPenta6(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLSolidTetra10(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLSolidTetra4(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLFaceLinear(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLFaceQuadratic(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLLine(pid,startNID,startEID)
        ansysString += self.WritetoAnsysAPDLPoint(pid,startNID,startEID)
        return ansysString
    
    def WritetoAnsysAPDLSolidTetra4(self, pid, startNID, startEID):
        ansysString = ""
        numTetra4Solid = self.GetNumberofTetra4Elements()
        if numTetra4Solid != 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA4":
                    ansysString += element.GenerateAnsysAPDLKeyword()        
        return ansysString

    def WritetoAnsysAPDLSolidTetra10(self, pid, startNID, startEID):
        ansysString = ""
        numTetra10Solid = self.GetNumberofTetra10Elements()
        if numTetra10Solid != 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "TETRA10":
                    ansysString += element.GenerateAnsysAPDLKeyword()        
        return ansysString

    def WritetoAnsysAPDLSolidPenta6(self, pid, startNID, startEID):
        ansysString = ""
        numPenta6Solid = self.GetNumberofPenta6Elements()
        if numPenta6Solid != 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "PENTA6":
                    ansysString += element.GenerateAnsysAPDLKeyword()        
        return ansysString

    def WritetoAnsysAPDLSolidHexa8(self, pid, startNID, startEID):
        ansysString = ""
        numHexa8Solid = self.GetNumberofHexa8Elements()
        if numHexa8Solid != 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "HEXA8":
                    ansysString += element.GenerateAnsysAPDLKeyword()        
        return ansysString

    def WritetoAnsysAPDLSolidHexa20(self, pid, startNID, startEID):
        ansysString = ""
        numHexa20Solid = self.GetNumberofHexa20Elements()
        if numHexa20Solid != 0:
            for key in self.elements:
                element : SolidElement = self.elements[key]
                if element.type == "HEXA20":
                    ansysString += element.GenerateAnsysAPDLKeyword()        
        return ansysString 

    def WritetoAnsysAPDLFaceLinear(self, pid, startNID, startEID):
        ansysString = ""
        numLinearFace = self.GetNumberofLinearFaceElements()
        if numLinearFace != 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI3":
                    ansysString += element.GenerateAnsysAPDLKeyword()
                elif element.type == "QUAD4":
                    ansysString += element.GenerateAnsysAPDLKeyword()            
        return ansysString
    
    def WritetoAnsysAPDLFaceQuadratic(self, pid, startNID, startEID):        
        numQuadraticFace = self.GetNumberofQuadraticFaceElements()
        ansysString = ""        
        numQuadraticFace = self.GetNumberofQuadraticFaceElements()
        if numQuadraticFace != 0:
            for key in self.elements:
                element : FaceElement = self.elements[key]
                if element.type == "TRI6":
                    ansysString += element.GenerateAnsysAPDLKeyword()
                elif element.type == "QUAD8":
                    ansysString += element.GenerateAnsysAPDLKeyword()
        return ansysString

    def WritetoAnsysAPDLLine(self, pid, startNID, startEID):        
        # developing
        pass

    def WritetoAnsysAPDLPoint(self, pid, startNID, startEID):
        ansysString = ""
        if self.GetNumberofPointElements() > 0:
            firstElement : PointElement = self.elements[next(iter(self.elements))]
            massX = firstElement.mass
            if firstElement.massY != 0.0:
                massY = firstElement.massY
            else:
                massY = massX

            if firstElement.massZ != 0.0:
                massZ = firstElement.massZ
            else:
                massZ = massX
            
            ansysString += "R,{pid},{massX},{massY},{massZ}\n".format(pid=pid,massX=massX,massY=massY,massZ=massZ)
            ansysString += "TYPE,{pid}\n".format(pid=pid)
            ansysString += "REAL,{pid}\n".format(pid=pid)

            for key in self.elements:
                element : PointElement = self.elements[key]
                if element.type == "POINT":
                    formatString = "E,{nid}\n".format(nid = element.nodes[0].id + startNID)
                    ansysString += formatString
        
        return ansysString


    def WritetoABAQUSSolid(self, pid, startNID, startEID):
        pass    

    def WritetoABAQUSTri3(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=S3,ELSET=PART_Tri3_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                formatString = "{eid},{n1},{n2},{n3}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamTri3(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=S3,ELSET=PART_Tri3_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI3":
                formatString = "{eid},{n1},{n2},{n3}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID)
                stream.write(formatString)
    
    def WritetoABAQUSTri6(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=S6,ELSET=PART_Tri6_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI6":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamTri6(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=S6,ELSET=PART_Tri6_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "TRI6":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID)
                stream.write(formatString)
    
    def WritetoABAQUSQuad4(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=S4,ELSET=PART_Quad4_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "QUAD4":
                formatString = "{eid},{n1},{n2},{n3},{n4}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamQuad4(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=S4,ELSET=PART_Quad4_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "QUAD4":
                formatString = "{eid},{n1},{n2},{n3},{n4}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID)
                stream.write(formatString)
    
    def WritetoABAQUSQuad8(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=S8,ELSET=PART_Quad8_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "QUAD8":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamQuad8(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=S8,ELSET=PART_Quad8_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : FaceElement = self.elements[key]
            if element.type == "QUAD8":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID)
                stream.write(formatString)
    
    def WritetoABAQUSTetra4(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=C3D4,ELSET=PART_Tetra4_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "TETRA4":
                formatString = "{eid},{n1},{n2},{n3},{n4}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID)
                abaqusString += formatString
        return abaqusString 
    
    def WritetoABAQUSStreamTetra4(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=C3D4,ELSET=PART_Tetra4_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "TETRA4":
                formatString = "{eid},{n1},{n2},{n3},{n4}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID)
                stream.write(formatString)
    
    def WritetoABAQUSTetra10(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=C3D10,ELSET=PART_Tetra10_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "TETRA10":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID,n9=element.nodes[8].id+startNID,n10=element.nodes[9].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamTetra10(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=C3D10,ELSET=PART_Tetra10_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "TETRA10":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID,n9=element.nodes[8].id+startNID,n10=element.nodes[9].id+startNID)
                stream.write(formatString)

    def WritetoABAQUSPenta6(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=C3D6,ELSET=PART_Penta6_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "PENTA6":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID)
                abaqusString += formatString
        return abaqusString

    def WritetoABAQUSStreamPenta6(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=C3D6,ELSET=PART_Penta6_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "PENTA6":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID)
                stream.write(formatString)

    def WritetoABAQUSHexa8(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=C3D8,ELSET=PART_Hexa8_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "HEXA8":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID)
                abaqusString += formatString
        return abaqusString
    
    def WritetoABAQUSStreamHexa8(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=C3D8,ELSET=PART_Hexa8_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "HEXA8":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID)
                stream.write(formatString)

    def WritetoABAQUSHexa20(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += "*ELEMENT,TYPE=C3D20,ELSET=PART_Hexa20_{pid}\n".format(pid=pid)
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "HEXA20":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10},{n11},{n12},{n13},{n14},{n15},{n16},{n17},{n18},{n19},{n20}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID,n9=element.nodes[8].id+startNID,n10=element.nodes[9].id+startNID,n11=element.nodes[10].id+startNID,n12=element.nodes[11].id+startNID,n13=element.nodes[12].id+startNID,n14=element.nodes[13].id+startNID,n15=element.nodes[14].id+startNID,n16=element.nodes[15].id+startNID,n17=element.nodes[16].id+startNID,n18=element.nodes[17].id+startNID,n19=element.nodes[18].id+startNID,n20=element.nodes[19].id+startNID)
                abaqusString += formatString
        return abaqusString    
    
    def WritetoABAQUSStreamHexa20(self, stream, pid, startNID, startEID):
        stream.write("*ELEMENT,TYPE=C3D20,ELSET=PART_Hexa20_{pid}\n".format(pid=pid))
        for key in self.elements:
            element : SolidElement = self.elements[key]
            if element.type == "HEXA20":
                formatString = "{eid},{n1},{n2},{n3},{n4},{n5},{n6},{n7},{n8},{n9},{n10},{n11},{n12},{n13},{n14},{n15},{n16},{n17},{n18},{n19},{n20}\n".format(eid=element.id+startEID,n1=element.nodes[0].id+startNID,n2=element.nodes[1].id+startNID,n3=element.nodes[2].id+startNID,n4=element.nodes[3].id+startNID,n5=element.nodes[4].id+startNID,n6=element.nodes[5].id+startNID,n7=element.nodes[6].id+startNID,n8=element.nodes[7].id+startNID,n9=element.nodes[8].id+startNID,n10=element.nodes[9].id+startNID,n11=element.nodes[10].id+startNID,n12=element.nodes[11].id+startNID,n13=element.nodes[12].id+startNID,n14=element.nodes[13].id+startNID,n15=element.nodes[14].id+startNID,n16=element.nodes[15].id+startNID,n17=element.nodes[16].id+startNID,n18=element.nodes[17].id+startNID,n19=element.nodes[18].id+startNID,n20=element.nodes[19].id+startNID)
                stream.write(formatString)                

    def WritetoABAQUS(self, pid, startNID, startEID):
        abaqusString = ""
        abaqusString += self.WritetoABAQUSTetra4(pid,startNID,startEID)
        abaqusString += self.WritetoABAQUSTetra10(pid,startNID,startEID)
        abaqusString += self.WritetoABAQUSPenta6(pid,startNID,startEID)
        abaqusString += self.WritetoABAQUSHexa8(pid,startNID,startEID)
        abaqusString += self.WritetoABAQUSHexa20(pid,startNID,startEID)
        return abaqusString
    
    def WritetoABAQUSStream(self, stream, pid, startNID, startEID):
        self.WritetoABAQUSStreamTetra4(stream,pid,startNID,startEID)
        self.WritetoABAQUSStreamTetra10(stream,pid,startNID,startEID)
        self.WritetoABAQUSStreamPenta6(stream,pid,startNID,startEID)
        self.WritetoABAQUSStreamHexa8(stream,pid,startNID,startEID)
        self.WritetoABAQUSStreamHexa20(stream,pid,startNID,startEID)
    
    def GetExternalObjString(self):
        boundaries = self.GetExternalBoundary(True)
        nodes ={}
        i = 1 
        for boundary in boundaries:
            for node in boundary:
                if node not in nodes:
                    nodes[node] = i
                    i += 1
        objString = ""
        for key in nodes:
            node = self.nodeManager.nodes[key]
            objString += "v {x} {y} {z}\n".format(x=node.x,y=node.y,z=node.z)
        
        for boundary in boundaries:
            objString += "f"
            for node in boundary:
                objString += " {i}".format(i=nodes[node])
            objString += "\n"
        return objString 
    
    def GetExternalTriBoundary(self):
        boundaries = self.GetExternalBoundary(True)
        
        external_tri_boundaries = {}
        ith = 0 
        for boundary in boundaries:            
            if len(boundary) == 3:
                external_tri_boundaries[ith] = boundary
                ith += 1
            elif len(boundary) == 4:
                external_tri_boundaries[ith] = [boundary[0], boundary[1], boundary[2]]
                ith += 1
                external_tri_boundaries[ith] = [boundary[0], boundary[2], boundary[3]]
                ith += 1
        return external_tri_boundaries                            
            
    def GetExternalBoundary(self, sortedBoundary = False):
        boundaries = [] 
        for key in self.elements:
            element = self.elements[key]
            if len(element.boundaries) == 0:
                element.SetBoundaries()
            boundaries.extend(element.boundaries)            
            
        '''# count duplicates, but keep the order of the nodes in the boundary
        boundary = [tuple(b) for b in boundaries]
        boundary_reverse = [tuple(reversed(b)) for b in boundaries]
        boundary_counts = Counter(boundary + boundary_reverse)
        unique_boundaries = [list(b) for b, count in boundary_counts.items() if count == 2]
        # first half 
        len_unique_boundaries = int(len(unique_boundaries)/2)
        unique_boundaries = unique_boundaries[1:len_unique_boundaries]'''
        
        boundary_counts = Counter(tuple(sorted(b)) for b in boundaries)
        
        
        unique_boundaries = [tuple(list(b)) for b, count in boundary_counts.items() if count == 1]
        #unique_boundaries_set = {tuple(sorted(boundary)) for boundary in unique_boundaries}

        # find original boundaries from the unique boundaries
        
        
        
        if sortedBoundary == True:
            # Step 3: Create a mapping from sorted boundaries to their original (unsorted) versions
            boundary_map = {tuple(sorted(b)): b for b in boundaries}
            
            # Step 4: Retrieve the original boundaries using the unique boundaries and the map
            original_boundaries = [boundary_map[b] for b in unique_boundaries if b in boundary_map]

            '''original_boundaries = []
            # allocate memory
            boundary_sorted = [tuple(sorted(b)) for b in boundaries]                           
            for boundary in unique_boundaries:
                if boundary in boundary_sorted:
                    ith = boundary_sorted.index(boundary)
                    curBoundary_not_sorted =  boundaries[ith]
                    original_boundaries.append(curBoundary_not_sorted)'''
            #for boundary in boundaries:
            #    boundarysorted = tuple(sorted(boundary))
            #    if boundarysorted in unique_boundaries:
            #        original_boundaries.append(boundary)                                 
            print(f"Number of unsorted external boundaries: {len(original_boundaries)} (Part {self.elementManagerID}, {len(self.elements)} elements)")
            return original_boundaries
        else:
            print(f"Number of external boundaries: {len(unique_boundaries)} (Part {self.elementManagerID}, {len(self.elements)} elements)")
            return unique_boundaries
    
    def GetExternalNodes(self):
        boundaries = self.GetExternalBoundary()
        external_nodes = []
        for boundary in boundaries:
            external_nodes.extend(boundary) 
        
        # count the number of times each node appears in the external boundary
        boundary_node_counts = Counter(external_nodes)
        # remove duplicates
        unique_external_nodes = [b for b, count in boundary_node_counts.items()]
                
        print("Number of external nodes: ", len(unique_external_nodes))
        
        #boundary_node_counts = Counter(tuple(sorted(b)) for b in external_nodes)
        #unique_external_nodes = [list(b) for b, count in boundary_node_counts.items() if count == 1]
        #print("Number of external nodes: ", len(unique_external_nodes))
        unique_external_nodes = self.nodeManager.FindNodesfromIDs(unique_external_nodes)
        return unique_external_nodes
    
    def GetExternalBoundariesandNodeDict(self, sortedBoundary = True):
        boundaries  = self.GetExternalBoundary(sortedBoundary)
        external_nodes = []
        for boundary in boundaries:
            external_nodes.extend(boundary)
        boundary_node_counts = Counter(external_nodes)
        unique_external_nodes = [b for b, count in boundary_node_counts.items()]                
        print("Number of external nodes: ", len(unique_external_nodes))        
        unique_external_nodes = self.nodeManager.FindSubNodeDictfromIDs(unique_external_nodes)
        return boundaries, unique_external_nodes
    
    def GetExternalNodeCoordinates(self):
        poly_faces = self.GetExternalBoundary(False)
        nodeMan = self.nodeManager
        node_segments = [] 
        for face in poly_faces:
            curSegment = [] 
            if len(face) == 3:
                n1 = nodeMan.GetNode(face[0])
                n2 = nodeMan.GetNode(face[1])
                n3 = nodeMan.GetNode(face[2])
                curSegment.append(np.array([n1.x, n1.y, n1.z]))
                curSegment.append(np.array([n2.x, n2.y, n2.z]))
                curSegment.append(np.array([n3.x, n3.y, n3.z]))                                
            elif len(face) == 4:
                n1 = nodeMan.GetNode(face[0])
                n2 = nodeMan.GetNode(face[1])
                n3 = nodeMan.GetNode(face[2])
                n4 = nodeMan.GetNode(face[3])
                curSegment.append(np.array([n1.x, n1.y, n1.z]))
                curSegment.append(np.array([n2.x, n2.y, n2.z]))
                curSegment.append(np.array([n3.x, n3.y, n3.z]))
                curSegment.append(np.array([n4.x, n4.y, n4.z]))
            node_segments.append(curSegment)
        return node_segments
    
    def GetElementNodes(self):
        nodes = {}
        for key in self.elements:
            element = self.elements[key]
            for node in element.nodes:
                nodes[node.id] = node
        return nodes        
    
    def GetElementNodesIncludingExternalElements(self, nodes = {}):
        if len(nodes) == 0:
            nodes = self.GetElementNodes()
        
        shared_nodes = {}
        for key in nodes:
            node = nodes[key]
            for elemID in node.elems:
                if elemID not in self.elements:
                    shared_nodes[key] = node
                    break
        return shared_nodes
    
    def GetBoundaryBox(self):
        #nodes = self.nodeManager.nodes
        # dict to listt 
        #nodes = list(nodes.values())
        nodes = [] 
        for eid in self.elements:
            element = self.elements[eid]
            for node in element.nodes:
                nodes.append(node)
        return self.GetBoundaryBoxfromNodes(nodes)        
    
    def GetBoundaryBoxfromNodes(self, nodes):
        if not nodes:
            return 0, 0, 0, 0, 0, 0
        coords = np.array([[node.x, node.y, node.z] for node in nodes])
        xmin, ymin, zmin = np.min(coords, axis=0)
        xmax, ymax, zmax = np.max(coords, axis=0)
        return xmin, xmax, ymin, ymax, zmin, zmax
        '''x = []
        y = []
        z = []
        for node in nodes:
            x.append(node.x)
            y.append(node.y)
            z.append(node.z)
        return min(x),max(x),min(y),max(y),min(z),max(z)'''

    def GetBoundaryElements(self):
        boundaries = self.GetExternalBoundary(True)
        elements = {}
        for eid in self.elements:
            element = self.elements[eid]
            for bd in element.boundaries:
                if bd in boundaries:
                    if eid not in elements:
                        elements[eid] = 1
                    else:
                        elements[eid] += 1
        return elements
    
    def SetBoundaryNodes(self):
        boundaries = self.GetExternalBoundary(False)
        self.boundaryNodes = {}
        for boundary in boundaries:
            for nodeid in boundary:
                if nodeid not in self.boundaryNodes:
                    self.boundaryNodes[nodeid] = self.nodeManager.nodes[nodeid] 

    def GetBoundaryNodesWithVectorwithAngle(self, zVec, angle):
        boundaries = self.GetExternalBoundary(True)
        nodes = {}
        for boundary in boundaries:
            if len(boundary) >=3:
                n1 = self.nodeManager.nodes[boundary[0]]
                n2 = self.nodeManager.nodes[boundary[1]]
                n3 = self.nodeManager.nodes[boundary[2]]
                v1 = np.array([n2.x - n1.x, n2.y - n1.y, n2.z - n1.z])
                v2 = np.array([n3.x - n1.x, n3.y - n1.y, n3.z - n1.z])
                v1 = v1/np.linalg.norm(v1)
                v2 = v2/np.linalg.norm(v2)
                v3 = np.cross(v1, v2)
                v3 = v3/np.linalg.norm(v3)
                
                anglev3tozVec = np.arccos(np.dot(v3, zVec))
                if np.degrees(anglev3tozVec) < angle:
                    for nodeid in boundary:
                        if nodeid not in nodes:
                            nodes[nodeid] = self.nodeManager.nodes[nodeid]
                        
        return nodes
                            
                    
    
    def GetBoundariesOnLocation(self, location, tolerance = 1e-6):
        boundaries = self.GetExternalBoundary(True)
        minX, maxX, minY, maxY, minZ, maxZ = self.GetBoundaryBox()
        newBoundaries = []            
        
        if location.lower() == "top":
            if maxZ - minZ < tolerance:
                pass
            else:
                tolerance = tolerance/(maxZ - minZ)
            
            for boundary in boundaries:
                
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.z - maxZ) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
        if location.lower() == "bottom":
            if maxZ - minZ < tolerance:
                pass
            else:
                tolerance = tolerance/(maxZ - minZ)
            for boundary in boundaries:
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.z - minZ) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
        if location.lower() == "left":
            if maxX - minX < tolerance:
                pass
            else:
                tolerance = tolerance/(maxX - minX)
            for boundary in boundaries:
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.x - minX) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
        if location.lower() == "right":
            if maxX - minX < tolerance:
                pass
            else:
                tolerance = tolerance/(maxX - minX)
            for boundary in boundaries:
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.x - maxX) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
        if location.lower() == "front":
            if maxY - minY < tolerance:
                pass
            else:
                tolerance = tolerance/(maxY - minY)
            for boundary in boundaries:
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.y - minY) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
        if location.lower() == "back":
            if maxY - minY < tolerance:
                pass
            else:
                tolerance = tolerance/(maxY - minY)
            for boundary in boundaries:
                curBoundaries = []            
                for nodeid in boundary:
                    node = self.nodeManager.nodes[nodeid]
                    if abs(node.y - maxY) > tolerance:                        
                        break
                    else:
                        curBoundaries.append(nodeid)
                if len(curBoundaries) == len(boundary):
                    newBoundaries.append(boundary)
                    
        return newBoundaries
            
    def GetNodesOnLocation(self, location, tolerance = 1e-6):
        nodes = self.GetExternalNodes()
        minX, maxX, minY, maxY, minZ, maxZ = self.GetBoundaryBoxfromNodes(nodes)
        newNodes = [] 
        
        if location.lower() == "top":
            if maxZ - minZ < tolerance:
                pass
            else:
                tolerance = tolerance/(maxZ - minZ)
            for node in nodes:
                if abs(node.z - maxZ) < tolerance:
                    newNodes.append(node)
        elif location.lower() == "bottom":
            if maxZ - minZ < tolerance:
                pass
            else:
                tolerance = tolerance/(maxZ - minZ)
            for node in nodes:
                if abs(node.z - minZ) < tolerance:
                    newNodes.append(node)
        elif location.lower() == "left":
            if maxX - minX < tolerance:
                pass
            else:
                tolerance = tolerance/(maxX - minX)                                
            for node in nodes:
                if abs(node.x - minX) < tolerance:
                    newNodes.append(node)
        elif location.lower() == "right":
            if maxX - minX < tolerance:
                pass
            else:
                tolerance = tolerance/(maxX - minX)                
            for node in nodes:
                if abs(node.x - maxX) < tolerance:
                    newNodes.append(node)
        elif location.lower() == "front":
            if maxY - minY < tolerance:
                pass
            else:
                tolerance = tolerance/(maxY - minY)
            for node in nodes:
                if abs(node.y - minY) < tolerance:
                    newNodes.append(node)
        elif location.lower() == "back":
            if maxY - minY < tolerance:
                pass
            else:
                tolerance = tolerance/(maxY - minY)                
            for node in nodes:
                if abs(node.y - maxY) < tolerance:
                    newNodes.append(node)
        return newNodes
    
    def FindFarthestNodes(self, direction):
        nodes = self.GetExternalNodes()
        minDotProduct = 1e99
        maxDocProduct = -1e99
        minNode = None
        maxNode = None
        for node in nodes:
            innerProduct = node.x*direction[0] + node.y*direction[1] + node.z*direction[2]
            if innerProduct < minDotProduct:
                minDotProduct = innerProduct
                minNode = node
            if innerProduct > maxDocProduct:
                maxDocProduct = innerProduct
                maxNode = node

        return minNode, maxNode
    
    def CreateStructuredMesh(self, minPoint, xDirection, yDirection, zDirection, xLength, yLength, zLength, numX, numY, numZ):
        dx = xLength / numX
        dy = yLength / numY
        dz = zLength / numZ
        
        nodesTensor = [] 
        for i in range(numX + 1):
            nodesMat = [] 
            for j in range(numY + 1):
                nodesVec = [] 
                for k in range(numZ + 1):
                    x = minPoint + i * dx * xDirection + j * dy * yDirection + k * dz * zDirection
                    node : Node = self.nodeManager.CreateNode(x[0], x[1], x[2])
                    self.nodeManager.AddNode(node)
                    nodesVec.append(node)
                nodesMat.append(nodesVec)
            nodesTensor.append(nodesMat)
        
        # create elements
        for i in range(numX):
            for j in range(numY):
                for k in range(numZ):
                    n1 = nodesTensor[i][j][k]
                    n2 = nodesTensor[i + 1][j][k]
                    n3 = nodesTensor[i + 1][j + 1][k]
                    n4 = nodesTensor[i][j + 1][k]
                    n5 = nodesTensor[i][j][k + 1]
                    n6 = nodesTensor[i + 1][j][k + 1]
                    n7 = nodesTensor[i + 1][j + 1][k + 1]
                    n8 = nodesTensor[i][j + 1][k + 1]
                    self.CreateHexahedronLinearElement(n1, n2, n3, n4, n5, n6, n7, n8)
    
    def CreateStructuredMeshWithFillet(
        self,
        minPoint, xDirection, yDirection, zDirection,
        xLength, yLength, zLength,
        numX, numY, numZ,
        R,                    # fillet radius (same unit as length)
        smooth_iters=10,      # Laplacian smoothing iterations for interior
        lam=0.5               # smoothing strength (0~1)
    ):
        """
        - 외곽은 R 필렛 형태로 스무싱
        - 내부는 라플라시안 스무딩 (경계 고정)
        - Node: node.x, node.y, node.z 접근 가능
        """
        import math

        # 1) 기본 격자 생성 (원본 함수와 동일)
        dx = xLength / numX
        dy = yLength / numY
        dz = zLength / numZ

        nodesTensor = []
        for i in range(numX + 1):
            nodesMat = []
            for j in range(numY + 1):
                nodesVec = []
                for k in range(numZ + 1):
                    # 물리 좌표
                    x = minPoint + i * dx * xDirection + j * dy * yDirection + k * dz * zDirection
                    node = self.nodeManager.CreateNode(x[0], x[1], x[2])
                    self.nodeManager.AddNode(node)
                    nodesVec.append(node)
                nodesMat.append(nodesVec)
            nodesTensor.append(nodesMat)

        # 편의를 위해 로컬 직육면체 좌표계를 하나 더 유지 (u,v,w in [0, Lx/Ly/Lz])
        # minPoint를 원점(0,0,0)으로, xDirection/yDirection/zDirection을 직교단위벡터라고 가정
        # (이미 그렇다고 가정하신 듯한 코드라 그대로 씀)
        def to_local(i,j,k):
            ux = i * dx
            uy = j * dy
            uz = k * dz
            return ux, uy, uz

        def set_from_local(i,j,k, ux,uy,uz):
            # 물리 좌표 = minPoint + ux*xDir + uy*yDir + uz*zDir
            px = minPoint + ux * xDirection + uy * yDirection + uz * zDirection
            n = nodesTensor[i][j][k]
            n.x, n.y, n.z = px[0], px[1], px[2]

        Lx, Ly, Lz = xLength, yLength, zLength
        # 축별 “필렛 기준선” (면에서 R만큼 들어온 위치)
        xR0, xR1 = R, Lx - R
        yR0, yR1 = R, Ly - R
        zR0, zR1 = R, Lz - R

        # 2) 바깥 경계 + 엣지/코너 필렛 처리
        #    규칙:
        #    - 면(i=0 or numX): 해당 축 좌표를 R로 클램프(반대쪽은 L-R로)
        #    - 엣지: 두 축 모두 필렛 구간이면 1/4 원/원통 투영
        #    - 코너: 세 축 모두 필렛 구간이면 R-구면으로 투영
        for i in range(numX + 1):
            for j in range(numY + 1):
                for k in range(numZ + 1):
                    is_x_face_min = (i == 0)
                    is_x_face_max = (i == numX)
                    is_y_face_min = (j == 0)
                    is_y_face_max = (j == numY)
                    is_z_face_min = (k == 0)
                    is_z_face_max = (k == numZ)

                    # 경계가 아니면 일단 패스 (내부는 나중에 스무딩)
                    if not (is_x_face_min or is_x_face_max or is_y_face_min or is_y_face_max or is_z_face_min or is_z_face_max):
                        continue

                    ux, uy, uz = to_local(i,j,k)

                    # 각 축에 대해 "면 안쪽으로 R 클램프" (필렛 구간 안이면 R선으로 당김)
                    # 단, 어느 면에 붙었는지에 따라 기준선을 선택
                    if is_x_face_min and ux < xR0: ux = xR0
                    if is_x_face_max and ux > xR1: ux = xR1
                    if is_y_face_min and uy < yR0: uy = yR0
                    if is_y_face_max and uy > yR1: uy = yR1
                    if is_z_face_min and uz < zR0: uz = zR0
                    if is_z_face_max and uz > zR1: uz = zR1

                    # 엣지/코너 투영(필렛 원/구면)
                    # 어떤 쪽 경계인지에 따라 원/구면의 "센터"가 결정됨
                    cx = xR0 if is_x_face_min else (xR1 if is_x_face_max else None)
                    cy = yR0 if is_y_face_min else (yR1 if is_y_face_max else None)
                    cz = zR0 if is_z_face_min else (zR1 if is_z_face_max else None)

                    # 세 축 중 몇 개가 경계인지
                    face_count = (1 if cx is not None else 0) + (1 if cy is not None else 0) + (1 if cz is not None else 0)

                    if face_count == 2:
                        # 엣지 필렛: 두 축에 대해 원호(반경 R)로 투영, 나머지 축은 그대로
                        if cx is not None and cy is not None:
                            vx, vy = ux - cx, uy - cy
                            r = math.hypot(vx, vy)
                            if r < 1e-12:
                                # 엣지 꼭지점 한가운데면 적당히 한 방향으로 밀기(균등)
                                vx, vy = -1.0, -1.0
                                r = math.sqrt(2.0)
                            scale = R / r
                            ux = cx + vx * scale
                            uy = cy + vy * scale
                        elif cx is not None and cz is not None:
                            vx, vz = ux - cx, uz - cz
                            r = math.hypot(vx, vz)
                            if r < 1e-12:
                                vx, vz = -1.0, -1.0
                                r = math.sqrt(2.0)
                            scale = R / r
                            ux = cx + vx * scale
                            uz = cz + vz * scale
                        elif cy is not None and cz is not None:
                            vy, vz = uy - cy, uz - cz
                            r = math.hypot(vy, vz)
                            if r < 1e-12:
                                vy, vz = -1.0, -1.0
                                r = math.sqrt(2.0)
                            scale = R / r
                            uy = cy + vy * scale
                            uz = cz + vz * scale

                    elif face_count == 3:
                        # 코너 필렛: 3축 모두에 대해 반경 R 구면으로 투영
                        vx = ux - cx
                        vy = uy - cy
                        vz = uz - cz
                        r = math.sqrt(vx*vx + vy*vy + vz*vz)
                        if r < 1e-12:
                            # 정확히 코너면 대각선 방향으로 밀어냄
                            vx = vy = vz = -1.0
                            r = math.sqrt(3.0)
                        scale = R / r
                        ux = cx + vx * scale
                        uy = cy + vy * scale
                        uz = cz + vz * scale

                    # 좌표 반영
                    set_from_local(i,j,k, ux,uy,uz)

        # 3) 내부 라플라시안 스무딩 (경계는 고정)
        #    6-이웃(±x, ±y, ±z), lam만큼 평균으로 이동
        for _ in range(max(0, smooth_iters)):
            # 새 좌표 버퍼
            newpos = [[[None]*(numZ+1) for _ in range(numY+1)] for __ in range(numX+1)]

            for i in range(numX + 1):
                for j in range(numY + 1):
                    for k in range(numZ + 1):
                        # 경계면이면 고정
                        if i==0 or i==numX or j==0 or j==numY or k==0 or k==numZ:
                            n = nodesTensor[i][j][k]
                            newpos[i][j][k] = (n.x, n.y, n.z)
                            continue

                        # 내부: 6-이웃 평균
                        neigh = [
                            nodesTensor[i-1][j][k], nodesTensor[i+1][j][k],
                            nodesTensor[i][j-1][k], nodesTensor[i][j+1][k],
                            nodesTensor[i][j][k-1], nodesTensor[i][j][k+1]
                        ]
                        ax = ay = az = 0.0
                        for nn in neigh:
                            ax += nn.x; ay += nn.y; az += nn.z
                        ax /= 6.0; ay /= 6.0; az /= 6.0

                        cur = nodesTensor[i][j][k]
                        nx = (1.0 - lam) * cur.x + lam * ax
                        ny = (1.0 - lam) * cur.y + lam * ay
                        nz = (1.0 - lam) * cur.z + lam * az
                        newpos[i][j][k] = (nx, ny, nz)

            # 업데이트
            for i in range(numX + 1):
                for j in range(numY + 1):
                    for k in range(numZ + 1):
                        x,y,z = newpos[i][j][k]
                        n = nodesTensor[i][j][k]
                        n.x, n.y, n.z = x,y,z

        # 4) 요소 생성 (원본과 동일)
        for i in range(numX):
            for j in range(numY):
                for k in range(numZ):
                    n1 = nodesTensor[i][j][k]
                    n2 = nodesTensor[i + 1][j][k]
                    n3 = nodesTensor[i + 1][j + 1][k]
                    n4 = nodesTensor[i][j + 1][k]
                    n5 = nodesTensor[i][j][k + 1]
                    n6 = nodesTensor[i + 1][j][k + 1]
                    n7 = nodesTensor[i + 1][j + 1][k + 1]
                    n8 = nodesTensor[i][j + 1][k + 1]
                    self.CreateHexahedronLinearElement(n1, n2, n3, n4, n5, n6, n7, n8)
                       
    def CreateImpactBox(self, impactPoint, impactDirection, xDirection, xLength, yLength, zLength, numX, numY, numZ):
        # create a box with the impact point as the center
        # the box is aligned with the global coordinate system
        Zdir = impactDirection
        Xdir = xDirection
        Ydir = np.cross(Zdir,Xdir)
        dx = xLength/(numX)
        dy = yLength/(numY)
        dz = zLength/(numZ)
        
        xMinVec = -xLength/2.0*Xdir
        yMinVec = -yLength/2.0*Ydir
        
        xMinyMinVec = impactPoint + xMinVec + yMinVec
        nodesTensor = []
        
        nodesFixed = {}
        for i in range(numX+1):
            nodesMat = []
            for j in range(numY+1):
                nodesVec = []
                for k in range(numZ+1):
                    x = xMinyMinVec + i*dx*Xdir + j*dy*Ydir + k*dz*Zdir
                    node = self.nodeManager.CreateNode(x[0],x[1],x[2])
                    self.nodeManager.AddNode(node)
                    nodesVec.append(node)
                    if k == numZ:
                        nodesFixed[node.id] = node
                nodesMat.append(nodesVec)
            nodesTensor.append(nodesMat)
        
        # create elements
        for i in range(numX):
            for j in range(numY):
                for k in range(numZ):
                    n1 = nodesTensor[i][j][k]
                    n2 = nodesTensor[i+1][j][k]
                    n3 = nodesTensor[i+1][j+1][k]
                    n4 = nodesTensor[i][j+1][k]
                    n5 = nodesTensor[i][j][k+1]
                    n6 = nodesTensor[i+1][j][k+1]
                    n7 = nodesTensor[i+1][j+1][k+1]
                    n8 = nodesTensor[i][j+1][k+1]
                    self.CreateHexahedronLinearElement(n1,n2,n3,n4,n5,n6,n7,n8)
        return nodesFixed   
    
       
    def CreateImpactBoxwithRoughness(self, impactPoint, z_direction, x_direction,xLength,yLength,zLength,numX,numY,numZ, roughnessMode, RMax, ShapeFactor, ShapeFactor2):
        Zdir = z_direction
        Xdir = x_direction
        Ydir = np.cross(Zdir,Xdir)
        dx = xLength/(numX)
        dy = yLength/(numY)
        dz = zLength/(numZ)
        
        zMatrix = np.zeros((numX+1,numY+1))
        if roughnessMode.lower() == "xsin":
            frequency = ShapeFactor
            for i in range(numX+1):
                for j in range(numY+1):
                    zMatrix[i][j] = RMax*np.sin(2*np.pi*frequency*(-numX/2.0+i))
            maxSurface = max(zMatrix.max(),-zMatrix.min())
            zMatrix = 1.0/maxSurface*zMatrix*RMax
        elif roughnessMode.lower() == "ysin":
            frequency = ShapeFactor
            for i in range(numX+1):
                for j in range(numY+1):
                    zMatrix[i][j] = RMax*np.sin(2*np.pi*frequency*(-numY/2.0+j))
            maxSurface = max(zMatrix.max(),-zMatrix.min())
            zMatrix = 1.0/maxSurface*zMatrix*RMax
        elif roughnessMode.lower() == "xysin":
            frequencyX = ShapeFactor
            frequencyY = ShapeFactor2
            for i in range(numX+1):
                for j in range(numY+1):
                    zMatrix[i][j] = RMax*np.sin(2*np.pi*frequencyX*(-numX/2.0+i))*np.sin(2*np.pi*frequencyY*(-numY/2.0+j))
            maxSurface = max(zMatrix.max(),-zMatrix.min())
            zMatrix = 1.0/maxSurface*zMatrix*RMax
        elif roughnessMode.lower() == "xrandom":
            frequencies_x = np.fft.fftfreq(numX+1,d=dx)
            psd_1d = np.exp(-ShapeFactor*frequencies_x**2)
            
            random_phase_1d = np.random.uniform(0, 2*np.pi, numX+1)
            
            complex_spectrum_1d = np.sqrt(psd_1d) * (np.cos(random_phase_1d))

            surface = np.real(np.fft.ifft(complex_spectrum_1d))
            surface_2d = np.zeros((numX+1,numY+1))
            for i in range(numX+1):
                for j in range(numY+1):
                    surface_2d[i][j] = surface[i]
            maxSurface = max(surface_2d.max(),-surface_2d.min())
            zMatrix = 1.0/maxSurface*surface_2d*RMax
        elif roughnessMode.lower() == "yrandom":
            frequencies_y = np.fft.fftfreq(numY+1,d=dy)
            psd_1d = np.exp(-ShapeFactor*frequencies_y**2)
            
            random_phase_1d = np.random.uniform(0, 2*np.pi, numY+1)
            
            complex_spectrum_1d = np.sqrt(psd_1d) * (np.cos(random_phase_1d))
            
            surface = np.real(np.fft.ifft(complex_spectrum_1d))
            surface_2d = np.zeros((numX+1,numY+1))
            for i in range(numX+1):
                for j in range(numY+1):
                    surface_2d[i][j] = surface[j]
            maxSurface = max(surface_2d.max(),-surface_2d.min())
            zMatrix = 1.0/maxSurface*surface_2d*RMax
        elif roughnessMode.lower() == "xyrandom":
            frequencies_x = np.fft.fftfreq(numX+1,d=dx)
            frequencies_y = np.fft.fftfreq(numY+1,d=dy)
            freq_x, freq_y = np.meshgrid(frequencies_x,frequencies_y)
            psd_2d = np.exp(-ShapeFactor*freq_x**2 - ShapeFactor*freq_y**2)
            
            random_phase_2d = np.random.uniform(0, 2*np.pi, (numX+1, numY+1))
            
            complex_spectrum_2d = np.sqrt(psd_2d) * (np.cos(random_phase_2d) + 1j*np.sin(random_phase_2d))

            surface_2d = np.real(np.fft.ifft2(complex_spectrum_2d))

            maxSurface = max(surface_2d.max(),-surface_2d.min())
            zMatrix = 1.0/maxSurface*surface_2d*RMax
        
        maxZ = -zMatrix.min() 
        xMinVec = -xLength/2.0*Xdir
        yMinVec = -yLength/2.0*Ydir
        
        xMinyMinVec = impactPoint + xMinVec + yMinVec
        nodesTensor = []
        nodeSetFixed = {}
        for i in range(numX+1):
            nodesMat = []
            for j in range(numY+1):
                nodesVec = []
                for k in range(numZ+1):
                    x = xMinyMinVec + i*dx*Xdir + j*dy*Ydir + (zMatrix[i][j]+k*dz+maxZ)*Zdir
                    node = self.nodeManager.CreateNode(x[0],x[1],x[2])
                    self.nodeManager.AddNode(node)
                    nodesVec.append(node)
                    if k == numZ:
                        nodeSetFixed[node.id] = node                        
                nodesMat.append(nodesVec)
            nodesTensor.append(nodesMat)
        
        # create elements
        for i in range(numX):
            for j in range(numY):
                for k in range(numZ):
                    n1 = nodesTensor[i][j][k]
                    n2 = nodesTensor[i+1][j][k]
                    n3 = nodesTensor[i+1][j+1][k]
                    n4 = nodesTensor[i][j+1][k]
                    n5 = nodesTensor[i][j][k+1]
                    n6 = nodesTensor[i+1][j][k+1]
                    n7 = nodesTensor[i+1][j+1][k+1]
                    n8 = nodesTensor[i][j+1][k+1]
                    self.CreateHexahedronLinearElement(n1,n2,n3,n4,n5,n6,n7,n8)
        return nodeSetFixed
    def RemoveOuterElement(self, locX, locY, locZ, Radius):
        
        elems = self.elements
        boundayNodes = [] 
        removedElems = {} 
        nodesSustained = {}
        for key in elems:
            element = elems[key]
            numNodes = len(element.nodes)
            nodes = element.nodes
            numOuterNodes = 0
            outerNodeList = []
            for node in nodes:
                x = node.x
                y = node.y
                z = node.z
                if (x-locX)**2 + (y-locY)**2 + (z-locZ)**2 > Radius**2:
                    numOuterNodes += 1
                    outerNodeList.append(node)
            if numOuterNodes == numNodes:
                removedElems[key] = element
            elif numOuterNodes >0:
                boundayNodes.extend(outerNodeList)
                for node in nodes:
                    nodesSustained[node.id] = node
            else:
                for node in nodes:
                    nodesSustained[node.id] = node
                    
        for key in removedElems:
            self.RemoveElement(removedElems[key])
            
        removedNodes = self.nodeManager.RemoveComplementaryNodes(nodesSustained)
        return boundayNodes, removedElems, removedNodes
    
    def IsOverlappingwithSphere(self, locX, locY, locZ, Radius):
        elems = self.elements
        for key in elems:
            element = elems[key]
            numNodes = len(element.nodes)
            nodes = element.nodes
            numOuterNodes = 0
            for node in nodes:
                x = node.x
                y = node.y
                z = node.z
                if (x-locX)**2 + (y-locY)**2 + (z-locZ)**2 > Radius**2:
                    numOuterNodes += 1
            if numOuterNodes < numNodes:
                return True
        return False
    
    def GetOuterandBoundaryandInnerElement(self, locX, locY, locZ, Radius):
        elems = self.elements
        outerElems = {} 
        boundaryElems = {} 
        innerElems = {}
        for key in elems:
            element = elems[key]
            numNodes = len(element.nodes)
            nodes = element.nodes
            numOuterNodes = 0
            for node in nodes:
                x = node.x
                y = node.y
                z = node.z
                if (x-locX)**2 + (y-locY)**2 + (z-locZ)**2 > Radius**2:
                    numOuterNodes += 1
            if numOuterNodes == numNodes:
                outerElems[key] = element
            elif numOuterNodes >0:
                boundaryElems[key] = element
            else:
                innerElems[key] = element
        return outerElems, boundaryElems, innerElems
    
    def MergeElementNodeswithTolerance(self, tol = 1.e-9):
        elems = self.elements
        mergeNodes = {} 
        
        for key in elems:
            element = elems[key]
            numNodes = len(element.nodes)
            nodes = element.nodes
            for i in range(len(nodes)):
                node = nodes[i] 
                mergeNodes[node.id] = node        
        self.nodeManager.MergeGivenNodes(mergeNodes,tol)
    
    
    def ComputeCentroids(self):
        centroids = {}
        for key in self.elements:
            element = self.elements[key]
            centroid = np.mean([[node.x, node.y, node.z] for node in element.nodes], axis=0)
            centroids[element.id] = centroid
        centroidsvalues = np.array(list(centroids.values()))
        centroidids = np.array(list(centroids.keys()))
        return centroidsvalues, centroidids
    
    def BuildNodetoElementsMap(self):
        node_to_elems = defaultdict(set)
        for eid in self.elements:
            for node in self.elements[eid].nodes:
                node_to_elems[node.id].add(eid)
        return node_to_elems
    
    def FindSharedFace(self, econn1, econn2):
        return len(set(econn1) & set(econn2))
    

    def AssignStructuredGridIndices(self):
        firstElemment = next(iter(self.elements.values()))
        if firstElemment.type != "HEXA8":
            return None, None, None

        centroids, element_ids = self.ComputeCentroids()
        node_to_elems = self.BuildNodetoElementsMap()

        index_map = {}
        grid_dict = {}
        visited_eids = set()
        deferred_queue = set()

        root_eid = element_ids[0]
        queue = deque()
        queue.append((root_eid, (0, 0, 0)))

        index_map[root_eid] = (0, 0, 0)
        grid_dict[(0, 0, 0)] = root_eid
        visited_eids.add(root_eid)

        face_to_dir = {}
        direction_codes = [(0, 0, -1), (0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1)]
        
        while queue:
            while queue:
                current_eid, (i, j, k) = queue.popleft()
                current_faces = self.elements[current_eid].GetBoundaries()
                for ith in range(len(current_faces)):
                    face = current_faces[ith]
                    fset = frozenset(sorted(face))                  
                    di, dj, dk = direction_codes[ith]
                    new_idx = (i + di, j + dj, k + dk)
                    if new_idx[0] >7 or new_idx[1] > 7 or new_idx[2] > 7:
                        pass

                    neighbor_candidates = []
                    for nid in face:
                        neighbor_candidates.extend(node_to_elems[nid])
                    # remove except which is duplicated 4 times 
                    counter = Counter(neighbor_candidates)

                    neighbor_candidates = [item for item, count in counter.items() if count == 4]                                       
                    neighbor_candidates = set(neighbor_candidates) - {current_eid}

                    for neighbor_eid in neighbor_candidates:
                        if neighbor_eid in visited_eids:
                            continue
                        neighbor_faces = self.elements[neighbor_eid].GetBoundaries()
                        matched = False
                        for jth in range(len(neighbor_faces)):  
                            nface = neighbor_faces[jth]                        
                            nfset = frozenset(sorted(nface))
                            if fset == nfset:                                
                                if new_idx not in grid_dict:
                                    if neighbor_eid == 394:
                                        pass 
                                    index_map[neighbor_eid] = new_idx
                                    grid_dict[new_idx] = neighbor_eid
                                    visited_eids.add(neighbor_eid)
                                    queue.append((neighbor_eid, new_idx))
                                    self.elements[neighbor_eid].FixConnectivityHexa8withNeighborElement(self.elements[current_eid])
                                    # exchange node coonnectivity of neighbor element same to current element                                    
                                matched = True                                
                                break         
            print("Number of Visited Elements: ", len(visited_eids))                                       
            break
            for element_id in self.elements:
                if element_id not in visited_eids:
                    for face in self.elements[element_id].GetBoundaries():
                        fset = frozenset(sorted(face))
                        neighbor_candidates = set()
                        for nid in face:
                            neighbor_candidates |= node_to_elems[nid]
                        neighbor_candidates -= {element_id}
                        for neighbor_eid in neighbor_candidates:
                            if neighbor_eid in visited_eids:
                                matched = False 
                                neighbor_faces = self.elements[neighbor_eid].GetBoundaries()
                                for jth in range(len(neighbor_faces)):
                                    nface = neighbor_faces[jth]
                                    nfset = frozenset(sorted(nface))
                                    if fset == nfset:
                                        ni, nj, nk = index_map[neighbor_eid]
                                        di, dj, dk = direction_codes[jth]
                                        new_idx = (ni + di, nj + dj, nk + dk)
                                        index_map[element_id] = new_idx
                                        grid_dict[new_idx] = element_id
                                        visited_eids.add(element_id)
                                        queue.append((element_id, new_idx))
                                        matched = True
                                if matched:
                                    break
            print("Number of Visited Elements: ", len(visited_eids))                                       
                                              
        all_indices = np.array(list(grid_dict.keys()))
        min_indices = all_indices.min(axis=0)
        offset = tuple(-min_indices)

        shifted_dict = {}        
        mini = 100000000000000000
        minj = 100000000000000000
        mink = 100000000000000000
        maxi = -100000000000000000
        maxj = -100000000000000000
        maxk = -100000000000000000
            
        for (i, j, k), eid in grid_dict.items():
            new_idx = (i + offset[0], j + offset[1], k + offset[2])
            shifted_dict[new_idx] = eid
            mini = min(mini, new_idx[0])
            minj = min(minj, new_idx[1])
            mink = min(mink, new_idx[2])
            maxi = max(maxi, new_idx[0])
            maxj = max(maxj, new_idx[1])
            maxk = max(maxk, new_idx[2])
        
        

        ni, nj, nk = np.max(np.array(list(shifted_dict.keys())), axis=0) + 1
        id_array = np.full((ni, nj, nk), fill_value=-1, dtype=int)
        for (i, j, k), eid in shifted_dict.items():
            id_array[i, j, k] = eid
                                   
        '''for i in range(ni):
            for j in range(nj):
                for k in range(nk):
                    print(f"ID at ({i}, {j}, {k}): {id_array[i, j, k]}")'''

        return id_array, shifted_dict, offset

    '''def AssignStructuredGridIndices(self):
        #first element 
        firstElemment = next(iter(self.elements.values()))
        elements = list(self.elements.values())
        if firstElemment.type != "HEXA8":
            return None, None, None
        
        centroids, element_ids = self.ComputeCentroids()
        node_to_elems = self.BuildNodetoElementsMap()

        visited = set()
        index_map = {}            # element_id → (i,j,k)
        grid_dict = {}            # (i,j,k) → element_id

        root_eid = 0 
        queue = deque()
        queue.append(0)
        index_map[root_eid] = (0, 0, 0)
        grid_dict[(0, 0, 0)] = element_ids[root_eid]
        visited.add(root_eid)

        # 초기 6방향 단위 벡터 추출
        base = centroids[root_eid]
        directions = {}
        neighbors = set()
        for node in elements[root_eid].nodes:
            neighbors |= node_to_elems[node.id]
        neighbors -= {root_eid}

        used_dirs = []
        dir_table = {}
        direction_codes = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]

        for neighbor_eid in neighbors:
            rootConnectivity = elements[root_eid].Connectivity()
            neighborConnectivity = elements[neighbor_eid].Connectivity()
            if self.FindSharedFace(rootConnectivity, neighborConnectivity) >= 4:
                vec = centroids[neighbor_eid] - base
                vec /= np.linalg.norm(vec)
                rounded_vec = tuple(np.round(vec, 6))
                if rounded_vec not in directions:
                    directions[rounded_vec] = neighbor_eid

        sorted_dirs = list(directions.items())[:3]
        for code, ((vec_key), _) in zip(direction_codes, sorted_dirs):
            dir_table[vec_key] = code
            dir_table[tuple(-np.array(vec_key))] = tuple(-np.array(code))

        # BFS 진행
        while queue:
            eid = queue.popleft()
            i, j, k = index_map[eid]

            for node in elements[eid].nodes:
                nid = node.id
                for nid_eid in node_to_elems[nid]:
                    if nid_eid == eid or nid_eid in visited:
                        continue
                    eidConntectivity = elements[eid].Connectivity()
                    nid_eidConnectivity = elements[nid_eid].Connectivity()
                    if self.FindSharedFace(eidConntectivity, nid_eidConnectivity) >= 4:
                        vec = centroids[nid_eid] - centroids[eid]
                        vec /= np.linalg.norm(vec)
                        key = tuple(np.round(vec, 6))
                        if key in dir_table:
                            di, dj, dk = dir_table[key]
                            new_idx = (i + di, j + dj, k + dk)
                            if new_idx not in grid_dict:
                                index_map[nid_eid] = new_idx
                                grid_dict[new_idx] = element_ids[nid_eid]
                                visited.add(nid_eid)
                                queue.append(nid_eid)

        # 인덱스 오프셋 조정 (모두 양수로 만들기 위해)
        all_indices = np.array(list(grid_dict.keys()))
        min_indices = all_indices.min(axis=0)
        offset = tuple(-min_indices)

        # 오프셋 적용된 새로운 3D 배열 만들기
        shifted_dict = {}
        for (i, j, k), eid in grid_dict.items():
            new_idx = (i + offset[0], j + offset[1], k + offset[2])
            shifted_dict[new_idx] = eid

        ni, nj, nk = np.max(np.array(list(shifted_dict.keys())), axis=0) + 1
        id_array = np.full((ni, nj, nk), fill_value=-1, dtype=int)
        for (i, j, k), eid in shifted_dict.items():
            id_array[i, j, k] = eid

        return id_array, shifted_dict, offset'''


    # Example usage (you need to define your own `element_ids`, `elements`, and `nodes`):
    # id_array, grid_dict, offset = assign_structured_grid_indices(elements, nodes, element_ids)
    # print(id_array.shape)  # should be (ni, nj, nk)
    # print(id_array)        # 3D array with element IDs


def compute_segment_normal(seg, nodeManager):
    """segment(노드ID 리스트) → 법선 벡터 (numpy array, 단위벡터). 실패 시 None."""
    coords = []
    for nid in seg:
        n = nodeManager.GetNode(nid)
        if n is None:
            return None
        coords.append((n.x, n.y, n.z))
    if len(coords) < 3:
        return None
    v1 = np.array(coords[1]) - np.array(coords[0])
    v2 = np.array(coords[2]) - np.array(coords[0])
    normal = np.cross(v1, v2)
    norm = np.linalg.norm(normal)
    if norm < 1e-30:
        return None
    return normal / norm


def compute_segment_center(seg, nodeManager):
    """segment(노드ID 리스트) → 중심점 (numpy array). 실패 시 None."""
    cx, cy, cz, nn = 0.0, 0.0, 0.0, 0
    for nid in seg:
        n = nodeManager.GetNode(nid)
        if n is None:
            return None
        cx += n.x; cy += n.y; cz += n.z; nn += 1
    if nn == 0:
        return None
    return np.array([cx / nn, cy / nn, cz / nn])


def are_segments_facing(normalA, normalB, angle_limit_deg):
    """두 법선이 마주보는지 판정. cos(angle) < -cos(limit) 이면 True."""
    if normalA is None or normalB is None:
        return True  # 법선 계산 실패 시 보수적으로 통과
    cos_limit = math.cos(math.radians(angle_limit_deg))
    dot = np.dot(normalA, normalB)
    return dot < -cos_limit

