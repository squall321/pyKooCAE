import os
import sys
from io import StringIO
import numpy as np 

from pyDOE import lhs

from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooSection import *
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter
from KooCAEManager.KooDynaKeyword import *
from KooThreePointBendingSimulationGenerator import KooThreePointBendingSimulationGenerator
from KooImpactSimulationGenerator import KooImpactSimulationGenerator

class KooDynaDOEManager():
    
    def __init__(self):
        self.optimizationSimulationTool = "LSDYNA"
        self.currentDirectory = os.getcwd()        
        self.materialDOEFile = None
        self.outputFile = "input.txt"

        self.impactMode = {}
        self.impactInputFile = {}
        self.impactOutputOption = {}
        self.impactEstimationOption = {}
        self.impactNodeManager = {}
        self.impactNodeSetManager = {}
        self.impactPartManager = {}
        self.impactSectionManager = {}
        self.impactMaterialManager = {}
        self.impactResultManager = {}
        self.impactImporter = {}
        

        self.threePointBendingMode = {}
        self.threePointBendingInputFile = {}
        self.threePointBendingOutputOption = {}
        self.threePointBendingEstimationOption = {}
        self.threePointBendingNodeManager = {}
        self.threePointBendingNodeSetManager = {}
        self.threePointBendingPartManager = {}
        self.threePointBendingSectionManager = {}
        self.threePointBendingMaterialManager = {}
        self.threePointBendingResultManager = {}
        self.threePointBendingImporter = {}
        #self.threePointBendingLength = {}
        #self.threePointBendingWidth = {}
        #self.threePointBendingThickness = {}
        #self.threePointBendingMaterialIDList = {}
        
        self.tensileElasticMode = "Theory"
        self.tensileElasticInputFile = None
        self.tensileElasticOutputOption = None
        self.tensileElasticLength = 0.0
        self.tensileElasticWidth = 0.0
        self.tensileElasticThickness = []
        self.tensileElasticMaterialIDList = [] 
        self.tensileElasticNodeManager : NodeManager = NodeManager()    
        self.tensileElasticPartManager : KooPartManager = KooPartManager()
        self.tensileElasticImporter : KooDynaImporter = KooDynaImporter(self.tensileElasticNodeManager, self.tensileElasticPartManager)

        self.matKeywordDict = {}
        self.matOptionNameDict = {}
        self.matKeywordTypeDict = {}
        self.matDOEDict = {} 
        self.matNormalDistDict = {}
        self.matLatinHyperCubeDict = {}
        self.materials = {}

        self.doeMIDList = None

        pass

    def importDynaKeyfile(self, path):
        self.importer.importDynaFile(path)

    def importLSDynaDOEFile(self, path):
        print("Importing LSDyna DOE File")
        folderPath = os.path.dirname(path)        
        self.currentDirectory = folderPath
        os.chdir(self.currentDirectory)
        fileName = os.path.basename(path)
        
        with open(fileName, 'r') as file:
            line = file.readline()
            while True:
                
                if not line:
                    break
                if line.find("*OptimizationTool") != -1:
                    svector = line.split(",")
                    self.optimizationSimulationTool = svector[1].replace("\n","")
                    print("Optimization Tool: ", self.optimizationSimulationTool)
                    pass
                elif line.find("*OutputFile") != -1:
                    svector = line.split(",")
                    self.outputFile = svector[1].replace("\n","")
                    print("Output File: ", self.outputFile)
                    pass
                elif line.find("*Mat") != -1:
                    line = file.readline()
                    line = line.replace("\n","")
                    self.materialDOEFile = line
                    print("Material DOE File: ", self.materialDOEFile)
                    pass
                elif "*TensileElastic" in line:                    
                    svector = line.split(",")                    
                    self.tensileElasticMode = svector[1]           
                    print("TensileElastic Mode: ", self.tensileElasticMode)         
                    while True:
                        line = file.readline()
                        line = line.replace("\n","")
                        if line.find("*") != -1:
                            break
                        if "Length" in line:
                            svector = line.split(",")
                            self.tensileElasticLength = float(svector[1])
                            print("TensileElastic Length: ", self.tensileElasticLength)
                        elif "Width" in line:
                            svector = line.split(",")
                            self.tensileElasticWidth = float(svector[1])
                            print("TensileElastic Width: ", self.tensileElasticWidth)
                        elif "Thickness" in line:
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                self.tensileElasticThickness.append(float(svector[i]))
                            print("TensileElastic Thickness: ", self.tensileElasticThickness)                            
                        elif "MaterialID" in line:
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                self.tensileElasticMaterialIDList.append(int(svector[i]))
                            print("TensileElastic MaterialID: ", self.tensileElasticMaterialIDList)
                        elif "InputFile" in line:
                            svector = line.split(",")
                            inputFileName = svector[1]
                            path = os.path.join(self.currentDirectory, inputFileName)
                            self.tensileElasticInputFile = path
                            print("TensileElastic InputFile: ", self.tensileElasticInputFile)
                        elif "OutputOption" in line:
                            svector = line.split(",")
                            self.tensileElasticOutputOption = svector[1]
                            print("TensileElastic OutputOption: ", self.tensileElasticOutputOption)                            
                   
                elif "*3ptBending" in line:
                    svector = line.split(",")
                    
                    index = int(svector[2])
                    self.threePointBendingMode[index] = svector[1]
                    print("3ptBending Mode: ", self.threePointBendingMode[index])
                    if self.threePointBendingMode[index] == "Simulation":
                        self.threePointBendingNodeManager[index] = NodeManager()
                        self.threePointBendingNodeSetManager[index] = NodeSetManager()
                        self.threePointBendingPartManager[index] = KooPartManager()                                                
                        self.threePointBendingSectionManager[index] = KooSectionManager()
                        self.threePointBendingMaterialManager[index] = KooMaterialManager()
                        self.threePointBendingResultManager[index] = KooResultManager((self.threePointBendingNodeManager[index]))
                        self.threePointBendingImporter[index] = KooDynaImporter(self.threePointBendingNodeManager[index], self.threePointBendingPartManager[index], self.threePointBendingResultManager[index], self.threePointBendingMaterialManager[index], self.threePointBendingSectionManager[index])
                    while True:
                        line = file.readline()
                        line = line.replace("\n","")
                        if line.find("#") != -1:
                            pass
                        if line.find("*") != -1:
                            break
                        if "Length" in line:
                            svector = line.split(",")
                            self.threePointBendingLength[index] = float(svector[1])

                            print("3ptBending Length: ", self.threePointBendingLength[index])
                        elif "Width" in line:
                            svector = line.split(",")
                            self.threePointBendingWidth[index] = float(svector[1])
                            print("3ptBending Width: ", self.threePointBendingWidth[index])
                        elif "Thickness" in line:
                            svector = line.split(",")
                            curThicknessList = [] 
                            for i in range(1, len(svector)):
                                curThicknessList.append(float(svector[i]))
                            self.threePointBendingThickness[index] = curThicknessList
                            print("3ptBending Thickness: ", self.threePointBendingThickness[index])
                        elif "MaterialID" in line:
                            svector = line.split(",")
                            curBendingMaterialIDList = []
                            for i in range(1, len(svector)):
                                curBendingMaterialIDList.append(int(svector[i]))
                            self.threePointBendingMaterialIDList[index] = curBendingMaterialIDList
                            print("3ptBending MaterialID: ", self.threePointBendingMaterialIDList[index])                            
                        elif "InputFile" in line:
                            svector = line.split(",")
                            inputFileName = svector[1]
                            path = os.path.join(self.currentDirectory, inputFileName)
                            self.threePointBendingInputFile[index] = path
                            print("3ptBending InputFile: ", self.threePointBendingInputFile[index])
                        elif "OutputOption" in line:
                            svector = line.split(",")
                            outputOptionFileName = svector[1]
                            path = os.path.join(self.currentDirectory, outputOptionFileName)
                            self.threePointBendingOutputOption[index] = path
                            print("3ptBending OutputOption: ", self.threePointBendingOutputOption[index])   
                        elif "nodout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.threePointBendingEstimationOption, otherwise make new list 
                                if index not in self.threePointBendingEstimationOption.keys():
                                    self.threePointBendingEstimationOption[index] = {}
                                self.threePointBendingEstimationOption[index]["nodout"] = []                                 
                                # dt
                                self.threePointBendingEstimationOption[index]["nodout"].append(float(svector[1]))
                                # binary
                                self.threePointBendingEstimationOption[index]["nodout"].append(int(svector[2]))
                                # lcur
                                self.threePointBendingEstimationOption[index]["nodout"].append(int(svector[3]))
                                # ioopt
                                self.threePointBendingEstimationOption[index]["nodout"].append(int(svector[4]))
                                # node set id
                                self.threePointBendingEstimationOption[index]["nodout"].append(int(svector[5]))
                                print("3ptBending nodout: ", self.threePointBendingEstimationOption[index]["nodout"])
                        elif "nodfor" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.threePointBendingEstimationOption, otherwise make new list 
                                if index not in self.threePointBendingEstimationOption.keys():
                                    self.threePointBendingEstimationOption[index] = {}
                                self.threePointBendingEstimationOption[index]["nodfor"] = []       
                                # dt                                                         
                                self.threePointBendingEstimationOption[index]["nodfor"].append(float(svector[1]))
                                # binary
                                self.threePointBendingEstimationOption[index]["nodfor"].append(int(svector[2]))
                                # lcur
                                self.threePointBendingEstimationOption[index]["nodfor"].append(int(svector[3]))
                                # ioopt
                                self.threePointBendingEstimationOption[index]["nodfor"].append(int(svector[4]))
                                # node set id 
                                self.threePointBendingEstimationOption[index]["nodfor"].append(int(svector[5]))
                                # coordinate id
                                self.threePointBendingEstimationOption[index]["nodfor"].append(int(svector[6]))
                                print("3ptBending nodfor: ", self.threePointBendingEstimationOption[index]["nodfor"])
                        elif "bndout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.threePointBendingEstimationOption, otherwise make new list 
                                if index not in self.threePointBendingEstimationOption.keys():
                                    self.threePointBendingEstimationOption[index] = {}
                                self.threePointBendingEstimationOption[index]["bndout"] = []       
                                # dt                                                         
                                self.threePointBendingEstimationOption[index]["bndout"].append(float(svector[1]))
                                # binary
                                self.threePointBendingEstimationOption[index]["bndout"].append(int(svector[2]))
                                # lcur
                                self.threePointBendingEstimationOption[index]["bndout"].append(int(svector[3]))
                                # ioopt
                                self.threePointBendingEstimationOption[index]["bndout"].append(int(svector[4]))
                                print("3ptBending bndout: ", self.threePointBendingEstimationOption[index]["bndout"])
                        elif "elout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.threePointBendingEstimationOption, otherwise make new list 
                                if index not in self.threePointBendingEstimationOption.keys():
                                    self.threePointBendingEstimationOption[index] = {}
                                self.threePointBendingEstimationOption[index]["elout"] = []       
                                # dt                                                         
                                self.threePointBendingEstimationOption[index]["elout"].append(float(svector[1]))
                                # binary
                                self.threePointBendingEstimationOption[index]["elout"].append(int(svector[2]))
                                # lcur
                                self.threePointBendingEstimationOption[index]["elout"].append(int(svector[3]))
                                # ioopt
                                self.threePointBendingEstimationOption[index]["elout"].append(int(svector[4]))
                                # element set id
                                self.threePointBendingEstimationOption[index]["elout"].append(int(svector[5]))
                                if len(svector) > 6:
                                    # element set type  Beam, Shell, Solid                                
                                    self.threePointBendingEstimationOption[index]["elout"].append(svector[6])
                                print("3ptBending elout: ", self.threePointBendingEstimationOption[index]["elout"])                                

                    continue
                elif "*Impact" in line:
                    svector = line.split(",")
                    index = int(svector[2])
                    self.impactMode[index] = svector[1]
                    print("Impact Mode: ", self.impactMode[index])
                    if self.impactMode[index] == "Simulation":
                        self.impactNodeManager[index] = NodeManager()
                        self.impactNodeSetManager[index] = NodeSetManager()
                        self.impactPartManager[index] = KooPartManager()                                                
                        self.impactSectionManager[index] = KooSectionManager()
                        self.impactMaterialManager[index] = KooMaterialManager()
                        self.impactResultManager[index] = KooResultManager((self.impactNodeManager[index]))
                        self.impactImporter[index] = KooDynaImporter(self.impactNodeManager[index], self.impactPartManager[index], self.impactResultManager[index], self.impactMaterialManager[index], self.impactSectionManager[index])
                    while True:
                        line = file.readline()
                        line = line.replace("\n","")
                        if line.find("#") != -1:
                            pass
                        if line.find("*") != -1:
                            break
                        if "InputFile" in line:
                            svector = line.split(",")
                            inputFileName = svector[1]
                            path = os.path.join(self.currentDirectory, inputFileName)
                            self.impactInputFile[index] = path
                            print("Impact InputFile: ", self.impactInputFile[index])
                        elif "OutputOption" in line:
                            svector = line.split(",")
                            outputOptionFileName = svector[1]
                            path = os.path.join(self.currentDirectory, outputOptionFileName)
                            self.impactOutputOption[index] = path
                            print("Impact OutputOption: ", self.impactOutputOption[index])
                        elif "nodout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.impactEstimationOption, otherwise make new list 
                                if index not in self.impactEstimationOption.keys():
                                    self.impactEstimationOption[index] = {}
                                self.impactEstimationOption[index]["nodout"] = []                                 
                                # dt
                                self.impactEstimationOption[index]["nodout"].append(float(svector[1]))
                                # binary
                                self.impactEstimationOption[index]["nodout"].append(int(svector[2]))
                                # lcur
                                self.impactEstimationOption[index]["nodout"].append(int(svector[3]))
                                # ioopt
                                self.impactEstimationOption[index]["nodout"].append(int(svector[4]))
                                # node set id
                                self.impactEstimationOption[index]["nodout"].append(int(svector[5]))
                                print("Impact nodout: ", self.impactEstimationOption[index]["nodout"])
                        elif "nodfor" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.impactEstimationOption, otherwise make new list 
                                if index not in self.impactEstimationOption.keys():
                                    self.impactEstimationOption[index] = {}
                                self.impactEstimationOption[index]["nodfor"] = []       
                                # dt                                                         
                                self.impactEstimationOption[index]["nodfor"].append(float(svector[1]))
                                # binary
                                self.impactEstimationOption[index]["nodfor"].append(int(svector[2]))
                                # lcur
                                self.impactEstimationOption[index]["nodfor"].append(int(svector[3]))
                                # ioopt
                                self.impactEstimationOption[index]["nodfor"].append(int(svector[4]))
                                # node set id 
                                self.impactEstimationOption[index]["nodfor"].append(int(svector[5]))
                                # coordinate id
                                self.impactEstimationOption[index]["nodfor"].append(int(svector[6]))
                                print("Impact nodfor: ", self.impactEstimationOption[index]["nodfor"])
                        elif "bndout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.impactEstimationOption, otherwise make new list 
                                if index not in self.impactEstimationOption.keys():
                                    self.impactEstimationOption[index] = {}
                                self.impactEstimationOption[index]["bndout"] = []       
                                # dt                                                         
                                self.impactEstimationOption[index]["bndout"].append(float(svector[1]))
                                # binary
                                self.impactEstimationOption[index]["bndout"].append(int(svector[2]))
                                # lcur
                                self.impactEstimationOption[index]["bndout"].append(int(svector[3]))
                                # ioopt
                                self.impactEstimationOption[index]["bndout"].append(int(svector[4]))
                                print("Impact bndout: ", self.impactEstimationOption[index]["bndout"])
                        elif "elout" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                # get if it exists in self.impactEstimationOption, otherwise make new list 
                                if index not in self.impactEstimationOption.keys():
                                    self.impactEstimationOption[index] = {}
                                self.impactEstimationOption[index]["elout"] = []       
                                # dt                                                         
                                self.impactEstimationOption[index]["elout"].append(float(svector[1]))
                                # binary
                                self.impactEstimationOption[index]["elout"].append(int(svector[2]))
                                # lcur
                                self.impactEstimationOption[index]["elout"].append(int(svector[3]))
                                # ioopt
                                self.impactEstimationOption[index]["elout"].append(int(svector[4]))
                                # element set id
                                self.impactEstimationOption[index]["elout"].append(int(svector[5]))
                                if len(svector) > 6:
                                    # element set type  Beam, Shell, Solid                                
                                    self.impactEstimationOption[index]["elout"].append(svector[6])
                                print("Impact elout: ", self.impactEstimationOption[index]["elout"])
                    continue
                else:
                    pass
                line = file.readline()
            file.close()

    def importModel(self):        
        if self.optimizationSimulationTool == "LSDYNA":
            if self.threePointBendingInputFile is not None:
                print("Importing 3ptBending Model")
                for key in self.threePointBendingInputFile.keys():
                    curModel : KooDynaImporter = self.threePointBendingImporter[key]                                        
                    if key in self.threePointBendingOutputOption.keys():
                        curOutputOptionPath = self.threePointBendingOutputOption[key]                        
                    else:
                        curOutputOptionPath = None
                    curModel.importDynaFile(self.threePointBendingInputFile[key])                    
                    if curOutputOptionPath is not None:
                        maxNID = curModel.importNode()                        
                        maxPID = curModel.importPart()  
                        maxNSID = curModel.importNodeSet()
                        maxSID = curModel.importSection()
                        maxMID = curModel.importMaterial()
                        maxEID = curModel.partManager.FindMaxEID()
                        if self.doeMIDList is not None:
                            for id in self.doeMIDList:
                                curModel.matManager.RemoveMaterialbyID(id)
                                
                        dynaScenarioMan = KooThreePointBendingSimulationGenerator(curModel)
                        dynaScenarioMan.SetPreMaxMeshID(maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID)                                                        
                        dynaScenarioMan.SetMeshPath("TempMesh")
                        dynaScenarioMan.SetLoadBoundaryOptionPath(curOutputOptionPath)
                        dynaScenarioMan.SetLoadBoundaryOption()
                        dynaFileList = dynaScenarioMan.GenerateDynabyLoadBoundaryOption()
                        self.threePointBendingNodeManager[key] = NodeManager()
                        self.threePointBendingNodeSetManager[key] = NodeSetManager()
                        self.threePointBendingPartManager[key] = KooPartManager()                                                
                        self.threePointBendingSectionManager[key] = KooSectionManager()
                        self.threePointBendingMaterialManager[key] = KooMaterialManager()
                        self.threePointBendingResultManager[key] = KooResultManager((self.threePointBendingNodeManager[key]))
                        self.threePointBendingImporter[key] = KooDynaImporter(self.threePointBendingNodeManager[key], self.threePointBendingPartManager[key], self.threePointBendingResultManager[key], self.threePointBendingMaterialManager[key], self.threePointBendingSectionManager[key], self.threePointBendingNodeSetManager[key])
                        curModel : KooDynaImporter = self.threePointBendingImporter[key]                                                                
                        folderofInput = os.path.dirname(self.threePointBendingInputFile[key])
                        newFilePath = os.path.join(folderofInput, dynaFileList[0])
                        curModel.importDynaFile(newFilePath)
                        
                    

                    if "DATABASE_BNDOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.threePointBendingEstimationOption.keys():
                            if "bndout" in self.threePointBendingEstimationOption[key].keys():
                                curOption = self.threePointBendingEstimationOption[key]["bndout"]                                 
                                curModel.SetBNDOUT(curOption[0],curOption[1],curOption[2],curOption[3])                  
                    if "DATABASE_NODOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.threePointBendingEstimationOption.keys():
                            if "nodout" in self.threePointBendingEstimationOption[key].keys():
                                curOption = self.threePointBendingEstimationOption[key]["nodout"]                                
                                curModel.SetNODOUT(curOption[0],curOption[1],curOption[2],curOption[3])
                                if curOption[4] == 0:
                                    curModel.SetHistoryNodeforAll()
                                else:
                                    curModel.SetHistoryNodeforSet(curOption[4])
                                
                    if "DATABASE_NODFOR" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.threePointBendingEstimationOption.keys():
                            if "nodfor" in self.threePointBendingEstimationOption[key].keys():
                                curOption = self.threePointBendingEstimationOption[key]["nodfor"]                                
                                curModel.SetNODFOR(curOption[0],curOption[1],curOption[2],curOption[3])
                                curModel.SetNodalForceGroup(curOption[4],curOption[5])
                                
                    if "DATABASE_ELOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.threePointBendingEstimationOption.keys():
                            if "elout" in self.threePointBendingEstimationOption[key].keys():
                                curOption = self.threePointBendingEstimationOption[key]["elout"]                                
                                curModel.SetELOUT(curOption[0],curOption[1],curOption[2],curOption[3])
                                if curOption[4] == 0:
                                    curModel.SetHistoryElementforAll()
                                else:
                                    elementType = curOption[5]
                                    if elementType.lower() == "beam":
                                        curModel.SetHistoryElementforBeamSet(curOption[4])
                                    elif elementType.lower() == "shell":
                                        curModel.SetHistoryElementforShellSet(curOption[4])
                                    elif elementType.lower() == "solid":
                                        curModel.SetHistoryElementforSolidSet(curOption[4])                    
                    
                    print("3ptBending Model " + str(key) + " Imported")
            if self.impactInputFile is not None:
                print("Importing Impact Model")
                
                for key in self.impactInputFile.keys():
                    curModel : KooDynaImporter = self.impactImporter[key]
                    if key in self.impactOutputOption.keys():
                        curOutputOptionPath = self.impactOutputOption[key]
                    else:
                        curOutputOptionPath = None
                    curModel.importDynaFile(self.impactInputFile[key])
                    if curOutputOptionPath is not None:
                        maxNID = curModel.importNode()
                        maxNSID = curModel.importNodeSet()
                        maxPID = curModel.importPart()
                        maxSID = curModel.importSection()
                        maxMID = curModel.importMaterial()
                        maxEID = curModel.partManager.FindMaxEID()
                        if self.doeMIDList is not None:
                            for id in self.doeMIDList:
                                curModel.matManager.RemoveMaterialbyID(id)
                        dynaScenarioMan = KooImpactSimulationGenerator(curModel)
                        dynaScenarioMan.SetPreMaxMeshID(maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID)
                        dynaScenarioMan.SetMeshPath("TempMesh")
                        dynaScenarioMan.SetLoadBoundaryOptionPath(curOutputOptionPath)
                        dynaScenarioMan.SetLoadBoundaryOption()
                        dynaFileList = dynaScenarioMan.GenerateDynabyLoadBoundaryOption()
                        self.impactNodeManager[key] = NodeManager()
                        self.impactNodeSetManager[key] = NodeSetManager()
                        self.impactPartManager[key] = KooPartManager()
                        self.impactSectionManager[key] = KooSectionManager()
                        self.impactMaterialManager[key] = KooMaterialManager()
                        self.impactResultManager[key] = KooResultManager((self.impactNodeManager[key]))
                        self.impactImporter[key] = KooDynaImporter(self.impactNodeManager[key], self.impactPartManager[key], self.impactResultManager[key], self.impactMaterialManager[key], self.impactSectionManager[key], self.impactNodeSetManager[key])
                        curModel : KooDynaImporter = self.impactImporter[key]
                        folderofInput = os.path.dirname(self.impactInputFile[key])
                        newFilePath = os.path.join(folderofInput, dynaFileList[0])
                        curModel.importDynaFile(newFilePath)
                    if "DATABASE_BNDOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.impactEstimationOption.keys():
                            if "bndout" in self.impactEstimationOption[key].keys():
                                curOption = self.impactEstimationOption[key]["bndout"]
                                curModel.SetBNDOUT(curOption[0],curOption[1],curOption[2],curOption[3])
                    if "DATABASE_NODOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.impactEstimationOption.keys():
                            if "nodout" in self.impactEstimationOption[key].keys():
                                curOption = self.impactEstimationOption[key]["nodout"]
                                curModel.SetNODOUT(curOption[0],curOption[1],curOption[2],curOption[3])
                                if curOption[4] == 0:
                                    curModel.SetHistoryNodeforAll()
                                else:
                                    curModel.SetHistoryNodeforSet(curOption[4])
                    if "DATABASE_NODFOR" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.impactEstimationOption.keys():
                            if "nodfor" in self.impactEstimationOption[key].keys():
                                curOption = self.impactEstimationOption[key]["nodfor"]
                                curModel.SetNODFOR(curOption[0],curOption[1],curOption[2],curOption[3])
                                curModel.SetNodalForceGroup(curOption[4],curOption[5])

                    if "DATABASE_ELOUT" in curModel.dynaManager.dynaKeywordMan.keywords:
                        pass
                    else:
                        if key in self.impactEstimationOption.keys():
                            if "elout" in self.impactEstimationOption[key].keys():
                                curOption = self.impactEstimationOption[key]["elout"]
                                curModel.SetELOUT(curOption[0],curOption[1],curOption[2],curOption[3])
                                if curOption[4] == 0:
                                    curModel.SetHistoryElementforAll()
                                else:
                                    elementType = curOption[5]
                                    if elementType.lower() == "beam":
                                        curModel.SetHistoryElementforBeamSet(curOption[4])
                                    elif elementType.lower() == "shell":
                                        curModel.SetHistoryElementforShellSet(curOption[4])
                                    elif elementType.lower() == "solid":
                                        curModel.SetHistoryElementforSolidSet(curOption[4])
                    print("Impact Model " + str(key) + " Imported")



            
            if self.tensileElasticInputFile is not None:
                print("Importing TensileElastic Model")
                self.tensileElasticImporter.importDynaFile(self.tensileElasticInputFile)
                self.tensileElasticImporter.importNode()
                self.tensileElasticImporter.importNodeSet()
                self.tensileElasticImporter.importPart()
                self.tensileElasticImporter.SetELOUT()
                self.tensileElasticImporter.SetNODOUT()
                self.tensileElasticImporter.SetHistoryNodeforAll()
                self.tensileElasticImporter.SetHistoryElementforAll()
                print("TensileElastic Model Imported")            
        pass            

    def ImportMaterialDOE(self):
        if self.materialDOEFile is None:
            return
        filePath = os.path.join(self.currentDirectory, self.materialDOEFile)
        print("Importing Material DOE File: ", filePath)
        doeMIDList = [] 
        with open(filePath, 'r') as file:
            line = file.readline()
            line = line.replace("\n","")
            while True:
                if not line:
                    break
                if "**End" in line:
                    break
                elif "**MaterialOriginal" in line:
                    dynaKeyword = DynaKeyword("dummy")
                    svector = line.split(",")
                    materialID = int(svector[1])
                    doeMIDList.append(materialID)
                    matLines = [] 
                    matLinesName = [] 
                    line = file.readline()
                    line = line.replace("\n","")
                    #matLines.append(line)
                    if "$$" in line:
                        line = line.replace("$$","  ")
                        parsed = dynaKeyword.parse_whole(line,[10,10,10,10,10,10,10,10])
                        parsed = [s.replace(" ", "") for s in parsed]
                        matLinesName.append(parsed)
                    name = line.replace("*","")
                    print("Material Name: ", name)
                    while True:
                        line = file.readline()
                        line = line.replace("\n","")

                        if line.find("**") != -1:
                            break
                        if "$$" in line:
                            line = line.replace("$$","  ")
                            parsed = dynaKeyword.parse_whole(line,[10,10,10,10,10,10,10,10])
                            parsed = [s.replace(" ", "") for s in parsed]
                            matLinesName.append(parsed)

                        else:
                            matLines.append(line)

                    print("Material ID: ", materialID)
                    print("Material Lines: ")
                    for i in range(len(matLines)):
                        print(matLines[i])
                    print("Material Lines Name: ")
                    for i in range(len(matLinesName)):
                        outString = ""
                        for j in range(len(matLinesName[i])):
                            outString += matLinesName[i][j] + " "
                        print(outString)
                    self.matKeywordDict[materialID] = matLines
                    self.matOptionNameDict[materialID] = matLinesName
                    self.matKeywordTypeDict[materialID] = name
                elif "**MaterialDOE" in line:
                    line = line.replace("\n","")
                    svector = line.split(",")
                    materialID = int(svector[1])
                    doeMIDList.append(materialID)
                    mode = svector[2]
                    print("Material ID: ", materialID)
                    print("Mode: ", mode)
                    if mode == "DOE":
                        materialDOEs = {}
                        line = file.readline()
                        line = line.replace("\n","")
                        nameVector = line.split(",")
                        outstr = ""
                        for i in range(len(nameVector)):
                            materialDOEs[nameVector[i]] = []
                            outstr += nameVector[i] + " "
                        print(outstr)
                        while True:
                            line = file.readline()
                            line = line.replace("\n","")
                            if line.find("**") != -1:
                                break
                            svector = line.split(",")
                            materialDOEs[nameVector[0]].append(svector[0])
                            outstr = svector[0] + " "
                            for i in range(1,len(nameVector)):
                                materialDOEs[nameVector[i]].append(float(svector[i]))
                                outstr += str(svector[i]) + " "
                            print(outstr)
                        self.matDOEDict[materialID] = materialDOEs
                        print("Material DOE for Material ID: ", materialID," is imported")
                    elif mode == "NORMALDIST":
                        numofSamples = int(svector[3])
                        materialNormalDist = {}
                        line = file.readline()
                        line = line.replace("\n","")
                        nameVector = line.split(",")
                        outstr = ""
                        for i in range(len(nameVector)):
                            materialNormalDist[nameVector[i]] = []
                            outstr += nameVector[i] + " "
                        print(outstr)
                        materialNormalDist["Count"] = numofSamples
                        print("Number of Samples: ", numofSamples)
                        while True:
                            line = file.readline()
                            line = line.replace("\n","")
                            if line.find("**") != -1:
                                break
                            svector = line.split(",")
                            materialNormalDist[nameVector[0]].append(svector[0])
                            outstr = svector[0] + " "
                            for i in range(1,len(nameVector)):
                                materialNormalDist[nameVector[i]].append(float(svector[i]))
                                outstr += str(svector[i]) + " "
                            print(outstr)
                        self.matNormalDistDict[materialID] = materialNormalDist
                        print("Material DOE for Material ID: ", materialID," is imported")
                    elif mode == "LHS":
                        numofSamples = int(svector[3])
                        materialLHS = {}
                        line = file.readline()
                        line = line.replace("\n","")
                        nameVector = line.split(",")
                        outstr = ""
                        for i in range(len(nameVector)):
                            materialLHS[nameVector[i]] = []
                            outstr += nameVector[i] + " "
                        print(outstr)
                        materialLHS["Count"] = numofSamples
                        print("Number of Samples: ", numofSamples)
                        while True:
                            line = file.readline()
                            line = line.replace("\n","")
                            if line.find("**") != -1:
                                break
                            svector = line.split(",")
                            materialLHS[nameVector[0]].append(svector[0])
                            outstr = svector[0] + " "
                            for i in range(1,len(nameVector)):
                                materialLHS[nameVector[i]].append(float(svector[i]))
                                outstr += str(svector[i]) + " "
                            print(outstr)
                        self.matLatinHyperCubeDict[materialID] = materialLHS
                        print("Material DOE for Material ID: ", materialID," is imported")


                else:
                    line = file.readline()
                    line = line.replace("\n","")
            file.close()
            self.doeMIDList = doeMIDList
        
    def GenerateMaterialLSDynaKeyword(self):
        self.materials = {}
        for key in self.matKeywordTypeDict.keys():
            print("Generating LSDyna Keyword for Material ID: ", key)
            matName = self.matKeywordTypeDict[key]
            material = None
            if "MAT_ELASTIC" == matName:
                material = MatElastic()
            elif "MAT_ELASTIC_TITLE" == matName:
                material = MatElasticTitle()
            elif "MAT_SOIL_AND_FOAM" == matName:
                material = MatSoilAndFoam()
            elif "MAT_SOIL_AND_FOAM_FAILURE" == matName:
                material = MatSoilAndFoamFailure()
            elif "MAT_RIGID" == matName:
                material = MatRigid()
            elif "MAT_RIGID_TITLE" == matName:
                material = MatRigidTitle()
            elif "MAT_COMPOSITE_DAMAGE" == matName:
                material = MatCompositeDamage()
            elif "MAT_COMPOSITE_DAMAGE_TITLE" == matName:
                material = MatCompositeDamageTitle()
            elif "MAT_PLASTIC_KINEMATIC" == matName:
                material = MatPlasticKinematic()
            elif "MAT_PLASTIC_KINEMATIC_TITLE" == matName:
                material = MatPlasticKinematicTitle()
            elif "MAT_PIECEWISE_LINEAR_PLASTICITY" == matName:
                material = MatPiecewiseLinearPlasticity()
            elif "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" == matName:
                material = MatPiecewiseLinearPlasticityTitle()
            elif "MAT_MOONEY-RIVLIN_RUBBER" == matName:
                material = MatMooneyRivlinRubber()
            elif "MAT_MOONEY-RIVLIN_RUBBER_TITLE" == matName:
                material = MatMooneyRivlinRubberTitle()
            elif "MAT_SPOTWELD" == matName:
                material = MatSpotweld()
            elif "MAT_SPOTWELD_TITLE" == matName:
                material = MatSpotweldTitle()
            if material is not None:
                material.parse([self.matKeywordDict[key]])
                self.materials[key] = material
                print("LSDyna Keyword for Material ID: ", key, " is generated")            
           
        

    def GenerateMaterialDOE(self,numberofSamples=0):
        if self.materials is None:
            return
                
        path_for_output = os.path.join(self.currentDirectory, self.outputFile)
        latinHyperCubeGenerated = None
        
        if len(self.matLatinHyperCubeDict)>0:
            print("Generating Material DOE from Latin Hyper Cube Sampling...")
            totalNumberofVariables = 0  
            for id in self.matLatinHyperCubeDict.keys():
                totalNumberofVariables += len(self.matLatinHyperCubeDict[id].keys())-2
            if numberofSamples == 0:
                for id in self.matLatinHyperCubeDict.keys():
                    numberofSamples += self.matLatinHyperCubeDict[id]['Count']
            print("Total Number of Variables: ", totalNumberofVariables) 
            print("Number of Samples: ", numberofSamples)                  
            latinHyperCubeGenerated = lhs(n=totalNumberofVariables, samples=numberofSamples)            
            i = 0 
            for id in self.matLatinHyperCubeDict.keys():
                curmatLHS = self.matLatinHyperCubeDict[id]                
                materialDOEs = {}                
                jmin = 0
                jmax = 0
                for j in range(len(curmatLHS['Option'])):                            
                    if curmatLHS['Option'][j] == "MIN":
                        jmin = j
                    elif curmatLHS['Option'][j] == "MAX":
                        jmax = j                
                materialDOEs['Option'] = []
                for j in range(0,numberofSamples):
                    materialDOEs['Option'].append(j)
                for name in curmatLHS.keys():
                    if name != "Count" and name != "Option":
                        materialDOEs[name] = []
                        
                        for j in range(0,numberofSamples):
                            curValue = latinHyperCubeGenerated[j][i]
                            minValue = curmatLHS[name][jmin]
                            maxValue = curmatLHS[name][jmax]
                            value = minValue + (maxValue - minValue) * curValue                            
                            materialDOEs[name].append(value)
                        i += 1     
                        print("Material Variable Name: ", name)
                        print("Min Value: ", minValue)
                        print("Max Value: ", maxValue)
                print("Material DOE for Material ID: ", id, " is generated") 

                self.matDOEDict[id] = materialDOEs
            print("Material DOE from Latin Hyper Cube Sampling is generated")

        print("Generating Material DOE for LSDyna Keyword...")   
        with open(path_for_output, 'w') as outFile:   
            outline = "Sample Number"
            for mkey in self.materials.keys():
                material = self.materials[mkey]
                if mkey in self.matDOEDict.keys():
                    materialDOE = self.matDOEDict[mkey]
                    matOptionName = self.matOptionNameDict[mkey]
                    curjth = [] 
                    curkth = []
                    curname = []
                    # from matOptionName, find location of "E"

                    for j in range(len(matOptionName)):
                        for k in range(len(matOptionName[j])):
                            for m in materialDOE.keys():
                                if m == matOptionName[j][k] and m != "Option":
                                    if "TITLE" in material.name:
                                        curjth.append(j+1)
                                    else:
                                        curjth.append(j)
                                    curkth.append(k)
                                    curname.append(m)                    
                    for j in range(len(curjth)):                    
                        outline += "," + curname[j] + str(mkey)                    
                if mkey in self.matNormalDistDict.keys():
                    
                    materialNormalDistDict = self.matNormalDistDict[mkey]
                    matOptionName = self.matOptionNameDict[mkey]
                    curjth = []      
                    curkth = [] 
                    curname = [] 
                    for j in range(len(matOptionName)):
                        for k in range(len(matOptionName[j])):
                            for m in materialNormalDistDict.keys():
                                if m == matOptionName[j][k] and m != "Option":
                                    if "TITLE" in material.name:
                                        curjth.append(j+1)
                                    else:
                                        curjth.append(j)
                                    curkth.append(k)
                                    curname.append(m)
                    outline = "Sample Number"
                    for j in range(len(curjth)):                    
                        outline += "," + curname[j] + str(mkey)
            outFile.write(outline + "\n")

            for i in range(numberofSamples):
                outline = str(i)
                outString = StringIO()
                for mkey in self.materials.keys():
                    #print("Generating Material DOE for Sample: ", i+1, " Material ID: ", mkey)
                    material = self.materials[mkey]
                    if mkey in self.matDOEDict.keys():
                        #print("Material DOE for Sample: ", i+1, " Material ID: ", mkey)
                        
                        materialDOE = self.matDOEDict[mkey]
                        matOptionName = self.matOptionNameDict[mkey]
                        size = len(materialDOE['Option'])

                        curIndexofSample = materialDOE['Option'][i%size]
                        curjth = [] 
                        curkth = []
                        curname = []
                        # from matOptionName, find location of "E"

                        for j in range(len(matOptionName)):
                            for k in range(len(matOptionName[j])):
                                for m in materialDOE.keys():
                                    if m == matOptionName[j][k] and m != "Option":
                                        if "TITLE" in material.name:
                                            curjth.append(j+1)
                                        else:
                                            curjth.append(j)
                                        curkth.append(k)
                                        curname.append(m)
                        
                        for j in range(len(curjth)):
                            value = materialDOE[curname[j]][i%size]
                            formatted_string = format(value, ">10.4e")
                            try:
                                material.setIthJthKth(0,curjth[j], curkth[j], formatted_string)
                            except:
                                print("cur jth kth", curjth[j], curkth[j])
                                print("Error in setting value: ", formatted_string)
                            
                            outline += "," + str(materialDOE[curname[j]][i%size])
                        #print("Material DOE for Sample: ", i+1, " Material ID: ", mkey, " is generated")
                    elif mkey in self.matNormalDistDict.keys():
                        #print("Material Normal Distribution for Sample: ", i+1, " Material ID: ", mkey)
                        materialNormalDistDict = self.matNormalDistDict[mkey]
                        matOptionName = self.matOptionNameDict[mkey]
                        size = materialNormalDistDict['Count']
                        # find location of 'AVG' in materialNormalDistDict
                        javg = 0
                        jstd = 0
                        jmin = 0
                        jmax = 0
                        for j in range(len(materialNormalDistDict['Option'])):                            
                            if materialNormalDistDict['Option'][j] == "AVG":
                                javg = j
                            elif materialNormalDistDict['Option'][j] == "STD":
                                jstd = j
                            elif materialNormalDistDict['Option'][j] == "MIN":
                                jmin = j
                            elif materialNormalDistDict['Option'][j] == "MAX":
                                jmax = j
                        
                        curjth = []      
                        curkth = [] 
                        curname = [] 
                        for j in range(len(matOptionName)):
                            for k in range(len(matOptionName[j])):
                                for m in materialNormalDistDict.keys():
                                    if m == matOptionName[j][k] and m != "Option":
                                        if "TITLE" in material.name:
                                            curjth.append(j+1)
                                        else:
                                            curjth.append(j)
                                        curkth.append(k)
                                        curname.append(m)
                        for j in range(len(curjth)):
                            avg = materialNormalDistDict[curname[j]][javg] 
                            std = materialNormalDistDict[curname[j]][jstd]
                            min = materialNormalDistDict[curname[j]][jmin]
                            max = materialNormalDistDict[curname[j]][jmax]
                            value = np.random.normal(avg,std) 
                            while value < min or value > max:
                                value = np.random.normal(avg,std)                                         
                            formatted_string = format(value, ">10.4e")
                            material.setIthJthKth(0,curjth[j], curkth[j], formatted_string)
                            outline += "," + str(value)
                        
                        #print("Material Normal Distribution for Sample: ", i+1, " Material ID: ", mkey, " is generated")
                        #materialNormalDistDict['Option']                    
                
                    material.write(outString)                
                outString.seek(0)                
                curMatString = outString.read()
                
                #outFile.write(curMatString)                
                
                # str(i+1) with 6-digit number
                svalue = str(i+1)
                svalue = svalue.zfill(8)
                
                for key in self.threePointBendingInputFile.keys():
                    folder_path = "3ptBending_" + str(key) + "_" + svalue
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)                                             
                    file_path = os.path.join(folder_path, '3ptBending_' + str(key) + "_" + svalue + '.k')
                    curImporter : KooDynaImporter = self.threePointBendingImporter[key]
                    curImporter.writeDynaFile(file_path,materialKeywords=curMatString)
                    outline += "," + file_path
                for key in self.impactInputFile.keys():
                    folder_path = "Impact_" + str(key) + "_" + svalue
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)                                             
                    file_path = os.path.join(folder_path, 'Impact_' + str(key) + "_" + svalue + '.k')
                    curImporter : KooDynaImporter = self.impactImporter[key]
                    curImporter.writeDynaFile(file_path,materialKeywords=curMatString)
                    outline += "," + file_path
                outFile.write(outline + "\n")
                if i%1000 == 0:
                    print("Material DOE for Sample: ", i+1, " is generated")
            print("Material DOE for Sample: ", i+1, " is generated")
                
                    
                    


        

        

        

if __name__ ==  "__main__":
    if len(sys.argv) < 2:
        sys.argv.clear()
        # set current directory D:\OpenCASCADE-7.7.0-vc14-64\pythonoccenv310\occProject\Generators\dist\KooOptimizer
        os.chdir("D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/occProject/Generators/dist/KooOptimizer")
        sys.argv.append("KooDynaDOEManager")
        sys.argv.append("LSDynaDOE.txt")
        #
        os.chdir("D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/occProject/Generators/dist/DisplayImpactBall")
        sys.argv.append("KooDynaDOEManager")
        sys.argv.append("LSDynaDOE.txt")
    



    dynaDOEManager = KooDynaDOEManager()
    curPath = os.getcwd()
    inName = sys.argv[1]
    inPath = os.path.join(curPath, inName)
    dynaDOEManager.importLSDynaDOEFile(inPath)
    dynaDOEManager.ImportMaterialDOE()
    dynaDOEManager.importModel()
    dynaDOEManager.GenerateMaterialLSDynaKeyword()
    dynaDOEManager.GenerateMaterialDOE(0)

