# DECISIONS_OPEN — VIBRATION 모드 사용자 확정 필요 사항

> **목적:** Final Plan §9 (다음 행동) + Design Decisions (7 채택안 A–G)을 사용자 confirm용 단일 시트로 통합. 답변 즉시 P1 인프라 구현 시작.
>
> **관련 문서:**
> - `/tmp/vib_workflow_outputs/final_plan.md` (§9 다음 행동)
> - `/tmp/vib_workflow_outputs/design_decisions.md` (7 결정 채택안 A–G)

---

## 1. 사용자 확정 필요 — 구현 시작 전 결정

### Q1. 캡/코일 인식 방법

| 옵션 | 설명 | 장점 | 단점 |
|---|---|---|---|
| A | partname `{Group}\` prefix 자동 제안 (예: `PKG\*`, `PCB\*` PID 후보) | 사용자 입력 최소 | naming convention 의존, false positive 가능 |
| B | scenario.json 에 PID list 명시 (`cap_pids: [4,5,6]`) | 명시적, 검증 쉬움 | 모델 변경 시 수동 갱신 |
| C | 외부 `components.json` 참조 | 재사용 가능, 분리 | indirection 비용 |
| **A+B** | **자동 제안 + 사용자 명시 확정 (추천)** | 휴리스틱 + 명시 안전망 | 두 경로 모두 구현 필요 |

**추천: A+B 병행** — heuristic으로 후보 제시, 사용자가 scenario에 final list 박는다.

### Q2. "Body 상하단면" 정의

| 옵션 | 설명 | 채택 가능성 |
|---|---|---|
| A | Z축 max/min face 자동 추출 (KooMeshModifier `GetExternalBoundary`) | P5 적합 |
| B | scenario 에 segment set ID 명시 | 즉시 가능, 수동 비용 |
| C | **Phase 1 미지원, body force 만 (단순화) — 추천** | YAGNI |

**추천: C → P5에서 A** — Phase 1은 body load 전용, segment 기반은 P5로 연기.

### Q3. 회로 정의 위치

| 옵션 | 설명 | Design Decision E와 정합 |
|---|---|---|
| A | **scenario.json inline `circuits` 블록 (추천)** | E 채택안과 일치 |
| B | 외부 `components.yaml` + scenario path 참조 | E의 `components_ref` hook |
| C | partname 3-level (`Group\Circuit\Name`) 명명 규칙 | naming 의존 — 기각 |

**추천: A** — 외부 ref hook은 schema에 예약(`components_ref` 필드)하되 P4까지 미구현. Decision E와 일치.

### Q4. "캡 크기" 정의

| 옵션 | 설명 | 구현 상태 |
|---|---|---|
| **A** | **solid element volume 합 (기존 `VolumeProportional`) — 추천** | **이미 구현, 검증됨** |
| B | surface area | 신규 코드 필요 |
| C | mass (= rho × V) | KooMeshModifier 변경 필요 |

**추천: A** — `KooVibrationLoad.py`의 `RelativeMode=VolumeProportional`이 이미 작동.

### Q5. base_curve 입력 형식

| Phase | 채택 옵션 | 근거 (Design Decision G) |
|---|---|---|
| P1 | **A (inline) + C (sine 함수식)** | G의 `kind: inline` 즉시 구현 |
| P2 | **B (CSV 경로) + D (library lookup)** | G의 `kind: csv` + `library_ref` hook |

**추천: A+C (P1) + B+D (P2)** — discriminated union `kind` 필드로 forward-compat.

### Q6. DOE 패턴 우선순위

| Pattern | Phase | 비용 | 비고 |
|---|---|---|---|
| `per_cap` (각 캡 1개씩, N=캡 수) | **P1** | 낮음 | 최소 source |
| `explicit_factors` (사용자 PartFactors 직접) | **P1** | 낮음 | escape hatch |
| `circuit_group` (회로 1개씩, N=회로 수) | **P2** | 중간 | ⭐ **핵심 — 회로 단위 진동 평가** |
| `cap_combination` (C(N,k)) | **P3** | 높음 (DOE explosion 가드 필수) | Verify2-Q1 적용 |
| `curve_library` (각 history 1 sim) | **P3+** | 낮음 (registry 1개 추가) | G 채택안 후속 |

**추천:**
- **P1** = `per_cap` + `explicit_factors`
- **P2** = `circuit_group`
- **P3+** = `cap_combination` + `curve_library`

---

## 2. Zero-Hardcode 채택안 Confirmation

`design_decisions.md` 7 채택안(A–G) 동의 여부.

| ID | 항목 | 채택안 | 동의 (체크) |
|---|---|---|---|
| A | source_type dispatch | **Registry + Decorator** (정적 import, Nuitka 안전) | [ ] 동의 / [ ] 변경 요청 |
| B | step_config 직렬화 | **`StepConfigBuilder.build_vibration_load_block()` 함수** (DROP 패턴 대칭) | [ ] 동의 / [ ] 변경 요청 |
| C | Mode dispatch | **기존 `SimulationMode` Enum + mapping table 유지** (`_FIRST_TEMPLATE_BY_MODE`) | [ ] 동의 / [ ] 변경 요청 |
| D | scenario.json source_type 위치 | **discriminator string (registry validation)** — schema enum 없음 | [ ] 동의 / [ ] 변경 요청 |
| E | components 정의 | **Inline 시작 + `components_ref` hook 예약** (YAGNI) | [ ] 동의 / [ ] 변경 요청 |
| F | Direction 표현 | **axis string "X/Y/Z"** (향후 vector hook `oneOf`) | [ ] 동의 / [ ] 변경 요청 |
| G | base_curve 입력 | **discriminated union (`kind: inline / csv / sine / library_lookup`)** | [ ] 동의 / [ ] 변경 요청 |

---

## 3. 추가 결정 필요 (workflow 식별 항목)

### Q7. amplitude 분배 방식 P1 범위

KooVibrationLoad RelativeMode 옵션 4가지를 P1에 모두 노출할지.

| Mode | 의미 | P1 포함 |
|---|---|---|
| `mass_proportional` | rho × V 비례 | P2 |
| `volume_proportional` | V 비례 (기존 KooMeshModifier `VolumeProportional`) | **P1** |
| `equal` | 모든 part 동일 amplitude | P2 |
| `custom_weights` (explicit) | scenario PartFactors 직접 | **P1** |

**추천: P1 = `explicit` (custom) + `volume_proportional`, P2 = `mass_proportional` + `equal`**
이유: P1에 explicit (가장 안전) + volume_proportional (기존 구현 재사용) 두 가지면 검증 가능, 회귀 없음.

### Q8. `max_doe_count` 가드 임계값

DOE explosion 가드(Verify2-Q1: C(50,5)=2.1M 무방어) 기본값.

| 옵션 | 설명 | 트레이드오프 |
|---|---|---|
| 기본값 500 (final_plan §1) | 5배 마진 (Test_005=100 기준) | 적정선, 가장 무난 |
| 환경변수 `KOOCHAIN_MAX_DOE` 정의 | 사용자별 설정 | 진입로 복잡화 |
| **scenario 명시 강제 (default 없음) — 추천** | fail-fast, 명시성 강제 | 사용자 매번 입력 부담 |

**추천: scenario `environment.max_doe_count` 명시 강제 + 미명시 시 prepare 단계에서 fail-fast.**
이유: 묵시적 기본값은 사고 원천. 명시 강제는 CLAUDE.md §1 "가정 명시" 부합.

대안: **softer 추천 = 기본 500 + WARN, scenario override 가능** — 사용자 부담 줄이려면 이쪽.

### Q9. KooMeshModifier 측 변경 — 별도 PR 분리?

| 범위 | 변경 대상 | 위치 |
|---|---|---|
| P1–P4 | Runner layer만 (`Runner/*.py`) | `pyKooCAE/Runner/` |
| P5 (node/segment 기반) | KooMeshModifier 본체 (KooVibrationLoad 확장) | `pyKooCAE/occProject/Generators/KooCAEManager/KooVibrationLoad.py` |

| 옵션 | 설명 |
|---|---|
| 별도 repo 분리 | 회귀 영향 최소화, but 두 repo 동기 비용 |
| **동일 repo + 별도 PR (추천)** | pyKooCAE monorepo 내부 통합, PR은 분리 |

**추천: pyKooCAE 안에 `occProject/Generators/KooCAEManager/KooVibrationLoad.py` 직접 수정하되 P5 시점에 별도 PR로 분리.**
이유: P1–P4 PR은 KooMeshModifier 변경 0줄 보장 (Design Decision E,F,G 모두 "KooMeshModifier 변경 없음" 명시). Nuitka 빌드 재구성도 P5 시점에만.

---

## 4. 답변 요청 형식

다음과 같이 답변 부탁드립니다 (한 줄씩):

```
Q1: A+B
Q2: C
Q3: A
Q4: A
Q5: A+C (P1), B+D (P2)
Q6: P1=per_cap+explicit, P2=circuit_group, P3+=combination+library
Q7: P1=explicit+volume_proportional, P2=mass+equal
Q8: scenario 명시 강제   (또는: 기본 500 + WARN)
Q9: 동일 repo, 별도 PR

Zero-Hardcode confirm: A-G 모두 동의
(또는: B만 변경 요청 — IMPACT/THERM도 같이 리팩토링 / D는 enum 사용 / ...)
```

---

## 5. 답변 후 진행

답변 받으면 즉시:

1. `Runner/VibrationSource.py` (Registry + Decorator, P1) 생성
2. `Runner/StepConfigBuilder.py` 에 `build_vibration_load_block()` 추가 (P1)
3. 단위 테스트 (`tests/test_vibration_registry.py`, `tests/test_step_config_builder_vib.py`) 작성
4. `pytest -q` 통과 후 P2 (per_cap + explicit_factors 등록) 진입

검증 기준 (Goal-Driven Execution, CLAUDE.md §4):
- P1 종료: 미등록 source_type 호출 → `Registered: []` 포함 ValueError, 빌더 골든 텍스트 비교 통과
- P2 종료: Example A (캡1) 시뮬레이션 LS-DYNA error 0 완주
- P3 종료: Test_005 (100 DOE) `runner_config.json` byte-level diff 0 (회귀)

**구현 시작 전 반드시 Q1–Q9 + Zero-Hardcode A–G confirm 필요.**
