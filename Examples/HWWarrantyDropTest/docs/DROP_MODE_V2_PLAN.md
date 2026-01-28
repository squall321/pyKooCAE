# DROP Mode V2 - Enhanced Architecture Plan

## 📋 현재 문제점 분석

### 1. V1의 한계점

현재 구현된 DROP 모드(V1)는 다음과 같은 제약이 있습니다:

#### 1.1 제한된 각도 소스
- **현재**: F1-F6, E1-E12, C1-C8 (26개 정형 각도)만 지원
- **문제**: 전각도 분석(Fibonacci, Pitching, Rolling)과 연동 불가
- **필요**:
  - Fibonacci 격자 (1°~40° 간격, 26~41,253 케이스)
  - Pitching 모드 (Roll 고정, Pitch 스윕)
  - Rolling 모드 (Pitch 고정, Roll 스윕)
  - 사용자 정의 각도 파일

#### 1.2 산포(Tolerance) 제한
- **현재**: 정형 각도에만 산포 적용 가능
- **문제**: F1, E1, C1 자체는 정확한 각도이며, 산포 적용 시 별도 DOE 필요
- **필요**: 각 컨디션마다 ±1°, ±2°, ±5° 등 산포 DOE 지원

#### 1.3 단일 시나리오 제약
- **현재**: 하나의 누적 시나리오만 정의 가능
- **문제**: 26개 F/E/C 각각에 대해 3-step 누적을 한번에 돌릴 수 없음
- **필요**:
  - 여러 시나리오를 병렬로 실행
  - 예: F1→F1→F1 (3회), F2→F2→F2 (3회), ..., C8→C8→C8 (3회) 총 26개 시나리오

#### 1.4 정의 불명확
- **현재**: F1-F6, E1-E12, C1-C8의 물리적 위치 정의 없음
- **문제**: 사용자가 각 컨디션이 어느 방향인지 직관적으로 알기 어려움
- **필요**: 좌표계 및 방향 벡터 명확한 정의

#### 1.5 표준 Case txt 파일 미활용
- **현재**: JSON 설정에서 각도를 직접 입력하거나 하드코딩
- **문제**: 기존에 잘 정의된 표준 Case txt 파일들을 재사용하지 못함
- **필요**:
  - 표준 Case txt 파일 직접 참조 시스템
  - 예: `26case_6F12E8C_cuboid.txt`, `fibonacci_10deg_413cases.txt` 등을 입력 파일로 직접 사용

#### 1.6 KooMeshModifier 템플릿 부재
- **현재**: 각 모드마다 KooMeshModifier 설정을 매번 수동 생성
- **문제**:
  - 표준 DROP 모델링 자동화 형식 재사용 불가
  - DYNAIN_TO_INITIAL + Dynamic Relaxation 패턴 반복 작성
  - 누적 시뮬레이션 초기화 방식 선택 불가
- **필요**:
  - KooMeshModifier 템플릿 시스템
  - 템플릿 종류:
    - `STANDARD_DROP`: 일반 낙하 (초기 상태)
    - `CUMULATIVE_DROP_WITH_DYNAIN`: DYNAIN → INITIAL 변환 + Dynamic Relaxation
    - `CUMULATIVE_DROP_DIRECT`: DYNAIN 직접 사용 (Relaxation 생략)
    - `THERMAL_INITIAL`: 열해석 초기화
    - `MIXED_MODE`: 혼합 모드 (THERM → DROP 등)

---

## 🎯 V2 목표

### 1. 다양한 각도 소스 지원

```
DROP_MODE_V2 각도 소스:
├── 1. Cuboid Geometry (정형 각도)
│   ├── F1~F6 (6 faces)
│   ├── E1~E12 (12 edges)
│   └── C1~C8 (8 corners)
│
├── 2. Fibonacci Lattice (구면 균등 분포)
│   ├── fibonacci_01deg (41,253 cases)
│   ├── fibonacci_02deg (10,313 cases)
│   ├── fibonacci_04deg (2,578 cases)
│   ├── fibonacci_05deg (1,650 cases)
│   ├── fibonacci_06deg (1,146 cases)
│   ├── fibonacci_10deg (413 cases)
│   ├── fibonacci_20deg (103 cases)
│   └── fibonacci_40deg (26 cases)
│
├── 3. Parametric Sweep (파라메트릭 스윕)
│   ├── Pitching (Roll=0 고정, Pitch -90~90°)
│   └── Rolling (Pitch=0 고정, Roll -180~170°)
│
├── 4. Standard Case txt File (표준 케이스 파일) ⭐ 신규
│   ├── 26case_6F12E8C_cuboid.txt
│   ├── fibonacci_*_*.txt
│   ├── pitching_10deg_19cases.txt
│   ├── rolling_10deg_36cases.txt
│   └── 사용자 정의 txt 파일
│
└── 5. Custom File (사용자 정의 - 기타 형식)
    └── JSON, CSV 등 사용자 제공 파일
```

### 2. 산포(Tolerance) 강화

```python
# 각 컨디션마다 산포 적용 가능
tolerance_config = {
    "base_condition": "F1",  # 또는 "E5", "C3", Fibonacci index 등
    "doe_method": "lhs",     # lhs, grid, random
    "doe_count": 10,
    "roll_range": [-2, 2],   # ±2도
    "pitch_range": [-2, 2],
    "yaw_range": [-1, 1]     # ±1도
}
```

### 3. 다중 시나리오 병렬 실행

```json
{
  "analysisType": "multiScenarioCumulative",
  "scenarios": [
    {
      "scenario_id": "F1_3drop",
      "steps": [
        {"step": 1, "mode": "DROP", "condition": "F1"},
        {"step": 2, "mode": "DROP", "condition": "F1"},
        {"step": 3, "mode": "DROP", "condition": "F1"}
      ]
    },
    {
      "scenario_id": "F2_3drop",
      "steps": [
        {"step": 1, "mode": "DROP", "condition": "F2"},
        {"step": 2, "mode": "DROP", "condition": "F2"},
        {"step": 3, "mode": "DROP", "condition": "F2"}
      ]
    },
    ... (총 26개 또는 더 많은 시나리오)
  ]
}
```

### 4. 조건 명확한 정의

F1-F6, E1-E12, C1-C8의 정확한 물리적 위치, 방향 벡터, Euler 각도 문서화

---

## 🏗️ V2 아키텍처 설계

### 1. 각도 소스 타입 확장

#### 1.1 AngleSourceType 정의

```python
from typing import Literal

AngleSourceType = Literal[
    "cuboid_geometry",    # F1-F6, E1-E12, C1-C8
    "fibonacci_lattice",  # 피보나치 격자 (케이스 수 지정)
    "pitching_sweep",     # Pitching 스윕 (Roll 고정)
    "rolling_sweep",      # Rolling 스윕 (Pitch 고정)
    "full_sweep",         # Roll × Pitch 전체 그리드
    "custom_file"         # 사용자 정의 파일
]
```

#### 1.2 각도 소스 설정 구조

```python
@dataclass
class AngleSourceConfig:
    """각도 소스 설정"""
    source_type: AngleSourceType

    # Cuboid Geometry (F/E/C)
    condition: Optional[str] = None  # "F1", "E5", "C3" 등

    # Fibonacci Lattice
    fibonacci_spacing: Optional[Literal["01deg", "02deg", "04deg", "05deg",
                                        "06deg", "10deg", "20deg", "40deg"]] = None
    fibonacci_index: Optional[int] = None  # 특정 인덱스 선택 (0-based)

    # Parametric Sweep
    sweep_config: Optional[Dict[str, Any]] = None
    # {
    #   "roll_range": [-180, 170],
    #   "roll_step": 10,
    #   "pitch_range": [-90, 90],
    #   "pitch_step": 10,
    #   "yaw_fixed": 0
    # }

    # Custom File
    custom_file_path: Optional[str] = None  # Euler 각도 파일 경로
```

### 2. Tolerance/DOE 시스템

#### 2.1 ToleranceConfig 확장

```python
@dataclass
class ToleranceConfig:
    """산포 설정 (V2)"""
    enabled: bool = False

    # DOE 방법
    method: Literal["lhs", "grid", "random", "sobol"] = "lhs"
    doe_count: int = 10

    # 각 축 산포 범위 (도)
    roll: Dict[str, float] = None   # {"min": -2, "max": 2}
    pitch: Dict[str, float] = None  # {"min": -2, "max": 2}
    yaw: Dict[str, float] = None    # {"min": -1, "max": 1}

    # 높이 산포 (옵션)
    height: Optional[Dict[str, float]] = None  # {"min": 1.4, "max": 1.6}
```

#### 2.2 사용 예시

```python
# 예시 1: F1 조건에 ±2도 산포, LHS 10개
angle_source = AngleSourceConfig(
    source_type="cuboid_geometry",
    condition="F1"
)
tolerance = ToleranceConfig(
    enabled=True,
    method="lhs",
    doe_count=10,
    roll={"min": -2, "max": 2},
    pitch={"min": -2, "max": 2},
    yaw={"min": -1, "max": 1}
)

# 예시 2: Fibonacci 10deg 격자, 특정 인덱스에 산포
angle_source = AngleSourceConfig(
    source_type="fibonacci_lattice",
    fibonacci_spacing="10deg",
    fibonacci_index=42  # 413개 중 43번째 점
)
tolerance = ToleranceConfig(
    enabled=True,
    method="grid",
    doe_count=27,  # 3×3×3 그리드
    roll={"min": -1, "max": 1},
    pitch={"min": -1, "max": 1},
    yaw={"min": -0.5, "max": 0.5}
)
```

### 3. 다중 시나리오 시스템

#### 3.1 MultiScenarioCumulative 타입

```python
@dataclass
class ScenarioDefinition:
    """개별 시나리오 정의"""
    scenario_id: str
    description: str
    steps: List[MixedStepConfig]
    tolerance: Optional[ToleranceConfig] = None

@dataclass
class MultiScenarioCumulativeConfig:
    """다중 시나리오 누적 분석"""
    id: str
    name: str
    analysisType: Literal["multiScenarioCumulative"]
    projectName: str
    scenarios: List[ScenarioDefinition]

    # 각 시나리오는 독립적으로 실행
    # 전체 작업 수 = sum(len(scenario.steps) × scenario.tolerance.doe_count for scenario in scenarios)
```

