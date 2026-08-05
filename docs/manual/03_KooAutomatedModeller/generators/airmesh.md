# AIRMESH — STEP 공기영역/공동 메시 + STL 추출

> **한 줄 요약.** 솔리드 STEP 하나와 JSON 하나로, bounding box(+패딩)에서 솔리드를 뺀 **공기영역**을 경계추종 사면체로 채우고 공동/외곽 STL을 뽑는다.
>
> 소스 `occProject/Generators/KooAirMesh/` (AirMeshCore.py / AirMeshGenerator.py) · 후크 `KooAutomatedModeller.py`의 `GenerateAirMesh` + `elif mode == "AIRMESH"`
> 설계 문서 `docs/PLAN_AirMeshGeneration.md` · 회귀 테스트 `tests/test_airmesh_regression.py` (29체크)
> 이 문서의 예제 설정값은 전부 회귀 스위트에서 실제로 도는 값이다.

---

## 목차

1. [목적](#1-목적)
2. [실행 방법](#2-실행-방법)
3. [예제 모음](#3-예제-모음)
4. [설정 레퍼런스](#4-설정-레퍼런스)
5. [산출물](#5-산출물)
6. [성패 판정과 오류 코드](#6-성패-판정과-오류-코드)
7. [주의사항 (실증 기반)](#7-주의사항-실증-기반)
8. [검증 방법](#8-검증-방법)
9. [설계·배포 노트](#9-설계배포-노트)
10. [범위 밖](#10-범위-밖-v1-미구현)

---

## 1. 목적

솔리드 STEP 파일 하나와 문제정의 JSON 하나로, bounding box(+패딩)에서 솔리드를 뺀 **공기영역**을 경계추종(boundary-conforming) 사면체로 채우고 외곽 삼각형 스킨을 STL로 추출한다. 메시가 B-rep 표면을 그대로 따르므로 복셀 방식의 계단(staircase) 문제가 없다.

백엔드는 gmsh Python API(in-process)이며 기존 `KooMeshManagerGMSH`(.geo/서브프로세스)와 완전히 분리되어 있다.

---

## 2. 실행 방법

```bash
# 운영 (배포 바이너리)
KooAutomatedModeller AIRMESH airmesh.json /출력/디렉토리

# 개발 (소스)
cd occProject/Generators
../../venv312/bin/python KooAutomatedModeller.py AIRMESH airmesh.json /출력/디렉토리
```

- argv 관행은 기존 모드와 동일하다(라이선스/IP 게이트, workdir chdir 상속). 4번째 인자 `displayMode`는 받되 무시한다(완전 headless).
- 3번째 인자 = 작업/출력 디렉토리(생략 시 현재 디렉토리). `outputs.dir`로도 지정할 수 있다.
- **종료 코드는 항상 0이다**(하우스 컨벤션). 성패는 [§6](#6-성패-판정과-오류-코드) 방법으로 판정해야 한다.

### 최소 설정 (필수 3키)

```json
{
  "airmesh_version": 1,
  "input_step": "housing.stp",
  "mesh_size": 2.0
}
```

`input_step`은 **JSON 파일 위치 기준** 상대경로로 해석된다. 산출물 접두어(`prefix`)의 기본값은 **JSON 파일명**이라 `airmesh.json` → `airmesh_air.stl` / `airmesh_cavity.stl`로 떨어진다.

---

## 3. 예제 모음

### E1. 기본 — 단순 솔리드 주변 공기 (골든 예제)

`Examples/automatedmodeller/airmesh_sphere/`를 그대로 실행한다(`run.sh`).

```json
{
  "airmesh_version": 1,
  "input_step": "sphere_cyl.stp",
  "mesh_size": 4.0,
  "units": "mm",
  "padding": 15.0
}
```

솔리드 bbox를 사방 15mm 키운 박스에서 솔리드를 뺀 공기영역을 4mm 사면체로 채운다.

### E2. 밀폐 내부 보이드가 있는 하우징

속이 빈 하우징처럼 **내부에 갇힌 공동**이 있어도 그대로 잡힌다(공기 = 외부 공기 + 내부 보이드).

```json
{
  "airmesh_version": 1,
  "input_step": "hollow_housing.step",
  "mesh_size": 2.0,
  "padding": 5.0
}
```

> 검증(T2). 30³ 박스 − (20³ 솔리드 − 10³ 보이드) = 공기 20000(보이드 1000 포함) 체적 일치.
> 내부 보이드 법선은 `outputs.fix_orientation`(기본 on)이 중첩 깊이 홀짝 규칙으로 보정한다.

### E3. 솔리드가 여러 개인 STEP

```json
{
  "airmesh_version": 1,
  "input_step": "assembly.step",
  "mesh_size": 3.0,
  "padding": 8.0
}
```

`solid_selection` 기본값이 `"all"`이라 STEP 안의 모든 솔리드가 차집합 도구로 쓰인다.

### E4. 일부 솔리드만 빼고 싶을 때

```json
{
  "airmesh_version": 1,
  "input_step": "assembly.step",
  "mesh_size": 2.0,
  "padding": 5.0,
  "solid_selection": [1]
}
```

- 인덱스는 **1-based**다.
- ⚠ **미선택 솔리드는 모델에서 제거된다**(공기영역에 흡수됨). 리포트에 경고가 남는다.

### E5. 한쪽 면만 벽에 붙이기 (방향별 패딩)

```json
{
  "airmesh_version": 1,
  "input_step": "solid_box.step",
  "mesh_size": 2.0,
  "padding": [0, 5, 5, 5, 5, 5]
}
```

배열 순서는 `[x-, x+, y-, y+, z-, z+]`이다. 위 예는 x− 방향만 밀착(패딩 0)이다.

> 주의. **모든 방향을 0으로 주면** 솔리드가 박스를 꽉 채워 공기가 0이 되고 `E_BOOLEAN`으로 실패한다(T9에서 의도적으로 검증).

### E6. 미터 단위 모델

```json
{
  "airmesh_version": 1,
  "input_step": "part_in_meters.step",
  "mesh_size": 0.002,
  "padding": 0.005
}
```

`mesh_size`/`padding`은 **모델 단위 그대로**다. 단위 변환이 필요하면 `occ_target_unit`(`"MM"`, `"M"` 등)으로 OCC 리스케일을 건다.

### E7. 미세 형상(PCB/ECAD 등) — 요소 폭발 방지

```json
{
  "airmesh_version": 1,
  "input_step": "pcb_multiscale.stp",
  "mesh_size": 0.2,
  "padding": 2.0,
  "mesh": { "size_guard": false }
}
```

`size_guard`(기본 on)는 `h ≤ 0.25 × 최소 솔리드 대각`으로 클램프하는데, 15µm 층 같은 미세 피처가 있으면 h가 극단적으로 작아져 요소가 폭발한다. **의도한 해상도를 강제**하려면 위처럼 끄고 `mesh_size`를 명시한다.

> 실증. 273 트레이스 멀티스케일 Cu/PPG 회로에서 watertight 공기 STL 생성을 확인했다.
> 겹치는 Cu/PPG 솔리드가 있으면 air.stl은 정확하나(union 절단) 체적 교차검증이 겹침을 경고한다.

### E8. 대형 모델 — 안전하게 먼저 찔러보기

```json
{
  "airmesh_version": 1,
  "input_step": "big_assembly.step",
  "mesh_size": 5.0,
  "padding": 10.0,
  "mesh": { "max_estimated_elements": 5000000 },
  "outputs": { "volume_mesh": "none" }
}
```

- `max_estimated_elements`. **메시 생성 전에** 요소 수를 추산해 초과 시 `E_TOO_LARGE`로 중단한다 → 메모리 사고 방지.
- `volume_mesh: "none"`. STL만 필요할 때 .msh를 안 써서 시간·용량을 절약한다.

### E9. 메시 알고리즘 바꾸기

```json
{
  "airmesh_version": 1,
  "input_step": "tricky.step",
  "mesh_size": 1.5,
  "padding": 5.0,
  "mesh": { "algorithm3d": "delaunay", "fallback": true }
}
```

기본 `hxt`가 실패하면 `fallback: true`(기본값)가 `delaunay` → `frontal` 사다리를 자동으로 탄다. 특정 알고리즘을 고정하고 싶을 때만 지정한다.

---

## 4. 설정 레퍼런스

필수 키는 3개뿐이며 나머지는 전부 디폴트가 있다.

### 최상위

| 키 | 기본값 | 의미 |
|---|---|---|
| `airmesh_version` | **필수** | 스키마 버전, `1` 고정 |
| `input_step` | **필수** | STEP 경로 — config 파일 위치 기준 상대경로 해석 |
| `mesh_size` | **필수** | 목표 요소 크기 h (>0, 모델 단위) |
| `units` | `"model"` | 문서화 라벨 — 변환 없음, 리포트에 에코 |
| `occ_target_unit` | `""` | 비었으면 파일 단위 유지, `"MM"`/`"M"` 등이면 OCC가 리스케일 |
| `padding` | `0.0` | 스칼라 또는 `[x-,x+,y-,y+,z-,z+]` |
| `padding_relative` | `false` | `true`면 padding을 bbox 대각선 비율로 해석 |
| `solid_selection` | `"all"` | `"all"` 또는 1-based 인덱스 리스트. 미선택 솔리드는 제거됨 |
| `heal` | `"auto"` | `auto`(필요 시만) \| `always` \| `never` — ⚠ `always` 금지 권장([§7](#7-주의사항-실증-기반)) |
| `heal_tolerance` | `1e-8` | 힐링 허용오차 |

### `mesh`

| 키 | 기본값 | 의미 |
|---|---|---|
| `mode` | `"tetra"` | v1은 tetra만 (`hex_core`는 Phase 5 예약) |
| `algorithm3d` | `"hxt"` | `hxt` \| `delaunay` \| `frontal` |
| `fallback` | `true` | 실패 시 알고리즘 사다리 자동 재시도 |
| `optimize` | `true` | 메시 품질 최적화 |
| `threads` | `0` | 0 = 자동 |
| `size_guard` | `true` | `h ≤ 0.25×최소솔리드대각` 클램프 + 경고 |
| `max_estimated_elements` | `50000000` | 사전 요소수 가드 — 초과 시 실행 전 중단 |

### `outputs`

| 키 | 기본값 | 의미 |
|---|---|---|
| `prefix` | config 파일명 stem | 산출물 접두어 |
| `dir` | cwd (=workdir 인자) | 출력 디렉토리 |
| `air_stl` | `true` | 공기영역 STL 생성 |
| `split_stls` | `true` | cavity / outer_box 분리 STL |
| `volume_mesh` | `"msh"` | `msh`(4.1 ASCII) \| `vtk` \| `both` \| `none` |
| `stl_binary` | `true` | binary STL (false면 ASCII) |
| `fix_orientation` | `true` | air.stl 법선을 공기-외향으로 보정 — ⚠ 끄지 말 것 |
| `geometry_debug` | `false` | 디버그 형상 덤프 |

### `validation`

| 키 | 기본값 | 의미 |
|---|---|---|
| `volume_error_warn` | `0.05` | 체적 오차 경고 임계 (5%) |
| `min_sicn_warn` | `0.10` | 최소 품질 경고 임계 |
| `fail_on_inverted` | `true` | 역요소 존재 시 status=failed (산출물은 보존) |

---

## 5. 산출물

`prefix`가 `airmesh`일 때 기준이다.

| 파일 | 내용 |
|---|---|
| `airmesh_air.stl` | **주 산출물.** 공기영역 폐곡면(binary), 공기-외향 법선, signed volume = 이산 공기체적 |
| `airmesh_cavity.stl` | **솔리드 스킨 = 내부 공동 면** |
| `airmesh_outer_box.stl` | 패딩 박스 6면 |
| `airmesh_air.msh` | 체적 사면체 메시 + 물리그룹(`air_volume`/`cavity`/`outer_box`) |
| `airmesh_report.json` | **실패해도 항상 기록.** status/error, bbox, 불리언 재시도 이력, 품질(minSICN 히스토그램), 체적 검증, STL watertight, 타이밍, gmsh 로그 꼬리 |

---

## 6. 성패 판정과 오류 코드

종료 코드는 **항상 0**이므로 아래 둘 중 하나로 판정한다.

```bash
# 방법 1 — stdout 라인
KooAutomatedModeller AIRMESH airmesh.json "$OUT" | tee log.txt
grep -q "^Complete AIRMESH" log.txt && echo OK || echo FAIL

# 방법 2 — 리포트 status (권장)
python -c "import json;print(json.load(open('$OUT/airmesh_report.json'))['status'])"
```

성공 시 `Complete AIRMESH : <report경로>`, 실패 시 `AIRMESH FAILED : <사유>`가 stdout에 찍힌다.

| 코드 | 원인 | 대처 |
|---|---|---|
| `E_CONFIG` | 설정 오류 (전부 나열됨) | 메시지대로 수정. 필수 3키·경로 확인 |
| `E_STEP_IMPORT` | STEP 임포트 실패 | 파일 손상/버전 확인 |
| `E_STEP_NO_SOLID` | **서피스 모델** (닫힌 솔리드 없음) | 리포트의 엔티티 요약(dim:개수) 확인 → CAD에서 솔리드화 |
| `E_BOOLEAN` | 공기 볼륨 0 (eps-pad·힐링 재시도 후) | `padding`을 키운다. 솔리드가 박스를 꽉 채운 상태 |
| `E_TOO_LARGE` | 사전 요소수 가드 초과 | `mesh_size`를 키우거나 `max_estimated_elements` 조정 |
| `E_MESH` | 알고리즘 사다리 소진 | 형상 품질 점검, `heal:"auto"` 유지, `mesh_size` 조정 |
| `E_QUALITY` | 역요소 존재 | `mesh_size` 조정. 산출물은 보존되니 리포트 히스토그램 확인 |
| `E_STL_INVALID` | 비수밀 STL | 형상/패딩 재검토 |
| `E_GMSH_INIT` | libgmsh 로드 실패 | **배포 문제.** dist에 `libgmsh.so.4.15` 누락 |
| `E_INTERNAL` | 기타 | 리포트의 gmsh 로그 꼬리 확인 |

---

## 7. 주의사항 (실증 기반)

- **P1 orientation.** gmsh가 쓰는 air STL의 cavity 법선은 솔리드-외향이라 signed volume이 틀어진다. `fix_orientation`(기본 on)이 중첩 깊이 홀짝 규칙으로 보정한다 — 밀폐 하우징의 내부 보이드, 분리 공기영역까지 처리한다. **끄지 말 것.**
- **`heal: "always"` 금지 권장.** 깨끗한 형상에 healShapes를 강제하면 구면이 주기면으로 재구성되어 메시가 불가능해진다(`Impossible to mesh periodic surface`). 기본 `auto`를 유지한다.
- **불리언 재시도 사다리.** eps-pad(1e-3·diag, 형상 무손상) → 힐링(최후 수단) 순이다. 재시도 시 유효 bbox가 분류·리포트에 반영된다.
- **체적 검증.** 이산 기대값(box − 이산 cavity) 대비로 판정하고 CAD 차이는 faceting 오차로 별도 보고한다. 조대 메시는 에러가 아니라 경고+클램프다.
- **요소 수 폭발.** 미세 피처 + `size_guard` on 조합에서 발생한다. [E7](#e7-미세-형상pcbecad-등--요소-폭발-방지) 참고.
- **실제 ECAD/PCB 실증됨.** 멀티스케일 Cu/PPG 회로(273 트레이스, 15µm 층)까지 watertight 공기 STL 생성을 확인했다. 겹치는 Cu/PPG 솔리드는 air.stl이 정확하나(union 절단) 체적 교차검증이 겹침을 경고한다.

---

## 8. 검증 방법

기능을 수정했으면 아래를 돌린다.

```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE
./venv312/bin/python tests/test_airmesh_regression.py     # 29체크, ~1분
```

커버 범위. 골든 재현(T1), 밀폐 보이드 체적(T2), 다중 솔리드(T3), 솔리드 선택 + 잔류메시 없음(T4), eps-pad 재시도(T5), 미터 스케일(T6), 실패 계약/리포트(T7), 서피스 모델 우아한 실패(T8), 한 면 밀착·공기 0(T9).

---

## 9. 설계·배포 노트

- **백엔드 분리.** gmsh Python API를 in-process로 쓴다. 기존 `KooMeshManagerGMSH`(.geo 파일 + 서브프로세스)와 코드·수명주기가 완전히 분리되어 있다.
- **배포(Nuitka) 함정.** gmsh Python API의 libgmsh는 ctypes 로드라 Nuitka가 번들하지 않는다. 빌드 스크립트가 `libgmsh.so.4.15`를 dist 루트에 복사하고 AIRMESH 스모크 테스트로 검증한다(`build_automatedmodeller_python312.sh`). 누락되면 배포 머신에서 첫 호출에 크래시한다(`E_GMSH_INIT`).
- **healShapes 수명주기.** gmsh healShapes는 원본을 소모하고 치유본으로 교체한다. 원본 remove 금지이며 `getEntities(3)`로 다시 조회해야 한다.
- **분류 eps.** OCC bbox는 절대 1e-7만큼 부풀려 나오므로 분류 epsilon의 하한으로 쓴다.
- **물리그룹.** 빈 물리그룹 + `SaveAll=0` 조합이면 전체 요소가 유출된다.

---

## 10. 범위 밖 (v1 미구현)

- `mesh.mode: "hex_core"` (헥사 코어 + 오면체 피라미드 전이) — Phase 5 계약, `docs/PLAN_AirMeshGeneration.md` §8에 예약되어 있다.
