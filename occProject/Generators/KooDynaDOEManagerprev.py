import os
import sys
from io import StringIO
import numpy as np 

from pyDOE import lhs

from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter
from KooCAEManager.KooDynaKeyword import *

class KooDynaDOEManager():
    
    def __init__(self):
        self.optimizationSimulationTool = "LSDYNA"
        self.currentDirectory = os.getcwd()        
        self.materialDOEFile = None
        self.outputFile = "input.txt"

        self.threePointBendingMode = "Simulation"
        self.threePointBendingInputFile = None
        self.threePointBendingOutputOption = None
        self.threePointBendingLength = 0.0 
        self.threePointBendingWidth = 0.0
        self.threePointBendingThickness = []
        self.threePointBendingMaterialIDList = []
        self.threePointBendingNodeManager : NodeManager = NodeManager()
        self.threePointBendingPartManager : KooPartManager = KooPartManager()
        self.threePointBendingImporter : KooDynaImporter = KooDynaImporter(self.threePointBendingNodeManager, self.threePointBendingPartManager)        
        
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
                    self.threePointBendingMode = svector[1]
                    print("3ptBending Mode: ", self.threePointBendingMode)
                    while True:
                        line = file.readline()
                        line = line.replace("\n","")
                        if line.find("*") != -1:
                            break
                        if "Length" in line:
                            svector = line.split(",")
                            self.threePointBendingLength = float(svector[1])
                            print("3ptBending Length: ", self.threePointBendingLength)
                        elif "Width" in line:
                            svector = line.split(",")
                            self.threePointBendingWidth = float(svector[1])
                            print("3ptBending Width: ", self.threePointBendingWidth)
                        elif "Thickness" in line:
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                self.threePointBendingThickness.append(float(svector[i]))
                            print("3ptBending Thickness: ", self.threePointBendingThickness)
                        elif "MaterialID" in line:
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                self.threePointBendingMaterialIDList.append(int(svector[i]))
                            print("3ptBending MaterialID: ", self.threePointBendingMaterialIDList)                            
                        elif "InputFile" in line:
                            svector = line.split(",")
                            inputFileName = svector[1]
                            path = os.path.join(self.currentDirectory, inputFileName)
                            self.threePointBendingInputFile = path
                            print("3ptBending InputFile: ", self.threePointBendingInputFile)
                        elif "OutputOption" in line:
                            svector = line.split(",")
                            self.threePointBendingOutputOption = svector[1]                 
                            print("3ptBending OutputOption: ", self.threePointBendingOutputOption)   
                else:
                    pass
                line = file.readline()
            file.close()

    def importModel(self):
        if self.optimizationSimulationTool == "LSDYNA":
            if self.threePointBendingInputFile is not None:
                print("Importing 3ptBending Model")
                self.threePointBendingImporter.importDynaFile(self.threePointBendingInputFile)
                self.threePointBendingImporter.importNode()
                self.threePointBendingImporter.importPart()
                self.threePointBendingImporter.SetELOUT()
                self.threePointBendingImporter.SetNODOUT()
                self.threePointBendingImporter.SetHistoryNodeforAll()
                self.threePointBendingImporter.SetHistoryElementforAll()
                print("3ptBending Model Imported")
            if self.tensileElasticInputFile is not None:
                print("Importing TensileElastic Model")
                self.tensileElasticImporter.importDynaFile(self.tensileElasticInputFile)
                self.tensileElasticImporter.importNode()
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

                folder_path = '3ptBending_' + svalue
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                
                file_path = os.path.join(folder_path, '3ptBending_' + svalue + '.k')
                self.threePointBendingImporter.writeDynaFile(file_path,curMatString)
                outline += "," + file_path
                outFile.write(outline + "\n")
                if i%1000 == 0:
                    print("Material DOE for Sample: ", i+1, " is generated")

                
                    
                    


        

        

        

if __name__ ==  "__main__":
    if len(sys.argv) < 2:
        sys.argv.clear()
        sys.argv.append("KooDynaDOEManager")
        sys.argv.append("LSDynaDOE.txt")
    



    dynaDOEManager = KooDynaDOEManager()
    curPath = os.getcwd()
    inName = sys.argv[1]
    inPath = os.path.join(curPath, inName)
    dynaDOEManager.importLSDynaDOEFile(inPath)
    dynaDOEManager.importModel()
    
    dynaDOEManager.ImportMaterialDOE()
    dynaDOEManager.GenerateMaterialLSDynaKeyword()
    dynaDOEManager.GenerateMaterialDOE(0)

