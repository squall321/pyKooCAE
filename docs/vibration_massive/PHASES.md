# PHASES.md — VIBRATION 모드 단계별 구현 문서

> **목표:** Zero-Hardcode 통합 설계(`final_plan.md` / `design_decisions.md`)를 6개 Phase로 분해하여 순차 구현. 각 Phase는 독립 검증 가능한 산출물을 가지며, CLAUDE.md §4 Goal-Driven 원칙에 따라 검증 통과 시에만 다음 Phase 진입.
>
> **사용자 핵심 요구 우선순위:** P2 `circuit_group`(회로별 일괄 진동) ≥ P3 `cap_combination`(DOE 조합) > 나머지.
>
> **Surgical 원칙:** IMPACT/THERM 인라인 f-string 리팩토링, KooMeshModifier 내부 로직 변경, sbatch 호출 site 7개 일괄 마이그레이션은 **본 시리즈 범위 외** (별도 PR).

---

## P1. 최소 통합 (Registry + explicit_factors + per_cap)

본 시리즈의 인프라 Phase. Registry / StepConfigBuilder / mode dispatch 3개 layer를 한 번에 도입하고, source 2개(`per_cap`, `explicit_factors`)로 end-to-end 경로를 검증한다. 사용자 핵심인 `circuit_group`은 P2로 분리하여 P1의 변경 폭을 최소화한다.

| 항목 | 값 |
|---|---|
| 목적 | Registry/Builder/Dispatch 3 layer 인프라 구축 + 최소 source 2개로 E2E 경로 증명 |
| 수정 파일 (file:function) | - `Runner/VibrationSource.py` (신규): `register_vibration_source`, `parse_vibration_source`, `VibrationLoadSpec`, `_parse_per_cap`, `_parse_explicit_factors`, `materialize_curve`(inline only), `validate_direction`<br>- `Runner/StepConfigBuilder.py` (수정): `build_vibration_load_block`, `_VIB_KEYWORDS`, `_VIB_OPTION_KEYS`, `_serialize_load_curve`, `_serialize_part_factors`<br>- `Runner/CumulativeScenarioRunner.py:_run_step` L1175 근방: `elif mode == "VIB":` 분기 (~12 LOC)<br>- `Runner/TemplateManager.py:select_template_for_step`: `_FIRST_TEMPLATE_BY_MODE` / `_CUMULATIVE_TEMPLATE_BY_MODE` mapping dict (기존 if/elif 평탄화, `SimulationMode.VIB` 항목 추가)<br>- `Runner/CumulativeDesigner.py`: `_DOE_SOURCE_BY_MODE` 추가 + `_process_vibration_scenario` 신설<br>- `Examples/vibration_source/scenario_A_single_cap.json` (신규)<br>- `Examples/vibration_source/scenario_explicit_factors.json` (신규)<br>- `tests/test_vibration_registry.py`, `tests/test_step_config_builder_vib.py` (신규) |
| LOC | ~450 (VibrationSource 250 + Builder 90 + Runner 12 + TemplateManager 10 + Designer 60 + examples 30) |
| 검증 단위 | - **단위:** Registry 등록/중복(`RuntimeError`)/미등록(`ValueError` + Registered 목록); Builder 골든 텍스트 1건 (per_cap 출력 ↔ 수기 작성 step_config); direction validator (`"W"` reject); inline curve materialize (빈 points reject)<br>- **통합:** scenario_A → `parse_vibration_source` → `build_vibration_load_block` → 문자열 검증 (KooMeshModifier 키워드 7개 모두 포함)<br>- **E2E:** scenario_A → CumulativeDesigner → runner_config.json → CumulativeScenarioRunner → KooMeshModifier → LS-DYNA 1 step 완주, exit 0, d3plot 생성 확인 |
| 의존성 | — (인프라 Phase) |
| 예상 시간 | 2-3일 |

**Goal-Driven 통과 기준:** Example A 시뮬레이션이 `error 0` + d3plot 산출, 기존 DROP Test_005 회귀 byte-diff 0.

---

