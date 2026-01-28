# Cumulative Drop Automation - Context v2.1

**Date**: 2026-01-22
**Version**: 2.1
**Status**: DROP MODE V2 설계 완료, 워크플로 검증 완료, 구현 대기
**Project**: 누적 낙하 자동화 (Cumulative Drop Automation)

---

## 📋 Quick Start (새 대화에서 시작할 때)

### 필수 읽기 파일 (순서대로)

1. **[PROGRESS_SUMMARY.md](../PROGRESS_SUMMARY.md)** - 전체 진행 상황 요약
2. **[MODE_CONDITION_Reference.md](../MODE_CONDITION_Reference.md)** - 모드/컨디션 종류 정의
3. **[DROP_MODE_V2_PLAN.md](../DROP_MODE_V2_PLAN.md)** - DROP MODE V2 상세 설계 (⭐ 최신)
4. **[CumulativeDrop_Automation_Plan.md](../CumulativeDrop_Automation_Plan.md)** - 원래 계획서 (Phase 1-4)

### 핵심 코드 파일

- **[KooDynaAutomaticSimulationScriptGenerator.py](../../../occProject/Generators/KooCAEManager/KooDynaAutomaticSimulationScriptGenerator.py)** - 시뮬레이션 JSON 생성기 (Designer)
- **[KooDynaAdvancedModification.py](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py)** - DROP_ATTITUDE, DYNAIN_TO_INITIAL 구현 (⭐ 워크플로 확인됨)
- **[CumulativeScenarioRunner.py](../../../Runner/CumulativeScenarioRunner.py)** - 시뮬레이션 실행기 (Executor) (미구현)

### 표준 Case txt 파일 (11개)

- **[FullAngleDrop/](../FullAngleDrop/)** 디렉토리 참조
  - `26case_6F12E8C_cuboid.txt` - Cuboid 26 케이스
  - `fibonacci_10deg_413cases.txt` - Fibonacci 10° 간격
  - `pitching_10deg_19cases.txt` - Pitching 스윕
  - `rolling_10deg_36cases.txt` - Rolling 스윕
  - 등 (총 11개 파일)

---

## 🎯 프로젝트 개요

### 목적

HW Warranty 낙하 테스트를 위한 **대규모 누적 시뮬레이션 자동화 시스템** 구축

### 핵심 기능

1. **단일 낙하 자동화**: 26개 F/E/C 조건
2. **누적 낙하 자동화**: 동일/다른 조건으로 N회 반복
3. **혼합 모드**: 열응력 + 낙하 조합
4. **Fibonacci 각도**: 수백~수만 개 각도 소스 지원
5. **Tolerance/DOE**: 각도 산포 분석 (±1°~±5°)
6. **표준 Case txt 파일**: 11개 표준 파일 직접 활용
7. **자동 템플릿 선택**: Dynamic Relaxation, DYNAIN_TO_INITIAL 자동 처리

---

## 🏗️ 시스템 아키텍처

