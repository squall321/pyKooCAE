# 취약조건 × 파트이동 DOE — 컨텍스트 노트

계획: [PLAN_RiskConditionPartDOE.md](PLAN_RiskConditionPartDOE.md)

---

## 2026-08-05 — 조사에서 확정된 사실 (설계 근거)

### KMM 은 한 옵션 파일에서 여러 `*Mode` 를 순서대로 실행한다

`KooMeshModifier.py` 의 `self.modeList` 는 리스트이고, `GenerateModifiedFile()` (L2938)
가 `for i in range(len(self.modeList))` 로 선언 순서대로 디스패치한다.
→ `PART_TRANSLATE,1` + `DROP_ATTITUDE,2` 를 한 파일에 넣으면 이동 후 회전이 적용된
단일 결과 .k 가 나온다. **별도 KMM 호출을 2회 하지 않아도 된다.**

### 누적 step≥2 는 이전 스텝의 `*_dti.k` 를 입력으로 쓴다

`CumulativeScenarioRunner.py` L1428-1448. `*_dti.k` 는 변형 형상 + 초기응력을 담고
있으므로 step1 에서 이동한 결과가 기하학적으로 승계된다.
→ **파트 이동은 step1 에서만 적용해야 한다.** 매 스텝 적용하면 이동량이 누적되어
step N 에서 N배 이동한다. `apply_step` 기본값을 1 로 둔 이유.

### 리스크 수확 알고리즘은 이미 있다

`Runner/AdaptiveOrientation.py`:

- `harvest(test_dir)` — deep_report result.json 수집
- `compute_risk(samples, z_thr, yield_factor)` — per-part z-score + yield 절대비 병행
- `hotspots(samples)` — is_hot 을 risk 내림차순

파일 헤더에 "risk 계산 자체는 방향 없이도 동작한다" 고 명시돼 있어 **IMPACT 위치에도
그대로 쓸 수 있다.** 새 알고리즘을 만들지 않고 CLI 래퍼만 붙인다.

---

## 설계 결정과 이유

### 왜 `TRANSLATION_DOE` 를 안 쓰고 새 모드를 만드는가

`GenerateTranslationDOE` 는 샘플마다 `_TranslationDOE_{i}.k` 를 쓴 뒤
`part.Translate(-transX, -transY, -transZ)` 로 **원복**한다. 즉 모드가 끝나면
메모리 상의 모델은 이동 전 상태다. 뒤따르는 `DROP_ATTITUDE` 는 이동되지 않은 모델을
회전시키게 되어 체이닝이 성립하지 않는다.

또 파일을 N개 방출하는 형태라 "DOE 케이스 1건 = 결과 1개" 라는 KooChainRun 의
스텝 모델과 맞지 않는다. 필요한 것은 **단발·적용 후 유지** 세만틱이다.

### 왜 `TRANSFORM` 에 PID 필터를 추가하지 않는가

`TRANSFORM` 은 모델 전역 변환이고 기존 사용처가 있다. PID 필터를 넣는 것은 공용
코드 수정이라 회귀 위험이 있다 (memory: protect_existing). 신규 모드는 순수 가산이라
기존 경로에 회귀 표면이 0 이다.

### 왜 취약조건을 scenario.json 에서 자동 해석하지 않는가

`"from_run": "<경로>"` 로 prepare 시점에 자동 추출하는 방식도 가능하지만 배제했다.

1. 500잡을 던지기 전에 어떤 조건이 뽑혔는지 **사람이 확인**해야 한다
2. 이전 run 디렉토리가 바뀌면 같은 scenario.json 이 다른 결과를 내 **재현성**이 깨진다
3. harvest 를 분리하면 사용자가 목록을 손으로 편집(추가/제외)할 수 있다

→ `harvest` 커맨드가 JSON 파일을 방출하고, scenario.json 은 그 **파일을 참조**한다.

### 왜 `part_doe` 가 scenario 레벨인가

`angle_source` / `position_source` / `tolerance` 가 모두 `scenarios[N]` 안에 있다
(`CumulativeDesigner._process_drop_scenario(scenario_cfg, ...)`). 일관성을 위해
`part_doe` 도 형제로 둔다. 최상위가 아니다.

