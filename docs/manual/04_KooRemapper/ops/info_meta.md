# KooRemapper ops — 정보·메타(info · modelmeta · version)

모델을 변형하지 않고 메시/모델의 상태만 읽어내는 조회·추출 op 묶음이다. `info` 는 메시 요약을 콘솔에 출력하고, `modelmeta` 는 파트별 기하·재료·연결성을 JSON으로 추출하며, `version` 은 바이너리 버전을 출력한다.

## 실행 방법

KooRemapper 는 `SmartTwinPreprocessor.sif` 안 `/opt/kooremapper/bin/KooRemapper` C++ CLI(v1.8.0)다. 두 가지 경로로 실행한다.

- 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> ...`
- 체인 실행: KooChainRun 의 `REMAP` 스텝. `params.op` 에 op 이름을 지정하고, positional op 는 `params.argv`(리스트), yaml-config op 는 `params.config`(dict)로 인자를 넘긴다.

이 페이지의 세 op 는 모두 정보 출력·메타 추출용이며, `info` 와 `version` 은 체인 산출 파일(다음 스텝으로 넘길 .k 등)을 만들지 않는다. `modelmeta` 만 JSON 파일을 남긴다.

---

## info

### 용도

LS-DYNA K-파일의 메시 정보를 분석해 콘솔에 출력한다. 노드/요소/파트 개수, 바운딩 박스와 크기, 메시 유효성, 요소 품질(Jacobian)을 한눈에 확인하는 조회용 op다.

### 호출 형태

바이너리 help 의 `Usage:` 줄과 정확히 일치한다.

```
Usage: KooRemapper info <mesh_file>
```

`<mesh_file>` 는 positional 인자다.

| 인자 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `<mesh_file>` | positional 1 | 필수 | 분석할 LS-DYNA K-파일 경로 |

### 출력 정보

| 항목 | 설명 |
|---|---|
| 파일명 | 입력 K-파일 이름 |
| 노드 수 | 전체 노드 개수 |
| 요소 수 | 전체 요소 개수 |
| 파트 수 | 파트 개수 |
| 바운딩 박스 | X/Y/Z 최소~최대 범위 |
| 크기 | X/Y/Z 방향 길이 |
| 검증 결과 | 메시 유효성 검사 |
| 요소 품질 | Jacobian 최소/최대, 음수 Jacobian 요소 수 |

### 예제

직접 실행이다.

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper info clip_board.k
```

REMAP 스텝(positional op)이다. `params.argv` 에 리스트로 넘긴다.

```yaml
params:
  op: info
  argv: ["clip_board.k"]
```

### 개발 현황

정본 매뉴얼에 수록된 op다(호출 형태·출력 항목 근거 존재). 체인 산출 파일은 없다.

---

## modelmeta

> 정본 매뉴얼에는 `modelmeta` 전용 섹션이 없다. 아래 내용은 바이너리 help 동작과 예제 YAML(`examples/modelmeta/modelmeta.yaml`)만을 근거로 기술했으며, 그 밖의 세부는 '확인 필요' 로 표기한다.

### 용도

K-파일을 읽어 파트별 기하 메트릭·재료·연결성(connectivity)을 구조화된 JSON 으로 추출한다. 모델을 변형하지 않는 읽기 전용 메타 추출 op다. `*CONTACT` 카드가 없어도 기하학적으로 닿는 파트쌍을 탐지할 수 있다.

### 호출 형태

`modelmeta` 는 config YAML 파일 경로를 positional 인자로 받는 yaml-config op다.

```
KooRemapper modelmeta <config.yaml>
```

근거: `modelmeta` 는 별도의 `Usage:` help 줄을 출력하지 않는다. `--help` 를 붙여 실행하면 이를 config 파일 경로로 간주해 `[ERROR] [modelmeta] Cannot open config: --help` 로 실패하는데, 이 동작이 "첫 positional 인자 = config 파일" 임을 보여준다. 실제 호출 형태는 예제 YAML 헤더의 `KooRemapper modelmeta examples/modelmeta/modelmeta.yaml` 을 따른다.

