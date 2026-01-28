# Cumulative Drop Automation Plan

## 목표

N회 누적낙하 시뮬레이션을 자동으로 수행하는 시스템 구축

```
Drop 1 → LS-DYNA → dynain → DYNAIN_TO_INITIAL → Drop 2 → ... → Drop N
```

---

## 1. 현재 보유한 기능 (파편적 구현)

| 기능 | 모드/시스템 | 상태 |
|------|------------|------|
| 낙하 시뮬레이션 생성 | DROP_ATTITUDE | ✅ 완료 |
| dynain → 초기조건 변환 | DYNAIN_TO_INITIAL | ✅ 완료 |
| 결과 폴더 자동 생성 | RunDirectoryMode | ✅ 완료 |
| 다음 단계 설정 파일 자동 생성 | dynaintoinitial.txt | ✅ 완료 |
| 메타데이터 관리 | MetaData 시스템 | ✅ 완료 |
| 시뮬레이션 자동화 설정 | SIMULATION_AUTOMATION | ⚠️ 파싱만 완료 |
| 전단계 결과 연계 | angleSource | ✅ 완료 |
| 좌표계 복원 | MovetoOrigin | ✅ 완료 |
| **별칭(Alias) 시스템** | simulation_index.json | ⚠️ 설계 완료 (구현 필요) |
| **LS-DYNA 실행** | - | ❌ 미구현 |
| **워크플로우 오케스트레이션** | - | ❌ 미구현 |

---

## 2. 전단계-후단계 연계 시스템 (기존 구현)

### 2.1 angleSource: 결과 연계 옵션

SIMULATION_AUTOMATION에서 이전 단계 결과를 다음 단계에 연계하는 시스템:

```python
AngleSource = Literal["lhs", "fromMBD", "usePrevResult"]
```

| angleSource | 설명 | 사용 시나리오 |
|-------------|------|--------------|
| `lhs` | Latin Hypercube Sampling | 새로운 각도 생성 (독립 실행) |
| `fromMBD` | MBD 시뮬레이션 결과 참조 | MBD → FEA 연계 |
| `usePrevResult` | 이전 단계 해석 결과 사용 | 누적 해석 (1:N, N:N) |

**연계 구조 (일대다 / 다대다):**

```
┌─────────────────────────────────────────────────────────────┐
│  일대다 (1:N) - MBD → Full Angle                            │
│                                                             │
│  MBD 시뮬레이션 (1개)                                        │
│       │                                                     │
│       └──► fullAngle 해석 (N개)                             │
│            angleSource = "fromMBD"                          │
│            angleSourceId = "MBD_result_id"                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  다대다 (N:M) - Cumulative Drop                             │
│                                                             │
│  DOE 케이스 1 ──► Drop 1 ──► Drop 2 ──► Drop 3             │
│  DOE 케이스 2 ──► Drop 1 ──► Drop 2 ──► Drop 3             │
│  DOE 케이스 3 ──► Drop 1 ──► Drop 2 ──► Drop 3             │
│       ...                                                   │
│  angleSource = "usePrevResult"                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 좌표계 복원 (MovetoOrigin)

낙하 후 변형된 모델을 원래 좌표계로 복원하는 기능:

| 옵션 | 설명 | 사용 시나리오 |
|------|------|--------------|
| `MovetoOriginAutomatic` | 자동 원점 복원 | 일반적인 누적낙하 |
| `MovetoOriginbyNode` | 특정 노드 기준 복원 | 정밀 위치 제어 필요 시 |

**자동 생성되는 dynaintoinitial.txt 예시:**

```
*Inputfile
DropSet.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainPath,Output/dynain
*IncludeStress,True              # 누적 응력/변형 포함
*RemoveDynamicRelaxation,True    # 이전 DR 설정 제거
*MovetoOriginAutomatic,True      # 좌표계 자동 복원
*RemovePartbyID,24               # 낙하면 파트 제거
*RemoveContactbyID,173           # 낙하면 접촉 제거
**EndDynainToInitial
*End
```

**좌표계 복원의 필요성:**

```
낙하 전           낙하 후 (변형+이동)      좌표 복원 후
   ┌───┐              ┌───┐                 ┌───┐
   │   │              │ ╲ │ ← 기울어짐       │ ╲ │ ← 변형 유지
   │   │              │   │                 │   │
   └───┘              └───┘                 └───┘
  원점 (0,0)         (dx, dy, dz)           원점 (0,0)
                      ↑ 이동됨               ↑ 위치 복원, 변형 유지
```

---

## 3. Run ID 및 별칭(Alias) 시스템 - 일반화된 누적 시나리오

### 3.1 현재 Run ID 생성 방식

```python
def GenerateRunID(self):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
    run_id = f"{timestamp}_{unique_hash}"
    return run_id
    # 예: "20260122_143052_a1b2c3"
```

**문제점:**
- 가독성 부족: 해시로는 어떤 케이스인지 알 수 없음
- 정렬 혼란: 타임스탬프 기준 정렬되어 논리적 순서와 다름
- 검색 불가: "F1 낙하 결과"를 찾으려면 모든 폴더를 열어야 함

### 3.2 지원 시뮬레이션 모드

**누적 시나리오는 낙하(Drop) 뿐만 아니라 다양한 시뮬레이션 모드를 지원:**

| 모드 코드 | 전체 모드명 | 설명 | Condition 예시 |
|-----------|------------|------|----------------|
| `DROP` | DROP_ATTITUDE | 낙하 시뮬레이션 | F1~F6, E1~E12, C1~C8 |
| `DWI` | DROP_WEIGHT_IMPACT | 중량 충격 시뮬레이션 | IMP01, IMP02, ... |
| `STAT` | STATIC_LOAD | 정적 하중 해석 | LOAD01, BEND01, ... |
| `THERM` | THERMAL_CYCLE | 열응력/열사이클 해석 | CYC01, HOT85, COLD-40 |
| `VIB` | VIBRATION | 진동 해석 | VIB01, RAND01, SINE01 |
| `COMB` | COMBINED | 복합 조건 해석 | THERM+DROP, VIB+STAT |

**열응력 시뮬레이션 (THERMAL_CYCLE) 상세:**

```
┌─────────────────────────────────────────────────────────────┐
│  열응력 시뮬레이션 시나리오 예시                              │
│                                                             │
│  Cycle 1: 상온(25°C) → 고온(85°C) → 상온(25°C)              │
│  Cycle 2: 상온(25°C) → 저온(-40°C) → 상온(25°C)             │
│  ...                                                        │
│  Cycle N: 반복 열사이클 후 누적 응력/변형 평가                │
│                                                             │
│  Condition 코드 예시:                                        │
│  - HOT85: 85°C 가열                                         │
│  - COLD-40: -40°C 냉각                                      │
│  - CYC01~CYC10: 열사이클 1~10                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 모든 모드에 공통되는 누적 시나리오 패턴

