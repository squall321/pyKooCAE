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
            self.gmshPath = "/opt/gmsh-4.14.1-Linux64/bin/gmsh"
        self.meshAlgoOption = "auto"        
        #Select mesh algorithm: auto, meshadapt, del2d, front2d, delquad, quadqs, initial2d, del3d, front3d, mmg3d, hxt, initial3d

        self.hide = False
        self.shape = None
        self.aisShape = None
        
        pass

    def SetPath(self, path):
        self.path = path
        # find gmsh.exe in the path
        self.gmshPath = join(path, ".\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe")
        if os.path.exists(self.gmshPath):
            pass
        else:
            self.gmshPath = join(path, "..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe")
            if os.path.exists(self.gmshPath):
                pass
            else:
                self.gmshPath = join(path, "..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe")
                if os.path.exists(self.gmshPath):
                    pass
                else:
                    self.gmshPath = join(path, "..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe")
                    if os.path.exists(self.gmshPath):
                        pass
                    else:
                        self.gmshPath = join(path, "..\\..\\..\\..\\Library\\gmsh-4.11.1-Windows64\\gmsh.exe")
                        if os.path.exists(self.gmshPath):
                            pass
                        else:
                            print("gmsh.exe not found")
                            sys.exit()
    
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
          

