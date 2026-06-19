# 기존 문서 통합 매핑

## 1. 목적/개요

`/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs/` 최상위에는 매뉴얼(`manual/`) 정비 이전에 작성된 설계서(`PLAN_*`)·구현 보고서·버그픽스 노트·HTML/DOCX/TXT 등 흩어진 문서가 다수 존재한다. 이 문서는 그 기존 문서들이 **현재 매뉴얼(`manual/`)의 어느 섹션에 대응/통합되는지**를 한눈에 보여주는 매핑 표다.

매핑 목적:
- 매뉴얼 독자가 더 자세한 배경(설계 의도, 버그 이력, 알고리즘 상세)을 찾을 때 원본 문서 위치 안내
- 매뉴얼 정비 시 누락/중복 식별 (어떤 기존 문서가 아직 매뉴얼에 흡수되지 않았는지)

기준 디렉터리(절대경로): `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs/`

> 본 문서의 모든 매뉴얼 경로는 `docs/manual/` 기준 상대경로로 표기한다. 기존 문서 경로는 `docs/` 기준 상대경로로 표기한다.

---

## 2. 입력 옵션·인자 (표)

이 문서는 실행형 기능이 아니라 정적 매핑 표이므로 입력 옵션·인자는 없다. 매핑 표의 각 열 의미는 다음과 같다.

| 열 | 의미 |
|----|------|
| 기존 문서 | `docs/` 최상위의 원본 파일 |
| 문서 유형 | 계획서(PLAN) / 구현·버그픽스 보고서 / 참조(HTML·TXT·DOCX) |
| 주제 | 문서가 다루는 핵심 기능 |
| 대응 매뉴얼 섹션 | `docs/manual/` 내 대응 파일. "신규 후보"는 아직 매뉴얼 파일이 없음을 뜻함 |
| 통합 상태 | 흡수됨 / 부분 흡수 / 미흡수(배경자료) |

근거: 디렉터리 목록은 `ls /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs` 및 `find docs/manual -type f -name '*.md'` 결과.

---

## 3. 매핑 표 (실제 파일 목록 기반)

### 3-1. IGA / FEM_TO_IGA 계열

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `fem_to_iga_mode.md` | 계획서 | MODE 22 FEM_TO_IGA 설계 | `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md` | 흡수됨 |
| `FEM_TO_IGA_MODE_IMPLEMENTATION.md` | 구현 보고서 | MODE 22 구현 결과 | `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md` | 흡수됨 |
| `FEM_TO_IGA_BUGFIXES.md` | 버그픽스 노트 | 옵션 파싱(빈 줄 break 등) 버그 | `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md` (주의사항으로 일부 반영) | 부분 흡수 (배경자료) |
| `part_iga.md` | 계획서 | IGA Part Generator (FEM 솔리드→IGA 별도 .k) | `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md` | 부분 흡수 (배경자료) |
| `IGA_IMPLEMENTATION_SUMMARY.md` | 구현 보고서 | IGA Part Generator 구현 결과 | `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md` | 부분 흡수 (배경자료) |
| `PLAN_IncludeAndIGA.md` | 계획서 | `*INCLUDE` 처리 + IGA 키워드 보존 (메인/include 분리) | `02_KooMeshModifier/modes/k_io/IMPORT_MERGE_K.md`, `.../MERGE_K.md`, `.../DECOMPOSE_K.md` + `FEM_TO_IGA.md` | 부분 흡수 |

근거: FEM_TO_IGA 모드 매뉴얼 존재 (`02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md:1-12`). 코드 디스패치 `occProject/Generators/KooMeshModifier.py:319`(`modeList.append("FEM_TO_IGA")`), `:2861`(`elif mode == "FEM_TO_IGA"`), `:2916`(IGA INCLUDE 문 추가), `:2944`(IGA 파트 파일 복사). Include/IGA 키워드 입출력은 k_io 모드 매뉴얼 군이 가장 근접.

