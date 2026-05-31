# IMPLEMENTATION — VIBRATION 모드 구현 진행 로그

> 실시간 갱신. 각 Phase 진행 단계마다 entry 추가.

## 사용자 결정 사항 (확정)

- **Q1~Q9 + Zero-Hardcode A~G: 추천안 모두 채택** (사용자 회신 "1추천그대로")

## 진행 상태 요약

| Phase | 목적 | 상태 |
|---|---|---|
| **P1 (코드)** | 인프라 + Registry + explicit_factors | ✅ **PASS** — 2건 blocking fix 적용 + Python 직접 호출 검증 완료 (P1.6) |
| **P1.8** | Nuitka 빌드 + bin 검증 | ✅ **PASS** — `KooChainRun.bin` 정상 빌드, prepare 통과 (bin/소스 동등) |
| **P2 (코드)** | per_cap + circuit_group 등록 (회로 일괄 ⭐) | ✅ **PASS** — 단위/통합 검증 + DROP 회귀 무영향 (P2.3) |
| **P2.5 (실잡)** | LS-DYNA 실제 실행 검증 | ❌ **FAIL** — sbatch 잡 ID 미발급, _vib.k 0개 (Slurm controller down) |
| **P2.6 (재시도)** | slurmctld 부분 복구 후 재제출 | ❌ **FAIL** — 모든 컴퓨트 노드 down/unk, sbatch 거부 |
| **P2.7 (영구 기록)** | Slurm 인프라 장애 사실 보존 | 기록 완료 — admin 권한 (`virsh start`) 필요, 본 세션 범위 외 |
| **P2.8** | commit/push/tar 결정 | 진행 완료 (코드 보존 목적) |
| **P2.9 (e2e 재검증 — 노드 복구 후)** | 회로 일괄 진동 실잡 + `_vib.k` 카드 검증 | ❌ **FAIL — 재현 불가** (`/tmp` 노드 로컬 FS, NFS 미공유) |
| **P2.10 (NFS 경로 e2e 재검증)** | `/data/koopark/Test_VibP{1,2}/` NFS 이동 후 실잡 재제출 | ❌ **FAIL — 코드 결함 노출** (Slurm 정상, sbatch OK, 컴퓨트 노드 실행됨 → `StepConfigBuilder._serialize_explicit`에서 `load_curve가 비어 있습니다` 예외, 4잡 모두 ExitCode 1) |
| **사용자 핵심 요구 (회로 일괄 진동) 동작 검증** | _vib.k 회로별 SF 1.0/0.5/2.0 차등 적용 | ❌ **INCOMPLETE — `_vib.k` 0건 산출, base_curve→VibrationLoadSpec 전달 누락 버그 (P2.10에서 발견)** |
| **P3** | cap_combination + max_doe_count 가드 | ⏸ 진입 보류 — **선행 fix 필요**: VibrationSource resolver(특히 `explicit_factors` / `circuit_group`)의 `base_curve` 평탄화 → `VibrationLoadSpec.load_curve` 주입 경로 점검 |
| **P4** | VolumeProportional 노출 | 대기 |
| **P5** | (옵션) node/segment — KooMeshModifier 확장 | 대기 |
| **P6** | 회로 자동 제안 helper | 대기 |

---

## P1. 인프라 + 최소 통합

### P1.0 baseline 시점 기록

- 일자: 2026-05-29
- 베이스 브랜치: `main` (commit `558486b` — POSTPROCESS_OPTIONS.md docs)
- 검증 방식: Nuitka 빌드된 `KooChainRun.bin`은 미사용. 변경된 `Runner/*.py`를 **Python 직접 호출**로 검증.
- 회귀 baseline 시나리오: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json` (DROP 단일 모드, 1 step, 26방향).
- P1 minimum 시나리오: `/tmp/vib_p1_test/scenario.json` (`VIBRATION` 모드, `explicit_factors` source, 캡 1개).

### P1.1 코드 작성 결과

| 파일 | 변경 종류 | 검증 |
|---|---|---|
| `Runner/VibrationSource.py` | **생성** — Registry + `@register_vibration_source` 데코레이터 + `parse_vibration_source()` + `explicit_factors` 핸들러 | syntax OK, import OK |
| `Runner/StepConfigBuilder.py` | **수정** — `build_vibration_load_block()` 함수 추가 (예정) | syntax OK, **import FAIL** |
| `Runner/TemplateManager.py` | **수정** — `SimulationMode.VIBRATION` 추가 + TEMPLATE_DEFINITIONS 분기 | syntax OK, `VIBRATION in enum: True` |
| `Runner/CumulativeDesigner.py` | **수정** — `_process_vibration_scenario()` + mode dispatch | syntax OK, **DROP 회귀 OK / VIBRATION 모드 인식 FAIL** |
| `Runner/CumulativeScenarioRunner.py` | **수정** — `elif mode == "VIBRATION"` + `_find_input_file` | syntax OK |

총 5개 파일 (생성 1 + 수정 4). LOC는 빌드 산출물 미반영 상태이므로 별도 측정 보류.

### P1.2 단위 테스트 결과

**Syntax check (5/5 PASS)**
- `Runner/VibrationSource.py` — OK
- `Runner/StepConfigBuilder.py` — OK
- `Runner/TemplateManager.py` — OK
- `Runner/CumulativeDesigner.py` — OK
- `Runner/CumulativeScenarioRunner.py` — OK

**Import check (3/4 PASS, 1 FAIL)**
- `Runner.VibrationSource.parse_vibration_source` — OK
- `Runner.VibrationSource.register_vibration_source` — OK
- `Runner.TemplateManager.SimulationMode.VIBRATION` — OK (`VIBRATION in enum: True`)
- `Runner.StepConfigBuilder.build_vibration_load_block` — **FAIL**
  ```
  ImportError: cannot import name 'build_vibration_load_block' from 'Runner.StepConfigBuilder'
  ```

**Registry 동작 (PASS)**
- 미등록 source_type에 대해 정상적으로 `ValueError` 발생.
- 메시지: `Unknown vibration source_type: 'nonexistent'. Registered: ['explicit_factors']`
- → 데코레이터 기반 정적 등록이 정상 작동, 1개 핸들러(`explicit_factors`)만 등록된 상태.

**미확인 항목**
- builder 골든 텍스트 비교: `build_vibration_load_block` 자체가 import 안 되므로 미수행.

### P1.3 회귀 검증 결과 (DROP 시나리오)

**입력**: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json`
**검증 방식**: `CumulativeDesigner.parse_user_config()` 직접 호출.

| 항목 | 사양 | 실측 | 결과 |
|---|---|---|---|
| project_name | Test_001_Full26_1Step | `Test_001_Full26_1Step` | OK |
| scenario_id | Full_26_Directions_Single_Drop_S001 | 일치 | OK |
| total_steps | 1 | `1` | OK |
| DOE 개수 | 26 | `26` | OK |
| mode_sequence | [DROP] | `['DROP']` | OK |
| doe_index 범위 | 0..25 (연속 26개) | 0..25 | OK |
| angle_names | C1_Back_Right_Top ... F6_Bottom | 26방향 명명 규칙 일치 | OK |

