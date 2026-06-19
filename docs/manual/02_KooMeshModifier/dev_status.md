# KooMeshModifier 개발 현황

> 근거 파일
> - 디스패치/등록부: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooMeshModifier.py`
> - 모드 핸들러 본체: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
> - 계획 문서: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs/PLAN_*.md`
> - git log: `git log --oneline` (HEAD = `177e332`)

---

## 1. 목적 / 개요

본 문서는 `KooMeshModifier`(KMM)가 디스패치하는 **모드별 개발 현황**을 코드 근거와 함께 정리한다.

KMM은 옵션 파일(`*Mode` 블록)에 나열된 모드를 순서대로 동일 모델에 누적 적용한다.
디스패치 루프는 `GenerateModifiedFile()`(KooMeshModifier.py:2781)의 단일 `if/elif mode == ...`
체인(L2786–L2878)으로 구현되어 있으며, 각 분기는 `self.Generate*` 핸들러를 호출하고
대부분의 핸들러는 다시 `self.advancedModification.*`
(= `KooDynaAdvancedModification`, KooMeshModifier.py:55, 83) 의 실제 구현 메서드로 위임한다.

이 문서의 "개발 현황" 판정은 다음 기준을 따른다.

- **구현됨**: 디스패치 분기 + 핸들러 + 실제 변환 로직(또는 위임 대상 모듈/메서드 본체)이 모두 존재.
- **부분구현**: 동작하나 보조 경로가 주석/미연결이거나, 별도 PLAN 에서 "고도화" 항목이 계획 단계로 남아 있음.
- **계획**: 디스패치에 등록되지 않았고 PLAN 문서만 존재.
- **미확인**: 코드만으로 동작 여부를 단정할 수 없음(런타임 의존, 확인 필요).

---

## 2. 입력 옵션 · 인자 (개발 현황 판정에 쓰인 식별 키)

| 항목 | 위치 | 코드 근거 |
|---|---|---|
| 모드 이름→내부 enum 등록 | 옵션 파일 `*Mode` 블록 파서 | KooMeshModifier.py:234–339 |
| 모드 디스패치 체인 | `GenerateModifiedFile()` | KooMeshModifier.py:2783–2878 |
| 위임 대상 클래스 | `KooDynaAdvancedModification` | KooMeshModifier.py:55, 83 |
| 미등록 모드 처리 | `print("Invalid mode"); exit()` | KooMeshModifier.py:337–339 |
| 기본 write 스킵 플래그 | `_skip_default_write` | KooMeshModifier.py:2866, 2869, 2875, 2878, 2883 |

> 참고: 등록부(L234–339)와 디스패치(L2786–2878)는 별개로 유지된다.
> `TRANSFORM`, `THERMAL_LOAD` 등 일부는 디스패치에는 있으나 등록부 분기 위치가 다르므로,
> 한 모드가 양쪽에 모두 존재하는지가 "구현됨" 판정의 1차 조건이다.

---

## 3. 사용 예제

### 3.1 옵션 파일 — DROP_ATTITUDE (발췌)

`Examples/alldropangles/drop_attitude.txt` 원문(가공 없음):

```
*Inputfile
MinimumModel.k
*RunDirectoryMode,True,Data/Results,Data/Metadata
*Info,M1,DV1
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,108.40071741034467,-96.70843214185096,...
EulerPitching,-42.36402149151405,89.103109042852,...
Height,1500,1500,1500,1500,1500
OffsetDistance,0.1
Density,2700
YoungsModulus,70000000000
PoissonRatio,0.3
tFinal,0.001
dt,0.000001
**EndDropAttitude
*End
```

`robust_contact`(최근 작업)는 같은 `**DropAttitude` 블록의 `RobustContact,True` /
`RobustContactTolerance,0.1` 키로 켜진다(파서: KooMeshModifier.py:1526–1531).

### 3.2 옵션 파일 — REMESH_TETRA (발췌)

`Examples/remesh_tetra/step_config.txt` 원문(가공 없음):

```
*Inputfile
model.k
*Mode
REMESH_TETRA,1
**RemeshTetra,1
*PID,100099,35202
*MinDt,1.0e-8
*TargetEdgeLength,0.5
*MaxAspectRatio,10.0
*SmoothingIterations,5
*PreserveSharedNodes,True
**EndRemeshTetra
*End
```

### 3.3 CLI 실행

```
python KooMeshModifier.py <option.txt> [working_dir]
```

(진입점 인자 분기: KooMeshModifier.py:3142–3147. 실제 파이프라인에서는
`KooChainRun`이 `scenario.json`을 위 옵션 파일로 변환해 호출한다.)

---

## 4. 동작 원리 (코드 근거)

디스패치 루프는 등록된 모드를 순회하며 모드명에 대응하는 핸들러를 호출하고
접미사(`additionalword`)를 누적한 뒤, 마지막에 `WriteModifiedFile(additionalword)`로
`<원본>_<접미사>.k` 를 출력한다(KooMeshModifier.py:2783–2888).

