# KooDynaAutomaticSimulationScriptGenerator.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
import json
import datetime
import hashlib
import uuid

# ---------- 타입 정의 ----------
AnalysisType = Literal["fullAngleMBD", "fullAngle", "fullAngleCumulative", "partialImpact"]
AngleSource = Literal["lhs", "preMBD", "fromMBD", "preFA", "fromFA"]
PartialImpactMode = Literal["default", "txt"]
HeightMode = Literal["const", "lhs"]
SurfaceType = Literal["steelPlate", "pavingBlock", "concrete", "wood"]
CumDirection = str  # "F1..F6", "E1..E12", "C1..C8" 문자열


# ---------- JSON 타입 힌트 ----------
class ScenarioRow(TypedDict, total=False):
    id: str
    name: str
    runids: Optional[List[str]]
    fileName: Optional[str]
    objFileName: Optional[str]
    analysisType: AnalysisType
    params: Dict[str, Any]


# ---------- 내부 유틸 ----------
def _params(d: ScenarioRow) -> Dict[str, Any]:
    """params가 dict일 때만 반환, 아니면 빈 dict"""
    return (d.get("params") or {}) if isinstance(d.get("params"), dict) else {}


def _parse_common_drop(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    모든 전각도 해석 공통 파라미터(높이/표면) 파싱 & 기본값/검증
    프론트 기본값과 동일:
      heightMode="const", heightConst=1.0, heightMin=0.5, heightMax=1.5, surface="steelPlate"
    """
    heightMode: HeightMode = p.get("heightMode", "const")  # type: ignore
    heightConst = float(p.get("heightConst", 1.0))
    heightMin = float(p.get("heightMin", 0.5))
    heightMax = float(p.get("heightMax", 1.5))
    surface: SurfaceType = p.get("surface", "steelPlate")  # type: ignore

    # 안전 보정: LHS인데 min > max면 스왑
    if heightMode == "lhs" and heightMin > heightMax:
        heightMin, heightMax = heightMax, heightMin

    return {
        "heightMode": heightMode,
        "heightConst": heightConst,
        "heightMin": heightMin,
        "heightMax": heightMax,
        "surface": surface,
    }


# ---------- dataclass: Type별 파싱 결과 ----------
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
    # 공통(높이/표면)
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType


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
    preMbdCount: int
    preFaTotal: int
    angleSourceId: Optional[str]
    angleSourceFileName: Optional[str]
    # 공통(높이/표면)
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType


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
    # 공통(높이/표면)
    heightMode: HeightMode
    heightConst: float
    heightMin: float
    heightMax: float
    surface: SurfaceType


@dataclass
class PartialImpactConfig:
    id: str
    name: str
    analysisType: AnalysisType
    fileName: Optional[str]
    runids: List[str]
    mode: PartialImpactMode
    piTxtName: Optional[str]


# ======================================================================
#  메인 클래스
# ======================================================================

class KooDynaAutomaticSimulationScriptGenerator:
    """
    사용법:
      gen = KooDynaAutomaticSimulationScriptGenerator(jsonOptionList)
      out = gen.generate_for_all()
    """

    def __init__(self, jsonOptionList: List[ScenarioRow]) -> None:
        # 이미 list[dict]로 들어온 JSON 옵션을 그대로 저장
        self.projectName = ""
        self.revision = ""
        self.scenarios: List[ScenarioRow] = self._sanitize(jsonOptionList)

    def GenerateRunID(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
        run_id = f"{timestamp}_{unique_hash}"
        print(run_id + " is generated as run_id")
        return run_id

    @staticmethod
    def _sanitize(data: List[ScenarioRow]) -> List[ScenarioRow]:
        """최소 스키마 보정"""
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

    # ---------- Type별 파서 ----------
    def parse_full_angle_mbd(self, row: ScenarioRow) -> FullAngleMBDConfig:
        p = _params(row)
        common = _parse_common_drop(p)
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
            **common,  # height/surface
        )

    def parse_full_angle(self, row: ScenarioRow) -> FullAngleConfig:
        p = _params(row)
        common = _parse_common_drop(p)
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
            preMbdCount=int(p.get("preMbdCount", 10000)),
            preFaTotal=int(p.get("preFaTotal", 100)),
            angleSourceId=p.get("angleSourceId"),
            angleSourceFileName=p.get("angleSourceFileName"),
            **common,
        )

    def parse_full_angle_cumulative(self, row: ScenarioRow) -> FullAngleCumulativeConfig:
        p = _params(row)
        common = _parse_common_drop(p)
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

    # ---------- 디스패처 ----------
    def parse_scenario_by_type(
        self, row: ScenarioRow
    ) -> Union[FullAngleMBDConfig, FullAngleConfig, FullAngleCumulativeConfig, PartialImpactConfig]:
        atype: AnalysisType = row.get("analysisType", "fullAngleMBD")  # type: ignore
        if atype == "fullAngleMBD":
            return self.parse_full_angle_mbd(row)
        elif atype == "fullAngle":
            return self.parse_full_angle(row)
        elif atype == "fullAngleCumulative":
            return self.parse_full_angle_cumulative(row)
        elif atype == "partialImpact":
            return self.parse_partial_impact(row)
        else:
            return self.parse_full_angle_mbd(row)

    # ---------- 각 타입별 스크립트 자리 ----------
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

        return {
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
        preMbdCount = cfg.preMbdCount
        preFaTotal = cfg.preFaTotal
        angleSourceId = cfg.angleSourceId
        angleSourceFileName = cfg.angleSourceFileName
        heightMode = cfg.heightMode
        heightConst = cfg.heightConst
        heightMin = cfg.heightMin
        heightMax = cfg.heightMax
        surface = cfg.surface

        scriptStr = ""
        scriptStr += f"*Inputfile\n"
        scriptStr += f"{fileName}\n"
        scriptStr += f"*RunDirectoryMode,True,Data/Results,Data/Metadata\n"
        scriptStr += f"*Info,{self.projectName},{self.revision}\n"
        scriptStr += f"*Description,This is a full angle analysis, "
        if angleSource == "lhs":
            scriptStr += f"Latin Hypercube Sampling is used for angle generation\n"
        elif angleSource == "preMBD":
            scriptStr += f"Pre-processed Multi-Body Dynamic Simulation is used for angle generation\n"
        elif angleSource == "fromMBD":
            scriptStr += f"Existing Multi-Body Dynamic Simulation is used for angle generation\n"
        elif angleSource == "preFA":
            scriptStr += f"Pre-processed Full Angle Analysis is used for angle generation\n"
        elif angleSource == "fromFA":
            scriptStr



        return {
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
            "preMbdCount": preMbdCount,
            "preFaTotal": preFaTotal,
            "angleSourceId": angleSourceId,
            "angleSourceFileName": angleSourceFileName,
            "heightMode": heightMode,
            "heightConst": heightConst,
            "heightMin": heightMin,
            "heightMax": heightMax,
            "surface": surface,
        }

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

        return {
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


    def generate_runids_for_all(self) -> List[str]:
        for row in self.scenarios:
            cfg = self.parse_scenario_by_type(row)
            runids = row.get("runids", [])
            if isinstance(cfg, FullAngleMBDConfig):
                runids.append(self.GenerateRunID())
            elif isinstance(cfg, FullAngleConfig):
                for i in range(cfg.faTotal):
                    runids.append(self.GenerateRunID())
            elif isinstance(cfg, FullAngleCumulativeConfig):
                for i in range(cfg.cumRepeatCount):
                    for j in range(cfg.cumDOECount):
                        runids.append(self.GenerateRunID())
            elif isinstance(cfg, PartialImpactConfig):
                runids.append(self.GenerateRunID())
            row["runids"] = runids
        return self.scenarios

        # ---------- 전체 실행 ----------
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
            elif isinstance(cfg, PartialImpactConfig):
                outputs.append(self.script_partial_impact(cfg))
        return outputs


# ---------- 모듈 단독 실행 테스트 ----------
if __name__ == "__main__":
    # 샘플 리스트 (보통은 외부에서 jsonOptionList를 생성해서 넘겨줌)
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
        }
    ]
    gen = KooDynaAutomaticSimulationScriptGenerator(sample)
    print(json.dumps(gen.generate_for_all(), ensure_ascii=False, indent=2))
