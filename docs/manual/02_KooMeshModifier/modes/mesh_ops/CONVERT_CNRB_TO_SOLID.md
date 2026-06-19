# KooMeshModifier 모드: CONVERT_CNRB_TO_SOLID

## 1. 목적/개요

`CONVERT_CNRB_TO_SOLID` 모드는 모델 내의 **CNRB(`*CONSTRAINED_NODAL_RIGID_BODY`)를 탄성 solid hexa 실린더 파트로 치환**하는 모드이다.

볼트/핀/리벳 등을 강체(CNRB)로 단순화한 모델에서, 강체로 인한 비물리적 강성/접촉 거동을 제거하고 실제 탄성 거동을 부여하고자 할 때 사용한다. 처리 결과는 다음과 같다.

- CNRB가 묶고 있던 노드 집합으로부터 원통 형상을 추정하여, O-grid(butterfly) 단면을 갖는 hexa 실린더 메시를 생성한다.
- 생성한 실린더 파트에 `*SECTION_SOLID` + `*MAT_ELASTIC`를 부여한다.
- 기존(원래 CNRB가 묶던) 노드와 새 실린더를 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`로 연결한다.
- 원본 CNRB 카드와 그 중심(PNODE) 노드를 삭제한다.

근거: 입력 트리거 등록부 `KooMeshModifier.py:291-293`, dispatch 분기 `KooMeshModifier.py:2837-2839`, 옵션 파서 `KooMeshModifier.py:821-873`, 핸들러 `KooMeshModifier.py:2565-2567`, 실제 동작 `KooDynaAdvancedModification.py:5224-5568`.

## 2. 입력 옵션·인자

`CONVERT_CNRB_TO_SOLID`는 두 부분으로 입력된다. (1) `*Mode` 블록에서 모드를 등록하고, (2) `**ConvertCNRBtoSolid` 옵션 블록에서 재료/형상 파라미터를 지정한다.

### 2-1. `*Mode` 등록 (모드 활성화)

| 항목 | 값 | 설명 | 근거 |
|------|-----|------|------|
| 키워드 토큰 | `convert_cnrb_to_solid` | `*Mode` 블록 내 한 줄로 작성 (대소문자 무시) | `KooMeshModifier.py:291` |
| `<modeID>` | 정수 | 토큰 다음 콤마로 구분된 모드 ID. 옵션 블록과 매칭됨 | `KooMeshModifier.py:292-293` |

### 2-2. `**ConvertCNRBtoSolid` 옵션 블록

옵션 라인 형식은 `키,값` 이며, 매칭은 키 문자열의 부분일치(대소문자 무시)로 이루어진다. `**end` 또는 빈 줄을 만나면 블록이 종료된다(`KooMeshModifier.py:835-841`).

| 옵션 | 형식 | 기본값 | 설명 | 근거 |
|------|------|--------|------|------|
| 블록 헤더 | `**ConvertCNRBtoSolid,<modeID>` | — | `<modeID>`는 `*Mode`에서 등록한 ID와 일치해야 함 | `KooMeshModifier.py:821-823` |
| `ALL` | `ALL,<True\|False>` | `True` | 대상 선택 방식. `True`면 모델 내 모든 CNRB를 변환. `false`(문자열 비교, 대소문자 무시)일 때만 `False` | `KooMeshModifier.py:825, 842-844`; `KooDynaAdvancedModification.py:5244-5247` |
| `CNRB_IDs` | `CNRB_IDs,<id1>,<id2>,...` | `[]` | `ALL,False`일 때 변환할 CNRB ID 목록 | `KooMeshModifier.py:845-847`; `KooDynaAdvancedModification.py:5247` |
| `E` | `E,<value>` | `200000000000` | 생성 실린더 `*MAT_ELASTIC`의 영률 | `KooMeshModifier.py:827, 848-850`; `KooDynaAdvancedModification.py:5234, 5255` |
| `PR` | `PR,<value>` | `0.3` | 푸아송비 | `KooMeshModifier.py:828, 851-853`; `KooDynaAdvancedModification.py:5234` |
| `RHO` | `RHO,<value>` | `7850` | 밀도 | `KooMeshModifier.py:829, 854-856`; `KooDynaAdvancedModification.py:5235` |
| `RadiusScale` | `RadiusScale,<value>` | `0.999` | 추정 반경에 곱하는 스케일. 실린더 외경을 원본보다 약간 작게 만들어 tied 접촉 관통을 방지 | `KooMeshModifier.py:830, 857-859`; `KooDynaAdvancedModification.py:5236, 5441` |
| `NumCircumNodes` | `NumCircumNodes,<int>` | `0` | 원주 방향 노드 수. `0`이면 자동 결정(레벨별 최대 노드 수와 6 중 큰 값). 내부적으로 4의 배수로 반올림됨 | `KooMeshModifier.py:831, 860-862`; `KooDynaAdvancedModification.py:5237, 5377-5380, 5401-5403` |
| `AxisDirection` | `AxisDirection,<Auto\|X\|Y\|Z>` | `Auto` | 실린더 축 방향. `Auto`는 노드 분포 PCA(최대 분산 방향) 사용 | `KooMeshModifier.py:832, 863-865`; `KooDynaAdvancedModification.py:5238, 5299-5311` |
| `InnerRadiusRatio` | `InnerRadiusRatio,<value>` | `0.3` | O-grid 코어(중앙 사각 격자) 크기 비율 | `KooMeshModifier.py:833, 866-868`; `KooDynaAdvancedModification.py:5239, 5405` |
| `ZTolerance` | `ZTolerance,<value>` | `0.01` | 축 방향(Z) 레벨 그룹화 허용오차(mm) | `KooMeshModifier.py:834, 869-871`; `KooDynaAdvancedModification.py:5240, 5325` |

추가 참고: `RTolerance`(반경 방향 클러스터링 허용오차, 기본 `0.5`)는 옵션 파서에서 별도로 노출되지 않으나 동작 코드에서 `option.get("RTolerance", 0.5)`로 읽는다(`KooDynaAdvancedModification.py:5342`). 즉 `**ConvertCNRBtoSolid` 블록 파서(`KooMeshModifier.py:821-873`)에는 `RTolerance` 분기가 없어 사실상 항상 기본값 `0.5`가 적용된다(확인 필요 — 파서 측 노출 누락으로 보임).

## 3. 사용 예제

`Examples/meshmodifier/ConvertCNRBtoSolid/` 와 `Examples/meshmodifier/ConvertCNRBtoSolid_NonUniform/` 에 실제 예제가 있다.

### 3-1. 입력 step_config (균일 실린더 예제)

`Examples/meshmodifier/ConvertCNRBtoSolid/step_config.txt` 발췌:

```
*Inputfile
sample_cnrb.k
*Mode
CONVERT_CNRB_TO_SOLID,1
**ConvertCNRBtoSolid,1
ALL,True
E,200000000000
PR,0.3
RHO,7850
RadiusScale,0.999
NumCircumNodes,8
AxisDirection,Auto
InnerRadiusRatio,0.3
ZTolerance,0.1
**EndConvertCNRBtoSolid
*End
```

`NonUniform` 예제(`ConvertCNRBtoSolid_NonUniform/step_config.txt`)는 거의 동일하나 `NumCircumNodes,0`(자동), `ZTolerance,0.5` 로 설정되어 있다.

> 참고: 블록 종료 토큰을 `**EndConvertCNRBtoSolid`로 적어도 파서는 `**end` 부분일치로 종료를 인식한다(`KooMeshModifier.py:840`).

### 3-2. 원본 .k의 CNRB 블록 (변환 대상)

`Examples/meshmodifier/ConvertCNRBtoSolid/sample_cnrb.k:55-63` 발췌 — 노드셋(`*SET_NODE_LIST_TITLE`)과 이를 묶는 `*CONSTRAINED_NODAL_RIGID_BODY_TITLE`:

```
*SET_NODE_LIST_TITLE
CNRB_NodeSet
         1       0.0       0.0       0.0       0.0
         2         3         4         5         6         7         8         9
        10        11        12        13        14        15        16        17
        18        19        20        21        22        23        24        25