**핵심 원칙: 모든 시뮬레이션 모드는 동일한 누적 패턴을 따름**

```
┌─────────────────────────────────────────────────────────────┐
│  공통 워크플로우 (모든 시뮬레이션 모드)                        │
│                                                             │
│  Step N:                                                    │
│    1. 시뮬레이션 실행 (LS-DYNA)                              │
│    2. dynain 생성 (최종 응력/변형 상태)                       │
│    3. DYNAIN_TO_INITIAL (Dynamic Relaxation)                │
│       - 좌표계 복원 (MovetoOrigin)                          │
│       - 응력/변형 보존                                       │
│    4. 다음 단계 입력 파일 생성                               │
│                                                             │
│  Step N+1:                                                  │
│    → 이전 단계의 손상 상태를 초기 조건으로 사용                │
│    → 누적 손상 평가                                          │
└─────────────────────────────────────────────────────────────┘
```

**모드별 워크플로우 비교:**

| 단계 | DROP (낙하) | THERM (열응력) | STAT (정적) | VIB (진동) |
|------|-------------|---------------|-------------|------------|
| 입력 | 각도, 높이 | 온도 경계조건 | 하중/구속 | 주파수, 가속도 |
| 해석 | 충격 해석 | 열-구조 연성 | 선형/비선형 | 모달/Random |
| dynain | ✅ 필수 | ✅ 필수 | ✅ 필수 | ✅ 필수 |
| DR 복원 | ✅ 좌표+응력 | ✅ 좌표+응력 | ✅ 좌표+응력 | ✅ 좌표+응력 |
| 누적 대상 | 소성변형, 균열 | 열변형, 잔류응력 | 변형, 응력 | 피로 손상 |

### 3.4 별칭(Alias) 시스템 설계

**원칙: 기존 run_id는 유지하고, 별칭과 컴포넌트를 추가**

#### 3.3.1 일반화된 별칭 네이밍 규칙

```
{Project}_{ScenarioType}{TotalSteps}_DOE{Index}_S{Step}_{ModeCode}_{Condition}
```

| 컴포넌트 | 형식 | 설명 |
|---------|------|------|
| Project | 문자열 | 프로젝트명 (예: GalaxyS25) |
| ScenarioType | CUM/SEQ | CUM=DOE별 누적, SEQ=단일 시퀀스 |
| TotalSteps | 숫자(3자리) | 총 단계 수 (003, 005, 024 등) |
| DOE Index | 001~999 | DOE 케이스 번호 (SEQ는 생략) |
| Step | 001~999 | 현재 단계 번호 |
| ModeCode | DROP/THERM/STAT/... | 시뮬레이션 모드 코드 |
| Condition | 문자열 | 모드별 조건 (F1, HOT85, LOAD01 등) |

#### 3.3.2 단일 모드 시나리오 별칭 예시

**3회 누적낙하 (DROP 모드, DOE 5개):**
```
GalaxyS25_CUM003_DOE001_S001_DROP_F1    # DOE 1, Step 1, F1 낙하
GalaxyS25_CUM003_DOE001_S002_DROP_E3    # DOE 1, Step 2, E3 낙하
GalaxyS25_CUM003_DOE001_S003_DROP_C2    # DOE 1, Step 3, C2 낙하
GalaxyS25_CUM003_DOE002_S001_DROP_F2    # DOE 2, Step 1, F2 낙하
...
GalaxyS25_CUM003_DOE005_S003_DROP_C4    # DOE 5, Step 3
```

**5회 열사이클 (THERM 모드, DOE 3개):**
```
GalaxyS25_CUM005_DOE001_S001_THERM_HOT85     # DOE 1, Step 1, 85°C 가열
GalaxyS25_CUM005_DOE001_S002_THERM_COLD-40   # DOE 1, Step 2, -40°C 냉각
GalaxyS25_CUM005_DOE001_S003_THERM_HOT85     # DOE 1, Step 3, 85°C 가열
GalaxyS25_CUM005_DOE001_S004_THERM_COLD-40   # DOE 1, Step 4, -40°C 냉각
GalaxyS25_CUM005_DOE001_S005_THERM_HOT85     # DOE 1, Step 5, 최종 가열
...
```

**24회 순차 시나리오 (단일 시퀀스, DROP 모드):**
```
GalaxyS25_SEQ024_S001_DROP_F1
GalaxyS25_SEQ024_S002_DROP_F2
GalaxyS25_SEQ024_S003_DROP_F3
...
GalaxyS25_SEQ024_S024_DROP_C8
```

#### 3.3.3 혼합 모드 시나리오 별칭 예시

**6회 누적 시나리오 (열사이클 + 낙하 복합):**
```
GalaxyS25_CUM006_DOE001_S001_THERM_HOT85     # Step 1: 열 스트레스
GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40   # Step 2: 냉각 스트레스
GalaxyS25_CUM006_DOE001_S003_DROP_F1         # Step 3: F1 낙하
GalaxyS25_CUM006_DOE001_S004_THERM_CYC03     # Step 4: 열사이클 3회
GalaxyS25_CUM006_DOE001_S005_DROP_E5         # Step 5: E5 낙하
GalaxyS25_CUM006_DOE001_S006_DROP_C2         # Step 6: C2 낙하 (최종)
```

