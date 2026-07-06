# AIRMESH 컨텍스트 노트 — 결정과 근거

계획: [PLAN_AirMeshGeneration.md](PLAN_AirMeshGeneration.md) · 체크리스트: [AirMesh_checklist.md](AirMesh_checklist.md)

## 2026-07-03 — 계획 수립 (조사 4방향 + 설계안 3개 경쟁 + 3-렌즈 심사)

### 어떻게 결정했나
독립 설계안 3개(단순견고=순수 tet / 격자충실=헥사코어+오면체 / 재사용=기존 .geo 파이프라인 확장)를 경쟁시키고 3개 렌즈(견고성·기존보호·의도부합)로 심사. 견고성·기존보호 렌즈는 단순견고 1위(9점), 의도부합 렌즈는 헥사코어 1위(9점). 수렴 결론: **순수 tet를 Phase 1로 출하하고, 헥사코어+오면체를 같은 계약 아래 Phase 5 목적지로 고정**(사면체 자동 폴백 유지).

### 주요 결정과 이유

1. **gmsh Python API 채택, .geo/CLI 배제** — .geo 텍스트로는 discrete entity·피라미드·샌드위치 볼륨 표현이 불가능해 헥사코어를 영구 봉쇄함(재사용안의 치명 결함으로 판정). headless 동작은 프로토타입으로 확인(디스플레이 불필요).
2. **KooMeshManagerGMSH 불사용** — sys.exit 실패지점 9~11곳(gmsh 실패 시 KAM 프로세스 전체 사망) + 매니저 6종 결합. 세 설계안이 독립적으로 같은 결론. 패턴만 차용, 코드는 신규 자급자족 패키지.
3. **JSON, YAML 배제** — 트리에 YAML 전례 0. PyYAML은 Nuitka에 `--include-package=yaml --include-module=_yaml` 필요하고 누락 시 조용한 pure-Python 폴백으로 실패. JSON은 stdlib라 빌드 리스크 0.
4. **함수-로컬 import 강제** — gmsh.py가 import 시점에 CDLL(libgmsh)을 실행함. 최상단 import면 기존 5개 모드 전부가 라이브러리 부재 시 죽음. Nuitka는 함수-로컬 import도 정적 추적하므로 번들엔 문제없음.
5. **exit 0 고정 + stdout 라인/report.json이 기계 계약** — 기존 Generate* 전부 print-and-return 관행. 한 모드만 exit code를 쓰면 일관성 파괴.
6. **libgmsh.so.4.15 수동 cp** — Nuitka는 ctypes 로드 라이브러리를 절대 번들하지 않음. CDLL(None)은 예외를 안 던져서 실패가 "배포 머신에서 첫 API 호출 시 missing-symbol 크래시"로 지연 발현. 두 빌드 스크립트 cp(가산) + dist 스모크 테스트 + initialize() try/except 3중 방어. 후퇴선: shipped 4.14.1 CLI 바이너리 방식(tetra만 가능, 재사용안에서 검증됨).
7. **v1에서 헥사코어 배제** — 매니폴드 수리(O10)가 토이(12삼각형)에서만 검증. 3-4주 추정도 낙관적(심사 판정). 대신 검증된 메커니즘(피라미드 apex 격리, 좌표 재매핑, 체적 폐합)을 계약으로 문서화.
8. **"grid cell" 해석** — v1은 균일 far-field 메시 사이즈로 충족(경계는 B-rep 추종이라 계단 문제 원천 차단). 사용자의 명시적 오면체 요구는 Phase 5 계약으로 존중 — 각주가 아니라 계획 본문에 포함(의도부합 심사자 강제).

### 실증에서 나온 비자명 함정 (구현자 필독)

- **P1**: gmsh air STL의 cavity 법선은 솔리드-외향(공기-내향) → watertight 검사 통과하면서 signed volume 오염. trimesh 후처리 없이 출하 금지.
- **generate(3)는 노드 태그를 재번호화**(좌표는 비트 보존) — 태그로 스킨 노드 추적 금지, 좌표-정확 재매핑만.
- **KooElement.AddElementsfromMSH에 5절점 분기 없음** — 피라미드 무경고 소실. 헥사코어 전 차단기.
- **Mesh.SaveAll 전역 상태** — write 전 명시 설정 + 그룹 사이 removePhysicalGroups 순서 고정.
- **조대 메시는 에러가 아님** — 크래시 없이 체적 오차만 커짐(−25.7% 사례). 클램프+경고가 옳고 하드 실패는 정당한 조대 실행을 막음.
- **체적 검증은 이산 기대값 대비** — CAD 값 대비 빡빡한 톨러런스는 facet화 오차로 거짓 실패.
- **STEP 왕복 시 면 분할** — 면 수 가정 금지, bbox-평면 테스트로 분류.

