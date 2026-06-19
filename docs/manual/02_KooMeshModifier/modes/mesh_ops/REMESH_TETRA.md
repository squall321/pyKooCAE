# KooMeshModifier 모드: REMESH_TETRA

## 1. 목적 / 개요

`REMESH_TETRA`는 찌그러진(품질이 낮은) **사면체(TETRA) 솔리드 파트**를 외부 메셔 **gmsh**로 다시 메싱하여 메시 품질을 개선하는 KooMeshModifier 모드이다. 외곽면을 STL로 추출한 뒤 gmsh로 3D 재메시하고, 원본 노드/요소를 새 메시로 교체한다.

핵심 동작 요약 (`KooTetraRemesher.py:4-5` docstring):
- 외곽면 STL 추출 → gmsh 3D 메시 생성 → 원본 교체
- 재료 물성 → P-파 음속 → 최소 안정 dt를 만족하는 최소 요소 크기(`L_min`)를 gmsh `CharacteristicLengthMin`으로 설정하여 최소 timestep을 확보
- 다른 파트와 공유하는 노드는 좌표/ID를 보존(기본값)하여 Tied/접촉 안전성 유지

대상은 TETRA4 / TETRA10, 또는 퇴화된 HEXA8(고유 노드 5개 이하)이며, 그 외 솔리드 타입은 skip 된다 (`KooTetraRemesher.py:110-116`).

## 2. 입력 옵션 · 인자

KooMeshModifier 입력 `.k`(step_config) 안에서 `*Mode` 블록에 `REMESH_TETRA,<modeid>`를 등록하고, 별도의 `**RemeshTetra,<modeid>` 옵션 블록에 세부 옵션을 기술한다.

모드 등록: `KooMeshModifier.py:255-257` (`remesh_tetra` → `REMESH_TETRA`)
옵션 파싱: `KooMeshModifier.py:1831-1869` (`**remeshtetra` 블록)
디스패치: `KooMeshModifier.py:2801-2803` → `GenerateRemeshTetra` (`KooMeshModifier.py:2552-2554`)

| 옵션 카드 | 인자 | 의미 | 기본값 | 근거 |
|---|---|---|---|---|
| `*PID` | `pid1,pid2,...` | 리메시 대상 파트 ID 리스트 (복수 가능) | (없으면 종료) | `KooMeshModifier.py:1843-1846` |
| `*MinDt` | `value` | 보장할 최소 안정 timestep. 이 값을 만족하는 최소 요소 크기를 `CharacteristicLengthMin`으로 설정 | `0.0` (제한 없음) | `KooMeshModifier.py:1847-1849`, `KooTetraRemesher.py:69,247` |
| `*TargetEdgeLength` | `value` | 목표 요소 크기(`CharacteristicLengthMax`). `0`이면 objective에 따라 자동 결정 | `0.0` (자동) | `KooMeshModifier.py:1850-1852`, `KooTetraRemesher.py:70,250-258` |
| `*MaxAspectRatio` | `value` | 검증 시 허용 최대 aspect ratio(max_edge/min_edge). 초과 요소가 있으면 경고 + 재시도 트리거 | `10.0` | `KooMeshModifier.py:1853-1855`, `KooTetraRemesher.py:71,441-447` |
| `*SmoothingIterations` | `int` | gmsh `Mesh.Smoothing`(Laplacian) 반복 횟수 | `5` | `KooMeshModifier.py:1856-1858`, `KooTetraRemesher.py:72,552` |
| `*PreserveSharedNodes` | `True`/`False` | 다른 파트와 공유하는 노드의 좌표/ID 보존 여부. `false`(대소문자 무관)만 False, 그 외는 True | `True` | `KooMeshModifier.py:1859-1861`, `KooTetraRemesher.py:73` |
| `*Objective` | `quality`/`coarsen`/`refine`/`match_dt` | 목표 요소 크기 자동 결정 방식 (TargetEdgeLength=0일 때만 적용) | `quality` | `KooMeshModifier.py:1862-1864`, `KooTetraRemesher.py:74-75,250-258` |

`*Objective`별 자동 목표 크기 (`TargetEdgeLength<=0`일 때, `KooTetraRemesher.py:250-258`):
- `quality`: `avg_edge` (기존 평균 유지)
- `coarsen`: `avg_edge * 2.0` (요소 수 감소)
- `refine`: `avg_edge * 0.5` (요소 수 증가)
- `match_dt`: `max(L_min*1.5, avg_edge*0.5)` (min_dt 지정 시)

