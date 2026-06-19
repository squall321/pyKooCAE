# pyKooCAE 매뉴얼

전자패키지/HW(PKG·PBA·PCB)의 **낙하·충격·진동·열** CAE 해석을 자동 생성부터 대량 시뮬레이션, 후처리까지 일괄 처리하는 도구 모음(pyKooCAE)의 통합 매뉴얼입니다.

pyKooCAE는 Nuitka로 컴파일된 단일 바이너리 형태의 3개 도구로 구성되며, Slurm 클러스터와 Apptainer(SIF) 컨테이너 환경에서 동작합니다.

---

## 3개 도구 한눈에

| 도구 | 역할 | 입력 → 출력 | 매뉴얼 |
|------|------|-----------|--------|
| **KooChainRun** | CAE 시뮬레이션 오케스트레이션 CLI. 시나리오 준비 → Slurm 제출 → 상태 추적 → 결과 수집 → 후처리까지 워크플로우 전체를 제어 | `scenario.json` → Slurm 작업 → 결과/리포트 | [01_KooChainRun](01_KooChainRun/README.md) |
| **KooMeshModifier** | LS-DYNA `.k` 모델 변형 엔진. 낙하 자세, 메시 연산, 재료/파트 교체, DOE 변환, 하중 부여 등 30여 개 모드 제공 | 입력 `.k` + 제어 `.txt` → 변형된 `.k` | [02_KooMeshModifier](02_KooMeshModifier/README.md) |
| **KooAutomatedModeller** | CAD/ECAD(ODB++) 기반 형상 자동 모델러. PKG/PBA/PCB/커패시터 등 패키지 형상을 생성하고 LS-DYNA `.k`·STEP으로 출력 | ODB++/정의파일 → `.k` + STEP | [03_KooAutomatedModeller](03_KooAutomatedModeller/README.md) |

일반적인 파이프라인:

```
KooAutomatedModeller        KooMeshModifier            KooChainRun
(CAD/ECAD → .k, STEP)  →   (.k 변형: 자세/메시/하중)  →  (DOE 생성 → Slurm 대량 실행 → 후처리)
```

---

## 매뉴얼 목차

### 00 · 개요 (Overview)

| 문서 | 설명 |
|------|------|
| [pyKooCAE 아키텍처 개요](00_overview/architecture.md) | 3개 도구 구조, 데이터 흐름, 배포 형태 |
| [빌드 · 배포 가이드](00_overview/install_build.md) | Nuitka 빌드 스크립트, 배포 대상, SIF 패키징 |
| [용어집](00_overview/glossary.md) | 핵심 용어 · 약어 정의 |

### 01 · KooChainRun (오케스트레이션 CLI)

| 문서 | 설명 |
|------|------|
| [KooChainRun 개요 · 커맨드 맵](01_KooChainRun/README.md) | 전체 커맨드 구조와 워크플로우 라우팅 |
| [scenario.json 레퍼런스](01_KooChainRun/scenarios/scenario_reference.md) | 시나리오 정의 파일 키 전체 레퍼런스 |
| [DOE · 위치/각도 소스](01_KooChainRun/doe_methods/doe_methods.md) | grid/lhs/part_center/spacing 등 DOE 생성 방법 |
| [후처리 자동화 (deep/sphere/impact)](01_KooChainRun/postprocess/postprocess.md) | deep·sphere·impact 리포트 자동 후처리 파이프라인 |
| [KooChainRun 개발 현황](01_KooChainRun/dev_status.md) | 구현/부분구현/미구현 현황 |

**커맨드 레퍼런스**

| 커맨드 | 설명 |
|--------|------|
| [prepare](01_KooChainRun/commands/prepare.md) | `scenario.json` → `runner_config.json` 변환 |
| [submit](01_KooChainRun/commands/submit.md) | Slurm 작업 제출 |
| [status](01_KooChainRun/commands/status.md) | 작업 진행 상태 조회 |
| [run](01_KooChainRun/commands/run.md) | 로컬/직접 실행 |
| [collect](01_KooChainRun/commands/collect.md) | 결과 수집 |
| [stop](01_KooChainRun/commands/stop.md) | 작업 취소 |
| [rerun](01_KooChainRun/commands/rerun.md) | 실패 작업 재실행 |
| [diagnose](01_KooChainRun/commands/diagnose.md) | 실패 원인 진단 |
| [postprocess](01_KooChainRun/commands/postprocess.md) | 후처리 작업 제출 |

