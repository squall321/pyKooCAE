# KooMeshModifier 모드: CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM

> 근거 코드 (모두 `occProject/Generators/` 기준):
> - 모드 등록(트리거): `KooMeshModifier.py:288-290`
> - 옵션 블록 파서: `KooMeshModifier.py:776-819`
> - 디스패치 분기: `KooMeshModifier.py:2834-2836`
> - 핸들러: `KooMeshModifier.py:2561-2563` (`GenerateConstrainedNodalRigidBodyToBeam`)
> - 실제 로직: `KooCAEManager/KooDynaAdvancedModification.py:5192-5219` (`ConstrainedNodalRigidBodyToBeam`)
> - 코어 변환: `KooCAEManager/KooConstrained.py:719-762` (`ChangeConstrainedNodalRigidBodytoBeam`)

---

## 1. 목적 / 개요

기존 LS-DYNA 모델의 `*CONSTRAINED_NODAL_RIGID_BODY`(CNRB)를 **탄성 빔(beam) 요소 묶음으로 치환**하는 모드이다. CNRB가 강체 구속(완전 강체)으로 묶고 있던 절점 집합을, 각 절점에서 새로 만든 중심 절점으로 연결되는 탄성 빔(스포크/바퀴살 형태)으로 바꾼다.

동작 결과:

1. 대상 CNRB의 노드셋(`nsid`) 절점들의 **기하 중심(centroid)**에 새 중심 절점 1개 생성.
2. 노드셋의 각 절점마다 "중심 절점 ↔ 해당 절점"을 잇는 빔 요소 1개 생성(빔 방향 정의용 제3절점 자동 생성).
3. 새 빔들을 담는 새 Part + `*MAT_ELASTIC`(빔 재료) + `*SECTION_BEAM`(ELFORM 13) 생성.
4. 처리한 CNRB는 모델에서 삭제(`del`).

즉 강체 구속을 **강성을 가진(탄성) 빔 연결**로 완화(soft coupling)하는 변환이다.

근거: `KooConstrained.py:726-756`(중심 계산 + 빔 생성), `KooConstrained.py:758-761`(CNRB 삭제), `KooDynaAdvancedModification.py:5204-5214`(재료/단면/Part 생성).

---

## 2. 입력 옵션 · 인자 (표)

옵션 파일(`.txt`) 안에서 `**ConstrainedNodalRigidbodyToBeam,<modeID>` 블록으로 기술한다. 블록 종료는 빈 줄 또는 `**End` 마커이며, 토큰은 콤마 구분·대소문자 무시이다.

근거: 블록 파서 `KooMeshModifier.py:776-819`.

