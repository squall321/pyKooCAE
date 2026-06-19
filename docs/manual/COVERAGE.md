# 매뉴얼 커버리지 리포트

pyKooCAE 매뉴얼 작성 현황과 후속 보완 대상을 정리한다. 본 리포트의 분류는 각 문서의 작성 상태(`status`)와 대상 기능의 구현 현황(`dev_status`)을 기준으로 한다.

- **status**: 문서 작성 자체의 완료 여부 (`written` 완료 / `failed` 미완·검증 실패)
- **dev_status**: 문서가 다루는 *기능*의 구현 상태 (`구현됨` / `부분구현`)

---

## 1. 집계

전체 **66개** 문서.

| 구분 | 개수 | 설명 |
|------|------|------|
| 작성 완료 (written) | 63 | 본문 작성 완료 |
| 작성 실패 (failed) | 3 | 파일은 존재하나 검증/리뷰 단계에서 failed로 표기 — 재검토 필요 |
| **합계** | **66** | |

작성 완료(written) 63개를 기능 구현 상태로 다시 분류:

| dev_status | 개수 |
|------------|------|
| 구현됨 | 50 |
| 부분구현 (partial) | 13 |
| **합계** | **63** |

> 참고: 거의 모든 written 문서에 정도 차이는 있으나 "확인 필요"/예제 부재 등의 gaps가 존재한다. 아래 3·4절은 (a) status=failed, (b) dev_status=부분구현, (c) 그 외 written 중 운영상 주의가 필요한 주요 gaps 순으로 정리한다.

---

## 2. 후속 보완 우선순위 요약

| 우선순위 | 대상 | 사유 |
|----------|------|------|
| **P0 (재작성)** | failed 3건 | 검증 실패 상태 — 본문은 존재하나 신뢰성 미확보 |
| **P1 (부분구현 기능)** | 부분구현 13건 | 기능 자체가 미완성/스텁이라 문서도 한계가 명확 |
| **P2 (검증 보강)** | written·구현됨 중 "예제 부재 / 실모델 e2e 미검증" 다수 | 코드 근거는 확보됐으나 실행 산출물 미확인 |

---

## 3. status = failed (재검토 대상, P0)

본문은 존재하나 작성 검증이 failed로 표기된 문서. 내용 정확성 재검토 후 status 갱신 필요.

| 경로 | 제목 | 비고 |
|------|------|------|
| [00_overview/architecture.md](00_overview/architecture.md) | pyKooCAE 아키텍처 개요 | failed — 재검토 필요 (gaps 미기록) |
| [00_overview/install_build.md](00_overview/install_build.md) | 빌드 · 배포 가이드 | failed — 재검토 필요 (gaps 미기록) |
| [01_KooChainRun/scenarios/scenario_reference.md](01_KooChainRun/scenarios/scenario_reference.md) | scenario.json 레퍼런스 | failed — 재검토 필요 (gaps 미기록) |

---

## 4. dev_status = 부분구현 (기능 미완, P1)

문서는 작성됐으나 대상 기능이 부분구현/스텁/계획 단계인 항목.