### doe_index 곱셈 규칙

`doe_index = cond_idx * n_moves + move_idx` (0-based).
`doe_count = len(set(doe_index))` 로 계산되므로 **인덱스가 겹치면 케이스가 조용히
사라진다.** 실제로 tolerance 생성기에서 같은 결함으로 80건 중 70건이 소실된 적이
있다 (2026-08-04 수정, 전역 `doe_seq` 도입). 이번에도 곱셈 결과가 조밀한 0..N-1
연속열이 되는지 반드시 단위 테스트로 확인한다.

---

## 구현 중 발견한 기존 결함 2건 (곱셈 재인덱싱의 blast radius 안이라 함께 수정)

### (1) tolerance doe_index off-by-one — 커밋 ef89f9c

`save_runner_config` 는 `doe_angles` 키를 `doe_index + 1` 로 만들고 러너는
`range(1, doe_count+1)` 을 조회한다. tolerance 3종 생성기가 `doe_index` 를
1-based 로 발급해 키가 **2..N+1** 이 되어 있었다.

- DOE 1 → 키 "1" 없음 → `_condition_to_euler` 폴백(근사 각도)로 실행
- DOE N+1 → `doe_count` 범위 밖이라 영영 실행되지 않음

원래 코드도 `i+1` 이었으므로 2026-08-04 의 `doe_seq` 수정이 만든 것이 아니라
그 이전부터 있던 결함이다. append 후 증가로 바꿔 0-based 정렬.

### (2) DOE 고유 각도 소실 — 커밋 c88e005 에 포함

`_process_drop_scenario` 가 각 DOE 의 고유 각도(`doe_roll/pitch/yaw`)를 버리고
`angle_sequence[i]` 로 덮어썼다. `angle_sequence` 는 `all_base_angles`(각 base
그룹의 **첫** DOE)에서 나오는데, 그룹의 2번째 이후 DOE 는 이름 매칭에 실패해
`current_base_idx` 가 0 으로 떨어졌다.

실측(base 6 × lhs 3 = 18케이스): **고유 (roll,pitch) 조합이 6개뿐**이고 13건이
첫 base 각도 `F1_Back_DOE001` 로 중복. 즉 tolerance 산포가 사실상 작동하지
않고 있었다.

수정: `base_order` 를 enumerate 해 `current_base_idx = base_idx` 로 확정하고,
`local_base_angles[base_idx]` 에 이 DOE 자신의 각도를 꽂아 넣는다.
tolerance/파트이동이 없으면 그룹당 DOE 가 1개라 예전과 완전히 동일 → 회귀 0.

→ 18/18 고유 확인. 회귀 스위트 15건은 tolerance 를 쓰지 않아 바이트 동일 유지.

---

## 실증 기록

### PART_TRANSLATE 체이닝 (Examples/MinimumModel.k, 28293 노드)

- 단독 실행: PID 3 의 1188 노드만 정확히 (1.5,-2.5,0.75) 이동, 27105 노드 불변
- 체이닝(PART_TRANSLATE + DROP_ATTITUDE): 결과 31176 노드 중 1188 개만
  `|d|=3.010` 변위. `|(1.5,-2.5,0.75)| = 3.0104` 와 정확히 일치 —
  회전이 크기를 보존하므로 이동이 회전 **전에** 올바르게 적용됐다는 증거.
  나머지 29988 노드는 변위 정확히 0.

### e2e (harvest → explicit.file → prepare → 옵션 txt)

sphere 12건 중 의도적 고응력 2건이 HOT 상위 → 4각도 방출 →
`doe_count = 4 × 5 = 20`, 인덱스 1..20 조밀 → 옵션 txt 에
`PART_TRANSLATE,1` + `DROP_ATTITUDE,2` 및 이동량이 카탈로그와 일치.

---

## KooD3plotReader PR 이 필요한가 — 불필요로 판단

`sphere_report.json` 은 `results_summary[].angle{roll,pitch,yaw}` 와
`parts{pid:{peak_stress}}` 를, `impact_report.json` 은
`results[]{pos_id,x,y,part_id,peak_stress}` 를 이미 담고 있다.
`RiskHarvester` 가 이 두 파일을 직접 읽으므로 리포터 쪽 수정 없이 동작한다.

