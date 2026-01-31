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
import math
import zipfile
import threading
import numpy as np
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Circ, gp_Ax2, gp_Elips
from OCC.Core.GC import GC_MakeArcOfCircle
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRep import BRep_Tool

from OCC.Core.TopoDS import topods
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Splitter
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID  
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.TopAbs import TopAbs_FACE

from OCC.Core.BRepFeat import BRepFeat_Gluer

if __name__ == '__main__':
    from Symbol import Symbol
else:
    from KooODBCADManager.Symbol import Symbol

class Layer: 
    def __init__(self, name="", thickness=0.1,udSymbolMap = {}):
        self.name = name         
        self.thickness = thickness       
        self.udSymbolMap = udSymbolMap 
        self.symbolMap = {} 

        self.patternXList = []
        self.patternYList = []
        self.patternSymbolIDList = []
        self.patternPolarityList = []
        self.patternClockwiseList = []   
        
        self.LayerCUStpList = [] 
        self.LayerPPGStpList = []

        self.row = 0
        self.context = ""
        self.type = "" 
        self.polarity = 1
        self.startName = ""
        self.endName = ""
        self.oldName = ""

    def CombinePatternofLayer(self, layer):
        self.patternXList.extend(layer.patternXList)
        self.patternYList.extend(layer.patternYList)
        self.patternSymbolIDList.extend(layer.patternSymbolIDList)
        self.patternPolarityList.extend(layer.patternPolarityList)
        self.patternClockwiseList.extend(layer.patternClockwiseList)
        self.udSymbolMap.update(layer.udSymbolMap)
        self.symbolMap.update(layer.symbolMap)

    def SetStartName(self, startName):
        self.startName = startName

    def SetEndName(self, endName):
        self.endName = endName

    def SetMatrixOption(self, row, context, type, name, polarity, startName,endName,oldName):
        self.row = row
        self.context = context
        self.type = type
        self.name = name
        self.polarity = polarity
        self.startName = startName
        self.endName = endName
        self.oldName = oldName    
                
    def ImportPatternfromODBFile(self, filePath):
        with open(filePath, 'r') as file:
            self.ImportPatternfromODBStream(file)


    def ImportPatternfromODBStringList(self, stringList):

        symbolID = [] 

        unit = 1.0/1000.0
        unit = 1.0
        tol = 1.0e-9

        curPolarity = 1
        
        
        for i in range(0,len(stringList)):        
            line = stringList[i]
            line = line.decode('utf-8')
            line = line.replace('\r\n','')
            line = line.replace('\n','')
            #print(line.strip())
            #byte to string
            if len(line) == 0:                
                continue


            
            string_vector = line.split(' ')
            firstString = string_vector[0]
            firstChar = firstString[0]
            secondChar = ""
            if len(firstString) > 1:
                secondChar = firstString[1]
            if firstChar == "U":
                if len(string_vector) == 1:
                    string_vector = line.split('=')
                if string_vector[1] == "MM":
                    unit = 1.0 / 1000.0
                    unit = 1.0
                else:    
                    unit = unit * 25.4#/1000.0
            elif firstChar == "$":
                string_vector[0] = string_vector[0].replace("$","")
                symbolName = string_vector[1]
                symbolName.lower()
                symbolID.append(int(string_vector[0].replace("$","")))

                if symbolName in self.udSymbolMap:
                    aSymbol = self.udSymbolMap[symbolName]
                else:
                    aSymbol = Symbol(symbolName)
                    curunit = unit*0.001
                    aSymbol.SetSymbol(symbolName,curunit)                        
                self.symbolMap.update({symbolID[-1]:aSymbol})
            elif firstChar == "S":
                pass
            elif firstChar == "P":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                
                xi = unit * float(string_vector[1])
                yi = unit * float(string_vector[2])                    
                symbolid = int(string_vector[3])

                xVec = [] 
                yVec = []
                xVec.append(xi)
                yVec.append(yi)
                self.patternSymbolIDList.append(symbolid)
                self.patternXList.append(xVec)
                self.patternYList.append(yVec)
                self.patternPolarityList.append(curPolarity)
                self.patternClockwiseList.append([])

            elif firstChar == "L":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                xi = unit * float(string_vector[1])
                yi = unit * float(string_vector[2])
                xf = unit * float(string_vector[3])
                yf = unit * float(string_vector[4])
                symbolid = int(string_vector[5])

                xVec = []
                yVec = []
                xVec.append(xi)
                xVec.append(xf)
                yVec.append(yi)
                yVec.append(yf)
                self.patternSymbolIDList.append(symbolid)
                self.patternXList.append(xVec)
                self.patternYList.append(yVec)
                self.patternPolarityList.append(curPolarity)
                self.patternClockwiseList.append([])
            elif firstChar == "A":
                if "N" in line:
                    curPolarity = 0
                else:
                    curPolarity = 1
                xi = unit * float(string_vector[1])
                yi = unit * float(string_vector[2])
                xf = unit * float(string_vector[3])
                yf = unit * float(string_vector[4])
                xc = unit * float(string_vector[5])
                yc = unit * float(string_vector[6])
                symbolid = int(string_vector[7])

                xVec = []
                yVec = []
                xVec.append(xi)
                xVec.append(xf)
                xVec.append(xc)
                yVec.append(yi)
                yVec.append(yf)
                yVec.append(yc)
                self.patternSymbolIDList.append(symbolid)
                self.patternXList.append(xVec)
                self.patternYList.append(yVec)
                self.patternPolarityList.append(curPolarity)
                self.patternClockwiseList.append([])

            elif "OB" in line:
                if firstChar != "O" or secondChar != "B":
                    continue

                xStart = unit * float(string_vector[1])
                yStart = unit * float(string_vector[2])
                xMat = []
                yMat = []
                cwList = []
                while True:
                    i = i + 1
                    line = stringList[i]
                    line = line.decode('utf-8')
                    line = line.replace('\r\n','')
                    line = line.replace('\n','')

                    if "OE" in line:
                        break
                    string_vector = line.split(' ')
                    if "OC" in line:
                        xEnd = unit * float(string_vector[1])
                        yEnd = unit * float(string_vector[2])
                        xCenter = unit * float(string_vector[3])
                        yCenter = unit * float(string_vector[4])
                        cw = string_vector[5].strip().lower()
                        if cw == "y":
                            cwList.append(1)
                        else:
                            cwList.append(0)
                        xMat.append([xStart, xEnd, xCenter])
                        yMat.append([yStart, yEnd, yCenter])
                        xStart = xEnd
                        yStart = yEnd
                    else:
                        xEnd = unit * float(string_vector[1])
                        yEnd = unit * float(string_vector[2])
                        cwList.append(None)
                        xMat.append([xStart, xEnd])
                        yMat.append([yStart, yEnd])
                        xStart = xEnd
                        yStart = yEnd
                self.patternXList.append(xMat)
                self.patternYList.append(yMat)
                self.patternSymbolIDList.append(-1)
                self.patternPolarityList.append(curPolarity)
                self.patternClockwiseList.append(cwList)
        return len(self.patternXList)
        
    def ImportPatternfromODBStream(self, file):

        symbolID = [] 

        unit = 1.0/1000.0
        unit = 1.0
        tol = 1.0e-9

        curPolarity = 1
        try:
            line = file.readline()
            line = line.decode('utf-8')
            line = line.replace('\r\n','')
            line = line.replace('\n','')
            while file._eof == False:
                #print(line.strip())
                #byte to string
                if len(line) == 0:
                    line = file.readline()
                    line = line.decode('utf-8')
                    line = line.replace('\r\n','')
                    line = line.replace('\n','')

                
                string_vector = line.split(' ')
                firstString = string_vector[0]
                firstChar = firstString[0]
                secondChar = ""
                if len(firstString) > 1:
                    secondChar = firstString[1]
                if firstChar == "U":
                    if string_vector[1] == "MM":
                        unit = 1.0 / 1000.0
                        unit = 1.0
                    else:    
                        unit = unit * 25.4#/1000.0
                elif firstChar == "$":
                    string_vector[0] = string_vector[0].replace("$","")
                    symbolName = string_vector[1]
                    symbolName.lower()
                    symbolID.append(int(string_vector[0].replace("$","")))

                    if symbolName in self.udSymbolMap:
                        aSymbol = self.udSymbolMap[symbolName]
                    else:
                        aSymbol = Symbol(symbolName)
                        curunit = unit*0.001
                        aSymbol.SetSymbol(symbolName,curunit)                        
                    self.symbolMap.update({symbolID[-1]:aSymbol})
                elif firstChar == "S":
                    pass
                elif firstChar == "P":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    
                    xi = unit * float(string_vector[1])
                    yi = unit * float(string_vector[2])                    
                    symbolid = int(string_vector[3])

                    xVec = [] 
                    yVec = []
                    xVec.append(xi)
                    yVec.append(yi)
                    self.patternSymbolIDList.append(symbolid)
                    self.patternXList.append(xVec)
                    self.patternYList.append(yVec)
                    self.patternPolarityList.append(curPolarity)
                    self.patternClockwiseList.append([])

                elif firstChar == "L":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    xi = unit * float(string_vector[1])
                    yi = unit * float(string_vector[2])
                    xf = unit * float(string_vector[3])
                    yf = unit * float(string_vector[4])
                    symbolid = int(string_vector[5])

                    xVec = []
                    yVec = []
                    xVec.append(xi)
                    xVec.append(xf)
                    yVec.append(yi)
                    yVec.append(yf)
                    self.patternSymbolIDList.append(symbolid)
                    self.patternXList.append(xVec)
                    self.patternYList.append(yVec)
                    self.patternPolarityList.append(curPolarity)
                    self.patternClockwiseList.append([])
                elif firstChar == "A":
                    if "N" in line:
                        curPolarity = 0
                    else:
                        curPolarity = 1
                    xi = unit * float(string_vector[1])
                    yi = unit * float(string_vector[2])
                    xf = unit * float(string_vector[3])
                    yf = unit * float(string_vector[4])
                    xc = unit * float(string_vector[5])
                    yc = unit * float(string_vector[6])
                    symbolid = int(string_vector[7])

                    xVec = []
                    yVec = []
                    xVec.append(xi)
                    xVec.append(xf)
                    xVec.append(xc)
                    yVec.append(yi)
                    yVec.append(yf)
                    yVec.append(yc)
                    self.patternSymbolIDList.append(symbolid)
                    self.patternXList.append(xVec)
                    self.patternYList.append(yVec)
                    self.patternPolarityList.append(curPolarity)
                    self.patternClockwiseList.append([])

                elif "OB" in line:
                    if firstChar != "O" or secondChar != "B":
                        line = file.readline()
                        line = line.decode('utf-8')
                        line = line.replace('\r\n','')
                        line = line.replace('\n','')
                        break

                    xStart = unit * float(string_vector[1])
                    yStart = unit * float(string_vector[2])
                    xMat = []
                    yMat = []
                    cwList = []
                    while True:
                        line = file.readline()
                        line = line.decode('utf-8')
                        line = line.replace('\r\n','')
                        line = line.replace('\n','')

                        if "OE" in line:
                            break
                        string_vector = line.split(' ')
                        if "OC" in line:
                            xEnd = unit * float(string_vector[1])
                            yEnd = unit * float(string_vector[2])
                            xCenter = unit * float(string_vector[3])
                            yCenter = unit * float(string_vector[4])
                            cw = string_vector[5].strip().lower()
                            if cw == "y":
                                cwList.append(1)
                            else:
                                cwList.append(0)
                            xMat.append([xStart, xEnd, xCenter])
                            yMat.append([yStart, yEnd, yCenter])
                            xStart = xEnd
                            yStart = yEnd
                        else:
                            xEnd = unit * float(string_vector[1])
                            yEnd = unit * float(string_vector[2])
                            cwList.append(None)
                            xMat.append([xStart, xEnd])
                            yMat.append([yStart, yEnd])
                            xStart = xEnd
                            yStart = yEnd
                    self.patternXList.append(xMat)
                    self.patternYList.append(yMat)
                    self.patternSymbolIDList.append(-1)
                    self.patternPolarityList.append(curPolarity)
                    self.patternClockwiseList.append(cwList)
                line = file.readline()
                line = line.decode('utf-8')
                line = line.replace('\r\n','')
                line = line.replace('\n','')
        except:
            print("Error in reading the file")
            

