
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


import json
from io import StringIO
import copy
#from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Ax2, gp_Circ
#from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
#from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
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

if __name__ == "__main__":
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


class KooSimulationGenerator():
    def __init__(self, dynaImporter : KooDynaImporter):
        self.dynaImporter : KooDynaImporter = dynaImporter
        self.curDir = os.getcwd()
        self.addScriptList = []
        self.inputFileName = ""
        self.maxNID = 0 
        self.maxEID = 0 
        self.maxPID = 0 
        self.maxSID = 0 
        self.maxMID = 0 
        self.maxNSID = 0        
    
    def SetCurrentDirectory(self, curDir):
        self.curDir = curDir
        
    def ImportDynaFile(self, fileName):
        filePath = os.path.join(self.curDir, fileName)
        self.dynaImporter.importDynaFile(filePath)
        self.dynaImporter.importKeywordstoManager()
        
    def ImportBaseFile(self, fileName = ""):
        if fileName == "":
            fileName = self.inputFileName
        
        self.ImportDynaFile(fileName)        
        self.dynaImporter.PrintImportStatus()
        #self.dynaImporterCopied = copy.deepcopy(self.dynaImporter)
        self.dynaImporter.SyncronizeMaxID()
        metaFileName = fileName.replace(".k",".json")
        prevMetaData = {}
        self.dynaImporter.InitializeMetaData()        
        
        if os.path.exists(metaFileName):
            with open(metaFileName, "r") as f:
                prevMetaData = json.load(f)
            self.dynaImporter.ImportMetaDatafromPreviousStep(prevMetaData)            
        
    def WriteMetaData(self, fileName = "", indent = 2):
        if fileName == "":
            fileName = self.inputFileName.replace(".k",".json")
        with open(fileName, "w") as f:
            json.dump(self.dynaImporter.metaData,f,ensure_ascii=False, indent=indent)
            
        
        
    def ExportDynaFile(self, fileName):
        filePath = os.path.join(self.curDir, fileName)
        with open(filePath, "w") as f:
            f.write("*KEYWORD\n")
            f.write(self.dynaImporter.ExportDynaString())
            f.write("*END\n")
        


if __name__ == "__main__":
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
    curDir = os.getcwd()
    filePath = os.path.join(curDir, "PackageInfoDMAShellTest.k")
    
    
    filePath = "D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/OpenRadioss/examples/taylor_A.k/taylor_A.k"
    filePath = "D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/OpenRadioss/examples/Contact_Automatic/tube.k"
    filePath = "D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/OpenRadioss/examples/Udemy_LSDYNA/3 pt bending test/test_3/test_3pt_bending_3.k"
    filePath = "D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/OpenRadioss/examples/Contact_Eroding/birdball/birdball.k"
    filePath = "D:/OpenCASCADE-7.7.0-vc14-64/pythonoccenv310/OpenRadioss/examples/Contact_Foam/matfoamsoil.k"
    dynaImporter.importDynaFile(filePath)
    dynaImporter.importKeywordstoManager()
    
    '''dynaImporter.importControl()
    dynaImporter.importDatabase()
    maxNID = dynaImporter.importNode()
    maxPID = dynaImporter.importPart()
    maxNSID = dynaImporter.importNodeSet()
    maxSID = dynaImporter.importSection()
    matMID = dynaImporter.importMaterial()
    matDID = dynaImporter.importDefine()
    maxEID = dynaImporter.partManager.FindMaxEID()
    maxDampID = dynaImporter.importDamping()
    maxSSID = dynaImporter.importSegmentSet()
    maxBID = dynaImporter.importBoundaryNode()
    maxLID = dynaImporter.importLoad()
    maxCID = dynaImporter.importContact()    
    dynaImporter.importInitial()
    dynaImporter.importAdditional()'''
    dynaImporter.PrintImportStatus()
    
    simulGen = KooSimulationGenerator(dynaImporter)
    resultTest = os.path.join(curDir, "testDyna.k")
    with open(resultTest, "w") as f:
        f.write("*Keyword\n")
        f.write(dynaImporter.ExportDynaString())
        f.write("*End\n")