## P2. circuit_group ⭐ 사용자 핵심

사용자가 명시적으로 요구한 **"회로별 일괄 진동"** 기능. P1 Registry 위에 source parser 1개를 등록하는 것이 본질이며, 코드 변경은 최소. 핵심은 components 평탄화 로직(회로 → 개별 part_id 리스트)과 `amplitude_distribution` 매핑.

| 항목 | 값 |
|---|---|
| 목적 | 회로 단위로 part 그룹을 묶어 일괄 가진 (사용자 명시 요구) — 회로 내부 모든 part가 동일 base_curve를 amplitude_distribution 비율로 받음 |
| 수정 파일 (file:function) | - `Runner/VibrationSource.py`: `@register_vibration_source("circuit_group") _parse_circuit_group` 함수 1개 (~50 LOC)<br>- `Runner/VibrationSource.py:resolve_components` 헬퍼 (inline `components` dict 평탄화; `components_ref` hook은 미구현 — `NotImplementedError`로 P6 예약)<br>- `Runner/VibrationSource.py:_apply_distribution` (`mass_proportional` / `volume_proportional` / `equal` → `RelativeMode` 매핑)<br>- `Examples/vibration_source/scenario_B_circuit.json` (신규)<br>- `tests/test_circuit_group.py` (신규): inline 평탄화 / distribution 매핑 / 빈 회로 reject |
| LOC | ~120 (parser 50 + resolver 30 + distribution 20 + example/test 20) |
| 검증 단위 | - **단위:** `resolve_components({"circuit_A": {"parts":[101,102]}, "circuit_B": {"parts":[201,202,203]}})` → `[101,102,201,202,203]` (순서 보존); `_apply_distribution("equal", 5)` → `[(101,1.0),(102,1.0),...]`; 알 수 없는 distribution → `ValueError`<br>- **통합:** scenario_B → `_parse_circuit_group` → `VibrationLoadSpec.part_list` 정확<br>- **E2E:** 회로 2개 합산 5 part 대상 LS-DYNA 1 step 완주, `*SET_PART_LIST` 카드에 5개 part_id 모두 출력 확인 |
| 의존성 | P1 (Registry / Builder / Runner 분기 필요) |
| 예상 시간 | 1-2일 |

**Goal-Driven 통과 기준:** Example B 시뮬레이션 완주 + 회로 합산 part_id 리스트가 KooMeshModifier 입력 .k 파일에 정확히 출력.

---

## P3. cap_combination + DOE 폭발 가드 (semaphore)

`itertools.combinations(N, k)` 기반 조합 DOE 생성. C(50,5)=2.1M 같은 무방어 폭발을 막기 위해 `environment.max_doe_count` 가드와 prepare 단계 dry-run preview를 필수로 한다. 기존 stage-out token-file semaphore 패턴(`db04ce1` 커밋)을 sbatch submit throttle에도 재사용.

