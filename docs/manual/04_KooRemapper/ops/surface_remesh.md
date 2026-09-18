# KooRemapper ops — 표면·재메시(extract-surface · tetremesh · meshfix · cnrb2solid · merge · strip)

솔리드에서 셸 표면을 뽑고, TET4를 재메시하고, CNRB를 솔리드로 바꾸고, 적층을 병합하고, 키워드를 제거하는 KooRemapper의 여섯 op에 대한 레퍼런스다.

> 이 중 extract-surface·tetremesh·meshfix·merge·strip 5개는 `KooRemapper --help` 최상위 목록에 보이지 않는 숨은(hidden) op이고, cnrb2solid는 최상위 목록에 정식으로 등재된 명령이다. hidden op 5개는 op 이름만 주고 실행하면 고유한 Usage/YAML 스키마를 출력한다(help로 확인함).

## 실행 형태 (공통)

KooRemapper는 `SmartTwinPreprocessor.sif` 안의 C++ CLI `/opt/kooremapper/bin/KooRemapper`(v1.8.0)다. 두 가지 방법으로 호출한다.

- 컨테이너 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> ...`
- KooChainRun의 `REMAP` 스텝: 아래 각 op의 "REMAP 스텝" 줄 참조.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

호출 형태가 두 종류로 갈린다.

- **positional op** — `extract-surface` 하나뿐이다. REMAP 스텝에서 `params.op=extract-surface` 와 순서를 지킨 `params.argv`(리스트)로 인자를 전달한다.
- **yaml-config op** — `tetremesh`, `meshfix`, `cnrb2solid`, `merge`, `strip`. 모두 `KooRemapper <op> <config.yaml>` 한 개 인자를 받는다. REMAP 스텝에서는 `params.op=<op>` 와 config YAML 내용을 그대로 담은 `params.config`(dict)로 전달한다.

> Usage 줄에는 짧은 이름 `KooRemapper`로 표기되지만, 컨테이너 안 실제 바이너리 경로는 `/opt/kooremapper/bin/KooRemapper`다.

---

## extract-surface

### 용도

솔리드 K파일에서 표면 셸을 추출한다. (help Usage 기준. 정본 섹션·예제 없음)

### 호출형태

positional op다. help의 `Usage:` 줄과 정확히 일치한다.

```
KooRemapper extract-surface <solid.k> <output_shell.k> [--pid N] [--face top|bottom|all] [--output-pid N]
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper extract-surface <solid.k> <output_shell.k> [--pid N] [--face top|bottom|all] [--output-pid N]
```

REMAP 스텝: `params.op=extract-surface`, `params.argv=["<solid.k>", "<output_shell.k>"]`(옵션 사용 시 `"--pid", "N"`, `"--face", "all"`, `"--output-pid", "N"` 등을 뒤에 이어 붙인다).

### 인자

| 인자 / 옵션 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `solid.k` | positional 1 | 예 | 입력 솔리드 K파일 |
| `output_shell.k` | positional 2 | 예 | 출력 셸 K파일 경로 |
| `--pid N` | 옵션 | 아니오 | 대상 파트 ID(플래그명 기준. 정확한 동작 확인 필요) |
| `--face top\|bottom\|all` | 옵션 | 아니오 | 추출할 면 선택(top/bottom/all) |
| `--output-pid N` | 옵션 | 아니오 | 출력 셸에 부여할 파트 ID(플래그명 기준. 정확한 동작 확인 필요) |

> 옵션 인자의 세부 의미는 정본 섹션·예제가 없어 help의 플래그 이름으로만 표기했다. 정확한 기본값·동작은 확인 필요.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인). 정본 문서 섹션과 예제 YAML은 없다.

---

## tetremesh

### 용도

기존 TET4 파트를 품질 게이트(스케일드 자코비안·종횡비)로 스캔하고, 불량 요소 패치를 국소 재메시하여 요소 품질을 개선한다. 두 가지 백엔드(`localimprove`, `tetgen`)를 지원한다. (help)

### 호출형태

yaml-config op다. help의 `Usage:` 줄과 정확히 일치한다.

```
KooRemapper tetremesh <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper tetremesh config.yaml
```

REMAP 스텝: `params.op=tetremesh`, `params.config={config.yaml 내용을 dict로}`.

### 인자 (YAML 스키마, help)

| 키 | 기본값 | 설명 |
|---|---|---|
| `model` | (필수) | 입력 K파일 |
| `output` | (필수) | 출력 K파일 |
| `backend` | `localimprove` | 주 백엔드: `localimprove` \| `tetgen` |
| `fallback` | (없음) | 주 백엔드가 패치에서 실패할 때 쓸 백엔드(선택) |
| `report_only` | `false` | `true`면 스캔·보고만 하고 재메시하지 않음 |
| `target_pids` | `[]`(전체) | 대상 파트 ID 리스트. 비우면 전체 파트 |
| `quality.min_jacobian` | `0.2` | 스케일드 자코비안 하한(<0.1 매우 나쁨, 0.2~0.5 허용, >0.7 우수) |
| `quality.max_aspect_ratio` | `8.0` | 종횡비 상한 |
| `patch.ring_expand` | `2` | 불량 요소 주변 확장 링 수 |
| `patch.surface_flatness_deg` | `5.0` | 평면 판정 각도(deg) |
| `patch.surface_move_tolerance` | `0.0` | `>0`이면 평면 표면 접선 방향 이동 허용 |
| `patch.preserve_multi_material` | `true` | 다중 재료 경계 보존 |
| `improve.laplacian_iters` | `5` | (Phase A) Laplacian 스무딩 반복 |
| `improve.max_outer_iters` | `3` | (Phase A) 외부 반복 |
| `improve.allow_subdivide` | `true` | (Phase A) 세분화 허용 |
| `tetgen.quality_ratio` | `1.4` | (Phase B) TetGen `-q` 반경/에지 비 |
| `tetgen.min_dihedral_deg` | `10.0` | (Phase B) 최소 이면각(deg) |

### 예제

```yaml
model:   input.k
output:  output.k
backend: localimprove
target_pids: [1, 2, 3]
quality:
  min_jacobian:     0.2
  max_aspect_ratio: 8.0
