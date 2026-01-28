# KooDynaAutomaticSimulationScriptGenerator.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
import json
import datetime
import hashlib
import uuid

# ---------- 타입 정의 ----------
AnalysisType = Literal["fullAngleMBD", "fullAngle", "fullAngleCumulative", "multiRepeatCumulative", "partialImpact", "mixedCumulative"]
AngleSource = Literal["lhs", "fromMBD", "usePrevResult"]
PartialImpactMode = Literal["default", "txt"]
HeightMode = Literal["const", "lhs"]
SurfaceType = Literal["steelPlate", "pavingBlock", "concrete", "wood"]
CumDirection = str  # "F1..F6", "E1..E12", "C1..C8" 등
ToleranceMode = Literal["enabled", "disabled"]

# ---------- 시뮬레이션 모드 정의 ----------
SimulationMode = Literal["DROP", "THERM", "STAT", "VIB", "DWI", "COMB"]

SIMULATION_MODES = {
    "DROP": {"full_name": "DROP_ATTITUDE", "description": "낙하 시뮬레이션"},
    "DWI": {"full_name": "DROP_WEIGHT_IMPACT", "description": "중량 충격 시뮬레이션"},
    "STAT": {"full_name": "STATIC_LOAD", "description": "정적 하중 해석"},
    "THERM": {"full_name": "THERMAL_CYCLE", "description": "열응력/열사이클 해석"},
    "VIB": {"full_name": "VIBRATION", "description": "진동 해석"},
    "COMB": {"full_name": "COMBINED", "description": "복합 조건 해석"},
}


# ---------- JSON ?? ?? ----------
class ScenarioRow(TypedDict, total=False):
    id: str
    name: str
    runids: Optional[List[str]]
    fileName: Optional[str]
    objFileName: Optional[str]
    analysisType: AnalysisType
    params: Dict[str, Any]


# ---------- ?? ?? ----------
def _params(d: ScenarioRow) -> Dict[str, Any]:
    """params? dict? ?? ??, ??? ? dict"""
    return (d.get("params") or {}) if isinstance(d.get("params"), dict) else {}