class PrintedCircuitBoard():
    def __init__(self):
        self.features = []
        self.layers = [] 
        self.layerFilePaths = [] 
        self.udSymbolMap = {}
        self.aislayers = []
        self.LayerSolderMaskStpList = [] 
        self.LayerSolderPasteStpList = []
    
    def ClearLayer(self):
        self.features = []
        self.layers = [] 
        self.layerFilePaths = []    

    def AddLayer(self, layerName, thickness, layerFilePath):
        layer = Layer(layerName, thickness, self.udSymbolMap)
        self.layers.append(layer)
        self.layerFilePaths.append(layerFilePath)        
        layer.ImportPatternfromODBFile(layerFilePath)

    def SetUserDefinedSymbol(self, symbolPath):
        # in the symbolPath, there are many folders which have 
        current_directory = os.getcwd()
        symbolPath = os.path.join(current_directory,symbolPath)

        for root, dirs, files in os.walk(symbolPath):
            for file in files:
                file_path = os.path.join(root, file)
                
                print("File:", file_path)
                if file == "features":
                    symbolName = file_path.replace(symbolPath,"")
                    symbolName = symbolName.replace("\\","")
                    symbolName = symbolName.replace("features","")                    
                # read the features file    
                    with open(file_path, 'r') as stream:
                        aSymbol : Symbol = Symbol(symbolName)                        
                        self.udSymbolMap[symbolName] = aSymbol
                        aSymbol.ImportSymbols(file_path, self.udSymbolMap)        
    def AddUserDefinedSymbol(self, symbolName, symbolLines):
        aSymbol : Symbol = Symbol(symbolName)
        self.udSymbolMap[symbolName] = aSymbol
        aSymbol.ImportSymbolsfromLines(symbolLines, self.udSymbolMap)
        print("Symbol ", symbolName, " is added.")
 
    def ImportMatrix(self, config_text):
        layers = [] 
        features = [] 
        layer_sections = config_text.split('LAYER {')[1:]

        for section in layer_sections:
            section = section.replace("}","")
            section = section.replace(" ","")
            section = section.replace("\t","")
            section = section.strip()
            layerRow = 0 
            layerContext = ""
            layerType = ""
            layerName = ""
            layerPolairty = 1
            layerStartName = ""
            layerEndName = ""
            layerOldName = ""

            sectionVector = section.split('\n')
            for eachSection in sectionVector:
                keyContents = eachSection.split('=')
                if len(keyContents) == 2:
                    if keyContents[0] == "ROW":
                        layerRow = int(keyContents[1])
                    elif keyContents[0] == "CONTEXT":
                        layerContext = keyContents[1]
                    elif keyContents[0] == "TYPE":
                        layerType = keyContents[1]
                    elif keyContents[0] == "NAME":
                        layerName = keyContents[1]
                    elif keyContents[0] == "POLARITY":
                        if keyContents[1] == "NEGATIVE":
                            layerPolarity = 0
                        else:
                            layerPolarity = 1
                    elif keyContents[0] == "START_NAME":
                        layerStartName = keyContents[1]
                    elif keyContents[0] == "END_NAME":
                        layerEndName = keyContents[1]
                    elif keyContents[0] == "OLD_NAME":
                        layerOldName = keyContents[1]
            # Create a Layer object and append it to the list
            layerName = layerName.lower()
            layer = Layer(layerName,0.1,self.udSymbolMap)
            layers.append(layer)
            layer.SetMatrixOption(layerRow,layerContext,layerType,layerName,layerPolarity,layerStartName,layerEndName,layerOldName)

            feature = Layer(layerName,0.1,self.udSymbolMap)
            features.append(feature)

            print(layerName," layer is added.")
        
        for layer in layers:             
            self.layers.append(layer)
        for feature in features:
            self.features.append(feature)

    def ImportODBZipExternalGeometry(self, odbPath):
        feature = Layer("ExternalGeometry",0.1)
        nameList = [] 
        with zipfile.ZipFile(odbPath,'r') as zip_file:
            #sort by name 
            zip_file.namelist().sort()
            if "matrix/matrix" in zip_file.namelist():
                file_name = "matrix/matrix"
                with zip_file.open(file_name, 'r') as file:                    
                    contents = file.readlines()
                    print(file_name)                    
                    print("matrix file found")
                    #contents as a string list
                    contents = [x.decode('utf-8') for x in contents]                            

                    contents = " ".join(contents)
                    contents = contents.replace("\r","")
                    self.ImportMatrix(contents)
            thickness = [] 
            
            for file_name in zip_file.namelist():                 
                with zip_file.open(file_name, 'r') as file:                    
                    if "steps/pcb/profile" in file_name or "steps/mentor/profile" in file_name:
                        file.close()
                        print("Import profile data...")
                        
                        #contents = file.readlines()
                        with zip_file.open(file_name, 'r') as file2:           
                            file2String = file2.readlines()
                            size = feature.ImportPatternfromODBStringList(file2String)                   
                            file2.close()
                        pass 
                    elif "features" in file_name:                        
                        if "steps/pcb/layers/" in file_name or "steps/mentor/layers/" in file_name:
                            pass
                        else:
                            continue
                        #print("File Name : ", file_name)
                        layerName = file_name.replace("steps/pcb/layers/","")
                        layerName = layerName.replace("steps/mentor/layers/","")
                        layerName = layerName.replace("/features","")
                        #print("Layer Name : ", layerName)
                        for curLayer in self.layers:
                            if layerName.lower() == curLayer.name.lower():
                                layer : Layer = curLayer                                
                                print("Layer", layerName, "is found.")
                                layer.ImportPatternfromODBStream(file)

                    file.close()
            self.SetAISLayers(0,thickness,0.0,0.0)
            for i in range(len(self.aislayers)):
                nameList.append(self.aislayers[i].layer.name)
        return feature.patternXList, feature.patternYList, feature.patternSymbolIDList, feature.patternPolarityList, nameList

    def ImportODBZip(self, odbPath):
        with zipfile.ZipFile(odbPath,'r') as zip_file:
            #sort by name 
            zip_file.namelist().sort()
            for file_name in zip_file.namelist():          
                if "symbols" in file_name:
                    symbolName = file_name.replace("symbols/","")                    
                    symbolName = symbolName.replace("/features","")
                    if "/features" in file_name: 
                        
                        with zip_file.open(file_name, 'r') as file:
                            contents = file.readlines()
                            contents = [x.decode('utf-8') for x in contents]                                                        
                            self.AddUserDefinedSymbol(symbolName, contents)
                    #self.SetUserDefinedSymbol("symbols")
                    
                 
            if "matrix/matrix" in zip_file.namelist():
                file_name = "matrix/matrix"
                with zip_file.open(file_name, 'r') as file:                    
                    contents = file.readlines()
                    print(file_name)                    
                    print("matrix file found")
                    #contents as a string list
                    contents = [x.decode('utf-8') for x in contents]                            

                    contents = " ".join(contents)
                    contents = contents.replace("\r","")
                    self.ImportMatrix(contents)
            for file_name in zip_file.namelist():                 
                with zip_file.open(file_name, 'r') as file:                    
                    
                    '''if "matrix/matrix" in file_name:
                        contents = file.readlines()
                        print(file_name)                    
                        print("matrix file found")
                        #contents as a string list
                        contents = [x.decode('utf-8') for x in contents]                            

                        contents = " ".join(contents)
                        contents = contents.replace("\r","")
                        self.ImportMatrix(contents)
                    el'''
                    if "steps/pcb/profile" in file_name or "steps/mentor/profile" in file_name:
                        file.close()
                        print("Import profile data...")
                        for curFeature in self.features:
                            feature : Layer = curFeature
                            #contents = file.readlines()
                            with zip_file.open(file_name, 'r') as file2:           
                                file2String = file2.readlines()
                                size = feature.ImportPatternfromODBStringList(file2String)
                                print("Layer : ",curFeature.name , "Number of patterns in ", file_name, " : ", size)
                                file2.close()
                        pass 

                    elif "features" in file_name:                        
                        if "steps/pcb/layers/" in file_name or "steps/mentor/layers/" in file_name:
                            pass
                        else:
                            continue
                        #print("File Name : ", file_name)
                        layerName = file_name.replace("steps/pcb/layers/","")
                        layerName = layerName.replace("steps/mentor/layers/","")
                        layerName = layerName.replace("/features","")
                        #print("Layer Name : ", layerName)
                        for curLayer in self.layers:
                            if layerName.lower() == curLayer.name.lower():
                                layer : Layer = curLayer                                
                                print("Layer", layerName, "is found.")
                                layer.ImportPatternfromODBStream(file)

                    file.close()

    def SetAISLayers(self,zLocation = 0.0,thicknessList = [],thicknessSolderPaste = 0.0, thicknessSolderMask = 0.0):
        self.aislayers = [] 
        self.aisfeatures = [] 
        self.aisSolderMaskFeatures = [] 
        self.aisSolderPasteFeatures = []
        layerList = [] 
        featureList = [] 
        self.aisSolderPastelayers = []
        self.aisSolderMaskLayers = []
        solderPasteLayerList = [] 
        solderMaskLayerList = [] 
        
        
        solderPasteFeatureList = [] 
        solderMaskFeatureList = []
        for i in range(len(self.layers)):
            layer = self.layers[i]
            if layer.type == "SIGNAL":
                layerList.append(layer)                
            elif layer.type == "SOLDER_PASTE":
                solderPasteLayerList.append(layer)
                #solderPasteFeatureList.append(self.features[i])                
            elif layer.type == "SOLDER_MASK":
                solderMaskLayerList.append(layer)
                #solderMaskFeatureList.append(self.features[i])

        j = 0
        for i in range(1,len(layerList)):
            ppgLayer : Layer = Layer("ppg{}_{}".format(i-1,i),0.1,self.udSymbolMap)
            ppgLayer.SetStartName(layerList[i-1].name)
            ppgLayer.SetEndName(layerList[i].name)
            layerList.insert(i+j,ppgLayer)
            j = j + 1
        print("LayerName StartName EndName")
        for i in range(0,len(layerList)):
            print(layerList[i].name,layerList[i].startName,layerList[i].endName)

        for i in range(len(layerList)):
            feature = self.features[i]
            featureList.append(feature)
        for i in range(len(layerList),len(layerList)+2):
            feature = self.features[i]
            solderPasteFeatureList.append(feature)
        for i in range(len(layerList)+2,len(layerList)+4):
            feature = self.features[i]
            solderMaskFeatureList.append(feature)
        

        for layer in self.layers: 
            if layer.type == "DRILL":
                starti = -1
                endi = -1
                i = 0
                for curLayer in layerList:
                    if curLayer.name.lower() == layer.startName.lower():
                        starti = i
                    elif curLayer.name.lower() == layer.endName.lower():
                        endi = i
                    i = i + 1
                if starti != -1 and endi != -1:
                    for i in range(starti,endi):
                        ppgLayer : Layer = layerList[i]
                        ppgLayer.CombinePatternofLayer(layer)

        if len(thicknessList) > 0:
            size = len(thicknessList)
            if size > len(layerList):
                size = len(layerList)
            for i in range(size):
                layer : Layer = layerList[i]
                layer.thickness = thicknessList[i]
                feature : Layer = featureList[i]
                feature.thickness = thicknessList[i]
            if len(thicknessList) < len(layerList):
                for i in range(len(thicknessList),len(layerList)):
                    layer : Layer = layerList[i]
                    layer.thickness = thicknessList[-1]
                    feature : Layer = featureList[i]
                    feature.thickness = thicknessList[-1]
        if thicknessSolderPaste > 0.0:
            for i in range(len(solderPasteLayerList)):
                solderPasteLayer : Layer = solderPasteLayerList[i]                
                solderPasteLayer.thickness = thicknessSolderPaste
                solderPasteFeature : Layer = solderPasteFeatureList[i]
                solderPasteFeature.thickness = thicknessSolderPaste
        if thicknessSolderMask > 0.0:
            for i in range(len(solderMaskLayerList)):
                solderMaskLayer : Layer = solderMaskLayerList[i]
                solderMaskLayer.thickness = thicknessSolderMask
                solderMaskFeature : Layer = solderMaskFeatureList[i]
                solderMaskFeature.thickness = thicknessSolderMask
                
                
        zPos = zLocation
        
        if thicknessSolderPaste > 0.0:
            if len(solderPasteLayerList) > 0:
                solderPasteLayer = solderPasteLayerList[0]
                aisLayer : AISLayer = AISLayer(solderPasteLayer,zPos)
                zPos = zPos + solderPasteLayer.thickness
                self.aisSolderPastelayers.append(aisLayer)
        if thicknessSolderMask > 0.0:
            if len(solderMaskLayerList) > 0:
                solderMaskLayer = solderMaskLayerList[0]
                zPos = zPos - thicknessSolderMask
                aisLayer : AISLayer = AISLayer(solderMaskLayer,zPos)
                zPos = zPos + solderMaskLayer.thickness
                self.aisSolderMaskLayers.append(aisLayer)
        for layer in layerList:
            aisLayer : AISLayer = AISLayer(layer,zPos)
            self.aislayers.append(aisLayer) 
            zPos = zPos + layer.thickness
        
        if thicknessSolderMask > 0.0:
            if len(solderMaskLayerList) > 1:
                solderMaskLayer = solderMaskLayerList[1]
                aisLayer : AISLayer = AISLayer(solderMaskLayer,zPos)
                zPos = zPos + solderMaskLayer.thickness            
                self.aisSolderMaskLayers.append(aisLayer)
        if thicknessSolderPaste > 0.0:
            if len(solderPasteLayerList) > 1:
                solderPasteLayer = solderPasteLayerList[1]
                zPos = zPos - thicknessSolderMask
                aisLayer : AISLayer = AISLayer(solderPasteLayer,zPos)
                zPos = zPos + solderPasteLayer.thickness
                self.aisSolderPastelayers.append(aisLayer)
        
            
        zPos = zLocation
        if thicknessSolderMask > 0.0:
            solderMaskLayer = solderMaskLayerList[0]              
            aisFeature : AISLayer = AISLayer(solderMaskFeatureList[0],zPos)
            self.aisSolderMaskFeatures.append(aisFeature)
            zPos = zPos + solderMaskLayer.thickness        
            
        if thicknessSolderPaste > 0.0:
            solderPasteLayer = solderPasteLayerList[0]            
            if thicknessSolderMask > 0.0:
                aisFeature : AISLayer = AISLayer(solderPasteFeatureList[0],zPos - solderMaskLayer.thickness)
                self.aisSolderPasteFeatures.append(aisFeature)
            else:
                aisFeature : AISLayer = AISLayer(solderPasteFeatureList[0],zPos)
                self.aisSolderPasteFeatures.append(aisFeature)
                zPos = zPos + solderPasteLayer.thickness
                                            
        for feature in featureList:
            aisFeature : AISLayer = AISLayer(feature,zPos)
            self.aisfeatures.append(aisFeature)
            zPos = zPos + feature.thickness
        
        if thicknessSolderMask > 0.0:
            if len(solderMaskFeatureList) > 1:
                solderMaskFeature = solderMaskFeatureList[1]
                aisFeature : AISLayer = AISLayer(solderMaskFeature,zPos)
                self.aisSolderMaskFeatures.append(aisFeature)
                zPos = zPos + solderMaskFeature.thickness
        
        if thicknessSolderPaste > 0.0:
            if len(solderPasteFeatureList) > 1:
                solderPasteFeature = solderPasteFeatureList[1]
                if thicknessSolderMask > 0.0:
                    aisFeature : AISLayer = AISLayer(solderPasteFeature,zPos - solderMaskFeature.thickness)
                    self.aisSolderPasteFeatures.append(aisFeature)
                else:
                    aisFeature : AISLayer = AISLayer(solderPasteFeature,zPos)
                    self.aisSolderPasteFeatures.append(aisFeature)
                    zPos = zPos + solderPasteFeature.thickness
                
        
        
            
        

    def SetAISLayersOriginal(self,zLocation = 0.0,thicknessList = []):
        self.aislayers = [] 
        self.aisfeatures = [] 
        layerList = [] 
        featureList = [] 
        for layer in self.layers:
            if layer.type == "SIGNAL":
                layerList.append(layer)
        for i in range(len(self.layers)):
            layer = self.layers[i]
            if layer.type == "SIGNAL":
                feature = self.features[i]
                featureList.append(feature)
        
        for layer in self.layers: 
            if layer.type == "DRILL":
                i = 1
                for curLayer in layerList:
                    if curLayer.name.lower() == layer.startName.lower():
                        layerList.insert(i,layer)
                        break
                    i = i + 1
        for j in range(len(self.layers)):
            layer = self.layers[j]
            feature = self.features[j]
            if layer.type == "DRILL":
                i = 1
                for curLayer in layerList:
                    if curLayer.name.lower() == layer.endName.lower():
                        featureList.insert(i,feature)
                        break
                    i = i + 1

        if len(thicknessList) > 0:
            for i in range(len(thicknessList)):
                layer : Layer = layerList[i]
                layer.thickness = thicknessList[i]
                feature : Layer = featureList[i]
                feature.thickness = thicknessList[i]
            
        zPos = zLocation
        for layer in layerList:
            aisLayer : AISLayer = AISLayer(layer,zPos)
            self.aislayers.append(aisLayer) 
            zPos = zPos + layer.thickness
        zPos = zLocation
        for feature in featureList:
            aisFeature : AISLayer = AISLayer(feature,zPos)
            self.aisfeatures.append(aisFeature)
            zPos = zPos + feature.thickness

    def ExportEachShape(self, fileName, shape):
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        step_writer = STEPControl_Writer()
        step_writer.Transfer(shape, STEPControl_AsIs)
        status = step_writer.Write(fileName)
        print("Exporting STEP file is done.")       

    def ExportShapeArea(self, fileName, xmin, ymin, xmax, ymax, skipLayerList=None):
        if skipLayerList is None:
            skipLayerList = []
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        print("Generate Solder Mask and Paste")
        if len(self.aisSolderMaskLayers) > 0:
            solderMaskShape = self.GenerateSolderMask(xmin,ymin,xmax,ymax)
            print("Solder Mask Shape is generated")
        else:
            solderMaskShape = []
            print("No Solder Mask Shape is generated")
                
        if len(self.aisSolderPastelayers) > 0:
            solderPasteShape = self.GenerateSolderPaste(xmin,ymin,xmax,ymax)
            print("Solder Paste Shape is generated")
        else:
            solderPasteShape = []
            print("No Solder Paste Shape is generated")
            
        print("Generate PPG and CU")
        originalShape, cushapeList, ppgshapeList = self.GeneratePPG(xmin,ymin,xmax,ymax, skipLayerList)
        print("PPG and CU Shape is generated")
        #shapeList = self.GeneratePPGMultiThread(xmin,ymin,xmax,ymax)
        for shape in originalShape:
            if shape is not None:
                builder.Add(compound,shape)
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        step_writer = STEPControl_Writer()
        step_writer.Transfer(compound, STEPControl_AsIs)
        status = step_writer.Write(fileName)                
        print("Exporting STEP file is done.")
        
        builderCU = BRep_Builder()
        builderPPG = BRep_Builder()
        compoundCU = TopoDS_Compound()
        compoundPPG = TopoDS_Compound()
        builderCU.MakeCompound(compoundCU)
        builderPPG.MakeCompound(compoundPPG)
        for shape in cushapeList:
            if shape is not None:
                builderCU.Add(compoundCU,shape)
        for shape in ppgshapeList:
            if shape is not None:
                builderPPG.Add(compoundPPG,shape)
        
        stepWriterCU = STEPControl_Writer()
        stepWriterPPG = STEPControl_Writer()    
        stepWriterCU.Transfer(compoundCU, STEPControl_AsIs)
        status = stepWriterCU.Write(fileName.replace(".stp","_CU.stp"))
        stepWriterPPG.Transfer(compoundPPG, STEPControl_AsIs)
        status = stepWriterPPG.Write(fileName.replace(".stp","_PPG.stp"))
        
        if len(solderMaskShape) > 0:
            builderSM = BRep_Builder()
            compoundSM = TopoDS_Compound()
            builderSM.MakeCompound(compoundSM)
            for shape in solderMaskShape:
                if shape is not None:
                    builderSM.Add(compoundSM,shape)
            stepWriterSM = STEPControl_Writer()
            stepWriterSM.Transfer(compoundSM, STEPControl_AsIs)
            status = stepWriterSM.Write(fileName.replace(".stp","_SM.stp"))
        if len(solderPasteShape) > 0:
            builderSP = BRep_Builder()
            compoundSP = TopoDS_Compound()
            builderSP.MakeCompound(compoundSP)
            for shape in solderPasteShape:
                if shape is not None:
                    builderSP.Add(compoundSP,shape)
            stepWriterSP = STEPControl_Writer()
            stepWriterSP.Transfer(compoundSP, STEPControl_AsIs)
            status = stepWriterSP.Write(fileName.replace(".stp","_SP.stp"))
                    
        print("Exporting STEP file is done.")
        dx = xmax - xmin
        dy = ymax - ymin
        davg = (dx + dy) / 2.0 / 50.0
        meshfileInfo = fileName.replace(".stp","_mesh.txt")
        with open(meshfileInfo, 'w') as file:
            file.write("*Layer,CircuitPattern\n")
            file.write("Location,0,0,0\n")
            file.write("MeshGenerationType,Solid,Tetra\n")
            file.write("MeshSizeInPlane,{0}\n".format(davg))
            file.write("MeshPath,PackageMesh\n")
            file.write("MaterialID,1\n")
            file.write("StepFile,0.0,0.0,{0},0.001,0.001,0.001,1\n".format(fileName.replace(".stp","_CU.stp")))
            file.write("StepFile,0.0,0.0,{0},0.001,0.001,0.001,2\n".format(fileName.replace(".stp","_PPG.stp")))
            if len(solderMaskShape) > 0:
                file.write("StepFile,0.0,0.0,{0},0.001,0.001,0.001,3\n".format(fileName.replace(".stp","_SM.stp")))
            if len(solderPasteShape) > 0:
                file.write("StepFile,0.0,0.0,{0},0.001,0.001,0.001,4\n".format(fileName.replace(".stp","_SP.stp")))
            file.write("*Material\n")
            file.write("Material.txt\n")
            file.write("*End\n")
        
        
        shapeList = []
        for shape in originalShape:
            shapeList.append(shape)
        '''for shape in cushapeList:
            shapeList.append(shape)
        for shape in ppgshapeList:
            shapeList.append(shape)'''
            
        ### stp file separator by layer       
        
        meshDetailFileInfo = fileName.replace(".stp","_mesh_detail.txt") 
        
        with open(meshDetailFileInfo, 'w') as file:
            file.write("*Layer,CircuitPattern\n")    
            file.write("Location,0,0,0\n")
            file.write("MeshGenerationType,Solid,Tetra\n")
            file.write("MeshSizeInPlane,{0}\n".format(davg))
            file.write("MeshPath,PackageMesh\n")
            file.write("MaterialID,1\n")
            pid = 0
            if len(self.LayerSolderMaskStpList) > 0:
                curSolderMaskShape = self.LayerSolderMaskStpList[0]
                builderCurrentSolderMask = BRep_Builder()
                compoundCurrentSolderMask = TopoDS_Compound()
                builderCurrentSolderMask.MakeCompound(compoundCurrentSolderMask)
                for shape in curSolderMaskShape:
                    if shape is not None:
                        builderCurrentSolderMask.Add(compoundCurrentSolderMask,shape)
                compoundIterator = TopExp_Explorer(compoundCurrentSolderMask,TopAbs_SOLID)
                if not compoundIterator.More():
                    pidbotsm = -1
                else:
                    stepWriteCurrentSolderMaskLayer = STEPControl_Writer()
                    stepWriteCurrentSolderMaskLayer.Transfer(compoundCurrentSolderMask, STEPControl_AsIs)
                    status = stepWriteCurrentSolderMaskLayer.Write(fileName.replace(".stp","_SM_BOT.stp"))
                    pid = pid + 1
                    pidbotsm = pid            
                    file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,3\n".format(pidbotsm,fileName.replace(".stp","_SM_BOT.stp")))
            else:
                pidbotsm = -1
            
            if len(self.LayerSolderMaskStpList) > 1:
                curSolderPasteShape = self.LayerSolderPasteStpList[0]
                builderCurrentSolderPaste = BRep_Builder()
                compoundCurrentSolderPaste = TopoDS_Compound()
                builderCurrentSolderPaste.MakeCompound(compoundCurrentSolderPaste)
                for shape in curSolderPasteShape:
                    if shape is not None:
                        builderCurrentSolderPaste.Add(compoundCurrentSolderPaste,shape)
                compoundIterator = TopExp_Explorer(compoundCurrentSolderPaste,TopAbs_SOLID)
                if not compoundIterator.More():
                    pidbotsp = -1
                else:                
                    stepWriteCurrentSolderPasteLayer = STEPControl_Writer()
                    stepWriteCurrentSolderPasteLayer.Transfer(compoundCurrentSolderPaste, STEPControl_AsIs)
                    status = stepWriteCurrentSolderPasteLayer.Write(fileName.replace(".stp","_SP_BOT.stp"))
                    pid = pid + 1
                    pidbotsp = pid
                    file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,4\n".format(pidbotsp, fileName.replace(".stp","_SP_BOT.stp")))
            else:
                pidbotsp = -1
            pidcuList = [] 
            pidppgList = [] 
            for i in range(len(self.LayerCUStpList)):
                curCUShape = self.LayerCUStpList[i]
                curPPGShape = self.LayerPPGStpList[i]
                
                builderCurrentCU = BRep_Builder()
                builderCurrentPPG = BRep_Builder()
                compoundCurrentCU = TopoDS_Compound()
                compoundCurrentPPG = TopoDS_Compound()
                builderCurrentCU.MakeCompound(compoundCurrentCU)
                builderCurrentPPG.MakeCompound(compoundCurrentPPG)
                if curCUShape is not None:
                    for shape in curCUShape:
                        if shape is not None:
                            builderCurrentCU.Add(compoundCurrentCU,shape)
                            
                    compoundIterator = TopExp_Explorer(compoundCurrentCU,TopAbs_SOLID)
                    if not compoundIterator.More():
                        pidcuList.append(-1)
                    else:
                        stepWriteCurrentCULayer = STEPControl_Writer()
                        stepWriteCurrentCULayer.Transfer(compoundCurrentCU, STEPControl_AsIs)
                        status = stepWriteCurrentCULayer.Write(fileName.replace(".stp","_CU_{0}.stp".format(i)))
                        pid = pid + 1
                        pidcuList.append(pid)
                        file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,{2}\n".format(pid, fileName.replace(".stp","_CU_{0}.stp".format(i)),1))
                    
                if curPPGShape is not None:
                    for shape in curPPGShape:
                        if shape is not None:
                            builderCurrentPPG.Add(compoundCurrentPPG,shape)
                    compoundIterator = TopExp_Explorer(compoundCurrentPPG,TopAbs_SOLID)
                    if not compoundIterator.More():
                        pidppgList.append(-1)
                    else:
                        stepWriteCurrentPPGLayer = STEPControl_Writer()
                        stepWriteCurrentPPGLayer.Transfer(compoundCurrentPPG, STEPControl_AsIs)
                        status = stepWriteCurrentPPGLayer.Write(fileName.replace(".stp","_PPG_{0}.stp".format(i)))
                        pid = pid + 1
                        pidppgList.append(pid)
                        file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,{2}\n".format(pid, fileName.replace(".stp","_PPG_{0}.stp".format(i)),2))
            if len(self.LayerSolderMaskStpList) > 1:
                curSolderPasteShape = self.LayerSolderPasteStpList[1]
                builderCurrentSolderPaste = BRep_Builder()
                compoundCurrentSolderPaste = TopoDS_Compound()
                builderCurrentSolderPaste.MakeCompound(compoundCurrentSolderPaste)
                for shape in curSolderPasteShape:
                    if shape is not None:
                        builderCurrentSolderPaste.Add(compoundCurrentSolderPaste,shape)
                compoundIterator = TopExp_Explorer(compoundCurrentSolderPaste,TopAbs_SOLID)
                if not compoundIterator.More():
                    pidtopsp = -1
                else:
                    stepWriteCurrentSolderPasteLayer = STEPControl_Writer()
                    stepWriteCurrentSolderPasteLayer.Transfer(compoundCurrentSolderPaste, STEPControl_AsIs)
                    status = stepWriteCurrentSolderPasteLayer.Write(fileName.replace(".stp","_SP_TOP.stp"))
                    pid = pid + 1
                    pidtopsp = pid
                    file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,4\n".format(pid, fileName.replace(".stp","_SP_TOP.stp")))
            else:
                pidtopsp = -1
            if len(self.LayerSolderMaskStpList) > 1:
                curSolderMaskShape = self.LayerSolderMaskStpList[1]
                builderCurrentSolderMask = BRep_Builder()
                compoundCurrentSolderMask = TopoDS_Compound()
                builderCurrentSolderMask.MakeCompound(compoundCurrentSolderMask)
                for shape in curSolderMaskShape:
                    if shape is not None:
                        builderCurrentSolderMask.Add(compoundCurrentSolderMask,shape)
                compoundIterator = TopExp_Explorer(compoundCurrentSolderMask,TopAbs_SOLID)
                if not compoundIterator.More():
                    pidtopsm = -1
                else:                
                    stepWriteCurrentSolderMaskLayer = STEPControl_Writer()
                    stepWriteCurrentSolderMaskLayer.Transfer(compoundCurrentSolderMask, STEPControl_AsIs)
                    status = stepWriteCurrentSolderMaskLayer.Write(fileName.replace(".stp","_SM_TOP.stp"))
                    pid = pid + 1
                    pidtopsm = pid
                    file.write("StepFile#{0},0.0,0.0,{1},0.001,0.001,0.001,3\n".format(pid, fileName.replace(".stp","_SM_TOP.stp")))
            else:
                pidtopsm = -1
               
                    
                               
            file.write("*Contact\n")
            if pidbotsm != -1 and pidppgList[0] != -1:
                file.write("Tied,Part,{0},{1}\n".format(pidbotsm,pidppgList[0]))
            if pidbotsp != -1 and pidcuList[0] != -1:
                file.write("Tied,Part,{0},{1}\n".format(pidbotsp,pidcuList[0]))                
            if pidtopsm != -1 and pidppgList[-1] != -1:
                file.write("Tied,Part,{0},{1}\n".format(pidtopsm,pidppgList[-1]))
            if pidtopsp != -1 and pidcuList[-1] != -1:
                file.write("Tied,Part,{0},{1}\n".format(pidtopsp,pidcuList[-1]))
                
            
            
            for i in range(1,len(pidcuList)):
                if pidcuList[i-1] != -1 and pidcuList[i] != -1:
                    file.write("Tied,Part,{0},{1}\n".format(pidcuList[i-1],pidcuList[i]))
                if pidppgList[i-1] != -1 and pidppgList[i] != -1:
                    file.write("Tied,Part,{0},{1}\n".format(pidppgList[i-1],pidppgList[i]))
            for i in range(0, len(pidcuList)):
                if pidcuList[i] != -1 and pidppgList[i] != -1:
                    file.write("Tied,Part,{0},{1}\n".format(pidcuList[i],pidppgList[i]))
            
            #if len(solderMaskShape) > 0:
            file.write("*Material\n")
            file.write("Material.txt\n")
            file.write("*End\n")  
        return shapeList
    
    def ExportShapeExternal(self, fileName):
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        shapeList = self.GenerateExternalSolid()
        for shape in shapeList:
            if shape is not None:
                builder.Add(compound,shape)
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        step_writer = STEPControl_Writer()
        step_writer.Transfer(compound, STEPControl_AsIs)
        status = step_writer.Write(fileName)
        print("Exporting STEP file is done.")
        return shapeList         

    def ExportShape(self, fileName):

        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        shapeList = self.GenerateCombinedSolid()       
        for shape in shapeList:
            if shape is not None:
                builder.Add(compound,shape)
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        step_writer = STEPControl_Writer()
        step_writer.Transfer(compound, STEPControl_AsIs)
        status = step_writer.Write(fileName)
        print("Exporting STEP file is done.")        
        return shapeList

                
    def GenerateSolid(self):
        shapeList = [ ]
        for layer in self.aislayers:
            print(layer.layer.name)
            print("Number of shapes :", len(layer.layer.patternXList))
            print("Number of symbols : ", len(layer.layer.symbolMap))
            shapeList.extend(layer.GetShape())            
        return shapeList
    
    def ExportUnitFeature(self, unitFeaturePath, zLoc = 0.0, thicknessList = [], tsp = 0.0, tsm = 0.0):
        with open(unitFeaturePath, 'w') as file:
            firstFeature : AISLayer = self.aisfeatures[0]
            patternX = firstFeature.layer.patternXList[0]
            patternY = firstFeature.layer.patternYList[0]
            cwList = []
            if len(firstFeature.layer.patternClockwiseList) > 0:
                cwList = firstFeature.layer.patternClockwiseList[0]
            hasArc = len(cwList) > 0 and any(cw is not None for cw in cwList)

            # Flatten xMat/yMat to flat lists for min/max and RDP
            # OB 블록(symbolID==-1)은 항상 2D 리스트(xMat) 구조
            isMatFormat = len(patternX) > 0 and isinstance(patternX[0], list)
            if isMatFormat:
                flatX = []
                flatY = []
                for seg in patternX:
                    for v in seg:
                        flatX.append(v)
                for seg in patternY:
                    for v in seg:
                        flatY.append(v)
            else:
                flatX = patternX
                flatY = patternY

            xMin = min(flatX)
            xMax = max(flatX)
            yMin = min(flatY)
            yMax = max(flatY)
            lengthMin = min(xMax - xMin, yMax - yMin)
            numLayer = len(thicknessList)
            if tsp != 0.0:
                numLayer = numLayer + 1
            if tsm != 0.0:
                numLayer = numLayer + 1

            totalThickness = max(tsp, tsm)
            for thickness in thicknessList:
                totalThickness = totalThickness + thickness
            file.write("*Layer,PCB\n")
            if zLoc == 0.0:
                file.write("Location,0.0,0.0\n")
            else:
                file.write("Location,0.0,0.0,{0}\n".format(zLoc))

            file.write("MeshGenerationType,Solid,Hexa\n")
            file.write("Thickness,{0}\n".format(totalThickness*0.001))
            file.write("MeshPath,PackageMesh\n")
            file.write("MeshSizeInPlane,{0}\n".format(lengthMin/100.0*0.001))
            file.write("NumberofElementinThickness,4\n")
            file.write("Part,Polynomial,Solid,1\n")

            if hasArc:
                # Export with OC for arc segments
                for i in range(len(patternX)):
                    seg_x = patternX[i]
                    seg_y = patternY[i]
                    if i == 0:
                        file.write("OB {0} {1} I\n".format(format(seg_x[0]*0.001,".5e"),format(seg_y[0]*0.001,".5e")))
                    if cwList[i] is None:
                        file.write("OS {0} {1}\n".format(format(seg_x[1]*0.001,".5e"),format(seg_y[1]*0.001,".5e")))
                    else:
                        cw_str = "Y" if cwList[i] == 1 else "N"
                        file.write("OC {0} {1} {2} {3} {4}\n".format(
                            format(seg_x[1]*0.001,".5e"), format(seg_y[1]*0.001,".5e"),
                            format(seg_x[2]*0.001,".5e"), format(seg_y[2]*0.001,".5e"),
                            cw_str))
                file.write("OE\n")
            else:
                newPoints = firstFeature.create_closed_vector_rdp(flatX, flatY, totalThickness)
                newPatternX = []
                newPatternY = []
                for i in range(len(newPoints)):
                    newPatternX.append(newPoints[i][0]*0.001)
                    newPatternY.append(newPoints[i][1]*0.001)
                newPatternX.append(newPoints[0][0]*0.001)
                newPatternY.append(newPoints[0][1]*0.001)
                for i in range(len(newPatternX)):
                    if i == 0:
                        file.write("OB {0} {1} I\n".format(format(newPatternX[i],".5e"),format(newPatternY[i],".5e")))
                    elif i == len(newPatternX) - 1:
                        file.write("OS {0} {1}\n".format(format(newPatternX[i],".5e"),format(newPatternY[i],".5e")))
                        file.write("OE\n")
                    else:
                        file.write("OS {0} {1}\n".format(format(newPatternX[i],".5e"),format(newPatternY[i],".5e")))

            file.write("MaterialID,1\n")
            file.write("*Material\n")
            file.write("Material.txt\n")
            file.write("*End")

                 
    

    def GenerateExternalSolid(self):
        shapeList = [] 
        for layer in self.aisfeatures:
            curShapeList = layer.GetShape()
            shapeList.extend(curShapeList)
        return shapeList
    
    def GenerateSolderPaste(self, xmin, ymin, xmax, ymax):
        solderPasteShapeList = []
        originalShape = []
        
        self.LayerSolderPasteStpList = []
        for layer in self.aisSolderPasteFeatures:
            curShapeList = layer.GetExternalShape()
            if len(curShapeList) > 0:
                originalShape.append(curShapeList[0])
            curLayer : AISLayer = layer
            curLayer.GetRectanglePPGShape(xmin,ymin,xmax,ymax)
            curShapeList = curLayer.RemoveRectangularfromOriginalShape()
            
        for i in range(len(self.aisSolderPastelayers)):
            layer = self.aisSolderPastelayers[i]
            curShape = layer.GetShape()
            curLayer : AISLayer = layer
            #curLayer.GetRectanglePPGShape(xMin,yMin,xMax,yMax)
            curLayer.GetRectanglePPGShapeRemoveShape(xmin, ymin, xmax, ymax,originalShape[i])
            cuShape, ppgShape = curLayer.RemovePattenfromPPGShape()            
            solderPasteShapeList.extend(cuShape)
            if type(cuShape) == list:
                self.LayerSolderPasteStpList.append(cuShape)
            else:
                self.LayerSolderPasteStpList.append([cuShape])
        return solderPasteShapeList

    def GenerateSolderMask(self, xmin, ymin, xmax, ymax):        
        solderMaskShapeList = [] 
        originalShape = [] 
        self.LayerSolderMaskStpList = []
        
            
        for layer in self.aisSolderMaskFeatures:     
            curShapeList = layer.GetExternalShape()
            if len(curShapeList) > 0:
                originalShape.append(curShapeList[0])
            curLayer : AISLayer = layer
            curLayer.GetRectanglePPGShape(xmin,ymin,xmax,ymax)
            curShapeList = curLayer.RemoveRectangularfromOriginalShape()
            
        for i in range(len(self.aisSolderMaskLayers)):            
            layer = self.aisSolderMaskLayers[i]
            curShape = layer.GetShape()
            curLayer : AISLayer = layer
            #curLayer.GetRectanglePPGShape(xMin,yMin,xMax,yMax)
            curLayer.GetRectanglePPGShapeRemoveShape(xmin, ymin, xmax, ymax,originalShape[i])
            cuShape, ppgShape = curLayer.RemovePattenfromPPGShape()
            #shapeList.extend(curShapeList)
            solderMaskShapeList.extend(ppgShape)
            if type(ppgShape) == list:
                self.LayerSolderMaskStpList.append(ppgShape)
            else:
                self.LayerSolderMaskStpList.append([ppgShape])
                
        return solderMaskShapeList
    
    def GeneratePPG(self,xmin,ymin,xmax,ymax, skipLayerList=None):
        if skipLayerList is None:
            skipLayerList = []
        ppgShapeList = []
        cuShapeList = []
        originalShape = []
        print("Generate PPG and CU External Shape")
        for layer in self.aisfeatures:
            curShapeList = layer.GetExternalShape()
            if len(curShapeList) >0:
                originalShape.append(curShapeList[0])
            curLayer : AISLayer = layer
            curLayer.GetRectanglePPGShape(xmin,ymin,xmax,ymax)
            curShapeList = curLayer.RemoveRectangularfromOriginalShape()

            print("Number of shapes :", len(curShapeList), "are generated")

        print("Generate PPG and CU Internal Shape")
        self.LayerCUStpList = []
        self.LayerPPGStpList = []
        for i in range(len(self.aislayers)):
            layer = self.aislayers[i]
            curLayer : AISLayer = layer
            layerName = curLayer.layer.name

            if layerName in skipLayerList:
                # 스킵된 레이어: BoundaryBox 전체를 솔리드 구리로 출력
                print("SkipLayer: ", layerName, " -> Solid Copper Sheet")
                cuShape = [curLayer.GenerateSolidCopperSheet(xmin, ymin, xmax, ymax, originalShape[i])]
                ppgShape = []
            else:
                # 기존 로직: 회로 패턴 생성
                curShape = layer.GetShape()
                curLayer.GetRectanglePPGShapeRemoveShape(xmin,ymin,xmax,ymax,originalShape[i])
                cuShape, ppgShape = curLayer.RemovePattenfromPPGShape()

            if cuShape is None or ppgShape is None:
                print("No shape is generated")
                continue
            cuShapeList.extend(cuShape)
            ppgShapeList.extend(ppgShape)
            if type(cuShape) == list:
                self.LayerCUStpList.append(cuShape)
            else:
                self.LayerCUStpList.append([cuShape])
            if type(ppgShape) == list:
                self.LayerPPGStpList.append(ppgShape)
            else:
                self.LayerPPGStpList.append([ppgShape])

        return originalShape, cuShapeList, ppgShapeList

    def process_layer(self,layer, shapeList,xmin,ymin,xmax,ymax):
        curShape = layer.GetShape()
        curLayer : AISLayer = layer
        curLayer.GetRectanglePPGShape(xmin,ymin,xmax,ymax)
        curShapeList = curLayer.RemovePattenfromPPGShape()
        shapeList.extend(curShapeList)

    def GeneratePPGMultiThread(self,xmin,ymin,xmax,ymax):
        shapeList = []
        threads = [] 
        for layer in self.aislayers:
            thread = threading.Thread(target=self.process_layer, args=(layer,shapeList,xmin,ymin,xmax,ymax))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

        return shapeList
        
    
    def GenerateCombinedSolid(self):
        shapeList = [ ]
        for layer in self.aislayers:
            curShapeList = layer.GetShape()
            for curShape in curShapeList:
                if type(curShape) == TopoDS_Compound:
                    print("We have a compound")
                   

        for layer in self.aislayers:
            #layer.RemoveOverlapExperimental()
            layer.RemoveOverlap()

        
        for layer in self.aislayers:
            for shape in layer.odbShapeList:
                if shape is not None:
                    shapeList.append(shape.shape)            
        return shapeList


  





        


        '''
        def GenerateCombinedSolid(self):
                
            shapeList = [ ]
            for layer in self.aislayers:
                curShapeList = layer.GetShape()

                for i in range(len(curShapeList)):
                    for j in range(i+1,len(curShapeList)):
                        #tmpShape = BRepAlgoAPI_Cut(shapeList[i], shapeList[j]).Shape()
                        # Check for overlap using the Common operation
                        common = BRepAlgoAPI_Common(curShapeList[i], curShapeList[j])
                        tmpShape = common.Shape()                
                        if not common.IsDone() or common.HasErrors():
                            print("The two solids do not overlap")
                        else:
                            
                            print("The two geometries overlap.")                    
                            curShapeList[i] = BRepAlgoAPI_Cut(curShapeList[i], curShapeList[j]).Shape()
                            print(i,'/',len(curShapeList),' geometry is cut by ', j, ' geometry.')                    
                shapeList.extend(curShapeList)
            return shapeList
        '''
        '''
        for i in range(len(shapeList)):
            if i == 0:
                combinedShape = shapeList[i]
            else:

                tmpShape = BRepAlgoAPI_Fuse(combinedShape, shapeList[i]).Shape()
                if tmpShape is not None:
                    combinedShape = tmpShape
                else:
                    print(i,'/',len(shapeList),'is done.')
                
           
        return combinedShape
        '''