**실제 제품 신뢰성 테스트 시나리오:**
```
┌─────────────────────────────────────────────────────────────┐
│  제품 신뢰성 복합 테스트 시나리오                             │
│                                                             │
│  Step 1~3: 열사이클 (85°C ↔ -40°C × 3회)                   │
│  Step 4~6: HW 보증 낙하 (F1, E3, C2 × 1.5m)                │
│  Step 7~9: 추가 열사이클 (잔여 응력 평가)                    │
│  Step 10: 최종 낙하 (최악 조건)                              │
│                                                             │
│  → 누적 손상 및 열-기계적 복합 열화 평가                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 확장된 JSON 메타데이터 구조

```json
{
    "run_id": "20260122_143052_a1b2c3",
    "alias": "GalaxyS25_CUM006_DOE001_S003_DROP_F1",
    "alias_components": {
        "project": "GalaxyS25",
        "scenario_type": "CUM",
        "total_steps": 6,
        "doe_index": 1,
        "step": 3,
        "mode": "DROP",
        "condition": "F1"
    },
    "simulation_mode": {
        "code": "DROP",
        "full_name": "DROP_ATTITUDE",
        "parameters": {
            "euler_roll": 0,
            "euler_pitch": 0,
            "euler_yaw": 0,
            "height_mm": 1500
        }
    },
    "mechanism_chain": {
        "step_index": 3,
        "prev_run_ids": {
            "20260122_143050_x1y2z3": true
        },
        "prev_alias": "GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40",
        "next_run_ids": {},
        "next_alias": null
    },
    "dynain_status": {
        "generated": true,
        "path": "Output/dynain",
        "dynamic_relaxation_applied": true
    }
}
```

**열응력 시뮬레이션 메타데이터 예시:**

```json
{
    "run_id": "20260122_143050_x1y2z3",
    "alias": "GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40",
    "alias_components": {
        "project": "GalaxyS25",
        "scenario_type": "CUM",
        "total_steps": 6,
        "doe_index": 1,
        "step": 2,
        "mode": "THERM",
        "condition": "COLD-40"
    },
    "simulation_mode": {
        "code": "THERM",
        "full_name": "THERMAL_CYCLE",
        "parameters": {
            "initial_temp_C": 25,
            "target_temp_C": -40,
            "ramp_time_s": 600,
            "hold_time_s": 1800
        }
    },
    "mechanism_chain": {
        "step_index": 2,
        "prev_run_ids": {
            "20260122_143048_p1q2r3": true
        },
        "prev_alias": "GalaxyS25_CUM006_DOE001_S001_THERM_HOT85",
        "next_run_ids": {
            "20260122_143052_a1b2c3": true
        },
        "next_alias": "GalaxyS25_CUM006_DOE001_S003_DROP_F1"
    },
    "dynain_status": {
        "generated": true,
        "path": "Output/dynain",
        "dynamic_relaxation_applied": true
    }
}
```

### 3.6 마스터 인덱스 파일 (simulation_index.json)

SIMULATION_AUTOMATION 레벨에서 전체 시나리오 관계 관리:

```json
{
    "project": "GalaxyS25",
    "created": "2026-01-22T14:30:52",
    "scenarios": [
        {
            "id": "scenario_001",
            "name": "6회 열-낙하 복합 신뢰성 테스트",
            "type": "mixedCumulative",
            "total_steps": 6,
            "doe_count": 3,
            "total_runs": 18,
            "status": "in_progress",
            "mode_sequence": ["THERM", "THERM", "DROP", "THERM", "DROP", "DROP"],
            "runs": {
                "GalaxyS25_CUM006_DOE001_S001_THERM_HOT85": {
                    "run_id": "20260122_143048_p1q2r3",
                    "status": "completed",
                    "folder": "Run_20260122_143048_p1q2r3",
                    "mode": "THERM",
                    "condition": "HOT85",
                    "prev": null,
                    "next": ["GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40"]
                },
                "GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40": {
                    "run_id": "20260122_143050_x1y2z3",
                    "status": "completed",
                    "folder": "Run_20260122_143050_x1y2z3",
                    "mode": "THERM",
                    "condition": "COLD-40",
                    "prev": ["GalaxyS25_CUM006_DOE001_S001_THERM_HOT85"],
                    "next": ["GalaxyS25_CUM006_DOE001_S003_DROP_F1"]
                },
                "GalaxyS25_CUM006_DOE001_S003_DROP_F1": {
                    "run_id": "20260122_143052_a1b2c3",
                    "status": "running",
                    "folder": "Run_20260122_143052_a1b2c3",
                    "mode": "DROP",
                    "condition": "F1",
                    "prev": ["GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40"],
                    "next": []
                }
            }
        },
        {
            "id": "scenario_002",
            "name": "3회 HW보증 누적낙하",
            "type": "fullAngleCumulative",
            "total_steps": 3,
            "doe_count": 5,
            "total_runs": 15,
            "status": "pending",
            "mode_sequence": ["DROP", "DROP", "DROP"],
            "runs": {}
        },
        {
            "id": "scenario_003",
            "name": "10회 열사이클",
            "type": "thermalCumulative",
            "total_steps": 10,
            "doe_count": 1,
            "total_runs": 10,
            "status": "pending",
            "mode_sequence": ["THERM", "THERM", "THERM", "THERM", "THERM",
                             "THERM", "THERM", "THERM", "THERM", "THERM"],
            "runs": {}
        }
    ]
}
```

### 3.7 별칭 생성 함수 (SIMULATION_AUTOMATION 레벨)

```python
# 지원 시뮬레이션 모드 정의
SIMULATION_MODES = {
    "DROP": {"full_name": "DROP_ATTITUDE", "description": "낙하 시뮬레이션"},
    "DWI": {"full_name": "DROP_WEIGHT_IMPACT", "description": "중량 충격 시뮬레이션"},
    "STAT": {"full_name": "STATIC_LOAD", "description": "정적 하중 해석"},
    "THERM": {"full_name": "THERMAL_CYCLE", "description": "열응력/열사이클 해석"},
    "VIB": {"full_name": "VIBRATION", "description": "진동 해석"},
    "COMB": {"full_name": "COMBINED", "description": "복합 조건 해석"},
}


def generate_alias_cumulative(project: str, total_steps: int,
                               doe_index: int, step: int,
                               mode: str, condition: str) -> str:
    """DOE 기반 누적 시나리오용 별칭 생성 (일반화)

    Args:
        project: 프로젝트명 (예: GalaxyS25)
        total_steps: 총 단계 수
        doe_index: DOE 케이스 번호 (1-based)
        step: 현재 단계 번호 (1-based)
        mode: 시뮬레이션 모드 코드 (DROP, THERM, STAT, VIB 등)
        condition: 모드별 조건 (F1, HOT85, LOAD01 등)

    Returns:
        별칭 문자열 (예: GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40)
    """
    return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"


