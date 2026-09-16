# KooRemapper ops — 솔버 설정(explicit · implicit · modal · ale · optimize)

LS-DYNA `.k` 모델의 솔버 설정을 변환·복원하는 KooRemapper의 다섯 가지 yaml-config op(explicit 복원 · implicit 변환 · modal 해석 · ALE 변환 · 재료 최적화)에 대한 레퍼런스다.

## 실행 형태 (공통)

KooRemapper는 `SmartTwinPreprocessor.sif` 안의 C++ CLI `/opt/kooremapper/bin/KooRemapper`(v1.8.0)다. 두 가지로 호출한다.

- 컨테이너 직접 실행. `apptainer exec <sif> /opt/kooremapper/bin/KooRemapper <op> <config.yaml>`
- KooChainRun의 `REMAP` 스텝. 아래 각 op의 "REMAP 스텝" 줄 참조.

다섯 op 모두 **yaml-config op**이라 `config.yaml`(독립 실행) 또는 REMAP 스텝의 `params.config`(dict)로 인자를 준다. REMAP 스텝에서는 `params.op=<op>` 와 `params.config`(dict)를 지정하며, `model`/`output` 은 러너가 자동 주입하므로 config dict에서 생략한다. (README §호출 규약)

---

## explicit

### 용도

모델에서 DR + Implicit + Modal 관련 키워드를 모두 제거해 순수 Explicit 설정으로 복원한다. implicit/modal/relax 변환이 삽입한 제어 카드를 한 번에 정리하는 역변환이다. (정본 §32, help)

### 호출형태

```
KooRemapper explicit <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper explicit config.yaml
```

REMAP 스텝. `params.op=explicit`, `params.config={"keep_dr_curves": false}`.

### config 인자

| 키 | 타입 | 기본 | 설명 |
|---|---|---|---|
| `model` | str | (러너 자동 주입) | 입력 K 파일 |
| `output` | str | (러너 자동 주입) | 출력 K 파일 |
| `keep_dr_curves` | bool | `false` | `true`면 SIDR=1 DEFINE_CURVE 유지, 기본은 제거 (help) |

### 제거 대상 (정본 §32)

`*CONTROL_DYNAMIC_RELAXATION`, `*DATABASE_BINARY_D3DRLF`(relax 계열), `*CONTROL_IMPLICIT_GENERAL/DYNAMICS/SOLUTION/AUTO/STABILIZATION/SOLVER`(implicit 계열), `*CONTROL_IMPLICIT_EIGENVALUE/MODAL_DYNAMIC/ROTATIONAL_DYNAMICS/INERTIA_RELIEF`(modal 계열), `*DEFINE_CURVE`(SIDR=1, `keep_dr_curves=false`일 때).

### 예제

```yaml
model: implicit_model.k
output: explicit_model.k
keep_dr_curves: false
```

(정본 §32)

### 동작 원리

세 계열(DR·implicit·modal)의 제어 카드를 일괄 제거한다. 개별 op의 `strip: true`가 자기 계열 키워드만 지우는 것과 달리, explicit는 세 계열을 통째로 정리해 explicit 상태로 되돌린다. (help)

### 주의사항

- explicit op 자체엔 level 파라미터가 없다. `model`/`output`/`keep_dr_curves`만 받는다. (help)
- `examples/explicit/level01.yaml`~`level12.yaml`는 이 explicit 복원 op이 아니라 별도 op인 **`stabilize`**(파일 내용이 `stabilize: explicit` + `level: 1~12`, 호출은 `KooRemapper stabilize levelNN.yaml`)용 예제다. explicit 복원 op과 혼동에 주의한다. **확인 필요**: explicit 복원 op에 별도 프리셋/level 체계가 있다는 근거는 없다. (examples/explicit/level01.yaml, examples/explicit/level12.yaml)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).

---

## implicit

### 용도

Explicit LS-DYNA K 파일을 Implicit 해석 설정으로 변환한다. explicit 전용 카드를 제거하고 `*CONTROL_IMPLICIT_*` 블록을 삽입한다. (정본 §29, help)

### 호출형태

```
KooRemapper implicit <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper implicit config.yaml
```

REMAP 스텝. `params.op=implicit`, `params.config={"mode": "static", "level": 2, "endtime": 1.0}`.

### config 인자

| 키 | 타입 | 기본 | 설명 |
|---|---|---|---|
| `model` / `output` | str | (러너 자동 주입) | 입출력 K 파일 |
| `mode` | str | `static` | `static`(IMASS=0, 준정적) \| `dynamic`(IMASS=1, 구조동역학) |
| `level` | int | `2` | 1(공격적)~8(좌굴/스냅스루) 프리셋 |
| `endtime` | float | — | `*CONTROL_TERMINATION` + DT 기준값 갱신 |
| `strip` | bool | `false` | `true`면 `*CONTROL_IMPLICIT_*` 제거만(삽입 없음) |