### 미해결 / 다음 세션 확인 사항

- 실전(비합성) STEP에서 힐링 사다리 미실증 — Phase 2 게이트.
- libgmsh.so.4.15(92MB, venv312/lib 존재 확인)의 ldd 의존성이 배포 환경에서 해소되는지 Phase 3에서 확인.
- 내부 공동(internal void) 처리는 v1 범위 외(문서화만).
- 프로토타입 스크립트 05_discrete_sandwich.py는 원본이 stale(getNode 크래시가 오히려 태그 재번호화의 증거) — Phase 5 착수 시 재현 테스트로 재작성 필요.

## 2026-07-03 — Phase 1(+2 일부) 구현 완료

### 구현/검증 결과
- `Generators/KooAirMesh/{__init__,AirMeshCore,AirMeshGenerator}.py` + KAM 2-hunk(가산 15줄). 골든 예제 `Examples/automatedmodeller/airmesh_sphere/`.
- e2e 게이트 통과: 직접 호출 + KAM 진입점(라이선스 게이트 포함) 양쪽. 사면체 10,737개, watertight, 이산 체적오차 1.8e-14%, faceting 0.19%, 역요소 0.
- 보호 회귀: KooAutomatedModeller.py diff = 가산 2-hunk뿐 + PKG conformal 예제 원본(HEAD)과 **바이트 동일 A/B 통과**. 예제 내 gmsh 서브프로세스 경고는 원본에서도 동일(기존 환경 이슈).
- 실패 경로: config 오류/없는 STEP → FAILED 라인 + exit 0 + best-effort 리포트. 조대 h → 클램프+경고. 다중 솔리드+both 출력+orientation 후처리 게이트 통과(체적오차 1.2e-14%).

### 구현 중 발견 (계획에 없던 사실)
- 🔴 **gmsh healShapes는 원본을 소모하고 치유 복사본으로 교체**한다. 반환 리스트는 하위 엔티티 중복 포함 노이즈. 원본 태그를 추가 remove하면 태그 충돌로 치유본까지 삭제됨(Volume does not exist). 수정: heal 후 `getEntities(3)`으로 수집, remove 금지.
- 🔴 **heal="always"를 깨끗한 형상에 강제하면 구면이 주기면으로 재구성돼 메시 불가**("Impossible to mesh periodic surface") — 알고리즘 3종 모두 실패. 기본값 auto가 정답인 실증 근거. E_MESH 메시지에 힌트 추가함.
- 다중 솔리드를 heal=always로 돌리면 healShapes가 컴파운드 1개 볼륨으로 합침(n_solids 보고 변화). 기능상 문제없음(체적/бbox 합산 동일).
- S6 분류에서 combined=True 외피와 per-volume 경계를 분리 — 공기 볼륨 간 내부 공유 면은 STL 외피에서 제외(O9 방어). 발견 시 경고 기록.

### 남은 항목 (Phase 2 잔여 + 3~5)
- 깨진 STEP(비봉합 셸) 고장 주입 테스트, pad=0 밀착면 테스트, 실제(비합성) STEP 실증, 프로토 검증의 단위 테스트화.
- Phase 3: 빌드 스크립트 cp libgmsh.so.4.15 + dist 스모크 (Nuitka 빌드 시점에).
- 멀티에이전트 적대적 리뷰는 세션 한도로 미실행(4 finder 전원 한도 초과) — 직접 정밀 리뷰+실증으로 대체했고, 한도 리셋 후 wf_89c3ffe4-4df resume으로 재실행 가능.

## 2026-07-05 — 적대적 리뷰 완주(3차 시도) + 확정 결함 일괄 수정

### 리뷰 결과
에이전트 54개(4-렌즈 탐색 → 발견당 반박자 2명, 3.1M 토큰). 확정 21건(중복 포함, 실질 14건) / 반박 기각 4건. 상위 결함은 전부 **실행 재현 근거** 포함.