```

### 동작 원리 (help)

- **백엔드 `localimprove`** — 스무딩 + 2-3 face-edge swap + 세분화. 외부 라이브러리가 없어 항상 사용 가능하다.
- **백엔드 `tetgen`** — `third_party/tetgen`을 통한 제약 들로네 사면체화. 빌드 플래그 `KOOREMAPPER_BUILD_TETGEN`이 ON이어야 한다(TetGen은 AGPL v3).

### 주의사항

- `tetgen` 백엔드는 해당 빌드 플래그가 켜진 바이너리에서만 동작한다. 없으면 `localimprove`만 쓸 수 있다. (help)
- `report_only: true`로 먼저 품질 스캔만 돌려 대상을 파악한 뒤 재메시하는 것이 안전하다. (help)
- **`model`·`output` 의 상대 경로는 이제 YAML 폴더 기준이다**(2026-09-18 실행 확인). `KooRemapper tetremesh cfg/tet.yaml` 은 `cfg/` 에서 읽고 `cfg/` 에 쓴다 — 예전에는 작업 폴더 기준이었다. `meshfix` 도 같다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage·YAML 스키마 확인). 정본 문서 섹션은 없고 근거는 help 스키마다.

---

## meshfix

### 용도

기존 TET4 파트를 Gmsh로 **완전 재메시**하여 요소 품질을 개선한다. STL 경계 추출 → Gmsh 실행 → MSH2 파싱 → 원본 K파일 스플라이스 파이프라인으로 동작한다. Gmsh 실행 파일이 `dist/gmsh/gmsh.exe`(또는 `dist/gmsh-<ver>/gmsh.exe`)에 있어야 한다. (정본 §40, help)

### 호출형태

yaml-config op다. help의 `Usage:` 줄과 정확히 일치한다.

```
KooRemapper meshfix <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper meshfix config.yaml
```

REMAP 스텝: `params.op=meshfix`, `params.config={config.yaml 내용을 dict로}`.

### 인자 (YAML 스키마, help)

| 키 | 기본값 | 설명 |
|---|---|---|
| `model` | (필수) | 입력 K파일 |
| `output` | (필수) | 출력 K파일 |
| `pid` | (필수) | 재메시할 파트 ID(TET4) |
| `lc_target` | `1.0` | 목표 평균 요소 크기 |
| `lc_min` | auto | 최소 요소 크기(또는 `min_dt`에서 자동) |
| `lc_max` | `lc_target*2` | 최대 요소 크기 |
| `min_dt` | — | LS-DYNA explicit dt 하한(초). `lc_min` 대체용 |
| `density` / `E` / `nu` | — | `min_dt` 기반 `lc_min` 계산용 재료값(t/mm³, MPa, -) |
| `min_layers_thin` | `2` | 얇은 방향 최소 요소 레이어 수 |
| `adaptive` | `false` | bbox 코너 어트랙터 사이즈 필드(help는 false를 안전 기본값으로 명시) |
| `attractor_ratio` | `0.4` | 에지 < `lc_target*ratio`이면 어트랙터로 처리 |
| `decay_factor` | `8.0` | 사이즈 램프 거리 = `lc_min*factor` |
| `boundary_nodes` | `free` | 경계 노드 처리: `free` \| `fixed` \| `snap` |
| `snap_tolerance` | `0.001` | snap 모드 탐색 반경 |
| `algorithm` | `hxt` | Gmsh 3D 메셔: `hxt` \| `frontal3d` \| `del3d` |
| `optimize_netgen` | `true` | Gmsh 내장 Netgen 최적화 |
| `warn_min_jac` | `0.15` | 이 값 미만 요소에 경고 |
| `refine_surface` | `0`(off) | 경계 STL feature-edge(이면각 > 40°) conforming 세분화 레벨(1~3) |
| `polish` | `false` | (실험적) 나쁜 요소 국소 재메시 |
| `polish_jac` | `0.10` | polish 대상 임계값(J < 값) |
| `polish_max_iter` | `2` | polish 최대 반복 |

> 정본 §40의 옵션 요약표(표 40-1)는 일부 기본값이 help와 다르다(예: `adaptive`가 §40은 true, help는 false / §40은 `refine_surface: auto`, `optimize_passes: 3`을 추가로 기술). 위 표는 v1.8.0 바이너리 help 스키마를 기준으로 했고, 세부 파이프라인은 정본 §40을 참고하라.

### 예제

정본 §40 실행 예시.

```yaml
model:      examples/arc30/arc30_flat_tet.k
output:     output/remeshed.k
pid:        1
lc_target:  5.0
adaptive:   true
warn_min_jac: 0.15
```

### 동작 원리 (정본 §40)

K파일 로드 → TET4 추출 → 메시 분석(`lc_min/max` 자동 계산, geomThin 감지) → 경계 STL 추출 → STL 전처리(feature-edge 세분화·스무딩) → Gmsh `.geo` 생성(적응형 사이즈 필드) → Gmsh 실행(HXT: Mesh 2 → Mesh 3 → Netgen 최적화) → MSH2 파싱·스케일드 자코비안 품질 검사 → (polish) 국소 재메시 → K파일 스플라이스(다른 파트 보존).

**스케일드 자코비안** $J_s = 6\sqrt{2}\,V / L_{max}^3$ (정규 TET4에서 1.0). 판정 기준(정본 §40 표 40-3).

| 범위 | 판정 |
|---|---|
| $J_s \geq 0.5$ | 우수(LS-DYNA 권장) |
| $0.2 \leq J_s < 0.5$ | 양호 |
| $0.15 \leq J_s < 0.2$ | 주의(`warn_min_jac` 기준) |
| $0 < J_s < 0.15$ | 불량 |
| $J_s \leq 0$ | 역전(음의 체적, 해석 불가) |

### 주의사항 (정본 §40, help)

- **Gmsh 필수** — 탐색 순서는 (0) `$KOOREMAPPER_GMSH`(실행 파일 전체 경로) → (1) 바이너리 옆 `gmsh/gmsh(.exe)` → (2) 바이너리 옆 `gmsh-<ver>/[bin/]gmsh(.exe)` → (3) `PATH` → (4) `/opt/gmsh-*/bin/gmsh` 다. **작업 폴더의 `dist/gmsh/` 는 탐색 대상이 아니다**(2026-09-18 실행 확인 — 거기에 두기만 하면 `[ERROR] Gmsh not found — set KOOREMAPPER_GMSH, or place gmsh(.exe) in gmsh/ or gmsh-<ver>/[bin/] next to KooRemapper, …` 로 rc=1). SIF 안에서는 (1) 로 걸린다.
- **TET4 전용** — 입력 파트는 TET4(또는 퇴화 HEX8)여야 한다.
- **처리 시간** — 10만 요소 이상에서 수 분 걸릴 수 있다.
- **기하 한계** — 90° 직각 코너 인접 TET4는 기하 구속으로 이론적 최솟값($J_{s,min}^{corner} \approx 0.03{\sim}0.07$)이 있어, 기하 수정(코너 라운딩·필렛) 없이는 개선 불가하다.
- **polish 제한** — `polish: true`는 실험적 기능이며 90° 코너 구속 형상에서는 자동 스킵된다.
- **`model`·`output` 의 상대 경로는 이제 YAML 폴더 기준이다**(2026-09-18 실행 확인). `KooRemapper meshfix cfg/meshfix.yaml` 은 `cfg/` 에서 읽고 `cfg/` 에 쓴다 — 예전에는 작업 폴더 기준이었다.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage·YAML 스키마 확인). 정본 §40에 상세 문서 존재.

---

## cnrb2solid

### 용도

FE 모델의 `*CONSTRAINED_NODAL_RIGID_BODY`(CNRB, 강체 볼트 구속)를 O-grid(butterfly) 토폴로지의 HEX8 솔리드 실린더로 변환하고, 원본 노드와 신규 솔리드 사이에 `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET`를 생성한다. 명시적 동역학(낙하·충격)에서 실제 볼트 변형 거동을 포착하기 위한 op다. 볼트 헤드(플랜지)도 자동 생성할 수 있다. (concept 문서)

### 호출형태

yaml-config op다. 바이너리에 `--help`를 주면 버전 배너(v1.8.0)만 찍고 인자를 config 경로로 여겨 `Cannot open: --help`를 낸다. 즉 config 파일 하나를 받는다(concept 문서 §3.1, examples/cnrb2solid).

```
KooRemapper cnrb2solid <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper cnrb2solid basic.yaml
```

REMAP 스텝: `params.op=cnrb2solid`, `params.config={config.yaml 내용을 dict로}`.

### 인자 (examples/cnrb2solid, concept 문서)

실제 예제(`examples/cnrb2solid/basic.yaml`, `with_head.yaml`)는 모든 키를 최상위(flat)에 둔다.

| 키 | 기본값 | 설명 |
|---|---|---|
| `model` | (필수) | 입력 K파일 |
| `output` | (필수) | 출력 K파일 |
| `E` | (필수) | 탄성계수 [MPa] |
| `PR` | (필수) | 포아송비 |
| `RHO` | (필수) | 밀도 [t/mm³] |
| `radius_scale` | `0.999` | 링 노드 반경 = 볼트홀 R × scale(살짝 안쪽) |
| `num_circum_nodes` | `0`(자동) | 원주 노드 수(4의 배수), 0이면 자동 감지 |
| `inner_radius_ratio` | `0.3` | 코어 사각형 반변 / R 비율 |
| `axis_direction` | `auto` | 실린더 축: `auto` \| `x` \| `y` \| `z`(PCA 자동 감지) |
| `z_tolerance` | `0.1` | Z-레벨 그룹핑 허용오차 [mm] |
| `r_tolerance` | `0.5` | 다중 반경 클러스터링 허용오차 [mm](스텝 볼트용) |
| `head_offset_r` | `0.0` | 헤드 반경 오프셋(R_head = R_shaft + 값 [mm]). 0이면 헤드 미생성 |
| `head_thickness` | `2.0` | 볼트 헤드 축방향 두께 [mm] |
| `head_position` | `auto` | 헤드 위치: `auto`(큰 R 쪽/또는 Z_max) \| `top` \| `bottom` \| `none` |
| `target` | `all` | 변환 대상: `all` \| PID 리스트(concept 문서 §3.1) |

> concept 문서 §3.1은 이들을 `cnrb2solid:` 하위 블록으로 감싼 형태(및 `target` 키)를 함께 제시하나, 실제 배포 예제(examples/)는 위처럼 최상위 flat 형태를 쓴다. 검증된 config 모양은 예제 쪽이다.

### 예제

`examples/cnrb2solid/basic.yaml`(헤드 없음).

```yaml
model: bolt_simple.k
output: bolt_simple_solid.k
E: 200000.0
PR: 0.3
RHO: 7.85e-9
radius_scale: 0.999
num_circum_nodes: 8
inner_radius_ratio: 0.3
axis_direction: auto
z_tolerance: 0.1
r_tolerance: 0.5
```

헤드를 붙이려면 `head_offset_r`, `head_thickness`, `head_position`을 추가한다(`examples/cnrb2solid/with_head.yaml`).

### 동작 원리 (concept 문서)

PCA로 CNRB 노드 공분산 행렬을 고유값 분해해 실린더 축을 감지하고, 원통좌표 변환·Z-레벨 그룹핑·R-값 클러스터링 후, R_max 기준으로 O-grid 단면(코어 정사각 격자 + 외곽 원형 링)을 만들고 Z-레벨별 로컬 R로 요소를 필터링한다. LS-DYNA 노드 순서로 HEX8을 생성하고, 원본 노드 ↔ 신규 솔리드 파트 간 Tied Contact를 만든 뒤 CNRB와 중심노드(PNODE)를 제거한다. 헤드는 헤드 Z-레벨을 추가하고 R_local 맵에 R_head를 등록하면 기존 필터링 로직이 그대로 처리한다.

### 주의사항 (concept 문서)

- CNRB가 없는 모델은 경고 후 원본을 그대로 출력한다.
- PNODE가 없는 CNRB(PNODE=0)는 노드셋 중심점을 사용한다.
- 노드가 4개 미만이면 O-grid를 만들 수 없어 에러를 낸다.
- 재료값(E/PR/RHO)은 변환 없이 그대로 쓰이므로 모델 K파일 단위계(예제는 t-mm-s)와 반드시 일치시켜야 한다.

### 개발 현황

v1.8.0 바이너리에 구현됨(op 실행·예제 제공 확인). 정본 문서 섹션은 없고 근거는 concept 문서(`docs/cnrb2solid_concept.md`)와 예제 YAML이다.

---

## merge

### 용도

적층(stack)된 여러 파트(PID)를 하나의 균질화(homogenized) 재료 레이어로 병합한다. 예제는 Steel + Polymer + Aluminum 3층을 Voigt-Reuss-Hill 평균으로 단일 레이어로 합친다. (examples/merge)

### 호출형태

yaml-config op다. help의 `Usage:` 줄과 정확히 일치한다.

```
KooRemapper merge <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper merge merge_test.yaml
```

REMAP 스텝: `params.op=merge`, `params.config={config.yaml 내용을 dict로}`.

### 인자 (examples/merge/merge_test.yaml)

| 키 | 예제값 | 설명 |
|---|---|---|
| `model` | `three_layer.k` | 입력 K파일 |
| `output` | `merged_output.k` | 출력 K파일 |
| `direction` | `z` | 적층 방향 |
| `method` | `vrh` | 균질화 방법: `voigt` \| `reuss` \| `vrh`(Voigt-Reuss-Hill 평균) |
| `merge` | 리스트 | 병합 그룹 목록. 각 항목은 `pids`(합칠 PID 리스트)와 `name`(결과 파트 이름) |

> help는 `Usage: KooRemapper merge <config.yaml>` 한 줄만 출력한다. 정본 섹션이 없어 위 스키마는 예제 YAML 한 개에서 확인한 범위이며, `direction`의 다른 값이나 추가 키 여부는 확인 필요.

### 예제

`examples/merge/merge_test.yaml`.

```yaml
model: three_layer.k
output: merged_output.k
direction: z
method: vrh        # voigt / reuss / vrh (Voigt-Reuss-Hill average)
merge:
  - pids: [1, 2, 3]
    name: "Homogenized_Stack"