참고: `*Objective`는 README.txt에는 없지만 코드 파서와 구현에 존재한다.

## 3. 사용 예제

### KooMeshModifier 입력 (step_config) — `Examples/remesh_tetra/step_config.txt` 그대로

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

실행:

```
KooMeshModifier step_config.txt
```

### scenario.json (KooChainRun 연동) — `Examples/remesh_tetra/README.txt` 발췌

```json
{
  "simulation_params": {
    "remesh_tetra": {
      "pids": [100099, 35202],
      "min_dt": 1.0e-8,
      "target_edge_length": 0.5,
      "max_aspect_ratio": 10.0,
      "smoothing_iterations": 5,
      "preserve_shared_nodes": true
    }
  }
}
```

(확인 필요: 위 scenario.json `remesh_tetra` 블록 → step_config 변환 경로는 README 예시 기준이며, KooChainRun/CumulativeDesigner 측 매핑 코드는 본 조사 범위에서 미확인.)

## 4. 동작 원리 (코드 근거)

진입점은 `GenerateRemeshTetra` → `advancedModification.RemeshTetra(curOption)` (`KooMeshModifier.py:2552-2554`) → `KooDynaAdvancedModification.RemeshTetra`가 `KooTetraRemesher.remesh_tetra_parts` 호출 (`KooDynaAdvancedModification.py:5052-5055`).

`remesh_tetra_parts` (`KooTetraRemesher.py:49-165`):
- 옵션 파싱 후 PID가 없으면 즉시 종료 (`KooTetraRemesher.py:77-79`).
- **보존 include 충돌 검사**: 대상 PID가 `preserve_includes`로 지정된 include 안에 있으면 `ValueError`로 중단 (`KooTetraRemesher.py:18-46`, `82`).
- gmsh 바이너리 경로 탐색: `KooPart._find_linux_gmsh(basePath=...)` (`KooTetraRemesher.py:88-91`). 예상 경로 예: `Library/gmsh-4.14.1-Linux64/bin/gmsh` (README 기준, 확인 필요).
- PID마다 사면체/재료 유효성 검사 후 `_remesh_single_part`를 최대 3회 재시도(`max_retries=3`). 성공 + bad AR=0이면 종료, bad AR이 남으면 `target_edge *= 0.7`로 줄여 재시도 (`coarsen`은 재시도 안 함) (`KooTetraRemesher.py:139-160`).

`_remesh_single_part`의 5단계 (`KooTetraRemesher.py:168-467`):

1. **사전 분석** (`KooTetraRemesher.py:180-240`): 요소별 min edge length, 안정 dt 계산 → `min/avg/max edge`, `old_min_dt`, worst/초과 aspect ratio 출력. dt·edge는 `compute_element_stable_dt`, `compute_element_min_edge_length`(`KooElement`) 사용.

2. **L_min 및 목표 크기 결정** (`KooTetraRemesher.py:242-266`):
   - P-파 음속 `c = sqrt(E*factor/rho)`, `factor=(1-nu)/((1+nu)(1-2nu))` (`KooTetraRemesher.py:243-246`).
   - `L_min = min_dt * c` (min_dt>0), 아니면 `avg_edge * 0.1` (`KooTetraRemesher.py:247`).
   - 목표 요소 크기는 objective에 따라 결정 (위 2절) (`KooTetraRemesher.py:250-258`).

3. **공유 노드 수집** (`KooTetraRemesher.py:268-296`): `preserve_shared=True`면 다른 파트 요소가 사용하는 노드 중 본 파트와 겹치는 노드를 `shared_nids`로 모으고 좌표 저장.