def generate_alias_sequential(project: str, total_steps: int,
                               step: int, mode: str, condition: str) -> str:
    """순차 시나리오용 별칭 생성 (DOE 없음)

    Args:
        project: 프로젝트명
        total_steps: 총 단계 수
        step: 현재 단계 번호 (1-based)
        mode: 시뮬레이션 모드 코드
        condition: 모드별 조건

    Returns:
        별칭 문자열 (예: GalaxyS25_SEQ024_S001_DROP_F1)
    """
    return f"{project}_SEQ{total_steps:03d}_S{step:03d}_{mode}_{condition}"


def parse_alias(alias: str) -> dict:
    """별칭을 컴포넌트로 파싱 (일반화)"""
    import re

    # CUM 패턴: GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40
    cum_pattern = r"(.+)_CUM(\d{3})_DOE(\d{3})_S(\d{3})_([A-Z]+)_(.+)"
    # SEQ 패턴: GalaxyS25_SEQ024_S001_DROP_F1
    seq_pattern = r"(.+)_SEQ(\d{3})_S(\d{3})_([A-Z]+)_(.+)"

    cum_match = re.match(cum_pattern, alias)
    if cum_match:
        return {
            "project": cum_match.group(1),
            "scenario_type": "CUM",
            "total_steps": int(cum_match.group(2)),
            "doe_index": int(cum_match.group(3)),
            "step": int(cum_match.group(4)),
            "mode": cum_match.group(5),
            "condition": cum_match.group(6)
        }

    seq_match = re.match(seq_pattern, alias)
    if seq_match:
        return {
            "project": seq_match.group(1),
            "scenario_type": "SEQ",
            "total_steps": int(seq_match.group(2)),
            "doe_index": None,
            "step": int(seq_match.group(3)),
            "mode": seq_match.group(4),
            "condition": seq_match.group(5)
        }

    return None


def get_mode_info(mode_code: str) -> dict:
    """모드 코드로 모드 정보 조회"""
    return SIMULATION_MODES.get(mode_code, {"full_name": "UNKNOWN", "description": "알 수 없는 모드"})
```

### 3.8 별칭 ↔ Run ID 검색 유틸리티

```python
class AliasManager:
    """별칭-Run ID 매핑 관리 (일반화된 버전)"""

    def __init__(self, index_path: str):
        with open(index_path, 'r') as f:
            self.index = json.load(f)
        self._build_lookup()

    def _build_lookup(self):
        """역참조 테이블 생성"""
        self.alias_to_runid = {}
        self.runid_to_alias = {}
        self.alias_to_mode = {}  # 모드 정보 추가

        for scenario in self.index["scenarios"]:
            for alias, info in scenario["runs"].items():
                run_id = info["run_id"]
                self.alias_to_runid[alias] = run_id
                self.runid_to_alias[run_id] = alias
                self.alias_to_mode[alias] = {
                    "mode": info.get("mode"),
                    "condition": info.get("condition")
                }

    def get_run_id(self, alias: str) -> str:
        """별칭 → Run ID"""
        return self.alias_to_runid.get(alias)

    def get_alias(self, run_id: str) -> str:
        """Run ID → 별칭"""
        return self.runid_to_alias.get(run_id)

    def get_folder(self, alias: str) -> str:
        """별칭 → 폴더 경로"""
        for scenario in self.index["scenarios"]:
            if alias in scenario["runs"]:
                return scenario["runs"][alias]["folder"]
        return None

    def get_mode(self, alias: str) -> dict:
        """별칭 → 시뮬레이션 모드 정보"""
        return self.alias_to_mode.get(alias)

    def get_chain(self, alias: str) -> list:
        """해당 alias의 전체 체인 반환 (첫 단계부터 끝까지)"""
        components = parse_alias(alias)
        if not components:
            return []

        chain = []
        for scenario in self.index["scenarios"]:
            for a, info in scenario["runs"].items():
                a_comp = parse_alias(a)
                if (a_comp and
                    a_comp["project"] == components["project"] and
                    a_comp["scenario_type"] == components["scenario_type"] and
                    a_comp["total_steps"] == components["total_steps"] and
                    a_comp.get("doe_index") == components.get("doe_index")):
                    chain.append((a_comp["step"], a, a_comp["mode"], a_comp["condition"]))

        chain.sort(key=lambda x: x[0])
        return [(a, mode, cond) for _, a, mode, cond in chain]

    def get_chain_by_mode(self, alias: str, mode_filter: str = None) -> list:
        """특정 모드만 필터링한 체인 반환

        Args:
            alias: 기준 별칭
            mode_filter: 필터링할 모드 (None이면 전체)

        Returns:
            [(alias, mode, condition), ...] 리스트
        """
        chain = self.get_chain(alias)
        if mode_filter:
            return [(a, m, c) for a, m, c in chain if m == mode_filter]
        return chain

    def get_scenario_summary(self, scenario_id: str) -> dict:
        """시나리오 요약 정보 반환"""
        for scenario in self.index["scenarios"]:
            if scenario["id"] == scenario_id:
                mode_counts = {}
                for alias, info in scenario["runs"].items():
                    mode = info.get("mode", "UNKNOWN")
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1

                return {
                    "name": scenario["name"],
                    "type": scenario["type"],
                    "total_steps": scenario["total_steps"],
                    "doe_count": scenario["doe_count"],
                    "total_runs": scenario["total_runs"],
                    "status": scenario["status"],
                    "mode_sequence": scenario.get("mode_sequence", []),
                    "mode_counts": mode_counts
                }
        return None
```

### 3.9 폴더 이름 변경 없이 별칭으로 작업

```
실제 폴더 구조 (변경 없음):
Data/Results/
├── Run_20260122_143048_p1q2r3/    # 기존 run_id 기반
├── Run_20260122_143050_x1y2z3/
├── Run_20260122_143052_a1b2c3/
└── simulation_index.json           # 마스터 인덱스

사용자가 보는 뷰 (별칭 기반):
$ python alias_lookup.py "GalaxyS25_CUM006_DOE001_S003_DROP_F1"
→ Folder: Run_20260122_143052_a1b2c3
→ Mode: DROP (DROP_ATTITUDE)
→ Condition: F1
→ Status: running
→ Prev: GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40
→ Next: (pending)

