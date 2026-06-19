# 네이밍 표준

## 1. 목적/개요

pyKooCAE에는 성격이 다른 두 가지 네이밍 표준이 있다.

1. **별칭(Alias) 패턴** — Runner가 실행하는 각 시뮬레이션 Run에 자동으로 붙이는 식별자.
   `{project}_CUM{n}_DOE{n}_S{n}_{mode}_{condition}` 형식이며 **코드로 생성·파싱이 구현되어 있다.**
   누적 DOE 시나리오의 수백~수천 개 Run을 사람이 읽을 수 있는 고유 이름으로 구분하고,
   `simulation_index.json`에서 Run 폴더(`Run_<run_id>`)·상태·이전 step을 역참조하는 키로 쓰인다.

2. **CAD/BOM/CAE 파트 이름 표준** — 기구 CAD 파트 이름을 5개 필드로 표준화해
   재질·요소타입·접촉·서브셋을 자동 추론하려는 설계안.
   문서(`docs/CAD_BOM_CAE_Automation_NamingStandard.html`)에만 존재하며 **현재 코드에는 미구현**이다(6절 참조).

이 두 표준은 적용 대상이 다르다. 별칭은 *Run(시뮬레이션 케이스)* 이름이고,
CAD/BOM 표준은 *모델 내부 파트* 이름이다.

---

## 2. 입력 옵션·인자 (표)

### 2.1 별칭 구성 필드 (CUM 패턴)

별칭은 5개 메타데이터 필드를 언더스코어로 연결한다. 각 필드의 출처(코드 근거)는 다음과 같다.

| 필드 | 형식 | 값 출처 | 근거 |
|------|------|---------|------|
| `project` | 문자열(자유) | `runner_config["project"]["name"]` | `CumulativeScenarioRunner.py:653` |
| `CUM{n}` | `CUM` + 3자리 0패딩 | `scenario["total_steps"]` (시나리오의 **총 step 수**) | `CumulativeScenarioRunner.py:654-655` |
| `DOE{n}` | `DOE` + 3자리 0패딩 | `doe_index` (1-based) | `CumulativeScenarioRunner.py:655` |
| `S{n}` | `S` + 3자리 0패딩 | `step` (1-based, 현재 step 번호) | `CumulativeScenarioRunner.py:655` |
| `mode` | 대문자 토큰 | `step_config["mode"]` (DROP, THERM, IMPACT, VIB 등) | `CumulativeScenarioRunner.py:893` |
| `condition` | 조건 식별자 | DOE별 `position_name`/`angle_name` 우선, 없으면 `step_config["condition"]` | `CumulativeScenarioRunner.py:897-905` |

> 주의: `CUM{n}`의 `n`은 "현재 step"이 아니라 **시나리오 전체 step 수**(`total_steps`)다.
> 현재 step 번호는 `S{n}` 필드에 들어간다. 예) 1-step 시나리오는 모든 Run이 `CUM001_..._S001`.

`condition` 필드의 실제 값은 모드별로 다른 소스를 쓴다(`CumulativeDesigner`가 `angle_name`에 통일 저장):

| 모드 계열 | condition 값 | 근거 |
|-----------|--------------|------|
| DROP(낙하 각도) | 각도 이름(`angle_name`), 예 `F1`, `P0001` | `CumulativeDesigner.py:701`, `714` |
| IMPACT(부분충격) | 위치 이름(`position_name`) | `CumulativeScenarioRunner.py:903`, `CumulativeDesigner.py:732` |
| THERM(열) | thermal 조건 식별자(`angle_name`에 보존) | `CumulativeDesigner.py:239` |
| VIBRATION | 케이스 이름(`case_name`, `angle_name`에 보존) | `CumulativeDesigner.py:483` |

### 2.2 SEQ 패턴 (순차 시나리오)

DOE 없이 순차 누적만 하는 경우 `SEQ` 패턴이 정의되어 있다(파서·생성기 존재).

| 형식 | 근거 |
|------|------|
| `{project}_SEQ{total_steps:03d}_S{step:03d}_{mode}_{condition}` | `AliasManager.py:73` (생성), `AliasManager.py:35` (파싱) |

### 2.3 별칭과 구분되는 식별자 — run_id

별칭과 별개로 각 Run에는 폴더용 `run_id`가 따로 생성된다(별칭은 사람이 읽는 이름, `run_id`는 충돌 방지용 고유 ID).

| 항목 | 형식 | 근거 |
|------|------|------|
| `run_id` | `{YYYYMMDD}_{HHMMSS}_{md5 6자리}` | `CumulativeScenarioRunner.py:647-649` |
| Run 폴더명 | `Run_{run_id}` | `CumulativeScenarioRunner.py:929` |

### 2.4 CAD/BOM/CAE 파트 이름 5필드 (설계안, 미구현)

근거: `docs/CAD_BOM_CAE_Automation_NamingStandard.html` "파트 이름 표준" 표.

