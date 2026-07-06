# AIRMESH — STEP 공기영역(bbox−솔리드) 사면체 메시 + STL 추출

> 근거 소스: `occProject/Generators/KooAirMesh/` (AirMeshCore.py / AirMeshGenerator.py), 후크 `KooAutomatedModeller.py`의 `GenerateAirMesh` + `elif mode == "AIRMESH"`
> 설계 문서: `docs/PLAN_AirMeshGeneration.md` · 회귀 테스트: `tests/test_airmesh_regression.py`

## 1. 목적

솔리드 STEP 파일 하나와 문제정의 JSON 하나로, bounding box(+패딩)에서 솔리드를 뺀 **공기영역**을 경계추종(boundary-conforming) 사면체로 채우고 외곽 삼각형 스킨을 STL로 추출한다. 메시가 B-rep 표면을 그대로 따르므로 복셀 방식의 계단(staircase) 문제가 없다. 백엔드는 gmsh Python API(in-process)이며 기존 KooMeshManagerGMSH(.geo/서브프로세스)와 완전히 분리되어 있다.

## 2. 사용법

```
KooAutomatedModeller AIRMESH airmesh.json [workdir|none] [displayMode]
```

- 기존 모드와 동일한 argv 관행(라이선스/IP 게이트, workdir chdir 상속). `displayMode`는 받되 무시(완전 headless).
- 종료 코드는 항상 0 (하우스 컨벤션). 기계 판정은 stdout의 `Complete AIRMESH : <report경로>` / `AIRMESH FAILED : <사유>` 라인과 `<prefix>_report.json`의 `status`로 한다.

## 3. 문제정의 JSON

필수 키는 3개뿐이며 나머지는 전부 디폴트가 있다.

```json
{ "airmesh_version": 1, "input_step": "housing.stp", "mesh_size": 2.0 }
```

| 키 | 기본값 | 의미 |
|---|---|---|
| `airmesh_version` | (필수) | 스키마 버전, 1 고정 |
| `input_step` | (필수) | STEP 경로 — **config 파일 위치 기준** 상대경로 해석 |
| `mesh_size` | (필수) | 목표 요소 크기 h (모델 단위) |
| `units` | `"model"` | 문서화 라벨(변환 없음). 리포트에 에코 |
| `occ_target_unit` | `""` | 비었으면 파일 단위 유지, `"MM"`/`"M"` 등이면 OCC가 리스케일 |
| `padding` | `0.0` | 스칼라 또는 `[x-,x+,y-,y+,z-,z+]`. `padding_relative:true`면 대각선 비율 |
| `solid_selection` | `"all"` | 차집합 도구로 쓸 솔리드(1-based). 미선택 솔리드는 모델에서 제거됨 |
| `heal` | `"auto"` | `auto`(필요 시만)\|`always`\|`never`. ⚠ `always`는 깨끗한 형상을 열화시킬 수 있음(§7) |
| `mesh.algorithm3d` | `"hxt"` | `hxt`\|`delaunay`\|`frontal` (+`fallback:true`면 실패 시 사다리) |
| `mesh.size_guard` | `true` | h ≤ 0.25·최소솔리드대각 클램프+경고 |
| `mesh.max_estimated_elements` | `5e7` | 사전 요소수 가드 — 초과 시 실행 전 중단 |
| `outputs.split_stls` | `true` | cavity/outer_box 분리 STL |
| `outputs.volume_mesh` | `"msh"` | `msh`(4.1 ASCII)\|`vtk`\|`both`\|`none` |
| `outputs.fix_orientation` | `true` | air.stl 법선을 공기-외향으로 보정(§7 P1) — 끄지 말 것 |
| `validation.fail_on_inverted` | `true` | 역요소 존재 시 status=failed (산출물은 보존) |

## 4. 산출물

| 파일 | 내용 |
|---|---|
| `<prefix>_air.stl` | **주 산출물.** 공기영역 폐곡면(binary), 공기-외향 법선, signed volume = 이산 공기체적 |
| `<prefix>_cavity.stl` / `_outer_box.stl` | 솔리드 스킨 / 패딩 박스면 분리 STL |
| `<prefix>_air.msh` | 체적 사면체 메시 + 물리그룹(air_volume/cavity/outer_box) |
| `<prefix>_report.json` | 상시 기록(실패 시에도) — status/error, bbox, 불리언(재시도 이력), 품질(minSICN 히스토그램), 체적 검증, STL watertight, 타이밍, gmsh 로그 꼬리 |

## 5. 오류 코드

`E_CONFIG`(설정 오류 전체 나열) · `E_STEP_IMPORT` · `E_STEP_NO_SOLID`(서피스 모델 — 임포트 엔티티 요약 포함) · `E_BOOLEAN`(eps-pad·힐링 재시도 후) · `E_TOO_LARGE`(사전 가드, size_guard 클램프 힌트 포함) · `E_MESH`(알고리즘 사다리 소진) · `E_QUALITY`(역요소) · `E_STL_INVALID`(비수밀) · `E_GMSH_INIT`(libgmsh 로드 실패 — 배포 문제) · `E_INTERNAL`.

## 6. 예제

골든 예제 `Examples/automatedmodeller/airmesh_sphere/` (`run.sh` 실행). 회귀 스위트 `venv312/bin/python tests/test_airmesh_regression.py` — 밀폐 보이드, 다중 솔리드, 불리언 실패 주입, 미터 스케일, 밀착면 등 29체크.

## 7. 주의사항 (실증 기반)

- **P1 orientation**: gmsh가 쓰는 air STL의 cavity 법선은 솔리드-외향이라 signed volume이 틀어진다. `fix_orientation`(기본 on)이 중첩 깊이 홀짝 규칙으로 보정한다 — 밀폐 하우징의 내부 보이드, 분리 공기영역까지 처리.
- **heal=always 금지 권장**: 깨끗한 형상에 healShapes를 강제하면 구면이 주기면으로 재구성되어 메시 불가("Impossible to mesh periodic surface"). 기본 `auto` 유지.
- **불리언 재시도 사다리**: eps-pad(1e-3·diag, 형상 무손상) → 힐링(최후 수단). 재시도 시 유효 bbox가 분류·리포트에 반영된다.
- **체적 검증**: 이산 기대값(box−이산 cavity) 대비로 판정하고 CAD 차이는 faceting 오차로 별도 보고 — 조대 메시는 에러가 아니라 경고+클램프.
- **배포(Nuitka)**: gmsh Python API의 libgmsh는 ctypes 로드라 Nuitka가 번들하지 않는다. 빌드 스크립트가 `libgmsh.so.4.15`를 dist 루트에 복사하고 AIRMESH 스모크 테스트로 검증한다(`build_automatedmodeller_python312.sh`). 누락 시 배포 머신에서 첫 호출에 크래시.
- **실제 ECAD/PCB (실증됨)**: 멀티스케일 Cu/PPG 회로(273 트레이스, 15µm 층)까지 watertight 공기 STL 생성 확인. 단 미세 트레이스가 있으면 `size_guard`(기본 on)가 h를 극단적으로 클램프해 요소가 폭발할 수 있음 — 이 경우 `mesh.size_guard:false` + 명시적 `mesh_size`로 의도한 해상도를 강제하고, 겹치는 Cu/PPG 솔리드는 air.stl은 정확(union 절단)하나 체적 교차검증이 겹침을 경고한다.
- **미구현(v1 범위 외)**: `mesh.mode:"hex_core"`(헥사 그리드+오면체 피라미드 전이)는 Phase 5 계약으로 예약 — `docs/PLAN_AirMeshGeneration.md` §8.