리포터를 고쳐야 하는 경우는 HTML 리포트 안에서 사람이 조건을 골라 바로
내보내고 싶을 때뿐이다. 그건 편의 기능이지 이 워크플로우의 전제가 아니다.

---

## 취약 판정을 옮길 파트 기준으로 (2026-08-06)

사용자 제안. 기본 `risk = max_p(...)` 는 **전 파트 최대**라, PID 12 를 옮길
계획인데 무관한 파트가 뜨거운 조건이 뽑힌다. 옮길 파트로 필터하면 μ·s 도 그
파트 분포로 계산돼 선정이 정확해진다.

`compute_risk` 에 `parts_filter` 인자가 **이미 있었는데** 내가 안 쓰고 있었다.
배선만 하면 되는 일이었다.

- `--parts 12,15` — 손으로 지정
- `--from-scenario scenario.json` — `part_doe.parts[].pid` / `cases[].moves[].pid` 자동 추출

가드: 지정 파트가 리포트에 하나도 없으면 `compute_risk` 가 전 조건 risk=0 을
조용히 반환해 "위험한 조건 없음"으로 오독된다 → `ValueError` 로 끊는다.
일부만 없으면 경고 후 제외.

검증: 파트1 은 Run_003/004, 파트2 는 Run_008/009 에서만 고응력인 모사 리포트로
`--parts 1` → Run_003/004, `--parts 2` → Run_008/009 로 정확히 갈리는 것 확인.
파트 미지정 시 기존과 동일(둘 다 섞여 나옴).

---

## 🔴 절대 기준(항복비)이 통합 리포트 경로에서 비작동

`compute_risk` 는 상대(z-score) + 절대(a = σ/yield) 두 기준을 병행하는데,
**통합 리포트가 파트별 항복강도를 직렬화하지 않는다.**

| 소스 | 상대(z) | 절대(항복비) | 근거 |
|---|---|---|---|
| `sphere_report.json` | 작동 | **비작동** | `yield_stress` 가 CLI 스칼라로 안전율 계산에만 쓰이고 `results_summary[].parts` 에 미포함 |
| `impact_report.json` | 작동 | **비작동** | `PartInfo` 에 `part_id/part_name/group/footprint/z_range` 만 있음 |
| `result.json` 스캔 | 작동 | 작동 | deep_report 가 `stress_limit` 을 파트별로 담음 |

→ 통합 리포트로 뽑으면 `a_p = 0` 이 되어 상대 기준만으로 판정된다.

**내 검증이 이걸 못 걸렀다.** 모사 리포트를 만들 때 `stress_limit: 250.0` 을
직접 넣어서 두 기준이 다 도는 것처럼 보였다(로그의 `z=2.23, a=1.6`).
합성 데이터로 검증할 때는 **실제 산출물에 그 필드가 있는지 먼저 확인**해야 한다.

영향: 전 조건이 고르게 위험하면 평균이 같이 올라가 z 가 안 튀어 아무것도 안
뽑힌다. `--hot-only` 도 "항복 초과"가 아니라 "평균보다 1.5σ 높음"이 된다.

해결안 (미구현)

1. `harvest --yield <값>` / `--yield-by-part 3:350,7:120` — 우리 쪽만 고치면 됨
2. KooD3plotReader PR — 두 리포트가 파트별 항복강도를 JSON 에 싣도록 (근본)

→ **KooD3plotReader PR 이 실제로 필요해지는 지점은 여기다.** 조건 선정 자체가
아니라 항복강도 전달이다 (위 "PR 불필요" 판단은 조건 선정에 한정한 것).

---

## 미해결 / 결정 대기

- `tolerance` 와 `part_doe` 병용 시 3중 곱 — 허용하되 경고만? 금지? (현재안: 허용 + 경고)
- `harvest` 의 기본 선별 기준을 `--top N` 으로 할지 `--hot-only` 로 할지 (현재안: 둘 다 제공, top 우선)
- 실클러스터 e2e (실제 잡 제출까지) 미실시
