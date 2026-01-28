# SIMULATION_AUTOMATION 모드 상세 분석

## 1. 개요

**목적**: JSON 설정 파일을 기반으로 다양한 시뮬레이션 시나리오를 자동으로 생성하고 실행하는 메타 모드

**파일 위치**:
- 파서: `KooMeshModifier.py` (라인 776-792)
- 실행: `KooDynaAdvancedModification.py` (라인 4608-4654)
- 스크립트 생성기: `KooDynaAutomaticSimulationScriptGenerator.py`

**출력 접미사**: `_sa`

**현재 상태**: ⚠️ **개발 중** - 기본 프레임워크는 구현되었으나, 각 분석 타입별 실제 실행 로직 완성 필요

---

## 2. 설계 목표

### 2.1 최종 비전

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SIMULATION_AUTOMATION 최종 목표                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  scenarios.json                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [                                                                    │   │
│  │   { "analysisType": "fullAngleMBD", "mbdCount": 1000 },             │   │
│  │   { "analysisType": "fullAngle", "faTotal": 26 },                   │   │
│  │   { "analysisType": "fullAngleCumulative", "cumRepeatCount": 5 }    │   │
│  │ ]                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                        SIMULATION_AUTOMATION                                │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐       │
│  │ fullAngleMBD │          │  fullAngle   │          │ cumulative   │       │
│  │ MBD 시뮬로   │          │  26방향 낙하  │          │ 반복 낙하    │       │
│  │ 각도 결정   │          │  시뮬레이션   │          │ 시뮬레이션   │       │
│  └─────────────┘           └─────────────┘           └─────────────┘       │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  DROP_ATTITUDE            DROP_ATTITUDE            DROP_ATTITUDE +         │
│  DYNAIN_TO_INITIAL        DYNAIN_TO_INITIAL        DYNAIN_TO_INITIAL       │
│                                                    (반복 적용)              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 지원 예정 분석 타입

| 분석 타입 | 설명 | 구현 상태 |
|-----------|------|----------|
| fullAngleMBD | MBD 시뮬레이션으로 낙하 각도 결정 | 파싱 완료, 실행 미완 |
| fullAngle | 26방향(6면+12모서리+8코너) 낙하 | 파싱 완료, 실행 미완 |
| fullAngleCumulative | 누적 반복 낙하 시험 | 파싱 완료, 실행 미완 |
| multiRepeatCumulative | 다중 반복 누적 낙하 | 파싱 완료, 실행 미완 |
| partialImpact | 부분 충격 시험 | 파싱 완료, 실행 미완 |

---

## 3. 현재 구현 상태

### 3.1 구현 완료

1. **JSON 파서**: `KooDynaAutomaticSimulationScriptGenerator.py`
   - 모든 분석 타입 파싱 완료
   - 설정 검증 및 기본값 처리
   - RunID 자동 생성

2. **데이터 클래스 정의**:
   - `FullAngleMBDConfig`
   - `FullAngleConfig`
   - `FullAngleCumulativeConfig`
   - `MultiRepeatCumulativeConfig`
   - `PartialImpactConfig`
   - `ToleranceConfig`

3. **스크립트 생성 프레임워크**:
   - `script_full_angle_mbd()`
   - `script_full_angle()`
   - `script_full_angle_cumulative()`
   - `script_multi_repeat_cumulative()`
   - `script_partial_impact()`

### 3.2 미완성 부분

1. **실제 시뮬레이션 실행 로직**:
   - MBD 각도 계산
   - DROP_ATTITUDE 자동 호출
   - DYNAIN_TO_INITIAL 자동 체인
   - 반복 낙하 구현

2. **결과 관리**:
   - 결과 파일 수집
   - 메타데이터 업데이트
   - 후처리 자동화

---

## 4. JSON 스키마 상세

### 4.1 기본 구조

```json
[
  {
    "id": "시나리오ID",
    "name": "시나리오명",
    "fileName": "입력파일.k",
    "objFileName": "3D모델.obj",
    "runids": ["runid1", "runid2"],
    "analysisType": "분석타입",
    "params": {
      // 분석 타입별 파라미터
    }
  }
]
```

### 4.2 fullAngleMBD 파라미터

