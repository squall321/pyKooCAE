# SIMULATION_AUTOMATION 분석 타입 참조

## Overview

SIMULATION_AUTOMATION은 JSON 설정을 통해 다양한 LS-DYNA 시뮬레이션을 자동화하는 모드입니다.

---

## 1. 분석 타입 요약

| 분석 타입 | 목적 | 케이스 수 |
|----------|------|----------|
| **fullAngleMBD** | MBD 시뮬레이션 기반 전각도 분석 | 1개 (MBD 내부에서 처리) |
| **fullAngle** | 전각도 드롭 분석 (6F+12E+8C) | faTotal개 |
| **fullAngleCumulative** | 누적 전각도 분석 (DOE × 반복) | cumDOECount × cumRepeatCount |
| **multiRepeatCumulative** | 다중 반복 누적 분석 | multiRepeatCount개 |
| **partialImpact** | 부분 임팩트 분석 | 1개 |

---

## 2. 분석 타입별 상세

### 2.1 fullAngleMBD (다물체동역학 기반 전각도)

MBD(Multi-Body Dynamics) 시뮬레이션 결과를 이용하여 드롭 각도 생성

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| mbdCount | int | 1000 | MBD 시뮬레이션 개수 |
| angleSource | string | - | "lhs", "fromMBD", "usePrevResult" |
| angleSourceId | string | - | 각도 소스 ID |
| angleSourceFileName | string | - | 각도 소스 파일명 |
| objFileName | string | - | OBJ 파일명 |

**angleSource 옵션**:
- `lhs`: Latin Hypercube Sampling 사용
- `fromMBD`: MBD 결과로부터 각도 생성
- `usePrevResult`: 이전 결과 활용

---

### 2.2 fullAngle (전각도 분석)

6면 + 12모서리 + 8꼭짓점 전각도 드롭

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| faTotal | int | 100 | 전체 각도 개수 |
| includeFace6 | bool | True | 6개 면 포함 여부 |
| includeEdge12 | bool | True | 12개 모서리 포함 여부 |
| includeCorner8 | bool | True | 8개 꼭짓점 포함 여부 |
| angleSource | string | - | "lhs", "fromMBD", "usePrevResult" |
| fileName | string | - | LS-DYNA 입력 파일명 |

---

### 2.3 fullAngleCumulative (누적 전각도 분석)

DOE 조건 × 반복 횟수 조합의 누적 드롭 분석

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| cumRepeatCount | int | 3 | 반복 횟수 (2~5) |
| cumDOECount | int | 5 | DOE 개수 |
| cumDirectionsGrid | 2D array | 자동생성 | [DOE][반복] 방향 배열 |
| fileName | string | - | LS-DYNA 입력 파일명 |

**방향 형식**:
- F1~F6: 면 (Face)
- E1~E12: 모서리 (Edge)
- C1~C8: 꼭짓점 (Corner)

**cumDirectionsGrid 예시**:
```json
"cumDirectionsGrid": [
  ["F1", "E2", "C3"],
  ["F2", "E3", "C4"]
]
```

---

### 2.4 multiRepeatCumulative (다중 반복 누적)

단일 방향 리스트를 여러 번 반복하는 누적 분석

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| multiRepeatCount | int | 24 | 반복 횟수 |
| multiRepeatDirections | array | 자동생성 | 방향 리스트 |
| fileName | string | - | LS-DYNA 입력 파일명 |

**multiRepeatDirections 예시**:
```json
"multiRepeatDirections": ["F1", "F2", "E1", "E2", "C1", "C2", ...]
```

---

### 2.5 partialImpact (부분 임팩트)

특정 부분 영역에만 임팩트를 적용하는 분석

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| mode | string | "default" | "default" 또는 "txt" |
| piTxtName | string | - | 설정 텍스트 파일명 |
| fileName | string | - | LS-DYNA 입력 파일명 |

---

