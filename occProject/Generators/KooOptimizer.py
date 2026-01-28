import os
import sys 
import numpy as np


from dynareadout import D3plot
from KooDynaDOEManager import KooDynaDOEManager
from KooRunSimulationManager import KooRunSimulationManager
from KooPostProcessManager import KooPostProcessManager

class KooOptimizationProcessor():
    def __init__(self):
        self.dynaDOEManager : KooDynaDOEManager = KooDynaDOEManager()        
        self.runSimManager : KooRunSimulationManager = KooRunSimulationManager() 
        self.postProcessor : KooPostProcessManager = KooPostProcessManager()
        pass 

    def RunDOEManager(self, infileName,numberofSamples=0):
        curPath = os.getcwd()
        inPath = os.path.join(curPath, infileName)
        self.dynaDOEManager.importLSDynaDOEFile(inPath)
        self.dynaDOEManager.ImportMaterialDOE()
        self.dynaDOEManager.importModel()        
        self.dynaDOEManager.GenerateMaterialLSDynaKeyword()
        self.dynaDOEManager.GenerateMaterialDOE(numberofSamples)
    
    def RunSimulationManager(self, infileName,numofBatchFile=1):
        curPath = os.getcwd()
        inPath = os.path.join(curPath, infileName)
        self.runSimManager.SetCurrentDirectory(curPath)
        self.runSimManager.ImportOption(inPath)
        self.runSimManager.Solve(numofBatchFile)        

    def RunPostProcessor(self, infileName,folderPath="", outputFileName="simOutput.txt"):
        if folderPath != "":
            curPath = folderPath
        else:
            curPath = os.getcwd()
        inPath = os.path.join(curPath, infileName)
        outPath = os.path.join(curPath, outputFileName)
        self.postProcessor.SetCurrentDirectory(curPath)
        self.postProcessor.SetOutputFileName(outPath)
        self.postProcessor.ImportOption(inPath)
        self.postProcessor.PostProcessor()



if __name__ == "__main__":
    if len(sys.argv) < 3:
        #Error 
        #Post Process
        curDir = os.getcwd()
        sys.argv.append("PostProcess")
        sys.argv.append("PostOption.txt")
        #sys.argv.append("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_DOE")        
        sys.argv.append(os.path.join(curDir,"occProject\\Generators\\dist\\KooOptimizer"))
        
        ##### Display DOE Example
        sys.argv.append(os.path.join(curDir,"occProject\\Generators\\dist\\DisplayImpact2"))
        
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")
        sys.argv.append("DOE")
        sys.argv.append("LSDynaDOE.txt")
        sys.argv.append("1")
        
        #### Post Processor Test Example
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")
        sys.argv.append("PostProcess")
        sys.argv.append("PostOption.txt")
        #sys.argv.append(os.path.join(curDir,"OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_DOE"))
        sys.argv.append(os.path.join(curDir,"occProject\\Generators\\dist\\KooOptimizer")) 
     
       
        ##### Display DOE Example
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\DisplayImpactBall"))
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")
        sys.argv.append("MakeBatch")
        sys.argv.append("SimulationOption.txt")
        sys.argv.append("1")
        
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\DisplayImpactBall"))
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")
        sys.argv.append("DOE")
        #sys.argv.append("LSDynaDOE.txt")
        sys.argv.append("LSDynaDOERefine.txt")
        sys.argv.append("1")
        
        os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples")
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")
        sys.argv.append("1.DisplayImpactBall_Peridynamics")
        sys.argv.append("DOE")        
        sys.argv.append("LSDynaDOERefine.txt")
        sys.argv.append("1")
               
        os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples\\1.DisplayImpactBallPeridynamics")
        
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")        
        sys.argv.append("DOEMakeBatch")
        sys.argv.append("LSDynaDOERefine.txt")
        sys.argv.append("1")
        sys.argv.append("SimulationOption.txt")
        sys.argv.append("1")


        os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples\\2.Display3ptBendingPeridynamics")
        
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")        
        sys.argv.append("DOEMakeBatch")
        sys.argv.append("LSDynaDOERefine.txt")
        sys.argv.append("1")
        sys.argv.append("SimulationOption.txt")
        sys.argv.append("1")
        
        os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples\\1.DisplayImpactBallPeridynamicsFine")
        sys.argv.clear()
        sys.argv.append("KooOptimizer.exe")        
        sys.argv.append("DOEMakeBatch")
        sys.argv.append("LSDynaDOERefine.txt")
        sys.argv.append("1")
        sys.argv.append("SimulationOption.txt")
        sys.argv.append("1")
        
        #exit(0)
    i = 1
    mode = sys.argv[i]
    if "DOE" in mode or "MakeBatch" in mode or "PostProcess" in mode:
        curDir = os.getcwd()
    else:
        curDir = os.getcwd()
        curDir = os.path.join(curDir,mode)
        os.chdir(curDir)        
        i = i + 1
        mode = sys.argv[i]
        
    i = i + 1
    processor = KooOptimizationProcessor()   
    if "DOE" in mode:
        inName = sys.argv[i]
        i = i + 1
        numberofSamples = int(sys.argv[i])                
        i = i + 1
        processor.RunDOEManager(inName,numberofSamples)
    if "MakeBatch" in mode:
        inName = sys.argv[i]
        i = i + 1
        numofBatchFile = int(sys.argv[i])
        i = i + 1
        processor.RunSimulationManager(inName,numofBatchFile)        
    if "PostProcess" in mode:
        inName = sys.argv[i]
        i = i + 1
        folderPath = sys.argv[i]
        i = i + 1
        if len(sys.argv) > i:
            outputFileName = sys.argv[i]            
        else:
            outputFileName = "simOutput.txt"

        processor.RunPostProcessor(inName,folderPath,outputFileName)
        
       
    