#### 3.2 사용 예시

```json
{
  "id": "26_scenario_3drop",
  "name": "26개 조건 각각 3회 낙하",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "scenarios": [
    {
      "scenario_id": "F1_3drop",
      "description": "F1 조건 3회 연속 낙하",
      "steps": [
        {"step": 1, "mode": "DROP", "condition": "F1", "params": {...}},
        {"step": 2, "mode": "DROP", "condition": "F1", "params": {...}},
        {"step": 3, "mode": "DROP", "condition": "F1", "params": {...}}
      ],
      "tolerance": {
        "enabled": true,
        "method": "lhs",
        "doe_count": 5,
        "roll": {"min": -1, "max": 1},
        "pitch": {"min": -1, "max": 1},
        "yaw": {"min": -0.5, "max": 0.5}
      }
    },
    {
      "scenario_id": "F2_3drop",
      "description": "F2 조건 3회 연속 낙하",
      "steps": [
        {"step": 1, "mode": "DROP", "condition": "F2", "params": {...}},
        {"step": 2, "mode": "DROP", "condition": "F2", "params": {...}},
        {"step": 3, "mode": "DROP", "condition": "F2", "params": {...}}
      ],
      "tolerance": {
        "enabled": true,
        "method": "lhs",
        "doe_count": 5,
        "roll": {"min": -1, "max": 1},
        "pitch": {"min": -1, "max": 1},
        "yaw": {"min": -0.5, "max": 0.5}
      }
    }
    ... (F3~F6, E1~E12, C1~C8 계속)
  ]
}
```

---

## 📐 조건 정의 (F1-F6, E1-E12, C1-C8)

### 1. 좌표계 정의

```
스마트폰 좌표계 (LS-DYNA 글로벌 좌표계)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────┐
│             │ ↑ +Y (위)
│   DISPLAY   │
│   (Front)   │
│             │
└─────────────┘
      ↗ +X (오른쪽)
     /
    ↙ +Z (전면, 디스플레이 방향)

원점: 스마트폰 하단 중심
```

**Euler 각도 순서**: Roll → Pitch → Yaw (Z-Y-X 내재 회전)

### 2. Face 조건 (6개)

| ID | 방향명 | 물리적 위치 | 방향 벡터 (x,y,z) | Roll | Pitch | Yaw | 설명 |
|----|--------|------------|------------------|------|-------|-----|------|
| **F1** | Back | 후면 (뒷면) | (0, 0, -1) | 0° | 0° | 0° | 디스플레이 반대편 (카메라 쪽) |
| **F2** | Front | 전면 (앞면) | (0, 0, +1) | 180° | 0° | 0° | 디스플레이 쪽 |
| **F3** | Right | 우측면 | (+1, 0, 0) | 0° | -90° | 0° | 오른쪽 측면 |
| **F4** | Left | 좌측면 | (-1, 0, 0) | 0° | +90° | 0° | 왼쪽 측면 |
| **F5** | Top | 상단면 | (0, +1, 0) | 90° | 0° | 0° | 윗면 (헤드폰 잭 방향) |
| **F6** | Bottom | 하단면 | (0, -1, 0) | -90° | 0° | 0° | 아랫면 (충전 포트 방향) |

### 3. Edge 조건 (12개)

| ID | 방향명 | 물리적 위치 | 방향 벡터 (정규화) | Roll | Pitch | Yaw | 설명 |
|----|--------|------------|-------------------|------|-------|-----|------|
| **E1** | Back-Right | 후면-우측 모서리 | (+0.707, 0, -0.707) | 0° | -45° | 0° | 후면과 우측 경계 |
| **E2** | Back-Left | 후면-좌측 모서리 | (-0.707, 0, -0.707) | 0° | +45° | 0° | 후면과 좌측 경계 |
| **E3** | Back-Top | 후면-상단 모서리 | (0, +0.707, -0.707) | 45° | 0° | 0° | 후면과 상단 경계 |
| **E4** | Back-Bottom | 후면-하단 모서리 | (0, -0.707, -0.707) | -45° | 0° | 0° | 후면과 하단 경계 |
| **E5** | Front-Right | 전면-우측 모서리 | (+0.707, 0, +0.707) | 180° | +45° | 0° | 전면과 우측 경계 |
| **E6** | Front-Left | 전면-좌측 모서리 | (-0.707, 0, +0.707) | 180° | -45° | 0° | 전면과 좌측 경계 |
| **E7** | Front-Top | 전면-상단 모서리 | (0, +0.707, +0.707) | 135° | 0° | 0° | 전면과 상단 경계 |
| **E8** | Front-Bottom | 전면-하단 모서리 | (0, -0.707, +0.707) | -135° | 0° | 0° | 전면과 하단 경계 |
| **E9** | Right-Top | 우측-상단 모서리 | (+0.707, +0.707, 0) | 90° | -45° | 0° | 우측과 상단 경계 |
| **E10** | Right-Bottom | 우측-하단 모서리 | (+0.707, -0.707, 0) | -90° | -45° | 0° | 우측과 하단 경계 |
| **E11** | Left-Top | 좌측-상단 모서리 | (-0.707, +0.707, 0) | 90° | +45° | 0° | 좌측과 상단 경계 |
| **E12** | Left-Bottom | 좌측-하단 모서리 | (-0.707, -0.707, 0) | -90° | +45° | 0° | 좌측과 하단 경계 |

### 4. Corner 조건 (8개)

| ID | 방향명 | 물리적 위치 | 방향 벡터 (정규화) | Roll | Pitch | Yaw | 설명 |
|----|--------|------------|-------------------|------|-------|-----|------|
| **C1** | Back-Right-Top | 후면-우측-상단 꼭짓점 | (+0.577, +0.577, -0.577) | 45° | -45° | 0° | 후면, 우측, 상단 교점 |
| **C2** | Back-Right-Bottom | 후면-우측-하단 꼭짓점 | (+0.577, -0.577, -0.577) | -45° | -45° | 0° | 후면, 우측, 하단 교점 |
| **C3** | Back-Left-Top | 후면-좌측-상단 꼭짓점 | (-0.577, +0.577, -0.577) | 45° | +45° | 0° | 후면, 좌측, 상단 교점 |
| **C4** | Back-Left-Bottom | 후면-좌측-하단 꼭짓점 | (-0.577, -0.577, -0.577) | -45° | +45° | 0° | 후면, 좌측, 하단 교점 |
| **C5** | Front-Right-Top | 전면-우측-상단 꼭짓점 | (+0.577, +0.577, +0.577) | 135° | +45° | 0° | 전면, 우측, 상단 교점 |
| **C6** | Front-Right-Bottom | 전면-우측-하단 꼭짓점 | (+0.577, -0.577, +0.577) | -135° | +45° | 0° | 전면, 우측, 하단 교점 |
| **C7** | Front-Left-Top | 전면-좌측-상단 꼭짓점 | (-0.577, +0.577, +0.577) | 135° | -45° | 0° | 전면, 좌측, 상단 교점 |
| **C8** | Front-Left-Bottom | 전면-좌측-하단 꼭짓점 | (-0.577, -0.577, +0.577) | -135° | -45° | 0° | 전면, 좌측, 하단 교점 |

**주의**:
- 방향 벡터는 **중력 방향** (낙하 시 땅을 향하는 방향)
- Corner 방향 벡터는 (1/√3, 1/√3, 1/√3) ≈ (0.577, 0.577, 0.577) 정규화

### 5. 시각적 다이어그램

```
           E3         E7
        C3 ●━━━━━━━━━● C7
         ╱│          ╱│
     E11╱ │      E9 ╱ │
       ╱  │E2     ╱  │E6
   C4 ●━━━━━━━━━● C8 │
      │   │ F4   │ F2│
      │E4 ●━━━━━━│━━━● E8
      │  ╱ C1    │  ╱ C5
   E12│ ╱     E10│ ╱
      │╱   F1    │╱
      ●━━━━━━━━━●
     C2   E1    C6

Face:
  F1: Back (후면)
  F2: Front (전면)
  F3: Right (우측)
  F4: Left (좌측)
  F5: Top (상단)
  F6: Bottom (하단)
```

---

## 🔄 Fibonacci & Sweep 각도 소스

### 1. Fibonacci Lattice 파일 구조

```
Examples/HWWarrantyDropTest/FullAngleDrop/
├── fibonacci_01deg_41253cases.txt  (1° 간격, 41,253 케이스)
├── fibonacci_02deg_10313cases.txt  (2° 간격, 10,313 케이스)
├── fibonacci_04deg_2578cases.txt   (4° 간격, 2,578 케이스)
├── fibonacci_05deg_1650cases.txt   (5° 간격, 1,650 케이스)
├── fibonacci_06deg_1146cases.txt   (6° 간격, 1,146 케이스)
├── fibonacci_10deg_413cases.txt    (10° 간격, 413 케이스)
├── fibonacci_20deg_103cases.txt    (20° 간격, 103 케이스)
└── fibonacci_40deg_26cases.txt     (40° 간격, 26 케이스)
```

**파일 형식**: 각 줄은 `name, roll, pitch, yaw`
```
P0001, 45.23, -12.67, 0.00
P0002, -32.11, 87.45, 0.00
...
```

### 2. Parametric Sweep 파일 구조

```
Examples/HWWarrantyDropTest/FullAngleDrop/
├── pitching_10deg_19cases.txt   (Pitch -90~90°, Roll=0 고정)
└── rolling_10deg_36cases.txt    (Roll -180~170°, Pitch=0 고정)
```

**pitching_10deg_19cases.txt**:
- Roll = 0° (고정)
- Pitch = -90° ~ +90° (10° 간격, 19개)
- Yaw = 0°

**rolling_10deg_36cases.txt**:
- Roll = -180° ~ +170° (10° 간격, 36개)
- Pitch = 0° (고정)
- Yaw = 0°

---

