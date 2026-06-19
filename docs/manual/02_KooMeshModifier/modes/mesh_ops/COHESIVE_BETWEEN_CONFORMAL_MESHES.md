# KooMeshModifier 모드: COHESIVE_BETWEEN_CONFORMAL_MESHES

## 1. 목적/개요

`COHESIVE_BETWEEN_CONFORMAL_MESHES` 모드는 **공유 절점(conformal, 노드를 공유하도록 정합된)으로 맞붙은 두 솔리드 파트 사이에 응집 요소(cohesive element) 층을 자동으로 삽입**하는 모드이다.

기존에 노드를 직접 공유하던 두 파트의 경계면을 분리(node split)한 뒤, 그 사이에 `*MAT_COHESIVE_MIXED_MODE` 재료와 cohesive shell 단면(`ELFORM=20`)을 갖는 신규 cohesive 파트를 만들고, cohesive 파트의 양면을 각각 원래의 파트 A·B 경계면에 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`로 묶는다. 즉 "공유 절점으로 완전 결합되어 있던 계면"을 "응집 영역 모델(cohesive zone model)로 떼어지면서 파괴/박리될 수 있는 계면"으로 치환한다.

이를 통해 두 파트 사이의 박리(delamination)·계면 파괴를 명시적(explicit) 해석에서 모델링할 수 있게 된다.

근거: 입력 트리거 등록부 `KooMeshModifier.py:303-305`, dispatch 분기 `KooMeshModifier.py:2849-2851`, 래퍼 메서드 `KooMeshModifier.py:2583-2585`, 실제 동작 `KooDynaAdvancedModification.py:6126-6218`.

## 2. 입력 옵션·인자

입력은 두 부분으로 구성된다. (1) `*Mode` 블록에서 모드를 등록하고, (2) `**CohesiveBetweenConformalMeshes` 옵션 블록에서 응집 재료 물성과 적용할 파트 쌍을 지정한다.

### 2-1. `*Mode` 등록 (모드 활성화)

| 항목 | 값 | 설명 | 근거 |
|------|-----|------|------|
| 키워드 토큰 | `cohesive_between_conformal_meshes` | `*Mode` 블록 내 한 줄로 작성 (대소문자 무시) | `KooMeshModifier.py:303` |
| `<modeID>` | 정수 | 토큰 다음 콤마로 구분된 모드 ID. 옵션 블록과 매칭됨 | `KooMeshModifier.py:304-305` |

### 2-2. `**CohesiveBetweenConformalMeshes` 옵션 블록

블록 헤더는 `**CohesiveBetweenConformalMeshes,<modeID>` 형식이며 `<modeID>`는 `*Mode`에서 등록한 ID와 일치해야 한다 (`KooMeshModifier.py:514-516`). 블록은 `**End`(또는 `**EndCohesiveBetweenConformalMeshes` 등 `**end` 포함 토큰) 혹은 빈 줄에서 종료된다 (`KooMeshModifier.py:543-546`).

각 옵션 라인은 `키,값` 형식이다. 응집 재료 물성은 `*MAT_COHESIVE_MIXED_MODE` 카드 인자에 그대로 매핑된다.

| 옵션 | 형식 | 기본값 | 설명 | 근거 |
|------|------|--------|------|------|
| `Pair` | `Pair,<pidA>,<pidB>,<thickness>` | — | 응집 요소를 삽입할 **파트 쌍과 cohesive shell 두께**. 여러 줄 작성 시 각 쌍마다 cohesive 파트 1개씩 생성 | `KooMeshModifier.py:551-555` |
| `RO` | `RO,<value>` | `2.3e-9` | 응집 재료 밀도 | `KooMeshModifier.py:519, 604-606` |
| `ROFlag` | `ROFlag,<int>` | `0` | 밀도 플래그(ROFLG) | `KooMeshModifier.py:520, 568-570` |
| `INTFAIL` | `INTFAIL,<value>` | `0` | 요소 삭제 적분점 개수(INTFAIL) | `KooMeshModifier.py:521, 572-574` |
| `EN` | `EN,<value>` | `1000.0` | 법선 방향 강성(normal stiffness) | `KooMeshModifier.py:522, 584-586` |
| `ET` | `ET,<value>` | `100.0` | 접선 방향 강성(tangential stiffness) | `KooMeshModifier.py:523, 588-590` |
| `GIC` | `GIC,<value>` | `10.0` | 모드 I 에너지 해방률(파괴 에너지) | `KooMeshModifier.py:524, 576-578` |
| `GIIC` | `GIIC,<value>` | `10.0` | 모드 II 에너지 해방률 | `KooMeshModifier.py:525, 580-582` |
| `XMU` | `XMU,<value>` | `1.0` | 혼합 모드 파괴 기준 지수(exponent) | `KooMeshModifier.py:527, 592-594` |
| `T` | `T,<value>` | `100.0` | 법선 방향 최대 응력(peak traction, normal) | `KooMeshModifier.py:529, 596-598` |
| `S` | `S,<value>` | `100.0` | 접선 방향 최대 응력(peak traction, shear) | `KooMeshModifier.py:530, 600-602` |
| `UND` | `UND,<value>` | `10.0` | 법선 방향 극한 변위(ultimate displacement, normal) | `KooMeshModifier.py:532, 560-562` |
| `UTD` | `UTD,<value>` | `10.0` | 접선 방향 극한 변위 | `KooMeshModifier.py:534, 564-566` |
| `GAMMA` | `GAMMA,<value>` | `1.0` | Benzeggagh-Kenane 법칙 추가 지수 | `KooMeshModifier.py:536, 556-558` |

물성을 생략하면 위 기본값이 사용된다(기본값은 블록 진입 시 `curOptions["CohesiveMat"]`에 미리 세팅됨, `KooMeshModifier.py:518-536`).

> 주의 (파서 한계, 확인 필요): 옵션 키 매칭이 대소문자 무시 + `in` 기반 부분문자열 비교로 이뤄진다(`KooMeshModifier.py:556-606`). 단문자 키 `T`(`"t" in line`)·`S`(`"s" in line`)는 다른 키 라인의 부분문자열과 충돌할 소지가 있으나, 코드에서 더 구체적인 키(`gamma/und/utd/roflag/intfail/gic/giic/en/et/xmu`)를 먼저 검사하고 각 분기마다 `continue`로 빠지므로 위 표의 키들을 정확한 토큰으로 사용하면 의도대로 파싱된다. 표에 없는 임의 라인을 추가하면 오매칭될 수 있다.

## 3. 사용 예제

전용 예제가 빌드 산출물 디렉터리에 포함되어 있다(아래 경로). 가공 없이 발췌한다.

발췌 원본: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/CohesiveBetweenConformalMeshes/CohesiveBetweenConformalMeshes.txt`

