# Cumulative Drop Automation 진행 상황 정리

## 📋 프로젝트 개요

**목표**: 다단계 누적 시뮬레이션(Cumulative Scenario) 자동화 시스템 구축
- 여러 물리 해석 모드(DROP, THERM, DWI 등)를 순차적으로 연결
- 이전 스텝의 변형 상태를 다음 스텝의 초기 조건으로 활용
- DOE(Design of Experiments) 병렬 실행 지원
- HPC(SLURM) 환경에서의 대규모 시뮬레이션 자동화

---

## 🏗️ 시스템 아키텍처

### 2-Stage 분리 설계

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Designer (SIMULATION_AUTOMATION)                   │
│ - 위치: KooDynaAutomaticSimulationScriptGenerator.py        │
│ - 역할: 시나리오 파싱, runner_config.json 생성              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   runner_config.json
                   simulation_index.json
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Executor (CumulativeScenarioRunner.py)             │
│ - 위치: Runner/CumulativeScenarioRunner.py                  │
│ - 역할: JSON 읽어서 실제 시뮬레이션 순차 실행               │
└─────────────────────────────────────────────────────────────┘
```

**분리 이유**:
- Designer는 KooMeshModifier 환경에서 실행 (GUI/전처리 환경)
- Executor는 HPC 클러스터에서 실행 (계산 환경)
- JSON 파일로 데이터 전달 → 환경 독립성 확보

---

## ✅ 완료된 작업 (Phase 1 & 2)

### 1. Designer 구현 (KooDynaAutomaticSimulationScriptGenerator.py)

#### 추가된 주요 타입 및 상수
```python
SimulationMode = Literal["DROP", "THERM", "STAT", "VIB", "DWI", "COMB"]

SIMULATION_MODES = {
    "DROP": {"full_name": "DROP_ATTITUDE", "description": "낙하 시뮬레이션"},
    "THERM": {"full_name": "THERMAL_CYCLE", "description": "열응력/열사이클 해석"},
    "DWI": {"full_name": "DROP_WEIGHT_IMPACT", "description": "중량 충격 시뮬레이션"},
    "STAT": {"full_name": "STATIC_LOAD", "description": "정적 하중 해석"},
    "VIB": {"full_name": "VIBRATION", "description": "진동 해석"},
    "COMB": {"full_name": "COMBINED", "description": "복합 조건 해석"},
}
```

#### 추가된 데이터 클래스
- `MixedStepConfig`: 각 스텝의 모드, 컨디션, 파라미터 저장
- `MixedCumulativeConfig`: 전체 시나리오 구성 정보

#### 핵심 함수
| 함수명 | 역할 | 위치 |
|--------|------|------|
| `parse_mixed_cumulative()` | mixedCumulative 시나리오 JSON 파싱 | KooDynaAutomaticSimulationScriptGenerator.py:~300 |
| `script_mixed_cumulative()` | 각 스텝별 KooMeshModifier 스크립트 생성 | KooDynaAutomaticSimulationScriptGenerator.py:~400 |
| `generate_runner_config()` | runner_config.json 생성 (Executor용) | KooDynaAutomaticSimulationScriptGenerator.py:~500 |
| `generate_simulation_index()` | simulation_index.json 생성 (상태 추적용) | KooDynaAutomaticSimulationScriptGenerator.py:~600 |
| `generate_alias()` | 시뮬레이션 별칭 생성 | KooDynaAutomaticSimulationScriptGenerator.py:~700 |

#### 생성되는 JSON 파일 구조

**runner_config.json**:
```json
{
  "project_name": "HWWarranty",
  "total_steps": 6,
  "doe_count": 10,
  "base_runid": "KUMHO_DROP_RIGID_GROUND",
  "scenarios": [
    {
      "doe_index": 0,
      "steps": [
        {"step": 1, "mode": "THERM", "condition": "HOT85", "params": {...}},
        {"step": 2, "mode": "DROP", "condition": "F1", "params": {...}},
        ...
      ]
    },
    ...
  ]
}
```

**simulation_index.json**:
```json
{
  "HWWarranty_CUM006_DOE000_S001_THERM_HOT85": {
    "alias": "HWWarranty_CUM006_DOE000_S001_THERM_HOT85",
    "run_id": "KUMHO_DROP_RIGID_GROUND_001",
    "folder": "KUMHO_DROP_RIGID_GROUND_001",
    "doe_index": 0,
    "step": 1,
    "total_steps": 6,
    "mode": "THERM",
    "condition": "HOT85",
    "prev_alias": null
  },
  ...
}
```

---

### 2. Executor 구현 (Runner/)

#### 생성된 파일 목록

| 파일명 | 역할 | 주요 클래스/함수 |
|--------|------|------------------|
| `CumulativeScenarioRunner.py` | 메인 실행기 | `CumulativeScenarioRunner`, `LSDynaSolverRunner` |
| `AliasManager.py` | 별칭 관리 유틸리티 | `AliasManager`, `parse_alias()`, `generate_alias_cumulative()` |
| `run_scenario.sh` | SLURM 단일 작업 스크립트 | - |
| `run_scenario_parallel.sh` | SLURM 병렬 DOE 스크립트 | - |

#### CumulativeScenarioRunner.py 핵심 기능

**1. Checkpoint/Restart 지원**:
```python
# checkpoint.json 구조
{
  "last_completed_step": 2,
  "last_completed_doe": 1,
  "total_completed": 23,
  "timestamp": "2026-01-22T10:30:00"
}
```

**2. DROP 모드 Euler 각도 매핑**:
```python
def _condition_to_euler(self, condition: str) -> Optional[Tuple[float, float, float]]:
    """
    F1~F6 (6 faces), E1~E12 (12 edges), C1~C8 (8 corners)
    → (phi, theta, psi) Euler angles
    """
    # 예: F1 → (0, 0, 0), F2 → (180, 0, 0), E1 → (0, 45, 0), ...
