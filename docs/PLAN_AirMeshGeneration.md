# PLAN — AIRMESH: STEP 솔리드 여집합(공기영역) 메시 + STL 추출 자동화

작성일: 2026-07-03. 대상 도구: **KooAutomatedModeller (KAM)** 신규 모드.
근거: 조사 에이전트 4방향 + 독립 설계안 3개 경쟁 + 3-렌즈 심사 (워크플로우 `airmesh-feature-plan`, 프로토타입 실증 포함).

---

## 1. 목표 / 사용자 요구

솔리드 `.stp` 파일 하나와 간단한 문제정의 JSON 하나만 주면, 전 과정 자동으로

1. STEP 임포트 → **bounding box** 계산 (+패딩)
2. 지정한 **메시 사이즈**로 bbox에서 솔리드를 뺀 **빈 공간(공기영역)** 을 체적 메시로 채움
3. 복셀 계단(staircase) 문제가 없는 **매끈한 경계** — 솔리드 표면에 경계추종(boundary-conforming)
4. 사면체(+장래 헥사 그리드·오면체 피라미드)로 채운 뒤 **외곽 삼각형 스킨을 STL로 추출**
5. 최종 산출물: "bbox에서 그 솔리드만 빠진" **공기 STL** (+체적 메시, 검증 리포트)

기존 5개 모드(CAPACITOR/PCB/ArrayPCB/PBA/PKG)에 대한 회귀 0이 절대 조건.

## 2. 핵심 결정 사항 (설계 경쟁 + 심사 수렴 결과)

| 결정 | 채택 | 근거 |
|---|---|---|
| v1 메시 방식 | **순수 사면체(경계추종)** | 프로토타입으로 전 구간 실증 완료(0.06초 e2e, watertight). "계단 없음"은 B-rep 추종으로 구조적으로 보장. 그리드 셀+오면체는 Phase 5 계약으로 고정 |
| 백엔드 | **gmsh 4.15.2 Python API** (in-process) | .geo/CLI로는 discrete entity·피라미드·샌드위치 표현 불가(장래 헥사코어 봉쇄). headless 동작 프로토타입 확인 |
| 설정 파일 | **JSON** (YAML 배제) | 트리 전체에 YAML 전례 0, json은 stdlib(Nuitka 플래그 불필요). YAML은 `--include-package=yaml` 누락 시 조용한 실패 |
| 코드 배치 | **신규 자급자족 패키지 `Generators/KooAirMesh/`** | KooMeshManagerGMSH 확장 금지 — sys.exit 실패지점 9~11곳 + 6개 매니저 결합으로 기존 모드 회귀 노출. 세 설계안·세 심사자 전원 일치 |
| 진입점 | **KooAutomatedModeller.py 2-hunk만** (Generate 함수 1개 + elif 1개) | Capacitor 패턴 복제. 상호배타 분기라 기존 모드에 사문(死文) |
| import 방식 | **함수-로컬(lazy) import** | gmsh.py는 import 시 CDLL 실행 — 모듈 최상단 import는 기존 5개 모드 전체를 위험에 노출. Nuitka는 함수-로컬 import도 정적 추적함 |
| 종료 규약 | **항상 exit 0** + `Complete AIRMESH :`/`AIRMESH FAILED :` stdout 라인 + `_report.json` 상시 기록 | 하우스 컨벤션(기존 Generate*는 print-and-return). 예외는 절대 KAM __main__으로 전파 금지 |
| 오면체(그리드) | **Phase 5 계약 고정** — 같은 config/산출물 계약, `mesh.mode:"hex_core"` 옵트인, 사면체 자동 폴백 | 사용자 명시 요구이므로 목적지로 계획에 포함하되, 매니폴드 수리(O10)가 실규모 미실증이라 v1 금지(심사 만장일치) |

## 3. 실증 근거 (Phase 0 프로토타입 — 완료)