## 3. 공통 파라미터 (partialImpact 제외)

### 3.1 높이 설정

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| heightMode | string | "const" | "const" 또는 "lhs" |
| heightConst | float | 1.0 | 고정 높이 (m) |
| heightMin | float | 0.5 | LHS 최소 높이 (m) |
| heightMax | float | 1.5 | LHS 최대 높이 (m) |

### 3.2 바닥면 설정

| 파라미터 | 타입 | 기본값 | 옵션 |
|---------|------|-------|------|
| surface | string | "steelPlate" | steelPlate, pavingBlock, concrete, wood |

### 3.3 Tolerance 설정 (선택)

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| tolerance.mode | string | - | "enabled" / "disabled" |
| tolerance.faceTolerance | float | 5.0 | 면 허용오차 (°) |
| tolerance.edgeTolerance | float | 5.0 | 모서리 허용오차 (°) |
| tolerance.cornerTolerance | float | 5.0 | 꼭짓점 허용오차 (°) |

---

## 4. JSON 설정 예시

### 4.1 fullAngleMBD 예시

```json
{
  "id": "1",
  "name": "MBD_Analysis",
  "analysisType": "fullAngleMBD",
  "objFileName": "phone.obj",
  "params": {
    "mbdCount": 1000,
    "angleSource": "lhs",
    "heightMode": "lhs",
    "heightMin": 0.8,
    "heightMax": 1.2,
    "surface": "pavingBlock",
    "tolerance": {
      "mode": "enabled",
      "faceTolerance": 5.0,
      "edgeTolerance": 5.0,
      "cornerTolerance": 5.0
    }
  }
}
```

### 4.2 fullAngle 예시

```json
{
  "id": "2",
  "name": "FullAngle_100",
  "analysisType": "fullAngle",
  "fileName": "model.k",
  "params": {
    "faTotal": 100,
    "includeFace6": true,
    "includeEdge12": true,
    "includeCorner8": true,
    "heightMode": "const",
    "heightConst": 1.5,
    "surface": "steelPlate"
  }
}
```

### 4.3 fullAngleCumulative 예시

```json
{
  "id": "3",
  "name": "Cumulative_3x5",
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
    "heightMode": "const",
    "heightConst": 1.0,
    "surface": "steelPlate"
  }
}
```

### 4.4 multiRepeatCumulative 예시

```json
{
  "id": "4",
  "name": "MultiRepeat_24",
  "analysisType": "multiRepeatCumulative",
  "fileName": "model.k",
  "params": {
    "multiRepeatCount": 24,
    "multiRepeatDirections": ["F1", "F2", "F3", "F4", "F5", "F6",
                              "E1", "E2", "E3", "E4", "E5", "E6",
                              "E7", "E8", "E9", "E10", "E11", "E12",
                              "C1", "C2", "C3", "C4", "C5", "C6"],
    "heightMode": "const",
    "heightConst": 1.5,
    "surface": "steelPlate"
  }
}
```

---

## 5. Run ID 생성 규칙

| 분석 타입 | Run ID 개수 | 생성 규칙 |
|----------|------------|----------|
| fullAngleMBD | 1 | 1개 고정 |
| fullAngle | faTotal | faTotal만큼 생성 |
| fullAngleCumulative | cumRepeatCount × cumDOECount | 반복 × DOE |
| multiRepeatCumulative | multiRepeatCount | 반복 횟수만큼 |
| partialImpact | 1 | 1개 고정 |

**Run ID 형식**: `{YYYYMMDD_HHMMSS}_{MD5_6자리}`

---

## 6. 관련 파일

- **Config 정의**: `KooCAEManager/KooDynaAutomaticSimulationScriptGenerator.py`
- **실행 로직**: `KooCAEManager/KooDynaAdvancedModification.py`
- **모드 파싱**: `KooMeshModifier.py`

---

## Author

- Creator: koo.park
- Email: koo.park@samsung.com
- Group: CAE
