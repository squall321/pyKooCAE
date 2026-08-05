# 취약조건 × 파트이동 DOE — scenario.json 포맷 결정 및 구현 계획

작성: 2026-08-05 / 대상: KooChainRun (Designer + Runner) + KooMeshModifier

---

## 1. 목표 워크플로우

```
① 전각도 낙하(500방향) 또는 전위치 부분충격(10×10 그리드)  실행
        ↓
② 결과에서 취약 조건 추출  (risk z-score / yield 비)
        ↓
③ 취약 조건 N개 × 파트이동 DOE M개  = N×M 시뮬레이션 자동 실행
```

②→③ 을 손작업 없이 잇는 것이 이 작업의 목적이다.

---

## 2. 설계 원칙

| 원칙 | 적용 |
|---|---|
| 기존 구조 불변 | `part_doe` 블록이 없으면 기존과 **바이트 동일** 출력 |
| 축의 직교화 | 조건(각도/위치) 축과 파트이동 축을 분리, 곱연산으로 결합 |
| 감사 가능성 | 취약조건 추출은 **별도 커맨드 → 파일** (자동 해석 아님). 500잡 던지기 전 눈으로 확인 가능 |
| 가산만 | 공용 코드 수정 대신 신규 모드/신규 카탈로그 추가 |

---

## 3. 결정된 scenario.json 포맷

### 3.1 축 1-A — 낙하 각도 열거 (`angle_source.source_type = "explicit"`)

```json
"angle_source": {
  "source_type": "explicit",
  "explicit": {
    "angles": [
      { "name": "C1_Back_Right_Top", "roll": 45.0, "pitch": -45.0, "yaw": 0.0 },
      { "name": "R0412",             "roll": 31.7, "pitch":  12.4, "yaw": 0.0 }
    ]
  }
}
```

파일 참조형 (수확 결과를 그대로 물림 — 500개를 scenario.json 에 인라인하지 않기 위함):

```json
"angle_source": {
  "source_type": "explicit",
  "explicit": { "file": "risk_angles.json" }
}
```

- `risk_angles.json` = `{ "angles": [ {name, roll, pitch, yaw}, ... ] }`
- `name` 생략 시 `A0001` 자동 부여, `yaw` 생략 시 0.0
- `angles` 와 `file` 동시 지정 시 에러 (모호성 차단)
- 기존 `cuboid_geometry.only` (F1~F6/E01~E12/C1~C8 이름 지정) 는 **그대로 유지** — 정자세 26방향만 짧게 쓸 때 편함

### 3.2 축 1-B — 충격 위치 열거 (`position_source.manual` 확장)

```json
"position_source": {
  "source_type": "manual",
  "manual": {
    "positions": [
      { "name": "P_003_005", "x": 12.5, "y": 40.0 },
      { "name": "P_007_002", "x": 30.0, "y": 55.0 }
    ]
  }
}
```

- 기존 `[[x, y], ...]` 배열 형식 **그대로 동작** (하위호환). 이름 없으면 `P_0001` 자동
- 파일 참조: `"manual": { "file": "risk_positions.json" }`, 내용 `{ "positions": [...] }`

### 3.3 축 2 — 파트 이동 DOE (신규 `part_doe`, scenario 레벨)

`scenarios[N]` 안, `angle_source`/`position_source`/`tolerance` 와 형제.

**(a) LHS 샘플링**

```json
"part_doe": {
  "enabled": true,
  "apply_step": 1,
  "sampling": { "method": "lhs", "num_samples": 20, "seed": 42 },
  "parts": [
    { "pid": 12, "dx": [-0.5, 0.5], "dy": [-0.3, 0.3], "dz": [0.0, 0.0] },
    { "pid": 15, "dx": [-0.2, 0.2] }
  ]
}
```

**(b) 균등 격자**

```json
"part_doe": {
  "enabled": true,
  "sampling": { "method": "grid", "nx": 5, "ny": 5, "nz": 1 },
  "parts": [ { "pid": 12, "dx": [-0.5, 0.5], "dy": [-0.3, 0.3] } ]
}
```
총 조합 = nx·ny·nz.

**(c) 명시 열거**

```json
"part_doe": {
  "enabled": true,
  "sampling": { "method": "explicit" },
  "cases": [
    { "name": "M001", "moves": [ { "pid": 12, "dx":  0.30, "dy": -0.10, "dz": 0.0 } ] },
    { "name": "M002", "moves": [ { "pid": 12, "dx": -0.40, "dy":  0.20, "dz": 0.0 },
                                 { "pid": 15, "dx":  0.05 } ] }
  ]
}
```

공통 규약
- 좌표계 = 모델 글로벌 XYZ, 단위 = 모델 단위 그대로 (환산 없음)
- 생략된 축은 0.0 고정 (`dz` 없으면 Z 이동 없음)
- `name` 생략 → `M0001` 자동
- `apply_step` 기본값 **1**. 누적 step≥2 는 이전 스텝 `*_dti.k`(이미 이동된 변형 형상)를 물려받으므로 재적용 금지
- 여러 파트를 동시에 다른 양만큼 이동 가능 (`parts`/`moves` 가 리스트)

### 3.4 결합 규칙

```
doe_count = (조건 수) × (파트이동 케이스 수)
doe_index = cond_idx * n_moves + move_idx        # 0-based
condition  = "{조건명}__{이동명}"                 # 예: C1_Back_Right_Top__M003
```