- 분기 본체: `if mode == "ELASTIC_TO_RIGID": ... elif ...`
  (KooMeshModifier.py:2786–2878).
- 출력 자체를 핸들러가 직접 수행하는 모드는 `_skip_default_write = True`로
  공용 write 를 우회한다(예: `DECOMPOSE_K` L2866, `MERGE_K` L2869,
  `VIBRATION_LOAD` L2875, `THERMAL_LOAD` L2878 → 스킵 처리 L2883–2884).
- 대부분 핸들러는 1–2줄 위임자다. 예:
  `GenerateRemeshTetra`(KooMeshModifier.py:2552) →
  `advancedModification.RemeshTetra`(KooDynaAdvancedModification.py:5052) →
  `KooTetraRemesher.remesh_tetra_parts`(gmsh 기반, KooTetraRemesher.py:49).
- `ELASTIC_TO_RIGID`(KooMeshModifier.py:2501) 와
  `PART_EXCHANGE`(KooMeshModifier.py:2626)는 핸들러 내부에 변환 로직을 직접 보유한다.

---

## 5. 주의사항 · 한계

- 등록부(L234–339)와 디스패치(L2786–2878)가 이원화되어 있어, 새 모드 추가 시
  **두 곳을 모두 수정**해야 한다. 한쪽만 추가하면 "Invalid mode"(L338) 또는
  무동작이 된다.
- `import_merge_k`는 `merge_k` 부분문자열 충돌을 피하려 먼저 검사한다
  (등록부 L330–336 주석).
- `SIMULATION_AUTOMATION`은 현재 `generate_for_all()` 경로만 활성이며,
  구버전 분기(`SimulationAutomationPrevious`)는 `run_*` 호출이 주석 처리되어
  `print`만 한다(KooDynaAdvancedModification.py:6396–6437) — 이 구버전 경로는
  사용하지 말 것.
- `REMESH_TETRA`/`PART_VALIDATION_SPLIT` 등 외부 의존(gmsh) 모드는 gmsh 바이너리
  탐색에 의존한다(KooTetraRemesher.py:91, `_find_linux_gmsh`). 실행 환경 확인 필요.

---

## 6. 개발 현황

### 6.1 모드별 현황 표

판정 근거 표기: `M:<라인>` = KooMeshModifier.py 디스패치/핸들러 라인,
`A:<라인>` = KooDynaAdvancedModification.py 위임 메서드 라인.

| 모드 | 현황 | 비고 / 근거 |
|---|---|---|
| ELASTIC_TO_RIGID | 구현됨 | 핸들러 내 직접 변환(matManager.ExchangetoRigid). M:2786/2501 |
| MATERIAL_EXCHANGE | 구현됨 | A:4858 `MaterialExchange`. M:2789/2518 |
| PART_LOCATION_DOE | 구현됨 | A:4900 `PartLocationDOE`. M:2792/2525 |
| ERODING_MIN_DT | 구현됨 | A:5186 `ErodingMinDT`(AddErosion dtmin). M:2795/2532 |
| RIGIDIFY_SMALL_DT | 구현됨 | partManager.RigidifySmallDtElements 직접 호출. M:2798/2537 |
| REMESH_TETRA | 부분구현 | 기본 gmsh 리메시 동작(A:5052 → KooTetraRemesher.py:49). 단 "외곽면 품질+최소 dt 보장 고도화"는 계획 단계(PLAN_AutomationInventory_ThermalSimulation.md:66, `project_remesh_tetra_plan.md`). M:2801/2552 |
| PART_VALIDATION_SPLIT | 구현됨 | A:5181 → KooPartValidator.split_parts_for_validation. git 6502e14("전체 워크플로우"). M:2804/2556 |
| PART_EXCHANGE | 구현됨 | 핸들러 내 직접 변환(section/mat 치환, Hexa/구조화 변환). M:2807/2626 |
| REMOVE_DUPLICATE_TIED_CONTACTS | 구현됨 | A:6439 → contactManager.RemoveDuplicateTiedContacts. M:2810/2459 |
| WEAK_COUPLING | 구현됨 | A:109 `WeakCoupling`. M:2813/2463 |
| DEFEATURE_MESH | 구현됨 | A:171 `DefeatureMesh`. M:2816/2467 |
| DROP_ATTITUDE | 구현됨 | A:2035 `DropAttitude`(robust_contact 포함, A:2334~2635). M:2819/2471 |
| TRANSLATION_DOE | 구현됨 | A:6331 `TranslationDOE`(FastDOE 캐시 경로 포함). M:2822/2491 |
| TRANSFORM | 구현됨 | A:3081 `Transform`. M:2825/2497 |
| DROP_WEIGHT_IMPACT_TEST | 구현됨 | 3개 서브모드 분기(DampingSpring/OutsideRigid*/Part) A:3596/3185/4412. M:2828/2478 |
| PART_MORPHING | 구현됨 | A:5570 `PartMorphing`. M:2831/2615 |
| CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | 구현됨 | A:5192 `ConstrainedNodalRigidBodyToBeam`. M:2834/2561 |
| CONVERT_CNRB_TO_SOLID | 구현됨 | A:5224 `ConvertCNRBtoSolidCylinder`. git 5b35104. M:2837/2565 |
| WARPED_PART | 구현됨 | A:5692 `WarpedPart`. M:2840/2569 |
| WARPED_TO_INITIAL_STRESS_PART | 구현됨 | A:5744 `WarpedtoInitialStressPart`. M:2843/2573 |
| DIMENSIONAL_TOLERANCE | 구현됨 | A:5820 `DimensionalTolerance`(List/Norm/LHS 변형 A:5830/5895/5996). M:2846/2577 |
| COHESIVE_BETWEEN_CONFORMAL_MESHES | 구현됨 | A:6126 `CohesiveBetweenConformalMeshes`(공유노드 기반 cohesive shell). M:2849/2583 |
| DYNAIN_TO_INITIAL | 구현됨 | A:6221 `DynaintoInitial`. M:2852/2605 |
| CONTACT_AUTO_DECOMPOSITION | 구현됨 | A:6319 `ContactAutoDecomposition`(ASS5→ASTS pair). M:2855/2587 |
| SIMULATION_AUTOMATION | 부분구현 | 활성 경로 A:6392 `generate_for_all()`만 동작. 구버전 A:6396 `...Previous`는 `run_*` 주석 처리(print만). M:2858/2591 |
| FEM_TO_IGA | 구현됨 | A:6447 `FEMtoIGA`. PLAN_IncludeAndIGA.md 참조. M:2861/2611 |
| DECOMPOSE_K | 구현됨 | A:5057 → KooKFileDecomposer.decompose_k_file. git 909c7e0(v1.2.0). M:2864/2435 |
| MERGE_K | 구현됨 | A:5062 → KooKFileMerger.merge_k_file. git 909c7e0. M:2867/2439 |
| IMPORT_MERGE_K | 구현됨 | A:5067 → KooImportMerger.import_merge_k. git 909c7e0. M:2870/2443 |
| VIBRATION_LOAD | 구현됨 | A:5072 → KooVibrationLoad.apply_vibration_load + RunDirectoryMode write. git 94c8ea2/5b6f8b3/381ba31. M:2873/2447 |
| THERMAL_LOAD | 구현됨 | A:5124 `ThermalLoad`(LOAD_THERMAL_VARIABLE+CTE). git 177e332. M:2876/2453 |

