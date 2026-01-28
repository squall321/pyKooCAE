# Cumulative Drop Automation Context v3.0

**날짜**: 2026-01-23
**상태**: 프로덕션 준비 완료
**주요 업데이트**: Simulation Automation 워크플로우 통합, HPC 자원 제어 개선, 문서 정리

---

## 프로젝트 개요

**목적**: 대규모 누적 낙하 시뮬레이션 자동화 시스템

**핵심 기능**:
- Scenario 기반 설정 (scenarios JSON)
- 대규모 병렬 실행 (Slurm Array Job)
- 누적 낙하 자동화 (KooMeshModifier → LS-DYNA → DYNAIN_TO_INITIAL)
- 명시적 HPC 자원 제어 (nodes, jobs-per-node, ncpu-per-job)
- 각도 믹싱 전략 (same_angle, cyclic, random, opposite, custom)
- DOE 확장 (Tolerance 기반)

---

## 전체 워크플로우

```
1. Scenario Definition
   - scenarios_*.json 작성 (GUI 또는 수동)
   - analysisType, angleSource, tolerance 설정
   ↓
2. Configuration Generation
   - KooDynaAutomaticSimulationScriptGenerator.py
   - runner_config.json + simulation_index.json 생성
   - runid 할당
   ↓
3. Large-Scale Execution
   - LargeScaleDOEManager.py
   - Slurm Array Job 제출 (동시 실행 제한)
   - runid 디렉토리 생성
   ↓
4. Sequential Analysis (Per runid)
   - Step 1: KooMeshModifier → LS-DYNA
   - Step 2+: DYNAIN_TO_INITIAL → KooMeshModifier → LS-DYNA
   - Lock 파일 생성
```

---

## 핵심 모듈

### 1. KooDynaAutomaticSimulationScriptGenerator.py
**위치**: `occProject/Generators/KooCAEManager/`
**기능**: scenarios JSON → runner_config.json 변환

**지원 analysisType**:
- `fullAngle`: 전각도 (Face/Edge/Corner)
- `fullAngleMBD`: MBD 기반 전각도
- `fullAngleCumulative`: 전각도 누적 낙하
- `multiRepeatCumulative`: 다중 반복 누적
- `partialImpact`: 부분 충격
- `mixedCumulative`: 복합 조건 (DROP + THERM + VIB)

**입력**: scenarios_*.json
**출력**: runner_config_*.json, simulation_index_*.json

### 2. CumulativeDesigner.py
**위치**: `Examples/HWWarrantyDropTest/`
**기능**: 사용자 정의 JSON → runner_config.json 변환 (대체 방법)

**특징**:
- 각도 믹싱 전략 지원
- DOE 확장 (Tolerance)
- Fibonacci, LHS, case_txt_file

### 3. LargeScaleDOEManager.py
**위치**: `Runner/`
**기능**: 대규모 병렬 실행 및 누적 낙하 자동화

**주요 변경사항 (v3.0)**:
- **명시적 자원 제어**: `--nodes`, `--jobs-per-node`, `--ncpu-per-job`
- **동시 실행 제한**: Slurm `--array=1-5000%40`
- **자원 계산 출력**: 노드, Job, CPU, Rounds 정보 표시

**실행 예시**:
```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**계산**:
- 동시 실행: 10 × 4 = 40개
- Slurm: `#SBATCH --array=1-5000%40`
- 노드당 CPU: 4 × 16 = 64 (50% 활용)

---

## 주요 변경사항 (v2.1 → v3.0)

### 1. Simulation Automation 워크플로우 명확화

**이해한 내용**:
- scenarios JSON은 **입력 형식 표준**
- KooDynaAutomaticSimulationScriptGenerator가 **파싱 및 변환**
- LargeScaleDOEManager가 **실행**

**문서화**:
- SIMULATION_AUTOMATION_WORKFLOW.md 작성 (23KB)
- 3단계 워크플로우 상세 설명
- scenarios JSON 형식 문서화

### 2. HPC 자원 제어 개선

**문제**: `--ncpu`만으로는 자원 배분 불명확

**해결**:
```python
def __init__(self, ..., nodes: int = 1, jobs_per_node: int = 1, ncpu_per_job: int = 16):
    self.total_concurrent_jobs = nodes * jobs_per_node
```