### 2-Stage 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Designer (SIMULATION_AUTOMATION)                       │
│ ─────────────────────────────────────────────────────────────── │
│ JSON 설정 → runner_config.json 생성                             │
│ - 각도 소스 확장 (Cuboid, Fibonacci, Pitching, Rolling)         │
│ - Tolerance/DOE 확장                                             │
│ - 다중 시나리오 확장                                              │
│ - 템플릿 자동 선택                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Executor (CumulativeScenarioRunner)                    │
│ ─────────────────────────────────────────────────────────────── │
│ runner_config.json → 시뮬레이션 실행                             │
│ - Step 1 → Step 2 → ... → Step N 순차 실행                      │
│ - 각 Step마다 KooMeshModifier 호출                               │
│ - DROP_ATTITUDE → DYNAIN_TO_INITIAL → DROP_ATTITUDE (자동)       │
└─────────────────────────────────────────────────────────────────┘
```

### 주요 컴포넌트

1. **JSON 설정 파일** (사용자 작성)
   - 시나리오 정의 (조건, 스텝, 파라미터)
   - 각도 소스 지정 (Cuboid, Fibonacci, Case txt 등)
   - Tolerance/DOE 설정

2. **Designer** (KooDynaAutomaticSimulationScriptGenerator.py)
   - JSON → runner_config.json 생성
   - 각도 소스 파싱
   - Tolerance 적용 → DOE 확장
   - 다중 시나리오 확장

3. **Executor** (CumulativeScenarioRunner.py - 미구현)
   - runner_config.json 읽기
   - 시뮬레이션 순차 실행
   - 템플릿 자동 선택
   - KooMeshModifier 호출

4. **KooMeshModifier** (기존 코드)
   - DROP_ATTITUDE: 낙하 시뮬레이션 설정
   - DYNAIN_TO_INITIAL: dynain → initial 변환
   - THERMAL_CYCLE: 열응력 시뮬레이션

---

## 🔑 주요 기술적 발견사항 (⭐ 중요!)

### DROP_ATTITUDE 자동 워크플로

**KooDynaAdvancedModification.py** 코드를 직접 조사한 결과:

#### ✅ 이미 완벽하게 구현되어 있음:

1. **Dynamic Relaxation 자동 추가** ([Line 2005](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L2005))
   ```python
   partSet = self.dynaImporter.partManager.CreatePartSet(name="Dynamic Relaxation Set")
   self.dynaImporter.additionalManager.CreateInterfaceSpringbackLSDyna(partSet.psid)
   # → *CONTROL_DYNAMIC_RELAXATION 자동 포함
   ```

2. **dynaintoinitial.txt 자동 생성** ([Line 2191-2211](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L2191))
   ```python
   with open(dynaintoinitialPath, "w") as f:
       f.write("*RemoveDynamicRelaxation,True\n")  # DR 제거
       f.write("*MovetoOriginAutomatic,True\n")    # 원점 이동
       f.write("*RemovePartbyID," + str(part.id) + "\n")  # 바닥면 제거
       f.write("*RemoveContactbyID," + str(contact.cid) + "\n")  # 접촉 제거
   ```

3. **DYNAIN_TO_INITIAL 자동 처리** ([Line 4481-4482](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py#L4481))
   - dynaintoinitial.txt 읽어서 자동 처리
   - DR 제거, 파트 제거, 접촉 제거 모두 자동
   - 다음 DROP_ATTITUDE에서 DR 다시 자동 추가

#### 실제 누적 낙하 워크플로:

```
Step 1 (DROP_ATTITUDE)
  → *CONTROL_DYNAMIC_RELAXATION 자동 추가
  → LS-DYNA 실행 (DR + 낙하)
  → dynain 생성
  → dynaintoinitial.txt 자동 생성 (Step 2용)

DYNAIN_TO_INITIAL (자동)
  → dynain 읽기
  → DR 제거 (RemoveDynamicRelaxation,True)
  → 바닥면/접촉 제거
  → 원점 이동
  → Initial 상태 생성

Step 2 (DROP_ATTITUDE)
  → *CONTROL_DYNAMIC_RELAXATION 자동 재추가
  → LS-DYNA 실행 (DR + 새 각도 낙하)
  → dynain 생성
  → dynaintoinitial.txt 자동 생성 (Step 3용)

