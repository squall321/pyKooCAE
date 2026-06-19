# KooChainRun 개발 현황

> 근거 파일(절대경로):
> - 본체: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/KooChainRun`
> - 후처리 sh 생성: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/PostprocessShellGenerator.py`
> - 설계기/실행기: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/CumulativeDesigner.py`, `Runner/CumulativeScenarioRunner.py`
> - VIBRATION 빌더: `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Runner/StepConfigBuilder.py`, `Runner/VibrationSource.py`
> - 버전: `KooChainRun` L9 / L56 = `1.4.0`

이 문서는 **KooChainRun(KCR) 및 `Runner/` 모듈의 개발 현황**을 다룬다.
커맨드별 사용법은 [README.md](README.md) 와 `commands/` 하위 문서를, 시나리오 입력 스키마는
[scenarios/scenario_reference.md](scenarios/scenario_reference.md) 를 참조한다. 본 문서는
**무엇이 최근 바뀌었고, 무엇이 구현/부분구현/계획 상태인지**에 집중한다.

---

## 1. 목적 / 개요

KooChainRun 코드베이스의 진행 상태를 **git log(KooChainRun/Runner 관련 최근 커밋)** 와
**코드 내 TODO/주석** 을 근거로 정리한다. 분류 기준:

- **구현됨**: 커맨드/기능이 코드에 정의되어 있고 실제 디스패치/호출 경로가 존재.
- **부분구현**: 진입점은 있으나 본체에 "not yet implemented"/"coming soon" 등 미완성 마커가 있거나
  특정 분기만 동작.
- **계획**: 코드에 `TODO`/주석 placeholder 로만 존재(진입로만 표시, 본체 미구현).

최근 개발 줄기는 크게 네 가지다(섹션 2 참조):
**VIBRATION 모드 통합**, **IMPACT 종합 리포트 배선(`auto_impact`)**, **d3plot cleanup 옵션**,
**후처리 인자 pass-through(`*_extra_args`)**.

---

## 2. 입력 옵션 · 인자 (최근 추가/변경분)

아래 표는 **최근 커밋으로 신설/변경된** 입력 키만 추린다. 전체 서브커맨드 인자는
[README.md §2](README.md) 표를 참조한다.

| 키 / 인자 | 위치 | 의미 | 기본값 | 근거(file:line) |
|---|---|---|---|---|
| `postprocess.auto_impact` | scenario `postprocess` 블록 | IMPACT 시나리오 submit 후 impact_report dependent job 자동 제출 | `True` | `KooChainRun` L852 |
| `postprocess.auto_sphere` | scenario `postprocess` 블록 | DROP 시나리오 submit 후 sphere_report dependent job 자동 제출 | `True` | `KooChainRun` L858 |
| `postprocess --impact` | `postprocess` 서브커맨드 | impact_report.sh 만 수동 실행(전위치 부분충격 IMPACT) | — | `KooChainRun` L315–L316 |
| `postprocess.deep_extra_args` | `postprocess` 블록 | `koo_deep_report` 명령 끝에 임의 인자 추가(override 가능) | `""` | `PostprocessShellGenerator.py` L86–L87, L37–L54 |
| `postprocess.sphere_extra_args` | `postprocess` 블록 | `koo_sphere_report` 끝에 인자 추가 | `""` | `PostprocessShellGenerator.py` L161–L162 |
| `postprocess.impact_extra_args` | `postprocess` 블록 | `koo_impact_report` 끝에 인자 추가 | `""` | `PostprocessShellGenerator.py` L262–L263 |
| `postprocess.delete_d3plot_after_deep` | `postprocess` 블록 | deep_report 성공(`set -e`) 후 `RUN_DIR` 의 d3plot/d3plot* 삭제(디스크 절약, report/ 보존) | `False` | `PostprocessShellGenerator.py` L93–L100 |
| `postprocess.impact_yield_stress` | `postprocess` 블록 | 있으면 impact_report 에 `--yield-stress` 부착, 없으면 per-part `*MAT` 사용 | `None` | `PostprocessShellGenerator.py` L257–L260 |
| `postprocess.impact_ncpu/_memory/_partition/_time_limit` | `postprocess` 블록 | impact dependent sbatch 자원(우선순위: postprocess > environment > default) | ncpu 8 / mem 16G / 04:00:00 | `PostprocessShellGenerator.py` L441–L444 |
| `vibration_source` | scenario | VIBRATION 모드 진동 케이스(DOE) 정의 (`source_type`: `explicit_factors`/`per_cap`/`circuit_group`) | — | `CumulativeDesigner.py` L446–L448; `VibrationSource.py` |
| `cumulative.mode_sequence: ["VIBRATION"]` | scenario | step mode 를 VIBRATION 으로 지정 | — | `CumulativeDesigner.py` L186–L201 |

> 참고: `auto_impact`/`auto_sphere` 는 `postprocess.enabled` 가 `True` 일 때만 평가된다
> (`KooChainRun` L838). `report_mode_from_runner_config` 가 DROP↔IMPACT 를 판정하여 둘 중
> 하나만 라우팅한다(`PostprocessShellGenerator.py` L300–L327).

---

## 3. 사용 예제 (실측 발췌)

### 3-1. IMPACT 종합 리포트 + d3plot cleanup (`postprocess` 블록)

`Examples/scenario_examples/impact_cylinder_8pi.json` L75–L82 (가공 없음):

```json
"postprocess": {
  "enabled": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "auto_deep": true,
  "auto_deep_mode": "inline",
  "delete_d3plot_after_deep": true,
  "auto_impact": true
}
```

`mode_sequence: ["IMPACT"]` 시나리오에서 submit 끝에 impact_report dependent job 이 자동
제출되고(`auto_impact: true`), 각 Run 의 deep_report 성공 후 d3plot 이 삭제된다
(`delete_d3plot_after_deep: true`). impact aggregate 는 `report/` 만 읽으므로 삭제 영향 없음
(`PostprocessShellGenerator.py` L90–L92 주석).

### 3-2. DROP 후처리 블록 (`auto_sphere`)

`Examples/postprocess_pipeline/scenario_with_postprocess.json` L30–L44 (가공 없음):

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "sif_path": "/opt/apptainers/SmartTwinPostprocessor.sif",
  "yield_stress_mpa": 350,
  "section_view_axes": ["z"],
  "section_view_fields": ["von_mises"],
  "section_view_mode": "section",
  "ua_threads": 8,
  "sv_threads": 8,
  "deep_timeout_seconds": 7200,
  "sphere_memory": "32G",
  "sphere_time_limit": "04:00:00"
}
```