class ODBShape():
    def __init__(self, shape, xmin,ymin,xmax,ymax):
        self.shape = shape
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax



class AISLayer():
    def __init__(self,layer : Layer, zPos):
        self.layer = layer
        self.zPos = zPos         

        self.odbShapeList = [] 
        self.ppgShapeList = [] 
    
    def RemoveRectangularfromOriginalShape(self):
        shapeList = [] 
        for i in range(len(self.odbShapeList)):
            odbShape = self.odbShapeList[i].shape
            for ppgShape in self.ppgShapeList:
                curShape = ppgShape.shape 
                cutShape = BRepAlgoAPI_Cut(odbShape,curShape).Shape()
                if cutShape is not None:
                    odbShape = cutShape
            
            shapeList.append(odbShape)
        return shapeList
                



    def RemovePattenfromPPGShape(self):
        
        ppgShapeList = [] 
        patternShapeList = [] 
        print("Remove Pattern from PPG Shape")
        print("Number of shapes :", len(self.ppgShapeList), "are generated")
        count = 0 
        for ppgShape in self.ppgShapeList:
            curShape = ppgShape.shape
            originalShape = curShape
            xminj = ppgShape.xmin
            xmaxj = ppgShape.xmax
            yminj = ppgShape.ymin
            ymaxj = ppgShape.ymax

            for i in range(len(self.odbShapeList)):
                odbShape = self.odbShapeList[i]
                xmini = odbShape.xmin
                xmaxi = odbShape.xmax
                ymini = odbShape.ymin
                ymaxi = odbShape.ymax
                if xmaxi < xminj or xmaxj < xmini or ymaxi < yminj or ymaxj < ymini:
                    pass
                else:                    
                    shape1 = odbShape.shape
                    cutShape = BRepAlgoAPI_Cut(curShape,shape1).Shape()
                    count = count + 1
                    if count % 100 == 0:
                        #print("ppg shape is cut by",i,"th shape")
                        print(count, "th cut shape is done")
                    if cutShape is not None:
                        curShape = cutShape
            
            ppgShapeList.append(curShape)
            ppgShape.shape = curShape
            curShape = BRepAlgoAPI_Cut(originalShape,curShape).Shape()
            
            patternShapeList.append(curShape)
        
        print(count, "th cut shape is done")   
        print("Number of shapes :", len(patternShapeList), "are cut by PPG shape :", count)
        
        return patternShapeList, ppgShapeList


                
                
                    
                    
                   




    def RemoveOverlapExperimental(self):
        for i in range(len(self.odbShapeList)):
            for j in range(i+1,len(self.odbShapeList)):
                xmini = self.odbShapeList[i].xmin
                xmaxi = self.odbShapeList[i].xmax
                ymini = self.odbShapeList[i].ymin
                ymaxi = self.odbShapeList[i].ymax
                xminj = self.odbShapeList[j].xmin
                xmaxj = self.odbShapeList[j].xmax
                yminj = self.odbShapeList[j].ymin
                ymaxj = self.odbShapeList[j].ymax

                if (xmaxi < xminj or xmaxj < xmini) or (ymaxi < yminj or ymaxj < ymini):
                    pass
                else:
                    shape1 = self.odbShapeList[i].shape
                    shape2 = self.odbShapeList[j].shape

                    if shape1 is None or shape2 is None:
                        continue                                                                                
                        
                    common = BRepAlgoAPI_Common(shape1, shape2)                    
                    commonFace = self.get_faces(common.Shape())

                    
                    #if not common.IsDone() or common.HasErrors():
                    #    print("The two solids do not overlap")
                    if len(commonFace) == 0:
                        pass
                    else:

                        print("The two geometries overlap.")                    
                        try:
                            if i == 21 and j == 78:
                                print("break")

                            shape1re = BRepAlgoAPI_Cut(shape1, common.Shape()).Shape()
                            
                            shape1Face = self.get_faces(shape1re)
                            
                            partnerFaceShape1List = [] 
                            partnerFaceShape1CommonList = [] 
                            partnerFaceShape2List = [] 
                            partnerFaceShape2CommonList = [] 
                        

                            for face in shape1Face:
                                for cFace in commonFace:
                                    if face.IsPartner(cFace):
                                        partnerFaceShape1List.append(face)
                                        partnerFaceShape1CommonList.append(cFace)                                    
                            glue = BRepFeat_Gluer(shape1re,common.Shape())
                            for ii in range(len(partnerFaceShape1List)):
                                glue.Bind(partnerFaceShape1List[ii],partnerFaceShape1CommonList[ii])                                                    
                            if glue.Shape() == None:
                                print("glue" "is failed")
                            if len(partnerFaceShape1List)>0:                         
                                modifiedShape1 = glue.Shape()
                            else:
                                 print("Error!")


                            shape2re = BRepAlgoAPI_Cut(shape2, modifiedShape1).Shape()
                            shape2Face = self.get_faces(shape2re)

                            modiShapeFace = self.get_faces(modifiedShape1)                    

                            
                            for face in shape2Face:
                                for cFace in modiShapeFace:
                                    if face.IsPartner(cFace):
                                        partnerFaceShape2List.append(face)
                                        partnerFaceShape2CommonList.append(cFace)
                            glue = BRepFeat_Gluer(shape2re,modifiedShape1)
                            for ii in range(len(partnerFaceShape2List)):
                                glue.Bind(partnerFaceShape2List[ii],partnerFaceShape2CommonList[ii])
                            if len(partnerFaceShape2List)>0:
                                modifiedShape2 = glue.Shape()
                                shape = modifiedShape2
                            else:
                                print("Error!")
                                shape = modifiedShape1
                        
                            #shape = BRepAlgoAPI_Cut(shape1,shape2).Shape()

                            #facesA = self.get_faces(shape)
                            #facesB = self.get_faces(shape2)

                            #glue = BRepFeat_Gluer(shape,shape2)
                            #glue.Bind()

                            #shape = BRepAlgoAPI_Fuse(shape, shape2).Shape()

                            '''
                            from OCC.Core.Quantity import Quantity_Color
                            from OCC.Display.SimpleGui import init_display
                            display, start_display, add_menu, add_functionto_menu = init_display()
                            
                            display.DisplayShape(shape) 
                            start_display()
                            '''
                            self.odbShapeList[i].shape = None
                            self.odbShapeList[j].shape = shape 
                            self.odbShapeList[i].xmin = min(self.odbShapeList[i].xmin, self.odbShapeList[j].xmin)   
                            self.odbShapeList[i].xmax = max(self.odbShapeList[i].xmax, self.odbShapeList[j].xmax)
                            self.odbShapeList[i].ymin = min(self.odbShapeList[i].ymin, self.odbShapeList[j].ymin)
                            self.odbShapeList[i].ymax = max(self.odbShapeList[i].ymax, self.odbShapeList[j].ymax)
                        except:                            
                            shape1re = BRepAlgoAPI_Cut(shape1, shape2).Shape()
                            shape2re = BRepAlgoAPI_Cut(shape2, shape1).Shape()

                            if shape1re == None:
                                self.odbShapeList[i].shape = None
                                self.odbShapeList[j].shape = shape2
                                self.odbShapeList[i].xmin = min(self.odbShapeList[i].xmin, self.odbShapeList[j].xmin)   
                                self.odbShapeList[i].xmax = max(self.odbShapeList[i].xmax, self.odbShapeList[j].xmax)
                                self.odbShapeList[i].ymin = min(self.odbShapeList[i].ymin, self.odbShapeList[j].ymin)
                                self.odbShapeList[i].ymax = max(self.odbShapeList[i].ymax, self.odbShapeList[j].ymax)
                                
                            elif shape2re == None:
                                self.odbShapeList[i].shape = None
                                self.odbShapeList[j].shape = shape1
                                self.odbShapeList[i].xmin = min(self.odbShapeList[i].xmin, self.odbShapeList[j].xmin)   
                                self.odbShapeList[i].xmax = max(self.odbShapeList[i].xmax, self.odbShapeList[j].xmax)
                                self.odbShapeList[i].ymin = min(self.odbShapeList[i].ymin, self.odbShapeList[j].ymin)
                                self.odbShapeList[i].ymax = max(self.odbShapeList[i].ymax, self.odbShapeList[j].ymax)
                                
                            else:
                                
                                fuse = BRepAlgoAPI_Fuse(shape1re, common.Shape())
                                fuse.Build()
                                fuse = BRepAlgoAPI_Fuse(fuse.Shape(), shape2re)
                                fuse.Build()
                                shape = fuse.Shape()
                            
                                self.odbShapeList[i].shape = None
                                self.odbShapeList[j].shape = shape 
                                self.odbShapeList[i].xmin = min(self.odbShapeList[i].xmin, self.odbShapeList[j].xmin)   
                                self.odbShapeList[i].xmax = max(self.odbShapeList[i].xmax, self.odbShapeList[j].xmax)
                                self.odbShapeList[i].ymin = min(self.odbShapeList[i].ymin, self.odbShapeList[j].ymin)
                                self.odbShapeList[i].ymax = max(self.odbShapeList[i].ymax, self.odbShapeList[j].ymax)
                                
                            

                            
                         
                       
                        print(i,'/',len(self.odbShapeList),' geometry is cut by ', j, ' geometry.')
    def RemoveOverlap(self):
        for i in range(len(self.odbShapeList)):
            for j in range(i+1,len(self.odbShapeList)):
                xmini = self.odbShapeList[i].xmin
                xmaxi = self.odbShapeList[i].xmax
                ymini = self.odbShapeList[i].ymin
                ymaxi = self.odbShapeList[i].ymax
                xminj = self.odbShapeList[j].xmin
                xmaxj = self.odbShapeList[j].xmax
                yminj = self.odbShapeList[j].ymin
                ymaxj = self.odbShapeList[j].ymax

                if (xmaxi < xminj or xmaxj < xmini) or (ymaxi < yminj or ymaxj < ymini):
                    pass
                else:
                    shape1 = self.odbShapeList[i].shape
                    shape2 = self.odbShapeList[j].shape

                    if shape1 is None or shape2 is None:
                        continue                                                                                
                        
                    common = BRepAlgoAPI_Common(shape1, shape2)                    
                    commonFace = self.get_faces(common.Shape())

                    
                    #if not common.IsDone() or common.HasErrors():
                    #    print("The two solids do not overlap")
                    if len(commonFace) == 0:
                        pass
                    else:
                        print("The two geometries overlap.")                    
                        shape1re = BRepAlgoAPI_Cut(shape1, shape2).Shape()
                        shape2re = BRepAlgoAPI_Cut(shape2, shape1).Shape()

                        fuse = BRepAlgoAPI_Fuse(shape1re, common.Shape())
                        fuse.Build()
                        fuse = BRepAlgoAPI_Fuse(fuse.Shape(), shape2re)
                        fuse.Build()
                        shape = fuse.Shape()
                    
                        #shape = BRepAlgoAPI_Cut(shape1,shape2).Shape()

                        #facesA = self.get_faces(shape)
                        #facesB = self.get_faces(shape2)

                        #glue = BRepFeat_Gluer(shape,shape2)
                        #glue.Bind()

                        #shape = BRepAlgoAPI_Fuse(shape, shape2).Shape()
                        self.odbShapeList[i].shape = None
                        self.odbShapeList[j].shape = shape 
                        self.odbShapeList[i].xmin = min(self.odbShapeList[i].xmin, self.odbShapeList[j].xmin)   
                        self.odbShapeList[i].xmax = max(self.odbShapeList[i].xmax, self.odbShapeList[j].xmax)
                        self.odbShapeList[i].ymin = min(self.odbShapeList[i].ymin, self.odbShapeList[j].ymin)
                        self.odbShapeList[i].ymax = max(self.odbShapeList[i].ymax, self.odbShapeList[j].ymax)
                        
                       
                        print(i,'/',len(self.odbShapeList),' geometry is cut by ', j, ' geometry.')
                                 
    def get_faces(self,_shape):
        """return the faces from `_shape`

        :param _shape: TopoDS_Shape, or a subclass like TopoDS_Solid
        :return: a list of faces found in `_shape`
        """
        
        topExp = TopExp_Explorer()
        topExp.Init(_shape, TopAbs_FACE)
        _faces = []

        while topExp.More():
            fc = TopoDS_Face(topExp.Current())
            _faces.append(fc)
            topExp.Next()

        

        return _faces

    def RemoveOverlapPre(self):
        for i in range(len(self.odbShapeList)):
            for j in range(i+1,len(self.odbShapeList)):
                xmini = self.odbShapeList[i].xmin
                xmaxi = self.odbShapeList[i].xmax
                ymini = self.odbShapeList[i].ymin
                ymaxi = self.odbShapeList[i].ymax
                xminj = self.odbShapeList[j].xmin
                xmaxj = self.odbShapeList[j].xmax
                yminj = self.odbShapeList[j].ymin
                ymaxj = self.odbShapeList[j].ymax

                if (xmaxi < xminj or xmaxj < xmini) or (ymaxi < yminj or ymaxj < ymini):
                    pass
                else:
                    shape1 = self.odbShapeList[i].shape
                    shape2 = self.odbShapeList[j].shape
                    
                    
                    if type(shape1) == TopoDS_Compound or type(shape2) == TopoDS_Compound:
                        print("We have a compound")
                        
                    common = BRepAlgoAPI_Common(shape1, shape2)
                    tmpShape = common.Shape()                
                    if not common.IsDone() or common.HasErrors():
                        print("The two solids do not overlap")
                    else:
                        print("The two geometries overlap.")                    
                        #shape = BRepAlgoAPI_Cut(self.odbShapeList[i].shape, self.odbShapeList[j].shape).Shape()
                        
                        '''
                        if i == 118:
                            from OCC.Display.SimpleGui import init_display

                            # Initialize the display
                            display, start_display, add_menu, add_function_to_menu = init_display()

                            # Display the wire
                            #display.DisplayShape(shapeList, update=True)
                            display.DisplayShape(shape1, update=True)
                            display.DisplayShape(shape2, update=True)
                            display.FitAll()

                            # Start the display
                            start_display()
                        '''
                        shape = BRepAlgoAPI_Cut(self.odbShapeList[i].shape, self.odbShapeList[j].shape).Shape()
                       


                        if type(shape) == TopoDS_Compound:
                            explorer = TopExp_Explorer(shape, TopAbs_SOLID)
                            while explorer.More():
                                solid_shape = topods.Solid(explorer.Current())
                                self.odbShapeList[i].shape = solid_shape
                                explorer.Next()

                            '''
                            fuse = BRepAlgoAPI_Fuse()

                            # Create an explorer to iterate over the shapes in the compound
                              
                            explorer = TopExp_Explorer(shape, TopAbs_SOLID)                            
                           
                            while explorer.More():
                                solid_shape2 = topods.Solid(explorer.Current())  # Get the solid shape
                                fuse = BRepAlgoAPI_Fuse(solid_shape1,solid_shape2)
                                solid_shape1 = fuse.Shape()
                                explorer.Next()
                            fuse.Build()  # Build the fuse operation
                            if fuse.IsDone():
                                self.odbShapeList[i].shape = fuse.Shape()
                            '''
                            
                        else:
                            self.odbShapeList[i].shape = shape
                      
                        print(i,'/',len(self.odbShapeList),' geometry is cut by ', j, ' geometry.')
                        
    def GetExternalShape(self):
        layer = self.layer
        patternXList = layer.patternXList
        patternYList = layer.patternYList
        patternSymbolIDList = layer.patternSymbolIDList
        patternPolarityList = layer.patternPolarityList
        patternClockwiseList = layer.patternClockwiseList
        symbolMap = layer.symbolMap
        zLoc = self.zPos
        thickness = layer.thickness

        shapeList = []

        for i in range(len(patternXList)):
            xVec = patternXList[i]
            yVec = patternYList[i]

            symbolID = patternSymbolIDList[i]
            polarity = patternPolarityList[i]
            cwList = patternClockwiseList[i] if i < len(patternClockwiseList) else []

            if symbolID == -1:
                if len(xVec) == 1 or len(xVec) == 2:
                    continue

                shape = self.GetOBShape(xVec, yVec, zLoc, thickness, cwList)

                shapeList.append(shape)
            else:
                aSymbol = symbolMap[symbolID]
                curShapeList = self.GetShapewithSymbol(xVec, yVec, aSymbol, zLoc, thickness)
                if curShapeList is not None:
                    shapeList.extend(curShapeList)
                else:
                    print("Error! curShapeList is None")
                    continue

        return shapeList

    def GetShape(self):
        layer = self.layer
        patternXList = layer.patternXList
        patternYList = layer.patternYList
        patternSymbolIDList = layer.patternSymbolIDList
        patternPolarityList = layer.patternPolarityList
        patternClockwiseList = layer.patternClockwiseList
        symbolMap = layer.symbolMap
        zLoc = self.zPos
        thickness = layer.thickness

        shapeList = []

        for i in range(len(patternXList)):
            xVec = patternXList[i]
            yVec = patternYList[i]

            symbolID = patternSymbolIDList[i]
            polarity = patternPolarityList[i]
            cwList = patternClockwiseList[i] if i < len(patternClockwiseList) else []

            if symbolID == -1:
                if len(xVec) == 1 or len(xVec) == 2:
                    continue
                shape = self.GetOBShape(xVec, yVec, zLoc, thickness, cwList)

                shapeList.append(shape)
            else:
                aSymbol = symbolMap[symbolID]
                curShapeList = self.GetShapewithSymbol(xVec, yVec, aSymbol, zLoc, thickness)
                if curShapeList is not None:
                    shapeList.extend(curShapeList)

        return shapeList
    
    def GetRectanglePPGShapewithRemoved(self, xmin, ymin, xmax, ymax):
        p1 = gp_Pnt(xmin,ymin,self.zPos)
        p2 = gp_Pnt(xmax,ymin,self.zPos)
        p3 = gp_Pnt(xmax,ymax,self.zPos)
        p4 = gp_Pnt(xmin,ymax,self.zPos)
        e1 = BRepBuilderAPI_MakeEdge(p1,p2).Edge()
        e2 = BRepBuilderAPI_MakeEdge(p2,p3).Edge()  
        e3 = BRepBuilderAPI_MakeEdge(p3,p4).Edge()
        e4 = BRepBuilderAPI_MakeEdge(p4,p1).Edge()
        w = BRepBuilderAPI_MakeWire(e1,e2,e3,e4).Wire()
        f = BRepBuilderAPI_MakeFace(w).Face()
        
        vec = gp_Vec(0,0,self.layer.thickness)
        prism = BRepPrimAPI_MakePrism(f,vec)
        prism.Build()
        shape = prism.Shape()
        ppgShape = ODBShape(shape, xmin,ymin,xmax,ymax)

        shapeList = [] 
        for i in range(len(self.odbShapeList)):
            odbShape = self.odbShapeList[i].shape
           
            curShape = ppgShape.shape 
            cutShape = BRepAlgoAPI_Cut(odbShape,curShape).Shape()
                    
            ppgShape = BRepAlgoAPI_Cut(ppgShape.shape,cutShape).Shape()
            shapeList.append(odbShape)
        self.ppgShapeList.extend(shapeList)
        return shapeList
                
    def GetRectanglePPGShapeRemoveShape(self, xmin, ymin, xmax, ymax, shape):
        p1 = gp_Pnt(xmin,ymin,self.zPos)
        p2 = gp_Pnt(xmax,ymin,self.zPos)
        p3 = gp_Pnt(xmax,ymax,self.zPos)
        p4 = gp_Pnt(xmin,ymax,self.zPos)
        e1 = BRepBuilderAPI_MakeEdge(p1,p2).Edge()
        e2 = BRepBuilderAPI_MakeEdge(p2,p3).Edge()  
        e3 = BRepBuilderAPI_MakeEdge(p3,p4).Edge()
        e4 = BRepBuilderAPI_MakeEdge(p4,p1).Edge()
        w = BRepBuilderAPI_MakeWire(e1,e2,e3,e4).Wire()
        f = BRepBuilderAPI_MakeFace(w).Face()
        
        vec = gp_Vec(0,0,self.layer.thickness)
        prism = BRepPrimAPI_MakePrism(f,vec)
        prism.Build()
        preshape = prism.Shape()
        shape =  BRepAlgoAPI_Common(preshape,shape).Shape()
        ppgShape = ODBShape(shape, xmin,ymin,xmax,ymax)
        self.ppgShapeList.append(ppgShape)
        return shape

    def GenerateSolidCopperSheet(self, xmin, ymin, xmax, ymax, externalShape):
        """스킵된 레이어의 BoundaryBox 영역을 솔리드 구리로 생성.
        BoundaryBox 사각형 prism을 만든 뒤 외곽 형상과 교집합."""
        p1 = gp_Pnt(xmin,ymin,self.zPos)
        p2 = gp_Pnt(xmax,ymin,self.zPos)
        p3 = gp_Pnt(xmax,ymax,self.zPos)
        p4 = gp_Pnt(xmin,ymax,self.zPos)
        e1 = BRepBuilderAPI_MakeEdge(p1,p2).Edge()
        e2 = BRepBuilderAPI_MakeEdge(p2,p3).Edge()
        e3 = BRepBuilderAPI_MakeEdge(p3,p4).Edge()
        e4 = BRepBuilderAPI_MakeEdge(p4,p1).Edge()
        w = BRepBuilderAPI_MakeWire(e1,e2,e3,e4).Wire()
        f = BRepBuilderAPI_MakeFace(w).Face()
        vec = gp_Vec(0,0,self.layer.thickness)
        prism = BRepPrimAPI_MakePrism(f,vec)
        prism.Build()
        preshape = prism.Shape()
        shape = BRepAlgoAPI_Common(preshape, externalShape).Shape()
        return shape

    def GetRectanglePPGShape(self, xmin, ymin, xmax, ymax):
        p1 = gp_Pnt(xmin,ymin,self.zPos)
        p2 = gp_Pnt(xmax,ymin,self.zPos)
        p3 = gp_Pnt(xmax,ymax,self.zPos)
        p4 = gp_Pnt(xmin,ymax,self.zPos)
        e1 = BRepBuilderAPI_MakeEdge(p1,p2).Edge()
        e2 = BRepBuilderAPI_MakeEdge(p2,p3).Edge()  
        e3 = BRepBuilderAPI_MakeEdge(p3,p4).Edge()
        e4 = BRepBuilderAPI_MakeEdge(p4,p1).Edge()
        w = BRepBuilderAPI_MakeWire(e1,e2,e3,e4).Wire()
        f = BRepBuilderAPI_MakeFace(w).Face()
        
        vec = gp_Vec(0,0,self.layer.thickness)
        prism = BRepPrimAPI_MakePrism(f,vec)
        prism.Build()
        shape = prism.Shape()
        ppgShape = ODBShape(shape, xmin,ymin,xmax,ymax)
        self.ppgShapeList.append(ppgShape)
        return shape
    
    def calculate_circle_center_radius(self, p1, p2, p3):
        x1 = p1.X()
        y1 = p1.Y()
        x2 = p2.X()
        y2 = p2.Y()
        x3 = p3.X()
        y3 = p3.Y()
        
        # 각 점의 좌표를 numpy 배열로 저장
        A = np.array([x1, y1])
        B = np.array([x2, y2])
        C = np.array([x3, y3])
        
        # 두 변의 중점 계산
        midAB = (A + B) / 2
        midBC = (B + C) / 2
        
        # 두 변의 방향 벡터
        AB = B - A
        BC = C - B
        
        # 두 변의 수직 이등분선 벡터
        perpAB = np.array([-AB[1], AB[0]])
        perpBC = np.array([-BC[1], BC[0]])
        
        # 두 벡터가 평행한지 확인
        if np.cross(perpAB, perpBC) == 0:
            return [0,0],0
        
        # 연립 방정식을 풀어 교점(외심) 계산
        M = np.array([perpAB, -perpBC]).T
        t_s = np.linalg.solve(M, midBC - midAB)
        
        # 외심 좌표 계산
        center = midAB + t_s[0] * perpAB
        radius = np.linalg.norm(center - A)
        return center, radius

    def create_closed_vector_rdp(self, xVec, yVec, epsilon):
        if len(xVec) < 3:
            return xVec, yVec
        points = []
        for i in range(len(xVec)-1):
            points.append([xVec[i], yVec[i]])    
        return self.ramer_douglas_peucker(points, epsilon)


    def ramer_douglas_peucker(self, points, epsilon):
        
        # 시작점과 끝점을 연결하는 직선에서 가장 먼 점을 찾음
        start, end = points[0], points[-1]
        line = np.array(end) - np.array(start)
        max_dist = 0
        index = 0
        
        for i in range(1, len(points) - 1):
            # 점에서 직선까지의 거리 계산
            point = np.array(points[i])
            dist = np.linalg.norm(np.cross(line, point - start)) / np.linalg.norm(line)
            if dist > max_dist:
                max_dist = dist
                index = i

        # 최대 거리 점이 허용 오차보다 크면 해당 점을 기준으로 분할
        if max_dist > epsilon:
            left = self.ramer_douglas_peucker(points[:index + 1], epsilon)
            right = self.ramer_douglas_peucker(points[index:], epsilon)
            return left[:-1] + right
        else:
            # 시작점과 끝점만 유지
            return [start, end]  
    
        

    def create_closed_vector(self, xVec, yVec):
        points = [gp_Pnt(x, y, 0) for x, y in zip(xVec, yVec)]
        if points[0].Distance(points[-1]) < 1.e-9:
            points.pop()
        p1 : gp_Pnt = points[0]
        

        centerList = [] 
        radiusList = [] 
        
        for i in range(len(points)):
            if i == 0:
                p1 = points[-1]
                p2 = points[i]
                p3 = points[i + 1]
            elif i == len(points) - 1:
                p1 = points[i - 1]
                p2 = points[i]
                p3 = points[0]
            else:
                p1 = points[i - 1]
                p2 = points[i]
                p3 = points[i + 1]
            center,radius = self.calculate_circle_center_radius(p1, p2, p3)
            
            centerList.append(center)
            radiusList.append(radius)
            
        #for i in range(len(centerList)):
        #    print(centerList[i], radiusList[i])
        
        edgePoints = []     
        centerPrev = centerList[0]
        radiusPrev = radiusList[0]
        for i in range(len(centerList)):
            if i == 0:
                edgePoints.append([points[0]])
                centerPrev = centerList[i]
                radiusPrev = radiusList[i]
            else:
                center = centerList[i]
                radius = radiusList[i]
                
                dist = math.sqrt((center[0] - centerPrev[0])**2 + (center[1] - centerPrev[1])**2)
                distLengthRatio = dist / (radius + radiusPrev)
                radiusRatio = abs(radius-radiusPrev) / (radiusPrev+radius)
                
                if distLengthRatio < 0.05 and radiusRatio < 0.05:
                    edgePoints[-1].append(points[i])
                else:
                    edgePoints[-1].append(points[i])
                    edgePoints.append([points[i]])
                
                centerPrev = center
                radiusPrev = radius
        
        newEdgePoints = [] 
        lastPoint = None
        for i in range(len(edgePoints)):
            if len(edgePoints[i]) < 3:
                newPoints = []
                for j in range(len(edgePoints[i])):
                    newPoints.append(edgePoints[i][j])
                newEdgePoints.append(newPoints)
            else:
                newPoints = [] 
                newPoints.append(edgePoints[i][0])
                numPoints = len(edgePoints[i])            
                centernum = numPoints // 2
                newPoints.append(edgePoints[i][centernum])
                newPoints.append(edgePoints[i][-1])
                newEdgePoints.append(newPoints)
                lastPoint = newPoints[-1]
        
        newLastPoints = [lastPoint, newEdgePoints[0][0]]
        newEdgePoints.append(newLastPoints)

        '''for i in range(len(newEdgePoints)):
            for j in range(len(newEdgePoints[i])):
                print(newEdgePoints[i][j].X(), newEdgePoints[i][j].Y())
            print("----")     '''      
            
        newXVec = [] 
        newYVec = []
        
        for i in range(len(newEdgePoints)):
            for j in range(1):
                newXVec.append(newEdgePoints[i][j].X())
                newYVec.append(newEdgePoints[i][j].Y())
                if i == len(newEdgePoints)-1 and j == len(newEdgePoints[i])-2:
                    newXVec.append(newEdgePoints[i][len(newEdgePoints[i])-1].X())
                    newYVec.append(newEdgePoints[i][len(newEdgePoints[i])-1].Y())
             
        return newXVec, newYVec
    

    def create_closed_loop(self, xVec, yVec, zLoc):
        points = [gp_Pnt(x, y, zLoc) for x, y in zip(xVec, yVec)]
        if points[0].Distance(points[-1]) < 1.e-9:
            points.pop()
        p1 : gp_Pnt = points[0]
        

        centerList = [] 
        radiusList = [] 
        
        for i in range(len(points)):
            if i == 0:
                p1 = points[-1]
                p2 = points[i]
                p3 = points[i + 1]
            elif i == len(points) - 1:
                p1 = points[i - 1]
                p2 = points[i]
                p3 = points[0]
            else:
                p1 = points[i - 1]
                p2 = points[i]
                p3 = points[i + 1]
            center,radius = self.calculate_circle_center_radius(p1, p2, p3)
            
            centerList.append(center)
            radiusList.append(radius)
            
        #for i in range(len(centerList)):
        #    print(centerList[i], radiusList[i])
        
        edgePoints = []     
        centerPrev = centerList[0]
        radiusPrev = radiusList[0]
        for i in range(len(centerList)):
            if i == 0:
                edgePoints.append([points[0]])
                centerPrev = centerList[i]
                radiusPrev = radiusList[i]
            else:
                center = centerList[i]
                radius = radiusList[i]
                
                dist = math.sqrt((center[0] - centerPrev[0])**2 + (center[1] - centerPrev[1])**2)
                distLengthRatio = dist / (radius + radiusPrev)
                radiusRatio = abs(radius-radiusPrev) / (radiusPrev+radius)
                
                if distLengthRatio < 0.05 and radiusRatio < 0.05:
                    edgePoints[-1].append(points[i])
                else:
                    edgePoints[-1].append(points[i])
                    edgePoints.append([points[i]])
                
                centerPrev = center
                radiusPrev = radius

        # 경계 edge 흡수: arc 그룹(3점 이상) 양쪽의 작은 그룹(1~2점)이
        # arc의 원 위에 있으면 arc 그룹에 흡수
        changed = True
        while changed:
            changed = False
            newMerged = []
            skip = set()
            for i in range(len(edgePoints)):
                if i in skip:
                    continue
                group = edgePoints[i]
                if len(group) >= 3:
                    # 이 그룹의 중심/반경 계산
                    mid = len(group) // 2
                    gc, gr = self.calculate_circle_center_radius(group[0], group[mid], group[-1])
                    if gr > 0:
                        # 앞쪽 흡수: 이전 그룹이 1~2점이면
                        if len(newMerged) > 0 and len(newMerged[-1]) <= 2:
                            prevGroup = newMerged[-1]
                            allOnArc = True
                            for pt in prevGroup:
                                dist = math.sqrt((pt.X() - gc[0])**2 + (pt.Y() - gc[1])**2)
                                if abs(dist - gr) / gr > 0.05:
                                    allOnArc = False
                                    break
                            if allOnArc:
                                group = prevGroup + group
                                newMerged.pop()
                                changed = True
                        # 뒤쪽 흡수: 다음 그룹이 1~2점이면
                        if i + 1 < len(edgePoints) and i + 1 not in skip and len(edgePoints[i + 1]) <= 2:
                            nextGroup = edgePoints[i + 1]
                            allOnArc = True
                            for pt in nextGroup:
                                dist = math.sqrt((pt.X() - gc[0])**2 + (pt.Y() - gc[1])**2)
                                if abs(dist - gr) / gr > 0.05:
                                    allOnArc = False
                                    break
                            if allOnArc:
                                group = group + nextGroup
                                skip.add(i + 1)
                                changed = True
                newMerged.append(group)
            edgePoints = newMerged

        newEdgePoints = []
        lastPoint = None
        for i in range(len(edgePoints)):
            if len(edgePoints[i]) < 3:
                newPoints = []
                for j in range(len(edgePoints[i])):
                    newPoints.append(edgePoints[i][j])
                newEdgePoints.append(newPoints)
            else:
                newPoints = []
                newPoints.append(edgePoints[i][0])
                numPoints = len(edgePoints[i])
                centernum = numPoints // 2
                newPoints.append(edgePoints[i][centernum])
                newPoints.append(edgePoints[i][-1])
                newEdgePoints.append(newPoints)
                lastPoint = newPoints[-1]

        newLastPoints = [lastPoint, newEdgePoints[0][0]]
        newEdgePoints.append(newLastPoints)

        return newEdgePoints
    
    def GetOBShape(self, xVec, yVec, zLoc, thickness, cwList=None):
        # OB 블록은 항상 xMat/yMat 2D 구조
        isMatFormat = len(xVec) > 0 and isinstance(xVec[0], list)
        hasArc = isMatFormat and cwList is not None and len(cwList) > 0 and any(cw is not None for cw in cwList)

        # xMat 구조이면 flat 좌표로 변환
        if isMatFormat:
            flatX = []
            flatY = []
            for seg in xVec:
                if not flatX:
                    flatX.append(seg[0])
                flatX.append(seg[1])
            for seg in yVec:
                if not flatY:
                    flatY.append(seg[0])
                flatY.append(seg[1])
            xVec = flatX
            yVec = flatY

        # Arc가 있었던 OB 블록은 직선 polygon으로 처리 (create_closed_loop의 자동 arc 감지가 segfault 유발)
        if hasArc:
            return self.GetOBShapePrev(xVec, yVec, zLoc, thickness)

        solid = None
        xmin = 1.0e99
        ymin = 1.0e99
        xmax = -1.0e99
        ymax = -1.0e99
        for j in range(len(xVec)):
            xmin = min(xmin, xVec[j])
            xmax = max(xmax, xVec[j])
            ymin = min(ymin, yVec[j])
            ymax = max(ymax, yVec[j])
        if xVec[0] != xVec[-1] or yVec[0] != yVec[-1]:
            xmin = min(xmin, xVec[0])
            xmax = max(xmax, xVec[0])
            ymin = min(ymin, yVec[0])
            ymax = max(ymax, yVec[0])

        try:
            edgePoints = self.create_closed_loop(xVec, yVec, zLoc)
            for i in range(len(edgePoints)-1):
                if len(edgePoints[i]) == 1:
                    if len(edgePoints[i+1]) == 1:
                        edgePoints[i].append(edgePoints[i+1][0])
                        
                    elif edgePoints[i+1][0] == None:
                        edgePoints[i].append(edgePoints[i+1][1])
                        edgePoints[i+1] = []    
                
            wire = BRepBuilderAPI_MakeWire()
            for i in range(len(edgePoints)):
                if len(edgePoints[i]) == 2:
                    if edgePoints[i][0] == None or edgePoints[i][1] == None:
                        continue
                    edge = BRepBuilderAPI_MakeEdge(edgePoints[i][0], edgePoints[i][1]).Edge()
                    wire.Add(edge)
                elif len(edgePoints[i]) == 3:
                    arc = GC_MakeArcOfCircle(edgePoints[i][0], edgePoints[i][1], edgePoints[i][2])
                    if arc.IsDone():
                        edge = BRepBuilderAPI_MakeEdge(arc.Value()).Edge()
                        wire.Add(edge)
                    else:
                        # Arc 생성 실패 → 시작-끝 직선으로 fallback
                        edge = BRepBuilderAPI_MakeEdge(edgePoints[i][0], edgePoints[i][2]).Edge()
                        wire.Add(edge)
            closed_loop_wire = wire.Wire()
            face = BRepBuilderAPI_MakeFace(closed_loop_wire).Face()
            solid = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, thickness)).Shape()
            odbShape = ODBShape(solid, xmin,ymin,xmax,ymax)
            self.odbShapeList.append(odbShape)
        except:
            print("Error!")
            print("XVector : ", xVec)
            print("XVector : ", yVec)
        return solid

    def GetOBShapePrev(self, xVec, yVec, zLoc, thickness, cwList=None):
        shape = None
        xmin = 1.0e99
        ymin = 1.0e99
        xmax = -1.0e99
        ymax = -1.0e99

        # OB 블록은 항상 xMat/yMat 2D 구조로 저장됨 (OC 유무와 무관)
        isMatFormat = len(xVec) > 0 and isinstance(xVec[0], list)
        hasArc = isMatFormat and cwList is not None and len(cwList) > 0 and any(cw is not None for cw in cwList)

        try:
            if isMatFormat:
                # xVec/yVec are xMat/yMat (2D lists)
                wire_builder = BRepBuilderAPI_MakeWire()
                for j in range(len(xVec)):
                    seg_x = xVec[j]
                    seg_y = yVec[j]
                    for coord_x in seg_x:
                        xmin = min(xmin, coord_x)
                        xmax = max(xmax, coord_x)
                    for coord_y in seg_y:
                        ymin = min(ymin, coord_y)
                        ymax = max(ymax, coord_y)

                    if not hasArc or cwList[j] is None or len(seg_x) < 3:
                        p1 = gp_Pnt(seg_x[0], seg_y[0], zLoc)
                        p2 = gp_Pnt(seg_x[1], seg_y[1], zLoc)
                        edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
                    else:
                        pStart = gp_Pnt(seg_x[0], seg_y[0], zLoc)
                        pEnd = gp_Pnt(seg_x[1], seg_y[1], zLoc)
                        pCenter = gp_Pnt(seg_x[2], seg_y[2], zLoc)
                        rStart = pCenter.Distance(pStart)
                        rEnd = pCenter.Distance(pEnd)
                        # Arc 유효성 검증: center-start와 center-end 반경이 비슷해야 함
                        if rStart < 1.e-9 or rEnd < 1.e-9 or abs(rStart - rEnd) / max(rStart, rEnd) > 0.01:
                            # Degenerate arc → 직선으로 fallback
                            edge = BRepBuilderAPI_MakeEdge(pStart, pEnd).Edge()
                        else:
                            radius = (rStart + rEnd) / 2.0
                            if cwList[j] == 1:
                                normal = gp_Dir(0, 0, -1)
                            else:
                                normal = gp_Dir(0, 0, 1)
                            ax2 = gp_Ax2(pCenter, normal)
                            arcBuilder = BRepBuilderAPI_MakeEdge(gp_Circ(ax2, radius), pStart, pEnd)
                            if arcBuilder.IsDone():
                                edge = arcBuilder.Edge()
                            else:
                                edge = BRepBuilderAPI_MakeEdge(pStart, pEnd).Edge()
                    wire_builder.Add(edge)
                # Close the wire if not closed
                first_seg = xVec[0]
                last_seg = xVec[-1]
                first_x, first_y = first_seg[0], yVec[0][0]
                last_x = last_seg[1]
                last_y = yVec[-1][1]
                if abs(first_x - last_x) > 1.e-9 or abs(first_y - last_y) > 1.e-9:
                    p1 = gp_Pnt(last_x, last_y, zLoc)
                    p2 = gp_Pnt(first_x, first_y, zLoc)
                    edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
                    wire_builder.Add(edge)
                wire = wire_builder.Wire()
            else:
                # Legacy: xVec/yVec are flat lists (P/L/A symbols)
                polygon_builder = BRepBuilderAPI_MakePolygon()
                for j in range(len(xVec)):
                    polygon_builder.Add(gp_Pnt(xVec[j], yVec[j], zLoc))
                    xmin = min(xmin, xVec[j])
                    xmax = max(xmax, xVec[j])
                    ymin = min(ymin, yVec[j])
                    ymax = max(ymax, yVec[j])
                if xVec[0] != xVec[-1] or yVec[0] != yVec[-1]:
                    polygon_builder.Add(gp_Pnt(xVec[0], yVec[0], zLoc))
                wire = polygon_builder.Wire()

            face_builder = BRepBuilderAPI_MakeFace(wire, True)
            face = face_builder.Face()
            prism_builder = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, thickness))
            shape = prism_builder.Shape()

            odbShape = ODBShape(shape, xmin, ymin, xmax, ymax)
            self.odbShapeList.append(odbShape)
        except:
            print("Error!")
            print("XVector : ", xVec)
            print("YVector : ", yVec)
        return shape
    
    def GetShapewithSymbol(self, xVec, yVec, aSymbol, zLoc, thickness):
        # Point
        if len(xVec) == 1:
            return self.GetPointShape(xVec, yVec, aSymbol, zLoc, thickness)
        # Line
        elif len(xVec) == 2:

            return self.GetLineShape(xVec, yVec, aSymbol, zLoc, thickness)
        # Arc
        elif len(xVec) == 3:
            pass 
        print("Error! The number of points is not correct.")
        return None

    def GetPointShape(self, xVec, yVec, aSymbol, zLoc, thickness):
        shapeList = []         
        xLoc = xVec[0] 
        yLoc = yVec[0]
        xmin = 1.e99
        ymin = 1.e99
        xmax = -1.e99
        ymax = -1.e99
      

        if aSymbol.type == "Round":
            radius = aSymbol.valueList[0]/2.0
            xmin = xLoc - radius
            xmax = xLoc + radius
            ymin = yLoc - radius
            ymax = yLoc + radius

            # Make a circle
            center = gp_Pnt(xLoc, yLoc, zLoc)
            normal = gp_Dir(0, 0, 1)
            
            circle_geom = gp_Circ(gp_Ax2(center, normal), radius)            
            circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
            circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
            circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(circle_face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)
        
        elif aSymbol.type == "Square":
            xSize = aSymbol.valueList[0]/2.0
            ySize = aSymbol.valueList[0]/2.0
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize

            # Make a square
            p1 = gp_Pnt(xLoc - xSize, yLoc - ySize, zLoc)
            p2 = gp_Pnt(xLoc + xSize, yLoc - ySize, zLoc)
            p3 = gp_Pnt(xLoc + xSize, yLoc + ySize, zLoc)
            p4 = gp_Pnt(xLoc - xSize, yLoc + ySize, zLoc)
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
            edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
            wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3, edge4).Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)

        elif aSymbol.type == "Rectangle":
            xSize = aSymbol.valueList[0]/2.0
            ySize = aSymbol.valueList[1]/2.0
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize

            # Make a rectangle
            p1 = gp_Pnt(xLoc - xSize, yLoc - ySize, zLoc)
            p2 = gp_Pnt(xLoc + xSize, yLoc - ySize, zLoc)
            p3 = gp_Pnt(xLoc + xSize, yLoc + ySize, zLoc)
            p4 = gp_Pnt(xLoc - xSize, yLoc + ySize, zLoc)
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
            edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
            wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3, edge4).Wire()
            face = BRepBuilderAPI_MakeFace(wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)
            pass
        elif aSymbol.type == "RoundedRectangle": 
            #print("RoundedRectangle is not supported yet.")
            xSize = aSymbol.valueList[0]/2.0
            ySize = aSymbol.valueList[1]/2.0
            radius = aSymbol.valueList[2]
            radiuslocation = aSymbol.valueList[3]
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            xminpradius = xLoc - xSize + radius
            xmaxpradius = xLoc + xSize - radius
            yminpradius = yLoc - ySize + radius
            ymaxpradius = yLoc + ySize - radius
            # Make a rectangle with rounded corner 
            # radiuslocation 1 : top right 2 : top left 3 : bottom left 4 : bottom right
            
            edgeList = []            
            normal_vector = gp_Dir(0,0,1)            
            if "1" in radiuslocation:
                p0 = gp_Pnt(xmax, ymaxpradius, zLoc)
                p1 = gp_Pnt(xmaxpradius, ymaxpradius, zLoc)
                p2 = gp_Pnt(xmaxpradius, ymax, zLoc)                
                coordinate_system = gp_Ax2(p1,normal_vector)                
                arc1 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p0,p2)
                #edge1 = BRepBuilderAPI_MakeEdge(arc1.Value()).Edge()
            else:
                p0 = gp_Pnt(xmax, ymax, zLoc)
                p2 = gp_Pnt(xmax, ymax, zLoc)
                arc1 = None
            if arc1 is not None:
                edgeList.append(arc1.Edge())
                
            if "2" in radiuslocation:
                p3 = gp_Pnt(xminpradius, ymax, zLoc)
                p4 = gp_Pnt(xminpradius, ymaxpradius, zLoc)
                p5 = gp_Pnt(xmin, ymaxpradius, zLoc)
                coordinate_system = gp_Ax2(p4,normal_vector)                
                arc2 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p3,p5)
                
            else:
                p3 = gp_Pnt(xmin, ymax, zLoc)
                p5 = gp_Pnt(xmin, ymax, zLoc)
                arc2 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p2,p3).Edge())
            if arc2 is not None:
                edgeList.append(arc2.Edge())
                            
            if "3" in radiuslocation:
                p6 = gp_Pnt(xmin, yminpradius, zLoc)
                p7 = gp_Pnt(xminpradius, yminpradius, zLoc)
                p8 = gp_Pnt(xminpradius, ymin, zLoc)                
                coordinate_system = gp_Ax2(p7,normal_vector)
                arc3 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p6,p8)    
            else:
                p6 = gp_Pnt(xmin, ymin, zLoc)
                p8 = gp_Pnt(xmin, ymin, zLoc)
                arc3 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p5,p6).Edge())
            if arc3 is not None:
                edgeList.append(arc3.Edge())
            
            
            if "4" in radiuslocation:
                p9 = gp_Pnt(xmaxpradius, ymin, zLoc)
                p10 = gp_Pnt(xmaxpradius, yminpradius, zLoc)
                p11 = gp_Pnt(xmax, yminpradius, zLoc)
                coordinate_system = gp_Ax2(p10,normal_vector)
                arc4 = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius),p9,p11)                
            else:
                p9 = gp_Pnt(xmax, ymin, zLoc)
                p11 = gp_Pnt(xmax, ymin, zLoc)
                arc4 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p8,p9).Edge())
            if arc4 is not None:
                edgeList.append(arc4.Edge())                
            edgeList.append(BRepBuilderAPI_MakeEdge(p11,p0).Edge())
            
            wire = BRepBuilderAPI_MakeWire()
            for edge in edgeList:
                wire.Add(edge)
            face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
            vec = gp_Vec(0,0,thickness)
            prismShape = BRepPrimAPI_MakePrism(face,vec)
            prismShape.Build()
            shape = prismShape.Shape()
            shapeList.append(shape)
            pass
        elif aSymbol.type == "Oval":
            #print("Oval is not supported yet.")
            r1 = aSymbol.valueList[0]/2.0
            r2 = aSymbol.valueList[1]/2.0                        
            if r1>r2: 
                major_r1 = r1
                major_r2 = r2
                xdir = gp_Dir(1,0,0)
            else:
                major_r1 = r2
                major_r2 = r1
                xdir = gp_Dir(0,1,0)
                
            
            center_point = gp_Pnt(xLoc, yLoc, zLoc)
            major_axis = gp_Dir(0,0,1)
            axis2_placement = gp_Ax2(center_point, major_axis, xdir)
            
            ellipse_geom = gp_Elips(axis2_placement, major_r1, major_r2)
            ellipse_edge = BRepBuilderAPI_MakeEdge(ellipse_geom).Edge()
            ellipse_wire = BRepBuilderAPI_MakeWire(ellipse_edge).Wire()
            ellipse_face = BRepBuilderAPI_MakeFace(ellipse_wire).Face()
            vec = gp_Vec(0,0,thickness)
            cylinder_shape = BRepPrimAPI_MakePrism(ellipse_face,vec)
            cylinder_shape.Build()
            shape = cylinder_shape.Shape()
            shapeList.append(shape)
            pass                             
                        
        elif aSymbol.type == "ChemferedRectangle":
            #print("ChemferedRectangle is not supported yet.")
            xSize = aSymbol.valueList[0]/2.0
            ySize = aSymbol.valueList[1]/2.0
            radius = aSymbol.valueList[2]
            radiuslocation = aSymbol.valueList[3]
            xmin = xLoc - xSize
            xmax = xLoc + xSize
            ymin = yLoc - ySize
            ymax = yLoc + ySize
            xminpradius = xLoc - xSize + radius
            xmaxpradius = xLoc + xSize - radius
            yminpradius = yLoc - ySize + radius
            ymaxpradius = yLoc + ySize - radius
            # Make a rectangle with chemfered corner
            # radiuslocation 1 : top right 2 : top left 3 : bottom left 4 : bottom right
            edgeList = [] 
            if "1" in radiuslocation:
                p0 = gp_Pnt(xmax, ymaxpradius, zLoc)
                p1 = gp_Pnt(xmaxpradius, ymax, zLoc)
                edge1 = BRepBuilderAPI_MakeEdge(p0, p1).Edge()
            else:
                p0 = gp_Pnt(xmax, ymax, zLoc)
                p1 = gp_Pnt(xmax, ymax, zLoc)
                edge1 = None
            if edge1 is not None:
                edgeList.append(edge1)
            
            if "2" in radiuslocation:
                p2 = gp_Pnt(xminpradius, ymax, zLoc)
                p3 = gp_Pnt(xmin, ymaxpradius, zLoc)
                edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            else:
                p2 = gp_Pnt(xmin, ymax, zLoc)
                p3 = gp_Pnt(xmin, ymax, zLoc)
                edge2 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p1, p2).Edge())
            if edge2 is not None:
                edgeList.append(edge2)
                
            if "3" in radiuslocation:
                p4 = gp_Pnt(xmin, yminpradius, zLoc)
                p5 = gp_Pnt(xminpradius, ymin, zLoc)
                edge3 = BRepBuilderAPI_MakeEdge(p4, p5).Edge()
            else:
                p4 = gp_Pnt(xmin, ymin, zLoc)
                p5 = gp_Pnt(xmin, ymin, zLoc)
                edge3 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p3, p4).Edge())
            if edge3 is not None:
                edgeList.append(edge3)
            
            if "4" in radiuslocation:
                p6 = gp_Pnt(xmaxpradius, ymin, zLoc)
                p7 = gp_Pnt(xmax, yminpradius, zLoc)
                edge4 = BRepBuilderAPI_MakeEdge(p6, p7).Edge()
            else:
                p6 = gp_Pnt(xmax, ymin, zLoc)
                p7 = gp_Pnt(xmax, ymin, zLoc)
                edge4 = None
            edgeList.append(BRepBuilderAPI_MakeEdge(p5, p6).Edge())
            if edge4 is not None:
                edgeList.append(edge4)
            edgeList.append(BRepBuilderAPI_MakeEdge(p7, p0).Edge())
            
            wire = BRepBuilderAPI_MakeWire()
            for edge in edgeList:
                wire.Add(edge)
            face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
            vec = gp_Vec(0,0,thickness)
            prismShape = BRepPrimAPI_MakePrism(face,vec)
            prismShape.Build()
            shape = prismShape.Shape()
            shapeList.append(shape)                                      
            pass
        else:                      
                
            subShapeList = aSymbol.GetShape(xLoc, yLoc, zLoc, thickness)
            xmin, ymin, xmax, ymax = aSymbol.GetMinMax()
            if subShapeList is not None:
                for subShape in subShapeList:
                    shapeList.append(subShape)
                    odbShape = ODBShape(subShape, xmin+xLoc,ymin+yLoc,xmax+xLoc,ymax+yLoc)
                    self.odbShapeList.append(odbShape)
                    
                shape = None
            else:
                print("Error! Unknown symbol type.")
                print("{0} is not supported yet.".format(aSymbol.name))
                shape = None
        if shape is not None:
            odbShape = ODBShape(shape, xmin,ymin,xmax,ymax)
            self.odbShapeList.append(odbShape)
        
        return shapeList

    def GetLineShape(self, xVec, yVec, aSymbol, zLoc, thickness):
        shapeList = []         
        x1 = xVec[0] 
        y1 = yVec[0]
        x2 = xVec[1]
        y2 = yVec[1]
        xmin = 1.e99
        ymin = 1.e99
        xmax = -1.e99
        ymax = -1.e99
        
        distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if distance == 0:
            return self.GetPointShape(xVec, yVec, aSymbol, zLoc, thickness)
        try:
            if aSymbol.type == "Round":
                radius = aSymbol.valueList[0]/2.0            
                dir = gp_Dir(x2-x1, y2-y1, 0)
                norm = dir.Crossed(gp_Dir(0,0,1))
                normalizeVec = gp_Vec(norm)
                normalizeVec.Scale(radius)
                tangentialVec = gp_Vec(x2-x1, y2-y1, 0)
                tangentialVec.Normalize()
                tangentialVec.Scale(radius)
                #left bottom point
                p1 = gp_Pnt(x1, y1, zLoc)
                #right bottom point
                p2 = gp_Pnt(x2, y2, zLoc)
                #point pb1, pb2, ... pb6
                pb1 = gp_Pnt(x1, y1, zLoc)
                pb1.Translate(normalizeVec)
                pb2 = gp_Pnt(x1, y1, zLoc)
                pb2.Translate(tangentialVec.Reversed())
                pb3 = gp_Pnt(x1, y1, zLoc)
                pb3.Translate(normalizeVec.Reversed())

                pb4 = gp_Pnt(x2, y2, zLoc)
                pb4.Translate(normalizeVec.Reversed())
                pb5 = gp_Pnt(x2, y2, zLoc)
                pb5.Translate(tangentialVec)
                pb6 = gp_Pnt(x2, y2, zLoc)
                pb6.Translate(normalizeVec)

                xmin = min(x1,x2) - radius
                xmax = max(x1,x2) + radius
                ymin = min(y1,y2) - radius
                ymax = max(y1,y2) + radius            

                arc1 = GC_MakeArcOfCircle(pb1,pb2,pb3)
                arc2 = GC_MakeArcOfCircle(pb4,pb5,pb6)
                arc_edge1 = BRepBuilderAPI_MakeEdge(arc1.Value()).Edge()
                arc_edge2 = BRepBuilderAPI_MakeEdge(arc2.Value()).Edge()
                line1 = BRepBuilderAPI_MakeEdge(pb3, pb4).Edge()
                line2 = BRepBuilderAPI_MakeEdge(pb6, pb1).Edge()

                w = BRepBuilderAPI_MakeWire()
                w.Add(arc_edge1)
                w.Add(line1)
                w.Add(arc_edge2)
                w.Add(line2)
                w.Build()
                f = BRepBuilderAPI_MakeFace(w.Wire()).Face()
                vec = gp_Vec(0,0,thickness)
                cylinder_shape = BRepPrimAPI_MakePrism(f,vec)
                cylinder_shape.Build()
                shape = cylinder_shape.Shape()
                shapeList.append(shape)

            elif aSymbol.type == "Square":
                xSize = aSymbol.valueList[0]/2.0
                ySize = aSymbol.valueList[0]/2.0
                dir = gp_Dir(x2-x1, y2-y1, 0)
                norm = dir.Crossed(gp_Dir(0,0,1))
                normalizeVec = gp_Vec(norm)
                normalizeVec.Scale(ySize)
                tangentialVec = gp_Vec(x2-x1, y2-y1, 0)
                tangentialVec.Normalize()
                tangentialVec.Scale(xSize)
                #left bottom point
                p1 = gp_Pnt(x1-tangentialVec.X()-normalizeVec.X(), y1-tangentialVec.Y()-normalizeVec.Y(), zLoc)
                #right bottom point
                p2 = gp_Pnt(x2+tangentialVec.X()-normalizeVec.X(), y2+tangentialVec.Y()-normalizeVec.Y(), zLoc)
                #right top point
                p3 = gp_Pnt(x2+tangentialVec.X()+normalizeVec.X(), y2+tangentialVec.Y()+normalizeVec.Y(), zLoc)
                #left top point
                p4 = gp_Pnt(x1-tangentialVec.X()+normalizeVec.X(), y1-tangentialVec.Y()+normalizeVec.Y(), zLoc)

                xmin = min(p1.X(),p2.X(),p3.X(),p4.X())
                xmax = max(p1.X(),p2.X(),p3.X(),p4.X())
                ymin = min(p1.Y(),p2.Y(),p3.Y(),p4.Y())
                ymax = max(p1.Y(),p2.Y(),p3.Y(),p4.Y())

                edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
                edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
                edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
                edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
                wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3, edge4).Wire()
                face = BRepBuilderAPI_MakeFace(wire).Face()
                vec = gp_Vec(0,0,thickness)
                cylinder_shape = BRepPrimAPI_MakePrism(face,vec)
                cylinder_shape.Build()
                shape = cylinder_shape.Shape()
                shapeList.append(shape)

            elif aSymbol.type == "RoundedRectangle": 
                print("RoundedRectangle is not supported yet.")
                shape = None
                pass
            elif aSymbol.type == "Oval":
                print("Oval is not supported yet.")
                shape = None
                pass
            elif aSymbol.type == "ChemferedRectangle":
                print("ChemferedRectangle is not supported yet.")
                shape = None
                pass

            if shape is not None:
                odbShape = ODBShape(shape, xmin,ymin,xmax,ymax)
                self.odbShapeList.append(odbShape)            
        except:
            print("Error!")
            print("XVector : ", xVec)
            print("XVector : ", yVec)
        return shapeList