| 항목 | 값 |
|---|---|
| 목적 | Cap pool에서 k개씩 조합으로 DOE 생성 + DOE 폭발(C(n,k)) 사전 차단 + prepare 단계 사용자 확인 |
| 수정 파일 (file:function) | - `Runner/VibrationSource.py`: `@register_vibration_source("cap_combination") _parse_cap_combination` (itertools 사용, ~60 LOC)<br>- `Runner/VibrationSource.py:_check_doe_count_guard(candidate_n, ctx)` — `ctx.max_doe_count` 초과 시 `DOEExplosionError` + `--yes` override 안내<br>- `Runner/CumulativeDesigner.py:prepare` 단계: candidate count 계산 → `[VibrationSource] cap_combination: C(n,k) = X cases` stdout preview → 임계 초과 시 `input('Proceed? [y/N]')` (TTY) 또는 `--yes` 필요<br>- `Runner/SlurmSubmit.py` (신규, ~80 LOC): `submit_with_throttle(cmd, *, token_dir, max_concurrent, dry_run)` — stage-out과 동일한 token-file semaphore 패턴 재사용<br>- `Examples/vibration_source/scenario_C_combination.json` (신규, max_doe_count=200 예시)<br>- `tests/test_doe_guard.py`: 정확히 == max(통과), max+1(reject), C(50,5) abort, `--yes` override |
| LOC | ~250 (parser 60 + guard 30 + designer dry-run 40 + SlurmSubmit 80 + example/test 40) |
| 검증 단위 | - **단위:** `_check_doe_count_guard(100, ctx(max=100))` 통과; `_check_doe_count_guard(101, ctx(max=100))` → `DOEExplosionError`; `comb(50,5) == 2118760` 명시 검증<br>- **통합:** scenario_C (n=10, k=3, max=200) → prepare 시 stdout에 `C(10,3)=120` + `120 <= max(200) → proceed` 표시; scenario_C2 (n=50, k=5) → abort + exit 2<br>- **E2E:** scenario_C 120 DOE submit dry-run (`--dry-run`) → 120 slurm script 생성 확인 (실제 제출 X)<br>- **회귀:** stage-out semaphore 동작 변화 없음 (기존 token_dir 방식 유지) |
| 의존성 | P1 (Registry), P2 (preview 메시지 패턴 정렬) |
| 예상 시간 | 2-3일 |

**Goal-Driven 통과 기준:** Example C dry-run 120 DOE 생성 + max_doe_count abort 동작, 기존 DROP submit throttle 회귀 0.

---

## P4. VolumeProportional + size-based 노출

이미 `KooVibrationLoad.py:33-34` 및 KooMeshModifier 측에 구현되어 있는 `RelativeMode=VolumeProportional` / `mass_proportional` 옵션을 scenario.json layer에 명시적으로 노출. **KooMeshModifier 변경 0줄**, scenario schema와 parser만 추가.

| 항목 | 값 |
|---|---|
| 목적 | 이미 KooMeshModifier에 있는 부피/질량 비례 분포 옵션을 scenario.json에서 직접 지정 가능하게 노출 (현재는 P2 `circuit_group`의 distribution 키워드로만 간접 접근) |
| 수정 파일 (file:function) | - `Runner/VibrationSource.py:_parse_per_cap`, `_parse_circuit_group`, `_parse_explicit_factors`에 `relative_mode` 옵션 추가 (`"Explicit" | "VolumeProportional" | "MassProportional"`)<br>- `Runner/StepConfigBuilder.py:build_vibration_load_block`은 P1에서 이미 `relative_mode` 인자 받음 → schema/parser layer만 노출<br>- `Runner/VibrationSource.py:_RELATIVE_MODE_ALIASES` dict: `"volume_proportional"→"VolumeProportional"`, `"mass_proportional"→"MassProportional"` (사용자 친화 alias)<br>- `Examples/vibration_source/scenario_D_volume_proportional.json` (신규)<br>- `tests/test_relative_mode.py`: 3개 mode 모두 step_config 텍스트 검증, 알 수 없는 alias → `ValueError` |
| LOC | ~80 (parser 옵션 추가 30 + alias dict 10 + example/test 40) |
| 검증 단위 | - **단위:** 3개 relative_mode 각각 `build_vibration_load_block` 출력에 `RelativeMode,VolumeProportional` 등 정확 행 포함; alias 정규화 통과<br>- **통합:** scenario_D → step_config → KooMeshModifier 파싱 통과 (`*VolumeProportional` 키워드 인식)<br>- **E2E:** scenario_D LS-DYNA 1 step 완주, d3plot 응답 진폭이 part 부피에 비례하는지 가시 확인 (질적 검증, 단위 통과를 1차 기준으로) |
| 의존성 | P1 (Builder), P2 (distribution 키워드와 일관성) |
| 예상 시간 | 1일 |

**Goal-Driven 통과 기준:** scenario_D 완주 + step_config 텍스트에 RelativeMode 행 정확 출력 + 회귀 0.

---

## P5. (옵션) Node/Segment 하중 — KooMeshModifier 확장