스크립트·테스트 STEP 보존 위치: `Examples/automatedmodeller/airmesh_proto/` (airmesh_lib.py = 참조 구현).

- 단일 솔리드(구+실린더 융합, h=4, pad=15): **총 0.062초**, HXT 사면체 11,238개, minSICN min 0.349 / 역요소 0, air.stl watertight ✔
- 물리그룹 분리 STL(cavity/outer_box): `Mesh.SaveAll=0` + `removePhysicalGroups()` 순서 고정 시 삼각형 수 정확 일치(346==346, 2936==2936) ✔
- 다중 분리 솔리드: `occ.cut` 도구 다중 전달로 코드 변경 없이 동작 ✔
- 조대 메시(h≫형상): 크래시 없음, 다만 cavity 체적 −25.7% (facet화) → **클램프+경고**가 옳음, 에러 아님 ✔
- Delaunay 폴백 경로 검증 ✔. headless: 디스플레이/X 불필요 ✔
- 헥사코어 핵심 메커니즘(discrete sandwich): 스킨 12→12 삼각형 보존, 좌표-정확 노드 재매핑 16/16, 체적 폐합 7488.00 정확 (심사자 재검증)

### 프로토타입이 밝혀낸 함정 (P1~P5 — 구현 시 필수 반영)

- **P1 (치명)**: gmsh가 쓰는 air STL의 cavity 삼각형 법선은 **솔리드 기준 바깥**(공기 기준 안쪽) — watertight/winding 검사는 통과하면서 signed volume이 box+solid로 틀림. **trimesh 후처리 필수**: `split()` → 최대 bbox 바디=외곽 `fix_normals()` → cavity 바디 `invert()` → concatenate → binary 저장 (검증: 157,792.37 = box−solid, +0.16%)
- **P2**: 체적 검증은 CAD 값이 아니라 **이산(discrete) 기대값**(box − 이산 cavity) 대비로. CAD 차이는 faceting_error로 별도 보고
- **P3**: gmsh STL 기본이 ASCII(~5배 큼) → `Mesh.Binary=1`
- **P4**: `Mesh.SaveAll`은 전역 상태 — 모든 write 전에 명시 설정 + 그룹 write 사이 `removePhysicalGroups()` 순서 고정
- **P5**: STEP 왕복 시 면이 분할됨 — "솔리드 1개=스킨 면 1개" 가정 금지. 면별 bbox가 패딩박스 6평면 위(tol 1e-6·diag)면 outer, 아니면 cavity로 분류

## 4. 설정 파일 스키마 (airmesh.json)

```json
{
  "airmesh_version": 1,
  "input_step": "housing.stp",
  "mesh_size": 2.0,
  "units": "mm",
  "occ_target_unit": "",
  "padding": 0.0,
  "padding_relative": false,
  "solid_selection": "all",
  "heal": "auto",
  "heal_tolerance": 1e-8,
  "mesh": {
    "mode": "tetra",
    "algorithm3d": "hxt",
    "fallback": true,
    "optimize": true,
    "threads": 0,
    "size_guard": true,
    "max_estimated_elements": 50000000
  },
  "outputs": {
    "prefix": null,
    "dir": null,
    "air_stl": true,
    "split_stls": true,
    "volume_mesh": "msh",
    "geometry_debug": false,
    "stl_binary": true,
    "fix_orientation": true
  },
  "validation": {
    "volume_error_warn": 0.05,
    "min_sicn_warn": 0.10,
    "fail_on_inverted": true
  }
}
```

- 필수는 `airmesh_version`(=1), `input_step`, `mesh_size` 뿐. 나머지 전부 디폴트.
- `input_step`은 **config 파일 위치 기준** 상대경로 해석.
- 단위 정책(리포트에 상시 인쇄): 모든 길이는 모델 단위(`occ_target_unit` 스케일 적용 후). `units`는 문서화 라벨일 뿐 변환 없음. `bbox_diag/h > 1e5` 또는 `< 2`면 단위 실수 경고.
- 알 수 없는 키 → 경고(전방호환). 필수 누락/타입 오류 → 문제 전부 나열 후 `AIRMESH FAILED : invalid config`.
- `mesh.mode`: v1은 `"tetra"`만 유효. `"hex_core"`는 Phase 5 예약(같은 계약).