| 필드 | 역할 | 규칙 | 예시 |
|------|------|------|------|
| Assembly | 제품/최상위 어셈블리 | 대문자, 약어 가능 | PHONE, TABLET, MODULE |
| SubAssy | BOM 중간 서브어셈블리 (서브셋 추출 단위) | 기능 그룹 단위 | HOUSING, BATTERY, DISPLAY |
| PartType | 파트의 기능/형상 역할 (요소타입 결정) | 사전 정의 어휘 | COVER, FRAME, POUCH, CELL |
| Material | 재질 코드 (MAT 카드 매핑) | 하이픈으로 등급 구분 | PC-ABS, AL6061, SUS304 |
| Instance | 동일 파트 복수 배치 | 3자리 숫자(001~) | 001, 002, 003 |

5필드를 언더스코어로 연결: `{Assembly}_{SubAssy}_{PartType}_{Material}_{Instance}`.

---

## 3. 사용 예제

### 3.1 실제 생성된 별칭 (simulation_index.json 발췌)

`/data/koopark/Test_010_Sequential_Quick/output/simulation_index.json` 에서 실제로 생성된 별칭
(1-step × DOE 10, IMPACT 위치 DOE):

```
Test_010_Sequential_Quick_CUM001_DOE001_S001_DROP_P0001 | run_id=20260419_090909_f5ed78 | mode=DROP | condition=P0001 | completed
Test_010_Sequential_Quick_CUM001_DOE002_S001_DROP_P0002 | run_id=20260419_091450_20bdb0 | mode=DROP | condition=P0002 | completed
Test_010_Sequential_Quick_CUM001_DOE003_S001_DROP_P0003 | run_id=20260419_092027_0de29e | mode=DROP | condition=P0003 | completed
```

분해:
- `project` = `Test_010_Sequential_Quick`
- `CUM001` = total_steps 1
- `DOE002` = 2번째 DOE
- `S001` = step 1
- `DROP` = 모드
- `P0002` = 조건(위치 이름)

### 3.2 runner_config.json 입력 → 별칭 (Test_010)

별칭을 만드는 입력 측 데이터(`runner_config.json`의 `scenario`):

```json
"project": { "name": "Test_010_Sequential_Quick" },
"scenario": {
  "type": "cumulative",
  "total_steps": 1,
  "doe_count": 10,
  "steps": [ { "step": 1, "mode": "DROP", "condition": "P0001", "params": {} } ],
  "doe_angles": {
    "1": { "1": { "angle_name": "P0001", "roll": 0.0, "pitch": -0.0, "yaw": 0.0 } },
    "2": { "1": { "angle_name": "P0002", "roll": 0.0, "pitch": -0.0, "yaw": 0.0 } }
  }
}
```

DOE 2 / step 1 처리 시:
`doe_angles["2"]["1"]["angle_name"]` = `"P0002"` 가 condition을 덮어써(`CumulativeScenarioRunner.py:904-905`)
→ `Test_010_Sequential_Quick_CUM001_DOE002_S001_DROP_P0002`.

### 3.3 별칭 조회 CLI (AliasManager)

`AliasManager.py:8-15` 의 usage 예:

```bash
# 별칭으로 Run 폴더/상태 조회
python AliasManager.py index.json "GalaxyS25_CUM006_DOE001_S003_DROP_F1"

# 한 DOE의 전체 누적 체인 조회 (step 순 정렬)
python AliasManager.py index.json "GalaxyS25_CUM006_DOE001_S003_DROP_F1" --chain

# 시나리오 요약
python AliasManager.py index.json --summary scenario_001
```

### 3.4 CAD/BOM 파트 이름 예시 (설계안)

근거: HTML "실제 제품 적용 예시 (스마트폰)" 표.

```
PHONE_HOUSING_COVER_PC-ABS_001   → 후면 커버 (Shell, MAT_024, exterior contact)
PHONE_DISPLAY_PANEL_OLED_001     → OLED 패널 (Shell, MAT_024, process target)
PHONE_BATTERY_CELL_JELLYROLL_001 → 젤리롤   (Solid, MAT_126, internal)
```

---

## 4. 동작 원리 (코드 근거)

### 4.1 별칭 생성

세 곳에서 **동일한 f-string**으로 생성한다(중복 정의 — 4.4 주의 참조):

- `CumulativeScenarioRunner.py:651-655`
  ```python
  def _generate_alias(self, doe_index, step, mode, condition):
      project = self.config["project"]["name"]
      total_steps = self.config["scenario"]["total_steps"]
      return f"{project}_CUM{total_steps:03d}_DOE{doe_index:03d}_S{step:03d}_{mode}_{condition}"
  ```
- `JobManager.py:105-123` — `JobManager._generate_alias()` (주석: "`CumulativeScenarioRunner._generate_alias()`와 동일한 패턴").
- `AliasManager.py:64-67` — `generate_alias_cumulative()` (모듈 함수).

condition 결정 로직은 `run_single_step()`에서 수행된다(`CumulativeScenarioRunner.py:890-907`):
`step_config["condition"]`을 기본값으로 두고, DOE별 `doe_positions`(IMPACT) → `doe_angles`(DROP/THERM/VIB) 순으로 실제 값을 덮어쓴 뒤 `_generate_alias()`에 넘긴다.