본 Phase는 **KooMeshModifier 내부 확장이 필요**하므로 별도 PR로 분리한다. 기존 P1-P4는 Runner layer만 건드리며 KooMeshModifier 변경 0이지만, Node/Segment 단위 하중은 `KooVibrationLoad.py`에 `*LOAD_NODE_SET` / `*LOAD_SEGMENT_SET` 생성 경로를 신설해야 한다. SF(scale factor) 단위계도 Part body force 대비 재설계 필요 (Force/area vs Force/node vs Force/segment).

| 항목 | 값 |
|---|---|
| 목적 | 노드/세그먼트 단위 정밀 가진 — 본드와이어, 솔더 조인트 등 국소 부위 하중 |
| 수정 파일 (file:function) | - `occProject/Generators/KooCAEManager/KooVibrationLoad.py`: `LoadTarget` enum(`Part`/`NodeSet`/`SegmentSet`), `*LOAD_NODE_SET_POINT` 카드 생성, `*LOAD_SEGMENT_SET` 카드 생성 (~200 LOC)<br>- `Runner/VibrationSource.py`: `@register_vibration_source("node_set")`, `@register_vibration_source("segment_set")` (~80 LOC)<br>- `Runner/StepConfigBuilder.py`: `build_vibration_load_block`에 `target_kind` 인자 추가 + 분기 (~30 LOC)<br>- SF 단위계 재설계 문서 (`docs/vibration_massive/UNITS.md`) — Force/area, Force/node, Force/segment 환산표<br>- `tests/test_node_segment_load.py`<br>- KooMeshModifier 회귀 테스트 (DROP/IMPACT 변경 0 확인) |
| LOC | ~300 (KooVibrationLoad 200 + Runner 80 + Builder 30 — units 문서 별도) |
| 검증 단위 | - **단위:** node_set/segment_set 파서 출력 검증; KooVibrationLoad의 `*LOAD_NODE_SET_POINT` 카드 골든 텍스트<br>- **통합:** node_set scenario → KooMeshModifier → LS-DYNA 파싱 성공<br>- **E2E:** 본드와이어 모델에 NodeSet 하중 → LS-DYNA 완주 + 응답 검증<br>- **회귀:** P1-P4 Part body force 출력 byte-diff 0 (`LoadTarget=Part`가 default) |
| 의존성 | P1-P4 완료 + **KooMeshModifier 빌드 재실행 필요** (Nuitka 재컴파일) |
| 예상 시간 | 4-5일 (KooMeshModifier 확장 + Nuitka 빌드 + SF 단위계 검증) |

**Goal-Driven 통과 기준:** node_set / segment_set E2E 완주 + 기존 Part body force 경로 byte-exact 회귀 0 + KooMeshModifier 빌드 사이즈 증가 <5%.

**별도 PR 사유:** ① KooMeshModifier 재빌드 필요(~20분) ② SF 단위계 재설계는 사용자 검토 사이클 필요 ③ Runner layer 변경(P1-P4)과 의존 방향이 반대.

---

## P6. 회로 자동 제안 helper

`partname` 기반 휴리스틱으로 `suggested_circuits.json`을 자동 생성하는 보조 도구. **자동 적용 금지** — 항상 사용자 검토 후 scenario.json에 수동 반영해야 함. 임계 시나리오 수(50)를 넘어 `components_ref` 외부화 단계로 이행할 때 마이그레이션 진입로 역할.