### 3-3. VIBRATION 시나리오 (`vibration_source`)

`Examples/scenario_examples/vibration_example.json` L42–L65 (가공 없음, `circuit_group`):

```json
"vibration_source": {
  "source_type": "circuit_group",
  "direction": "Z",
  "load_type": "Force",
  "relative_mode": "Explicit",
  "base_curve": {
    "kind": "inline",
    "points": [[0, 0], [0.0005, 500], [0.001, 0]]
  },
  "circuit_group": {
    "circuits": {
      "C1_power": {"parts": [4, 5], "amplitude": 1.0},
      "C2_signal": {"parts": [9, 10], "amplitude": 0.5},
      "C3_motor": {"parts": [18], "amplitude": 2.0}
    }
  }
},
"cumulative": { "num_steps": 1, "mode_sequence": ["VIBRATION"] }
```

### 3-4. 후처리 인자 pass-through (`deep_extra_args`) — 코드 docstring 예시

`PostprocessShellGenerator.py` L23 / L69–L70 의 예시 형식:

```json
"deep_extra_args": ["--per-part-render", "--yield-stress", "350"]
```

값은 **JSON 리스트(권장)** 또는 공백 구분 문자열을 모두 받으며, 고정 플래그 **뒤**에 붙으므로
argparse "마지막 우선" 규칙으로 기본값을 override 한다(`PostprocessShellGenerator.py` L22, L85).

### 3-5. 수동 후처리 CLI

```bash
# scenario mode 에 맞는 종합 리포트 1개 + deep 전부 (무플래그 == --all)
KooChainRun postprocess /path/to/runner_config.json

# IMPACT 종합 리포트만 강제
KooChainRun postprocess /path/to/runner_config.json --impact
```

근거: `KooChainRun` L2561–L2571 (플래그→`do_deep/do_sphere/do_impact` 결정).

---

## 4. 동작 원리 (코드 근거)

### 4-1. IMPACT 리포트 배선 (`auto_impact`) — 커밋 7018730 (2026-06-16)

submit 4경로(large_scale/cumulative/part_validation/dwi)가 끝나면 공통으로
`_maybe_submit_sphere_after(rc, config_path)` 가 호출된다(`KooChainRun` L808, L813, L822).
이 함수는 `report_mode_from_runner_config` 로 **scenario mode 를 판정**한 뒤(L850),
`IMPACT` 면 `auto_impact` 를 검사하고 `build_impact_sbatch` 로,
`DROP` 면 `auto_sphere` 를 검사하고 `build_sphere_sbatch` 로 분기한다(L851–L862).
이전에는 `auto_sphere` 만 검사해 IMPACT 데이터에도 sphere(전각도 DROP 전용)가 돌던 버그가
있었다(L829–L830 주석). dependent job 은 `jobs.json` 의 모든 `job_id` 를 모아
`afterany` 로 묶어 제출한다(L880–L907).