| 옵션 라인 | 인자 | 기본값 | 의미 | 코드 근거 |
|---|---|---|---|---|
| `*PID,all` 또는 `*PID,<id1>,<id2>,...` | `all` 또는 CNRB ID 목록 | `ALL=False`, 빈 목록 | 변환 대상 CNRB 지정. `all`이면 모델의 모든 CNRB 대상, 아니면 나열한 CNRB ID만 대상 | `KooMeshModifier.py:794-802` |
| `*E,<값>` | float | `1.0E6` | 빔 재료 영률(Young's modulus) | `KooMeshModifier.py:803-805` |
| `*PR,<값>` | float | `0.3` | 빔 재료 포아송비 | `KooMeshModifier.py:806-808` |
| `*RHO,<값>` | float | `7.0E-9` | 빔 재료 밀도 | `KooMeshModifier.py:809-811` |
| `*Width,<값>` | float | `1.0` | 빔 단면 폭(SECTION_BEAM TS1/TS2) | `KooMeshModifier.py:812-814` |
| `*Height,<값>` | float | `1.0` | 빔 단면 높이(SECTION_BEAM TT1/TT2) | `KooMeshModifier.py:815-817` |

내부 처리 매핑:

- `*PID,all` → `curOptions["ALL"]=True`. 실행 시 `ConstrainedNodalRigidBodyToBeam`가 모델의 전체 CNRB ID를 대상 딕셔너리에 채운다 (`KooDynaAdvancedModification.py:5201-5203`).
- `*PID,<id...>` → `curOptions["ALL"]=False` + `curOptions["CNRB"][id]=id` (각 ID 등록) (`KooMeshModifier.py:799-802`).
- `*Width` → 단면 `SetWidth`(TS1/TS2 동시 설정), `*Height` → `SetHeight`(TT1/TT2 동시 설정) (`KooSection.py:42-48`, 호출은 `KooDynaAdvancedModification.py:5208-5209`).
- 단면 ELFORM은 코드에서 **고정 13**으로 강제 설정 (`KooDynaAdvancedModification.py:5210`). 사용자가 옵션으로 바꿀 수 없음.

값은 `KooDynaFloat` / `KooDynaInt` 로 파싱되므로 파라미터 치환(예: `&param`) 표기를 그대로 쓸 수 있다 (`KooMeshModifier.py:801, 805` 등). 구체적 파라미터 문법은 별도 입력 포맷 문서 참조 — 본 모드 한정으로는 숫자/파라미터 둘 다 허용된다는 점만 확인됨. (확인 필요: 파라미터 표기 상세는 본 모드 코드 범위 밖)

---

## 3. 사용 예제

> 전용 예제 파일 없음. `Examples/` 및 저장소 전체 grep 결과 이 모드의 실제 입력 예제 `.k`/`.txt`는 존재하지 않음(확인: `grep -rln "constrainednodalrigidbodytobeam"` → 코드와 매뉴얼 문서만 매칭). 아래는 **파서 코드(`KooMeshModifier.py:776-819`)에서 역산한 최소 블록 형태**이며, 실측 예제가 아니다(확인 필요).

옵션 파일(`.txt`) 발췌 (코드 기반 재구성):

```
*Inputfile
MinimumModel.k

*Mode
constrained_nodal_rigidbody_to_beam,1
*End

**ConstrainedNodalRigidbodyToBeam,1
*PID,all
*E,1.0E6
*PR,0.3
*RHO,7.0E-9
*Width,1.0
*Height,1.0
**End
```

특정 CNRB만 대상으로 할 경우 `*PID` 라인만 교체:

```
*PID,1001,1002,1003
```

CLI 실행(다른 모드의 일반 호출 규약과 동일, `KooMeshModifier.py:3143` 기준):

```
KooMeshModifier <옵션파일.txt>
```

---

## 4. 동작 원리 (코드 근거)

### 4.1 디스패치 → 핸들러 → 로직

- `GenerateModifiedFile()` 루프에서 `mode == "CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM"` 분기 → `self.GenerateConstrainedNodalRigidBodyToBeam(modeid)` 호출, 출력 파일명에 `_crb` 접미사 추가 (`KooMeshModifier.py:2834-2836`).
- 핸들러는 해당 modeID의 옵션을 꺼내 `advancedModification.ConstrainedNodalRigidBodyToBeam(curOption)` 호출 (`KooMeshModifier.py:2561-2563`).

### 4.2 재료 / 단면 / Part 생성

`ConstrainedNodalRigidBodyToBeam`에서:

- 대상 결정: `allOption == True`면 `constrainedManager.constrainedNodalRigidbodyList`의 모든 ID를 대상에 추가 (`KooDynaAdvancedModification.py:5201-5203`).
- 빔 재료: `CreateElasticMaterial("BeamMaterial", rho, E, pr)` → `*MAT_ELASTIC` (`KooDynaAdvancedModification.py:5206`).
- 빔 단면: `CreateBeamSection("BeamSection")` 후 `SetWidth(w)`, `SetHeight(h)`, `SetElform(13)` (`KooDynaAdvancedModification.py:5207-5210`). 단면 카드는 `*SECTION_BEAM_TITLE` 로 출력됨 (`KooSection.py:53-59`).
- 새 Part 생성: `KooPart(...)` + `partManager.CreatePartfromKooPart(part)` (`KooDynaAdvancedModification.py:5213-5214`).
- 변환 위임: `constrainedManager.ChangeConstrainedNodalRigidBodytoBeam(cnrbOption, part, nodeSetManager)` 호출, 전후로 `SyncronizeMaxID()` (`KooDynaAdvancedModification.py:5217-5219`).

### 4.3 코어 변환 (CNRB → 빔 묶음)

`ChangeConstrainedNodalRigidBodytoBeam` (`KooConstrained.py:719-762`):

- 각 대상 CNRB의 노드셋(`cnrb.nsid`) 절점들을 평균하여 **중심 좌표(centroid)** 계산 (`KooConstrained.py:726-737`).
- 중심에 새 절점 `n1` 생성 (`KooConstrained.py:739`).
- 노드셋의 각 절점 `n2`에 대해:
  - 중심→절점 벡터 `v1` 계산. 영벡터(중심과 동일 위치)면 skip (`KooConstrained.py:743-745`).
  - 전역 Z축 기준 수직 성분 `v2`(`find_perpendicular_component`)로 빔 방향 정의용 제3절점 `n3`를 거리만큼 떨어뜨려 생성 (`KooConstrained.py:746-755`).
  - `CreateLineQuadraticElement(n1, n2, n3)`로 빔 요소 생성 → 중심 `n1`–대상 `n2` 연결, `n3`는 빔 방향(orientation) 절점 (`KooConstrained.py:756`, 요소 생성 `KooElement.py:3387-3394`).
- 모든 변환 후 처리한 CNRB를 `constrainedNodalRigidbodyList`에서 삭제 (`KooConstrained.py:758-761`).

결과적으로 노드셋의 N개 절점에 대해 빔 N개(또는 중심과 겹치는 절점 제외분만큼 적게)와 추가 절점들이 생성되고, 원래의 강체 구속은 제거된다.

---

## 5. 주의사항 · 한계

- **ELFORM 고정(13)**: 빔 정식은 코드에서 13으로 강제되며 옵션으로 변경 불가 (`KooDynaAdvancedModification.py:5210`). Width/Height는 단면 카드에 기록되지만 ELFORM 13(트러스/케이블 계열)에서의 실제 단면 해석 의미는 LS-DYNA 정식 정의에 따른다. (확인 필요: ELFORM 13에서 TS/TT 단면이 의도대로 반영되는지는 솔버 동작 영역)
- **강체 → 탄성 치환**: 변환 후 구속은 더 이상 강체가 아니라 탄성 빔 강성이 된다. `E`/`Width`/`Height`로 강성을 조절해야 하며, 너무 작으면 모델이 헐거워지고 너무 크면 시간스텝(stable dt)이 작아질 수 있다. 기본값(E=1.0E6, W=H=1.0)은 임의 기본값이므로 단위계/모델 규모에 맞춰 조정 필요.
- **재료/단면 공유**: 대상 CNRB가 여러 개여도 단일 `BeamMaterial`/`BeamSection`을 공유한다 (`KooDynaAdvancedModification.py:5206-5214` — 루프 밖 1회 생성). CNRB별 다른 강성을 주는 기능은 없음.
- **중심과 겹치는 절점**: 중심과 정확히 같은 위치의 절점은 빔이 생성되지 않고 skip 된다 (`KooConstrained.py:744-745`).
- **방향 절점(n3) 생성**: 빔마다 orientation용 제3절점을 추가 생성하므로 절점 수가 늘어난다. Z축 기준 수직 성분으로 방향을 잡으므로 Z축에 평행/수직인 특수 배치에서의 강건성은 코드상 별도 분기 없음(확인 필요).
- **PNODE 미사용**: `ConvertCNRBtoSolidCylinder`와 달리 이 모드는 CNRB의 PNODE를 중심으로 쓰지 않고 항상 노드셋 centroid를 중심으로 한다 (`KooConstrained.py:726-739`).
- **전용 예제 부재**: 저장소에 검증된 입력 예제가 없어, 위 예제는 파서 코드 기반 재구성이다.

---

## 6. 개발 현황

**구현됨 (부분 검증 불가)**.

- 근거: 모드 등록(`KooMeshModifier.py:288-290`), 옵션 파서(`KooMeshModifier.py:776-819`), 디스패치(`KooMeshModifier.py:2834-2836`), 핸들러(`KooMeshModifier.py:2561-2563`), 로직(`KooDynaAdvancedModification.py:5192-5219`), 코어 변환(`KooConstrained.py:719-762`)까지 전 경로가 코드에 존재하고 연결되어 있음.
- 단, 저장소에 **전용 입력 예제·회귀 테스트가 없어** 실제 모델에서의 동작/결과는 코드 정적 분석으로만 확인됨(실행 검증은 미확인).