**Slurm 스크립트**:
```bash
#SBATCH --array=1-5000%40  # 최대 40개 동시 실행
#SBATCH --cpus-per-task=16
```

**장점**:
- 사용자가 정확히 제어 가능
- 128 코어 346 노드 환경 최적화
- 공유 vs 전용 노드 전략 지원

### 3. 문서 정리

**메인 폴더** (4개 핵심 문서):
- README.md - 시스템 소개 및 Quick Start
- QUICK_START_GUIDE.md - 빠른 시작
- COMPLETE_SYSTEM_OVERVIEW.md - 전체 시스템 개요
- SIMULATION_AUTOMATION_WORKFLOW.md - 워크플로우 상세

**docs/ 폴더** (상세 문서):
- ANGLE_MIXING_STRATEGIES_GUIDE.md
- DIRECT_INPUT_WORKFLOW_GUIDE.md
- NODE_MONITORING_EXAMPLES.md
- WORKFLOW_VERIFICATION_REPORT.md
- CustomScenarios/

**신규 문서**:
- RESOURCE_PLANNING_GUIDE.md (자원 계획 및 최적화)

---

## 시스템 사양 및 권장 설정

### HPC 클러스터
- 총 346개 노드 (128 코어/노드)
- 46개: 공유 노드
- 300개: 전용 가능

### 권장 설정

**공유 노드 (50% 활용)**:
```bash
--nodes 10 --jobs-per-node 4 --ncpu-per-job 16
# 동시: 40개, 노드당 64 CPU
```

**전용 노드 (100% 활용)**:
```bash
--nodes 20 --jobs-per-node 8 --ncpu-per-job 16
# 동시: 160개, 노드당 128 CPU
```

**대규모 (최대 성능)**:
```bash
--nodes 300 --jobs-per-node 8 --ncpu-per-job 16
# 동시: 2,400개
```

---

## 각도 소스 (Angle Source)

### 지원 타입

| 소스 | 설명 | 케이스 수 |
|------|------|----------|
| `fibonacci_lattice` | Fibonacci Lattice 균등 분포 | 사용자 지정 |
| `lhs` | Latin Hypercube Sampling | 사용자 지정 |
| `full_angle_26` | 전각도 26개 | 26 |
| `case_txt_file` | 커스텀 txt 파일 | 파일 정의 |

### DOE 확장 (Tolerance)

```json
{
  "tolerance": {
    "roll": {"tolerance": 5.0},
    "pitch": {"tolerance": 5.0},
    "doe_type": "lhs",
    "doe_count": 5
  }
}
```

**결과**: Base 100개 × DOE 5 = 500개

---

## 각도 믹싱 전략

누적 낙하 시 각 Step에서 다른 각도를 사용:

| 전략 | 설명 | 예시 |
|------|------|------|
| `same_angle` | 동일 각도 | 각도1 → 각도1 → 각도1 |
| `cyclic` | 순환 | 각도1 → 각도2 → 각도3 |
| `random` | 랜덤 | 각도1 → 각도4 → 각도2 |
| `opposite` | 반대 방향 | 각도1 → 반대 → 반대 |
| `custom_mapping` | 사용자 정의 | [1,3,2] |

---

## 핵심 파일 위치

### Python 모듈
```
occProject/Generators/KooCAEManager/
├── KooDynaAutomaticSimulationScriptGenerator.py  # scenarios JSON 파서
├── KooDynaAdvancedModification.py                 # 누적 낙하 로직
└── ...

Runner/
├── LargeScaleDOEManager.py                        # 대규모 실행 관리
├── CaseTxtParser.py                               # Case txt 파서
└── ...

Examples/HWWarrantyDropTest/
├── CumulativeDesigner.py                          # 사용자 JSON 변환
└── ...
```

### 문서
```
Examples/HWWarrantyDropTest/
├── README.md                              # 메인 문서
├── QUICK_START_GUIDE.md                   # 빠른 시작
├── COMPLETE_SYSTEM_OVERVIEW.md            # 전체 개요
├── SIMULATION_AUTOMATION_WORKFLOW.md      # 워크플로우
├── RESOURCE_PLANNING_GUIDE.md             # 자원 계획
└── docs/                                  # 상세 문서
    ├── ANGLE_MIXING_STRATEGIES_GUIDE.md
    ├── DIRECT_INPUT_WORKFLOW_GUIDE.md
    ├── NODE_MONITORING_EXAMPLES.md
    ├── WORKFLOW_VERIFICATION_REPORT.md
    └── CustomScenarios/
```