판정 규칙(`PostprocessShellGenerator.py` L300–L327): `scenario.steps[].mode` 가
모두 IMPACT→`"IMPACT"`, 모두 DROP→`"DROP"`, 혼합→첫 step mode, 비어있으면
`doe_positions`(IMPACT) vs `doe_angles`(DROP) fallback, 그것도 없으면 `"DROP"`.

`prepare`(save_runner_config) 단계에서는 `postprocess` 블록이 있으면 sphere/impact 두 sh 가
**항상** 생성된다(수동 trigger 보장, `CumulativeDesigner.py` L871–L907).

### 4-2. d3plot cleanup — 커밋 8717f31 (2026-06-17)

`build_deep_report_sh` 가 `delete_d3plot_after_deep` 옵션을 받으면, 스크립트 끝에
`rm -f "$RUN_DIR"/d3plot "$RUN_DIR"/d3plot[0-9]*` cleanup_block 을 추가한다
(`PostprocessShellGenerator.py` L93–L100, L131). `set -e`(L105) 라서 `koo_deep_report` 가
성공해 이 줄에 도달했을 때만 삭제되고, 실패 시 d3plot 은 보존된다(L88–L92 주석).

### 4-3. 후처리 인자 pass-through (`*_extra_args`) — 커밋 8717f31

공용 헬퍼 `_extra_args_str(options, key)` 가 list/str 입력을 `shlex` 로 정규화하고 원소별
`shlex.quote` 로 감싼다(`PostprocessShellGenerator.py` L37–L54). 각 builder 가 고정 플래그
뒤에 `extra_line`(`" \\\n    {extra}"`)으로 붙인다:
deep L86–L87, sphere L161–L162, impact L262–L263. 값이 없으면 라인 자체를 생략해
dangling backslash 가 생기지 않는다.

### 4-4. VIBRATION 모드 — 커밋 8e91724 (2026-05-29) ~ 381ba31 (2026-06-03)

- **Designer**: `CumulativeDesigner._parse_scenario` 가 `mode_sequence` 에
  `VIB`/`VIBRATION` 이 있으면(`SimulationMode.VIB`/`VIBRATION` 둘 다, L192–L193)
  `_process_vibration_scenario` 로 분기한다(L200–L201). 이전엔 `VIB` 만 검사해 `"VIBRATION"`
  문자열이 DROP 경로로 새던 버그가 있었다(L187–L191 주석).
  진동 케이스는 `parse_vibration_source(cfg, ctx)` 로 파싱되어(L446–L448)
  `doe_vibrations` 테이블로 직렬화된다(L462 주석).
- **Runner**: `CumulativeScenarioRunner` 의 mode 분기에서 `build_vibration_load_config` 를 호출
  (`CumulativeScenarioRunner.py` L1329–L1400). 입력값 우선순위는
  `params(step) > doe_vibrations(DOE 카탈로그) > simulation_params.vibration`(L1360–L1367).
- **zero-hardcode registry**: 모드 키워드/옵션 키/직렬화는 `StepConfigBuilder` 의
  `_VIB_KEYWORDS`(L195), `_VIB_OPTION_KEYS`(L207), `_VIB_SERIALIZERS` 데코레이터
  registry(L215, L225)에서만 관리된다. 미등록 `relative_mode` 는 명시적 에러(L335–L336).
- **고정 출력 파일명**: VIBRATION 산출물은 `VibrationSet.k` 로 강제된다
  (`CumulativeScenarioRunner.py` L1655–L1656, `_find_input_file`). DROP(`DropSet.k`)/
  IMPACT(`DropWeightImpactTestSet.k`)/THERM(`ThermalSet.k`)과 동일 컨벤션(L1645–L1647).
- **정식 카드 fix**: 비정식 `*LOAD_BODY_PARTS_<dir>` 가 LS-DYNA input phase 에서 reject 되던
  문제를 `*LOAD_BODY_GENERALIZED_SET_PART` 로 교체(커밋 381ba31). 이 변경은
  `occProject/.../KooLoad.py` 측이며 KooChainRun/Runner 배선과 연동된다.

---

## 5. 주의사항 · 한계

- **d3plot 삭제는 복구 불가** — `delete_d3plot_after_deep: true` 는 운영 전 1~2잡으로 검증 권장
  (`Examples/scenario_examples/impact_cylinder_8pi.json` L74 경고). impact aggregate 는 deep
  output(`report/analysis_result.json` + `motion/`)만 읽으므로 d3plot 부재 시에도 동작해야
  하며, `koo_impact_report` 의 deep-output 재사용이 전제다(`PostprocessShellGenerator.py` L91–L92).
