# VIBRATION Massive 자동화 — Master PLAN

> **본 문서의 역할:** 전체 개요 + 7 zero-hardcode 결정 요약 + 요구사항 매트릭스만 유지.
> 상세 설계/단계/예제/미결사항은 형제 문서로 분리.

---

## 1. 목적

사용자 핵심 요구는 **"캡 / 코일 / 회로 단위 진동 시뮬레이션의 massive 자동화"** 이다.

| 항목 | 내용 |
|---|---|
| 대상 | PCB / 배터리 모듈의 캡(cap), 코일(coil), 회로(circuit) 그룹 단위 진동 가진 |
| 입력 | 회로별 part 그룹, 방향(X/Y/Z), 가진 곡선(inline 또는 CSV), 분포 모드 |
| 출력 | KooMeshModifier 호환 `*VibrationLoad` step_config + LS-DYNA 실행 + dynain |
| 규모 | 단일 캡 → 회로 일괄 → 캡 조합 DOE(최대 수백~수천 케이스) |
| 원칙 | **zero-hardcode** — 신규 source_type / curve / mode 추가 시 dispatcher / enum / schema 동시 수정 금지 |

기존 KooChainRun 의 DROP/IMPACT/THERM 모드와 **동등한 격으로 VIB 모드**를 추가하되,
IMPACT/THERM 의 인라인 f-string 안티패턴과 AngleSource/ImpactPosition 의 if/elif dispatcher 함정을 **회피**한다.

---

## 2. 현재 상태 요약

| 영역 | 있는 것 | 없는 것 |
|---|---|---|
| 솔버 layer | `KooVibrationLoad.py` (X/Y/Z 가진 + Force/Acceleration + RelativeMode + PartFactors/PartList) | — |
| 파서 | KooMeshModifier 의 `**VibrationLoad,1` 블록 파싱 | — |
| Runner mode enum | `SimulationMode.VIB` (이미 정의됨, line 34) | VIB 분기 미구현 (Runner/Designer/Template 전체) |
| StepConfig 빌더 | `build_drop_attitude_config()` (DROP 모범 사례) | `build_vibration_load_block()` |
| Designer dispatch | `if has_impact else` 2-way 분기 | mode → handler lookup dict |
| 회로 정의 어휘 | 시나리오에 인라인 (battery_study 사례) | components 표준 schema |
| Curve 입력 | KooVibrationLoad 가 inline `[(t,v),…]` 만 받음 | CSV / library / analytic 진입로 |
| DOE 생성 | DROP angle 100 DOE 검증됨 | cap_combination C(n,k) 폭주 가드 미존재 |
| Submit | sbatch 호출 site 7곳 분산 | 단일 throttle helper |

---

## 3. 사용자 요구사항 매트릭스

| # | 요구사항 | 현재 가능 | 본 PR 작업 | Phase |
|---|---|---|---|---|
| R1 | 단일 캡 단방향 가진 | 솔버 OK / Runner X | per_cap resolver + VIB elif 분기 | P1-P2 |
| R2 | 방향 X/Y/Z 선택 | OK (KooVibrationLoad) | scenario.json `direction` 필드 정형화 (F) | P2 |
| R3 | Force / Acceleration 선택 | OK | StepConfigBuilder 전달 | P2 |
| R4 | inline 곡선 입력 | OK | `base_curve.kind=inline` materializer | P2 |
| R5 | CSV 외부 곡선 라이브러리 | X | `base_curve.kind=csv` + `vibration_curves/` 폴더 규약 | P5 |
| R6 | **회로별 일괄 진동** (cap+coil 같은 회로) | X | `circuit_group` resolver + components inline | **P4** |
| R7 | 회로 정의 외부화 (yaml) | X | `components_ref` 진입로 (v1 inline + hook) | P4(예약) |
| R8 | 캡 조합 DOE (combinations) | X | `cap_combination` resolver + `max_doe_count` 가드 | P4 |
| R9 | 대규모 DOE (≥1000) | runner_config.json 단일 파일 | streaming writer + `doe_index.jsonl` | P3 |
| R10 | 대규모 sbatch 제출 throttle | site 분산 | `SlurmSubmit.submit_with_throttle()` 단일화 | P6 |

**핵심 사용자 시나리오(R6):** "PCB 회로 A 에 속한 cap 3개 + coil 2개를 한 번에 mass-proportional 로 Z 축 60Hz 가진" → P1+P2+P4 완료 시 동작.

---

## 4. Zero-Hardcode 7 결정 요약 (A~G)

