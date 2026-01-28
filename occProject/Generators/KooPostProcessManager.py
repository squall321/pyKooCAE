import os
import sys
import pyvista as pv
from pyvista import CellType

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from KooCAEManager.KooResult import *
from KooCAEManager.KooMeshImporter import *
from KooPostProcessor import *
from KooThreePointBendingSimulationGenerator import *

class KooPostProcessManager():
    def __init__(self):
        self.currentDirectory = os.getcwd() 
        self.solverTyper = "LSDyna"
        self.folderPrefix = ""
        self.inputFileName = None
        self.outputOptionDict = {}
        self.outputFileName = "simOutput.txt"
        
    
    def SetCurrentDirectory(self, path):
        self.currentDirectory = path
        pass

    def SetOutputFileName(self, name):
        self.outputFileName = name
        pass

    def ImportOption(self, path):
        file = open(path, 'r') 
        line = file.readline()
        line = line.replace('\n','')
        while True:
            if "*InputFile" in line:
                svector = line.split(',')
                self.inputFileName = svector[1]
            elif "*OutputOptionFile" in line:
                svector = line.split(',')
                if len(svector) > 2:
                    #self.outputOptionFileNameDict[svector[1]] = svector[2]                                                
                    if "3ptBending" in svector[1]:
                        threeptBSimulGen : KooThreePointBendingSimulationGenerator = KooThreePointBendingSimulationGenerator()                    
                        path = os.path.join(self.currentDirectory,svector[2])                        
                        self.outputOptionDict[svector[1]] = threeptBSimulGen.ImportLoadBoundaryOption(path)                        
                        
            line = file.readline()
            line = line.replace('\n','')
            if not line:
                break                    
        pass 

    def PostProcessor(self):
        searchFolder = self.currentDirectory
        i = 0
        file = open(self.outputFileName, "w")
        file.write("Model Name,Max Displacement,Min Displacement,Max Displacement X,Min Displacement X,Max Displacement Y,Min Displacement Y,Max Displacement Z,Min Displacement Z\n")

        for root, dirs, files in os.walk(searchFolder):                       
            
            for curDir in dirs:
                curDirName = curDir
                curDir = os.path.join(root, curDir)
                for subRoot, subDirs, subFiles in os.walk(curDir):
                    kFileName = "" 
                    nodoutFile = ""
                    eloutFile = ""
                    for subFile in subFiles:
                        if subFile.endswith("nodout"):
                            nodoutFile = os.path.join(curDir, subFile)                    
                            
                            pass
                        if subFile.endswith("elout"):
                            eloutFile = os.path.join(curDir, subFile)
                            pass
                        if subFile.endswith(".k"):
                            kFileName = os.path.join(curDir, subFile)
                            pass
                if kFileName != "":
                    nodeManager = NodeManager()
                    partManager = KooPartManager()
                    resultMan = KooResultManager(nodeManager)
                    importer = KooDynaImporter(nodeManager,partManager,resultMan)
                    importer.importDynaFile(kFileName,False)
                    importer.importNode()
                    importer.importPart()
                    print("Model Imported : ", kFileName)
                    if nodoutFile != "":
                        importer.importNODOUT(nodoutFile)
                        print("NODOUT Imported : ", nodoutFile)
                    if eloutFile != "":
                        importer.importELOUT(eloutFile)
                        print("ELOUT Imported : ", eloutFile)
                    maxDisp = nodeManager.MaxDisplacement()[1]
                    minDisp = nodeManager.MinDisplacement()[1]
                    maxDispX = nodeManager.MaxDisplacementX()[1]
                    minDispX = nodeManager.MinDisplacementX()[1]
                    maxDispY = nodeManager.MaxDisplacementY()[1]
                    minDispY = nodeManager.MinDisplacementY()[1]
                    maxDispZ = nodeManager.MaxDisplacementZ()[1]
                    minDispZ = nodeManager.MinDisplacementZ()[1]

                    file.write(curDirName +",")
                    file.write(str(maxDisp) + ",")
                    file.write(str(minDisp) + ",")
                    file.write(str(maxDispX) + ",")
                    file.write(str(minDispX) + ",")
                    file.write(str(maxDispY) + ",")
                    file.write(str(minDispY) + ",")
                    file.write(str(maxDispZ) + ",")
                    file.write(str(minDispZ) + "\n")


                        
                    #window = PostWindow(nodeManager, partManager)
                    #window.UpdateAllParts()
                    #window.UpdateColorVonMisesStress()
        file.close()            

        
                