```

**3. KooMeshModifier Config 생성**:
```python
def _create_step_config(self, scenario: dict, step_info: dict, prev_alias: Optional[str]) -> dict:
    """
    각 스텝별로 KooMeshModifier용 config_simulation_XXX.json 생성
    - DROP 모드: DROP_ATTITUDE 설정
    - THERM 모드: THERMAL_CYCLE 설정 (템플릿만 존재)
    """
```

**4. LS-DYNA 실행 래퍼**:
```python
class LSDynaSolverRunner:
    def run(self, k_file: str, ncpu: int = 32) -> bool:
        """
        mpp-dyna 실행 및 로그 모니터링
        - d3hsp 파일 생성 확인
        - Normal termination 체크
        """
```

#### AliasManager.py 기능

**별칭 형식**: `{Project}_CUM{TotalSteps:03d}_DOE{Index:03d}_S{Step:03d}_{Mode}_{Condition}`

예시:
- `HWWarranty_CUM006_DOE000_S001_THERM_HOT85`
- `HWWarranty_CUM006_DOE000_S002_DROP_F1`
- `HWWarranty_CUM003_DOE005_S003_DROP_E7`

주요 메서드:
- `get_run_id(alias)`: 별칭 → run_id 변환
- `get_alias(run_id)`: run_id → 별칭 변환
- `get_chain(alias)`: 해당 별칭의 전체 스텝 체인 반환
- `get_scenario_summary()`: DOE별 시나리오 요약

#### SLURM 스크립트

**run_scenario.sh** (단일 순차 실행):
```bash
#!/bin/bash
#SBATCH --job-name=CumScenario
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --time=48:00:00

python3 CumulativeScenarioRunner.py runner_config.json
```

**run_scenario_parallel.sh** (DOE 병렬 실행):
```bash
#!/bin/bash
#SBATCH --job-name=CumDOE
#SBATCH --array=0-9  # DOE 개수만큼
#SBATCH --nodes=1
#SBATCH --ntasks=32

