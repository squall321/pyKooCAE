# KooMeshModifier 모드: RIGIDIFY_SMALL_DT

## 1. 목적 / 개요

`RIGIDIFY_SMALL_DT`는 안정 timestep(stable dt)이 너무 작거나 종횡비(aspect ratio)가 너무 큰 **불량 요소**, 또는 사용자가 수동 지정한 요소를 원본 파트에서 떼어내 **새 강체(MAT_RIGID) 파트로 분리**하는 KooMeshModifier 모드이다. 명시적(explicit) 해석에서 소수의 찌그러진 요소가 전체 timestep을 끌어내리는 문제를 완화하기 위한 것으로, 해당 요소들을 강체화하여 minimum dt를 확보하는 것이 목적이다.

핵심 동작 요약 (`KooPart.py:2842-2854` docstring):
- 요소별 stable dt / aspect ratio / 수동 지정 ID 기준으로 분리 대상을 판정
- 대상 요소를 원본 파트에서 제거하고 새 강체 재료·섹션을 가진 새 파트로 이동
- 자동 기준(dt, aspect ratio)은 **TETRA(사면체) 요소에만** 적용되며 HEXA는 자동 기준에서 제외(수동 지정은 타입 무관 허용)

전용 예제(Examples 디렉터리, scenario.json)는 **부재**하다. 본 문서는 전적으로 코드 근거로 작성되었으며, 일부는 "확인 필요"로 표기한다.

## 2. 입력 옵션 · 인자

KooMeshModifier 입력 `.k`(step_config) 안에서 `*Mode` 블록에 `RIGIDIFY_SMALL_DT,<modeid>`를 등록하고, 별도의 `**RigidifySmallDt,<modeid>` 옵션 블록에 세부 옵션을 기술한다. (파서는 `**rigifysmalldt` 와 `**rigidifysmalldt` 두 철자를 모두 허용한다 — `KooMeshModifier.py:1800`.)

모드 등록: `KooMeshModifier.py:258-260` (`rigidify_small_dt` → `RIGIDIFY_SMALL_DT`)
옵션 파싱: `KooMeshModifier.py:1800-1830` (`**rigifysmalldt`/`**rigidifysmalldt` 블록)
디스패치: `KooMeshModifier.py:2798-2800` → `GenerateRigidifySmallDT` (`KooMeshModifier.py:2537-2550`)

| 옵션 카드 | 인자 | 의미 | 기본값 | 근거 |
|---|---|---|---|---|
| `*DtThreshold` (또는 `*Dt`) | `value` | 이 값 **이하**의 stable dt를 가진 TETRA 요소를 강체화. `0`이면 dt 기준 비활성 | `1.0e-8` | `KooMeshModifier.py:1811-1813`, `KooPart.py:2847,2910-2913` |
| `*MaxAspectRatio` | `value` | 이 값을 **초과**하는 aspect ratio(max_edge/min_edge)의 TETRA 요소를 강체화. `0`이면 aspect ratio 기준 비활성 | `0.0` | `KooMeshModifier.py:1814-1816`, `KooPart.py:2849,2916-2935` |
| `*ElementIDs` | `eid1,eid2,...` | 수동 지정 요소 ID 리스트. 타입(TETRA/HEXA/Shell) 무관하게 강체화 | `None` | `KooMeshModifier.py:1817-1819`, `KooPart.py:2850,2906-2907` |
| `*ExceptPID` | `pid1,pid2,...` | 강체화 대상에서 제외할 PID set | `set()`(없음) | `KooMeshModifier.py:1820-1825`, `KooPart.py:2848,2867-2868` |

주의: `*Dt`는 `*DtThreshold`와 동일하게 매핑된다 (`elif "*dtthreshold" in line.lower() or "*dt" in line.lower()`, `KooMeshModifier.py:1811`). 옵션 블록은 `**End`(대소문자 무관) 또는 빈 줄을 만나면 종료된다 (`KooMeshModifier.py:1807-1810`).

기본값은 두 군데에서 정의된다: 파서가 인자를 변환할 때(`KooDynaFloat(svector[1], <기본값>)`)와, 옵션 카드 자체가 없을 때 `GenerateRigidifySmallDT`의 `curOption.get(..., <기본값>)` (`KooMeshModifier.py:2539-2542`). 위 표의 기본값은 후자(카드 미기재 시 적용값) 기준이다.

## 3. 사용 예제