```

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인). 정본 섹션은 없고 근거는 예제 YAML(`examples/merge/`)이다.

---

## strip

### 용도

`keywords` 리스트로 지정한 LS-DYNA 키워드를 K파일에서 **제거**한다. 예제는 `*NODE`, `*ELEMENT_SOLID` 등 부피 큰 메시 데이터를 빼고 옵션·컨트롤 카드만 남긴다. (examples/strip)

### 호출형태

yaml-config op다. help의 `Usage:` 줄과 정확히 일치한다.

```
KooRemapper strip <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper strip strip_test.yaml
```

REMAP 스텝: `params.op=strip`, `params.config={config.yaml 내용을 dict로}`.

### 인자 (examples/strip/strip_test.yaml)

| 키 | 설명 |
|---|---|
| `model` | 입력 K파일 |
| `output` | 출력 K파일 |
| `keywords` | 제거할 키워드 문자열 리스트(예: `*NODE`, `*ELEMENT_SOLID`, `*ELEMENT_SHELL`, `*INITIAL_STRESS_SOLID`, `*INITIAL_STRESS_SHELL`) |

### 예제

`examples/strip/strip_test.yaml`.

```yaml
model: ../assemble_display/al_box.k
output: stripped_output.k
keywords:
  - "*NODE"
  - "*ELEMENT_SOLID"
  - "*ELEMENT_SHELL"
  - "*INITIAL_STRESS_SOLID"
  - "*INITIAL_STRESS_SHELL"
```

### 주의사항

- 이 standalone `strip` op은 `keywords`에 나열한 임의 키워드를 제거하는 op다. 정본 §38의 `strip: true`는 이와 별개로 `implicit`/`modal`/`relax`/`explicit` 명령에 붙여 해당 명령 소속 키워드만 제거하는 옵션이다(둘 다 "제거만 하고 새 키워드는 삽입하지 않는다"는 점은 같다). (정본 §38, examples/strip)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인). 근거는 예제 YAML(`examples/strip/`)이며, 정본 §38은 관련 `strip: true` 옵션을 다룬다.