| 경로 | 제목 | 부분구현 사유 (요약) |
|------|------|----------------------|
| [01_KooChainRun/commands/status.md](01_KooChainRun/commands/status.md) | KooChainRun status | `--watch` 플래그가 파서에만 정의되고 본문 미사용(무동작). config 기반 상세 진행률은 코드 내 TODO로 미구현. squeue 출력에만 의존(추적파일 미사용) |
| [01_KooChainRun/commands/collect.md](01_KooChainRun/commands/collect.md) | KooChainRun collect | 일반 DOE 경로는 TODO 미구현(수동복사 안내만 출력). part_validation/drop_weight_impact만 리포트 생성 |
| [02_KooMeshModifier/dev_status.md](02_KooMeshModifier/dev_status.md) | KooMeshModifier 개발 현황 | REMESH_TETRA 고도화·SIMULATION_AUTOMATION 구버전 경로 등 부분구현 항목 집계 |
| [02_KooMeshModifier/modes/mesh_ops/REMESH_TETRA.md](02_KooMeshModifier/modes/mesh_ops/REMESH_TETRA.md) | REMESH_TETRA | 기본 gmsh 리메시는 동작하나 외곽면 품질·최소 dt 보장 고도화는 계획 단계. scenario→step_config 변환 경로 미확인 |
| [02_KooMeshModifier/modes/mesh_ops/DEFEATURE_MESH.md](02_KooMeshModifier/modes/mesh_ops/DEFEATURE_MESH.md) | DEFEATURE_MESH | collapse 이웃 평균화 로직 대부분 주석 처리(단순 node merge로만 동작). 전용 예제 부재. output.stl 고정 파일명 충돌 가능성 |
| [02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md](02_KooMeshModifier/modes/mesh_ops/FEM_TO_IGA.md) | FEM_TO_IGA | 입력 옵션 8개로 제한, NURBS 차수·세분화는 고정 디폴트. 비솔리드 파트 변환 미명시. 입력 .k 예제 부재 |
| [02_KooMeshModifier/modes/material_part/DIMENSIONAL_TOLERANCE.md](02_KooMeshModifier/modes/material_part/DIMENSIONAL_TOLERANCE.md) | DIMENSIONAL_TOLERANCE | WEIBULL 모드 미구현(주석만). NORM/LHS 동적완화 자동제어 주석 처리. 수렴 정확도 미검증 |
| [02_KooMeshModifier/modes/validation_contact/WEAK_COUPLING.md](02_KooMeshModifier/modes/validation_contact/WEAK_COUPLING.md) | WEAK_COUPLING | 좌표 수집부 `tuple(node.x, node.y, node.z)` 호출이 TypeError 유발 의심. 트리거 키워드 불일치(weak_coupling vs *weakcoupling). 예제 부재 |
| [02_KooMeshModifier/modes/automation/SIMULATION_AUTOMATION.md](02_KooMeshModifier/modes/automation/SIMULATION_AUTOMATION.md) | SIMULATION_AUTOMATION | generate_for_all() 파싱 결과가 호출부에서 버려져 config 미저장. 다운스트림 전달 경로 미확인 |
| [03_KooAutomatedModeller/README.md](03_KooAutomatedModeller/README.md) | KooAutomatedModeller 개요 | LSDYNADOE 분기 pass 스텁(미구현). Nastran/ANSYS/ABAQUS/OBJ 출력 전부 주석 처리. generators/examples 하위 페이지 미작성. IP 화이트리스트+라이선스 만료 게이트 |
| [03_KooAutomatedModeller/generators/package_pkg.md](03_KooAutomatedModeller/generators/package_pkg.md) | PKG 패키지 생성 | 레이어 메시/비메시 혼합 동작 미확인. 다중 솔버 출력 비활성. check_cylinders.py가 가정한 클래스 API 부재. GenerateDOEforLSDYNA 스텁 |
| [03_KooAutomatedModeller/cad_import.md](03_KooAutomatedModeller/cad_import.md) | CAD/ECAD Import | ImportCADManager 호출처 없음(CLI 미연결). 단위계 환산 주석 부재. 다중 솔버 export 비활성. ODB++ 해석부 내부 미조사 |
| [03_KooAutomatedModeller/examples/examples.md](03_KooAutomatedModeller/examples/examples.md) | KooAutomatedModeller 예제 | ConformalHexa .txt 별도 실행 필요. 실행 게이트(IP/날짜). Library/OCC 의존 부재. check_cylinders.py stale. 다중 솔버 출력 주석 처리 |
| [03_KooAutomatedModeller/dev_status.md](03_KooAutomatedModeller/dev_status.md) | KooAutomatedModeller 개발 현황 | 전용 SIF/.def 미발견(Nuitka standalone만). 라이선스 게이트로 미등록 환경 실행 차단. 다중 솔버 export 주석. LSDYNADOE 스텁 |
| [99_appendix/file_formats.md](99_appendix/file_formats.md) | 파일 포맷 레퍼런스 | jobs.json 최상위 메타 생성 코드 라인 미확인. dynain/리포트 내부 스키마는 외부 패키지 소관으로 확정 불가. runner_config.json 신·구 포맷 공존 |
| [99_appendix/naming_standard.md](99_appendix/naming_standard.md) | 네이밍 표준 | generate_alias_sequential(SEQ) 호출처 없음(미연동). CAD/BOM/CAE 파트 이름 표준은 HTML 설계 문서에만 존재, 코드 미구현 |