- **old-SIF soft-degrade** — `koo_impact_report` 미포함 구버전 SIF 면 impact_report.sh 가
  경고 후 `exit 0` 으로 skip 한다(`PostprocessShellGenerator.py` L282–L286). sphere 에는 이
  사전 검사가 없다(확인 필요: 의도적 비대칭인지).
- **혼합 mode_sequence 의 종합 리포트** — `report_mode_from_runner_config` 는 혼합 시퀀스에서
  **첫 step mode** 로만 라우팅한다(`PostprocessShellGenerator.py` L323). DROP+IMPACT 혼합
  케이스의 종합 리포트 정책은 단순화되어 있다.
- **VIBRATION 은 P1 범위(explicit_factors)만 본체 구현** — `per_cap`/`circuit_group` 도
  `vibration_source` 로 받지만, `relative_mode` 직렬화 측 `PerCap`/`CircuitGroup`/
  `VolumeProportional` serializer 는 아직 주석 placeholder 다
  (`StepConfigBuilder.py` L272–L280). Runner 분기에도 동일 TODO(`CumulativeScenarioRunner.py`
  L1340, L1383). 확인 필요: `circuit_group` 입력이 P1 serializer(`Explicit`)로 평탄화되어
  돌아가는지 vs 미지원으로 에러나는지(코드상 미등록 mode 는 L335–L336 에서 에러).
- **NFS 공유 경로 필수** — 모든 후처리 sbatch 는 compute node 에서 `output_dir` 를 다시 읽으므로
  `/data/...` 공유 경로 필요(`/tmp` 금지). 프로젝트 메모리 규칙 및 README §5 와 일치.

---

## 6. 개발 현황

| 항목 | 분류 | 근거 |
|---|---|---|
| IMPACT 종합 리포트 배선(`auto_impact`) + mode 라우팅 | **구현됨** | `KooChainRun` L808/L813/L822, L850–L862; 커밋 7018730 |
| impact_report.sh / sbatch 생성 | **구현됨** | `PostprocessShellGenerator.py` L231–L297, L425–L464; `CumulativeDesigner.py` L894–L907 |
| d3plot cleanup(`delete_d3plot_after_deep`) | **구현됨** | `PostprocessShellGenerator.py` L93–L100, L131; 커밋 8717f31 |
| 후처리 인자 pass-through(`deep/sphere/impact_extra_args`) | **구현됨** | `PostprocessShellGenerator.py` L37–L54, L86/L161/L262; 커밋 8717f31 |
| VIBRATION 모드 — explicit_factors(P1) | **구현됨** | `CumulativeDesigner.py` L200–L201, L446–L448; `CumulativeScenarioRunner.py` L1329–L1400; `StepConfigBuilder.py` L249 (`Explicit` serializer); 커밋 8e91724/381ba31 |
| VIBRATION `per_cap`/`circuit_group`/`VolumeProportional` 직렬화 | **계획** | `StepConfigBuilder.py` L272–L280 (주석 placeholder); `CumulativeScenarioRunner.py` L1340/L1383 `TODO(P2)`; `VibrationSource.py` L596–L602 `TODO(P3)` |
| `status` config 기반 상세 진행률 | **부분구현** | `KooChainRun` L2001–L2003 (`TODO`, "coming soon") |
| `collect` 기본/cumulative 결과 수집 | **부분구현** | `KooChainRun` L2051–L2052 ("not yet implemented") |
| THERM(고온 열응력) 모드 | **구현됨**(연동) | `_find_input_file` THERM 분기 `CumulativeScenarioRunner.py` L1653–L1654; `ThermalSet.k`; 커밋 177e332. 상세 본체는 occProject 측 |
| IMPACT 낙하속도/단위계 fix | **구현됨**(occProject 측) | 커밋 177e332/381ba31. KooChainRun/Runner 배선 외부(`occProject/Generators/...`)이므로 본 문서 범위 밖 — 상세는 02_KooMeshModifier 참조 |

**총평: 구현됨(일부 부분구현/계획).** 본 문서가 다룬 최근 4개 줄기(VIBRATION 통합 P1,
IMPACT report 배선, d3plot cleanup, extra_args pass-through)는 모두 코드에 실제 디스패치/호출
경로가 존재한다. VIBRATION 의 비-Explicit serializer 와 `status`/`collect` 일부 경로는
미완성 마커가 코드에 남아 있다.

> 미확인/확인 필요:
> - sphere_report.sh 에 impact 같은 old-SIF soft-degrade 가 없는 것이 의도적인지(§5).
> - `circuit_group`/`per_cap` 입력이 현재 P1 serializer 로 실제 평탄화되어 e2e 통과하는지
>   (예제 `vibration_example.json` 은 존재하나, serializer registry 에 해당 mode 가 미등록).
