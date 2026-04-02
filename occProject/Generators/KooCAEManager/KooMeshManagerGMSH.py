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

from os.path import join
import sys
from OCC.Core.BRepTools import breptools_Write
from OCC.Extend.DataExchange import read_stl_file

from KooCAEManager.KooMeshImporter import *
from KooCAEManager.KooElementSet import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooNode import *
from KooCAEManager.KooSection import *  
from KooCAEManager.KooMaterial import *

from OCC.Core.gp import gp_Trsf
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
import OCC.Core.STEPControl as STEPControl
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone
class KooMeshManagerList:
    def __init__(self):
        self.path = ".\\"
        self.name = "MeshManager"
        self.meshManagerList = []

    def AddMeshManager(self, meshManager):
        self.meshManagerList.append(meshManager)

    def GetMeshManager(self, index):
        return self.meshManagerList[index]
    
    def SetPath(self, path):
        self.path = path
    
    def SetName(self, name):
        self.name = name

    def GetMaxIDs(self):
        maxNID = 0
        maxEID = 0
        
        for meshManager in self.meshManagerList:
            maxNID, maxEID = meshManager.GetMaxIDs()
        return maxNID, maxEID
    
    def GenerateStructuredMesh(self, ptList, meshSize, numElementinThickness, thicknessList, matidList, eosidList, maxNID = 0, maxEID = 0, maxPID = 0, sectionManager :KooSectionManager = 0, nodeSetManager : NodeSetManager = None):
        if len(ptList) < 8:
            print("ptList must have 8 points")
            return
        numLayer = len(thicknessList)
        zMin = ptList[0].Z()
        zMax = ptList[4].Z()
        zPosList = []
        zPosList.append(zMin)
        for i in range(numLayer):
            for j in range(numElementinThickness):
                zLast = zPosList[-1]
                zPosList.append(zLast + thicknessList[i])


        for i in range(numLayer):
            meshManager = KooMeshManagerGMSH(sectionMan=sectionManager, nodeSetMan=nodeSetManager)
            meshManager.SetName(self.name + "_" + str(i))
            meshManager.SetPath(self.path)
            meshManager.part.SetMaterialID(matidList[i])
            meshManager.part.SetID(maxPID + i + 1)
            if len(eosidList) > i:
                meshManager.part.SetEOSID(eosidList[i])
            meshManager.sectionMan.CreateSolidSection("SolidSection_" + str(i))
            meshManager.part.SetSectionID(meshManager.sectionMan.maxid)
            self.AddMeshManager(meshManager)

        numEleminXDirection = int((ptList[1].X() - ptList[0].X())/meshSize)
        if numEleminXDirection < 1:
            numEleminXDirection = 1
        numEleminYDirection = int((ptList[3].Y() - ptList[0].Y())/meshSize)
        if numEleminYDirection < 1:
            numEleminYDirection = 1
        numEleminZDirection = len(zPosList) - 1

        nid = maxNID+1
        # 3D array of nodes
        node3DMatrix = []
        
        for i in range(0, numEleminXDirection+1):
            node2DMatrix = [] 
            for j in range(0, numEleminYDirection+1):
                node1DMatrix = []
                for k in range(0, numEleminZDirection+1):
                    x = ptList[0].X() + i*meshSize
                    y = ptList[0].Y() + j*meshSize
                    z = zPosList[k]
                   

                    node = Node(nid)
                    node.SetXYZ(x,y,z)
                    node1DMatrix.append(node)
                    nid += 1      
                   
                    
                    if k == 0:
                        self.meshManagerList[0].nodeMan.AddNode(node)
                    elif k == numEleminZDirection:
                        self.meshManagerList[-1].nodeMan.AddNode(node)
                    elif k % numElementinThickness == 0:
                        self.meshManagerList[k//numElementinThickness].nodeMan.AddNode(node)
                        self.meshManagerList[k//numElementinThickness-1].nodeMan.AddNode(node)
                    else:
                        self.meshManagerList[k//numElementinThickness].nodeMan.AddNode(node)
                node2DMatrix.append(node1DMatrix)
            node3DMatrix.append(node2DMatrix)
        eid = maxEID + 1
        for k in range(0, numEleminZDirection):
            curMeshManager : KooMeshManager = self.meshManagerList[k//numElementinThickness]
            for j in range(0, numEleminYDirection):
                for i in range(0, numEleminXDirection):
                    node1 = node3DMatrix[i][j][k]
                    node2 = node3DMatrix[i+1][j][k]
                    node3 = node3DMatrix[i+1][j+1][k]
                    node4 = node3DMatrix[i][j+1][k]
                    node5 = node3DMatrix[i][j][k+1]
                    node6 = node3DMatrix[i+1][j][k+1]
                    node7 = node3DMatrix[i+1][j+1][k+1]
                    node8 = node3DMatrix[i][j+1][k+1]
                    
                    
                    curMeshManager.elementMan.AddHexahedronLinearElement(eid, node1, node2, node3, node4, node5, node6, node7, node8)
                    eid += 1
        
        return maxNID, maxEID, maxPID       

        
class KooMeshManager:
    def __init__(self, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        self.type = "Solid"
        if nodeMan is None:
            self.nodeMan : NodeManager = NodeManager()
        else:
            self.nodeMan : NodeManager = nodeMan
        if elementMan is None:
            self.elementMan : ElementManager = ElementManager(self.nodeMan)
        else:
            self.elementMan : ElementManager = elementMan
        
        self.mat : KooMaterial = None
        self.section : KooSection = None
        if partMan is None:
            self.partMan : KooPartManager = KooPartManager()
        else:
            if part is None:
                partMan.CreatePartfromKooPart(self.part)
        if sectionMan is None:
            self.sectionMan : KooSectionManager = KooSectionManager()
        else:
            self.sectionMan : KooSectionManager = sectionMan

        if materialMan is None:
            self.materialMan : KooMaterialManager = KooMaterialManager()
        else:
            self.materialMan : KooMaterialManager = materialMan
            
        if nodeSetMan is None:
            self.nodeSetMan : NodeSetManager = NodeSetManager()
        else:
            self.nodeSetMan : NodeSetManager = nodeSetMan
        if part is None:
            self.part = KooPart(self.nodeMan, self.elementMan,nodeSetManager = self.nodeSetMan)
        else:
            self.part = part
        self.mshImporter : KooMSHImporter = KooMSHImporter(self.nodeMan,self.elementMan)
    
    def GenerateStructuredMeshbyNumberofElement(self, ptList, numElementinXDir, numElementinYDir, numElementinZDir, maxNID = 0, maxEID = 0):
        if len(ptList) < 8:
            print("ptList must have 8 points")
            return
        ptXMinYMinZMin = ptList[0]
        ptXMaxYMinZMin = ptList[1]
        ptXMaxYMaxZMin = ptList[2]
        ptXMinYMaxZMin = ptList[3]
        ptXMinYMinZMax = ptList[4]
        ptXMaxYMinZMax = ptList[5]
        ptXMaxYMaxZMax = ptList[6]
        ptXMinYMaxZMax = ptList[7]
        numEleminXDirection = numElementinXDir
        numEleminYDirection = numElementinYDir
        numEleminZDirection = numElementinZDir
        nid = maxNID+1
        # 3D array of nodes
        node3DMatrix = []
        meshXRatioStep = 1.0/(float(numEleminXDirection))
        meshYRatioStep = 1.0/(float(numEleminYDirection))   
        meshZRatioStep = 1.0/(float(numEleminZDirection))
        
        for i in range(0, numEleminXDirection+1):
            node2DMatrix = []
            for j in range(0, numEleminYDirection+1):
                node1DMatrix = []
                for k in range(0, numEleminZDirection+1):
                    
                    ptYMinZMin = gp_Pnt(ptXMinYMinZMin.X() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMin.X() * meshXRatioStep*i,
                                        ptXMinYMinZMin.Y() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMin.Y() * meshXRatioStep*i,
                                        ptXMinYMinZMin.Z() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMin.Z() * meshXRatioStep*i)
                    
                    ptYMaxZMin = gp_Pnt(ptXMinYMaxZMin.X() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMin.X() * meshXRatioStep*i,
                                        ptXMinYMaxZMin.Y() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMin.Y() * meshXRatioStep*i,
                                        ptXMinYMaxZMin.Z() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMin.Z() * meshXRatioStep*i)
                    
                    ptZMin = gp_Pnt(ptYMinZMin.X() * (1.0 - meshYRatioStep*j) + ptYMaxZMin.X() * meshYRatioStep*j,
                                    ptYMinZMin.Y() * (1.0 - meshYRatioStep*j) + ptYMaxZMin.Y() * meshYRatioStep*j,
                                    ptYMinZMin.Z() * (1.0 - meshYRatioStep*j) + ptYMaxZMin.Z() * meshYRatioStep*j)
                    
                    ptYMinZMax = gp_Pnt(ptXMinYMinZMax.X() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMax.X() * meshXRatioStep*i,
                                        ptXMinYMinZMax.Y() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMax.Y() * meshXRatioStep*i,
                                        ptXMinYMinZMax.Z() * (1.0 - meshXRatioStep*i) + ptXMaxYMinZMax.Z() * meshXRatioStep*i)
                    
                    ptYMaxZMax = gp_Pnt(ptXMinYMaxZMax.X() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMax.X() * meshXRatioStep*i,
                                        ptXMinYMaxZMax.Y() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMax.Y() * meshXRatioStep*i,
                                        ptXMinYMaxZMax.Z() * (1.0 - meshXRatioStep*i) + ptXMaxYMaxZMax.Z() * meshXRatioStep*i)
                    
                    ptZMax = gp_Pnt(ptYMinZMax.X() * (1.0 - meshYRatioStep*j) + ptYMaxZMax.X() * meshYRatioStep*j,
                                    ptYMinZMax.Y() * (1.0 - meshYRatioStep*j) + ptYMaxZMax.Y() * meshYRatioStep*j,
                                    ptYMinZMax.Z() * (1.0 - meshYRatioStep*j) + ptYMaxZMax.Z() * meshYRatioStep*j)
                    pt = gp_Pnt(ptZMin.X() * (1.0 - meshZRatioStep*k) + ptZMax.X() * meshZRatioStep*k,
                                ptZMin.Y() * (1.0 - meshZRatioStep*k) + ptZMax.Y() * meshZRatioStep*k,
                                ptZMin.Z() * (1.0 - meshZRatioStep*k) + ptZMax.Z() * meshZRatioStep*k)
                    
                    x = pt.X()
                    y = pt.Y()
                    z = pt.Z()                    
                    
                    node = Node(nid)
                    node.SetXYZ(x,y,z)
                    node1DMatrix.append(node)
                    self.nodeMan.AddNode(node)  
                    nid += 1        
                node2DMatrix.append(node1DMatrix)
            node3DMatrix.append(node2DMatrix)
        
        eid = maxEID + 1
        for k in range(0, numEleminZDirection):
            for j in range(0, numEleminYDirection):
                for i in range(0, numEleminXDirection):
                    node1 = node3DMatrix[i][j][k]
                    node2 = node3DMatrix[i+1][j][k]
                    node3 = node3DMatrix[i+1][j+1][k]
                    node4 = node3DMatrix[i][j+1][k]
                    node5 = node3DMatrix[i][j][k+1]
                    node6 = node3DMatrix[i+1][j][k+1]
                    node7 = node3DMatrix[i+1][j+1][k+1]
                    node8 = node3DMatrix[i][j+1][k+1]
                    nodes = [node1, node2, node3, node4, node5, node6, node7, node8]
                    
                    element = SolidElement(eid, nodes)
                    element.SetType("HEXA8")
                    self.elementMan.AddElement(element)
                    eid += 1
        self.type = "Solid"
        self.section = self.sectionMan.CreateSolidSection("SolidSection")
        self.part.SetSectionID(self.sectionMan.maxid)
        pass
    
    def GenerateStructuredMesh(self, ptList, meshSize, numElementinThickness, maxNID = 0, maxEID = 0):
        if len(ptList) < 8:
            print("ptList must have 8 points")
            return
        ptXMinYMinZMin = ptList[0]
        ptXMaxYMinZMin = ptList[1]
        ptXMaxYMaxYMin = ptList[2]
        ptXMinYMaxYMin = ptList[3]
        ptXMinYMinZMax = ptList[4]
        ptXMaxYMinZMax = ptList[5]
        ptXMaxYMaxYMax = ptList[6]
        ptXMinYMaxYMax = ptList[7]
        numEleminXDirection = int((ptXMaxYMinZMin.X() - ptXMinYMinZMin.X())/meshSize)
        if numEleminXDirection < 1:
            numEleminXDirection = 1
        numEleminYDirection = int((ptXMinYMaxYMin.Y() - ptXMinYMinZMin.Y())/meshSize)
        if numEleminYDirection < 1:
            numEleminYDirection = 1
        numEleminZDirection = numElementinThickness
        
        nid = maxNID+1
        # 3D array of nodes
        node3DMatrix = []
        meshSizeZ = (ptXMinYMinZMax.Z() - ptXMinYMinZMin.Z())/numEleminZDirection
        
        for i in range(0, numEleminXDirection+1):
            node2DMatrix = []
            for j in range(0, numEleminYDirection+1):
                node1DMatrix = []
                for k in range(0, numEleminZDirection+1):
                    x = ptXMinYMinZMin.X() + i*meshSize
                    y = ptXMinYMinZMin.Y() + j*meshSize
                    z = ptXMinYMinZMin.Z() + k*meshSizeZ
                    node = Node(nid)
                    node.SetXYZ(x,y,z)
                    node1DMatrix.append(node)
                    self.nodeMan.AddNode(node)  
                    nid += 1        
                node2DMatrix.append(node1DMatrix)
            node3DMatrix.append(node2DMatrix)
        
        eid = maxEID + 1
        for k in range(0, numEleminZDirection):
            for j in range(0, numEleminYDirection):
                for i in range(0, numEleminXDirection):
                    node1 = node3DMatrix[i][j][k]
                    node2 = node3DMatrix[i+1][j][k]
                    node3 = node3DMatrix[i+1][j+1][k]
                    node4 = node3DMatrix[i][j+1][k]
                    node5 = node3DMatrix[i][j][k+1]
                    node6 = node3DMatrix[i+1][j][k+1]
                    node7 = node3DMatrix[i+1][j+1][k+1]
                    node8 = node3DMatrix[i][j+1][k+1]
                    nodes = [node1, node2, node3, node4, node5, node6, node7, node8]
                    
                    element = SolidElement(eid, nodes)
                    element.SetType("HEXA8")
                    self.elementMan.AddElement(element)
                    eid += 1
        self.type = "Solid"
        self.section = self.sectionMan.CreateSolidSection("SolidSection")
        self.part.SetSectionID(self.sectionMan.maxid)
        pass
        
    
class KooMeshManagerGMSH(KooMeshManager):

    def __init__(self, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan  = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):

        super(KooMeshManagerGMSH, self).__init__(nodeMan, elementMan, partMan, sectionMan, materialMan, nodeSetMan, part)

        self.inputFileName = "temp.brep"
        self.outputFileName = "temp.stl"
        self.geoFileName = "temp.geo"
        self.gmshOutputFileName = "temp.msh"
        self.path = ".\\"
        if sys.platform.startswith("win"):
            self.gmshPath = ".\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"
        else:
            self.gmshPath = self._find_linux_gmsh()
        self.meshAlgoOption = "auto"
        #Select mesh algorithm: auto, meshadapt, del2d, front2d, delquad, quadqs, initial2d, del3d, front3d, mmg3d, hxt, initial3d

        self.hide = False
        self.shape = None
        self.aisShape = None

        pass

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
        # which gmsh fallback
        import shutil
        found = shutil.which("gmsh")
        if found:
            return found
        print("gmsh not found")
        sys.exit()

    def SetPath(self, path):
        self.path = os.path.normpath(path)
        # 디렉토리가 없으면 생성 (gmsh 경로 탐색에 필요)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if sys.platform.startswith("win"):
            # find gmsh.exe in the path
            winCandidates = [
                join(path, ".\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                join(path, "..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                join(path, "..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                join(path, "..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
                join(path, "..\\..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe"),
            ]
            for c in winCandidates:
                if os.path.exists(c):
                    self.gmshPath = c
                    return
            print("gmsh.exe not found")
            sys.exit()
        else:
            self.gmshPath = self._find_linux_gmsh(self.path)
    
    def ImportMSHFile(self, fileName, maxNID = 0, maxEID = 0,delX=0.0,delY=0.0,delZ=0.0,scaleX=1.0,scaleY=1.0,scaleZ=1.0):
        mshFilePath = join(self.path, fileName)
        self.mshImporter.import_msh_file(mshFilePath)
        self.mshImporter.UpdateManager(maxNID, maxEID, 3)
        self.RelocationNodes(delX, delY, delZ, scaleX, scaleY, scaleZ)
        nodeMan : NodeManager = NodeManager()
        elementMan : ElementManager = ElementManager(nodeMan)
        msh2DImporter = KooMSHImporter(nodeMan, elementMan)
        msh2DImporter.import_msh_file(mshFilePath)
        msh2DImporter.UpdateManager(maxNID, maxEID, 2)
        nodeMan.RelocationNodes(delX, delY, delZ, scaleX, scaleY, scaleZ)
        nodes = nodeMan.nodes
        elems = elementMan.elements
        
        nodesList = []
        for i in nodes:
            node = nodes[i]
            nodesList.append([node.x, node.y, node.z])
        nodesList = np.array(nodesList)
        # add nodes
        keytoID = {}
        i = 0
        for id in nodes:
            keytoID[id] = i
            i += 1
        elemsList = []
        for id in elems:
            element = elems[id]
            if element.type == "TRI3":
                elemsList.append([keytoID[element.nodes[0].id], keytoID[element.nodes[1].id], keytoID[element.nodes[2].id]])
            elif element.type == "QUAD4":
                elemsList.append([keytoID[element.nodes[0].id], keytoID[element.nodes[1].id], keytoID[element.nodes[2].id]])
                elemsList.append([keytoID[element.nodes[2].id], keytoID[element.nodes[3].id], keytoID[element.nodes[0].id]])
        from stl import mesh
        faces = np.array(elemsList)
        stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        
        for i, face in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = nodesList[face[j], :]
        stlPath = mshFilePath.replace(".msh",".stl")            
        stl_mesh.save(stlPath)
        self.shape = read_stl_file(stlPath)            
        return self.shape
        
        
    def RelocationNodes(self, delX, delY, delZ, scaleX, scaleY, scaleZ):
        self.nodeMan.RelocationNodes(delX, delY, delZ, scaleX, scaleY, scaleZ)
        
    
    def SetPartasComposite(self,midiList, thickiList, biList):
        name = self.part.name 
        secid = self.part.secid
        self.part = KooPartComposite(self.nodeMan, self.elementMan, self.nodeSetMan)
        self.part.SetName(name)
        self.part.SetSectionID(secid)
        self.part.SetLaminates(midiList, thickiList, biList)

    def SetName(self, name):
        self.part.SetName(name)
        self.inputFileName = name + ".brep"
        self.outputFileName = name + ".stl"
        self.geoFileName = name + ".geo"
        self.gmshOutputFileName = name + ".msh"

    def SetNamewithID(self, name, ID):
        self.inputFileName = name + str(ID) + ".brep"
        self.outputFileName = name + str(ID) + ".stl"
        self.geoFileName = name + str(ID) + ".geo"
        self.gmshOutputFileName = name + str(ID) + ".msh"

    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if self.shape is not None:                
                if trsf == None:
                    self.aisShape = viewer._display.DisplayShape(self.shape, update=update)
                else:
                    shape = BRepBuilderAPI_Transform(self.shape, trsf).Shape()
                    self.aisShape = viewer._display.DisplayShape(shape, update=update)

    def Erase(self, viewer, update = False):
        #erase self.shape from viewer
        if self.aisShape is not None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape, update)

    def mesh_shape_tri_2D(self, shape, meshSize,maxNID = 0, maxEID = 0, thickness = 0.0, stype = ""):
        meshSizeMin = meshSize*0.8
        meshSizeMax = meshSize*1.2
        inputFilePath = self.path
        inputFilePath = join(inputFilePath,self.inputFileName)
        breptools_Write(shape, inputFilePath)
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        Mesh.RecombineAll = 1;
        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        """
        geomFilePath = join(self.path,self.geoFileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)        
        command = self.gmshPath + " -setnumber General.Verbosity 0 \"" + geomFilePath + "\" -2 " + " -o \"" + gmshOutputFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)
        outputFilePath = join(self.path, self.outputFileName)
      
        if os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            outputFilePath = join(self.path, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            
            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 2)
            self.type = "Shell"
            if len(stype) != 0:
                self.type = stype

            if thickness != 0.0:
                name = os.path.basename(self.inputFileName)
                name = name.replace(".brep","")
                self.section = self.sectionMan.CreateShellSection(name, thickness)                                
                self.part.SetSectionID(self.sectionMan.maxid)

            return self.shape
        
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()
    def mesh_shape_quad_2D(self, shape, meshSize, maxNID = 0, maxEID = 0, thickness = 0.0, stype = "", algorithmoption = 8):
        meshSizeMin = meshSize*0.8
        meshSizeMax = meshSize*1.2
        inputFilePath = self.path
        inputFilePath = join(inputFilePath,self.inputFileName)
        breptools_Write(shape, inputFilePath)
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        """
        gmsh_geo_file_content += "Mesh.Algorithm = {algorithm};\n".format(algorithm = algorithmoption)
        gmsh_geo_file_content += """Mesh.RecombineAll = 1;

        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        """
        geomFilePath = join(self.path,self.geoFileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)        
        command = self.gmshPath + " -setnumber General.Verbosity 0 \"" + geomFilePath + "\" -2 " + " -o \"" + gmshOutputFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)
        outputFilePath = join(self.path, self.outputFileName)
      
        if os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            outputFilePath = join(self.path, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            
            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 2)
            self.type = "Shell"
            if len(stype) != 0:
                self.type = stype
            if thickness != 0.0:
                name = os.path.basename(self.inputFileName)
                name = name.replace(".brep","")
                self.section = self.sectionMan.CreateShellSection(name, thickness)                                
                self.part.SetSectionID(self.sectionMan.maxid)

            return self.shape
        
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()

    def mesh_shape_extrude_2D(self, shape, meshSizeInPlane, numberofElementinThickness, direction = [0,0,1], maxNID = 0, maxEID = 0, stype = ""):
        meshSizeMin = meshSizeInPlane*0.5
        meshSizeMax = meshSizeInPlane*1.5
        inputFilePath = self.path
        inputFilePath = join(inputFilePath,self.inputFileName)
        breptools_Write(shape, inputFilePath)
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        
        Extrude {""" + str(direction[0]) + "," + str(direction[1]) + "," + str(direction[2]) + """} {
            line{a}; Layers{""" + str(numberofElementinThickness) + """};
        }"""
        # 
        # 
        geomFilePath = join(self.path,self.geoFileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)        
        command = self.gmshPath + " -setnumber General.Verbosity 0 \"" + geomFilePath + "\" -2 " + " -o \"" + gmshOutputFilePath + "\" -format msh"
        #command = self.gmshPath + " " + geomFilePath + " -3 " + " -o " + gmshOutputFilePath + " -format msh"
        print(command)
        gmsh_success = os.system(command)
        outputFilePath = join(self.path, self.outputFileName)
      
        if os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            outputFilePath = join(self.path, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            #self.shape = read_stl_file(outputFilePath)            
            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 2)
            self.type = "Solid"
            if len(stype) != 0:
                self.type = stype
            name = os.path.basename(self.inputFileName)
            name = name.replace(".brep","")
            self.section = self.sectionMan.CreateSolidSection(name)
            self.part.SetSectionID(self.sectionMan.maxid)
            return self.shape
        
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()

    def mesh_shape_extrude_3D(self, shape, meshSizeInPlane,numberofElementinThickness, direction = [0,0,1], meshAlgo = 11, maxNID = 0, maxEID = 0, stype = ""):        
        meshSizeMin = meshSizeInPlane*0.5
        meshSizeMax = meshSizeInPlane*1.5
        inputFilePath = self.path
        inputFilePath = join(inputFilePath,self.inputFileName)
        breptools_Write(shape, inputFilePath)
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        Mesh.Algorithm = """ + str(meshAlgo) + """;
       
        Mesh.Algorithm = 2; // Delaunay
        Mesh.RecombineAll = 1;

        Extrude {""" + str(direction[0]) + "," + str(direction[1]) + "," + str(direction[2]) + """} {
            Surface{a}; Layers{""" + str(numberofElementinThickness) + """}; Recombine;
        }"""
        # 
        # 
        geomFilePath = join(self.path,self.geoFileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)        
        command = self.gmshPath + " -setnumber General.Verbosity 0 \"" + geomFilePath + "\" -3 " + " -o \"" + gmshOutputFilePath + "\" -format msh"
        #command = self.gmshPath + " " + geomFilePath + " -3 " + " -o " + gmshOutputFilePath + " -format msh"
        print(command)
        gmsh_success = os.system(command)
        outputFilePath = join(self.path, self.outputFileName)
      
        if os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            outputFilePath = join(self.path, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            
            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 3)
            self.type = "Solid"
            if len(stype) != 0:
                self.type = stype
            name = os.path.basename(self.inputFileName)
            name = name.replace(".brep","")
            self.section = self.sectionMan.CreateSolidSection(name) 
            self.part.SetSectionID(self.sectionMan.maxid)
            return self.shape
        
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()

    def mesh_shape_from_stl_without_surface_nodes(self, stl_file_path, boundaryNodes, part, meshSizeMin, meshSizeMax):
        inputFilePath = self.path
        curdir = inputFilePath
        inputFilePath = join(inputFilePath,self.inputFileName)
        
        gmsh_geo_file_content = """
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        // Import the STL file
        Merge "{stl_file_path}";
        // Create a volume from the surface mesh
        Surface Loop(1) = {{1}};
        Volume(1) = {{1}};

        // Generate the 3D mesh
        Mesh 3;
        """
        gmsh_geo_file_content = gmsh_geo_file_content.format(stl_file_path = stl_file_path)
        geomFilePath = join(self.path,self.geoFileName)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)       
        
        curGeomFilePath = geomFilePath        
        curGmshOutputFilePath = gmshOutputFilePath
        command = self.gmshPath + "  -setnumber General.Verbosity 0  \"" + curGeomFilePath + "\" "  + "-3 -o \"" + curGmshOutputFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)        
        outputFilePath = join(self.path, self.outputFileName) 
        print(gmsh_success)
        if gmsh_success == 0 and os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)    
            
            outputFilePath = join(curdir,self.path)
            outputFilePath = join(outputFilePath, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            

            self.mshImporter.import_msh_file(gmshOutputFilePath)  
            # 3 means dimension          
            self.mshImporter.UpdateManagerwithoutBoundary(0, 0, 3, boundaryNodes)
            name = os.path.basename(stl_file_path)
          
            return self.shape
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit() 

    def mesh_shape_from_stl(self, stl_file_path, meshSizeMin, meshSizeMax, meshAlgo = None, maxNID = 0, maxEID = 0, stype = ""):
        inputFilePath = self.path
        curdir = inputFilePath
        inputFilePath = join(inputFilePath,self.inputFileName)
        
        gmsh_geo_file_content = """
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;
        // Import the STL file
        Merge "{stl_file_path}";
        // Create a volume from the surface mesh
        Surface Loop(1) = {{1}};
        Volume(1) = {{1}};

        // Generate the 3D mesh
        Mesh 3;
        """
        gmsh_geo_file_content = gmsh_geo_file_content.format(stl_file_path = stl_file_path)
        geomFilePath = join(self.path,self.geoFileName)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)
        if meshAlgo is not None:
            self.meshAlgoOption = meshAlgo
            self.type = "Solid"        
        
        curGeomFilePath = geomFilePath        
        curGmshOutputFilePath = gmshOutputFilePath
        command = self.gmshPath + "  -setnumber General.Verbosity 0  \"" + curGeomFilePath + "\" "  + "-3 -o \"" + curGmshOutputFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)        
        outputFilePath = join(self.path, self.outputFileName) 
        print(gmsh_success)
        if gmsh_success == 0 and os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)    
            
            outputFilePath = join(curdir,self.path)
            outputFilePath = join(outputFilePath, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            

            self.mshImporter.import_msh_file(gmshOutputFilePath)  
            # 3 means dimension          
            self.mshImporter.UpdateManager(maxNID, maxEID, 3)
            name = os.path.basename(stl_file_path)
          
            self.type = "Solid"                
            self.section = self.sectionMan.CreateSolidSection(name) 
            self.part.SetSectionID(self.sectionMan.maxid)
            if len(stype) != 0:
                self.type = stype

            return self.shape
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit() 

    def mesh_shape(self, shape, meshSizeMin, meshSizeMax,dimension,meshAlgo = None, maxNID = 0, maxEID = 0, thickness = 0.0, stype = ""):
        #curdir = os.getcwd()
        #inputFilePath = join(curdir,self.path)
        inputFilePath = self.path
        curdir = inputFilePath
        # if there are no folder of curdir, then make the folder
        if not os.path.exists(curdir):
            os.makedirs(curdir)
        inputFilePath = join(inputFilePath,self.inputFileName)
        
        breptools_Write(shape, inputFilePath)
        
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = """ + str(meshSizeMin) + """;
        Mesh.CharacteristicLengthMax = """ + str(meshSizeMax) + """;

        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        """
        geomFilePath = join(self.path,self.geoFileName)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        #gmsh_success = os.system(self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.outputFileName + " -format stl")
        #command = self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.gmshOutputFileName + " -format msh"
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)
        if dimension == 2:
            self.meshAlgoOption = "quadqs"
            self.type = "Shell"
        if meshAlgo is not None:
            self.meshAlgoOption = meshAlgo
            self.type = "Solid"        
        
        curGeomFilePath = geomFilePath        
        #curGeomFilePath = curGeomFilePath.replace("\\","\\\\")
        curGmshOutputFilePath = gmshOutputFilePath
        #curGmshOutputFilePath = curGmshOutputFilePath.replace("\\","\\\\")

        command = self.gmshPath + "  -setnumber General.Verbosity 0  \"" + curGeomFilePath + "\" -" + str(dimension)+ " -algo " + self.meshAlgoOption + " -o \"" + curGmshOutputFilePath + "\" -format msh"
        #command = self.gmshPath + " " + geomFilePath + " -" + str(dimension)+ " -algo " + self.meshAlgoOption + " -o " + gmshOutputFilePath + " -format msh"
        print(command)
        gmsh_success = os.system(command)        

        outputFilePath = join(self.path, self.outputFileName)
        
        #gmsh_success = os.system(self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.gmshOutputFileName + " -format msh " + " -o " + self.outputFileName + " -format stl")        
        print(gmsh_success)
        if gmsh_success == 0 and os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            
            
            outputFilePath = join(curdir,self.path)
            outputFilePath = join(outputFilePath, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            

            self.mshImporter.import_msh_file(gmshOutputFilePath)            
            self.mshImporter.UpdateManager(maxNID, maxEID, dimension)
            name = os.path.basename(self.inputFileName)
            name = name.replace(".brep","")
            if dimension == 2:
                self.type = "Shell"
                if thickness != 0.0:
                    self.section = self.sectionMan.CreateShellSection(name, thickness)
                    self.part.SetSectionID(self.sectionMan.maxid)
            else:
                self.type = "Solid"                
                self.section = self.sectionMan.CreateSolidSection(name) 
                self.part.SetSectionID(self.sectionMan.maxid)
            if len(stype) != 0:
                self.type = stype

            #from OCC.Core.TopAbs import TopAbs_FACE
            #from OCC.Core.TopExp import TopExp_Explorer

            #face_explorer = TopExp_Explorer(self.shape,TopAbs_FACE)
            #faces = []
            #while face_explorer.More():
                #face = face_explorer.Current()
                #faces.append(face)
                #face_explorer.Next()

            return self.shape
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()
    
    def mesh_shape_refine(self, shape, meshSize, meshSizeRefine, centerRefine,characteristicLength, dimension,meshAlgo = None, maxNID = 0, maxEID = 0, thickness = 0.0, stype = ""):
        #curdir = os.getcwd()
        #inputFilePath = join(curdir,self.path)
        xCenter = centerRefine[0]
        yCenter = centerRefine[1]
        zCenter = centerRefine[2]

        inputFilePath = self.path
        curdir = inputFilePath
        inputFilePath = join(inputFilePath,self.inputFileName)
        breptools_Write(shape, inputFilePath)
        
        gmsh_geo_file_content = """SetFactory("OpenCASCADE");"""
        gmsh_geo_file_content += "Field[1] = MathEval;\n"
        meshRatio = meshSize/meshSizeRefine
        gmsh_geo_file_content += "Field[1].F = \"{meshSizeRefine}*(1.0+{meshRatio}/{chLength}*sqrt((x-{x0})^2+(y-{y0})^2+(z-{z0})^2))\";\n".format(meshSizeRefine = meshSizeRefine, meshRatio = meshRatio, chLength = characteristicLength, x0 = xCenter, y0 = yCenter, z0 = zCenter)
        #gmsh_geo_file_content += "Field[1].F = \"((sqrt((x-{x0})^2+(y-{y0})^2+(z-{z0})))<{meshSizeRefine}*10)*{meshSizeRefine} + ((sqrt((x-{x0})^2+(y-{y0})^2+(z-{z0})))>=meshSizeRefine*10)*{meshSizeRefine}*(1.0+{meshRatio}/{chLength}*sqrt((x-{x0})^2+(y-{y0})^2+(z-{z0})^2))\";\n".format(meshSizeRefine = meshSizeRefine, meshRatio = meshRatio, chLength = characteristicLength, x0 = xCenter, y0 = yCenter, z0 = zCenter)
        gmsh_geo_file_content += "Background Field = 1;\n"
        gmsh_geo_file_content += """
        a() = ShapeFromFile(\"""" + inputFilePath + """\");
        """
        geomFilePath = join(self.path,self.geoFileName)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geo_file_content)
        gmsh_geo_file.close()
        #gmsh_success = os.system(self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.outputFileName + " -format stl")
        #command = self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.gmshOutputFileName + " -format msh"
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)
        if dimension == 2:
            self.meshAlgoOption = "quadqs"
            self.type = "Shell"
        if meshAlgo is not None:
            self.meshAlgoOption = meshAlgo
            self.type = "Solid"        
        
        curGeomFilePath = geomFilePath        
        #curGeomFilePath = curGeomFilePath.replace("\\","\\\\")
        curGmshOutputFilePath = gmshOutputFilePath
        #curGmshOutputFilePath = curGmshOutputFilePath.replace("\\","\\\\")

        command = self.gmshPath + "  -setnumber General.Verbosity 0  \"" + curGeomFilePath + "\" -" + str(dimension)+ " -algo " + self.meshAlgoOption + " -o \"" + curGmshOutputFilePath + "\" -format msh"
        #command = self.gmshPath + " " + geomFilePath + " -" + str(dimension)+ " -algo " + self.meshAlgoOption + " -o " + gmshOutputFilePath + " -format msh"
        print(command)
        gmsh_success = os.system(command)        

        outputFilePath = join(self.path, self.outputFileName)
        
        #gmsh_success = os.system(self.gmshPath + " " + self.geoFileName + " -" + str(dimension) + " -o " + self.gmshOutputFileName + " -format msh " + " -o " + self.outputFileName + " -format stl")        
        print(gmsh_success)
        if gmsh_success == 0 and os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            
            
            outputFilePath = join(curdir,self.path)
            outputFilePath = join(outputFilePath, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)            

            self.mshImporter.import_msh_file(gmshOutputFilePath)            
            self.mshImporter.UpdateManager(maxNID, maxEID, dimension)
            name = os.path.basename(self.inputFileName)
            name = name.replace(".brep","")
            if dimension == 2:
                self.type = "Shell"
                if thickness != 0.0:
                    self.section = self.sectionMan.CreateShellSection(name, thickness)
                    self.part.SetSectionID(self.sectionMan.maxid)
            else:
                self.type = "Solid"                
                self.section = self.sectionMan.CreateSolidSection(name) 
                self.part.SetSectionID(self.sectionMan.maxid)
            if len(stype) != 0:
                self.type = stype

            #from OCC.Core.TopAbs import TopAbs_FACE
            #from OCC.Core.TopExp import TopExp_Explorer

            #face_explorer = TopExp_Explorer(self.shape,TopAbs_FACE)
            #faces = []
            #while face_explorer.More():
                #face = face_explorer.Current()
                #faces.append(face)
                #face_explorer.Next()

            return self.shape
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()


    def mesh_shape_extrude_3D_polygon_refine(self, ptList,elemthickness,numelemThickness, meshSizeBig, meshSizeSmall, refineLocationX, refineLocationY, maxNID = 0, maxEID = 0, mode = "FEM"):
        
        gmsh_geoFileContent = ""
        xMin = ptList[0].X()
        xMax = ptList[0].X()
        yMin = ptList[0].Y()
        yMax = ptList[0].Y()

        for i in range(len(ptList)):
            if ptList[i].X() < xMin:
                xMin = ptList[i].X()
            if ptList[i].X() > xMax:
                xMax = ptList[i].X()
            if ptList[i].Y() < yMin:
                yMin = ptList[i].Y()
            if ptList[i].Y() > yMax:
                yMax = ptList[i].Y()
            gmsh_geoFileContent += "Point(" + str(i+1) + ") = {" + str(ptList[i].X()) + "," + str(ptList[i].Y()) + "," + str(ptList[i].Z()) + "};\n"
        diagonalLength = math.sqrt((xMax-xMin)**2 + (yMax-yMin)**2)
        for i in range(len(ptList)):
            if i == len(ptList)-1:
                gmsh_geoFileContent += "Line(" + str(i+1) + ") = {" + str(i+1) + "," + str(1) + "};\n"
            else:
                gmsh_geoFileContent += "Line(" + str(i+1) + ") = {" + str(i+1) + "," + str(i+2) + "};\n"
        loopNum = len(ptList) + 1
        gmsh_geoFileContent += "Curve Loop({loopNum}) =".format(loopNum = loopNum) + "{"
        for i in range(len(ptList)):
            if i == len(ptList)-1:
                gmsh_geoFileContent += str(i+1)
            else:
                gmsh_geoFileContent += str(i+1) + ","
        gmsh_geoFileContent += "};\n"

        surfaceNum = loopNum + 1
        gmsh_geoFileContent += "Plane Surface({surfaceNum}) = ".format(surfaceNum = surfaceNum)
        gmsh_geoFileContent += "{"
        gmsh_geoFileContent += str(loopNum)
        gmsh_geoFileContent += "};\n"
        
        #gmsh_geoFileContent += "// Define the step function\n"
        #gmsh_geoFileContent += "Function step = DefineFunction \"Return { Return [ x >= 0 ? 1 : 0 ]; };\";\n"
        
        gmsh_geoFileContent += "Field[1] = MathEval;\n"
        gmsh_geoFileContent += "Field[1].F = "
        meshRatio = meshSizeBig/meshSizeSmall
        
        

        gmsh_geoFileContent += " \"{meshSizeSmall}*(1.0+{meshRatio}/{diagonalLength}/{diagonalLength}*sqrt(((x-{x0})^2+(y-{y0})^2)))\";\n".format(meshSizeSmall = meshSizeSmall, meshRatio = meshRatio, x0 = refineLocationX, y0 = refineLocationY, diagonalLength = diagonalLength)
        #gmsh_geoFileContent += " \"{meshSizeSmall}*(1.0*(1-((sqrt(((x-{x0})^2+(y-{y0})^2)-5.0*{meshSizeSmall}) < 0 ? 1 : 0))+((sqrt(((x-{x0})^2+(y-{y0})^2)-5.0*{meshSizeSmall}) < 0 ? 1 : 0)*{meshRatio}/{diagonalLength}/{diagonalLength}*sqrt(((x-{x0})^2+(y-{y0})^2)))\";\n".format(meshSizeSmall = meshSizeSmall, meshRatio = meshRatio, x0 = refineLocationX, y0 = refineLocationY, diagonalLength = diagonalLength)
        #gmsh_geoFileContent += " \"{meshSizeSmall}*(If(sqrt((x-{x0})^2+(y-{y0})^2))<{meshSizeSmall}*10.0,1,1.0/{diagonalLength}/{diagonalLength}))\";\n".format(meshSizeSmall = meshSizeSmall, meshRatio = meshRatio, x0 = refineLocationX, y0 = refineLocationY, diagonalLength = diagonalLength)
        #gmsh_geoFileContent += " \"{meshSizeSmall}*(1.0+{meshRatio}/{diagonalLength}/{diagonalLength}*log((((x-{x0})^2+(y-{y0}^2)))\";\n".format(meshSizeSmall = meshSizeSmall, meshRatio = meshRatio, x0 = refineLocationX, y0 = refineLocationY, diagonalLength = diagonalLength)
        
        #gmsh_geoFileContent += " \"{meshSizeSmall}*(sqrt(((x-{x0})^2+(y-{y0})^2))<={meshSizeSmall}*5.0) +(sqrt(((x-{x0})^2+(y-{y0})^2))>{meshSizeSmall}*5.0)*{meshSizeSmall}*(1.0+{meshRatio}/{diagonalLength}/{diagonalLength}*sqrt(((x-{x0})^2+(y-{y0})^2)))\";\n".format(meshSizeSmall = meshSizeSmall, meshRatio = meshRatio, x0 = refineLocationX, y0 = refineLocationY, diagonalLength = diagonalLength)
        
        
        gmsh_geoFileContent += "Background Field = 1;\n"
        
        gmsh_geoFileContent += "Recombine Surface {"
        gmsh_geoFileContent += str(surfaceNum)
        gmsh_geoFileContent += "};\n"
        gmsh_geoFileContent += "Extrude {0,0," + str(elemthickness) + "} {\n"
        gmsh_geoFileContent += "Surface{" + str(surfaceNum) + "};\n"
        gmsh_geoFileContent += "Layers{" + str(numelemThickness) + "};\n"
        gmsh_geoFileContent += "Recombine;\n"
        gmsh_geoFileContent += "}\n"
        


        geomFilePath = join(self.path,self.geoFileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        gmsh_geo_file = open(geomFilePath, "w")
        gmsh_geo_file.write(gmsh_geoFileContent)
        gmsh_geo_file.close()
        gmshOutputFilePath = join(self.path, self.gmshOutputFileName)
        command = self.gmshPath + " -setnumber General.Verbosity 0 \"" + geomFilePath + "\" -3 " + " -o \"" + gmshOutputFilePath + "\" -format msh"
        print(command)
        gmsh_success = os.system(command)
        outputFilePath = join(self.path, self.outputFileName)
        if os.path.isfile(gmshOutputFilePath):
            command = self.gmshPath + " \"" + gmshOutputFilePath + "\" -format stl -save -o \"" + outputFilePath + "\" " +" -nopopup"
            print(command)
            gmsh_success = os.system(command)
            outputFilePath = join(self.path, self.outputFileName)
            outputFilePath = outputFilePath.replace(".\\","")
            print(outputFilePath)
            self.shape = read_stl_file(outputFilePath)

            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 3)
            
            self.type = "Solid"
            name = os.path.basename(self.inputFileName)
            name = name.replace(".brep","")
            if "FEM" in mode:
                self.section = self.sectionMan.CreateSolidSection(name)
            elif "PERI" in mode or "Peridynamics" in mode:
                self.section = self.sectionMan.CreateSolidSectionPeri(name)
            elif "ALE" in mode or "ArbitraryLagrangianEulerian" in mode:
                self.section = section = self.sectionMan.CreateSolidSection(name,5)
            elif "PAE" in mode or "PoorAspectratioEfficient" in mode:
                self.section = self.sectionMan.CreateSolidSection(name,-1)
            elif "PAA" in mode or "PoorAspectratioAccurate" in mode:
                self.section= self.sectionMan.CreateSolidSection(name,-2)
                
            self.part.SetSectionID(self.sectionMan.maxid)
            return self.shape
        else:
            print("Be sure gmsh is in your PATH")
            sys.exit()



    def mesh_shape_structured(self, ptList, meshSize, elementinThickness, maxNID = 0, maxEID = 0):
        pass

    def mesh_conformal_extrude_hexa(self, bodyParams, cylinderParams, meshSize,
                                     numElemThick, maxNID=0, maxEID=0,
                                     boxParams=None, nOwnCylinders=0):
        """
        2D BooleanFragments + Extrude로 conformal hexa 생성.
        실린더/박스와 본체가 공유 엣지에서 conformal하게 메쉬됨.

        bodyParams: dict {x, y, z, xLen, yLen, thickness}
        cylinderParams: list of (cx, cy, r) — own + adjacent 전체
        nOwnCylinders: int — 자기 층 실린더 개수 (meshSize cap에만 사용)
        boxParams: list of (bx, by, bxLen, byLen) — 내부 사각형 영역
        """
        if boxParams is None:
            boxParams = []

        # 균일 밀도: meshSize 기준, ±20% 범위
        # 자기 층 실린더가 있을 때만 meshSize를 R로 cap → 실린더당 ~4개 요소
        # 인접 층 실린더는 BooleanFragments에만 포함, meshSize에는 영향 없음
        effectiveMeshSize = meshSize
        if nOwnCylinders > 0:
            ownCylParams = cylinderParams[:nOwnCylinders]
            minR = min(r for _, _, r in ownCylParams)
            if effectiveMeshSize > minR:
                effectiveMeshSize = minR
        meshSizeMin = effectiveMeshSize * 0.8
        meshSizeMax = effectiveMeshSize * 1.2

        geo = 'SetFactory("OpenCASCADE");\n'
        geo += 'Mesh.CharacteristicLengthMin = {0};\n'.format(meshSizeMin)
        geo += 'Mesh.CharacteristicLengthMax = {0};\n'.format(meshSizeMax)
        geo += 'Mesh.MeshSizeFromCurvature = 0;\n'
        geo += 'Mesh.MeshSizeExtendFromBoundary = 0;\n\n'

        bx = bodyParams["x"]
        by = bodyParams["y"]
        bz = bodyParams["z"]
        bxLen = bodyParams["xLen"]
        byLen = bodyParams["yLen"]
        bThick = bodyParams["thickness"]

        # 본체 사각형 (Surface ID = 1)
        geo += 'Rectangle(1) = {{{0}, {1}, {2}, {3}, {4}}};\n\n'.format(
            bx, by, bz, bxLen, byLen)

        # 실린더 원들 (Disk ID = 2, 3, ...)
        nCyl = len(cylinderParams)
        surfID = 2
        for i, (cx, cy, r) in enumerate(cylinderParams):
            geo += 'Disk({0}) = {{{1}, {2}, {3}, {4}}};\n'.format(
                surfID + i, cx, cy, bz, r)

        # 내부 박스 사각형들 (Rectangle ID = nCyl+2, ...)
        nBox = len(boxParams)
        boxStartID = surfID + nCyl
        for i, (rbx, rby, rbxLen, rbyLen) in enumerate(boxParams):
            geo += 'Rectangle({0}) = {{{1}, {2}, {3}, {4}, {5}}};\n'.format(
                boxStartID + i, rbx, rby, bz, rbxLen, rbyLen)

        # BooleanFragments (conformal 핵심)
        nFragments = nCyl + nBox
        if nFragments > 0:
            fragIds = ",".join(str(surfID + i) for i in range(nFragments))
            geo += '\nBooleanFragments{{ Surface{{1}}; Delete; }}{{ Surface{{{0}}}; Delete; }}\n'.format(fragIds)

        # Recombine → Quad 메쉬
        geo += '\nMesh.Algorithm = 8;  // Frontal-Delaunay for Quads\n'
        geo += 'Mesh.RecombineAll = 1;\n'
        geo += 'Mesh.SubdivisionAlgorithm = 2;  // All Quads\n'

        # Extrude → Hexa
        geo += '\nExtrude {{0, 0, {0}}} {{\n'.format(bThick)
        geo += '  Surface{:}; Layers{' + str(numElemThick) + '}; Recombine;\n'
        geo += '}\n'

        # GEO 파일 저장 (경로 정규화)
        normPath = os.path.normpath(self.path)
        geomFilePath = os.path.join(normPath, self.geoFileName)
        if not os.path.exists(normPath):
            os.makedirs(normPath)
        with open(geomFilePath, "w") as f:
            f.write(geo)

        # Gmsh 실행
        gmshOutputFilePath = os.path.join(normPath, self.gmshOutputFileName)
        command = '{0} -setnumber General.Verbosity 0 "{1}" -3 -o "{2}" -format msh'.format(
            self.gmshPath, geomFilePath, gmshOutputFilePath)
        print(command)
        gmsh_success = os.system(command)

        if os.path.isfile(gmshOutputFilePath):
            # STL export (시각화용)
            outputFilePath = os.path.join(normPath, self.outputFileName)
            command = '{0} "{1}" -format stl -save -o "{2}" -nopopup'.format(
                self.gmshPath, gmshOutputFilePath, outputFilePath)
            print(command)
            os.system(command)
            outputFilePath = outputFilePath.replace(".\\", "")
            self.shape = read_stl_file(outputFilePath)

            # MSH import
            self.mshImporter.import_msh_file(gmshOutputFilePath)
            self.mshImporter.UpdateManager(maxNID, maxEID, 3)
            self.type = "Solid"
            name = os.path.basename(self.geoFileName).replace(".geo", "")
            self.section = self.sectionMan.CreateSolidSection(name)
            self.part.SetSectionID(self.sectionMan.maxid)
            return self.shape
        else:
            print("Gmsh conformal mesh generation failed. Check gmsh is in PATH.")
            return None

    def mesh_tetra_buffer(self, bottomNodeMan, topNodeMan,
                          zBottom, zTop, bufferBox,
                          maxNID=0, maxEID=0):
        """
        버퍼가 정의된 층(bufferBox) 전체를 tetra로 채움.
        - bufferBox 영역: bottom 층 전체 면적
        - 인접 층(top)이 있는 영역: top 층 노드 사용
        - 인접 층이 없는 외곽: bottom 노드를 zTop으로 투영한 새 노드 생성
        """
        from scipy.spatial import Delaunay
        import numpy as np

        xMin, yMin, xMax, yMax = bufferBox
        tol = 1e-6
        thickness = zTop - zBottom

        # 1. 아래 층 상면 노드 수집 (bufferBox 전체)
        bottomNodeList = []
        bottomXYmap = {}  # (x_round, y_round) -> node
        for nid, node in bottomNodeMan.nodes.items():
            if abs(node.z - zBottom) < tol:
                if xMin - tol <= node.x <= xMax + tol and yMin - tol <= node.y <= yMax + tol:
                    bottomNodeList.append(node)
                    key = (round(node.x, 8), round(node.y, 8))
                    bottomXYmap[key] = node

        # 2. 위 층 하면 노드 수집 (있는 영역만)
        topNodeList = []
        topXY = set()
        for nid, node in topNodeMan.nodes.items():
            if abs(node.z - zTop) < tol:
                if xMin - tol <= node.x <= xMax + tol and yMin - tol <= node.y <= yMax + tol:
                    topNodeList.append(node)
                    topXY.add((round(node.x, 8), round(node.y, 8)))

        # 3. 외곽 영역: top 층이 없는 bottom 노드 → zTop으로 투영
        curNID = maxNID
        projectedTopList = []
        for key, bNode in bottomXYmap.items():
            if key not in topXY:
                curNID += 1
                newNode = self.nodeMan.AddNodewithID(curNID, bNode.x, bNode.y, zTop)
                projectedTopList.append(newNode)

        nBottom = len(bottomNodeList)
        nTop = len(topNodeList)
        nProj = len(projectedTopList)
        allTopList = topNodeList + projectedTopList

        print("Buffer: {0} bottom(z={1}), {2} top(z={3}), {4} projected top".format(
            nBottom, zBottom, nTop, zTop, nProj))

        if nBottom < 3:
            print("Not enough boundary nodes for buffer mesh")
            return None

        # 4. 중간 평면 노드 생성 (전체 XY 합집합)
        zMid = (zBottom + zTop) / 2.0
        allXY = set(bottomXYmap.keys()) | topXY
        midNodeList = []
        for xy in allXY:
            curNID += 1
            newNode = self.nodeMan.AddNodewithID(curNID, xy[0], xy[1], zMid)
            midNodeList.append(newNode)
        nMid = len(midNodeList)

        nTotal = nBottom + nMid + len(allTopList)
        print("Buffer: {0} mid(z={1:.4f}), total={2} points".format(
            nMid, zMid, nTotal))

        # 5. Z-스케일링
        xyExtent = max(xMax - xMin, yMax - yMin)
        zScale = xyExtent / thickness if thickness > 0 and xyExtent > 0 else 1.0

        # 6. 3D 점 배열 (bottom + mid + allTop)
        points3D = np.zeros((nTotal, 3))
        nodeDict = {}

        idx = 0
        for node in bottomNodeList:
            points3D[idx] = [node.x, node.y, (node.z - zBottom) * zScale]
            nodeDict[idx] = node
            idx += 1
        for node in midNodeList:
            points3D[idx] = [node.x, node.y, (node.z - zBottom) * zScale]
            nodeDict[idx] = node
            idx += 1
        for node in allTopList:
            points3D[idx] = [node.x, node.y, (node.z - zBottom) * zScale]
            nodeDict[idx] = node
            idx += 1

        # 7. 3D Delaunay (z-jitter로 co-planar degeneracy 방지)
        jitter = np.random.uniform(-1e-6, 1e-6, nTotal) * zScale
        points3D[:, 2] += jitter
        tri = Delaunay(points3D)
        print("Delaunay done: {0} simplices".format(len(tri.simplices)))

        # 8. 유효 tetra 필터링 + 체적/방향 체크 (numpy 벡터 연산)
        simplices = tri.simplices  # (nSimplex, 4)

        # 원본 좌표로 z범위 체크 (스케일링 안 된 좌표)
        origZ = np.zeros(nTotal)
        for i, node in nodeDict.items():
            origZ[i] = node.z

        # z범위 필터링: 모든 꼭짓점의 z가 [zBottom-tol, zTop+tol] 범위 내
        simpZ = origZ[simplices]  # (nSimplex, 4)
        zMask = (simpZ.min(axis=1) >= zBottom - tol) & (simpZ.max(axis=1) <= zTop + tol)
        validSimp = simplices[zMask]
        print("After z-filter: {0} simplices".format(len(validSimp)))

        # 원본 좌표로 체적 계산
        origCoords = np.zeros((nTotal, 3))
        for i, node in nodeDict.items():
            origCoords[i] = [node.x, node.y, node.z]

        p0 = origCoords[validSimp[:, 0]]
        p1 = origCoords[validSimp[:, 1]]
        p2 = origCoords[validSimp[:, 2]]
        p3 = origCoords[validSimp[:, 3]]

        a = p1 - p0
        b = p2 - p0
        c = p3 - p0
        signedVol = (a[:, 0]*(b[:, 1]*c[:, 2] - b[:, 2]*c[:, 1])
                    - a[:, 1]*(b[:, 0]*c[:, 2] - b[:, 2]*c[:, 0])
                    + a[:, 2]*(b[:, 0]*c[:, 1] - b[:, 1]*c[:, 0])) / 6.0

        minVol = thickness * 1e-10
        volMask = np.abs(signedVol) >= minVol
        degenerateCount = int(np.sum(~volMask))

        finalSimp = validSimp[volMask]
        finalVol = signedVol[volMask]
        print("After vol-filter: {0} valid, {1} degenerate".format(len(finalSimp), degenerateCount))

        # element 추가
        curEID = maxEID
        validCount = 0
        for i in range(len(finalSimp)):
            n0, n1, n2, n3 = finalSimp[i]
            nd0, nd1, nd2, nd3 = nodeDict[n0], nodeDict[n1], nodeDict[n2], nodeDict[n3]
            curEID += 1
            if finalVol[i] < 0:
                self.elementMan.AddTetrahedronLinearElement(curEID, nd0, nd2, nd1, nd3)
            else:
                self.elementMan.AddTetrahedronLinearElement(curEID, nd0, nd1, nd2, nd3)
            validCount += 1

        self.type = "Solid"
        name = self.geoFileName.replace(".geo", "")
        self.section = self.sectionMan.CreateSolidSection(name)
        self.part.SetSectionID(self.sectionMan.maxid)
        self.shape = None

        print("Buffer mesh: {0} valid tetra, {1} degenerate removed (of {2} total)".format(
            validCount, degenerateCount, len(tri.simplices)))
        return True

    @staticmethod
    def extract_face_msh(inputMshFile, outputMshFile, targetZ, tol=1e-6):
        """
        MSH 4.1 파일에서 특정 z좌표의 2D surface 요소를 추출하여 별도 MSH 파일로 저장.
        Buffer mesh 생성 시 Merge하여 boundary constraint로 사용.
        """
        with open(inputMshFile, 'r') as f:
            content = f.read()

        # --- Parse Nodes ---
        nstart = content.find('$Nodes')
        nend = content.find('$EndNodes')
        node_section = content[nstart:nend].split('\n')
        # line 1: numEntityBlocks numNodes minTag maxTag
        header = node_section[1].split()
        numEntityBlocks = int(header[0])

        all_nodes = {}  # id -> (x, y, z)
        i = 2
        while i < len(node_section):
            parts = node_section[i].split()
            if len(parts) < 4:
                i += 1
                continue
            entityDim, entityTag, parametric, numNodesInBlock = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            # Read node tags
            node_tags = []
            for j in range(numNodesInBlock):
                i += 1
                node_tags.append(int(node_section[i].strip()))
            # Read node coordinates
            for j in range(numNodesInBlock):
                i += 1
                coords = node_section[i].split()
                x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
                all_nodes[node_tags[j]] = (x, y, z)
            i += 1

        # --- Find nodes at targetZ ---
        face_node_ids = set()
        for nid, (x, y, z) in all_nodes.items():
            if abs(z - targetZ) < tol:
                face_node_ids.add(nid)

        if len(face_node_ids) == 0:
            print("No nodes found at z={0}".format(targetZ))
            return False

        # --- Parse Elements, find 2D elements using only face nodes ---
        estart = content.find('$Elements')
        eend = content.find('$EndElements')
        elem_section = content[estart:eend].split('\n')

        face_elements = []  # (elemTag, node1, node2, node3, node4)
        i = 2
        while i < len(elem_section):
            parts = elem_section[i].split()
            if len(parts) < 4:
                i += 1
                continue
            entityDim, entityTag, elemType, numElemsInBlock = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            for j in range(numElemsInBlock):
                i += 1
                eparts = elem_section[i].split()
                if entityDim == 2:  # 2D surface elements
                    elemTag = int(eparts[0])
                    enodes = [int(x) for x in eparts[1:]]
                    if all(n in face_node_ids for n in enodes):
                        face_elements.append((elemTag, elemType, enodes))
            i += 1

        if len(face_elements) == 0:
            print("No face elements found at z={0}".format(targetZ))
            return False

        # --- Collect used nodes ---
        used_node_ids = set()
        for (etag, etype, enodes) in face_elements:
            for n in enodes:
                used_node_ids.add(n)

        # --- Write output MSH 2.2 (simpler, better Merge support) ---
        with open(outputMshFile, 'w') as f:
            f.write('$MeshFormat\n2.2 0 8\n$EndMeshFormat\n')
            # Nodes
            sorted_nodes = sorted(used_node_ids)
            f.write('$Nodes\n')
            f.write('{0}\n'.format(len(sorted_nodes)))
            for nid in sorted_nodes:
                x, y, z = all_nodes[nid]
                f.write('{0} {1:.15e} {2:.15e} {3:.15e}\n'.format(nid, x, y, z))
            f.write('$EndNodes\n')
            # Elements
            f.write('$Elements\n')
            f.write('{0}\n'.format(len(face_elements)))
            for idx, (etag, etype, enodes) in enumerate(face_elements):
                node_str = ' '.join(str(n) for n in enodes)
                f.write('{0} {1} 0 {2}\n'.format(idx + 1, etype, node_str))
            f.write('$EndElements\n')

        print("Extracted {0} face elements ({1} nodes) at z={2} -> {3}".format(
            len(face_elements), len(used_node_ids), targetZ, outputMshFile))
        return True

    def GetMaxIDs(self):
        maxNID = self.nodeMan.maxID
        maxEID = self.elementMan.maxID
        return maxNID, maxEID
        

    def ExportStepFile(self, fileName, shape):
        if not fileName.endswith(".step"):
            fileName += ".step"
        stepFilePath = join(self.path, fileName)
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)
        
        
        step_writer = STEPControl_Writer()
        step_writer.Transfer(shape, STEPControl_AsIs)
        status = step_writer.Write(stepFilePath)
        if status == IFSelect_RetDone:
            print("STEP file written successfully to: " + stepFilePath)
        else:
            print("Error writing STEP file.")
          