## 5. CLI 계약 + 진입점 후크

```
KooAutomatedModeller AIRMESH airmesh.json [workdir|none] [displayMode]
```

- 기존 argv 관행 그대로(라이선스/IP 게이트·os.execv 재실행·workdir chdir 모두 상속). displayMode는 받되 무시(완전 headless).
- **KooAutomatedModeller.py 변경은 정확히 2-hunk** (다른 기존 파일 수정 0).

Hunk 1 — GenerateCapacitor 뒤에 (~L213):

```python
def GenerateAirMesh(fileName):
    # AIRMESH: STEP 솔리드의 bbox 공기영역을 경계추종 사면체로 채우고 STL 스킨 추출
    print("Generate AIRMESH ...")
    curPath = os.getcwd()
    inputFilePath = os.path.join(curPath, fileName)
    if os.path.exists(inputFilePath) == False:
        print("AIRMESH FAILED : config file not exist : " + inputFilePath)
        return
    from KooAirMesh.AirMeshGenerator import run_from_config
    run_from_config(inputFilePath)
```

Hunk 2 — 디스패치 체인(L789-800) PKG 분기 뒤에:

```python
    elif mode == "AIRMESH":
        GenerateAirMesh(fileName)
```

`run_from_config`는 내부에서 모든 예외를 잡음 — KAM __main__으로 전파 절대 금지. `import gmsh`/`import trimesh`는 KooAirMesh 모듈 내부(함수-로컬)에만 둠.

## 6. 모듈 구성 (신규 3파일)

| 파일 | 역할 |
|---|---|
| `Generators/KooAirMesh/__init__.py` | 네임스페이스만 |
| `Generators/KooAirMesh/AirMeshGenerator.py` (~250줄) | 문제정의 JSON 로드·검증(오류 전부 수집), 스테이지 타이밍, 리포트 조립, Complete/FAILED 라인 — 오케스트레이터 |
| `Generators/KooAirMesh/AirMeshCore.py` (~400줄) | gmsh Python API 코어 — 프로토타입 `airmesh_lib.py`의 강화 이식: 세션 관리(`isInitialized()` 가드, finally에서 `finalize()`), import/heal/bbox/boolean/분류/사면체화/품질/출력/orientation 후처리 |

**기존 코드 import: 의도적으로 0.** 재사용은 (a) 패턴(Capacitor Generate* 골격, Complete 라인), (b) 빌드에 이미 포함된 의존성(trimesh/numpy/json)만. KooMeshManagerGMSH·매니저 6종은 건드리지 않음 — 기존 gmsh 바이너리 파이프라인 무영향.

## 7. 파이프라인 (Phase 1~3, tetra 경로)