def _parse_common_drop(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    ?? ??? ?? ?? ????(??/??) ?? & ???/??
    ??? ???? ??:
      heightMode="const", heightConst=1.0, heightMin=0.5, heightMax=1.5, surface="steelPlate"
    """
    heightMode: HeightMode = p.get("heightMode", "const")  # type: ignore
    heightConst = float(p.get("heightConst", 1.0))
    heightMin = float(p.get("heightMin", 0.5))
    heightMax = float(p.get("heightMax", 1.5))
    surface: SurfaceType = p.get("surface", "steelPlate")  # type: ignore

    # ?? ??: LHS?? min > max? ??
    if heightMode == "lhs" and heightMin > heightMax:
        heightMin, heightMax = heightMax, heightMin

    return {
        "heightMode": heightMode,
        "heightConst": heightConst,
        "heightMin": heightMin,
        "heightMax": heightMax,
        "surface": surface,
    }


def _parse_tolerance(p: Dict[str, Any]) -> Optional[ToleranceConfig]:
    """
    Parse tolerance parameters from params dict
    Returns None if tolerance is not present or disabled
    """
    tolerance_data = p.get("tolerance")
    if not isinstance(tolerance_data, dict):
        return None
    
    mode: ToleranceMode = tolerance_data.get("mode", "disabled")  # type: ignore
    if mode == "disabled":
        return None
    
    return ToleranceConfig(
        mode=mode,
        faceTolerance=float(tolerance_data.get("faceTolerance", 5.0)),
        edgeTolerance=float(tolerance_data.get("edgeTolerance", 5.0)),
        cornerTolerance=float(tolerance_data.get("cornerTolerance", 5.0))
    )


# ---------- dataclass: Type? ?? ?? ----------
@dataclass
class ToleranceConfig:
    mode: ToleranceMode
    faceTolerance: float
    edgeTolerance: float
    cornerTolerance: float

@dataclass
class FullAngleMBDConfig:
    id: str
    name: str
    analysisType: AnalysisType
    objFileName: Optional[str]
    mbdCount: int
    runids: List[str]
    angleSource: AngleSource
    angleSourceId: Optional[str]
    angleSourceFileName: Optional[str]
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType
    # Tolerance support
    tolerance: Optional[ToleranceConfig]


@dataclass
class FullAngleConfig:
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    faTotal: int
    includeFace6: bool
    includeEdge12: bool
    includeCorner8: bool
    runids: List[str]
    angleSource: AngleSource
    angleSourceId: Optional[str]
    angleSourceFileName: Optional[str]
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType
    # Tolerance support
    tolerance: Optional[ToleranceConfig]


@dataclass
class FullAngleCumulativeConfig:
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    cumRepeatCount: int               # 2~5
    cumDOECount: int
    runids: List[str]
    cumDirectionsGrid: List[List[CumDirection]]  # [DOE][repeat]
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType
    # Tolerance support
    tolerance: Optional[ToleranceConfig]


@dataclass
class MultiRepeatCumulativeConfig:
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    multiRepeatCount: int              # ?? (?? 24)
    runids: List[str]
    multiRepeatDirections: List[CumDirection]  # 1?? ??
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType
    # Tolerance support
    tolerance: Optional[ToleranceConfig]


@dataclass
class PartialImpactConfig:
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    runids: List[str]
    mode: PartialImpactMode
    piTxtName: Optional[str]


@dataclass
class MixedStepConfig:
    """혼합 시나리오의 개별 Step 설정"""
    step: int
    mode: SimulationMode
    mode_full: str
    condition: str
    params: Dict[str, Any]


@dataclass
class MixedCumulativeConfig:
    """혼합 누적 시나리오 설정 (DROP + THERM 등 다중 모드)"""
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    projectName: str
    doeCount: int
    totalSteps: int
    steps: List[MixedStepConfig]
    runids: List[str]
    # Tolerance support
    tolerance: Optional[ToleranceConfig]


# ======================================================================
#  메인 클래스
# ======================================================================

class KooDynaAutomaticSimulationScriptGenerator:
    """
      gen = KooDynaAutomaticSimulationScriptGenerator(jsonOptionList)
      out = gen.generate_for_all()
    """

    def __init__(self, jsonOptionList: List[ScenarioRow], metaData: Dict[str, Any]) -> None:
        """
        jsonOptionList: List[ScenarioRow]
        """
        self.metaData = metaData
        self.scenarios: List[ScenarioRow] = self._sanitize(jsonOptionList)

    def GenerateRunID(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
        run_id = f"{timestamp}_{unique_hash}"
        print(run_id + " is generated as run_id")
        return run_id

    @staticmethod
    def _sanitize(data: List[ScenarioRow]) -> List[ScenarioRow]:
        """?? ??? ??"""
        scenarios: List[ScenarioRow] = []
        for d in data:
            if not isinstance(d, dict):
                continue
            item: ScenarioRow = {
                "id": d.get("id", ""),
                "name": d.get("name", "Unnamed"),
                "fileName": d.get("fileName"),
                "objFileName": d.get("objFileName"),
                "analysisType": d.get("analysisType", "fullAngleMBD"),
                "params": d.get("params", {}) if isinstance(d.get("params"), dict) else {},
            }
            scenarios.append(item)
        return scenarios

    # ---------- Type? ?? ----------
    def parse_full_angle_mbd(self, row: ScenarioRow) -> FullAngleMBDConfig:
        p = _params(row)
        common = _parse_common_drop(p)
        tolerance = _parse_tolerance(p)
        runids = row.get("runids", [])
        return FullAngleMBDConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "fullAngleMBD"),  # type: ignore
            objFileName=row.get("objFileName"),
            mbdCount=int(p.get("mbdCount", 1000)),
            runids=runids,
            angleSource=p.get("angleSource", "lhs"),
            angleSourceId=p.get("angleSourceId"),
            angleSourceFileName=p.get("angleSourceFileName"),
            tolerance=tolerance,
            **common,  # height/surface
        )

    def parse_full_angle(self, row: ScenarioRow) -> FullAngleConfig:
        p = _params(row)
        common = _parse_common_drop(p)
        tolerance = _parse_tolerance(p)
        runids = row.get("runids", [])
        return FullAngleConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "fullAngle"),  # type: ignore
            fileName=row.get("fileName"),
            faTotal=int(p.get("faTotal", 100)),
            includeFace6=bool(p.get("includeFace6", True)),
            includeEdge12=bool(p.get("includeEdge12", True)),
            includeCorner8=bool(p.get("includeCorner8", True)),
            runids=runids,
            angleSource=p.get("angleSource", "lhs"),
            angleSourceId=p.get("angleSourceId"),
            angleSourceFileName=p.get("angleSourceFileName"),
            tolerance=tolerance,
            **common,
        )

    def parse_full_angle_cumulative(self, row: ScenarioRow) -> FullAngleCumulativeConfig:
        p = _params(row)
        common = _parse_common_drop(p)
        tolerance = _parse_tolerance(p)
        repeat = int(p.get("cumRepeatCount", 3))
        doe = int(p.get("cumDOECount", 5))
        grid = p.get("cumDirectionsGrid")
        runids = row.get("runids", [])
        def _valid_grid(g: Any) -> bool:
            return (
                isinstance(g, list)
                and len(g) == doe
                and all(isinstance(rw, list) and len(rw) == repeat for rw in g)
            )

        if not _valid_grid(grid):
            oneD = p.get("cumDirections")
            if isinstance(oneD, list) and len(oneD) == repeat:
                base = oneD
                grid = []
                for r in range(doe):
                    shift = r % repeat
                    row_r = [base[(i + shift) % repeat] for i in range(repeat)]
                    grid.append(row_r)
            else:
                face = [f"F{i}" for i in range(1, 7)]
                edge = [f"E{i}" for i in range(1, 13)]
                corner = [f"C{i}" for i in range(1, 9)]
                pool = face + edge + corner
                base = [pool[i % len(pool)] for i in range(repeat)]
                grid = []
                for r in range(doe):
                    shift = r % repeat
                    row_r = [base[(i + shift) % repeat] for i in range(repeat)]
                    grid.append(row_r)

        return FullAngleCumulativeConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "fullAngleCumulative"),  # type: ignore
            fileName=row.get("fileName"),
            cumRepeatCount=repeat,
            cumDOECount=doe,
            cumDirectionsGrid=grid,  # type: ignore
            runids=runids,
            tolerance=tolerance,
            **common,
        )

    def parse_multi_repeat_cumulative(self, row: ScenarioRow) -> MultiRepeatCumulativeConfig:
        p = _params(row)
        common = _parse_common_drop(p)
        tolerance = _parse_tolerance(p)
        repeat = int(p.get("multiRepeatCount", 24))
        directions = p.get("multiRepeatDirections")
        runids = row.get("runids", [])
        
        # 유효성 검사 및 기본값 생성
        if not isinstance(directions, list) or len(directions) != repeat:
            face = [f"F{i}" for i in range(1, 7)]
            edge = [f"E{i}" for i in range(1, 13)]
            corner = [f"C{i}" for i in range(1, 9)]
            pool = face + edge + corner
            directions = [pool[i % len(pool)] for i in range(repeat)]
        
        return MultiRepeatCumulativeConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "multiRepeatCumulative"),  # type: ignore
            fileName=row.get("fileName"),
            multiRepeatCount=repeat,
            multiRepeatDirections=directions,  # type: ignore
            runids=runids,
            tolerance=tolerance,
            **common,
        )

    def parse_partial_impact(self, row: ScenarioRow) -> PartialImpactConfig:
        p = _params(row)
        runids = row.get("runids", [])
        return PartialImpactConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "partialImpact"),  # type: ignore
            fileName=row.get("fileName"),
            mode=p.get("piMode", "default"),
            piTxtName=p.get("piTxtName"),
            runids=runids,
        )

    def parse_mixed_cumulative(self, row: ScenarioRow) -> MixedCumulativeConfig:
        """혼합 누적 시나리오 파싱 (DROP + THERM 등 다중 모드 지원)"""
        p = _params(row)
        tolerance = _parse_tolerance(p)
        runids = row.get("runids", [])

        projectName = p.get("projectName", self.metaData.get("model_name", "Project"))
        doeCount = int(p.get("doeCount", 1))

        # steps 파싱
        raw_steps = p.get("steps", [])
        steps: List[MixedStepConfig] = []

        for i, step_data in enumerate(raw_steps):
            if isinstance(step_data, dict):
                mode = step_data.get("mode", "DROP")
                condition = step_data.get("condition", "F1")
                step_params = step_data.get("params", {})
            elif isinstance(step_data, list) and len(step_data) >= 2:
                # 간단한 형식: ["THERM", "HOT85"] 또는 ["DROP", "F1"]
                mode = step_data[0]
                condition = step_data[1]
                step_params = step_data[2] if len(step_data) > 2 else {}
            else:
                mode = "DROP"
                condition = "F1"
                step_params = {}

            mode_info = SIMULATION_MODES.get(mode, {"full_name": "UNKNOWN"})

            steps.append(MixedStepConfig(
                step=i + 1,
                mode=mode,
                mode_full=mode_info["full_name"],
                condition=condition,
                params=step_params
            ))

        # steps가 비어있으면 기본값 생성
        if not steps:
            steps = [
                MixedStepConfig(step=1, mode="DROP", mode_full="DROP_ATTITUDE", condition="F1", params={}),
                MixedStepConfig(step=2, mode="DROP", mode_full="DROP_ATTITUDE", condition="E1", params={}),
                MixedStepConfig(step=3, mode="DROP", mode_full="DROP_ATTITUDE", condition="C1", params={}),
            ]

        return MixedCumulativeConfig(
            id=row.get("id", ""),
            name=row.get("name", "Unnamed"),
            analysisType=row.get("analysisType", "mixedCumulative"),  # type: ignore
            fileName=row.get("fileName"),
            projectName=projectName,
            doeCount=doeCount,
            totalSteps=len(steps),
            steps=steps,
            runids=runids,
            tolerance=tolerance,
        )

    # ---------- 타입별 파싱 ----------
    def parse_scenario_by_type(
        self, row: ScenarioRow
    ) -> Union[FullAngleMBDConfig, FullAngleConfig, FullAngleCumulativeConfig, MultiRepeatCumulativeConfig, PartialImpactConfig, MixedCumulativeConfig]:
        atype: AnalysisType = row.get("analysisType", "fullAngleMBD")  # type: ignore
        if atype == "fullAngleMBD":
            return self.parse_full_angle_mbd(row)
        elif atype == "fullAngle":
            return self.parse_full_angle(row)
        elif atype == "fullAngleCumulative":
            return self.parse_full_angle_cumulative(row)
        elif atype == "multiRepeatCumulative":
            return self.parse_multi_repeat_cumulative(row)
        elif atype == "partialImpact":
            return self.parse_partial_impact(row)
        elif atype == "mixedCumulative":
            return self.parse_mixed_cumulative(row)
        else:
            return self.parse_full_angle_mbd(row)

    # ---------- ? ??? ???? ?? ----------
    def script_full_angle_mbd(self, cfg: FullAngleMBDConfig) -> Dict[str, Any]:
        # unpack to locals
        id = cfg.id
        name = cfg.name
        analysisType = cfg.analysisType
        objFileName = cfg.objFileName
        mbdCount = cfg.mbdCount
        runids = cfg.runids
        angleSource = cfg.angleSource
        angleSourceId = cfg.angleSourceId
        angleSourceFileName = cfg.angleSourceFileName
        heightMode = cfg.heightMode
        heightConst = cfg.heightConst
        heightMin = cfg.heightMin
        heightMax = cfg.heightMax
        surface = cfg.surface
        tolerance = cfg.tolerance

        result = {
            "id": id,
            "name": name,
            "analysisType": analysisType,
            "objFileName": objFileName,
            "mbdCount": mbdCount,
            "runids": runids,
            "angleSource": angleSource,
            "angleSourceId": angleSourceId,
            "angleSourceFileName": angleSourceFileName,
            "heightMode": heightMode,
            "heightConst": heightConst,
            "heightMin": heightMin,
            "heightMax": heightMax,
            "surface": surface,
        }
        
        if tolerance:
            result["tolerance"] = {
                "mode": tolerance.mode,
                "faceTolerance": tolerance.faceTolerance,
                "edgeTolerance": tolerance.edgeTolerance,
                "cornerTolerance": tolerance.cornerTolerance
            }
        
        return result

    def script_full_angle(self, cfg: FullAngleConfig) -> Dict[str, Any]:
        # unpack to locals
        id = cfg.id
        name = cfg.name
        analysisType = cfg.analysisType
        fileName = cfg.fileName
        faTotal = cfg.faTotal
        includeFace6 = cfg.includeFace6
        includeEdge12 = cfg.includeEdge12
        includeCorner8 = cfg.includeCorner8
        runids = cfg.runids
        angleSource = cfg.angleSource
        angleSourceId = cfg.angleSourceId
        angleSourceFileName = cfg.angleSourceFileName
        heightMode = cfg.heightMode
        heightConst = cfg.heightConst
        heightMin = cfg.heightMin
        heightMax = cfg.heightMax
        surface = cfg.surface
        tolerance = cfg.tolerance

        scriptStr = ""
        scriptStr += f"*Inputfile\n"
        scriptStr += f"{fileName}\n"
        scriptStr += f"*RunDirectoryMode,True,Data/Results,Data/Metadata\n"
        scriptStr += f"*Info,{self.metaData['model_name']},{self.metaData['stage']}\n"

        scriptStr += f"*Description,This is a full angle analysis, "
        if angleSource == "lhs":
            scriptStr += f"Latin Hypercube Sampling is used for angle generation\n"
        elif angleSource == "fromMBD":
            scriptStr += f"Pre-processed Multi-Body Dynamic Simulation is used for angle generation\n"        
        elif angleSource == "usePrevResult":
            scriptStr += f"Previous result is used for angle generation\n"

        scriptStr += f"*Creator,{self.metaData['created_by']['name']},{self.metaData['created_by']['email']},{self.metaData['created_by']['group']},{self.metaData['created_by']['team']}\n"
        scriptStr += f"*Mode\n"
        scriptStr += f"DROP_ATTITUDE,1\n"

        scriptStr += f"**DropAttitude,1\n"
        scriptStr += f"**EndDropAttitude\n"
        scriptStr += f"*End\n"
       




        result = {
            "id": id,
            "name": name,
            "analysisType": analysisType,
            "fileName": fileName,
            "faTotal": faTotal,
            "includeFace6": includeFace6,
            "includeEdge12": includeEdge12,
            "includeCorner8": includeCorner8,
            "runids": runids,
            "angleSource": angleSource,
            "angleSourceId": angleSourceId,
            "angleSourceFileName": angleSourceFileName,
            "heightMode": heightMode,
            "heightConst": heightConst,
            "heightMin": heightMin,
            "heightMax": heightMax,
            "surface": surface,
        }
        
        if tolerance:
            result["tolerance"] = {
                "mode": tolerance.mode,
                "faceTolerance": tolerance.faceTolerance,
                "edgeTolerance": tolerance.edgeTolerance,
                "cornerTolerance": tolerance.cornerTolerance
            }
        
        return result

    def script_full_angle_cumulative(self, cfg: FullAngleCumulativeConfig) -> Dict[str, Any]:
        # unpack to locals
        id = cfg.id
        name = cfg.name
        analysisType = cfg.analysisType
        fileName = cfg.fileName
        runids = cfg.runids
        cumRepeatCount = cfg.cumRepeatCount
        cumDOECount = cfg.cumDOECount
        cumDirectionsGrid = cfg.cumDirectionsGrid
        heightMode = cfg.heightMode
        heightConst = cfg.heightConst
        heightMin = cfg.heightMin
        heightMax = cfg.heightMax
        surface = cfg.surface
        tolerance = cfg.tolerance

        result = {
            "id": id,
            "name": name,
            "analysisType": analysisType,
            "fileName": fileName,
            "cumRepeatCount": cumRepeatCount,
            "cumDOECount": cumDOECount,
            "cumDirectionsGrid": cumDirectionsGrid,
            "runids": runids,
            "heightMode": heightMode,
            "heightConst": heightConst,
            "heightMin": heightMin,
            "heightMax": heightMax,
            "surface": surface,
        }
        
        if tolerance:
            result["tolerance"] = {
                "mode": tolerance.mode,
                "faceTolerance": tolerance.faceTolerance,
                "edgeTolerance": tolerance.edgeTolerance,
                "cornerTolerance": tolerance.cornerTolerance
            }
        
        return result

    def script_multi_repeat_cumulative(self, cfg: MultiRepeatCumulativeConfig) -> Dict[str, Any]:
        # unpack to locals
        id = cfg.id
        name = cfg.name
        analysisType = cfg.analysisType
        fileName = cfg.fileName
        runids = cfg.runids
        multiRepeatCount = cfg.multiRepeatCount
        multiRepeatDirections = cfg.multiRepeatDirections
        heightMode = cfg.heightMode
        heightConst = cfg.heightConst
        heightMin = cfg.heightMin
        heightMax = cfg.heightMax
        surface = cfg.surface
        tolerance = cfg.tolerance

        result = {
            "id": id,
            "name": name,
            "analysisType": analysisType,
            "fileName": fileName,
            "multiRepeatCount": multiRepeatCount,
            "multiRepeatDirections": multiRepeatDirections,
            "runids": runids,
            "heightMode": heightMode,
            "heightConst": heightConst,
            "heightMin": heightMin,
            "heightMax": heightMax,
            "surface": surface,
        }
        
        if tolerance:
            result["tolerance"] = {
                "mode": tolerance.mode,
                "faceTolerance": tolerance.faceTolerance,
                "edgeTolerance": tolerance.edgeTolerance,
                "cornerTolerance": tolerance.cornerTolerance
            }
        
        return result

    def script_partial_impact(self, cfg: PartialImpactConfig) -> Dict[str, Any]:
        # unpack to locals
        id = cfg.id
        name = cfg.name
        analysisType = cfg.analysisType
        fileName = cfg.fileName
        mode = cfg.mode
        piTxtName = cfg.piTxtName

        return {
            "id": id,
            "name": name,
            "analysisType": analysisType,
            "fileName": fileName,
            "mode": mode,
            "piTxtName": piTxtName,
        }

    def script_mixed_cumulative(self, cfg: MixedCumulativeConfig) -> Dict[str, Any]:
        """혼합 누적 시나리오 출력 생성"""
        steps_output = []
        for step in cfg.steps:
            steps_output.append({
                "step": step.step,
                "mode": step.mode,
                "mode_full": step.mode_full,
                "condition": step.condition,
                "params": step.params
            })

        result = {
            "id": cfg.id,
            "name": cfg.name,
            "analysisType": cfg.analysisType,
            "fileName": cfg.fileName,
            "projectName": cfg.projectName,
            "doeCount": cfg.doeCount,
            "totalSteps": cfg.totalSteps,
            "steps": steps_output,
            "runids": cfg.runids,
        }

        if cfg.tolerance:
            result["tolerance"] = {
                "mode": cfg.tolerance.mode,
                "faceTolerance": cfg.tolerance.faceTolerance,
                "edgeTolerance": cfg.tolerance.edgeTolerance,
                "cornerTolerance": cfg.tolerance.cornerTolerance
            }

        return result

    def generate_runids_for_all(self) -> List[str]:
        for row in self.scenarios:
            cfg = self.parse_scenario_by_type(row)
            runids = row.get("runids", [])
            if isinstance(cfg, FullAngleMBDConfig):
                runids.append(self.GenerateRunID())
            elif isinstance(cfg, FullAngleConfig):
                for _ in range(cfg.faTotal):
                    runids.append(self.GenerateRunID())
            elif isinstance(cfg, FullAngleCumulativeConfig):
                for _ in range(cfg.cumRepeatCount):
                    for _ in range(cfg.cumDOECount):
                        runids.append(self.GenerateRunID())
            elif isinstance(cfg, MultiRepeatCumulativeConfig):
                for _ in range(cfg.multiRepeatCount):
                    runids.append(self.GenerateRunID())
            elif isinstance(cfg, PartialImpactConfig):
                runids.append(self.GenerateRunID())
            elif isinstance(cfg, MixedCumulativeConfig):
                # DOE 수 × Step 수 만큼 run_id 생성
                for _ in range(cfg.doeCount):
                    for _ in range(cfg.totalSteps):
                        runids.append(self.GenerateRunID())
            row["runids"] = runids
        return self.scenarios

    # ---------- 전체 생성 ----------
    def generate_for_all(self) -> List[Dict[str, Any]]:
        outputs: List[Dict[str, Any]] = []
        self.generate_runids_for_all()
        for row in self.scenarios:
            cfg = self.parse_scenario_by_type(row)
            if isinstance(cfg, FullAngleMBDConfig):
                outputs.append(self.script_full_angle_mbd(cfg))
            elif isinstance(cfg, FullAngleConfig):
                outputs.append(self.script_full_angle(cfg))
            elif isinstance(cfg, FullAngleCumulativeConfig):
                outputs.append(self.script_full_angle_cumulative(cfg))
            elif isinstance(cfg, MultiRepeatCumulativeConfig):
                outputs.append(self.script_multi_repeat_cumulative(cfg))
            elif isinstance(cfg, PartialImpactConfig):
                outputs.append(self.script_partial_impact(cfg))
            elif isinstance(cfg, MixedCumulativeConfig):
                outputs.append(self.script_mixed_cumulative(cfg))
        return outputs

    # ---------- runner_config.json 생성 ----------
    def generate_runner_config(self, cfg: MixedCumulativeConfig, output_dir: str = "Data/Results") -> Dict[str, Any]:
        """
        MixedCumulativeConfig를 runner_config.json 스키마로 변환
        CumulativeScenarioRunner.py에서 사용할 설정 파일 생성
        """
        steps_config = []
        for step in cfg.steps:
            step_dict = {
                "step": step.step,
                "mode": step.mode,
                "mode_full": step.mode_full,
                "condition": step.condition,
                "config_template": f"step_{step.step:03d}_{step.mode}_{step.condition}.txt",
                "params": step.params
            }
            steps_config.append(step_dict)

        runner_config = {
            "$schema": "runner_config_schema_v1",
            "generated_by": "SIMULATION_AUTOMATION",
            "generated_at": datetime.datetime.now().isoformat(),
            "version": "1.0",

            "environment": {
                "koomeshmodifier_path": "/opt/pyKooCAE/KooMeshModifier.py",
                "lsdyna_path": "/opt/lsdyna/lsdyna",
                "ncpu": 32,
                "memory": "2000m",
                "mpi_enabled": True
            },

            "project": {
                "name": cfg.projectName,
                "model_file": cfg.fileName,
                "output_dir": output_dir,
                "index_file": f"{output_dir}/simulation_index.json"
            },

            "scenario": {
                "id": cfg.id,
                "name": cfg.name,
                "type": cfg.analysisType,
                "doe_count": cfg.doeCount,
                "total_steps": cfg.totalSteps,
                "steps": steps_config
            },

            "execution": {
                "checkpoint_enabled": True,
                "checkpoint_file": f"{output_dir}/checkpoint.json",
                "retry_on_failure": True,
                "max_retries": 2,
                "timeout_per_step_seconds": 7200
            }
        }

        return runner_config

    def generate_simulation_index(self, cfg: MixedCumulativeConfig, output_dir: str = "Data/Results") -> Dict[str, Any]:
        """
        simulation_index.json 초기화 생성
        모든 DOE × Step에 대한 초기 상태를 pending으로 설정
        """
        mode_sequence = [step.mode for step in cfg.steps]

        simulation_index = {
            "project": cfg.projectName,
            "created": datetime.datetime.now().isoformat(),
            "scenarios": [
                {
                    "id": cfg.id,
                    "name": cfg.name,
                    "type": cfg.analysisType,
                    "total_steps": cfg.totalSteps,
                    "doe_count": cfg.doeCount,
                    "total_runs": cfg.doeCount * cfg.totalSteps,
                    "status": "pending",
                    "mode_sequence": mode_sequence,
                    "runs": {}
                }
            ]
        }

        return simulation_index

    def generate_alias(self, project: str, total_steps: int, doe_index: int,
                       step: int, mode: str, condition: str) -> str:
        """별칭 생성: {Project}_CUM{TotalSteps}_DOE{Index}_S{Step}_{Mode}_{Condition}"""
        return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"

    def save_runner_config(self, cfg: MixedCumulativeConfig, output_path: str) -> str:
        """runner_config.json을 파일로 저장"""
        import os
        output_dir = os.path.dirname(output_path) or "Data/Results"
        runner_config = self.generate_runner_config(cfg, output_dir)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(runner_config, f, ensure_ascii=False, indent=2)

        print(f"runner_config.json saved: {output_path}")
        return output_path

    def save_simulation_index(self, cfg: MixedCumulativeConfig, output_path: str) -> str:
        """simulation_index.json을 파일로 저장"""
        import os
        output_dir = os.path.dirname(output_path) or "Data/Results"
        simulation_index = self.generate_simulation_index(cfg, output_dir)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(simulation_index, f, ensure_ascii=False, indent=2)

        print(f"simulation_index.json saved: {output_path}")
        return output_path

    def generate_and_save_all_configs(self, output_dir: str = "Data/Results") -> List[str]:
        """
        모든 mixedCumulative 시나리오에 대해 runner_config.json과 simulation_index.json 생성
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []

        self.generate_runids_for_all()

        for row in self.scenarios:
            cfg = self.parse_scenario_by_type(row)
            if isinstance(cfg, MixedCumulativeConfig):
                # runner_config.json 저장
                runner_path = os.path.join(output_dir, f"runner_config_{cfg.id}.json")
                self.save_runner_config(cfg, runner_path)
                saved_files.append(runner_path)

                # simulation_index.json 저장
                index_path = os.path.join(output_dir, f"simulation_index_{cfg.id}.json")
                self.save_simulation_index(cfg, index_path)
                saved_files.append(index_path)

        return saved_files


# ---------- ?? ?? ?? ??? ----------
if __name__ == "__main__":
    # ?? ??? (??? ???? jsonOptionList? ???? ???)
    sample = [
        {
            "id": "1",
            "name": "Case1",
            "analysisType": "fullAngleMBD",
            "objFileName": "phone.obj",
            "params": {
                "mbdCount": 1000,
                "heightMode": "lhs",
                "heightMin": 0.8,
                "heightMax": 1.2,
                "surface": "pavingBlock"
            }
        },
        {
            "id": "2",
            "name": "Case2",
            "analysisType": "partialImpact",
            "fileName": "model.k",
            "params": {
                "piMode": "txt",
                "piTxtName": "impact.txt"
            }
        },
        {
            "id": "3",
            "name": "Case3",
            "analysisType": "fullAngleCumulative",
            "fileName": "model2.k",
            "params": {
                "cumRepeatCount": 3,
                "cumDOECount": 2,
                "cumDirectionsGrid": [["F1", "E2", "C3"], ["F2", "E3", "C4"]],
                "heightMode": "const",
                "heightConst": 1.0,
                "surface": "steelPlate"
            }
        },
        {
            "id": "4",
            "name": "Case4 - MultiRepeat",
            "analysisType": "multiRepeatCumulative",
            "fileName": "model3.k",
            "params": {
                "multiRepeatCount": 24,
                "multiRepeatDirections": ["F1", "F2", "F3", "F4", "F5", "F6",
                                          "E1", "E2", "E3", "E4", "E5", "E6",
                                          "E7", "E8", "E9", "E10", "E11", "E12",
                                          "C1", "C2", "C3", "C4", "C5", "C6"],
                "heightMode": "lhs",
                "heightMin": 0.8,
                "heightMax": 1.5,
                "surface": "concrete"
            }
        },
        {
            "id": "5",
            "name": "Case5 - MixedCumulative (Thermal + Drop)",
            "analysisType": "mixedCumulative",
            "fileName": "model4.k",
            "params": {
                "projectName": "GalaxyS25",
                "doeCount": 3,
                "steps": [
                    {"mode": "THERM", "condition": "HOT85", "params": {"target_temp_C": 85, "hold_time_s": 1800}},
                    {"mode": "THERM", "condition": "COLD-40", "params": {"target_temp_C": -40, "hold_time_s": 1800}},
                    {"mode": "DROP", "condition": "F1", "params": {"height_mm": 1500, "surface": "steelPlate"}},
                    {"mode": "THERM", "condition": "CYC03", "params": {"cycles": 3}},
                    {"mode": "DROP", "condition": "E5", "params": {"height_mm": 1500}},
                    {"mode": "DROP", "condition": "C2", "params": {"height_mm": 1500}}
                ]
            }
        }
    ]
    metaData = {
        "model_name": "TestModel",
        "stage": "DV1",
        "created_by": {
            "name": "koo.park",
            "email": "koo.park@samsung.com",
            "group": "CAE",
            "team": "Samsung"
        }
    }
    gen = KooDynaAutomaticSimulationScriptGenerator(sample, metaData)
    print(json.dumps(gen.generate_for_all(), ensure_ascii=False, indent=2))