## 🛠️ 구현 계획

### Phase 1: 각도 소스 확장 (Designer)

#### 1.1 AngleSource 파서 구현

```python
def parse_angle_source(angle_config: AngleSourceConfig) -> List[Tuple[str, float, float, float]]:
    """
    각도 소스 설정 → (name, roll, pitch, yaw) 리스트 반환

    Returns:
        List of (condition_name, roll, pitch, yaw)
    """
    if angle_config.source_type == "cuboid_geometry":
        return parse_cuboid_geometry(angle_config.condition)

    elif angle_config.source_type == "fibonacci_lattice":
        return parse_fibonacci_lattice(
            angle_config.fibonacci_spacing,
            angle_config.fibonacci_index
        )

    elif angle_config.source_type == "pitching_sweep":
        return parse_pitching_sweep(angle_config.sweep_config)

    elif angle_config.source_type == "rolling_sweep":
        return parse_rolling_sweep(angle_config.sweep_config)

    elif angle_config.source_type == "full_sweep":
        return parse_full_sweep(angle_config.sweep_config)

    elif angle_config.source_type == "custom_file":
        return parse_custom_file(angle_config.custom_file_path)

    else:
        raise ValueError(f"Unknown angle source type: {angle_config.source_type}")
```

#### 1.2 Cuboid Geometry 매핑 (기존 코드 활용)

```python
CUBOID_GEOMETRY_MAP = {
    # Faces (6)
    "F1": ("Back", 0, 0, 0),
    "F2": ("Front", 180, 0, 0),
    "F3": ("Right", 0, -90, 0),
    "F4": ("Left", 0, 90, 0),
    "F5": ("Top", 90, 0, 0),
    "F6": ("Bottom", -90, 0, 0),

    # Edges (12)
    "E1": ("Back-Right", 0, -45, 0),
    "E2": ("Back-Left", 0, 45, 0),
    "E3": ("Back-Top", 45, 0, 0),
    "E4": ("Back-Bottom", -45, 0, 0),
    "E5": ("Front-Right", 180, 45, 0),
    "E6": ("Front-Left", 180, -45, 0),
    "E7": ("Front-Top", 135, 0, 0),
    "E8": ("Front-Bottom", -135, 0, 0),
    "E9": ("Right-Top", 90, -45, 0),
    "E10": ("Right-Bottom", -90, -45, 0),
    "E11": ("Left-Top", 90, 45, 0),
    "E12": ("Left-Bottom", -90, 45, 0),

    # Corners (8)
    "C1": ("Back-Right-Top", 45, -45, 0),
    "C2": ("Back-Right-Bottom", -45, -45, 0),
    "C3": ("Back-Left-Top", 45, 45, 0),
    "C4": ("Back-Left-Bottom", -45, 45, 0),
    "C5": ("Front-Right-Top", 135, 45, 0),
    "C6": ("Front-Right-Bottom", -135, 45, 0),
    "C7": ("Front-Left-Top", 135, -45, 0),
    "C8": ("Front-Left-Bottom", -135, -45, 0),
}

def parse_cuboid_geometry(condition: str) -> List[Tuple[str, float, float, float]]:
    """F1~C8 조건 파싱"""
    if condition not in CUBOID_GEOMETRY_MAP:
        raise ValueError(f"Invalid cuboid geometry condition: {condition}")

    name, roll, pitch, yaw = CUBOID_GEOMETRY_MAP[condition]
    return [(condition, roll, pitch, yaw)]
```

#### 1.3 Fibonacci Lattice 파서

```python
def parse_fibonacci_lattice(spacing: str, index: Optional[int] = None) -> List[Tuple[str, float, float, float]]:
    """
    Fibonacci 격자 파일 읽기

    Parameters:
        spacing: "01deg", "02deg", ..., "40deg"
        index: 특정 인덱스만 선택 (None이면 전체)

    Returns:
        List of (name, roll, pitch, yaw)
    """
    file_path = f"FullAngleDrop/fibonacci_{spacing}_{FIBONACCI_CASE_COUNT[spacing]}cases.txt"

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # KooMeshModifier 입력 파일 형식 파싱
    # EulerRolling, EulerPitching, EulerYawing 줄 찾기
    angles = []
    for line in lines:
        if line.startswith("EulerRolling"):
            rolls = [float(x) for x in line.split(',')[1:]]
        elif line.startswith("EulerPitching"):
            pitches = [float(x) for x in line.split(',')[1:]]
        elif line.startswith("EulerYawing"):
            yaws = [float(x) for x in line.split(',')[1:]]

    # (name, roll, pitch, yaw) 생성
    results = []
    for i, (r, p, y) in enumerate(zip(rolls, pitches, yaws)):
        if index is None or i == index:
            name = f"FIB{spacing.upper()}_{i:04d}"
            results.append((name, r, p, y))

    return results

FIBONACCI_CASE_COUNT = {
    "01deg": 41253,
    "02deg": 10313,
    "04deg": 2578,
    "05deg": 1650,
    "06deg": 1146,
    "10deg": 413,
    "20deg": 103,
    "40deg": 26,
}
```

#### 1.4 Pitching/Rolling Sweep 파서

```python
def parse_pitching_sweep(config: Dict[str, Any]) -> List[Tuple[str, float, float, float]]:
    """
    Pitching 스윕 (Roll 고정)

    config = {
        "pitch_min": -90,
        "pitch_max": 90,
        "pitch_step": 10,
        "roll_fixed": 0,
        "yaw_fixed": 0
    }
    """
    results = []
    roll = config.get("roll_fixed", 0)
    yaw = config.get("yaw_fixed", 0)

    pitch_min = config["pitch_min"]
    pitch_max = config["pitch_max"]
    pitch_step = config["pitch_step"]

    for pitch in range(pitch_min, pitch_max + 1, pitch_step):
        name = f"PITCH_{pitch:+04d}"
        results.append((name, roll, pitch, yaw))

    return results

def parse_rolling_sweep(config: Dict[str, Any]) -> List[Tuple[str, float, float, float]]:
    """
    Rolling 스윕 (Pitch 고정)

    config = {
        "roll_min": -180,
        "roll_max": 170,
        "roll_step": 10,
        "pitch_fixed": 0,
        "yaw_fixed": 0
    }
    """
    results = []
    pitch = config.get("pitch_fixed", 0)
    yaw = config.get("yaw_fixed", 0)

    roll_min = config["roll_min"]
    roll_max = config["roll_max"]
    roll_step = config["roll_step"]

    for roll in range(roll_min, roll_max + 1, roll_step):
        name = f"ROLL_{roll:+04d}"
        results.append((name, roll, pitch, yaw))

    return results
```

### Phase 2: Tolerance/DOE 시스템 (Designer)

#### 2.1 DOE 생성 함수

```python
def apply_tolerance_doe(
    base_angles: List[Tuple[str, float, float, float]],
    tolerance: ToleranceConfig
) -> List[Tuple[str, float, float, float, int]]:
    """
    각도 리스트에 산포 DOE 적용

    Parameters:
        base_angles: (name, roll, pitch, yaw)
        tolerance: 산포 설정

    Returns:
        List of (name, roll, pitch, yaw, doe_index)
    """
    if not tolerance.enabled:
        return [(n, r, p, y, 0) for n, r, p, y in base_angles]

    results = []

    for base_name, base_roll, base_pitch, base_yaw in base_angles:
        if tolerance.method == "lhs":
            doe_samples = generate_lhs_samples(tolerance)
        elif tolerance.method == "grid":
            doe_samples = generate_grid_samples(tolerance)
        elif tolerance.method == "random":
            doe_samples = generate_random_samples(tolerance)
        else:
            raise ValueError(f"Unknown DOE method: {tolerance.method}")

        for doe_idx, (d_roll, d_pitch, d_yaw) in enumerate(doe_samples):
            new_name = f"{base_name}_DOE{doe_idx:03d}"
            new_roll = base_roll + d_roll
            new_pitch = base_pitch + d_pitch
            new_yaw = base_yaw + d_yaw
            results.append((new_name, new_roll, new_pitch, new_yaw, doe_idx))

    return results

def generate_lhs_samples(tolerance: ToleranceConfig) -> List[Tuple[float, float, float]]:
    """LHS (Latin Hypercube Sampling) 생성"""
    from scipy.stats import qmc

    n = tolerance.doe_count
    sampler = qmc.LatinHypercube(d=3)  # 3D: roll, pitch, yaw
    samples = sampler.random(n=n)

    # [0, 1] → [min, max] 변환
    roll_min, roll_max = tolerance.roll["min"], tolerance.roll["max"]
    pitch_min, pitch_max = tolerance.pitch["min"], tolerance.pitch["max"]
    yaw_min, yaw_max = tolerance.yaw["min"], tolerance.yaw["max"]

    results = []
    for s in samples:
        roll = roll_min + s[0] * (roll_max - roll_min)
        pitch = pitch_min + s[1] * (pitch_max - pitch_min)
        yaw = yaw_min + s[2] * (yaw_max - yaw_min)
        results.append((roll, pitch, yaw))

    return results
```

### Phase 3: 다중 시나리오 지원 (Designer)

#### 3.1 MultiScenarioCumulative 파서

```python
def parse_multi_scenario_cumulative(json_path: str) -> MultiScenarioCumulativeConfig:
    """multiScenarioCumulative JSON 파싱"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    scenarios = []
    for scenario_data in data["scenarios"]:
        steps = []
        for step_data in scenario_data["steps"]:
            step = MixedStepConfig(
                step=step_data["step"],
                mode=step_data["mode"],
                mode_full=SIMULATION_MODES[step_data["mode"]]["full_name"],
                condition=step_data["condition"],
                params=step_data.get("params", {})
            )
            steps.append(step)

        tolerance = None
        if "tolerance" in scenario_data:
            tolerance = ToleranceConfig(**scenario_data["tolerance"])

        scenario = ScenarioDefinition(
            scenario_id=scenario_data["scenario_id"],
            description=scenario_data["description"],
            steps=steps,
            tolerance=tolerance
        )
        scenarios.append(scenario)

    return MultiScenarioCumulativeConfig(
        id=data["id"],
        name=data["name"],
        analysisType="multiScenarioCumulative",
        projectName=data["projectName"],
        scenarios=scenarios
    )
```