### config YAML 인자

`examples/modelmeta/modelmeta.yaml` 기준이다.

| 키 | 예제값 / 기본 | 설명 |
|---|---|---|
| `model` | (필수) | 분석 대상 K-파일. 읽기 전용, `*INCLUDE` 1단계 추적 |
| `detect` | `true`(예제값) | `*CONTACT` 없이도 기하학적으로 닿는 파트쌍 탐지 |
| `gap_tol` | `0.2`(예제값) | 탐지 갭 허용치(모델 길이 단위) |
| `output` | 생략 시 `model` 이름에서 유도 → `<model>_modelmeta.json` | 출력 JSON 이름 |
| `material_db` | 생략 시 실행파일 옆 번들 DB | 재료 DB 경로 |
| `db_mid_fallback` | `false`(opt-in) | MID 일치 폴백. 로컬 MID 충돌 위험이 있어 명시적으로 켤 때만 사용 |

`detect`/`gap_tol` 의 값은 예제에 설정된 값이며, 실제 내장 기본값 여부는 확인 필요. 그 밖의 키 존재 여부도 확인 필요.

### 출력

`output` 을 생략하면 `model` 이름에서 유도한 `<model>_modelmeta.json` 파일로 파트별 기하·재료·connectivity 메타가 기록된다. JSON 스키마의 상세 필드 구성은 확인 필요.

### 예제

직접 실행이다.

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper modelmeta examples/modelmeta/modelmeta.yaml
```

config YAML(`examples/modelmeta/modelmeta.yaml`) 예시다.

```yaml
model: clip_board.k        # 분석 대상 (읽기 전용, *INCLUDE 1단계 추적)
detect: true               # *CONTACT 없이도 기하학적으로 닿는 파트쌍 탐지
gap_tol: 0.2               # 탐지 갭 허용치 (모델 길이 단위)
# output: my_model         # 생략 시 model 이름에서 유도 → <model>_modelmeta.json
# material_db: /path/material_db.json   # 생략 시 실행파일 옆 번들 DB
# db_mid_fallback: false   # MID 일치 폴백 (로컬 MID 충돌 위험 — opt-in)
```

REMAP 스텝(yaml-config op)이다. `params.config` 에 위 YAML 키들을 dict 로 넘긴다.

```yaml
params:
  op: modelmeta
  config:
    model: clip_board.k
    detect: true
    gap_tol: 0.2
```

### 주의사항

- 정본에 없는 op 이므로, 위 인자표·동작은 help 동작과 단일 예제에서 유추한 것이다. 확인되지 않은 옵션·기본값은 실제 실행으로 검증할 것.
- `db_mid_fallback` 은 로컬 MID 충돌 위험 때문에 opt-in 이다. 근거 없이 켜지 말 것.
- `model` 은 읽기 전용으로 다루며 `*INCLUDE` 는 1단계까지만 추적한다.

### 개발 현황

바이너리(v1.8.0)에 op 로 존재하며(help 실행 시 `[modelmeta]` 태그로 응답), 동작 예제 YAML 이 제공된다. 정본 매뉴얼 섹션은 미작성 상태다.

---

## version

### 용도

KooRemapper 바이너리의 버전을 콘솔에 출력한다.

### 호출 형태

```
KooRemapper version
```

인자 없음.

### 예제

```bash
apptainer exec SmartTwinPreprocessor.sif \
  /opt/kooremapper/bin/KooRemapper version
```

출력 버전은 `1.8.0` 이다(help 배너 기준). REMAP 스텝으로 쓸 경우 `params.op: version` 이며, 정보 출력용이라 체인 산출 파일은 없다.

### 개발 현황

정본 매뉴얼에 전용 섹션은 없으나 버전 문자열은 바이너리 배너로 확인된다(v1.8.0).
