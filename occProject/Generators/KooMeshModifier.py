"""
KooMeshModifier (KMM) - LS-DYNA Model Transformation & Mesh Modification Engine

Reads LS-DYNA keyword (.k) files, applies mode-based transformations
(drop attitude, material exchange, part relocation, etc.),
and outputs modified models for sequential/chained CAE simulations.

Usage:
    python KooMeshModifier.py <option_file_path> [working_directory]

Author: koo.park
Email: koo.park@samsung.com
Group: CAE
"""

import sys
import os
import logging
import json
from pathlib import Path as PathLibPath
from typing import Any, Dict, List
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

import copy
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

from KooCAEManager.KooDynaAdvancedModification import KooDynaAdvancedModification


class KooMeshModifier(KooSimulationGenerator):
    def __init__(self, dynaImporter : KooDynaImporter = None):
        if dynaImporter == None:
            nodeMan = NodeManager()
            nodeSetMan = NodeSetManager(nodeMan)
            secMan = KooSectionManager()
            matMan = KooMaterialManager()
            elemMan = ElementManager()
            partMan = KooPartManager(nodeMan, elemMan)
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
        self.appFileName = "appfile.txt"
        self.modeList = []
        self.modeIDList = []
        self.modeIDOption = {}
        self.advancedModification = KooDynaAdvancedModification(dynaImporter)
        self.advancedModification.runDirectoryMode = False
        self.modelInfoMetadata = {}

        self.modelInfoMetadata["model_name"] = "Test"
        self.modelInfoMetadata["stage"] = "DV1"
        self.modelInfoMetadata["description"] = "Test Description"
        
        self.modelInfoMetadata["created_by"] = {}
        self.modelInfoMetadata["created_by"]["name"] = "koo.park"
        self.modelInfoMetadata["created_by"]["email"] = "koo.park@samsung.com"
        self.modelInfoMetadata["created_by"]["group"] = "CAE"
        self.modelInfoMetadata["created_by"]["team"] = "Samsung"
        
        self.inputFileName = None
        self.inputObjFileName = None 

    def GenerateMetaData(self):
        metaData = self.advancedModification.dynaImporter.metaData

        metaData["model_name"] = self.modelInfoMetadata["model_name"]
        metaData["stage"] = self.modelInfoMetadata["stage"]
        metaData["description"] = self.modelInfoMetadata["description"]
        
        metaData["created_by"]["name"] = self.modelInfoMetadata["created_by"]["name"]
        metaData["created_by"]["email"] = self.modelInfoMetadata["created_by"]["email"]
        metaData["created_by"]["group"] = self.modelInfoMetadata["created_by"]["group"]
        metaData["created_by"]["team"] = self.modelInfoMetadata["created_by"]["team"]


    def LoadScenariosJson(self, path: str | Path) -> List[Dict[str, Any]]:
        """
        시나리오 JSON 파일을 로드하여 dict 리스트로 반환한다.

        Parameters
        ----------
        path : str | Path
            시나리오 JSON 파일 경로

        Returns
        -------
        List[Dict[str, Any]]
            ScenarioRow 객체 리스트 (Python dict 형태)
        """
        p = PathLibPath(path)
        if not p.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {p}")

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("잘못된 포맷: 최상위 구조가 리스트가 아닙니다.")

        # 안전한 기본값 보정
        scenarios: List[Dict[str, Any]] = []
        for d in data:
            if not isinstance(d, dict):
                continue
            scenario = {
                "id": d.get("id"),
                "name": d.get("name", "Unnamed"),
                "fileName": d.get("fileName"),
                "objFileName": d.get("objFileName"),
                "analysisType": d.get("analysisType", "fullAngleMBD"),
                "params": d.get("params", {})
            }
            scenarios.append(scenario)

        return scenarios

    def ImportOption(self, fileName):
        filePath = os.path.join(self.curDir, fileName)

        with open(filePath, "r") as f:
            line = f.readline().strip()
            line = line.replace('\n','')
            while True:
                if "*end" in line.lower():
                    break
                if "*inputfile" in line.lower():
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    self.inputFileName = line
                if "*inputobjfile" in line.lower():
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    self.inputObjFileName = line
                if "*step" in line.lower():
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    self.advancedModification.step = int(line)
                if "rundirectorymode" in line.lower():
                    svector = line.split(",")
                    if svector[1].lower() == "true":
                        self.advancedModification.runDirectoryMode = True
                    else:
                        self.advancedModification.runDirectoryMode = False
                    if len(svector) > 2:
                        self.advancedModification.runDirectoryPath = svector[2]
                    if len(svector) > 3:
                        self.advancedModification.metaDirectoryPath = svector[3]
                if "*info" in line.lower():
                    svector = line.split(",")
                    name = svector[1]
                    revision = svector[2]
                    self.modelInfoMetadata["model_name"] = name
                    self.modelInfoMetadata["stage"] = revision
                if "*description" in line.lower():
                    svector = line.split(",")
                    description = svector[1]
                    self.modelInfoMetadata["description"] = description
                if "*creator" in line.lower():
                    svector = line.split(",")
                    if len(svector) > 1:
                        self.modelInfoMetadata["created_by"]["name"] = svector[1]
                    if len(svector) > 2:
                        self.modelInfoMetadata["created_by"]["email"] = svector[2]
                    if len(svector) > 3:
                        self.modelInfoMetadata["created_by"]["group"] = svector[3]
                    if len(svector) > 4:
                        self.modelInfoMetadata["created_by"]["team"] = svector[4]
                if "*mode" in line.lower():
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if "*" in line:
                            break
                        if not line:  # Skip empty lines
                            continue
                        svector = line.split(",")                    
                        if "elastic_to_rigid" in svector[0].lower():
                            self.modeList.append("ELASTIC_TO_RIGID")
                            self.modeIDList.append(int(svector[1]))                        
                        elif "material_exchange" in svector[0].lower():
                            self.modeList.append("MATERIAL_EXCHANGE")
                            self.modeIDList.append(int(svector[1]))
                        elif "part_location_doe" in svector[0].lower():
                            self.modeList.append("PART_LOCATION_DOE")
                            self.modeIDList.append(int(svector[1]))
                        elif "eroding_min_dt" in svector[0].lower():
                            self.modeList.append("ERODING_MIN_DT")
                            self.modeIDList.append(int(svector[1]))
                        elif "part_exchange" in svector[0].lower():
                            self.modeList.append("PART_EXCHANGE")                                        
                            self.modeIDList.append(int(svector[1]))
                        elif "part_morphing" in svector[0].lower():
                            self.modeList.append("PART_MORPHING")
                            self.modeIDList.append(int(svector[1]))                            
                        elif "weak_coupling" in svector[0].lower():
                            self.modeList.append("WEAK_COUPLING")
                            self.modeIDList.append(int(svector[1]))
                        elif "defeature_mesh" in svector[0].lower():
                            self.modeList.append("DEFEATURE_MESH")
                            self.modeIDList.append(int(svector[1]))
                        elif "drop_attitude" in svector[0].lower():
                            self.modeList.append("DROP_ATTITUDE")
                            self.modeIDList.append(int(svector[1]))
                        elif "translation_doe" in svector[0].lower():
                            self.modeList.append("TRANSLATION_DOE")
                            self.modeIDList.append(int(svector[1]))
                        elif "transform" in svector[0].lower():
                            self.modeList.append("TRANSFORM")
                            self.modeIDList.append(int(svector[1]))
                        elif "drop_weight_impact_test" in svector[0].lower():
                            self.modeList.append("DROP_WEIGHT_IMPACT_TEST")
                            self.modeIDList.append(int(svector[1]))
                        elif "constrained_nodal_rigidbody_to_beam" in svector[0].lower():
                            self.modeList.append("CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM")
                            self.modeIDList.append(int(svector[1]))
                        elif 'warped_part' in svector[0].lower():
                            self.modeList.append("WARPED_PART")
                            self.modeIDList.append(int(svector[1]))
                        elif "warped_to_initial_stress_part" in svector[0].lower(): 
                            self.modeList.append("WARPED_TO_INITIAL_STRESS_PART") 
                            self.modeIDList.append(int(svector[1]))
                        elif "dimensional_tolerance" in svector[0].lower():
                            self.modeList.append("DIMENSIONAL_TOLERANCE")
                            self.modeIDList.append(int(svector[1]))
                        elif "cohesive_between_conformal_meshes" in svector[0].lower():
                            self.modeList.append("COHESIVE_BETWEEN_CONFORMAL_MESHES")
                            self.modeIDList.append(int(svector[1]))
                        elif "dynain_to_initial" in svector[0].lower():
                            self.modeList.append("DYNAIN_TO_INITIAL")
                            self.modeIDList.append(int(svector[1]))
                        elif "contact_auto_decomposition" in svector[0].lower():
                            self.modeList.append("CONTACT_AUTO_DECOMPOSITION")
                            self.modeIDList.append(int(svector[1]))
                        elif "simulation_automation" in svector[0].lower():
                            self.modeList.append("SIMULATION_AUTOMATION")
                            self.modeIDList.append(int(svector[1]))
                        elif "remove_duplicate_tied_contacts" in svector[0].lower():
                            self.modeList.append("REMOVE_DUPLICATE_TIED_CONTACTS")
                            self.modeIDList.append(int(svector[1]))
                        elif "fem_to_iga" in svector[0].lower():
                            self.modeList.append("FEM_TO_IGA")
                            self.modeIDList.append(int(svector[1]))
                        else:
                            print("Invalid mode")
                            exit()
                    continue  
                elif "**remove_duplicate_tied_contacts" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["RemoveDuplicateTiedContacts"] = True
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "remove_duplicate_tied_contacts" in line.lower():
                            svector = line.split(",")
                            if len(svector) > 1:
                                if svector[1].lower() == "true":
                                    curOptions["RemoveDuplicateTiedContacts"] = True
                                else:
                                    curOptions["RemoveDuplicateTiedContacts"] = False
                            else:
                                curOptions["RemoveDuplicateTiedContacts"] = True
                        else:
                            print("Invalid option")
                            exit()
                    self.modeIDOption[curModeID] = curOptions

                elif "**simulationautomation" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "jsonfile" in line.lower():
                            svector = line.split(",")
                            curOptions["JsonFile"] = svector[1]
                    curOptions["MetaData"] = self.modelInfoMetadata                                                         
                    self.modeIDOption[curModeID] = curOptions
                    
                elif "**contactautodecomposition" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["SearchMarginX"] = 1.5
                    curOptions["SearchMarginY"] = 1.5
                    curOptions["SearchMarginZ"] = 1.5
                    curOptions["ContactKeyword"] = ""
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "$" in line.lower():
                            continue
                        elif "#" in line.lower():
                            continue
                        elif len(line) > 0 and line[0] == "#":
                            continue 
                        elif len(line) > 0 and line[0] == "$":
                            continue 
                        elif "searchmarginx" in line.lower():
                            svector = line.split(",")
                            curOptions["SearchMarginX"] = float(svector[1])
                        elif "searchmarginy" in line.lower():
                            svector = line.split(",")
                            curOptions["SearchMarginY"] = float(svector[1])
                        elif "searchmarginz" in line.lower():
                            svector = line.split(",")
                            curOptions["SearchMarginZ"] = float(svector[1])
                        elif "contactkeyword" in line.lower():
                            line = f.readline().rstrip("\n") 
                            contactKeyword = []
                            contactKeyword.append(line)
                            while True:
                                line = f.readline().rstrip("\n")
                                if not line:
                                    break
                                if "*" in line:
                                    break
                                if "$" in line.lower():
                                    continue
                                if "#" in line.lower():
                                    continue
                                chunks = [line[i:i+10] for i in range(0, len(line), 10)]
                                # split line by 10 characters

                                contactKeyword.append(chunks)
                                
                            curOptions["ContactKeyword"] = contactKeyword 
                    
                    self.modeIDOption[curModeID] = curOptions  
                elif "**dynaintoinitial" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["DynainPath"] = "dynain"
                    curOptions["IncludeStress"] = True
                    curOptions["RemoveDynamicRelaxation"] = True
                    curOptions["MovetoOriginbyNode"] = []
                    curOptions["MovetoOriginAutomatic"] = False
                    curOptions["RemovePartNameList"] = []
                    curOptions["RemovePartIDList"] = []
                    curOptions["DynamicRelaxation"] = False
                    curOptions["RemoveContactIDList"] = []

                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "dynainpath" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainPath"] = svector[1]
                        elif "includestress" in line.lower():
                            svector = line.split(",")
                            if svector[1].lower() == "true":
                                curOptions["IncludeStress"] = True
                            else:
                                curOptions["IncludeStress"] = False
                        elif "removedynamicrelaxation" in line.lower():
                            svector = line.split(",")
                            if svector[1].lower() == "true":
                                curOptions["RemoveDynamicRelaxation"] = True
                            else:
                                curOptions["RemoveDynamicRelaxation"] = False
                        elif "dynamicrelaxation" in line.lower():
                            svector = line.split(",")
                            if svector[1].lower() == "true":
                                curOptions["DynamicRelaxation"] = True
                            else:
                                curOptions["DynamicRelaxation"] = False
                        elif "movetooriginbynode" in line.lower():
                            svector = line.split(",")
                            curOptions["MovetoOriginbyNode"] = [int(x) for x in svector[1:]]
                        elif "movetooriginautomatic" in line.lower():
                            svector = line.split(",")
                            if svector[1].lower() == "true":
                                curOptions["MovetoOriginAutomatic"] = True
                            else:
                                curOptions["MovetoOriginAutomatic"] = False
                        elif "removepartbyname" in line.lower():
                            svector = line.split(",")
                            curOptions["RemovePartNameList"] = svector[1:]
                        elif "removepartbyid" in line.lower():
                            svector = line.split(",")
                            curOptions["RemovePartIDList"] = [int(x) for x in svector[1:]]
                        elif "removecontactbyid" in line.lower():
                            svector = line.split(",")
                            curOptions["RemoveContactIDList"] = [int(x) for x in svector[1:]]

                    self.modeIDOption[curModeID] = curOptions

                elif "**cohesivebetweenconformalmeshes" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["CohesiveMat"] = {}
                    curOptions["CohesiveMat"]["RO"] = 2.3e-9
                    curOptions["CohesiveMat"]["ROFlag"] = 0
                    curOptions["CohesiveMat"]["INTFAIL"] = 0 
                    curOptions["CohesiveMat"]["EN"] = 1000.0
                    curOptions["CohesiveMat"]["ET"] = 100.0
                    curOptions["CohesiveMat"]["GIC"] = 10.0
                    curOptions["CohesiveMat"]["GIIC"] = 10.0
                    #Exponent of the mixed mode criteria
                    curOptions["CohesiveMat"]["XMU"] = 1.0
                    #T:=Peak traction (stress units) in the normal direction. 
                    curOptions["CohesiveMat"]["T"] = 100.0
                    curOptions["CohesiveMat"]["S"] = 100.0
                    #UND:=Ultimate displacement in the normal direction
                    curOptions["CohesiveMat"]["UND"] = 10.0
                    #UTD:=Ultimate displacement in the tangential direction
                    curOptions["CohesiveMat"]["UTD"] = 10.0
                    #GAMMA:=Additional exponent for Benzeggagh-Kenane law (default = 1.0)
                    curOptions["CohesiveMat"]["GAMMA"] = 1.0
                    curOptions["PartA"] = []
                    curOptions["PartB"] = []
                    curOptions["Thickness"] = []
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "pair" in line.lower():
                            svector = line.split(",")
                            curOptions["PartA"].append(KooDynaInt(svector[1]))
                            curOptions["PartB"].append(KooDynaInt(svector[2]))
                            curOptions["Thickness"].append(KooDynaFloat(svector[3]))
                        elif "gamma" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["GAMMA"] = KooDynaFloat(svector[1])
                            continue
                        elif "und" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["UND"] = KooDynaFloat(svector[1])
                            continue
                        elif "utd" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["UTD"] = KooDynaFloat(svector[1])
                            continue
                        elif "roflag" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["ROFlag"] = KooDynaInt(svector[1])
                            continue
                        elif "intfail" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["INTFAIL"] = KooDynaFloat(svector[1])
                            continue
                        elif "gic" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["GIC"] = KooDynaFloat(svector[1])
                            continue
                        elif "giic" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["GIIC"] = KooDynaFloat(svector[1])
                            continue
                        elif "en" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["EN"] = KooDynaFloat(svector[1])
                            continue
                        elif "et" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["ET"] = KooDynaFloat(svector[1])
                            continue
                        elif "xmu" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["XMU"] = KooDynaFloat(svector[1])
                            continue
                        elif "t" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["T"] = KooDynaFloat(svector[1])
                            continue
                        elif "s" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["S"] = KooDynaFloat(svector[1])
                            continue
                        elif "ro" in line.lower():
                            svector = line.split(",")
                            curOptions["CohesiveMat"]["RO"] = KooDynaFloat(svector[1])
                            continue    
                    self.modeIDOption[curModeID] = curOptions

                elif "**dimensionaltolerance" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {} 
                    curOptions["Mode"] = "LIST"
                    # "LIST", "NORM", "LHS"
                    curOptions["PartOption"] = {}
                    curOptions["NumberofSamples"] = 1
                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break 
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "partdimtolerance" in line.lower():
                            svector = line.split(",")
                            mode = svector[1].lower()
                            if mode == "list":
                                curOptions["Mode"] = "LIST"
                            elif mode == "norm":
                                curOptions["Mode"] = "NORM"
                                if len(svector) > 2:
                                    curOptions["NumberofSamples"] = KooDynaInt(svector[2])
                                else:
                                    curOptions["NumberofSamples"] = 30                                    
                            elif mode == "lhs":
                                curOptions["Mode"] = "LHS"
                                if len(svector) > 2:
                                    curOptions["NumberofSamples"] = KooDynaInt(svector[2])
                                else:
                                    curOptions["NumberofSamples"] = 30
                                
                        else:
                            svector = line.split(",")
                            partid = KooDynaInt(svector[0])
                            direction = svector[1].lower()
                            options = svector[2:]
                            if partid in curOptions["PartOption"]:
                                curOptions["PartOption"][partid][direction] = options
                            else:
                                curOptions["PartOption"][partid] = {}
                                curOptions["PartOption"][partid][direction] = options
                                
                    self.modeIDOption[curModeID] = curOptions                      
                    
                elif "**warpedtoinitialstresspart" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["UnitScale"] = "mm"
                    curOptions["AmplitudeTop"] = 1.0
                    curOptions["AmplitudeBottom"] = 0.0
                    curOptions["Location"] = [0.0, 0.0, 0.0]
                    curOptions["XLength"] = 0.0
                    curOptions["YLength"] = 0.0
                    curOptions["Direction"] = [0.0, 0.0, 1.0]
                    curOptions["AdditionalThickness"] = 0.0
                    curOptions["WarpageFileTop"] = None
                    curOptions["WarpageFileBottom"] = None
                    curOptions["PIDs"] = []
                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "unitscale" in line.lower():
                            svector = line.split(",")
                            curOptions["UnitScale"] = svector[1]
                        elif "amplitudetop" in line.lower():
                            svector = line.split(",")
                            curOptions["AmplitudeTop"] = KooDynaFloat(svector[1])
                        elif "amplitudebottom" in line.lower():
                            svector = line.split(",")
                            curOptions["AmplitudeBottom"] = KooDynaFloat(svector[1])
                        elif "location" in line.lower():
                            svector = line.split(",")
                            curOptions["Location"] = [KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])]
                        elif "xlength" in line.lower():
                            svector = line.split(",")
                            curOptions["XLength"] = KooDynaFloat(svector[1])
                        elif "ylength" in line.lower():
                            svector = line.split(",")
                            curOptions["YLength"] = KooDynaFloat(svector[1])
                        elif "direction" in line.lower():
                            svector = line.split(",")
                            curOptions["Direction"] = [KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])]
                        elif "warpagefiletop" in line.lower():
                            svector = line.split(",")
                            curOptions["WarpageFileTop"] = svector[1]
                        elif "warpagefilebottom" in line.lower():
                            svector = line.split(",")
                            curOptions["WarpageFileBottom"] = svector[1]
                        elif "additionalthickness" in line.lower():
                            svector = line.split(",")
                            curOptions["AdditionalThickness"] = KooDynaFloat(svector[1])
                        elif "pid" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["PIDs"].append(KooDynaInt(svector[i]))
                    self.modeIDOption[curModeID] = curOptions
                    
                elif "**warpedpart" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["UnitScale"] = "mm"
                    curOptions["AmplitudeTop"] = 1.0
                    curOptions["AmplitudeBottom"] = 0.0
                    curOptions["Location"] = [0.0, 0.0, 0.0]
                    curOptions["XLength"] = 0.0
                    curOptions["YLength"] = 0.0
                    curOptions["Direction"] = [0.0, 0.0, 1.0]
                    curOptions["WarpageFileTop"] = "warpage.dat"
                    curOptions["WarpageFileBottom"] = None
                    curOptions["PIDs"] = []
                    
                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "unitscale" in line.lower():
                            svector = line.split(",")
                            curOptions["UnitScale"] = svector[1]
                        elif "amplitudetop" in line.lower():
                            svector = line.split(",")
                            curOptions["AmplitudeTop"] = KooDynaFloat(svector[1])
                        elif "amplitudebottom" in line.lower():
                            svector = line.split(",")
                            curOptions["AmplitudeBottom"] = KooDynaFloat(svector[1])
                        elif "location" in line.lower():
                            svector = line.split(",")
                            curOptions["Location"] = [KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])]
                        elif "xlength" in line.lower():
                            svector = line.split(",")
                            curOptions["XLength"] = KooDynaFloat(svector[1])
                        elif "ylength" in line.lower():
                            svector = line.split(",")
                            curOptions["YLength"] = KooDynaFloat(svector[1])
                        elif "direction" in line.lower():
                            svector = line.split(",")
                            curOptions["Direction"] = [KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])]
                        elif "warpagefiletop" in line.lower():
                            svector = line.split(",")
                            curOptions["WarpageFileTop"] = svector[1]
                        elif "warpagefilebottom" in line.lower():
                            svector = line.split(",")
                            curOptions["WarpageFileBottom"] = svector[1]
                        elif "pid" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["PIDs"].append(KooDynaInt(svector[i]))
                    self.modeIDOption[curModeID] = curOptions
                          
                elif "**constrainednodalrigidbodytobeam" in line.lower():
                    svector = line.split(",")
                    curModeID= int(svector[1])
                    curOptions = {}
                    curOptions["ALL"] = False
                    curOptions["CNRB"] = {} 
                    curOptions["E"] = 1.0E6
                    curOptions["PR"] = 0.3
                    curOptions["RHO"] = 7.0E-9
                    curOptions["Width"] = 1.0
                    curOptions["Height"] = 1.0
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "*pid" in line.lower():
                            svector = line.split(",")
                            if "all" in svector[1].lower():
                                curOptions["ALL"] = True
                            else:
                                curOptions["ALL"] = False
                                for i in range(1,len(svector)):
                                    curID = KooDynaInt(svector[i])
                                    curOptions["CNRB"][curID] = curID
                        elif "*e" in line.lower():
                            svector = line.split(",")
                            curOptions["E"] = KooDynaFloat(svector[1])
                        elif "*pr" in line.lower():
                            svector = line.split(",")
                            curOptions["PR"] = KooDynaFloat(svector[1])
                        elif "*rho" in line.lower():
                            svector = line.split(",")
                            curOptions["RHO"] = KooDynaFloat(svector[1])
                        elif "*width" in line.lower():
                            svector = line.split(",")
                            curOptions["Width"] = KooDynaFloat(svector[1])
                        elif "*height" in line.lower():
                            svector = line.split(",")
                            curOptions["Height"] = KooDynaFloat(svector[1])
                                                                                        
                    self.modeIDOption[curModeID] = curOptions                            

                elif "**partmorphing" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}                    
                    curOptions["UnitScale"] = 1.0
                    curOptions["GenerateMesh"] = False
                    curOptions["MeshSize"] = 1.0
                    curOptions["Morph"] = {}                    
                    morphid = 1
                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "unitscale" in line.lower():
                            curOptions["UnitScale"] = KooDynaFloat(line.split(",")[1])                            
                        elif "meshsize" in line.lower():
                            curOptions["MeshSize"] = KooDynaFloat(line.split(",")[1])
                            curOptions["GenerateMesh"] = True
                        elif "morphpid" in line.lower():
                            line = line.strip()
                            line = line.replace('(','')
                            line = line.replace(')','')
                            line = line.replace('\n','')                            
                            svector = line.split(",")
                            pid = int(svector[1])
                            ptargetid = int(svector[2])
                            xloc = 0.0 
                            yloc = 0.0
                            zloc = 0.0
                            xLength = 0.0
                            yLength = 0.0
                            zLength = 0.0
                            xdirX = KooDynaFloat(svector[3])
                            xdirY = KooDynaFloat(svector[4])
                            xdirZ = KooDynaFloat(svector[5])
                            zdirX = KooDynaFloat(svector[6])
                            zdirY = KooDynaFloat(svector[7])
                            zdirZ = KooDynaFloat(svector[8])
                            pushDistance = KooDynaFloat(svector[9])
                            EffectRadius = KooDynaFloat(svector[10])
                            angle = KooDynaFloat(svector[11])
                            numX = KooDynaInt(svector[12])
                            numY = KooDynaInt(svector[13])
                            morphOption = {}
                            morphOption["Type"] = "PIDBOX"
                            morphOption["PID"] = pid
                            morphOption["TargetPID"] = ptargetid
                            morphOption["Location"] = [xloc, yloc, zloc]
                            morphOption["XLength"] = xLength
                            morphOption["YLength"] = yLength
                            morphOption["ZLength"] = zLength
                            ampXDir = math.sqrt(xdirX*xdirX + xdirY*xdirY + xdirZ*xdirZ)
                            ampZDir = math.sqrt(zdirX*zdirX + zdirY*zdirY + zdirZ*zdirZ)
                            morphOption["XDir"] = [xdirX/ampXDir, xdirY/ampXDir, xdirZ/ampXDir]
                            morphOption["ZDir"] = [zdirX/ampZDir, zdirY/ampZDir, zdirZ/ampZDir]
                            if pushDistance > 0.0:
                                morphOption["Mode"] = "Pull"
                            else:
                                morphOption["Mode"] = "Push"
                            morphOption["PushDistance"] = abs(pushDistance)
                            morphOption["EffectRadius"] = EffectRadius
                            morphOption["Angle"] = angle
                            morphOption["NumberofBoxXDirection"] = numX
                            morphOption["NumberofBoxYDirection"] = numY
                            curOptions["Morph"][morphid] = morphOption                            
                            morphid += 1                                                            
                        
                        elif "morphfrompidbox" in line.lower():
                            line = line.strip()
                            line = line.replace('(','')
                            line = line.replace(')','')
                            line = line.replace('\n','')                            
                            svector = line.split(",")
                            pid = int(svector[1])
                            ptargetid = int(svector[2])
                            xloc = 0.0 
                            yloc = 0.0
                            zloc = 0.0
                            xLength = 0.0
                            yLength = 0.0
                            zLength = 0.0
                            xdirX = KooDynaFloat(svector[3])
                            xdirY = KooDynaFloat(svector[4])
                            xdirZ = KooDynaFloat(svector[5])
                            zdirX = KooDynaFloat(svector[6])
                            zdirY = KooDynaFloat(svector[7])
                            zdirZ = KooDynaFloat(svector[8])
                            pushDistance = KooDynaFloat(svector[9])
                            EffectRadius = KooDynaFloat(svector[10])
                            angle = KooDynaFloat(svector[11])
                            morphOption = {}
                            morphOption["Type"] = "PIDBOX"
                            morphOption["PID"] = pid
                            morphOption["TargetPID"] = ptargetid
                            morphOption["Location"] = [xloc, yloc, zloc]
                            morphOption["XLength"] = xLength
                            morphOption["YLength"] = yLength
                            morphOption["ZLength"] = zLength
                            ampXDir = math.sqrt(xdirX*xdirX + xdirY*xdirY + xdirZ*xdirZ)
                            ampZDir = math.sqrt(zdirX*zdirX + zdirY*zdirY + zdirZ*zdirZ)
                            morphOption["XDir"] = [xdirX/ampXDir, xdirY/ampXDir, xdirZ/ampXDir]
                            morphOption["ZDir"] = [zdirX/ampZDir, zdirY/ampZDir, zdirZ/ampZDir]
                            if pushDistance > 0.0:
                                morphOption["Mode"] = "Pull"
                            else:
                                morphOption["Mode"] = "Push"
                            morphOption["PushDistance"] = abs(pushDistance)
                            morphOption["EffectRadius"] = EffectRadius
                            morphOption["Angle"] = angle
                            curOptions["Morph"][morphid] = morphOption
                            morphid += 1                                                            
                        
                        elif "morphbox" in line.lower():
                            line = line.strip()
                            line = line.replace('(','')
                            line = line.replace(')','')
                            line = line.replace('\n','')                            
                            svector = line.split(",")
                            pid = int(svector[1])
                            xloc = KooDynaFloat(svector[2])
                            yloc = KooDynaFloat(svector[3])
                            zloc = KooDynaFloat(svector[4])
                            xLength = KooDynaFloat(svector[5])
                            yLength = KooDynaFloat(svector[6])
                            zLength = KooDynaFloat(svector[7])
                            xdirX = KooDynaFloat(svector[8])
                            xdirY = KooDynaFloat(svector[9])
                            xdirZ = KooDynaFloat(svector[10])
                            zdirX = KooDynaFloat(svector[11])
                            zdirY = KooDynaFloat(svector[12])
                            zdirZ = KooDynaFloat(svector[13])
                            pushDistance = KooDynaFloat(svector[14])
                            EffectRadius = KooDynaFloat(svector[15])
                            angle = KooDynaFloat(svector[16])
                            morphOption = {}
                            morphOption["Type"] = "Box"
                            morphOption["PID"] = pid
                            morphOption["Location"] = [xloc, yloc, zloc]
                            morphOption["XLength"] = xLength
                            morphOption["YLength"] = yLength
                            morphOption["ZLength"] = zLength                            
                            ampXDir = math.sqrt(xdirX*xdirX + xdirY*xdirY + xdirZ*xdirZ)
                            ampZDir = math.sqrt(zdirX*zdirX + zdirY*zdirY + zdirZ*zdirZ)                                                        
                            morphOption["XDir"] = [xdirX/ampXDir, xdirY/ampXDir, xdirZ/ampXDir]
                            morphOption["ZDir"] = [zdirX/ampZDir, zdirY/ampZDir, zdirZ/ampZDir]
                            
                            if pushDistance > 0.0:
                                morphOption["Mode"] = "Pull"
                            else:
                                morphOption["Mode"] = "Push"
                            morphOption["PushDistance"] = abs(pushDistance)
                            morphOption["EffectRadius"] = EffectRadius
                            morphOption["Angle"] = angle
                            curOptions["Morph"][morphid] = morphOption                            
                            morphid += 1
                    
                    self.modeIDOption[curModeID] = curOptions                            
                        
                        
                    
                    
                elif "**dropweightimpacttest" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["BoundaryDistance"] = 0.0
                    curOptions["StressWaveVelocity"] = 0.0
                    curOptions["DistanceMargin"] = 0.0
                    curOptions["DT"] = 1.0e-6
                    curOptions["TFinal"] = 0.0
                    # DampingSpring, OutsideRigidPart, OutsideRigidElement
                    curOptions["Mode"] = "DampingSpring"
                    curOptions["PartIDs"] = []
                    curOptions["OffsetDistance"] = 0.000000001
                    curOptions["LocationMode"] = []
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        
                        if "stresswavevelocity" in line.lower():
                            svector = line.split(",")
                            stressWaveVelocity = KooDynaFloat(svector[1])
                            curOptions["StressWaveVelocity"] = stressWaveVelocity
                        elif "generationmode" in line.lower():
                            svector = line.split(",")
                            curOptions["Mode"] = svector[1]
                        elif "offsetdistance" in line.lower():
                            svector = line.split(",")
                            if len(svector) == 2:
                                offsetDistance = KooDynaFloat(svector[1])
                            else:
                                offsetDistance = 0.000000001
                            curOptions["OffsetDistance"] = offsetDistance
                        elif "distancemargin" in line.lower():
                            svector = line.split(",")
                            distanceMargin = KooDynaFloat(svector[1])
                            curOptions["DistanceMargin"] = distanceMargin                        
                        elif "boundarydistance" in line.lower():
                            svector = line.split(",")
                            boundaryDistance = KooDynaFloat(svector[1])
                            curOptions["BoundaryDistance"] = boundaryDistance                        
                        elif "youngsmoduluswall" in line.lower():
                            svector = line.split(",")
                            youngsModulusWall = KooDynaFloat(svector[1])
                            curOptions["YoungsModulusWall"] = youngsModulusWall
                        elif "youngsmodulusimpactorfront" in line.lower():
                            svector = line.split(",")
                            youngsModulusImpactorFront = KooDynaFloat(svector[1])
                            curOptions["YoungsModulusImpactorFront"] = youngsModulusImpactorFront
                        elif "youngsmodulusdamper" in line.lower():
                            svector = line.split(",")
                            youngsModulusDamper = KooDynaFloat(svector[1])
                            curOptions["YoungsModulusDamper"] = youngsModulusDamper
                        elif "youngsmodulusimpactor" in line.lower():
                            svector = line.split(",")
                            youngsModulusImpactor = KooDynaFloat(svector[1])
                            curOptions["YoungsModulusImpactor"] = youngsModulusImpactor
                        elif "poissonratiowall" in line.lower():
                            svector = line.split(",")
                            poissonRatioWall = KooDynaFloat(svector[1])
                            curOptions["PoissonRatioWall"] = poissonRatioWall
                        elif "poissonratioimpactorfront" in line.lower():
                            svector = line.split(",")
                            poissonRatioImpactorFront = KooDynaFloat(svector[1])
                            curOptions["PoissonRatioImpactorFront"] = poissonRatioImpactorFront
                        elif "poissonratiodamper" in line.lower():
                            svector = line.split(",")
                            poissonRatioDamper = KooDynaFloat(svector[1])
                            curOptions["PoissonRatioDamper"] = poissonRatioDamper
                        elif "poissonratioimpactor" in line.lower():
                            svector = line.split(",")
                            poissonRatioImpactor = KooDynaFloat(svector[1])
                            curOptions["PoissonRatioImpactor"] = poissonRatioImpactor
                        elif "materialidwall" in line.lower():
                            svector = line.split(",")
                            materialIDWall = KooDynaInt(svector[1])
                            curOptions["MaterialIDWall"] = materialIDWall
                        elif "materialidimpactorfront" in line.lower():
                            svector = line.split(",")
                            materialIDImpactorFront = KooDynaInt(svector[1])
                            curOptions["MaterialIDImpactorFront"] = materialIDImpactorFront
                        elif "materialiddamper" in line.lower():
                            svector = line.split(",")
                            materialIDDamper = KooDynaInt(svector[1])
                            curOptions["MaterialIDDamper"] = materialIDDamper
                        elif "materialidimpactor" in line.lower():
                            svector = line.split(",")
                            materialIDImpactor = KooDynaInt(svector[1])
                            curOptions["MaterialIDImpactor"] = materialIDImpactor
                        elif "densitywall" in line.lower():
                            svector = line.split(",")
                            densityWall = KooDynaFloat(svector[1])
                            curOptions["DensityWall"] = densityWall
                        elif "densityimpactorfront" in line.lower():
                            svector = line.split(",")
                            densityImpactorFront = KooDynaFloat(svector[1])
                            curOptions["DensityImpactorFront"] = densityImpactorFront
                        elif "densitydamper" in line.lower():
                            svector = line.split(",")
                            densityDamper = KooDynaFloat(svector[1])
                            curOptions["DensityDamper"] = densityDamper                        
                        elif "densityimpactor" in line.lower():
                            svector = line.split(",")
                            densityImpactor = KooDynaFloat(svector[1])
                            curOptions["DensityImpactor"] = densityImpactor                         
                        elif "partids" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["PartIDs"].append(KooDynaInt(svector[i]))
                        elif "locationmode" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["LocationMode"].append(KooDynaString(svector[i]))
                        elif "locationx" in line.lower():
                            svector = line.split(",")
                            x = [KooDynaFloat(svector[1])]
                            if len(svector) > 2:
                                for i in range(2, len(svector)):
                                    x.append(KooDynaFloat(svector[i]))                        
                            curOptions["LocationX"] = x
                        elif "locationy" in line.lower():
                            svector = line.split(",")
                            y = [KooDynaFloat(svector[1])]  
                            if len(svector) > 2:
                                for i in range(2, len(svector)):
                                    y.append(KooDynaFloat(svector[i]))
                            curOptions["LocationY"] = y                                                              
                        elif "height" in line.lower():
                            svector = line.split(",")
                            heightList = [] 
                            for i in range(1, len(svector)):
                                height = KooDynaFloat(svector[i])
                                heightList.append(height)
                            curOptions["Height"] = heightList
                        elif "initialvelocityx" in line.lower():
                            svector = line.split(",")
                            velocityXList = []
                            for i in range(1, len(svector)):
                                velocityX = KooDynaFloat(svector[i])
                                velocityXList.append(velocityX)
                            curOptions["InitialVelocityX"] = velocityXList
                        elif "initialvelocityy" in line.lower():
                            svector = line.split(",")
                            velocityYList = []
                            for i in range(1, len(svector)):
                                velocityY = KooDynaFloat(svector[i])
                                velocityYList.append(velocityY)
                            curOptions["InitialVelocityY"] = velocityYList
                        elif "initialvelocityz" in line.lower():
                            svector = line.split(",")
                            velocityZList = []
                            for i in range(1, len(svector)):
                                velocityZ = KooDynaFloat(svector[i])
                                velocityZList.append(velocityZ)
                            curOptions["InitialVelocityZ"] = velocityZList
                        elif "tfinal" in line.lower():
                            svector = line.split(",")
                            tFinal = KooDynaFloat(svector[1])
                            curOptions["TFinal"] = tFinal
                        elif "dt" in line.lower():
                            svector = line.split(",")
                            dt = KooDynaFloat(svector[1])
                            curOptions["DT"] = dt
                        elif "type" in line.lower():
                            svector = line.split(",")
                            # Sphere, Cylinder, Box
                            curOptions["Type"] = svector[1]
                        elif "dimensiondamper" in line.lower():
                            svector = line.split(",")
                            dimensionDamper = [KooDynaFloat(svector[1])]
                            if len(svector) > 2:
                                for i in range(2, len(svector)):
                                    dimensionDamper.append(KooDynaFloat(svector[i]))                            
                            curOptions["DimensionDamper"] = dimensionDamper
                        elif "dimension" in line.lower():
                            svector = line.split(",")
                            if curOptions["Type"].lower() == "sphere":                                
                                v1 = KooDynaFloat(svector[1])
                                curOptions["Dimension"] = [v1]
                            elif curOptions["Type"].lower() == "cylinder":
                                v1 = KooDynaFloat(svector[1])
                                v2 = KooDynaFloat(svector[2])
                                v3 = KooDynaFloat(svector[3])
                                v4 = KooDynaFloat(svector[4])
                                if len(svector) > 5:
                                    v5 = KooDynaFloat(svector[5])
                                    curOptions["Dimension"] = [v1, v2, v3, v4, v5]
                                else:
                                    v5 = v2
                                    curOptions["Dimension"] = [v1, v2, v3, v4, v5]
                        elif "meshsize" in line.lower():
                            svector = line.split(",")
                            meshSize = KooDynaFloat(svector[1])
                            curOptions["MeshSize"] = meshSize
                    self.modeIDOption[curModeID] = curOptions
                    
                elif "**translation_doe" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["Translation"] = {}                    
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break                        
                        if "translationx" in line.lower():
                            pid = int(line.split(",")[1])

                            svector = line.split(",")[2:]
                            transXList = [KooDynaFloat(x) for x in svector]
                            if pid not in curOptions["Translation"]:                                
                                # add 0 list for y and z
                                curOptions["Translation"][pid]["Y"] = [0.0] * len(transXList)
                                curOptions["Translation"][pid]["Z"] = [0.0] * len(transXList)

                            curOptions["Translation"][pid]["X"] = transXList
                        if "translationy" in line.lower():
                            pid = int(line.split(",")[1])
                            svector = line.split(",")[2:]
                            transYList = [KooDynaFloat(x) for x in svector]
                            if pid not in curOptions["Translation"]:                                
                                # add 0 list for x and z
                                curOptions["Translation"][pid]["X"] = [0.0] * len(transYList)
                                curOptions["Translation"][pid]["Z"] = [0.0] * len(transYList)
                            curOptions["Translation"][pid]["Y"] = transYList
                        if "translationz" in line.lower():
                            pid = int(line.split(",")[1])
                            svector = line.split(",")[2:]
                            transZList = [KooDynaFloat(x) for x in svector]
                            if pid not in curOptions["Translation"]:                                
                                # add 0 list for x and y
                                curOptions["Translation"][pid]["X"] = [0.0] * len(transZList)
                                curOptions["Translation"][pid]["Y"] = [0.0] * len(transZList)
                            curOptions["Translation"][pid]["Z"] = transZList

                    self.modeIDOption[curModeID] = curOptions
                elif "**transform" in line.lower():
                    svector = line.split(",")
                    curModeID= int(svector[1])
                    curOptions = []
                    while True:
                        line = f.readline().strip() 
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        if "translation" in line.lower():
                            svector = line.split(",")                            
                            curOptions.append(["Translation", KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])])
                        elif "vectortovectorrotation" in line.lower():
                            svector = line.split(",")                                                        
                            curOptions.append(["VectorToVectorRotation", KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3]), KooDynaFloat(svector[4]), KooDynaFloat(svector[5]), KooDynaFloat(svector[6])])
                        elif "vectorrotation" in line.lower():
                            svector = line.split(",")                                                        
                            curOptions.append(["VectorRotation", KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])])
                        elif "rotation" in line.lower():
                            svector = line.split(",")                            
                            curOptions.append(["Rotation", KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])])
                        elif "scale" in line.lower():
                            svector = line.split(",")                            
                            curOptions.append(["Scale", KooDynaFloat(svector[1]), KooDynaFloat(svector[2]), KooDynaFloat(svector[3])])
                        elif "mirror" in line.lower():
                            svector = line.split(",")                            
                            curOptions.append(["Mirror", svector[1]])
                        
                    self.modeIDOption[curModeID] = curOptions
                            
                elif "**elastictorigid" in line.lower():
                    exceptPidList = []
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        if "*pidexcept" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                exceptPidList.append(int(svector[i]))
                    curOptions["PIDExcept"] = exceptPidList
                    self.modeIDOption[curModeID] = curOptions  
                elif "*dropattitude" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["TFinal"] = 0.0
                    curOptions["DT"] = 0.0
                    curOptions["DropSurface"] = ["Plane", 0.0, 0.0, 0.0, 10, 10, 10]
                    curOptions["runid"] = []
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        if "runid" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["runid"].append(int(svector[i]))
                        if "eulerrolling" in line.lower():
                            svector = line.split(",")
                            eulerXList = []
                            for i in range(1, len(svector)):
                                eulerX = KooDynaFloat(svector[i])
                                eulerXList.append(eulerX)
                            curOptions["EulerRolling"] = eulerXList
                        elif "eulerpitching" in line.lower():
                            svector = line.split(",")
                            eulerYList = []
                            for i in range(1, len(svector)):
                                eulerY = KooDynaFloat(svector[i])
                                eulerYList.append(eulerY)
                            curOptions["EulerPitching"] = eulerYList
                        elif "euleryawing" in line.lower():
                            svector = line.split(",")
                            eulerZList = []
                            for i in range(1, len(svector)):
                                eulerZ = KooDynaFloat(svector[i])
                                eulerZList.append(eulerZ)
                            curOptions["EulerYawing"] = eulerZList
                        elif "height" in line.lower():
                            svector = line.split(",")
                            heightList = [] 
                            for i in range(1, len(svector)):
                                height = KooDynaFloat(svector[i])
                                heightList.append(height)
                            curOptions["Height"] = heightList
                        elif "initialvelocityx" in line.lower():
                            svector = line.split(",")
                            velocityXList = []
                            for i in range(1, len(svector)):
                                velocityX = KooDynaFloat(svector[i])
                                velocityXList.append(velocityX)
                            curOptions["InitialVelocityX"] = velocityXList
                        elif "initialvelocityy" in line.lower():
                            svector = line.split(",")
                            velocityYList = []
                            for i in range(1, len(svector)):
                                velocityY = KooDynaFloat(svector[i])
                                velocityYList.append(velocityY)
                            curOptions["InitialVelocityY"] = velocityYList
                        elif "initialvelocityz" in line.lower():
                            svector = line.split(",")
                            velocityZList = []
                            for i in range(1, len(svector)):
                                velocityZ = KooDynaFloat(svector[i])
                                velocityZList.append(velocityZ)
                            curOptions["InitialVelocityZ"] = velocityZList
                        elif "initialangularvelocityx" in line.lower():
                            svector = line.split(",")
                            angularVelocityXList = []
                            for i in range(1, len(svector)):
                                angularVelocityX = KooDynaFloat(svector[i])
                                angularVelocityXList.append(angularVelocityX)
                            curOptions["InitialAngularVelocityX"] = angularVelocityXList
                        elif "initialangularvelocityy" in line.lower():
                            svector = line.split(",")
                            angularVelocityYList = []
                            for i in range(1, len(svector)):
                                angularVelocityY = KooDynaFloat(svector[i])
                                angularVelocityYList.append(angularVelocityY)
                            curOptions["InitialAngularVelocityY"] = angularVelocityYList
                        elif "initialangularvelocityz" in line.lower():
                            svector = line.split(",")
                            angularVelocityZList = []
                            for i in range(1, len(svector)):
                                angularVelocityZ = KooDynaFloat(svector[i])
                                angularVelocityZList.append(angularVelocityZ)
                            curOptions["InitialAngularVelocityZ"] = angularVelocityZList
                        elif "offsetdistance" in line.lower():
                            svector = line.split(",")
                            if len(svector) == 2:
                                offsetDistance = KooDynaFloat(svector[1])
                            else:
                                offsetDistance = 0.000000001
                            curOptions["OffsetDistance"] = offsetDistance
                        elif "density" in line.lower():
                            svector = line.split(",")
                            density = KooDynaFloat(svector[1])
                            curOptions["Density"] = density
                        elif "youngsmodulus" in line.lower():
                            svector = line.split(",")
                            youngsModulus = KooDynaFloat(svector[1])
                            curOptions["YoungsModulus"] = youngsModulus
                        elif "poissonratio" in line.lower():
                            svector = line.split(",")
                            poissonRatio = KooDynaFloat(svector[1])
                            curOptions["PoissonRatio"] = poissonRatio
                        elif "tfinal" in line.lower():
                            svector = line.split(",")
                            tFinal = KooDynaFloat(svector[1])
                            curOptions["TFinal"] = tFinal
                        elif "dt" in line.lower():
                            svector = line.split(",")
                            dt = KooDynaFloat(svector[1])
                            curOptions["DT"] = dt
                        elif "dropsurface" in line.lower():
                            svector = line.split(",")
                            dropSurface = svector[1]
                            if dropSurface.lower() == "plane":
                                xLength = KooDynaFloat(svector[2])
                                yLength = KooDynaFloat(svector[3])
                                zLength = KooDynaFloat(svector[4])
                                
                                numX = KooDynaInt(svector[5])
                                numY = KooDynaInt(svector[6])
                                numZ = KooDynaInt(svector[7])
                                curOptions["DropSurface"] = ["Plane", xLength, yLength, zLength, numX, numY, numZ]
                                                                
                            elif dropSurface.lower() == "planewithroughness":
                                xLength = KooDynaFloat(svector[2])
                                yLength = KooDynaFloat(svector[3])
                                zLength = KooDynaFloat(svector[4])
                                
                                numX = KooDynaInt(svector[5])
                                numY = KooDynaInt(svector[6])
                                numZ = KooDynaInt(svector[7])
                                roughnessMode = svector[8]
                                # XYRandom, XRandom, YRandom, XSin, YSin, XYSin
                                RMax = KooDynaFloat(svector[9])
                                ShapeFactor = KooDynaFloat(svector[10])
                                if len(svector) > 11:
                                    ShapeFactor2 = KooDynaFloat(svector[11])
                                    curOptions["DropSurface"] = ["PlanewithRoughness", xLength, yLength, zLength, numX, numY, numZ, roughnessMode, RMax, ShapeFactor, ShapeFactor2]
                                else:
                                    curOptions["DropSurface"] = ["PlanewithRoughness", xLength, yLength, zLength, numX, numY, numZ, roughnessMode, RMax, ShapeFactor, ShapeFactor]
                              
                    self.modeIDOption[curModeID] = curOptions
                elif "*weakcoupling" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    boundaryBox = None 
                    curOptions["BoundaryBox"] = boundaryBox
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        if "filepath" in line.lower():
                            svector = line.split(",")
                            filePath = svector[1]
                            curOptions["FilePath"] = filePath
                        elif "set" in line.lower():
                            svector = line.split(",")
                            mode = svector[1]
                            sid = KooDynaInt(svector[2])
                            # NodeSet, SegmentSet
                            curOptions["Mode"] = mode
                            curOptions["SetID"] = sid
                        elif "boundarybox" in line.lower():
                            svector = line.split(",")
                            minX = KooDynaFloat(svector[1])
                            maxX = KooDynaFloat(svector[2])
                            minY = KooDynaFloat(svector[3])
                            maxY = KooDynaFloat(svector[4])
                            minZ = KooDynaFloat(svector[5])
                            maxZ = KooDynaFloat(svector[6])
                            boundaryBox = [minX, maxX, minY, maxY, minZ, maxZ]
                            curOptions["BoundaryBox"] = boundaryBox
                    self.modeIDOption[curModeID] = curOptions
                elif "**defeaturemesh" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}                    
                    curOptions["PIDS"] = []
                                                            
                    while True:
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "pids" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                pid = KooDynaInt(svector[i])
                                curOptions["PIDS"].append(pid)
                        elif "pid" in line.lower():
                            svector = line.split(",")
                            pid = KooDynaInt(svector[1])
                            curOptions["PIDS"].append(pid)
                        elif "minlength" in line.lower():
                            svector = line.split(",")
                            minLength = KooDynaFloat(svector[1])
                            curOptions["MinLength"] = minLength
                            
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        
                    self.modeIDOption[curModeID] = curOptions
                elif "**materialexchange" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["MIDs"] = {}
                    curOptions["Vars"] = {}
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    
                    while True:                       
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        if "*varlist" in line.lower():
                            svector = line.split(",")
                            name = svector[1].replace("*","")
                            varOption = curOptions["Vars"]
                            # svector without svector[0],svector[1]
                            varList = svector[2:]                                                        
                            # varList to float list
                            varList = [KooDynaFloat(var) for var in varList]                                                        
                            varOption[name] = varList
                            line = f.readline().strip()
                            line = line.replace('\n','')
                        elif "*mid" in line.lower():
                            svector = line.split(",")
                            name = svector[0].replace("*","")
                            curKeyword = []
                            curKeywordName = svector[1]
                            curKeyword.append(svector[1])
                            i = 0
                            while True:
                                line = f.readline()
                                line = line.replace('\n','')
                                if not line:
                                    break
                                if "*" in line:
                                    break
                                if "$" in line:
                                    continue
                                if i == 0 and "title" in curKeywordName.lower():
                                    curKeyword.append([line])
                                else:
                                    svector = parse_whole(line, [10, 10, 10, 10, 10, 10, 10, 10])
                                    curKeyword.append(svector)
                                i = i + 1
                    curOptions["MIDs"][name] = curKeyword
                    self.modeIDOption[curModeID] = curOptions
                    line = line.strip()
                    continue      
                elif "**partlocationdoe" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["PIDs"] = []
                    curOptions["MaskPID"] = 0
                    curOptions["ObstaclePIDs"] = []
                    curOptions["DX"] = 0.0
                    curOptions["DY"] = 0.0
                    curOptions["DZ"] = 0.0
                    curOptions["NX"] = 10
                    curOptions["NY"] = 10
                    curOptions["NZ"] = 0
                    curOptions["Dilation"] = 1
                    curOptions["Sampling"] = {}
                    
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    
                    while True:
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "*pids" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                pid = KooDynaInt(svector[i])
                                curOptions["PIDs"].append(pid)
                        elif "*maskpid" in line.lower():
                            svector = line.split(",")
                            maskPID = KooDynaInt(svector[1])
                            curOptions["MaskPID"] = maskPID
                        elif "*obstaclepid" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                pid = KooDynaInt(svector[i])
                                curOptions["ObstaclePIDs"].append(pid)
                        elif "*dx" in line.lower():
                            svector = line.split(",")
                            dx = KooDynaFloat(svector[1])
                            curOptions["DX"] = dx
                        elif "*dy" in line.lower():
                            svector = line.split(",")
                            dy = KooDynaFloat(svector[1])
                            curOptions["DY"] = dy
                        elif "*dz" in line.lower():
                            svector = line.split(",")
                            dz = KooDynaFloat(svector[1])
                            curOptions["DZ"] = dz
                        elif "*nx" in line.lower():
                            svector = line.split(",")
                            nx = KooDynaInt(svector[1])
                            curOptions["NX"] = nx
                        elif "*ny" in line.lower():
                            svector = line.split(",")
                            ny = KooDynaInt(svector[1])
                            curOptions["NY"] = ny
                        elif "*nz" in line.lower():
                            svector = line.split(",")
                            nz = KooDynaInt(svector[1])
                            curOptions["NZ"] = nz
                        elif "*dilation" in line.lower():
                            svector = line.split(",")
                            dilation = KooDynaInt(svector[1])
                            curOptions["Dilation"] = dilation
                        elif "*sampling" in line.lower():
                            svector = line.split(",")
                            method = svector[1]
                            numberofSamples = KooDynaInt(svector[2])                            
                            curOptions["Sampling"]["Method"] = method
                            curOptions["Sampling"]["NumberofSamples"] = numberofSamples
                        
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        

                    self.modeIDOption[curModeID] = curOptions
                    line = line.strip()
                    continue    


                                                        
                elif "**erodingmindt" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    while True:
                        
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "*dt" in line.lower():
                            svector = line.split(",")
                            dt = KooDynaFloat(svector[1],1.0e-9)
                            curOptions["DT"] = dt   
                        line = f.readline().strip()
                        line = line.replace('\n','')
                    self.modeIDOption[curModeID] = curOptions
                    line  = line.strip()
                    continue
                elif "**partexchange" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}            
                    curOptions["MIDs"] = {}
                    curOptions["THKs"] = {}
                    curOptions["NUMEs"] = {}
                    curOptions["EOSs"] = {}
                    curOptions["HGIDs"] = {}
                    curOptions["Layup"] = None
                    curOptions["PIDS"] = []
                    curOptions["LayerThickness"] = []
                    curOptions["DesiredLengthRatio"] = {}
                    curOptions["InplaneRotation"] = []
                    curOptions["Constraints"] = {}                    
                    curOptions["NumberofElements"] = 0

                    pid = 0 
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    while True:
                        
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "*pids" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                pid = svector[i]
                                curOptions["PIDS"].append(pid)
                            
                        elif "*pid" in line.lower():
                            svector = line.split(",")
                            pid = int(svector[1])
                            curOptions["PID"] = pid
                        elif "*unstructuredtostructured" in line.lower():
                            line = line.replace("(","")
                            line = line.replace(")","")
                            line = line.strip()
                            line = line.replace('\n','')
                            svector = line.split(",")
                            curOption = {}
                            curOption["NX"] = KooDynaInt(svector[1])
                            curOption["NY"] = KooDynaInt(svector[2])
                            curOption["NZ"] = KooDynaInt(svector[3])
                            curOptions["UnstructuredtoStructured"] = curOption
                        elif "*layerthickness" in line.lower():
                            thicknessList = []
                            while True:
                                line = f.readline()
                                line = line.replace('\n','')
                                if not line:
                                    break
                                if "*" in line:
                                    break
                                if "$" in line:
                                    continue
                                thicknessList.append(KooDynaFloat(line))
                            curOptions["LayerThickness"] = thicknessList
                        elif "*converthexato" in line.lower():                            
                            line = line.replace("(","")
                            line = line.replace(")","")
                            line = line.strip()
                            line = line.replace('\n','')
                            svector = line.split(",")
                            curOption = {}
                            # Shell or TShell or Solid or SolidComp or ShellSolidComp or SolidwithSlack or SolidStructuredZSlack
                            curOption["Type"] = svector[1]
                            v1 = KooDynaFloat(svector[2])
                            v2 = KooDynaFloat(svector[3])
                            v3 = KooDynaFloat(svector[4])
                            curOption["Vector"] = [v1, v2, v3]                                                        
                            curOption["ToleranceAngle"] = KooDynaFloat(svector[5])
                            if curOption["Type"].lower() == "solidwithslack":
                                if len(svector) < 9:
                                    z1 = 0.0
                                    z2 = 0.0
                                    z3 = 1.0
                                else:
                                    z1 = KooDynaFloat(svector[6])
                                    z2 = KooDynaFloat(svector[7])
                                    z3 = KooDynaFloat(svector[8])
                                lengthZ = math.sqrt(z1*z1 + z2*z2 + z3*z3)
                                curOption["ZDirection"] = [z1/lengthZ, z2/lengthZ, z3/lengthZ]
                                
                            curOptions["converthexato"] = curOption                        
                        elif "*desiredlengthratiosamples" in line.lower():
                            svector = line.split(",")
                            curOption = curOptions["DesiredLengthRatio"]
                            curOption["Samples"] = []
                            for i in range(1, len(svector)):
                                curOption["Samples"].append(KooDynaFloat(svector[i]))
                            
                        elif "*desiredlengthratiostatistics" in line.lower():
                            svector = line.split(",")
                            if len(svector) < 6:
                                print("Invalid desired length statistics")
                                exit()
                            # number of samples
                            curOption = curOptions["DesiredLengthRatio"]
                            curOption["NumberofSamples"] = KooDynaInt(svector[1])
                            # average
                            curOption["Average"] = KooDynaFloat(svector[2])
                            # standard deviation
                            curOption["StandardDeviation"] = KooDynaFloat(svector[3])                            
                            # minimum
                            curOption["Minimum"] = KooDynaFloat(svector[4])
                            # maximum
                            curOption["Maximum"] = KooDynaFloat(svector[5])
                               
                        elif "*constraintpids" in line.lower():
                            svector = line.split(",")
                            curOption = curOptions["Constraints"]
                            curOption["PIDs"] = []
                            for i in range(1, len(svector)):
                                pid = svector[i] 
                                curOption["PIDs"].append(pid)
                                                                                        
                        elif "*inplanerotation" in line.lower():
                            svector = line.split(",")
                            curOption = curOptions["InplaneRotation"]
                            angle = KooDynaFloat(svector[1])
                            location = KooDynaFloat(svector[2])
                            curOption.append([angle, location])
                        
                        elif "*numberofelements" in line.lower():
                            NumberofElements = KooDynaInt(line.split(",")[1])
                            curOptions["NumberofElements"] = NumberofElements
                            
                        elif "*layup" in line.lower():
                            layupString = ""
                            while True:
                                line = f.readline().strip()
                                line = line.replace('\n','')
                                if not line:
                                    break
                                if "*" in line:
                                    break
                                if "$" in line:
                                    continue
                                layupString = layupString + line + "\n"
                            curOptions["Layup"] = layupString  
                        elif "*thk" in line.lower():
                            svector = line.split(",")
                            name = svector[0].replace("*","")
                            thkOption = curOptions["THKs"]
                            thkOption[name] = KooDynaFloat(svector[1])
                        elif "*nume" in line.lower():
                            svector = line.split(",")
                            name = svector[0].replace("*","")
                            numeOption = curOptions["NUMEs"]
                            numeOption[name] = KooDynaInt(svector[1])
                        elif "*mid" in line.lower() or "*eos" in line.lower() or "*hgid" in line.lower():
                            svector = line.split(",")
                            name = svector[0].replace("*","")   
                            curKeyword = [] 
                            curKeywordName = svector[1]
                            curKeyword.append(svector[1])
                            i = 0
                            while True:
                                line = f.readline()
                                line = line.replace('\n','')
                                if not line:
                                    break
                                if "*" in line:
                                    break
                                if "$" in line:
                                    continue
                                if i == 0 and "title" in curKeywordName.lower():
                                    curKeyword.append([line])
                                else:
                                    svector = parse_whole(line, [10, 10, 10, 10, 10, 10, 10, 10])
                                    curKeyword.append(svector)
                                i = i + 1
                            if "mid" in name.lower():
                                curOptions["MIDs"][name] = curKeyword
                            elif "eos" in name.lower():
                                curOptions["EOSs"][name] = curKeyword
                            elif "hgid" in name.lower():
                                curOptions["HGIDs"][name] = curKeyword
                            line = line.strip()
                            continue
                            
                        elif "*" in line[0]:
                            curKeyword = []
                            curKeywordName = line
                            curKeyword.append(line)
                            i = 0 
                            while True:
                                line = f.readline()
                                line = line.replace('\n','')
                                if not line:
                                    break
                                if "*" in line.lower():
                                    break                                    
                                if "$" in line:
                                    continue
                                # split line with each 10 characters
                                if i == 0 and "title" in curKeywordName.lower():
                                    curKeyword.append([line])
                                elif i == 0 and "_id" in curKeywordName.lower():
                                    svector = parse_whole(line, [10, 70])
                                    curKeyword.append(svector)
                                else:
                                    svector = parse_whole(line, [10, 10, 10, 10, 10, 10, 10, 10])
                                    curKeyword.append(svector)                                                          
                                i = i + 1
                                
                                
                            curOptions[curKeywordName] = curKeyword
                            line = line.strip()
                            continue
                        line = f.readline().strip()
                        line = line.replace('\n','')
                                               
                    self.modeIDOption[curModeID] = curOptions

                elif "**femtoiga" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["IGAParts"] = []  # List of IGA part configs

                    while True:
                        line = f.readline()
                        if not line:  # EOF
                            break
                        line = line.strip()
                        line = line.replace('\n','')
                        if not line:  # Empty line, skip it
                            continue
                        if "**end" in line.lower():
                            break
                        elif len(line) > 0 and line[0] == "#":
                            continue
                        elif len(line) > 0 and line[0] == "$":
                            continue
                        elif "*iga" in line.lower():
                            svector = line.split(",")

                            # 필수 파라미터
                            source_pid = int(svector[1])
                            iga_id = int(svector[2])
                            output_file = svector[3]

                            # 선택 파라미터 (디폴트)
                            rr = float(svector[4]) if len(svector) > 4 else 0.6
                            rs = float(svector[5]) if len(svector) > 5 else 0.6
                            rt = float(svector[6]) if len(svector) > 6 else 0.6
                            ratio = float(svector[7]) if len(svector) > 7 else 1.1
                            ir = int(svector[8]) if len(svector) > 8 else 0

                            iga_config = {
                                'source_pid': source_pid,
                                'iga_id': iga_id,
                                'output_file': output_file,
                                'element_edge_length': {'rr': rr, 'rs': rs, 'rt': rt},
                                'bbox_offset_ratio': ratio,
                                'integration_rule': ir
                            }

                            curOptions["IGAParts"].append(iga_config)
                        else:
                            print(f"Invalid option in FEMtoIGA: {line}")
                            exit()

                    self.modeIDOption[curModeID] = curOptions


                line = f.readline()
                if not line:  # EOF
                    break
                line = line.replace('\n','')
                line = line.strip()
                if not line:  # Empty line, skip it
                    continue

    def GenerateRemoveDuplicateTiedContacts(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.RemoveDuplicateTiedContacts(curOption)
                
    def GenerateWeakCoupling(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.WeakCoupling(curOption)
    
    def GenerateDefeatureMesh(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.DefeatureMesh(curOption)    
        
    def GenerateDropAttitude(self, modeid):
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        
        curOption = self.modeIDOption[modeid]
        self.advancedModification.DropAttitude(curOption, filePath)
    
    def GenerateDropWeightImpactTest(self, modeid):
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        
        curOption = self.modeIDOption[modeid]
        #DampingSpring, OutsideRigidPart, OutsideRigidElement
        if curOption["Mode"] == "DampingSpring":
            self.advancedModification.DropWeightImpactTest(curOption, filePath)
        elif curOption["Mode"] == "OutsideRigidElement" or curOption["Mode"] == "OutsideRigidPart":
            self.advancedModification.DropWeightImpactTestwithPartialRigid(curOption, filePath)
        elif curOption["Mode"] == "Part":
            self.advancedModification.DropWeightImpactTestbyPart(curOption, filePath)

    def GenerateTranslationDOE(self, modeid):
        curOption = self.modeIDOption[modeid]
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        self.advancedModification.TranslationDOE(curOption, filePath)
    
    def Transform(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.Transform(curOption)
        
    def GenerateElasticToRigid(self, modeid):                      
        
        curOption = self.modeIDOption[modeid]
        curPIDExcept = curOption["PIDExcept"]
        curMIDExcept = [] 
        for pid in curPIDExcept:
            if pid not in self.dynaImporter.partManager.parts:
                continue            
            part = self.dynaImporter.partManager.parts[pid] 
            if part.mid != 0:
                curMIDExcept.append(part.mid)
            
        self.dynaImporter.matManager.ExchangetoRigid(curMIDExcept)     
        self.dynaImporter.partManager.UpdateMaterial(self.dynaImporter.matManager)   
        self.dynaImporter.constrainedManager.GenerageConstraintforAllRigidBodies(self.dynaImporter.partManager, 1)
        
    
    def GenerateMaterialExchange(self, modeid):
        curOption = self.modeIDOption[modeid]
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        
        self.advancedModification.MaterialExchange(curOption, filePath)
    
    def GeneratePartLocationDOE(self, modeid):
        curOption = self.modeIDOption[modeid]
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        
        self.advancedModification.PartLocationDOE(curOption, filePath)
    
    def GenerateErodingMinDT(self, modeid):
        curOption = self.modeIDOption[modeid]
        dt = curOption["DT"]
        self.advancedModification.ErodingMinDT(dt)
    
    def GenerateConstrainedNodalRigidBodyToBeam(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ConstrainedNodalRigidBodyToBeam(curOption)
   
    def GenerateWarpedPart(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.WarpedPart(curOption)
    
    def GenerateWarpedtoInitialStressPart(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.WarpedtoInitialStressPart(curOption)
   
    def GenerateDimensionalTolerance(self, modeid):
        curOption = self.modeIDOption[modeid]
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        self.advancedModification.DimensionalTolerance(curOption,filePath)

    def GenerateCohesiveBetweenConformalMeshes(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.CohesiveBetweenConformalMeshes(curOption)

    def GenerateContactAutoDecomposition(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ContactAutoDecomposition(curOption)

    def GenerateSimulationAutomation(self, modeid):
        curOption = self.modeIDOption[modeid]

        inputFile = self.inputFileName
        inputObjFile = self.inputObjFileName
        jsonPath = os.path.join(self.curDir, curOption["JsonFile"])
        jsonOption = self.LoadScenariosJson(jsonPath)
        metaData = curOption["MetaData"]
        if inputFile is not None:
            for i in range(len(jsonOption)):
                jsonOption[i]["fileName"] = inputFile
                
        self.advancedModification.SimulationAutomation(jsonOption, inputFile, inputObjFile, metaData)

    def GenerateDynainToInitial(self, modeid):
        curOption = self.modeIDOption[modeid]
        folderPath = self.curDir
        filePath = os.path.join(folderPath, "dynain")
        self.advancedModification.DynaintoInitial(curOption, folderPath, filePath)

    def GenerateFEMtoIGA(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.FEMtoIGA(curOption)

    def GeneratePartMorphing(self, modeid):
        curOption = self.modeIDOption[modeid]["Morph"]
        unitscale = self.modeIDOption[modeid]["UnitScale"]
        meshSize = self.modeIDOption[modeid]["MeshSize"]
        generateMesh = self.modeIDOption[modeid]["GenerateMesh"]
        subOption = {}
        subOption["UnitScale"] = unitscale
        subOption["MeshSize"] = meshSize
        subOption["GenerateMesh"] = generateMesh
        self.advancedModification.PartMorphing(curOption, subOption)
    
    def GeneratePartExchange(self, modeid):
        curOption = self.modeIDOption[modeid]
        curPID = 0 
        part = None 
        section = None
        mat = None
        convertHexaToOption = None
        convertUnstrToStrOption = None
        thks = None
        mats = None
        numes = None
        eoss = None
        hgids = None        
        layup = None
        partComp = None
        curPIDs = []
        layerThicknesList = []  
        for optionid in curOption:
            curKeyword = curOption[optionid]                                    
            
            if "pids" in optionid.lower():
                curPIDs = curKeyword
            elif "pid" in optionid.lower():
                curPID = curKeyword
                if curPID in self.dynaImporter.partManager.parts:
                    part = self.dynaImporter.partManager.parts[curPID]    
            elif "converthexato" in optionid.lower():
                convertHexaToOption = curKeyword
            elif "unstructuredtostructured" in optionid.lower():
                convertUnstrToStrOption = curKeyword
            elif "layerthickness" in optionid.lower():
                layerThicknesList = curKeyword
            elif "thk" in optionid.lower():
                thks = curKeyword
            elif "nume" in optionid.lower():
                numes = curKeyword
            elif "mids" in optionid.lower():
                mats = curKeyword
            elif "eos" in optionid.lower():
                eoss = curKeyword
            elif "hgid" in optionid.lower():
                hgids = curKeyword
            elif "layup" in optionid.lower():
                layup = curKeyword
            elif "*part_composite" in optionid.lower():
                partComp = curKeyword
            elif type(curKeyword) == list:
                if len(curKeyword) == 0:
                    continue
                elif type(curKeyword[0]) == str:
                    if "*section" in curKeyword[0].lower():
                        section = self.dynaImporter.sectionManager.AddSectionfromDyna(curKeyword)            
                    elif "*mat" in curKeyword[0].lower():
                        mat = self.dynaImporter.matManager.AddMaterialfromDyna(curKeyword)
                    elif "*part" in curKeyword[0].lower():
                        pass
            
        
        if part is not None:
            if section is not None:
                part.section = section
                print("Section is added")
            else:
                print("Invalid section ID")
            if mat is not None:
                part.mid = mat.id
            else:
                print("Invalid material ID")
        else:
            print("Invalid part ID")
            
        
        mattoid = {}
        for matid in mats:
            newMat = self.dynaImporter.matManager.AddMaterialfromDyna(mats[matid])
            mattoid[matid] = newMat.id
        eostoid = {}
        for eosid in eoss: 
            newEos = self.dynaImporter.matManager.AddEOSfromDyna(eoss[eosid])
            eostoid[eosid] = newEos.id
        hgtoid = {}
        for hgid in hgids:
            newHg = self.dynaImporter.additionalManager.SetAdditionalfromDyna(hgids[hgid])
            hgtoid[hgid] = newHg.id
                    
                    
        if part is not None and partComp is not None:
            for i in range(1,len(partComp)):
                for j in range(len(partComp[i])):
                    if "PID" in partComp[i][j]:
                        partComp[i][j] = str(curPID)
                    for thkid in thks:
                        if thkid in partComp[i][j]:
                            partComp[i][j] = str(thks[thkid])
                    for matid in mattoid:
                        if matid in partComp[i][j]:
                            partComp[i][j] = str(mattoid[matid])
            part = self.advancedModification.ConvertParttoPartComp(partComp)
            if convertHexaToOption is not None:
                if convertHexaToOption["Type"].lower() == "tshell":
                    part.SetTShellMode(True) 
        
        layupList = []
        if layup is not None:
            for thkid in thks:
                layup = layup.replace(thkid, str(thks[thkid]))
            for matid in mattoid:
                layup = layup.replace(matid, str(mattoid[matid]))
            for eosid in eostoid:
                layup = layup.replace(eosid, str(eostoid[eosid]))
            for hgid in hgtoid:
                layup = layup.replace(hgid, str(hgtoid[hgid]))
            for numeid in numes:
                layup = layup.replace(numeid, str(numes[numeid]))
            if part is not None:
                layup = layup.replace("EOS",format(part.eosid,">10"))
                layup = layup.replace("HGID",format(part.hgid,">10"))
            layupVec = layup.split("\n")        
            
            for layupValue in layupVec:
                curVec = layupValue.split(",")
                if len(curVec) < 4:
                    continue
                else:
                    layupList.append(curVec)
        
        if part is not None and convertHexaToOption is not None:
            convertHexaToOption["PID"] = curPID            
            self.ConvertHexato(convertHexaToOption,layupList,curOption)    
        if len(curPIDs)>0 and convertUnstrToStrOption is not None:
            convertUnstrToStrOption["PIDS"] = curPIDs
            if len(layerThicknesList) == 0:
                self.ConvertUnstructuredtoStructuredPrev(convertUnstrToStrOption)
            else:
                convertUnstrToStrOption["LayerThickness"] = layerThicknesList
                self.ConvertUnstructuredtoStructured(convertUnstrToStrOption)
        
    def ConvertHexato(self, option,layupList = [], curOption = None):
        if option is None:
            return 
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        
        self.advancedModification.ConvertHexato(option,layupList,curOption,filePath)
        
    def ConvertUnstructuredtoStructuredPrev(self, option):
        if option is None:
            return
        self.advancedModification.ConvertUnstructuredtoStructuredPrev(option)
    
    def ConvertUnstructuredtoStructured(self, option):
        if option is None:
            return
        self.advancedModification.ConvertUnstructuredtoStructured(option) 
    
    def GenerateModifiedFile(self):
        additionalword = ""
        for i in range(len(self.modeList)):
            mode = self.modeList[i]
            modeid = self.modeIDList[i]
            if mode == "ELASTIC_TO_RIGID":
                self.GenerateElasticToRigid(modeid)
                additionalword += "_etor"
            elif mode == "MATERIAL_EXCHANGE":
                self.GenerateMaterialExchange(modeid)
                additionalword += "_mex"
            elif mode == "PART_LOCATION_DOE":
                self.GeneratePartLocationDOE(modeid)
                additionalword += "_pld"
            elif mode == "ERODING_MIN_DT":
                self.GenerateErodingMinDT(modeid)
                additionalword += "_emdt"
            elif mode == "PART_EXCHANGE":
                self.GeneratePartExchange(modeid)
                additionalword += "_pex"
            elif mode == "REMOVE_DUPLICATE_TIED_CONTACTS":
                self.GenerateRemoveDuplicateTiedContacts(modeid)
                additionalword += "_rdc"
            elif mode == "WEAK_COUPLING":
                self.GenerateWeakCoupling(modeid)
                additionalword += "_wc"
            elif mode == "DEFEATURE_MESH":
                self.GenerateDefeatureMesh(modeid)
                additionalword += "_def"
            elif mode == "DROP_ATTITUDE":
                self.GenerateDropAttitude(modeid)
                additionalword += "_drop"
            elif mode == "TRANSLATION_DOE":
                self.GenerateTranslationDOE(modeid)
                additionalword += "_trans"
            elif mode == "TRANSFORM":
                self.Transform(modeid)
                additionalword += "_trans"
            elif mode == "DROP_WEIGHT_IMPACT_TEST":
                self.GenerateDropWeightImpactTest(modeid)
                additionalword += "_dwit"
            elif mode == "PART_MORPHING":
                self.GeneratePartMorphing(modeid)
                additionalword += "_pm"            
            elif mode == "CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM":
                self.GenerateConstrainedNodalRigidBodyToBeam(modeid)
                additionalword += "_crb"
            elif mode == "WARPED_PART":
                self.GenerateWarpedPart(modeid)
                additionalword += "_warp"
            elif mode == "WARPED_TO_INITIAL_STRESS_PART":
                self.GenerateWarpedtoInitialStressPart(modeid)
                additionalword += "_w2is"
            elif mode == "DIMENSIONAL_TOLERANCE":
                self.GenerateDimensionalTolerance(modeid)
                additionalword += "_dt"
            elif mode == "COHESIVE_BETWEEN_CONFORMAL_MESHES":
                self.GenerateCohesiveBetweenConformalMeshes(modeid)
                additionalword += "_cbcm"
            elif mode == "DYNAIN_TO_INITIAL":
                self.GenerateDynainToInitial(modeid)
                additionalword += "_dti"
            elif mode == "CONTACT_AUTO_DECOMPOSITION":
                self.GenerateContactAutoDecomposition(modeid)
                additionalword += "_cad"
            elif mode == "SIMULATION_AUTOMATION":
                self.GenerateSimulationAutomation(modeid)
                additionalword += "_sa"
            elif mode == "FEM_TO_IGA":
                self.GenerateFEMtoIGA(modeid)
                additionalword += "_iga"

            self.dynaImporter.SyncronizeMaxID()
        ## write modified File
        import time 
        print("Write LS-Dyna Modified File")
        starttime = time.time()
        self.WriteModifiedFile(additionalword)
        endtime = time.time()
        print("Time : ", endtime - starttime)
        print("Complete")
         
        '''print("Write Nastran Modified File") 
        starttime = time.time()       
        self.WriteNastranModifiedFile(additionalword)
        endtime = time.time()
        print("Time : ", endtime - starttime)
        print("Complete")'''
        '''print("Write Abaqus Modified File")
        starttime = time.time()
        self.WriteAbaqusModifiedFile(additionalword)
        endtime = time.time()
        print("Time : ", endtime - starttime)
        print("Complete")'''
        
    def WriteModifiedFile(self, modifiedKeyword):

        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        filePath = filePath + modifiedKeyword + ".k"
        with open(filePath, "w") as f:
            f.write("*KEYWORD\n")
            f.write(self.dynaImporter.WriteStreamDynaKeyword())

            # IGA Include 문 추가
            if len(self.dynaImporter.partManager.igaParts) > 0:
                self.dynaImporter.partManager.WriteIGAIncludes(f)

            f.write("*END\n")
            
    
    def WriteNastranModifiedFile(self, modifiedKeyword):
        
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        filePath = filePath + modifiedKeyword + ".bdf"
        with open(filePath, "w") as f:
            f.write(self.dynaImporter.WriteStreamNastranKeyword())    
        
    def WriteAbaqusModifiedFile(self, modifiedKeyword):
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k","")
        filePath = filePath + modifiedKeyword + ".inp"
        with open(filePath, "w") as f:
            f.write(self.dynaImporter.WriteStreamAbaqusKeyword())
        

class DualOutput:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for s in self.streams:
            s.write(message)
            s.flush()  # 버퍼 비우기

    def flush(self):
        for s in self.streams:
            s.flush()
               
if __name__ == "__main__":
    
    if len(sys.argv) == 1:
        mode = "apptainer"
        mode = "local"
        if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/"
        # ELASTIC_TO_RIGID
        #optionName = "ElasticToRigidOption.txt"
        #optionName = "SolidtoShellOption.txt"
        #optionName = "UnstructuredtoStructured.txt"
        #optionName = "UnstructuredtoStructuredLayered.txt"
        #optionName = "Defeature.txt"
        #optionName = "DropAttitude.txt"
        #optionName = "DropAttitudeMacroscale.txt"
        #optionName = "WeakCoupling.txt"
        #optionName = "Transform.txt"
        #optionName = 'DropAttitudeRoughness.txt'
        #optionName = 'DropAttitudeCurve.txt'
        #optionName = 'DropAttitudeRoughnessSin.txt'
        #optionName = "DropWeightImpactTest.txt"
        #optionName = "DropWeightImpactTestCylinder.txt"
        #optionName = "DropWeightImpactTest_OutsideRigidElements.txt"
        #optionName = "DropWeightImpactTestbyPart.txt"
        #optionName = "MaterialExchange.txt"
        #optionName = "SolidtoSolidComposite_PS.txt"
        #optionName = "SolidtoTShell.txt"
        if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\DynamicRelaxation"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/DynamicRelaxation/"
        optionName = "drop_attitude.txt"
        #optionName = "DynainToInitial.txt"
        #optionName = "DynainToInitial_dti.txt"
        
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\ContactAutoDecomposition"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/ContactAutoDecomposition/"'''
        #optionName = "ContactAutoDecomposition.txt"
        # 끝면을 통한 FPCB 단차 생성
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\ConnectorGeneration\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/ConnectorGeneration/"'''
        #optionName = "SolidtoSolidwithSlack.txt"
        #optionName = "SolidStructuredZSlack.txt"
        
        
        ### Part Morphing
        '''if sys.platform.startswith("win"):           
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\Morph\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/Morph/"'''
        #optionName = "PartMorph.txt"
        #optionName = "PartMorphNoRemesh.txt"
        #optionName = "PartMorphNoRemeshPIDBox.txt"
        #optionName = "PartMorphTest.txt"
        #
        ### Warped Part
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\WarpedPart\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/WarpedPart/"'''
        #optionName = "WarpedPart.txt"
        
        ### Warped to Initial Stress Part
        ### dynamic relaxation을 통한 초기 응력 생성
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\WarpedtoInitialStressPart\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/WarpedtoInitialStressPart/"'''
        #optionName = "WarpedtoInitialStressPart.txt"
        #optionName = "WarpedtoInitialStressPartTopBottom.txt"
        #optionName = "WarpedtoInitialStressPartWarpedTied.txt"
        
        ### Dimensional Tolerance 
        ### dynamic relaxation을 통한 초기 두께 산포의 생성  
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\DimensionalTolerance\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/DimensionalTolerance/"'''
        #optionName = "DimensionalTolerance.txt"
        #optionName = "DimensionalTolerance_norm_dist.txt"
        #optionName = "DimensionalTolerance_LHS.txt"

        ### Cohesive Between Conformal Meshes
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\CohesiveBetweenConformalMeshes\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/CohesiveBetweenConformalMeshes/"'''
        #optionName = "CohesiveBetweenConformalMeshes.txt"
        
        
        ### Dynain to Initial 
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\DynaintoInitial\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/DynaintoInitial/"'''
        
        #optionName = "DynainToInitial.txt"

        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\Eroding_Dtmin\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/Eroding_Dtmin/"'''
        #curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\Eroding_Dtmin\\"
        #optionName = "Eroding_Dtmin.txt"
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\PartLocationDOE\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/PartLocationDOE/"'''
        #curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\PartLocationDOE\\"
        #optionName = "PartLocationDOE.txt"
        '''if sys.platform.startswith("win"):
            curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\ConstrainedNodalRigidbodytoBeam\\"
        else:
            curDir = "/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/ConstrainedNodalRigidbodytoBeam/"'''
        #curDir = "D:\\pyKooCAE\\occProject\\Generators\\dist\\Examples\\5.SimulationModify\\ConstrainedNodalRigidbodytoBeam\\"
        #optionName = "ConstrainedNodalRigidBodytoBeam.txt"

        '''if mode == "local":            
            curDir = "/home/koopark/claude/pyKooCAE/Examples/alldropangles"
            optionName = "simulation_automation.txt"'''
          

    elif len(sys.argv) == 2:        
        optionName = sys.argv[1]
        curDir = os.path.curdir
    elif len(sys.argv) == 3:
        optionName = sys.argv[1]
        curDir = sys.argv[2]
    
    
    logfileName = optionName.replace(".txt", ".log")
    logfileName = os.path.join(curDir, logfileName)
    with open(logfileName, "w") as logFile:
        sys.stdout = DualOutput(sys.__stdout__, logFile)
        print("Start")
        print("Current Directory : ", curDir)   
        print("Option Name : ", optionName)    
        simGenerator : KooMeshModifier = KooMeshModifier()    
        
        simGenerator.SetCurrentDirectory(curDir)
        print("Import Option")
        simGenerator.ImportOption(optionName)    
        print("Import Base File")
        simGenerator.ImportBaseFile()
        simGenerator.GenerateMetaData()
        print("Generate Modified File")
        simGenerator.GenerateModifiedFile()        
        print("Done")
        sys.stdout = sys.__stdout__  # stdout 복원