### 3-2. 낙하·충격 (HPC 워크플로우 / 실린더 임팩터)

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `FullAngleDrop_HPC_Workflow.md` | 가이드 | 전각도(N방향) 낙하 Slurm HPC 실행+후처리 | `01_KooChainRun/examples/full_angle_drop.md`, `01_KooChainRun/postprocess/postprocess.md`, `01_KooChainRun/doe_methods/doe_methods.md` | 흡수됨 |
| `PLAN_Cylinder3Stage_Impactor.md` | 설계서 | 3단 실린더(고무팁+중간+본체) 부분충격 충격추 | `02_KooMeshModifier/modes/drop_impact/DROP_WEIGHT_IMPACT_TEST.md`, `01_KooChainRun/scenarios/scenario_reference.md`, `01_KooChainRun/examples/partial_impact.md` | 부분 흡수 |
| `PLAN_FastDOEGeneration.md` | 계획서 | KooMeshModifier DOE 생성 고속화(배치) | `01_KooChainRun/doe_methods/doe_methods.md`, `01_KooChainRun/commands/submit.md` | 부분 흡수 (배경자료) |

근거: 전각도 낙하 예제 매뉴얼 `01_KooChainRun/examples/full_angle_drop.md` 존재. DOE 소스(각도/위치) 매뉴얼 `01_KooChainRun/doe_methods/doe_methods.md:1-10`, 코드 `Runner/AngleSourceParser.py:5-6`(`cuboid_geometry`, `fibonacci_lattice`), `:25-26`. 실린더 임팩터 시나리오 예제 `Examples/scenario_examples/impact_cylinder_8pi.json`, `impact_cylinder_15pi.json` 존재(부분충격 매뉴얼 `partial_impact.md`와 연결). 3단 실린더 형상 상세는 매뉴얼에 형상 표까지는 옮겨지지 않음 → 부분 흡수.

### 3-3. 열전달·열응력 / 진동

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `PLAN_ThermalStress_Automation.md` | 계획서 | 고온 열전달·열응력 자동화(키워드+시나리오) | `02_KooMeshModifier/modes/loads/THERMAL_LOAD.md`, `01_KooChainRun/scenarios/scenario_reference.md` | 부분 흡수 |
| `PLAN_AutomationInventory_ThermalSimulation.md` | 인벤토리+계획 | 자동화 현황 인벤토리 + IC 발열·열응력 계획 | `00_overview/architecture.md` (Part 1 인벤토리), `02_KooMeshModifier/modes/loads/THERMAL_LOAD.md` (Part 2 계획) | 부분 흡수 (배경자료) |
| `vibration_massive/` (디렉터리: PLAN/DESIGN/PHASES/EXAMPLES/IMPLEMENTATION/DECISIONS_OPEN/README) | 설계+구현 문서군 | 대규모 진동 가진 자동화 | `02_KooMeshModifier/modes/loads/VIBRATION_LOAD.md` | 부분 흡수 (배경자료) |

근거: 로드 모드 매뉴얼 `02_KooMeshModifier/modes/loads/THERMAL_LOAD.md`, `.../VIBRATION_LOAD.md` 존재. 코드 디스패치 `occProject/Generators/KooMeshModifier.py:325`(`VIBRATION_LOAD`), `:328`(`THERMAL_LOAD`), `:2873`/`:2876`(mode 처리). 진동 예제 `Examples/scenario_examples/vibration_example.json` 존재. `vibration_massive/`는 단계별 설계·구현 상세를 담은 배경자료(매뉴얼은 정리된 요약만 보유).

### 3-4. KooAutomatedModeller (Conformal Mesh)

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `PLAN_ConformalMeshGeneration.md` | 계획서 | PKG 모드 **완전 conformal mesh** 신규 생성(솔버 호환) | `03_KooAutomatedModeller/dev_status.md` (기존 ConformalHexa 부분), `03_KooAutomatedModeller/generators/package_pkg.md` | 미흡수 (신규 계획) |

근거: 기존 **buffer 기반 ConformalHexa**는 이미 구현·매뉴얼화됨 (`03_KooAutomatedModeller/dev_status.md:170-171` "구현됨", `PackageGenerator.py:315-323`, `:336-339` `ConformalBufferThickness`). 반면 `PLAN_ConformalMeshGeneration.md`는 "완전 conformal mesh"를 새로 추가하려는 **계획**으로, 미구현 함수(`KooMeshManagerGMSH.mesh_conformal_extrude_hexa()`, `PackageLayer.GenerateConformalMesh()` 등)를 신규 구현 대상으로 명시(`docs/PLAN_ConformalMeshGeneration.md:470-480`). 따라서 매뉴얼 본문에는 아직 흡수되지 않은 계획 단계.