#### 3.2 MultiScenario → runner_config 변환

```python
def generate_multi_scenario_runner_config(config: MultiScenarioCumulativeConfig) -> dict:
    """
    MultiScenarioCumulativeConfig → runner_config.json

    각 시나리오는 독립적인 "doe_index" 그룹으로 취급
    """
    runner_config = {
        "project_name": config.projectName,
        "analysis_type": "multiScenarioCumulative",
        "total_scenarios": len(config.scenarios),
        "scenarios": []
    }

    scenario_index = 0
    for scenario_def in config.scenarios:
        # 각도 소스 파싱 (첫 스텝의 condition 기준)
        first_condition = scenario_def.steps[0].condition
        angle_source = AngleSourceConfig(source_type="cuboid_geometry", condition=first_condition)
        base_angles = parse_angle_source(angle_source)

        # Tolerance 적용
        doe_angles = apply_tolerance_doe(base_angles, scenario_def.tolerance or ToleranceConfig())

        for doe_idx, (cond_name, roll, pitch, yaw, _) in enumerate(doe_angles):
            scenario_entry = {
                "scenario_id": f"{scenario_def.scenario_id}_DOE{doe_idx:03d}",
                "original_scenario_id": scenario_def.scenario_id,
                "doe_index": doe_idx,
                "total_steps": len(scenario_def.steps),
                "steps": []
            }

            for step_config in scenario_def.steps:
                step_entry = {
                    "step": step_config.step,
                    "mode": step_config.mode,
                    "condition": step_config.condition,
                    "roll": roll,
                    "pitch": pitch,
                    "yaw": yaw,
                    "params": step_config.params
                }
                scenario_entry["steps"].append(step_entry)

            runner_config["scenarios"].append(scenario_entry)

        scenario_index += 1

    return runner_config
```

### Phase 4: 표준 Case txt 파일 시스템 ⭐ 신규

#### 4.1 표준 Case txt 파일 형식

**목적**: 기존에 잘 정의된 표준 낙하 각도 파일을 재사용하여 JSON 설정을 단순화

**표준 형식**:
```
*Inputfile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,Smartphone,FullAngle_26case_Cuboid
*Description,Full Angle Drop - 26 cases (6 Face + 12 Edge + 8 Corner)
*Creator,koo.park,koo.park@samsung.com,CAE,HE
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ ============================================================================
$ Case names (comma-separated)
$ F1_Back,F2_Front,F3_Right,...
EulerRolling,0,180,0,0,90,-90,...
EulerPitching,0,0,-90,90,0,0,...
EulerYawing,0,0,0,0,0,0,...
Height,1500,1500,1500,...
InitialVelocityX,0,0,0,...
InitialVelocityY,0,0,0,...
InitialVelocityZ,0,0,0,...
InitialAngularVelocityX,0,0,0,...
InitialAngularVelocityY,0,0,0,...
InitialAngularVelocityZ,0,0,0,...
OffsetDistance,0.1
Density,7850
YoungsModulus,200000000000
PoissonRatio,0.3
tFinal,0.005
dt,0.000001
DropSurface,Plane,300,300,20,30,30,2
**EndDropAttitude
*End
```

#### 4.2 표준 Case txt 파일 목록

| 파일명 | 케이스 수 | 설명 | 각도 형식 |
|--------|----------|------|----------|
| `26case_6F12E8C_cuboid.txt` | 26 | 직육면체 기하 (6F+12E+8C) | 정형 각도 |
| `fibonacci_01deg_41253cases.txt` | 41,253 | Fibonacci 1° 간격 | 구면 균등 분포 |
| `fibonacci_02deg_10313cases.txt` | 10,313 | Fibonacci 2° 간격 | 구면 균등 분포 |
| `fibonacci_04deg_2578cases.txt` | 2,578 | Fibonacci 4° 간격 | 구면 균등 분포 |
| `fibonacci_05deg_1650cases.txt` | 1,650 | Fibonacci 5° 간격 | 구면 균등 분포 |
| `fibonacci_06deg_1146cases.txt` | 1,146 | Fibonacci 6° 간격 | 구면 균등 분포 |
| `fibonacci_10deg_413cases.txt` | 413 | Fibonacci 10° 간격 | 구면 균등 분포 |
| `fibonacci_20deg_103cases.txt` | 103 | Fibonacci 20° 간격 | 구면 균등 분포 |
| `fibonacci_40deg_26cases.txt` | 26 | Fibonacci 40° 간격 | 구면 균등 분포 |
| `pitching_10deg_19cases.txt` | 19 | Pitching 스윕 (Roll=0) | Pitch -90~90° |
| `rolling_10deg_36cases.txt` | 36 | Rolling 스윕 (Pitch=0) | Roll -180~170° |

#### 4.3 각도 믹싱 전략 시스템 ⭐

**목적**: 누적 시뮬레이션에서 각 스텝의 각도를 어떻게 샘플링할지 정의

```python
from typing import Literal
import random
import numpy as np

AngleMixingStrategy = Literal[
    "same_angle",      # 동일 각도 반복
    "cyclic",          # 순환 (인덱스 +offset)
    "random",          # 랜덤 샘플링
    "opposite",        # 대칭 각도
    "custom_mapping"   # 사용자 정의
]

@dataclass
class CumulativeAngleConfig:
    """누적 시뮬레이션 각도 설정"""
    repeat_count: int  # 반복 횟수 (2~10)
    angle_mixing_strategy: AngleMixingStrategy

    # Cyclic 전략 파라미터
    cyclic_offset: Optional[int] = 1  # 순환 오프셋

    # Random 전략 파라미터
    random_seed: Optional[int] = None  # 재현성 시드

    # Custom Mapping 전략 파라미터
    step_angle_sources: Optional[List[Any]] = None  # 각 스텝별 각도 소스

    # 템플릿
    templates: List[str] = None  # 각 스텝별 템플릿

def generate_cumulative_angle_sequences(
    base_angles: List[Tuple[str, float, float, float]],
    config: CumulativeAngleConfig
) -> List[List[Tuple[str, float, float, float]]]:
    """
    누적 시뮬레이션을 위한 각도 시퀀스 생성

    Parameters:
        base_angles: 기본 각도 리스트 [(name, roll, pitch, yaw), ...]
        config: 누적 각도 설정

    Returns:
        List of sequences: [
            [Step1_angles, Step2_angles, ...],  # Scenario 0
            [Step1_angles, Step2_angles, ...],  # Scenario 1
            ...
        ]
    """
    n_cases = len(base_angles)
    sequences = []

    if config.angle_mixing_strategy == "same_angle":
        # 전략 1: 동일 각도 반복
        for i, angle in enumerate(base_angles):
            sequence = [angle] * config.repeat_count
            sequences.append(sequence)

    elif config.angle_mixing_strategy == "cyclic":
        # 전략 2: 순환
        offset = config.cyclic_offset
        for i in range(n_cases):
            sequence = []
            for step in range(config.repeat_count):
                idx = (i + step * offset) % n_cases
                sequence.append(base_angles[idx])
            sequences.append(sequence)

    elif config.angle_mixing_strategy == "random":
        # 전략 3: 랜덤
        if config.random_seed is not None:
            random.seed(config.random_seed)

        for i in range(n_cases):
            sequence = [base_angles[i]]  # 첫 스텝은 원래 각도
            for step in range(1, config.repeat_count):
                random_idx = random.randint(0, n_cases - 1)
                sequence.append(base_angles[random_idx])
            sequences.append(sequence)

    elif config.angle_mixing_strategy == "opposite":
        # 전략 4: 대칭 각도
        for i, (name, roll, pitch, yaw) in enumerate(base_angles):
            sequence = [(name, roll, pitch, yaw)]

            # 반대편 각도 계산 (구면 대칭)
            opposite_roll = -roll if abs(roll) != 90 else roll
            opposite_pitch = (pitch + 180) % 360 - 180
            opposite_yaw = (yaw + 180) % 360 - 180

            opposite_name = f"{name}_OPP"
            sequence.append((opposite_name, opposite_roll, opposite_pitch, opposite_yaw))

            # 3회 이상이면 원래 각도 반복
            for step in range(2, config.repeat_count):
                sequence.append((name, roll, pitch, yaw))

            sequences.append(sequence)

    elif config.angle_mixing_strategy == "custom_mapping":
        # 전략 5: 사용자 정의 매핑
        if not config.step_angle_sources:
            raise ValueError("custom_mapping requires step_angle_sources")

        # 각 스텝별로 서로 다른 각도 소스 사용
        step_angle_lists = []
        for source in config.step_angle_sources:
            angles = parse_case_txt_file(source)  # 각 소스 파싱
            step_angle_lists.append(angles)

        # 최소 길이 찾기
        min_length = min(len(angles) for angles in step_angle_lists)

        for i in range(min_length):
            sequence = [step_angles[i] for step_angles in step_angle_lists]
            sequences.append(sequence)

    else:
        raise ValueError(f"Unknown angle mixing strategy: {config.angle_mixing_strategy}")

    return sequences
```

#### 4.4 Case txt 파일 파서 구현

