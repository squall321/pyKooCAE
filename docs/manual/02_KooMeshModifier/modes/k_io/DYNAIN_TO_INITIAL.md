# KooMeshModifier 모드: DYNAIN_TO_INITIAL

## 1. 목적 / 개요

`DYNAIN_TO_INITIAL`은 LS-DYNA 해석 결과로 생성된 `dynain` 파일(변형 형상 + 초기 응력/이력)을
원본 모델(`*Inputfile`)에 다시 적용하여, 변형 후 상태를 초기 조건으로 갖는 새 입력 `.k`를
만드는 모드입니다. 누적 해석(cumulative simulation) 체인에서 한 단계의 종료 상태를
다음 단계의 시작 상태로 넘기는 데 사용됩니다.

주요 동작:
- `dynain` 파일을 별도 importer로 읽어 원본 모델 위에 덮어씀(노드 좌표/요소 상태 갱신).
- 옵션에 따라 초기 응력(`*INITIAL_STRESS_*`) 포함/제외.
- 동적 이완(dynamic relaxation) 카드 제거 또는 신규 설정.
- 모델을 원점으로 정렬(세 노드 기준 변환).
- 불필요한 파트(예: 임팩터)·접촉 제거.

근거: dispatch 분기 `KooMeshModifier.py:2852-2854`, 핵심 구현
`KooDynaAdvancedModification.py:6221-6316`.

## 2. 입력 옵션 · 인자

모드 트리거는 `*Mode` 블록의 `DYNAIN_TO_INITIAL,<modeid>`로 등록되고
(`KooMeshModifier.py:306-308`), 세부 옵션은 `**DynainToInitial,<modeid>` ~
`**EndDynainToInitial` 블록에서 파싱됩니다(`KooMeshModifier.py:447-512`).

| 옵션 키 (입력 라인) | 기본값 | 설명 | 근거 |
|---|---|---|---|
| `*DynainPath,<경로>` | `dynain` | 적용할 dynain 파일 경로. `dynain`이면 현재 디렉터리의 `dynain` 사용, 그 외에는 `folderPath` 기준 상대경로로 결합 | `KooMeshModifier.py:451,472-474`; `KooDynaAdvancedModification.py:6222-6226` |
| `*IncludeStress,True\|False` | `True` | True면 dynain의 초기 응력을 유지하고 원본 모델의 기존 초기조건을 제거; False면 dynain의 초기조건을 제거(형상만 적용) | `KooMeshModifier.py:452,475-480`; `KooDynaAdvancedModification.py:6287-6290` |
| `*RemoveDynamicRelaxation,True\|False` | `True` | True면 기존 `*CONTROL_DYNAMIC_RELAXATION` 카드를 제거 | `KooMeshModifier.py:453,481-486`; `KooDynaAdvancedModification.py:6241-6242` |
| `*DynamicRelaxation,True\|False` | `False` | True면 control/database 초기화 후 동적 이완 카드를 신규 설정(`SetControlDynamicRelaxation(250,1e-5,0.35,1e99,0.3,0,1e-4,-1)`) | `KooMeshModifier.py:458,487-492`; `KooDynaAdvancedModification.py:6302-6305` |
| `*MovetoOriginbyNode,<n1>,<n2>,<n3>` | `[]` | 원점 정렬 기준이 될 세 노드 ID. 정확히 3개여야 사용됨 | `KooMeshModifier.py:454,493-495`; `KooDynaAdvancedModification.py:6255-6270` |
| `*MovetoOriginAutomatic,True\|False` | `False` | True면 바운딩 박스 코너에 가장 가까운 노드 3개를 자동 선정해 원점 정렬 | `KooMeshModifier.py:455,496-501`; `KooDynaAdvancedModification.py:6245-6253` |
| `*RemovePartbyName,<name1>,<name2>,...` | `[]` | 지정한 이름의 파트를 제거(접촉 포함) | `KooMeshModifier.py:456,502-504`; `KooDynaAdvancedModification.py:6307-6309` |
| `*RemovePartbyID,<id1>,<id2>,...` | `[]` | 지정한 파트 ID를 제거(접촉 포함) | `KooMeshModifier.py:457,505-507`; `KooDynaAdvancedModification.py:6310-6312` |
| `*RemovecontactbyID,<id1>,<id2>,...` | `[]` | 지정한 접촉 ID를 제거 | `KooMeshModifier.py:459,508-510`; `KooDynaAdvancedModification.py:6314-6316` |

참고(원점 정렬 우선순위): `MovetoOriginAutomatic == True` 이거나 `MovetoOriginbyNode`가
3개 미만이면 자동 모드로 동작합니다(`KooDynaAdvancedModification.py:6245`). 노드 3개를
지정했더라도 그 중 하나라도 찾지 못하면 자동 모드로 fallback 합니다
(`KooDynaAdvancedModification.py:6261-6266`).

## 3. 사용 예제

### 3-1. 노드 지정 정렬 + 파트 제거 (전용 예제 발췌)

`occProject/Generators/dist/Examples/5.SimulationModify/DynaintoInitial/DynainToInitial.txt`
(가공 없이 그대로):

```
*Inputfile
PlateSolid_DimensionalTolerance_1.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginbyNode,2,5,6
*RemovePartbyName,Impactor
*RemovePartbyID,1
**EndDynainToInitial
*End
```

### 3-2. 자동 원점 정렬 변형 (전용 예제 발췌)

`occProject/Generators/dist/Examples/5.SimulationModify/DynamicRelaxation/DynainToInitial.txt`
(가공 없이 그대로):

```
*Inputfile
MinimumModel_001_DA_EX_108.401_..._WZ_0.000.k
*Mode
DYNAIN_TO_INITIAL,1
**DynainToInitial,1
*DynainPath,dynain
*IncludeStress,True
*RemoveDynamicRelaxation,True
*MovetoOriginAutomatic,True
*RemovePartbyID,23
**EndDynainToInitial
*End
```

