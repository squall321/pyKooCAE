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

## 미해결 / 결정 대기

- `tolerance` 와 `part_doe` 병용 시 3중 곱 — 허용하되 경고만? 금지? (현재안: 허용 + 경고)
- `harvest` 의 기본 선별 기준을 `--top N` 으로 할지 `--hot-only` 로 할지 (현재안: 둘 다 제공, top 우선)
</content>
</invoke>