| ID | 항목 | 채택안 | 핵심 이유 |
|---|---|---|---|
| **A** | `source_type` dispatch | **Registry + Decorator (정적 import)** | OCP 만족, 신규 source 추가 시 4곳→1곳, Nuitka 안전 |
| **B** | step_config 직렬화 | **`StepConfigBuilder.build_vibration_load_block()`** | DROP 모범 패턴 대칭, KooMeshModifier 키워드 단일 격리 |
| **C** | Mode dispatch (Template/Designer) | **기존 `SimulationMode.VIB` enum 재사용 + mapping dict** | enum line 34 이미 존재, elif chain → lookup 평탄화 |
| **D** | `source_type` 위치 (schema) | **resolver discriminator (open-set string)** | enum 폐쇄 회피, 검증은 registry lookup 에 위임 |
| **E** | components (회로) 정의 | **Inline 시작 + `components_ref` 필드 예약** | 시나리오 수 < 임계 → YAGNI, 마이그레이션 forward-compatible |
| **F** | Direction 표현 | **axis string "X/Y/Z" + 향후 vector hook** | `KooVibrationLoad:33-34` hard validation = 솔버 한계 반영 |
| **G** | base_curve 입력 | **discriminated union `{kind: inline\|csv}` v1** | 확장 hook 보존, sine/PSD/library 는 hook만 예약 |

**추가 결정 (verify 라운드 산출):**

| + | 항목 | 채택안 | 핵심 이유 |
|---|---|---|---|
| H | DOE explosion 가드 | `environment.max_doe_count` default 500 + `--yes` override | C(50,5)=2.1M 무방어 차단 |
| I | runner_config.json 스트리밍 | `step_template` 추출 + `doe_index.jsonl` per-line | 1000 DOE 임계, 100 DOE=56KB 선형 |
| J | sbatch throttle | `Runner/SlurmSubmit.submit_with_throttle()` helper 단일화 | 현재 7개 호출 site 분산 → 별도 PR |

---

## 5. 관련 문서 링크

| 파일 | 내용 |
|---|---|
| [`DESIGN.md`](./DESIGN.md) | 통합 아키텍처 다이어그램 (Layer 0~5), 7 결정의 코드 구조 / 시그니처 상세 |
| [`PHASES.md`](./PHASES.md) | P1~P6 단계별 구현 계획, 파일별 LOC, 검증 기준, 회귀 테스트 plan |
| [`EXAMPLES.md`](./EXAMPLES.md) | 3 예제 시나리오 (A 캡1 / B 회로 / C cap_combination DOE), components.yaml / CSV 포맷 |
| [`DECISIONS_OPEN.md`](./DECISIONS_OPEN.md) | 사용자 confirm 대기 Q1~Q9 (A/B/D/E/G 채택, max_doe_count default, threshold 등) |
| [`IMPLEMENTATION.md`](./IMPLEMENTATION.md) | 신규/수정 파일 정확 목록, 함수 시그니처, 외부 파일 schema (components.yaml / vibration_curves/) |

---

## 6. Goal-Driven 검증 기준

CLAUDE.md §4 (Goal-Driven Execution) 에 따라 본 PLAN 의 **성공 = 다음 검증 통과**.

| Phase | 검증 기준 (verify 가능 산출물) |
|---|---|
| P1 | `pytest tests/test_vibration_source.py` — 등록 0개 상태에서 미등록 source 호출 시 `Registered: []` 포함 ValueError. 빌더 골든 텍스트 비교. |
| P2 | Example A (캡1, R1+R2+R3+R4) → KooMeshModifier → LS-DYNA 1 step error 0 완주. |
| **P1+P2 종료 시점 = 사용자 핵심 요구 R1-R4 충족** | — |
| P3 | Test_005 DROP 100 DOE 회귀: 신구 `runner_config.json` byte-level diff = 0 (streaming threshold 미만). |
| **P4** | **Example B (회로 일괄, R6) → cap+coil 5개 part 동시 가진 시뮬레이션 완주 = 사용자 핵심 요구 충족**. Example C C(10,3)=120 정상 / C(50,5)=2.1M `max_doe_count` abort. |
| P5 | CSV curve (R5) 로드 → KooMeshModifier 입력 → LS-DYNA dt 변경 없이 통과. |
| P6 | Nuitka 빌드 산출물에 `VibrationSource.py` 포함 grep + `KooChainRun list-vibration-sources` smoke test 5개 출력. |

**최종 zero-hardcode 효과 측정 (확장성):**
신규 source 추가 시 — Before(if/elif): 5파일 ~60 LOC / After(Registry): 1파일 ~40 LOC / 기존 코드 touch = 0.

---

**다음 행동:** `DECISIONS_OPEN.md` 의 사용자 확정 사항 처리 후 P1 시작.