```python
@dataclass
class CaseTxtConfig:
    """표준 Case txt 파일 설정"""
    file_path: str
    case_indices: Optional[List[int]] = None  # None이면 전체, 아니면 특정 인덱스만 선택
    apply_tolerance: bool = False
    tolerance: Optional[ToleranceConfig] = None

def parse_case_txt_file(config: CaseTxtConfig) -> List[Tuple[str, float, float, float]]:
    """
    표준 Case txt 파일 파싱

    Parameters:
        config: Case txt 파일 설정

    Returns:
        List of (case_name, roll, pitch, yaw)
    """
    with open(config.file_path, 'r') as f:
        lines = f.readlines()

    # 각도 데이터 추출
    rolls = []
    pitches = []
    yaws = []
    case_names = []

    for line in lines:
        line = line.strip()
        if line.startswith('$ ') and ',' in line:
            # Case 이름 줄: $ F1_Back,F2_Front,...
            case_names = [name.strip() for name in line[2:].split(',')]
        elif line.startswith('EulerRolling,'):
            rolls = [float(x.strip()) for x in line.split(',')[1:]]
        elif line.startswith('EulerPitching,'):
            pitches = [float(x.strip()) for x in line.split(',')[1:]]
        elif line.startswith('EulerYawing,'):
            yaws = [float(x.strip()) for x in line.split(',')[1:]]

    # Case 이름이 없으면 자동 생성
    if not case_names or len(case_names) != len(rolls):
        case_names = [f"CASE{i+1:04d}" for i in range(len(rolls))]

    # (name, roll, pitch, yaw) 생성
    results = []
    for i, (name, roll, pitch, yaw) in enumerate(zip(case_names, rolls, pitches, yaws)):
        # 특정 인덱스만 선택
        if config.case_indices is None or i in config.case_indices:
            results.append((name, roll, pitch, yaw))

    return results
```

#### 4.4 Case txt 파일 사용 예시

**예시 1: Fibonacci 10deg 전체 케이스 (413개) 사용**

```json
{
  "id": "fibonacci_10deg_full",
  "name": "Fibonacci 10deg 413케이스 단일 낙하",
  "analysisType": "singleDrop",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt",
      "case_indices": null
    }
  },
  "params": {"height": 1.5, "surface": "steelPlate"}
}
```

**예시 2: Fibonacci 10deg 특정 케이스만 선택 (0, 50, 100, 200, 400번 인덱스)**

```json
{
  "id": "fibonacci_10deg_partial",
  "name": "Fibonacci 10deg 5개 케이스만",
  "analysisType": "singleDrop",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt",
      "case_indices": [0, 50, 100, 200, 400]
    }
  },
  "params": {"height": 1.5}
}
```

**예시 3: 26case Cuboid + Tolerance ±2°**

```json
{
  "id": "cuboid_26_with_tolerance",
  "name": "Cuboid 26케이스 + 산포",
  "analysisType": "singleDrop",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/26case_6F12E8C_cuboid.txt"
    }
  },
  "tolerance": {
    "enabled": true,
    "method": "lhs",
    "doe_count": 10,
    "roll": {"min": -2, "max": 2},
    "pitch": {"min": -2, "max": 2},
    "yaw": {"min": -1, "max": 1}
  }
}
```
→ 결과: 26 케이스 × 10 DOE = 260개 시뮬레이션

**예시 4: Pitching 19케이스 사용**

```json
{
  "id": "pitching_19cases",
  "name": "Pitching 스윕 19케이스",
  "analysisType": "singleDrop",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/pitching_10deg_19cases.txt"
    }
  }
}
```

---

### Phase 5: KooMeshModifier 워크플로 이해 ⭐ 중요

#### 5.1 기존 DROP_ATTITUDE 자동 워크플로

**DROP_ATTITUDE는 이미 완벽한 누적 낙하 시스템을 내장하고 있습니다!**

```python
# DROP_ATTITUDE 실행 시 자동 처리:
def DropAttitude(...):
    # 1. Dynamic Relaxation 자동 추가
    partSet = self.dynaImporter.partManager.CreatePartSet(name="Dynamic Relaxation Set")
    self.dynaImporter.additionalManager.CreateInterfaceSpringbackLSDyna(partSet.psid)
    # → *CONTROL_DYNAMIC_RELAXATION 자동 포함 ⭐

    # 2. DropSet.k 파일 생성 (Output/, DynamicRelaxation/ 폴더에 복사)
    self.WriteModifiedFile(modifiedKeyword, "", True)

    # 3. dynaintoinitial.txt 생성 (다음 스텝용)
    with open(dynaintoinitialPath, "w") as f:
        f.write("*Mode\n")
        f.write("DYNAIN_TO_INITIAL,1\n")
        f.write("**DynainPath," + dynainPath + "\n")
        f.write("*IncludeStress,True\n")  # ⭐ 응력 포함
        f.write("*RemoveDynamicRelaxation,True\n")  # ⭐ DR 제거
        f.write("*MovetoOriginAutomatic,True\n")  # ⭐ 원점 이동
        f.write("*RemovePartbyID," + str(part.id) + "\n")  # ⭐ 바닥면 제거
        f.write("*RemoveContactbyID," + str(contact.cid) + "\n")  # ⭐ 접촉 제거
```

#### 5.2 실제 누적 낙하 워크플로

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 첫 번째 낙하 (DROP_ATTITUDE)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. DropSet.k 생성                                           │
│    └─ *CONTROL_DYNAMIC_RELAXATION 자동 포함 ⭐              │
│ 2. LS-DYNA 실행                                             │
│    ├─ Dynamic Relaxation (중력 안정화)                      │
│    └─ 낙하 시뮬레이션                                        │
│ 3. Output/dynain 생성                                       │
│ 4. DynamicRelaxation/dynaintoinitial.txt 생성 ⭐            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DYNAIN_TO_INITIAL 처리 (자동)                               │
├─────────────────────────────────────────────────────────────┤
│ 1. dynain 파일 읽기                                         │
│ 2. *INITIAL_FOAM_REFERENCE_GEOMETRY 생성                    │
│ 3. *INITIAL_STRESS_SHELL 생성                               │
│ 4. *CONTROL_DYNAMIC_RELAXATION 제거 ⭐                      │
│ 5. 바닥면 파트 제거                                          │
│ 6. 접촉 카드 제거                                            │
│ 7. 원점 이동 (MovetoOriginAutomatic)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 두 번째 낙하 (DROP_ATTITUDE)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. INITIAL 상태에서 새로운 DropSet.k 생성                   │
│    └─ *CONTROL_DYNAMIC_RELAXATION 자동 추가 ⭐ (다시!)      │
│ 2. LS-DYNA 실행                                             │
│    ├─ Dynamic Relaxation (변형 상태 안정화)                 │
│    └─ 새 각도로 낙하                                         │
│ 3. Output/dynain 생성                                       │
│ 4. dynaintoinitial.txt 생성 (Step 3용)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                        (반복...)
```

#### 5.3 핵심 포인트

**✅ 이미 구현되어 있는 것:**
1. **Dynamic Relaxation 자동 추가**: 모든 DROP_ATTITUDE 실행 시 자동 포함
2. **DYNAIN_TO_INITIAL 자동 설정**: dynaintoinitial.txt 자동 생성
3. **Dynamic Relaxation 제거**: `*RemoveDynamicRelaxation,True` 자동 설정
4. **바닥면/접촉 제거**: 자동 처리
5. **원점 이동**: `*MovetoOriginAutomatic,True` 자동 설정

**❌ 새로 추가할 필요 없는 것:**
1. ~~별도 Dynamic Relaxation 템플릿~~ → 이미 자동
2. ~~DYNAIN_TO_INITIAL 수동 설정~~ → 이미 자동

**⭐ V2에서 추가할 것:**
1. **각도 소스 확장**: Fibonacci, Pitching, Rolling 지원
2. **각도 믹싱 전략**: same_angle, cyclic, random, opposite, custom
3. **표준 Case txt 파일 활용**: 기존 파일 직접 참조
4. **Tolerance/DOE 시스템**: 산포 분석
5. **다중 시나리오 자동화**: 26개 조건 × N회 자동 생성

#### 5.4 간소화된 템플릿 시스템

| 템플릿 ID | 용도 | 실제 동작 |
|----------|------|----------|
| `DROP_FIRST` | 첫 번째 낙하 | DROP_ATTITUDE 실행 (DR 자동 포함) |
| `DROP_CUMULATIVE` | 누적 낙하 | DYNAIN_TO_INITIAL → DROP_ATTITUDE (DR 자동 재추가) |
| `THERMAL_FIRST` | 첫 번째 열해석 | THERMAL_CYCLE 실행 |
| `THERMAL_CUMULATIVE` | 누적 열해석 | DYNAIN_TO_INITIAL → THERMAL_CYCLE |
| `THERMAL_TO_DROP` | 열→낙하 | DYNAIN_TO_INITIAL(열) → DROP_ATTITUDE |

#### 5.5 템플릿 데이터 구조 (간소화)

```python
from typing import Literal

KooMeshModifierTemplate = Literal[
    "DROP_FIRST",          # 첫 번째 낙하
    "DROP_CUMULATIVE",     # 누적 낙하
    "THERMAL_FIRST",       # 첫 번째 열해석
    "THERMAL_CUMULATIVE",  # 누적 열해석
    "THERMAL_TO_DROP"      # 열→낙하
]

@dataclass
class StepConfig:
    """단일 스텝 설정"""
    step: int
    mode: SimulationMode  # "DROP", "THERM", etc.
    template: KooMeshModifierTemplate

    # 각도 설정 (DROP 모드)
    angle_source: Optional[AngleSourceConfig] = None

    # 모드별 파라미터
    params: Dict[str, Any] = None
    # {
    #   "height": 1.5,
    #   "surface": "steelPlate",
    #   "temperature": 85,  (THERM 모드)
    # }
```

#### 5.6 템플릿별 실제 동작

##### 템플릿 1: DROP_FIRST

**용도**: 첫 번째 낙하 (초기 상태)

**실제 실행**:
```python
# DROP_ATTITUDE 실행
# → *CONTROL_DYNAMIC_RELAXATION 자동 포함
# → dynaintoinitial.txt 자동 생성 (다음 스텝용)
```

**JSON 설정**:
```json
{
  "step": 1,
  "mode": "DROP",
  "template": "DROP_FIRST",
  "angle_source": {
    "source_type": "cuboid_geometry",
    "condition": "F1"
  },
  "params": {"height": 1.5, "surface": "steelPlate"}
}
```

---

##### 템플릿 2: DROP_CUMULATIVE

**용도**: 누적 낙하 (이전 스텝 변형 반영)

**실제 실행**:
```python
# 1. DYNAIN_TO_INITIAL 실행
#    - dynaintoinitial.txt 사용 (이전 스텝에서 자동 생성됨)
#    - *RemoveDynamicRelaxation,True (자동 설정됨)
#    - 바닥면/접촉 제거 (자동 설정됨)

