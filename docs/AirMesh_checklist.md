# AIRMESH 구현 체크리스트

계획: [PLAN_AirMeshGeneration.md](PLAN_AirMeshGeneration.md) · 결정 기록: [AirMesh_context-notes.md](AirMesh_context-notes.md)

## Phase 0 — 프로토타입 (완료)
- [x] gmsh Python API 파이프라인 e2e 실증 (import→cut→HXT tet→STL, 0.062초)
- [x] 물리그룹 분리 STL(cavity/outer_box) 삼각형 수 정확 일치 확인
- [x] 다중 솔리드 cut 무변경 동작 확인
- [x] 조대 메시 무크래시(경고 대상) 확인, Delaunay 폴백 확인
- [x] P1 orientation 함정 발견 + trimesh 후처리 검증
- [x] discrete sandwich(헥사코어 버퍼) 메커니즘 검증 — 좌표 재매핑·체적 폐합
- [x] 프로토타입 저장소 보존: `Examples/automatedmodeller/airmesh_proto/`

## Phase 1 — MVP e2e
- [x] `Generators/KooAirMesh/__init__.py` 생성
- [x] `AirMeshCore.py`: 세션 관리(isInitialized 가드, finally finalize, sys.argv 미전달)
- [x] `AirMeshCore.py`: S2 임포트(dim-3 필터, solid_selection) + S4 bbox/패딩/size_guard
- [x] `AirMeshCore.py`: S5 불리언 cut + CAD 체적 검증(rel 1e-6)
- [x] `AirMeshCore.py`: S6 면 분류(6평면 bbox 테스트, tol 1e-6·diag)
- [x] `AirMeshCore.py`: S7 HXT 메시(사전 n_est 가드 포함) + S8 품질(타입=={tet4} 하드 단언)
- [x] `AirMeshCore.py`: S9 출력 — .msh(4.1 ASCII) + air.stl(Binary=1, SaveAll 순서 고정)
- [x] `AirMeshGenerator.py`: config 로드/검증(오류 전부 수집, 알 수 없는 키 경고)
- [x] `AirMeshGenerator.py`: run_from_config 전체 try/except, report.json 상시 기록, Complete/FAILED 라인
- [x] KooAutomatedModeller.py 2-hunk: GenerateAirMesh 함수 + AIRMESH elif (함수-로컬 import)
- [x] 예제 `Examples/automatedmodeller/airmesh_sphere/` (airmesh.json + STEP)
- [x] 검증: Complete 라인 + report ok + watertight + 체적오차 <0.5%
- [x] 🔴 보호 회귀: CAPACITOR·PKG conformal 예제 diff 전후 byte-identical + git diff 2-hunk 확인

## Phase 2 — 강화
- [x] 분리 STL(cavity/outer_box) + P1 orientation 후처리(trimesh split/fix_normals/invert)
- [x] heal 사다리(auto/always/never + healShapes 재시도)
- [x] 다중 솔리드 + 슬리버 제거(1e-9·V_box) + eps-pad 재시도
- [x] .vtk 출력 옵션, geometry_debug(brep)
- [x] 검증 블록 전체(volume_error_warn/min_sicn_warn/fail_on_inverted)
- [ ] 테스트: 2-솔리드 / 조대-h 경고 / 깨진 STEP(FAILED+exit0+부분 리포트) / pad=0 밀착면
- [ ] 🔴 실제(비합성) STEP 파일 1개 이상으로 힐링 사다리 실증
- [ ] 단위 테스트: 프로토 검증 항목의 재현 가능한 테스트화 (tests/)

## Phase 3 — Nuitka 빌드/배포
- [ ] build_automatedmodeller_python312.sh에 `cp libgmsh.so.4.15` + dist 스모크 테스트 (가산만)
- [ ] build_all_python312.sh 동일 반영
- [ ] initialize() try/except → E_GMSH_INIT 명확 메시지
- [ ] dist 바이너리 스모크 통과 (grep "Complete AIRMESH")
- [ ] `/data/SmartTwinPreprocessor` 배포본 스모크 통과
- [ ] 커밋+푸시 (기존 관례: tar까지 세트면 sudo 필요)

## Phase 4 — 문서/예제
- [ ] docs/manual/03_KooAutomatedModeller/에 AIRMESH 모드 문서 + README 모드 표 갱신
- [ ] 예제 사다리 4종(단일/다중/조대/고장 주입)
- [ ] dev_status.md 갱신

## Phase 5 — 헥사코어+오면체 (옵트인, 계약 고정)
- [ ] 선행: KooElement.AddElementsfromMSH 5절점(피라미드) 분기 추가 또는 우회 확정
- [ ] 셀 분류(CUT 마킹→flood-fill→침식→매니폴드 수리→promote)
- [ ] 피라미드 삽입(apex=제거셀 중심) + 내부 스킨 폐합 단언
- [ ] discrete sandwich 버퍼(좌표-정확 재매핑, 스킨 삼각형 수 불변)
- [ ] 게이트: 체적 폐합 + assert_conformal + watertight
- [ ] fallback_to_tetra 자동 폴백 + 패딩 하한 (buffer_layers+2)·h