| 항목 | 값 |
|---|---|
| 목적 | partname 휴리스틱(`Group_*` / `CIRCUIT_*` / `CAP_*` prefix)으로 회로 후보를 자동 추출, 사용자가 검토 후 components.yaml로 외부화 |
| 수정 파일 (file:function) | - `Runner/CircuitSuggester.py` (신규): `suggest_circuits_from_partnames(k_file_path) → dict`, `_extract_partnames`, `_group_by_prefix_heuristic` (`Group\s*(\w+)`, `CIRCUIT_(\w+)`, `CAP_(\w+)` 정규식 3종)<br>- CLI 명령: `KooChainRun suggest-circuits <model.k> --output suggested_circuits.json` (Runner CLI dispatcher에 1줄 등록)<br>- 사용자 검토 강제: 출력 파일 header에 `# REVIEW REQUIRED: do NOT use this file directly. Copy reviewed entries into your scenario.json.` 명시<br>- `tests/test_circuit_suggester.py`: 3가지 partname 패턴 입력 → 그룹 정확성, prefix 무관 part는 `ungrouped` 버킷, 빈 .k → 빈 dict |
| LOC | ~150 (suggester 80 + CLI 10 + heuristic 30 + test 30) |
| 검증 단위 | - **단위:** `Group A`, `Group B`, `CAP_PWR`, `Group A`(중복) → `{"Group_A":[...], "Group_B":[...], "CAP_PWR":[...]}` (중복 part_id 정렬+dedup)<br>- **통합:** 실제 battery_study .k 파일 입력 → 사람이 읽을 만한 회로 후보 출력<br>- **E2E:** 자동 생성된 `suggested_circuits.json`에서 회로 1개를 골라 사용자가 scenario.json에 수동 반영 → P2 circuit_group 경로 완주 |
| 의존성 | P2 (`circuit_group` resolver 완성 후에 의미 있음) |
| 예상 시간 | 1-2일 |

**Goal-Driven 통과 기준:** battery_study 실제 .k 파일 → 사람이 회로 5개 이상 식별 가능한 출력 + 자동 적용 경로가 코드에 존재하지 않음 (검토 강제).

---

## 전체 LOC 합산표

| Phase | 신규 LOC | 누적 LOC | 변경 파일 수 (신규+수정) | KooMeshModifier 변경 |
|---|---:|---:|---:|---|
| P1 | 450 | 450 | 신규 4 + 수정 3 | 0 |
| P2 | 120 | 570 | 신규 2 + 수정 1 | 0 |
| P3 | 250 | 820 | 신규 3 + 수정 2 | 0 |
| P4 | 80 | 900 | 신규 2 + 수정 2 | 0 |
| **P1~P4 소계 (메인 PR 후보)** | **~900** | **~900** | **신규 11 + 수정 8** | **0** |
| P5 (옵션, 별도 PR) | +300 | 1200 | 신규 3 + 수정 3 | **+200** |
| P6 (옵션, 별도 PR) | +150 | 1350 | 신규 2 + 수정 1 | 0 |

> **메인 PR 권장 범위:** P1~P4 (~900 LOC). 사용자 핵심 요구(`circuit_group` + `cap_combination` + `VolumeProportional`)를 모두 포함하면서 KooMeshModifier 재빌드를 회피.
> **간이 빠른 통합 옵션:** P1+P2만(~570 LOC, ~3-5일). 회로 단위 진동만 필요한 경우.

---

## 빌드 명령

| 변경 범위 | 빌드 명령 | 소요 시간 | 비고 |
|---|---|---|---|
| **P1~P4 (Runner layer만)** | `bash build_KooChainRun_python312.sh` | **~3분** | KooChainRun 단독 Nuitka 빌드, `/data/SmartTwinPreprocessor/lib/KooChainRun/` 자동 배포 |
| **P5 포함 (KooMeshModifier 확장)** | `bash build_without_automatedmodeller.sh` | **~20분** | KooMeshModifier + KooChainRun 동시 빌드, AutomatedModeller 기존 바이너리 보존 |
| 전체 재빌드 (필요 시) | `bash build_all_python312.sh` | ~50-70분 | AutomatedModeller까지 포함, P5 단독으로는 불요 |

**Nuitka 호환성 사전 점검 (P1 종료 시 필수):**

```bash
bash build_KooChainRun_python312.sh
find build_dist/lib/KooChainRun -name "VibrationSource*" | grep -q VibrationSource && echo OK
KooChainRun list-vibration-sources  # registry 등록 source 출력 (P1 종료 시 2개, P3 종료 시 4개)
KooChainRun validate-scenario Examples/vibration_source/scenario_A_single_cap.json
```

실패 시 fallback: `build_KooChainRun_python312.sh`에 `--include-package=jsonschema_specifications --include-package-data=jsonschema_specifications` 추가 (Verify1-Q5 대응).