```json
{
  "analysisType": "fullAngleMBD",
  "objFileName": "phone.obj",
  "params": {
    "mbdCount": 1000,
    "angleSource": "lhs",
    "angleSourceId": null,
    "angleSourceFileName": null,
    "heightMode": "const",
    "heightConst": 1.5,
    "heightMin": 0.8,
    "heightMax": 1.5,
    "surface": "steelPlate",
    "tolerance": {
      "mode": "enabled",
      "faceTolerance": 5.0,
      "edgeTolerance": 5.0,
      "cornerTolerance": 5.0
    }
  }
}
```

**파라미터 설명**:

| 파라미터 | 타입 | 설명 | 기본값 |
|----------|------|------|--------|
| mbdCount | int | MBD 시뮬레이션 샘플 수 | 1000 |
| angleSource | string | 각도 소스 (lhs/fromMBD/usePrevResult) | "lhs" |
| angleSourceId | string | 이전 시나리오 ID (usePrevResult용) | null |
| angleSourceFileName | string | 각도 파일명 (fromMBD용) | null |
| heightMode | string | 높이 모드 (const/lhs) | "const" |
| heightConst | float | 고정 높이 (const 모드) | 1.0 |
| heightMin | float | 최소 높이 (lhs 모드) | 0.5 |
| heightMax | float | 최대 높이 (lhs 모드) | 1.5 |
| surface | string | 바닥 재질 | "steelPlate" |

**angleSource 옵션**:
- `lhs`: Latin Hypercube Sampling으로 각도 생성
- `fromMBD`: MBD 시뮬레이션 결과에서 각도 추출
- `usePrevResult`: 이전 시나리오 결과 사용

**surface 옵션**:
- `steelPlate`: 강판
- `pavingBlock`: 보도블록
- `concrete`: 콘크리트
- `wood`: 나무

### 4.3 fullAngle 파라미터

```json
{
  "analysisType": "fullAngle",
  "fileName": "model.k",
  "params": {
    "faTotal": 26,
    "includeFace6": true,
    "includeEdge12": true,
    "includeCorner8": true,
    "angleSource": "lhs",
    "heightMode": "const",
    "heightConst": 1.5,
    "surface": "steelPlate",
    "tolerance": {
      "mode": "enabled",
      "faceTolerance": 5.0,
      "edgeTolerance": 5.0,
      "cornerTolerance": 5.0
    }
  }
}
```

**파라미터 설명**:

| 파라미터 | 타입 | 설명 | 기본값 |
|----------|------|------|--------|
| faTotal | int | 총 시뮬레이션 수 | 100 |
| includeFace6 | bool | 6면 포함 | true |
| includeEdge12 | bool | 12모서리 포함 | true |
| includeCorner8 | bool | 8코너 포함 | true |

**26방향 정의**:
```
       F1 (상면)
         │
    F3 ──┼── F4
      \  │  /
       \ │ /
    F5 ──●── F6
       / │ \
      /  │  \
         F2 (하면)

모서리 (12개): E1-E12
코너 (8개): C1-C8
```

### 4.4 fullAngleCumulative 파라미터

```json
{
  "analysisType": "fullAngleCumulative",
  "fileName": "model.k",
  "params": {
    "cumRepeatCount": 3,
    "cumDOECount": 5,
    "cumDirectionsGrid": [
      ["F1", "E2", "C3"],
      ["F2", "E3", "C4"],
      ["F3", "E4", "C5"],
      ["F4", "E5", "C6"],
      ["F5", "E6", "C7"]
    ],
    "heightMode": "lhs",
    "heightMin": 0.8,
    "heightMax": 1.2,
    "surface": "pavingBlock"
  }
}
```

**파라미터 설명**:

| 파라미터 | 타입 | 설명 | 기본값 |
|----------|------|------|--------|
| cumRepeatCount | int | 1회당 반복 낙하 수 (2-5) | 3 |
| cumDOECount | int | DOE 케이스 수 | 5 |
| cumDirectionsGrid | List[List[str]] | 방향 그리드 [DOE][repeat] | 자동 생성 |

**누적 낙하 워크플로우**:
```
DOE #1:
  낙하1 (F1) → dynain →
  낙하2 (E2) → dynain →
  낙하3 (C3) → 최종 결과

DOE #2:
  낙하1 (F2) → dynain →
  낙하2 (E3) → dynain →
  낙하3 (C4) → 최종 결과

...
```

