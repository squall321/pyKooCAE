import os
from KooSimulationGenerator import KooSimulationGenerator   
from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooSection import *  
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooSegment import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooContact import *
from KooCAEManager.KooDynaControl import *
from KooCAEManager.KooDamping import *

from KooCAEManager.KooDynaKeyword import *
from KooCAEManager.KooDynaResult import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH


class KooWearSimulationGenerator(KooSimulationGenerator):
    def __init__(self, dynaImporter : KooDynaImporter = None):
        if dynaImporter == None:
            nodeMan = NodeManager()
            nodeSetMan = NodeSetManager(nodeMan)
            secMan = KooSectionManager()
            matMan = KooMaterialManager()
            elemMan = ElementManager()
            partMan = KooPartManager()
            loadMan = KooLoadManager()
            boundaryNodeMan = KooBoundaryNodeManager()
            defineManager = KooDefineManager()
            contactMan = KooContactManager()
            segSetMan = KooSegmentSetManager()
            controlMan = KooControlManager()
            dampingMan = KooDampingManager()
            dynaResultManager = KooDynaResultManager(defineManager=defineManager,boundaryNodeManager=boundaryNodeMan)
            resultMan = KooResultManager(nodeMan)
            dynaImporter = KooDynaImporter(nodeMan,partMan,resultMan,matMan,secMan,nodeSetMan,loadMan,boundaryNodeMan,defineManager,contactMan,segSetMan,dynaResultManager,controlMan, dampingMan)    
        super().__init__(dynaImporter)
        self.dynaPath = ""
        self.batchFileName = "Start.bat"
    
 
    
    def ImportWearSimulationOption(self, fileName):
        filePath = os.path.join(self.curDir, fileName)
        
        with open(filePath, "r") as f:
            line = f.readline()
            line = line.replace('\n','')
            while True:
                if "*end" in line.lower():
                    break
                if "*inputfolder" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.inputFolder = line    
                if "*dynapath" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','') 
                    self.dynaPath = line
                if "*lsprepostpath" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.LSPrePostPath = line                    
                if "*batchfilename" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.batchFileName = line                                  
                if "*inputfilename" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.inputFileName = line
                if "*suffix" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.suffix = line
                if "*prefix" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.prefix = line
                if "*wearfilename" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.wearFileName = line
                if "*maxdistancelist" in line.lower():
                    line = f.readline()
                    line = line.replace('\n','')
                    self.maxDistanceList = []
                    while True:
                        if "*" in line.lower():
                            break                        
                        self.maxDistanceList.append(float(line))
                        line = f.readline()
                        line = line.replace('\n','')
                        
                    continue     
                line = f.readline()
                line = line.replace('\n','')
                if not line:
                    break
                
    def GenerateWearSimulationFiles(self):
        
        
        wearFileName = self.wearFileName
        #count # in wearFileName
        num = wearFileName.count("#")
        changeString = ""
        for i in range(num):
            changeString += "#"
        wearFileNameList = []
        for i in range(len(self.maxDistanceList)):
            # 4 digit number such as 0004 , 0153
            
            indigit = format(str(i).zfill(num))                        
            wearFileNameList.append(wearFileName.replace(changeString, indigit))
            
        for i in range(len(self.maxDistanceList)-1):
            # 4 digit number such as 0004 , 0153
            
            cfileName = curDir + "\\" + wearFileNameList[i] + ".cfile"
            with open(cfileName, "w") as f:
                inFilePath = os.path.join(self.curDir, wearFileNameList[i])
                dynain = os.path.join(inFilePath, "dynain")
                inFilePath = os.path.join(inFilePath, wearFileNameList[i])
                inFilePath += ".k"
                
                f.write("openc keyword \"" + inFilePath+ "\"\n")
                f.write("import keyword nooffset\n")
                f.write("import keyword \"" + dynain + "\"\n")
                f.write("save keywordoutversion 7\n")
                f.write("wear maxdist {wear}\n".format(wear = self.maxDistanceList[i]))
                f.write("wear compute\n")
                f.write("wear smooth\n")
                f.write("wear accept\n")
                nextName = os.path.join(self.curDir, wearFileNameList[i])
                nextName = os.path.join(nextName, wearFileNameList[i+1])
                nextName += ".k"
                f.write("save keyword \"{nextName}\"".format(nextName = nextName))                
                
                
        
        batchFilePath = os.path.join(self.curDir, self.batchFileName)
        with open(batchFilePath, "w") as f:
            f.write("cd " + self.curDir + "\n")
            for i in range(len(self.maxDistanceList)):
                f.write("mkdir " + wearFileNameList[i] + "\n") 
                if i == 0:
                    tmpInputPath = os.path.join(self.inputFolder, "tmpfile.k") 
                    self.dynaImporter.writeDynaFile(tmpInputPath)
                    #f.write("copy \"" + self.inputFolder + "\\" + self.inputFileName + "\" .\\" + wearFileNameList[i] + "\\" + wearFileNameList[i] +".k" + "\n")
                    f.write("copy \"" + tmpInputPath + "\" .\\" + wearFileNameList[i] + "\\" + wearFileNameList[i] +".k" + "\n")
                    
                else:
                    f.write("copy .\\" + wearFileNameList[i-1] + "\\" + wearFileNameList[i] + ".k" + " .\\" + wearFileNameList[i] + "\\" + wearFileNameList[i] + ".k" + "\n")
                f.write("copy \"" + self.inputFolder + "\\" + wearFileNameList[i] + ".cfile" + "\"" + " .\\" + wearFileNameList[i] + "\\" + wearFileNameList[i] + ".cfile" + "\n")
                    
                f.write("cd " + wearFileNameList[i] + "\n")
                lsrun = "\"" + self.dynaPath + "\" " + self.prefix
                lsrun += wearFileNameList[i] + ".k"
                lsrun += self.suffix
                lsrun += "\n"
                f.write(lsrun)
                lsprepost = "\"" + self.LSPrePostPath + "\"" + " -nographics c="
                lsprepost += wearFileNameList[i] + ".cfile"
                lsprepost += "\n"
                f.write(lsprepost)
                f.write("cd .." + "\n")
                
            
        pass 
                  
     
        

if __name__ == "__main__":
    curDir = "D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples\\3.WearSimulation\\WearAutomation"
    optionName = "WearSimulationAutomation.txt"  
    simGenerator : KooWearSimulationGenerator = KooWearSimulationGenerator()
    simGenerator.SetCurrentDirectory(curDir)
    simGenerator.ImportWearSimulationOption(optionName)
    simGenerator.ImportBaseFile()
    simGenerator.GenerateWearSimulationFiles()
    pass 