... (반복)
```

#### ❌ 불필요한 것들:

- ~~별도 Dynamic Relaxation 템플릿~~ → 이미 자동
- ~~DYNAIN_TO_INITIAL 수동 설정~~ → 이미 자동
- ~~6개 템플릿 JSON 파일~~ → 코드에 하드코딩으로 충분

---

## 📊 시뮬레이션 모드 및 조건

### 모드 종류 (6가지)

| 모드 ID | 이름 | 설명 | 구현 상태 |
|---------|------|------|----------|
| **DROP** | 낙하 | 자유낙하 시뮬레이션 | ✅ 완료 (V1: F/E/C, V2: Fibonacci 설계) |
| **THERM** | 열응력 | 열 사이클 시뮬레이션 | 🔄 설계됨 (미구현) |
| **STAT** | 정적 하중 | 정적 압력 시뮬레이션 | 🔄 설계됨 (미구현) |
| **VIB** | 진동 | 랜덤 진동 시뮬레이션 | 🔄 설계됨 (미구현) |
| **DWI** | 수침 | 방수 압력 시뮬레이션 | 🔄 설계됨 (미구현) |
| **COMB** | 조합 | 복합 모드 조합 | 🔄 설계됨 (미구현) |

### DROP 모드 조건 (V2)

#### 각도 소스 타입 (5가지)

1. **cuboid_geometry**: F1-F6 (Face), E1-E12 (Edge), C1-C8 (Corner) - 26개
2. **fibonacci_lattice**: 구면 균등 분포 (26~41,253 케이스)
3. **pitching_sweep**: Pitch -90~90° 스윕 (Roll 고정)
4. **rolling_sweep**: Roll -180~170° 스윕 (Pitch 고정)
5. **case_txt_file**: 표준 Case txt 파일 (11개 파일 지원)

#### 각도 믹싱 전략 (5가지)

누적 시뮬레이션에서 각 스텝의 각도 조합 방식:

| 전략 | 설명 | 예시 (2회 누적) |
|------|------|----------------|
| **same_angle** | 동일 각도 반복 | P001 → P001 |
| **cyclic** | 순환 (인덱스 +offset) | P001 → P002 → P003 |
| **random** | 랜덤 샘플링 | P001 → P187 (random) |
| **opposite** | 대칭 각도 | P001 → P001_OPPOSITE |
| **custom_mapping** | 사용자 정의 | Fib10deg_P001 → Fib20deg_P001 |

#### F1-F6, E1-E12, C1-C8 정의

**좌표계**: LS-DYNA 글로벌 (X=오른쪽, Y=위, Z=전면)
**Euler 각도**: Roll → Pitch → Yaw (Z-Y-X 내재 회전)

**Face 조건 (6개)**:
- F1 (Back): Roll=0°, Pitch=0°, Yaw=0°
- F2 (Front): Roll=180°, Pitch=0°, Yaw=0°
- F3 (Right): Roll=0°, Pitch=-90°, Yaw=0°
- F4 (Left): Roll=0°, Pitch=90°, Yaw=0°
- F5 (Top): Roll=90°, Pitch=0°, Yaw=0°
- F6 (Bottom): Roll=-90°, Pitch=0°, Yaw=0°

**Edge 조건 (12개)**: 45° 조합 (예: E1 Back-Right: Roll=0°, Pitch=-45°)
**Corner 조건 (8개)**: ±45° 조합 (예: C1 Back-Right-Top: Roll=45°, Pitch=-45°)

자세한 정의는 [DROP_MODE_V2_PLAN.md](../DROP_MODE_V2_PLAN.md) 참조

---

## 🗂️ 표준 Case txt 파일 시스템

### 파일 목록 (11개)

| 파일명 | 케이스 수 | 설명 |
|--------|----------|------|
| `26case_6F12E8C_cuboid.txt` | 26 | Cuboid 기하 (6F+12E+8C) |
| `fibonacci_01deg_41253cases.txt` | 41,253 | Fibonacci 1° 간격 |
| `fibonacci_02deg_10313cases.txt` | 10,313 | Fibonacci 2° 간격 |
| `fibonacci_04deg_2578cases.txt` | 2,578 | Fibonacci 4° 간격 |
| `fibonacci_05deg_1650cases.txt` | 1,650 | Fibonacci 5° 간격 |
| `fibonacci_06deg_1146cases.txt` | 1,146 | Fibonacci 6° 간격 |
| `fibonacci_10deg_413cases.txt` | 413 | Fibonacci 10° 간격 |
| `fibonacci_20deg_103cases.txt` | 103 | Fibonacci 20° 간격 |
| `fibonacci_40deg_26cases.txt` | 26 | Fibonacci 40° 간격 |
| `pitching_10deg_19cases.txt` | 19 | Pitch -90~90° (Roll=0) |
| `rolling_10deg_36cases.txt` | 36 | Roll -180~170° (Pitch=0) |

### 파일 형식

```
*Inputfile
MinimumModel.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ Case names (comma-separated)
EulerRolling,0,180,0,0,90,-90,...
EulerPitching,0,0,-90,90,0,0,...
EulerYawing,0,0,0,0,0,0,...
Height,1500,1500,1500,...
...
**EndDropAttitude
*End
```

### 활용 방법

JSON 설정에서 직접 참조:

```json
{
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt": {
      "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt"
    }
  }
}
```

결과: 413개 각도 자동 파싱 및 시뮬레이션 생성

---

## 🛠️ 템플릿 시스템 (자동 선택)

### 템플릿 종류 (5개)

| 템플릿 ID | 용도 | 실제 동작 |
|----------|------|----------|
| `DROP_FIRST` | 첫 번째 낙하 | DROP_ATTITUDE 실행 (DR 자동 포함) |
| `DROP_CUMULATIVE` | 누적 낙하 | DYNAIN_TO_INITIAL → DROP_ATTITUDE (DR 자동 재추가) |
| `THERMAL_FIRST` | 첫 번째 열해석 | THERMAL_CYCLE 실행 |
| `THERMAL_CUMULATIVE` | 누적 열해석 | DYNAIN_TO_INITIAL → THERMAL_CYCLE |
| `THERMAL_TO_DROP` | 열→낙하 전환 | DYNAIN_TO_INITIAL(열) → DROP_ATTITUDE |

### 자동 선택 로직

```python
def select_template_for_step(step: int, mode: str, prev_mode: Optional[str] = None) -> str:
    if step == 1:
        return "DROP_FIRST" if mode == "DROP" else "THERMAL_FIRST"
    else:
        if mode == "DROP":
            return "THERMAL_TO_DROP" if prev_mode == "THERM" else "DROP_CUMULATIVE"
        elif mode == "THERM":
            return "THERMAL_CUMULATIVE"