```
*Inputfile
Impact_1_00000001.k
*Mode
COHESIVE_BETWEEN_CONFORMAL_MESHES,1
**CohesiveBetweenConformalMeshes,1
RO,2.3e-9
ROFlag,0
INTFAIL,0.0
EN,1000.0
ET,100.0
GIC,10.0
GIIC,10.0
XMU,1.0
T,100.0
S,100.0
UND,10.0
UTD,10.0
GAMMA,1.0
Pair,1,2,0.00015
**EndCohesiveBetweenConformalMeshes
*End
```

위 입력은 파트 1과 파트 2 사이에 두께 `0.00015`의 cohesive shell 층을 삽입한다. 산출 결과 파일은 입력명에 접미사 `_cbcm`이 붙는다(`Impact_1_00000001_cbcm.k`, 근거 `KooMeshModifier.py:2851`).

### 출력 검증 (실제 산출물 발췌)

산출 파일 `Impact_1_00000001_cbcm.k`에서 실제로 생성된 카드:

- `*MAT_COHESIVE_MIXED_MODE_TITLE` (제목 `CohesiveMixedModeMaterial`) — 입력 물성이 그대로 기록됨 (`RO=2.300e-09, EN=1.000e+03, ET=1.000e+02, GIC=GIIC=1.000e+01, T=S=1.000e+02, UND=UTD=1.000e+01, GAMMA=1.000e+00`).
- `*SECTION_SHELL_TITLE` (제목 `CohesiveShell`) — `ELFORM=20`(cohesive shell), 4절점 두께 모두 `1.500e-04`(입력 `Pair` 두께).
- `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID` 2건 — cohesive 파트(SSID=7)를 SSTYP=3, MSTYP=2로 각각 파트 A·B의 segment set(MSID=1, MSID=2)에 tie.