python3 CumulativeScenarioRunner.py runner_config.json --doe-index $SLURM_ARRAY_TASK_ID
```

---

### 3. 테스트 예제 생성

**sample_mixed_cumulative.json**:
- 6단계 혼합 시나리오: THERM(HOT85) → DROP(F1~F6)
- 3단계 DROP 전용 시나리오: DROP(F1, E1, C1)

---

### 4. 문서화 작업

**MODE_CONDITION_Reference.md**: 모든 모드와 컨디션 정의 문서
- 6가지 시뮬레이션 모드 설명
- DROP 모드 26개 컨디션 매핑 (F1~F6, E1~E12, C1~C8)
- THERM 모드 컨디션 계획 (HOT85, COLD-40, CYC01~10)
- 구현 상태 매트릭스

---

## 📊 구현 상태 요약

### 모드별 구현 현황

| 모드 | Designer 파싱 | Designer 스크립트 | KooMeshModifier | Runner 실행 | 상태 |
|------|--------------|------------------|----------------|-------------|------|
| DROP | ✅ | ✅ | ✅ | ✅ | **완료** |
| THERM | ✅ | ✅ | ❌ | ⚠️ (템플릿) | **부분 구현** |
| DWI | ❌ | ❌ | ✅ | ❌ | **부분 구현** |
| STAT | ❌ | ❌ | ❌ | ❌ | 미착수 |
| VIB | ❌ | ❌ | ❌ | ❌ | 미착수 |
| COMB | ❌ | ❌ | ❌ | ❌ | 미착수 |

### 컨디션 구현 현황

**DROP 모드**: 26개 전체 구현 완료
- Face: F1~F6 (6개) ✅
- Edge: E1~E12 (12개) ✅
- Corner: C1~C8 (8개) ✅

**THERM 모드**: 설계 완료, 구현 대기
- 정적 온도: HOT85, COLD-40 (2개)
- 열사이클: CYC01~CYC10 (10개)

**기타 모드**: 컨디션 정의 대기

---

## 🔧 주요 기술 구현

### 1. DYNAIN_TO_INITIAL 워크플로

모든 누적 시뮬레이션의 핵심 패턴:
```
Step N-1 실행 → d3plot 생성 → dynain 추출
         ↓
Step N 실행 시 *INITIAL_FOAM_REFERENCE_GEOMETRY, *INITIAL_STRESS_SHELL 적용
```

### 2. Tolerance 기반 DOE 생성

초기 자세 DOE 생성 시 공차 적용:
```python
tolerance = {
    "phi": {"min": -5, "max": 5},
    "theta": {"min": -5, "max": 5},
    "psi": {"min": -5, "max": 5}
}
```

### 3. 별칭 시스템 (Traceability)

복잡한 DOE × 다단계 시뮬레이션을 추적 가능하게 관리:
- Human-readable: `HWWarranty_CUM006_DOE000_S001_THERM_HOT85`
- Unique run_id 매핑: `KUMHO_DROP_RIGID_GROUND_001`
- 전체 체인 추적: DOE000의 S001 → S002 → ... → S006

---

## 📂 파일 구조

```
pyKooCAE/
├── occProject/Generators/KooCAEManager/
│   └── KooDynaAutomaticSimulationScriptGenerator.py  (Designer - 수정됨)
├── Runner/
│   ├── CumulativeScenarioRunner.py  (Executor - 신규)
│   ├── AliasManager.py              (Utility - 신규)
│   ├── run_scenario.sh              (SLURM script - 신규)
│   └── run_scenario_parallel.sh     (SLURM DOE script - 신규)
└── Examples/HWWarrantyDropTest/
    ├── sample_mixed_cumulative.json      (예제 - 신규)
    ├── MODE_CONDITION_Reference.md       (문서 - 신규)
    ├── CumulativeDrop_Automation_Plan.md (설계 문서 - 기존)
    └── CumulativeDrop_Workflow_Reference.md (워크플로 - 기존)
```

---

## 🚀 사용 방법

### Step 1: Designer에서 시나리오 정의

```json
{
  "id": "mixed_thermal_drop",
  "name": "6-Step Mixed Scenario",
  "analysisType": "mixedCumulative",
  "projectName": "HWWarranty",
  "doeCount": 10,
  "steps": [
    {"step": 1, "mode": "THERM", "condition": "HOT85", "params": {...}},
    {"step": 2, "mode": "DROP", "condition": "F1", "params": {...}},
    ...
  ]
}
```

### Step 2: SIMULATION_AUTOMATION 실행

KooMeshModifier UI 또는 스크립트로 실행:
```python
from KooDynaAutomaticSimulationScriptGenerator import generate_and_save_all_configs