```

**사용자는 JSON에 템플릿을 지정할 필요 없음** - 시스템이 자동으로 선택

### 템플릿 선택 예시

| 시나리오 | Step 1 | Step 2 | Step 3 |
|---------|--------|--------|--------|
| 3회 연속 낙하 | DROP_FIRST | DROP_CUMULATIVE | DROP_CUMULATIVE |
| 열→낙하 | THERMAL_FIRST | THERMAL_TO_DROP | DROP_CUMULATIVE |
| 열→열→낙하 | THERMAL_FIRST | THERMAL_CUMULATIVE | THERMAL_TO_DROP |

---

## 📝 현재 구현 상태

### ✅ 완료된 것 (Phase 1-4)

1. **JSON 스키마 설계**
   - `singleDrop`, `mixedCumulative` 타입 정의
   - 기본 각도 소스 (F/E/C 26개)

2. **문서화**
   - [CumulativeDrop_Automation_Plan.md](../CumulativeDrop_Automation_Plan.md)
   - [PROGRESS_SUMMARY.md](../PROGRESS_SUMMARY.md)
   - [MODE_CONDITION_Reference.md](../MODE_CONDITION_Reference.md)

3. **DROP MODE V2 설계**
   - [DROP_MODE_V2_PLAN.md](../DROP_MODE_V2_PLAN.md) 완성
   - Fibonacci, Pitching, Rolling 각도 소스 설계
   - Tolerance/DOE 시스템 설계
   - 표준 Case txt 파일 시스템 설계
   - 템플릿 자동 선택 로직 설계
   - 각도 믹싱 전략 설계

4. **워크플로 검증**
   - DROP_ATTITUDE 자동 워크플로 확인
   - Dynamic Relaxation 자동 추가 확인
   - DYNAIN_TO_INITIAL 자동 생성 확인
   - 불필요한 템플릿 제거

### 🔄 진행 중

없음 (설계 완료, 구현 대기)

### ❌ 미구현

#### Priority 1: 표준 Case txt 파일 시스템 (HIGH) ⭐
- [ ] `CaseTxtConfig` 데이터 클래스 추가
- [ ] `parse_case_txt_file()` 구현
- [ ] Case 이름 자동 추출 ($ 주석 라인 파싱)
- [ ] 특정 인덱스 선택 기능 구현
- [ ] Case txt + Tolerance 조합 구현

#### Priority 2: 템플릿 자동 선택 시스템 (HIGH) ⭐
- [ ] `select_template_for_step()` 자동 선택 함수 구현
- [ ] 5개 템플릿 정의
- [ ] 자동 템플릿 선택 로직

#### Priority 3: 각도 소스 확장 (HIGH)
- [ ] `AngleSourceConfig` 데이터 클래스 추가
- [ ] `parse_angle_source()` 메인 함수 구현
- [ ] `parse_cuboid_geometry()` 구현 (F/E/C 매핑)
- [ ] `parse_fibonacci_lattice()` 구현 (txt 파일 파싱 활용)
- [ ] `parse_pitching_sweep()`, `parse_rolling_sweep()` 구현
- [ ] `parse_custom_file()` 구현

#### Priority 4: Tolerance/DOE 시스템 (MEDIUM)
- [ ] `ToleranceConfig` 확장
- [ ] `apply_tolerance_doe()` 구현
- [ ] LHS, Grid, Random DOE 생성기 구현

#### Priority 5: 다중 시나리오 (MEDIUM)
- [ ] `MultiScenarioCumulativeConfig` 데이터 클래스 추가
- [ ] `parse_multi_scenario_cumulative()` 구현
- [ ] `generate_multi_scenario_runner_config()` 구현
- [ ] `MultiScenarioCumulativeRunner` 클래스 구현

#### Priority 6: 각도 믹싱 전략 (MEDIUM)
- [ ] `CumulativeAngleConfig` 데이터 클래스 추가
- [ ] `generate_cumulative_angle_sequences()` 구현
- [ ] 5가지 전략 구현 (same_angle, cyclic, random, opposite, custom_mapping)

#### Priority 7: Executor 구현 (LOW)
- [ ] `CumulativeScenarioRunner` 클래스 구현
- [ ] runner_config.json 파싱
- [ ] 시뮬레이션 순차 실행 로직

---

## 🚀 다음 단계 (새 대화에서 이어가기)

### 즉시 시작 가능한 작업

1. **Phase 1 구현: Case txt 파일 파서**
   ```python
   # 구현할 파일: Runner/CaseTxtParser.py
   def parse_case_txt_file(file_path: str) -> List[Tuple[str, float, float, float]]:
       """
       표준 Case txt 파일 파싱

       Returns:
           List of (case_name, roll, pitch, yaw)
       """
       pass
   ```

2. **Phase 2 구현: 각도 소스 파서**
   ```python
   # 구현할 파일: Runner/AngleSourceParser.py
   def parse_angle_source(angle_config: AngleSourceConfig) -> List[Tuple[str, float, float, float]]:
       """
       각도 소스 설정 → (name, roll, pitch, yaw) 리스트 반환
       """
       pass
   ```

3. **Phase 3 구현: 템플릿 자동 선택**
   ```python
   # 구현할 파일: Runner/TemplateManager.py
   def select_template_for_step(step: int, mode: str, prev_mode: Optional[str] = None) -> str:
       """
       스텝 번호와 모드에 따라 자동으로 템플릿 선택
       """
       pass
   ```

### 구현 시 참고사항

- **기존 코드 활용**: KooDynaAdvancedModification.py의 DROP_ATTITUDE, DYNAIN_TO_INITIAL 로직은 이미 완벽함
- **표준 파일 활용**: 11개 Case txt 파일 형식 참조
- **설계 문서 참조**: DROP_MODE_V2_PLAN.md의 상세 설계 활용
- **워크플로 이해**: Dynamic Relaxation, DYNAIN_TO_INITIAL은 모두 자동 처리됨

---

## 📚 주요 참고 문서

### 프로젝트 문서
- [CumulativeDrop_Automation_Plan.md](../CumulativeDrop_Automation_Plan.md) - 원래 계획서
- [PROGRESS_SUMMARY.md](../PROGRESS_SUMMARY.md) - 진행 상황 요약
- [MODE_CONDITION_Reference.md](../MODE_CONDITION_Reference.md) - 모드/컨디션 정의
- [DROP_MODE_V2_PLAN.md](../DROP_MODE_V2_PLAN.md) - DROP MODE V2 상세 설계 (⭐ 최신)

### 코드 파일
- [KooDynaAutomaticSimulationScriptGenerator.py](../../../occProject/Generators/KooCAEManager/KooDynaAutomaticSimulationScriptGenerator.py)
- [KooDynaAdvancedModification.py](../../../occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py) (⭐ 워크플로 검증됨)

### 표준 파일
- [FullAngleDrop/](../FullAngleDrop/) - 11개 표준 Case txt 파일

---

## 💡 중요한 설계 결정사항

### 1. 템플릿 수 감소 (6개 → 5개)
- **이유**: Dynamic Relaxation과 DYNAIN_TO_INITIAL이 이미 자동 처리됨
- **제거된 템플릿**: `CUMULATIVE_DROP_WITH_DYNAIN_RELAX` (불필요)
- **결과**: 간소화된 시스템, 사용자 혼란 감소

### 2. 템플릿 자동 선택
- **이유**: 사용자가 템플릿을 수동으로 지정할 필요 없음
- **방식**: 스텝 번호 + 현재/이전 모드 기반 자동 선택
- **결과**: JSON 설정 간소화, 오류 감소

### 3. 표준 Case txt 파일 활용
- **이유**: 이미 잘 정의된 11개 표준 파일 존재
- **장점**: JSON 설정 간소화, 각도 수동 입력 불필요
- **결과**: 사용자 편의성 대폭 향상

### 4. 각도 믹싱 전략 추가
- **이유**: Fibonacci 누적 낙하 시 각도 조합 방식 필요
- **전략**: same_angle, cyclic, random, opposite, custom_mapping
- **결과**: 유연한 누적 시뮬레이션 설계 가능

---

## 🔍 기술적 세부사항

### Fibonacci Lattice 공식

```python
# Golden angle
phi = (1 + sqrt(5)) / 2
golden_angle = 2 * pi * (1 - 1/phi)  # ≈ 137.508°