# 2. DROP_ATTITUDE 실행
#    - *CONTROL_DYNAMIC_RELAXATION 자동 재추가 ⭐
#    - dynaintoinitial.txt 자동 재생성 (다음 스텝용)
```

**JSON 설정**:
```json
{
  "step": 2,
  "mode": "DROP",
  "template": "DROP_CUMULATIVE",
  "angle_source": {
    "source_type": "cuboid_geometry",
    "condition": "E1"
  },
  "params": {"height": 1.5}
}
```

---

##### 템플릿 3: THERMAL_FIRST

**용도**: 첫 번째 열해석

**실제 실행**:
```python
# THERMAL_CYCLE 실행
# → dynaintoinitial.txt 생성 (다음 스텝용)
```

**JSON 설정**:
```json
{
  "step": 1,
  "mode": "THERM",
  "template": "THERMAL_FIRST",
  "params": {
    "temperature": 85,
    "thermal_time": 0.5
  }
}
```

---

##### 템플릿 4: THERMAL_TO_DROP

**용도**: 열응력 후 낙하

**실제 실행**:
```python
# 1. DYNAIN_TO_INITIAL 실행 (열 스텝 dynain 사용)
# 2. DROP_ATTITUDE 실행
#    - *CONTROL_DYNAMIC_RELAXATION 자동 추가
#    - 열응력 상태에서 낙하
```

**JSON 설정**:
```json
{
  "step": 2,
  "mode": "DROP",
  "template": "THERMAL_TO_DROP",
  "angle_source": {
    "source_type": "cuboid_geometry",
    "condition": "F1"
  },
  "params": {"height": 1.5}
}
```

#### 5.7 템플릿 선택 가이드

| 시나리오 | Step 1 | Step 2 | Step 3 |
|---------|--------|--------|--------|
| 3회 연속 낙하 | DROP_FIRST | DROP_CUMULATIVE | DROP_CUMULATIVE |
| 열→낙하 | THERMAL_FIRST | THERMAL_TO_DROP | DROP_CUMULATIVE |
| 열→열→낙하 | THERMAL_FIRST | THERMAL_CUMULATIVE | THERMAL_TO_DROP |

#### 5.8 템플릿 자동 선택 로직

**CumulativeScenarioRunner에서 자동으로 템플릿 선택**:

```python
def select_template_for_step(step: int, mode: str, prev_mode: Optional[str] = None) -> str:
    """
    스텝 번호와 모드에 따라 자동으로 템플릿 선택

    Parameters:
        step: 현재 스텝 번호 (1부터 시작)
        mode: 현재 모드 ("DROP", "THERM", etc.)
        prev_mode: 이전 스텝 모드 (None if step=1)

    Returns:
        Template ID
    """
    if step == 1:
        # 첫 번째 스텝
        if mode == "DROP":
            return "DROP_FIRST"
        elif mode == "THERM":
            return "THERMAL_FIRST"
    else:
        # 누적 스텝 (step >= 2)
        if mode == "DROP":
            if prev_mode == "THERM":
                return "THERMAL_TO_DROP"  # 열→낙하 전환
            else:
                return "DROP_CUMULATIVE"   # 낙하→낙하
        elif mode == "THERM":
            return "THERMAL_CUMULATIVE"    # 열→열

    raise ValueError(f"Unknown mode combination: step={step}, mode={mode}, prev_mode={prev_mode}")
```

**JSON 설정 예시** (템플릿 자동 선택):

```json
{
  "id": "thermal_drop_6step",
  "name": "열응력 + 6회 낙하",
  "analysisType": "mixedCumulative",
  "projectName": "HWWarranty",
  "steps": [
    {
      "step": 1,
      "mode": "THERM",
      "condition": "HOT85",
      "params": {"temperature": 85, "thermal_time": 0.5}
    },
    {
      "step": 2,
      "mode": "DROP",
      "condition": "F1",
      "params": {"height": 1.5}
    },
    {
      "step": 3,
      "mode": "DROP",
      "condition": "F2",
      "params": {"height": 1.5}
    },
    {
      "step": 4,
      "mode": "DROP",
      "condition": "E1",
      "params": {"height": 1.5}
    },
    {
      "step": 5,
      "mode": "DROP",
      "condition": "E2",
      "params": {"height": 1.5}
    },
    {
      "step": 6,
      "mode": "DROP",
      "condition": "C1",
      "params": {"height": 1.5}
    }
  ]
}
```

**자동 선택된 템플릿**:
- Step 1 (THERM): `THERMAL_FIRST`
- Step 2 (DROP after THERM): `THERMAL_TO_DROP`
- Step 3-6 (DROP after DROP): `DROP_CUMULATIVE`

---

### Phase 6: Runner 업데이트

#### 6.1 multiScenarioCumulative 실행기

```python
class MultiScenarioCumulativeRunner:
    """다중 시나리오 누적 실행기"""

    def __init__(self, runner_config_path: str):
        with open(runner_config_path, 'r') as f:
            self.config = json.load(f)

        self.analysis_type = self.config.get("analysis_type")
        if self.analysis_type != "multiScenarioCumulative":
            raise ValueError("Runner config is not multiScenarioCumulative type")

    def run(self, scenario_filter: Optional[str] = None):
        """
        모든 시나리오 실행

        Parameters:
            scenario_filter: 특정 시나리오 ID만 실행 (예: "F1_3drop")
        """
        scenarios = self.config["scenarios"]

        if scenario_filter:
            scenarios = [s for s in scenarios if s["original_scenario_id"] == scenario_filter]

        for scenario in scenarios:
            print(f"Running scenario: {scenario['scenario_id']}")
            self._run_single_scenario(scenario)

    def _run_single_scenario(self, scenario: dict):
        """단일 시나리오 실행 (기존 CumulativeScenarioRunner 로직 활용)"""
        # 기존 CumulativeScenarioRunner와 동일한 로직
        # Step 1 → Step 2 → ... → Step N 순차 실행
        pass
```

---

## 📊 사용 예시

### 예시 1: F1 조건 3회 낙하, ±2° 산포 10개 DOE

```json
{
  "id": "f1_3drop_tolerance",
  "name": "F1 조건 3회 낙하 with 산포",
  "analysisType": "mixedCumulative",
  "projectName": "HWWarranty",
  "steps": [
    {
      "step": 1,
      "mode": "DROP",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "condition": "F1"
      },
      "params": {"height": 1.5, "surface": "steelPlate"}
    },
    {
      "step": 2,
      "mode": "DROP",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "condition": "F1"
      },
      "params": {"height": 1.5, "surface": "steelPlate"}
    },
    {
      "step": 3,
      "mode": "DROP",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "condition": "F1"
      },
      "params": {"height": 1.5, "surface": "steelPlate"}
    }
  ],
  "tolerance": {
    "enabled": true,
    "method": "lhs",
    "doe_count": 10,
    "roll": {"min": -2, "max": 2},
    "pitch": {"min": -2, "max": 2},
    "yaw": {"min": -1, "max": 1}
  }
}
```

**결과**: 10개 DOE × 3 스텝 = 30개 시뮬레이션

---

### 예시 2A: Fibonacci 10deg Case txt 파일 사용, 단일 낙하 (표준 파일 활용)

```json
{
  "id": "fibonacci_10deg_single_from_txt",
  "name": "Fibonacci 10deg 413케이스 단일 낙하 (Case txt 파일)",
  "analysisType": "singleDrop",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "params": {"height": 1.5, "surface": "steelPlate"}
}
```

**결과**: 413개 시뮬레이션 (단일 낙하, 자동으로 `DROP_FIRST` 템플릿 적용)

**특징**:
- ✅ 표준 Case txt 파일 직접 사용
- ✅ JSON 설정 간단 (각도 수동 입력 불필요)
- ✅ 템플릿 자동 선택 (단일 낙하 → DROP_FIRST)

---

### 예시 2B: Fibonacci 10deg, 각 케이스마다 2회 누적 낙하 (Case txt + 템플릿)

**중요**: Fibonacci 누적 낙하에서 각도 조합 전략이 필요합니다!

#### 전략 1: 동일 각도 반복 (Same Angle Repeat)

**용도**: 동일한 각도로 반복 낙하하여 특정 방향의 누적 손상 분석

```json
{
  "id": "fibonacci_10deg_2drop_same_angle",
  "name": "Fibonacci 10deg 413케이스 각 2회 누적 (동일 각도)",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "cumulative_config": {
    "repeat_count": 2,
    "angle_mixing_strategy": "same_angle"  // ⭐ 전략 지정
    // 템플릿은 자동 선택: DROP_FIRST → DROP_CUMULATIVE
  },
  "params": {"height": 1.5, "surface": "steelPlate"}
}
```

**내부 확장 결과**:
```
케이스 0 (P0001, Roll=-90°, Pitch=0°):
  Step 1: P0001 각도 낙하 (DROP_FIRST, DR 자동 추가)
  Step 2: P0001 각도 낙하 (DROP_CUMULATIVE, DYNAIN_TO_INITIAL → DR 자동 재추가)

케이스 1 (P0002, Roll=-66.93°, Pitch=-137.51°):
  Step 1: P0002 각도 낙하 (DROP_FIRST)
  Step 2: P0002 각도 낙하 (DROP_CUMULATIVE)
...
```

**결과**: 413개 케이스 × 2 스텝 = 826개 시뮬레이션

**장점**:
- 특정 방향의 누적 손상 집중 분석
- 동일 각도 반복 낙하의 효과 확인

---

#### 전략 2: 각도 순환 (Cyclic Rotation)

**용도**: Fibonacci 각도를 순환시켜 다양한 각도 조합 테스트

```json
{
  "id": "fibonacci_10deg_2drop_cyclic",
  "name": "Fibonacci 10deg 413케이스 각 2회 누적 (순환)",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "cumulative_config": {
    "repeat_count": 2,
    "angle_mixing_strategy": "cyclic",  // ⭐ 순환 전략
    "cyclic_offset": 1  // 다음 인덱스로 순환
    // 템플릿 자동 선택: DROP_FIRST → DROP_CUMULATIVE
  },
  "params": {"height": 1.5}
}
```

**내부 확장 결과**:
```
케이스 0 (P0001):
  Step 1: P0001 각도 낙하
  Step 2: P0002 각도 낙하  (cyclic_offset=1)

