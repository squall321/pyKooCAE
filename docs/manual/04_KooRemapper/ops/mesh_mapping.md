# KooRemapper ops — 메시 매핑(map · shellmap · unfold)

굽힘(bent)/평면(flat) 메시 사이를 오가는 KooRemapper의 세 가지 positional op에 대한 레퍼런스다.

## 실행 형태 (공통)

KooRemapper는 `SmartTwinPreprocessor.sif` 안의 C++ CLI `/opt/kooremapper/bin/KooRemapper`(v1.8.0)다. 두 가지 방법으로 호출한다.

- 컨테이너 직접 실행: `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> ...`
- KooChainRun의 `REMAP` 스텝: 아래 각 op의 "REMAP 스텝" 줄 참조.
- YAML 설정의 BOM·탭·상대 경로 공통 규칙과 새로 거절되는 열거값은 [README §YAML 설정 공통 규칙](../README.md#yaml-설정-공통-규칙) 참조.

세 op 모두 **positional op**이므로, REMAP 스텝에서는 `params.op=<op>` 와 순서를 지킨 `params.argv`(리스트)로 인자를 전달한다.

---

## map

### 용도

평면(flat) 비구조 상세 메시를 굽힘(bent) **구조화 HEX8** 참조 메시에 등매개변수(isoparametric) 방법으로 매핑한다. 참조 메시는 반드시 구조화 HEX8이어야 하고, 상세 메시는 임의 형상이어도 무방하다. (정본 §4, help)

### 호출형태

```
KooRemapper map [--single] <bent_mesh> <flat_mesh> <output>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper map [--single] <bent_mesh> <flat_mesh> <output>
```

REMAP 스텝: `params.op=map`, `params.argv=["<bent_mesh>", "<flat_mesh>", "<output>"]`(단일 스레드가 필요하면 맨 앞에 `"--single"` 추가).

### 인자

| 인자 / 옵션 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `bent_mesh` | positional 1 | 예 | 굽힘 구조화 참조 메시(k-file) |
| `flat_mesh` | positional 2 | 예 | 매핑 대상 평면 메시(k-file) |
| `output` | positional 3 | 예 | 매핑 결과 출력 파일 경로 |
| `--single`, `-s` | 옵션 | 아니오 | 단일 스레드 모드. 기본은 병렬(OpenMP) |

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper map t_bent.k t_flat.k mapped.k
```

### 동작 원리

각 상세 메시 노드 p에 대해 (1) 참조 메시에서 포함 요소 검색, (2) 자연 좌표 (ξ, η, ζ)를 Newton-Raphson으로 역계산, (3) 같은 자연 좌표를 굽힘 참조 형상에 적용해 위치를 변환한다. HEX8 형상 함수를 사용한다. (정본 §4)

### 주의사항

- 참조 메시는 반드시 규칙적 HEX8 구조여야 한다. (정본 §4)
- 상세 메시 노드가 참조 요소 외부에 있으면 경고를 출력한다. (정본 §4)
- 기본은 병렬 처리다. OpenMP를 못 쓰거나 디버깅할 때 `--single`을 쓴다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## shellmap

### 용도

굽힘 **QUAD4 셸** 참조 형상을 기준으로 평면 상세 메시(고체 또는 셸)를 굽힘 형상으로 매핑한다. `map`이 구조화 HEX8 참조를 요구하는 것과 달리, `shellmap`은 비구조 QUAD4 셸을 참조로 쓴다. 셸을 평면으로 전개(edge-length preserving)한 뒤 평면 상세 노드를 굽힘 셸 표면에 매핑한다. (정본 §5, help)

### 호출형태

```
KooRemapper shellmap [options] <bent_shell> <flat_detail> <output>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper shellmap [--thickness <t>] <bent_shell> <flat_detail> <output>
```

REMAP 스텝: `params.op=shellmap`, `params.argv=["<bent_shell>", "<flat_detail>", "<output>"]`(두께 지정 시 맨 앞에 `"--thickness", "<t>"` 추가).

### 인자

| 인자 / 옵션 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `bent_shell` | positional 1 | 예 | 굽힘 셸 참조 메시(QUAD4, k-file) |
| `flat_detail` | positional 2 | 예 | 매핑 대상 평면 상세 메시(고체 또는 셸, k-file) |
| `output` | positional 3 | 예 | 매핑 결과 출력 파일 경로 |
| `--thickness <t>` | 옵션 | 아니오 | Z-오프셋 매핑용 셸 두께. 기본은 평면 메시 Z-범위 자동 감지 |

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper shellmap --thickness 2.0 bent_shell.k flat_detail.k mapped.k
```

### 동작 원리

(1) 셸 참조 메시로부터 법선 벡터 n̂을 계산하고, (2) 평면 노드의 면내 위치 (u, v)를 셸 면에 투영한 뒤, (3) 두께 방향 위치 z를 셸 면에서 ±t/2 범위로 매핑한다. (정본 §5) help 기준으로는 셸을 평면으로 전개(edge-length preserving)한 다음 평면 상세 노드를 굽힘 셸 표면에 매핑한다.

### 주의사항

- 가전개(developable, 단일 곡률 예: 실린더) 면에 최적화되어 있다. 비가전개 면에서는 왜곡 경고를 출력한다. (정본 §5, help)
- QUAD4 전용이며 TRIA3은 미지원이다. (정본 §5)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## unfold

### 용도

굽힘 구조화 HEX8 메시로부터 평면(flat) 전개 메시를 생성한다. `map`의 역방향 연산으로, 굽힘 구조화 메시의 호 길이(arc-length) 매개변수화를 사용해 평면 형상을 복원한다. 생성된 평면 메시는 상세 평면 메시를 다시 굽힘 형상으로 매핑할 때의 참조로 쓸 수 있다. (정본 §9, help)

### 호출형태

```
KooRemapper unfold <bent_mesh> <output_flat>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper unfold <bent_mesh> <output_flat>
```

REMAP 스텝: `params.op=unfold`, `params.argv=["<bent_mesh>", "<output_flat>"]`.

### 인자

| 인자 | 위치 | 필수 | 설명 |
|---|---|---|---|
| `bent_mesh` | positional 1 | 예 | 굽힘 구조화 HEX8 메시(k-file, 입력) |
| `output_flat` | positional 2 | 예 | 전개된 평면 메시(출력 경로) |

### 예제

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper unfold t_bent.k flat_ref.k
```

### 동작 원리

(1) 입력 메시의 구조화 격자 차원 (I, J, K)을 자동 감지하고(정본 §9), (2) 중심선(centerline)을 따라 호 길이를 계산해 X 차원을 만들며, (3) Y·Z(단면) 크기는 보존한다. (help) 콘솔에는 격자 차원 (I, J, K)과 평면 길이(I=호 길이, J, K)를 출력한다. (정본 §9)

### 주의사항

- 입력 메시는 반드시 규칙적 HEX8 구조화 메시여야 하며, 비구조 메시에는 사용할 수 없다. (정본 §9)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).