if __name__ == "__main__":
    mode = "MSH"    
    mode = "DYNA"
    example = "BeamShellSolid"

    example = "3ptBendingShell"

    app = QApplication(sys.argv)
    if mode == "MSH":
        path = os.getcwd()
        path = os.path.join(path,'Example\\Model\\New_Model_1\\Solid4\\Solid4.msh')
        importer = KooMSHImporter()
        importer.import_msh_file(path)
    elif mode == "DYNA":
        path = os.getcwd()
        if example == "3ptBendingShell":
            path = os.path.join(path,'OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_DOE\\3ptBending_1_00000001')            
            inPath = os.path.join(path,"3ptBending_1_00000001.k")        
        elif example == "BeamShellSolid":
            path = os.path.join(path,'OpenRadioss\\examples\\ElasticBeam')
            inPath = os.path.join(path,"Elastic_Beams_etc.k")
        nodeManager = NodeManager()
        partManager = KooPartManager()
        resultMan = KooResultManager(nodeManager)
        importer = KooDynaImporter(nodeManager,partManager,resultMan)
        
        importer.importDynaFile(inPath)
        importer.importNode()
        importer.importPart()
        nodoutPath = os.path.join(path,"nodout")
        eloutPath = os.path.join(path,"elout")
        nodforPath = os.path.join(path,"nodfor")
        bndoutPath = os.path.join(path,"bndout")
        if os.path.exists(nodoutPath):
            importer.importNODOUT(nodoutPath)
        if os.path.exists(eloutPath):
            importer.importELOUT(eloutPath)                
        if os.path.exists(nodforPath):
            importer.importNODFOR(nodforPath)
        if os.path.exists(bndoutPath):
            importer.importBNDOUT(bndoutPath)
        
        window = PostWindow(nodeManager, partManager)
        maxDisp = nodeManager.MaxDisplacement()[1]
        minDisp = nodeManager.MinDisplacement()[1]
        maxDispX = nodeManager.MaxDisplacementX()[1]
        minDispX = nodeManager.MinDisplacementX()[1]
        maxDispY = nodeManager.MaxDisplacementY()[1]
        minDispY = nodeManager.MinDisplacementY()[1]
        maxDispZ = nodeManager.MaxDisplacementZ()[1]
        minDispZ = nodeManager.MinDisplacementZ()[1]
        print("Max Displacement: ", maxDisp)
        print("Min Displacement: ", minDisp)
        print("Max Displacement X: ", maxDispX)
        print("Min Displacement X: ", minDispX)
        print("Max Displacement Y: ", maxDispY)
        print("Min Displacement Y: ", minDispY)
        print("Max Displacement Z: ", maxDispZ)
        print("Min Displacement Z: ", minDispZ)

        for part in partManager.parts.values():
            elementManager : ElementManager = part.elementManager
            vonMises = elementManager.GetMaximumVonMisesStress()
            principal = elementManager.GetMaximumPrincipalStress()
            hydroStatic = elementManager.GetMaximumHydrostaticStress()
            print("Part ID: ", part.id)
            print("Max Von Mises Stress: ", vonMises)
            print("Max Principal Stress: ", principal)
            print("Max Hydrostatic Stress: ", hydroStatic)
        window.UpdateAllParts()
        window.UpdateColorVonMisesStress()
    sys.exit(app.exec_())