```
S1 세션    gmsh.initialize()  ※ sys.argv 절대 전달 금지. Terminal=1, logger.start()
S2 임포트  occ.importShapes → dim==3 필터, solid_selection 적용. 0개면 S3 후 재시도→실패
S3 힐링    (조건부) occ.healShapes(tolerance, fixDegenerated/SmallEdges/SmallFaces/sewFaces/makeSolids)
S4 bbox    솔리드별 getBoundingBox 합집합 + getMass(CAD체적). size_guard: h ≤ 0.25·최소솔리드대각 클램프+경고. 패딩 적용
S5 불리언  addBox → occ.cut(box, solids). 검증 ΣgetMass(air) ≈ V_box−ΣV_solid (rel 1e-6)
           실패 사다리: eps-pad(1e-3·diag, 형상 무손상) 재시도 → 힐링 재시도(최후 수단) → FAIL. 슬리버(<1e-9·V_box) 제거+기록. 재시도 시 유효 bbox를 분류·리포트에 전파, 실패한 cut의 잔류 박스 제거
S6 분류    getBoundary(combined=True)=air 스킨 / (False)=면별. 면 bbox가 6평면 위 → outer, else cavity (P5)
S7 메시    MeshSizeMin=Max=h, MeshSizeFromCurvature=0, Algorithm3D=10(HXT)
           사전 가드: n_est≈8.49·V_air/h³ > max_estimated_elements → 실행 전 중단(권장 h 제시)
           실패 시 mesh.clear()→Delaunay(1)→Frontal(4) 폴백
S8 품질    getElements(3) 타입 집합=={tet4} 하드 단언 (5절점 피라미드 유입 금지 — KooElement 함정)
           getElementQualities(minSICN/gamma), fail_on_inverted 정책
S9 출력    .msh(MSH 4.1 ASCII, SaveAll=1) → STL(Binary=1, 그룹별 SaveAll=0+removePhysicalGroups 순서 고정)
           air/cavity/outer_box 3종 → air.stl에 trimesh orientation 후처리(P1) 필수
S10 검증   trimesh watertight/winding/signed volume(이산 기대값 대비, P2), _report.json, Complete 라인
```

## 8. Phase 5 계약 — 헥사 그리드 + 오면체(피라미드) 전이 (사용자 요구 최종형)

같은 config(`mesh.mode:"hex_core"`, `fallback_to_tetra:true` 디폴트)·같은 산출물 이름·같은 리포트 스키마. **계약을 메커니즘보다 강하게 고정**(선행 ConformalMesh 계획의 교훈 — 메커니즘은 구현 중 바뀐다).

검증된 메커니즘(계약의 이행 수단 후보).

1. **셀 분류**(numpy 격자): cavity 표면 삼각메시 AABB 스태빙으로 CUT 셀 마킹(보수적 초과집합=안전) → (0,0,0)에서 6-연결 flood-fill로 AIR 판정 → `buffer_layers`회 침식으로 CORE 후보 → 비매니폴드 엣지/버텍스 수리(단조 축소=수렴 보장)
2. **피라미드 삽입**: 노출된 헥사 스킨 quad마다 이웃 제거셀 중심을 apex로 하는 피라미드 1개 — **구성상 피라미드끼리·cavity와 교차 불가능**(각자 완전-공기 셀 내부에 격리). 밑변 h×h, 높이 h/2 → SICN≈0.41 균일
3. **버퍼 사면체(discrete sandwich)**: `addDiscreteEntity`로 내부 스킨+cavity 스킨 등록 → surface loop → volume → `generate(3)`. **주의(실증)**: generate(3)가 노드 태그를 재번호화하므로 태그 신뢰 금지 — **좌표-정확 재매핑** 필수. 스킨 삼각형 수 불변 단언
4. **패딩 하한**: `max(user_pad, (buffer_layers+2)·h)` — 버퍼가 bbox 벽에 닿지 않게. 위반 시 tetra 모드 자동 전환+경고
5. **기계 검증 게이트**: 체적 폐합 `V_hex+V_pyr+V_tet == V_box−V_solid_discrete`(정확 분할 불변식) + `assert_conformal()`(면 해시: 피라미드 밑면↔헥사면 1:1, 측면 삼각형↔tet면 1:1, 경계면 1회, 내부면 2회)

**선행 조건(차단기)**: `KooElement.AddElementsfromMSH`의 3D 디스패치에 5절점 분기가 없어 **피라미드가 무경고 소실**됨(검증: 4/6/8절점만 존재). 헥사코어 산출물을 매니저/.k로 내보내기 전에 임포터 확장 또는 우회 필수. v1 범위에서는 구조적으로 회피(순수 tet).

## 9. 장애물 카탈로그 (검출 → 완화)