- 조건 = 각도(DROP) 또는 위치(IMPACT) 또는 thermal_conditions(THERM)
- `part_doe` 없음 / `enabled:false` → 이동 케이스 1개(무이동)로 취급 → **기존 출력과 완전 동일**
- `tolerance` 와 병용 시 3중 곱(조건×tolerance×이동)이 되므로 총 케이스 수를 prepare 시 로그로 경고

### 3.5 runner_config.json 출력 — 신규 카탈로그 `doe_part_moves`

`doe_positions` / `doe_vibrations` 와 동일한 `1-based DOE key → step key` 구조.

```json
"doe_part_moves": {
  "1": { "1": { "move_name": "M001",
                "moves": [ { "pid": 12, "dx": 0.3, "dy": -0.1, "dz": 0.0 } ] } },
  "2": { "1": { "move_name": "M002", "moves": [ ... ] } }
}
```

- step key 는 `apply_step` 에 해당하는 것만 존재. 나머지 스텝은 조회 실패 → 이동 미적용(정상)

---

## 4. KMM 배선 — 신규 단발 모드 `PART_TRANSLATE`

Runner 가 생성하는 옵션 txt 에 기존 모드 **앞에** 삽입:

```
*Mode
PART_TRANSLATE,1
DROP_ATTITUDE,2
**PartTranslate,1
Translate,12,0.3,-0.1,0.0
Translate,15,0.05,0.0,0.0
**EndPartTranslate
**DropAttitude,2
...
**EndDropAttitude
*End
```

**왜 기존 모드를 안 쓰는가**

| 후보 | 배제 사유 |
|---|---|
| `TRANSLATION_DOE` | 샘플마다 파일을 쓰고 **역이동으로 원복**한다. 뒤따르는 `DROP_ATTITUDE` 에 이동이 전달되지 않아 체이닝 불가 |
| `PART_LOCATION_DOE` | 마스크/장애물 기반 유효영역 검증이 목적. 3축 동시 이동 불가, 역시 N파일 방출형 |
| `TRANSFORM` 에 PID 필터 추가 | 기존 전역 변환 기능의 **공용 코드 수정** — 회귀 위험. 가산 원칙 위배 |

→ "적용 후 유지" 단발 모드가 신규로 필요. `KooPart.Translate()` 가 이미 있어 구현은 소규모.

---

## 5. 취약조건 수확 — `KooChainRun harvest`

```bash
KooChainRun harvest --test-dir <이전 테스트 디렉토리> \
                    --top 10 \
                    [--z-thr 1.5] [--yield-factor 1.0] [--hot-only] \
                    --out risk_angles.json
```

- `AdaptiveOrientation.harvest()` → `compute_risk()` → `hotspots()` **재사용** (신규 알고리즘 없음)
- runner_config 의 `doe_angles`/`doe_positions` 존재 여부로 DROP/IMPACT 자동 판별
- 출력 = `{"angles":[...]}` 또는 `{"positions":[...]}` → 그대로 `explicit.file` / `manual.file` 에 물림
- 왜 scenario.json 안에서 자동 해석(`"from_run": ...`)하지 않는가: 500잡을 던지기 전에 **어떤 조건이 뽑혔는지 사람이 확인**할 수 있어야 하고, 파일로 고정해야 재현성이 보장된다

---

## 6. 구현 범위

| # | 파일 | 변경 |
|---|---|---|
| 1 | `Runner/AngleSourceParser.py` | `EXPLICIT` enum + `ExplicitAnglesConfig` + `parse_explicit_angles()` |
| 2 | `Runner/ImpactPositionSource.py` | `parse_manual()` 이 dict/`file` 수용 (배열 하위호환 유지) |
| 3 | `Runner/PartMoveDOE.py` **(신규)** | `parse_part_doe()` — lhs/grid/explicit → `PartMoveCase` 리스트 |
| 4 | `Runner/CumulativeDesigner.py` | 조건×이동 곱, `doe_part_moves` 카탈로그 방출 |
| 5 | `Runner/CumulativeScenarioRunner.py` | `_get_doe_part_moves()` + 옵션 txt 에 `PART_TRANSLATE` 블록 삽입 |
| 6 | `occProject/Generators/KooMeshModifier.py` | `PART_TRANSLATE` 파서/디스패치 (가산 2-hunk) |
| 7 | `occProject/Generators/KooDynaAdvancedModification.py` | `PartTranslate()` 본체 |
| 8 | `KooChainRun` | `harvest` 서브커맨드 |
| 9 | `docs/manual/01_KooChainRun/doe_methods/doe_methods.md` | 신규 3종 문서화 |

---

## 7. 검증 기준

1. `part_doe` 없는 기존 scenario.json → runner_config **바이트 동일** (회귀 0)
2. 조건 3 × 이동 4 → `doe_count == 12`, doe_index 충돌 0 (ToleranceDOEGenerator 의 doe_seq 결함 재발 방지)
3. `PART_TRANSLATE` + `DROP_ATTITUDE` 체이닝 → 이동+회전이 모두 반영된 단일 .k
4. 누적 2스텝: step1 만 이동, step2 는 `*_dti.k` 승계 (이중 이동 없음)
5. `harvest` → `explicit.file` → `prepare` 왕복 e2e