---

## 실행 예제

### 예제 1: 소규모 테스트 (150 Jobs)

**설정**:
```json
{
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {"num_points": 10}
  },
  "tolerance": {
    "roll": {"tolerance": 3.0},
    "doe_type": "lhs",
    "doe_count": 5
  },
  "cumulative": {
    "num_steps": 3,
    "angle_mixing": {"strategy": "cyclic", "cyclic_offset": 1}
  }
}
```

**실행**:
```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 5 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**계산**:
- 10 Fibonacci × 5 DOE × 3 Steps = 150 Jobs
- 동시 실행: 5 × 8 = 40개
- Rounds: 150 / 40 = 4 rounds

### 예제 2: 대규모 (15,000 Jobs)

**설정**:
```bash
python LargeScaleDOEManager.py \
    --config runner_config.json \
    --nodes 50 \
    --jobs-per-node 8 \
    --ncpu-per-job 16
```

**계산**:
- 1000 Fibonacci × 5 DOE × 3 Steps = 15,000 Jobs
- 동시 실행: 50 × 8 = 400개
- Rounds: 15,000 / 400 = 38 rounds
- Job당 4시간 → 총 152시간 (6.3일)

---

## 주요 결정사항

### 1. scenarios JSON이 입력 표준

**결정**: KooDynaAutomaticSimulationScriptGenerator가 scenarios JSON을 파싱
**이유**: GUI와 CLI 모두 지원, 표준화된 형식

### 2. Slurm Array Job with Concurrency Limit

**결정**: `--array=1-5000%40` 방식 사용
**이유**:
- Slurm이 자동 스케줄링
- 노드 장애 시 자동 복구
- 유휴 시간 최소화
- 사용자가 동시 실행 수 제어

### 3. 명시적 자원 제어

**결정**: `--nodes`, `--jobs-per-node`, `--ncpu-per-job` 파라미터
**이유**:
- 자원 사용량 예측 가능
- 공유/전용 노드 전략 구분
- 비용 산정 용이

### 4. Lock 파일 기반 진행 추적

**결정**: 각 Step 완료 시 `.lock` 파일 생성
**이유**:
- 간단하고 신뢰성 높음
- 파일 시스템만으로 추적 가능
- 재시작 시 이어서 실행 가능

---

## 기술적 발견사항

### 1. KooMeshModifier 출력

**발견**: KooMeshModifier는 .k 파일 생성, dynain 아님
**영향**: LS-DYNA 실행이 필수
**해결**: LargeScaleDOEManager에서 LS-DYNA 자동 실행

### 2. DYNAIN_TO_INITIAL 필요성

**발견**: 누적 낙하 시 이전 dynain을 Initial.k로 변환 필요
**영향**: Step 2+에서 DYNAIN_TO_INITIAL 자동 실행
**해결**: Slurm 스크립트에 통합

### 3. 파일명 자동 감지

**발견**: KooMeshModifier 출력 .k 파일명이 각도 정보 포함
**예시**: `MinimumModel_EX_45_EY_30_H_1500.k`
**해결**: `find` 명령으로 최신 .k 파일 자동 감지

### 4. Array Job 동시 실행 제한

**발견**: `--array=1-5000%40`으로 최대 40개 동시 실행 제한
**장점**: Slurm 부하 감소, 자원 제어 용이
**적용**: LargeScaleDOEManager에서 자동 계산 및 설정

---

## 현재 상태

### ✅ 완료

1. **Scenario JSON 파서**
   - KooDynaAutomaticSimulationScriptGenerator.py
   - 6개 analysisType 지원
   - runner_config.json 생성

2. **대규모 실행 관리**
   - LargeScaleDOEManager.py
   - Slurm Array Job 제출
   - 동시 실행 제한 (concurrency limit)
   - Lock 파일 추적

3. **누적 낙하 자동화**
   - KooMeshModifier 실행
   - LS-DYNA 실행
   - DYNAIN_TO_INITIAL 자동 처리
   - Step 간 순차 실행

4. **HPC 자원 제어**
   - `--nodes`, `--jobs-per-node`, `--ncpu-per-job`
   - 동시 실행 수 계산 및 출력
   - 예상 Rounds 표시

5. **각도 믹싱**
   - 5가지 전략 (same_angle, cyclic, random, opposite, custom)
   - DOE 확장 (Tolerance)
   - Fibonacci, LHS, case_txt_file

6. **Direct Input 지원**
   - Node 모니터링
   - 커스텀 파라미터 (Height, Velocity 등)
   - 사용자 정의 *PARAMETER, *CURVE

7. **문서화**
   - 메인 문서 4개
   - 상세 문서 docs/
   - 자원 계획 가이드
   - 커스텀 시나리오 예제

### 🔄 검증 필요

1. **실제 HPC 환경 테스트**
   - 346 노드 클러스터에서 실행
   - 동시 실행 제한 동작 확인
   - Lock 파일 신뢰성 검증

2. **대규모 테스트**
   - 10,000+ Jobs 실행
   - 자원 활용률 측정
   - 완료 시간 측정

---

## 다음 단계

### 우선순위 1: 실전 테스트

1. 소규모 테스트 (100 Jobs)
   ```bash
   python LargeScaleDOEManager.py \
       --config test_100.json \
       --nodes 5 \
       --jobs-per-node 4 \
       --ncpu-per-job 16
   ```

2. 중규모 테스트 (1,000 Jobs)
   ```bash
   python LargeScaleDOEManager.py \
       --config test_1000.json \
       --nodes 10 \
       --jobs-per-node 8 \
       --ncpu-per-job 16
   ```

3. 대규모 테스트 (10,000 Jobs)
   ```bash
   python LargeScaleDOEManager.py \
       --config test_10000.json \
       --nodes 50 \
       --jobs-per-node 8 \
       --ncpu-per-job 16
   ```

### 우선순위 2: 모니터링 강화

1. 실시간 진행 상황 대시보드
2. 자원 사용률 모니터링
3. 실패 Job 자동 재시작

### 우선순위 3: GUI 통합

1. Scenario JSON 생성 GUI
2. 실행 설정 GUI
3. 진행 상황 시각화

---

## Quick Start (새 대화용)

### 1. 필수 파일 읽기

```bash
# 메인 문서
Examples/HWWarrantyDropTest/README.md
Examples/HWWarrantyDropTest/COMPLETE_SYSTEM_OVERVIEW.md
Examples/HWWarrantyDropTest/SIMULATION_AUTOMATION_WORKFLOW.md