$ python alias_lookup.py --chain "GalaxyS25_CUM006_DOE001_S003_DROP_F1"
→ Chain for DOE001:
  Step 1: GalaxyS25_CUM006_DOE001_S001_THERM_HOT85    [completed] (열응력)
  Step 2: GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40  [completed] (열응력)
  Step 3: GalaxyS25_CUM006_DOE001_S003_DROP_F1        [running]   (낙하)
  Step 4: GalaxyS25_CUM006_DOE001_S004_THERM_CYC03    [pending]   (열응력)
  Step 5: GalaxyS25_CUM006_DOE001_S005_DROP_E5        [pending]   (낙하)
  Step 6: GalaxyS25_CUM006_DOE001_S006_DROP_C2        [pending]   (낙하)

$ python alias_lookup.py --mode-summary "scenario_001"
→ Scenario: 6회 열-낙하 복합 신뢰성 테스트
→ Mode Breakdown:
  - THERM: 3 steps (50%)
  - DROP:  3 steps (50%)
→ Mode Sequence: [THERM, THERM, DROP, THERM, DROP, DROP]
```

---

## 4. 2단계 분리 아키텍처: 설계자 + 실행자

### 4.1 아키텍처 개요

**핵심 원칙: "설계"와 "실행"의 완전 분리**

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: SIMULATION_AUTOMATION (설계자)                     │
│  위치: KooMeshModifier.py 내부                               │
│                                                             │
│  ▶ 역할: "무엇을 할지" 정의                                   │
│    - 시나리오 정의 (모드, 조건, DOE)                         │
│    - runner_config.json 생성                                │
│    - simulation_index.json 초기화                           │
│    - ❌ 실행은 하지 않음!                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓ JSON 파일 전달
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: CumulativeScenarioRunner.py (실행자)               │
│  위치: 별도 독립 Python 파일                                 │
│                                                             │
│  ▶ 역할: "정의된 대로" 실행                                   │
│    - runner_config.json 읽기                                │
│    - SLURM Job 내에서 순차 실행                              │
│    - KooMeshModifier 호출 (모델링)                          │
│    - LS-DYNA 실행 (시뮬레이션)                              │
│    - DYNAIN_TO_INITIAL 호출 (DR)                           │
│    - simulation_index.json 업데이트 (상태 추적)              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 분리의 장점

| 측면 | 장점 |
|------|------|
| **안전성** | 기존 KooMeshModifier 코드 수정 최소화 |
| **테스트** | Runner만 독립 테스트 가능 |
| **유연성** | Runner 교체로 다른 HPC 환경 지원 가능 (SLURM, PBS, LSF) |
| **디버깅** | JSON 파일로 중간 상태 확인 가능 |
| **재시작** | JSON 기반이라 체크포인트/재시작 용이 |
| **역할분리** | 시뮬레이션 로직 ↔ HPC 실행 로직 분리 |

### 4.3 파일 구조

```
pyKooCAE/
├── KooMeshModifier.py                    # 기존 (설계자 역할 추가)
├── KooCAEManager/
│   └── KooDynaAutomaticSimulationScriptGenerator.py  # runner_config 생성
│
├── Runner/                               # 신규 디렉토리
│   ├── CumulativeScenarioRunner.py       # 실행자 (메인)
│   ├── LSDynaSolverRunner.py             # LS-DYNA 실행기
│   ├── AliasManager.py                   # 별칭 관리 유틸리티
│   └── run_scenario.sh                   # SLURM Job 스크립트 템플릿
│
└── Examples/HWWarrantyDropTest/
    ├── scenario_definition.txt           # 사용자 입력 (시나리오 정의)
    ├── runner_config.json                # 자동 생성 (설계 결과)
    └── Data/Results/
        ├── simulation_index.json         # 실행 상태 추적
        └── Run_xxx/                      # 각 시뮬레이션 결과
```

---

## 5. Phase 1: 설계자 (SIMULATION_AUTOMATION)

### 5.1 역할

SIMULATION_AUTOMATION 모드가 시나리오를 파싱하고 **runner_config.json을 생성**

```
┌─────────────────────────────────────────────────────────────┐
│  사용자 입력: scenario_definition.txt                        │
│                                                             │
│  *Mode                                                      │
│  SIMULATION_AUTOMATION,1                                    │
│  **AnalysisType,mixedCumulative                            │
│  **Project,GalaxyS25                                        │
│  **DOECount,3                                               │
│  **Steps                                                    │
│  THERM,HOT85                                                │
│  THERM,COLD-40                                              │
│  DROP,F1                                                    │
│  THERM,CYC03                                                │
│  DROP,E5                                                    │
│  DROP,C2                                                    │
│  **EndSteps                                                 │
│  **EndSimulationAutomation                                  │
│  *End                                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  KooMeshModifier.py 실행                                    │
│  $ python KooMeshModifier.py scenario_definition.txt        │
│                                                             │
│  출력:                                                      │
│  ✅ runner_config.json 생성                                 │
│  ✅ simulation_index.json 초기화                            │
│  ✅ 각 Step별 KooMeshModifier 설정 파일 템플릿 생성          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 runner_config.json 스키마