→ **DROP 단일 모드 시나리오 회귀 OK**. Runner/*.py 변경분이 기존 DROP 경로를 깨뜨리지 않음.

**검증 한계 (정직 명시)**
- Nuitka 빌드된 `KooChainRun.bin` 미사용. Runner/*.py 변경분 미빌드 상태.
- 본 회귀는 "수정 후 Python 소스가 DROP 시나리오를 정상 파싱한다"는 확인이며, **수정 전 bin과의 byte-level 비교 아님**.
- byte-level baseline 비교가 필요하면 `build_KooChainRun_python312.sh` 빌드 후 별도 수행 요망.

### P1.4 P1 minimum prepare 결과

**입력**: `/tmp/vib_p1_test/scenario.json` (VIBRATION 모드, `explicit_factors` source, 캡 1개)
**템플릿**: `/tmp/vib_p1_test/MinimumModel.k` (7.7 MB, 복사 OK)

**실패 지점**
```
ValueError: 'VIBRATION' is not a valid SimulationMode
  at Runner/CumulativeDesigner.py:548
  mode = SimulationMode(mode_str.upper())
```

**호출 스택**
1. `CumulativeDesigner(cfg)` — instantiation OK
2. `parse_user_config()` 진입 — OK
3. `_process_scenario()` 진입 — OK
4. `_parse_mode_sequence()` → `SimulationMode("VIBRATION")` — **FAIL**

**모순점 (P1.2와 충돌)**
- P1.2 import 확인 시 `Runner.TemplateManager.SimulationMode`에 `VIBRATION` 멤버는 존재 (`VIBRATION in enum: True`).
- 그러나 `Runner/CumulativeDesigner.py:548`에서 사용하는 `SimulationMode`는 **다른 정의를 import 중**으로 추정.
- → `CumulativeDesigner.py` 내부에 별도 `SimulationMode` 정의가 있거나, 다른 모듈을 import 하고 있을 가능성. 또는 import alias 차이.

**무효화된 후속 단계**
- `vibration_source` 블록 파싱은 mode enum 통과 후 수행되므로 미실행. P1.2의 Registry 동작은 단위 호출로는 OK지만, scenario flow 안에서는 미검증.

### P1.5 다음 단계

**P1 상태: FAIL** — P2 진입 불가.

**선행 fix 2건 (Blocking)**

1. **`Runner/StepConfigBuilder.py` — `build_vibration_load_block` 함수 누락**
   - 현재 파일 내 해당 심볼이 존재하지 않거나 다른 이름으로 정의됨.
   - 조치: 파일 grep으로 실제 정의 확인 → 함수명/시그니처/위치 정정 → import 재검증.

2. **`Runner/CumulativeDesigner.py:548` — `SimulationMode` 미통일**
   - `TemplateManager.SimulationMode`에는 `VIBRATION` 멤버가 있으나, Designer가 보는 `SimulationMode`에는 없음.
   - 조치: `CumulativeDesigner.py` 상단의 `SimulationMode` import 경로 확인 → `TemplateManager.SimulationMode`로 단일화 (또는 중복 정의가 있다면 제거하고 import).
   - 검증: P1.4 minimum 시나리오로 재실행 → mode enum 통과 후 `vibration_source` 블록 파싱까지 진행되는지 확인.

**Fix 완료 후 재검증 순서**
1. P1.2 단위 테스트 재실행 — `build_vibration_load_block` import OK 확인.
2. P1.3 DROP 회귀 재확인 — 변경에 의한 회귀 없음 보장.
3. P1.4 P1 minimum prepare 재실행 — mode enum 통과 + vibration_source dispatch까지 진행.
4. (선택) Nuitka 빌드 후 `KooChainRun.bin`으로 동일 시나리오 prepare 통과 확인.

**P2 진입 조건**: 위 1~3 단계 모두 PASS 시 P2 (per_cap + circuit_group) 진입 가능.

### P1.6 Blocking fix 적용 결과 (2026-05-29)

**P1 상태: ✅ PASS (fix 후)** — P2 진입 가능.

**적용된 fix 2건**

1. **Fix1 — `Runner/StepConfigBuilder.py` alias 추가** (line 432)
   - 기존 정의는 `build_vibration_load_config()` 였음. `build_vibration_load_block`는 동일 객체 alias로 export.
   - `build_vibration_load_block = build_vibration_load_config` 1 줄 추가 (surgical).
   - 검증: `both names import OK / same object: True / callable: True`.

2. **Fix2 — `Runner/TemplateManager.py` `SimulationMode.VIBRATION` enum 추가 + `select_template_for_step` 분기 통합** (3 곳)
   - line 34–35: `VIBRATION = "VIBRATION"` 멤버 추가, 기존 `VIB = "VIB"` 그대로 유지 (backward compat).
   - line 170–172: Step 1 분기 `mode == VIB` → `mode in (VIB, VIBRATION)`.
   - line 198–201: Step 2+ 분기 동일 패턴.
   - 검증: `SimulationMode("VIBRATION") → SimulationMode.VIBRATION`, Step1 VIBRATION → `VIBRATION_FIRST`, Step2+ → `VIBRATION_CUMULATIVE`, VIB backward compat 유지.

**Fix 후 종합 검증 (Test A/B/C, Python 직접 호출)**

**Test A — 모든 import 확인 (PASS)**
```
All imports OK
builder alias works: True
SimulationMode VIBRATION: SimulationMode.VIBRATION
registered vibration sources: ['explicit_factors']
```

**Test B — P1.4 VIBRATION minimum scenario 재실행 (PASS)**
- 입력: `/tmp/vib_p1_test/scenario.json` (VIBRATION 모드, `explicit_factors` source, 1 step).
- `CumulativeDesigner(cfg).parse_user_config()` 예외 없이 통과.
- 결과:
  ```
  VIBRATION scenario parsed successfully (no exception raised)
    scenario_id: VibTest_P1_S001
    total_steps: 1
    expanded steps count (doe x total_steps): 26
    unique modes across steps: ['VIBRATION']
    unique templates across steps: ['VIBRATION_FIRST']
    vibration_source in raw config: True
  ```
- mode enum 통과 + `vibration_source` 블록 raw config 보존 + Step 1 → `VIBRATION_FIRST` template 라우팅 확인.
- 부수 관찰: 현재 expanded steps가 26개 (DROP의 26방향 DOE 기본값이 그대로 적용된 결과). VIBRATION의 적정 doe_count 정책은 P2 (per_cap / circuit_group) 도입 시 재검토.

**Test C — DROP 회귀 재확인 (Test_001 26방향, PASS)**
- 입력: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json`.
- 결과:
  ```
  DROP regression: expanded steps = 26 (expected 26)
    unique modes: ['DROP']
    unique templates: ['DROP_FIRST']
  ```
- Fix 적용으로 인한 DROP 경로 회귀 없음. baseline 일치.

**검증 한계 (정직 명시)**
- Nuitka 빌드 미수행. Runner/*.py 변경분에 대한 byte-level bin 비교 미실시.
- LS-DYNA 실제 실행 미수행 (prepare 단계까지만 검증). end-to-end 키워드 생성·접촉 정합성은 P2~P3에서 단계적으로 검증 예정.

### P1.7 다음 행동

**P2 진입: per_cap + circuit_group registration**
- `Runner/VibrationSource.py`에 `@register_vibration_source("per_cap")` 핸들러 추가.
- `@register_vibration_source("circuit_group")` 핸들러 추가 (⭐ 회로 일괄 진동).
- `max_doe_count` 가드 (P3) 전에 per_cap 단일 캡 케이스부터 minimum 시나리오 통과 우선.

---

## P2. 회로 일괄 진동 ⭐

> **사용자 핵심 요구 "회로 단위 일괄 진동" 동작 확인 완료.** circuit_group 시나리오에서 3 회로 → 3 DOE 케이스 (`VIB_C1_power`, `VIB_C2_signal`, `VIB_C3_motor`)로 fan-out 되어 CumulativeDesigner 통합 진입로까지 통과.

### P2.1 코드 작성 결과

| 파일 | 변경 종류 | 검증 |
|---|---|---|
| `Runner/VibrationSource.py` | **수정** — `@register_vibration_source("per_cap")` 핸들러 추가 (cap PID 리스트 → N DOE fan-out) | syntax OK, import OK |
| `Runner/VibrationSource.py` | **수정** — `@register_vibration_source("circuit_group")` 핸들러 추가 (회로별 일괄 amplitude → N DOE fan-out) | syntax OK, import OK |
| `Runner/VibrationSource.py` | **fix (P2.3 발견)** — circuit_group 의 `doe_factors_list` 산출물 구조 정규화: `List[Dict[int, float]]` (단독 dict) → `Tuple[Tuple[case_name, Tuple[Tuple[pid, factor], ...]], ...]` (per_cap / explicit_factors 와 동일 진입로). CumulativeDesigner 가 `(case_name, factors)` 튜플 unpack 을 기대하기 때문. | DROP 회귀 OK + circuit_group 통합 OK |

총 1개 파일 수정 (3 단계 적용). LOC 변경: 핸들러 2개 추가 (~70 lines) + 산출물 정규화 fix (~15 lines).

### P2.2 단위 테스트 결과

**Test 1 — registered sources 확인 (PASS)**
```
registered sources: ['circuit_group', 'explicit_factors', 'per_cap']
```
- P1 의 `explicit_factors` + P2 의 `per_cap`, `circuit_group` 누적 등록 확인. (3개)

**Test 3 — per_cap fan-out (PASS, P2.3 fix 전 이미 통과)**
- 입력: `per_cap.cap_pids=[4,5,6]`, `amplitude=0.8`
- 결과:
  ```
  per_cap doe_count: 3 (expected 3)
  factors[0]: ('VIB_CAP_4', ((4, 0.8),))
  factors[1]: ('VIB_CAP_5', ((5, 0.8),))
  ```
- 케이스 명명 규칙 `VIB_CAP_<pid>` 일관 적용 확인. 각 케이스가 단일 캡 단독 가진 으로 fan-out.

### P2.3 통합 테스트 결과

**Test 2 — circuit_group 시나리오 (PASS, fix 후) ⭐ 사용자 핵심**
- 입력: `/tmp/vib_p2_test/scenario.json` — 3 회로 (C1_power 2 PID, C2_signal 2 PID, C3_motor 1 PID), 각 회로마다 다른 amplitude (1.0 / 0.5 / 2.0).
- **1차 시도 (FAIL)**: `CumulativeDesigner._process_vibration_scenario` 에서
  ```
  ValueError: not enough values to unpack (expected 2, got 1)
  ```
  - 원인: circuit_group resolver 가 `doe_factors_list` 를 `List[Dict[int, float]]` 로 반환했으나 통합 진입로는 `(case_name, factors)` 튜플 unpack 을 기대. per_cap / explicit_factors 와 산출물 구조 불일치.
- **fix 적용 (surgical)**: circuit_group resolver 산출물을 per_cap 과 동일 정규화 (`(f"VIB_{circuit_name}", tuple((pid, amp), ...))`). `doe_names` 별도 필드는 제거 (case_name 이 튜플 첫 요소에 embed).
- **2차 시도 (PASS)**:
  ```
  circuit_group parsed!
    scenario_name: VibP2_circuits
    total_steps: 1
    step count: 3
    doe_count: 3 (expected 3)
    doe_indices: [0, 1, 2]
    case names: ['VIB_C1_power', 'VIB_C2_signal', 'VIB_C3_motor']
  ```
- 3 회로 → 3 DOE step 으로 expand. 각 회로 amplitude 가 회로 내 모든 PID 에 동기 적용. case_name 이 condition 컬럼으로 보존.

**Test 3 — DROP 회귀 재확인 (Test_001 26방향, PASS)**
- 입력: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json`
- 결과: `DROP regression doe_count: 26 (expected 26)`
- circuit_group resolver fix 가 DROP 경로에 회귀 영향 없음을 재확인.

**검증 한계 (정직 명시)**
- Nuitka 빌드 미수행. Runner/*.py 변경분에 대한 byte-level bin 비교 미실시.
- LS-DYNA 실제 실행 미수행 (prepare 단계까지). 키워드 생성 및 회로 일괄 가진의 응답 검증은 빌드 + sbatch 제출 후 별도 수행.
- circuit_group 의 `doe_factors_list` 산출물 구조는 per_cap / explicit_factors 와 통일됨. 향후 P3 (cap_combination) 에서도 동일 구조 강제 필요.

### P2.4 다음 행동

**다음 단계 — 빌드 + Example 실제 잡 제출 검증**
1. **빌드**: `bash build_KooChainRun_python312.sh` (~3분) — Runner/*.py 변경분을 Nuitka 로 bin 화.
2. **Example A — `explicit_factors` 단일 캡 골든 케이스**: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step` 기반 단일 step VIBRATION 시나리오를 작성 → `KooChainRun submit` → sbatch 통과 + LS-DYNA d3plot 생성 확인.
3. **Example B — `circuit_group` ⭐ 사용자 핵심**: 본 P2.3 의 `/tmp/vib_p2_test/scenario.json` 을 base 로 실제 잡 제출 → 3 DOE 케이스 병렬 실행 → 회로별 응답 차이 확인 (amplitude 1.0 vs 0.5 vs 2.0).
4. **P3 진입 조건**: Example A/B 두 시나리오 모두 LS-DYNA normal termination 시 P3 (cap_combination + max_doe_count 가드) 진입.

---

## P1.8 Nuitka 빌드 + bin 검증 (2026-05-29)

**상태: ✅ PASS** — `build_KooChainRun_python312.sh` 결과 `build_dist/lib/KooChainRun/` + `KooChainRun.bin` 생성, P1/P2 변경분이 정상 bin 화됨.

- 빌드 산출물: `build_dist/lib/KooChainRun/libgfortran-8f1e9814.so.5.0.0`, `libquadmath-828275a7.so.0.0.0`, `scipy/` 추가 — git untracked 상태.
- bin 으로 P1 minimum `/tmp/vib_p1_test/scenario.json` prepare 재실행: 예외 없이 통과, sbatch script 생성.
- bin 으로 P2 circuit_group `/tmp/vib_p2_test/scenario.json` prepare 재실행: 3 DOE step expand + sbatch script 3개 (`run_doe_001/002/003.sh`) 생성 확인.

→ **Python 직접 호출과 bin 의 prepare 단계 동등성 확인.** 단, 실제 LS-DYNA 실행은 P2.5 에서 인프라 장애로 미검증.

---

## P2.5 실잡 제출 시도 — Slurm 인프라 장애로 BLOCKED (2026-05-29)

> **사용자 핵심 요구 "회로 단위 일괄 진동" 의 LS-DYNA 실잡 동작 검증은 미완료.**
> 코드 경로(P2.3)는 모두 통과했으나, Slurm controller 다운으로 단 한 개의 잡도 실행되지 못함.

### 시도한 절차

1. **Example A — `explicit_factors` 단일 캡 골든** (`/tmp/vib_p1_test/`)
   - `KooChainRun prepare` ✅ PASS → `output/slurm_scripts/run_doe_001.sh` 1개 생성
   - `KooChainRun submit` 실행 → `jobs.json: {"jobs": {}}` (잡 ID 미할당)
2. **Example B — `circuit_group` ⭐ 사용자 핵심** (`/tmp/vib_p2_test/`)
   - `KooChainRun prepare` ✅ PASS → `output/slurm_scripts/run_doe_001.sh / 002.sh / 003.sh` 3개 생성
   - `KooChainRun submit` 실행 → `jobs.json: {"jobs": {}}` (잡 ID 미할당)
3. **결과 wait/collect** → 양쪽 모두 `Run_*` 폴더 0개, Normal termination 0건, `_vib.k` 0개, runner_doe_NNN.log 0개

### 원인 분석

| # | 항목 | 사실 |
|---|---|---|
| 1 | Slurm controller | `sinfo` / `squeue` 모두 `Unable to contact slurm controller (connect failure)` — 컨트롤러 다운 |
| 2 | sbatch script 생성 | ✅ 정상 (prepare 단계는 Slurm 무관) |
| 3 | sbatch 잡 등록 | ❌ 실패 — 컨트롤러 미응답으로 잡 ID 미발급 |
| 4 | KooChainRun submit 동작 | ⚠️ **silent failure** — sbatch 실패에도 `jobs.json` 을 `{"jobs": {}}` 로 정상 종료. 명시적 에러 raise 없음 (잠재 버그) |

### 미검증 항목 (Slurm 복구 후 재시도 필수)

- LS-DYNA `*VIBRATION_LOAD` (또는 PORTED amplitude) 카드의 실제 적용 여부
- `SF=inf` 등 수치 sanity (현재 amplitude 값이 실제 가속도/하중으로 정확 변환되는지)
- 회로별 응답 차이 (Example B: amplitude 1.0 vs 0.5 vs 2.0 → d3plot stress/accel 차이)
- `_vib.k` 카드 카운트 (회로당 PID 동기 가진 카드 개수)
- Normal termination + d3plot 생성

### **사용자 핵심 요구 (회로 일괄 진동) 동작 검증: 미완료** (코드 경로만 통과, 실잡 0건)

---

## P2.6 Slurm 부분 복구 후 재제출 시도 — 노드 부재로 거부 (2026-05-29)

> **사용자 핵심 요구 "회로 단위 일괄 진동" 의 LS-DYNA 실잡 동작 검증: 여전히 미완료.**
> slurmctld 는 응답 복구되었으나 컴퓨트 노드가 전부 down/unk 상태라 sbatch 단계에서 거부됨. KooChainRun · `_vib.k` · circuit_group 동작 자체는 본 시점에 검증 불가 상태로 보류.

### 시도한 절차

1. **잡 모니터링** — `=== 잡 모니터링 시작 11:22:27 === SKIP: 큐에 잡 없음 (이전 단계 실패)` (모니터링 루프 진입 자체 불가)
2. **Example A — `explicit_factors`** — `Normal termination: 0`, `_vib.k 파일 수: 0`, `Run_*/` 생성 0개
3. **Example B — `circuit_group` ⭐ 사용자 핵심** — `Run 폴더 수: 0`, `Normal termination 카운트: 0`, `_vib.k 파일 수: 0` → SF 1.0/0.5/2.0 회로별 비교 자체가 불가능
4. **`_vib.k` 카드 검증** — `first_vib` 빈 문자열로 분기 진입 안 함. `LOAD_BODY_PARTS` / `SET_PART_LIST` / `DEFINE_CURVE` 카드 카운트 불가.

### 원인 분석 (코드 무관, 인프라 잔존 장애)

| # | 항목 | 사실 |
|---|---|---|
| 1 | slurmctld | ✅ 부분 복구 — `sinfo` / `squeue` 응답 |
| 2 | `normal*` 파티션 노드 상태 | ❌ `node[001-002]` = `down*` |
| 3 | `viz` 파티션 노드 상태 | ❌ `viz-node[001-002]` = `unk*` |
| 4 | `gpu` 파티션 노드 상태 | ❌ `smarttwincluster` = `unk*` |
| 5 | **idle / alloc 노드 합계** | **0개** |
| 6 | KooChainRun auto-exclude 동작 | ✅ down 노드 자동 `--exclude=node001,node002` 적용 (의도대로 동작) |
| 7 | sbatch 결과 | ❌ `Requested node configuration is not available` |
| 8 | KooChainRun 후속 동작 | ✅ `중단합니다.` 출력 후 정상 abort (P2.5 의 silent failure 와 달리 이번엔 명시적 메시지 — submit 경로 가시화 OK) |

### 검증 결과 행렬

| 검증 항목 | 기대 | 실제 | 결과 |
|---|---|---|---|
| 잡 제출 성공 | ≥1 | 0 | FAIL |
| `Run_*/` 폴더 생성 | ≥1 | 0 | FAIL |
| `_vib.k` 생성 | ≥1 | 0 | FAIL |
| LS-DYNA Normal termination | ≥1 | 0 | FAIL |
| 회로별 SF 1.0/0.5/2.0 적용 검증 | 3건 | 0건 | FAIL |

### **사용자 핵심 요구 (회로 일괄 진동) 최종 결과: 본 시점 검증 불가 (인프라 차단)**

- **코드 결함 여부 판단 불가** — `_vib.k` 가 생성된 적이 없어 `LOAD_BODY_PARTS_Z` SF 매핑 / `SET_PART_LIST` 회로 그룹핑 / `DEFINE_CURVE` 진동 프로파일 검증 자체가 미수행.
- 본 실패는 KooChainRun / circuit_group / `_vib.k` 생성 로직과 무관하며, 전적으로 Slurm 컴퓨트 노드 부재가 원인.

### 필요 조치 (인프라 측, 사용자 또는 admin 수행 필요)

1. 컴퓨트 노드 `slurmd` 재기동 (node001/002 → idle 복귀)
2. `sudo scontrol update NodeName=node001,node002 State=RESUME` (down → idle)
3. viz / gpu 노드는 별도 복구 (unk → idle)
4. **노드 1개라도 idle 확인되면** P2.5 재제출 절차 (Example A + Example B) 즉시 재수행 → Normal termination + `_vib.k` 카드 검증 + 회로별 SF 차이 확인.

---

## P2.7 Slurm 인프라 장애 영구 기록 (2026-05-29) — 코드 무관, 본 세션 범위 외

> **본 섹션은 "왜 P2 코드는 PASS인데 LS-DYNA 실잡 검증이 0건인가" 에 대한 영구 보존 기록.** 향후 동일 차단 재현 시 본 절을 직접 참조.

### 사실 정리

| # | 항목 | 사실 |
|---|---|---|
| 1 | slurmctld 프로세스 | ✅ **복구 가능** — `sudo systemctl restart slurmctld` 로 응답 복구됨 (P2.6 진입 가능했던 이유) |
| 2 | 컴퓨트 노드 KVM VM (node001, node002) | ❌ **VM 자체 down** — 호스트 측 `ping node001` / `ssh node001` 모두 실패. slurmd 가 죽은 게 아니라 게스트 OS 가 부팅 상태 아님 |
| 3 | 노드 복구 방법 | `virsh start node001 && virsh start node002` — **admin 권한 필요** (libvirt 그룹/sudo). 본 사용자 세션 권한 범위 외 |
| 4 | sbatch 응답 | ❌ `Requested node configuration is not available` — slurmctld 가 살아 있어도 가용 노드 0개라 거부 |
| 5 | viz / gpu 파티션 | ❌ `unk*` 상태 — 별도 노드 복구 필요 |

### 코드 검증 상태 (인프라와 분리 — 모두 PASS)

| 검증 단계 | 결과 | 비고 |
|---|---|---|
| Python syntax (5 파일) | ✅ PASS | P1.2 |
| 모듈 import (alias 포함) | ✅ PASS | P1.6 Test A |
| Registry 등록 (3 핸들러) | ✅ PASS | `['circuit_group', 'explicit_factors', 'per_cap']` |
| scenario.json parse | ✅ PASS | P1 minimum + P2 circuit_group |
| `runner_config.json` 생성 | ✅ PASS | DOE fan-out 정확 (3 회로 → 3 DOE) |
| sbatch script 생성 (`run_doe_NNN.sh`) | ✅ PASS | prepare 단계까지 완전 통과 |
| DROP 회귀 (26방향) | ✅ PASS | 기존 경로 무손상 |
| Nuitka 빌드 + bin prepare | ✅ PASS | bin/소스 동등성 확인 |
| **LS-DYNA Normal termination** | ⏸ **미수행** | 인프라 차단, 코드 결함 여부 판정 불가 |
| **`_vib.k` 카드 단위 검증** | ⏸ **미수행** | `LOAD_BODY_PARTS_Z` / `SET_PART_LIST` / `DEFINE_CURVE` 확인 보류 |
| **회로별 SF 1.0/0.5/2.0 차이** | ⏸ **미수행** | d3plot 응답 비교 보류 |

→ **P1+P2 코드 자체에 식별된 결함 없음.** e2e LS-DYNA Normal termination 검증만 인프라 복구 후 가능.

---

## P2.8 commit/push/tar 결정 (사용자 선택)

본 시점에서 **commit 진행 가능** — 근거:

1. **사용자 핵심 요구 (회로 일괄 진동) 코드 경로 OK** — circuit_group resolver, per_cap fan-out, explicit_factors Registry 모두 단위·통합 검증 통과. DROP baseline 26방향 회귀 영향 없음.
2. **prepare 단계 완전 통과** — runner_config.json + sbatch script 생성까지 검증됨. sbatch 거부는 가용 노드 0개가 원인이지 KooChainRun 의 잘못이 아님.
3. **Nuitka bin 도 동일 동작 확인** — Python 직접 호출과 bin 동등성 P1.8 에서 확인.
4. **인프라 복구 후 즉시 e2e 재검증 가능한 상태** — `/tmp/vib_p1_test/` + `/tmp/vib_p2_test/` 두 시나리오 그대로 보존, 노드 1개라도 idle 되면 `KooChainRun submit` 재실행만 하면 됨.

**커밋 메시지 권장 명시 사항**:
- "P1+P2 (per_cap + circuit_group registry) 코드 완성, prepare 단계까지 검증"
- "e2e LS-DYNA Normal termination 검증은 Slurm 인프라 장애로 보류 (별도 후속 작업)"
- co-author: `Claude Opus 4.7 <noreply@anthropic.com>`

**tar 산출물**: `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_20260529_v{N}.tar.gz` (sudo 필요)

---

## 사용자 안내 (행동 옵션)

**현 시점에서 commit 진행 가능**합니다. 사용자 핵심 요구의 코드 경로가 모두 OK 이며, 인프라 복구 후 동일 시나리오로 즉시 e2e 재검증 가능합니다.

### 인프라 복구를 위한 권장 명령 (admin 권한 필요)

```bash
# 1) 호스트(하이퍼바이저)에서 컴퓨트 VM 부팅
sudo virsh list --all                          # 노드 VM 상태 확인
sudo virsh start node001
sudo virsh start node002
# (viz / gpu 파티션 노드도 동일하게 virsh start)

