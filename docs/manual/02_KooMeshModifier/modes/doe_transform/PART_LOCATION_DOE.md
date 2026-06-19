# KooMeshModifier 모드: PART_LOCATION_DOE

## 1. 목적 / 개요

`PART_LOCATION_DOE`는 지정한 파트(들)를 한 평면(XY/XZ/YZ) 위에서 무작위로 평행이동시키며,
유효 영역(마스크) 안에 들어오는 위치만 채택하여 **서로 다른 위치 조합의 .k 파일 다수를 생성**하는
DOE(실험계획법) 모드이다. 충격/낙하 시 충돌 위치를 변수로 두는 위치 민감도 연구(예: `Impact_*` 모델)에
사용되도록 작성되어 있다.

핵심 동작:
- 대상 파트의 경계상자(bounding box) 중심을 기준으로, 평면 내에서 LatinHypercube 샘플링으로 (Δa, Δb) 변위 생성
- `MaskPID`(허용 영역) 및 `ObstaclePIDs`(금지 영역)로 2D 마스크를 구성하고, 이동된 파트가 마스크 내부에 있는지 검사
- 유효한 샘플만 파일명에 변위를 인코딩하여 export

> 근거: 진입 분기는 `KooMeshModifier.py:2792` `elif mode == "PART_LOCATION_DOE"` → `GeneratePartLocationDOE`(`KooMeshModifier.py:2525`) → `KooDynaAdvancedModification.PartLocationDOE`(`KooDynaAdvancedModification.py:4900`).

---

## 2. 입력 옵션 · 인자 (표)

모드 등록은 `*Mode` 섹션에서 `PART_LOCATION_DOE,<modeid>`로, 세부 옵션은
`**PartLocationDOE,<modeid>` ~ `**EndPartLocationDOE` 블록으로 기술한다.
파서는 모든 키를 소문자 비교로 인식한다(대소문자 무관).

| 옵션 키 | 형식 | 기본값 | 설명 | 근거(file:line) |
|---|---|---|---|---|
| `*PIDs` | `*PIDs,p1,p2,...` | `[]` | 이동시킬 대상 파트 ID 목록. 각 PID에 대해 독립적으로 DOE 수행 | KooMeshModifier.py:1720-1724 |
| `*MaskPID` | `*MaskPID,id` | `0` | 허용(유효) 영역을 정의하는 파트 ID. 0/미존재 시 평면 전체를 유효로 간주 | KooMeshModifier.py:1725-1728 / KooDynaAdvancedModification.py:4938-4986 |
| `*ObstaclePID` | `*ObstaclePID,o1,o2,...` | `[]` | 금지(제외) 영역 파트 ID 목록. 마스크에서 제외 처리 | KooMeshModifier.py:1729-1733 / KooDynaAdvancedModification.py:4988-4990 |
| `*dx` | `*dx,값` | `0.0` | x방향 변위 반경. 0이면 해당 축을 샘플링 평면의 법선으로 사용 | KooMeshModifier.py:1734-1737 |
| `*dy` | `*dy,값` | `0.0` | y방향 변위 반경 | KooMeshModifier.py:1738-1741 |
| `*dz` | `*dz,값` | `0.0` | z방향 변위 반경 | KooMeshModifier.py:1742-1745 |
| `*nx` | `*nx,정수` | `10` | x방향 마스크 격자 분해능 | KooMeshModifier.py:1746-1749 |
| `*ny` | `*ny,정수` | `10` | y방향 마스크 격자 분해능 | KooMeshModifier.py:1750-1753 |
| `*nz` | `*nz,정수` | `0` | z방향 마스크 격자 분해능 | KooMeshModifier.py:1754-1757 |
| `*Dilation` | `*Dilation,정수` | `1` | 마스크 팽창(dilation) 픽셀 수 | KooMeshModifier.py:1758-1761 |
| `*Sampling` | `*Sampling,Method,N` | `{}` | 샘플링 방법과 샘플 수. 현재 `LatinHypercube`만 동작 | KooMeshModifier.py:1762-1767 / KooDynaAdvancedModification.py:4992 |