케이스 1 (P0002):
  Step 1: P0002 각도 낙하
  Step 2: P0003 각도 낙하

케이스 412 (P0413):
  Step 1: P0413 각도 낙하
  Step 2: P0001 각도 낙하  (순환)
```

**장점**:
- 다양한 각도 조합 테스트
- 초기 각도와 다른 방향으로 2차 낙하

---

#### 전략 3: 랜덤 믹싱 (Random Mixing)

**용도**: 각 케이스마다 무작위 각도 조합으로 실제 사용 환경 시뮬레이션

```json
{
  "id": "fibonacci_10deg_2drop_random",
  "name": "Fibonacci 10deg 413케이스 각 2회 누적 (랜덤)",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "cumulative_config": {
    "repeat_count": 2,
    "angle_mixing_strategy": "random",  // ⭐ 랜덤 전략
    "random_seed": 42  // 재현성을 위한 시드
    // 템플릿 자동 선택: DROP_FIRST → DROP_CUMULATIVE
  },
  "params": {"height": 1.5}
}
```

**내부 확장 결과** (random_seed=42 기준):
```
케이스 0 (P0001):
  Step 1: P0001 각도 낙하
  Step 2: P0187 각도 낙하  (랜덤 선택)

케이스 1 (P0002):
  Step 1: P0002 각도 낙하
  Step 2: P0324 각도 낙하  (랜덤 선택)
...
```

**장점**:
- 실제 사용 환경의 무작위성 반영
- 다양한 각도 조합 탐색

---

#### 전략 4: 대칭 각도 (Opposite Angle)

**용도**: 초기 각도의 반대편 각도로 낙하 (구면 대칭)

```json
{
  "id": "fibonacci_10deg_2drop_opposite",
  "name": "Fibonacci 10deg 413케이스 각 2회 누적 (대칭)",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "cumulative_config": {
    "repeat_count": 2,
    "angle_mixing_strategy": "opposite",  // ⭐ 대칭 전략
    "templates": ["STANDARD_DROP", "CUMULATIVE_DROP_WITH_DYNAIN_RELAX"]
  },
  "params": {"height": 1.5}
}
```

**내부 확장 결과**:
```
케이스 0 (P0001, Roll=-90°, Pitch=0°):
  Step 1: Roll=-90°, Pitch=0° 낙하
  Step 2: Roll=+90°, Pitch=180° 낙하  (반대편)

케이스 1 (P0002, Roll=-66.93°, Pitch=-137.51°):
  Step 1: Roll=-66.93°, Pitch=-137.51°
  Step 2: Roll=+66.93°, Pitch=+42.49° (반대편)
...
```

**장점**:
- 양면 손상 분석
- 대칭 방향의 영향 비교

---

#### 전략 5: 사용자 정의 매핑 (Custom Mapping)

**용도**: 사용자가 각 Step의 각도를 직접 지정

```json
{
  "id": "fibonacci_10deg_2drop_custom",
  "name": "Fibonacci 10deg 413케이스 각 2회 누적 (사용자 정의)",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  },
  "cumulative_config": {
    "repeat_count": 2,
    "angle_mixing_strategy": "custom_mapping",  // ⭐ 사용자 정의
    "step_angle_sources": [
      {"source_type": "case_txt_file", "case_txt": {"file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"}},
      {"source_type": "case_txt_file", "case_txt": {"file_path": "FullAngleDrop/fibonacci_20deg_103cases.txt"}}
    ]
    // 템플릿 자동 선택: DROP_FIRST → DROP_CUMULATIVE
  },
  "params": {"height": 1.5}
}
```

**내부 확장 결과**:
```
케이스 0:
  Step 1: fibonacci_10deg의 P0001 각도
  Step 2: fibonacci_20deg의 P0001 각도

케이스 1:
  Step 1: fibonacci_10deg의 P0002 각도
  Step 2: fibonacci_20deg의 P0002 각도