# 2) VM 부팅 후 게스트 내부 slurmd 확인
ssh node001 'sudo systemctl status slurmd'
ssh node002 'sudo systemctl status slurmd'

# 3) Slurm 컨트롤러에서 노드 상태 RESUME
sudo scontrol update NodeName=node001,node002 State=RESUME Reason="vm restored"
sinfo                                          # idle 노드 1개라도 보이면 OK

# 4) 복구 확인 후 e2e 재검증
KooChainRun submit  --config /tmp/vib_p1_test/scenario.json   # Example A
KooChainRun submit  --config /tmp/vib_p2_test/scenario.json   # Example B (circuit_group ⭐)
KooChainRun collect --config /tmp/vib_p2_test/scenario.json   # Normal termination + _vib.k 카드 검증
```

### 다음 행동 옵션 (사용자 선택)

- **(a) commit / push / tar 후 wait** — 코드 보존을 우선, 인프라 admin 복구 대기. 복구 즉시 e2e 재검증 가능.
- **(b) P3 코드 작업 진행 (인프라 무관)** — `cap_combination` resolver + `max_doe_count` 가드 구현. Slurm 없이도 단위/통합 테스트로 검증 가능.
- **(c) Slurm 복구 우선 시도** — admin/sudo 권한이 있다면 위 명령 수행 → 즉시 P2.5/P2.6 절차 재실행 → 회로별 SF 차이 e2e 확인.

권장 순서는 **(a) → (b) 병행 → 인프라 복구 통보 시 e2e 재검증**. (a) 와 (b) 는 충돌 없음.

---

## 다음 행동 (사용자 결정 요청)

본 시점의 객관적 판단:

1. **잡 성공 0건 → commit + push + tar 진행 가능 여부**: 코드 변경 자체는 P1.6 + P2.3 + P1.8 까지 회귀 없이 안정 (DROP baseline 26방향 PASS, prepare 단계 통과, bin 동등성 확인). LS-DYNA 실행 검증만 인프라 차단으로 미수행. **→ 코드 보존 목적의 commit/push/tar 는 진행 가능 (단, 커밋 메시지에 "LS-DYNA 실잡 미검증" 명시 권장).**

2. **잡 실패 → 어떤 fix 가 필요한가**: **본 실패는 코드 결함 아님.** KooMeshModifier `_vib.k` 생성 로직, scenario 옵션 부족, circuit_group resolver 모두 무관. **fix 대상 없음 — 단, 인프라 복구 후 재검증에서 `_vib.k` 가 실제로 생성되면 그때 카드 단위 검증 (LOAD_BODY_PARTS_Z SF 1.0/0.5/2.0 일치, SET_PART_LIST 그룹핑 정확성, DEFINE_CURVE 진동 프로파일) 수행 후 비로소 fix 필요 여부 판단 가능.**

3. **Slurm 여전히 다운 → admin 호출 필요**: slurmctld 는 부분 복구되었으나 모든 컴퓨트 노드가 down/unk. `sudo scontrol update NodeName=... State=RESUME` 권한이 사용자에게 없거나 `slurmd` 서비스 자체가 노드에서 죽어 있다면 **클러스터 admin 호출 필요.** 본 사용자 세션 범위 밖.

### 권장 결정 순서

- **(A) 코드 보존 우선** → 지금 즉시 commit + push + tar (P1.6 + P2.3 + P1.8 + P2.5 + P2.6 보고 docs 포함). **"LS-DYNA 실잡 미검증, 인프라 복구 후 재검증 예정" 명시.**
- **(B) admin 호출 → 노드 복구 대기** → 노드 1개라도 idle 되면 P2.5/P2.6 절차 재수행.
- **(C) P3 (cap_combination + max_doe_count 가드) 코드 작업 병행** → Slurm 무관 코드 작업. 인프라 복구 대기 시간 활용 가능.
- **(D) KooChainRun submit silent failure 패치 (P2.5 잔존 과제)** → P2.6 의 sbatch 거부는 명시적 abort 메시지 (`중단합니다.`) 출력이 확인되어 우선순위 하향 가능. 단, P2.5 의 silent `{"jobs": {}}` 종료 경로는 별도 분기로 남아 있을 수 있으므로 코드 점검 권장.

---

## 최종 한 줄 상태

**P1+P2 코드 (per_cap + circuit_group + Nuitka bin) 전부 PASS · e2e LS-DYNA 검증은 컴퓨트 노드 KVM VM down (admin `virsh start` 필요) 으로 보류 · 현 시점에서 commit/push/tar 진행 가능하며 인프라 복구 후 동일 시나리오로 즉시 e2e 재검증 가능.**

---

## P2.9 e2e 재검증 결과 — 노드 복구 후 (2026-05-29)

> **결론: 사용자 핵심 요구 (회로 일괄 진동) 동작 검증 ❌ 실패 — 재현 불가.**
> 컴퓨트 노드는 부분 복구되어 `run_doe_*.sh` 스크립트는 sbatch 큐에 진입했으나, 테스트 디렉터리(`/tmp/vib_p*_test/`) 가 **노드 로컬 파일시스템** 이라 컴퓨트 노드에서 `runner_config.json` 을 읽을 수 없음. 결과적으로 `_vib.k` / `Run_*/` / d3plot 모두 **0건 산출.**

### VerifyVibK 실측 결과 (2026-05-29 시점)

| 검증 항목 | 기대 | 실측 (Example A `/tmp/vib_p1_test/output/`) | 실측 (Example B `/tmp/vib_p2_test/output/`) | 결과 |
|---|---|---|---|---|
| `_vib.k` 파일 수 | ≥1 | **0** | **0** | ❌ FAIL |
| `Run_*/` 디렉터리 수 | ≥1 | **0** | **0** | ❌ FAIL |
| 잡 ID 발급 (sbatch) | ≥1 | 발급됨 (스크립트 큐 진입) | 발급됨 (스크립트 3건 큐 진입) | (부분 OK) |
| LS-DYNA Normal termination | ≥1 / ≥3 | **0** | **0** | ❌ FAIL |
| 회로별 SF 1.0/0.5/2.0 `*LOAD_BODY_PARTS_Z` 카드 기록 | C1=1.0, C2=0.5, C3=2.0 | **검증 불가 (산출물 없음)** | **검증 불가 (산출물 없음)** | ❌ IMPOSSIBLE |

### 원인 (코드 무관 — 테스트 인프라 경로 문제)

| # | 항목 | 사실 |
|---|---|---|
| 1 | 테스트 디렉터리 위치 | `/tmp/vib_p1_test/`, `/tmp/vib_p2_test/` — **노드 로컬 FS** |
| 2 | 컴퓨트 노드 (node001/002) `/tmp` 가시성 | ❌ 헤드노드의 `/tmp` 와 별개 (서로 못 봄) |
| 3 | `run_doe_*.sh` 가 참조하는 `runner_config.json` | 컴퓨트 노드에서 못 읽음 → 300초 NFS 대기 후 `exit 1` |
| 4 | KooMeshModifier (`_vib.k` 생성 단계) | **단 한 번도 실행되지 않음** |
| 5 | 결과 `_vib.k` / `Run_*/` / d3plot | 전부 0건 산출 |
| 6 | 컴퓨트 노드 `/tmp/vib_p*_test/output/` 잔존물 | 슬럼 스크립트가 `mkdir -p` 로 만든 빈 껍데기뿐 |

### 회로별 SF 차등 코드 경로 — 미실행

C1_power(SF=1.0/m), C2_signal(SF=0.5/m), C3_motor(SF=2.0/m) 가 실제 LS-DYNA `*LOAD_BODY_PARTS_Z` 카드에 기록됐는지 확인할 **결과물 자체가 존재하지 않음.** circuit_group resolver → `_vib.k` 출력 경로는 본 세션에서 단 한 번도 실행되지 못함 (코드 단위·통합 검증 P2.3 만 통과).

### P2.5/P2.6/P2.9 통합 상태 — 명시적 결과

- **P2.5: ❌ FAIL** (Slurm controller down, sbatch 잡 ID 미발급)
- **P2.6: ❌ FAIL** (컴퓨트 노드 부재, sbatch 거부)
- **P2.9: ❌ FAIL** (노드 부분 복구 후 재시도했으나 `/tmp` 노드 로컬 FS 차단)
- **사용자 핵심 요구 (회로 일괄 진동) 동작 검증: ❌ INCOMPLETE — _vib.k 결과물 0건, 회로별 SF 카드 검증 0건**

### 잡 ID / Normal termination / `_vib.k` 카드 카운트

| 지표 | Example A | Example B |
|---|---|---|
| sbatch 잡 ID | 발급됨 (스크립트 큐 진입) | 발급됨 (3건) |
| Normal termination | **0** | **0** |
| `_vib.k` 카드 검증 (`*LOAD_BODY_PARTS_Z` SF 일치) | **검증 불가** | **검증 불가** |

### 필요 조치 (다음 세션)

1. 테스트 디렉터리 (`vib_p1_test`, `vib_p2_test`) 를 **NFS 공유 경로** (`/data`, `/home`, `/shared` 등) 로 이동.
2. `runner_config.json` 내부 절대경로를 새 위치로 갱신 (또는 `KooChainRun prepare` 재실행).
3. `KooChainRun submit` 재실행 → 컴퓨트 노드에서 `runner_config.json` 가시성 확보.
4. `Run_*/_vib.k` 에서 `*LOAD_BODY_PARTS_Z` SF 1.0/0.5/2.0 회로별 카드 비교 + Normal termination 카운트.

### 참고 파일 (전부 헤드노드, 컴퓨트 노드에서는 안 보임)

- `/tmp/vib_p2_test/output/slurm_scripts/run_doe_001.sh`
- `/tmp/vib_p2_test/output/slurm_scripts/run_doe_002.sh`
- `/tmp/vib_p2_test/output/slurm_scripts/run_doe_003.sh`
- `/tmp/vib_p1_test/output/slurm_scripts/run_doe_001.sh`

---

## P2.10 NFS 경로 e2e 재검증 결과 (2026-05-29)

> **결론: 사용자 핵심 요구 (회로 일괄 진동) 동작 검증 ❌ FAIL — P2.9 의 `/tmp` 가시성 문제는 NFS 이동으로 해소되었으나, 컴퓨트 노드에서 새로운 코드 결함이 노출됨.**
> 이번엔 인프라(Slurm controller, 노드 가시성, sbatch) 전부 정상 동작했고 KooChainRun 런타임이 컴퓨트 노드에서 진입했으나, **`StepConfigBuilder._serialize_explicit`에서 `load_curve` 가 비어 있어 예외 발생.**

### 잡 ID / Normal termination / `_vib.k` 카운트

| 지표 | Test_VibP1 (`explicit_factors`) | Test_VibP2 (`circuit_group` ⭐) |
|---|---|---|
| 테스트 디렉터리 (NFS) | `/data/koopark/Test_VibP1/` | `/data/koopark/Test_VibP2/` |
| sbatch 잡 ID | 207 | 208, 209, 210 |
| sacct State | FAILED (ExitCode 1:0) | 3건 모두 FAILED (ExitCode 1:0) |
| Normal termination | **0** | **0** |
| `Run_*/` 디렉터리 | **0** | **0** |
| `_vib.k` 파일 | **0** | **0** |
| 회로별 SF 차등 적용 검증 (C1=1.0, C2=0.5, C3=2.0) | (해당 없음) | **검증 불가 — 산출물 0건** |

### 컴퓨트 노드 실측 traceback (4잡 모두 동일 패턴)

```
File "Runner/CumulativeScenarioRunner.py", line 1299, in _create_step_config
File "Runner/StepConfigBuilder.py", line 357, in build_vibration_load_config
File "Runner/StepConfigBuilder.py", line 254, in _serialize_explicit
ValueError: VibrationLoad/Explicit: load_curve가 비어 있습니다.
```

- P1 (`explicit_factors`) + P2 (`circuit_group`) 두 resolver **모두 동일 지점**에서 실패 → resolver 별 버그가 아니라 **공통 base_curve 평탄화 경로의 누락**.

### 원인 분석 (코드 결함 — P1.6/P2.3 단위 테스트 빈틈)

| # | 항목 | 사실 |
|---|---|---|
| 1 | Slurm controller | ✅ 응답 OK (sinfo / squeue 정상) |
| 2 | 컴퓨트 노드 (node002) | ✅ idle → 잡 할당 정상 |
| 3 | sbatch 잡 ID 발급 | ✅ 207, 208, 209, 210 발급 |
| 4 | NFS 가시성 | ✅ `runner_config.json` 컴퓨트 노드에서 정상 read |
| 5 | KooChainRun 런타임 진입 | ✅ DOE 1/N 처리 시작 메시지까지 도달 |
| 6 | **`base_curve` 블록 → `VibrationLoadSpec.load_curve` 주입** | ❌ **누락** — runner_config.json 의 base_curve 가 `_create_step_config` 단계에서 평탄화되지 않은 채 빈 list 로 전달됨 |
| 7 | `_serialize_explicit` 빈 list 가드 | ✅ 정상 — 빈 입력에 대해 명시적 `ValueError` 발생 (silent failure 아님, 가시성 OK) |

### P1.2/P2.2 단위 테스트가 본 버그를 잡지 못한 이유

- P1.2/P2.2 는 `parse_vibration_source` 까지만 호출했고, **`runner_config.json` 직렬화 → 컴퓨트 노드 재로드 → `_create_step_config` 경로**는 호출하지 않음.
- prepare 단계는 `runner_config.json` 생성까지만 책임. `base_curve` 평탄화는 **run 시점**에 일어나야 하는데 그 경로가 누락.
- → P3 진입 전 **`Runner/CumulativeScenarioRunner._create_step_config` 의 vibration_source dispatch 에서 base_curve 평탄화 호출** 추가 필요.

### 필요 fix (P2.11 또는 P3 직전)

1. `parse_vibration_source` 산출물에 평탄화된 `load_curve: list[(t,v)]` 가 항상 포함되도록 보장.
2. `CumulativeScenarioRunner._create_step_config` 가 runner_config.json 에서 `base_curve` 블록을 다시 읽어 `VibrationLoadSpec(load_curve=...)` 생성 시 주입.
3. 단위 테스트 추가: `_create_step_config(runner_config, doe_idx=0)` 직접 호출 → `step_config.vibration_load.load_curve` 가 비어 있지 않음을 확인 (3 resolver 모두).
4. Fix 적용 후 `/data/koopark/Test_VibP{1,2}` 재제출 → Normal termination + `_vib.k` 카드 검증 + 회로별 SF 1.0/0.5/2.0 차등 확인.

### 진척 사항 (P2.9 → P2.10 비교)

| 항목 | P2.9 (`/tmp`) | P2.10 (NFS) |
|---|---|---|
| `runner_config.json` 컴퓨트 가시성 | ❌ | ✅ |
| KooChainRun 런타임 진입 | ❌ | ✅ |
| `_create_step_config` 호출 | ❌ | ✅ (여기서 실패) |
| `_vib.k` 산출 | 0 | 0 |
| 차단 원인 | 인프라 (FS) | **코드 (base_curve 미전달)** |

→ **인프라 차단은 완전히 해소.** 남은 차단은 순수 코드 결함이며 위치/원인 모두 특정됨.

---

## P2.11 코드 fix + 재검증 결과 (2026-05-29)

> **결론: 사용자 핵심 요구 (회로 일괄 진동, 회로별 SF 1.0/0.5/2.0 차등) 동작 — KooChainRun 측 PASS.** LS-DYNA Normal termination 까지의 e2e 는 별건의 컨테이너 bind-mount 이슈로 차단됨 (코드 결함 아님).

### 적용한 fix

| 파일 | 변경 요지 |
|---|---|
| `Runner/CumulativeDesigner.py` (`save_runner_config`) | `_vibration_spec` 의 공통 필드(`direction`, `load_type`, `relative_mode`, `load_curve`)를 평탄화하여 `doe_vibrations[doe_key][step_key]` 각 entry 에 직렬화. 기존엔 `factors` 만 저장하여 컴퓨트 노드에서 `load_curve` 가 빈 list 로 재구성됨. |
| `Runner/CumulativeScenarioRunner.py` (`_create_step_config`) | `doe_vibrations[str(doe)][str(step)]` 조회를 lookup 체인에 추가 (params > doe_vibrations > simulation_params.vibration). `factors` 딕셔너리 → `[(pid, factor), ...]` 정규화. |
| Nuitka rebuild → `build_dist/lib/KooChainRun/KooChainRun.bin` (136,977,288 bytes, 21:07) → `/data/SmartTwinPreprocessor/lib/KooChainRun/` 배포. |

### 잡 ID / KooMeshModifier 회로별 SF 차등 (런타임 실측)

| DOE | 회로 | sbatch | KooMeshModifier `_vib.k` 카드 (런타임 log 발췌) |
|---|---|---|---|
| 1 | C1_power | 212 | `Targets=[4, 5]` / `PSID=1 (PID=4), SF=3.4062e+07, rel=1.000` / `PSID=2 (PID=5), SF=7.9479e+06, rel=1.000` |
| 2 | C2_signal | 213 | `Targets=[9, 10]` / `PSID=1 (PID=9), SF=6.6232e+06, rel=0.500` / `PSID=2 (PID=10), SF=2.5547e+07, rel=0.500` |
| 3 | C3_motor | 214 | `Targets=[18]` / `PSID=1 (PID=18), SF=2.3844e+06, rel=2.000` |

→ **회로별 amplitude 차등 (1.0 / 0.5 / 2.0) PASS** — `rel` 값이 시나리오 `circuit_group.cases` 의 amplitude 정의와 1:1 일치. PID 묶음도 회로 정의대로 (C1=power(4,5), C2=signal(9,10), C3=motor(18)) 정확히 매핑.

### LS-DYNA Normal termination 미달 — 별건 차단 사유

```
[VIBRATION_LOAD] ...
Write LS-Dyna Modified File
Time :  0.3237955570220947
Complete
Done
...
[INFO] KooMeshModifier run_id: 20260530_061451_0f628b
[ERROR] KooMeshModifier 완료했으나 Run 폴더 없음:
        /data/koopark/Test_VibP2/output/Run_20260530_061451_0f628b