```json
{
    "$schema": "runner_config_schema_v1",
    "generated_by": "SIMULATION_AUTOMATION",
    "generated_at": "2026-01-22T14:30:00",
    "version": "1.0",

    "environment": {
        "koomeshmodifier_path": "/opt/pyKooCAE/KooMeshModifier.py",
        "lsdyna_path": "/opt/lsdyna/lsdyna",
        "ncpu": 32,
        "memory": "2000m",
        "mpi_enabled": true
    },

    "project": {
        "name": "GalaxyS25",
        "model_file": "MinimumModel.k",
        "output_dir": "Data/Results",
        "index_file": "Data/Results/simulation_index.json"
    },

    "scenario": {
        "id": "scenario_001",
        "name": "6회 열-낙하 복합 신뢰성 테스트",
        "type": "mixedCumulative",
        "doe_count": 3,
        "total_steps": 6,

        "steps": [
            {
                "step": 1,
                "mode": "THERM",
                "mode_full": "THERMAL_CYCLE",
                "condition": "HOT85",
                "config_template": "step_001_THERM_HOT85.txt",
                "params": {
                    "initial_temp_C": 25,
                    "target_temp_C": 85,
                    "ramp_time_s": 600,
                    "hold_time_s": 1800
                }
            },
            {
                "step": 2,
                "mode": "THERM",
                "mode_full": "THERMAL_CYCLE",
                "condition": "COLD-40",
                "config_template": "step_002_THERM_COLD-40.txt",
                "params": {
                    "initial_temp_C": 25,
                    "target_temp_C": -40,
                    "ramp_time_s": 600,
                    "hold_time_s": 1800
                }
            },
            {
                "step": 3,
                "mode": "DROP",
                "mode_full": "DROP_ATTITUDE",
                "condition": "F1",
                "config_template": "step_003_DROP_F1.txt",
                "params": {
                    "euler_roll": 0,
                    "euler_pitch": 0,
                    "euler_yaw": 0,
                    "height_mm": 1500,
                    "surface": "steelPlate"
                }
            },
            {
                "step": 4,
                "mode": "THERM",
                "mode_full": "THERMAL_CYCLE",
                "condition": "CYC03",
                "config_template": "step_004_THERM_CYC03.txt",
                "params": {
                    "cycles": 3,
                    "temp_high": 85,
                    "temp_low": -40
                }
            },
            {
                "step": 5,
                "mode": "DROP",
                "mode_full": "DROP_ATTITUDE",
                "condition": "E5",
                "config_template": "step_005_DROP_E5.txt",
                "params": {
                    "euler_roll": 45,
                    "euler_pitch": 45,
                    "euler_yaw": 0,
                    "height_mm": 1500,
                    "surface": "steelPlate"
                }
            },
            {
                "step": 6,
                "mode": "DROP",
                "mode_full": "DROP_ATTITUDE",
                "condition": "C2",
                "config_template": "step_006_DROP_C2.txt",
                "params": {
                    "euler_roll": 35.264,
                    "euler_pitch": 45,
                    "euler_yaw": 0,
                    "height_mm": 1500,
                    "surface": "steelPlate"
                }
            }
        ]
    },

    "execution": {
        "checkpoint_enabled": true,
        "checkpoint_file": "Data/Results/checkpoint.json",
        "retry_on_failure": true,
        "max_retries": 2,
        "timeout_per_step_seconds": 7200
    }
}
```

---

## 6. Phase 2: 실행자 (CumulativeScenarioRunner.py)

### 6.1 역할

runner_config.json을 읽고 **실제 시뮬레이션을 순차 실행**

```
┌─────────────────────────────────────────────────────────────┐
│  SLURM Job 제출                                             │
│                                                             │
│  $ sbatch run_scenario.sh runner_config.json                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  CumulativeScenarioRunner.py 실행 (SLURM Job 내부)           │
│                                                             │
│  for doe in range(1, doe_count+1):                          │
│      for step in steps:                                     │
│          1. 체크포인트 확인 (이미 완료된 step 건너뛰기)        │
│          2. KooMeshModifier 호출 (모델링)                   │
│             - DROP_ATTITUDE 또는 THERMAL_CYCLE 등           │
│          3. LS-DYNA 실행 (MPI 병렬)                         │
│          4. dynain 생성 대기                                 │
│          5. KooMeshModifier 호출 (DYNAIN_TO_INITIAL)        │
│          6. simulation_index.json 업데이트                   │
│          7. 체크포인트 저장                                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 CumulativeScenarioRunner.py 구조

```python
#!/usr/bin/env python3
"""
Cumulative Scenario Runner - 독립 실행자

SIMULATION_AUTOMATION에서 생성한 runner_config.json을 읽고
실제 시뮬레이션을 순차 실행합니다.

Usage:
    python CumulativeScenarioRunner.py runner_config.json [--resume]
"""

import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime


class LSDynaSolverRunner:
    """LS-DYNA Solver 실행 및 관리"""

    def __init__(self, config):
        self.solver_path = config["environment"]["lsdyna_path"]
        self.ncpu = config["environment"]["ncpu"]
        self.memory = config["environment"]["memory"]
        self.mpi_enabled = config["environment"].get("mpi_enabled", False)

    def run(self, input_file, working_dir, timeout=7200):
        """LS-DYNA 실행 및 완료 대기"""
        if self.mpi_enabled:
            cmd = [
                "mpirun", "-np", str(self.ncpu),
                self.solver_path,
                f"i={input_file}",
                f"memory={self.memory}"
            ]
        else:
            cmd = [
                self.solver_path,
                f"i={input_file}",
                f"ncpu={self.ncpu}",
                f"memory={self.memory}"
            ]

        logging.info(f"Executing: {' '.join(cmd)}")
        logging.info(f"Working directory: {working_dir}")

        process = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            process.kill()
            logging.error(f"LS-DYNA timed out after {timeout} seconds")
            return False

    def wait_for_dynain(self, output_dir, timeout=7200, interval=10):
        """dynain 파일 생성 대기"""
        dynain_path = os.path.join(output_dir, "dynain")
        elapsed = 0

        while elapsed < timeout:
            if os.path.exists(dynain_path):
                # 파일 크기 안정화 확인
                size1 = os.path.getsize(dynain_path)
                time.sleep(2)
                size2 = os.path.getsize(dynain_path)
                if size1 == size2 and size1 > 0:
                    logging.info(f"dynain generated: {dynain_path}")
                    return True
            time.sleep(interval)
            elapsed += interval

        logging.error(f"dynain not generated within {timeout} seconds")
        return False