---

## 회귀 검증 체크리스트 (기존 DROP/IMPACT E2E 회귀 X)

각 Phase 종료 시점에 아래 체크리스트를 통과해야 다음 Phase 진입 가능. **하나라도 실패 시 해당 Phase rollback 및 원인 분석 필수.**

| # | 검증 항목 | 방법 | 통과 기준 | Phase |
|---|---|---|---|---|
| R1 | DROP Test_005 (100 DOE) 회귀 | 신규 코드로 `runner_config.json` 재생성 → 기존 파일과 `diff` | byte-level diff 0 (total_doe < 1000) | P1, P3, P4 |
| R2 | IMPACT `scenario_part_center.json` 회귀 | 재생성 → diff | byte-level diff 0 | P1, P3, P4 |
| R3 | TemplateManager dispatch 회귀 | 기존 elif → mapping dict 변환 후 DROP/IMPACT/THERM 모든 입력 출력 비교 | bit-exact | P1 |
| R4 | CumulativeDesigner mode dispatch 회귀 | 기존 `if has_impact` → `_DOE_SOURCE_BY_MODE` lookup 후 DROP/IMPACT 출력 비교 | bit-exact | P1 |
| R5 | Nuitka 빌드 산출물 smoke | `find build_dist -name "VibrationSource*"` + `KooChainRun --version` | 산출물 존재 + 정상 실행 | P1, P3 |
| R6 | sbatch throttle 회귀 (기존 stage-out semaphore) | 기존 stage-out token_dir 패턴 변화 없음 확인 (P3 SlurmSubmit 신규 helper는 token_dir 동일 재사용) | token-file semaphore 동작 byte-exact | P3 |
| R7 | KooMeshModifier 호환성 (P1-P4) | scenario_A → step_config → KooMeshModifier 파싱 성공 + 알 수 없는 키워드 0 | 파싱 exit 0 | P1, P2, P4 |
| R8 | DROP/IMPACT body force 카드 byte-exact (P5) | P5 도입 후 `LoadTarget=Part` default 경로의 `*LOAD_BODY_PARTS_*` 카드 출력이 P4와 동일 | byte-diff 0 | P5 |
| R9 | jobs.json / simulation_index.json 스키마 회귀 | DROP Test_005 submit → 기존 jobs.json 키 셋과 비교 | 키 셋 동일 (값은 timestamp 차이 허용) | P3 |
| R10 | 빌드 사이즈 증가 한계 | `du -sb build_dist/lib/KooChainRun` 비교 | P1~P4 누적 <10%, P5 추가 <5% | P1, P5 |

**핵심 안전 장치:** R1, R2는 모든 Runner-layer Phase(P1, P3, P4)에서 반드시 통과. 실패 시 Registry/Builder/Dispatch 도입이 기존 경로를 손상시킨 것이므로 즉시 rollback. R6는 P3의 SlurmSubmit helper가 기존 token-file semaphore(`db04ce1`)와 호환되는지를 검증. R8은 P5에서만 적용되며, `LoadTarget=Part`가 default일 때 P4까지의 출력과 byte-exact 동일해야 함.

---

## Phase 진행 흐름도 (의존성)

```
P1 (인프라 + per_cap, explicit_factors)
 ├── P2 (circuit_group)    ⭐ 사용자 핵심
 │    ├── P4 (VolumeProportional 노출)
 │    └── P6 (회로 자동 제안 helper, 별도 PR)
 └── P3 (cap_combination + DOE 가드)
      └── P4 (선택적, P2/P3 어느 쪽 후에도 가능)

P5 (Node/Segment) ── 별도 PR, P1-P4 완료 후 시작
```

**권장 순서:** P1 → P2 → P3 → P4 → (PR 머지) → P5 → P6.
**최단 경로 (회로 진동만):** P1 → P2 → (PR 머지). ~5일.
**완전 경로 (조합 DOE 포함):** P1 → P2 → P3 → P4 → (PR 머지). ~8-10일.