### 3-5. KooChainRun 병렬 잡 (동시 실행 버그픽스)

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `KooChainRun_ConcurrentJob_Bugfixes.md` | 버그픽스 보고서 | 병렬 잡 동시 실행 시 jobs.json 경합 등 수정 | `01_KooChainRun/commands/submit.md`, `01_KooChainRun/commands/status.md`, `01_KooChainRun/dev_status.md` | 부분 흡수 (배경자료) |
| `KooChainRun_ConcurrentJob_Bugfixes.docx` | 동일(워드 포맷) | (위와 동일) | (위와 동일) | 부분 흡수 (중복 포맷) |
| `KooChainRun_ConcurrentJob_Bugfixes.tar.gz` | 아카이브 | 위 문서 배포 압축본 | — (산출물) | 해당 없음 |

근거: 버그픽스 보고서 대상 코드는 `KooChainRun`, `Runner/CumulativeScenarioRunner.py`, `Runner/JobManager.py`(`KooChainRun_ConcurrentJob_Bugfixes.md:5`). JobManager 실재 확인 `Runner/JobManager.py:21`(`class JobManager`), `:29`(`load_jobs`), `:48`(`_save_jobs`). 잡 추적/상태 기능은 submit/status 명령 매뉴얼에 대응. 버그 이력 자체는 매뉴얼 본문으로 옮기지 않음 → 배경자료.

### 3-6. 참조·개요 문서 (HTML / TXT)

| 기존 문서 (`docs/`) | 문서 유형 | 주제 | 대응 매뉴얼 섹션 (`docs/manual/`) | 통합 상태 |
|---|---|---|---|---|
| `KooChainRun_Overview.html` | HTML 개요 | KooChainRun 기능 개요 | `01_KooChainRun/README.md`, `00_overview/architecture.md` | 흡수됨 |
| `SmartTwinPreprocessor_Programs.txt` | TXT 프로그램 설명서 | 3개 도구(KCR/KMM/KAM) 요약 | `00_overview/architecture.md` | 흡수됨 |
| `CAD_BOM_CAE_Automation_NamingStandard.html` | HTML 표준서 | CAD BOM 기반 CAE 자동화 + 네이밍 표준 | `00_overview/glossary.md` (네이밍/Alias), `01_KooChainRun/scenarios/scenario_reference.md` | 부분 흡수 |
| `plan_wall_part_advanced_options.md` | 계획서 | DropSurface 설정화 + DeformableToRigidAutomatic | `01_KooChainRun/scenarios/scenario_reference.md` (DropSurface), `02_KooMeshModifier/modes/material_part/ELASTIC_TO_RIGID.md` | 부분 흡수 |

근거: HTML 제목 확인 — `KooChainRun_Overview.html` `<title>KooChainRun — Feature Overview</title>`, `CAD_BOM_..._NamingStandard.html` `<title>CAD BOM 기반 CAE 시뮬레이션 자동화 - SmartTwinCluster</title>`. `SmartTwinPreprocessor_Programs.txt`는 3개 도구를 항목별 요약(KCR/KMM/KAM)하여 `00_overview/architecture.md` 표(KCR/KMM/KAM)와 1:1 대응. Alias 네이밍 규약은 글로벌 메모리 `Alias Pattern` 및 `00_overview/glossary.md`에 정리. `plan_wall_part_advanced_options.md:1-?`은 `CumulativeScenarioRunner._create_step_config()`의 DropSurface 하드코딩 문제를 다루며 시나리오 참조 문서의 DropSurface 항목과 연결.

---

## 4. 동작 원리 (코드/파일 근거)

이 매핑 자체는 코드가 아니라 디렉터리 구조와 모드 디스패치에 근거한다. 대응 관계의 핵심 근거는 다음과 같다.