| # | 장애 | 검출 | 완화/폴백 |
|---|---|---|---|
| O1 | 더러운 STEP(열린 셸, 봉합 틈) | importShapes에 dim-3 없음 / cut 예외 | heal 사다리 후 1회 재시도 → 실패 시 명확한 메시지("8 faces, 0 solids — 서피스 모델"). sys.exit 절대 금지 |
| O2 | 다중 솔리드/어셈블리 | len(solids)>1 (기록) | cut 도구 다중 전달(실증). solid_selection으로 수동 필터. >100개면 성능 경고 |
| O3 | 솔리드가 bbox 면에 접촉(pad=0) | bbox 극값 일치(1e-6·diag) / cut 실패 | 공면 접촉은 자연 탈락(분류 정상). cut 실패 시 eps-pad 자동 재시도(기록). 문서로 padding≥mesh_size 권장 |
| O4 | 얇은 공기 틈(<h) | air 볼륨 bbox 최소치수<h / 낮은 SICN | 비치명 — HXT가 국소 세분. "mesh_size를 틈/2 이하로" 경고 |
| O5 | h ≫ 형상 크기 | size_guard / 체적 오차(실증 −25.7%, 크래시 없음) | 클램프+경고(에러 아님). faceting_error 상시 보고 |
| O6 | 불리언 실패(OCC 예외) | Python API 예외 | eps-pad→재시도(형상 무손상 우선), heal→재시도(깨끗한 형상 열화 위험이 실증되어 최후 수단) → FAIL+OCC 메시지 |
| O7 | 슬리버 air 조각 | 볼륨별 getMass < 1e-9·V_box | occ.remove+경고+제거 체적 기록 |
| O8 | 대형 모델 성능/메모리 | 사전 n_est 가드, >5M 삼각형 | generate 전 중단(권장 h 제시). Binary STL 필수. orientation 후처리는 >5M에서 자동 스킵+경고 |
| O9 | STL 비수밀/비매니폴드 | trimesh 게이트 | 구조적 예방: combined=True 스킨+물리그룹 write. 실패 시 status=failed로 산출물 보존 |
| O10 | **Nuitka가 libgmsh 미포함** | 사후 dist 스모크 테스트 / initialize() try/except | ctypes 로드 라이브러리는 Nuitka가 절대 번들 안 함 — 실패가 지연된 missing-symbol 크래시로 나타남. **두 빌드 스크립트에 `cp venv312/lib/libgmsh.so.4.15 KooAutomatedModeller.dist/` 추가(가산적) + 스모크 테스트** |
| O11 | 단위 혼동(mm/m) | 리포트 bbox 에코 + 비율 경고 | occ_target_unit 명시 리스케일. 조용한 변환 절대 금지 |
| O12 | gmsh 세션 상태 | — | sys.argv 미전달, isInitialized 가드, finally에서 finalize, 스테이지별 모델 분리 |
| O13 | 피라미드 무경고 소실(KooElement 5절점 분기 부재) | S8 타입 집합 단언 | v1은 순수 tet로 구조 회피. 헥사코어 전 임포터 확장 필수(§8) |

## 10. 단계별 롤아웃 + 검증 기준

- **Phase 0 — 프로토타입: 완료.** `Examples/automatedmodeller/airmesh_proto/`에 보존.
- **Phase 1 — MVP e2e**: KooAirMesh 패키지(S1-S10, 분리 STL 제외) + 2-hunk 후크 + 예제 `Examples/automatedmodeller/airmesh_sphere/`.
  검증: `venv312/bin/python KooAutomatedModeller.py AIRMESH airmesh.json <예제dir>` → stdout `Complete AIRMESH` + report status=ok + trimesh watertight + 체적오차 <0.5%.
  **보호 회귀(비협상)**: 기존 CAPACITOR·PKG conformal 예제를 diff 전후 실행, .k/.step **byte-identical**(`diff -r`) + `git diff --stat`이 2-hunk+신규 패키지만 표시.