전용 예제 파일이 **없으므로**, 아래는 파서/구현 코드(`KooMeshModifier.py:1800-1830`, `258-260`)가 기대하는 입력 형식을 코드 기반으로 재구성한 것이다. (실제 Examples 산출물에서 발췌한 것이 아님 — 확인 필요.)

### KooMeshModifier 입력 (step_config) 형식 — 코드 기반 재구성

```
*Inputfile
model.k
*Mode
RIGIDIFY_SMALL_DT,1
**RigidifySmallDt,1
*DtThreshold,1.0e-8
*MaxAspectRatio,20.0
*ElementIDs,100501,100502,100503
*ExceptPID,5,6
**End
*End
```

실행:

```
KooMeshModifier step_config.txt
```

위에서:
- `*DtThreshold,1.0e-8` → stable dt ≤ 1e-8 인 TETRA 요소 강체화
- `*MaxAspectRatio,20.0` → aspect ratio > 20 인 TETRA 요소 강체화
- `*ElementIDs,...` → 지정한 요소를 타입 무관 강체화
- `*ExceptPID,5,6` → PID 5, 6은 검사에서 제외

(확인 필요: scenario.json(KooChainRun/CumulativeDesigner) → step_config 변환 경로 및 키 이름은 본 조사 범위에서 미확인. `RIGIDIFY_SMALL_DT` 전용 scenario 예제는 Examples에 존재하지 않음.)

참고 — DROP 워크플로우 내 별도 경로: `KooMeshModifier.py:1516-1525`에는 `RigidifySmallDtThreshold` / `RigidifyMaxAspectRatio` / `RigidifyElementIDs` 라는 **다른 키**로 rigidify 옵션을 받는 파서가 존재하나, 이는 `**RigidifySmallDt` 독립 블록이 아니라 다른(DROP 계열) 모드 옵션 블록 안에 내장된 것으로 보인다. 본 문서가 다루는 독립 `RIGIDIFY_SMALL_DT` 모드와는 키·경로가 다르다. (해당 내장 경로의 실제 소비처는 본 조사 범위 밖 — 확인 필요.)

## 4. 동작 원리 (코드 근거)

진입점은 `GenerateRigidifySmallDT(modeid)` (`KooMeshModifier.py:2537-2550`)로, 옵션을 꺼내 `partManager.RigidifySmallDtElements(...)`를 호출한다:

```
dt_threshold = curOption.get("DtThreshold", 1.0e-8)
except_pids  = curOption.get("ExceptPIDs", set())
max_ar       = curOption.get("MaxAspectRatio", 0.0)
elem_ids     = curOption.get("ElementIDs", None)
self.dynaImporter.partManager.RigidifySmallDtElements(
    matManager, sectionManager,
    dt_threshold=..., exceptPIDs=..., max_aspect_ratio=..., element_ids=...)
```

실제 로직은 `KooPart.py:2840-2983` `RigidifySmallDtElements`:

1. **파트 순회 / 사전 필터** (`KooPart.py:2866-2887`):
   - `exceptPIDs`에 속한 PID는 skip (`2867-2868`).
   - 요소가 없거나, 재료가 없거나, `E<=0` 또는 `rho<=0`이면 skip (`2869-2880`).
   - 이미 강체 재료(`dtype` 또는 재료 이름에 `RIGID` 포함)면 skip (`2882-2887`).

2. **요소별 판정** (`KooPart.py:2896-2938`):
   - 수동 지정: `eid`가 `element_ids`에 있으면 타입 무관 강체화 (`2905-2907`).
   - dt 기준(TETRA만): `dt_threshold>0` 이고 사면체 요소(고유 노드 ≤5)일 때 `compute_element_stable_dt(elem, E, rho, nu)` ≤ `dt_threshold`면 강체화 (`2909-2913`).
   - aspect ratio 기준(TETRA만): `max_aspect_ratio>0` 이고 사면체일 때, 고유 좌표 4개 이상의 노드 간 모든 edge 길이 중 `max/min > max_aspect_ratio`면 강체화 (`2915-2935`).
   - TETRA 판정: `isinstance(elem, SolidElement)` 이면서 고유 노드 수 ≤5 (`2902-2903`). 즉 정상 HEXA8은 자동 기준 대상에서 제외된다.