**예제**

| 문서 | 설명 |
|------|------|
| [전각도 낙하 (DROP)](01_KooChainRun/examples/full_angle_drop.md) | 전 각도 낙하 시뮬레이션 e2e 예제 |
| [전위치 부분충격 (IMPACT)](01_KooChainRun/examples/partial_impact.md) | 전 위치 부분 충격 시뮬레이션 e2e 예제 |

### 02 · KooMeshModifier (`.k` 변형 엔진)

| 문서 | 설명 |
|------|------|
| [KooMeshModifier 모드 카탈로그](02_KooMeshModifier/README.md) | 전체 모드 목록과 카테고리 분류 |
| [입력 `.k` 블록 문법](02_KooMeshModifier/input_format.md) | 입력 `.k`/제어 `.txt`의 `*Mode`·`**옵션` 블록 문법 |
| [KooMeshModifier 개발 현황](02_KooMeshModifier/dev_status.md) | 모드별 구현/부분구현 현황 |

**모드 카탈로그 (카테고리별)**

| 카테고리 | 모드 |
|----------|------|
| 낙하·충격 (drop_impact) | [DROP_ATTITUDE](02_KooMeshModifier/modes/drop_impact/DROP_ATTITUDE.md) · [DROP_WEIGHT_IMPACT_TEST](02_KooMeshModifier/modes/drop_impact/DROP_WEIGHT_IMPACT_TEST.md) |
| 하중 (loads) | [VIBRATION_LOAD](02_KooMeshModifier/modes/loads/VIBRATION_LOAD.md) · [THERMAL_LOAD](02_KooMeshModifier/modes/loads/THERMAL_LOAD.md) |
| 메시 연산 (mesh_ops) | [REMESH_TETRA](02_KooMeshModifier/modes/mesh_ops/REMESH_TETRA.md) · [DEFEATURE_MESH](02_KooMeshModifier/modes/mesh_ops/DEFEATURE_MESH.md) · [RIGIDIFY_SMALL_DT](02_KooMeshModifier/modes/mesh_ops/RIGIDIFY_SMALL_DT.md) · [ERODING_MIN_DT](02_KooMeshModifier/modes/mesh_ops/ERODING_MIN_DT.md) · [CONVERT_CNRB_TO_SOLID](02_KooMeshModifier/modes/mesh_ops/CONVERT_CNRB_TO_SOLID.md) · [CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM](02_KooMeshModifier/modes/mesh_ops/CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM.md) · [COHESIVE_BETWEEN_CONFORMAL_MESHES](02_KooMeshModifier/modes/mesh_ops/COHESIVE_BETWEEN_CONFORMAL_MESHES.md) · [FEM_TO_IGA](02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md) |
| 재료·파트 (material_part) | [ELASTIC_TO_RIGID](02_KooMeshModifier/modes/material_part/ELASTIC_TO_RIGID.md) · [MATERIAL_EXCHANGE](02_KooMeshModifier/modes/material_part/MATERIAL_EXCHANGE.md) · [PART_EXCHANGE](02_KooMeshModifier/modes/material_part/PART_EXCHANGE.md) · [PART_MORPHING](02_KooMeshModifier/modes/material_part/PART_MORPHING.md) · [WARPED_PART](02_KooMeshModifier/modes/material_part/WARPED_PART.md) · [WARPED_TO_INITIAL_STRESS_PART](02_KooMeshModifier/modes/material_part/WARPED_TO_INITIAL_STRESS_PART.md) · [DIMENSIONAL_TOLERANCE](02_KooMeshModifier/modes/material_part/DIMENSIONAL_TOLERANCE.md) |
| DOE·변환 (doe_transform) | [PART_LOCATION_DOE](02_KooMeshModifier/modes/doe_transform/PART_LOCATION_DOE.md) · [TRANSLATION_DOE](02_KooMeshModifier/modes/doe_transform/TRANSLATION_DOE.md) · [TRANSFORM](02_KooMeshModifier/modes/doe_transform/TRANSFORM.md) |
| `.k` 입출력 (k_io) | [MERGE_K](02_KooMeshModifier/modes/k_io/MERGE_K.md) · [IMPORT_MERGE_K](02_KooMeshModifier/modes/k_io/IMPORT_MERGE_K.md) · [DECOMPOSE_K](02_KooMeshModifier/modes/k_io/DECOMPOSE_K.md) · [DYNAIN_TO_INITIAL](02_KooMeshModifier/modes/k_io/DYNAIN_TO_INITIAL.md) |
| 검증·접촉 (validation_contact) | [PART_VALIDATION_SPLIT](02_KooMeshModifier/modes/validation_contact/PART_VALIDATION_SPLIT.md) · [CONTACT_AUTO_DECOMPOSITION](02_KooMeshModifier/modes/validation_contact/CONTACT_AUTO_DECOMPOSITION.md) · [REMOVE_DUPLICATE_TIED_CONTACTS](02_KooMeshModifier/modes/validation_contact/REMOVE_DUPLICATE_TIED_CONTACTS.md) · [WEAK_COUPLING](02_KooMeshModifier/modes/validation_contact/WEAK_COUPLING.md) |
| 자동화 (automation) | [SIMULATION_AUTOMATION](02_KooMeshModifier/modes/automation/SIMULATION_AUTOMATION.md) |