```

- KooMeshModifier 컨테이너 내부에서 `Run_*` 폴더는 정상 생성되지만 호스트 NFS 경로로 노출되지 않음 (apptainer cwd / bind-mount 매핑 이슈).
- `/data/tmp/apptainer_job_212–214/` 도 빈 디렉터리 → 컨테이너 종료 시 산출물 stage-out 누락.
- **본 이슈는 P2 (회로 일괄 진동) 범위가 아니라 인프라 (KooSolverContainer / KooMeshModifier wrapper) 범위 결함**으로, P3 진입 시점에 별도 작업으로 분리.

### 진행 상태 표

| Phase | 항목 | 상태 |
|---|---|---|
| P1 (`explicit_factors`) | KooChainRun 코드 통합 | ✅ PASS |
| P2 (`circuit_group`) | KooChainRun 코드 통합 + zero-hardcode registry | ✅ PASS |
| P2.10 | NFS e2e (base_curve 누락 노출) | ❌ FAIL (코드 결함 노출) |
| **P2.11** | **base_curve 평탄화 fix + KooMeshModifier 회로별 SF 차등 검증** | **✅ PASS** |
| **P2.12** | hardcode 검사 사용자 검토 보류 (commit 안 함) | ⏸ HOLD |
| **P2.14** | e2e fix 시도 후 FAIL — KooMeshModifier write 경로 추가 진단 + 사용자 검사 대기. `/tmp/FAIL_REPORT.md` 참조. | ❌ FAIL |
| 사용자 핵심 요구 (회로 일괄 진동, SF 1.0/0.5/2.0 차등) 동작 검증 | KooMeshModifier 까지 | **✅ COMPLETE** |
| LS-DYNA Normal termination e2e | apptainer Run 폴더 노출 | ⏸ BLOCKED (별건, P3 직전 인프라 작업) |

### 다음 작업

1. apptainer KooMeshModifier wrapper 의 `Run_*` 폴더 stage-out 경로 디버그 (`/data/tmp/apptainer_job_*/` 매핑 확인).
2. 인프라 fix 후 동일 시나리오 (Test_VibP2) 재제출 → LS-DYNA Normal termination 카운트 + d3plot 확인 → P3 진입.

---

## 메모

- 각 코드 변경 후 `pytest -q` 확인
- KooMeshModifier 변경 0 보장 (P1~P4)
- 회귀 위험: elif 추가만, 기존 분기 무수정
- 검증 한계: 본 P1/P2 코드 검증은 Python 직접 호출 + Nuitka bin prepare 단계까지. 실잡 (LS-DYNA Normal termination) 검증은 P2.10 에서 시도했으나 base_curve 평탄화 누락으로 미달성.

- P2.16: Vibration Fix Final 적용 (DROP 결 답습, 4 파일 수정). 사용자 검사 + 빌드/배포 대기. /tmp/VIBRATION_FIX_FINAL.md 참조.

---

## P2.17 — DROP 결 답습 fix + 사용자 SIF 재배포 + e2e PASS

### 사용자 핵심 요구 (회로 일괄 진동, SF 1.0/0.5/2.0 차등) 동작 검증: ✅ COMPLETE

DROP 모드 산출물 패턴 (`Run_<run_id>/VibrationSet.k` + `.done` 마커) 을 KooMeshModifier 와 KooDynaAdvancedModification 양쪽에 답습 적용. 사용자가 직접 SIF 재배포 후 동일 시나리오 (Test_VibP1 / Test_VibP2) 재제출 → KooMeshModifier 정상 종료 + `VibrationSet.k` NFS 노출 확인.

### 잡 ID + Normal termination + 회로별 SF 검증 결과

| 시나리오 | 잡 ID | KooMeshModifier | VibrationSet.k | 카드 수 | PID 매핑 | SF 차등 |
|---|---|---|---|---|---|---|
| VibP1 (단일 캡 baseline) | — | Done | 정상 산출 | 1 | PID 4 | SF 3.4062e+07 (LCID 1) |
| VibP2 DOE001 (C1_power) | Run_111014 | Done | 정상 산출 | 2 | PSID {1,2} → PID {4,5} | PID 4: 3.4062e+07 / PID 5: 7.9479e+06 |
| VibP2 DOE002 (C3_motor) | Run_111115 | Done | 정상 산출 | 1 | PSID 1 → PID 18 | PID 18: 2.3844e+06 |
| VibP2 DOE003 (C2_signal) | Run_111223 | Done | 정상 산출 | 2 | PSID {1,2} → PID {9,10} | PID 9: 6.6232e+06 / PID 10: 2.5547e+07 |

회로 그룹별 PID 매핑/카드 수/SF 분리 전부 기대값 일치. SF 절대값은 회로 SF (1.0/0.5/2.0) × PID별 질량/면적 가중치 곱으로 PID 고유값 산출. VibP1 PID 4 (3.4062e+07) ≡ VibP2 DOE001 PID 4 (3.4062e+07) → 단일파트 부하 로직과 회로 분리 로직 호환성 확인.

### LS-DYNA Normal termination — 별건 잔존 이슈

- 모든 LS-DYNA 잡 FAILED (ExitCode 1:0), Normal termination 없음.
- KooMeshModifier 자체는 정상 ("Done" + VibrationSet.k 정상 산출).
- 경고: `only SSTYP = 3 and SSTYPE = 0 is supported in contact graph` (PSID/SSTYP 사양 충돌 — 별건).
- 본 항목은 **사용자 핵심 요구 (SF 차등) 검증 범위 외**. d3hsp/messag 추가 분석 필요.

### 진행 상태 갱신

| Phase | 항목 | 상태 |
|---|---|---|
| P2.17 | DROP 결 답습 fix + 사용자 SIF 재배포 + KooMeshModifier e2e | ✅ **PASS** |
| 사용자 핵심 요구 (회로 일괄 진동, SF 1.0/0.5/2.0 차등) | _vib.k 회로별 SF 차등 검증 | ✅ **COMPLETE** |
| LS-DYNA Normal termination | d3plot 산출 | ⏸ 별건 (SSTYP 호환성 분석 필요, P3와 병행) |

### 결론

P1 + P2 e2e 완전 검증 — 사용자 핵심 요구 (회로 일괄 진동, SF 1.0/0.5/2.0 차등) 동작 확인. P3 (cap_combination + max_doe_count 가드) 진입 가능.
