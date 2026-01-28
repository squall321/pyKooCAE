import os
import sys
#import pyvista as pv
#from pyvista import CellType
#from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
#from pyvistaqt import QtInteractor

from KooCAEManager.KooMeshImporter import *
from KooPostProcessor import *

class KooRunSimulationManager():
    def __init__(self):
        self.currentDirectory = os.getcwd()
        self.solverType = "LSDyna"
        self.folderPrefix = ""
        self.nCPU = 1
        self.memory = "10m"
        self.runFile = ""
        self.removeBinaryFile = False


    def SetCurrentDirectory(self, path):
        self.currentDirectory = path
    
    def ImportOption(self,path):
        with open(path, 'r') as file:
            line = file.readline()
            line = line.replace('\n','')    
            while True:
                if not line:
                    break 
                elif line[0] == '#':
                    pass
                elif "*Solver" in line:
                    svector = line.split(',')
                    self.solverType = svector[1]
                    line = file.readline()
                    line = line.replace('\n','')
                    self.runFile = line
                elif "*FolderPrefix" in line:
                    line = file.readline()
                    line = line.replace('\n','')
                    self.folderPrefix = line
                elif "*NCPU" in line:
                    svector = line.split(',')
                    self.nCPU = int(svector[1])
                elif "*Memory" in line:
                    svector = line.split(',')
                    self.memory = svector[1]
                elif "*RemoveBinary" in line:
                    svector = line.split(',')
                    if "True" in svector[1]:
                        self.removeBinaryFile = True
                    else:
                        self.removeBinaryFile = False


                line = file.readline()
                line = line.replace('\n','')
        pass 

    def Solve(self,size=1):
        
        searchFolder = self.currentDirectory
        #find all files with .k file
        #make bat file
        print("Make bat file for running simulation...") 
        
        batFilePath = [] 
        for i in range(size):
            batFilePath.append(os.path.join(searchFolder, "run{i}.bat".format(i=i)))
        
        batFileList = []
        for i in range(size):
            batFileList.append(open(batFilePath[i], "w"))
            batFileList[i].write("@echo off\n")
            batFileList[i].write("setlocal\n")

        i = 0 
       
        for root, dirs, files in os.walk(searchFolder):
            for file in files:
                if file.endswith(".k"):
                    kFile = file #os.path.join(root, file)
                    kFile = kFile.replace("/","\\")                        
                    #find folder name
                    folderName = os.path.basename(root)
                    if self.folderPrefix.lower() in folderName.lower():
                        pass
                    else:
                        continue
                    batFile = batFileList[i]
                    i = i + 1
                    if i >= size:
                        i = 0
                    batFile.write("set \"searchFolder=.\\" + folderName + "\"\n")
                    batFile.write("set \"searchFile=nodout\"\n")
                    batFile.write("dir /b /s \"%searchFolder%\%searchFile%\" >nul 2>&1\n")
                    batFile.write("if %errorlevel% == 0 (\n")
                    batFile.write("echo %searchFolder% was already analyzed !\n")
                    batFile.write(") else (\n")
                    #run solver
                    batFile.write("cd " + folderName + "\n")

                    #kFile = os.path.join(folderName,kFile)
                    if self.solverType == "LSDyna":
                        outstr = "" 
                        outstr += "\"{0}\"".format(self.runFile)
                        outstr += " i=" + "\""+ kFile + "\""
                        outstr += " ncpu=" + str(self.nCPU)
                        outstr += " memory=" + self.memory
                        batFile.write(outstr + "\n")
                        print("LSDyna - i=" + kFile + " ncpu=" + str(self.nCPU) + " memory=" + self.memory, " is added to run.bat")
                    elif self.solverType == "Radioss":                            
                        #os.system("radioss -s " + kFile + " -np " + str(self.nCPU) + " -nt 1 -memory " + self.memory)                            
                        pass
                    elif self.solverType == "Abaqus":
                        #os.system("abaqus job=" + kFile + " cpus=" + str(self.nCPU) + " memory=" + self.memory)
                        pass
                    else:
                        pass 
                    
                    if self.removeBinaryFile:
                        batFile.write("for /f \"delims=\" %%i in ('dir /b /a-d \"d3*\"') do (")
                        batFile.write("del \"%%i\"")
                        batFile.write(")\n")                                               

                    batFile.write("cd ..\n")
                    batFile.write(")\n")
            
        for i in range(size):
            batFileList[i].close()
            print("run{i}.bat".format(i=i) + " is created")
        pass

    def SolvePrev(self):
        
        searchFolder = self.currentDirectory
        #find all files with .k file
        #make bat file
        print("Make bat file for running simulation...") 
        batFilePath = os.path.join(searchFolder, "run.bat")        
        with open(batFilePath, "w") as batFile:
            batFile.write("@echo off\n")
            batFile.write("setlocal\n")
            for root, dirs, files in os.walk(searchFolder):
                for file in files:
                    if file.endswith(".k"):
                        kFile = file #os.path.join(root, file)
                        kFile = kFile.replace("/","\\")                        
                        #find folder name
                        folderName = os.path.basename(root)
                        if self.folderPrefix.lower() in folderName.lower():
                            pass
                        else:
                            continue
                        batFile.write("set \"searchFolder=.\\" + folderName + "\"\n")
                        batFile.write("set \"searchFile=nodout\"\n")
                        batFile.write("dir /b /s \"%searchFolder%\%searchFile%\" >nul 2>&1\n")
                        batFile.write("if %errorlevel% == 0 (\n")
                        batFile.write("echo %searchFolder% was already analyzed !\n")
                        batFile.write(") else (\n")
                        #run solver
                        batFile.write("cd " + folderName + "\n")

                        #kFile = os.path.join(folderName,kFile)
                        if self.solverType == "LSDyna":
                            outstr = "" 
                            outstr += "\"{0}\"".format(self.runFile)
                            outstr += " i=" + "\""+ kFile + "\""
                            outstr += " ncpu=" + str(self.nCPU)
                            outstr += " memory=" + self.memory
                            batFile.write(outstr + "\n")
                            print("LSDyna - i=" + kFile + " ncpu=" + str(self.nCPU) + " memory=" + self.memory, " is added to run.bat")
                        elif self.solverType == "Radioss":                            
                            #os.system("radioss -s " + kFile + " -np " + str(self.nCPU) + " -nt 1 -memory " + self.memory)                            
                            pass
                        elif self.solverType == "Abaqus":
                            #os.system("abaqus job=" + kFile + " cpus=" + str(self.nCPU) + " memory=" + self.memory)
                            pass
                        else:
                            pass 
                        
                        batFile.write("for /f \"delims=\" %%i in ('dir /b /a-d \"d3*\"') do (")
                        batFile.write("del \"%%i\"")
                        batFile.write(")\n")                                               

                        batFile.write("cd ..\n")
                        batFile.write(")\n")
            
            batFile.close()
        pass




if __name__ == "__main__":
    mode = "RunMode"        
    if mode == "RunMode":
        
        if len(sys.argv) < 2:
            sys.argv.clear()
            sys.argv.append("KooRunSimulationManager")
            sys.argv.append("SimulationOption.txt")
            sys.argv.append(1)


        curPath = os.getcwd()
        inName = sys.argv[1]
        inPath = os.path.join(curPath, inName)

        searchPath = "OpenRadioss/examples/Udemy_LSDYNA/3 pt bending test/test_DOE"
        searchPath = os.path.join(curPath, searchPath)
        
        runSimManager = KooRunSimulationManager()
        runSimManager.SetCurrentDirectory(searchPath)
        runSimManager.ImportOption(inPath)
        runSimManager.Solve(int(sys.argv[2]))
    