세부 오버라이드(생략 시 level 기본값 사용). `dctol`, `ectol`, `dt0`, `dtmax`, `nsolvr`(12=BFGS, -2=BFGS+line search), `kfail`, `rctol`, `lsolvr`(7=sparse, 30=MUMPS), `stab`, `stab_scale`, `arc_length`, `fix_shell_elform`, `keep_dr_curves`. (help)

### level 프리셋

lv1~lv8. `examples/implicit/level1.yaml`~`level8.yaml`(static) 및 `dynamic_lv1.yaml`~`dynamic_lv8.yaml`(dynamic)이 각 단계의 대표 설정을 담는다. 요약 (help Table 1/2, 정본 §29).

| Lv | 이름 | 특징 |
|----|------|------|
| 1 | 공격적 | 빠른 수렴 시도, NSOLVR=12, 느슨한 허용치 |
| 2 | 표준 | 기본값 |
| 3 | 안정 | ILIMIT/MAXREF 증가 |
| 4 | 수렴우선 | NSOLVR=-2(line search), KFAIL 시작 |
| 5 | 강건 | +STABILIZATION(IAS=1) |
| 6 | 고강건 | +MUMPS 솔버(LSOLVR=30), RCTOL 활성 |
| 7 | 최대안정 | 최소 허용치 |
| 8 | 좌굴/스냅스루 | +Arc-length(Crisfield), NSOLVR=7 |

> help의 파라미터 주석은 범위를 "1~7"로 적지만, help/정본의 Table과 예제 파일(`level8.yaml`, `dynamic_lv8.yaml`)은 level 8까지 존재한다. 8단계 기준으로 문서화한다.

mode 별 Newmark 계수 (help, 정본 §29).

| 파라미터 | static | dynamic |
|----------|--------|---------|
| IMASS | 0 | 1 |
| GAMMA | 0.5 | 0.6 |
| BETA | 0.25 | 0.30 |

### 예제

```yaml
model: explicit.k
output: implicit.k
mode: static
level: 2
endtime: 1.0
```

(examples/implicit/implicit_minimal.yaml)

### 동작 원리

항상 제거. `*CONTROL_DYNAMIC_RELAXATION`, `*CONTROL_BULK_VISCOSITY`, `*DATABASE_BINARY_D3DRLF`, `*DEFINE_CURVE`(SIDR=1, `keep_dr_curves=false`). 항상 삽입. `*CONTROL_IMPLICIT_GENERAL/DYNAMICS/SOLUTION/AUTO`. level 5+ 에서 `*CONTROL_IMPLICIT_STABILIZATION`, level 6+ 에서 `*CONTROL_IMPLICIT_SOLVER`(MUMPS), level 8 또는 `arc_length: true`에서 `*CONTROL_IMPLICIT_SOLUTION` Card 3(arc-length)을 추가한다. (help, 정본 §29)

### 주의사항

- 세부 오버라이드 키를 주면 해당 level 기본값을 덮어쓴다. (help)
- `arc_length`는 NSOLVR이 6~9 범위여야 하며 필요 시 자동으로 7로 맞춘다. (help)
- `strip: true`는 level/mode 검증을 건너뛴다. (정본 §29)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage + examples/implicit 확인).

---

## modal

### 용도

LS-DYNA 모델을 모달(고유진동수/고유모드) 해석 설정으로 변환한다. explicit 전용 카드를 제거하고 `*CONTROL_IMPLICIT_EIGENVALUE`를 삽입한다. (정본 §30, help)

### 호출형태

```
KooRemapper modal <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper modal config.yaml
```

REMAP 스텝. `params.op=modal`, `params.config={"nmode": 10, "fmax": 2000.0}`.

### config 인자

| 키 | 타입 | 기본 | 설명 |
|---|---|---|---|
| `model` / `output` | str | (러너 자동 주입) | 입출력 K 파일 |
| `nmode` | int | `10` | 추출 모드 수 |
| `fmin` | float | `0.0` | 하한 주파수 Hz(0=하한 없음, LFLAG=0) |
| `fmax` | float | `0.0` | 상한 주파수 Hz(0=상한 없음, RFLAG=0) |
| `center` | float | `0.0` | 중심 주파수 shift Hz |
| `eigmth` | int | `2` | 고유치 방법(아래 표) |
| `solver` | int | `7` | 선형 솔버(7=sparse, 30=MUMPS) |
| `fix_shell_elform` | bool | `false` | `true`면 ELFORM=16→2 자동 수정, 기본은 경고만 |
| `keep_dr_curves` | bool | `false` | `true`면 SIDR=1 DEFINE_CURVE 유지 |
| `strip` | bool | `false` | `true`면 modal 키워드 제거만(삽입 없음) |

