#from dynareadout import D3plot
from scipy.spatial import KDTree
import os
import numpy as np

from KooCAEManager.KooNode import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooBoundaryNode import *


class KooDynaNodalResult:
    def __init__(self, path = "", nodes = [], tol = 1e-3):
        
        self.path = path
        self.nodes = nodes
        self.tolerance = tol
        
        ## Nodal Result Vector
        self.time = []
        self.coord = None
        self.ids = []
        self.disp = []
        self.velocity = []
        self.acceleration = []
        
        self.nodesInterpolatedDisp = []
    
        #if path != "":
        #    self.d3plot = D3plot(path)
    
    def SetPath(self, path):
        self.path = path
        #self.d3plot = D3plot(path)
    
    def SetNodes(self,nodes):
        self.nodes = nodes
        
    def ImportResults(self):
        self.ReadDisplacement()
        pass

    '''def ReadDisplacement(self):
        original_coords = self.d3plot.read_node_coordinates(0)
        original_coords = list(original_coords)
        X = np.array(original_coords)
        self.coord = X
        node_ids = self.d3plot.read_node_ids()
        self.ids = []
        for (i, nid) in enumerate(node_ids):
            self.ids.append(nid)

        # read time
        num_step = self.d3plot.num_time_steps()
        self.time = []
        for i in range(num_step):
            time = self.d3plot.read_time(i)
            self.time.append(time)
        

        for j in range(1,self.d3plot.num_time_steps()):
            node_coords = self.d3plot.read_node_coordinates(j)
            # node_coords to list
            node_coords = list(node_coords)
            Xp1 = np.array(node_coords)
            disp = Xp1 - X
            self.disp.append(disp)'''
    
    
    def InterpolateDisplacement(self):
        # 기존 코드를 최적화한 버전
        points = np.array(self.coord)
        tree = KDTree(points)

        for node in self.nodes:
            dispHistory = []
            nodeID = node.id
            point = np.array([node.x, node.y, node.z])
            
            # tolerance 내의 포인트들을 가져옴
            indices = tree.query_ball_point(point, self.tolerance)
            if len(indices) == 0:
                self.nodesInterpolatedDisp.append(None)
                continue
            # 인덱스에 해당하는 좌표들 추출
            neighbor_coords = np.array([self.coord[idx] for idx in indices])
            
            # 거리 계산 (벡터화)
            diffs = neighbor_coords - point
            dists = np.linalg.norm(diffs, axis=1)
            
            # 가중치 계산 (거리 0이면 바로 가중치 1)
            if np.any(dists == 0.0):
                weightedList = np.zeros(len(dists))
                weightedList[np.argmin(dists)] = 1.0
            else:
                weights = 1.0 / dists
                weightedList = weights / weights.sum()
            disp = np.zeros(3)
            dispHistory.append(disp)    
            # 변위 계산 (벡터화)
            for i in range(1, len(self.disp)):
                disp = np.dot(weightedList, self.disp[i][indices])
                dispHistory.append(disp)
            
            self.nodesInterpolatedDisp.append(dispHistory)
            
            
    def InterpolateDisplacementOld(self):
        points = np.array(self.coord)        
        tree = KDTree(points)
                
        for node in self.nodes:
            dispHistory = []
            nodeID = node.id
            point = np.array([node.x, node.y, node.z])
            indices = tree.query_ball_point(point,self.tolerance)
            if len(indices) == 0:
                self.nodesInterpolatedDisp.append(None)
                continue
            dist = 1.0e99
            weightedList =[]
            # resize weightedList as 100 
            for i in range(len(indices)):
                weightedList.append(0.0)
            total = 0.0
            curdist = 0.0
            for j in range(len(indices)):
                idx = indices[j]
                X = self.coord[idx][0]
                Y = self.coord[idx][1]
                Z = self.coord[idx][2]
                curdist = np.sqrt((X - node.x)**2 + (Y - node.y)**2 + (Z - node.z)**2)
                if curdist == 0.0:
                    for i in range(len(indices)):
                        weightedList[i] = 0.0
                    weightedList[j] = 1.0
                    break
                else:
                    weightedList[j] = 1.0/curdist
                    total += 1.0/curdist
            if curdist != 0.0:
                for i in range(len(indices)):
                    weightedList[i] /= total
            disp = np.zeros(3)
            dispHistory.append(disp)    
            for i in range(1,len(self.disp)):
                disp = np.zeros(3)
                for j in range(len(indices)):
                    idx = indices[j]
                    disp += self.disp[i][idx] * weightedList[j]
                dispHistory.append(disp)
            self.nodesInterpolatedDisp.append(dispHistory)
   
    def WritetoDynaKeyword(self, startCID = 0, startLID = 0):
        keyword = ""
        return keyword
        
    def Print(self):
        print("DispHistory :")
        for disp in self.nodesInterpolatedDisp:
            for i in range(len(disp)):
                print(disp[i][0],disp[i][1],disp[i][2])     


