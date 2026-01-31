import os
import subprocess
import zipfile
from unlzw3 import unlzw
from os.path import dirname
from os.path import join
import zipfile
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Builder
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

if __name__ == '__main__':
    from Polygon import Polygon2D as Poly
    from Package import Package
    from Component import Component, PackageComponent, PCBComponent
    from PolygonManager import PolygonManager2D as PolygonManager
    from PCBManager import PCBManager
    from PackageManager import PackageManager
    from ComponentManager import ComponentManager
    from Layer import PrintedCircuitBoard
else:
    from KooODBCADManager.Polygon import Polygon2D as Poly
    from KooODBCADManager.Package import Package
    from KooODBCADManager.Component import Component, PackageComponent, PCBComponent
    from KooODBCADManager.PolygonManager import PolygonManager2D as PolygonManager
    from KooODBCADManager.PCBManager import PCBManager
    from KooODBCADManager.PackageManager import PackageManager
    from KooODBCADManager.ComponentManager import ComponentManager
    from KooODBCADManager.Layer import PrintedCircuitBoard


class ODBCADManager():
    
    def __init__(self):
        self.polygonManager = PolygonManager()
        self.packageManager = PackageManager(self.polygonManager)
        self.pcbManager = PCBManager(self.polygonManager)
        self.componentManager = []

        ## PCB Array list 
        self.PCBArrayFileList = []        
        self.PCBArrayLocationList = []
        self.PCBArrayRotationList = [] 
        self.PCBArrayMirrorList = []
        self.PCBArrayLayupList = [] 
        self.PCBArrayThicknessList = []
        self.PCBArrayMaterialFileList = [] 
        self.PCBArrayPatternFeaturesList = [] 
        self.PCBArraySymbolsFolderList = []
        self.PCBArrayWarpageList = []

        ## ODB File list
        self.ODBFile = [] 
        self.zLocationODBFile = [] 
        self.thicknessODBFile = [] 
        self.thicknessSolderPaste = 0.0
        self.thicknessSolderMask = 0.0

        ## Detail Model 
        self.detailOption = False
        self.minimumSize = 0.0        
        self.xmin = -1.e99
        self.xmax = 1.e99 
        self.ymin = -1.e99
        self.ymax = 1.e99
        self.detailPADName = {}
        self.udPKGName = {}
        self.skipLayerList = []
        self.unitamp = 25.4

        self.exportPKGOption = False
        self.exportPKGFolderName = "PackageExported"

        ## PCB Unit list  
        self.PCBFileList = []
        self.PCBLocationList = [] 
        self.PCBRotationList = [] 
        self.PCBMirrorList = []
        self.PCBLayupList = [] 
        self.PCBThicknessList = []
        self.PCBMaterialFileList = [] 
        self.PCBPatternFeaturesList = [] 
        self.PCBSymbolsFolderList = []
        self.PCBWarpageList = []

        self.PackageFileList = []
        self.PackageSolderThickness = []
        self.ComponentTopFileList = []
        self.ComponentBottomFileList = []

        self.shapeList = [] 



    
    def ImportModellingOptions(self, path, fileName):
        self.inputFileName = fileName
        if len(fileName) == 0:
            return None
        with open(join(path,fileName)) as stream:            
            sline = stream.readline()
            sline = sline.lstrip()
            while not self.is_eof(stream):                
                if len(sline) == 0:
                    sline = stream.readline()
                    sline = sline.lstrip()            
                    pass
                elif len(sline)>0:
                    if sline.find("#") == 0:
                        pass
                    elif sline.find("*ArrayPCB") == 0:
                        print("Array PCB options found")
                        patternFeatures = {}
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                print("Array PCB options end")
                                break
                            elif sline.find("FileName") == 0:
                                self.PCBArrayFileList.append(svector[1])
                                print("Array PCB file name: ", svector[1])
                                pass
                            elif sline.find("Location") == 0:
                                self.PCBArrayLocationList.append([float(x) for x in svector[1:]])
                                print("Array PCB location: ", svector[1:])
                                pass
                            elif sline.find("Rotation") == 0:
                                self.PCBArrayRotationList.append(int(svector[1]))
                                print("Array PCB rotation: ", svector[1])
                                pass
                            elif sline.find("Mirror") == 0:
                                if svector[1] == "True":
                                    self.PCBArrayMirrorList.append(True)
                                else:
                                    self.PCBArrayMirrorList.append(False)
                                print("Array PCB mirror: ", svector[1])
                                pass
                            elif sline.find("Layup") == 0:
                                layups = svector[1:]
                                self.PCBArrayLayupList.append(layups)
                                print("Array PCB layup: ", layups)
                                pass
                            elif sline.find("Thickness") == 0:
                                thickness = svector[1:]
                                thickness = [float(x) for x in thickness]
                                thickness = [x*1000 for x in thickness]
                                self.PCBArrayThicknessList.append(thickness)
                                print("Array PCB thickness: ", thickness)                            
                                pass
                            elif sline.find("MaterialFileName") == 0:
                                self.PCBArrayMaterialFileList.append(svector[1])
                                print("Array PCB material file name: ", svector[1])
                                pass
                            elif sline.find("PatternFeatures") == 0:
                                patternFeatures[svector[2]] = svector[1]
                                print("Array PCB pattern feature: ", svector[2], svector[1])
                                pass
                            elif sline.find("SymbolsFolder") == 0:
                                self.PCBArraySymbolsFolderList.append(svector[1])
                                print("Array PCB symbols folder: ", svector[1])
                                pass
                            elif sline.find("Warpage") == 0:
                                self.PCBArrayWarpageList.append(svector[1])
                                print("Array PCB warpage: ", svector[1])
                                pass
                        self.PCBArrayPatternFeaturesList.append(patternFeatures)
                    elif sline.find("*PCB") == 0:
                        print("PCB options found")
                        patternFeatures = {}
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                print("PCB options end")
                                break
                            elif sline.find("FileName") == 0:
                                self.PCBFileList.append(svector[1])
                                print("PCB file name: ", svector[1])
                                pass
                            elif sline.find("Location") == 0:
                                self.PCBLocationList.append([float(x) for x in svector[1:]])
                                print("PCB location: ", svector[1:])
                                pass
                            elif sline.find("Rotation") == 0:
                                self.PCBRotationList.append(int(svector[1]))
                                print("PCB rotation: ", svector[1])
                                pass
                            elif sline.find("Mirror") == 0:
                                if svector[1] == "True":
                                    self.PCBMirrorList.append(True)
                                else:
                                    self.PCBMirrorList.append(False)
                                print("PCB mirror: ", svector[1])
                                pass
                            elif sline.find("Layup") == 0:
                                layups = svector[1:]
                                self.PCBLayupList.append(layups)
                                print("PCB layup: ", layups)
                                pass
                            elif sline.find("Thickness") == 0:
                                thickness = svector[1:]
                                thickness = [float(x) for x in thickness]
                                thickness = [x*1000 for x in thickness]
                                self.PCBThicknessList.append(thickness)
                                print("PCB thickness: ", thickness)
                                pass
                            elif sline.find("MaterialFileName") == 0:
                                self.PCBMaterialFileList.append(svector[1])
                                print("PCB material file name: ", svector[1])
                                pass
                            elif sline.find("PatternFeatures") == 0:
                                patternFeatures[svector[2]] = svector[1]
                                print("PCB pattern feature: ", svector[2], ',', svector[1])
                                pass             
                            elif sline.find("SymbolsFolder") == 0:
                                self.PCBSymbolsFolderList.append(svector[1])
                                print("PCB symbols folder: ", svector[1])
                                pass     
                            elif sline.find("Warpage") == 0:
                                self.PCBWarpageList.append(svector[1])
                                print("PCB warpage: ", svector[1])
                                pass                       
                        self.PCBPatternFeaturesList.append(patternFeatures)
                    elif sline.find("*Packages") ==0:
                        solderThickness = {}
                        print("Packages options found")
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                break
                            elif sline.find("FileName") == 0:
                                self.PackageFileList.append(svector[1])
                                print("Package file name: ", svector[1])
                                pass
                            elif sline.find("SolderThickness") == 0:
                                solderThickness[svector[1]] = float(svector[2])
                                print("Package solder thickness: ", svector[1], ',', svector[2])
                                pass                            
                        self.PackageSolderThickness.append(solderThickness)
                        print("Packages options end")
                    elif sline.find("*ComponentTop") ==0:
                        print("Component top options found")
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                break
                            elif sline.find("FileName") == 0:
                                self.ComponentTopFileList.append(svector[1])
                                print("Component top file name: ", svector[1])
                                pass
                        print("Component top options end")
                        pass
                    elif sline.find("*ComponentBottom") ==0:
                        print("Component bottom options found")
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                break
                            elif sline.find("FileName") == 0:
                                self.ComponentBottomFileList.append(svector[1])
                                print("Component bottom file name: ", svector[1])
                                pass
                        print("Component bottom options end")
                        pass
                    elif sline.find("*ODB") == 0:
                        print("ODB options found")
                        while True:
                            sline = stream.readline()
                            sline = sline.lstrip()
                            sline = sline.replace('\n','')  
                            svector = sline.split(',')
                            if len(sline) == 0:
                                continue
                            elif sline.find("*") == 0:
                                break
                            elif sline.find("ODBFile") == 0:
                                self.ODBFile.append(svector[1])
                                print("ODB file name: ", svector[1])
                                pass
                            elif sline.find("BoundaryBox") == 0:
                                self.detailOption = True
                                self.xmin = float(svector[1])*1000.0
                                self.ymin = float(svector[2])*1000.0
                                self.xmax = float(svector[3])*1000.0                                
                                self.ymax = float(svector[4])*1000.0

                                print("ODB BoundaryBox: ", svector[1], ',', svector[2], ',', svector[3], ',', svector[4])
                                pass                               
                            elif sline.find("ZLocation") == 0:
                                self.zLocationODBFile.append(float(svector[1]))
                                print("ODB ZLocation: ", svector[1])
                            elif sline.find("ThicknessSolderPaste") == 0:
                                thickness = svector[1]
                                self.thicknessSolderPaste = float(thickness)*1000.0
                                pass
                            elif sline.find("ThicknessSolderMask") == 0:
                                thickness = svector[1]
                                self.thicknessSolderMask = float(thickness)*1000.0
                                pass
                            elif sline.find("Thickness") == 0:
                                #self.thicknessODBFile.append(float(svector[1]))
                                thickness = svector[1:]
                                thickness = [float(x) for x in thickness]
                                thickness = [x*1000 for x in thickness]
                                self.thicknessODBFile.append(thickness)
                                print("PCB thickness: ", thickness)                            
                            elif sline.find("DetailPAD") == 0:                                
                                self.detailPADName[svector[1]] = 1                                
                                print("ODB DetailPAD: ", svector[1])
                                pass
                            elif sline.find("MinimumSize") == 0:
                                self.minimumSize = float(svector[1])*1000.0                                
                                print("ODB MinimumSize: ", svector[1])
                                pass
                            elif sline.find("UndefinedUnitAmps") == 0:
                                self.unitamp = float(svector[1])
                                print("ODB UndefinedUnitAmps: ", svector[1])
                                pass  
                            elif sline.find("ExportPackage") == 0:
                                if len(svector) < 2:
                                    print("ExportPackage option is not enough")
                                    continue
                                if "true" in svector[1].lower():
                                    self.exportPKGOption = True
                                else:
                                    self.exportPKGOption = False
                                if len(svector) > 2:                                    
                                    self.exportPKGFolderName = svector[2]
                                else:
                                    self.exportPKGFolderName = "PackageExported"
                                print("ExportPackage: ", svector[1])
                                print("Exported Package Folder Name: ", self.exportPKGFolderName)

                                
                                
                            elif sline.find("SkipLayer") == 0:
                                self.skipLayerList.append(svector[1].strip())
                                print("ODB SkipLayer: ", svector[1])
                            elif sline.find("PKG") == 0:
                                if len(svector) < 3:
                                    print("PKG option is not enough")
                                    continue
                                self.udPKGName[svector[1]] = svector[2]
                                



                        print("ODB options end")                        

                    else:
                        sline = stream.readline()
                        sline = sline.lstrip()
                else:
                    sline = stream.readline()
                    sline = sline.lstrip()
        print("Import modelling options end")            
        pass

    def ImportArrayPCB(self):
        print("Import array PCB start")
        curPath = os.getcwd()

    def ImportArrayPCBs(self):
        print("Import array PCBs start")
        curPath = os.getcwd()
        for i in range(len(self.PCBArrayFileList)):
            print("Import array PCB: ", self.PCBArrayFileList[i])
            curPCB = self.load_arrayPCB(curPath, self.PCBArrayFileList[i])
            if curPCB != None:
                curPCB.SetLayup(self.PCBArrayLayupList[i])
                curPCB.SetThickness(self.PCBArrayThicknessList[i])
                curPCB.SetMaterialFile(self.PCBArrayMaterialFileList[i])
                curPCB.SetPatternFeatures(self.PCBArrayPatternFeaturesList[i])
                curPCB.SetSymbolsFolder(self.PCBArraySymbolsFolderList[i])
                curPCB.SetLocation(self.PCBArrayLocationList[i])
                curPCB.SetRotation(self.PCBArrayRotationList[i])                
                curPCB.SetMirror(self.PCBArrayMirrorList[i])                
                curPCB.SetWarpageFile(self.PCBArrayWarpageList[i])
                
                print("Array PCB: ", self.PCBArrayFileList[i])
            ## Visualization 
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
            #curShapeList = curPCB.Generate()            
            if self.PCBArrayWarpageList[i] == "None":
                curShapeList = curPCB.Generate()
            else:
                curShapeList = curPCB.GenerateSolidwithWarpage()            

            if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
                for curShape in curShapeList:
                    if curShape != None:
                        display.DisplayShape(curShape, update=True)
                display.FitAll()
                start_display()
            #if __name__ == '__main__':
            from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer            
            print("Save ArrayPCB: ", self.PCBArrayFileList[i])
            fileName = "ArrayPCB_" + str(i) + ".stp"
            step_writer = STEPControl_Writer()
            for curShape in curShapeList:
                if curShape != None:
                    step_writer.Transfer(curShape, STEPControl_AsIs)
            status = step_writer.Write(fileName)
            if status == 0:  # check status
                print("Error: can't write file.")
            else:
                print("Done.")


    def ImportPCBs(self):
        print("Import PCBs start")
        curPath = os.getcwd()
        for i in range(len(self.PCBFileList)):
            print("Import PCB: ", self.PCBFileList[i])
            curPCB = self.load_PCB(curPath, self.PCBFileList[i])
            if curPCB != None:                
                curPCB.SetLayup(self.PCBLayupList[i])
                curPCB.SetThickness(self.PCBThicknessList[i])
                curPCB.SetMaterialFile(self.PCBMaterialFileList[i])
                curPCB.SetPatternFeatures(self.PCBPatternFeaturesList[i])
                curPCB.SetSymbolsFolder(self.PCBSymbolsFolderList[i])
                curPCB.SetLocation(self.PCBLocationList[i])
                curPCB.SetRotation(self.PCBRotationList[i])
                curPCB.SetMirror(self.PCBMirrorList[i])
                curPCB.SetWarpageFile(self.PCBWarpageList[i])
                print("PCB: ", self.PCBFileList[i], " is created")
            
            ## Visualization 
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

            # solid 생성             
            #curShapeList = curPCB.Generate()
            # warpage 포함 Solid 생성 
            if self.PCBWarpageList[i] == "None":
                curShapeList = curPCB.Generate()
            else:
                curShapeList = curPCB.GenerateSolidwithSurface()            
            # warpage 포함 Surface 생성 
            #curShapeList = curPCB.GenerateSurfacewithWarpage()
            if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
                for curShape in curShapeList:
                    display.DisplayShape(curShape, update=True)
            
                display.FitAll()
                start_display()    
            ## Save a File  
            #if __name__ == '__main__':
            from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer                            
            from OCC.Core.STEPControl import STEPControl_ManifoldSolidBrep
            from OCC.Core.STEPControl import STEPControl_ShellBasedSurfaceModel
            print("Save PCB: ", self.PCBFileList[i])
            fileName = "PCB_" + str(i) + ".stp"
            step_writer = STEPControl_Writer()
            ii = 0
            for curShape in curShapeList:
                ii = ii + 1                     
                step_writer.Transfer(curShape, STEPControl_AsIs)
                print(ii,'th Shape are saved')
            
            status = step_writer.Write(fileName)


            if status == 0:  # check status
                print("Error: can't write file.")
            else:
                print("Done.")
            
                        

        print("Import PCBs end")    
  
    def ImportPCBDetail(self):
        print("Import PCB detail start")
        curPath = os.getcwd()
        totalShapeList = [] 
        for i in range(len(self.ODBFile)):
            odbPath = os.path.join(curPath, self.ODBFile[i])
                        
            print("Import PCB detail: ", self.ODBFile[i])
            board : PrintedCircuitBoard = PrintedCircuitBoard()
            board.ImportODBZip(odbPath)                        
            board.SetAISLayers(self.zLocationODBFile[i],self.thicknessODBFile[i], self.thicknessSolderPaste, self.thicknessSolderMask) 
            #board.SetAISLayersOriginal(self.zLocationODBFile[i],self.thicknessODBFile[i])
            
            if self.detailOption == True:
                #change zip to stp 
                #odbSTPPath = odbPath.replace(".zip","_pcb_multiscale.stp")
                odbSTPPath = self.inputFileName.replace(".txt","_pcb_multiscale.stp")
                shape = board.GenerateSolid()
                shapeList = board.ExportShapeArea(odbSTPPath,self.xmin,self.ymin,self.xmax,self.ymax, self.skipLayerList)
                totalShapeList.extend(shapeList)
            else:
                #change zip to stp 
                #odbSTPPath = odbPath.replace(".zip","_pcb.stp")
                odbSTPPath = self.inputFileName.replace(".txt","_pcb.stp")
                shapeList = board.ExportShapeExternal(odbSTPPath)
                totalShapeList.extend(shapeList)
                
            unitFeaturePath = self.inputFileName.replace(".txt","_unitfeature.txt")
            board.ExportUnitFeature(unitFeaturePath, self.zLocationODBFile[i], self.thicknessODBFile[i], self.thicknessSolderPaste, self.thicknessSolderMask)
            
            #from OCC.Display.SimpleGui import init_display
            #display, start_display, add_menu, add_function_to_menu = init_display()
            #for curShape in shapeList:
            #    if curShape != None:
            #        display.DisplayShape(curShape, update=True)
            #display.FitAll()
            #start_display()   
        return totalShapeList

    def ExtractTGZ(self, fileName, extract_path="."):
        import tarfile
        if not os.path.exists(fileName):
            raise FileNotFoundError(f"File {fileName} does not exist.")
        
        with tarfile.open(fileName, "r:gz") as tar:
            tar.extractall(path=extract_path)
            print(f"Extracted {fileName} to '{extract_path}' directory.")
            
    
    
    def ExtractAllZFiles(self, directory):
        for dirPath, dirNames, fileNames in os.walk(directory):
            for fileName in fileNames:
                if fileName.endswith('.z') or fileName.endswith('.Z'):
                    zPath = os.path.join(dirPath, fileName)
                    print (f"Extracting {zPath}...")
                    self.Extract_z_file(zPath, dirPath)
                

    def Extract_z_file(self, z_path, output_dir='.'):
        # 파일명에서 확장자 제거
        base_name = os.path.basename(z_path)
        if base_name.lower().endswith('.z'):
            output_name = base_name[:-2]  # remove '.Z'
        else:
            raise ValueError("Not a .Z file")

        # 압축 해제 대상 경로
        output_path = os.path.join(output_dir, output_name)

        # .Z 파일 열기 및 압축 해제
        with open(z_path, 'rb') as f:
            compressed_data = f.read()
            decompressed_data = unlzw(compressed_data)

        # 결과 파일 저장
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)

        print(f"Extracted to: {output_path}")
    
    def ZipFolder(self, folder_path, output_zip):
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

    def ImportPBA(self):
        ith = 0 
        shapeList = [] 
        filePath = os.getcwd()
        if self.exportPKGOption == True:
            exportFolderPath =  os.path.join(filePath,self.exportPKGFolderName)
            if not os.path.exists(exportFolderPath):
                os.makedirs(exportFolderPath)          
        
        curI = 0

        for fileName in self.ODBFile:
            print("Import PBA: ", fileName)
            
            if ".tgz" in fileName:
                filePath = os.path.dirname(fileName)
                fileName = os.path.basename(fileName)                
                curFullPath = os.path.join(filePath, fileName)
                self.ExtractTGZ(curFullPath, filePath)
                filePath = os.path.join(filePath, fileName)
                filePath = filePath.replace(".tgz","")
                self.ExtractAllZFiles(filePath)
                outFilePath = filePath + ".zip"
                self.ZipFolder(filePath, outFilePath)
                fileName = outFilePath
                self.ODBFile[curI] = outFilePath
                
            curI = curI + 1
            
            
            addedList = self.ImportPCBDetail()
            print("Number of PCB Shapes :", len(addedList))
            shapeList.extend(addedList)
            
            fileName = os.path.join(filePath,fileName)
            
            self.ImportODBZipforPackage(ith, fileName)
            if self.exportPKGOption == True:
                self.packageManager.ExportPackage(exportFolderPath,self.minimumSize)
                
            pkgBodyShapeList = []
            pkgSolderShapeList = []
            for compMan in self.componentManager:
                compMan : ComponentManager = compMan
                addedList, bodyList, solderList = compMan.Generate(self.minimumSize,self.detailPADName,self.udPKGName,
                                             self.xmin,self.ymin,self.xmax,self.ymax)
                if self.exportPKGOption == True:
                    compMan.ExportComponent(exportFolderPath,self.minimumSize)
                shapeList.extend(addedList)
                pkgBodyShapeList.extend(bodyList)
                pkgSolderShapeList.extend(solderList)
            print("Number of Total Shapes : ", len(shapeList))

            # 패키지 합친 STEP 파일 출력 (본체 + 솔더)
            def _flatten_shapes_to_compound(shapeItems):
                from OCC.Core.TopoDS import TopoDS_Compound
                from OCC.Core.BRep import BRep_Builder
                compound = TopoDS_Compound()
                builder = BRep_Builder()
                builder.MakeCompound(compound)
                count = 0
                for item in shapeItems:
                    if item is None:
                        continue
                    if isinstance(item, list):
                        for shape in item:
                            if shape is not None:
                                builder.Add(compound, shape)
                                count += 1
                    else:
                        builder.Add(compound, item)
                        count += 1
                return compound, count

            from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer

            # PKG 본체 STEP
            compoundPKG, countPKG = _flatten_shapes_to_compound(pkgBodyShapeList)
            if countPKG > 0:
                pkgSTPPath = self.inputFileName.replace(".txt","_PKG.stp")
                stepWriterPKG = STEPControl_Writer()
                stepWriterPKG.Transfer(compoundPKG, STEPControl_AsIs)
                stepWriterPKG.Write(pkgSTPPath)
                print("Exporting Package Body STEP file: ", pkgSTPPath)

            # 솔더 STEP
            compoundS, countS = _flatten_shapes_to_compound(pkgSolderShapeList)
            if countS > 0:
                solderSTPPath = self.inputFileName.replace(".txt","_S.stp")
                stepWriterS = STEPControl_Writer()
                stepWriterS.Transfer(compoundS, STEPControl_AsIs)
                stepWriterS.Write(solderSTPPath)
                print("Exporting Solder STEP file: ", solderSTPPath)

            ith = ith + 1
        self.shapeList = shapeList
        return shapeList
    
    def ImportODBZipforPackage(self,ith, odbPath):
        mode = 1
        with zipfile.ZipFile(odbPath,'r') as zip_file:
             for file_name in zip_file.namelist():
                 if mode == 1:
                     if "eda/data" in file_name:
                        if ".Z" in file_name:
                            pass
                        else:
                            zip_file.extract(file_name, 'extracted_files')
                            extracted_file_path = 'extracted_files/' + file_name
                            # Open and read the contents of the extracted file
                            with open(extracted_file_path, 'r', encoding='utf-8') as file:
                                self.packageManager.SetUnitAmp(self.unitamp)
                                self.packageManager.ImportPackagesfromODB(file)
                                file.close()
                                
                     elif "steps" in file_name and "components" in file_name:
                         if ".Z" in file_name:
                            pass
                         else:
                            zip_file.extract(file_name, 'extracted_files')
                            extracted_file_path = 'extracted_files/' + file_name
                            compName = file_name.replace("steps/pcb/layers/","")
                            compName = compName.replace("/components","")
                            compManID = len(self.componentManager)+1
                            print("Start to import component: ", compName)
                            isTop = False
                            if "top" in file_name:
                                isTop = True
                            sumThickness = 0.0
                            for thickness in self.thicknessODBFile[ith]:
                                sumThickness = sumThickness + thickness
                            
                            compMan = ComponentManager(compManID,compName,self.packageManager,isTop, self.zLocationODBFile[ith], sumThickness)
                            # Open and read the contents of the extracted file
                            with open(extracted_file_path, 'r', encoding='utf-8') as file:                                                           
                                compMan.SetUnitAmp(self.unitamp)
                                compMan.ImportComponentfromODB(file)
                                if len(compMan.components) == 0:
                                    continue
                                self.componentManager.append(compMan)     
                                print("End to import component: ", compName) 
                                file.close()
                            
                         pass
                 elif mode == 2:
                    with zip_file.open(file_name, 'r') as file:                    
                        
                        #if "matrix/matrix" in file_name:
                        #elif "steps/pcb/profile" in file_name:
                        #elif "steps/pcb/layers/" in file_name and "features" in file_name:                        
                        ## package file 
                        if "eda/data" in file_name:                        
                            self.packageManager.ImportPackagesfromODB(file)
                            pass
                        ## component file
                        elif "steps" in file_name and "components" in file_name:
                            compName = file_name.replace("steps/pcb/layers/","")
                            compName = compName.replace("/components","")
                            compManID = len(self.componentManager)+1                          
                            print("Start to import component: ", compName)
                            isTop = False
                            if "top" in file_name:
                                isTop = True                        
                            sumThickness = 0.0
                            for thickness in self.thicknessODBFile[ith]:
                                sumThickness = sumThickness + thickness
                            compMan = ComponentManager(compManID,compName,self.packageManager,isTop, self.zLocationODBFile[ith], sumThickness)
                            compMan.ImportComponentfromODB(file)
                            if len(compMan.components) == 0:
                                continue
                            self.componentManager.append(compMan)     
                            print("End to import component: ", compName)           

                            pass
                        file.close()
    
    def GeneratePackages(self):
        print("Generate Packages start")


    def load_PCB(self, path, filename):
        if len(filename) == 0:
            return None
        with open(join(path,filename)) as stream:
            #return self.pcbManager.ImportPCBfromODB(stream)   
            return self.pcbManager.ImportPCBfromOCBTwo(stream)
        
    def load_arrayPCB(self,path,filename):
        if len(filename) == 0:
            return None
        with open(join(path,filename)) as stream:
            return self.pcbManager.ImportArrayPCBfromODB(stream)

    def load_package(self, path, filename):
        if len(filename) ==0:
            return None

        with open(join(path,filename)) as stream:
            self.packageManager.ImportPackagesfromODB(stream)
        
    def load_component(self, path, fileName):
        if len(fileName) == 0:
            return None
        for aFileName in fileName:
            with open(join(path,aFileName)) as stream:
                compManID = len(self.componentManager)+1
                fname = aFileName 
                compMan = ComponentManager(compManID,fname,self.packageManager)
                compMan.ImportComponentfromODB(stream)
                if len(compMan.components) == 0:
                    continue
                self.componentManager.append(compMan)                
    
    def export_package(self, path, fileName):
        with open(join(path,fileName),'w') as stream:
            self.packageManager.WritePackagestoFile(stream)
                                                    

    def export_all_components(self, path, fileName):
        layerFileName = "{name}_{layer}.txt"
        for i in range(len(self.componentManager)):
            curFileName = layerFileName.format(name=fileName,layer=i)
            with open(join(path,curFileName),'w') as stream:
                self.componentManager[i].ExportComponenttoODB(stream)        
    
    def ExportShapes(self, fileName, shapeList = []):
        if len(shapeList) == 0:
            shapeList = self.shapeList        
        #chk time
        import time
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_SOLID
        start = time.time()

        step_writer = STEPControl_Writer()
        builder = BRep_Builder()
        i = 0
        compound = TopoDS_Compound()        
        builder.MakeCompound(compound)
        for shape in shapeList:            
            if type(shape) == list:                                                              
                print("Number of shape in list: ", len(shape))
                #print("Shape Name List", shape)
                for subShape in shape:
                    if subShape != None:
                        builder.Add(compound,subShape)                                
            elif type(shape) == TopoDS_Compound:
                # Extract TopoDS_Solid from TopoDS_Compound 
                
                exp = TopExp_Explorer(shape, TopAbs_SOLID)
                while exp.More():
                    solid = exp.Current()
                    builder.Add(compound,solid)
                    exp.Next()                
                    print("Shape", solid)
                
            elif shape is not None:      
                builder.Add(compound,shape)
            else:
                print("Shape is unknown", shape)
                       
            i = i + 1
            print(i,'th Shape are saved')
                 
        step_writer.Transfer(compound, STEPControl_AsIs)           
        end = time.time()
        print("Exporting STEP file is done. Time: ", end-start)     
        status = step_writer.Write(fileName)        

    def ExportShapesOld(self, fileName, shapeList = []):
        if len(shapeList) == 0:
            shapeList = self.shapeList        
                
        #chk time
        import time
        start = time.time()

        step_writer = STEPControl_Writer()
        builder = BRep_Builder()
        i = 0
        for shape in shapeList:            
            if type(shape) == list:
               
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)                
                
                for subShape in shape:
                    if subShape != None:
                        builder.Add(compound,subShape)                
                step_writer.Transfer(compound, STEPControl_AsIs)
            elif type(shape) == TopoDS_Compound:
                compound = shape
                step_writer.Transfer(compound, STEPControl_AsIs)
            elif shape is not None:                
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)                                
                builder.Add(compound,shape)

                step_writer.Transfer(compound, STEPControl_AsIs)           
            
            i = i + 1
            print(i,'th Shape are saved')
                 
        end = time.time()
        print("Exporting STEP file is done. Time: ", end-start)     
        status = step_writer.Write(fileName)
        print("Exporting STEP file is done.")

    def ExportShapesOriginal(self, fileName, shapeList = []):
        if len(shapeList) == 0:
            shapeList = self.shapeList        
                
        step_writer = STEPControl_Writer()
        for shape in shapeList:            
            if type(shape) == list:
                builder = BRep_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)                
                
                for subShape in shape:
                    if subShape != None:
                        builder.Add(compound,subShape)                
                step_writer.Transfer(compound, STEPControl_AsIs)
            elif type(shape) == TopoDS_Compound:
                compound = shape
                step_writer.Transfer(compound, STEPControl_AsIs)
            elif shape is not None:
                builder = BRep_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)                                
                builder.Add(compound,shape)

                step_writer.Transfer(compound, STEPControl_AsIs)           
                 
                
        status = step_writer.Write(fileName)
        print("Exporting STEP file is done.")

    def is_eof(self,f):
        cur = f.tell()
        f.seek(0, os.SEEK_END)
        end = f.tell()
        f.seek(cur, os.SEEK_SET)
        return cur == end
    



'''
if __name__ == '__main__':
    odbManager = ODBCADManager()
    
    mode = "PCB"
    mode = "ArrayPCB"
    fileName = "ECADNowarpage.txt"
    #Get Current Path
    curPath = os.getcwd()
    curFilePath = os.path.join(curPath,fileName)
    print(curFilePath)
    odbManager.ImportModellingOptions(curPath,fileName)
    if mode == "PCB":
        odbManager.ImportPCBs()
    elif mode == "ArrayPCB":
        odbManager.ImportArrayPCBs()
'''