- **Phase 2 — 강화**: 분리 STL+orientation 후처리, heal 사다리, 다중 솔리드·슬리버, size guard, eps-pad, .vtk, 검증 블록 전체.
  검증: (a) 2-솔리드 예제 → watertight 분리 STL 2개, 삼각형 수 일치 (b) 조대-h → 경고 확인 (c) 고의로 깨뜨린 STEP(비봉합 셸) → `AIRMESH FAILED`+exit 0+부분 리포트 (d) pad=0 밀착면 → 정상 분류 또는 eps-pad 기록. **+실제(비합성) STEP 1개 이상** — 힐링 사다리는 아직 실전 미실증(심사 지적).
- **Phase 3 — Nuitka 빌드/배포**: 두 빌드 스크립트에 cp 1줄씩(가산) + dist 스모크 테스트(grep `Complete AIRMESH`). dist와 `/data/SmartTwinPreprocessor` 배포본 양쪽에서 스모크 통과. `build_without_automatedmodeller.sh`로는 불충분(이 기능은 KAM 빌드 필요).
- **Phase 4 — 문서/예제 사다리**: docs/manual/03_KooAutomatedModeller에 AIRMESH 문서, 예제 4종(단일/다중/조대/고장 주입). 매뉴얼 README 모드 표 갱신.
- **Phase 5 — 헥사코어+오면체(옵트인)**: §8 계약. 선행: KooElement 5절점 분기(§8) → 프로토 검증 스크립트의 재현 가능한 단위 테스트화 → S4-S8 구현 → 게이트 통과.

## 11. 산출물 정의

| 파일 | 내용 |
|---|---|
| `<prefix>_air.stl` | **주 산출물.** 공기영역 폐곡면(외곽 박스면+cavity 벽), orientation 수정 완료 — 공기 기준 외향 법선, signed volume=이산 공기체적 |
| `<prefix>_cavity.stl` | 솔리드 스킨만(법선은 솔리드 외향) |
| `<prefix>_outer_box.stl` | 패딩 박스 6면 |
| `<prefix>_air.msh` | MSH 4.1 ASCII 체적 메시 + 물리그룹(air/cavity/outer_box) — KooMSHImporter 전방호환 |
| `<prefix>_report.json` | 상시 기록(실패 시에도 best-effort): status/error, config 에코, bbox, 불리언(heal/eps-pad/슬리버), 메시(알고리즘/폴백/품질 히스토그램), 체적(이산/faceting오차), STL별 watertight/winding, 타이밍, 경고, gmsh 로그 꼬리 50줄 |

## 12. 빌드/배포 변경 (가산적 변경만)

1. `occProject/Generators/build_automatedmodeller_python312.sh`: nuitka 후 `cp ../../venv312/lib/libgmsh.so.4.15 KooAutomatedModeller.dist/` + 스모크 테스트
2. `build_all_python312.sh`: KAM 구간에 동일 cp(경로 조정)
3. 기존 nuitka 플래그·라인은 절대 변경 금지(전 모드 공유). trimesh/numpy/json은 이미 포함, gmsh.py는 함수-로컬 import를 Nuitka가 정적 추적하므로 플래그 불필요(라이브러리만 cp)
4. 후퇴선(문서화): libgmsh 번들이 스모크에서 실패하면 shipped 4.14.1 CLI 바이너리+subprocess 방식으로 tetra 경로만 대체 가능(헥사코어는 불가) — reuse 설계안의 검증된 대안

## 13. 리스크 요약

- **최대 리스크는 배포(O10)** — 기능 자체가 아니라 libgmsh 번들. cp+스모크로 관리, 후퇴선 확보
- 더러운 실전 STEP은 미실증 — Phase 2에서 실파일 게이트 필수
- 헥사코어 매니폴드 수리는 토이 검증만 — v1에서 배제, Phase 5 계약으로 관리
- 기존 기능 보호는 구조적(사문 elif+독립 패키지)+절차적(byte-identical 회귀)으로 이중 보장
