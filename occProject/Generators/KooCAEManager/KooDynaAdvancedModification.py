import copy
import os
getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
import sys
import shutil
if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path

from KooODBCADManager.Module import *
from KooODBCADManager.ModuleManager import *

from KooCAEManager.KooMeshImporter import *
from KooCAEManager.KooPart import *

from KooCAEManager.KooDynaAutomaticSimulationScriptGenerator import *

from scipy.spatial import KDTree
from scipy.stats import truncnorm

import numpy as np
import math
import csv
import json
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf, gp_Ax1, gp_Pln


def truncated_normal_samples(mu, sigma, x, size=1000,eps=50):
    # 범위 계산
    lower = max(-100+eps, mu - x * sigma)   # 양수 조건 반영
    upper = mu + x * sigma
    
    # truncnorm은 표준화된 구간 (a, b) 필요
    a, b = (lower - mu) / sigma, (upper - mu) / sigma
    
    # 절단 정규분포 샘플링
    samples = truncnorm.rvs(a, b, loc=mu, scale=sigma, size=size)
    return samples

def lhs_unit(n_samples: int, n_dims: int, rng: np.random.Generator) -> np.ndarray:
    """
    기본 LHS on [0,1]: 각 차원마다 n개의 동일 길이 구간에서 하나씩 선택하고 무작위로 섞음.
    반환 shape: (n_samples, n_dims)
    """
    if n_dims <= 0:
        raise ValueError("LHS 차원 수가 0입니다. 샘플링할 변수가 없습니다.")
    # 각 차원별로 균등한 구간에서 하나씩 뽑고, 구간 내부에서 jitter 적용
    cut = np.linspace(0, 1, n_samples + 1)
    u = rng.uniform(low=0, high=1, size=(n_samples, n_dims))
    a = cut[:-1]
    b = cut[1:]
    # 각 차원마다 구간 인덱스 0..n-1를 랜덤하게 섞어 배정
    samples = np.zeros((n_samples, n_dims), dtype=float)
    for j in range(n_dims):
        order = rng.permutation(n_samples)
        samples[:, j] = a[order] + u[:, j] * (b[order] - a[order])
    return samples