# Fibonacci 포인트 i (총 N개)
theta_i = acos(1 - 2*i/(N-1))  # Polar angle [0, π]
phi_i = i * golden_angle % (2*pi)  # Azimuthal angle [0, 2π]

# Euler 각도 변환 (Drop 방향 = -Z)
roll = degrees(phi_i) - 180
pitch = degrees(theta_i) - 90
yaw = 0
```

### Tolerance DOE 생성

**Latin Hypercube Sampling (LHS)** 권장:

```python
def generate_lhs_samples(base_angles, tolerance_config):
    """
    LHS로 DOE 샘플 생성

    Parameters:
        base_angles: [(name, roll, pitch, yaw), ...]
        tolerance_config: {
            "doe_count": 10,
            "roll": {"min": -2, "max": 2},
            "pitch": {"min": -2, "max": 2},
            "yaw": {"min": -1, "max": 1}
        }

    Returns:
        [(name, roll, pitch, yaw, doe_index), ...]
    """
    pass
```

### Alias 시스템

```
{Project}_CUM{Steps:03d}_DOE{Index:03d}_S{Step:03d}_{Mode}_{Condition}

예시:
HWWarranty_CUM003_DOE005_S001_DROP_F1
HWWarranty_CUM003_DOE005_S002_DROP_E1
HWWarranty_CUM003_DOE005_S003_DROP_C1
```

---

## 📞 문의 및 이슈

**GitHub**: https://github.com/anthropics/claude-code/issues
**작성자**: Claude Code (Sonnet 4.5)
**날짜**: 2026-01-22

---

**이 문서를 새 대화 시작 시 읽어주세요!**