고유치 방법(`eigmth`). (help, 정본 §30)

| 값 | 방법 | 용도 |
|----|------|------|
| 2 | Block Shift Lanczos | 범용(기본) |
| 101 | MCMS | NVH, 수백~수천 모드 |
| 102 | LOBPCG | 대규모 모델, 반복법 |
| 103 | Fast Lanczos | MPP 병렬 |

### 예제

```yaml
model:  explicit.k
output: modal.k
nmode:  10
fmax:   2000.0
```

(examples/modal/modal_minimal.yaml)

NVH(대량 모드) 예. `nmode: 200`, `fmax: 5000.0`, `eigmth: 101`(MCMS), `solver: 30`(MUMPS). (examples/modal/modal_nvh.yaml)

### 동작 원리

삽입. `*CONTROL_IMPLICIT_GENERAL`(IMFLAG=1, DT0=1.0, IMFORM=2, IGS=2), `*CONTROL_IMPLICIT_EIGENVALUE`(NEIG, LFLAG/RFLAG, EIGMTH), `*CONTROL_IMPLICIT_SOLUTION`(NSOLVR=12, 표준 허용치), `*CONTROL_IMPLICIT_SOLVER`(`solver: 30`일 때만). `fmin>0`이면 LFLAG=1·LFTEND=fmin, `fmax>0`이면 RFLAG=1·RHTEND=fmax로 설정한다. (help, 정본 §30)

### 주의사항

- 결과는 DATABASE 카드 없이 자동 생성된다. `eigout`(ASCII 주파수 목록), `d3eigv`(바이너리 모드형상). (help)
- `strip: true`는 `*CONTROL_IMPLICIT_EIGENVALUE`/`_GENERAL`/`_SOLUTION`/`_SOLVER`만 제거한다. (정본 §30)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage + examples/modal 확인).

---

## ale

### 용도

지정한 solid 파트를 ALE(Arbitrary Lagrangian-Eulerian)로 변환한다. 14종 재료 프리셋과 커스텀 번들 파일을 지원한다. ELFORM 변경과 함께 `*CONTROL_ALE`, AMMG, 재료 카드, FSI 커플링을 삽입한다. (정본 §35, help)

### 호출형태

```
KooRemapper ale <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper ale config.yaml
```

REMAP 스텝. `params.op=ale`, `params.config={"ale_parts": [...], "fsi_pids": [...]}`.

### config 인자 (help·examples 권위)

| 키 | 타입 | 기본 | 설명 |
|---|---|---|---|
| `model` / `output` | str | (러너 자동 주입) | 입출력 K 파일 |
| `ale_parts` | 리스트 | (필수) | 변환 대상 파트. 각 항목 `{pid, material}` |
| `ale_parts[].pid` | int | (필수) | 대상 파트 ID |
| `ale_parts[].material` | str | (필수) | 프리셋 이름 또는 커스텀 `.k` 번들 경로 |
| `fsi_pids` | 리스트 | (옵션) | FSI 커플링용 라그랑지안 파트 |
| `elform` | int | `11` | ALE ELFORM(11=multi-mat, 12=single) |
| `dct` | int | `1` | Advection 로직(1=기본, -1=개선) |
| `nadv` | int | `1` | Advection cycles |
| `meth` | int | `2` | Advection 방법(2=Van Leer) |
| `ctype` | int | `2` | FSI coupling type(2=accel+vel) |
| `pfac` | float | `0.1` | FSI penalty factor |
| `detonation` | dict | (옵션) | `{pid, x, y, z, lt}`, tnt/c4 프리셋용 기폭점 |