...
```

**장점**:
- 완전한 유연성
- 다른 각도 세트 조합 가능

---

#### 전략 비교표

| 전략 | 각도 조합 예시 (2회) | 장점 | 단점 | 권장 용도 |
|------|---------------------|------|------|----------|
| **same_angle** | P001 → P001 | 특정 방향 누적 손상 집중 분석 | 각도 다양성 부족 | 동일 방향 반복 낙하 효과 분석 |
| **cyclic** | P001 → P002<br>P002 → P003 | 인접 각도 조합 탐색 | 멀리 떨어진 각도 조합 불가 | 인접 방향 연속 낙하 |
| **random** | P001 → P187<br>P002 → P324 | 다양한 조합, 실제 환경 반영 | 재현성 관리 필요 | 실제 사용 환경 시뮬레이션 |
| **opposite** | P001 → P001_OPP<br>(앞면 → 뒷면) | 양면 손상 분석 | 대칭 각도만 가능 | 양면 충격 테스트 |
| **custom_mapping** | Fib10deg_P001 → Fib20deg_P001 | 완전한 제어 | 설정 복잡 | 특정 각도 조합 실험 |

#### 전략별 시뮬레이션 수

Fibonacci 10deg (413 케이스) 기준:

| 전략 | 2회 누적 | 3회 누적 | 5회 누적 |
|------|----------|----------|----------|
| **same_angle** | 413 × 2 = 826 | 413 × 3 = 1,239 | 413 × 5 = 2,065 |
| **cyclic** | 413 × 2 = 826 | 413 × 3 = 1,239 | 413 × 5 = 2,065 |
| **random** | 413 × 2 = 826 | 413 × 3 = 1,239 | 413 × 5 = 2,065 |
| **opposite** | 413 × 2 = 826 | 413 × 3 = 1,239 | 413 × 5 = 2,065 |
| **custom_mapping** | min(N1, N2) × 2 | min(N1, N2, N3) × 3 | min(N1, ..., N5) × 5 |

**주의**: 모든 전략은 동일한 시뮬레이션 수를 생성하지만, **각도 조합 방식**이 다릅니다!

---

### 예시 3: 26개 F/E/C 조건, 각각 3회 낙하

```json
{
  "id": "26conditions_3drop",
  "name": "26개 조건 각 3회 낙하",
  "analysisType": "multiScenarioCumulative",
  "projectName": "HWWarranty",
  "scenarios": [
    {
      "scenario_id": "F1_3drop",
      "description": "F1 조건 3회 낙하",
      "steps": [
        {"step": 1, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F1"}, "params": {"height": 1.5}},
        {"step": 2, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F1"}, "params": {"height": 1.5}},
        {"step": 3, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F1"}, "params": {"height": 1.5}}
      ]
    },
    {
      "scenario_id": "F2_3drop",
      "description": "F2 조건 3회 낙하",
      "steps": [
        {"step": 1, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F2"}, "params": {"height": 1.5}},
        {"step": 2, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F2"}, "params": {"height": 1.5}},
        {"step": 3, "mode": "DROP", "angle_source": {"source_type": "cuboid_geometry", "condition": "F2"}, "params": {"height": 1.5}}
      ]
    }
    ... (F3~F6, E1~E12, C1~C8 반복, 총 26개)
  ]
}
```

**결과**: 26개 조건 × 3 스텝 = 78개 시뮬레이션

---

### 예시 4: Pitching 스윕 19케이스, 단일 낙하

```json
{
  "id": "pitching_sweep_19cases",
  "name": "Pitching 스윕 -90~90도 19케이스",
  "analysisType": "mixedCumulative",
  "projectName": "HWWarranty",
  "steps": [
    {
      "step": 1,
      "mode": "DROP",
      "angle_source": {
        "source_type": "pitching_sweep",
        "sweep_config": {
          "pitch_min": -90,
          "pitch_max": 90,
          "pitch_step": 10,
          "roll_fixed": 0,
          "yaw_fixed": 0
        }
      },
      "params": {"height": 1.5}
    }
  ]
}
```

**결과**: 19개 각도 × 1 스텝 = 19개 시뮬레이션

---

## 🚀 구현 우선순위

### Priority 1: 표준 Case txt 파일 시스템 (HIGH) ⭐
- [ ] `CaseTxtConfig` 데이터 클래스 추가
- [ ] `parse_case_txt_file()` 구현
- [ ] Case 이름 자동 추출 ($ 주석 라인 파싱)
- [ ] 특정 인덱스 선택 기능 구현
- [ ] Case txt + Tolerance 조합 구현

### Priority 2: KooMeshModifier 템플릿 자동 선택 시스템 (HIGH) ⭐
- [ ] `select_template_for_step()` 자동 선택 함수 구현
- [ ] 5개 템플릿 정의 (DROP_FIRST, DROP_CUMULATIVE, THERMAL_FIRST, THERMAL_CUMULATIVE, THERMAL_TO_DROP)
- [ ] 자동 템플릿 선택 로직 (스텝 번호, 현재/이전 모드 기반)
- [ ] ~~DYNAIN_TO_INITIAL 수동 설정~~ → **이미 자동 처리됨 (dynaintoinitial.txt 자동 생성)**
- [ ] ~~Dynamic Relaxation 수동 추가~~ → **이미 자동 처리됨 (DROP_ATTITUDE 실행 시 자동 포함)**
- [ ] THERMAL → DROP 혼합 모드 지원 (THERMAL_TO_DROP 템플릿)

### Priority 3: 각도 소스 확장 (HIGH)
- [ ] `AngleSourceConfig` 데이터 클래스 추가
- [ ] `parse_angle_source()` 메인 함수 구현
- [ ] `parse_cuboid_geometry()` 구현 (F/E/C 매핑)
- [ ] `parse_fibonacci_lattice()` 구현 (txt 파일 파싱 활용)
- [ ] `parse_pitching_sweep()`, `parse_rolling_sweep()` 구현
- [ ] `parse_custom_file()` 구현

### Priority 4: Tolerance/DOE 시스템 (MEDIUM)
- [ ] `ToleranceConfig` 확장
- [ ] `apply_tolerance_doe()` 구현
- [ ] LHS, Grid, Random DOE 생성기 구현
- [ ] `generate_lhs_samples()` 구현

### Priority 5: 다중 시나리오 (MEDIUM)
- [ ] `MultiScenarioCumulativeConfig` 데이터 클래스 추가
- [ ] `parse_multi_scenario_cumulative()` 구현
- [ ] `generate_multi_scenario_runner_config()` 구현
- [ ] `MultiScenarioCumulativeRunner` 클래스 구현
- [ ] Case txt 파일 기반 자동 시나리오 확장 (`cumulative_config.repeat_count`)

### Priority 6: 문서 및 테스트 (MEDIUM)
- [ ] F1-F6, E1-E12, C1-C8 상세 문서 작성
- [ ] 각도 소스별 테스트 예제 작성
- [ ] Tolerance DOE 검증 스크립트 작성
- [ ] 템플릿별 테스트 예제 작성

### Priority 7: 기존 코드 리팩토링 (LOW)
- [ ] V1 코드와 V2 코드 통합
- [ ] 하위 호환성 유지 (기존 mixedCumulative 지원)
- [ ] Alias 시스템 확장 (Fibonacci, Sweep 지원)

---

## 📁 파일 구조 (V2)

```
pyKooCAE/
├── occProject/Generators/KooCAEManager/
│   └── KooDynaAutomaticSimulationScriptGenerator.py  (V2 확장)
│
├── Runner/
│   ├── CumulativeScenarioRunner.py         (기존)
│   ├── MultiScenarioCumulativeRunner.py    (신규)
│   ├── AngleSourceParser.py                (신규 - 각도 소스 파서)
│   ├── CaseTxtParser.py                    (신규 - Case txt 파일 파서) ⭐
│   ├── TemplateManager.py                  (신규 - 템플릿 관리자) ⭐
│   ├── ToleranceDOEGenerator.py            (신규 - DOE 생성기)
│   └── AliasManager.py                     (기존, V2 확장)
│
├── Templates/                              (템플릿은 자동 선택되므로 파일 불필요)
│   └── (템플릿 정의는 코드에 하드코딩됨)
│
└── Examples/HWWarrantyDropTest/
    ├── FullAngleDrop/                      (표준 Case txt 파일) ⭐
    │   ├── 26case_6F12E8C_cuboid.txt       (기존)
    │   ├── fibonacci_01deg_41253cases.txt  (기존)
    │   ├── fibonacci_02deg_10313cases.txt  (기존)
    │   ├── fibonacci_04deg_2578cases.txt   (기존)
    │   ├── fibonacci_05deg_1650cases.txt   (기존)
    │   ├── fibonacci_06deg_1146cases.txt   (기존)
    │   ├── fibonacci_10deg_413cases.txt    (기존)
    │   ├── fibonacci_20deg_103cases.txt    (기존)
    │   ├── fibonacci_40deg_26cases.txt     (기존)
    │   ├── pitching_10deg_19cases.txt      (기존)
    │   └── rolling_10deg_36cases.txt       (기존)
    │
    ├── SampleScenarios/                    (신규 - 예제 시나리오) ⭐
    │   ├── sample_case_txt_fibonacci_10deg.json       (Case txt 사용)
    │   ├── sample_case_txt_with_tolerance.json        (Case txt + Tolerance)
    │   ├── sample_template_thermal_drop.json          (템플릿 사용)
    │   ├── sample_multi_scenario_26conditions.json    (다중 시나리오)
    │   └── sample_fibonacci_cumulative_2drop.json     (Fibonacci 누적)
    │
    ├── PROGRESS_SUMMARY.md                 (진행 상황)
    ├── MODE_CONDITION_Reference.md         (모드/컨디션 정의)
    └── DROP_MODE_V2_PLAN.md                (본 문서)
```

---

## 🎯 기대 효과

### 1. 유연성 대폭 향상
- 26개 정형 → 수천~수만 개 각도 소스 지원
- Fibonacci, Pitching, Rolling, Custom 모두 지원

### 2. 산포 분석 가능
- 각 조건에 ±1°~±5° 산포 DOE 적용
- 실제 제품 변동성 반영 가능

### 3. 대규모 DOE 자동화
- 26개 조건 × 3회 낙하 = 78개 시뮬레이션 자동화
- 413개 Fibonacci × 2회 낙하 = 826개 시뮬레이션 가능

### 4. 명확한 정의
- F1~C8 물리적 위치, 방향 벡터, Euler 각도 완벽 문서화
- 사용자 혼란 제거

### 5. 표준 Case txt 파일 재사용 ⭐
- 기존에 잘 정의된 표준 파일 직접 활용
- JSON 설정 간소화 (각도 수동 입력 불필요)
- 11개 표준 파일 즉시 사용 가능:
  - Cuboid 26개, Fibonacci 8종, Pitching/Rolling 각 1종

### 6. KooMeshModifier 자동 템플릿 시스템 ⭐
- **표준 워크플로 자동 적용**: 스텝 번호와 모드에 따라 자동으로 템플릿 선택
- **Dynamic Relaxation 자동 처리**: DROP_ATTITUDE 실행 시 자동으로 *CONTROL_DYNAMIC_RELAXATION 포함 (수동 설정 불필요)
- **DYNAIN_TO_INITIAL 자동 생성**: dynaintoinitial.txt 자동 생성 (RemoveDynamicRelaxation, 바닥면/접촉 제거, 원점 이동 자동 설정)
- **5가지 템플릿으로 모든 시나리오 커버**: DROP_FIRST, DROP_CUMULATIVE, THERMAL_FIRST, THERMAL_CUMULATIVE, THERMAL_TO_DROP
- **사용자는 JSON에 템플릿 지정 불필요**: 시스템이 자동으로 최적 템플릿 선택

### 7. 가지수 배분 전략
- 예시 2B: Fibonacci 413개 각도 × 2회 누적 = 826개 시뮬레이션
  - 피보나치 각도로 초기 각도 분포 확보
  - 누적 낙하로 손상 누적 효과 분석
- 예시: 26개 Cuboid + Tolerance ±2° (10 DOE) = 260개
  - 정형 각도로 대표 조건 파악
  - 산포로 변동성 분석

---

## 📝 다음 단계

1. **사용자 피드백**
   - 본 계획서 검토 및 요구사항 확인
   - 우선순위 조정

2. **Phase 1 구현 시작**
   - AngleSourceConfig 추가
   - parse_angle_source() 구현
   - Fibonacci/Pitching/Rolling 파서 구현

3. **Phase 2 구현**
   - ToleranceConfig 확장
   - DOE 생성기 구현

4. **테스트 및 검증**
   - 소규모 케이스로 검증
   - 대규모 케이스 (413개) 테스트

---

## 🔍 워크플로 검증 결과 (중요!)

### 핵심 발견사항

이 계획서를 작성하는 과정에서 **KooDynaAdvancedModification.py의 기존 워크플로를 상세히 조사**한 결과, 다음과 같은 중요한 사실을 확인했습니다:

#### ✅ 이미 완벽하게 구현되어 있는 것들:

1. **Dynamic Relaxation 자동 추가**
   - `DROP_ATTITUDE` 실행 시 `CreateInterfaceSpringbackLSDyna()` 호출
   - `*CONTROL_DYNAMIC_RELAXATION` 자동으로 DropSet.k에 포함
   - **사용자가 수동으로 설정할 필요 없음**

2. **dynaintoinitial.txt 자동 생성**
   - `DROP_ATTITUDE` 실행 시 자동으로 생성
   - 다음 스텝을 위한 완벽한 설정 포함:
     - `*RemoveDynamicRelaxation,True` (DR 제거)
     - `*MovetoOriginAutomatic,True` (원점 이동)
     - `*RemovePartbyID` (바닥면 제거)
     - `*RemoveContactbyID` (접촉 제거)

3. **DYNAIN_TO_INITIAL 자동 처리**
   - dynaintoinitial.txt 읽어서 자동으로 처리
   - DR 제거, 파트 제거, 접촉 제거 모두 자동
   - 다음 DROP_ATTITUDE에서 DR 다시 자동 추가

#### ❌ 불필요한 것들 (초안에서 제거됨):

1. ~~별도 Dynamic Relaxation 템플릿~~ → 이미 자동
2. ~~DYNAIN_TO_INITIAL 수동 설정~~ → 이미 자동
3. ~~6개 템플릿 파일 (JSON)~~ → 코드에 하드코딩으로 충분

#### ⭐ V2에서 실제로 추가할 것:

1. **각도 소스 확장**: Fibonacci, Pitching, Rolling 지원
2. **각도 믹싱 전략**: same_angle, cyclic, random, opposite, custom
3. **표준 Case txt 파일 활용**: 11개 표준 파일 직접 참조
4. **Tolerance/DOE 시스템**: 산포 분석
5. **템플릿 자동 선택 로직**: 스텝/모드 기반 자동 선택

### 검증 방법

다음 파일들을 직접 읽어 확인:
- [KooDynaAdvancedModification.py:2005](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L2005) - DR 자동 추가
- [KooDynaAdvancedModification.py:2191-2211](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L2191) - dynaintoinitial.txt 자동 생성
- [KooDynaAdvancedModification.py:4481-4482](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L4481) - DR 제거 로직
- [26case_6F12E8C_cuboid.txt](FullAngleDrop/26case_6F12E8C_cuboid.txt) - 표준 Case txt 예시
- [fibonacci_40deg_26cases.txt](FullAngleDrop/fibonacci_40deg_26cases.txt) - Fibonacci 예시
- [rolling_10deg_36cases.txt](FullAngleDrop/rolling_10deg_36cases.txt) - Rolling 예시
- [pitching_10deg_19cases.txt](FullAngleDrop/pitching_10deg_19cases.txt) - Pitching 예시

---

**문서 작성일**: 2026-01-22
**작성자**: Claude Code (Sonnet 4.5)
**버전**: V2.0
**상태**: 설계 완료, 워크플로 검증 완료, 구현 대기