if __name__ == '__main__':

    odbFile = "odb.zip"
    odbPath = os.path.join(os.getcwd(), odbFile)
    zLocation = 0.8
    thickness = [0.2, 1.2, 0.2] 
    board : PrintedCircuitBoard = PrintedCircuitBoard()
    board.ImportODBZip(odbPath)
    board.SetAISLayers(zLocation,thickness)    
    shapeList = board.GenerateExternalSolid()

    #shapeList = board.GeneratePPG(5.4,4.3,6.7,6.5)
    #board.ExportEachShape("TestBoard.stp",shape)    
    # Initialize the display
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:
        # 정상 GUI 모드
        from OCC.Display.SimpleGui import init_display
        display, start_display, add_menu, add_function_to_menu = init_display()
    '''
    for shape in shapeList:
        if shape is not None:
            display.DisplayShape(shape, update=True)
    display.FitAll()
    start_display()
    '''
    #for shape in shapeList:
    #    if shape is not None:
    #        display.DisplayShape(shape, update=True)
    #display.FitAll()
    
    #shapeList = board.GenerateCombinedSolid()
    #shapeList = board.ExportShape("TestBoard.stp") #board.GenerateCombinedSolid()
    shapeList = board.GenerateSolid()
    shapeList = board.ExportShapeArea("TestBoard.stp",5.4,4.3,6.7,6.5) 
    #shapeList = board.ExportShapeArea("TestBoard.stp",0,0,20,20)

   

    # Display the wire
    #display.DisplayShape(shapeList, update=True)

    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:    
        for shape in shapeList:
            if shape is not None:
                display.DisplayShape(shape, update=True)
        display.FitAll()

        # Start the display
        start_display()



    print(odbPath)


    

 