- **3개 도구 ↔ 매뉴얼 3개 디렉터리**: `docs/manual/01_KooChainRun`, `02_KooMeshModifier`, `03_KooAutomatedModeller`는 각각 KCR/KMM/KAM 도구에 대응. 도구 정의는 `00_overview/architecture.md`의 도구 표(KooChainRun=`KooChainRun:1-9`, KooMeshModifier=`occProject/Generators/KooMeshModifier.py:1-6`, KooAutomatedModeller=`occProject/Generators/KooAutomatedModeller.py:1-6`).
- **KMM 모드 문서 ↔ 코드 모드 디스패치**: 흩어진 모드 계획서(FEM_TO_IGA, THERMAL_LOAD, VIBRATION_LOAD)는 매뉴얼 `02_KooMeshModifier/modes/` 하위 동명 파일과 코드 디스패치 라인에 직접 대응. 근거: `occProject/Generators/KooMeshModifier.py:319,325,328`(모드 등록), `:2861,2873,2876`(모드 실행 분기).
- **DOE/낙하 워크플로우 ↔ Runner 코드**: `FullAngleDrop_HPC_Workflow.md`, `PLAN_FastDOEGeneration.md`의 각도/위치 생성은 `Runner/AngleSourceParser.py:5-6,23-26`(`cuboid_geometry`, `fibonacci_lattice`)에 근거하며 매뉴얼 `01_KooChainRun/doe_methods/doe_methods.md`에 정리됨.
- **병렬 잡 버그픽스 ↔ JobManager**: `Runner/JobManager.py:21`(`class JobManager`), `:29`(`load_jobs`), `:48`(`_save_jobs`)가 동시 실행 시 jobs.json 경합 대상 코드.

---

## 5. 주의사항·한계

- **"부분 흡수 (배경자료)" 문서는 삭제 금지**: 버그 이력(`*_Bugfixes.md`), 설계 의도(`PLAN_*`, `part_iga.md`), 단계별 구현 기록(`vibration_massive/`)은 매뉴얼 본문에 요약만 옮겨졌다. 디버깅/회귀 분석 시 원본이 필요하므로 보존한다.
- **중복 포맷 존재**: `KooChainRun_ConcurrentJob_Bugfixes`는 `.md` / `.docx` / `.tar.gz` 3종으로 존재. 내용 기준은 `.md`이며 나머지는 배포/아카이브용이다. (`.tar.gz`는 산출물로 매핑 대상 아님.)
- **`PLAN_ConformalMeshGeneration.md`는 신규 계획**: 기존 buffer 기반 ConformalHexa(`03_KooAutomatedModeller/dev_status.md:170-171` "구현됨")와 혼동 금지. 이 PLAN의 "완전 conformal mesh"는 미구현 함수 신규 작성을 전제(`docs/PLAN_ConformalMeshGeneration.md:470-480`)로 한다.
- **HTML/DOCX 내부 라인 근거 한계**: HTML/DOCX는 file:line 인용이 불안정하여 본 매핑은 `<title>`/항목명 단위로만 근거를 댔다. 세부 문장 인용은 원본을 직접 열어 확인 필요.
- **권한 제한 파일**: `fem_to_iga_*` 일부, `IGA_IMPLEMENTATION_SUMMARY.md`, `part_iga.md`, `PLAN_AutomationInventory_ThermalSimulation.md`는 권한이 `-rw-------`(소유자 전용). 매뉴얼 독자가 접근하지 못할 수 있으므로 핵심 내용은 매뉴얼 본문에 옮겨 두는 것을 권장. **(권한·접근성은 운영 시 확인 필요.)**

---

## 6. 개발 현황

**구현됨 (정적 문서로서 완성)** — 근거:
- 매핑 표의 모든 기존 문서는 `ls /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/docs` 실측 목록과 일치한다(존재 확인 완료).
- 대응 매뉴얼 파일은 `find docs/manual -type f -name '*.md'` 실측 목록에 모두 존재함을 확인했다(예: `02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md`, `02_KooMeshModifier/modes/loads/THERMAL_LOAD.md`·`VIBRATION_LOAD.md`, `01_KooChainRun/examples/full_angle_drop.md`, `01_KooChainRun/doe_methods/doe_methods.md`, `03_KooAutomatedModeller/dev_status.md`).
- 코드 근거(모드 디스패치, AngleSourceParser, JobManager, PackageGenerator)는 실제 grep으로 라인 확인 완료.

> 단, 매핑 표의 "통합 상태"(흡수됨/부분 흡수/미흡수) 판정 중 일부는 매뉴얼 본문을 전수 비교한 것이 아니라 제목·헤더·grep 키워드 매칭에 근거한다. 세부 문장 수준의 흡수 완전성은 **확인 필요**.
