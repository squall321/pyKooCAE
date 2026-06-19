# KooMeshModifier 모드 카탈로그

> 근거 파일: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooMeshModifier.py`
> 모드 등록부(`*mode` 블록 파싱): L234–L339 / 모드 디스패치 루프: L2783–L2880
> 핸들러 메서드: `Generate*` (L2435–L2780) / 모듈 docstring: "KooMeshModifier (KMM) - LS-DYNA Model Transformation & Mesh Modification Engine" (L1–L14)
> CLI 진입점: `if __name__ == "__main__"` L3014–L3168

---

## 1. 목적 / 개요

`KooMeshModifier`(KMM)는 **LS-DYNA 키워드(.k) 파일을 읽어 모드 기반 변환을 적용한 뒤
수정된 .k 모델을 출력하는 모델 변환·메시 수정 엔진**이다. 모듈 docstring은
"Reads LS-DYNA keyword (.k) files, applies mode-based transformations (drop attitude,
material exchange, part relocation, etc.), and outputs modified models for
sequential/chained CAE simulations" 라고 정의한다(L4–L6).

KMM은 단독 실행도 가능하지만, 실제 파이프라인에서는 `KooChainRun`이 사용자의
`scenario.json`을 KMM **옵션 파일(.txt)**로 변환해 호출하는 전처리 단계로 동작한다
(`KooChainRun` → `KooMeshModifier` → LS-DYNA → dynain 흐름).

### 실행 방식 (입력 .k 기반)

CLI 진입점(L3014–L3168)은 인자 개수로 동작을 분기한다.

- `python KooMeshModifier.py <option.txt> [working_dir]` (L3142–L3147)
- 인자 1개면 작업 디렉토리는 현재 경로(L3144), 2개면 두 번째 인자(L3147)

실행 플로우(L3157–L3167):

1. `ImportOption(option.txt)` — 옵션 파일을 파싱(L154~). `*Inputfile` 다음 줄에서 **변환 대상 .k 파일명**을 읽고(L163–L166), `*Mode` 블록에서 적용할 모드들을 등록하며(L234~), 각 `**ModeName,id … **EndModeName` 블록에서 모드별 옵션을 읽는다.
2. `ImportBaseFile()` — `*Inputfile`로 지정한 **베이스 .k 모델을 메모리로 로드**한다(L3163).
3. `GenerateModifiedFile()` — 등록된 모드를 순서대로 디스패치 실행하고(L2781~, 루프 L2783), 결과를 `<원본>_<접미사>.k`로 저장한다(`WriteModifiedFile`, L2906~).

즉 **입력은 항상 `.k` (베이스 모델) + 옵션 파일(`.txt`)** 두 가지이며, 모드는 `*Mode` 블록에
나열한 순서대로 동일 모델에 누적 적용된다(`for i in range(len(self.modeList))`, L2783).

---

## 2. 입력 옵션 · 인자 (옵션 파일 구조)

`ImportOption`(L154)이 파싱하는 옵션 파일의 최상위 키워드.

| 키워드 | 의미 | 코드 근거 |
|---|---|---|
| `*Inputfile` | 다음 줄에 변환 대상 베이스 `.k` 파일명 | L163–L166 |
| `*Inputobjfile` | (선택) obj 입력 파일명 | L167–L170 |
| `*Step` | (선택) 누적 시뮬레이션 단계 번호 | L171–L174 |
| `rundirectorymode` | (선택) `True/False` + 런/메타 디렉토리 경로 | L175–L184 |
| `*Info` | (선택) 모델 메타데이터(name, revision …) | L185~ |
| `*Mode` | 적용할 모드 목록 블록. 각 줄 `MODE_NAME,modeID` | L234–L340 |
| `**<ModeName>,<id>` … `**End<ModeName>` | 모드별 세부 옵션 블록 | 각 모드 파서(L341~) |
| `*End` | 옵션 파일 종료 | L161 |

`*Mode` 블록 안의 각 줄은 `이름,정수ID` 형식이며, 이름을 소문자로 비교해
`self.modeList`/`self.modeIDList`에 등록한다(L242–L339). 미등록 이름이면
`"Invalid mode"` 출력 후 종료한다(L337–L339).

> 주의: `import_merge_k`는 `merge_k` 부분문자열 충돌을 피하려 먼저 검사한다(L330–L336).

---

## 3. 사용 예제

### 3-1. KooMeshModifier 옵션 파일 (.txt) — DROP_WEIGHT_IMPACT_TEST

출처: `occProject/Generators/dist/Examples/5.SimulationModify/DropWeightImpactTest.txt` (발췌, 가공 없음)

```
*Inputfile
MultiscaleTest_1_unitfeature.k
*Mode
DROP_WEIGHT_IMPACT_TEST,1
**DropWeightImpactTest,1
BoundaryDistance,0.0
LocationX,0.02,0.01
LocationY,0.00,0.01
Height,0.5,0.5
tFinal,0.001
YoungModulusDamper,70e9
PoissonRatioDamper,0.3
Density,2700
YoungModulus,201e9
Type,Sphere
DimensionDamper,0.0001,0.0001,0.01
Dimension,0.008
MeshSize,0.001
**EndDropWeightImpactTest
*End
```

### 3-2. 여러 모드 누적 — ELASTIC_TO_RIGID + PART_EXCHANGE

출처: `occProject/Generators/dist/Examples/5.SimulationModify/ElasticToRigidOption.txt` (발췌)

```
*Inputfile
Impact_1_00000001.k
*Mode
ELASTIC_TO_RIGID,1
PART_EXCHANGE,2
**ElastictoRigid,1
*PIDExcept,5
**EndElastictoRigid
**PartExchange,2
*PID,5
*SECTION_SOLID_TITLE
...
**EndPartExchange
*End
```

`*Mode` 블록에 두 모드를 나열하면 등록 순서대로(L2783 루프) 같은 모델에 차례로 적용된다.

### 3-3. CLI 호출

```bash
python KooMeshModifier.py DropWeightImpactTest.txt /작업/디렉토리
```

(인자 분기 L3142–L3147)

### 3-4. 상위 워크플로우(scenario.json)와의 관계

`KooChainRun`의 `scenario.json`(예: `Examples/drop_weight_impact/scenario_part_center.json`)은
`"mode": "drop_weight_impact"` 등 고수준 입력을 받아 내부적으로 위 옵션 파일(.txt)을 만들어
KMM을 호출한다. scenario.json 자체는 KMM이 직접 읽는 입력이 아니다(KMM 입력은 .txt + .k).

---

## 4. 전체 모드 카탈로그 (~31개)

등록부(`*mode` 파서) L242–L336 / 디스패치 L2786–L2878 기준. 총 31개 모드.
"문서링크"는 카테고리별 상세 문서 디렉토리(`modes/<카테고리>/`, 현재 미작성)를 가리킨다.

| # | 모드명(`*Mode` 표기) | 카테고리 | 한줄 설명 | 핸들러 (file:line) | 문서링크 |
|---|---|---|---|---|---|
| 1 | `DROP_ATTITUDE` | drop_impact | 낙하 자세(각도/높이/바닥면)로 모델 회전·초기속도 부여 | `GenerateDropAttitude` (L2471) | [drop_impact/](modes/drop_impact/) |
| 2 | `DROP_WEIGHT_IMPACT_TEST` | drop_impact | 충격추(구/실린더) 생성 + 낙하 충격 시험 셋업 | `GenerateDropWeightImpactTest` (L2478) | [drop_impact/](modes/drop_impact/) |
| 3 | `TRANSLATION_DOE` | drop_impact | 낙하/이동 위치 DOE 변형 생성 | `GenerateTranslationDOE` (L2491) | [drop_impact/](modes/drop_impact/) |
| 4 | `VIBRATION_LOAD` | loads | 진동(base motion) 하중 카드 생성 | `GenerateVibrationLoad` (L2447) | [loads/](modes/loads/) |
| 5 | `THERMAL_LOAD` | loads | 고온 열응력(THERMAL_LOAD/온도곡선·CTE) 하중 생성 | `GenerateThermalLoad` (L2453) | [loads/](modes/loads/) |
| 6 | `WEAK_COUPLING` | loads | 약결합(weak coupling) 하중 전달 셋업 | `GenerateWeakCoupling` (L2463) | [loads/](modes/loads/) |
| 7 | `DEFEATURE_MESH` | mesh_ops | 메시 디피처링(미세 특징 제거) | `GenerateDefeatureMesh` (L2467) | [mesh_ops/](modes/mesh_ops/) |
| 8 | `REMESH_TETRA` | mesh_ops | 사면체 외곽면 리메시(gmsh) + 최소 dt 개선 | `GenerateRemeshTetra` (L2552) | [mesh_ops/](modes/mesh_ops/) |
| 9 | `ERODING_MIN_DT` | mesh_ops | 최소 시간간격 이하 요소 erosion 처리 | `GenerateErodingMinDT` (L2532) | [mesh_ops/](modes/mesh_ops/) |
| 10 | `RIGIDIFY_SMALL_DT` | mesh_ops | stable dt 이하 요소를 MAT_RIGID로 강체화 | `GenerateRigidifySmallDT` (L2537) | [mesh_ops/](modes/mesh_ops/) |
| 11 | `DIMENSIONAL_TOLERANCE` | mesh_ops | 치수 공차(절점 위치) DOE 변형 | `GenerateDimensionalTolerance` (L2577) | [mesh_ops/](modes/mesh_ops/) |
| 12 | `PART_MORPHING` | mesh_ops | 파트 형상 모핑(+선택적 재메시) | `GeneratePartMorphing` (L2615) | [mesh_ops/](modes/mesh_ops/) |
| 13 | `WARPED_PART` | mesh_ops | 휨(warpage) 형상을 파트에 반영 | `GenerateWarpedPart` (L2569) | [mesh_ops/](modes/mesh_ops/) |
| 14 | `WARPED_TO_INITIAL_STRESS_PART` | mesh_ops | 휨 형상→초기응력 파트로 변환 | `GenerateWarpedtoInitialStressPart` (L2573) | [mesh_ops/](modes/mesh_ops/) |
| 15 | `ELASTIC_TO_RIGID` | material_part | 탄성 재료 파트를 MAT_RIGID로 교체 + 강체 구속 | `GenerateElasticToRigid` (L2501) | [material_part/](modes/material_part/) |
| 16 | `MATERIAL_EXCHANGE` | material_part | 파트 재료 카드 교체 | `GenerateMaterialExchange` (L2518) | [material_part/](modes/material_part/) |
| 17 | `PART_EXCHANGE` | material_part | 파트 단면/재료/요소 형식 교체(solid↔shell/tshell 등) | `GeneratePartExchange` (L2626) | [material_part/](modes/material_part/) |
| 18 | `CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM` | material_part | CNRB(절점 강체 구속)를 beam 요소로 변환 | `GenerateConstrainedNodalRigidBodyToBeam` (L2561) | [material_part/](modes/material_part/) |
| 19 | `CONVERT_CNRB_TO_SOLID` | material_part | CNRB를 솔리드(실린더)로 변환 | `GenerateConvertCNRBtoSolid` (L2565) | [material_part/](modes/material_part/) |
| 20 | `COHESIVE_BETWEEN_CONFORMAL_MESHES` | material_part | 정합 메시 사이 cohesive 요소 삽입 | `GenerateCohesiveBetweenConformalMeshes` (L2583) | [material_part/](modes/material_part/) |
| 21 | `FEM_TO_IGA` | material_part | FEM 메시를 IGA(등기하해석)로 변환 | `GenerateFEMtoIGA` (L2611) | [material_part/](modes/material_part/) |
| 22 | `PART_LOCATION_DOE` | doe_transform | 파트 위치 DOE 변형 생성 | `GeneratePartLocationDOE` (L2525) | [doe_transform/](modes/doe_transform/) |
| 23 | `TRANSFORM` | doe_transform | 모델 좌표 변환(회전/이동/스케일) | `Transform` (L2497) | [doe_transform/](modes/doe_transform/) |
| 24 | `DECOMPOSE_K` | k_io | .k 파일을 분할(별도 출력, 기본 write 생략) | `GenerateDecomposeK` (L2435) | [k_io/](modes/k_io/) |
| 25 | `MERGE_K` | k_io | 분할된 .k들을 병합(별도 출력) | `GenerateMergeK` (L2439) | [k_io/](modes/k_io/) |
| 26 | `IMPORT_MERGE_K` | k_io | 외부 .k를 import해 현재 모델에 병합 | `GenerateImportMergeK` (L2443) | [k_io/](modes/k_io/) |
| 27 | `DYNAIN_TO_INITIAL` | k_io | dynain(결과 응력/변형)을 초기상태 카드로 변환 | `GenerateDynainToInitial` (L2605) | [k_io/](modes/k_io/) |
| 28 | `PART_VALIDATION_SPLIT` | validation_contact | 파트별 독립 .k 분할 + 0도 낙하 검증용 | `GeneratePartValidationSplit` (L2556) | [validation_contact/](modes/validation_contact/) |
| 29 | `REMOVE_DUPLICATE_TIED_CONTACTS` | validation_contact | 중복된 tied 접촉 제거 | `GenerateRemoveDuplicateTiedContacts` (L2459) | [validation_contact/](modes/validation_contact/) |
| 30 | `CONTACT_AUTO_DECOMPOSITION` | validation_contact | 접촉 기반 도메인 자동 분해 | `GenerateContactAutoDecomposition` (L2587) | [validation_contact/](modes/validation_contact/) |
| 31 | `SIMULATION_AUTOMATION` | automation | scenario JSON 기반 다단계 시뮬레이션 자동화 | `GenerateSimulationAutomation` (L2591) | [automation/](modes/automation/) |

> 위 표는 등록부(L244–L335)의 31개 고유 모드와 1:1 일치한다(`DIMENSIONAL_TOLERANCE`는 #11에 한 번만 등재).
> 31개 목록 확인: DROP_ATTITUDE, DROP_WEIGHT_IMPACT_TEST, TRANSLATION_DOE, VIBRATION_LOAD,
> THERMAL_LOAD, WEAK_COUPLING, DEFEATURE_MESH, REMESH_TETRA, ERODING_MIN_DT, RIGIDIFY_SMALL_DT,
> DIMENSIONAL_TOLERANCE, PART_MORPHING, WARPED_PART, WARPED_TO_INITIAL_STRESS_PART, ELASTIC_TO_RIGID,
> MATERIAL_EXCHANGE, PART_EXCHANGE, CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM, CONVERT_CNRB_TO_SOLID,
> COHESIVE_BETWEEN_CONFORMAL_MESHES, FEM_TO_IGA, PART_LOCATION_DOE, TRANSFORM, DECOMPOSE_K, MERGE_K,
> IMPORT_MERGE_K, DYNAIN_TO_INITIAL, PART_VALIDATION_SPLIT, REMOVE_DUPLICATE_TIED_CONTACTS,
> CONTACT_AUTO_DECOMPOSITION, SIMULATION_AUTOMATION = **31개** (`grep self.modeList.append` L244–L335 일치).

### 카테고리 분류 근거(확인 필요 표기)

- 카테고리(drop_impact / loads / mesh_ops / material_part / doe_transform / k_io /
  validation_contact / automation)는 **문서 디렉토리 구조**(`modes/<카테고리>/`, L: docs 트리)와
  모드 핸들러 동작에 근거해 분류했다. 코드 자체에는 카테고리 enum이 없으므로(등록부는 평면 리스트, L242~)
  일부 경계(예: `TRANSLATION_DOE`를 drop_impact vs doe_transform)는 동작 의미 기준 판단이다 — **확인 필요**.

---

## 5. 동작 원리 (코드 근거)

1. **옵션 파싱**: `ImportOption`(L154)이 `*Inputfile`로 베이스 .k 파일명을 잡고(L163–L166),
   `*Mode` 블록에서 줄 단위로 `MODE,id`를 읽어 `self.modeList`/`self.modeIDList`에 등록한다
   (L242–L339). 각 모드의 `**<Name>` 블록은 별도 분기에서 `self.modeIDOption[modeid]`로 저장된다.
2. **베이스 로드**: `ImportBaseFile()`(L3163 호출)이 .k를 `dynaImporter`의 각 매니저(Node/Element/Part/
   Material/Section/Contact …, L61–L76)로 적재한다.
3. **모드 디스패치**: `GenerateModifiedFile`(L2781)의 루프(L2783)가 `self.modeList[i]` 문자열을
   `if mode == "..."` 체인으로 비교해(L2786–L2878) 대응 `Generate*` 핸들러를 호출한다.
   대부분의 핸들러는 `self.advancedModification`(KooDynaAdvancedModification, L55·L83)에 위임한다.
4. **ID 동기화·출력**: 각 모드 후 `SyncronizeMaxID()`(L2880)로 ID 충돌을 방지하고,
   `_skip_default_write`가 아니면 `WriteModifiedFile(additionalword)`로 `<원본><접미사>.k`를 저장한다
   (L2883–L2891). `DECOMPOSE_K`/`MERGE_K`/`VIBRATION_LOAD`/`THERMAL_LOAD`는 자체 출력을 하므로
   기본 write를 건너뛴다(`_skip_default_write = True`, L2866·L2869·L2875·L2878).

각 모드에 부여되는 출력 파일 접미사(`additionalword`)는 디스패치에서 모드별로 누적된다
(예: `_drop`, `_dwit`, `_etor`, `_pex`, L2788~L2872).

---

## 6. 주의사항 · 한계

- **입력은 옵션 .txt + 베이스 .k 두 개가 필수**다. scenario.json은 KMM 직접 입력이 아니며
  KooChainRun이 .txt로 변환한 뒤 호출한다(§3-4).
- `*Mode`에 미등록 모드명을 적으면 `"Invalid mode"` 출력 후 즉시 `exit()` 한다(L337–L339).
- `import_merge_k`/`merge_k`처럼 부분문자열이 겹치는 모드명은 파서 순서에 의존한다
  (`import_merge_k`를 먼저 검사, L330–L336) — 신규 모드명 추가 시 충돌 주의.
- `DECOMPOSE_K`/`MERGE_K`는 기본 .k write를 생략하므로 출력 경로/형식이 다른 모드와 다르다
  (L2864–L2869, `_skip_default_write`).
- 다수 핸들러가 `KooDynaAdvancedModification`(외부 모듈)에 위임하므로, 본 카탈로그의 한줄 설명은
  KMM 측 호출부 기준이다. 각 모드의 세부 알고리즘·옵션 키는 해당 모듈 및 예제 .txt에서
  추가 확인이 필요하다 — **확인 필요**.

---

## 7. 개발 현황

**구현됨.**

근거:
- 31개 모드 전부 `*mode` 등록부(L244–L335)와 디스패치(L2786–L2878)에 코드로 존재하며,
  각각 대응하는 `Generate*` 핸들러(L2435–L2780)가 정의되어 있다.
- 실제 옵션 파일 예제가 `occProject/Generators/dist/Examples/5.SimulationModify/`에 다수 존재한다
  (DropWeightImpactTest.txt, ElasticToRigidOption.txt 등, §3 발췌).
- 일부 신규 모드(`REMESH_TETRA`, `VIBRATION_LOAD`, `THERMAL_LOAD`)는 최근 커밋 이력
  (git log: vibration/thermal feat 커밋)에서 활성 개발 중임이 확인된다.

단, 본 카탈로그의 **카테고리 분류**와 **모드별 세부 옵션 사양**은 코드 카테고리 enum 부재로
일부 동작 의미 기반 추정이 포함되어 있어 모드별 상세 문서(`modes/<카테고리>/`)에서 확정이 필요하다.