### 4.2 별칭 파싱

`AliasManager.parse_alias()` (`AliasManager.py:30-61`)가 정규식으로 역분해한다:

- CUM 패턴 (`AliasManager.py:33`): `r"(.+)_CUM(\d{3})_DOE(\d{3})_S(\d{3})_([A-Z]+)_(.+)"`
- SEQ 패턴 (`AliasManager.py:35`): `r"(.+)_SEQ(\d{3})_S(\d{3})_([A-Z]+)_(.+)"`

`mode` 그룹은 `[A-Z]+`(대문자만), `project`·`condition`은 `.+`(언더스코어 포함 가능)로 매칭한다.

### 4.3 별칭의 용도 — index 역참조 / 체인

`simulation_index.json`의 `scenarios[].runs`는 **별칭을 key**로 Run 정보(`run_id`, `folder`, `mode`, `condition`, `status`, `prev`)를 저장한다(`CumulativeScenarioRunner.py:934-936`, `990-992`).
`AliasManager`는 이를 읽어 `alias→run_id`, `run_id→alias` 역참조 테이블을 만들고(`AliasManager.py:85-97`),
`get_chain()`(`AliasManager.py:125-148`)은 같은 `project`+`scenario_type`+`total_steps`+`doe_index`를 공유하는 별칭들을 step 순으로 모아 한 DOE의 누적 체인을 복원한다.
이전 step 별칭은 `_get_prev_alias()`(`CumulativeScenarioRunner.py:657-676`)가 같은 규칙으로 생성한다.

### 4.4 CAD/BOM 표준 — 설계 문서상의 동작

HTML 문서는 파트 이름 5필드에서 다음을 자동 추론한다고 기술한다(매핑 테이블 절):
- PartType → 요소타입·메쉬 전략 (COVER/PANEL=Shell, CELL/BLOCK=Solid, SCREW=Beam/Rigid 등)
- Material → MAT 카드 (PC-ABS→MAT_024, GLASS→MAT_032 등)
- SubAssy → 서브셋 추출 필터 (`*_DISPLAY_*`, `*_BATTERY_*`)

단, 이 추론 로직은 코드에서 확인되지 않는다(6절).

---

## 5. 주의사항·한계

- **CUM 숫자 = total_steps**. 현재 step 번호가 아니다. 혼동 주의(2.1 표 주석).
- **별칭 생성기가 3곳에 중복 정의**되어 있다(`CumulativeScenarioRunner.py:655`, `JobManager.py:123`, `AliasManager.py:67`).
  포맷 변경 시 세 곳을 모두 고쳐야 정합성이 유지된다. (현재 세 f-string은 동일.)
- **condition에 언더스코어가 들어가면 파싱이 흔들릴 수 있다.** 파서의 condition 그룹은 `.+`(탐욕적)이라
  마지막 필드를 통째로 가져가므로 단일 condition은 안전하지만, mode 그룹은 `[A-Z]+`라서
  **mode는 반드시 대문자**여야 파싱된다(`AliasManager.py:33`). 소문자 모드는 파싱 실패(`parse_alias` → None).
- **별칭은 폴더명이 아니다.** 디스크 폴더는 `Run_{run_id}`이고, 별칭→폴더 매핑은 index를 거쳐야 한다(`AliasManager.get_folder`).
- **SEQ 패턴은 파서/생성기에는 있으나** 현재 `CumulativeDesigner`가 출력하는 `scenario.type`은 `"cumulative"`(CUM)다(`CumulativeDesigner.py:805`). SEQ 경로의 실제 사용처는 확인 필요.
- CAD/BOM 표준의 자동 추론(재질/요소/서브셋)은 **현재 파이프라인에 연결되어 있지 않다**(6절).

---

## 6. 개발 현황

| 항목 | 상태 | 근거 |
|------|------|------|
| CUM 별칭 생성·파싱·역참조 | **구현됨** | `CumulativeScenarioRunner.py:651-676`, `AliasManager.py:30-198`, `JobManager.py:105-123`; 실제 별칭 `/data/koopark/Test_010_Sequential_Quick/output/simulation_index.json` 에 존재 |
| SEQ 별칭 생성·파싱 | **부분구현** | 생성기/파서는 존재(`AliasManager.py:35`, `73`)하나 Designer 출력은 cumulative 고정(`CumulativeDesigner.py:805`), 실사용 경로 확인 필요 |
| CAD/BOM/CAE 파트 이름 표준 (5필드, 재질·요소·서브셋 자동 추론) | **계획** | 설계 문서(`docs/CAD_BOM_CAE_Automation_NamingStandard.html`)에만 존재. `subset_filter`, `bom_version`, `material_library`, `can_rigidify`, `SmartTwinCluster` 키워드를 코드 전역 grep 시 HTML 외 매칭 0건 — 코드 미구현 |

> **확인 필요**: SEQ 패턴을 실제로 생성하는 진입점(어떤 워크플로우가 `generate_alias_sequential`을 호출하는지)은 이번 조사 범위에서 발견하지 못했다.