### 수정한 확정 결함
- 🔴 **eps-pad 재시도 오염(CRITICAL)**: 재시도로 박스가 커져도 분류·체적 검증이 원래 평면 기준 → outer 0면, 빈 물리그룹이 전체 요소를 STL로 유출, 실패한 cut의 잔류 박스가 함께 메시(tet 2배). 수정: 유효 bbox 전파 + 잔류 박스 방어 제거 + outer 0면이면 E_INTERNAL. 사다리 순서도 eps-pad(무손상) 우선, 힐링은 최후 수단으로 계획(O6) 보정.
- 🔴 **orientation 홀짝 규칙(CRITICAL)**: 최대-대각=외곽 1개 가정이 밀폐 하우징 내부 보이드/분리 공기영역을 잘못 반전(보이드 1000이 −1000으로, 주류 입력에서 signed volume 조용히 오염). 수정: 중첩 깊이(다른 셸에 포함된 횟수) 홀수만 반전. 회귀 T2: 보이드 포함 signed=20000.0 정확.
- **solid_selection(MAJOR)**: 미선택 솔리드가 모델에 남아 메시·품질 게이트·.msh 오염. 수정: occ.remove 후 진행. 회귀 T4.
- **분류 톨러런스(MAJOR)**: OCC bbox가 절대 ~1e-7 부풀려 반환 → 미터 단위 소형 부품(diag<0.1)에서 전 면 오분류. 수정: eps=max(1e-6·diag, 1e-6). 회귀 T6.
- **run.sh(MAJOR)**: cd 후 상대 $PY 해석 실패. 절대경로로 재작성. 회귀 T1.
- MINOR 9건: 빈 그룹 STL 가드(E_INTERNAL), E_GMSH_INIT 도달성(libgmsh 부재는 CDLL(None) 성공 후 첫 호출 AttributeError — 전용 가드 추가), OSError 오분류 제거, gmsh.initialize(readConfigFiles=False)로 ~/.gmshrc 차단, stl_binary=false 존중(orientation 재작성 시), prefix/dir 타입 검증, minSICN 히스토그램(PLAN §11), E_TOO_LARGE에 size_guard 클램프 힌트, 실패 경로 경고 콘솔 출력, 리포트 기록 실패 시 FAILED 계약 라인.
- 리팩토링 중 자체 버그 1건(반환 튜플 2→4 누락)을 T1이 즉시 검출 — 테스트 우선의 가치 실증.

### 회귀 테스트 (tests/test_airmesh_regression.py, 24체크 전부 통과)
T1 골든예제 run.sh e2e / T2 밀폐 보이드 orientation / T3 다중 솔리드 / T4 solid_selection / T5 불리언 실패 주입(eps-pad 경로) / T6 미터 스케일 / T7 실패 계약. venv312로 실행, ~1분.

### 기각된 주장(수정 불필요 판정)
잔류 박스 별개 변형 주장 1건(중복), solid_selection·heal 순서 주석, cavity STL 방향 정규화, libgmsh 빌드 미반영(Phase 3 계획대로 연기).

## 2026-07-06 — Phase 3 빌드 통합 + re-exec 배포 버그 발견

### libgmsh 번들 (계획대로)
두 빌드 스크립트(build_automatedmodeller_python312.sh, build_all_python312.sh)에 `cp venv312/lib/libgmsh.so.4.15 dist/` 가산 + dist 스모크(골든 예제 → grep "Complete AIRMESH"). 실증: dist에서 AIRMESH가 사면체 10737개 정상 생성 → gmsh Python API + libgmsh 번들 정상.

### 🔴 발견: 컴파일 바이너리 re-exec 크래시 (기존 전 모드 영향, AIRMESH가 표면화)
- KooAutomatedModeller.py:46 `os.execv(sys.executable, ...)` 가 Nuitka 컴파일 바이너리에서 FileNotFoundError로 즉사. `sys.executable`이 유효 파이썬 경로가 아님. **배포된 프로덕션 바이너리 `/data/SmartTwinPreprocessor/bin/KooAutomatedModeller --help`도 동일 크래시** — 즉 배포본은 직접 호출로 어떤 모드도 기동 불가였던 잠재 버그.
- 수정: `if "__compiled__" not in globals(): os.execv(...)`. 센티넬 검증(별도 Nuitka onefile 실증): 소스=False(re-exec 실행), 컴파일=True(skip). Nuitka는 Qt/OCC를 RPATH로 번들하므로 컴파일 바이너리엔 LD_LIBRARY_PATH re-exec가 불필요.
- 안전성 증명: (a) 소스 모드 AIRMESH 정상(가드 no-op), (b) 기존 dist PKG를 re-exec 우회로 실행 → .k 정상 생성(472B, 바이트동일 기준과 일치) = Qt/OCC 로딩 무영향. **이 변경은 원래 "2-hunk만" 범위를 넘어선 공유 시작코드 수정이나, 기존 배포를 깨는 게 아니라 이미 깨져있던 것을 고침.**
- 회귀 스위트 T8/T9 추가(비봉합 셸 E_STEP_NO_SOLID / pad=0 밀착면 완주·전면밀착 E_BOOLEAN) → 29체크. E_STEP_NO_SOLID 메시지가 힐링 후 빈 dims 대신 원본 임포트 요약을 표시하도록 수정.