*CONSTRAINED_NODAL_RIGID_BODY_TITLE
                                                                       Bolt_CNRB
       200         0         1         1         0         0         0
```

### 3-3. 실행

`Examples/meshmodifier/ConvertCNRBtoSolid/run.sh` 발췌:

```bash
MESHMOD="${MESHMOD:-/data/SmartTwinPreprocessor/bin/KooMeshModifier}"
# ...
$MESHMOD step_config.txt
```

### 3-4. 출력

`*Inputfile`의 베이스 이름에 접미사 `_cnrb2solid`가 붙은 .k 파일이 생성된다(예: `sample_cnrb_cnrb2solid.k`). 접미사는 dispatch 단계에서 `additionalword += "_cnrb2solid"`로 결정된다(`KooMeshModifier.py:2839`).

출력 `sample_cnrb_cnrb2solid.k`에서 확인되는 결과 카드:

- `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID` (라인 7)
- `*MAT_ELASTIC_TITLE` (라인 16, 19), `*SECTION_SOLID_TITLE` (라인 26)
- 신규 `*PART` (라인 29, 50), tie 노드용 `*SET_NODE_LIST` (라인 156, 163)
- 원본의 `*CONSTRAINED_NODAL_RIGID_BODY_TITLE`는 출력에서 사라짐 (CNRB 삭제됨)

실행 로그 예시(`ConvertCNRBtoSolid/step_config.log:78-84`):

```
ConvertCNRBtoSolidCylinder: 1 CNRBs to convert
  CNRB 1: PID=200, 3 Z-levels, 8 circum nodes, axis=[0.000,0.000,1.000]
  Created 24 hexa elements (O-grid: 2x2 core + 8 outer per layer, 2 layers) for CNRB 1
  Created TIED_SURFACE_TO_SURFACE_OFFSET (CID=1)
  Removed CNRB 1
  Removed center node 1