class CumulativeScenarioRunner:
    """누적 시나리오 실행자"""

    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.solver = LSDynaSolverRunner(self.config)
        self.koomesh_path = self.config["environment"]["koomeshmodifier_path"]
        self.output_dir = self.config["project"]["output_dir"]
        self.index_file = self.config["project"]["index_file"]
        self.checkpoint_file = self.config["execution"]["checkpoint_file"]

        self._setup_logging()
        self._load_checkpoint()
        self._load_index()

    def _setup_logging(self):
        """로깅 설정"""
        log_file = os.path.join(self.output_dir, "runner.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _load_checkpoint(self):
        """체크포인트 로드"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                self.checkpoint = json.load(f)
            logging.info(f"Checkpoint loaded: DOE {self.checkpoint['current_doe']}, Step {self.checkpoint['current_step']}")
        else:
            self.checkpoint = {
                "current_doe": 1,
                "current_step": 1,
                "completed_runs": []
            }

    def _save_checkpoint(self, doe, step):
        """체크포인트 저장"""
        self.checkpoint["current_doe"] = doe
        self.checkpoint["current_step"] = step
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def _load_index(self):
        """simulation_index.json 로드"""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = self._init_index()

    def _init_index(self):
        """simulation_index.json 초기화"""
        return {
            "project": self.config["project"]["name"],
            "created": datetime.now().isoformat(),
            "scenarios": [{
                "id": self.config["scenario"]["id"],
                "name": self.config["scenario"]["name"],
                "type": self.config["scenario"]["type"],
                "total_steps": self.config["scenario"]["total_steps"],
                "doe_count": self.config["scenario"]["doe_count"],
                "status": "in_progress",
                "runs": {}
            }]
        }

    def _update_index(self, alias, run_info):
        """simulation_index.json 업데이트"""
        scenario = self.index["scenarios"][0]
        scenario["runs"][alias] = run_info
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def run_all(self):
        """전체 시나리오 실행"""
        scenario = self.config["scenario"]
        doe_count = scenario["doe_count"]
        steps = scenario["steps"]

        logging.info(f"Starting scenario: {scenario['name']}")
        logging.info(f"DOE count: {doe_count}, Steps per DOE: {len(steps)}")

        for doe in range(self.checkpoint["current_doe"], doe_count + 1):
            start_step = self.checkpoint["current_step"] if doe == self.checkpoint["current_doe"] else 1

            for step_config in steps:
                step_num = step_config["step"]
                if step_num < start_step:
                    continue

                success = self.run_single_step(doe, step_config)

                if not success:
                    logging.error(f"Step {step_num} failed for DOE {doe}")
                    if not self.config["execution"]["retry_on_failure"]:
                        return False
                    # 재시도 로직
                    for retry in range(self.config["execution"]["max_retries"]):
                        logging.info(f"Retry {retry + 1}/{self.config['execution']['max_retries']}")
                        success = self.run_single_step(doe, step_config)
                        if success:
                            break
                    if not success:
                        return False

                self._save_checkpoint(doe, step_num + 1)

            # DOE 완료, 다음 DOE 준비
            self._save_checkpoint(doe + 1, 1)

        logging.info("All scenarios completed successfully!")
        return True

    def run_single_step(self, doe_index, step_config):
        """단일 Step 실행"""
        step_num = step_config["step"]
        mode = step_config["mode"]
        condition = step_config["condition"]

        alias = self._generate_alias(doe_index, step_num, mode, condition)
        logging.info(f"Running: {alias}")

        # 1. 작업 디렉토리 생성
        run_id = self._generate_run_id()
        run_dir = os.path.join(self.output_dir, f"Run_{run_id}")
        os.makedirs(run_dir, exist_ok=True)
        os.makedirs(os.path.join(run_dir, "Output"), exist_ok=True)

        # 2. KooMeshModifier 설정 파일 생성
        config_file = self._create_step_config(doe_index, step_config, run_dir)

        # 3. KooMeshModifier 실행 (모델링)
        if not self._run_koomeshmodifier(config_file):
            return False

        # 4. LS-DYNA 실행
        input_file = self._find_input_file(run_dir, mode)
        if not self.solver.run(input_file, run_dir):
            return False

        # 5. dynain 생성 대기
        output_dir = os.path.join(run_dir, "Output")
        if not self.solver.wait_for_dynain(output_dir):
            return False

        # 6. DYNAIN_TO_INITIAL 실행 (마지막 step 제외)
        if step_num < self.config["scenario"]["total_steps"]:
            dti_file = os.path.join(run_dir, "DynamicRelaxation", "dynaintoinitial.txt")
            if os.path.exists(dti_file):
                self._run_koomeshmodifier(dti_file)

        # 7. Index 업데이트
        self._update_index(alias, {
            "run_id": run_id,
            "status": "completed",
            "folder": f"Run_{run_id}",
            "mode": mode,
            "condition": condition,
            "completed_at": datetime.now().isoformat()
        })

        logging.info(f"Completed: {alias}")
        return True

    def _generate_alias(self, doe_index, step, mode, condition):
        """별칭 생성"""
        project = self.config["project"]["name"]
        total_steps = self.config["scenario"]["total_steps"]
        return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"

    def _generate_run_id(self):
        """Run ID 생성"""
        import hashlib
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
        return f"{timestamp}_{unique_hash}"

    def _create_step_config(self, doe_index, step_config, run_dir):
        """Step별 KooMeshModifier 설정 파일 생성"""
        # 구현: step_config["params"]를 기반으로 설정 파일 생성
        # 이전 step의 결과(dynain)를 입력으로 사용
        pass

    def _run_koomeshmodifier(self, config_file):
        """KooMeshModifier 실행"""
        cmd = ["python3", self.koomesh_path, config_file]
        logging.info(f"Running KooMeshModifier: {config_file}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"KooMeshModifier failed: {result.stderr}")
            return False
        return True

    def _find_input_file(self, run_dir, mode):
        """LS-DYNA 입력 파일 찾기"""
        if mode == "DROP":
            return "DropSet.k"
        elif mode == "THERM":
            return "ThermalSet.k"
        else:
            return "SimulationSet.k"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python CumulativeScenarioRunner.py runner_config.json [--resume]")
        sys.exit(1)

    config_path = sys.argv[1]
    runner = CumulativeScenarioRunner(config_path)
    success = runner.run_all()
    sys.exit(0 if success else 1)
```

---

## 7. SLURM 연동

### 7.1 SLURM Job 스크립트 (run_scenario.sh)

```bash
#!/bin/bash
#SBATCH --job-name=CumScenario
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --time=48:00:00
#SBATCH --output=scenario_%j.out
#SBATCH --error=scenario_%j.err

# 환경 설정
module load python/3.9
module load lsdyna/R13

# 설정 파일 경로
CONFIG_FILE=${1:-runner_config.json}

# Runner 실행
echo "Starting Cumulative Scenario Runner..."
echo "Config: $CONFIG_FILE"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"

python /opt/pyKooCAE/Runner/CumulativeScenarioRunner.py $CONFIG_FILE

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Scenario completed successfully"
else
    echo "Scenario failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
```

### 7.2 실행 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  1. 로컬에서 시나리오 정의 및 설정 생성                       │
│                                                             │
│  $ python KooMeshModifier.py scenario_definition.txt        │
│  → runner_config.json 생성                                  │
│  → simulation_index.json 초기화                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. SLURM Job 제출                                          │
│                                                             │
│  $ sbatch run_scenario.sh runner_config.json                │
│  → Job ID: 12345                                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. HPC 노드에서 Runner 실행 (자동)                          │
│                                                             │
│  CumulativeScenarioRunner.py가 순차적으로:                   │
│    - DOE 1: Step 1 → Step 2 → ... → Step N                 │
│    - DOE 2: Step 1 → Step 2 → ... → Step N                 │
│    - ...                                                    │
│  각 Step마다 체크포인트 저장                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 완료 또는 재시작                                         │
│                                                             │
│  정상 완료: simulation_index.json에 모든 결과 기록           │
│  시간 초과: $ sbatch run_scenario.sh runner_config.json     │
│            → 체크포인트에서 자동 재개                        │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 DOE 병렬 실행 (선택적)

독립적인 DOE 케이스는 병렬 실행 가능:

```bash
#!/bin/bash
#SBATCH --job-name=CumScenario_Parallel
#SBATCH --nodes=5
#SBATCH --ntasks-per-node=32
#SBATCH --time=24:00:00

CONFIG_FILE=${1:-runner_config.json}

# DOE 5개를 5개 노드에서 병렬 실행
for DOE in 1 2 3 4 5; do
    srun --nodes=1 --ntasks=32 --exclusive \
        python /opt/pyKooCAE/Runner/CumulativeScenarioRunner.py \
        $CONFIG_FILE --doe=$DOE &
done

wait
echo "All DOE cases completed"
```

---

## 8. 체크포인트 및 재시작

### 8.1 체크포인트 파일 (checkpoint.json)

```json
{
    "scenario_id": "scenario_001",
    "current_doe": 2,
    "current_step": 4,
    "completed_runs": [
        "GalaxyS25_CUM006_DOE001_S001_THERM_HOT85",
        "GalaxyS25_CUM006_DOE001_S002_THERM_COLD-40",
        "GalaxyS25_CUM006_DOE001_S003_DROP_F1",
        "GalaxyS25_CUM006_DOE001_S004_THERM_CYC03",
        "GalaxyS25_CUM006_DOE001_S005_DROP_E5",
        "GalaxyS25_CUM006_DOE001_S006_DROP_C2",
        "GalaxyS25_CUM006_DOE002_S001_THERM_HOT85",
        "GalaxyS25_CUM006_DOE002_S002_THERM_COLD-40",
        "GalaxyS25_CUM006_DOE002_S003_DROP_F1"
    ],
    "last_updated": "2026-01-22T18:45:30",
    "failure_count": 0
}
```

### 8.2 재시작 시나리오

```
시나리오: DOE 2의 Step 4에서 Job 시간 초과

1. Job 재제출
   $ sbatch run_scenario.sh runner_config.json

2. Runner가 checkpoint.json 로드
   → current_doe=2, current_step=4 확인

3. DOE 1 건너뛰기 (이미 완료)

4. DOE 2의 Step 1~3 건너뛰기 (이미 완료)

5. DOE 2의 Step 4부터 재개
```

---

## 9. 폴더 구조 예시 (6회 복합 시나리오)

```
Data/Results/
├── runner_config.json               # 설계자가 생성한 설정
├── simulation_index.json            # 실행 상태 추적
├── checkpoint.json                  # 재시작용 체크포인트
├── runner.log                       # 실행 로그
│
├── Run_20260122_143048_p1q2r3/      # DOE001_S001_THERM_HOT85
│   ├── ThermalSet.k
│   ├── ThermalSet.json
│   ├── Output/
│   │   ├── d3plot
│   │   └── dynain
│   └── DynamicRelaxation/
│       └── dynaintoinitial.txt
│
├── Run_20260122_143050_x1y2z3/      # DOE001_S002_THERM_COLD-40
│   ├── ThermalSet.k
│   ├── Output/
│   │   ├── d3plot
│   │   └── dynain
│   └── DynamicRelaxation/
│       └── dynaintoinitial.txt
│
├── Run_20260122_143052_a1b2c3/      # DOE001_S003_DROP_F1
│   ├── DropSet.k
│   ├── DropSet.json
│   ├── Output/
│   │   ├── d3plot
│   │   └── dynain
│   └── DynamicRelaxation/
│       └── dynaintoinitial.txt
│
...  (DOE001_S004 ~ S006, DOE002, DOE003 ...)
```

---

## 10. 구현 로드맵

### Phase 1: 설계자 구현 (SIMULATION_AUTOMATION)

1. **mixedCumulative 파싱 로직 추가** (`KooDynaAutomaticSimulationScriptGenerator.py`)
2. **runner_config.json 생성 로직 구현**
3. **simulation_index.json 초기화 로직 구현**
4. **Step별 config template 생성 로직 구현**

### Phase 2: 실행자 구현 (CumulativeScenarioRunner.py)

1. **Runner 디렉토리 구조 생성** (`/Runner/`)
2. **CumulativeScenarioRunner.py 핵심 로직 구현**
3. **LSDynaSolverRunner.py 분리**
4. **AliasManager.py 유틸리티 구현**
5. **체크포인트/재시작 로직 구현**

### Phase 3: SLURM 연동

1. **run_scenario.sh 템플릿 작성**
2. **DOE 병렬 실행 옵션 구현**
3. **Job 모니터링 유틸리티 구현**

### Phase 4: 테스트 및 검증

1. **단일 DOE 2-3 step 테스트**
2. **다중 DOE 테스트**
3. **체크포인트/재시작 테스트**
4. **SLURM 환경 테스트**

---

## 11. 결정 사항 요약

| 항목 | 결정 |
|------|------|
| **아키텍처** | 2단계 분리 (설계자 + 실행자) |
| **설계자 위치** | KooMeshModifier 내부 (SIMULATION_AUTOMATION) |
| **실행자 위치** | 별도 Python 파일 (CumulativeScenarioRunner.py) |
| **데이터 전달** | runner_config.json |
| **상태 추적** | simulation_index.json |
| **재시작 지원** | checkpoint.json |
| **HPC 연동** | SLURM (run_scenario.sh) |
| **DOE 병렬화** | 선택적 지원 |

---

## Author

- Creator: koo.park
- Email: koo.park@samsung.com
- Group: CAE