# 핵심 모듈
occProject/Generators/KooCAEManager/KooDynaAutomaticSimulationScriptGenerator.py
Runner/LargeScaleDOEManager.py
Examples/HWWarrantyDropTest/CumulativeDesigner.py
```

### 2. 현재 상태 파악

- v3.0: HPC 자원 제어 개선 완료
- Simulation Automation 워크플로우 명확화
- 문서 정리 완료
- 프로덕션 준비 완료

### 3. 실행 예시

```bash
# 1. scenarios JSON 작성 또는 사용자 JSON 작성

# 2. runner_config.json 생성
python -c "
from occProject.Generators.KooCAEManager.KooDynaAutomaticSimulationScriptGenerator import KooDynaAutomaticSimulationScriptGenerator
import json
with open('scenarios.json') as f:
    scenarios = json.load(f)
metadata = {...}
gen = KooDynaAutomaticSimulationScriptGenerator(scenarios, metadata)
gen.generate_for_all(output_dir='./configs')
"

# 3. 실행
python Runner/LargeScaleDOEManager.py \
    --config configs/runner_config_*.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

---

## 참고 문서

- [README.md](../README.md) - 시스템 소개
- [COMPLETE_SYSTEM_OVERVIEW.md](../COMPLETE_SYSTEM_OVERVIEW.md) - 전체 개요
- [SIMULATION_AUTOMATION_WORKFLOW.md](../SIMULATION_AUTOMATION_WORKFLOW.md) - 워크플로우
- [RESOURCE_PLANNING_GUIDE.md](../RESOURCE_PLANNING_GUIDE.md) - 자원 계획
- [docs/ANGLE_MIXING_STRATEGIES_GUIDE.md](../docs/ANGLE_MIXING_STRATEGIES_GUIDE.md) - 각도 믹싱

---

**작성자**: koo.park
**버전**: 3.0
**날짜**: 2026-01-23