ConvertCNRBtoSolidCylinder completed
```

> 주의: 위 로그는 이전 버전에서 생성된 것으로, 현재 코드의 hexa 개수 출력 문구는 `Total: {n} hexa elements for CNRB {id}` 형식이다(`KooDynaAdvancedModification.py:5545`). 동작 의미(생성 개수)는 동일하다.

## 4. 동작 원리

핸들러 `GenerateConvertCNRBtoSolid`(`KooMeshModifier.py:2565-2567`)는 옵션 dict를 그대로 `advancedModification.ConvertCNRBtoSolidCylinder(option)`에 전달한다. 핵심 로직(`KooDynaAdvancedModification.py:5224-5568`)은 다음 순서로 동작한다.

1. **대상 CNRB 수집** — `ALL=True`면 전체 CNRB, 아니면 `CNRB_IDs` 목록을 대상으로 한다 (`KooDynaAdvancedModification.py:5242-5251`). 대상이 없으면 종료.
2. **공통 section/material 생성** — `*SECTION_SOLID`(`CreateSolidSection`)와 `*MAT_ELASTIC`(`CreateElasticMaterial`, `RHO/E/PR` 사용)를 1회 생성해 모든 변환에 공유 (`KooDynaAdvancedModification.py:5254-5255`).
3. **노드 수집 / 중심 결정** — CNRB의 노드셋(`nsid`)에서 노드를 모은다. 노드 3개 미만이면 skip (`5269-5278`). 중심은 PNODE가 있으면 그 좌표, 없으면 노드 무게중심 (`5280-5296`).
4. **축 방향 결정** — `Auto`면 노드 분포 공분산의 최대 고유값 방향(PCA)을 축으로, `X/Y/Z`면 해당 단위벡터를 사용 (`5298-5311`).
5. **원통좌표 변환** — 각 노드를 (R, θ, Z_local)로 변환 (`5313-5322`).
6. **Z 레벨 그룹화** — `ZTolerance`로 라운딩하여 동일 Z 레벨로 묶는다. 레벨 2개 미만이면 skip (`5324-5339`).
7. **R 클러스터링 / 실린더 체인 구성** — `RTolerance`로 동일 반경 클러스터를 만들고, 유사 R끼리 묶어 다중 동심 실린더 체인을 구성한다. Z레벨 2개 미만 체인은 제거 (`5341-5374`).
8. **원주 노드 수 결정** — `NumCircumNodes=0`이면 레벨별 최대 노드 수와 6 중 큰 값으로 자동 결정, 이후 4의 배수로 반올림 (`5376-5403`).
9. **신규 Part 생성** — CNRB의 PID를 재사용해 새 solid 파트 `CNRB_<id>_Solid` 생성 (`5418-5426`).
10. **O-grid hexa 메시 생성** — `InnerRadiusRatio`로 코어 사각 격자를 만들고, `R_max·RadiusScale`까지 동심 링을 쌓아 코어+링 hexa 요소를 Z 레이어별로 생성한다. 각 Z 구간의 로컬 R 한도를 넘는 링은 생략(비균일 형상 대응) (`5390-5545`).
11. **Tied 접촉 생성** — 원본 노드들을 노드셋으로 묶어 새 실린더 파트와 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`로 연결 (`5547-5556`).
12. **CNRB/중심노드 삭제** — 원본 CNRB 카드 삭제, PNODE가 있으면 중심 노드도 삭제 (`5558-5565`).
13. 최종적으로 `SyncronizeMaxID()` 호출 후 종료 (`5567-5568`). 이후 dispatch에서 `WriteModifiedFile(additionalword)`로 결과 .k를 기록한다 (`KooMeshModifier.py:2837-2839, 2886-2888`).