class KooDynaNodalResultNodalDisp(KooDynaNodalResult):
    def __init__(self, path = "", nodes = [], tol = 1e-3, defineMan : KooDefineManager = None, boundaryMan : KooBoundaryNodeManager = None):
        super().__init__(path,nodes,tol)
        self.defineMan = defineMan
        self.boundaryNodeMan = boundaryMan
    
    def GenenerateNodalDisp(self):
        for j in range(len(self.nodesInterpolatedDisp)):
            disp = self.nodesInterpolatedDisp[j]
            node = self.nodes[j]
            if disp is not None:
                A1 = []
                O1 = [] 
                O2 = []
                O3 = []
                for i in range(len(disp)):
                    A1.append(self.time[i])
                    O1.append(disp[i][0])
                    O2.append(disp[i][1])
                    O3.append(disp[i][2])                                                    
                curveX = self.defineMan.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,A1,O1)
                curveY = self.defineMan.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,A1,O2)
                curveZ = self.defineMan.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,A1,O3)
                #vad 2 : displacement
                self.boundaryNodeMan.CreateBoundaryPrescribedMotionNode(node,1,2,curveX.lcid,1.0,0,1.0e28,0.0,"{0}_X".format(node.id))
                self.boundaryNodeMan.CreateBoundaryPrescribedMotionNode(node,2,2,curveY.lcid,1.0,0,1.0e28,0.0,"{0}_Y".format(node.id))
                self.boundaryNodeMan.CreateBoundaryPrescribedMotionNode(node,3,2,curveZ.lcid,1.0,0,1.0e28,0.0,"{0}_Z".format(node.id))                
                
                
                
    
    def WritetoDynaKeyword(self, startCID = 0, startLID = 0):
        keyword = "" 
        return keyword
        
        

class KooDynaResultManager:
    def __init__(self, defineManager : KooDefineManager = None, boundaryNodeManager : KooBoundaryNodeManager = None):
        self.maxid = 0 
        self.results = {}
        if defineManager is None:
            self.defineMan = KooDefineManager()
        else:
            self.defineMan = defineManager
        if boundaryNodeManager is None:
            self.boundaryMan = KooBoundaryNodeManager()
        else:
            self.boundaryMan = boundaryNodeManager
        
    def AddDynaNodalResultNodalDisp(self, path = "", nodes = [], tol = 1e-3):
        self.maxid += 1
        result = KooDynaNodalResultNodalDisp(path,nodes,tol,self.defineMan,self.boundaryMan)
        self.results[self.maxid] = result
        return result
    
    def WritetoDynaKeyword(self, startCID = 0, startLID = 0):
        keyword = ""
        for key in self.results.keys():
            result = self.results[key]
            keyword += result.WritetoDynaKeyword(startCID,startLID)
        return keyword