축 / 평면 규칙 (KooDynaAdvancedModification.py:4915-4937):
- 정확히 한 축의 변위가 0이어야 한다. `dx*dy*dz != 0`(세 축 모두 0이 아님)이면 `"x-y-z sampling is not supported"`를 출력하고 즉시 반환.
- `dx==0` → YZ 평면, `dy==0` → XZ 평면, `dz==0` → XY 평면.
- 평면 내 두 축은 각각 `(da, db)` = (0이 아닌 두 변위)로 매핑되며, 샘플 범위는 `(-da, da) × (-db, db)`이고 마스크 격자 분해능은 `(na, nb)` = (해당 두 축의 n)이다.

---

## 3. 사용 예제

전용 매뉴얼 시나리오 외에 실제 입력 .txt 예제가 코드 배포본에 존재한다.

파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/dist/Examples/5.SimulationModify/PartLocationDOE/PartLocationDOE.txt`

```
*Inputfile
Impact_1_00000001.k
*Mode
PART_LOCATION_DOE,1
**PartLocationDOE,1
*PIDs,1
*dx,0.0005
*dy,0.0005
*nx,10
*ny,10
*MaskPID,2
*Dilation,1
*Sampling,LatinHypercube,100
**EndPartLocationDOE
*End
```

해석:
- 파트 1을 대상으로, `dx≠0, dy≠0, dz`(미지정→기본 0.0) → `dz==0` 분기 → XY 평면 샘플링.
- 변위 범위 ±0.0005(x) × ±0.0005(y), 마스크 격자 10×10, 파트 2의 노드 영역을 허용 마스크로 사용, dilation 1.
- LatinHypercube로 100개 후보 생성 후, 유효한 것만 파일로 export.

생성 파일명 형식 (XY 평면 기준, KooDynaAdvancedModification.py:5042):
`<입력파일명>_DX_<dx>_DY_<dy>.k` — 변위는 `'.3e'` 지수표기.
실제 출력 예(같은 예제 폴더 `lspost.cfile`에서 확인):
`Impact_1_00000001_DX_2.771e-04_DY_3.027e-04.k`

> 참고: 예제는 `*dz`/`*nz`/`*ObstaclePID`를 사용하지 않는다. 본 모드용 scenario.json/CLI 별도 예제는 확인되지 않았다(확인 필요). 위 .txt는 KooMeshModifier가 직접 읽는 옵션 파일 형식이다.

---

## 4. 동작 원리 (코드 근거)

1. **입력 파싱**: `**partlocationdoe` 라인을 만나면 옵션 dict 기본값을 세팅하고 `**end`까지 키들을 읽어 `self.modeIDOption[curModeID]`에 저장.
   - 근거: `KooMeshModifier.py:1696-1775`

2. **디스패치**: `GenerateModifiedFile` 루프에서 `mode == "PART_LOCATION_DOE"`일 때 `GeneratePartLocationDOE(modeid)` 호출, 결과 파일명 접미사 `_pld` 추가.
   - 근거: `KooMeshModifier.py:2792-2794`

3. **평면/축 결정**: `checkDimension = dx*dy*dz`가 0이어야 하며, 0인 축이 평면의 법선이 된다. 셋 다 0이 아니면 미지원으로 반환.
   - 근거: `KooDynaAdvancedModification.py:4915-4937`

4. **마스크 구성**:
   - 대상 파트마다 `GetBoundaryBox()`로 경계상자 중심(`xmid,ymid,zmid`) 계산.
   - 평면 두 축 한계 `alim/blim`을 중심±(da/db)로 설정.
   - `MaskPID`가 유효하면 그 파트의 노드로 허용 마스크를 `FastMaskDilationfromNodes(..., "include")` 구성, 없으면 전체 1(모두 유효).
   - 각 `ObstaclePID` 파트는 `FastMaskDilationfromNodes(..., "exclude")`로 마스크에서 제외.
   - 근거: `KooDynaAdvancedModification.py:4956-4990`, 마스크 함수 `KooPart.py:1502`

5. **샘플링 & 검증 & export** (`LatinHypercube`):
   - `sample_lhs_2d(N, (-da,da), (-db,db))`로 2D 변위 샘플 생성(`KooOperator.py:192`).
   - 각 샘플에 대해 `part.Translate(...)`로 임시 이동 → `CheckinsideValidArea(mask, alim, blim, plane)`로 마스크 내부 여부 검사(`KooPart.py:1460`).
   - 유효하면 변위를 파일명에 인코딩하여 export, 검사 후 `part.Translate(-...)`로 원위치 복원.
   - 근거: 평면별 분기 `KooDynaAdvancedModification.py:4992-5050`

6. **Fast DOE 모드(성능 최적화)**: 샘플 수 > 1이면 노드 제외 캐시(`WriteStreamPreNodesKeyword`/`WriteStreamPostNodesKeyword`)를 만들어 `_WriteCachedExceptNodesFile`로 빠르게 출력하고, 실패 시 일반 `WriteModifiedFile` 폴백.
   - 근거: `KooDynaAdvancedModification.py:4943-4954`, 출력 분기 `:5006-5009` 등

---

## 5. 주의사항 · 한계

- **세 축 동시 샘플링 불가**: `dx,dy,dz`가 모두 0이 아니면 `"x-y-z sampling is not supported"` 출력 후 아무것도 하지 않고 종료. 반드시 한 축은 0이어야 한다(평면 DOE 전용). (KooDynaAdvancedModification.py:4936-4937, 4976-4978)
- **샘플링 방법 제한**: 코드 분기는 `samplingMethod == "LatinHypercube"`만 처리한다. 다른 값이면 어떤 파일도 export되지 않는다(else 분기 없음). (KooDynaAdvancedModification.py:4992)
- **PID 존재 가정**: 대상 PID는 `self.dynaImporter.partManager.parts[pid]`로 직접 접근하므로, 미존재 PID는 예외를 유발할 수 있다(가드 없음). (KooDynaAdvancedModification.py:4957)
- **MaskPID=0 또는 미존재**: 허용 마스크가 전체 1로 채워져 사실상 영역 제한이 없어진다. (KooDynaAdvancedModification.py:4983-4984)
- **유효성 검사 정밀도**: 마스크는 `na×nb`(=평면 두 축의 n) 격자 해상도로 노드를 양자화하여 판정하므로, 분해능(`*nx/*ny/*nz`)이 낮으면 경계 근처 판정이 거칠어질 수 있다. (KooPart.py:1468-1500)
- **유효 샘플 수 ≤ N**: 100개 요청해도 마스크 밖 샘플은 버려지므로 실제 생성 파일 수는 그보다 적을 수 있다.
- **출력 위치**: `filePath`는 입력 .k 경로에서 `.k`를 제거한 접두로, 동일 디렉터리에 변위 접미사를 붙여 저장된다. (KooMeshModifier.py:2527-2530)

---

## 6. 개발 현황

**구현됨 (부분 제한 있음)**

- 근거: 입력 파서(`KooMeshModifier.py:1696-1775`), 디스패치(`KooMeshModifier.py:2792-2794`), 핸들러(`GeneratePartLocationDOE`, `KooMeshModifier.py:2525-2530`), 알고리즘 본체(`KooDynaAdvancedModification.PartLocationDOE`, `KooDynaAdvancedModification.py:4900-5050`)와 보조 함수(`sample_lhs_2d`/`FastMaskDilationfromNodes`/`CheckinsideValidArea`)가 모두 존재하며, 실제 입력 예제 및 산출 파일명(`Impact_1_00000001_DX_..._DY_....k`)이 배포본에 남아 있다.
- 제한: 샘플링 방법은 `LatinHypercube`만, 평면(2축) DOE만 지원. 3축 동시 DOE 및 기타 샘플링 방법은 미구현.