config = parse_mixed_cumulative("sample_mixed_cumulative.json")
generate_and_save_all_configs(config, output_dir="./output/")
```

생성 결과:
- `runner_config.json`: Executor 입력 파일
- `simulation_index.json`: 상태 추적 파일
- `config_simulation_XXX.json`: 각 스텝별 KooMeshModifier 설정

### Step 3: HPC에서 Executor 실행

단일 순차 실행:
```bash
sbatch run_scenario.sh runner_config.json
```

DOE 병렬 실행:
```bash
sbatch --array=0-9 run_scenario_parallel.sh runner_config.json
```

재시작 (checkpoint 활용):
```bash
python3 CumulativeScenarioRunner.py runner_config.json --restart
```

### Step 4: 결과 확인

AliasManager로 결과 조회:
```python
from AliasManager import AliasManager

mgr = AliasManager("simulation_index.json")
summary = mgr.get_scenario_summary()
chain = mgr.get_chain("HWWarranty_CUM006_DOE000_S003_DROP_F3")
```

---

## ⚠️ 현재 제약사항

### 1. THERM 모드 미완성
- Designer에서 JSON 생성은 가능
- Runner에서 config 생성 템플릿만 존재
- **KooMeshModifier의 THERMAL_CYCLE 기능 구현 필요**

### 2. DWI 모드 미연결
- KooMeshModifier에 DROP_WEIGHT_IMPACT_TEST 기능은 존재
- Designer 파싱 및 Runner 연결 미구현

### 3. STAT/VIB/COMB 모드 미착수
- 모드 정의만 존재
- 전체 파이프라인 구현 필요

### 4. 에러 처리 강화 필요
- 시뮬레이션 실패 시 재시도 로직 부재
- 디스크 용량/메모리 부족 대응 미흡

---

## 📈 다음 단계 (우선순위)

### Priority 1: THERM 모드 완성
1. KooMeshModifier에 `THERMAL_CYCLE` 구현
   - 온도 로드 커브 생성
   - 경계 조건 설정
   - DYNAIN 초기화 연동
2. Runner의 `_create_step_config()` THERM 섹션 완성
3. 테스트: HOT85, COLD-40, CYC01 검증

### Priority 2: DWI 모드 연결
1. Designer에 DWI 파싱 추가 (`parse_mixed_cumulative()` 확장)
2. Runner에 DWI config 생성 로직 추가
3. 기존 DROP_WEIGHT_IMPACT_TEST 기능과 연동

### Priority 3: 안정성 개선
1. 시뮬레이션 실패 시 자동 재시도 (최대 3회)
2. 디스크 용량 사전 체크
3. 로그 수집 및 요약 리포트 생성

### Priority 4: STAT/VIB 모드 구현
- 사용자 요구사항 확인 후 우선순위 결정

---

## 🎯 핵심 성과

1. **2-Stage 아키텍처로 환경 분리 달성**
   - Designer(GUI) ↔ Executor(HPC) 완전 독립
   - JSON 기반 데이터 전달로 유연성 확보

2. **DROP 모드 전체 자동화 완성**
   - 26개 컨디션 (F/E/C) 전체 Euler 각도 매핑 완료
   - DOE × 다단계 누적 시뮬레이션 검증 가능

3. **확장 가능한 모드 시스템 구축**
   - 6개 모드 타입 정의 및 인터페이스 설계
   - 새로운 모드 추가 시 일관된 패턴 적용 가능

4. **Checkpoint/Restart로 안정성 확보**
   - 장시간 시뮬레이션 중단 시 이어서 실행 가능
   - HPC 자원 효율적 활용

5. **Alias 시스템으로 추적성 향상**
   - 수백~수천 개 시뮬레이션 체계적 관리
   - DOE-Step 체인 완전 추적 가능

---

## 📝 참고 문서

- [CumulativeDrop_Automation_Plan.md](CumulativeDrop_Automation_Plan.md): 초기 설계 문서
- [CumulativeDrop_Workflow_Reference.md](CumulativeDrop_Workflow_Reference.md): 워크플로 상세
- [MODE_CONDITION_Reference.md](MODE_CONDITION_Reference.md): 모드/컨디션 정의
- [SIMULATION_AUTOMATION_Reference.md](../SIMULATION_AUTOMATION_Reference.md): 전체 자동화 시스템 가이드

---

**문서 생성일**: 2026-01-22
**작성자**: Claude Code (Sonnet 4.5)
**프로젝트 상태**: Phase 1-2 완료, Phase 3 (THERM 구현) 대기 중