> 위 표는 16건이다. (dev_status 헤더 문구상 "부분구현"으로 분류된 13건 + dev_status 문자열 안에 부분구현/미연동 단서가 명시된 인접 3건 — status.md/collect.md/file_formats.md 등 — 을 운영 보완 관점에서 함께 묶었다. 핵심 부분구현 기능 13건은 표 상단부에 해당한다.)

---

## 5. written · 구현됨 — 주요 gaps (검증 보강, P2)

작성 완료·기능 구현됨으로 표기됐으나, 운영 시 확인이 필요한 대표 항목. (전체 written 문서 대부분에 "예제 부재/실모델 미검증" 류 gaps가 존재하므로, 여기서는 동작 오류 가능성·옵션 미연동 등 영향도가 있는 항목만 발췌한다.)

| 경로 | 제목 | 주요 gap |
|------|------|----------|
| [01_KooChainRun/commands/submit.md](01_KooChainRun/commands/submit.md) | submit | `--partition normal` 명시 시에도 코드의 `!= 'normal'` 비교로 environment.partition이 우선됨 — 의도 확인 필요 |
| [01_KooChainRun/commands/run.md](01_KooChainRun/commands/run.md) | run | `--resume` 플래그가 Runner 생성자에 전달되지 않고 헤더 출력에만 사용 — 미연결/부분 구현 |
| [01_KooChainRun/commands/stop.md](01_KooChainRun/commands/stop.md) | stop | sacct/squeue 모두 실패 시 UNKNOWN 분류 → 실행 중 작업 미취소 가능성. sequential 동일 job_id 공유 시 중복 scancel 결과 단정 불가 |
| [01_KooChainRun/postprocess/postprocess.md](01_KooChainRun/postprocess/postprocess.md) | 후처리 자동화 | delete_d3plot 후 impact aggregate의 deep output 재사용(force_reuse)이 SmartTwinPostprocessor.sif 측 구현 의존 — 코드만으로 미검증 |
| [01_KooChainRun/dev_status.md](01_KooChainRun/dev_status.md) | KooChainRun 개발 현황 | VIBRATION per_cap/circuit_group serializer 미등록(주석 placeholder), e2e 통과 여부 런타임 검증 필요 |
| [01_KooChainRun/doe_methods/doe_methods.md](01_KooChainRun/doe_methods/doe_methods.md) | DOE 방법 | fibonacci_lattice.angle_spacing 파서 미사용. LHS/Random 시드 미고정(재현성 미확인). position_source 단독 예제 동봉 여부 미확인 |
| [02_KooMeshModifier/README.md](02_KooMeshModifier/README.md) | 모드 카탈로그 | 코드에 카테고리 enum 없음 — 8개 카테고리 분류는 디렉토리/동작 의미 기준 추정 포함. 모드 상세 페이지 일부 미작성 |
| [02_KooMeshModifier/input_format.md](02_KooMeshModifier/input_format.md) | 입력 .k 블록 문법 | 제어 파일 실제 확장자는 .txt(문서 제목은 .k). WEAK_COUPLING 옵션 블록 헤더 누락. DROP_ATTITUDE 매칭이 단일 `*`로 검사됨 |
| [02_KooMeshModifier/modes/drop_impact/DROP_WEIGHT_IMPACT_TEST.md](02_KooMeshModifier/modes/drop_impact/DROP_WEIGHT_IMPACT_TEST.md) | DROP_WEIGHT_IMPACT_TEST | OffsetDistance 기본값이 파서(1e-9)와 소비측 fallback(1e-11) 불일치. 물성 키 부분일치 매핑 의존 |
| [02_KooMeshModifier/modes/loads/THERMAL_LOAD.md](02_KooMeshModifier/modes/loads/THERMAL_LOAD.md) | THERMAL_LOAD | TempCurve가 절대온도일 때 ts/tb 환산이 의도와 다를 수 있음. P2/P3(2-pass, 열응력→낙하 누적) 미구현. 전용 예제 부재 |
| [02_KooMeshModifier/modes/mesh_ops/CONVERT_CNRB_TO_SOLID.md](02_KooMeshModifier/modes/mesh_ops/CONVERT_CNRB_TO_SOLID.md) | CONVERT_CNRB_TO_SOLID | RTolerance가 동작 코드에서 읽히나 옵션 파서에 분기 없음(입력 조정 불가). 신규 파트가 원본 PID 재사용 → PID 충돌 가능성 |
| [02_KooMeshModifier/modes/material_part/MATERIAL_EXCHANGE.md](02_KooMeshModifier/modes/material_part/MATERIAL_EXCHANGE.md) | MATERIAL_EXCHANGE | 변수 치환이 10폭 필드 완전 일치 의존. 다중 *mid 블록 시 마지막 블록만 저장될 가능성 |
| [02_KooMeshModifier/modes/material_part/PART_MORPHING.md](02_KooMeshModifier/modes/material_part/PART_MORPHING.md) | PART_MORPHING | morphpid의 TargetPID/numX/numY가 PIDBOX 경로에서 미사용(미연동). 트리거(part_morphing) vs 블록 헤더(**partmorphing) 표기 상이 |
| [02_KooMeshModifier/modes/doe_transform/TRANSLATION_DOE.md](02_KooMeshModifier/modes/doe_transform/TRANSLATION_DOE.md) | TRANSLATION_DOE | 부분 축 입력 시 KeyError 가능. PID/축 길이 불일치 시 IndexError 가능(길이 검증 없음). 실모델 e2e 미검증 |
| [02_KooMeshModifier/modes/doe_transform/TRANSFORM.md](02_KooMeshModifier/modes/doe_transform/TRANSFORM.md) | TRANSFORM | scale이 중심기준 아닌 원점기준 직접 곱 — 의도 여부 확인 필요. 전용 예제/테스트 부재 |
| [02_KooMeshModifier/modes/material_part/WARPED_PART.md](02_KooMeshModifier/modes/material_part/WARPED_PART.md) | WARPED_PART | Direction은 Z방향만 동작(그 외 분기 부재). 비사각/회전 격자 매핑 미확인 |
| [02_KooMeshModifier/modes/material_part/WARPED_TO_INITIAL_STRESS_PART.md](02_KooMeshModifier/modes/material_part/WARPED_TO_INITIAL_STRESS_PART.md) | WARPED_TO_INITIAL_STRESS_PART | 적용 방향 Z 하드코딩(임의 방향 미지원). warpage.dat 9999 값 의미 미확인 |
| [02_KooMeshModifier/modes/material_part/PART_EXCHANGE.md](02_KooMeshModifier/modes/material_part/PART_EXCHANGE.md) | PART_EXCHANGE | converthexato SolidStructuredZSlack 경로 후속 처리 미확인(부분구현 의심). 10폭 토큰 일치 의존 |
| [02_KooMeshModifier/modes/validation_contact/CONTACT_AUTO_DECOMPOSITION.md](02_KooMeshModifier/modes/validation_contact/CONTACT_AUTO_DECOMPOSITION.md) | CONTACT_AUTO_DECOMPOSITION | 코드 내 예제 경로가 주석 데드코드. 사내 참고 매뉴얼 예시가 분해 조건 미충족(부적절 예시) |
| [02_KooMeshModifier/modes/validation_contact/REMOVE_DUPLICATE_TIED_CONTACTS.md](02_KooMeshModifier/modes/validation_contact/REMOVE_DUPLICATE_TIED_CONTACTS.md) | REMOVE_DUPLICATE_TIED_CONTACTS | on/off 플래그가 실행 분기에서 미검사(false여도 제거 수행 가능). SSTYP/MSTYP 미포함 페어 판정 |
| [02_KooMeshModifier/modes/validation_contact/PART_VALIDATION_SPLIT.md](02_KooMeshModifier/modes/validation_contact/PART_VALIDATION_SPLIT.md) | PART_VALIDATION_SPLIT | floor_size 옵션이 docstring에만 있고 미사용(항상 bbox 2배). 바닥판 재료 강철 하드코딩(타 단위계 미확인) |
| [02_KooMeshModifier/modes/mesh_ops/ERODING_MIN_DT.md](02_KooMeshModifier/modes/mesh_ops/ERODING_MIN_DT.md) | ERODING_MIN_DT | *DT 미입력 시 KeyError 가능(예외처리 미발견). DTMIN 단위 변환 없음. 전용 예제 부재 |
| [02_KooMeshModifier/modes/mesh_ops/RIGIDIFY_SMALL_DT.md](02_KooMeshModifier/modes/mesh_ops/RIGIDIFY_SMALL_DT.md) | RIGIDIFY_SMALL_DT | 전용 예제 0건(파서 기반 재구성). 강체 분리 후 접촉 제외 자동화 여부 미확인 |
| [02_KooMeshModifier/modes/drop_impact/DROP_ATTITUDE.md](02_KooMeshModifier/modes/drop_impact/DROP_ATTITUDE.md) | DROP_ATTITUDE | 옵션 누락 시 KeyError/IndexError 방어 미확인. DropContact 전체 키 목록 외부 문서화 미확인 |
| [02_KooMeshModifier/modes/loads/VIBRATION_LOAD.md](02_KooMeshModifier/modes/loads/VIBRATION_LOAD.md) | VIBRATION_LOAD | KooChainRun 진동 모드 연동 코드 직접 확인 못함. 단위 가정(9810=1g) 비변환 |
| [99_appendix/unit_system.md](99_appendix/unit_system.md) | 단위계 | g 자동 추정 규약이 DROP/실린더 경로와 DropWeightImpactWorkflow(g=9810 고정)에서 상이 — 통일 여부 불명확 |
| [01_KooChainRun/examples/full_angle_drop.md](01_KooChainRun/examples/full_angle_drop.md) | 예제: 전각도 낙하 | 라이선스 서버 IP가 테스트/문서 예시 상이. Test_010 apptainer_tmpdir=/tmp(컴퓨트 노드 가시성 확인 필요). sphere_report.html 산출물 미확인 |
| [01_KooChainRun/examples/partial_impact.md](01_KooChainRun/examples/partial_impact.md) | 예제: 전위치 부분충격 | 메인 CLI argparse 소스 부재로 submit 인자 file:line 근거 미확보. 140-DOE e2e 통합 결과 미확인 |
| [99_appendix/existing_docs_map.md](99_appendix/existing_docs_map.md) | 기존 문서 통합 매핑 | 흡수 완전성 일부는 제목/grep 매칭 근거(문장 수준 미비교). 권한 제한 파일 접근성 운영 확인 필요 |

---

## 6. 후속 보완 대상 정리

1. **P0 — failed 3건 재작성/검증** (3절): architecture.md, install_build.md, scenario_reference.md
2. **P1 — 부분구현 기능 완성 후 문서 갱신** (4절): 특히 WEAK_COUPLING(TypeError 의심), SIMULATION_AUTOMATION(config 미저장), KooAutomatedModeller LSDYNADOE/다중 솔버 export, KooChainRun collect 일반 DOE 경로
3. **P2 — 실모델 e2e 검증 보강** (5절): 예제 부재·산출물 미확인 다수. 특히 동작 오류 가능성이 있는 항목(submit partition 우선순위, run --resume 미연결, TRANSLATION_DOE KeyError/IndexError, CONVERT_CNRB_TO_SOLID PID 충돌, REMOVE_DUPLICATE_TIED_CONTACTS on/off 미검사) 우선
4. **미작성 하위 페이지**: 02_KooMeshModifier/modes/ 일부 카테고리 상세, 03_KooAutomatedModeller/generators·examples 하위 일부는 링크만 존재 → 추가 작성 필요
