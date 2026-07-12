from __future__ import annotations
import os 
import re
import datetime, hashlib, uuid

from io import StringIO
#from dynareadout import D3plot

from KooCAEManager.KooElementSet import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooNode import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooSection import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooDynaKeyword import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooContact import *
from KooCAEManager.KooSegment import *
from KooCAEManager.KooDynaResult import *
from KooCAEManager.KooDynaControl import *
from KooCAEManager.KooDynaDatabase import *
from KooCAEManager.KooInitial import *
from KooCAEManager.KooDynaAdditional import *
from KooCAEManager.KooDamping import *
from KooCAEManager.KooConstrained import *
from KooCAEManager.KooD3plot import *

class KooDynaImporter():
    def __init__(self, nodeManager = None, partManager = None, resultManager = None, matManager = None, sectionManager = None, nodeSetManager = None, loadManager = None, boundaryNodeManager = None, defineManager = None, contactManager = None, segmentSetManager = None, dynaResultManager = None, controlManager = None, dampingManager = None, databaseManager = None, initialManager = None, additionalManager = None, constrainedManager = None):
        self.title = ""
        self.nodeManager : NodeManager = nodeManager
        self.elementManager = {}
        self.partManager : KooPartManager = partManager
        self.resultManager : KooResultManager = resultManager
        self.matManager : KooMaterialManager = matManager
        self.sectionManager : KooSectionManager = sectionManager
        self.nodeSetManager : NodeSetManager = nodeSetManager        
        self.loadManager : KooLoadManager = loadManager
        self.boundaryNodeManager : KooBoundaryNodeManager = boundaryNodeManager
        self.defineManager : KooDefineManager = defineManager
        self.contactManager : KooContactManager = contactManager
        self.segmentSetManager : KooSegmentSetManager = segmentSetManager
        self.dynaResultManager : KooDynaResultManager = dynaResultManager
        self.controlManager : KooControlManager = controlManager
        self.dampingManager : KooDampingManager = dampingManager
        self.databaseManager : KooDatabaseManager = databaseManager
        self.initialManager : KooInitialManager = initialManager
        self.constrainedManager : KooConstrainedManager = constrainedManager
        self.additionalManager : KooDynaAdditionalManager = additionalManager
        if nodeManager is None:
            self.nodeManager = NodeManager()
        if partManager is None:
            self.partManager = KooPartManager(self.nodeManager)      
        if resultManager is None:
            self.resultManager = KooResultManager(self.nodeManager)
        if matManager is None:
            self.matManager = KooMaterialManager()
        if sectionManager is None:
            self.sectionManager = KooSectionManager()
        if nodeSetManager is None:
            self.nodeSetManager = NodeSetManager()
        if loadManager is None:
            self.loadManager = KooLoadManager()
        if boundaryNodeManager is None:
            self.boundaryNodeManager = KooBoundaryNodeManager()
        if defineManager is None:
            self.defineManager = KooDefineManager()
        if contactManager is None:
            self.contactManager = KooContactManager()
        if segmentSetManager is None:
            self.segmentSetManager = KooSegmentSetManager()
        if dynaResultManager is None:
            self.dynaResultManager = KooDynaResultManager()
        if controlManager is None:
            self.controlManager = KooControlManager()
        if dampingManager is None:
            self.dampingManager = KooDampingManager()
        if databaseManager is None:
            self.databaseManager = KooDatabaseManager()
        if initialManager is None:
            self.initialManager = KooInitialManager()
        if constrainedManager is None:
            self.constrainedManager = KooConstrainedManager()
        if additionalManager is None:   
            self.additionalManager = KooDynaAdditionalManager()            

        self.dynaManager : DynaManager = DynaManager()
        self.externalDynaResultManager = KooExternalDynaResultManager()
        self.metaData = {}
    
    def GenerateRunID(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
        run_id = f"{timestamp}_{unique_hash}"
        print(run_id + " is generated as run_id")  
        self.metaData["run_id"] = run_id
        return run_id
    
    def InitializeMetaData(self):
        self.metaData = {} 
        
        self.metaData["schema_version"] = "0.1.0"
        
        self.GenerateRunID()
        
        self.metaData["stage"] = "%STAGE%"
        self.metaData["model_name"] = "%MODEL%"
        self.metaData["description"] = "%DESCRIPTION%"
        self.metaData["created"] = "%CREATED%"
        self.metaData["created_by"] = {}
        self.metaData["created_by"]["name"] = "%CREATED_BY_NAME%"
        self.metaData["created_by"]["email"] = "%CREATED_BY_EMAIL%"        
        self.metaData["created_by"]["group"] = "%CREATED_BY_GROUP%"
        self.metaData["created_by"]["team"] = "%CREATED_BY_TEAM%"
        
        #  mode : DROP, IMPACT, CAPVIB, MOTORVIB, 3PTBEND, etc 
        self.metaData["scenario_mode"] = "%DROP%"
        self.metaData["initial_conditions"] = {}
        self.metaData["initial_conditions"]["orientation_euler_deg"] = {}
        self.metaData["initial_conditions"]["orientation_euler_deg"]["pitch"] = 0
        self.metaData["initial_conditions"]["orientation_euler_deg"]["roll"] = 0 
        self.metaData["initial_conditions"]["orientation_euler_deg"]["yaw"] = 0 
        self.metaData["initial_conditions"]["drop_height"] = 0.0        
        self.metaData["initial_conditions"]["velocity"] = [0.0, 0.0, 0.0] # mm/s
        self.metaData["initial_conditions"]["angular_velocity"] = [0.0, 0.0, 0.0] # deg/s
        
        self.metaData["environment"] = {}
        self.metaData["environment"]["wall"] = {} 
        self.metaData["environment"]["wall"]["type"] = "steel"
        self.metaData["environment"]["wall"]["roughness_um"] = 10.0 # um
        self.metaData["environment"]["wall"]["elasticity_modulus_gpa"] = 200000.0 # GPa
        self.metaData["environment"]["wall"]["poisson_ratio"] = 0.3
        self.metaData["environment"]["wall"]["density_gpcm3"] = 7.85e-9 # g/cm3
        
        self.metaData["model"] = {}
        self.metaData["model"]["material_db_version"] = "%MATERIAL_DB_VERSION%"
        
        self.metaData["model"]["parts"] = {}
        self.metaData["model"]["contact_graph"] = {}                
        self.metaData["model"]["ptos_contact"] = {}
        self.metaData["model"]["stop_contact"] = {}
        
        self.metaData["mechanism_chain"] = {}        
        self.metaData["mechanism_chain"]["step_index"] = 0 
        self.metaData["mechanism_chain"]["prev_run_ids"] = {}
        self.metaData["mechanism_chain"]["next_run_ids"] = {}
        self.metaData["mechanism_chain"]["prev_conditions"] = []
        
    
    def AddMetaDatafromManager(self):
        self.metaData["model"]["parts"] = {}
        self.metaData["model"]["contact_graph"] = {}        
        
        self.metaData["model"]["parts"] = self.partManager.UpdatePartGraph()
        try:
            self.metaData["model"]["contact_graph"], self.metaData["model"]["ptos_contact"], self.metaData["model"]["stop_contact"] = self.contactManager.UpdateContactGraph(self.partManager,self.segmentSetManager)
        except Exception as e:
            print(f"Warning: UpdateContactGraph failed ({e}), skipping contact graph")
            self.metaData["model"]["ptos_contact"] = {}
            self.metaData["model"]["stop_contact"] = {}
    
    def ImportMetaDatafromPreviousStep(self, jsonData):
        if "stage" in jsonData:
            self.metaData["stage"] = jsonData["stage"]
        if "model_name" in jsonData:
            self.metaData["model_name"] = jsonData["model_name"]
            
        if "mechanism_chain" in jsonData:
            if "step_index" in jsonData["mechanism_chain"]:
                self.metaData["mechanism_chain"]["step_index"] = jsonData["mechanism_chain"]["step_index"] + 1
            if "run_id" in jsonData:
                self.metaData["mechanism_chain"]["prev_run_ids"][jsonData["run_id"]] = True
            jsonData["mechanism_chain"]["next_run_ids"][self.metaData["run_id"]] = True    
            
            prevConditions = {}        
            if "scenario_mode" in jsonData:
                prevConditions["scenario_mode"] = jsonData["scenario_mode"]
            if "initial_conditions" in jsonData:
                prevConditions["initial_conditions"] = jsonData["initial_conditions"]
            if "environment" in jsonData:
                prevConditions["environment"] = jsonData["environment"]
            if len(prevConditions) > 0:
                self.metaData["mechanism_chain"]["prev_conditions"].append(prevConditions)
                
        
        

    def SetUpdateManager(self, nodeManager = None, partManager = None, resultManager = None, matManager = None, sectionManager = None, nodeSetManager = None, loadManager = None, boundaryNodeManager = None, defineManager = None, contactManager = None, segmentSetManager = None, dynaResultManager = None):
        self.nodeManager = nodeManager
        self.partManager = partManager    
        self.resultManager = resultManager
        self.matManager = matManager
        self.sectionManager = sectionManager        
        self.nodeSetManager = nodeSetManager
        self.loadManager = loadManager
        self.boundaryNodeManager = boundaryNodeManager
        self.defineManager = defineManager
        self.contactManager = contactManager
        self.segmentSetManager = segmentSetManager
        self.dynaResultManager = dynaResultManager
    
    def ImportExternalDynaResult(self, d3plotPath):
        self.externalDynaResultManager.SetD3Plot(d3plotPath)
    
    def ImportExternalDynaResultinBoundaryBox(self, d3plotPath, minX, maxX, minY, maxY, minZ, maxZ):
        self.externalDynaResultManager.SetD3PlotinBoundaryBox(d3plotPath, minX, maxX, minY, maxY, minZ, maxZ)    

    def SetNodalForceGroup(self,setID,coordID = 0):
        keywordMan = self.dynaManager.dynaKeywordMan
        nodalForceGroup = DatabaseNodalForceGroup()        
        parse = "{:10d}{:10d}".format(setID,coordID)
        parse = [[parse]]
        nodalForceGroup.parse(parse)
        keywordMan.addKeyword(nodalForceGroup)

    def SetHistoryNodeforAll(self):
        keywordMan = self.dynaManager.dynaKeywordMan
        #all nodes 
        nodes = self.nodeManager.nodes.keys() 
        parse = ""       
        i = 0   
        parses = []
        for nid in nodes:        
            i += 1
            parse += "{:10d}".format(nid)
            if i % 8 == 0:                
                parses.append(parse)
                parse = ""
        parse = [parses]
        historyNode = DatabaseHistoryNode()
        historyNode.parse(parse)
        keywordMan.addKeyword(historyNode)
    
    def SetHistoryNodeforSet(self,setID):
        keywordMan = self.dynaManager.dynaKeywordMan
        #set id 
        parses = "{:10d}".format(setID)
        parse = [[parses]]
        historyNodeSet = DatabaseHistoryNodeSet()        
        historyNodeSet.parse(parse)
        keywordMan.addKeyword(historyNodeSet)

    def SetHistoryElementforBeamSet(self,setID):
        keywordMan = self.dynaManager.dynaKeywordMan
        #set id 
        parses = "{:10d}".format(setID)
        parse = [[parses]]
        historyBeamSet = DatabaseHistoryBeamSet()        
        historyBeamSet.parse(parse)
        keywordMan.addKeyword(historyBeamSet)
    
    def SetHistoryElementforShellSet(self,setID):
        keywordMan = self.dynaManager.dynaKeywordMan
        #set id 
        parses = "{:10d}".format(setID)
        parse = [[parses]]
        historyShellSet = DatabaseHistoryShellSet()        
        historyShellSet.parse(parse)
        keywordMan.addKeyword(historyShellSet)
    
    def SetHistoryElementforSolidSet(self,setID):
        keywordMan = self.dynaManager.dynaKeywordMan
        #set id 
        parses = "{:10d}".format(setID)
        parse = [[parses]]
        historySolidSet = DatabaseHistorySolidSet()        
        historySolidSet.parse(parse)
        keywordMan.addKeyword(historySolidSet)

    def SetHistoryElementforAll(self):
        keywordMan = self.dynaManager.dynaKeywordMan
        #all elements
        parsesElementsBeam = []
        parsesElementsShell = []
        parsesElementsSolid = []
        parseElementsBeam = "" 
        parseElementsShell = ""
        parseElementsSolid = ""
        iBeam = 0
        iShell = 0 
        iSolid = 0 
        for id in self.partManager.parts:
            curKooPart : KooPart = self.partManager.parts[id]
            for eid in curKooPart.elementManager.elements:
                curElement : Element = curKooPart.elementManager.elements[eid]
                if "LINE" in curElement.type:
                    iBeam += 1
                    parseElementsBeam += "{:10d}".format(curElement.id)
                    if iBeam % 8 == 0:
                        parsesElementsBeam.append(parseElementsBeam)
                        parseElementsBeam = ""
                if "TRI" in curElement.type or "QUAD" in curElement.type:
                    iShell += 1
                    parseElementsShell += "{:10d}".format(curElement.id)
                    if iShell % 8 == 0:
                        parsesElementsShell.append(parseElementsShell)
                        parseElementsShell = ""
                if "TETRA" in curElement.type or "HEXA" in curElement.type:
                    iSolid += 1
                    parseElementsSolid += "{:10d}".format(curElement.id)
                    if iSolid % 8 == 0:
                        parsesElementsSolid.append(parseElementsSolid)
                        parseElementsSolid = ""
        if len(parsesElementsBeam) > 0:
            history_beam = DatabaseHistoryBeam()
            history_beam.parse([parsesElementsBeam])
            keywordMan.addKeyword(history_beam)
        if len(parsesElementsShell) > 0:
            history_shell = DatabaseHistoryShell()
            history_shell.parse([parsesElementsShell])
            keywordMan.addKeyword(history_shell)
        if len(parsesElementsSolid) > 0:
            history_solid = DatabaseHistorySolid()
            history_solid.parse([parsesElementsSolid])
            keywordMan.addKeyword(history_solid)

    def SetELOUT(self,dt=1.0e-3,binary=1,lcur=0,ioopt=1):
        #dt , bindary, lcur, ioopt have 10 each spaces 
        parse = "{:10.6f}{:10d}{:10d}{:10d}".format(dt,binary,lcur,ioopt)        
        parse = [[parse]]
        keywordMan = self.dynaManager.dynaKeywordMan
        eloutKeyword = DatabaseElout()
        eloutKeyword.parse(parse)
        keywordMan.addKeyword(eloutKeyword)
    
    def SetNODFOR(self,dt=1.0e-3,binary=1,lcur=0,ioopt=1):
        #dt , bindary, lcur, ioopt have 10 each spaces 
        parse = "{:10.6f}{:10d}{:10d}{:10d}".format(dt,binary,lcur,ioopt)        
        parse = [[parse]]
        keywordMan = self.dynaManager.dynaKeywordMan
        nodforKeyword = DatabaseNodfor()
        nodforKeyword.parse(parse)
        keywordMan.addKeyword(nodforKeyword)
    
    def SetBNDOUT(self,dt=1.0e-3,binary=1,lcur=0,ioopt=1):
        #dt , bindary, lcur, ioopt have 10 each spaces 
        parse = "{:10.6f}{:10d}{:10d}{:10d}".format(dt,binary,lcur,ioopt)        
        parse = [[parse]]
        keywordMan = self.dynaManager.dynaKeywordMan
        bndoutKeyword = DatabaseBndout()
        bndoutKeyword.parse(parse)
        keywordMan.addKeyword(bndoutKeyword)

    def SetNODOUT(self,dt=1.0e-3,binary=1,lcur=0,ioopt=1):
        #dt , bindary, lcur, ioopt have 10 each spaces 
        parse = "{:10.6f}{:10d}{:10d}{:10d}".format(dt,binary,lcur,ioopt)        
        parse = [[parse]]
        keywordMan = self.dynaManager.dynaKeywordMan
        nodoutKeyword = DatabaseNodout()
        nodoutKeyword.parse(parse)
        keywordMan.addKeyword(nodoutKeyword)

    def importDynaFile(self, filePath, writeLog = True):
        # folder path from filePath
        folderPath = os.path.dirname(filePath)
        fileNamewithoutext = os.path.splitext(os.path.basename(filePath))[0]
        ext = os.path.splitext(os.path.basename(filePath))[1]
        self.dynaManager.SetInputPath(filePath)
        outFilePath = os.path.join(folderPath, fileNamewithoutext + "_dump.k")
        self.dynaManager.ReadInputFile(outFilePath,writeLog)
        self.keywordInterpreted = self.dynaManager.keywordInterpreted
        # include 정보 저장
        self._include_sources = getattr(self.dynaManager, '_include_sources', {})
        self._include_files = getattr(self.dynaManager, '_include_files', [])
        self._main_file = getattr(self.dynaManager, '_main_file', filePath)
    
    def SyncronizeMaxID(self):
        self.SyncronizeMaxEID()
    
    def SyncronizeMaxEID(self):
        maxEID = 0 
        for id in self.partManager.parts:
            curPart = self.partManager.parts[id]
            maxEID = max(maxEID, curPart.elementManager.GetMaxID())
        self.maxEID = maxEID
        for id in self.partManager.parts:
            curPart = self.partManager.parts[id]
            curPart.elementManager.SetMaxID(maxEID)
            
    def CombineManager(self, other: KooDynaImporter):
        self.OffsetIDofManager(other)
        self.OverwritefromManager(other)
            
    def OffsetIDofManager(self, other: KooDynaImporter):
        offsetNID = self.nodeManager.maxID
        offsetPID = self.partManager.maxID
        offsetPSID = self.partManager.maxSID
        
        offsetNSID = self.nodeSetManager.maxID
        offsetSID = self.sectionManager.maxid
        offsetMID = self.matManager.maxid
        offsetDID = self.defineManager.maxid
        offsetCOORDID = self.defineManager.maxid
        offsetEID = self.partManager.FindMaxEID()
        offsetDampID = self.dampingManager.maxid
        offsetSSID = self.segmentSetManager.maxid
        offsetBID = self.boundaryNodeManager.maxid
        offsetLID = self.loadManager.maxid
        offsetCID = self.contactManager.maxid
        
        other.nodeManager.OffsetID(offsetNID)
        other.partManager.OffsetID(offsetPID, offsetPSID, offsetEID, -1)                
        other.nodeSetManager.OffsetID(offsetNSID)        
        other.sectionManager.OffsetID(offsetSID)        
        other.materialManager.OffsetID(offsetMID)
        other.defineManager.OffsetID(offsetDID, offsetCOORDID)        
        other.dampingManager.OffsetID(offsetDampID)        
        other.segmentSetManager.OffsetID(offsetSSID, offsetNID)        
        other.boundaryNodeManager.OffsetID(offsetBID)
        other.loadManager.OffsetID(offsetLID,offsetNID)
        other.contactManager.OffsetID(offsetCID)

    def OverwritefromManager(self, other: KooDynaImporter):
        self.controlManager.OverwritefromControlManager(other.controlManager)
        self.databaseManager.OverwritefromDatabaseManager(other.databaseManager)
        self.nodeManager.OverwritefromNodeManager(other.nodeManager)
        self.maxNID = self.nodeManager.maxID
        self.partManager.OverwritefromPartManager(other.partManager)
        self.maxPID = self.partManager.maxID
        self.nodeSetManager.OverwritefromNodeSetManager(other.nodeSetManager)
        self.maxNSID = self.nodeSetManager.maxID
        self.sectionManager.OverwritefromSectionManager(other.sectionManager)
        self.maxSID = self.sectionManager.maxid
        self.matManager.OverwritefromMaterialManager(other.matManager)
        self.maxMID = self.matManager.maxid
        self.defineManager.OverwritefromDefineManager(other.defineManager)
        self.maxDID = self.defineManager.maxid
        self.maxEID = self.partManager.FindMaxEID()
        self.dampingManager.OverwritefromDampingManager(other.dampingManager)
        self.maxDampID = self.dampingManager.maxid
        self.segmentSetManager.OverwritefromSegmentSetManager(other.segmentSetManager)
        self.maxSSID = self.segmentSetManager.maxid
        self.boundaryNodeManager.OverwritefromBoundaryNodeManager(other.boundaryNodeManager)
        self.maxBID = self.boundaryNodeManager.maxid
        self.loadManager.OverwritefromLoadManager(other.loadManager)
        self.maxLID = self.loadManager.maxid
        self.contactManager.OverwritefromContactManager(other.contactManager)
        self.maxCID = self.contactManager.maxid
        self.initialManager.OverwritefromInitialManager(other.initialManager)
        self.constrainedManager.OverwritefromConstrainedManager(other.constrainedManager)
        self.additionalManager.OverwritefromDynaAdditionalManager(other.additionalManager)

    def importKeywordstoManager(self):        
        self.importControl()
        print("Control Imported")
        self.importDatabase()
        print("Database Imported")
        self.maxNID = self.importNode()
        print("Node Imported")
        self.maxPID = self.importPart()
        print("Part Imported")
        self.maxNSID = self.importNodeSet()
        print("NodeSet Imported")
        self.maxSID = self.importSection()
        print("Section Imported")
        self.maxMID = self.importMaterial()
        print("Material Imported")
        self.maxDID = self.importDefine()
        print("Define Imported")
        self.maxEID = self.partManager.FindMaxEID()
        print("Element Imported")
        self.maxDampID = self.importDamping()
        print("Damping Imported")
        self.maxSSID = self.importSegmentSet()
        print("SegmentSet Imported")
        self.maxBID = self.importBoundaryNode()
        print("BoundaryNode Imported")
        self.maxLID = self.importLoad()
        print("Load Imported")
        self.maxCID = self.importContact()
        print("Contact Imported")
        self.importInitial()
        print("Initial Imported")
        self.importConstrained()
        print("Constrained Imported")
        # CNRB PID와 partManager.maxID 동기화 (ID 충돌 방지)
        if self.constrainedManager.maxCNRBID > self.partManager.maxID:
            self.partManager.maxID = self.constrainedManager.maxCNRBID
            print(f"  Part maxID synced with CNRB: {self.partManager.maxID}")
        self.importAdditional()
        print("Additional Imported")
        print("Import Completed")
        
        
    
    def PrintImportStatus(self):
        print("Import Status :")
        self.keywordInterpreted["KEYWORD"] = True
        self.keywordInterpreted["END"] = True
        cntInterpreted = 0 
        cntNonInterpreted = 0
        strInterpreted = ""
        strNonInterpreted = ""
        for key in self.keywordInterpreted:
            
            if self.keywordInterpreted[key] == True:
                cntInterpreted += 1
                strInterpreted += key + " : TRUE\n" 
            else:
                cntNonInterpreted += 1
                strNonInterpreted += key + " : FALSE\n"
        
        print("Interpreted : ", cntInterpreted)
        print(strInterpreted)
        print("Non Interpreted : ", cntNonInterpreted)
        print(strNonInterpreted)
        
    def importNode(self):
        dynaKeywords = self.dynaManager.dynaKeywordMan.keywords
        if "NODE" in dynaKeywords:
            self.keywordInterpreted["NODE"] = True
        nodeKeyword : DynaNode = dynaKeywords["NODE"]
        
        #import time
        '''start = time.time()
        nodes = nodeKeyword.getNodeListAdvanced()
        end = time.time()
        print("Node List Time Advanced: ", end - start)
        '''
        #start = time.time()        
        nodes = nodeKeyword.getNodeList()
        #end = time.time()
        #print("Node List Time Fast: ", end - start)
        
        #start = time.time()
        #nodes = nodeKeyword.getNodeListOld()
        #end = time.time()
        #print("Node List Time Old: ", end - start)
        
        # preallocate self.nodeManager.nodes (dict) 
        #self.nodeManager.nodes = {i: None for i in range(1, len(nodes)+1)}
        
        
        value = self.nodeManager.AddNodesfromDynaAdvanced(nodes)
        return value        
        #return self.nodeManager.AddNodesfromDyna(nodes)
        

    def importNodeSet(self):
        dynaKeywords = self.dynaManager.dynaKeywordMan.keywords
        if "SET_NODE_LIST" in dynaKeywords:
            self.keywordInterpreted["SET_NODE_LIST"] = True
        if "SET_NODE_LIST_TITLE" in dynaKeywords:
            self.keywordInterpreted["SET_NODE_LIST_TITLE"] = True
        if "SET_NODE_LIST_GENERATE" in dynaKeywords:
            self.keywordInterpreted["SET_NODE_LIST_GENERATE"] = True
        
        if "SET_NODE_LIST" in dynaKeywords:
            setNodeList : SetNodeList = dynaKeywords["SET_NODE_LIST"]
        else:
            setNodeList = None
        if "SET_NODE_LIST_TITLE" in dynaKeywords:
            setNodeListTitle : SetNodeListTitle = dynaKeywords["SET_NODE_LIST_TITLE"]
        else:
            setNodeListTitle = None
        if "SET_NODE_LIST_GENERATE" in dynaKeywords:
            setNodeListGenerate : SetNodeListGenerate = dynaKeywords["SET_NODE_LIST_GENERATE"]
        else:
            setNodeListGenerate = None
            
            
        if setNodeList is not None:
            nodeSets = setNodeList.getSetNodeList()
            self.nodeSetManager.AddNodeSetfromDyna(nodeSets)
        if setNodeListTitle is not None:
            nodeSets = setNodeListTitle.getSetNodeList()
            self.nodeSetManager.AddNodeSetfromDyna(nodeSets)
        if setNodeListGenerate is not None:
            nodeSets = setNodeListGenerate.getSetNodeList()
            self.nodeSetManager.AddNodeSetfromDyna(nodeSets)
            
    def importPart(self):
        dynaKeywords = self.dynaManager.dynaKeywordMan.keywords
        modePart = ""
        modePartComposite = ""
        maxID = 0 
        if "PART" in dynaKeywords:
            self.keywordInterpreted["PART"] = True
        if "PART_COMPOSITE" in dynaKeywords:
            self.keywordInterpreted["PART_COMPOSITE"] = True
        if "ELEMENT_MASS" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_MASS"] = True
        if "ELEMENT_MASS_NODE_SET" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_MASS_NODE_SET"] = True
        if "ELEMENT_BEAM" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_BEAM"] = True
        if "ELEMENT_SHELL" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_SHELL"] = True
        if "ELEMENT_SHELL_THICKNESS" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_SHELL_THICKNESS"] = True
        if "ELEMENT_SOLID" in dynaKeywords:
            self.keywordInterpreted["ELEMENT_SOLID"] = True
        if "SET_PART" in dynaKeywords:
            self.keywordInterpreted["SET_PART"] = True        
        if "SET_PART_LIST" in dynaKeywords:
            self.keywordInterpreted["SET_PART_LIST"] = True
        if "SET_PART_LIST_TITLE" in dynaKeywords:
            self.keywordInterpreted["SET_PART_LIST_TITLE"] = True          
        if "SET_SHELL" in dynaKeywords:
            self.keywordInterpreted["SET_SHELL"] = True
        if "SET_SHELL_LIST" in dynaKeywords:
            self.keywordInterpreted["SET_SHELL_LIST"] = True
        if "SET_SHELL_TITLE" in dynaKeywords:
            self.keywordInterpreted["SET_SHELL_TITLE"] = True
        if "SET_SOLID" in dynaKeywords:
            self.keywordInterpreted["SET_SOLID"] = True        
        if "SET_SOLID_TITLE" in dynaKeywords:
            self.keywordInterpreted["SET_SOLID_TITLE"] = True
                                  
        if "SET_SHELL" in dynaKeywords:
            setShellKeyword : SetShell = dynaKeywords["SET_SHELL"]
            setshells = setShellKeyword.getShellList()
            for setshell in setshells:
                self.partManager.elementManager.AddSetsfromDyna(setshell)                    
        if "SET_SHELL_LIST" in dynaKeywords:
            setShellListKeyword : SetShellList = dynaKeywords["SET_SHELL_LIST"]
            setshells = setShellListKeyword.getShellListList()
            for setshell in setshells:
                self.partManager.elementManager.AddSetsfromDyna(setshell)
        if "SET_SHELL_TITLE" in dynaKeywords:
            setShellTitleKeyword : SetShellTitle = dynaKeywords["SET_SHELL_TITLE"]
            setshells = setShellTitleKeyword.getShellTitleList()
            for setshell in setshells:
                self.partManager.elementManager.AddSetsfromDyna(setshell)
        if "SET_SOLID" in dynaKeywords:
            setSolidKeyword : SetSolid = dynaKeywords["SET_SOLID"]
            setsolids = setSolidKeyword.getSolidList()
            for setsolid in setsolids:
                self.partManager.elementManager.AddSetsfromDyna(setsolid)
        if "SET_SOLID_TITLE" in dynaKeywords:
            setSolidTitleKeyword : SetSolidTitle = dynaKeywords["SET_SOLID_TITLE"]
            setsolids = setSolidTitleKeyword.getSolidTitleList()
            for setsolid in setsolids:
                self.partManager.elementManager.AddSetsfromDyna(setsolid)
                
        
                  
        
        if "PART" in dynaKeywords:
            modePart = "PART"
            partKeyword : Part = dynaKeywords["PART"]
        if "PART_COMPOSITE" in dynaKeywords:
            modePartComposite = "PART_COMPOSITE"
            partCompositeKeyword : Part = dynaKeywords["PART_COMPOSITE"]

        if "ELEMENT_MASS" in dynaKeywords:
            elementMassKeyword : ElementMass = dynaKeywords["ELEMENT_MASS"]
        else:
            elementMassKeyword = None
            
        if "ELEMENT_MASS_NODE_SET" in dynaKeywords:
            elementMassNodeSetKeyword : ElementMassNodeSet = dynaKeywords["ELEMENT_MASS_NODE_SET"]
        else:
            elementMassNodeSetKeyword = None

        if "ELEMENT_BEAM" in dynaKeywords:
            elementBeamKeyword : ElementBeam = dynaKeywords["ELEMENT_BEAM"]
        else:
            elementBeamKeyword = None

        if "ELEMENT_SHELL" in dynaKeywords:          
            elementShellKeyword : ElementShell = dynaKeywords["ELEMENT_SHELL"]
        else:
            elementShellKeyword = None
        if "ELEMENT_SHELL_THICKNESS" in dynaKeywords:
            elementShellThickKeyword : ElementShellThickness = dynaKeywords["ELEMENT_SHELL_THICKNESS"]
        else:
            elementShellThickKeyword = None

        if "ELEMENT_SOLID" in dynaKeywords:
            elementSolidKeyword : ElementSolid = dynaKeywords["ELEMENT_SOLID"]
        else:
            elementSolidKeyword = None
        if modePart == "PART":
            def _part_int_or_blank(field, default=0):
                """PART 필드를 int로 변환. 공백이면 default 반환."""
                if field is None:
                    return default
                s = str(field).strip()
                if not s:
                    return default
                try:
                    return int(s)
                except ValueError:
                    return default

            def _part_int_or_empty(field):
                """PART 옵션 필드를 int로 변환. 공백이면 빈 문자열 반환 (write 시 빈칸)."""
                if field is None:
                    return ""
                s = str(field).strip()
                if not s:
                    return ""
                try:
                    return int(s)
                except ValueError:
                    return ""

            parts = partKeyword.getPartList()
            for part in parts:
                if len(part) < 9:
                    print(f"[WARNING] *PART 필드 수 부족 ({len(part)}/9) — 스킵: {part}")
                    continue
                name = str(part[0]).lstrip()
                id = _part_int_or_blank(part[1], 0)
                if id == 0:
                    print(f"[WARNING] *PART PID 파싱 실패 — 스킵: {part}")
                    continue
                if id > maxID:
                    maxID = id
                secid = _part_int_or_blank(part[2], 0)
                mid = _part_int_or_blank(part[3], 0)
                eosid = _part_int_or_empty(part[4])
                hgid = _part_int_or_empty(part[5])
                grav = _part_int_or_empty(part[6])
                adpopt = _part_int_or_empty(part[7])
                tmid = _part_int_or_empty(part[8])
                elementManager = ElementManager(self.nodeManager,id)
                self.partManager.CreatePart(id, name, secid, mid, eosid, hgid, grav, adpopt, tmid, self.nodeManager,elementManager)
                self.elementManager[id] = elementManager
        if modePartComposite == "PART_COMPOSITE":
            parts = partCompositeKeyword.getPartList()
            for part in parts:
                # all string in part is lstrip
                name = str(part[0]).lstrip()
                id = int(part[1][0])
                if id > maxID:
                    maxID = id
                elform = int(part[1][1])
                if len(part[1][2].lstrip()) >2:
                    shrf = int(part[1][2])
                else:
                    shrf = ""
                if len(part[1][3].lstrip()) >3:
                    nloc = int(part[1][3])
                else:
                    nloc = ""
                if len(part[1][4].lstrip()) >4:
                    marea = int(part[1][4])
                else:
                    marea = ""
                if len(part[1][5].lstrip()) >5:
                    hgid = int(part[1][5])
                else:
                    hgid = ""
                if len(part[1][6].lstrip()) >6:
                    adpopt = int(part[1][6])
                else:
                    adpopt = ""
                if len(part[1][7].lstrip()) >7:
                    thshel = int(part[1][7])
                else:
                    thshel = ""

                laminates = part[2:]
                midi = [] 
                thicki = [] 
                bi = [] 
                tmidi = []
                for i in range(len(laminates)):
                    if len(laminates[i][0].lstrip())>0:
                        midi.append(int(laminates[i][0]))
                    if len(laminates[i][1].lstrip())>0:
                        thicki.append(float(laminates[i][1]))
                    if len(laminates[i][2].lstrip())>0:
                        bi.append(float(laminates[i][2]))
                    if len(laminates[i][3].lstrip())>0:
                        tmidi.append(int(laminates[i][3]))
                    if len(laminates[i][4].lstrip())>0:
                        midi.append(int(laminates[i][4]))
                    if len(laminates[i][5].lstrip())>0:
                        thicki.append(float(laminates[i][5]))
                    if len(laminates[i][6].lstrip())>0:
                        bi.append(float(laminates[i][6]))
                    if len(laminates[i][7].lstrip())>0:
                        tmidi.append(int(laminates[i][7]))
                 
                
                part = self.partManager.CreatePartComposite(id,name,elform, shrf,nloc,marea,hgid,adpopt,thshel,self.nodeManager)
                part.SetLaminates(midi, thicki, bi, tmidi)

        if elementMassKeyword is not None:
            parametersMass = elementMassKeyword.parameters
            self.partManager.AddMassElementsfromDyna(parametersMass, "MASS")
        if elementMassNodeSetKeyword is not None:
            parametersMassNodeSet = elementMassNodeSetKeyword.parameters
            self.partManager.AddMassElementsfromDyna(parametersMassNodeSet, "MASS_NODE_SET")

        if elementBeamKeyword is not None:
            parametersBeam = elementBeamKeyword.parameters
            self.partManager.AddBeamElementsfromDyna(parametersBeam)

        if elementShellKeyword is not None:
            parametersShell = elementShellKeyword.parameters
            self.partManager.AddShellElementsfromDyna(parametersShell)

        if elementShellThickKeyword is not None:
            parametersShellThick = elementShellThickKeyword.parameters
            self.partManager.AddShellElementsfromDyna(parametersShellThick)
                        
        if elementSolidKeyword is not None:
            parametersSolid = elementSolidKeyword.parameters
            #import time 
            #start = time.time()
            self.partManager.AddSolidElementsfromDynaAdvanced(parametersSolid)
            #self.partManager.AddSolidElementsfromDyna(parametersSolid)
            #end = time.time()
            #print("Solid Element Time: ", end - start)
        if "SET_PART" in dynaKeywords:
            setPartKeyword : SetPart = dynaKeywords["SET_PART"]
            setParts = setPartKeyword.getSetPart()
            for setPart in setParts:
                self.partManager.AddPartSetfromDyna(setPart)
        if "SET_PART_LIST" in dynaKeywords:
            setPartListKeyword : SetPartList = dynaKeywords["SET_PART_LIST"]
            setParts = setPartListKeyword.getSetPartList()
            for setPart in setParts:
                self.partManager.AddPartSetfromDyna(setPart)
        if "SET_PART_LIST_TITLE" in dynaKeywords:
            setPartListTitleKeyword : SetPartListTitle = dynaKeywords["SET_PART_LIST_TITLE"]
            setParts = setPartListTitleKeyword.getsSetPartListTitle()
            for setPart in setParts:
                self.partManager.AddPartSetfromDyna(setPart)
        return maxID

    def importSection(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "SECTION_BEAM_TITLE" in dynaKeyword:
            self.keywordInterpreted["SECTION_BEAM_TITLE"] = True
        if "SECTION_BEAM" in dynaKeyword:
            self.keywordInterpreted["SECTION_BEAM"] = True
        if "SECTION_SHELL_TITLE" in dynaKeyword:
            self.keywordInterpreted["SECTION_SHELL_TITLE"] = True
        if "SECTION_SHELL" in dynaKeyword:
            self.keywordInterpreted["SECTION_SHELL"] = True
        if "SECTION_SOLID" in dynaKeyword:
            self.keywordInterpreted["SECTION_SOLID"] = True
        if "SECTION_SOLID_TITLE" in dynaKeyword:
            self.keywordInterpreted["SECTION_SOLID_TITLE"] = True
        if "SECTION_SOLID_PERI" in dynaKeyword:
            self.keywordInterpreted["SECTION_SOLID_PERI"] = True
        if "SECTION_SOLID_PERI_TITLE" in dynaKeyword:
            self.keywordInterpreted["SECTION_SOLID_PERI_TITLE"] = True
        if "SECTION_TSHELL" in dynaKeyword:
            self.keywordInterpreted["SECTION_TSHELL"] = True
        if "SECTION_TSHELL_TITLE" in dynaKeyword:
            self.keywordInterpreted["SECTION_TSHELL_TITLE"] = True 
               
        if "SECTION_BEAM_TITLE" in dynaKeyword:
            sectionBeamTitleKeyword : SectionBeamTitle = dynaKeyword["SECTION_BEAM_TITLE"]
            sections = sectionBeamTitleKeyword.getSectionBeams()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_BEAM" in dynaKeyword:
            sectionBeamKeyword : SectionBeam = dynaKeyword["SECTION_BEAM"]
            sections = sectionBeamKeyword.getSectionBeams()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section) 
        if "SECTION_SHELL_TITLE" in dynaKeyword:
            sectionShellTitleKeyword : SectionShellTitle = dynaKeyword["SECTION_SHELL_TITLE"]
            sections = sectionShellTitleKeyword.getSectionShells()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_SHELL" in dynaKeyword:
            sectionShellKeyword : SectionShell = dynaKeyword["SECTION_SHELL"]
            sections = sectionShellKeyword.getSectionShells()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_SOLID" in dynaKeyword:
            sectionSolidKeyword : SectionSolid = dynaKeyword["SECTION_SOLID"]
            sections = sectionSolidKeyword.getSectionSolids()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_SOLID_TITLE" in dynaKeyword:
            sectionSolidTitleKeyword : SectionSolidTitle = dynaKeyword["SECTION_SOLID_TITLE"]
            sections = sectionSolidTitleKeyword.getSectionSolids()
            for section in sections:                
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_SOLID_PERI" in dynaKeyword:
            sectionSolidPeriKeyword : SectionSolidPeri = dynaKeyword["SECTION_SOLID_PERI"]
            sections = sectionSolidPeriKeyword.getSectionSolidPeris()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_SOLID_PERI_TITLE" in dynaKeyword:
            sectionSolidPeriTitleKeyword : SectionSolidPeriTitle = dynaKeyword["SECTION_SOLID_PERI_TITLE"]
            sections = sectionSolidPeriTitleKeyword.getSectionSolidPeris()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_TSHELL" in dynaKeyword:
            sectionTShellKeyword : SectionTShell = dynaKeyword["SECTION_TSHELL"]
            sections = sectionTShellKeyword.getSectionTShells()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        if "SECTION_TSHELL_TITLE" in dynaKeyword:
            sectionTShellTitleKeyword : SectionTShellTitle = dynaKeyword["SECTION_TSHELL_TITLE"]
            sections = sectionTShellTitleKeyword.getSectionTShells()
            for section in sections:
                self.sectionManager.AddSectionfromDyna(section)
        for part in self.partManager.parts:
            curPart : KooPart = self.partManager.parts[part]
            if curPart.secid > 0:
                curSection = self.sectionManager.FindSectionfromID(curPart.secid)
                if curSection is not None:
                    curPart.SetSection(curSection)
                else:
                    # PART가 참조하는 SECID가 로드된 섹션에 없음(미지원 SECTION 변형·미해결 참조 등).
                    # 크래시 대신 스킵 — 섹션 카드는 _write_uninterpreted_raw_blocks로 출력에 보존됨.
                    print(f"  Warning: Part {getattr(curPart, 'id', part)} references SECID "
                          f"{curPart.secid} with no loaded section — SetSection skipped")
        return self.sectionManager.maxid
    
    def importMaterial(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "EOS_TABULATED" in dynaKeyword:
            self.keywordInterpreted["EOS_TABULATED"] = True
        if "EOS_LINEAR_POLYNOMIAL" in dynaKeyword:
            self.keywordInterpreted["EOS_LINEAR_POLYNOMIAL"] = True
        if "MAT_ADD_EROSION" in dynaKeyword:
            self.keywordInterpreted["MAT_ADD_EROSION"] = True
        if "MAT_ADD_PZELECTRIC" in dynaKeyword:
            self.keywordInterpreted["MAT_ADD_PZELECTRIC"] = True
        if "MAT_ELASTIC_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_ELASTIC_TITLE"] = True
        if "MAT_ELASTIC" in dynaKeyword:
            self.keywordInterpreted["MAT_ELASTIC"] = True
        if "MAT_PLASTIC_KINEMATIC" in dynaKeyword:
            self.keywordInterpreted["MAT_PLASTIC_KINEMATIC"] = True
        if "MAT_PLASTIC_KINEMATIC_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_PLASTIC_KINEMATIC_TITLE"] = True
        if "MAT_SOIL_AND_FOAM" in dynaKeyword:
            self.keywordInterpreted["MAT_SOIL_AND_FOAM"] = True
        if "MAT_SOIL_AND_FOAM_FAILURE" in dynaKeyword:
            self.keywordInterpreted["MAT_SOIL_AND_FOAM_FAILURE"] = True
        if "MAT_NULL" in dynaKeyword:
            self.keywordInterpreted["MAT_NULL"] = True
        if "MAT_RIGID" in dynaKeyword:
            self.keywordInterpreted["MAT_RIGID"] = True
        if "MAT_RIGID_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_RIGID_TITLE"] = True
        if "MAT_COMPOSITE_DAMAGE" in dynaKeyword:
            self.keywordInterpreted["MAT_COMPOSITE_DAMAGE"] = True
        if "MAT_COMPOSITE_DAMAGE_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_COMPOSITE_DAMAGE_TITLE"] = True
        if "MAT_PIECEWISE_LINEAR_PLASTICITY" in dynaKeyword:
            self.keywordInterpreted["MAT_PIECEWISE_LINEAR_PLASTICITY"] = True
        if "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE"] = True
        if "MAT_ORIENTED_CRACK" in dynaKeyword:
            self.keywordInterpreted["MAT_ORIENTED_CRACK"] = True
        if "MAT_ENHANCED_COMPOSITE_DAMAGE" in dynaKeyword:
            self.keywordInterpreted["MAT_ENHANCED_COMPOSITE_DAMAGE"] = True
        if "MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE"] = True
        if "MAT_MOONEY_RIVLIN_RUBBER" in dynaKeyword:
            self.keywordInterpreted["MAT_MOONEY_RIVLIN_RUBBER"] = True
        if "MAT_MOONEY_RIVLIN_RUBBER_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_MOONEY_RIVLIN_RUBBER_TITLE"] = True
        if "MAT_LOW_DENSITY_FOAM" in dynaKeyword:
            self.keywordInterpreted["MAT_LOW_DENSITY_FOAM"] = True
        if "MAT_LOW_DENSITY_FOAM_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_LOW_DENSITY_FOAM_TITLE"] = True
        if "MAT_SPOTWELD" in dynaKeyword:
            self.keywordInterpreted["MAT_SPOTWELD"] = True
        if "MAT_SPOTWELD_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_SPOTWELD_TITLE"] = True
        if "MAT_COHESIVE_MIXED_MODE" in dynaKeyword:
            self.keywordInterpreted["MAT_COHESIVE_MIXED_MODE"] = True
        if "MAT_COHESIVE_MIXED_MODE_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_COHESIVE_MIXED_MODE_TITLE"] = True
        if "MAT_ELASTIC_PERI" in dynaKeyword:
            self.keywordInterpreted["MAT_ELASTIC_PERI"] = True
        if "MAT_ELASTIC_PERI_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_ELASTIC_PERI_TITLE"] = True
        if "MAT_VISCOELASTIC" in dynaKeyword:
            self.keywordInterpreted["MAT_VISCOELASTIC"] = True
        if "MAT_VISCOELASTIC_TITLE" in dynaKeyword:
            self.keywordInterpreted["MAT_VISCOELASTIC_TITLE"] = True
        
        if "EOS_TABULATED" in dynaKeyword:
            eosTabulatedKeyword : EOSTabulated = dynaKeyword["EOS_TABULATED"]
            materials = eosTabulatedKeyword.getEOSList()
            for material in materials:
                self.matManager.AddEOSfromDyna(material)
        if "EOS_LINEAR_POLYNOMIAL" in dynaKeyword:
            eosLinearPolynomialKeyword : EosLinearPolynomial = dynaKeyword["EOS_LINEAR_POLYNOMIAL"]
            materials = eosLinearPolynomialKeyword.getEOSLinearPolynomialList()
            for material in materials:
                self.matManager.AddEOSfromDyna(material)
        if "MAT_ADD_EROSION" in dynaKeyword:
            matAddErosionKeyword : MatAddErosion = dynaKeyword["MAT_ADD_EROSION"]
            materials = matAddErosionKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_ADD_PZELECTRIC" in dynaKeyword:
            matAddPZElectricKeyword : MatAddPZElectric = dynaKeyword["MAT_ADD_PZELECTRIC"]
            materials = matAddPZElectricKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_ELASTIC_TITLE" in dynaKeyword:
            matElasticTitleKeyword : MatElasticTitle = dynaKeyword["MAT_ELASTIC_TITLE"]
            materials = matElasticTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                #print(material)
        if "MAT_ELASTIC" in dynaKeyword:
            matElasticKeyword : MatElastic = dynaKeyword["MAT_ELASTIC"]
            materials = matElasticKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                #print(material)
        if "MAT_PLASTIC_KINEMATIC" in dynaKeyword:
            matPlasticKinematicKeyword : MatPlasticKinematic = dynaKeyword["MAT_PLASTIC_KINEMATIC"]
            materials = matPlasticKinematicKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_PLASTIC_KINEMATIC_TITLE" in dynaKeyword:
            matPlasticKinematicTitleKeyword : MatPlasticKinematicTitle = dynaKeyword["MAT_PLASTIC_KINEMATIC_TITLE"]
            materials = matPlasticKinematicTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_SOIL_AND_FOAM" in dynaKeyword:
            matSoilandFoamKeyword : MatSoilAndFoam = dynaKeyword["MAT_SOIL_AND_FOAM"]
            materials = matSoilandFoamKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_SOIL_AND_FOAM_FAILURE" in dynaKeyword:
            matSoilandFoamFailureKeyword : MatSoilAndFoamFailure = dynaKeyword["MAT_SOIL_AND_FOAM_FAILURE"]
            materials = matSoilandFoamFailureKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_NULL" in dynaKeyword:
            matNullKeyword : MatNull = dynaKeyword["MAT_NULL"]
            materials = matNullKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_RIGID" in dynaKeyword:
            matRigidKeyword : MatRigid = dynaKeyword["MAT_RIGID"]
            materials = matRigidKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_RIGID_TITLE" in dynaKeyword:
            matRigidTitleKeyword : MatRigidTitle = dynaKeyword["MAT_RIGID_TITLE"]
            materials = matRigidTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_COMPOSITE_DAMAGE" in dynaKeyword:
            matCompositeDamageKeyword : MatCompositeDamage = dynaKeyword["MAT_COMPOSITE_DAMAGE"]
            materials = matCompositeDamageKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_COMPOSITE_DAMAGE_TITLE" in dynaKeyword:
            matCompositeDamageTitleKeyword : MatCompositeDamageTitle = dynaKeyword["MAT_COMPOSITE_DAMAGE_TITLE"]
            materials = matCompositeDamageTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_PIECEWISE_LINEAR_PLASTICITY" in dynaKeyword:
            matPiecewiseLinearPlasticityKeyword : MatPiecewiseLinearPlasticity = dynaKeyword["MAT_PIECEWISE_LINEAR_PLASTICITY"]
            materials = matPiecewiseLinearPlasticityKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" in dynaKeyword:
            matPiecewiseLinearPlasticityTitleKeyword : MatPiecewiseLinearPlasticityTitle = dynaKeyword["MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE"]
            materials = matPiecewiseLinearPlasticityTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_ORIENTED_CRACK" in dynaKeyword:
            matOrientedCrackKeyword : MatOrientedCrack = dynaKeyword["MAT_ORIENTED_CRACK"]
            materials = matOrientedCrackKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                #print(material)            
        if "MAT_ENHANCED_COMPOSITE_DAMAGE" in dynaKeyword:
            matEnhancedCompositeDamageKeyword : MatEnhancedCompositeDamage = dynaKeyword["MAT_ENHANCED_COMPOSITE_DAMAGE"]
            materials = matEnhancedCompositeDamageKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE" in dynaKeyword:
            matEnhancedCompositeDamageTitleKeyword : MatEnhancedCompositeDamageTitle = dynaKeyword["MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE"]
            materials = matEnhancedCompositeDamageTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_MOONEY_RIVLIN_RUBBER" in dynaKeyword:
            matMooneyRivlinRubberKeyword : MatMooneyRivlinRubber = dynaKeyword["MAT_MOONEY_RIVLIN_RUBBER"]
            materials = matMooneyRivlinRubberKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_MOONEY_RIVLIN_RUBBER_TITLE" in dynaKeyword:
            matMooneyRivlinRubberTitleKeyword : MatMooneyRivlinRubberTitle = dynaKeyword["MAT_MOONEY_RIVLIN_RUBBER_TITLE"]
            materials = matMooneyRivlinRubberTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_LOW_DENSITY_FOAM" in dynaKeyword:
            matLowDensityFoamKeyword : MatLowDensityFoam = dynaKeyword["MAT_LOW_DENSITY_FOAM"]
            materials = matLowDensityFoamKeyword.getMatList()
            
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                #print(material)
        if "MAT_LOW_DENSITY_FOAM_TITLE" in dynaKeyword:
            matLowDensityFoamTitleKeyword : MatLowDensityFoamTitle = dynaKeyword["MAT_LOW_DENSITY_FOAM_TITLE"]
            materials = matLowDensityFoamTitleKeyword.getMatList()
           
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                #print(material)
        if "MAT_SPOTWELD" in dynaKeyword:
            matSpotweldKeyword : MatSpotweld = dynaKeyword["MAT_SPOTWELD"]
            materials = matSpotweldKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_SPOTWELD_TITLE" in dynaKeyword:
            matSpotweldTitleKeyword : MatSpotweldTitle = dynaKeyword["MAT_SPOTWELD_TITLE"]
            materials = matSpotweldTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)                        
                #print(material)    
        if "MAT_COHESIVE_MIXED_MODE" in dynaKeyword:
            matCohesiveMixedModeKeyword : MatCohesiveMixedMode = dynaKeyword["MAT_COHESIVE_MIXED_MODE"]
            materials = matCohesiveMixedModeKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_COHESIVE_MIXED_MODE_TITLE" in dynaKeyword:
            matCohesiveMixedModeTitleKeyword : MatCohesiveMixedModeTitle = dynaKeyword["MAT_COHESIVE_MIXED_MODE_TITLE"]
            materials = matCohesiveMixedModeTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_ELASTIC_PERI_TITLE" in dynaKeyword:
            matElasticPeriTitleKeyword : MatElasticPeriTitle = dynaKeyword["MAT_ELASTIC_PERI_TITLE"]
            materials = matElasticPeriTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_VISCOELASTIC" in dynaKeyword:                
            matViscoelasticKeyword : MatViscoelastic = dynaKeyword["MAT_VISCOELASTIC"]
            materials = matViscoelasticKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
        if "MAT_VISCOELASTIC_TITLE" in dynaKeyword:
            matViscoelasticTitleKeyword : MatViscoelasticTitle = dynaKeyword["MAT_VISCOELASTIC_TITLE"]
            materials = matViscoelasticTitleKeyword.getMatList()
            for material in materials:
                self.matManager.AddMaterialfromDyna(material)
                    
        #print ("Material Import Done")
        #for mat in self.matManager.materials:
        #    print(self.matManager.materials[mat])
        for part in self.partManager.parts:
            curPart : KooPart = self.partManager.parts[part]
            if curPart.mid > 0:
                curMaterial = self.matManager.FindMaterialfromID(curPart.mid)
                #print(curMaterial)
                if curMaterial is not None:
                    curPart.SetMaterial(curMaterial)
                else:
                    # PART가 참조하는 MID가 로드된 재료에 없음(MAT_GENERAL_VISCOELASTIC 등 미지원 재료).
                    # 크래시 대신 스킵 — 재료 카드는 _write_uninterpreted_raw_blocks로 출력에 보존됨.
                    print(f"  Warning: Part {getattr(curPart, 'id', part)} references MID "
                          f"{curPart.mid} with no loaded material — SetMaterial skipped")
        return self.matManager.maxid

    def importDefine(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "DEFINE_CURVE" in dynaKeyword:
            self.keywordInterpreted["DEFINE_CURVE"] = True
        if "DEFINE_CURVE_TITLE" in dynaKeyword:
            self.keywordInterpreted["DEFINE_CURVE_TITLE"] = True
        if "DEFINE_COORDINATE_SYSTEM" in dynaKeyword:
            self.keywordInterpreted["DEFINE_COORDINATE_SYSTEM"] = True
        if "DEFINE_COORDINATE_SYSTEM_TITLE" in dynaKeyword:
            self.keywordInterpreted["DEFINE_COORDINATE_SYSTEM_TITLE"] = True
            
        if "DEFINE_CURVE" in dynaKeyword:
            defineCurveKeyword : DefineCurve = dynaKeyword["DEFINE_CURVE"]
            defines = defineCurveKeyword.getDefineCurveList()
            for define in defines:
                self.defineManager.AddDefinefromDyna(define)
        if "DEFINE_CURVE_TITLE" in dynaKeyword:
            defineCurveTitleKeyword : DefineCurveTitle = dynaKeyword["DEFINE_CURVE_TITLE"]
            defines = defineCurveTitleKeyword.getDefineCurveList()
            for define in defines:
                self.defineManager.AddDefinefromDyna(define)
        if "DEFINE_COORDINATE_SYSTEM" in dynaKeyword:
            defineCoordinateSystemKeyword : DefineCoordinateSystem = dynaKeyword["DEFINE_COORDINATE_SYSTEM"]
            defines = defineCoordinateSystemKeyword.getDefineCoordinateSystemList()
            for define in defines:
                self.defineManager.AddDefinefromDyna(define)
        if "DEFINE_COORDINATE_SYSTEM_TITLE" in dynaKeyword:
            defineCoordinateSystemTitleKeyword : DefineCoordinateSystemTitle = dynaKeyword["DEFINE_COORDINATE_SYSTEM_TITLE"]
            defines = defineCoordinateSystemTitleKeyword.getDefineCoordinateSystemTitleList()
            for define in defines:
                self.defineManager.AddDefinefromDyna(define)
            
        return self.defineManager.maxid
    
    def importLoad(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "LOAD_NODE_POINT" in dynaKeyword:
            self.keywordInterpreted["LOAD_NODE_POINT"] = True
        if "LOAD_SEGMENT" in dynaKeyword:
            self.keywordInterpreted["LOAD_SEGMENT"] = True
        if "LOAD_SEGMENT_ID" in dynaKeyword:
            self.keywordInterpreted["LOAD_SEGMENT_ID"] = True
        if "LOAD_SEGMENT_SET" in dynaKeyword:
            self.keywordInterpreted["LOAD_SEGMENT_SET"] = True
        if "LOAD_SEGMENT_SET_ID" in dynaKeyword:
            self.keywordInterpreted["LOAD_SEGMENT_SET_ID"] = True
        if "LOAD_BODY_X" in dynaKeyword:
            self.keywordInterpreted["LOAD_BODY_X"] = True
        if "LOAD_BODY_Y" in dynaKeyword:
            self.keywordInterpreted["LOAD_BODY_Y"] = True
        if "LOAD_BODY_Z" in dynaKeyword:
            self.keywordInterpreted["LOAD_BODY_Z"] = True
        if "LOAD_BODY_VECTOR" in dynaKeyword:
            self.keywordInterpreted["LOAD_BODY_VECTOR"] = True
        
        
        if "LOAD_NODE_POINT" in dynaKeyword:
            loadNodePointKeyword : LoadNodePoint = dynaKeyword["LOAD_NODE_POINT"]
            loads = loadNodePointKeyword.getLoadNodePointList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_SEGMENT" in dynaKeyword:
            loadSegmentKeyword : LoadSegment = dynaKeyword["LOAD_SEGMENT"]
            loads = loadSegmentKeyword.getLoadSegmentList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_SEGMENT_ID" in dynaKeyword:
            loadSegmentIDKeyword : LoadSegmentID = dynaKeyword["LOAD_SEGMENT_ID"]
            loads = loadSegmentIDKeyword.getLoadSegmentIDList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_SEGMENT_SET" in dynaKeyword:
            loadSegmentSetKeyword : LoadSegmentSet = dynaKeyword["LOAD_SEGMENT_SET"]
            loads = loadSegmentSetKeyword.getLoadSegmentSetList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_SEGMENT_SET_ID" in dynaKeyword:
            loadSegmentSetIDKeyword : LoadSegmentSetID = dynaKeyword["LOAD_SEGMENT_SET_ID"]
            loads = loadSegmentSetIDKeyword.getLoadSegmentSetIDList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_X" in dynaKeyword:
            loadBodyXKeyword : LoadBodyX = dynaKeyword["LOAD_BODY_X"]
            loads = loadBodyXKeyword.getLoadBodyXList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_Y" in dynaKeyword:
            loadBodyYKeyword : LoadBodyY = dynaKeyword["LOAD_BODY_Y"]
            loads = loadBodyYKeyword.getLoadBodyYList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_Z" in dynaKeyword:
            loadBodyZKeyword : LoadBodyZ = dynaKeyword["LOAD_BODY_Z"]
            loads = loadBodyZKeyword.getLoadBodyZList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_RX" in dynaKeyword:
            loadBodyRXKeyword : LoadBodyRX = dynaKeyword["LOAD_BODY_RX"]
            loads = loadBodyRXKeyword.getLoadBodyRXList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_RY" in dynaKeyword:
            loadBodyRYKeyword : LoadBodyRY = dynaKeyword["LOAD_BODY_RY"]
            loads = loadBodyRYKeyword.getLoadBodyRYList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_RZ" in dynaKeyword:
            loadBodyRZKeyword : LoadBodyRZ = dynaKeyword["LOAD_BODY_RZ"]
            loads = loadBodyRZKeyword.getLoadBodyRZList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)
        if "LOAD_BODY_VECTOR" in dynaKeyword:
            loadBodyVectorKeyword : LoadBodyVector = dynaKeyword["LOAD_BODY_VECTOR"]
            loads = loadBodyVectorKeyword.getLoadBodyVectorList()
            for load in loads:
                self.loadManager.AddLoadfromDyna(load, self.nodeManager,self.nodeSetManager,self.segmentSetManager)

    def importBoundaryNode(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "BOUNDARY_SPC_NODE" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_SPC_NODE"] = True
        if "BOUNDARY_SPC_NODE_ID" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_SPC_NODE_ID"] = True
        if "BOUNDARY_PRESCRIBED_MOTION_NODE" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_PRESCRIBED_MOTION_NODE"] = True
        if "BOUNDARY_PRESCRIBED_MOTION_NODE_ID" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_PRESCRIBED_MOTION_NODE_ID"] = True            
        if "BOUNDARY_PRESCRIBED_MOTION_RIGID" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_PRESCRIBED_MOTION_RIGID"] = True
        if "BOUNDARY_PRESCRIBED_MOTION_RIGID_ID" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_PRESCRIBED_MOTION_RIGID_ID"] = True
        if "BOUNDARY_PZEPOT" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_PZEPOT"] = True
        if "BOUNDARY_SPC_SET" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_SPC_SET"] = True
        if "BOUNDARY_SPC_SET_ID" in dynaKeyword:
            self.keywordInterpreted["BOUNDARY_SPC_SET_ID"] = True
        
        if "BOUNDARY_SPC_NODE" in dynaKeyword:
            boundarySpcNodeKeyword : BoundarySPCNode = dynaKeyword["BOUNDARY_SPC_NODE"]
            boundaryNodes = boundarySpcNodeKeyword.getBoundarySpcNodeList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_SPC_NODE_ID" in dynaKeyword:
            boundarySpcNodeIDKeyword : BoundarySPCNodeID = dynaKeyword["BOUNDARY_SPC_NODE_ID"]
            boundaryNodes = boundarySpcNodeIDKeyword.getBoundarySpcNodeIDList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_PRESCRIBED_MOTION_NODE" in dynaKeyword:
            boundaryPrescribedMotionNodeKeyword : BoundaryPrescribedMotionNode = dynaKeyword["BOUNDARY_PRESCRIBED_MOTION_NODE"]
            boundaryNodes = boundaryPrescribedMotionNodeKeyword.getBoundaryPrescribedMotionNodeList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_PRESCRIBED_MOTION_NODE_ID" in dynaKeyword:
            boundaryPrescribedMotionNodeIDKeyword : BoundaryPrescribedMotionNodeID = dynaKeyword["BOUNDARY_PRESCRIBED_MOTION_NODE_ID"]
            boundaryNodes = boundaryPrescribedMotionNodeIDKeyword.getBoundaryPrescribedMotionNodeIDList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_PRESCRIBED_MOTION_RIGID" in dynaKeyword:
            boundaryPrescribedMotionRigidKeyword : BoundaryPrescribedMotionRigid = dynaKeyword["BOUNDARY_PRESCRIBED_MOTION_RIGID"]
            boundaryNodes = boundaryPrescribedMotionRigidKeyword.getBoundaryPrescribedMotionRigidList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_PRESCRIBED_MOTION_RIGID_ID" in dynaKeyword:
            boundaryPrescribedMotionRigidIDKeyword : BoundaryPrescribedMotionRigidID = dynaKeyword["BOUNDARY_PRESCRIBED_MOTION_RIGID_ID"]
            boundaryNodes = boundaryPrescribedMotionRigidIDKeyword.getBoundaryPrescribedMotionRigidIDList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_PZEPOT" in dynaKeyword:
            boundaryPZEPOTKeyword : BoundaryPZEPOT = dynaKeyword["BOUNDARY_PZEPOT"]
            boundaryNodes = boundaryPZEPOTKeyword.getBoundaryPZEPOTList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_SPC_SET" in dynaKeyword:
            boundarySpcSetKeyword : BoundarySPCSet = dynaKeyword["BOUNDARY_SPC_SET"]
            boundaryNodes = boundarySpcSetKeyword.getBoundarySpcSetList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
        if "BOUNDARY_SPC_SET_ID" in dynaKeyword:
            boundarySpcSetIDKeyword : BoundarySPCSetID = dynaKeyword["BOUNDARY_SPC_SET_ID"]
            boundaryNodes = boundarySpcSetIDKeyword.getBoundarySpcSetIDList()
            for boundaryNode in boundaryNodes:
                self.boundaryNodeManager.AddBoundaryNodefromDyna(boundaryNode,self.nodeManager, self.nodeSetManager)
    
    def importControl(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "CONTROL_TERMINATION" in dynaKeyword:
            self.keywordInterpreted["CONTROL_TERMINATION"] = True 
        if "CONTROL_TIMESTEP" in dynaKeyword:
            self.keywordInterpreted["CONTROL_TIMESTEP"] = True
        if "CONTROL_HOURGLASS" in dynaKeyword:
            self.keywordInterpreted["CONTROL_HOURGLASS"] = True
        if "CONTROL_ACCURACY" in dynaKeyword:
            self.keywordInterpreted["CONTROL_ACCURACY"] = True
        if "CONTROL_DYNAMIC_RELAXATION" in dynaKeyword:
            self.keywordInterpreted["CONTROL_DYNAMIC_RELAXATION"] = True
        if "CONTROL_ENERGY" in dynaKeyword:
            self.keywordInterpreted["CONTROL_ENERGY"] = True
        if "CONTROL_CONTACT" in dynaKeyword:
            self.keywordInterpreted["CONTROL_CONTACT"] = True
        if "CONTROL_MPP_IO_NODUMP" in dynaKeyword:
            self.keywordInterpreted["CONTROL_MPP_IO_NODUMP"] = True
        if "CONTROL_BULK_VISCOSITY" in dynaKeyword:
            self.keywordInterpreted["CONTROL_BULK_VISCOSITY"] = True
        if "CONTROL_OUTPUT" in dynaKeyword:
            self.keywordInterpreted["CONTROL_OUTPUT"] = True
        if "CONTROL_SHELL" in dynaKeyword:
            self.keywordInterpreted["CONTROL_SHELL"] = True
        if "CONTROL_SOLID" in dynaKeyword:
            self.keywordInterpreted["CONTROL_SOLID"] = True
            
        if "CONTROL_TERMINATION" in dynaKeyword:
            controlTerminationKeyword : ControlTermination = dynaKeyword["CONTROL_TERMINATION"]
            control = controlTerminationKeyword.getControlTermination()
            self.controlManager.SetControlfromDyna(control)               
        if "CONTROL_TIMESTEP" in dynaKeyword:
            controlTimeStepKeyword : ControlTimeStep = dynaKeyword["CONTROL_TIMESTEP"]
            control = controlTimeStepKeyword.getControlTimeStep()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_HOURGLASS" in dynaKeyword:
            controlHourglassKeyword : ControlHourglass = dynaKeyword["CONTROL_HOURGLASS"]
            control = controlHourglassKeyword.getControlHourglass()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_ACCURACY" in dynaKeyword:
            controlAccuracyKeyword = dynaKeyword["CONTROL_ACCURACY"]
            control = controlAccuracyKeyword.getControlAccuracy()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_DYNAMIC_RELAXATION" in dynaKeyword:
            controlDynamicRelaxationKeyword : ControlDynamicRelaxation = dynaKeyword["CONTROL_DYNAMIC_RELAXATION"]
            control = controlDynamicRelaxationKeyword.getControlDynamicRelaxation()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_ENERGY" in dynaKeyword:
            controlEnergyKeyword : ControlEnergy = dynaKeyword["CONTROL_ENERGY"]
            control = controlEnergyKeyword.getControlEnergy()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_CONTACT" in dynaKeyword:
            controlContactKeyword : ControlContact = dynaKeyword["CONTROL_CONTACT"]            
            control = controlContactKeyword.getControlContact()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_MPP_IO_NODUMP" in dynaKeyword:
            controlMppIONoDumpKeyword : ControlMppIoNodump = dynaKeyword["CONTROL_MPP_IO_NODUMP"]
            control = controlMppIONoDumpKeyword.getControlMppIONoDump()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_BULK_VISCOSITY" in dynaKeyword:
            controlBulkViscosityKeyword : ControlBulkViscosity = dynaKeyword["CONTROL_BULK_VISCOSITY"]
            control = controlBulkViscosityKeyword.getControlBulkViscosity()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_OUTPUT" in dynaKeyword:
            controlOutputKeyword : ControlOutput = dynaKeyword["CONTROL_OUTPUT"]
            control = controlOutputKeyword.getControlOutput()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_SHELL" in dynaKeyword:
            controlShellKeyword : ControlShell = dynaKeyword["CONTROL_SHELL"]
            control = controlShellKeyword.getControlShell()
            self.controlManager.SetControlfromDyna(control)
        if "CONTROL_SOLID" in dynaKeyword:
            controlSolidKeyword : ControlSolid = dynaKeyword["CONTROL_SOLID"]
            control = controlSolidKeyword.getControlSolid()
            self.controlManager.SetControlfromDyna(control)

    def importContact(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "CONTACT_ADD_WEAR" in dynaKeyword:
            self.keywordInterpreted["CONTACT_ADD_WEAR"] = True
        if "CONTACT_AUTOMATIC_GENERAL" in dynaKeyword:
            self.keywordInterpreted["CONTACT_AUTOMATIC_GENERAL"] = True
        if "CONTACT_AUTOMATIC_GENERAL_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_AUTOMATIC_GENERAL_ID"] = True
        if "CONTACT_AUTOMATIC_SINGLE_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_AUTOMATIC_SINGLE_SURFACE"] = True
        if "CONTACT_AUTOMATIC_SINGLE_SURFACE_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_AUTOMATIC_SINGLE_SURFACE_ID"] = True
        if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"] = True
        if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID" in dynaKeyword:    
            self.keywordInterpreted["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"] = True
        if "CONTACT_ERODING_NODES_TO_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_ERODING_NODES_TO_SURFACE"] = True
        if "CONTACT_ERODING_NODES_TO_SURFACE_ID" in dynaKeyword:            
            self.keywordInterpreted["CONTACT_ERODING_NODES_TO_SURFACE_ID"] = True
        if "CONTACT_ERODING_SURFACE_TO_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_ERODING_SURFACE_TO_SURFACE"] = True
        if "CONTACT_ERODING_SURFACE_TO_SURFACE_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_ERODING_SURFACE_TO_SURFACE_ID"] = True
        if "CONTACT_FEM_PERI_TIE_BREAK_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_FEM_PERI_TIE_BREAK_ID"] = True
        if "CONTACT_SINGLE_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_SINGLE_SURFACE"] = True
        if "CONTACT_SINGLE_SURFACE_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_SINGLE_SURFACE_ID"] = True
        if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET"] = True
        if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID"] = True
        if "CONTACT_TIED_SURFACE_TO_SURFACE" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SURFACE_TO_SURFACE"] = True
        if "CONTACT_TIED_SURFACE_TO_SURFACE_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SURFACE_TO_SURFACE_ID"] = True        
        if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET"] = True
        if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID" in dynaKeyword:
            self.keywordInterpreted["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID"] = True
            
            
        if "CONTACT_ADD_WEAR" in dynaKeyword:
            contactAddWearKeyword : ContactAddWear = dynaKeyword["CONTACT_ADD_WEAR"]
            contacts = contactAddWearKeyword.getContactAddWearList()
            for contact in contacts:
                self.contactManager.AddContactAddWearfromDyna(contact)
        if "CONTACT_AUTOMATIC_GENERAL" in dynaKeyword:
            automaticGeneralKeyword : ContactAutomaticGeneral = dynaKeyword["CONTACT_AUTOMATIC_GENERAL"]
            contacts = automaticGeneralKeyword.getAutomaticGeneralList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_AUTOMATIC_GENERAL_ID" in dynaKeyword:
            automaticGeneralIDKeyword : ContactAutomaticGeneralID = dynaKeyword["CONTACT_AUTOMATIC_GENERAL_ID"]
            contacts = automaticGeneralIDKeyword.getAutomaticGeneralIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_AUTOMATIC_SINGLE_SURFACE" in dynaKeyword:
            automaticSingleSurfaceKeyword : ContactAutomaticSingleSurface = dynaKeyword["CONTACT_AUTOMATIC_SINGLE_SURFACE"]
            contacts = automaticSingleSurfaceKeyword.getAutomaticSingleSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_AUTOMATIC_SINGLE_SURFACE_ID" in dynaKeyword:
            automaticSingleSurfaceIDKeyword : ContactAutomaticSingleSurfaceID = dynaKeyword["CONTACT_AUTOMATIC_SINGLE_SURFACE_ID"]
            contacts = automaticSingleSurfaceIDKeyword.getAutomaticSingleSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" in dynaKeyword:
            automaticSurfaceToSurfaceKeyword : ContactAutomaticSurfaceToSurface = dynaKeyword["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"]
            contacts = automaticSurfaceToSurfaceKeyword.getAutomaticSurfacetoSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID" in dynaKeyword:
            automaticSurfaceToSurfaceIDKeyword : ContactAutomaticSurfaceToSurfaceID = dynaKeyword["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"]
            contacts = automaticSurfaceToSurfaceIDKeyword.getAutomaticSurfacetoSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_ERODING_NODES_TO_SURFACE" in dynaKeyword:
            erodingNodesToSurfaceKeyword : ContactErodingNodesToSurface = dynaKeyword["CONTACT_ERODING_NODES_TO_SURFACE"]
            contacts = erodingNodesToSurfaceKeyword.getErodingNodesToSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_ERODING_NODES_TO_SURFACE_ID" in dynaKeyword:
            erodingNodesToSurfaceIDKeyword : ContactErodingNodesToSurfaceID = dynaKeyword["CONTACT_ERODING_NODES_TO_SURFACE_ID"]
            contacts = erodingNodesToSurfaceIDKeyword.getErodingNodesToSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_ERODING_SURFACE_TO_SURFACE" in dynaKeyword:
            erodingSurfaceToSurfaceKeyword : ContactErodingSurfaceToSurface = dynaKeyword["CONTACT_ERODING_SURFACE_TO_SURFACE"]
            contacts = erodingSurfaceToSurfaceKeyword.getErodingSurfaceToSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_ERODING_SURFACE_TO_SURFACE_ID" in dynaKeyword:
            erodingSurfaceToSurfaceIDKeyword : ContactErodingSurfaceToSurfaceID = dynaKeyword["CONTACT_ERODING_SURFACE_TO_SURFACE_ID"]
            contacts = erodingSurfaceToSurfaceIDKeyword.getErodingSurfaceToSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_FEM_PERI_TIE_BREAK_ID" in dynaKeyword:
            femPeriTieBreakIDKeyword : ContactFEMPERITieBreakID = dynaKeyword["CONTACT_FEM_PERI_TIE_BREAK_ID"]
            contacts = femPeriTieBreakIDKeyword.getContactFEMPERITieBreakIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact) 
        if "CONTACT_SINGLE_SURFACE" in dynaKeyword:
            singleSurfaceKeyword : ContactSingleSurface = dynaKeyword["CONTACT_SINGLE_SURFACE"]
            contacts = singleSurfaceKeyword.getContactSingleSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_SINGLE_SURFACE_ID" in dynaKeyword:
            singleSurfaceIDKeyword : ContactSingleSurfaceID = dynaKeyword["CONTACT_SINGLE_SURFACE_ID"]
            contacts = singleSurfaceIDKeyword.getContactSingleSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET" in dynaKeyword:
            tiedShellEdgeToSurfaceBeamOffsetKeyword : ContactTiedShellEdgeToSurfaceBeamOffset = dynaKeyword["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET"]
            contacts = tiedShellEdgeToSurfaceBeamOffsetKeyword.getContactTiedShellEdgeToSurfaceBeamOffsetList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID" in dynaKeyword:
            tiedShellEdgeToSurfaceBeamOffsetIDKeyword : ContactTiedShellEdgeToSurfaceBeamOffsetID = dynaKeyword["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID"]
            contacts = tiedShellEdgeToSurfaceBeamOffsetIDKeyword.getContactTiedShellEdgeToSurfaceBeamOffsetIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_TIED_SURFACE_TO_SURFACE" in dynaKeyword:
            tiedSurfaceToSurfaceKeyword : ContactTiedSurfaceToSurface = dynaKeyword["CONTACT_TIED_SURFACE_TO_SURFACE"]
            contacts = tiedSurfaceToSurfaceKeyword.getContactTiedSurfaceToSurfaceList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_TIED_SURFACE_TO_SURFACE_ID" in dynaKeyword:
            tiedSurfaceToSurfaceIDKeyword : ContactTiedSurfaceToSurfaceID = dynaKeyword["CONTACT_TIED_SURFACE_TO_SURFACE_ID"]
            contacts = tiedSurfaceToSurfaceIDKeyword.getContactTiedSurfaceToSurfaceIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact)
        if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET" in dynaKeyword:
            tiedSurfaceToSurfaceOffsetKeyword : ContactTiedSurfaceToSurfaceOffset = dynaKeyword["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET"]
            contacts = tiedSurfaceToSurfaceOffsetKeyword.getContactTiedSurfaceToSurfaceOffsetList()
            for contact in contacts:
                self.contactManager.AddContactfromDyna(contact)
        if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID" in dynaKeyword:
            tiedSurfaceToSurfaceOffsetIDKeyword : ContactTiedSurfaceToSurfaceOffsetID = dynaKeyword["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID"]
            contacts = tiedSurfaceToSurfaceOffsetIDKeyword.getContactTiedSurfaceToSurfaceOffsetIDList()
            for contact in contacts:
                self.contactManager.AddContactfromDynawithID(contact) 
            
    def importSegmentSet(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "SET_SEGMENT" in dynaKeyword:
            self.keywordInterpreted["SET_SEGMENT"] = True
        if "SET_SEGMENT_TITLE" in dynaKeyword:
            self.keywordInterpreted["SET_SEGMENT_TITLE"] = True
        
        if "SET_SEGMENT" in dynaKeyword:
            setSegmentKeyword : SetSegment = dynaKeyword["SET_SEGMENT"]
            sets = setSegmentKeyword.getSetSegmentList()
            for aSet in sets:
                self.segmentSetManager.AddSegmentSetfromDyna(aSet)
        if "SET_SEGMENT_TITLE" in dynaKeyword:
            setSegmentTitleKeyword : SetSegmentTitle = dynaKeyword["SET_SEGMENT_TITLE"]
            sets = setSegmentTitleKeyword.getSetSegmentTitleList()
            for aSet in sets:
                self.segmentSetManager.AddSegmentSetfromDyna(aSet)
    
    def importDamping(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "DAMPING_GLOBAL" in dynaKeyword:
            self.keywordInterpreted["DAMPING_GLOBAL"] = True
        if "DAMPING_PART_STIFFNESS" in dynaKeyword:
            self.keywordInterpreted["DAMPING_PART_STIFFNESS"] = True
        if "DAMPING_PART_STIFFNESS_SET" in dynaKeyword:
            self.keywordInterpreted["DAMPING_PART_STIFFNESS_SET"] = True
        if "DAMPING_PART_MASS" in dynaKeyword:
            self.keywordInterpreted["DAMPING_PART_MASS"] = True
        if "DAMPING_PART_MASS_SET" in dynaKeyword:
            self.keywordInterpreted["DAMPING_PART_MASS_SET"] = True
        if "DAMPING_GLOBAL" in dynaKeyword:
            dampingGlobalKeyword : DampingGlobal = dynaKeyword["DAMPING_GLOBAL"]
            damping = dampingGlobalKeyword.getDampingGlobal()
            
            self.dampingManager.SetDampingfromDyna(damping)
        if "DAMPING_PART_STIFFNESS" in dynaKeyword:
            dampingPartStiffnessKeyword : DampingPartStiffness = dynaKeyword["DAMPING_PART_STIFFNESS"]
            dampings = dampingPartStiffnessKeyword.getDampingPartStiffness()
            for damping in dampings:
                self.dampingManager.SetDampingfromDyna(damping)
        if "DAMPING_PART_STIFFNESS_SET" in dynaKeyword:
            dampingPartStiffnessSetKeyword : DampingPartStiffnessSet = dynaKeyword["DAMPING_PART_STIFFNESS_SET"]
            dampings = dampingPartStiffnessSetKeyword.getDampingPartStiffnessSet()
            for damping in dampings:
                self.dampingManager.SetDampingfromDyna(damping)
        if "DAMPING_PART_MASS" in dynaKeyword:
            dampingPartMassKeyword : DampingPartMass = dynaKeyword["DAMPING_PART_MASS"]
            dampings = dampingPartMassKeyword.getDampingPartMass()
            for damping in dampings:
                self.dampingManager.SetDampingfromDyna(damping)
        if "DAMPING_PART_MASS_SET" in dynaKeyword:
            dampingPartMassSetKeyword : DampingPartMassSet = dynaKeyword["DAMPING_PART_MASS_SET"]
            dampings = dampingPartMassSetKeyword.getDampingPartMassSet()
            for damping in dampings:
                self.dampingManager.SetDampingfromDyna(damping)
                
    def importDatabase(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "DATABASE_BNDOUT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BNDOUT"] = True
        if "DATABASE_ELOUT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_ELOUT"] = True
        if "DATABASE_SPCFORC" in dynaKeyword:
            self.keywordInterpreted["DATABASE_SPCFORC"] = True
        if "DATABASE_RBDOUT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_RBDOUT"] = True
        if "DATABASE_RWFORC" in dynaKeyword:
            self.keywordInterpreted["DATABASE_RWFORC"] = True
        if "DATABASE_RCFORC" in dynaKeyword:
            self.keywordInterpreted["DATABASE_RCFORC"] = True
        if "DATABASE_NODFOR" in dynaKeyword:
            self.keywordInterpreted["DATABASE_NODFOR"] = True
        if "DATABASE_NODOUT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_NODOUT"] = True
        if "DATABASE_GLSTAT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_GLSTAT"] = True
        if "DATABASE_MATSUM" in dynaKeyword:
            self.keywordInterpreted["DATABASE_MATSUM"] = True        
        if "DATABASE_SLEOUT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_SLEOUT"] = True                             
        if "DATABASE_HISTORY_NODE" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_NODE"] = True
        if "DATABASE_HISTORY_BEAM" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_BEAM"] = True
        if "DATABASE_HISTORY_BEAM_SET" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_BEAM_SET"] = True
        if "DATABASE_HISTORY_SHELL" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_SHELL"] = True
        if "DATABASE_HISTORY_SHELL_SET" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_SHELL_SET"] = True
        if "DATABASE_HISTORY_SOLID" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_SOLID"] = True
        if "DATABASE_HISTORY_SOLID_SET" in dynaKeyword:
            self.keywordInterpreted["DATABASE_HISTORY_SOLID_SET"] = True
        if "DATABASE_BINARY_D3PLOT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BINARY_D3PLOT"] = True
        if "DATABASE_BINARY_D3THDT" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BINARY_D3THDT"] = True
        if "DATABASE_BINARY_D3DUMP" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BINARY_D3DUMP"] = True
        if "DATABASE_BINARY_INTFOR" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BINARY_INTFOR"] = True
        if "DATABASE_BINARY_INTFOR_FILE" in dynaKeyword:
            self.keywordInterpreted["DATABASE_BINARY_INTFOR_FILE"] = True
        if "DATABASE_EXTENT_BINARY" in dynaKeyword:
            self.keywordInterpreted["DATABASE_EXTENT_BINARY"] = True
        if "DATABASE_EXTENT_INTFOR" in dynaKeyword:
            self.keywordInterpreted["DATABASE_EXTENT_INTFOR"] = True                    
        if "DATABASE_NODAL_FORCE_GROUP" in dynaKeyword:
            self.keywordInterpreted["DATABASE_NODAL_FORCE_GROUP"] = True
            
        if "DATABASE_BNDOUT" in dynaKeyword:
            databaseBndoutKeyword : DatabaseBndout = dynaKeyword["DATABASE_BNDOUT"]
            database = databaseBndoutKeyword.getDatabaseBndout()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_ELOUT" in dynaKeyword:
            databaseEloutKeyword : DatabaseElout = dynaKeyword["DATABASE_ELOUT"]
            database = databaseEloutKeyword.getDatabaseElout()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_SPCFORC" in dynaKeyword:
            databaseSpcforcKeyword : DatabaseSpcforc = dynaKeyword["DATABASE_SPCFORC"]
            database = databaseSpcforcKeyword.getDatabaseSpcforc()
            self.databaseManager.SetDatabasefromDyna(database)            
        if "DATABASE_RBDOUT" in dynaKeyword:
            databaseRbdoutKeyword : DatabaseRbdout = dynaKeyword["DATABASE_RBDOUT"]
            database = databaseRbdoutKeyword.getDatabaseRbdout()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_RCFORC" in dynaKeyword:
            databaseRcforcKeyword : DatabaseRcforc = dynaKeyword["DATABASE_RCFORC"]
            database = databaseRcforcKeyword.getDatabaseRcforce()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_RWFORC" in dynaKeyword:
            databaseRwforcKeyword : DatabaseRwforc = dynaKeyword["DATABASE_RWFORC"]
            database = databaseRwforcKeyword.getDatabaseRwforc()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_NODFOR" in dynaKeyword:
            databaseNodforKeyword : DatabaseNodfor = dynaKeyword["DATABASE_NODFOR"]
            database = databaseNodforKeyword.getDatabaseNodfor()
            self.databaseManager.SetDatabasefromDyna(database)            
        if "DATABASE_NODOUT" in dynaKeyword:
            databaseNodoutKeyword : DatabaseNodout = dynaKeyword["DATABASE_NODOUT"]
            database = databaseNodoutKeyword.getDatabaseNodout()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_GLSTAT" in dynaKeyword:
            databaseGlstatKeyword : DatabaseGlstat = dynaKeyword["DATABASE_GLSTAT"]
            database = databaseGlstatKeyword.getDatabaseGlstat()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_MATSUM" in dynaKeyword:
            databaseMatsumKeyword : DatabaseMatsum = dynaKeyword["DATABASE_MATSUM"]
            database = databaseMatsumKeyword.getDatabaseMatsum()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_SLEOUT" in dynaKeyword:
            databaseSleoutKeyword : DatabaseSleout = dynaKeyword["DATABASE_SLEOUT"]
            database = databaseSleoutKeyword.getDatabaseSleout()
            self.databaseManager.SetDatabasefromDyna(database)        
        if "DATABASE_HISTORY_NODE" in dynaKeyword:
            databaseHistoryNodeKeyword : DatabaseHistoryNode = dynaKeyword["DATABASE_HISTORY_NODE"]
            database = databaseHistoryNodeKeyword.getDatabaseHistoryNode()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_BEAM" in dynaKeyword:
            databaseHistoryBeamKeyword : DatabaseHistoryBeam = dynaKeyword["DATABASE_HISTORY_BEAM"]
            database = databaseHistoryBeamKeyword.getDatabaseHistoryBeam()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_BEAM_SET" in dynaKeyword:
            databaseHistoryBeamSetKeyword : DatabaseHistoryBeamSet = dynaKeyword["DATABASE_HISTORY_BEAM_SET"]
            database = databaseHistoryBeamSetKeyword.getDatabaseHistoryBeamSet()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_SHELL" in dynaKeyword:
            databaseHistoryShellKeyword : DatabaseHistoryShell = dynaKeyword["DATABASE_HISTORY_SHELL"]
            database = databaseHistoryShellKeyword.getDatabaseHistoryShell()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_SHELL_SET" in dynaKeyword:
            databaseHistoryShellSetKeyword : DatabaseHistoryShellSet = dynaKeyword["DATABASE_HISTORY_SHELL_SET"]
            database = databaseHistoryShellSetKeyword.getDatabaseHistoryShellSet()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_SOLID" in dynaKeyword:
            databaseHistorySolidKeyword : DatabaseHistorySolid = dynaKeyword["DATABASE_HISTORY_SOLID"]
            database = databaseHistorySolidKeyword.getDatabaseHistorySolid()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_HISTORY_SOLID_SET" in dynaKeyword:
            databaseHistorySolidSetKeyword : DatabaseHistorySolidSet = dynaKeyword["DATABASE_HISTORY_SOLID_SET"]
            database = databaseHistorySolidSetKeyword.getDatabaseHistorySolidSet()
            self.databaseManager.SetDatabasefromDyna(database)            
        if "DATABASE_BINARY_D3PLOT" in dynaKeyword:
            databaseBinaryD3plotKeyword : DatabaseBinaryD3plot = dynaKeyword["DATABASE_BINARY_D3PLOT"]
            database = databaseBinaryD3plotKeyword.getDatabaseBinaryD3plot()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_BINARY_D3THDT" in dynaKeyword:
            databaseBinaryD3thdtKeyword : DatabaseBinaryD3thdt = dynaKeyword["DATABASE_BINARY_D3THDT"]
            database = databaseBinaryD3thdtKeyword.getDatabaseBinaryD3thdt()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_BINARY_D3DUMP" in dynaKeyword:
            databaseBinaryD3dumpKeyword : DatabaseBinaryD3Dump = dynaKeyword["DATABASE_BINARY_D3DUMP"]
            database = databaseBinaryD3dumpKeyword.getDatabaseBinaryD3dump()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_BINARY_INTFOR" in dynaKeyword:
            databaseBinaryIntforKeyword : DatabaseBinaryIntfor = dynaKeyword["DATABASE_BINARY_INTFOR"]
            database = databaseBinaryIntforKeyword.getDatabaseBinaryIntfor()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_BINARY_INTFOR_FILE" in dynaKeyword:
            databaseBinaryIntforFileKeyword : DatabaseBinaryIntforFile = dynaKeyword["DATABASE_BINARY_INTFOR_FILE"]
            database = databaseBinaryIntforFileKeyword.getDatabaseBinaryIntforFile()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_EXTENT_BINARY" in dynaKeyword:
            databaseExtentBinaryKeyword : DatabaseExtentBinary = dynaKeyword["DATABASE_EXTENT_BINARY"]
            database = databaseExtentBinaryKeyword.getDatabaseExtentBinary()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_EXTENT_INTFOR" in dynaKeyword:
            databaseExtentIntforKeyword : DatabaseExtentIntfor = dynaKeyword["DATABASE_EXTENT_INTFOR"]
            database = databaseExtentIntforKeyword.getDatabaseExtentIntfor()
            self.databaseManager.SetDatabasefromDyna(database)
        if "DATABASE_NODAL_FORCE_GROUP" in dynaKeyword:
            databaseNodalForceGroupKeyword : DatabaseNodalForceGroup = dynaKeyword["DATABASE_NODAL_FORCE_GROUP"]
            database = databaseNodalForceGroupKeyword.getDatabaseNodalForceGroup()
            self.databaseManager.SetDatabasefromDyna(database)
    
    def importInitial(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "INITIAL_STRESS_SOLID" in dynaKeyword:
            self.keywordInterpreted["INITIAL_STRESS_SOLID"] = True
        if "INITIAL_STRESS_SOLID_SET" in dynaKeyword:
            self.keywordInterpreted["INITIAL_STRESS_SOLID_SET"] = True
        if "INITIAL_VELOCITY_GENERATION" in dynaKeyword:
            self.keywordInterpreted["INITIAL_VELOCITY_GENERATION"] = True
        if "INITIAL_VELOCITY_NODE" in dynaKeyword:
            self.keywordInterpreted["INITIAL_VELOCITY_NODE"] = True
        if "INITIAL_VELOCITY" in dynaKeyword:
            self.keywordInterpreted["INITIAL_VELOCITY"] = True
        
        if "INITIAL_STRESS_SOLID" in dynaKeyword:
            initialStressSolidKeyword : InitialStressSolid = dynaKeyword["INITIAL_STRESS_SOLID"]
            initial = initialStressSolidKeyword.getInitialStressSolid()
            for init in initial:
                self.initialManager.AddInitialfromDyna(init)
        if "INITIAL_STRESS_SOLID_SET" in dynaKeyword:
            initialStressSolidSetKeyword : InitialStressSolidSet = dynaKeyword["INITIAL_STRESS_SOLID_SET"]
            initial = initialStressSolidSetKeyword.getInitialStressSolidSet()
            for init in initial:
                self.initialManager.AddInitialfromDyna(init)
        if "INITIAL_VELOCITY_GENERATION" in dynaKeyword:
            initialVelocityGenerationKeyword : InitialVelocityGeneration = dynaKeyword["INITIAL_VELOCITY_GENERATION"]
            initial = initialVelocityGenerationKeyword.getInitialVelocityGeneration()
            for init in initial:
                self.initialManager.AddInitialfromDyna(init)        
        if "INITIAL_VELOCITY_NODE" in dynaKeyword:
            initialVelocityNodeKeyword : InitialVelocityNode = dynaKeyword["INITIAL_VELOCITY_NODE"]
            initial = initialVelocityNodeKeyword.getInitialVelocityNode()
            for init in initial:
                self.initialManager.AddInitialfromDyna(init)
        if "INITIAL_VELOCITY" in dynaKeyword:
            initialVelocityKeyword : InitialVelocity = dynaKeyword["INITIAL_VELOCITY"]
            initial = initialVelocityKeyword.getInitialVelocity()
            for init in initial:
                self.initialManager.AddInitialfromDyna(init)
    
    def importConstrained(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "CONSTRAINED_NODE_SET" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_NODE_SET"] = True
        if "CONSTRAINED_NODE_SET_ID" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_NODE_SET_ID"] = True
        if "CONSTRAINED_NODAL_RIGID_BODY" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_NODAL_RIGID_BODY"] = True
        if "CONSTRAINED_NODAL_RIGID_BODY_TITLE" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_NODAL_RIGID_BODY_TITLE"] = True
        if "CONSTRAINED_INTERPOLATION" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_INTERPOLATION"] = True
        if "CONSTRAINED_RIGID_BODIES" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_RIGID_BODIES"] = True
        if "CONSTRAINED_RIGID_BODIES_SET" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_RIGID_BODIES_SET"] = True
        if "CONSTRAINED_EXTRA_NODES_NODE" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_EXTRA_NODES_NODE"] = True
        if "CONSTRAINED_EXTRA_NODES_SET" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_EXTRA_NODES_SET"] = True
        if "CONSTRAINED_JOINT_SPHERICAL" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_JOINT_SPHERICAL"] = True
        if "CONSTRAINED_JOINT_SPHERICAL_ID" in dynaKeyword:
            self.keywordInterpreted["CONSTRAINED_JOINT_SPHERICAL_ID"] = True
            
        if "CONSTRAINED_NODE_SET" in dynaKeyword:
            constrainedNodeSetKeyword : ConstrainedNodeSet = dynaKeyword["CONSTRAINED_NODE_SET"]
            constrained = constrainedNodeSetKeyword.getConstrainedNodeSetList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_NODE_SET_ID" in dynaKeyword:
            constrainedNodeSetIDKeyword : ConstrainedNodeSetID = dynaKeyword["CONSTRAINED_NODE_SET_ID"]
            constrained = constrainedNodeSetIDKeyword.getConstrainedNodeSetIDList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_NODAL_RIGID_BODY" in dynaKeyword:
            constrainedNodalRigidBodyKeyword : ConstrainedNodalRigidBody = dynaKeyword["CONSTRAINED_NODAL_RIGID_BODY"]
            constrained = constrainedNodalRigidBodyKeyword.getConstrainedNodalRigidBodyList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_NODAL_RIGID_BODY_TITLE" in dynaKeyword:
            constrainedNodalRigidBodyTitleKeyword : ConstrainedNodalRigidBodyTitle = dynaKeyword["CONSTRAINED_NODAL_RIGID_BODY_TITLE"]
            constrained = constrainedNodalRigidBodyTitleKeyword.getConstrainedNodalRigidBodyTitleList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)                
        if "CONSTRAINED_INTERPOLATION" in dynaKeyword:
            constrainedInterpolationKeyword : ConstrainedInterpolation = dynaKeyword["CONSTRAINED_INTERPOLATION"]
            constrained = constrainedInterpolationKeyword.getConstrainedInterpolationList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_RIGID_BODIES" in dynaKeyword:
            constrainedRigidBodiesKeyword : ConstrainedRigidBodies = dynaKeyword["CONSTRAINED_RIGID_BODIES"]
            constrained = constrainedRigidBodiesKeyword.getConstrainedRigidBodiesList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_RIGID_BODIES_SET" in dynaKeyword:
            constrainedRigidBodiesSetKeyword : ConstrainedRigidBodiesSet = dynaKeyword["CONSTRAINED_RIGID_BODIES_SET"]
            constrained = constrainedRigidBodiesSetKeyword.getConstrainedRigidBodiesSetList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_EXTRA_NODES_NODE" in dynaKeyword:
            constrainedExtraNodesNodeKeyword : ConstrainedExtraNodesNode = dynaKeyword["CONSTRAINED_EXTRA_NODES_NODE"]
            constrained = constrainedExtraNodesNodeKeyword.getConstrainedExtraNodesNodeList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_EXTRA_NODES_SET" in dynaKeyword:
            constrainedExtraNodesSetKeyword : ConstrainedExtraNodesSet = dynaKeyword["CONSTRAINED_EXTRA_NODES_SET"]
            constrained = constrainedExtraNodesSetKeyword.getConstrainedExtraNodesSetList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_JOINT_SPHERICAL" in dynaKeyword:
            constrainedJointSphericalKeyword : ConstrainedJointSpherical = dynaKeyword["CONSTRAINED_JOINT_SPHERICAL"]
            constrained = constrainedJointSphericalKeyword.getConstrainedJointSphericalList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
        if "CONSTRAINED_JOINT_SPHERICAL_ID" in dynaKeyword:
            constrainedJointSphericalIDKeyword : ConstrainedJointSphericalID = dynaKeyword["CONSTRAINED_JOINT_SPHERICAL_ID"]
            constrained = constrainedJointSphericalIDKeyword.getConstrainedJointSphericalIDList()
            for constrain in constrained:
                self.constrainedManager.SetConstrained(constrain)
    def importAdditional(self):
        dynaKeyword = self.dynaManager.dynaKeywordMan.keywords
        if "TITLE" in dynaKeyword:
            self.keywordInterpreted["TITLE"] = True
        # 단순 *RIGIDWALL_PLANAR / _ID — additionalManager로 통합 (출력 시 _MOVING_FORCES_ID 형식으로 변환됨, 의미 동일)
        if "RIGIDWALL_PLANAR" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_PLANAR"] = True
        if "RIGIDWALL_PLANAR_ID" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_PLANAR_ID"] = True
        if "RIGIDWALL_PLANAR_MOVING_FORCES" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_PLANAR_MOVING_FORCES"] = True
        if "RIGIDWALL_PLANAR_MOVING_FORCES_ID" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_PLANAR_MOVING_FORCES_ID"] = True
        if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY"] = True
        if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID" in dynaKeyword:
            self.keywordInterpreted["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"] = True
        if "HOURGLASS" in dynaKeyword:
            self.keywordInterpreted["HOURGLASS"] = True
        if "INTERFACE_SPRINGBACK_LSDYNA" in dynaKeyword:
            self.keywordInterpreted["INTERFACE_SPRINGBACK_LSDYNA"] = True

        if "TITLE" in dynaKeyword:
            titleKeyword : Title = dynaKeyword["TITLE"]
            additionals = titleKeyword.TITLE()
            self.title = additionals
            
        if "HOURGLASS" in dynaKeyword:
            hourglassKeyword : Hourglass = dynaKeyword["HOURGLASS"]
            additionals = hourglassKeyword.getHourglass()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
                
        if "RIGIDWALL_PLANAR" in dynaKeyword:
            rwPlanarKeyword : RigidWallPlanar = dynaKeyword["RIGIDWALL_PLANAR"]
            additionals = rwPlanarKeyword.getRigidWallPlanar()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)

        if "RIGIDWALL_PLANAR_ID" in dynaKeyword:
            rwPlanarIDKeyword : RigidWallPlanarID = dynaKeyword["RIGIDWALL_PLANAR_ID"]
            additionals = rwPlanarIDKeyword.getRigidWallPlanarID()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)

        if "RIGIDWALL_PLANAR_MOVING_FORCES" in dynaKeyword:
            rigidWallPlanarMovingForcesKeyword : RigidWallPlanarMovingForces = dynaKeyword["RIGIDWALL_PLANAR_MOVING_FORCES"]
            additionals = rigidWallPlanarMovingForcesKeyword.getRigidWallPlanarMovingForces()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
            
        if "RIGIDWALL_PLANAR_MOVING_FORCES_ID" in dynaKeyword:
            rigidWallPlanarMovingForcesIDKeyword : RigidWallPlanarMovingForcesID = dynaKeyword["RIGIDWALL_PLANAR_MOVING_FORCES_ID"]
            additionals = rigidWallPlanarMovingForcesIDKeyword.getRigidWallPlanarMovingForcesID()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
        
        if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY" in dynaKeyword:
            rigidWallGeometricFlatDisplayKeyword : RigidWallGeometricFlatDisplay = dynaKeyword["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY"]
            additionals = rigidWallGeometricFlatDisplayKeyword.getRigidWallGeometricFlatDisplay()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
                
        if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID" in dynaKeyword:
            rigidWallGeometricFlatDisplayIDKeyword : RigidWallGeometricFlatDisplayID = dynaKeyword["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"]
            additionals = rigidWallGeometricFlatDisplayIDKeyword.getRigidWallGeometricFlatDisplayID()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
        if "INTERFACE_SPRINGBACK_LSDYNA" in dynaKeyword:
            interfaceSpringbackKeyword : InterfaceSpringbackLSDYNA = dynaKeyword["INTERFACE_SPRINGBACK_LSDYNA"]
            additionals = interfaceSpringbackKeyword.getInterfaceSpringbackLSDYNA()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
        if "DEFORMABLE_TO_RIGID_AUTOMATIC" in dynaKeyword:
            d2rKeyword = dynaKeyword["DEFORMABLE_TO_RIGID_AUTOMATIC"]
            additionals = d2rKeyword.getDeformableToRigidAutomatic()
            for additional in additionals:
                self.additionalManager.SetAdditionalfromDyna(additional)
        pass
                    
    def importDynaResult(self):
        pass
    
    def WriteStreamAbaqusKeyword(self, partMode = False, mode = "LinearStatic"):
        stream = StringIO()
        
        if partMode == False:
            stream.write("*Heading\n")
            stream.write("KooAutomaticGenerator\n")
            stream.write("**\n")    
            stream.write("** PARTS\n")
            stream.write("**\n")
        for i in self.partManager.parts:
            part = self.partManager.parts[i]
            if part.partType == "Part":
                part : KooPart = part
            elif part.partType == "PartComposite":
                part : KooPartComposite = part                
            stream.write("*Part,NAME={name}\n".format(name=part.name))
            part.WritetoABAQUSStreamNodes(stream,0)
            part.WritetoABAQUSStreamElements(stream,0,0,self.matManager)            
        
        stream.write("*ORIENTATION,NAME=RECT1,DEFINITION=COORDINATES,SYSTEM=RECTANGULAR\n")
        stream.write("1.0,0.0,0.0,0.0,1.0,0.0\n")
        stream.write("0.0,0.0,0.0\n") 
        
        if partMode == False:
            stream.write("*End Part\n")
        
        return stream.getvalue()        
            
    def WriteStreamNastranKeyword(self, mode = "LinearStatic"):
        stream = StringIO()
        if mode == "LinearStatic":
            spcaddid = self.boundaryNodeManager.maxid + 1
            loadaddid = self.loadManager.maxid + 1
            stream.write("INIT MASTER(S)\n")
            stream.write("NASTRAN SYSTEM(442)=-1,SYSTEM(319)=1\n")
            stream.write("ID FEMAP,FEMAP\n")
            stream.write("SOL 101\n")
            stream.write("CEND\n")
            stream.write("  TITLE = KooAutomaticGenerator\n")
            stream.write("  ECHO = NONE\n")
            stream.write("  DISPLACEMENT(PLOT) = ALL\n")
            stream.write("  STRESS(PLOT,CORNER) = ALL\n")
            stream.write("  SPC = {spc}\n".format(spc=spcaddid))
            stream.write("  LOAD = {load}\n".format(load=loadaddid))
            stream.write("BEGIN BULK\n")
            stream.write("PARAM,PRGPST,NO\n")
            stream.write("PARAM,POST,-1\n")
            stream.write("PARAM,OGEOM,NO\n")
            stream.write("PARAM,AUTOSPC,YES\n")
            stream.write("PARAM,K6ROT,100.\n")
            stream.write("PARAM,GRDPNT,0\n")                            
                    
      
        self.nodeManager.WritetoNastranStream(stream,0)        
        addString = self.matManager.WritetoNastranKeyword(0)
        stream.write(addString)
        maxelemID = 0
        for i in self.partManager.parts:
            part : KooPart = self.partManager.parts[i]
            addString = part.WritetoNastranPart()
            stream.write(addString)                
            part.WritetoNastranStreamElements(stream,0,0)            
            maxelemID = max(maxelemID,part.elementManager.maxID)
        for i in self.partManager.constrainedParts:
            part = self.partManager.constrainedParts[i]
            addString = part.WritetoNastranPart(maxelemID)
            stream.write(addString)
        addString = self.boundaryNodeManager.WritetoNastranKeyword(0)
        stream.write(addString)
        addString = self.loadManager.WritetoNastranKeyword(0,loadaddid)
        stream.write(addString)
        
        ### write spcadd
        i = 1
        stream.write("SPCADD  ")
        i = i + 1
        stream.write(format(spcaddid,'>8d'))
        spcidList = self.boundaryNodeManager.boundaries.keys()
        for spcid in spcidList:
            stream.write(format(spcid,'>8d'))
            i = i + 1
            if i % 9 == 0:
                stream.write("\n")
                if i != len(spcidList)+1:
                    stream.write("        ")
        if i % 9 != 0:
            stream.write("\n")
        i = 1
    
        addString ="ENDDATA\n"
        stream.write(addString)
        
        return stream.getvalue()
    
    def WriteStreamDynaKeyword(self):
        stream = StringIO()
        if len(self.title) > 0:
            stream.write("*TITLE\n")
            stream.write(self.title)
            stream.write('\n')
        
        self.controlManager.WriteStreamDynaKeyword(stream)
        self.databaseManager.WriteStreamDynaKeyword(stream)
        self.contactManager.WriteStreamDynaKeyword(stream,0)
        self.dampingManager.WriteStreamDynaKeyword(stream,0)
        self.matManager.WriteStreamDynaKeyword(stream,0)
        self.sectionManager.WriteStreamDynaKeyword(stream)
        
        self.partManager.WriteStreamDynaKeyword(stream,0,0,0)
        self.nodeManager.WriteStreamDynaKeyword(stream,0)
        #if len(self.partManager.nodeManager.nodes) > 0:
        #    self.partManager.nodeManager.WriteStreamDynaKeyword(stream,0)
        if len(self.partManager.elementManager.elements) > 0 or len(self.partManager.elementManager.sets) > 0:
            self.partManager.elementManager.WriteStreamDynaKeyword(stream,0,0,0)
        self.nodeSetManager.WriteStreamDynaKeyword(stream,0)   
        self.segmentSetManager.WriteStreamDynaKeyword(stream,0)         
        self.defineManager.WriteStreamDynaKeyword(stream,0)  
        self.loadManager.WriteStreamDynaKeyword(stream,0)
        self.boundaryNodeManager.WriteStreamDynaKeyword(stream,0)
        self.initialManager.WriteStreamDynaKeyword(stream,0)
        self.constrainedManager.WriteStreamDynaKeyword(stream,0)
        self.additionalManager.WriteStreamDynaKeyword(stream)

        # include 처리
        # IGA passthrough: WriteModifiedFile의 WriteIGAIncludes에서 *INCLUDE 출력
        # 여기서는 preserve_includes 모드일 때만 출력
        if hasattr(self, '_include_files') and self._include_files:
            if getattr(self.dynaManager, 'preserve_includes', False):
                for inc_file in self._include_files:
                    stream.write("*INCLUDE\n")
                    stream.write(f" {os.path.basename(inc_file)}\n")
            # IGA passthrough는 WriteModifiedFile에서 처리 → 여기서 인라인하지 않음

        # 미인터프리트 키워드 raw 보존 — 매니저에 없는 키워드(SET_BEAM,
        # MAT_GENERAL_VISCOELASTIC 등)가 DropSet.k/ThermalSet.k 출력에서 유실되는 것 방지.
        # (WriteModifiedFile._write_uninterpreted_raw_blocks 와 동일 규약을 공유 writer 에도 적용)
        # 원본 슬라이스 그대로 출력 → byte-exact. 인터프리트된 키워드는 매니저가 이미 출력하므로 스킵.
        try:
            raw_dict = getattr(self.dynaManager, '_raw_keyword_dict', None)
            if raw_dict:
                interpreted = getattr(self, 'keywordInterpreted', {}) or {}
                SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END", "TITLE"}
                wrote_header = False
                for kw_name, blocks in raw_dict.items():
                    if kw_name in SKIP or interpreted.get(kw_name, False):
                        continue
                    if not wrote_header:
                        stream.write("$\n$--- Uninterpreted keywords (raw, preserved) ---\n$\n")
                        wrote_header = True
                    for block in blocks:
                        stream.write(f"*{kw_name}\n")
                        for line in block:
                            stream.write(line if line.endswith('\n') else line + '\n')
        except Exception as e:
            print(f"  Warning: uninterpreted raw 보존 실패 (skip): {e}")

        return stream.getvalue()

    def WriteStreamBaseKeyword(self, exclude_nodeset_sids=None, exclude_d2r=True):
        """베이스 모델 직렬화 (FastDOE용). nodeSetFixed와 D2R을 제외."""
        stream = StringIO()
        if len(self.title) > 0:
            stream.write("*TITLE\n")
            stream.write(self.title)
            stream.write('\n')
        self.controlManager.WriteStreamDynaKeyword(stream)
        self.databaseManager.WriteStreamDynaKeyword(stream)
        self.contactManager.WriteStreamDynaKeyword(stream, 0)
        self.dampingManager.WriteStreamDynaKeyword(stream, 0)
        self.matManager.WriteStreamDynaKeyword(stream, 0)
        self.sectionManager.WriteStreamDynaKeyword(stream)
        self.partManager.WriteStreamDynaKeyword(stream, 0, 0, 0)
        self.nodeManager.WriteStreamDynaKeyword(stream, 0)
        if len(self.partManager.elementManager.elements) > 0 or len(self.partManager.elementManager.sets) > 0:
            self.partManager.elementManager.WriteStreamDynaKeyword(stream, 0, 0, 0)
        # nodeSetManager — exclude specified SIDs
        if exclude_nodeset_sids:
            for key in self.nodeSetManager.nodeSets:
                if key not in exclude_nodeset_sids:
                    self.nodeSetManager.nodeSets[key].WriteStreamDynaKeyword(stream, 0)
        else:
            self.nodeSetManager.WriteStreamDynaKeyword(stream, 0)
        self.segmentSetManager.WriteStreamDynaKeyword(stream, 0)
        self.defineManager.WriteStreamDynaKeyword(stream, 0)
        self.loadManager.WriteStreamDynaKeyword(stream, 0)
        self.boundaryNodeManager.WriteStreamDynaKeyword(stream, 0)
        self.initialManager.WriteStreamDynaKeyword(stream, 0)
        self.constrainedManager.WriteStreamDynaKeyword(stream, 0)
        # additionalManager — exclude D2R if requested
        if exclude_d2r:
            for key in self.additionalManager.rigidwalls:
                self.additionalManager.rigidwalls[key].WriteStreamDynaKeyword(stream)
            for key in self.additionalManager.hourglasses:
                self.additionalManager.hourglasses[key].WriteStreamDynaKeyword(stream)
            for key in self.additionalManager.interfaces:
                self.additionalManager.interfaces[key].WriteStreamDynaKeyword(stream)
        else:
            self.additionalManager.WriteStreamDynaKeyword(stream)
        return stream.getvalue()

    def WriteStreamDeltaKeyword(self, base_state):
        """delta만 직렬화 (FastDOE용). base 이후 추가된 항목만."""
        stream = StringIO()
        # 1a. 새 파트 (base에 없던 PID)
        for pid in self.partManager.parts:
            if pid not in base_state["part_ids"]:
                part = self.partManager.parts[pid]
                part.WriteStreamDynaPart(stream, 0)
                if len(part.elementManager.elements) > 0:
                    part.WriteStreamDynaElements(stream, 0, 0)
        # 1b. 재사용 파트의 새 요소 (base에 있지만 DOE마다 요소 재생성)
        for pid in base_state.get("reusable_part_ids", set()):
            if pid in self.partManager.parts:
                part = self.partManager.parts[pid]
                if len(part.elementManager.elements) > 0:
                    part.WriteStreamDynaElements(stream, 0, 0)
        # 2. 새 노드 (ID > base max_nid)
        self.nodeManager.WriteStreamDeltaNodes(stream, base_state["max_nid"])
        # 3. 새 접촉
        for cid in self.contactManager.contacts:
            if cid not in base_state["contact_keys"]:
                self.contactManager.contacts[cid].WriteStreamDynaKeyword(stream, 0)
        # 4. 새 초기조건
        for iid in self.initialManager.inits:
            if iid not in base_state["initial_keys"]:
                self.initialManager.inits[iid].WriteStreamDynaKeyword(stream, 0)
        # 5. 제외했던 nodeSet (nodeSetFixed 등)
        for nsid in base_state.get("excluded_nodeset_sids", set()):
            if nsid in self.nodeSetManager.nodeSets:
                self.nodeSetManager.nodeSets[nsid].WriteStreamDynaKeyword(stream, 0)
        # 6. D2R automatics
        for key in self.additionalManager.d2r_automatics:
            self.additionalManager.d2r_automatics[key].WriteStreamDynaKeyword(stream)
        return stream.getvalue()

    def WriteStreamPreNodesKeyword(self):
        """노드 섹션 이전까지 직렬화 (섹션 1-7): TITLE~partManager (Group C FastDOE용)"""
        stream = StringIO()
        if len(self.title) > 0:
            stream.write("*TITLE\n")
            stream.write(self.title)
            stream.write('\n')
        self.controlManager.WriteStreamDynaKeyword(stream)
        self.databaseManager.WriteStreamDynaKeyword(stream)
        self.contactManager.WriteStreamDynaKeyword(stream, 0)
        self.dampingManager.WriteStreamDynaKeyword(stream, 0)
        self.matManager.WriteStreamDynaKeyword(stream, 0)
        self.sectionManager.WriteStreamDynaKeyword(stream)
        self.partManager.WriteStreamDynaKeyword(stream, 0, 0, 0)
        return stream.getvalue()

    def WriteStreamPostNodesKeyword(self):
        """노드 섹션 이후 직렬화 (섹션 9-17): elementManager~additional (Group C FastDOE용)"""
        stream = StringIO()
        if len(self.partManager.elementManager.elements) > 0 or len(self.partManager.elementManager.sets) > 0:
            self.partManager.elementManager.WriteStreamDynaKeyword(stream, 0, 0, 0)
        self.nodeSetManager.WriteStreamDynaKeyword(stream, 0)
        self.segmentSetManager.WriteStreamDynaKeyword(stream, 0)
        self.defineManager.WriteStreamDynaKeyword(stream, 0)
        self.loadManager.WriteStreamDynaKeyword(stream, 0)
        self.boundaryNodeManager.WriteStreamDynaKeyword(stream, 0)
        self.initialManager.WriteStreamDynaKeyword(stream, 0)
        self.constrainedManager.WriteStreamDynaKeyword(stream, 0)
        self.additionalManager.WriteStreamDynaKeyword(stream)
        return stream.getvalue()

    def ExportDynaString(self):
        keyword = ""      
        if len(self.title) > 0:
            keyword += "*TITLE\n"
            keyword += self.title
            keyword += '\n'
        keyword += self.controlManager.GenerateDynaKeyword()
        keyword += self.databaseManager.GenerateDynaKeyword()
        keyword += self.contactManager.WritetoDynaKeyword(0)
        keyword += self.dampingManager.GenerateDynaKeyword(0)
        keyword += self.matManager.WritetoDynaKeyword(0) 
        keyword += self.sectionManager.WritetoDynaKeyword(0)        
        '''for i in self.partManager.parts:
            curPart : KooPart = self.partManager.parts[i]
            keyword += curPart.WritetoDynaPart()
            keyword += curPart.WritetoDynaElements(0,0)
        '''
        keyword += self.partManager.WritetoDynaKeyword(0,0,0)
        keyword += self.nodeManager.WritetoDynaKeyword(0)
        if len(self.partManager.nodeManager.nodes) > 0:
            keyword += self.partManager.nodeManager.WritetoDynaKeyword(0)
        if len(self.partManager.elementManager.elements) > 0 or len(self.partManager.elementManager.sets) > 0:
            keyword += self.partManager.elementManager.WritetoDynaKeyword(0,0,0)
        
        keyword += self.nodeSetManager.WritetoDynaKeyword(0)
        keyword += self.segmentSetManager.WritetoDynaKeyword(0)
        keyword += self.defineManager.WritetoDynaKeyword(0)
        keyword += self.loadManager.WritetoDynaKeyword(0)
        keyword += self.boundaryNodeManager.WritetoDynaKeyword(0)
        keyword += self.initialManager.WritetoDynaKeyword(0)
        keyword += self.additionalManager.WritetoDynaKeyword()
        
        return keyword
   
    def parse_whole(self, curString, chunkList):
        chunk_size = len(chunkList)
        chunks = []

        start = 0
        for i in range(0,chunk_size):
            end = start + chunkList[i]
            chunks.append(curString[start:end])            
            start = end

        for i in range(0,chunk_size):
            if '\n' in chunks[i]:
                chunks[i] = chunks[i].replace('\n','')
            
        return chunks  
    
    def importD3plotDisp(self, filePath):
        pass
        '''try: 
            plot_File = D3plot(filePath)
        except RuntimeError as e:
            print(e)
            return  
        num_step = plot_File.num_time_steps()
        print("Total time step : ",num_step)
        for j in range(1,num_step):
            time = plot_File.read_time(j)
            self.nodeManager.AddTime(time)
        node_ids = plot_File.read_node_ids()
        nnode = len(node_ids)        
        for i in range(0,nnode):
            node_id = node_ids[i] 
            node : Node = self.nodeManager.FindNodefromID(node_id)
            if node is not None:
                node.SetTimeSize(num_step)
        
        node_coords_list = []
        for j in range(1,num_step):
            node_coords = plot_File.read_node_coordinates(j)
            node_coords_list.append(node_coords)
        # 노드 수와 스텝 수를 미리 변수에 저장
        num_nodes = len(node_ids)
        num_steps = len(node_coords_list)

        for i in range(num_nodes):
            node_id = node_ids[i]
            node = self.nodeManager.FindNodefromID(node_id)
            x0, y0, z0 = node_coords_list[0][i]

            if node is not None:
                # 변위를 미리 계산해둡니다.
                initial_coords = node_coords_list[0][i]
                for j in range(1, num_steps):
                    # 변위를 계산합니다.
                    current_coords = node_coords_list[j - 1][i]
                    dx, dy, dz = [current_coords[k] - initial_coords[k] for k in range(3)]

                    node.SetDisplacement(j - 1, dx, dy, dz)

            if i % 1000 == 0:
                print("Node ID : ", node_id, " is done")'''
    
    def importD3plotStress(self, filePath):
        pass
    
        '''try:
            plot_File = D3plot(filePath)
        except RuntimeError as e:
            print(e)
            return
        
        num_step = plot_File.num_time_steps()
        print("Total time step : ",num_step)
        
        part_ids = plot_File.read_part_ids()   
        
        for j in range(1,num_step):
            time = plot_File.read_time(j)
            for partID in self.partManager.parts:
                curPart : KooPart = self.partManager.parts[partID]
                curPart.elementManager.AddTime(time)
     
        beam_elements_ids = plot_File.read_beam_element_ids()
        shell_elements_ids = plot_File.read_shell_element_ids()
        solid_elements_ids = plot_File.read_solid_element_ids()
        # preallocate size
        beam_elements_ids_to_index = {beam_elements_ids[i]: i for i in range(len(beam_elements_ids))}
        shell_elements_ids_to_index = {shell_elements_ids[i]: i for i in range(len(shell_elements_ids))}
        solid_elements_ids_to_index = {solid_elements_ids[i]: i for i in range(len(solid_elements_ids))}
             
        
        
        beam_state_list = [] 
        shell_state_list = []
        solid_state_list = [] 
        
        for j in range(1,num_step):
            beam_state_list.append(plot_File.read_beams_state(j))
            shell_state_list.append(plot_File.read_shells_state(j)) 
            solid_state_list.append(plot_File.read_solids_state(j))
        
        i = 0
        for part_id in part_ids:
            part : KooPart= self.partManager.parts[part_id]
            part.elementManager.SetTimeSize() 
            part_dyna = plot_File.read_part(i)
            # element id in part
            element_ids = part_dyna.get_all_element_ids()
            ith = 0                 
            if part.GetPartDimension() == 1:
                
                for element_id in element_ids:
                    bindex = beam_elements_ids_to_index[element_id]
                    for j in range(1, num_step):
                        state = beam_state_list[j-1][bindex]
                        
                        element : LineElement = part.elementManager.elements[element_id]
                        bending_moment = state.bending_moment
                        shear_force = state.shear_force
                        element.AddResultant(0,shear_force[0],shear_force[1],bending_moment[0],bending_moment[1],0)
                    ith = ith + 1
                    if ith % 1000 == 0:
                        print("Beam Element ID : ",element_id, " is done")     
                    
            elif part.GetPartDimension() == 2:
                for element_id in element_ids:
                    sindex = shell_elements_ids_to_index[element_id]
                    element : FaceElement = part.elementManager.elements[element_id]
                    for j in range(1, num_step):
                        state = shell_state_list[j-1][sindex]      
                        ins = state.inner.stress
                        inps = state.inner.effective_plastic_strain
                        outs = state.outer.stress
                        outps = state.outer.effective_plastic_strain  
                        mids = state.mid.stress
                        midps = state.mid.effective_plastic_strain
                        
                        element.SetStressTensorandPlasticStrain(0,j-1,ins.x,ins.y,ins.z,ins.xy,ins.yz,ins.zx,inps)
                        element.SetStressTensorandPlasticStrain(1,j-1,outs.x,outs.y,outs.z,outs.xy,outs.yz,outs.zx,outps)
                        element.SetStressTensorandPlasticStrain(2,j-1,mids.x,mids.y,mids.z,mids.xy,mids.yz,mids.zx,midps)
                    ith = ith + 1
                    if ith % 1000 == 0:
                        print("Shell Element ID : ",element_id, " is done")    
            elif part.GetPartDimension() == 3:
                for element_id in element_ids:
                    solidindex = solid_elements_ids_to_index[element_id]
                    element : SolidElement = part.elementManager.elements[element_id]
                    for j in range(1, num_step):
                        state = solid_state_list[j-1][solidindex]
                        stress = state.stress
                        eps = state.effective_plastic_strain
                        element.SetStressTensorandPlasticStrain(0,j-1,stress.x,stress.y,stress.z,stress.xy,stress.yz,stress.zx,eps)
                    ith = ith + 1
                    if ith % 1000 == 0:
                        print("Solid Element ID : ",element_id, " is done")         
            print("Part ID : ",part_id, " is done")
            i = i + 1'''
             
    def importNODOUT(self, filePath):
        #timeStep = -1
        current_time = 0.0
        
        with open(filePath, 'r') as file:
            line = file.readline()
            while line:
                line = line.replace('\n','')               
                # Define regular expressions
                #time_step_pattern = r"t i m e  s t e p       (\d+)"
                current_time_pattern = r"at time (\d+\.\d+E[+-]\d+)"
                # Extract time step and current time
                #time_step_match = re.search(time_step_pattern, line)
                current_time_match = re.search(current_time_pattern, line)
                if "END LEGEND" in line:
                    line = file.readline()
                elif current_time_match:
                    #timeStep = int(time_step_match.group(1))
                    current_time = float(current_time_match.group(1))
                    self.nodeManager.AddTime(current_time)
                    line = file.readline()
                    line = file.readline()
                    if "rot" in line:
                        line = file.readline()
                        while len(line)>0:
                            line = line.replace('\n','')
                            if len(line) == 0:
                                break
                            parameters = self.parse_whole(line, [10, 12, 12, 12, 12, 12, 12, 12, 12, 12])
                            id = int(parameters[0])
                            rotX = float(parameters[1])
                            rotY = float(parameters[2])
                            rotZ = float(parameters[3])
                            rotVelX = float(parameters[4])
                            rotVelY = float(parameters[5])
                            rotVelZ = float(parameters[6])
                            rotAccX = float(parameters[7])
                            rotAccY = float(parameters[8])
                            rotAccZ = float(parameters[9])
                            node : Node = self.nodeManager.FindNodefromID(id)
                            if node is not None:                                
                                node.AddRotation(rotX,rotY,rotZ)
                                node.AddRotationVelocity(rotVelX,rotVelY,rotVelZ)
                                node.AddRotationAcceleration(rotAccX,rotAccY,rotAccZ)
                            line = file.readline()
                            
                    else:
                        line = file.readline()
                        while len(line)>0:
                            line = line.replace('\n','')
                            if len(line) == 0:
                                break
                            # 12 {str(element):>12 and 1 {str(element):>10}
                            
                            parameters = self.parse_whole(line, [10, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
                            id = int(parameters[0])
                            dispX = float(parameters[1])
                            dispY = float(parameters[2])
                            dispZ = float(parameters[3])
                            velX = float(parameters[4])
                            velY = float(parameters[5])
                            velZ = float(parameters[6])
                            accX = float(parameters[7])
                            accY = float(parameters[8])
                            accZ = float(parameters[9])
                            coordX = float(parameters[10])
                            coordY = float(parameters[11])
                            coordZ = float(parameters[12])

                            node : Node = self.nodeManager.FindNodefromID(id)
                            if node is not None:                                
                                node.AddDisplacement(dispX,dispY,dispZ)
                                node.AddVelocity(velX,velY,velZ)
                                node.AddAcceleration(accX,accY,accZ)
                                node.AddCoordinate(coordX,coordY,coordZ)                                
                            
                                                                   
                            line = file.readline()
                    line = file.readline()





                else:
                    line = file.readline()


                
        pass

    def importELOUT(self, filePath):
        current_time = 0.0 
        elementid = -1
        with open(filePath, 'r') as file:
            line = file.readline()
            while line:
                line = line.replace('\n','')
                # Define regular expressions
                current_time_pattern = r"at time (\d+\.\d+E[+-]\d+)"
                # Extract time step and current time
                current_time_match = re.search(current_time_pattern, line)
                if current_time_match and "e l e m e n t   s t r e s s" in line:
                    #timeStep = int(time_step_match.group(1))
                    current_time = float(current_time_match.group(1))
                    for i in range(0,5):
                        line = file.readline()
                    while len(line)>0:
                        line = line.replace('\n','')                        
                        length = len(line)
                        if length == 0:
                            break
                        elif length == 16:
                            parameters = self.parse_whole(line, [8,1,7])
                            elementid = int(parameters[0])
                        elif length == 117:
                            parameters = self.parse_whole(line, [8,9,12,12,12,12,12,12,14,14])                          
                            ipt = int(parameters[0])                            
                            sigXX = float(parameters[2])
                            sigYY = float(parameters[3])
                            sigZZ = float(parameters[4])
                            sigXY = float(parameters[5])
                            sigYZ = float(parameters[6])
                            sigXZ = float(parameters[7])
                            sigVM = float(parameters[8])
                            yieldFunction = float(parameters[9])
                            element = self.partManager.FindElementfromID(elementid)
                            element.AddStressTensorandVonMisesandYieldFunction(ipt,sigXX,sigYY,sigZZ,sigXY,sigYZ,sigXZ,sigVM,yieldFunction)
                        else:
                            parameters = self.parse_whole(line, [4,1,4,8,12, 12, 12,12, 12, 12,14])                          
                            ipt = int(parameters[0])
                            shl = int(parameters[2])
                            sigXX = float(parameters[4])
                            sigYY = float(parameters[5])
                            sigZZ = float(parameters[6])
                            sigXY = float(parameters[7])
                            sigYZ = float(parameters[8])
                            sigXZ = float(parameters[9])
                            plasticStrain = float(parameters[10])
                            element = self.partManager.FindElementfromID(elementid)
                            element.AddStressTensorandPlasticStrain(ipt,sigXX,sigYY,sigZZ,sigXY,sigYZ,sigXZ,plasticStrain)
                        line = file.readline()                        
                elif current_time_match and " r e s u l t a n t s   a n d   s t r e s s e s" in line:
                    current_time = float(current_time_match.group(1))
                    line = file.readline()
                    while len(line)>0:
                        if len(line) == 0:
                            break
                        line = line.replace('\n','')
                        if 'at time' in line:
                            break
                        elif 'beam' in line:
                            parameters = self.parse_whole(line, [15,8,16,10,20,8])
                            elementid = int(parameters[1])
                            partid = int(parameters[3])
                            materialid = int(parameters[5])
                        elif 'resultants' in line:
                            line = file.readline()
                            parameters = self.parse_whole(line, [11, 11, 11, 11, 11, 11, 11, 11])
                            axial = float(parameters[1])
                            shear_s = float(parameters[2])
                            shear_t = float(parameters[3])
                            moment_s = float(parameters[4])
                            moment_t = float(parameters[5])
                            torsion = float(parameters[6])
                            pleps = float(parameters[7])
                            element = self.partManager.FindElementfromID(elementid)
                            element.AddResultant(axial,shear_s,shear_t,moment_s,moment_t,torsion,pleps)
                        line = file.readline()
                    continue
                    
                    # beam element 처리하기 

                line = file.readline()                        
        pass

    def importBNDOUT(self, filePath):
        current_time = 0.0
        with open(filePath, 'r') as file:
            line = file.readline()
            while line:
                line = line.replace('\n','')
                # Define regular expressions
                current_time_pattern = r"t=   (\d+\.\d+E[+-]\d+)"
                current_time_match = re.search(current_time_pattern, line)
                if current_time_match:
                    current_time = float(current_time_match.group(1))
                    line = file.readline()
                    line = file.readline()
                    line = file.readline()
                    line = file.readline()
                    xforce = 0 
                    yforce = 0
                    zforce = 0
                    energy = 0
                    setid = 0
                    xmoment = 0 
                    ymoment = 0
                    zmoment = 0
                    while len(line)>0:
                        if "mat#" in line:
                            parameters = self.parse_whole(line, [4,8,10,12,11,12,10,12,11,12,10,8])
                            xforce = float(parameters[3])
                            yforce = float(parameters[5])
                            zforce = float(parameters[7])
                            energy = float(parameters[9])
                            setid = int(parameters[11])
                        elif "xmoment" in line:
                            parameters = self.parse_whole(line, [4,8,10,12,11,12,10,12])
                            xmoment = float(parameters[3])
                            ymoment = float(parameters[5])
                            zmoment = float(parameters[7])
                        elif "xtotal" in line:
                            self.resultManager.AddBndoutResult(setid,current_time,xforce,yforce,zforce,xmoment,ymoment,zmoment,energy)
                            pass
                        elif re.search(current_time_pattern, line):
                            break
                        line = file.readline()
                    continue

                
                line = file.readline()


    def importNODFOR(self, filePath):
        current_time = 0.0 
        groupid = -1
        with open(filePath, 'r') as file:
            line = file.readline()
            
            while line:
                line = line.replace('\n','')
                # Define regular expressions
                current_time_pattern = r"t=   (\d+\.\d+E[+-]\d+)"
                current_time_match = re.search(current_time_pattern, line)
                if current_time_match:
                    current_time = float(current_time_match.group(1))
                    line = file.readline()
                    line = file.readline()
                    group_id_pattern = r"number  (\d+)"
                    group_id_match = re.search(group_id_pattern, line)
                    
                    if group_id_match:
                        groupid = int(group_id_match.group(1))
                        line = file.readline()
                        line = file.readline()
                        while len(line)>0:
                            if "xtotal" in line:
                                pass
                            elif "t=" in line:
                                break
                            elif "nodal" in line:
                                #file 1 from  line="nodal group output number  1"
                                groupid = int(line.split()[-1])                                
                            elif "nd#" in line:
                                parameters = self.parse_whole(line, [4,8,10,12,11,12,10,12,11,12,10,8])
                                nid = int(parameters[1])
                                xForce = float(parameters[3])
                                yForce = float(parameters[5])
                                zForce = float(parameters[7])
                                energy = float(parameters[9])
                                setid = int(parameters[11])
                                node = self.nodeManager.FindNodefromID(nid)
                                if node is not None:
                                    nodeResult = self.resultManager.AddNodforResult(nid,current_time,xForce,yForce,zForce,energy)
                                    self.resultManager.AddNodeResultinGroup(groupid,nid,nodeResult)

                            line = file.readline()

                            
                        continue
                line = file.readline()

        pass

    def writeDynaFile(self, filePath,controlKeywords="", contactKeywords="", initialKeywords="", setKeywords="",rigidKeywords="",boundaryKeywords="",interfaceKeywords="",defineKeywords="",sectionKeywords="",materialKeywords="",loadKeywords="",meshKeywords=""):
        self.dynaManager.WriteOutputFile(filePath,controlKeywords, contactKeywords, initialKeywords, setKeywords, rigidKeywords, boundaryKeywords, interfaceKeywords, defineKeywords, sectionKeywords, materialKeywords, loadKeywords, meshKeywords)

    def FindBoundBox(self):
        minx = 1e10
        miny = 1e10
        minz = 1e10
        maxx = -1e10
        maxy = -1e10
        maxz = -1e10
        for nid in self.nodeManager.nodes:
            curNode = self.nodeManager.nodes[nid]
            if curNode.x < minx:
                minx = curNode.x
            if curNode.y < miny:
                miny = curNode.y
            if curNode.z < minz:
                minz = curNode.z
            if curNode.x > maxx:
                maxx = curNode.x
            if curNode.y > maxy:
                maxy = curNode.y
            if curNode.z > maxz:
                maxz = curNode.z
        return minx,miny,minz,maxx,maxy,maxz
    
    def RemovePartbyName(self, name, removeContact = True):
        remIDList = []
        for pid, part in self.partManager.parts.items():
            if name in part.name:
                remIDList.append(pid)
                
        for pid in remIDList:
            self.RemovePart(pid, removeContact)
        
    
    def RemovePart(self, pid, removeContact = True):
        if pid in self.partManager.parts:
            part : KooPart = self.partManager.parts[pid]
            nodes = part.elementManager.GetElementNodes()
            #elementIDs = part.elementManager.elements.keys()
            part.elementManager.RemoveAllElements()
            part.nodeManager.RemoveNodesExceptNodes(nodes)
            delnsidList = self.nodeSetManager.RemoveNodesExceptNodes(nodes)
            
            self.boundaryNodeManager.RemoveBoundaryfromNodeSetIDList(delnsidList)
            
            if removeContact == True:
                self.contactManager.RemoveContactbyPartID(pid)
            self.partManager.RemovePart(pid)
            
                
            
            
    

class KooMSHImporter():
    def __init__(self,nodeManager = None, elementManager = None):
        self.mshNodes = None
        self.mshElements = None
        self.nodeManager : NodeManager = nodeManager
        self.elementManager : ElementManager = elementManager
        pass

    def SetUpdateManager(self, nodeManager, elementManager):
        self.nodeManager = nodeManager
        self.elementManager = elementManager        

    def parse_mesh_format(self, lines):
        """
        Parse the MeshFormat section of the MSH file.

        :param lines: List of lines in the MeshFormat section.
        :return: Dictionary containing the version, file type, and data size.
        """

        # Initialize an empty dictionary to store the mesh format data
        mesh_format = {}

        # The first line should contain version, file type, and data size
        if len(lines) > 0:
            parts = lines[0].split()
            if len(parts) >= 3:
                mesh_format['version'] = float(parts[0])  # Convert version to float
                mesh_format['file_type'] = int(parts[1])  # Convert file type to int
                mesh_format['data_size'] = int(parts[2])  # Convert data size to int

        # Check for optional int value in binary mode
        if mesh_format.get('file_type') == 1 and len(lines) > 1:
            # In binary mode, the second line contains an int for endianness detection
            mesh_format['endianness'] = int(lines[1])

        return mesh_format

    def parse_physical_names(self, lines):
        """
        Parse the PhysicalNames section of the MSH file.

        :param lines: List of lines in the PhysicalNames section.
        :return: List of dictionaries, each containing dimension, physical tag, and name.
        """
        physical_names = []

        if len(lines) > 0:
            # The first line is the number of physical names
            num_physical_names = int(lines[0])

            for line in lines[1:num_physical_names + 1]:
                parts = line.split()
                if len(parts) >= 3:
                    # Extract dimension and physical tag, and strip quotes from the name
                    dimension = int(parts[0])
                    physical_tag = int(parts[1])
                    name = ' '.join(parts[2:]).strip('"')

                    physical_names.append({
                        'dimension': dimension,
                        'physical_tag': physical_tag,
                        'name': name
                    })

        return physical_names


    def parse_entities(self, lines):
        """
        Parse the Entities section of the MSH file.

        :param lines: List of lines in the Entities section.
        :return: Dictionary containing the parsed entities data.
        """
        entities = {
            'points': [],
            'curves': [],
            'surfaces': [],
            'volumes': []
        }

        if len(lines) > 0:
            # First line contains the count of different entities
            numPoints, numCurves, numSurfaces, numVolumes = map(int, lines[0].split())

            current_line = 1

            # Parse points
            for _ in range(numPoints):
                point_data = lines[current_line].split()
                point_tag = int(point_data[0])
                coordinates = tuple(map(float, point_data[1:4]))
                num_physical_tags = int(point_data[4])
                physical_tags = list(map(int, point_data[5:5+num_physical_tags]))
                entities['points'].append({
                    'point_tag': point_tag,
                    'coordinates': coordinates,
                    'physical_tags': physical_tags
                })
                current_line += 1

            # Parse curves
            for _ in range(numCurves):
                curve_data = lines[current_line].split()
                curve_tag = int(curve_data[0])
                min_coords = tuple(map(float, curve_data[1:4]))
                max_coords = tuple(map(float, curve_data[4:7]))
                num_physical_tags = int(curve_data[7])
                physical_tags = list(map(int, curve_data[8:8+num_physical_tags]))
                numBoundingPoints = int(curve_data[8+num_physical_tags])
                bounding_points = list(map(int, curve_data[9+num_physical_tags:9+num_physical_tags+numBoundingPoints]))
                entities['curves'].append({
                    'curve_tag': curve_tag,
                    'min_coords': min_coords,
                    'max_coords': max_coords,
                    'physical_tags': physical_tags,
                    'bounding_points': bounding_points
                })
                current_line += 1

            # Parse surfaces
            for _ in range(numSurfaces):
                surface_data = lines[current_line].split()
                surface_tag = int(surface_data[0])
                min_coords = tuple(map(float, surface_data[1:4]))
                max_coords = tuple(map(float, surface_data[4:7]))
                num_physical_tags = int(surface_data[7])
                physical_tags = list(map(int, surface_data[8:8+num_physical_tags]))
                numBoundingCurves = int(surface_data[8+num_physical_tags])
                bounding_curves = list(map(int, surface_data[9+num_physical_tags:9+num_physical_tags+numBoundingCurves]))
                entities['surfaces'].append({
                    'surface_tag': surface_tag,
                    'min_coords': min_coords,
                    'max_coords': max_coords,
                    'physical_tags': physical_tags,
                    'bounding_curves': bounding_curves
                })
                current_line += 1

            # Parse volumes
            for _ in range(numVolumes):
                volume_data = lines[current_line].split()
                volume_tag = int(volume_data[0])
                min_coords = tuple(map(float, volume_data[1:4]))
                max_coords = tuple(map(float, volume_data[4:7]))
                num_physical_tags = int(volume_data[7])
                physical_tags = list(map(int, volume_data[8:8+num_physical_tags]))
                numBoundingSurfaces = int(volume_data[8+num_physical_tags])
                bounding_surfaces = list(map(int, volume_data[9+num_physical_tags:9+num_physical_tags+numBoundingSurfaces]))
                entities['volumes'].append({
                    'volume_tag': volume_tag,
                    'min_coords': min_coords,
                    'max_coords': max_coords,
                    'physical_tags': physical_tags,
                    'bounding_surfaces': bounding_surfaces
                })
                current_line += 1

        return entities

    def parse_partitioned_entities(self, lines):
        # Parse the PartitionedEntities section
        # ...
        pass

    def parse_nodes(self, lines):
        """
        Parse the Nodes section of the MSH file.

        :param lines: List of lines in the Nodes section.
        :return: Dictionary containing the nodes data.
        """
        nodes = {
            'numEntityBlocks': None,
            'numNodes': None,
            'minNodeTag': None,
            'maxNodeTag': None,
            'entities': []
        }

        if len(lines) > 0:
            # Parse the first line for overall nodes information
            numEntityBlocks, numNodes, minNodeTag, maxNodeTag = map(int, lines[0].split())
            nodes['numEntityBlocks'] = numEntityBlocks
            nodes['numNodes'] = numNodes
            nodes['minNodeTag'] = minNodeTag
            nodes['maxNodeTag'] = maxNodeTag

            current_line = 1

            # Iterate over each entity block
            for _ in range(numEntityBlocks):
                # Parse entity block information
                entity_info = lines[current_line].split()
                entityDim, entityTag, parametric, numNodesInBlock = map(int, entity_info[:4])
                current_line += 1
                if numNodesInBlock == 0:
                    continue

                # Parse node tags
                node_tags = []
                for j in range(numNodesInBlock):
                    node_tags.append(int(lines[current_line]))

                    current_line += 1

                # Parse node coordinates
                node_coordinates = []
                for _ in range(numNodesInBlock):
                    coords = list(map(float, lines[current_line].split()))
                    node_coordinates.append(tuple(coords))
                    current_line += 1

                # Store the entity information
                nodes['entities'].append({
                    'entityDim': entityDim,
                    'entityTag': entityTag,
                    'parametric': parametric,
                    'node_tags': node_tags,
                    'coordinates': node_coordinates
                })

        return nodes
    
    def parse_elements(self, lines):
        """
        Parse the Elements section of the MSH file.

        :param lines: List of lines in the Elements section.
        :return: Dictionary containing the elements data.
        """
        elements = {
            'numEntityBlocks': None,
            'numElements': None,
            'minElementTag': None,
            'maxElementTag': None,
            'entities': []
        }

        if len(lines) > 0:
            # Parse the first line for overall elements information
            numEntityBlocks, numElements, minElementTag, maxElementTag = map(int, lines[0].split())
            elements['numEntityBlocks'] = numEntityBlocks
            elements['numElements'] = numElements
            elements['minElementTag'] = minElementTag
            elements['maxElementTag'] = maxElementTag

            current_line = 1

            # Iterate over each entity block
            for _ in range(numEntityBlocks):
                # Parse entity block information
                entity_info = lines[current_line].split()
                entityDim, entityTag, elementType, numElementsInBlock = map(int, entity_info[:4])
                current_line += 1

                # Iterate over each element in the block
                element_list = []
                for _ in range(numElementsInBlock):
                    element_info = list(map(int, lines[current_line].split()))
                    elementTag = element_info[0]
                    nodeTags = element_info[1:]
                    element_list.append({'elementTag': elementTag, 'nodeTags': nodeTags})
                    current_line += 1

                # Store the entity information
                elements['entities'].append({
                    'entityDim': entityDim,
                    'entityTag': entityTag,
                    'elementType': elementType,
                    'elements': element_list
                })

        return elements
    def parse_periodic(self, lines):
        # Parse the Periodic section
        # ...
        pass

    def parse_ghost_elements(self, lines):
        # Parse the GhostElements section
        # ...
        pass

    def parse_parametrizations(self, lines):
        # Parse the Parametrizations section
        # ...
        pass

    def parse_node_data(self, lines):
        # Parse the NodeData section
        # ...
        pass

    def parse_element_data(self, lines):
        # Parse the ElementData section
        # ...
        pass

    def parse_element_node_data(self, lines):
        # Parse the ElementNodeData section
        # ...
        pass

    def parse_interpolation_scheme(self, lines):
        # Parse the InterpolationScheme section
        # ...
        pass

    def import_msh_file(self, filename):
        with open(filename, 'r') as file:
            lines = file.readlines()

        # Iterate through the lines and identify sections
        current_section = None
        section_lines = []

        print("Import MSH file")
        mshNodes = None
        mshElements = None
        for line in lines:
            line = line.strip()
            if line.startswith('$'):
                if current_section is not None:
                    # Process the current section
                    if current_section == '$MeshFormat':
                        self.parse_mesh_format(section_lines)
                    elif current_section == '$PhysicalNames':
                        self.parse_physical_names(section_lines)
                    elif current_section == '$Entities':
                        self.parse_entities(section_lines)
                    elif current_section == "$Nodes":
                        mshNodes = self.parse_nodes(section_lines)
                    elif current_section == "$Elements":
                        mshElements = self.parse_elements(section_lines)
                    # Add other sections here
                    # ...

                if 'End' in line:
                    current_section = None
                    section_lines = []
                else:
                    current_section = line
            elif current_section is not None:
                section_lines.append(line)
        self.mshNodes = mshNodes
        self.mshElements = mshElements
        print("Import MSH file done")

    def UpdateManager(self, maxNID = 0, maxEID = 0,dim = -1):
        if maxNID == 0:
            maxNID = self.nodeManager.maxID
        elif maxNID < self.nodeManager.maxID:
            maxNID = self.nodeManager.maxID + maxNID
        if maxEID == 0:
            maxEID = self.elementManager.maxID
        elif maxEID < self.elementManager.maxID:
            maxEID = self.elementManager.maxID + maxEID
        print("Update NodeManager...")
        if self.mshNodes is not None:
            self.nodeManager.AddNodesfromMSH(self.mshNodes,maxNID)
        print("Update ElementManager...")
        if self.mshElements is not None:
            self.elementManager.AddElementsfromMSH(self.mshElements,maxNID,maxEID,dim)
        
    def UpdateManagerwithoutBoundary(self, maxNID = 0, maxEID = 0, dim = -1, boundryNodes = {}):
        if maxNID == 0:
            maxNID = self.nodeManager.maxID
        elif maxNID < self.nodeManager.maxID:
            maxNID = self.nodeManager.maxID + maxNID
        if maxEID == 0:
            maxEID = self.elementManager.maxID
        elif maxEID < self.elementManager.maxID:
            maxEID = self.elementManager.maxID + maxEID
        print("Update NodeManager...")
        if self.mshNodes is not None:
            nodekeytoid = self.nodeManager.AddNodesfromMSHwithoutBoundary(self.mshNodes,maxNID,boundryNodes)
        else:
            nodekeytoid = {}
        print("Update ElementManager...")
        if self.mshElements is not None:
            self.elementManager.AddElementsfromMSH(self.mshElements,maxNID,maxEID,dim, nodekeytoid) 
        


if __name__ == "__main__":
    mode = "MSH"
    mode = "DYNA"
    if mode == "MSH":
        path = os.getcwd()
        path = os.path.join(path,'Example\\Model\\New_Model_1\\Solid4\\Solid4.msh')
        importer = KooMSHImporter()
        importer.import_msh_file(path)
    elif mode == "DYNA":
        path = os.getcwd()
        path = os.path.join(path,'OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_DOE\\3ptBending_00000001')
        inPath = os.path.join(path,"3ptBending_00000001.k")        
        importer = KooDynaImporter()
        importer.importDynaFile(path)
        nodoutPath = os.path.join(path,"nodout")
        importer.importNODOUT(nodoutPath)

        