### 4.5 multiRepeatCumulative 파라미터

```json
{
  "analysisType": "multiRepeatCumulative",
  "fileName": "model.k",
  "params": {
    "multiRepeatCount": 24,
    "multiRepeatDirections": [
      "F1", "F2", "F3", "F4", "F5", "F6",
      "E1", "E2", "E3", "E4", "E5", "E6",
      "E7", "E8", "E9", "E10", "E11", "E12",
      "C1", "C2", "C3", "C4", "C5", "C6"
    ],
    "heightMode": "lhs",
    "heightMin": 0.8,
    "heightMax": 1.5,
    "surface": "concrete"
  }
}
```

**용도**: 24회 연속 낙하 시험 (내구성 테스트)

### 4.6 partialImpact 파라미터

```json
{
  "analysisType": "partialImpact",
  "fileName": "model.k",
  "params": {
    "piMode": "txt",
    "piTxtName": "impact_locations.txt"
  }
}
```

**piMode 옵션**:
- `default`: 기본 충격 위치
- `txt`: 텍스트 파일에서 위치 읽기

---

## 5. 코드 구조 분석

### 5.1 KooDynaAutomaticSimulationScriptGenerator 클래스

```python
class KooDynaAutomaticSimulationScriptGenerator:
    def __init__(self, jsonOptionList: List[ScenarioRow], metaData: Dict[str, Any]):
        self.metaData = metaData
        self.scenarios = self._sanitize(jsonOptionList)

    # 파싱 메서드
    def parse_full_angle_mbd(self, row) -> FullAngleMBDConfig
    def parse_full_angle(self, row) -> FullAngleConfig
    def parse_full_angle_cumulative(self, row) -> FullAngleCumulativeConfig
    def parse_multi_repeat_cumulative(self, row) -> MultiRepeatCumulativeConfig
    def parse_partial_impact(self, row) -> PartialImpactConfig

    # 스크립트 생성 메서드
    def script_full_angle_mbd(self, cfg) -> Dict[str, Any]
    def script_full_angle(self, cfg) -> Dict[str, Any]
    def script_full_angle_cumulative(self, cfg) -> Dict[str, Any]
    def script_multi_repeat_cumulative(self, cfg) -> Dict[str, Any]
    def script_partial_impact(self, cfg) -> Dict[str, Any]

    # 메인 실행
    def generate_runids_for_all(self) -> List[str]
    def generate_for_all(self) -> List[Dict[str, Any]]
```

### 5.2 실행 흐름 (현재)

```python
# KooDynaAdvancedModification.py (라인 4608-4610)
def SimulationAutomation(self, jsonOptionList, inputFile, inputObjFile, metaData):
    dynaASScriptGenerator = KooDynaAutomaticSimulationScriptGenerator(jsonOptionList, metaData)
    dynaASScriptGenerator.generate_for_all()  # RunID 생성 + 스크립트 딕셔너리 반환
```

### 5.3 필요한 확장 (TODO)

```python
def SimulationAutomation(self, jsonOptionList, inputFile, inputObjFile, metaData):
    dynaASScriptGenerator = KooDynaAutomaticSimulationScriptGenerator(jsonOptionList, metaData)
    outputs = dynaASScriptGenerator.generate_for_all()

    for output in outputs:
        if output["analysisType"] == "fullAngleMBD":
            # TODO: MBD 시뮬레이션 실행
            # TODO: 각도 추출
            # TODO: DROP_ATTITUDE 호출
            pass

        elif output["analysisType"] == "fullAngle":
            # TODO: 26방향 각도 계산
            # TODO: 각 방향별 DROP_ATTITUDE 호출
            # TODO: DYNAIN_TO_INITIAL 체인
            pass

        elif output["analysisType"] == "fullAngleCumulative":
            # TODO: 누적 낙하 루프
            for doe_idx in range(output["cumDOECount"]):
                for repeat_idx in range(output["cumRepeatCount"]):
                    # DROP_ATTITUDE 호출
                    # DYNAIN_TO_INITIAL 호출
                    # 다음 낙하에 결과 전달
                    pass
```

---

## 6. 사용 예시