3. **stable dt 계산식** (`KooElement.py:5830-5854` `compute_element_stable_dt`):
   - `dt = L_char / c`, `L_char`는 요소 최소 edge 길이(`compute_element_min_edge_length`).
   - Solid: P-파 음속 `c = sqrt(E*factor/rho)`, `factor=(1-nu)/((1+nu)(1-2nu))` (`5840-5845`).
   - Shell: `c = sqrt(E/(rho*(1-nu^2)))` (`5846-5849`). `E<=0`/`rho<=0`/`L<=0`이면 `inf` 반환(=강체화 안 됨).

4. **강체 파트 생성 + 요소 이동** (`KooPart.py:2943-2976`):
   - 분리 대상이 1개 이상인 파트마다 강체 재료 생성: `materialMan.CreateRigidMaterial(f"RIGID_SmallDT_P{pid}", rho, E, nu)` (`2944-2945`).
   - 섹션 복제: 원본이 Shell이면 ShellSection(두께는 원본 두께 또는 0.1), Solid면 SolidSection (`2947-2956`).
   - 새 PID = `maxID+1`로 새 `KooPart` 생성, 이름 `RIGID_SmallDT_from_P{pid}` (`2958-2962`).
   - 대상 요소를 원본 `elementManager`에서 제거하고 새 파트에 추가 (`2964-2971`).

5. **등록 / 반환** (`KooPart.py:2978-2983`):
   - 생성된 강체 파트들을 `self.parts`에 등록, 생성된 강체 PID 리스트 반환.
   - 콘솔에 파트별/총합 강체화 요소 수를 출력 (`2976,2982`).

디스패치 시 출력 파일명에는 접미사 `_rsdt`가 붙는다 (`KooMeshModifier.py:2800`). 출력은 기본 `WriteModifiedFile`로 기록된다(`_skip_default_write` 미설정, `KooMeshModifier.py:2883-2891`).

## 5. 주의사항 · 한계

- **자동 기준은 TETRA 한정**: dt·aspect ratio 자동 판정은 사면체(고유 노드 ≤5)에만 적용된다. 정상 HEXA8 등은 자동으로는 강체화되지 않으며, 강제하려면 `*ElementIDs`로 수동 지정해야 한다 (`KooPart.py:2902-2916`).
- **재료 필요**: 파트에 재료가 없거나 `E<=0`/`rho<=0`이면 해당 파트 전체 skip(음속/dt 계산 불가) (`KooPart.py:2873-2880`).
- **이미 강체인 파트 skip**: 재료 `dtype` 또는 이름에 `RIGID`가 포함되면 skip (`KooPart.py:2882-2887`).
- **요소 분리 방식**: 요소를 새 PID로 옮기되 노드는 공유된다(노드 매니저 공유, `KooPart.py:2960`). 분리된 강체 파트는 새 MAT_RIGID이므로, 원본 파트와의 접촉·구속 처리(예: 접촉 제외/추가 정의)는 본 메서드 범위 밖이다 — 별도 처리 필요. (접촉 제외 자동화 여부는 본 조사 범위 밖, 확인 필요.)
- **두 종류의 입력 키 혼동 주의**: 독립 모드는 `**RigidifySmallDt` 블록 + `*DtThreshold/*MaxAspectRatio/*ElementIDs/*ExceptPID` (`KooMeshModifier.py:1800-1825`). DROP 계열 내장 옵션은 `RigidifySmallDtThreshold/RigidifyMaxAspectRatio/RigidifyElementIDs` (`KooMeshModifier.py:1516-1525`). 둘은 별개다.
- **전용 예제 부재**: Examples 및 scenario.json에 `RIGIDIFY_SMALL_DT`(또는 rigidify) 전용 예제가 존재하지 않는다(grep 결과 0건). 입력 형식은 코드 기반 재구성이므로 운영 적용 전 실제 파서 동작으로 검증 권장.

## 6. 개발 현황

**구현됨**

근거:
- 모드 등록·파싱·디스패치 경로 모두 존재: `KooMeshModifier.py:258-260`(등록), `1800-1830`(옵션 파싱), `2537-2550`·`2798-2800`(디스패치).
- 핵심 로직 전체 구현: `KooPart.py:2840-2983` `RigidifySmallDtElements` (필터 → 요소 판정 → 강체 파트 생성/요소 이동 → 등록까지 완비).
- stable dt 계산 보조 함수 구현: `KooElement.py:5830-5854`.

단, **동작 예제(Examples/scenario.json)는 부재**하여 end-to-end 검증 산출물은 확인되지 않았다(확인 필요). 코드 경로 자체는 완전히 연결되어 있어 "구현됨"으로 분류한다.