### 03 · KooAutomatedModeller (CAD/ECAD 형상 자동 모델러)

| 문서 | 설명 |
|------|------|
| [KooAutomatedModeller 개요](03_KooAutomatedModeller/README.md) | 전체 구조와 모드 |
| [CAD/ECAD Import](03_KooAutomatedModeller/cad_import.md) | ODB++/CAD 가져오기 |
| [KooAutomatedModeller 개발 현황](03_KooAutomatedModeller/dev_status.md) | 구현/부분구현 현황, 배포 형태 |

**형상 생성기 (generators)**

| 문서 | 설명 |
|------|------|
| [PKG 패키지 생성](03_KooAutomatedModeller/generators/package_pkg.md) | 반도체 패키지(PKG) 형상 생성 |
| [PCB 생성](03_KooAutomatedModeller/generators/pcb.md) | PCB 형상 생성 |
| [PBA 생성](03_KooAutomatedModeller/generators/pba.md) | PBA(부품 실장 보드) 생성 |
| [커패시터 생성](03_KooAutomatedModeller/generators/capacitor.md) | 커패시터 형상 생성 |
| [Array PCB 생성](03_KooAutomatedModeller/generators/array_pcb.md) | 어레이 PCB 생성 |

**예제**

| 문서 | 설명 |
|------|------|
| [KooAutomatedModeller 예제](03_KooAutomatedModeller/examples/examples.md) | 실행 예제 모음 |

### 99 · 부록 (Appendix)

| 문서 | 설명 |
|------|------|
| [단위계 (ton-mm-s)](99_appendix/unit_system.md) | 단위계 규약과 중력/밀도 보정 |
| [파일 포맷 레퍼런스](99_appendix/file_formats.md) | jobs.json/runner_config.json/dynain 등 파일 포맷 |
| [네이밍 표준](99_appendix/naming_standard.md) | CUM/SEQ 별칭 및 파트 이름 표준 |
| [기존 문서 통합 매핑](99_appendix/existing_docs_map.md) | 기존 산재 문서의 본 매뉴얼 흡수 매핑 |

---

## 문서 커버리지

본 매뉴얼은 총 66개 문서로 구성됩니다. 작성 상태(완료/부분/실패)와 각 문서의 미흡/확인 필요 항목(gaps)은 [COVERAGE.md](COVERAGE.md)에서 확인하세요.
