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
                if "*preserveincludes" in line.lower():
                    # *PreserveIncludes 블록: 다음 줄들에 패턴 (basename glob 또는 절대경로)
                    # 종료 조건: 다음 *키워드 또는 빈 줄 다음 *키워드
                    patterns = []
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if line.startswith('*'):
                            break
                        if not line or line.startswith('$'):
                            continue
                        # 한 줄에 여러 패턴 지원 (콤마 구분)
                        for tok in line.split(','):
                            tok = tok.strip()
                            if tok:
                                patterns.append(tok)
                    if patterns:
                        try:
                            self.dynaImporter.dynaManager._preserve_include_patterns = patterns
                            print(f"[PreserveIncludes] {len(patterns)} pattern(s) registered: {patterns}")
                        except AttributeError:
                            print(f"[PreserveIncludes] Warning: dynaManager not ready, patterns will be applied later: {patterns}")
                            self._pending_preserve_patterns = patterns
                    # *키워드를 만나서 종료된 경우 그 줄을 다음 루프로 넘기기 위해 continue 대신 처리 필요
                    # readline으로 한 줄 더 안 읽도록 — 현재 line 변수가 *키워드를 가리킴
                    # 그 *키워드를 다음 분기에서 처리해야 하므로 continue
                    continue
                if "*mode" in line.lower():
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if "*" in line:
                            break
                        if not line:  # Skip empty lines
                            continue
                        svector = line.split(",")                    
                        if "part_validation_split" in svector[0].lower():
                            self.modeList.append("PART_VALIDATION_SPLIT")
                            self.modeIDList.append(int(svector[1]))
                        elif "elastic_to_rigid" in svector[0].lower():
                            self.modeList.append("ELASTIC_TO_RIGID")
                            self.modeIDList.append(int(svector[1]))                        
                        elif "material_exchange" in svector[0].lower():
                            self.modeList.append("MATERIAL_EXCHANGE")
                            self.modeIDList.append(int(svector[1]))
                        elif "part_location_doe" in svector[0].lower():
                            self.modeList.append("PART_LOCATION_DOE")
                            self.modeIDList.append(int(svector[1]))
                        elif "remesh_tetra" in svector[0].lower():
                            self.modeList.append("REMESH_TETRA")
                            self.modeIDList.append(int(svector[1]))
                        elif "rigidify_small_dt" in svector[0].lower():
                            self.modeList.append("RIGIDIFY_SMALL_DT")
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
                        elif "convert_cnrb_to_solid" in svector[0].lower():
                            self.modeList.append("CONVERT_CNRB_TO_SOLID")
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
                        elif "decompose_k" in svector[0].lower():
                            self.modeList.append("DECOMPOSE_K")
                            self.modeIDList.append(int(svector[1]))
                        elif "vibration_load" in svector[0].lower():
                            self.modeList.append("VIBRATION_LOAD")
                            self.modeIDList.append(int(svector[1]))
                        elif "thermal_load" in svector[0].lower():
                            self.modeList.append("THERMAL_LOAD")
                            self.modeIDList.append(int(svector[1]))
                        elif "import_merge_k" in svector[0].lower():
                            # import_merge_k를 merge_k보다 먼저 체크 (substring 충돌 방지)
                            self.modeList.append("IMPORT_MERGE_K")
                            self.modeIDList.append(int(svector[1]))
                        elif "merge_k" in svector[0].lower():
                            self.modeList.append("MERGE_K")
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
                    curOptions["DynamicRelaxationNrcyck"] = 0
                    curOptions["DynamicRelaxationTol"] = 0.0
                    curOptions["DynamicRelaxationFctr"] = 0.0
                    curOptions["DynamicRelaxationTerm"] = 0.0
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
                        elif "dynamicrelaxationnrcyck" in line.lower():
                            svector = line.split(",")
                            curOptions["DynamicRelaxationNrcyck"] = int(float(svector[1]))
                        elif "dynamicrelaxationtol" in line.lower():
                            svector = line.split(",")
                            curOptions["DynamicRelaxationTol"] = KooDynaFloat(svector[1])
                        elif "dynamicrelaxationfctr" in line.lower():
                            svector = line.split(",")
                            curOptions["DynamicRelaxationFctr"] = KooDynaFloat(svector[1])
                        elif "dynamicrelaxationterm" in line.lower():
                            # 주의: 세부키들은 "dynamicrelaxation" 브랜치보다 먼저 와야 함(substring 포함)
                            svector = line.split(",")
                            curOptions["DynamicRelaxationTerm"] = KooDynaFloat(svector[1])
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

                elif "**convertcnrbtosolid" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["ALL"] = True
                    curOptions["CNRB_IDs"] = []
                    curOptions["E"] = 200000000000
                    curOptions["PR"] = 0.3
                    curOptions["RHO"] = 7850
                    curOptions["RadiusScale"] = 0.999
                    curOptions["NumCircumNodes"] = 0
                    curOptions["AxisDirection"] = "Auto"
                    curOptions["InnerRadiusRatio"] = 0.3
                    curOptions["ZTolerance"] = 0.01
                    curOptions["RTolerance"] = 0.5
                    while True:
                        line = f.readline().strip()
                        line = line.replace('\n','')
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "all" in line.lower():
                            svector = line.split(",")
                            curOptions["ALL"] = svector[1].strip().lower() != "false"
                        elif "cnrb_ids" in line.lower():
                            svector = line.split(",")
                            curOptions["CNRB_IDs"] = [int(x.strip()) for x in svector[1:] if x.strip()]
                        elif line.lower().startswith("e,"):
                            svector = line.split(",")
                            curOptions["E"] = KooDynaFloat(svector[1])
                        elif "pr," in line.lower():
                            svector = line.split(",")
                            curOptions["PR"] = KooDynaFloat(svector[1])
                        elif "rho," in line.lower():
                            svector = line.split(",")
                            curOptions["RHO"] = KooDynaFloat(svector[1])
                        elif "radiusscale" in line.lower():
                            svector = line.split(",")
                            curOptions["RadiusScale"] = KooDynaFloat(svector[1])
                        elif "numcircumnodes" in line.lower():
                            svector = line.split(",")
                            curOptions["NumCircumNodes"] = KooDynaInt(svector[1])
                        elif "axisdirection" in line.lower():
                            svector = line.split(",")
                            curOptions["AxisDirection"] = svector[1].strip()
                        elif "innerradiusratio" in line.lower():
                            svector = line.split(",")
                            curOptions["InnerRadiusRatio"] = KooDynaFloat(svector[1])
                        elif "ztolerance" in line.lower():
                            svector = line.split(",")
                            curOptions["ZTolerance"] = KooDynaFloat(svector[1])
                        elif "rtolerance" in line.lower():
                            svector = line.split(",")
                            curOptions["RTolerance"] = KooDynaFloat(svector[1])

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
                    curOptions["DynainDynamicRelaxation"] = False
                    curOptions["DynainDynamicRelaxationNrcyck"] = 0
                    curOptions["DynainDynamicRelaxationTol"] = 0.0
                    curOptions["DynainDynamicRelaxationFctr"] = 0.0
                    curOptions["DynainDynamicRelaxationTerm"] = 0.0
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
                        elif "youngsmodulusimpactormid" in line.lower():
                            curOptions["YoungsModulusImpactorMid"] = KooDynaFloat(line.split(",")[1])
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
                        elif "poissonratioimpactormid" in line.lower():
                            curOptions["PoissonRatioImpactorMid"] = KooDynaFloat(line.split(",")[1])
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
                        elif "materialidimpactormid" in line.lower():
                            curOptions["MaterialIDImpactorMid"] = KooDynaInt(line.split(",")[1])
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
                        elif "densityimpactormid" in line.lower():
                            curOptions["DensityImpactorMid"] = KooDynaFloat(line.split(",")[1])
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
                        elif "dynaindynamicrelaxationnrcyck" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationNrcyck"] = int(float(svector[1]))
                        elif "dynaindynamicrelaxationtol" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationTol"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxationfctr" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationFctr"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxationterm" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationTerm"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxation" in line.lower():
                            # 주의: 위 세부키들이 이 generic 브랜치보다 먼저 와야 함(substring)
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxation"] = svector[1].strip().lower() == "true"
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
                                # 2단(5값): radius,outerRadius,hFront,hBack,backRadius
                                # 3단(7값): radius,outerRadius,hFront,midRadius,hMid,backRadius,hBack
                                vals = [KooDynaFloat(svector[k]) for k in range(1, len(svector))]
                                if len(vals) >= 7:
                                    curOptions["Dimension"] = vals[:7]   # 3단
                                elif len(vals) >= 5:
                                    curOptions["Dimension"] = vals[:5]   # 2단
                                elif len(vals) == 4:
                                    curOptions["Dimension"] = vals + [vals[1]]  # v5=v2 보정 (기존 호환)
                                else:
                                    curOptions["Dimension"] = vals
                        elif "wallnumx" in line.lower():
                            curOptions["WallNumX"] = KooDynaInt(line.split(",")[1])
                        elif "wallnumy" in line.lower():
                            curOptions["WallNumY"] = KooDynaInt(line.split(",")[1])
                        elif "wallnumz" in line.lower():
                            curOptions["WallNumZ"] = KooDynaInt(line.split(",")[1])
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
                                curOptions["Translation"][pid] = {}
                                # add 0 list for y and z
                                curOptions["Translation"][pid]["Y"] = [0.0] * len(transXList)
                                curOptions["Translation"][pid]["Z"] = [0.0] * len(transXList)

                            curOptions["Translation"][pid]["X"] = transXList
                        if "translationy" in line.lower():
                            pid = int(line.split(",")[1])
                            svector = line.split(",")[2:]
                            transYList = [KooDynaFloat(x) for x in svector]
                            if pid not in curOptions["Translation"]:
                                curOptions["Translation"][pid] = {}
                                # add 0 list for x and z
                                curOptions["Translation"][pid]["X"] = [0.0] * len(transYList)
                                curOptions["Translation"][pid]["Z"] = [0.0] * len(transYList)
                            curOptions["Translation"][pid]["Y"] = transYList
                        if "translationz" in line.lower():
                            pid = int(line.split(",")[1])
                            svector = line.split(",")[2:]
                            transZList = [KooDynaFloat(x) for x in svector]
                            if pid not in curOptions["Translation"]:
                                curOptions["Translation"][pid] = {}
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
                    curOptions["DeformableToRigid"] = False
                    curOptions["DynainDynamicRelaxation"] = False
                    curOptions["DynainDynamicRelaxationNrcyck"] = 0
                    curOptions["DynainDynamicRelaxationTol"] = 0.0
                    curOptions["DynainDynamicRelaxationFctr"] = 0.0
                    curOptions["DynainDynamicRelaxationTerm"] = 0.0
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
                        elif "dtmin" in line.lower():
                            # CONTROL_TERMINATION DTMIN (발산 dt붕괴 시 자동종료).
                            # "dt" 검사보다 먼저 와야 dtmin 이 dt 로 오인되지 않음.
                            svector = line.split(",")
                            curOptions["DTMIN"] = KooDynaFloat(svector[1])
                        elif "controltimestep." in line.lower():
                            # *CONTROL_TIMESTEP override (TSSFAC/DT2MS/ERODE 등).
                            # "dt" 검사보다 먼저 와야 DT2MS 등이 dt로 오인되지 않음.
                            key = line.split(",")[0].split(".")[1].strip()
                            val = line.split(",")[1].strip()
                            if "ControlTimestep" not in curOptions:
                                curOptions["ControlTimestep"] = {}
                            try:
                                curOptions["ControlTimestep"][key] = float(val)
                            except ValueError:
                                curOptions["ControlTimestep"][key] = val
                        elif "controlhourglass." in line.lower():
                            # *CONTROL_HOURGLASS override (IHQ/QH)
                            key = line.split(",")[0].split(".")[1].strip()
                            val = line.split(",")[1].strip()
                            if "ControlHourglass" not in curOptions:
                                curOptions["ControlHourglass"] = {}
                            try:
                                curOptions["ControlHourglass"][key] = float(val)
                            except ValueError:
                                curOptions["ControlHourglass"][key] = val
                        elif "dt" in line.lower():
                            svector = line.split(",")
                            dt = KooDynaFloat(svector[1])
                            curOptions["DT"] = dt
                        elif "dropsurface" in line.lower():
                            svector = line.split(",")
                            dropSurface = svector[1].strip()
                            if dropSurface.lower() == "rigidwall":
                                curOptions["DropSurface"] = ["RigidWall"]
                            elif dropSurface.lower() == "plane":
                                xLength = KooDynaFloat(svector[2])
                                yLength = KooDynaFloat(svector[3])
                                zLength = KooDynaFloat(svector[4])
                                
                                numX = KooDynaInt(svector[5])
                                numY = KooDynaInt(svector[6])
                                numZ = KooDynaInt(svector[7])
                                curOptions["DropSurface"] = ["Plane", xLength, yLength, zLength, numX, numY, numZ]
                                                                
                            elif dropSurface.lower() == "planegraded":
                                # PlaneGraded,innerX,innerY,zLength,numInnerX,numInnerY,numZ,numOuterLayers,ratio
                                innerXLength = KooDynaFloat(svector[2])
                                innerYLength = KooDynaFloat(svector[3])
                                zLength = KooDynaFloat(svector[4])
                                numInnerX = KooDynaInt(svector[5])
                                numInnerY = KooDynaInt(svector[6])
                                numZ = KooDynaInt(svector[7])
                                numOuterLayers = KooDynaInt(svector[8]) if len(svector) > 8 else 5
                                ratio = KooDynaFloat(svector[9]) if len(svector) > 9 else 1.5
                                curOptions["DropSurface"] = ["PlaneGraded", innerXLength, innerYLength, zLength, numInnerX, numInnerY, numZ, numOuterLayers, ratio]
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
                        elif "deformabletorigid" in line.lower():
                            svector = line.split(",")
                            curOptions["DeformableToRigid"] = svector[1].strip().lower() == "true"
                        elif "dynaindynamicrelaxationnrcyck" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationNrcyck"] = int(float(svector[1]))
                        elif "dynaindynamicrelaxationtol" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationTol"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxationfctr" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationFctr"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxationterm" in line.lower():
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxationTerm"] = KooDynaFloat(svector[1])
                        elif "dynaindynamicrelaxation" in line.lower():
                            # 주의: 위 세부키들이 이 generic 브랜치보다 먼저 와야 함(substring)
                            svector = line.split(",")
                            curOptions["DynainDynamicRelaxation"] = svector[1].strip().lower() == "true"
                        elif "nonreflectingboundary" in line.lower():
                            svector = line.split(",")
                            curOptions["NonReflectingBoundary"] = svector[1].strip().lower() != "false"
                        elif "includewallingeneral" in line.lower():
                            svector = line.split(",")
                            curOptions["IncludeWallInGeneral"] = svector[1].strip().lower() != "false"
                        elif "rigifysmalldtthreshold" in line.lower() or "rigidifysmalldtthreshold" in line.lower():
                            svector = line.split(",")
                            curOptions["RigidifySmallDtThreshold"] = KooDynaFloat(svector[1])
                        elif "rigidifymaxaspectratio" in line.lower():
                            svector = line.split(",")
                            curOptions["RigidifyMaxAspectRatio"] = KooDynaFloat(svector[1])
                        elif "rigidifyelementids" in line.lower():
                            svector = line.split(",")
                            eids = [int(svector[i]) for i in range(1, len(svector))]
                            curOptions["RigidifyElementIDs"] = eids
                        elif "robustcontacttolerance" in line.lower():
                            svector = line.split(",")
                            curOptions["RobustContactTolerance"] = KooDynaFloat(svector[1])
                        elif "robustcontact" in line.lower():
                            svector = line.split(",")
                            curOptions["RobustContact"] = svector[1].strip().lower() != "false"
                        elif "ensuresinglesurface" in line.lower():
                            svector = line.split(",")
                            curOptions["EnsureSingleSurface"] = svector[1].strip().lower() != "false"
                        elif "convertgeneraltosinglesurf" in line.lower():
                            svector = line.split(",")
                            curOptions["ConvertGeneralToSingleSurface"] = svector[1].strip().lower() != "false"
                        elif "decomposegeneralcontact" in line.lower():
                            svector = line.split(",")
                            curOptions["DecomposeGeneralContact"] = svector[1].strip().lower() != "false"
                        elif "decomposecontactmargin" in line.lower():
                            svector = line.split(",")
                            curOptions["DecomposeContactMargin"] = float(svector[1].strip())
                        elif "decomposecontactabsolutemarginx" in line.lower():
                            svector = line.split(",")
                            curOptions["DecomposeContactAbsoluteMarginX"] = float(svector[1].strip())
                        elif "decomposecontactabsolutemarginy" in line.lower():
                            svector = line.split(",")
                            curOptions["DecomposeContactAbsoluteMarginY"] = float(svector[1].strip())
                        elif "decomposecontactabsolutemarginz" in line.lower():
                            svector = line.split(",")
                            curOptions["DecomposeContactAbsoluteMarginZ"] = float(svector[1].strip())
                        elif "dropcontact." in line.lower():
                            svector = line.split(",")
                            key = svector[0].split(".")[1].strip()
                            val = svector[1].strip()
                            if "DropContact" not in curOptions:
                                curOptions["DropContact"] = {}
                            try:
                                curOptions["DropContact"][key] = float(val)
                            except ValueError:
                                curOptions["DropContact"][key] = val
                        elif "tiedoptions." in line.lower():
                            svector = line.split(",")
                            key = svector[0].split(".")[1].strip()
                            val = svector[1].strip()
                            if "TiedOptions" not in curOptions:
                                curOptions["TiedOptions"] = {}
                            key_lower = key.lower()
                            # Boolean 필드
                            if key_lower == "converttosegment":
                                curOptions["TiedOptions"]["ConvertToSegment"] = val.lower() != "false"
                            else:
                                # 숫자 필드 (LS-DYNA contact card 전체 + 제어 옵션)
                                try:
                                    curOptions["TiedOptions"][key] = float(val)
                                except ValueError:
                                    curOptions["TiedOptions"][key] = val

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
                            # 각 *mid 블록을 고유 MID id 키로 저장 (다중 블록 누적; 과거엔
                            # 루프 밖 단일 저장이라 마지막 블록만 남았음)
                            curOptions["MIDs"][curKeywordName] = curKeyword
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
                elif "**rigifysmalldt" in line.lower() or "**rigidifysmalldt" in line.lower():
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
                        elif "*dtthreshold" in line.lower() or "*dt" in line.lower():
                            svector = line.split(",")
                            curOptions["DtThreshold"] = KooDynaFloat(svector[1], 1.0e-8)
                        elif "*maxaspectratio" in line.lower():
                            svector = line.split(",")
                            curOptions["MaxAspectRatio"] = KooDynaFloat(svector[1], 0.0)
                        elif "*elementids" in line.lower():
                            svector = line.split(",")
                            curOptions["ElementIDs"] = [int(svector[i]) for i in range(1, len(svector))]
                        elif "*exceptpid" in line.lower():
                            svector = line.split(",")
                            except_pids = set()
                            for i in range(1, len(svector)):
                                except_pids.add(int(svector[i]))
                            curOptions["ExceptPIDs"] = except_pids
                        line = f.readline().strip()
                        line = line.replace('\n','')
                    self.modeIDOption[curModeID] = curOptions
                    line = line.strip()
                    continue
                elif "**remeshtetra" in line.lower():
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    curOptions["PID"] = []
                    line = f.readline().strip()
                    line = line.replace('\n','')
                    while True:
                        if not line:
                            break
                        if "**end" in line.lower():
                            break
                        elif "*pid" in line.lower():
                            svector = line.split(",")
                            for i in range(1, len(svector)):
                                curOptions["PID"].append(int(svector[i]))
                        elif "*mindt" in line.lower():
                            svector = line.split(",")
                            curOptions["MinDt"] = KooDynaFloat(svector[1], 0.0)
                        elif "*targetedgelength" in line.lower():
                            svector = line.split(",")
                            curOptions["TargetEdgeLength"] = KooDynaFloat(svector[1], 0.0)
                        elif "*maxaspectratio" in line.lower():
                            svector = line.split(",")
                            curOptions["MaxAspectRatio"] = KooDynaFloat(svector[1], 10.0)
                        elif "*smoothingiterations" in line.lower():
                            svector = line.split(",")
                            curOptions["SmoothingIterations"] = int(svector[1])
                        elif "*preservesharednodes" in line.lower():
                            svector = line.split(",")
                            curOptions["PreserveSharedNodes"] = svector[1].strip().lower() != "false"
                        elif "*objective" in line.lower():
                            svector = line.split(",")
                            curOptions["Objective"] = svector[1].strip().lower()
                        line = f.readline().strip()
                        line = line.replace('\n','')
                    self.modeIDOption[curModeID] = curOptions
                    line = line.strip()
                    continue
                elif "**partvalidationsplit" in line.lower():
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
                        elif "*height" in line.lower():
                            svector = line.split(",")
                            curOptions["height"] = KooDynaFloat(svector[1], 100.0)
                        elif "*tfinal" in line.lower():
                            svector = line.split(",")
                            curOptions["tFinal"] = KooDynaFloat(svector[1], 0.0005)
                        elif "*dt" in line.lower():
                            svector = line.split(",")
                            curOptions["dt"] = KooDynaFloat(svector[1], 0.00001)
                        elif "*outputdir" in line.lower():
                            svector = line.split(",")
                            curOptions["output_dir"] = svector[1].strip()
                        elif "*exceptpid" in line.lower():
                            svector = line.split(",")
                            except_pids = []
                            for i in range(1, len(svector)):
                                except_pids.append(int(svector[i]))
                            curOptions["except_pids"] = except_pids
                        elif "*minelements" in line.lower():
                            svector = line.split(",")
                            curOptions["min_elements"] = int(svector[1])
                        line = f.readline().strip()
                        line = line.replace('\n','')
                    self.modeIDOption[curModeID] = curOptions
                    line = line.strip()
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

                elif "**decomposek" in line.lower():
                    # **DecomposeK,<modeID> 옵션 블록 파서
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {"Groups": []}
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if not line or line.startswith('$'):
                            continue
                        if "**end" in line.lower():
                            break
                        low = line.lower()
                        if low.startswith("group,"):
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) < 3:
                                print(f"  Warning: Group line missing members: {line}")
                                continue
                            group_name = parts[1]
                            members = [p for p in parts[2:] if p]
                            patterns = [m for m in members if any(c in m for c in "*?[]")]
                            exact = [m for m in members if m not in patterns]
                            curOptions["Groups"].append({
                                "name": group_name,
                                "patterns": patterns,
                                "parts": exact,
                            })
                        elif low.startswith("groupfromfile,"):
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) < 3:
                                print(f"  Warning: GroupFromFile line incomplete: {line}")
                                continue
                            curOptions["Groups"].append({
                                "name": parts[1],
                                "from_file": parts[2],
                            })
                        elif low.startswith("outputdir,"):
                            curOptions["OutputDir"] = line.split(",", 1)[1].strip()
                        elif low.startswith("defaultgroupname,"):
                            curOptions["DefaultGroupName"] = line.split(",", 1)[1].strip()
                        elif low.startswith("groupssubdir,"):
                            curOptions["GroupsSubdir"] = line.split(",", 1)[1].strip()
                        elif low.startswith("separatematerials,"):
                            curOptions["SeparateMaterials"] = (line.split(",", 1)[1].strip().lower() == "true")
                        elif low.startswith("sharednodespolicy,"):
                            curOptions["SharedNodesPolicy"] = line.split(",", 1)[1].strip()
                        elif low.startswith("emitgroupsets,"):
                            curOptions["EmitGroupSets"] = (line.split(",", 1)[1].strip().lower() == "true")
                        elif low.startswith("modelindependentsplit,"):
                            curOptions["ModelIndependentSplit"] = (line.split(",", 1)[1].strip().lower() == "true")
                        elif low.startswith("groupboundarypolicy,"):
                            curOptions["GroupBoundaryPolicy"] = line.split(",", 1)[1].strip()
                        else:
                            print(f"  Warning: unknown DecomposeK option line: {line}")
                    self.modeIDOption[curModeID] = curOptions

                elif "**vibrationload" in line.lower():
                    # **VibrationLoad,<modeID>
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {
                        "Direction": "Z",
                        "LoadType": "Force",
                        "RelativeMode": "Explicit",
                        "LoadCurve": [],
                        "PartFactors": {},
                        "PartList": [],
                    }
                    in_curve = False
                    in_factors = False
                    in_partlist = False
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if not line or line.startswith('$'):
                            continue
                        if "**end" in line.lower():
                            break
                        low = line.lower()
                        # 멀티라인 블록 종료 마커
                        if low.startswith("endloadcurve"):
                            in_curve = False; continue
                        if low.startswith("endpartfactors"):
                            in_factors = False; continue
                        if low.startswith("endpartlist"):
                            in_partlist = False; continue
                        # 블록 진입
                        if low == "loadcurve":
                            in_curve = True; continue
                        if low == "partfactors":
                            in_factors = True; continue
                        if low == "partlist":
                            in_partlist = True; continue
                        # 블록 내부 데이터
                        if in_curve:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                try:
                                    curOptions["LoadCurve"].append([float(parts[0]), float(parts[1])])
                                except ValueError:
                                    pass
                            continue
                        if in_factors:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                try:
                                    curOptions["PartFactors"][int(parts[0])] = float(parts[1])
                                except ValueError:
                                    pass
                            continue
                        if in_partlist:
                            for tok in line.split(","):
                                tok = tok.strip()
                                if tok:
                                    try:
                                        curOptions["PartList"].append(int(tok))
                                    except ValueError:
                                        pass
                            continue
                        # 단일 라인 옵션 (Key,Value)
                        if low.startswith("direction,"):
                            curOptions["Direction"] = line.split(",", 1)[1].strip()
                        elif low.startswith("loadtype,"):
                            curOptions["LoadType"] = line.split(",", 1)[1].strip()
                        elif low.startswith("relativemode,"):
                            curOptions["RelativeMode"] = line.split(",", 1)[1].strip()
                        elif low.startswith("referencepart,"):
                            try:
                                curOptions["ReferencePart"] = int(line.split(",", 1)[1].strip())
                            except ValueError:
                                pass
                        else:
                            print(f"  Warning: unknown VibrationLoad option line: {line}")
                    self.modeIDOption[curModeID] = curOptions

                elif "**thermalload" in line.lower():
                    # **ThermalLoad,<modeID> — 고온 열전달·열응력 (P1 T1: 균일온도)
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {
                        "ThermalType": "UniformChamber",
                        "BaseTempC": 25.0,
                        "TargetTempC": 85.0,
                        "RampTimeS": 1.0e-3,
                        "DT": 1.0e-6,
                        "TempCurve": [],
                        "PartCTE": {},
                        "DefaultCTE": 1.7e-5,
                        # ICPower (T2/T3) — apply_thermal_load._apply_ic_power 키와 일치
                        "Phase": "thermal",   # thermal(pass1) | structural(pass2)
                        "analysis_type": "transient",
                        "unit_system": "SI",
                        "initial_temperature_C": 25.0,
                        "materials": {},      # {pid: {rho,hc,tc,(cte)}}
                        "heat_sources": [],   # [{part,power_W,volume_mm3}]
                        "timestep": {},       # {its,tmax,dtemp}
                    }
                    in_curve = False
                    in_cte = False
                    in_mat = False
                    in_heat = False
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if not line or line.startswith('$'):
                            continue
                        if "**end" in line.lower():
                            break
                        low = line.lower()
                        if low.startswith("endtempcurve"):
                            in_curve = False; continue
                        if low.startswith("endpartcte"):
                            in_cte = False; continue
                        if low.startswith("endmaterials"):
                            in_mat = False; continue
                        if low.startswith("endheatsources"):
                            in_heat = False; continue
                        if low == "tempcurve":
                            in_curve = True; continue
                        if low == "partcte":
                            in_cte = True; continue
                        if low == "materials":
                            in_mat = True; continue
                        if low == "heatsources":
                            in_heat = True; continue
                        if in_curve:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                try:
                                    curOptions["TempCurve"].append([float(parts[0]), float(parts[1])])
                                except ValueError:
                                    pass
                            continue
                        if in_cte:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                try:
                                    curOptions["PartCTE"][int(parts[0])] = float(parts[1])
                                except ValueError:
                                    pass
                            continue
                        if in_mat:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 4:
                                try:
                                    mat = {"rho": float(parts[1]), "hc": float(parts[2]), "tc": float(parts[3])}
                                    if len(parts) >= 5 and parts[4] != "":
                                        mat["cte"] = float(parts[4])
                                    curOptions["materials"][int(parts[0])] = mat
                                except ValueError:
                                    pass
                            continue
                        if in_heat:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 3:
                                try:
                                    curOptions["heat_sources"].append({
                                        "part": int(parts[0]),
                                        "power_W": float(parts[1]),
                                        "volume_mm3": float(parts[2])})
                                except ValueError:
                                    pass
                            continue
                        if low.startswith("thermaltype,"):
                            curOptions["ThermalType"] = line.split(",", 1)[1].strip()
                        elif low.startswith("basetempc,"):
                            curOptions["BaseTempC"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("targettempc,"):
                            curOptions["TargetTempC"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("ramptimes,"):
                            curOptions["RampTimeS"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("dt,"):
                            curOptions["DT"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("defaultcte,"):
                            curOptions["DefaultCTE"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("phase,"):
                            curOptions["Phase"] = line.split(",", 1)[1].strip()
                        elif low.startswith("analysistype,"):
                            curOptions["analysis_type"] = line.split(",", 1)[1].strip()
                        elif low.startswith("unitsystem,"):
                            curOptions["unit_system"] = line.split(",", 1)[1].strip()
                        elif low.startswith("initialtemperaturec,"):
                            curOptions["initial_temperature_C"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("timestepits,"):
                            curOptions["timestep"]["its"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("timesteptmax,"):
                            curOptions["timestep"]["tmax"] = float(line.split(",", 1)[1].strip())
                        elif low.startswith("timestepdtemp,"):
                            curOptions["timestep"]["dtemp"] = float(line.split(",", 1)[1].strip())
                        else:
                            print(f"  Warning: unknown ThermalLoad option line: {line}")
                    self.modeIDOption[curModeID] = curOptions

                elif "**importmergek" in line.lower():
                    # **ImportMergeK,<modeID> 옵션 블록 파서 (mergek 보다 먼저 체크)
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if not line or line.startswith('$'):
                            continue
                        if "**end" in line.lower():
                            break
                        low = line.lower()
                        if low.startswith("importfile,"):
                            curOptions["ImportFile"] = line.split(",", 1)[1].strip()
                        else:
                            print(f"  Warning: unknown ImportMergeK option line: {line}")
                    self.modeIDOption[curModeID] = curOptions

                elif "**mergek" in line.lower():
                    # **MergeK,<modeID> 옵션 블록 파서
                    svector = line.split(",")
                    curModeID = int(svector[1])
                    curOptions = {}
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        line = line.strip().replace('\n', '')
                        if not line or line.startswith('$'):
                            continue
                        if "**end" in line.lower():
                            break
                        low = line.lower()
                        if low.startswith("outputfile,"):
                            curOptions["OutputFile"] = line.split(",", 1)[1].strip()
                        elif low.startswith("forceinlineiga,"):
                            curOptions["ForceInlineIGA"] = (line.split(",", 1)[1].strip().lower() == "true")
                        elif low.startswith("forceinlinepreserved,"):
                            curOptions["ForceInlinePreserved"] = (line.split(",", 1)[1].strip().lower() == "true")
                        else:
                            print(f"  Warning: unknown MergeK option line: {line}")
                    self.modeIDOption[curModeID] = curOptions

                line = f.readline()
                if not line:  # EOF
                    break
                line = line.replace('\n','')
                line = line.strip()
                if not line:  # Empty line, skip it
                    continue

    def GenerateDecomposeK(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.DecomposeK(curOption, self.curDir, self.inputFileName)

    def GenerateMergeK(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.MergeK(curOption, self.curDir, self.inputFileName)

    def GenerateImportMergeK(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ImportMergeK(curOption, self)

    def GenerateVibrationLoad(self, modeid):
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k", "")
        curOption = self.modeIDOption[modeid]
        self.advancedModification.VibrationLoad(curOption, filePath)

    def GenerateThermalLoad(self, modeid):
        filePath = os.path.join(self.curDir, self.inputFileName)
        filePath = filePath.replace(".k", "")
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ThermalLoad(curOption, filePath)

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
        dt = curOption.get("DT", 1.0e-9)
        self.advancedModification.ErodingMinDT(dt)

    def GenerateRigidifySmallDT(self, modeid):
        curOption = self.modeIDOption[modeid]
        dt_threshold = curOption.get("DtThreshold", 1.0e-8)
        except_pids = curOption.get("ExceptPIDs", set())
        max_ar = curOption.get("MaxAspectRatio", 0.0)
        elem_ids = curOption.get("ElementIDs", None)
        self.dynaImporter.partManager.RigidifySmallDtElements(
            self.dynaImporter.matManager,
            self.dynaImporter.sectionManager,
            dt_threshold=dt_threshold,
            exceptPIDs=except_pids,
            max_aspect_ratio=max_ar,
            element_ids=elem_ids
        )

    def GenerateRemeshTetra(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.RemeshTetra(curOption)

    def GeneratePartValidationSplit(self, modeid):
        curOption = self.modeIDOption[modeid]
        output_dir = curOption.get("output_dir", os.path.join(self.curDir, "validation_split"))
        self.advancedModification.PartValidationSplit(curOption, output_dir)
    
    def GenerateConstrainedNodalRigidBodyToBeam(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ConstrainedNodalRigidBodyToBeam(curOption)

    def GenerateConvertCNRBtoSolid(self, modeid):
        curOption = self.modeIDOption[modeid]
        self.advancedModification.ConvertCNRBtoSolidCylinder(curOption)
   
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
            elif mode == "RIGIDIFY_SMALL_DT":
                self.GenerateRigidifySmallDT(modeid)
                additionalword += "_rsdt"
            elif mode == "REMESH_TETRA":
                self.GenerateRemeshTetra(modeid)
                additionalword += "_remesh"
            elif mode == "PART_VALIDATION_SPLIT":
                self.GeneratePartValidationSplit(modeid)
                additionalword += "_pvsplit"
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
            elif mode == "CONVERT_CNRB_TO_SOLID":
                self.GenerateConvertCNRBtoSolid(modeid)
                additionalword += "_cnrb2solid"
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
            elif mode == "DECOMPOSE_K":
                self.GenerateDecomposeK(modeid)
                self._skip_default_write = True
            elif mode == "MERGE_K":
                self.GenerateMergeK(modeid)
                self._skip_default_write = True
            elif mode == "IMPORT_MERGE_K":
                self.GenerateImportMergeK(modeid)
                additionalword += "_imported"
            elif mode == "VIBRATION_LOAD":
                self.GenerateVibrationLoad(modeid)
                self._skip_default_write = True  # advancedModification에서 자체 write 처리 (DECOMPOSE_K 패턴)
            elif mode == "THERMAL_LOAD":
                self.GenerateThermalLoad(modeid)
                self._skip_default_write = True  # ThermalSet.k 자체 write (VibrationLoad 결)

            self.dynaImporter.SyncronizeMaxID()
        ## write modified File
        import time
        if getattr(self, '_skip_default_write', False):
            print("Default WriteModifiedFile skipped (DECOMPOSE_K / MERGE_K mode handled output)")
        else:
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
        outputDir = os.path.dirname(filePath)
        with open(filePath, "w") as f:
            f.write("*KEYWORD\n")
            f.write(self.dynaImporter.WriteStreamDynaKeyword())

            # IGA Include 문 추가 (FEM_TO_IGA 모드에서 생성된 경우)
            if len(self.dynaImporter.partManager.igaParts) > 0:
                self.dynaImporter.partManager.WriteIGAIncludes(f)

            # passthrough *INCLUDE 출력 (IGA 등 PARAMETER_LOCAL 스코프 유지)
            passthrough_data = getattr(self.dynaImporter.dynaManager, '_include_passthrough_data', [])
            if passthrough_data:
                f.write("$\n$--- Include Files (passthrough) ---\n$\n")
                for entry in passthrough_data:
                    inc_file = entry.get("file", "")
                    f.write("*INCLUDE\n")
                    f.write(f" {os.path.basename(inc_file)}\n")

            # 미인터프리트 키워드 raw 보존 (KooDynaImporter가 모르는 키워드도 손실 방지)
            self._write_uninterpreted_raw_blocks(f)

            f.write("*END\n")

        # *INCLUDE 참조 파일들을 출력 폴더에 복사
        import shutil
        include_files = getattr(self.dynaImporter, '_include_files', [])
        for src in include_files:
            if src and os.path.exists(src):
                dst = os.path.join(outputDir, os.path.basename(src))
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"  Include 파일 복사: {os.path.basename(src)}")

        # IGA 파트 파일도 복사 (FEM_TO_IGA 모드)
        for iga_part in self.dynaImporter.partManager.igaParts.values():
            src = getattr(iga_part, 'output_file_path', '')
            if src and os.path.exists(src):
                dst = os.path.join(outputDir, os.path.basename(src))
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"  IGA 파일 복사: {os.path.basename(src)}")
            
    
    def _write_uninterpreted_raw_blocks(self, f):
        """KooDynaImporter가 파싱 못 한 키워드들을 raw text로 보존 출력.

        매니저에 들어가지 못한 *RIGIDWALL_PLANAR(단순형), *DEFINE_FRICTION 등
        모든 미지원 키워드의 원본 데이터를 그대로 출력하여 손실을 방지.
        """
        try:
            dyna_mgr = self.dynaImporter.dynaManager
            raw_dict = getattr(dyna_mgr, '_raw_keyword_dict', None)
            if not raw_dict:
                return
            interpreted = getattr(self.dynaImporter, 'keywordInterpreted', {}) or {}
            # passthrough/특수 키워드는 별도 처리됨
            SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END"}
            wrote_header = False
            for kw_name, blocks in raw_dict.items():
                if kw_name in SKIP:
                    continue
                if interpreted.get(kw_name, False):
                    continue
                # 미인터프리트 → raw 출력
                if not wrote_header:
                    f.write("$\n$--- Uninterpreted keywords (raw, preserved) ---\n$\n")
                    wrote_header = True
                for block in blocks:
                    f.write(f"*{kw_name}\n")
                    for line in block:
                        f.write(line if line.endswith('\n') else line + '\n')
        except Exception as e:
            print(f"  Warning: uninterpreted raw 출력 실패 (skip): {e}")

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