4. **STL 추출 + gmsh 리메시** (`KooTetraRemesher.py:298-331`):
   - 외곽면: `elemMan.GetExternalBoundary(False)` (`KooTetraRemesher.py:300`).
   - `_write_stl`로 STL 작성, `_write_geo`로 .geo 작성 후 gmsh subprocess 실행:
     `gmsh ... -setnumber Mesh.MshFileVersion 2.2 input.geo -3 -o output.msh -format msh2` (`KooTetraRemesher.py:324-326`).
   - `_write_geo` (`KooTetraRemesher.py:528-567`) 주요 설정:
     - `ClassifySurfaces{40 * Pi/180, 1, 1}` — feature edge 40도 기준 면 분류 (`line 537`)
     - `Mesh.CharacteristicLengthMin = L_min`, `...Max = target_edge` (`line 547-548`)
     - `Mesh.Algorithm3D = 10` (HXT), `OptimizeNetgen=1`, `Optimize=1` (`line 549-551`)
     - `Mesh.QualityType = 2` (SICN), `OptimizeThreshold = 0.3`, `AnisoMax = 3.0` (`line 554-556`)
     - `Mesh.ElementOrder = 1` (선형, TETRA4) (`line 553`)
     - 공유 노드는 `Point{...} In Volume{1}`로 고정점 삽입 (`line 559-567`)

5. **결과 교체 + 검증** (`KooTetraRemesher.py:333-467`):
   - `.msh`(v2) 파싱: 노드 + 사면체만 추출 (`_read_msh`, `KooTetraRemesher.py:570`).
   - 공유 노드는 KDTree로 좌표 매칭(tolerance `1e-4`)하여 원본 NID로 유지 (`KooTetraRemesher.py:344-356`).
   - 기존 노드/요소 삭제(공유 노드 제외) → 새 노드/요소를 max NID/EID 이후 번호로 추가 (`KooTetraRemesher.py:358-403`). 재료/섹션/PID는 그대로 유지(파트 컨테이너 자체는 보존).
   - 검증: 새 min dt / edge / aspect ratio 출력, 전후 비교 표 출력. `min_dt` 미달 또는 AR 초과 요소가 있으면 경고 (`KooTetraRemesher.py:408-462`).

디스패치 시 출력 파일명에는 접미사 `_remesh`가 붙는다 (`KooMeshModifier.py:2803`).

## 5. 주의사항 · 한계

- **대상 한정**: TETRA4/TETRA10 및 퇴화 HEXA8(고유 노드 ≤5)만 처리. 정상 HEXA8/PENTA6 등은 skip (`KooTetraRemesher.py:110-116`).
- **재료 필요**: 파트에 재료가 없거나 `E<=0` 또는 `rho<=0`이면 skip (음속/dt 계산 불가) (`KooTetraRemesher.py:120-128`). `nu>0.45`는 음속 계산용으로 0.45로 클램프 (`KooTetraRemesher.py:131-133`).
- **gmsh 의존**: 외부 gmsh 바이너리가 있어야 하며, 없거나 실행 실패(exit≠0 또는 .msh 미생성) 시 해당 파트는 실패 처리 (`KooTetraRemesher.py:328-331`).
- **초기 상태 소실**: 노드/요소가 완전히 교체되므로 기존 초기 응력/변형률 등 요소 상태는 보존되지 않음 (재메시 본질, README.txt 명시).
- **보존 include 충돌**: 대상 PID가 `preserve_includes`에 포함되면 `ValueError`로 즉시 중단 (`KooTetraRemesher.py:18-46`).
- **공유 노드 매칭 실패 가능**: KDTree 매칭 tolerance(`1e-4`) 초과 시 경고만 출력하고 해당 공유 노드는 보존되지 않음 → Tied/접촉 재확인 필요 (`KooTetraRemesher.py:355-356`).
- **실행 순서 권장**: README.txt 기준 `REMESH_TETRA → DROP_ATTITUDE → robust_contact`. `PreserveSharedNodes=False`일 때 Tied 접촉 재매핑 필요. (확인 필요: 순서 강제 로직은 코드에서 확인되지 않음, 운영 가이드 성격.)

## 6. 개발 현황

**구현됨 (부분 — gmsh 외부 의존)**

근거:
- 모드 등록·파싱·디스패치 경로 모두 존재: `KooMeshModifier.py:255-257`, `1831-1869`, `2552-2554`, `2801-2803`.
- 실제 로직 전체 구현: `KooTetraRemesher.py:49-615` (분석/L_min/공유노드/STL/gmsh/교체/검증, 5단계 완비).
- 동작하는 예제 존재: `Examples/remesh_tetra/step_config.txt`, `README.txt`.

"부분"으로 표기한 이유: 외부 gmsh 바이너리 설치/경로에 의존하며, scenario.json `remesh_tetra` → step_config 매핑(KooChainRun 연동) 코드 경로는 본 조사에서 직접 확인하지 못함(확인 필요). 핵심 메시 변환 기능 자체는 완전 구현 상태이다.