(위 2-2 예제의 `*Inputfile` 라인은 표기 편의를 위해 파일명 중간을 `...`로 축약했습니다.
실제 파일에는 전체 파일명이 그대로 들어 있습니다.)

## 4. 동작 원리 (코드 근거)

1. 모드 등록: `*Mode` 블록에서 `dynain_to_initial` 토큰을 만나면
   `modeList`에 `"DYNAIN_TO_INITIAL"`, `modeIDList`에 modeid를 추가
   (`KooMeshModifier.py:306-308`).
2. 옵션 파싱: `**dynaintoinitial` 헤더 이후 라인을 읽어 위 표의 키들을 `curOptions`에 채우고
   `**end` 또는 빈 줄에서 종료(`KooMeshModifier.py:447-512`).
3. dispatch: `GenerateModifiedFile()` 루프에서 `mode == "DYNAIN_TO_INITIAL"`이면
   `GenerateDynainToInitial(modeid)` 호출, 출력 접미어 `additionalword += "_dti"`
   (`KooMeshModifier.py:2852-2854`).
4. 래퍼: `GenerateDynainToInitial`은 `folderPath=self.curDir`,
   `filePath=<curDir>/dynain`을 만들어
   `advancedModification.DynaintoInitial(curOption, folderPath, filePath)` 호출
   (`KooMeshModifier.py:2605-2609`).
5. 핵심 처리 `DynaintoInitial`(`KooDynaAdvancedModification.py:6221-6316`):
   - dynain 경로 결정(`6222-6226`).
   - `RemoveDynamicRelaxation`이면 기존 동적이완 카드 제거(`6241-6242`).
   - 원점 정렬용 노드 3개 결정(자동/노드지정/fallback) 및 회전 행렬 기준점 `P` 구성
     (`6243-6278`).
   - 새 `KooDynaImporter`로 dynain을 import하고 매니저에 적재
     (`6279-6285`).
   - `IncludeStress`에 따라 dynain 또는 원본의 초기조건을 `ClearInitial()`
     (`6287-6290`).
   - `OverwritefromManager(dynainImporter)`로 dynain 상태를 원본 모델에 덮어씀
     (`6292`).
   - 회전이 활성화되면 덮어쓴 뒤의 노드 좌표 `Q`를 구해
     `ApplyTransformfromThreePoints(P, Q, None, True)`로 원점/축 정렬
     (`6294-6300`).
   - `DynamicRelaxation`이 True면 control/database를 clear 후 동적이완 카드 신규 설정
     (`6302-6305`).
   - `RemovePartNameList` / `RemovePartIDList` / `RemoveContactIDList`에 따라
     파트·접촉 제거(`6307-6316`).
6. 출력 쓰기: `_skip_default_write` 플래그를 세우지 않으므로
   기본 `WriteModifiedFile("_dti")`가 실행되어
   `<inputFileName에서 .k 제거>_dti.k`로 저장됨
   (`KooMeshModifier.py:2882-2891`, `2906-2910`).

## 5. 주의사항 · 한계

- `*DynainPath`를 `dynain`으로 두면 현재 디렉터리의 `dynain` 파일을 그대로 사용합니다.
  해당 파일이 없으면 import 단계에서 실패하므로, 선행 해석이 `dynain`을 생성했는지 확인 필요.
- 옵션 키 매칭은 부분 문자열 소문자 비교입니다. 특히 `removedynamicrelaxation` 검사가
  `dynamicrelaxation`보다 먼저 평가되므로(`KooMeshModifier.py:481`, `487`) 의도한 키가
  올바르게 분기됩니다. 다만 사용자 정의 라인 작성 시 오타로 인한 silent miss(기본값 유지)에
  주의해야 합니다.
- `IncludeStress=True`일 때는 원본 모델의 기존 초기조건이 제거되고 dynain의 초기응력만
  남습니다(`KooDynaAdvancedModification.py:6290`). 두 모델의 초기조건을 합성하지는 않습니다.
- 원점 정렬은 세 노드(또는 자동 선정 노드)가 dynain 적용 전후로 동일 ID를 유지한다는 가정에
  의존합니다(`6276` vs `6295-6298`). 정렬 노드가 속한 파트를 제거하는 구성과 함께 쓸 때는
  처리 순서상 정렬이 먼저 수행되므로(`6294-6300` 이후 `6307-` 제거) 결과를 검증 필요.
- 출력 파일명은 입력 파일명에 `_dti` 접미어가 붙습니다. 이 모드를 체인으로 반복 적용하면
  접미어가 누적될 수 있습니다(예제 폴더의 `..._dti_dti.k` 산출물 참고). — 확인 필요.

## 6. 개발 현황

구현됨. 모드 등록(`KooMeshModifier.py:306-308`), 옵션 파싱(`447-512`),
dispatch(`2852-2854`), 래퍼(`2605-2609`), 핵심 로직
(`KooDynaAdvancedModification.py:6221-6316`)이 모두 존재하며,
전용 예제 입력 파일과 실제 산출물(`*_dti.k`, 로그)이 예제 폴더에 함께 존재합니다
(`occProject/Generators/dist/Examples/5.SimulationModify/DynaintoInitial/`,
`.../DynamicRelaxation/`).

비고: scenario.json 기반 호출 경로(누적 러너에서의 호출 형식)는 본 조사 범위에서
직접 확인하지 않았습니다. 본 문서의 입력 형식은 KooMeshModifier 입력 `.txt`(`*Mode`/
`**DynainToInitial` 블록) 기준입니다. — scenario.json 연동은 확인 필요.
</content>
</invoke>