### 6.1 설정 파일 (option.txt)

```
*Inputfile
model.k
*InputObjFile
model.obj
*Info,PhoneModel,DropTest
*Creator,Engineer,email@company.com,CAE,Team
*Mode
SIMULATION_AUTOMATION,1
**SimulationAutomation,1
JsonFile,scenarios.json
**EndSimulationAutomation
*End
```

### 6.2 시나리오 파일 (scenarios.json)

```json
[
  {
    "id": "1",
    "name": "Full Angle Drop Test",
    "analysisType": "fullAngle",
    "fileName": "model.k",
    "params": {
      "faTotal": 26,
      "includeFace6": true,
      "includeEdge12": true,
      "includeCorner8": true,
      "heightMode": "const",
      "heightConst": 1.5,
      "surface": "steelPlate"
    }
  },
  {
    "id": "2",
    "name": "Cumulative Drop Test",
    "analysisType": "fullAngleCumulative",
    "fileName": "model.k",
    "params": {
      "cumRepeatCount": 5,
      "cumDOECount": 10,
      "heightMode": "lhs",
      "heightMin": 0.8,
      "heightMax": 1.2,
      "surface": "pavingBlock"
    }
  }
]
```

---

## 7. 개발 로드맵

### Phase 1: 기본 연동 (현재 → 다음 단계)

1. [ ] fullAngle 타입에서 DROP_ATTITUDE 자동 호출
2. [ ] 26방향 오일러 각도 계산 함수 구현
3. [ ] DYNAIN_TO_INITIAL 자동 체인

### Phase 2: 누적 낙하

1. [ ] fullAngleCumulative 반복 로직
2. [ ] dynain 파일 자동 경로 관리
3. [ ] 중간 결과 저장

### Phase 3: MBD 연동

1. [ ] fullAngleMBD의 MBD 시뮬레이션 실행
2. [ ] MBD 결과에서 충격 각도 추출
3. [ ] 통계적 각도 분포 계산

### Phase 4: 후처리

1. [ ] 결과 자동 수집
2. [ ] 리포트 생성
3. [ ] 통계 분석

---

## 8. 26방향 각도 계산 참고

### 8.1 면 (Face) 방향

| ID | 방향 | Roll | Pitch | Yaw |
|----|------|------|-------|-----|
| F1 | +Z (상면) | 0 | 0 | 0 |
| F2 | -Z (하면) | 180 | 0 | 0 |
| F3 | +X (우측) | 0 | 90 | 0 |
| F4 | -X (좌측) | 0 | -90 | 0 |
| F5 | +Y (전면) | -90 | 0 | 0 |
| F6 | -Y (후면) | 90 | 0 | 0 |

### 8.2 모서리 (Edge) 방향

```
E1-E4: 상면 모서리 (Z+ 기준)
E5-E8: 중간 수직 모서리
E9-E12: 하면 모서리 (Z- 기준)
```

### 8.3 코너 (Corner) 방향

```
C1-C4: 상면 코너
C5-C8: 하면 코너
```

---

## 9. 관련 모드 연계도

```
SIMULATION_AUTOMATION
        │
        ├──► DROP_ATTITUDE ──► LS-DYNA (동적이완) ──► dynain
        │                                              │
        │                                              ▼
        ├──► DYNAIN_TO_INITIAL ◄───────────────────────┘
        │           │
        │           ▼
        │    초기응력 모델
        │           │
        │           ▼
        └──► DROP_WEIGHT_IMPACT_TEST (선택)
                    │
                    ▼
              최종 충격 해석
```

---

## 10. 결론

SIMULATION_AUTOMATION 모드는 KooMeshModifier의 **최종 목표**인 완전 자동화된 시뮬레이션 파이프라인을 구현하기 위한 핵심 모드입니다.

현재 JSON 파싱과 설정 구조는 완성되어 있으며, DROP_ATTITUDE와 DYNAIN_TO_INITIAL을 연결하는 실행 로직 구현이 필요합니다.

이 모드가 완성되면:
1. JSON 파일 하나로 수백 개의 시뮬레이션 자동 생성
2. MBD-FEA 연동 워크플로우 자동화
3. 누적 낙하 시험 자동화
4. 대규모 DOE 실험 자동 실행

가능해집니다.