## 4. 동작 원리

dispatch → 래퍼 → 실제 구현 순서로 호출된다.

- `KooMeshModifier.py:2849-2851` — `mode == "COHESIVE_BETWEEN_CONFORMAL_MESHES"`일 때 `GenerateCohesiveBetweenConformalMeshes(modeid)` 호출, 출력 접미사 `_cbcm` 추가.
- `KooMeshModifier.py:2583-2585` — 옵션 dict를 꺼내 `self.advancedModification.CohesiveBetweenConformalMeshes(curOption)` 호출.

실제 처리(`KooDynaAdvancedModification.py:6126-6218`):

1. **응집 재료 생성** (`6130-6144`): 옵션의 `CohesiveMat` 물성으로 `CreateCohesiveMixedModeMaterial(...)` 호출 → `KooMaterialCohesiveMixedMode` 객체 생성. 이 재료는 `*MAT_COHESIVE_MIXED_MODE_TITLE` 카드로 기록된다(`KooMaterial.py:1107-1110`, 카드 포맷 `KooMaterial.py:744-756`).
2. **파트 쌍 루프** (`6149`): `Pair` 라인 수만큼 반복. 각 반복 시작에서 `SyncronizeMaxID()`로 ID 동기화.
3. **단면 생성** (`6156`): `CreateShellSection("CohesiveShell", thickness, 20)` → `ELFORM=20`(cohesive shell) 단면. 두께는 `Pair`의 세 번째 인자(`KooSection.py:354-359`).
4. **경계면·공유 절점 추출** (`6158-6165`): 파트 A·B 각각에서 `GetExternalBoundariesandNodeDict(True)`로 외곽 면(boundary)과 외곽 절점 dict를 얻고(`KooElement.py:4577-4586`), 두 파트가 **동일 키(절점 ID)로 공유하는 절점**만 `sharedNodes`로 모은다. 즉 conformal하게 절점을 공유하던 계면을 식별한다.
5. **계면 segment 분리** (`6166-6177`): 공유 절점을 하나라도 포함하는 외곽 면만 `boundaryCohesiveA`/`boundaryCohesiveB`로 추린다.
6. **노드 스플릿** (`6178-6179`): 파트 A·B에 대해 `SplitNodes(sharedNodes)` 호출. 공유 절점 각각에 대해 새 절점을 만들어 해당 파트 요소가 새 절점을 참조하도록 remap한다(`KooElement.py:1956-1966`). 결과적으로 두 파트가 더 이상 절점을 직접 공유하지 않고 물리적으로 분리된다.
7. **cohesive 파트·요소 생성** (`6180-6183`): 신규 `ElementManager`/`KooPart`(재료=응집재료, 단면=CohesiveShell)를 만들고, `CreateElementsfromSegments(sharedNodes, boundaryCohesiveA)`로 공유 계면 면들로부터 cohesive 요소(삼각형/사각형)를 생성한다(`KooElement.py:3521-3543`).
8. **segment set 생성** (`6184-6187`): 파트 A 계면면(`boundaryCohesiveA`)과 파트 B 계면면(`boundaryCohesiveB`)을 각각 segment set으로 등록.
9. **tied contact 생성** (`6190-6216`): cohesive 파트(SSID)와 두 segment set(파트 A, 파트 B) 사이에 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`를 2건 생성. 고정 파라미터: `SSTYP=3`(part), `MSTYP=2`(segment set), `VDC=5.0`, `DT=1.0E+20`, 나머지 마찰/스케일 0 또는 공란(`KooContact.py:786-792`).
10. **기존 tied contact 제거** (`6218`): `RemoveTiedContactBetweenTwoPart(partA.id, partB.id)` — 파트 A·B를 직접 묶고 있던 기존 tied surface-to-surface 접촉(SSTYP=MSTYP=3)이 있으면 제거(`KooContact.py:825-833`).

수정 후 `WriteModifiedFile`로 `_cbcm.k` 파일이 기록된다(`KooMeshModifier.py:2880-2891`).

## 5. 주의사항·한계

- **conformal(절점 공유) 메시 전제**: 동작의 핵심은 두 파트가 동일 절점 ID를 공유하는 정합 계면이라는 점이다. 공유 절점이 식별되지 않으면(`sharedNodes`가 비면) cohesive 요소가 생성되지 않는다(`KooDynaAdvancedModification.py:6161-6183`). 비정합(non-conformal) 계면에는 적용되지 않는다.
- **tied contact 기반 결합**: cohesive 층은 노드 병합이 아니라 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`로 양쪽에 묶인다. 따라서 tie 접촉 파라미터(고정값 `VDC=5.0` 등)와 cohesive 물성이 결과에 함께 영향을 준다.
- **물성 단위계는 입력값에 의존**: 기본값(`RO=2.3e-9`, `EN=1000.0` 등)은 특정 단위계(예: mm-tonne-s)를 가정한 값으로 보이나 코드상 단위 변환·검증은 없다. 모델 단위계에 맞는 값을 직접 입력해야 한다(확인 필요 — 단위계 검증 로직 미발견).
- **`Pair` 필수**: `Pair` 라인이 없으면 `partAList`가 비어 cohesive가 전혀 생성되지 않는다(`KooDynaAdvancedModification.py:6145-6149`).
- **단문자 키 파서 충돌 가능성**: 2-2절 표 하단 주의 참조. 옵션 키는 정확한 토큰으로만 사용할 것.
- **고정 tie 파라미터**: tie 접촉의 `SSTYP/MSTYP/VDC/DT` 등은 코드에 하드코딩되어 있어 입력으로 조정 불가(`KooDynaAdvancedModification.py:6192-6214`).