class KooDynaAdvancedModification:
    def __init__(self, dynaImporter : KooDynaImporter):
        self.dynaImporter : KooDynaImporter = dynaImporter    
        self.dynaSubImporter : Dict[str, KooDynaImporter] = {}
        
        self.moduleManager = ModuleManager()
        self.step = 1
        self.runDirectoryMode = False
        self.runDirectoryPath = ""        
        self.metaDirectoryPath = ""
        
    def WriteModifiedFile(self, filePath,modifiedKeyword="",copytoOutputFolder=False):
        if ".k" in modifiedKeyword:
            curPath = filePath + modifiedKeyword
            jsonPath = filePath + modifiedKeyword.replace(".k",".json")
        else:
            curPath = filePath + modifiedKeyword + ".k"
            jsonPath = filePath + modifiedKeyword + ".json"


        with open(curPath, "w") as f:
            f.write("*KEYWORD\n")
            f.write(self.dynaImporter.WriteStreamDynaKeyword())
            f.write("*END\n")

        self.dynaImporter.AddMetaDatafromManager()
        with open(jsonPath, "w") as f:
            json.dump(self.dynaImporter.metaData,f,ensure_ascii=False, indent=2)

        if copytoOutputFolder:
            folderPath = curPath.split("/")[:-1]
            folderPath = "/".join(folderPath)
            outputFolderPath = os.path.join(folderPath, "Output")
            if not os.path.exists(outputFolderPath):
                os.makedirs(outputFolderPath)
            dynamicRelaxPath = os.path.join(folderPath, "DynamicRelaxation")
            if not os.path.exists(dynamicRelaxPath):
                os.makedirs(dynamicRelaxPath)

            shutil.copy(curPath, outputFolderPath)
            shutil.copy(curPath, dynamicRelaxPath)

    def WeakCoupling(self, option):
        d3plotPath = option["FilePath"]
        # NodeSet or SegmentSet
        setMode = option["Mode"]
        setID = option["SetID"]
        boundaryBox = option["BoundaryBox"]
        
        
        if boundaryBox is None:
            self.dynaImporter.ImportExternalDynaResult(d3plotPath)
        else:
            minX = boundaryBox[0]
            maxX = boundaryBox[1]
            minY = boundaryBox[2]
            maxY = boundaryBox[3]
            minZ = boundaryBox[4]
            maxZ = boundaryBox[5]
            self.dynaImporter.ImportExternalDynaResultinBoundaryBox(d3plotPath, minX, maxX, minY, maxY, minZ, maxZ)
        points = {}
        if setMode == "NodeSet":
            nodeSet : NodeSet = self.dynaImporter.nodeSetManager.nodeSets[setID]
            nodes = nodeSet.nodes
            for i in nodes:
                node = nodes[i]
                points[node.id] = tuple(node.x, node.y, node.z)
        elif setMode == "SegmentSet":
            segmentSet : KooSegmentSet = self.dynaImporter.segmentSetManager.segmentSetList[setID]
            for i in range(len(segmentSet.segments)):
                segment = segmentSet.segments[i]
                for nodeid in segment:
                    node = self.dynaImporter.nodeManager.nodes[nodeid]
                    points[node.id] = tuple(node.x, node.y, node.z)
        times = self.dynaImporter.externalDynaResultManager.GetTimeData()
        point_disps = self.dynaImporter.externalDynaResultManager.InterpolateDisplacement(points)
        for nid in points:    
            node = self.dynaImporter.nodeManager.nodes[nid]
            dispx = []
            dispy = []
            dispz = [] 
            for i in range(len(times)):
                dispx.append(point_disps[i][nid][0])
                dispy.append(point_disps[i][nid][1])
                dispz.append(point_disps[i][nid][2])
            
            define_curve_x = self.dynaImporter.defineManager.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,times,dispx)
            define_curve_y = self.dynaImporter.defineManager.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,times,dispy)
            define_curve_z = self.dynaImporter.defineManager.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,times,dispz)
            cidx = define_curve_x.lcid
            cidy = define_curve_y.lcid
            cidz = define_curve_z.lcid
            namex = "WeakCoupling_"+str(nid) + "_X"
            namey = "WeakCoupling_"+str(nid) + "_Y"
            namez = "WeakCoupling_"+str(nid) + "_Z"
            self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionNode(namex,node,1,0,cidx,1.0,0,1.e28,0)
            self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionNode(namey,node,2,0,cidy,1.0,0,1.e28,0)
            self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionNode(namez,node,3,0,cidz,1.0,0,1.e28,0)
            
        tFinal = times[-1]
        dt = tFinal/len(times)
        self.SetControlandDatabaseExplicit(tFinal, dt)
          
      
    def DefeatureMesh(self, option):
        pids = option["PIDS"]
        minLength = option["MinLength"]
        
        
        
        for pid in pids:
            
            curMaxLength = -1.e99
            self.dynaImporter.SyncronizeMaxID()        
            part = self.dynaImporter.partManager.parts[pid]
            
            nodeMan : NodeManager = part.nodeManager
            elemMan : ElementManager = part.elementManager
            
            segments = elemMan.GetExternalBoundary(True)
            #list to dictionary
            segments = {i:segments[i] for i in range(len(segments))}
            nodesExternal = elemMan.GetExternalNodes()
            nodesExternal = {nodesExternal[i].id :nodesExternal[i] for i in range(len(nodesExternal))}
            popiList = {}
            while True: 
                i = 0 
                
                for i in segments:
                    segment = segments[i]
                    segmentLength = [] 
                    n1 = nodesExternal[segment[0]]
                    n2 = nodesExternal[segment[1]]
                    n3 = nodesExternal[segment[2]]
                    
                    l1 = ((n1.x-n2.x)**2+(n1.y-n2.y)**2+(n1.z-n2.z)**2)**0.5
                    l2 = ((n2.x-n3.x)**2+(n2.y-n3.y)**2+(n2.z-n3.z)**2)**0.5            
                    l3 = ((n3.x-n1.x)**2+(n3.y-n1.y)**2+(n3.z-n1.z)**2)**0.5
                    curMaxLength = max(curMaxLength, l1,l2,l3)
                    if max(l1,l2,l3) < minLength:
                        n1.x = (n1.x+n2.x+n3.x)/3.0
                        n1.y = (n1.y+n2.y+n3.y)/3.0
                        n1.z = (n1.z+n2.z+n3.z)/3.0
                        nodesExternal[segment[0]] = n1
                        nodesExternal[segment[1]] = n1
                        nodesExternal[segment[2]] = n1
                        popiList[i] = i
          
                for i in segments:
                    segment = segments[i]
                    segmentLength = [] 
                    n1 = nodesExternal[segment[0]]
                    n2 = nodesExternal[segment[1]]
                    n3 = nodesExternal[segment[2]]
                    if n1.id == n2.id or n2.id == n3.id or n3.id == n1.id:
                        popiList[i] = i
                removeCount = 0 
                for i in popiList:
                    segments.pop(i)
                    removeCount += 1
                print("Remove Count: ", removeCount)   
                if len(popiList) == 0:
                    break
                popiList = {}     
            
            popiList = {}
            i = 0 
            # segments to list
            # next key value of segments
            # dict's key list 
            segKey = list(segments.keys())
            # sort key list as descending order
            segKey.sort(reverse=True)
        
            while True: 
                        
               
                segment = segments[segKey[i]]
                n1 = nodesExternal[segment[0]]
                n2 = nodesExternal[segment[1]]
                n3 = nodesExternal[segment[2]]
                
                l1 = ((n1.x-n2.x)**2+(n1.y-n2.y)**2+(n1.z-n2.z)**2)**0.5
                l2 = ((n2.x-n3.x)**2+(n2.y-n3.y)**2+(n2.z-n3.z)**2)**0.5            
                l3 = ((n3.x-n1.x)**2+(n3.y-n1.y)**2+(n3.z-n1.z)**2)**0.5
                curMinLength = min(l1,l2,l3)
                if curMinLength < minLength:
                    popiList[segKey[i]] = segKey[i]
        
                    
                       
                        
                    if l1 == curMinLength:
                        '''n1.x = (n1.x+n2.x)/2.0
                        n1.y = (n1.y+n2.y)/2.0
                        n1.z = (n1.z+n2.z)/2.0'''
                        nodesExternal[segment[0]] = n1
                        nodesExternal[segment[1]] = n1
                        segment[0] = n1.id
                        segment[1] = n1.id
                        segments[segKey[i]] = segment
                        numNeighbors = 0
                        xNeighbor = 0.0
                        yNeighbor = 0.0
                        zNeighbor = 0.0
                        for j in range(len(segKey)):
                            segmentB = segments[segKey[j]]
                            bn1 = nodesExternal[segmentB[0]]                            
                            bn2 = nodesExternal[segmentB[1]]
                            bn3 = nodesExternal[segmentB[2]]
                            if bn1.id == n2.id:
                                segmentB[0] = n1.id                                
                            if bn2.id == n2.id:
                                segmentB[1] = n1.id
                            if bn3.id == n2.id:
                                segmentB[2] = n1.id                                                                
                            '''if n1.id in segmentB:
                                if bn1.id != n1.id:
                                    xNeighbor += bn1.x
                                    yNeighbor += bn1.y
                                    zNeighbor += bn1.z
                                    numNeighbors += 1
                                if bn2.id != n1.id:
                                    xNeighbor += bn2.x
                                    yNeighbor += bn2.y
                                    zNeighbor += bn2.z
                                    numNeighbors += 1
                                if bn3.id != n1.id:
                                    xNeighbor += bn3.x
                                    yNeighbor += bn3.y
                                    zNeighbor += bn3.z
                                    numNeighbors += 1'''
                            if bn1.id == bn2.id or bn2.id == bn3.id:
                                popiList[segKey[j]] = segKey[j]
                        if numNeighbors > 0:
                            n1.x = xNeighbor/float(numNeighbors)
                            n1.y = yNeighbor/float(numNeighbors)
                            n3.z = zNeighbor/float(numNeighbors)
                    elif l2 == curMinLength:
                        '''n2.x = (n2.x+n3.x)/2.0
                        n2.y = (n2.y+n3.y)/2.0
                        n2.z = (n2.z+n3.z)/2.0'''
                        nodesExternal[segment[1]] = n2
                        nodesExternal[segment[2]] = n2
                        segment[1] = n2.id
                        segment[2] = n2.id
                        segments[segKey[i]] = segment
                        numNeighbors = 0
                        xNeighbor = 0.0
                        yNeighbor = 0.0
                        zNeighbor = 0.0
                        for j in range(len(segKey)):
                            segmentB = segments[segKey[j]]
                            bn1 = nodesExternal[segmentB[0]]
                            bn2 = nodesExternal[segmentB[1]]
                            bn3 = nodesExternal[segmentB[2]]
                            if bn1.id == n3.id:
                                segmentB[0] = n2.id
                            if bn2.id == n3.id:
                                segmentB[1] = n2.id
                            if bn3.id == n3.id:
                                segmentB[2] = n2.id                                
                            '''if n2.id in segmentB:
                                if bn1.id != n2.id:
                                    xNeighbor += bn1.x
                                    yNeighbor += bn1.y
                                    zNeighbor += bn1.z
                                    numNeighbors += 1
                                if bn2.id != n2.id:
                                    xNeighbor += bn2.x
                                    yNeighbor += bn2.y
                                    zNeighbor += bn2.z
                                    numNeighbors += 1
                                if bn3.id != n2.id:
                                    xNeighbor += bn3.x
                                    yNeighbor += bn3.y
                                    zNeighbor += bn3.z
                                    numNeighbors += 1'''
                            if bn1.id == bn2.id or bn2.id == bn3.id:
                                popiList[segKey[j]] = segKey[j]
                        if numNeighbors > 0:
                            n2.x = xNeighbor/float(numNeighbors)
                            n2.y = yNeighbor/float(numNeighbors)
                            n2.z = zNeighbor/float(numNeighbors)
                    elif l3 == curMinLength:
                        '''n1.x = (n3.x+n1.x)/2.0
                        n1.y = (n3.y+n1.y)/2.0
                        n1.z = (n3.z+n1.z)/2.0'''
                        nodesExternal[segment[2]] = n1
                        nodesExternal[segment[0]] = n1
                        segment[2] = n1.id
                        segment[0] = n1.id
                        segments[segKey[i]] = segment
                        numNeighbors = 0
                        xNeighbor = 0.0
                        yNeighbor = 0.0
                        zNeighbor = 0.0
                        for j in range(len(segKey)):
                            segmentB = segments[segKey[j]]
                            bn1 = nodesExternal[segmentB[0]]
                            bn2 = nodesExternal[segmentB[1]]
                            bn3 = nodesExternal[segmentB[2]]
                            if bn1.id == n3.id:
                                segmentB[0] = n1.id
                            if bn2.id == n3.id:
                                segmentB[1] = n1.id
                            if bn3.id == n3.id:
                                segmentB[2] = n1.id
                            '''if n1.id in segmentB:
                                if bn1.id != n1.id:
                                    xNeighbor += bn1.x
                                    yNeighbor += bn1.y
                                    zNeighbor += bn1.z
                                    numNeighbors += 1
                                if bn2.id != n1.id:
                                    xNeighbor += bn2.x
                                    yNeighbor += bn2.y
                                    zNeighbor += bn2.z
                                    numNeighbors += 1
                                if bn3.id != n1.id:
                                    xNeighbor += bn3.x
                                    yNeighbor += bn3.y
                                    zNeighbor += bn3.z
                                    numNeighbors += 1'''
                            if bn1.id == bn2.id or bn2.id == bn3.id:
                                popiList[segKey[j]] = segKey[j]
                        if numNeighbors > 0:
                            n3.x = xNeighbor/float(numNeighbors)
                            n3.y = yNeighbor/float(numNeighbors)
                            n3.z = zNeighbor/float(numNeighbors)
                    else:
                        print("Error")
                    
                    removeCount = 0
                    #popiList as List
                    popiList = [popiList[i] for i in popiList]
                    # sort popiList in descending order
                    popiList.sort(reverse=True) 
                    for j in popiList:
                        key = j
                        # remove from segments
                        segments.pop(key)
                        # remove from segKey
                        segKey.remove(j)
                        removeCount += 1
                    print("Remove Count: ", removeCount) 
                    popiList = {}
                    i = 0
                    continue
                     
                i = i + 1
                if len(segments) == i:
                    break
                popiList = {}    
             
             
            i = 0 
             
            while True: 
                        
               
                segment = segments[segKey[i]]
                n1 = nodesExternal[segment[0]]
                n2 = nodesExternal[segment[1]]
                n3 = nodesExternal[segment[2]]
                
                la = ((n1.x-n2.x)**2+(n1.y-n2.y)**2+(n1.z-n2.z)**2)**0.5
                lb = ((n2.x-n3.x)**2+(n2.y-n3.y)**2+(n2.z-n3.z)**2)**0.5            
                lc = ((n3.x-n1.x)**2+(n3.y-n1.y)**2+(n3.z-n1.z)**2)**0.5
                
                semiperimeter = (la+lb+lc)/2.0
                area = (semiperimeter*(semiperimeter-la)*(semiperimeter-lb)*(semiperimeter-lc))**0.5
                radius = area/semiperimeter
                if radius < minLength/2.0:
                    largest = max(la,lb,lc)
                    if largest == la:
                        na = n1
                        nb = n2
                    elif largest == lb:
                        na = n2
                        nb = n3
                    elif largest == lc:
                        na = n3
                        nb = n1
                    
                    segmentA = segments[segKey[i]]
                    segmentB = None
                    for j in range(len(segKey)):
                        segmentC = segments[segKey[j]]
                        #if segKey[j] == segKey[i]:
                        #    continue                        
                        if set(segmentA) == set(segmentC):
                            continue
                        if na.id in segmentC and nb.id in segmentC:
                            segmentB = segmentC
                            break
                    # start from not shared node
                    if segmentB is not None:
                        curj = j
                        AindexList = []
                        for j in range(3):
                            if segmentA[j] not in segmentB:
                                AindexList.append(j)
                        AindexList.append((AindexList[0]+1) % 3)
                        AindexList.append((AindexList[1]+1) % 3)
                        BindexList = []
                        for j in range(3):
                            if segmentB[j] not in segmentA:
                                BindexList.append(j)
                        BindexList.append((BindexList[0]+1)%3)
                        BindexList.append((BindexList[1]+1)%3)
                        l1 = ((na.x-nb.x)**2+(na.y-nb.y)**2+(na.z-nb.z)**2)**0.5
                        nc = nodesExternal[segmentB[BindexList[0]]]
                        nd = nodesExternal[segmentA[AindexList[0]]]
                        l2 = ((nc.x-nd.x)**2+(nc.y-nd.y)**2+(nc.z-nd.z)**2)**0.5
                        if l1 > 6*radius:
                            segmentAre = [segmentA[AindexList[0]],segmentA[AindexList[1]],segmentB[BindexList[0]]]
                            segmentBre = [segmentB[BindexList[0]],segmentB[BindexList[1]],segmentA[AindexList[0]]]
                            segments[segKey[i]] = segmentAre
                            segments[segKey[curj]] = segmentBre
                            
                i = i + 1    
                if len(segments) == i:
                    break                      
                                
                            
                            
                        
                    
                    
                        
             
            from stl import mesh
            import numpy as np
            triangles = [] 
            #segments = {i:segments[i] for i in range(len(segments))}
            for i in segments:
                segment = segments[i]
                n1 = nodesExternal[segment[0]]
                n2 = nodesExternal[segment[1]]
                n3 = nodesExternal[segment[2]]
                triangles.append([n1.x, n1.y, n1.z, n2.x, n2.y, n2.z, n3.x, n3.y, n3.z])
            triangles_array = np.zeros(len(triangles), dtype=mesh.Mesh.dtype)
            for i, triangle in enumerate(triangles):
                triangles_array["vectors"][i] = [
                    [triangle[0], triangle[1], triangle[2]],
                    [triangle[3], triangle[4], triangle[5]],
                    [triangle[6], triangle[7], triangle[8]]
                ]
            
            mesh_data = mesh.Mesh(triangles_array)
            curdir = os.getcwd()
            curPath = os.path.join(curdir, "output.stl")
            mesh_data.save(curPath)
            
            from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH            
            meshMan : KooMeshManagerGMSH = KooMeshManagerGMSH(part.nodeManager, part.elementManager, self.dynaImporter.partManager,self.dynaImporter.sectionManager,self.dynaImporter.matManager,self.dynaImporter.nodeSetManager, part)
            
            nodes = part.elementManager.GetElementNodes()
            part.elementManager.RemoveAllElements()
            part.nodeManager.RemoveNodesExceptNodes(nodes)  
            
            meshMan.SetPath(curdir)
            meshMan.mesh_shape_from_stl("output.stl",minLength,curMaxLength,None,nodeMan.maxID+1, elemMan.maxID+1)
            
            # Mesh 객체 생성
            '''mesh_data = mesh.Mesh(triangles_array)
            mesh_data.save("output.stl")
            
            import trimesh

            # 메쉬 로드
            mesh = trimesh.load('output.stl')

            # Taubin smoothing 적용
            mesh_smoothed = mesh.copy()
            mesh_smoothed = trimesh.smoothing.filter_taubin(mesh_smoothed)

            # 스무딩된 메쉬 
            mesh_smoothed.export('smoothed_output.stl')'''

                
        
    def ConvertUnstructuredtoStructured(self, option):
        curPIDsStr = option["PIDS"]
        numberX = option["NX"]
        numberY = option["NY"]
        numberZ = option["NZ"]
        thicknessList = option["LayerThickness"]
        
        curPIDs = []
        for curStr in curPIDsStr:
            if "all" in curStr.lower():
                curPIDs = self.dynaImporter.partManager.parts.keys()
                break
            else:
                curPIDs.append(KooDynaInt(curStr)) 
            
        partDict = {}
        minX = minY = minZ = 1.0e10
        maxX = maxY = maxZ = -1.0e10
        curElemNodes = {}
        eidtopid = {}
        eidtopoints = {}
        eidtoMinMax = {}
        print("Find Min and Max Values")
        for curPID in curPIDs:
            part = self.dynaImporter.partManager.parts[curPID]
            partDict[curPID] = part
        
            nodeMan : NodeManager = part.nodeManager
            elemMan : ElementManager = part.elementManager
            #get boundary box
            boundaryBox =nodeMan.GetBoundingBox()
            minX = min(minX, boundaryBox[0])
            minY = min(minY, boundaryBox[1])
            minZ = min(minZ, boundaryBox[2])
            maxX = max(maxX, boundaryBox[3])
            maxY = max(maxY, boundaryBox[4])
            maxZ = max(maxZ, boundaryBox[5])
            addElemNodes = elemMan.GetElementNodes()
            curElemNodes = {**curElemNodes, **addElemNodes}
            for elemid in elemMan.elements:
                eidtopid[elemid] = curPID
                eidtopoints[elemid] = elemMan.elements[elemid].GetCenterPoint()
                eidtoMinMax[elemid] = [1.0e10, 1.0e10, 1.0e10, -1.0e10, -1.0e10, -1.0e10]
                for node in elemMan.elements[elemid].nodes:                    
                    eidtoMinMax[elemid][0] = min(eidtoMinMax[elemid][0], node.x)
                    eidtoMinMax[elemid][1] = min(eidtoMinMax[elemid][1], node.y)
                    eidtoMinMax[elemid][2] = min(eidtoMinMax[elemid][2], node.z)

                    eidtoMinMax[elemid][3] = max(eidtoMinMax[elemid][3], node.x)
                    eidtoMinMax[elemid][4] = max(eidtoMinMax[elemid][4], node.y)
                    eidtoMinMax[elemid][5] = max(eidtoMinMax[elemid][5], node.z)
                    
        print("...Finished")
        print("Analyze Thickness")
        zLocationList = [] 
        zLocationList.append(minZ)
        for i in range(len(thicknessList)):
            for j in range(numberZ):
                zLocationList.append(zLocationList[len(zLocationList)-1]+thicknessList[i]/float(numberZ))
        #zLocationList is minZ~maxZ
        for i in range(len(zLocationList)):
            zLocationList[i] = (zLocationList[i] - minZ) / zLocationList[-1]
        
        for i in range(len(zLocationList)):
            zLocationList[i] = minZ + zLocationList[i]*(maxZ-minZ)
        print("...Finished")
        
        # generate new nodes 
        dx = (maxX-minX)/numberX
        dy = (maxY-minY)/numberY
        numberZ = len(zLocationList)-1
         
        kdtree = KDTree(list(eidtopoints.values()))
        listelemids = list(eidtopoints.keys())
        
        print("Remove Old Nodes and Elements from Parts")
        
        self.dynaImporter.nodeManager.RemoveNodesExceptNodes(curElemNodes)
        for curPID in curPIDs:
            part = partDict[curPID]
            nodeMan : NodeManager = part.nodeManager
            elemMan : ElementManager = part.elementManager
            elemMan.RemoveAllElements()
        print("...Finished")
        print("Generate New Nodes")
        newNodes = {}
        newElems = {}
        maxnid = self.dynaImporter.nodeManager.maxID
        for i in range(numberX+1):
            for j in range(numberY+1):
                for k in range(numberZ+1):
                    x = minX+i*dx
                    y = minY+j*dy
                    z = zLocationList[k]
                    n = Node(maxnid+1 + i*(numberY+1)*(numberZ+1) + j*(numberZ+1) + k)
                    n.SetXYZ(x, y, z)
                    newNodes[(i,j,k)] = n
                    nodeMan.AddNode(n)
        self.dynaImporter.SyncronizeMaxID()
        maxeid = self.dynaImporter.maxEID
        print("...Finished")
        print("Make kdTree for each layer")
        # zLocationList의 범위별로 KDTree를 저장할 리스트
        filtered_kdtree_list = []
        filtered_listelemids_list = []

        # zLocationList의 각 범위별로 KDTree 생성
        for i in range(len(zLocationList) - 1):
            z_min = zLocationList[i]
            z_max = zLocationList[i + 1]
            
            # z축 범위에 해당하는 점들만 필터링
            filtered_points = {eid: point for eid, point in eidtopoints.items() if z_min <= point[2] <= z_max}
            filtered_eidtopoints = list(filtered_points.values())
            filtered_listelemids = list(filtered_points.keys())
            
            # 필터링된 점들로 새로운 KDTree 생성
            filtered_kdtree = KDTree(filtered_eidtopoints)
            
            # 리스트에 추가
            filtered_kdtree_list.append(filtered_kdtree)
            filtered_listelemids_list.append(filtered_listelemids)
        print("...Finished")
        print("Generate New Elements")
                
        dzMax = 0.0
        for k in range(numberZ):
            dzMax = max(dzMax, abs(zLocationList[k+1]-zLocationList[k]))
        distPixel = (dx*dx + dy*dy + dzMax*dzMax)**0.5

        for k in range(numberZ):
            # 중심점의 z 위치에 맞는 KDTree 선택 (only once per k iteration)
            z_min, z_max = zLocationList[k], zLocationList[k + 1]
            for idx, (z_min_val, z_max_val) in enumerate(zip(zLocationList[:-1], zLocationList[1:])):
                if z_min <= z_max_val and z_max >= z_min_val:
                    kdtree = filtered_kdtree_list[idx]
                    listelemids = filtered_listelemids_list[idx]
                    break

            for j in range(numberY):
                for i in range(numberX):
                    n1 = newNodes[(i, j, k)]
                    n2 = newNodes[(i + 1, j, k)]
                    n3 = newNodes[(i + 1, j + 1, k)]
                    n4 = newNodes[(i, j + 1, k)]
                    n5 = newNodes[(i, j, k + 1)]
                    n6 = newNodes[(i + 1, j, k + 1)]
                    n7 = newNodes[(i + 1, j + 1, k + 1)]
                    n8 = newNodes[(i, j + 1, k + 1)]
                    centerPoint = (
                        (n1.x + n2.x + n3.x + n4.x + n5.x + n6.x + n7.x + n8.x) / 8.0,
                        (n1.y + n2.y + n3.y + n4.y + n5.y + n6.y + n7.y + n8.y) / 8.0,
                        (n1.z + n2.z + n3.z + n4.z + n5.z + n6.z + n7.z + n8.z) / 8.0,
                    )

                    # 선택된 KDTree에서 가장 가까운 점 찾기
                    dist, minIndex = kdtree.query(centerPoint)
                    eid = listelemids[minIndex]
                    curPID = eidtopid[eid]
                    part = partDict[curPID]
                    # 거리가 픽셀 크기보다 작은 경우에만 요소 추가
                    cureidnodes = part.elementManager.elements[eid].nodes
                    # check center point is located in the element
                    # cureidnodes are nodes of the element, tetra or hexa
                    curMinX = n1.x
                    curMinY = n1.y
                    curMinZ = n1.z
                    curMaxX = n1.x
                    curMaxY = n1.y
                    curMaxZ = n1.z

                    curMinX = min(curMinX, n2.x)
                    curMinY = min(curMinY, n2.y)        
                    curMinZ = min(curMinZ, n2.z)
                    curMaxX = max(curMaxX, n2.x)
                    curMaxY = max(curMaxY, n2.y)
                    curMaxZ = max(curMaxZ, n2.z)

                    curMinX = min(curMinX, n3.x)
                    curMinY = min(curMinY, n3.y)
                    curMinZ = min(curMinZ, n3.z)
                    curMaxX = max(curMaxX, n3.x)
                    curMaxY = max(curMaxY, n3.y)
                    curMaxZ = max(curMaxZ, n3.z)

                    curMinX = min(curMinX, n4.x)
                    curMinY = min(curMinY, n4.y)
                    curMinZ = min(curMinZ, n4.z)
                    curMaxX = max(curMaxX, n4.x)
                    curMaxY = max(curMaxY, n4.y)
                    curMaxZ = max(curMaxZ, n4.z)

                        
                    curMinX = min(curMinX, n5.x)
                    curMinY = min(curMinY, n5.y)
                    curMinZ = min(curMinZ, n5.z)
                    curMaxX = max(curMaxX, n5.x)
                    curMaxY = max(curMaxY, n5.y)
                    curMaxZ = max(curMaxZ, n5.z)

                    curMinX = min(curMinX, n6.x)
                    curMinY = min(curMinY, n6.y)
                    curMinZ = min(curMinZ, n6.z)
                    curMaxX = max(curMaxX, n6.x)
                    curMaxY = max(curMaxY, n6.y)
                    curMaxZ = max(curMaxZ, n6.z)

                    curMinX = min(curMinX, n7.x)
                    curMinY = min(curMinY, n7.y)
                    curMinZ = min(curMinZ, n7.z)
                    curMaxX = max(curMaxX, n7.x)
                    curMaxY = max(curMaxY, n7.y)
                    curMaxZ = max(curMaxZ, n7.z)
                    
                    curMinX = min(curMinX, n8.x)
                    curMinY = min(curMinY, n8.y)
                    curMinZ = min(curMinZ, n8.z)
                    curMaxX = max(curMaxX, n8.x)
                    curMaxY = max(curMaxY, n8.y)
                    curMaxZ = max(curMaxZ, n8.z)                                                                                        
                    
                    minLocX = eidtoMinMax[eid][0]
                    minLocY = eidtoMinMax[eid][1]
                    minLocZ = eidtoMinMax[eid][2]
                    maxLocX = eidtoMinMax[eid][3]
                    maxLocY = eidtoMinMax[eid][4]
                    maxLocZ = eidtoMinMax[eid][5]                                                           
                    if dist < distPixel*0.5:
                        pass
                    else:
                        if curMinX > maxLocX or curMaxX < minLocX:
                            continue
                        if curMinY > maxLocY or curMaxY < minLocY:
                            continue
                        if curMinZ > maxLocZ or curMaxZ < minLocZ:
                            continue                                    
                    '''if centerPoint[0] > maxLocX or centerPoint[0] < minLocX or centerPoint[1] > maxLocY or centerPoint[1] < minLocY or centerPoint[2] > maxLocZ or centerPoint[2] < minLocZ:
                        pass
                    else:'''
                    part.elementManager.AddHexahedronLinearElement(
                        maxeid + 1 + k * numberY * numberX + j * numberX + i,
                        n1, n2, n3, n4, n5, n6, n7, n8
                    )
                        
        newNodesList = list(newNodes.values())
        for node in newNodesList:
            if len(node.elems) == 0:
                nodeMan.RemoveNode(node)
                
        print("...Finished")
    
    def ConvertUnstructuredtoStructuredPrev(self, option):
        curPIDsStr = option["PIDS"]
        numberX = option["NX"]
        numberY = option["NY"]
        numberZ = option["NZ"]
        curPIDs = []
        for curStr in curPIDsStr:
            if "all" in curStr.lower():
                curPIDs = self.dynaImporter.partManager.parts.keys()
                break
            else:
                curPIDs.append(KooDynaInt(curStr)) 
            
        partDict = {}
        minX = minY = minZ = 1.0e10
        maxX = maxY = maxZ = -1.0e10
        curElemNodes = {}
        eidtopid = {}
        eidtopoints = {}
        eidtoMinMax = {}
        for curPID in curPIDs:
            part = self.dynaImporter.partManager.parts[curPID]
            partDict[curPID] = part
        
            nodeMan : NodeManager = part.nodeManager
            elemMan : ElementManager = part.elementManager
            #get boundary box
            boundaryBox =nodeMan.GetBoundingBox()
            minX = min(minX, boundaryBox[0])
            minY = min(minY, boundaryBox[1])
            minZ = min(minZ, boundaryBox[2])
            maxX = max(maxX, boundaryBox[3])
            maxY = max(maxY, boundaryBox[4])
            maxZ = max(maxZ, boundaryBox[5])
            addElemNodes = elemMan.GetElementNodes()
            curElemNodes = {**curElemNodes, **addElemNodes}
            for elemid in elemMan.elements:
                eidtopid[elemid] = curPID
                eidtopoints[elemid] = elemMan.elements[elemid].GetCenterPoint()
                eidtoMinMax[elemid] = [1.0e10, 1.0e10, 1.0e10, -1.0e10, -1.0e10, -1.0e10]
                for node in elemMan.elements[elemid].nodes:                    
                    eidtoMinMax[elemid][0] = min(eidtoMinMax[elemid][0], node.x)
                    eidtoMinMax[elemid][1] = min(eidtoMinMax[elemid][1], node.y)
                    eidtoMinMax[elemid][2] = min(eidtoMinMax[elemid][2], node.z)

                    eidtoMinMax[elemid][3] = max(eidtoMinMax[elemid][3], node.x)
                    eidtoMinMax[elemid][4] = max(eidtoMinMax[elemid][4], node.y)
                    eidtoMinMax[elemid][5] = max(eidtoMinMax[elemid][5], node.z)
                    
                        
        # generate new nodes 
        dx = (maxX-minX)/numberX
        dy = (maxY-minY)/numberY
        dz = (maxZ-minZ)/numberZ
         
        kdtree = KDTree(list(eidtopoints.values()))
        listelemids = list(eidtopoints.keys())
        
        self.dynaImporter.nodeManager.RemoveNodesExceptNodes(curElemNodes)
        for curPID in curPIDs:
            part = partDict[curPID]
            nodeMan : NodeManager = part.nodeManager
            elemMan : ElementManager = part.elementManager
            elemMan.RemoveAllElements()
        
                 
        newNodes = {}
        newElems = {}
        maxnid = self.dynaImporter.nodeManager.maxID
        
        distPixel = (dx*dx + dy*dy + dz*dz)**0.5
        
        for i in range(numberX+1):
            for j in range(numberY+1):
                for k in range(numberZ+1):
                    x = minX+i*dx
                    y = minY+j*dy
                    z = minZ+k*dz
                    n = Node(maxnid+1 + i*(numberY+1)*(numberZ+1) + j*(numberZ+1) + k)
                    n.SetXYZ(x, y, z)
                    newNodes[(i,j,k)] = n
                    nodeMan.AddNode(n)
        self.dynaImporter.SyncronizeMaxID()
        maxeid = self.dynaImporter.maxEID
        for i in range(numberX):
            for j in range(numberY):
                for k in range(numberZ):
                    n1 = newNodes[(i,j,k)]
                    n2 = newNodes[(i+1,j,k)]
                    n3 = newNodes[(i+1,j+1,k)]
                    n4 = newNodes[(i,j+1,k)]
                    n5 = newNodes[(i,j,k+1)]
                    n6 = newNodes[(i+1,j,k+1)]
                    n7 = newNodes[(i+1,j+1,k+1)]
                    n8 = newNodes[(i,j+1,k+1)]
                    centerPoint = (n1.x+n2.x+n3.x+n4.x+n5.x+n6.x+n7.x+n8.x)/8.0, (n1.y+n2.y+n3.y+n4.y+n5.y+n6.y+n7.y+n8.y)/8.0, (n1.z+n2.z+n3.z+n4.z+n5.z+n6.z+n7.z+n8.z)/8.0
                    dist, minIndex = kdtree.query(centerPoint)
                    eid = listelemids[minIndex]
                    curPID = eidtopid[eid]
                    part = partDict[curPID]     
                    curMinX = n1.x
                    curMinY = n1.y
                    curMinZ = n1.z
                    curMaxX = n1.x
                    curMaxY = n1.y
                    curMaxZ = n1.z

                    curMinX = min(curMinX, n2.x)
                    curMinY = min(curMinY, n2.y)        
                    curMinZ = min(curMinZ, n2.z)
                    curMaxX = max(curMaxX, n2.x)
                    curMaxY = max(curMaxY, n2.y)
                    curMaxZ = max(curMaxZ, n2.z)

                    curMinX = min(curMinX, n3.x)
                    curMinY = min(curMinY, n3.y)
                    curMinZ = min(curMinZ, n3.z)
                    curMaxX = max(curMaxX, n3.x)
                    curMaxY = max(curMaxY, n3.y)
                    curMaxZ = max(curMaxZ, n3.z)

                    curMinX = min(curMinX, n4.x)
                    curMinY = min(curMinY, n4.y)
                    curMinZ = min(curMinZ, n4.z)
                    curMaxX = max(curMaxX, n4.x)
                    curMaxY = max(curMaxY, n4.y)
                    curMaxZ = max(curMaxZ, n4.z)

                        
                    curMinX = min(curMinX, n5.x)
                    curMinY = min(curMinY, n5.y)
                    curMinZ = min(curMinZ, n5.z)
                    curMaxX = max(curMaxX, n5.x)
                    curMaxY = max(curMaxY, n5.y)
                    curMaxZ = max(curMaxZ, n5.z)

                    curMinX = min(curMinX, n6.x)
                    curMinY = min(curMinY, n6.y)
                    curMinZ = min(curMinZ, n6.z)
                    curMaxX = max(curMaxX, n6.x)
                    curMaxY = max(curMaxY, n6.y)
                    curMaxZ = max(curMaxZ, n6.z)

                    curMinX = min(curMinX, n7.x)
                    curMinY = min(curMinY, n7.y)
                    curMinZ = min(curMinZ, n7.z)
                    curMaxX = max(curMaxX, n7.x)
                    curMaxY = max(curMaxY, n7.y)
                    curMaxZ = max(curMaxZ, n7.z)
                    
                    curMinX = min(curMinX, n8.x)
                    curMinY = min(curMinY, n8.y)
                    curMinZ = min(curMinZ, n8.z)
                    curMaxX = max(curMaxX, n8.x)
                    curMaxY = max(curMaxY, n8.y)
                    curMaxZ = max(curMaxZ, n8.z)                                                                                        
                    
                    minLocX = eidtoMinMax[eid][0]
                    minLocY = eidtoMinMax[eid][1]
                    minLocZ = eidtoMinMax[eid][2]
                    maxLocX = eidtoMinMax[eid][3]
                    maxLocY = eidtoMinMax[eid][4]
                    maxLocZ = eidtoMinMax[eid][5]                                                           
                    
                    if dist < distPixel*0.5:
                        pass
                    else:
                        if curMinX > maxLocX or curMaxX < minLocX:
                            continue
                        if curMinY > maxLocY or curMaxY < minLocY:
                            continue
                        if curMinZ > maxLocZ or curMaxZ < minLocZ:
                            continue
                        
                                        
                    '''if centerPoint[0] > maxLocX or centerPoint[0] < minLocX or centerPoint[1] > maxLocY or centerPoint[1] < minLocY or centerPoint[2] > maxLocZ or centerPoint[2] < minLocZ:                                   
                        pass
                    else:'''
                    #if dist < maxDist:
                    part.elementManager.AddHexahedronLinearElement(maxeid+1 + i*numberY*numberZ + j*numberZ + k, n1, n2, n3, n4, n5, n6, n7, n8)
                    
        newNodesList = list(newNodes.values())
        for node in newNodesList:
            if len(node.elems) == 0:
                nodeMan.RemoveNode(node)
                
    
    def ConvertHexato(self,option, layupList = [], curOption = None, filePath = None):
        curPID = option["PID"]
        optionType = option["Type"]
        dirVector = option["Vector"]
        toleranceAngle = option["ToleranceAngle"]
        self.dynaImporter.SyncronizeMaxID()          
        part = self.dynaImporter.partManager.parts[curPID]

        
        if optionType.lower() == "shell":
            self.ConvertSolidtoShell(part, dirVector, toleranceAngle)
        elif optionType.lower() == "solid":
            pass
        elif optionType.lower() == "tshell":
            self.ConvertSolidtoTShell(part, dirVector, toleranceAngle)           
        elif optionType.lower() == "solidcomp":
            self.ConvertSolidtoSolidComp(part, dirVector, toleranceAngle, layupList)
        elif optionType.lower() == "solidwithslack":
            self.ConvertSolidtoSolidwithSlack(part, dirVector, toleranceAngle, layupList, curOption, filePath)
        elif optionType.lower() == "solidstructuredzslack":
            self.ConvertSolidtoStructuredSolidwithZSlack(part, dirVector, toleranceAngle, curOption, filePath)
    
    def ConvertSolidtoStructuredSolidwithZSlack(self, part, dirVector, toleranceAngle, curOption, filePath):
        print("Convert Solid to Structured Solid with Z Slack")
        print("Direction Vector: ", dirVector)
        print("Tolerance Angle: ", toleranceAngle)
        print("PID: ", part.id)
        
        nodeMan : NodeManager = part.nodeManager
        elemMan : ElementManager = part.elementManager
        
        id_array, shifted_dict, offset = elemMan.AssignStructuredGridIndices()
        # 1. 현재 축 크기
        shape = id_array.shape  # (xSize, ySize, zSize)
        print("Structured Grid Size:", shape)

        # 2. 어떤 축이 가장 긴지 확인
        longest_axis = np.argmax(shape)

        # 3. 가장 긴 축이 0번째(x)가 되도록 순서 변경
        if longest_axis != 0:
            # 나머지 축 순서를 보존하기 위해 기존 축 순서를 회전시킴
            # 예: longest_axis==1이면 (1,2,0), longest_axis==2이면 (2,0,1)
            new_order = [(longest_axis + i) % 3 for i in range(3)]
            id_array = np.transpose(id_array, new_order)
            print("Transposed to:", new_order)
            
            
        

    def ConvertSolidtoSolidwithSlack(self, part, dirVector, toleranceAngle, layupList, option, filePath):
        print("Convert Solid to Solid with Slack")
        print("Direction Vector: ", dirVector)
        print("Tolerance Angle: ", toleranceAngle)
        print("PID: ", part.id)
           
        nodeMan : NodeManager = part.nodeManager
        elemMan : ElementManager = part.elementManager
        nodes = nodeMan.nodes
        
        normDirVector = (dirVector[0]**2+dirVector[1]**2+dirVector[2]**2)**0.5
        dirVector = (dirVector[0]/normDirVector, dirVector[1]/normDirVector, dirVector[2]/normDirVector)
        outerSegments = elemMan.GetExternalBoundary(True)
        
        print("Number of Outer Segments: ", len(outerSegments))
        segDir = {}
        segCenter = []
        segRevDir = {}
        segCenterRev = []
        toleranceCos = math.cos(math.radians(toleranceAngle))
        i = 0
        j = 0
        k = 0
        nodesDirDict = {}
        nodesRevDirDict = {}
        for seg in outerSegments:
            
            n1 = nodes[seg[0]]
            n2 = nodes[seg[1]]
            n3 = nodes[seg[2]]
            n12 = (n2.x-n1.x, n2.y-n1.y, n2.z-n1.z)
            n13 = (n3.x-n1.x, n3.y-n1.y, n3.z-n1.z)
            elemNormDir = (n12[1]*n13[2]-n12[2]*n13[1], n12[2]*n13[0]-n12[0]*n13[2], n12[0]*n13[1]-n12[1]*n13[0])
            lendir = (elemNormDir[0]**2+elemNormDir[1]**2+elemNormDir[2]**2)**0.5
            elemNormDir = (elemNormDir[0]/lendir, elemNormDir[1]/lendir, elemNormDir[2]/lendir)
            dotProduct = elemNormDir[0]*dirVector[0]+elemNormDir[1]*dirVector[1]+elemNormDir[2]*dirVector[2]
            #print(dotProduct)
            if dotProduct > toleranceCos:
                segDir[i] = seg
                segCenter.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])
                i += 1
                for m in seg:
                    if nodes[m] not in nodesDirDict:
                        nodesDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            elif dotProduct < -toleranceCos:
                segRevDir[j] = seg
                segCenterRev.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])                
                j += 1
                for m in seg:
                    if nodes[m] not in nodesRevDirDict:
                        nodesRevDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            else:
                k = k + 1
        
        print("Number of Upper Surface Segments: ", len(segDir))
        print("Number of Lower Surface Segments: ", len(segRevDir))
        print("Number of Side Surface Segments: ", k)
       
        segCenter = np.array(segCenter)
        segCenterRev = np.array(segCenterRev)
        
        nodesDir = np.array(list(nodesDirDict.values()))    
        nodesRevDir = np.array(list(nodesRevDirDict.values()))
        listnodesidTop = list(nodesDirDict.keys())
        listnodesidBottom = list(nodesRevDirDict.keys())
        
        avgLocNodesDir = np.mean(nodesDir, axis=0)
        avgLocNodesRevDir = np.mean(nodesRevDir, axis=0)
        deltaLoc = avgLocNodesRevDir - avgLocNodesDir
        # Create a KDTree from segCenterRev
        kdtree = KDTree(segCenterRev)
        kdtree = KDTree(nodesRevDir)
        revidDict = {}
        for i in range(len(nodesDir)):
            curLoc = nodesDir[i]
            curRevLoc = deltaLoc + curLoc
            dist, minIndex = kdtree.query(curRevLoc)
            curNodesDir = nodesDir[i]
            curNodesRevDir = nodesRevDir[minIndex]
            revidDict[listnodesidTop[i]] = listnodesidBottom[minIndex]
            #newPoint = (curNodesDir[0]+curNodesRevDir[0])/2.0, (curNodesDir[1]+curNodesRevDir[1])/2.0, (curNodesDir[2]+curNodesRevDir[2])/2.0
            nodesDir[i] = curNodesDir
        
        # set nodesDirDict position to new position
        print("Set Bottom Nodes")
        for i in range(len(nodesDir)):
            id = listnodesidTop[i]
            x = nodesDir[i][0]
            y = nodesDir[i][1]
            z = nodesDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)
            print("ID: ", id, "X: ", x, "Y: ", y, "Z: ", z)
        
        print("Set Top Nodes")
        for i in range(len(nodesRevDir)):
            id = listnodesidBottom[i]
            x = nodesRevDir[i][0]
            y = nodesRevDir[i][1]
            z = nodesRevDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)
            print("ID: ", id, "X: ", x, "Y: ", y, "Z: ", z)
        

        listnodesid = [] 
        listnodesid.extend(listnodesidTop)
        listnodesid.extend(listnodesidBottom)
        
       
        elemNodes = elemMan.GetElementNodes()        
        nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
        self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
        print("Solid nodes are removed")
        curElems = elemMan.elements
        self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
        elemMan.RemoveAllElements()
        print("Solid elements are removed")
                       
        newNodes = {}
            
        desiredLengthRatioOption = option["DesiredLengthRatio"]
        
        lengthRatioList = [] 
        dlrSamplesOption = desiredLengthRatioOption["Samples"]
        for i in range(len(dlrSamplesOption)):
            lengthRatioList.append(dlrSamplesOption[i])
        
        numofSamples = desiredLengthRatioOption["NumberofSamples"]
        avgLengthRatio = desiredLengthRatioOption["Average"]
        stdLengthRatio = desiredLengthRatioOption["StandardDeviation"]
        minLengthRatio = desiredLengthRatioOption["Minimum"]
        maxLengthRatio = desiredLengthRatioOption["Maximum"]
        
        for i in range(numofSamples):
            randomLengthRatio = np.random.normal(avgLengthRatio, stdLengthRatio)
            if randomLengthRatio < minLengthRatio:
                i = i - 1
                continue
            if randomLengthRatio > maxLengthRatio:
                i = i - 1
                continue             
            found = any(math.isclose(val, randomLengthRatio, rel_tol=1e-9) for val in lengthRatioList)
            if found:
                i = i - 1
                continue            
            
            lengthRatioList.append(randomLengthRatio)
            

        fnTopminX = 1.0e99
        fnTopminY = 1.0e99
        fnTopminZ = 1.0e99
        fnBotminX = 1.0e99
        fnBotminY = 1.0e99
        fnBotminZ = 1.0e99
        
        
        for j in range(len(segCenter)):
            segTop = segDir[j]
            for k in range(len(segTop)):
                tn = nodes[segTop[k]]
                bn = nodes[segRevDir[j][k]]
                fnTopminX = min(fnTopminX, tn.x)
                fnTopminY = min(fnTopminY, tn.y)
                fnTopminZ = min(fnTopminZ, tn.z)
                fnBotminX = min(fnBotminX, bn.x)
                fnBotminY = min(fnBotminY, bn.y)
                fnBotminZ = min(fnBotminZ, bn.z)
                                
        pntStart3D = [fnBotminX, fnBotminY, fnBotminZ]
        pntEnd3D = [fnTopminX, fnTopminY, fnTopminZ]
        directLength = ((pntEnd3D[0]-pntStart3D[0])**2+(pntEnd3D[1]-pntStart3D[1])**2+(pntEnd3D[2]-pntStart3D[2])**2)**0.5
        xDirVector = dirVector        
        zDirVector = option["converthexato"]["ZDirection"]
        # x dirvector from y dirvector and z dirvector
        yDirVector = (zDirVector[1]*xDirVector[2]-zDirVector[2]*xDirVector[1], zDirVector[2]*xDirVector[0]-zDirVector[0]*xDirVector[2], zDirVector[0]*xDirVector[1]-zDirVector[1]*xDirVector[0])    
        lendir = (yDirVector[0]**2+yDirVector[1]**2+yDirVector[2]**2)**0.5
        yDirVector = (yDirVector[0]/lendir, yDirVector[1]/lendir, yDirVector[2]/lendir)
        moduleManager : ModuleManager = ModuleManager()
        numPoints = 100        
        if "NumberofElements" in option:
            numPoints = option["NumberofElements"]            
        connector : ConnectorFlexible  = moduleManager.CreateConnectorFlexible3DModule("ConnectorModule", pntStart3D, pntEnd3D,xDirVector, yDirVector, zDirVector,numPoints,directLength)
        
        
        pntStart3D_loc_xAmp = pntStart3D[0]*xDirVector[0] + pntStart3D[1]*xDirVector[1] + pntStart3D[2]*xDirVector[2]
        pntStart3D_loc_yAmp = pntStart3D[0]*yDirVector[0] + pntStart3D[1]*yDirVector[1] + pntStart3D[2]*yDirVector[2]
        pntStart3D_loc_zAmp = pntStart3D[0]*zDirVector[0] + pntStart3D[1]*zDirVector[1] + pntStart3D[2]*zDirVector[2]
        
        pntEnd3D_loc_xAmp = pntEnd3D[0]*xDirVector[0] + pntEnd3D[1]*xDirVector[1] + pntEnd3D[2]*xDirVector[2]
        pntEnd3D_loc_yAmp = pntEnd3D[0]*yDirVector[0] + pntEnd3D[1]*yDirVector[1] + pntEnd3D[2]*yDirVector[2]
        pntEnd3D_loc_zAmp = pntEnd3D[0]*zDirVector[0] + pntEnd3D[1]*zDirVector[1] + pntEnd3D[2]*zDirVector[2]
        
        
        
        
        ####################### Find Constraint from Neighboring Parts ####################### 
        
        pntList = [] 
        for i in range(numPoints):
            pntList.append((pntStart3D[0] + i*(pntEnd3D[0]-pntStart3D[0])/(numPoints-1), pntStart3D[1] + i*(pntEnd3D[1]-pntStart3D[1])/(numPoints-1), 0.0))      
            
        constraints = option["Constraints"]
        pids = constraints["PIDs"]  
        
        parts = self.dynaImporter.partManager.parts
        constraintParts = []
        for i in range(len(pids)):
            constraintParts.append(parts[int(pids[i])])
        
        for i in range(len(pntList)):
            curPoint = pntList[i]
            for j in range(len(constraintParts)):
                curPart = constraintParts[j]
                
                curt = curPart.GetRayDistance(curPoint,zDirVector)
                
                if curt is not None:
                    if curt > 0:
                        upperConstraintValue = curt
                        connector.maxConstraints[i] = curt
                    elif curt < 0:
                        lowerConstraintValue = curt
                        connector.minConstraints[i] = curt
                
            
            
            

        
        
        #######################
        
        elementsadded = {}
        nodesadded = {}           
        self.dynaImporter.SyncronizeMaxID()
        for k in range(len(lengthRatioList)):
            elemMan.RemoveElements(elementsadded)
            nodeMan.RemoveNodes(nodesadded)
            curLengthRatio = lengthRatioList[k]
            print("Current Length: ", curLengthRatio*directLength)
            xVal, yVal, zVal = connector.Generate3DPoints(update=True, ndegree=3, desired_length_ratio=curLengthRatio)
            
            
            for j in range(len(segCenter)):
                segTop = segDir[j] 
            
                
                for i in range(1,len(xVal)):    
                    botPos = (xVal[i-1], yVal[i-1], zVal[i-1])
                    topPos = (xVal[i], yVal[i], zVal[i])                   
                    nodeMan = part.nodeManager
                    elemMan = part.elementManager
                    if len(segTop) == 4:                    
                        n1 = nodes[revidDict[segTop[0]]]
                        n2 = nodes[revidDict[segTop[1]]]
                        n3 = nodes[revidDict[segTop[2]]]
                        n4 = nodes[revidDict[segTop[3]]]
                        n5 = nodes[segTop[0]]
                        n6 = nodes[segTop[1]]
                        n7 = nodes[segTop[2]]
                        n8 = nodes[segTop[3]]
                        if i == 1:
                            newN1 = n1
                            newN2 = n2
                            newN3 = n3
                            newN4 = n4
                            newN5 = nodeMan.CreateNode(n1.x-pntStart3D[0]+topPos[0], n1.y-pntStart3D[1]+topPos[1], n1.z-pntStart3D[2]+topPos[2])
                            newN6 = nodeMan.CreateNode(n2.x-pntStart3D[0]+topPos[0], n2.y-pntStart3D[1]+topPos[1], n2.z-pntStart3D[2]+topPos[2])
                            newN7 = nodeMan.CreateNode(n3.x-pntStart3D[0]+topPos[0], n3.y-pntStart3D[1]+topPos[1], n3.z-pntStart3D[2]+topPos[2])
                            newN8 = nodeMan.CreateNode(n4.x-pntStart3D[0]+topPos[0], n4.y-pntStart3D[1]+topPos[1], n4.z-pntStart3D[2]+topPos[2])
                            newNodes[(i-1)*len(segCenter)+j] = [newN5, newN6, newN7, newN8]
                            nodesadded[newN5.id] = newN5
                            nodesadded[newN6.id] = newN6
                            nodesadded[newN7.id] = newN7
                            nodesadded[newN8.id] = newN8
                                                    
                        elif i == len(xVal)-1:
                            newN1, newN2, newN3, newN4 = newNodes[(i-2)*len(segCenter)+j]
                            newN5 = n5
                            newN6 = n6
                            newN7 = n7
                            newN8 = n8    
                        else:
                            newN1, newN2, newN3, newN4 = newNodes[(i-2)*len(segCenter)+j]
                            newN5 = nodeMan.CreateNode(n1.x-pntStart3D[0]+topPos[0], n1.y-pntStart3D[1]+topPos[1], n1.z-pntStart3D[2]+topPos[2])
                            newN6 = nodeMan.CreateNode(n2.x-pntStart3D[0]+topPos[0], n2.y-pntStart3D[1]+topPos[1], n2.z-pntStart3D[2]+topPos[2])
                            newN7 = nodeMan.CreateNode(n3.x-pntStart3D[0]+topPos[0], n3.y-pntStart3D[1]+topPos[1], n3.z-pntStart3D[2]+topPos[2])
                            newN8 = nodeMan.CreateNode(n4.x-pntStart3D[0]+topPos[0], n4.y-pntStart3D[1]+topPos[1], n4.z-pntStart3D[2]+topPos[2])
                            newNodes[(i-1)*len(segCenter)+j] = [newN5, newN6, newN7, newN8]
                            nodesadded[newN5.id] = newN5
                            nodesadded[newN6.id] = newN6
                            nodesadded[newN7.id] = newN7
                            nodesadded[newN8.id] = newN8
                        elem = elemMan.CreateHexahedronLinearElement(newN1, newN2, newN3, newN4, newN5, newN6, newN7, newN8)
                        elementsadded[elem.id] = elem
                                   
            elemMan.MergeElementNodeswithTolerance()
            self.dynaImporter.SyncronizeMaxID()
            
            if filePath is not None: 
                #real Length Ratio 
                curLength = 0.0 
                for i in range(len(xVal)-1):
                    curLength += ((xVal[i+1]-xVal[i])**2+(yVal[i+1]-yVal[i])**2+(zVal[i+1]-zVal[i])**2)**0.5
                curLengthRatio = curLength / directLength                
                # 5 digits exponential notation
                curLengthRatioExp = "{:.5e}".format(curLengthRatio)
                modifiedKeyword = "_SolidWithSlack_" + str(k) + "_" + str(curLengthRatioExp)
                self.WriteModifiedFile(filePath, modifiedKeyword)                
        
        print("Solid with Slack Conversion Completed")
        pass 
   
    def ConvertSolidtoSolidComp(self, part, dirVector, toleranceAngle, layupList):
        print("Convert Solid to SolidComp") 
        print("Direction Vector: ", dirVector)
        print("Tolerance Angle: ", toleranceAngle)
        print("PID: ", part.id)
        
        matList = [] 
        thkList = [] 
        eosList = [] 
        hgidList = []
        numberofElementList = [] 
        for i in range(len(layupList)):
            layup = layupList[i]
            thkList.append(KooDynaFloat(layup[0]))
            matList.append(KooDynaInt(layup[1]))
            eosList.append(KooDynaInt(layup[2]))
            hgidList.append(KooDynaInt(layup[3]))
            numberofElementList.append(KooDynaInt(layup[4]))
        
        nodeMan : NodeManager = part.nodeManager        
        elemMan : ElementManager = part.elementManager
        nodes = nodeMan.nodes
                
        normDirVector = (dirVector[0]**2+dirVector[1]**2+dirVector[2]**2)**0.5
        dirVector = (dirVector[0]/normDirVector, dirVector[1]/normDirVector, dirVector[2]/normDirVector)
        outerSegments = elemMan.GetExternalBoundary(True)
        
        print("Number of Outer Segments: ", len(outerSegments))
        segDir = {}
        segCenter = []
        segRevDir = {} 
        segCenterRev = []
        toleranceCos = math.cos(math.radians(toleranceAngle))
        i = 0 
        j = 0
        k = 0 
        nodesDirDict = {}
        nodesRevDirDict = {}
        for seg in outerSegments:
            
            n1 = nodes[seg[0]]
            n2 = nodes[seg[1]]
            n3 = nodes[seg[2]]
            n12 = (n2.x-n1.x, n2.y-n1.y, n2.z-n1.z)
            n13 = (n3.x-n1.x, n3.y-n1.y, n3.z-n1.z)
            elemNormDir = (n12[1]*n13[2]-n12[2]*n13[1], n12[2]*n13[0]-n12[0]*n13[2], n12[0]*n13[1]-n12[1]*n13[0])
            lendir = (elemNormDir[0]**2+elemNormDir[1]**2+elemNormDir[2]**2)**0.5
            elemNormDir = (elemNormDir[0]/lendir, elemNormDir[1]/lendir, elemNormDir[2]/lendir)
            dotProduct = elemNormDir[0]*dirVector[0]+elemNormDir[1]*dirVector[1]+elemNormDir[2]*dirVector[2]
            #print(dotProduct)
            if dotProduct > toleranceCos:
                segDir[i] = seg
                segCenter.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])
                i += 1
                for m in seg:
                    if nodes[m] not in nodesDirDict:
                        nodesDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            elif dotProduct < -toleranceCos:
                segRevDir[j] = seg
                segCenterRev.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])                
                j += 1
                for m in seg:
                    if nodes[m] not in nodesRevDirDict:
                        nodesRevDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            else:
                k = k + 1
        
        print("Number of Upper Surface Segments: ", len(segDir))
        print("Number of Lower Surface Segments: ", len(segRevDir))
        print("Number of Side Surface Segments: ", k)
       
        segCenter = np.array(segCenter)
        segCenterRev = np.array(segCenterRev)
        
        nodesDir = np.array(list(nodesDirDict.values()))    
        nodesRevDir = np.array(list(nodesRevDirDict.values()))
        listnodesidTop = list(nodesDirDict.keys())
        listnodesidBottom = list(nodesRevDirDict.keys())
        
        # Create a KDTree from segCenterRev
        kdtree = KDTree(segCenterRev)
        kdtree = KDTree(nodesRevDir)
        revidDict = {}
        for i in range(len(nodesDir)):
            dist, minIndex = kdtree.query(nodesDir[i])
            curNodesDir = nodesDir[i]
            curNodesRevDir = nodesRevDir[minIndex]
            revidDict[listnodesidTop[i]] = listnodesidBottom[minIndex]
            #newPoint = (curNodesDir[0]+curNodesRevDir[0])/2.0, (curNodesDir[1]+curNodesRevDir[1])/2.0, (curNodesDir[2]+curNodesRevDir[2])/2.0
            nodesDir[i] = curNodesDir
        
        # set nodesDirDict position to new position
        
        for i in range(len(nodesDir)):
            id = listnodesidTop[i]
            x = nodesDir[i][0]
            y = nodesDir[i][1]
            z = nodesDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)
        
        for i in range(len(nodesRevDir)):
            id = listnodesidBottom[i]
            x = nodesRevDir[i][0]
            y = nodesRevDir[i][1]
            z = nodesRevDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)

        listnodesid = [] 
        listnodesid.extend(listnodesidTop)
        listnodesid.extend(listnodesidBottom)
        
       
        elemNodes = elemMan.GetElementNodes()
        elemNodesShared = elemMan.GetElementNodesIncludingExternalElements(elemNodes)
        listnodesid.extend(list(elemNodesShared.keys()))
        nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
        self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
        print("Solid nodes are removed")
        curElems = elemMan.elements
        self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
        elemMan.RemoveAllElements()
        print("Solid elements are removed")
        
        print("Generate New Parts")
        newPartList = []     
        for i in range(len(layupList)):
            nodeMan = part.nodeManager
            nodeSetMan = part.nodeSetManager             
            elemMan = ElementManager(nodeMan) 
            material = self.dynaImporter.matManager.materials[matList[i]]           
            section = self.dynaImporter.sectionManager.sections[part.secid]
            newPart = KooPart(nodeMan,elemMan,material,section,nodeSetMan)
            newPart.grav = part.grav
            newPart.adpopt = part.adpopt
            newPart.tmid = part.tmid
            newPart.partType = part.partType
            newPart.modelType = part.modelType
            newPart.eosid = eosList[i]
            newPart.hgid = hgidList[i]
            newPartList.append(newPart)
            self.dynaImporter.partManager.CreatePartfromKooPart(newPart)
        self.dynaImporter.SyncronizeMaxID()
        numetoPartIDList = [] 
        posList = []        
        posList.append(0.0)
        for i in range(len(layupList)):
            for j in range(numberofElementList[i]):
                numetoPartIDList.append(i)
                posList.append(thkList[i]/numberofElementList[i] + posList[-1])
        for i in range(len(posList)):
            posList[i] = posList[i]/posList[-1]
        
        newNodes = {}
        for i in range(1,len(posList)):
            botPos = posList[i-1]
            topPos = posList[i]
            curPart = newPartList[numetoPartIDList[i-1]]
            nodeMan = curPart.nodeManager
            elemMan = curPart.elementManager
            for j in range(len(segCenter)):
                segTop = segDir[j] 
                if len(segTop) == 4:                    
                    n1 = nodes[revidDict[segTop[0]]]
                    n2 = nodes[revidDict[segTop[1]]]
                    n3 = nodes[revidDict[segTop[2]]]
                    n4 = nodes[revidDict[segTop[3]]]
                    n5 = nodes[segTop[0]]
                    n6 = nodes[segTop[1]]
                    n7 = nodes[segTop[2]]
                    n8 = nodes[segTop[3]]
                    if i == 1:
                        newN1 = n1
                        newN2 = n2
                        newN3 = n3
                        newN4 = n4
                        newN5 = nodeMan.CreateNode(n1.x*(1-topPos)+n5.x*topPos, n1.y*(1-topPos)+n5.y*topPos, n1.z*(1-topPos)+n5.z*topPos)
                        newN6 = nodeMan.CreateNode(n2.x*(1-topPos)+n6.x*topPos, n2.y*(1-topPos)+n6.y*topPos, n2.z*(1-topPos)+n6.z*topPos)
                        newN7 = nodeMan.CreateNode(n3.x*(1-topPos)+n7.x*topPos, n3.y*(1-topPos)+n7.y*topPos, n3.z*(1-topPos)+n7.z*topPos)
                        newN8 = nodeMan.CreateNode(n4.x*(1-topPos)+n8.x*topPos, n4.y*(1-topPos)+n8.y*topPos, n4.z*(1-topPos)+n8.z*topPos)
                        newNodes[(i-1)*len(segCenter)+j] = [newN5, newN6, newN7, newN8]
                    elif i == len(posList)-1:
                        newN1, newN2, newN3, newN4 = newNodes[(i-2)*len(segCenter)+j]
                        newN5 = n5
                        newN6 = n6
                        newN7 = n7
                        newN8 = n8    
                    else:
                        newN1, newN2, newN3, newN4 = newNodes[(i-2)*len(segCenter)+j]
                        newN5 = nodeMan.CreateNode(n1.x*(1-topPos)+n5.x*topPos, n1.y*(1-topPos)+n5.y*topPos, n1.z*(1-topPos)+n5.z*topPos)
                        newN6 = nodeMan.CreateNode(n2.x*(1-topPos)+n6.x*topPos, n2.y*(1-topPos)+n6.y*topPos, n2.z*(1-topPos)+n6.z*topPos)
                        newN7 = nodeMan.CreateNode(n3.x*(1-topPos)+n7.x*topPos, n3.y*(1-topPos)+n7.y*topPos, n3.z*(1-topPos)+n7.z*topPos)
                        newN8 = nodeMan.CreateNode(n4.x*(1-topPos)+n8.x*topPos, n4.y*(1-topPos)+n8.y*topPos, n4.z*(1-topPos)+n8.z*topPos)
                        newNodes[(i-1)*len(segCenter)+j] = [newN5, newN6, newN7, newN8]
                    elemMan.CreateHexahedronLinearElement(newN1, newN2, newN3, newN4, newN5, newN6, newN7, newN8)
            self.dynaImporter.SyncronizeMaxID()
        
        psid = part.id
        self.dynaImporter.partManager.RemovePart(part.id)
        
        pids = []
        
        print("Part Set ID: ", psid)
        for i in range(len(newPartList)):
            part = newPartList[i]
            pids.append(part.id)
            print("Part ID: ", part.id)
        print("Part Set is Created")
        newPartSet = self.dynaImporter.partManager.CreatePartSetwithID(psid,0.0,0.0,0.0,0.0,"MECH",pids,"PartID{id}'s Set".format(id=psid))
        
        self.dynaImporter.contactManager.ChangePartIDtoPartSetID(psid,psid)    
    
        print("Solid to Solid Composite Conversion Completed") 
        
        
    
    def ConvertSolidtoTShell(self, part, dirVector, toleranceAngle):
        print("Convert Solid to Shell")
        print("Direction Vector: ", dirVector)
        print("Tolerance Angle: ", toleranceAngle)
        print("PID: ", part.id)
        prevSection = part.section 
        newSection =self.dynaImporter.sectionManager.CreateTShellSection("New TShell")
        part.SetSection(newSection)
              
         
        
        self.dynaImporter.SyncronizeMaxID()  
        nodeMan : NodeManager = part.nodeManager        
        elemMan : ElementManager = part.elementManager
        nodes = nodeMan.nodes
                
        normDirVector = (dirVector[0]**2+dirVector[1]**2+dirVector[2]**2)**0.5
        dirVector = (dirVector[0]/normDirVector, dirVector[1]/normDirVector, dirVector[2]/normDirVector)
        outerSegments = elemMan.GetExternalBoundary(True)
        
        print("Number of Outer Segments: ", len(outerSegments))
        segDir = {}
        segCenter = []
        segRevDir = {} 
        segCenterRev = []
        toleranceCos = math.cos(math.radians(toleranceAngle))
        i = 0 
        j = 0
        k = 0 
        nodesDirDict = {}
        nodesRevDirDict = {}
        for seg in outerSegments:
            
            n1 = nodes[seg[0]]
            n2 = nodes[seg[1]]
            n3 = nodes[seg[2]]
            n12 = (n2.x-n1.x, n2.y-n1.y, n2.z-n1.z)
            n13 = (n3.x-n1.x, n3.y-n1.y, n3.z-n1.z)
            elemNormDir = (n12[1]*n13[2]-n12[2]*n13[1], n12[2]*n13[0]-n12[0]*n13[2], n12[0]*n13[1]-n12[1]*n13[0])
            lendir = (elemNormDir[0]**2+elemNormDir[1]**2+elemNormDir[2]**2)**0.5
            elemNormDir = (elemNormDir[0]/lendir, elemNormDir[1]/lendir, elemNormDir[2]/lendir)
            dotProduct = elemNormDir[0]*dirVector[0]+elemNormDir[1]*dirVector[1]+elemNormDir[2]*dirVector[2]
            #print(dotProduct)
            if dotProduct > toleranceCos:
                segDir[i] = seg
                segCenter.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])
                i += 1
                for m in seg:
                    if nodes[m] not in nodesDirDict:
                        nodesDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            elif dotProduct < -toleranceCos:
                segRevDir[j] = seg
                segCenterRev.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])                
                j += 1
                for m in seg:
                    if nodes[m] not in nodesRevDirDict:
                        nodesRevDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            else:
                k = k + 1
        
        print("Number of Upper Surface Segments: ", len(segDir))
        print("Number of Lower Surface Segments: ", len(segRevDir))
        print("Number of Side Surface Segments: ", k)
        
        '''# closest i to j, optimize 
        for i in range(len(segDir)):
            minDist = 1.0e10
            minIndex = 0
            for j in range(len(segRevDir)):
                dist = (segCenter[i][0]-segCenterRev[j][0])**2+(segCenter[i][1]-segCenterRev[j][1])**2+(segCenter[i][2]-segCenterRev[j][2])**2
                if dist < minDist:
                    minDist = dist
                    minIndex = j
            print("Closest Segment: ", i, minIndex)'''
        segCenter = np.array(segCenter)
        segCenterRev = np.array(segCenterRev)
        
        nodesDir = np.array(list(nodesDirDict.values()))    
        nodesRevDir = np.array(list(nodesRevDirDict.values()))
        listnodesidTop = list(nodesDirDict.keys())
        listnodesidBottom = list(nodesRevDirDict.keys())
        
        # Create a KDTree from segCenterRev
        kdtree = KDTree(segCenterRev)
        kdtree = KDTree(nodesRevDir)
        revidDict = {}
        for i in range(len(nodesDir)):
            dist, minIndex = kdtree.query(nodesDir[i])
            curNodesDir = nodesDir[i]
            curNodesRevDir = nodesRevDir[minIndex]
            revidDict[listnodesidTop[i]] = listnodesidBottom[minIndex]
            #newPoint = (curNodesDir[0]+curNodesRevDir[0])/2.0, (curNodesDir[1]+curNodesRevDir[1])/2.0, (curNodesDir[2]+curNodesRevDir[2])/2.0
            nodesDir[i] = curNodesDir
        
        # set nodesDirDict position to new position
        
        for i in range(len(nodesDir)):
            id = listnodesidTop[i]
            x = nodesDir[i][0]
            y = nodesDir[i][1]
            z = nodesDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)
        
        for i in range(len(nodesRevDir)):
            id = listnodesidBottom[i]
            x = nodesRevDir[i][0]
            y = nodesRevDir[i][1]
            z = nodesRevDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)

        listnodesid = [] 
        listnodesid.extend(listnodesidTop)
        listnodesid.extend(listnodesidBottom)
        
       
        elemNodes = elemMan.GetElementNodes()        
        nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
        self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
        print("Solid nodes are removed")
        curElems = elemMan.elements
        
        self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
        
        elemMan.RemoveAllElements()        
        print("Solid elements are removed")
        
        print("Generate New Elements")
        
        self.dynaImporter.SyncronizeMaxID()
        '''if len(elemMan.sets) >0:
            curSet = elemMan.sets[elemMan.maxSID]
        else:
            curSet = elemMan.CreateSolidSet()
            self.dynaImporter.partManager.elementManager.RemoveAllElements  
        '''
        
        for i in range(len(segCenter)):
            segTop = segDir[i] 
            if len(segTop) == 4:
                n1 = nodes[segTop[0]]
                n2 = nodes[segTop[1]]
                n3 = nodes[segTop[2]]
                n4 = nodes[segTop[3]]
                n5 = nodes[revidDict[segTop[0]]]
                n6 = nodes[revidDict[segTop[1]]]
                n7 = nodes[revidDict[segTop[2]]]
                n8 = nodes[revidDict[segTop[3]]]
                elemMan.CreateHexahedronLinearElement(n5, n6, n7, n8, n1, n2, n3, n4)
        
        elemMan.SetTShellMode(True)
        print("Solid to TShell Conversion Completed")  
        
        
        
    
    def ConvertSolidtoShell(self, part, dirVector, toleranceAngle):        
        
        print("Convert Solid to Shell")
        print("Direction Vector: ", dirVector)
        print("Tolerance Angle: ", toleranceAngle)
        print("PID: ", part.id)
        
        nodeMan : NodeManager = part.nodeManager        
        elemMan : ElementManager = part.elementManager
        nodes = nodeMan.nodes
                
        normDirVector = (dirVector[0]**2+dirVector[1]**2+dirVector[2]**2)**0.5
        dirVector = (dirVector[0]/normDirVector, dirVector[1]/normDirVector, dirVector[2]/normDirVector)
        outerSegments = elemMan.GetExternalBoundary(True)
        
        print("Number of Outer Segments: ", len(outerSegments))
        segDir = {}
        segCenter = []
        segRevDir = {} 
        segCenterRev = []
        toleranceCos = math.cos(math.radians(toleranceAngle))
        i = 0 
        j = 0
        k = 0 
        nodesDirDict = {}
        nodesRevDirDict = {}
        for seg in outerSegments:
            
            n1 = nodes[seg[0]]
            n2 = nodes[seg[1]]
            n3 = nodes[seg[2]]
            n12 = (n2.x-n1.x, n2.y-n1.y, n2.z-n1.z)
            n13 = (n3.x-n1.x, n3.y-n1.y, n3.z-n1.z)
            elemNormDir = (n12[1]*n13[2]-n12[2]*n13[1], n12[2]*n13[0]-n12[0]*n13[2], n12[0]*n13[1]-n12[1]*n13[0])
            lendir = (elemNormDir[0]**2+elemNormDir[1]**2+elemNormDir[2]**2)**0.5
            elemNormDir = (elemNormDir[0]/lendir, elemNormDir[1]/lendir, elemNormDir[2]/lendir)
            dotProduct = elemNormDir[0]*dirVector[0]+elemNormDir[1]*dirVector[1]+elemNormDir[2]*dirVector[2]
            #print(dotProduct)
            if dotProduct > toleranceCos:
                segDir[i] = seg
                segCenter.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])
                i += 1
                for m in seg:
                    if nodes[m] not in nodesDirDict:
                        nodesDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            elif dotProduct < -toleranceCos:
                segRevDir[j] = seg
                segCenterRev.append([(n1.x+n2.x+n3.x)/3.0, (n1.y+n2.y+n3.y)/3.0, (n1.z+n2.z+n3.z)/3.0])                
                j += 1
                for m in seg:
                    if nodes[m] not in nodesRevDirDict:
                        nodesRevDirDict[m] = (nodes[m].x, nodes[m].y, nodes[m].z)
            else:
                k = k + 1
        
        print("Number of Upper Surface Segments: ", len(segDir))
        print("Number of Lower Surface Segments: ", len(segRevDir))
        print("Number of Side Surface Segments: ", k)
        
        '''# closest i to j, optimize 
        for i in range(len(segDir)):
            minDist = 1.0e10
            minIndex = 0
            for j in range(len(segRevDir)):
                dist = (segCenter[i][0]-segCenterRev[j][0])**2+(segCenter[i][1]-segCenterRev[j][1])**2+(segCenter[i][2]-segCenterRev[j][2])**2
                if dist < minDist:
                    minDist = dist
                    minIndex = j
            print("Closest Segment: ", i, minIndex)'''
        segCenter = np.array(segCenter)
        segCenterRev = np.array(segCenterRev)
        
        nodesDir = np.array(list(nodesDirDict.values()))    
        nodesRevDir = np.array(list(nodesRevDirDict.values()))
        

        # Create a KDTree from segCenterRev
        kdtree = KDTree(segCenterRev)
        kdtree = KDTree(nodesRevDir)
        for i in range(len(nodesDir)):
            dist, minIndex = kdtree.query(nodesDir[i])
            curNodesDir = nodesDir[i]
            curNodesRevDir = nodesRevDir[minIndex]
            newPoint = (curNodesDir[0]+curNodesRevDir[0])/2.0, (curNodesDir[1]+curNodesRevDir[1])/2.0, (curNodesDir[2]+curNodesRevDir[2])/2.0
            nodesDir[i] = newPoint
        
        # set nodesDirDict position to new position
        listnodesid = list(nodesDirDict.keys())
        for i in range(len(nodesDir)):
            id = listnodesid[i]
            x = nodesDir[i][0]
            y = nodesDir[i][1]
            z = nodesDir[i][2]
            n = Node(id)
            n.SetXYZ(x, y, z)
            nodeMan.AddNode(n)

        
       
        elemNodes = elemMan.GetElementNodes()        
        nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
        self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
        print("Solid nodes are removed")
        curElems = elemMan.elements
        
        self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
        elemMan.RemoveAllElements()
        
        print("Solid elements are removed")
        
        print("Generate New Elements")
        self.dynaImporter.SyncronizeMaxID()
        
        for i in range(len(segCenter)):
            segTop = segDir[i] 
            if len(segTop) == 4:
                n1 = nodes[segTop[0]]
                n2 = nodes[segTop[1]]
                n3 = nodes[segTop[2]]
                n4 = nodes[segTop[3]]
                elemMan.CreateQuadrangleLinearElement(n1, n2, n3, n4)
            elif len(segTop) == 3:
                n1 = nodes[segTop[0]]
                n2 = nodes[segTop[1]]
                n3 = nodes[segTop[2]]
                elemMan.CreateTriangleLinearElement(n1, n2, n3)
            
        print("Solid to Shell Conversion Completed")        
            
    def ConvertParttoPartComp(self, partCompKeyword):
        
        print("Convert Part to PartComp")
        print("PartComp Keyword is provided.")
        
        part = self.dynaImporter.partManager.AddPartfromDyna(partCompKeyword)
        
        print("Part to PartComp Conversion Completed")
        
        return part
    
    def SetControlandDatabaseExplicit(self, tFinal, dt):
        ENDTIM = tFinal
        ENDCYC = 0
        DTMIN = 1.0E-10
        ENDENG = 0.0
        ENDMAS = 10000000.0
        NOSOL = 0
        self.dynaImporter.controlManager.SetControlTermination(ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL)
        
        DTINIT = 0.0
        TSSFAC = 0.7
        ISDO = 0
        TSLIMT = 0.0
        DT2MS = 0.0
        LCTM = 0 
        ERODE = 1
        MSIST = 0 
        self.dynaImporter.controlManager.SetControlTimeStep(DTINIT, TSSFAC, ISDO, TSLIMT, DT2MS, LCTM, ERODE, MSIST)
        
        IHQ = 5
        qh = 0.1
        self.dynaImporter.controlManager.SetControlHourglass(IHQ, qh)
        
        binary = 1
        lcur = 0
        ioopt = 1
        self.dynaImporter.databaseManager.SetDatabaseNodout(dt, binary, lcur, ioopt)
        self.dynaImporter.databaseManager.SetDatabaseElout(dt, binary, lcur, ioopt)
        DTCYCL = dt
        LCDT = ""
        BEAM = 0
        NPLTC = int(tFinal/dt)
        PSETID = 0
        CID = 0
        self.dynaImporter.databaseManager.SetDatabaseBinaryD3plot(DTCYCL,LCDT,BEAM,NPLTC,PSETID,CID)
        
        
    
    def DropAttitude(self, option, filePath):
        fileName = os.path.basename(filePath)
        RxList = option["EulerRolling"]
        RyList = option["EulerPitching"]
        RzList = option["EulerYawing"]
        heightList = option["Height"]
        VxList = option["InitialVelocityX"]
        VyList = option["InitialVelocityY"]
        VzList = option["InitialVelocityZ"]
        wxList = option["InitialAngularVelocityX"]
        wyList = option["InitialAngularVelocityY"]
        wzList = option["InitialAngularVelocityZ"]
        runids = option["runid"]
        offset_distance = option["OffsetDistance"]
        rho = option["Density"]
        E = option["YoungsModulus"]
        nu = option["PoissonRatio"]

        dt = option["DT"]
        tFinal = option["TFinal"]

        dropSurface = option["DropSurface"]

        if dt != 0.0 and tFinal != 0.0:
            self.SetControlandDatabaseExplicit(tFinal, dt)


        # Select All Nodes as node set
        nodes = self.dynaImporter.nodeManager.nodes
        nodeSet = self.dynaImporter.nodeSetManager.CreateNodeSet("AllNodes")
        nodeSet.AddNodesfromDict(nodes)
        nsid = nodeSet.sid

        nodeSetFixed = self.dynaImporter.nodeSetManager.CreateNodeSet("BottomFix")
        spcBoundary = self.dynaImporter.boundaryNodeManager.CreateBoundarySPCNodeSet(nodeSetFixed,0,1,1,1,1,1,1,"FIXED")          


        section = self.dynaImporter.sectionManager.CreateSolidSection("RigidWall",1)

        material = self.dynaImporter.matManager.CreateElasticMaterial("RigidWall", rho, E, nu)

        boundingBox = self.dynaImporter.nodeManager.GetBoundingBox()
        xLength = boundingBox[3] - boundingBox[0]
        yLength = boundingBox[4] - boundingBox[1]
        zLength = boundingBox[5] - boundingBox[2]

        print("Bound Box ", boundingBox)

        self.dynaImporter.nodeManager.MoveNodes(-boundingBox[0]-xLength/2.0, -boundingBox[1]-yLength/2.0, -boundingBox[2]-zLength/2.0) 
        boundingBox = self.dynaImporter.nodeManager.GetBoundingBox()
        print("Bound Box ", boundingBox)
        xLength = max(xLength, yLength, zLength)*6.0
        yLength = xLength
        zLength = xLength
        numX = 10
        numY = 10
        numZ = 10
        roughnessMode = "Random"
        RMax = 0.0
        ShapeFactor = 0.0


        if dropSurface[0] == "Plane":
            xLength = dropSurface[1]
            yLength = dropSurface[2]
            zLength = dropSurface[3]
            numX = dropSurface[4]
            numY = dropSurface[5]
            numZ = dropSurface[6]
            if xLength == 0.0 or yLength == 0.0 or zLength == 0.0:
                xLength = boundingBox[3] - boundingBox[0]
                yLength = boundingBox[4] - boundingBox[1]
                zLength = boundingBox[5] - boundingBox[2]
                xLength = max(xLength, yLength, zLength)*1.5
                yLength = xLength
                zLength = xLength
        elif dropSurface[0] == "PlanewithRoughness":
            xLength = dropSurface[1]
            yLength = dropSurface[2]
            zLength = dropSurface[3]
            numX = dropSurface[4]
            numY = dropSurface[5]
            numZ = dropSurface[6]
            roughnessMode = dropSurface[7]
            # Random, XRandom, YRandom, XSin, YSin, XYSin
            RMax = dropSurface[8]
            ShapeFactor = dropSurface[9]
            ShapeFactor2 = dropSurface[10]
        part = None
        initV = None
        surfacetosurfaceContact = None



        # Generate Part Set
        partSet : PartSet = self.dynaImporter.partManager.CreatePartSet(name="Dynamic Relaxation Set")
        for pid, part in self.dynaImporter.partManager.parts.items():
            partSet.AddPart(pid)
        self.dynaImporter.additionalManager.CreateInterfaceSpringbackLSDyna(partSet.psid)
        outPathListFile = None
        if len(self.metaDirectoryPath) > 0:
            #first character
            if self.metaDirectoryPath[0] == "/":
                modifiedKeyword = self.metaDirectoryPath
            else:
                path = os.getcwd()
                modifiedKeyword = os.path.join(path,self.metaDirectoryPath)
            modifiedKeyword = os.path.join(modifiedKeyword,self.dynaImporter.metaData["model_name"])
            modifiedKeyword = os.path.join(modifiedKeyword,self.dynaImporter.metaData["stage"])
            modifiedKeyword = os.path.join(modifiedKeyword,"{0:03d}_FullAngleDrop".format(self.step))

            folderPath = modifiedKeyword
            if not os.path.exists(folderPath):
                os.makedirs(folderPath)
            outputPathListFileName = os.path.join(folderPath,"outputPathList.txt")

            outPathListFile = open(outputPathListFileName, 'w')


        for i in range(len(RxList)):
            if i != 0:
                nodes = part.elementManager.GetElementNodes()
                part.elementManager.RemoveAllElements()
                part.nodeManager.RemoveNodesExceptNodes(nodes)
                if surfacetosurfaceContact is not None:
                    self.dynaImporter.contactManager.RemoveContact(surfacetosurfaceContact)
                self.dynaImporter.partManager.RemovePart(part.id)
                self.dynaImporter.initialManager.RemoveInitial(initV.id)
                if nodeSetFixed != None:
                    nodeSetFixed.Clear()
                self.dynaImporter.additionalManager.d2r_automatics.clear()

            self.dynaImporter.SyncronizeMaxID()
            RxOrigin = RxList[i]
            RyOrigin = RyList[i]
            RzOrigin = RzList[i]
            height = heightList[i]
            Vx = VxList[i]
            Vy = VyList[i]
            Vz = VzList[i]
            wx = wxList[i]
            wy = wyList[i]
            wz = wzList[i]

            default_x_direction = [1.0, 0.0 ,0.0]
            default_y_direction = [0.0, 1.0, 0.0]
            default_plane_normal = [0.0, 0.0, 1.0]
            initial_velocity = [Vx, Vy, Vz]
            angular_velocity = [wx, wy, wz]
            # inverse rotation for plane normal
            Rx = -RxOrigin*3.141592653589793/180.0
            Ry = -RyOrigin*3.141592653589793/180.0
            Rz = -RzOrigin*3.141592653589793/180.0

            # Apply Euler Angles
            # Rotation Matrix
            # R = Rz * Ry * Rx
            RotMatx = np.array([[1, 0, 0], [0, math.cos(Rx), -math.sin(Rx)], [0, math.sin(Rx), math.cos(Rx)]])
            RotMaty = np.array([[math.cos(Ry), 0, math.sin(Ry)], [0, 1, 0], [-math.sin(Ry), 0, math.cos(Ry)]])
            RotMatz = np.array([[math.cos(Rz), -math.sin(Rz), 0], [math.sin(Rz), math.cos(Rz), 0], [0, 0, 1]])
            RotMat = np.dot(RotMatz, np.dot(RotMaty, RotMatx))

            # normal vector rotation
            x_direction = np.dot(RotMat, default_x_direction)
            y_direction = np.dot(RotMat, default_y_direction)
            z_direction = np.dot(RotMat, default_plane_normal)



            print("X Direction : ", x_direction)
            print("Y Direction : ", y_direction)
            print("Z Direction : ", z_direction)
            # velocity vector rotation
            velocity = np.dot(RotMat, initial_velocity)
            pure_velocity = velocity
            print("Rotated Velocity : ", velocity)
            if height > 100:
                velocity_from_height = [0.0, 0.0, -np.sqrt(2.0*9810.0*height)]
            else:
                velocity_from_height = [0.0, 0.0, -np.sqrt(2.0*9.81*height)]
            velocity_from_height = np.dot(RotMat, velocity_from_height)
            print("Rotated Velocity from Height", velocity_from_height)

            velocity = velocity + velocity_from_height
            # angular velocity vector rotation
            angular_velocity = np.dot(RotMat, angular_velocity)

            wAmplification = np.linalg.norm(angular_velocity)

            minNode, maxNode = self.dynaImporter.nodeManager.FindFarthestNodes(z_direction)

            impactPoint = [minNode.x, minNode.y, minNode.z]

            z_direction = -z_direction
            print("Z direction :", z_direction)
            print("Impact Point [", impactPoint[0],",", impactPoint[1],"," ,  impactPoint[2], "]")
            impactPoint = [impactPoint[0]+z_direction[0]*offset_distance, impactPoint[1]+z_direction[1]*offset_distance, impactPoint[2]+z_direction[2]*offset_distance]
            print("Impact Point [", impactPoint[0],",", impactPoint[1],"," ,  impactPoint[2], "]")
            initV = self.dynaImporter.initialManager.CreateInitialVelocity(nsid,0,0,0,0, velocity[0],velocity[1],velocity[2],angular_velocity[0],angular_velocity[1],angular_velocity[2],0.0,0.0,0.0,0.0,0.0,0.0)

            part = self.dynaImporter.partManager.AddSolidPart(self.dynaImporter.nodeManager, None, section, material)
            self.dynaImporter.SyncronizeMaxID()
            if dropSurface[0] == "Plane":

                nsFixed = part.elementManager.CreateImpactBox(impactPoint,z_direction, x_direction,xLength,yLength,zLength,numX,numY,numZ) 
                nodeSetFixed.AddNodesfromDict(nsFixed)
            elif dropSurface[0] == "PlanewithRoughness":
                nsFixed = part.elementManager.CreateImpactBoxwithRoughness(impactPoint,z_direction, x_direction,xLength,yLength,zLength,numX,numY,numZ, roughnessMode, RMax, ShapeFactor, ShapeFactor2)
                nodeSetFixed.AddNodesfromDict(nsFixed)

            SSID = 0
            MSID = part.id
            SSTYP = 5
            MSTYP = 3
            SBOXID = 0
            MBOXID = 0
            SPR = 0
            MPR = 0
            FS = 0.0
            FD = 0.0
            DC = 0.0
            VC = 0.0
            VDC = 5.0
            PENCHK = 0
            BT = 0.00
            DT = 1.00000E20
            SFS = ""
            SFM = ""
            SST = ""
            MST = ""
            SFST = ""
            SFMT = ""
            FSF = ""
            VSF = ""
            surfacetosurfaceContact = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            surfacetosurfaceContact.SetOptCardA(2)

            # DeformableToRigid Paired Switch
            if option.get("DeformableToRigid", False):
                cid = surfacetosurfaceContact.cid
                wall_pid = part.id
                # SWSET 20: contact force=0 → D2R (first)
                self.dynaImporter.additionalManager.CreateDeformableToRigidAutomatic(
                    swset=20, code=2, entno=cid, relsw=10, paired=1,
                    d2r_pids=[(wall_pid, 0)], r2d_pids=[])
                # SWSET 10: contact force!=0 → R2D (second)
                self.dynaImporter.additionalManager.CreateDeformableToRigidAutomatic(
                    swset=10, code=4, entno=cid, relsw=20, paired=-1,
                    d2r_pids=[], r2d_pids=[wall_pid])

            self.dynaImporter.metaData["scenario_mode"] = "DropAttitude"
            self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["pitch"] = RyOrigin
            self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["roll"] = RxOrigin
            self.dynaImporter.metaData["initial_conditions"]["orientation_euler_deg"]["yaw"] = RzOrigin
            self.dynaImporter.metaData["initial_conditions"]["velocity"][0] = pure_velocity[0]
            self.dynaImporter.metaData["initial_conditions"]["velocity"][1] = pure_velocity[1]
            self.dynaImporter.metaData["initial_conditions"]["velocity"][2] = pure_velocity[2]
            self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][0] = angular_velocity[0]
            self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][1] = angular_velocity[1]   
            self.dynaImporter.metaData["initial_conditions"]["angular_velocity"][2] = angular_velocity[2]
            self.dynaImporter.metaData["initial_conditions"]["drop_height"]= height
            if self.runDirectoryMode == True:
                if len(RxList) >= 1:
                    if len(runids)>i:
                        run_id = runids[i]
                    else:
                        run_id = self.dynaImporter.GenerateRunID()
                    if len(self.runDirectoryPath) == 0:
                        modifiedKeyword = os.path.join(filePath.replace(".k",""), "Run_" + run_id)
                    else:
                        if self.metaDirectoryPath[0] == "/":
                            # 절대 경로가 주어지면 그 경로를 그대로 사용 (run_id 추가 안함)
                            modifiedKeyword = self.metaDirectoryPath
                        else:
                            path = os.getcwd()
                            modifiedKeyword = os.path.join(path,self.runDirectoryPath)
                            modifiedKeyword = os.path.join(modifiedKeyword, "Run_" + run_id)

                    folderPath = modifiedKeyword
                    if not os.path.exists(folderPath):
                        os.makedirs(folderPath)
                    outputFolderPath = os.path.join(folderPath, "Output")
                    if not os.path.exists(outputFolderPath):
                        os.makedirs(outputFolderPath)

                    dynamicRelaxPath = os.path.join(folderPath, "DynamicRelaxation")
                    if not os.path.exists(dynamicRelaxPath):
                        os.makedirs(dynamicRelaxPath)


                    if len(self.runDirectoryPath) == 0:
                        modifiedKeyword = os.path.join(modifiedKeyword, fileName)
                    else:
                        modifiedKeyword = os.path.join(modifiedKeyword, "DropSet")
                    modifiedKeyword = modifiedKeyword.strip()
                    self.WriteModifiedFile(modifiedKeyword, "", True)

                    dynainPath = os.path.join(outputFolderPath, "dynain")
                    dynaintoinitialPath = os.path.join(dynamicRelaxPath, "dynaintoinitial.txt")
                    with open(dynaintoinitialPath, "w") as f:
                        f.write("*Inputfile\n")
                        f.write("DropSet.k\n")
                        f.write("*Mode\n")
                        f.write("DYNAIN_TO_INITIAL,1\n")
                        f.write("**DynainPath,")
                        f.write(dynainPath)
                        f.write("\n")
                        f.write("*IncludeStress,True\n")
                        f.write("*RemoveDynamicRelaxation,True\n")
                        f.write("*MovetoOriginAutomatic,True\n")
                        f.write("*RemovePartbyID,")
                        f.write(str(part.id))
                        f.write("\n")
                        f.write("*RemoveContactbyID,")
                        f.write(str(surfacetosurfaceContact.cid))
                        f.write("\n")
                        f.write("**EndDynainToInitial\n")
                        f.write("*End\n")



                    print("Drop Attitude ", i+1, " is Created")
                    if outPathListFile is not None:
                        if self.runDirectoryPath[0] == "/":
                            writePath = os.path.join(self.runDirectoryPath, "Run_"+ run_id, "DropSet.k")
                        else:
                            path = os.getcwd()
                            writePath = os.path.join(path,self.runDirectoryPath, "Run_"+ run_id, "DropSet.k")                        
                        writePath = writePath.replace("\\","/")
                        outPathListFile.write(writePath)
                        outPathListFile.write("\n")

                pass
            else:
                if len(RxList) > 1:
                    modifiedKeyword = "_" + format(i+1,'03d') + "_"
                    modifiedKeyword += "DA_"
                    modifiedKeyword += "EX_" + format(RxOrigin, '.3f')
                    modifiedKeyword += "_EY_" + format(RyOrigin, '.3f')
                    modifiedKeyword += "_EZ_" + format(RzOrigin, '.3f')
                    modifiedKeyword += "_H_" + format(height, '.3f')
                    modifiedKeyword += "_VX_" + format(Vx, '.3f')
                    modifiedKeyword += "_VY_" + format(Vy, '.3f')
                    modifiedKeyword += "_VZ_" + format(Vz, '.3f')
                    modifiedKeyword += "_WX_" + format(wx, '.3f')
                    modifiedKeyword += "_WY_" + format(wy, '.3f')
                    modifiedKeyword += "_WZ_" + format(wz, '.3f')
                    modifiedKeyword = modifiedKeyword.strip()
                    self.WriteModifiedFile(filePath, modifiedKeyword)
                    print("Drop Attitude ", i+1, " is Created")
        if outPathListFile is not None:
            outPathListFile.close()

    def Transform(self, option):
        nodeMan : NodeManager = self.dynaImporter.nodeManager
        for i in range(len(option)):
            curOption = option[i]
            curOptionMode = curOption[0]
            if curOptionMode.lower() == "translation":
                tx = curOption[1]
                ty = curOption[2]
                tz = curOption[3]
                nodeMan.MoveNodes(tx, ty, tz)
            elif curOptionMode.lower() == "rotation":
                angleX = curOption[1]
                angleY = curOption[2]
                angleZ = curOption[3]
                trsfX : gp_Trsf = gp_Trsf()
                axX = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(1,0,0))
                trsfX.SetRotation(axX, math.radians(angleX))
                trsfY : gp_Trsf = gp_Trsf()
                axY = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,1,0))
                trsfY.SetRotation(axY, math.radians(angleY))
                trsfZ : gp_Trsf = gp_Trsf()
                axZ = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1))
                trsfZ.SetRotation(axZ, math.radians(angleZ))
                combinedTrsf = trsfX.Multiplied(trsfY)
                combinedTrsf = combinedTrsf.Multiplied(trsfZ)
                nodeMan.Transform(combinedTrsf)
            elif curOptionMode.lower() == "scale":
                sx = curOption[1]
                sy = curOption[2]
                sz = curOption[3]
                nodeMan.Scaling(sx, sy, sz)
            elif curOptionMode.lower() == "mirror":
                mode = curOption[1]
                
                if mode.lower() == "xy":
                    trsf : gp_Trsf = gp_Trsf()
                    trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,0,1)))
                    for id in self.dynaImporter.nodeManager.nodes:
                        self.dynaImporter.nodeManager.nodes[id].Transform(trsf)
                    for id in self.dynaImporter.partManager.parts:
                        elemMan : ElementManager = self.dynaImporter.partManager.parts[id].elementManager
                        elemMan.SetMirrorConnectivityXYPlane()
                elif mode.lower() == "yz":
                    trsf : gp_Trsf = gp_Trsf()
                    trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(1,0,0)))
                    for id in self.dynaImporter.nodeManager.nodes:
                        self.dynaImporter.nodeManager.nodes[id].Transform(trsf)
                    for id in self.dynaImporter.partManager.parts:
                        elemMan : ElementManager = self.dynaImporter.partManager.parts[id].elementManager
                        elemMan.SetMirrorConnectivityYZPlane()
                elif mode.lower() == "xz":
                    trsf : gp_Trsf = gp_Trsf()
                    trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(0,1,0)))
                    for id in self.dynaImporter.nodeManager.nodes:
                        self.dynaImporter.nodeManager.nodes[id].Transform(trsf)
                    for id in self.dynaImporter.partManager.parts:
                        elemMan : ElementManager = self.dynaImporter.partManager.parts[id].elementManager
                        elemMan.SetMirrorConnectivityXZPlane()
            elif curOptionMode.lower() == "vectorrotation":
                x = curOption[1]
                y = curOption[2]
                z = curOption[3]
                length = (x**2+y**2+z**2)**0.5
                if length == 0.0:
                    print("Vector Length is Zero")
                    continue
                if x == 1.0 and y == 0.0 and z == 0.0:
                    print("Vector is X axis")
                    continue
                vectorR = gp_Vec(x, y, z)
                vectorX = gp_Vec(1, 0, 0)
                vectorXCrossR =  vectorX.Crossed(vectorR) 
                
                angleBetweenXR = vectorX.Angle(vectorR)

                trsf : gp_Trsf = gp_Trsf()
                ax = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(vectorXCrossR))
                trsf.SetRotation(ax, angleBetweenXR)
                nodeMan.Transform(trsf)
            elif curOptionMode.lower() == "vectortovectorrotation":
                x1 = curOption[1]
                y1 = curOption[2]
                z1 = curOption[3]
                x2 = curOption[4]
                y2 = curOption[5]
                z2 = curOption[6]
                if x1 == 0.0 and y1 == 0.0 and z1 == 0.0:
                    print("Vector1 Length is Zero")
                    continue
                if x2 == 0.0 and y2 == 0.0 and z2 == 0.0:
                    print("Vector2 Length is Zero")
                    continue
                if x1 == x2 and y1 == y2 and z1 == z2:
                    print("Vector1 and Vector2 are same")
                    continue
                vector1 = gp_Vec(x1, y1, z1)
                vector2 = gp_Vec(x2, y2, z2)
                vector1CrossVector2 = vector1.Crossed(vector2)
                angleBetweenVector1Vector2 = vector1.Angle(vector2)
                trsf : gp_Trsf = gp_Trsf()
                ax = gp_Ax1(gp_Pnt(0,0,0), gp_Dir(vector1CrossVector2))
                trsf.SetRotation(ax, angleBetweenVector1Vector2)
                nodeMan.Transform(trsf)                
                
    def DropWeightImpactTestwithPartialRigid(self, option, filePath):
        if "TFinal" in option:
            tfinal = option["TFinal"]
        else:
            tfinal = 0.0 
        if "DT" in option:
            dt = option["DT"]
        else:
            dt = 1.0e-6
        if "BoundaryDistance" in option:
            stressWaveDistance = option["BoundaryDistance"]
        else:
            stressWaveDistance = 0.0
        if "LocationX" in option:
            locX = option["LocationX"]
        else:
            locX = [0.0]
        if "LocationY" in option:
            locY = option["LocationY"]
        else:
            locY = [0.0]
            
            
        ############## Material 
            
        if "MaterialIDImpactorFront" in option:
            matIDImpactorFront = option["MaterialIDImpactorFront"]
        else:
            matIDImpactorFront = 0
        
        if "MaterialIDDamper" in option:
            matIDDamp = option["MaterialIDDamper"]
        else:
            matIDDamp = 0
        
        if "MaterialIDImpactor" in option:
            matIDImpactor = option["MaterialIDImpactor"]
        else:
            matIDImpactor = 0
        
        if "MaterialIDWall" in option:
            matIDWall = option["MaterialIDWall"]
        else:
            matIDWall = 0
        
            
        if "YoungsModulusImpactorFront" in option:
            EImpactorFront = option["YoungsModulusImpactorFront"]
        else:
            EImpactorFront = 2.07e11
        
        if "PoissonRatioImpactorFront" in option:
            nuImpactorFront = option["PoissonRatioImpactorFront"]
        else:
            nuImpactorFront = 0.3

        if "DensityImpactorFront" in option:
            rhoImpactorFront = option["DensityImpactorFront"]
        else:
            rhoImpactorFront = 7800.0                               
            
        if "YoungsModulusWall" in option:
            EWall = option["YoungsModulusWall"]
        else:
            EWall = 1.0e10
        if "PoissonRatioWall" in option:
            nuWall = option["PoissonRatioWall"]
        else:
            nuWall = 0.3
        if "DensityWall" in option:
            rhoWall = option["DensityWall"]
        else:
            rhoWall = 1000.0
                    
        if "YoungsModulusImpactor" in option:
            EImpactor = option["YoungsModulusImpactor"]
        else:
            EImpactor = 2.07e11
        if "PoissonRatioImpactor" in option:
            nuImpactor = option["PoissonRatioImpactor"]
        else:
            nuImpactor = 0.3
        if "DensityImpactor" in option:
            rhoImpactor = option["DensityImpactor"]
        else:
            rhoImpactor = 7800.0
            
        
        if "Type" in option:
            impactorType = option["Type"]
        else:
            impactorType = "Sphere"
            
        if "Dimension" in option:
            dimension = option["Dimension"]
        else:
            dimension = [0.008]
            
        if "MeshSize" in option:
            meshSize = option["MeshSize"]
        else:
            meshSize = 0.001
            
            
        if "InitialVelocityX" in option:
            VxList = option["InitialVelocityX"]
        else:
            VxList = [0.0]
        
        if "InitialVelocityY" in option:
            VyList = option["InitialVelocityY"]
        else:
            VyList = [0.0]
        
        if "InitialVelocityZ" in option:
            VzList = option["InitialVelocityZ"]
        else:
            VzList = [0.0]
        
        if "Height" in option:
            heightList = option["Height"]
        else:
            heightList = [0.5]
            
        if "OffsetDistance" in option:
            offset_distance = option["OffsetDistance"] 
        else:
            offset_distance = 0.00000000001
            
        if "Mode" in option:
            mode = option["Mode"]
        else:
            mode = "OutsideRigidElement"
    
         
        zDir = np.array([0.0, 0.0, -1.0])
        xDir = np.array([1.0, 0.0, 0.0])
        numX = 10
        numY = 10
        numZ = 10
        SSID = 0
       
        SSTYP = 5
        MSTYP = 3
        SBOXID = 0
        MBOXID = 0
        SPR = 0
        MPR = 0
        FS = 0.0
        FD = 0.0
        DC = 0.0
        VC = 0.0
        VDC = 0.0
        PENCHK = 0
        BT = 0.00
        DT = 1.00000E20
        SFS = ""
        SFM = ""
        SST = ""
        MST = ""
        SFST = ""
        SFMT = ""
        FSF = ""
        VSF = ""  
        
        if stressWaveDistance == 0.0:
            if "StressWaveVelocity" in option:
                stressWaveVelocity = option["StressWaveVelocity"]
                if "DistanceMargin" in option:
                    distanceMargin = option["DistanceMargin"]
                    stressWaveDistance = stressWaveVelocity*tfinal*distanceMargin   
            
        nodeMan = self.dynaImporter.nodeManager
        nodeSetMan = self.dynaImporter.nodeSetManager              
        self.SetControlandDatabaseExplicit(tfinal, dt)         
        matMan = self.dynaImporter.matManager
        secMan = self.dynaImporter.sectionManager
        
        ########################################
        if impactorType.lower() == "cylinder":
            if matIDImpactorFront != 0:
                materialImpactorFront = matMan.materials[matIDImpactorFront]
            else:
                materialImpactorFront = matMan.CreateElasticMaterial("ImpactorFrontMaterial", rhoImpactorFront, EImpactorFront, nuImpactorFront)
            sectionImpactorFront : KooSectionSolid = secMan.CreateSolidSection("ImpactorFrontSection", 1)    
            impactFrontElemMan : ElementManager = ElementManager(nodeMan)
            impactFrontPart = KooPart(nodeMan, impactFrontElemMan, materialImpactorFront, sectionImpactorFront, nodeSetMan)
            self.dynaImporter.partManager.CreatePartfromKooPart(impactFrontPart)        
        ########################################                    
        boundaryBox = nodeMan.GetBoundingBox()        
        zMax = boundaryBox[5]
        zMin = boundaryBox[2]                       
        
        ########## Impactor 
        if matIDImpactor != 0:
            materialImpactor = matMan.materials[matIDImpactor]
        else:
            materialImpactor = matMan.CreateElasticMaterial("ImpactorMaterial", rhoImpactor, EImpactor, nuImpactor)            
        sectionImpactor : KooSectionSolid = secMan.CreateSolidSection("ImpactorSection", 1)
        impactElemMan : ElementManager = ElementManager(nodeMan)
        impactorPart = KooPart(nodeMan, impactElemMan, materialImpactor, sectionImpactor, nodeSetMan)
        self.dynaImporter.partManager.CreatePartfromKooPart(impactorPart)                        
        
        ########## Wall
        sectionWall = secMan.CreateSolidSection("WallSection", 1)
        if matIDWall != 0:
            materialWall = matMan.materials[matIDWall]
        else:
            materialWall = matMan.CreateRigidMaterial("WallMaterial", rhoWall, EWall, nuWall)
        wallElemMan : ElementManager = ElementManager(nodeMan)
        wallPart = KooPart(nodeMan, wallElemMan, materialWall, sectionWall, nodeSetMan)
        self.dynaImporter.partManager.CreatePartfromKooPart(wallPart)
        
        
        xLength = boundaryBox[3] - boundaryBox[0]
        yLength = boundaryBox[4] - boundaryBox[1]
        zLength = boundaryBox[5] - boundaryBox[2]                        
        

        
        A1 = [0.0, tfinal]
        O1 = [0.0, 0.0]
        curve = self.dynaImporter.defineManager.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,A1,O1)
        
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 1, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 2, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 3, 2, curve.lcid)
        
        maxMatID = matMan.maxid
                
        self.dynaImporter.matManager.GenerateRigidMaterialswithOffsetID(maxMatID)
        self.dynaImporter.partManager.GenerateRigidPartforAll(self.dynaImporter.matManager, self.dynaImporter.sectionManager)                
        
        for i in range(len(locX)):
            Vx = VxList[i]
            Vy = VyList[i]
            Vz = VzList[i]
            height = heightList[i]
            velocity = [Vx, Vy, Vz-9.81*height]
                
            if i != 0:                
                self.dynaImporter.SyncronizeMaxID()                             
                exceptPIDs = {}
                exceptPIDs[wallPart.id] = wallPart.id
                if impactorType.lower() == "cylinder":
                    exceptPIDs[impactFrontPart.id] = impactFrontPart.id
                exceptPIDs[impactorPart.id] = impactorPart.id
                self.dynaImporter.partManager.MoveElementsfromRigidPartstoPart(exceptPIDs)                
                
                if impactorType.lower() == "cylinder":
                    nodesImpactFront = impactFrontElemMan.GetElementNodes()
                    nodeMan.RemoveNodes(nodesImpactFront)                
                    impactFrontElemMan.RemoveAllElements()
                    self.dynaImporter.initialManager.RemoveInitial(initVFront.id)
                    self.dynaImporter.contactManager.RemoveContact(tiedContactImpactortoFront)
                nodesImpact = impactElemMan.GetElementNodes()
                nodesWall = wallElemMan.GetElementNodes()
                
                nodeMan.RemoveNodes(nodesImpact)                
                nodeMan.RemoveNodes(nodesWall)     
                     
                impactElemMan.RemoveAllElements()
                wallElemMan.RemoveAllElements()
                
                self.dynaImporter.initialManager.RemoveInitial(initV.id)
                self.dynaImporter.contactManager.RemoveContact(contactWalltoObjects)
                self.dynaImporter.contactManager.RemoveContact(contactImpactortoObjects)
                    
                                
                
                self.dynaImporter.SyncronizeMaxID()
                
            
             
                
            impactPoint = [locX[i], locY[i], zMax]
            self.dynaImporter.SyncronizeMaxID()          
            if stressWaveDistance != 0.0:
                exceptPIDs = {}
                exceptPIDs[wallPart.id] = wallPart.id
                if impactorType.lower() == "cylinder":
                    exceptPIDs[impactFrontPart.id] = impactFrontPart.id
                exceptPIDs[impactorPart.id] = impactorPart.id                
                if mode == "OutsideRigidElement":
                    self.dynaImporter.partManager.ChangetoRigidElementsOutsideofSphere(impactPoint, stressWaveDistance, exceptPIDs)
                elif mode == "OutsideRigidPart":
                    self.dynaImporter.partManager.ChangetoRigidPartNotinSphere(impactPoint, stressWaveDistance, exceptPIDs)
                    
                                                                    
            self.dynaImporter.SyncronizeMaxID()  
            
            if impactorType.lower() == "sphere":
                radius = dimension[0]
                impactLoc = [locX[i], locY[i], zMax + radius+offset_distance]
                
                simodule = self.moduleManager.CreateSphereImpactModule("Impact Ball", radius, impactLoc)                
                simodule.SetMeshSize(meshSize)
                simodule.GenerateShape()
                
                impactorPart.GenerateTetraMeshfromShapes(simodule.shapes, meshSize, meshSize, 3)
            elif impactorType.lower() == "cylinder":
                radius = dimension[0]
                outerRadius = dimension[1]
                height1 = dimension[2]
                height2 = dimension[3]
                backRadius = dimension[4]
                impactLoc = [locX[i], locY[i], zMax+offset_distance]
                zDir = np.array([0.0, 0.0, 1.0])
                simodule = self.moduleManager.CreateCylinderwithMassImpactModule("Impact Cylinder", radius, outerRadius, height1, height2, impactLoc, zDir, backRadius)
                simodule.SetMeshSize(meshSize)
                simodule.GenerateShape()
                impactorPart.GenerateTetraMeshfromShapes(simodule.shapesBack, meshSize, meshSize, 3)
                self.dynaImporter.SyncronizeMaxID()
                impactFrontPart.GenerateTetraMeshfromShapes(simodule.shapesFront, meshSize, meshSize, 3)
                
                
                                        
                                    
            self.dynaImporter.SyncronizeMaxID()   
            
            wallLocation = [locX[i], locY[i], zMin]
            
            zDir = np.array([0.0, 0.0, -1.0])
                                    
            wallPart.elementManager.CreateImpactBox(wallLocation,zDir, xDir,xLength,yLength,zLength,numX,numY,numZ)                                
            MSID = wallPart.id        
            SSID = 0
            contactWalltoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)                    
            contactWalltoObjects.SetOptCardA(2)
            initV = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactorPart.id, 2, 0, velocity[0], velocity[1], velocity[2])
            if impactorType.lower() == "sphere":
                MSID = impactorPart.id
                contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)                
                contactImpactortoObjects.SetOptCardA(2)
            elif impactorType.lower() == "cylinder":
                MSID = impactFrontPart.id
                contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                contactImpactortoObjects.SetOptCardA(2)
                
                initVFront = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactFrontPart.id, 2, 0, velocity[0], velocity[1], velocity[2])
                
                MSID = impactorPart.id
                SSID = impactFrontPart.id            
                tiedContactImpactortoFront = self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID, 3, 3, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            
            
            if len(locX) > 1: 
                modifiedKeyword = "_MODE_"
                if mode == "OutsideRigidElement":
                    modifiedKeyword += "ORE"
                elif mode == "OutsideRigidPart":
                    modifiedKeyword += "ORP"
                if impactorType.lower() == "cylinder":
                    modifiedKeyword += "_CYL_"            
                    modifiedKeyword += format(dimension[0], '.3e')
                elif impactorType.lower() == "sphere":
                    modifiedKeyword += "_SPH_"
                    modifiedKeyword += format(dimension[0], '.3e')
                modifiedKeyword += "_LOCX_" + format(locX[i], '.3e')
                modifiedKeyword += "_LOCY_" + format(locY[i], '.3e')
                modifiedKeyword += "_VX_" + format(Vx, '.3e')
                modifiedKeyword += "_VY_" + format(Vy, '.3e')
                modifiedKeyword += "_VZ_" + format(Vz, '.3e')
                modifiedKeyword += "_H_" + format(height, '.3e')
                modifiedKeyword = modifiedKeyword.strip()
                self.WriteModifiedFile(filePath, modifiedKeyword)                
    
            
    def DropWeightImpactTest(self, option, filePath):
        
        if "TFinal" in option:
            tfinal = option["TFinal"]
        else:
            tfinal = 0.0 
        if "DT" in option:
            dt = option["DT"]
        else:
            dt = 1.0e-6
        if "BoundaryDistance" in option:
            stressWaveDistance = option["BoundaryDistance"]
        else:
            stressWaveDistance = 0.0
        if "LocationX" in option:
            locX = option["LocationX"]
        else:
            locX = [0.0]
        if "LocationY" in option:
            locY = option["LocationY"]
        else:
            locY = [0.0]
            
            
        ############## Material 
            
        if "MaterialIDImpactorFront" in option:
            matIDImpactorFront = option["MaterialIDImpactorFront"]
        else:
            matIDImpactorFront = 0
        
        if "MaterialIDDamper" in option:
            matIDDamp = option["MaterialIDDamper"]
        else:
            matIDDamp = 0
        
        if "MaterialIDImpactor" in option:
            matIDImpactor = option["MaterialIDImpactor"]
        else:
            matIDImpactor = 0
        
        if "MaterialIDWall" in option:
            matIDWall = option["MaterialIDWall"]
        else:
            matIDWall = 0
        
            
        if "YoungsModulusImpactorFront" in option:
            EImpactorFront = option["YoungsModulusImpactorFront"]
        else:
            EImpactorFront = 2.07e11
        
        if "PoissonRatioImpactorFront" in option:
            nuImpactorFront = option["PoissonRatioImpactorFront"]
        else:
            nuImpactorFront = 0.3

        if "DensityImpactorFront" in option:
            rhoImpactorFront = option["DensityImpactorFront"]
        else:
            rhoImpactorFront = 7800.0
            
            
        if "YoungsModulusDamper" in option:
            EDamp = option["YoungsModulusDamper"]
        else:
            EDamp = 1.0e10
        if "PoissonRatioDamper" in option:
            nuDamp = option["PoissonRatioDamper"]
        else:
            nuDamp = 0.3
        if "DensityDamper" in option:
            rhoDamp = option["DensityDamper"]
        else:
            rhoDamp = 1000.0
            
        if "YoungsModulusWall" in option:
            EWall = option["YoungsModulusWall"]
        else:
            EWall = 1.0e10
        if "PoissonRatioWall" in option:
            nuWall = option["PoissonRatioWall"]
        else:
            nuWall = 0.3
        if "DensityWall" in option:
            rhoWall = option["DensityWall"]
        else:
            rhoWall = 1000.0
                    
        if "YoungsModulusImpactor" in option:
            EImpactor = option["YoungsModulusImpactor"]
        else:
            EImpactor = 2.07e11
        if "PoissonRatioImpactor" in option:
            nuImpactor = option["PoissonRatioImpactor"]
        else:
            nuImpactor = 0.3
        if "DensityImpactor" in option:
            rhoImpactor = option["DensityImpactor"]
        else:
            rhoImpactor = 7800.0
            
        
        if "Type" in option:
            impactorType = option["Type"]
        else:
            impactorType = "Sphere"
            
        if "Dimension" in option:
            dimension = option["Dimension"]
        else:
            dimension = [0.008]
            
        if "MeshSize" in option:
            meshSize = option["MeshSize"]
        else:
            meshSize = 0.001
            
        if "DimensionDamper" in option:
            dimensionDamper = option["DimensionDamper"]
            if len(dimensionDamper) <3:
                for i in range(3-len(dimensionDamper)):
                    dimensionDamper.append(0.001)
        else:
            dimensionDamper = [0.001,0.001,0.001]
            
        if "InitialVelocityX" in option:
            VxList = option["InitialVelocityX"]
        else:
            VxList = [0.0]
        
        if "InitialVelocityY" in option:
            VyList = option["InitialVelocityY"]
        else:
            VyList = [0.0]
        
        if "InitialVelocityZ" in option:
            VzList = option["InitialVelocityZ"]
        else:
            VzList = [0.0]
        
        if "Height" in option:
            heightList = option["Height"]
        else:
            heightList = [0.5]
            
        if "OffsetDistance" in option:
            offset_distance = option["OffsetDistance"] 
        else:
            offset_distance = 0.00000000001
         
        zDir = np.array([0.0, 0.0, -1.0])
        xDir = np.array([1.0, 0.0, 0.0])
        numX = 10
        numY = 10
        numZ = 10
        SSID = 0
       
        SSTYP = 5
        MSTYP = 3
        SBOXID = 0
        MBOXID = 0
        SPR = 0
        MPR = 0
        FS = 0.0
        FD = 0.0
        DC = 0.0
        VC = 0.0
        VDC = 0.0
        PENCHK = 0
        BT = 0.00
        DT = 1.00000E20
        SFS = ""
        SFM = ""
        SST = ""
        MST = ""
        SFST = ""
        SFMT = ""
        FSF = ""
        VSF = ""  
        
        # Generate Part Set
        partSet : PartSet = self.dynaImporter.partManager.CreatePartSet(name="Dynamic Relaxation Set")
        for pid, part in self.dynaImporter.partManager.parts.items():
            partSet.AddPart(pid)
        self.dynaImporter.additionalManager.CreateInterfaceSpringbackLSDyna(partSet.psid)

        
        if stressWaveDistance == 0.0:
            if "StressWaveVelocity" in option:
                stressWaveVelocity = option["StressWaveVelocity"]
                if "DistanceMargin" in option:
                    distanceMargin = option["DistanceMargin"]
                    stressWaveDistance = stressWaveVelocity*tfinal*distanceMargin   
            
        nodeMan = self.dynaImporter.nodeManager
        nodeSetMan = self.dynaImporter.nodeSetManager              
        self.SetControlandDatabaseExplicit(tfinal, dt)         
        matMan = self.dynaImporter.matManager
        secMan = self.dynaImporter.sectionManager
        
        ########################################
        if impactorType.lower() == "cylinder":
            if matIDImpactorFront != 0:
                materialImpactorFront = matMan.materials[matIDImpactorFront]
            else:
                materialImpactorFront = matMan.CreateElasticMaterial("ImpactorFrontMaterial", rhoImpactorFront, EImpactorFront, nuImpactorFront)            
            sectionImpactorFront : KooSectionSolid = secMan.CreateSolidSection("ImpactorFrontSection", 1)    
            impactFrontElemMan : ElementManager = ElementManager(nodeMan)
            impactFrontPart = KooPart(nodeMan, impactFrontElemMan, materialImpactorFront, sectionImpactorFront, nodeSetMan)
            self.dynaImporter.partManager.CreatePartfromKooPart(impactFrontPart)        
        ########################################
        
        if matIDDamp != 0:
            materialBeam = matMan.materials[matIDDamp]
        else:
            materialBeam = matMan.CreateElasticMaterial("DamperMaterial", rhoDamp, EDamp, nuDamp)                
        sectionBeam : KooSectionBeam = secMan.CreateBeamSection("DamperSetion")
        boundaryBox = nodeMan.GetBoundingBox()        
        zMax = boundaryBox[5]
        zMin = boundaryBox[2]                       
        beamElemMan : ElementManager = ElementManager(nodeMan)                                       
        beamPart = KooPart(nodeMan,beamElemMan,materialBeam,sectionBeam,nodeSetMan) 
        
        self.dynaImporter.partManager.CreatePartfromKooPart(beamPart)
        ########################################
        
        if matIDImpactor != 0:
            materialImpactor = matMan.materials[matIDImpactor]
        else:
            materialImpactor = matMan.CreateElasticMaterial("ImpactorMaterial", rhoImpactor, EImpactor, nuImpactor)            
        sectionImpactor : KooSectionSolid = secMan.CreateSolidSection("ImpactorSection", 1)
        impactElemMan : ElementManager = ElementManager(nodeMan)
        impactorPart = KooPart(nodeMan, impactElemMan, materialImpactor, sectionImpactor, nodeSetMan)
        self.dynaImporter.partManager.CreatePartfromKooPart(impactorPart)                        
        
        sectionWall = secMan.CreateSolidSection("WallSection", 1)
        if matIDWall != 0:
            materialWall = matMan.materials[matIDWall]
        else:
            materialWall = matMan.CreateRigidMaterial("WallMaterial", rhoWall, EWall, nuWall)
        wallElemMan : ElementManager = ElementManager(nodeMan)
        wallPart = KooPart(nodeMan, wallElemMan, materialWall, sectionWall, nodeSetMan)
        self.dynaImporter.partManager.CreatePartfromKooPart(wallPart)
        
        
        xLength = boundaryBox[3] - boundaryBox[0]
        yLength = boundaryBox[4] - boundaryBox[1]
        zLength = boundaryBox[5] - boundaryBox[2]                        
        
        sectionBeam.SetWidth(dimensionDamper[0])
        sectionBeam.SetHeight(dimensionDamper[1])               
        offsetDampingDistance = dimensionDamper[2]
        nodeSetInside = None
        nodeSetFixed = None
        spcBoundary = None
        
        A1 = [0.0, tfinal]
        O1 = [0.0, 0.0]
        curve = self.dynaImporter.defineManager.CreateDefineCurve(0,1.0,1.0,0.0,0.0,0,0,A1,O1)
        
        
        ## Rigid 옵션이 붙은 경우 Part를 Node로 설정해야 함 
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 1, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 2, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 3, 2, curve.lcid)
        
        
        for i in range(len(locX)):
            Vx = VxList[i]
            Vy = VyList[i]
            Vz = VzList[i]
            height = heightList[i]
            velocity = [Vx, Vy, Vz-9.81*height]
                
            self.dynaImporter.SyncronizeMaxID()  
            if i != 0:                
                for pid in self.dynaImporter.partManager.parts:
                    self.dynaImporter.SyncronizeMaxID()                             
                    if pid == beamPart.id:
                        continue
                    if pid == impactorPart.id:
                        continue
                    if impactorType.lower() == "cylinder":
                        if pid == impactFrontPart.id:
                            continue
                    if pid == wallPart.id:
                        continue
                    part = self.dynaImporter.partManager.parts[pid] 
                    elemMan : ElementManager = part.elementManager 
                    if pid in removedElemList:
                        elemMan.AddElements(removedElemList[pid])
                    if pid in removedNodeList:
                        nodeMan.AddNodes(removedNodeList[pid])
                    
                self.dynaImporter.SyncronizeMaxID()                             
                if nodeSetInside != None:
                    nodeSetInside.Clear()
                if nodeSetFixed != None:
                    nodeSetFixed.Clear()
                nodeMan.RemoveNodeList(boundaryFixNodes)                                
                nodeMan.RemoveNodeList(boundaryBetweenNodes)
                if impactorType.lower() == "cylinder":
                    nodesImpactFront = impactFrontElemMan.GetElementNodes()
                    nodeMan.RemoveNodes(nodesImpactFront)
                nodesImpact = impactElemMan.GetElementNodes()
                nodeMan.RemoveNodes(nodesImpact)
                nodesWall = wallElemMan.GetElementNodes()
                nodeMan.RemoveNodes(nodesWall)
                beamElemMan.RemoveAllElements()
                if impactorType.lower() == "cylinder":
                    impactFrontElemMan.RemoveAllElements()
                impactElemMan.RemoveAllElements()
                wallElemMan.RemoveAllElements()
                self.dynaImporter.initialManager.RemoveInitial(initV.id)                
                self.dynaImporter.contactManager.RemoveContact(contactWalltoObjects)
                self.dynaImporter.contactManager.RemoveContact(contactImpactortoObjects)
                if impactorType.lower() == "cylinder":
                    self.dynaImporter.initialManager.RemoveInitial(initVFront.id)
                    self.dynaImporter.contactManager.RemoveContact(tiedContactImpactortoFront)
                if nodeSetInside != None:
                    self.dynaImporter.nodeSetManager.RemoveNodeSet(nodeSetInside)
                if nodeSetFixed != None:
                    self.dynaImporter.nodeSetManager.RemoveNodeSet(nodeSetFixed)
                if spcBoundary != None:
                    self.dynaImporter.boundaryNodeManager.RemoveBoundary(spcBoundary.bid)
                self.dynaImporter.SyncronizeMaxID()
                
            
             
                
            impactPoint = [locX[i], locY[i], zMax]
                    
            boundaryNodes = [] 
            removedElemList = {}
            removedNodeList = {}
            
            if stressWaveDistance != 0.0:
                nodeSetInside = self.dynaImporter.nodeSetManager.CreateNodeSetwithNodes("BoundaryNodes", 0.0,0.0,0.0,0.0,"MECH",0, [])
                nodeSetFixed = self.dynaImporter.nodeSetManager.CreateNodeSetwithNodes("BoundaryFixNodes", 0.0,0.0,0.0,0.0,"MECH",0, [])
                spcBoundary = self.dynaImporter.boundaryNodeManager.CreateBoundarySPCNodeSet(nodeSetFixed,0,1,1,1,1,1,1,"FIXED")          
        
                for pid in self.dynaImporter.partManager.parts:
                    
                    if pid == beamPart.id:
                        continue
                    if impactorType.lower() == "cylinder":
                        if pid == impactFrontPart.id:
                            continue
                    if pid == impactorPart.id:
                        continue
                    if pid == wallPart.id:
                        continue
                    part = self.dynaImporter.partManager.parts[pid]
                    elemMan : ElementManager = part.elementManager
                    
                    addBDNodes, removedElems, removedNodes = elemMan.RemoveOuterElement(impactPoint[0], impactPoint[1], impactPoint[2], stressWaveDistance)
                    removedElemList[pid] = removedElems
                    removedNodeList[pid] = removedNodes
                    boundaryNodes.extend(addBDNodes)
                                
                nodeSetInside.AddNodes(boundaryNodes)                                       
                
                                          
            else:
                nodeSetInside = None
                nodeSetFixed = None
                spcBoundary = None
            self.dynaImporter.SyncronizeMaxID()  
            boundaryFixNodes = []
            boundaryBetweenNodes = [] 
            addedBeamElems = {}
            
            if stressWaveDistance != 0.0:
                for node in boundaryNodes:
                    x1 = node.x
                    y1 = node.y
                    z1 = node.z            
                    dirR = (x1-impactPoint[0], y1-impactPoint[1], z1-impactPoint[2])
                    normDir = (dirR[0]**2+dirR[1]**2+dirR[2]**2)**0.5
                    dirR = (dirR[0]/normDir, dirR[1]/normDir, dirR[2]/normDir)
                    x2 = x1 + dirR[0]*offsetDampingDistance
                    y2 = y1 + dirR[1]*offsetDampingDistance
                    z2 = z1 + dirR[2]*offsetDampingDistance
                    
                    x3 = x1 + dirR[0]*offsetDampingDistance*0.5
                    y3 = y1 + dirR[1]*offsetDampingDistance*0.5
                    z3 = z1 + dirR[2]*offsetDampingDistance*0.5 + 0.5*offsetDampingDistance
                    
                    node2 = nodeMan.CreateNode(x2, y2, z2)
                    node3 = nodeMan.CreateNode(x3, y3, z3)
                    boundaryFixNodes.append(node2)
                    boundaryBetweenNodes.append(node3)
                    beamElem = beamElemMan.CreateLineQuadraticElement(node,node2,node3)
                    addedBeamElems[beamElem.id] = beamElem
                        
                nodeSetFixed.AddNodes(boundaryFixNodes)
                                
                
            self.dynaImporter.SyncronizeMaxID()
            if impactorType.lower() == "sphere":
                radius = dimension[0]
                impactLoc = [locX[i], locY[i], zMax + radius+offset_distance]
                
                simodule = self.moduleManager.CreateSphereImpactModule("Impact Ball", radius, impactLoc)                
                simodule.SetMeshSize(meshSize)
                simodule.GenerateShape()
                
                impactorPart.GenerateTetraMeshfromShapes(simodule.shapes, meshSize, meshSize, 3)
            elif impactorType.lower() == "cylinder":
                radius = dimension[0]
                outerRadius = dimension[1]
                height1 = dimension[2]
                height2 = dimension[3]
                backRadius = dimension[4]
                impactLoc = [locX[i], locY[i], zMax+offset_distance]
                zDir = np.array([0.0, 0.0, 1.0])
                simodule = self.moduleManager.CreateCylinderwithMassImpactModule("Impact Cylinder", radius, outerRadius, height1, height2, impactLoc, zDir, backRadius)
                simodule.SetMeshSize(meshSize)
                simodule.GenerateShape()
                impactorPart.GenerateTetraMeshfromShapes(simodule.shapesBack, meshSize, meshSize, 3)
                self.dynaImporter.SyncronizeMaxID()
                impactFrontPart.GenerateTetraMeshfromShapes(simodule.shapesFront, meshSize, meshSize, 3)
                
                
                                        
                                    
            self.dynaImporter.SyncronizeMaxID()   
            
            wallLocation = [locX[i], locY[i], zMin]
            
            zDir = np.array([0.0, 0.0, -1.0])
                                    
            wallPart.elementManager.CreateImpactBox(wallLocation,zDir, xDir,xLength,yLength,zLength,numX,numY,numZ)                                
            MSID = wallPart.id        
            SSID = 0
            contactWalltoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)                    
            contactWalltoObjects.SetOptCardA(2)
            initV = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactorPart.id, 2, 0, velocity[0], velocity[1], velocity[2])
            
            if impactorType.lower() == "sphere":
                MSID = impactorPart.id
                contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                contactImpactortoObjects.SetOptCardA(2)
            elif impactorType.lower() == "cylinder":
                MSID = impactFrontPart.id
                contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                contactImpactortoObjects.SetOptCardA(2)
                initVFront = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactFrontPart.id, 2, 0, velocity[0], velocity[1], velocity[2])            
                MSID = impactorPart.id
                SSID = impactFrontPart.id            
                tiedContactImpactortoFront = self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID, 3, 3, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                
            
            if len(locX) > 1: 
                modifiedKeyword = "_MODE_DS"   
                if impactorType.lower() == "cylinder":
                    modifiedKeyword += "_CYL_"            
                    modifiedKeyword += format(dimension[0], '.3e')
                elif impactorType.lower() == "sphere":
                    modifiedKeyword += "_SPH_"
                    modifiedKeyword += format(dimension[0], '.3e')
                modifiedKeyword += "_LOCX_" + format(locX[i], '.3e')
                modifiedKeyword += "_LOCY_" + format(locY[i], '.3e')
                modifiedKeyword += "_VX_" + format(Vx, '.3e')
                modifiedKeyword += "_VY_" + format(Vy, '.3e')
                modifiedKeyword += "_VZ_" + format(Vz, '.3e')
                modifiedKeyword += "_H_" + format(height, '.3e')
                modifiedKeyword = modifiedKeyword.strip()
                self.WriteModifiedFile(filePath, modifiedKeyword)                
    
    def DropWeightImpactTestbyPart(self, option, filePath):
        if "TFinal" in option:
            tfinal = option["TFinal"]
        else:
            tfinal = 0.0 
        if "DT" in option:
            dt = option["DT"]
        else:
            dt = 1.0e-6
        
        '''if "BoundaryDistance" in option:
            stressWaveDistance = option["BoundaryDistance"]
        else:
            stressWaveDistance = 0.0 '''
        
        ############## Material 
            
     
        '''if "MaterialIDDamper" in option:
            matIDDamp = option["MaterialIDDamper"]
        else:
            matIDDamp = 0
     
        if "YoungsModulusDamper" in option:
            EDamp = option["YoungsModulusDamper"]
        else:
            EDamp = 1.0e10
        if "PoissonRatioDamper" in option:
            nuDamp = option["PoissonRatioDamper"]
        else:
            nuDamp = 0.3
        if "DensityDamper" in option:
            rhoDamp = option["DensityDamper"]
        else:
            rhoDamp = 1000.0'''
                 
        if "Type" in option:
            impactorType = option["Type"]
        else:
            impactorType = "Sphere"
            
        if "Dimension" in option:
            dimension = option["Dimension"]
        else:
            dimension = [0.008]
            
        if "MeshSize" in option:
            meshSize = option["MeshSize"]
        else:
            meshSize = 0.001
            
        '''if "DimensionDamper" in option:
            dimensionDamper = option["DimensionDamper"]
            if len(dimensionDamper) <3:
                for i in range(3-len(dimensionDamper)):
                    dimensionDamper.append(0.001)
        else:
            dimensionDamper = [0.001,0.001,0.001]
        '''
        if "OffsetDistance" in option:
            offset_distance = option["OffsetDistance"] 
        else:
            offset_distance = 0.00000000001
       
        if "PartIDs" in option:
            partIDs = option["PartIDs"]
        else:
            partIDs = []
        if "LocationMode" in option:
            locationModes = option["LocationMode"]
        else:
            locationModes = ["1X1"]
        if "InitialVelocityX" in option:
            VxList = option["InitialVelocityX"]     
        else:
            VxList = [0.0]
        if "InitialVelocityY" in option:
            VyList = option["InitialVelocityY"]
        else:
            VyList = [0.0]
        if "InitialVelocityZ" in option:
            VzList = option["InitialVelocityZ"]
        else:
            VzList = [0.0]
        if "Height" in option:
            heightList = option["Height"]
        else:
            heightList = [0.5]
        
        
        zDir = np.array([0.0, 0.0, -1.0])
        xDir = np.array([1.0, 0.0, 0.0])
        numX = 10           
        numY = 10
        numZ = 10
        
        SSID = 0
        SSTYP = 5   
        MSTYP = 3
        SBOXID = 0
        MBOXID = 0
        SPR = 0
        MPR = 0
        FS = 0.0
        FD = 0.0
        DC = 0.0
        VC = 0.0
        VDC = 0.0
        PENCHK = 0
        BT = 0.00
        DT = 1.00000E20
        SFS = ""
        SFM = ""
        SST = ""
        MST = ""
        SFST = ""
        SFMT = ""
        FSF = ""
        VSF = ""
       
        self.SetControlandDatabaseExplicit(tfinal, dt)
        
        nodeMan = self.dynaImporter.nodeManager
        nodeSetMan = self.dynaImporter.nodeSetManager
        matMan = self.dynaImporter.matManager
        secMan = self.dynaImporter.sectionManager
        
        if impactorType.lower() == "cylinder":
            impactorPart, materialImpactor, sectionImpactor, impactElemMan, impactFrontPart, materialImpactorFront, sectionImpactorFront, impactFrontElemMan = self.CreateCylinderImpactorPart(option)
        else:
            impactorPart, materialImpactor, sectionImpactor, impactElemMan = self.CreateSphereImpactorPart(option)
        wallPart, materialWall, sectionWall, wallElemMan = self.CreateWallPart(option)        
        boundaryBox = nodeMan.GetBoundingBox()
        zMax = boundaryBox[5]
        zMin = boundaryBox[2]
        xLength = boundaryBox[3] - boundaryBox[0]
        yLength = boundaryBox[4] - boundaryBox[1]   
        zLength = boundaryBox[5] - boundaryBox[2]
        
        A1 = [0.0, tfinal]
        O1 = [0.0, 0.0]
        curve = self.dynaImporter.defineManager.CreateDefineCurve(0, 1.0, 1.0, 0.0, 0.0, 0, 0, A1, O1)
        
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 1, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 2, 2, curve.lcid)
        self.dynaImporter.boundaryNodeManager.CreateBoundaryPrescribedMotionRigid(wallPart, 3, 2, curve.lcid)
        i = 0
        for partID in partIDs:
            if partID not in self.dynaImporter.partManager.parts:
                continue
            part = self.dynaImporter.partManager.parts[partID]
            xMinPart, xMaxPart, yMinPart, yMaxPart, zMinPart, zMaxPart = part.elementManager.GetBoundaryBox()
            xcPart = (xMinPart + xMaxPart) / 2.0
            ycPart = (yMinPart + yMaxPart) / 2.0
            zcPart = (zMinPart + zMaxPart) / 2.0
            locationMode = locationModes[i]
            if locationMode.lower() == "1x1":
                locX = [xcPart]
                locY = [ycPart]
            elif locationMode.lower() == "1x2":
                locX = [xcPart, xcPart]
                locY = [yMinPart, yMaxPart]
            elif locationMode.lower() == "2x1":
                locX = [xMinPart, xMaxPart]
                locY = [ycPart, ycPart]
            elif locationMode.lower() == "2x2":
                locX = [xMinPart, xMaxPart, xMinPart, xMaxPart]
                locY = [yMinPart, yMinPart, yMaxPart, yMaxPart]
            elif locationMode.lower() == "1x3":
                locX = [xcPart, xcPart, xcPart]
                locY = [yMinPart, ycPart, yMaxPart]
            elif locationMode.lower() == "3x1":
                locX = [xMinPart, xcPart, xMaxPart]
                locY = [ycPart, ycPart, ycPart]
            elif locationMode.lower() == "3x3":
                locX = [xMinPart, xcPart, xMaxPart, xMinPart, xcPart, xMaxPart, xMinPart, xcPart, xMaxPart]
                locY = [yMinPart, yMinPart, yMinPart, ycPart, ycPart, ycPart, yMaxPart, yMaxPart, yMaxPart]
        
            Vx = VxList[i]
            Vy = VyList[i]
            Vz = VzList[i]
            height = heightList[i]
            velocity = [Vx, Vy, Vz-9.81*height]
        
            for j in range(len(locX)):
                self.dynaImporter.SyncronizeMaxID()
                if j != 0 or i != 0:
                    for pid in self.dynaImporter.partManager.parts:
                        self.dynaImporter.SyncronizeMaxID()                             
                        if pid == wallPart.id:
                            continue
                        if pid == impactorPart.id:
                            continue
                        if impactorType.lower() == "cylinder":
                            if pid == impactFrontPart.id:
                                continue
                        pidPart = self.dynaImporter.partManager.parts[pid] 
                        elemMan : ElementManager = pidPart.elementManager 
                        if pid in removedElemList:
                            elemMan.AddElements(removedElemList[pid])
                        if pid in removedNodeList:
                            nodeMan.AddNodes(removedNodeList[pid])        
                    self.dynaImporter.SyncronizeMaxID()
                    if impactorType.lower() == "cylinder":
                        nodesImpactFront = impactFrontElemMan.GetElementNodes()
                        nodeMan.RemoveNodes(nodesImpactFront)
                    nodesImpact = impactElemMan.GetElementNodes()
                    nodeMan.RemoveNodes(nodesImpact)
                    nodesWall = wallElemMan.GetElementNodes()   
                    nodeMan.RemoveNodes(nodesWall)
                    
                    if impactorType.lower() == "cylinder":
                        impactFrontElemMan.RemoveAllElements()
                    impactElemMan.RemoveAllElements()
                    wallElemMan.RemoveAllElements()
                    
                    self.dynaImporter.initialManager.RemoveInitial(initV.id)
                    self.dynaImporter.contactManager.RemoveContact(contactWalltoObjects)
                    self.dynaImporter.contactManager.RemoveContact(contactImpactortoObjects)
                    if impactorType.lower() == "cylinder":
                        self.dynaImporter.initialManager.RemoveInitial(initVFront.id)
                        self.dynaImporter.contactManager.RemoveContact(tiedContactImpactortoFront)
                    self.dynaImporter.SyncronizeMaxID()
                
                removedElemList = {}
                removedNodeList = {}
                
                if impactorType.lower() == "sphere":
                    radius = dimension[0]
                    impactLoc = [locX[j], locY[j], zMax + radius+offset_distance]
                    
                    simodule = self.moduleManager.CreateSphereImpactModule("Impact Ball", radius, impactLoc)                
                    simodule.SetMeshSize(meshSize)
                    simodule.GenerateShape()
                    
                    impactorPart.GenerateTetraMeshfromShapes(simodule.shapes, meshSize, meshSize, 3)
                elif impactorType.lower() == "cylinder":
                    radius = dimension[0]
                    outerRadius = dimension[1]
                    height1 = dimension[2]
                    height2 = dimension[3]
                    backRadius = dimension[4]
                    impactLoc = [locX[j], locY[j], zMax+offset_distance]
                    zDir = np.array([0.0, 0.0, 1.0])
                    simodule = self.moduleManager.CreateCylinderwithMassImpactModule("Impact Cylinder", radius, outerRadius, height1, height2, impactLoc, zDir, backRadius)
                    simodule.SetMeshSize(meshSize)
                    simodule.GenerateShape()
                    impactorPart.GenerateTetraMeshfromShapes(simodule.shapesBack, meshSize, meshSize, 3)
                    self.dynaImporter.SyncronizeMaxID()
                    impactFrontPart.GenerateTetraMeshfromShapes(simodule.shapesFront, meshSize, meshSize, 3)
                self.dynaImporter.SyncronizeMaxID()
                wallLocation = [locX[j], locY[j], zMin]
                zDir = np.array([0.0, 0.0, -1.0])
                wallPart.elementManager.CreateImpactBox(wallLocation, zDir, xDir, xLength, yLength, zLength, numX, numY, numZ)
                MSID = wallPart.id
                SSID = 0
                contactWalltoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                contactWalltoObjects.SetOptCardA(2)
                initV = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactorPart.id, 2, 0, velocity[0], velocity[1], velocity[2])

                if impactorType.lower() == "sphere":
                    MSID = impactorPart.id
                    contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                    contactImpactortoObjects.SetOptCardA(2)
                elif impactorType.lower() == "cylinder":
                    MSID = impactFrontPart.id
                    contactImpactortoObjects = self.dynaImporter.contactManager.CreateContactAutomaticSurfacetoSurface(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                    contactImpactortoObjects.SetOptCardA(2)
                    initVFront = self.dynaImporter.initialManager.CreateInitialVelocityGeneration(impactFrontPart.id, 2, 0, velocity[0], velocity[1], velocity[2])            
                    MSID = impactorPart.id
                    SSID = impactFrontPart.id            
                    tiedContactImpactortoFront = self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID, 3, 3, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                
                if len(locX) > 1:
                    modifiedKeyword = "_MODE_DWIP"   
                    if impactorType.lower() == "cylinder":
                        modifiedKeyword += "_CYL_"            
                        modifiedKeyword += format(dimension[0], '.3e')
                    elif impactorType.lower() == "sphere":
                        modifiedKeyword += "_SPH_"
                        modifiedKeyword += format(dimension[0], '.3e')
                    modifiedKeyword += "_PID_" + str(partID)
                    modifiedKeyword += "_LOCX_" + format(locX[j], '.3e')
                    modifiedKeyword += "_LOCY_" + format(locY[j], '.3e')
                    modifiedKeyword += "_VX_" + format(Vx, '.3e')
                    modifiedKeyword += "_VY_" + format(Vy, '.3e')
                    modifiedKeyword += "_VZ_" + format(Vz, '.3e')
                    modifiedKeyword += "_H_" + format(height, '.3e')
                    modifiedKeyword = modifiedKeyword.strip()
                    self.WriteModifiedFile(filePath, modifiedKeyword)
            i = i + 1

    def CreateWallPart(self, option):
        if "MaterialIDWall" in option:
            matIDWall = option["MaterialIDWall"]
        else:
            matIDWall = 0
        
        if "YoungsModulusWall" in option:
            EWall = option["YoungsModulusWall"]
        else:
            EWall = 1.0e6
        if "PoissonRatioWall" in option:
            nuWall = option["PoissonRatioWall"]
        else:
            nuWall = 0.3
        if "DensityWall" in option:
            rhoWall = option["DensityWall"]
        else:
            rhoWall = 1.0e-9
            
        if matIDWall != 0:
            materialWall = self.dynaImporter.matManager.materials[matIDWall]
        else:
            materialWall = self.dynaImporter.matManager.CreateRigidMaterial("WallMaterial", rhoWall, EWall, nuWall)
        
        sectionWall : KooSectionSolid = self.dynaImporter.sectionManager.CreateSolidSection("WallSection", 1)
        wallElemMan : ElementManager = ElementManager(self.dynaImporter.nodeManager)

        wallPart = KooPart(self.dynaImporter.nodeManager, wallElemMan, materialWall, sectionWall, self.dynaImporter.nodeSetManager)
        self.dynaImporter.partManager.CreatePartfromKooPart(wallPart)
        
        return wallPart, materialWall, sectionWall, wallElemMan
    
    def CreateSphereImpactorPart(self, option):
        if "MaterialIDImpactor" in option:
            matIDImpactor = option["MaterialIDImpactor"]
        else:
            matIDImpactor = 0   
        if "YoungsModulusImpactor" in option:
            EImpactor = option["YoungsModulusImpactor"]
        else:
            EImpactor = 2.07e5
        if "PoissonRatioImpactor" in option:
            nuImpactor = option["PoissonRatioImpactor"]
        else:
            nuImpactor = 0.3
        if "DensityImpactor" in option:
            rhoImpactor = option["DensityImpactor"]     
        else:
            rhoImpactor = 7.800E-9
        
        if matIDImpactor != 0:
            materialImpactor = self.dynaImporter.matManager.materials[matIDImpactor]
        else:
            materialImpactor = self.dynaImporter.matManager.CreateElasticMaterial("ImpactorMaterial", rhoImpactor, EImpactor, nuImpactor)
        sectionImpactor : KooSectionSolid = self.dynaImporter.sectionManager.CreateSolidSection("ImpactorSection", 1)
        impactElemMan : ElementManager = ElementManager(self.dynaImporter.nodeManager)

        impactorPart = KooPart(self.dynaImporter.nodeManager, impactElemMan, materialImpactor, sectionImpactor, self.dynaImporter.nodeSetManager)
        self.dynaImporter.partManager.CreatePartfromKooPart(impactorPart)
        
        return impactorPart, materialImpactor, sectionImpactor, impactElemMan

    def CreateCylinderImpactorPart(self, option):
        if "MaterialIDImpactor" in option:
            matIDImpactor = option["MaterialIDImpactor"]
        else:
            matIDImpactor = 0   
        if "YoungsModulusImpactor" in option:
            EImpactor = option["YoungsModulusImpactor"]
        else:
            EImpactor = 2.07e5
        if "PoissonRatioImpactor" in option:
            nuImpactor = option["PoissonRatioImpactor"]
        else:
            nuImpactor = 0.3
        if "DensityImpactor" in option:
            rhoImpactor = option["DensityImpactor"]     
        else:
            rhoImpactor = 7.800E-9
            
        if "MaterialIDImpactorFront" in option:
            matIDImpactorFront = option["MaterialIDImpactorFront"]  
        else:
            matIDImpactorFront = 0
        if "YoungsModulusImpactorFront" in option:
            EImpactorFront = option["YoungsModulusImpactorFront"]
        else:
            EImpactorFront = 2.07e5
        if "PoissonRatioImpactorFront" in option:
            nuImpactorFront = option["PoissonRatioImpactorFront"]
        else:
            nuImpactorFront = 0.3
        if "DensityImpactorFront" in option:
            rhoImpactorFront = option["DensityImpactorFront"]
        else:
            rhoImpactorFront = 7.800E-9
        
        if matIDImpactor != 0:
            materialImpactor = self.dynaImporter.matManager.materials[matIDImpactor]
        else:
            materialImpactor = self.dynaImporter.matManager.CreateElasticMaterial("ImpactorMaterial", rhoImpactor, EImpactor, nuImpactor)

        if matIDImpactorFront != 0:
            materialImpactorFront = self.dynaImporter.matManager.materials[matIDImpactorFront]
        else:
            materialImpactorFront = self.dynaImporter.matManager.CreateElasticMaterial("ImpactorMaterialFront", rhoImpactorFront, EImpactorFront, nuImpactorFront)

        sectionImpactor : KooSectionSolid = self.dynaImporter.sectionManager.CreateSolidSection("ImpactorSection", 1)
        impactElemMan : ElementManager = ElementManager(nodeMan)

        impactorPart = KooPart(nodeMan, impactElemMan, materialImpactor, sectionImpactor, self.dynaImporter.nodeSetManager)
        self.dynaImporter.partManager.CreatePartfromKooPart(impactorPart)
    
        sectionImpactorFront : KooSectionSolid = self.dynaImporter.sectionManager.CreateSolidSection("ImpactorFrontSection", 1)
        impactFrontElemMan : ElementManager = ElementManager(nodeMan)
        impactorPartFront = KooPart(nodeMan, impactFrontElemMan, materialImpactorFront, sectionImpactorFront, self.dynaImporter.nodeSetManager)
        self.dynaImporter.partManager.CreatePartfromKooPart(impactorPartFront)
        return impactorPart, materialImpactor, sectionImpactor, impactElemMan, impactorPartFront, materialImpactorFront, sectionImpactorFront, impactFrontElemMan

    def MaterialExchange(self, option, filePath = ""):
        
        
        matKeywords = option["MIDs"]
        vars = option["Vars"]
        
        # first of vars, vars is dict
        # key is the variable name
        firstVar = vars[list(vars.keys())[0]]
        size = len(firstVar)
        
        for i in range(size):            
            for varKey in vars:
                curVar = vars[varKey]
                # fill empty until the size becomes 10
                varKey = format(varKey, '>10')
                if i >= len(curVar):
                    curVal = curVar[-1]
                else:
                    curVal = curVar[i]
                modifiedPath = ""
                for matKeyword in matKeywords:
                    # deep copy
                    
                    modifiedMatKeyword = copy.deepcopy(matKeywords[matKeyword])                    
                    curValStr = format(curVal, '>10.3e')
                    # all the variables are replaced with the current value
                    for j in range(len(modifiedMatKeyword)):
                        for k in range(len(modifiedMatKeyword[j])):
                            if modifiedMatKeyword[j][k] == varKey:
                                modifiedMatKeyword[j][k] = curValStr                    
                    self.dynaImporter.matManager.AddMaterialfromDyna(modifiedMatKeyword)
                    modifiedPath = modifiedPath + "_" + varKey + "_"
                    modifiedPath = modifiedPath + curValStr
                modifiedPath = modifiedPath.strip()
                curPath = filePath + modifiedPath + ".k"
                
                with open(curPath, "w") as f:
                    f.write("*Keyword\n")
                    f.write(self.dynaImporter.WriteStreamDynaKeyword())
                    f.write("*End\n")
                    
    def PartLocationDOE(self, option, filePath = ""):
               
        pidList = option["PIDs"]
        maskPID = option["MaskPID"]
        obsPidList = option["ObstaclePIDs"]
        dx = option["DX"]
        dy = option["DY"]
        dz = option["DZ"]
        nx = option["NX"]
        ny = option["NY"]
        nz = option["NZ"]
        dilation = option["Dilation"]
        samplingMethod = option["Sampling"]["Method"]
        numofSamples = option["Sampling"]["NumberofSamples"]
        
        checkDimension = dx*dy*dz
        if checkDimension == 0.0:
            if dx == 0.0:
                print("y-z plane sampling")
                na = ny
                nb = nz
                da = dy
                db = dz                
            elif dy == 0.0:
                print("x-z plane sampling")
                na = nx
                nb = nz
                da = dx
                db = dz
            elif dz == 0.0:
                print("x-y plane sampling")
                na = nx
                nb = ny
                da = dx
                db = dy
        else:
            print("x-y-z sampling is not supported")
            return
        if maskPID in self.dynaImporter.partManager.parts:
            maskPart : KooPart = self.dynaImporter.partManager.parts[maskPID]
        else:
            maskPart : KooPart = None
                    
        for pid in pidList:
            part : KooPart = self.dynaImporter.partManager.parts[pid]  
            xmin, xmax, ymin, ymax, zmin, zmax = part.elementManager.GetBoundaryBox()
            
            xmid = (xmin+xmax)/2.0
            ymid = (ymin+ymax)/2.0
            zmid = (zmin+zmax)/2.0
            
            if dx == 0.0:
                alim = (ymid - da, ymid + da)
                blim = (zmid - db, zmid + db)
                plane = "YZ"
            elif dy == 0.0:
                alim = (xmid - da, xmid + da)
                blim = (zmid - db, zmid + db)
                plane = "XZ"
            elif dz == 0.0:
                alim = (xmid - da, xmid + da)
                blim = (ymid - db, ymid + db)
                plane = "XY"
            else:
                print("x-y-z sampling is not supported")
                return
                
                                        
            mask = np.zeros((na, nb), dtype = np.int32)
            
            if maskPart is None:
                mask = np.ones((na, nb), dtype = np.int32)
            else:
                mask = maskPart.FastMaskDilationfromNodes(mask, alim, blim, dilation, plane, "include")

            for opid in obsPidList:
                obsPart : KooPart = self.dynaImporter.partManager.parts[opid]
                mask = obsPart.FastMaskDilationfromNodes(mask, alim, blim, dilation, plane, "exclude")
            
            if samplingMethod == "LatinHypercube":
                samples = sample_lhs_2d(numofSamples, (-da, da), (-db, db))
                print("LatinHypercube sampling")
                print("Number of samples: ", numofSamples)
                if plane == "YZ":
                    for i in range(numofSamples):
                        curDx = 0.0
                        curDy = samples[i][0] 
                        curDz = samples[i][1]
                        part.Translate(0.0, curDy, curDz)                                                
                        if part.CheckinsideValidArea(mask, alim, blim, plane):
                            curDyExponent = format(curDy, '.3e')
                            curDzExponent = format(curDz, '.3e')                        
                            modifiedKeyword = "_DY_" + curDyExponent + "_DZ_" + curDzExponent + ".k"
                            self.WriteModifiedFile(filePath, modifiedKeyword)
                            print("DY: ", curDy, "DZ: ", curDz, " moved and exported")
                        else:
                            print("DY: ", curDy, "DZ: ", curDz, " is not valid")
                                
                        part.Translate(0.0, -curDy, -curDz)
                elif plane == "XZ":
                    for i in range(numofSamples):
                        curDx = samples[i][0] 
                        curDy = 0.0
                        curDz = samples[i][1]
                        part.Translate(curDx, 0.0, curDz)                                                
                        if part.CheckinsideValidArea(mask, alim, blim, plane):      
                            curDxExponent = format(curDx, '.3e')
                            curDzExponent = format(curDz, '.3e')                  
                            modifiedKeyword = "_DX_" + curDxExponent + "_DZ_" + curDzExponent + ".k"
                            self.WriteModifiedFile(filePath, modifiedKeyword)
                            print("DX: ", curDx, "DZ: ", curDz, " moved and exported")
                        else:
                            print("DX: ", curDx, "DZ: ", curDz, " is not valid")
                        part.Translate(-curDx, 0.0, -curDz)
                elif plane == "XY":
                    for i in range(numofSamples):
                        curDx = samples[i][0] 
                        curDy = samples[i][1]
                        curDz = 0.0
                        part.Translate(curDx, curDy, 0.0)
                        if part.CheckinsideValidArea(mask, alim, blim, plane):
                            curDxExponent = format(curDx, '.3e')
                            curDyExponent = format(curDy, '.3e')                        
                            modifiedKeyword = "_DX_" + curDxExponent + "_DY_" + curDyExponent + ".k"
                            self.WriteModifiedFile(filePath, modifiedKeyword)
                            print("DX: ", curDx, "DY: ", curDy, " moved and exported to")
                        else:
                            print("DX: ", curDx, "DY: ", curDy, " is not valid")
                        part.Translate(-curDx, -curDy, 0.0)
               
    def ErodingMinDT(self, dt):
        
        matMan : KooMaterialManager = self.dynaImporter.matManager
        
        matMan.GenerateAddErosionusingDtmin(dt)
        
    def ConstrainedNodalRigidBodyToBeam(self, option):
        cnrbOption = option["CNRB"]
        allOption = option["ALL"]
        E = option["E"]
        pr = option["PR"]
        rho = option["RHO"]
        w = option["Width"]
        h = option["Height"]
         
        if allOption == True:
            for id in self.dynaImporter.constrainedManager.constrainedNodalRigidbodyList:
                cnrbOption[id]= id
        matMan = self.dynaImporter.matManager
        secMan = self.dynaImporter.sectionManager
        materialBeam : KooMaterialElastic = matMan.CreateElasticMaterial("BeamMaterial", rho, E, pr)
        sectionBeam : KooSectionBeam = secMan.CreateBeamSection("BeamSection")
        sectionBeam.SetWidth(w)
        sectionBeam.SetHeight(h)
        sectionBeam.SetElform(13)
        
        elemMan : ElementManager = ElementManager(self.dynaImporter.nodeManager)
        part = KooPart(self.dynaImporter.nodeManager, elemMan, materialBeam, sectionBeam, self.dynaImporter.nodeSetManager)
        self.dynaImporter.partManager.CreatePartfromKooPart(part)
                
        
        self.dynaImporter.SyncronizeMaxID()
        self.dynaImporter.constrainedManager.ChangeConstrainedNodalRigidBodytoBeam(cnrbOption, part, self.dynaImporter.nodeSetManager)
        self.dynaImporter.SyncronizeMaxID()
                
            
        
        
    def PartMorphing(self, option, subOption):
        for i in option:
            curOption = option[i]        
            if "Box" == curOption["Type"]:
                self.PartMorphingBox(curOption, subOption)
            elif "PIDBOX" == curOption["Type"]:
                self.PartMorphingPIDBox(curOption, subOption)
                
                
    def PartMorphingPIDBox(self, option, subOption):
        pid = option["PID"]
        if pid in self.dynaImporter.partManager.parts:
            part: KooPart  = self.dynaImporter.partManager.parts[pid] 
        else:
            print("Part ID is not found")
            return 
        
        boundaryBox = part.elementManager.GetBoundaryBox()
        xMin = boundaryBox[0]
        xMax = boundaryBox[1]
        yMin = boundaryBox[2]
        yMax = boundaryBox[3]
        zMin = boundaryBox[4]
        zMax = boundaryBox[5]
        
        xCenter = (xMin+xMax)/2.0
        yCenter = (yMin+yMax)/2.0
        zCenter = (zMin+zMax)/2.0
        location = [xCenter, yCenter, zCenter]
        xLength = xMax - xMin
        yLength = yMax - yMin
        zLength = zMax - zMin
        xDir = option["XDir"]
        zDir = option["ZDir"]
        angle = option["Angle"]
        pushDistance = option["PushDistance"]
        mode = option["Mode"]
        effectRadius = option["EffectRadius"]
        
        unitscale = subOption["UnitScale"]
        meshSize = subOption["MeshSize"]
        generateMesh = subOption["GenerateMesh"]
        
        partManager = self.dynaImporter.partManager
        
        if generateMesh == True:
            part : KooSTLPart = partManager.AddSTLPartfromKooPart(pid)                        
            part.ExportSTL("temp.stl","",unitscale)
            self.dynaImporter.SyncronizeMaxID()
            elemMan = part.elementManager
            nodeMan = part.nodeManager
            elemNodes = elemMan.GetElementNodes()     
            listnodesid = part.boundaryNodes
            nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
            self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
            print("Solid nodes are removed")
            curElems = elemMan.elements
            self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
            elemMan.RemoveAllElements()            
            print("Solid elements are removed")
            self.dynaImporter.SyncronizeMaxID()
            
            part.GenerateSolidMeshfromSurfaceMesh(meshSize,meshSize)
            #part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius)
            part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius, angle)
        else:
            part : KooPart = partManager.parts[pid]
            part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius, angle)
        
           


    def PartMorphingBox(self, option, subOption):
        pid = option["PID"]
        location = option["Location"]
        xLength = option["XLength"]
        yLength = option["YLength"]
        zLength = option["ZLength"]
        xDir = option["XDir"]
        zDir = option["ZDir"]
        angle = option["Angle"]
        

            
        
        pushDistance = option["PushDistance"]
        mode = option["Mode"]
        effectRadius = option["EffectRadius"]
        
        unitscale = subOption["UnitScale"]
        meshSize = subOption["MeshSize"]
        generateMesh = subOption["GenerateMesh"]
        
        
        
        partManager = self.dynaImporter.partManager
                
                
        if generateMesh == True:
            part : KooSTLPart = partManager.AddSTLPartfromKooPart(pid)                        
            part.ExportSTL("temp.stl","",unitscale)
            self.dynaImporter.SyncronizeMaxID()
            elemMan = part.elementManager
            nodeMan = part.nodeManager
            elemNodes = elemMan.GetElementNodes()     
            listnodesid = part.boundaryNodes
            nodeMan.RemoveNodesExceptNodes(elemNodes, listnodesid)
            self.dynaImporter.nodeSetManager.RemoveNodesExceptNodes(elemNodes, listnodesid)
            print("Solid nodes are removed")
            curElems = elemMan.elements
            self.dynaImporter.partManager.elementManager.RemoveSetElements(curElems)
            elemMan.RemoveAllElements()            
            print("Solid elements are removed")
            self.dynaImporter.SyncronizeMaxID()
            
            part.GenerateSolidMeshfromSurfaceMesh(meshSize,meshSize)
            #part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius)
            part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius, angle)
        else:
            part : KooPart = partManager.parts[pid]
            part.MorphwithBox(location, [xLength, yLength, zLength], xDir, zDir, pushDistance, mode, effectRadius, angle)
        
    def WarpedPart(self, option):
        pids = option["PIDs"]
        warpageFileTop = option["WarpageFileTop"]
        warpageFileBottom = option["WarpageFileBottom"]
        unitScale = option["UnitScale"]
        amplitudeTop = option["AmplitudeTop"]
        amplitudeBottom = option["AmplitudeBottom"]
        location = option["Location"]
        xLength = option["XLength"]
        yLength = option["YLength"]
        direction = option["Direction"]
    
        xmin = 1.0e99
        xmax = -1.0e99
        ymin = 1.0e99
        ymax = -1.0e99
        zmin = 1.0e99
        zmax = -1.0e99
        
        for pid in pids:
            if pid in self.dynaImporter.partManager.parts:
                part : KooPart = self.dynaImporter.partManager.parts[pid]
                curxmin, curxmax, curymin, curymax, curzmin, curzmax = part.elementManager.GetBoundaryBox()
                xmin = min(xmin, curxmin)
                xmax = max(xmax, curxmax)
                ymin = min(ymin, curymin)
                ymax = max(ymax, curymax)
                zmin = min(zmin, curzmin)
                zmax = max(zmax, curzmax)
        if xLength == 0.0 or yLength == 0.0:
            xLength = xmax - xmin
            yLength = ymax - ymin
            location = [xmin, ymin, zmax]
    
                    
        nodesMoved = {}
        if warpageFileBottom == None:
            for pid in pids:
                if pid in self.dynaImporter.partManager.parts:
                    part : KooPart = self.dynaImporter.partManager.parts[pid]   
                    if direction[0] == 0.0 and direction[1] == 0.0 and direction[2] == 1.0:
                        addNodes = part.WarpZdirectionPart(warpageFileTop, location[0], location[1], location[2], xLength, yLength, unitScale, amplitudeTop, nodesMoved) 
                        nodesMoved = {**nodesMoved, **addNodes}

        else:
            for pid in pids:
                if pid in self.dynaImporter.partManager.parts:
                    part : KooPart = self.dynaImporter.partManager.parts[pid]   
                    if direction[0] == 0.0 and direction[1] == 0.0 and direction[2] == 1.0:
                        addNodes = part.WarpZdirectionPartfromTopBottom(warpageFileTop, warpageFileBottom, location[0], location[1], location[2], xLength, yLength, unitScale, amplitudeTop, amplitudeBottom, zmin, zmax, nodesMoved)          
                        nodesMoved = {**nodesMoved, **addNodes}
        
    def WarpedtoInitialStressPart(self, option):
        pids = option["PIDs"]
        warpageFileTop = option["WarpageFileTop"]
        warpageFileBottom = option["WarpageFileBottom"]
        unitScale = option["UnitScale"]
        amplitudeTop = option["AmplitudeTop"]
        amplitudeBottom = option["AmplitudeBottom"]
        location = option["Location"]
        xLength = option["XLength"]
        yLength = option["YLength"]
        direction = option["Direction"]
        addThickness = option["AdditionalThickness"]
     
    
        xmin = 1.0e99
        xmax = -1.0e99
        ymin = 1.0e99
        ymax = -1.0e99
        zmin = 1.0e99
        zmax = -1.0e99
        
        for pid in pids:
            if pid in self.dynaImporter.partManager.parts:
                part : KooPart = self.dynaImporter.partManager.parts[pid]
                curxmin, curxmax, curymin, curymax, curzmin, curzmax = part.elementManager.GetBoundaryBox()
                xmin = min(xmin, curxmin)
                xmax = max(xmax, curxmax)
                ymin = min(ymin, curymin)
                ymax = max(ymax, curymax)
                zmin = min(zmin, curzmin)
                zmax = max(zmax, curzmax)
        if xLength == 0.0 or yLength == 0.0:
            xLength = xmax - xmin
            yLength = ymax - ymin
            location = [xmin, ymin, zmax]
        
        if warpageFileBottom == None:
            for pid in pids:
                if pid in self.dynaImporter.partManager.parts:
                    part : KooPart = self.dynaImporter.partManager.parts[pid]   
                    if direction[0] == 0.0 and direction[1] == 0.0 and direction[2] == 1.0:
                        EidList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList = part.WarpZdirectionParttoInitialStress(warpageFileTop, location[0], location[1], location[2], xLength, yLength, unitScale, amplitudeTop, addThickness)
                        listSize = len(EidList)
                        if listSize > 0:
                            # 1 with listSize
                            nintList = [1] * listSize
                            nhisvList = [0] * listSize
                            largeList = [0] * listSize
                            iveflgList = [0] * listSize
                            ialegList = [0] * listSize
                            nthintList = [0] * listSize
                            nthhsvList = [0] * listSize
                            epsList = [[0.0]] * listSize
                            self.dynaImporter.initialManager.CreateInitialStressSolid(EidList, nintList, nhisvList, largeList, iveflgList, ialegList, nthintList, nthhsvList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList, epsList)
        else:
            for pid in pids:
                if pid in self.dynaImporter.partManager.parts:
                    part : KooPart = self.dynaImporter.partManager.parts[pid]   
                    if direction[0] == 0.0 and direction[1] == 0.0 and direction[2] == 1.0:
                        EidList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList = part.WarpZdirectionPartfromTopBottomtoInitialStress(warpageFileTop, warpageFileBottom, location[0], location[1], location[2], xLength, yLength, unitScale, amplitudeTop, amplitudeBottom, zmin, zmax, addThickness)
                        listSize = len(EidList)
                        if listSize > 0:
                            # 1 with listSize
                            nintList = [1] * listSize
                            nhisvList = [0] * listSize
                            largeList = [0] * listSize
                            iveflgList = [0] * listSize
                            ialegList = [0] * listSize
                            nthintList = [0] * listSize
                            nthhsvList = [0] * listSize
                            epsList = [[0.0]] * listSize
                            self.dynaImporter.initialManager.CreateInitialStressSolid(EidList, nintList, nhisvList, largeList, iveflgList, ialegList, nthintList, nthhsvList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList, epsList)
        
        if self.dynaImporter.controlManager.controlDynamicRelaxation == None:
            self.dynaImporter.controlManager.SetControlDynamicRelaxation()            

    def DimensionalTolerance(self, option, filePath):
        mode = option["Mode"]
        
        if mode == "LIST":
            self.DimensionalToleranceList(option, filePath)
        elif mode == "NORM":
            self.DimensionalToleranceNorm(option, filePath)    
        elif mode == "LHS":
            self.DimensionalToleranceLHS(option, filePath) 
        
    def DimensionalToleranceList(self, option, filePath):
        partOptions : dict = option["PartOption"]
        first_key = next(iter(partOptions))
        first_direction = next(iter(partOptions[first_key]))
        first_value = partOptions[first_key][first_direction]
        
        numofSamples = len(first_value)
        lengthDict = {}
        if self.dynaImporter.controlManager.controlDynamicRelaxation == None:
            self.dynaImporter.controlManager.SetControlDynamicRelaxation(250,0.00001,0.35,1.0e+99,0.3,0,0.0001,-1)            
        for pid in partOptions.keys():
            if pid in self.dynaImporter.partManager.parts:
                part : KooPart = self.dynaImporter.partManager.parts[pid]
                curxmin, curxmax, curymin, curymax, curzmin, curzmax = part.elementManager.GetBoundaryBox()
                lengthDict[pid] = [curxmax - curxmin, curymax - curymin, curzmax - curzmin]
            
        
        for i in range(0,numofSamples):            
            initList = []
            for pid, valueList in partOptions.items():
                if pid in self.dynaImporter.partManager.parts:
                    part : KooPart = self.dynaImporter.partManager.parts[pid]
                    
                    directions = list(valueList.keys())                    
                    ex = 0.0
                    ey = 0.0
                    ez = 0.0 
                    if "x" in directions:
                        ex = KooDynaFloat(valueList["x"][i])
                    if "y" in directions:
                        ey = KooDynaFloat(valueList["y"][i])
                    if "z" in directions:
                        ez = KooDynaFloat(valueList["z"][i])    
                    Lx = (lengthDict[pid][0])
                    Ly = (lengthDict[pid][1])
                    Lz = (lengthDict[pid][2])

                    EidList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList = part.LengthVariationbyTolerance(ex,ey,ez)
                    listSize = len(EidList)
                    if listSize > 0:
                        nintList = [1] * listSize
                        nhisvList = [0] * listSize
                        largeList = [0] * listSize
                        iveflgList = [0] * listSize
                        ialegList = [0] * listSize
                        nthintList = [0] * listSize
                        nthhsvList = [0] * listSize
                        epsList = [[0.0]] * listSize
                        initStress = self.dynaImporter.initialManager.CreateInitialStressSolid(EidList, nintList, nhisvList, largeList, iveflgList, ialegList, nthintList, nthhsvList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList, epsList)
                        initList.append(initStress)

            if filePath is not None:
                modifiedKey = f"_DimensionalTolerance_{i}.k"
                curPath = filePath + modifiedKey 
                with open(curPath, "w") as f:
                    f.write("*Keyword\n")
                    f.write(self.dynaImporter.WriteStreamDynaKeyword())
                    f.write("*End\n")

            initStressIDList = [initStress.id for initStress in initList]
            for initid in initStressIDList:
                self.dynaImporter.initialManager.RemoveInitial(initid)
            initList = []
        pass

    def DimensionalToleranceNorm(self, option, filePath):
        partOptions : dict = option["PartOption"]
        numofSamples = option["NumberofSamples"]
        #lengthDict = {}
        #if self.dynaImporter.controlManager.controlDynamicRelaxation == None:
        #    self.dynaImporter.controlManager.SetControlDynamicRelaxation(250,0.00001,0.35,1.0e+99,0.3,0,0.0001,-1)
        #for pid in partOptions.keys():
        #    if pid in self.dynaImporter.partManager.parts:
        #        part : KooPart = self.dynaImporter.partManager.parts[pid]
        #        curxmin, curxmax, curymin, curymax, curzmin, curzmax = part.elementManager.GetBoundaryBox()
        #        lengthDict[pid] = [curxmax - curxmin, curymax - curymin, curzmax - curzmin]
        
        strainDict = {}
        for pid, valueList in partOptions.items():
            if pid in self.dynaImporter.partManager.parts:
                directions = list(valueList.keys())                
                if "x" in directions:
                    avgX = KooDynaFloat(valueList["x"][0])
                    sigX = KooDynaFloat(valueList["x"][1])
                    limX = KooDynaFloat(valueList["x"][2])
                    strainXList = truncated_normal_samples(avgX,sigX,limX,numofSamples)
                else:
                    strainXList = np.zeros(numofSamples)                    
                    
                if "y" in directions:
                    avgY = KooDynaFloat(valueList["y"][0])
                    sigY = KooDynaFloat(valueList["y"][1])
                    limY = KooDynaFloat(valueList["y"][2])
                    strainYList = truncated_normal_samples(avgY,sigY,limY,numofSamples)
                else:
                    strainYList = np.zeros(numofSamples)

                if "z" in directions:
                    avgZ = KooDynaFloat(valueList["z"][0])
                    sigZ = KooDynaFloat(valueList["z"][1])
                    limZ = KooDynaFloat(valueList["z"][2])
                    strainZList = truncated_normal_samples(avgZ,sigZ,limZ,numofSamples)
                else:
                    strainZList = np.zeros(numofSamples)
                
                strainDict[pid] = {"x": strainXList, "y": strainYList, "z": strainZList}        
        
        if filePath is not None:
            inputVarFilePath = filePath + f"_DimensionalTolerance.txt"
            with open(inputVarFilePath, "w") as f:
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        f.write(f"PID:, {pid},,")
                f.write("\n")
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        f.write(f"Name:, {part.name},,")                        
                f.write("\n")
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        f.write("x,y,z,")
                f.write("\n")
                for i in range(numofSamples):
                    for pid in partOptions:
                        if pid in self.dynaImporter.partManager.parts:
                            f.write(f"{strainDict[pid]['x'][i]},{strainDict[pid]['y'][i]},{strainDict[pid]['z'][i]},")
                    f.write("\n")

            for i in range(0,numofSamples):
                initList = [] 
                for pid in partOptions:
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        
                        ex = strainDict[pid]["x"][i]
                        ey = strainDict[pid]["y"][i]
                        ez = strainDict[pid]["z"][i]
                        EidList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList = part.LengthVariationbyTolerance(ex,ey,ez)
                        listSize = len(EidList)
                        if listSize > 0:
                            nintList = [1] * listSize
                            nhisvList = [0] * listSize
                            largeList = [0] * listSize
                            iveflgList = [0] * listSize
                            ialegList = [0] * listSize
                            nthintList = [0] * listSize
                            nthhsvList = [0] * listSize
                            epsList = [[0.0]] * listSize
                            initStress = self.dynaImporter.initialManager.CreateInitialStressSolid(EidList, nintList, nhisvList, largeList, iveflgList, ialegList, nthintList, nthhsvList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList, epsList)
                            initList.append(initStress)                      
                
                modifiedKey = f"_DimensionalTolerance_{i}.k"
                curPath = filePath + modifiedKey 
                with open(curPath, "w") as f:
                    f.write("*Keyword\n")
                    f.write(self.dynaImporter.WriteStreamDynaKeyword())
                    f.write("*End\n")
            
                initStressIDList = [initStress.id for initStress in initList]
                for initid in initStressIDList:
                    self.dynaImporter.initialManager.RemoveInitial(initid)
                initList = []
            

    def DimensionalToleranceLHS(self, option, filePath):
        partOptions : dict = option["PartOption"]
        numofSamples = option["NumberofSamples"]
                
        strainMinMaxDict = {} 
        
        for pid, valueList in partOptions.items():
            if pid in self.dynaImporter.partManager.parts:
                directions = list(valueList.keys())
                if "x" in directions:
                    minX = KooDynaFloat(valueList["x"][0])
                    maxX = KooDynaFloat(valueList["x"][1])
                else:
                    minX = 0
                    maxX = 0
                if "y" in directions:
                    minY = KooDynaFloat(valueList["y"][0])
                    maxY = KooDynaFloat(valueList["y"][1])
                else:
                    minY = 0
                    maxY = 0
                if "z" in directions:
                    minZ = KooDynaFloat(valueList["z"][0])
                    maxZ = KooDynaFloat(valueList["z"][1])
                else:
                    minZ = 0
                    maxZ = 0
                strainMinMaxDict[pid] = [minX, maxX, minY, maxY, minZ, maxZ]

        # 1) 변수 목록 만들기 (min=max=0 인 변수만 제외)
        #    columns: CSV 칼럼명 (예: "123_x"), ranges: (min,max), const_mask: True면 상수
        columns = []
        ranges = []
        const_mask = []   # 상수 변수 여부 (min==max)
        pid_axis_pairs = []  # (pid, axis) 맵핑 복원용
        for pid, vdict in partOptions.items():
            # x,y,z 중 들어있는 키만 처리
            for axis in ("x", "y", "z"):
                if axis in vdict:
                    vmin, vmax = vdict[axis][0], vdict[axis][1]
                    # 질문 조건: min=max=0 인 경우만 제외
                    if float(vmin) == 0.0 and float(vmax) == 0.0:
                        continue
                    columns.append(f"{pid}_{axis}")
                    ranges.append((float(vmin), float(vmax)))
                    const_mask.append(float(vmin) == float(vmax))
                    pid_axis_pairs.append((pid, axis))
        seed = 42        
        rng = np.random.default_rng(seed)
        # 2) [0,1]에서 LHS 생성 (상수 변수를 포함해 차원 수는 columns 길이와 동일)
        unit = lhs_unit(numofSamples, len(columns), rng=rng)

        # 3) 각 변수 범위로 스케일링 (상수면 그대로 고정)
        samples_arr = np.zeros_like(unit)
        for j, ((mn, mx), is_const) in enumerate(zip(ranges, const_mask)):
            if is_const:
                samples_arr[:, j] = mn
            else:
                # 선형 스케일링: mn + unit * (mx - mn)
                samples_arr[:, j] = mn + unit[:, j] * (mx - mn)
        # 4) 결과를 샘플별 {pid: {"x":val, "y":val, "z":val}} 형태로 변환 (없는 축은 0)
        samples_list = []
        for i in range(numofSamples):
            by_part = {}
            # 먼저 pid별로 x,y,z를 0으로 초기화
            for pid, _ in partOptions.items():
                by_part[pid] = {"x": 0.0, "y": 0.0, "z": 0.0}

            # 샘플링된 값들 채워 넣기
            for j, (pid, axis) in enumerate(pid_axis_pairs):
                by_part[pid][axis] = float(samples_arr[i, j])

            samples_list.append(by_part)
                
        if filePath is not None:
            inputVarFilePath = filePath + f"_DimensionalTolerance.txt"
            with open(inputVarFilePath, "w") as f:
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        f.write(f"PID:, {pid},,")
                f.write("\n")
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        f.write(f"Name:, {part.name},,")
                f.write("\n")
                for pid, valueList in partOptions.items():
                    if pid in self.dynaImporter.partManager.parts:
                        f.write("x,y,z,")
                f.write("\n")                
                for samples in samples_list:
                    for pid, axis_dict in samples.items():
                        for axis, value in axis_dict.items():
                            f.write(f"{value},")
                        f.write("\n")
                
            for i in range(0,numofSamples):
                initList = [] 
                for pid in partOptions:
                    if pid in self.dynaImporter.partManager.parts:
                        part : KooPart = self.dynaImporter.partManager.parts[pid]
                        
                        ex = samples_list[i][pid]["x"]
                        ey = samples_list[i][pid]["y"]
                        ez = samples_list[i][pid]["z"]
                        EidList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList = part.LengthVariationbyTolerance(ex,ey,ez)
                        listSize = len(EidList)
                        if listSize > 0:
                            nintList = [1] * listSize
                            nhisvList = [0] * listSize
                            largeList = [0] * listSize
                            iveflgList = [0] * listSize
                            ialegList = [0] * listSize
                            nthintList = [0] * listSize
                            nthhsvList = [0] * listSize
                            epsList = [[0.0]] * listSize
                            initStress = self.dynaImporter.initialManager.CreateInitialStressSolid(EidList, nintList, nhisvList, largeList, iveflgList, ialegList, nthintList, nthhsvList, SxxList, SyyList, SzzList, SxyList, SyzList, SxzList, epsList)
                            initList.append(initStress)      
                modifiedKey = f"_DimensionalTolerance_{i}.k"
                curPath = filePath + modifiedKey
                with open(curPath, "w") as f:
                    f.write("*Keyword\n")
                    f.write(self.dynaImporter.WriteStreamDynaKeyword())
                    f.write("*End\n")
                initStressIDList = [initStress.id for initStress in initList]
                for initid in initStressIDList:
                    self.dynaImporter.initialManager.RemoveInitial(initid)
                initList = []
                
    def CohesiveBetweenConformalMeshes(self, option):

        curOption = option

        RO = curOption["CohesiveMat"]["RO"]
        ROFlag = curOption["CohesiveMat"]["ROFlag"]
        INTFAIL = curOption["CohesiveMat"]["INTFAIL"]
        EN = curOption["CohesiveMat"]["EN"]
        ET = curOption["CohesiveMat"]["ET"]
        GIC = curOption["CohesiveMat"]["GIC"]
        GIIC = curOption["CohesiveMat"]["GIIC"]
        XMU = curOption["CohesiveMat"]["XMU"]
        T = curOption["CohesiveMat"]["T"]
        S = curOption["CohesiveMat"]["S"]
        UND = curOption["CohesiveMat"]["UND"]
        UTD = curOption["CohesiveMat"]["UTD"]
        GAMMA = curOption["CohesiveMat"]["GAMMA"]

        mat = self.dynaImporter.matManager.CreateCohesiveMixedModeMaterial("CohesiveMixedModeMaterial", RO, ROFlag, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA)
        partAList = curOption["PartA"]
        partBList = curOption["PartB"]
        thicknessList = curOption["Thickness"]
        
        for i in range(len(partAList)):
            self.dynaImporter.SyncronizeMaxID()
            pidA = partAList[i]
            pidB = partBList[i]
            thickness = thicknessList[i]
            partA : KooPart = self.dynaImporter.partManager.parts[pidA]
            partB : KooPart = self.dynaImporter.partManager.parts[pidB]
            section = self.dynaImporter.sectionManager.CreateShellSection("CohesiveShell",thickness,20)

            boundaryA, nodesA = partA.elementManager.GetExternalBoundariesandNodeDict(True)
            boundaryB, nodesB = partB.elementManager.GetExternalBoundariesandNodeDict(True) 
            
            sharedNodes = {}
            for keyA, nodeA in nodesA.items():
                if keyA in nodesB:
                    nodeB = nodesB[keyA]
                    sharedNodes[keyA] = nodeA
            boundaryCohesiveA = []
            boundaryCohesiveB = [] 
            for boundary in boundaryA:
                for j in range(len(boundary)):
                    if boundary[j] in sharedNodes:
                        boundaryCohesiveA.append(boundary)
                        break
            for boundary in boundaryB:
                for j in range(len(boundary)):
                    if boundary[j] in sharedNodes:
                        boundaryCohesiveB.append(boundary)
                        break
            partA.elementManager.SplitNodes(sharedNodes)
            partB.elementManager.SplitNodes(sharedNodes)
            elemMan : ElementManager = ElementManager(self.dynaImporter.nodeManager)
            partCohesive = KooPart(self.dynaImporter.nodeManager, elemMan, mat, section, self.dynaImporter.nodeSetManager)
            self.dynaImporter.partManager.CreatePartfromKooPart(partCohesive)
            elemMan.CreateElementsfromSegments(sharedNodes, boundaryCohesiveA)
            segmentASet :KooSegmentSet = self.dynaImporter.segmentSetManager.CreateSegmentSet()
            segmentASet.AddSegments(boundaryCohesiveA)
            segmentBSet :KooSegmentSet = self.dynaImporter.segmentSetManager.CreateSegmentSet()
            segmentBSet.AddSegments(boundaryCohesiveB)


            SSID = partCohesive.id
            MSID = segmentASet.sid
            SSTYP = 3
            MSTYP = 2
            SBOXID = 0
            MBOXID = 0
            SPR = 0
            MPR = 0
            FS = 0.0
            FD = 0.0
            DC = 0.0
            VC = 0.0
            VDC = 5.0
            PENCHK = 0
            BT = 0.00
            DT = 1.00000E20
            SFS = ""
            SFM = ""
            SST = ""
            MST = ""
            SFST = ""
            SFMT = ""
            FSF = ""
            VSF = ""
            self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            MSID = segmentBSet.sid
            self.dynaImporter.contactManager.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)

            self.dynaImporter.contactManager.RemoveTiedContactBetweenTwoPart(partA.id, partB.id)


    def DynaintoInitial(self, option, folderPath, filePath):
        dynainpath = option["DynainPath"]
        if dynainpath == "dynain":
            dynainpath = filePath
        else:
            dynainpath = os.path.join(folderPath, dynainpath)
        #적용 완료
        includeStress = option["IncludeStress"]
        #적용 완료
        removeDynamicRelaxation = option["RemoveDynamicRelaxation"]
        dynamicRelaxation = option["DynamicRelaxation"]
        #적용 완료
        moveToOriginbyNode = option["MovetoOriginbyNode"]
        #적용 완료
        moveToOriginAutomatic = option["MovetoOriginAutomatic"]
        removePartNameList = option["RemovePartNameList"]
        removePartIDList = option["RemovePartIDList"]
        removeContactIDList = option["RemoveContactIDList"]


        if removeDynamicRelaxation is True and self.dynaImporter.controlManager.controlDynamicRelaxation is not None:
            self.dynaImporter.controlManager.controlDynamicRelaxation = None
        rotation = False
        rotationNodeList = []
        if moveToOriginAutomatic == True or len(moveToOriginbyNode) < 3:
            xmin, ymin, zmin, xmax, ymax, zmax = self.dynaImporter.nodeManager.GetBoundingBox()
            node1 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin,ymin,zmin)
            node2 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmax,ymin,zmin)
            node3 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin,ymax,zmin)
            rotationNodeList.append(node1)
            rotationNodeList.append(node2)
            rotationNodeList.append(node3)
            rotation = True

        elif len(moveToOriginbyNode) == 3:

            node1 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[0])
            node2 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[1])
            node3 = self.dynaImporter.nodeManager.FindNodefromID(moveToOriginbyNode[2])

            if node1 == None or node2 == None or node3 == None:
                xmin, ymin, zmin, xmax, ymax, zmax = self.dynaImporter.nodeManager.GetBoundingBox()
                node1 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin,ymin,zmin)
                node2 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmax,ymin,zmin)
                node3 = self.dynaImporter.nodeManager.FindClosestNodefromPoint(xmin,ymax,zmin)

            rotationNodeList.append(node1)
            rotationNodeList.append(node2)
            rotationNodeList.append(node3)
            rotation = True
        else:
            rotation = False


        if rotation == True:
            P = [[node1.x, node1.y, node1.z], [node2.x, node2.y, node2.z], [node3.x, node3.y, node3.z]]
        else:
            P = []
        dynainImporter : KooDynaImporter = KooDynaImporter()


        self.dynaSubImporter[dynainpath] = dynainImporter

        dynainImporter.importDynaFile(dynainpath)
        dynainImporter.importKeywordstoManager()

        if includeStress is False:
            dynainImporter.initialManager.ClearInitial()
        else:
            self.dynaImporter.initialManager.ClearInitial()

        self.dynaImporter.OverwritefromManager(dynainImporter)

        if rotation == True:
            movedNode1 = self.dynaImporter.nodeManager.FindNodefromID(node1.id)
            movedNode2 = self.dynaImporter.nodeManager.FindNodefromID(node2.id)
            movedNode3 = self.dynaImporter.nodeManager.FindNodefromID(node3.id)
            Q = [[movedNode1.x, movedNode1.y, movedNode1.z], [movedNode2.x, movedNode2.y, movedNode2.z], [movedNode3.x, movedNode3.y, movedNode3.z]]

            self.dynaImporter.nodeManager.ApplyTransformfromThreePoints(P,Q,None,True)

        if dynamicRelaxation == True:
            self.dynaImporter.controlManager.clear()
            self.dynaImporter.databaseManager.clear()
            self.dynaImporter.controlManager.SetControlDynamicRelaxation(250,0.00001,0.35,1.0e+99,0.3,0,0.0001,-1)

        if len(removePartNameList) > 0:
            for name in removePartNameList:
                self.dynaImporter.RemovePartbyName(name,True)
        if len(removePartIDList) > 0:
            for pid in removePartIDList:
                self.dynaImporter.RemovePart(pid,True)

        if len(removeContactIDList) > 0:
            for cid in removeContactIDList:
                self.dynaImporter.contactManager.RemoveContactbyID(cid)    


    def ContactAutoDecomposition(self, option):
        xMargin = option["SearchMarginX"]
        yMargin = option["SearchMarginY"]
        zMargin = option["SearchMarginZ"]
        contactKeyword = option["ContactKeyword"]

        if len(contactKeyword) > 0:
            curMaxCID = self.dynaImporter.contactManager.maxid + 1
            contactKeyword[1][0] = contactKeyword[1][0].replace("       CID", format(curMaxCID, ">10"))
        self.dynaImporter.contactManager.AddContactfromDynawithID(contactKeyword)
        self.dynaImporter.contactManager.ConvertAss5ToAstsPartPairs(self.dynaImporter.partManager, curMaxCID, xMargin,yMargin, zMargin)

    def TranslationDOE(self, option, filePath):
        curOption = option
        translationDict = curOption["Translation"]
        firstpid = list(translationDict.keys())[0]
        firstpidTransXList = translationDict[firstpid]["X"]
        numofSamples = len(firstpidTransXList)
        jsonFileName = filePath + "_TranslationDOE.json"
        f = open(jsonFileName, "w")
        jsonDict = {}
        for i in range(numofSamples):
            for pid in translationDict:
                transX = translationDict[pid]["X"][i]
                transY = translationDict[pid]["Y"][i]
                transZ = translationDict[pid]["Z"][i]
                part : KooPart = self.dynaImporter.partManager.parts[pid]
                part.Translate(transX, transY, transZ)

            modifiedKeyword = f"_TranslationDOE_{i}.k"
            curPath = filePath + modifiedKeyword
            with open(curPath, "w") as f:
                f.write("*Keyword\n")
                f.write(self.dynaImporter.WriteStreamDynaKeyword())
                f.write("*End\n")
            jsonDict[i] = {}
            jsonDict[i]["filePath"] = curPath
            jsonDict[i]["parts"] = {}
            for pid in translationDict:
                transX = translationDict[pid]["X"][i]
                transY = translationDict[pid]["Y"][i]
                transZ = translationDict[pid]["Z"][i]
                part : KooPart = self.dynaImporter.partManager.parts[pid]
                part.Translate(-transX, -transY, -transZ)
                jsonDict[i]["parts"][pid] = {"transX": transX, "transY": transY, "transZ": transZ}

        f.write(json.dumps(jsonDict, indent=4))
        f.close()

    def SimulationAutomation(self, jsonOptionList, inputFile, inputObjFile, metaData):
        dynaASScriptGenerator : KooDynaAutomaticSimulationScriptGenerator = KooDynaAutomaticSimulationScriptGenerator(jsonOptionList, metaData)                
        dynaASScriptGenerator.generate_for_all()

    def SimulationAutomationPrevious(self, jsonOptionList, inputFile, inputObjFile):
        for jsonOption in jsonOptionList:
            cfg = parse_scenario_by_type(jsonOption, inputFile, inputObjFile)
            if isinstance(cfg, FullAngleMBDConfig):
                mbdCount = cfg.mbdCount
                angleSource = cfg.angleSource
                obj_path = cfg.obj_path
                angle_src_path = cfg.angleSource_path
                print("[MBD]", cfg.name, mbdCount, angleSource, obj_path, angle_src_path)
            elif isinstance(cfg, FullAngleConfig):
                # === fullAngle ===
                faTotal = cfg.faTotal
                includeFace6 = cfg.includeFace6
                includeEdge12 = cfg.includeEdge12
                includeCorner8 = cfg.includeCorner8
                k_path = cfg.k_path
                angleSource = cfg.angleSource
                preMbdCount = cfg.preMbdCount
                preFaTotal = cfg.preFaTotal
                angle_src_path = cfg.angleSource_path
                # self.run_full_angle(cfg)
                print("[FA]", cfg.name, faTotal, includeFace6, includeEdge12, includeCorner8, k_path, angleSource, preMbdCount, preFaTotal, angle_src_path)

            elif isinstance(cfg, FullAngleCumulativeConfig):
                # === fullAngleCumulative ===
                repeat = cfg.cumRepeatCount
                doe = cfg.cumDOECount
                grid = cfg.cumDirectionsGrid  # [DOE][repeat]
                k_path = cfg.k_path
                # self.run_cumulative(cfg)
                print("[CUM]", cfg.name, repeat, doe, k_path)
                # 예: 각 DOE 행 출력
                # for i, row_dirs in enumerate(grid, 1):
                #     print(f"  DOE#{i}: {row_dirs}")

            elif isinstance(cfg, PartialImpactConfig):
                # === partialImpact ===
                mode = cfg.mode
                k_path = cfg.k_path
                txt_path = cfg.piTxt_path
                # self.run_partial(cfg)
                print("[PI]", cfg.name, mode, k_path, txt_path)

    def RemoveDuplicateTiedContacts(self, option):
        """
        중복된 Tied Contact를 제거합니다.
        SSID/MSID 순서에 상관없이 동일한 페어에 대해 중복된 Tied Contact가 있으면
        먼저 읽힌 것만 남기고 나머지는 삭제합니다.
        """
        return self.dynaImporter.contactManager.RemoveDuplicateTiedContacts()

    def FEMtoIGA(self, option):
        """
        FEM 파트들을 IGA로 일괄 변환

        option = {
            'IGAParts': [
                {
                    'source_pid': int,
                    'iga_id': int,
                    'output_file': str,
                    'element_edge_length': {'rr': float, 'rs': float, 'rt': float},
                    'bbox_offset_ratio': float,
                    'integration_rule': int
                },
                ...
            ]
        }
        """
        iga_parts_configs = option.get("IGAParts", [])

        if not iga_parts_configs:
            print("Warning: No IGA parts specified in FEMtoIGA mode")
            return

        partManager = self.dynaImporter.partManager
        materialManager = self.dynaImporter.matManager
        sectionManager = self.dynaImporter.sectionManager

        for config in iga_parts_configs:
            try:
                # CreateIGAPart 호출
                iga_part = partManager.CreateIGAPart(
                    source_pid=config['source_pid'],
                    materialManager=materialManager,
                    sectionManager=sectionManager,
                    options={
                        'iga_id': config['iga_id'],
                        'output_file': config['output_file'],
                        'element_edge_length': config['element_edge_length'],
                        'bbox_offset_ratio': config['bbox_offset_ratio'],
                        'integration_rule': config['integration_rule']
                    }
                )

                # IGA 파일 생성
                iga_part.WriteToFile()

                print(f"✓ IGA Part {config['iga_id']} created from FEM Part {config['source_pid']} → {config['output_file']}")

            except Exception as e:
                print(f"✗ Failed to create IGA Part {config.get('iga_id', '?')} from PID {config.get('source_pid', '?')}: {e}")
                raise