> **키 이름 주의**. 정본 §35 YAML 예시는 키를 `parts`/`preset`/`lagrangian_pids`로 적지만, 바이너리 help와 실제 예제 파일은 `ale_parts`/`material`/`fsi_pids`를 쓴다. help·examples 형식을 따른다. **확인 필요**(정본 §35 표기와 불일치). (help, examples/ale/*)

### 재료 프리셋 (14종)

| 분류 | 프리셋 | MAT | EOS |
|------|--------|-----|-----|
| 기체 | air, nitrogen, argon | MAT_NULL | EOS_LINEAR_POLYNOMIAL |
| 액체 | water, electrolyte, gasoline, oil, coolant, resin, tim, silicone | MAT_NULL | EOS_GRUNEISEN |
| 폭발물 | tnt, c4 | MAT_HIGH_EXPLOSIVE_BURN | EOS_JWL |
| 진공 | vacuum | MAT_VACUUM | — |

단위계는 t/mm/s → MPa 기준이다. (정본 §35, help)

### 예제

최소(단일 파트를 air로).

```yaml
model:  explicit.k
output: ale_minimal.k
ale_parts:
  - pid: 3
    material: air
```

(examples/ale/ale_minimal.yaml)

폭발(air + tnt + 기폭점). `ale_parts`에 air/tnt, `fsi_pids: [1, 2]`, `detonation: {pid: 5, x, y, z, lt}`. (examples/ale/ale_blast.yaml)
배터리(전해질 + 케이스 FSI). `ale_parts`에 `electrolyte`, `fsi_pids: [1, 2, 3]`, `dct: -1`(개선형 advection). (examples/ale/ale_battery.yaml)

### 동작 원리

자동 삽입. `*SECTION_SOLID`(ELFORM 변경 또는 공유 시 신규 section), 대상 파트별 `*MAT_*` + `*EOS_*` 교체, `*HOURGLASS`(IHQ=3), `*CONTROL_ALE`, `*ALE_MULTI-MATERIAL_GROUP`, `*ALE_REFERENCE_SYSTEM_GROUP`(PRTYPE=4, 메시 스무딩), `fsi_pids` 지정 시 `*CONSTRAINED_LAGRANGE_IN_SOLID`(FSI), 폭발물 프리셋에서 `*INITIAL_DETONATION`. (help, 정본 §35)

### 주의사항

- 프리셋 밀도/EOS 값은 t/mm/s → MPa 단위 기준이므로 모델 `.k` 단위계와 일치해야 한다. (help)
- `detonation`은 tnt/c4 폭발물 프리셋에서만 유효하다. (help)
- YAML 키 이름은 help/examples 형식(`ale_parts`/`material`/`fsi_pids`)을 사용한다(위 키 이름 주의 참조). **확인 필요**.

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage + examples/ale 확인).

---

## optimize

### 용도

특정 재료(현재 rubber만 지원)에 최적화된 LS-DYNA 컨트롤 카드를 자동 적용한다. 독립 실행하거나 matswap YAML 안에서 함께 쓸 수 있다. (정본 §34, help)

### 호출형태

```
KooRemapper optimize <config.yaml>
```

컨테이너 실행 예.

```
apptainer exec <sif> /opt/kooremapper/bin/KooRemapper optimize config.yaml
```

REMAP 스텝. `params.op=optimize`, `params.config={"optimize": "rubber", "pids": [2, 5, 8], "tssfac": 0.67}`.

### config 인자

독립형.

| 키 | 타입 | 기본 | 설명 |
|---|---|---|---|
| `model` / `output` | str | (러너 자동 주입) | 입출력 K 파일 |
| `optimize` | str | (필수) | 최적화 모드(현재 `rubber`만 지원) |
| `pids` | 리스트 | — | 최적화 대상 파트 ID(접촉 스코프) |
| `tssfac` | float | `0.67` | TSSFAC 설정값 |
| `analysis_type` | str | `""` | `"explicit"` \| `"implicit"` \| `""`(자동 감지) (정본 §34) |

matswap 통합형. `swaps`(리스트, 각 항목 `{bundle, pid}`) + `optimize: rubber` + `tssfac`. optimize는 matswap 이후에 적용된다. (help, 정본 §34)

### rubber 모드 동작

공통(explicit + implicit). `*CONTROL_ACCURACY` INN=4, `*CONTROL_ENERGY` HGEN/RWEN/SLNTEN/RYLEN=2, 대상 PID의 `*CONTACT_*` SOFT=0·SBOPT=2(강제 수정 + 알림).
explicit 전용. `*CONTROL_TIMESTEP` TSSFAC=0.67(강제), DT2MS≠0이면 경고, `*CONTROL_BULK_VISCOSITY` Q1/Q2가 비표준이면 경고. (help, 정본 §34)

### 예제

독립형.

```yaml
model: my_model.k
output: my_model_optimized.k
optimize: rubber
pids: [2, 5, 8]
tssfac: 0.67
analysis_type: ""
```

matswap 통합형.

```yaml
model: base_model.k
output: swapped_model.k
swaps:
  - bundle: rubber.k
    pid: 3
optimize: rubber
```

(정본 §34)

### 동작 원리 / 멱등성

이미 올바른 값은 수정하지 않는다. 같은 모델에 두 번 실행해도 결과가 동일하다. (정본 §34)

### 주의사항

- 현재 `rubber` 모드만 지원한다. (정본 §34, help)
- DT2MS≠0, 비표준 Q1/Q2는 수정하지 않고 경고만 낸다. (help)

### 개발 현황

v1.8.0 바이너리에 구현됨(help Usage 확인).