## 6. 개발 현황

**구현됨.**

근거:
- 입력 트리거·옵션 파서·dispatch·실제 동작이 모두 존재: `KooMeshModifier.py:303-305, 514-608, 2583-2585, 2849-2851`, `KooDynaAdvancedModification.py:6126-6218`.
- 빌드 산출물에 **실제 입력(.txt)과 산출물(.k) 예제가 동봉**되어 있고, 산출물 `Impact_1_00000001_cbcm.k`에 `*MAT_COHESIVE_MIXED_MODE_TITLE`, `*SECTION_SHELL_TITLE`(ELFORM=20), `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID` 2건이 정상 생성됨을 확인했다(경로: `occProject/Generators/dist/Examples/5.SimulationModify/CohesiveBetweenConformalMeshes/`). 실행 로그(`CohesiveBetweenConformalMeshes.log`)에도 외곽 경계 추출·파일 기록·`Done`이 기록되어 있다.

> 비고: `KooMeshModifier.py:3102-3107`에 이 모드용 예제 실행 경로가 (주석 처리된 형태로) 남아 있어, KooMeshModifier 단독 실행 시의 표준 예제로 의도되었음을 확인할 수 있다. scenario.json 기반 KooChainRun 워크플로우에서의 직접 노출 여부는 본 조사 범위에서 확인되지 않았다(확인 필요).