### 6.2 디스패치에 미등록된 계획 항목

| 항목 | 현황 | 근거 |
|---|---|---|
| Conformal Mesh Generation (Hexa Core + Tetra Buffer) | 계획 | `PLAN_ConformalMeshGeneration.md`. 대상은 **KooAutomatedModeller PKG 모드**이며 KMM 디스패치 모드가 아님(L6 "KooAutomatedModeller의 PKG 모드에 추가"). KMM 측 `COHESIVE_BETWEEN_CONFORMAL_MESHES`(별개 모드)와 혼동 주의 |
| REMESH_TETRA 고도화 | 계획 | PLAN_AutomationInventory_ThermalSimulation.md:66 "계획 단계", `project_remesh_tetra_plan.md` (외곽면 품질 + 최소 dt 보장) |
| vibration `cap_combination` / `curve_library` | 계획(미연결) | PLAN_AutomationInventory_ThermalSimulation.md:65 "registry 주석 상태" (확인 필요 — 본 작업에서 registry 본체 미열람) |

### 6.3 최근 작업 반영 요약 (git log 근거)

- **robust_contact** (a950006, 9f5f8fe, da32983 등): `DROP_ATTITUDE` 내부에 Segment Set
  방식으로 전면 재구현. Tied 인터페이스 면 제외 SINGLE_SURFACE 교체, SOFT=2/DEPTH=3
  강제, tolerance 기본 0.1mm. 코드: KooDynaAdvancedModification.py:2412–2635,
  옵션 파서 KooMeshModifier.py:1526–1531.
- **RIGIDIFY_SMALL_DT / PART_VALIDATION_SPLIT** (6502e14, 032021b): 신규 모드 + 워크플로우.
- **DECOMPOSE_K / MERGE_K / IMPORT_MERGE_K** (909c7e0, v1.2.0): 파일 분해·병합·import.
- **VIBRATION_LOAD** (94c8ea2 → 381ba31): 진동 하중 카드 + RunDirectoryMode write 정착.
- **THERMAL_LOAD + 3단 실린더 충격추** (177e332, HEAD): 고온 열응력 자동화.

---

## 7. 확인 필요

- `vibration` registry의 `cap_combination`/`curve_library` 주석 상태는 PLAN 문서
  표기에 의존했으며, registry 본체 코드는 본 작업에서 직접 열람하지 않았다(확인 필요).
- 각 위임 메서드의 **런타임 정상 동작**(gmsh 등 외부 의존 포함)은 정적 코드 존재로만
  판정했다. e2e PASS가 git 메시지에 명시된 모드(VIBRATION_LOAD, THERMAL_LOAD, IMPACT)
  외 모드의 실행 검증은 본 문서 범위를 벗어난다.