## 5. 주의사항·한계

- **대상 형상**: 본 모드는 CNRB 노드 분포가 **원통(실린더) 형상**임을 가정한다. 단면을 O-grid(butterfly) hexa로 메싱하므로 비원통/판상 분포에는 적합하지 않다 (`KooDynaAdvancedModification.py:5313-5403`).
- **skip 조건**: 노드 3개 미만(`5276`), Z 레벨 2개 미만(`5337`), 유효 실린더 체인 없음(`5372`)일 경우 해당 CNRB는 변환되지 않고 건너뛴다. 노드셋(`nsid`)을 찾지 못해도 skip된다(`5270-5272`).
- **재료/단면 공유**: 모든 변환 대상이 동일한 `*MAT_ELASTIC`/`*SECTION_SOLID`를 공유한다. CNRB별 개별 재료 지정은 불가 (`5254-5255`).
- **PID 재사용**: 신규 실린더 파트가 원본 CNRB의 PID를 그대로 사용한다(`5418-5426`). 동일 PID가 다른 용도로 쓰이고 있다면 충돌 가능 (확인 필요).
- **`RTolerance` 미노출**: 위 2절 참고. 옵션 블록 파서에 분기가 없어 입력으로 조정할 수 없으며 항상 `0.5`가 적용된다 (확인 필요).
- **단위계**: `ZTolerance`/`RadiusScale` 등은 모델 단위(주석상 mm 가정)를 따른다. 단위가 다르면 그룹화/스케일이 부적절해질 수 있다 (`5240`).
- **`E` 키 파싱**: `E` 옵션은 `line.lower().startswith("e,")`로 매칭한다(`KooMeshModifier.py:848`). 다른 옵션 키가 `e,`로 시작하지 않으므로 충돌은 없으나, 키 표기는 정확히 `E,`로 시작해야 한다.

## 6. 개발 현황

**구현됨.**

근거:
- 입력 트리거가 `modeList`에 정식 등록되어 있고(`KooMeshModifier.py:291-293`), dispatch 분기(`KooMeshModifier.py:2837-2839`)와 핸들러(`KooMeshModifier.py:2565-2567`)가 존재한다.
- 옵션 파서(`KooMeshModifier.py:821-873`)와 핵심 동작 로직(`KooDynaAdvancedModification.py:5224-5568`)이 모두 완전히 구현되어 있다.
- 동작 가능한 예제 2종(`Examples/meshmodifier/ConvertCNRBtoSolid`, `ConvertCNRBtoSolid_NonUniform`)이 입력(`sample_*.k`, `step_config.txt`), 출력(`*_cnrb2solid.k`), 실행 로그(`step_config.log`)와 함께 존재하며, 로그상 변환이 정상 완료(`ConvertCNRBtoSolidCylinder completed`)됨을 확인했다.
