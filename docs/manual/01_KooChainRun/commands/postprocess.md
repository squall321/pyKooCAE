# KooChainRun postprocess

## 1. 목적 / 개요

`KooChainRun postprocess` 는 KooD3plotReader 기반 후처리(post-processing)를 **수동으로 trigger** 하는 커맨드이다.

서브파서 정의상 help 는 "KooD3plotReader 후처리 수동 실행", description 은 "runner_config.json 기반 deep_report / sphere_report 수동 실행. auto 옵션 안 줬어도 prepare 시 생성된 sh를 trigger." 이다 (KooChainRun:303-308).

이 커맨드는 두 종류의 후처리 스크립트를 실행한다.

- **deep_report** : 시뮬레이션 케이스별 d3plot 후처리. 각 `output_dir/Run_*/deep_report.sh` 를 순차 실행한다 (KooChainRun:2584-2622).
- **종합 리포트** : 전 케이스 통합 리포트. 시나리오 mode 에 따라 분기한다 (KooChainRun:2557-2571).
  - **DROP** 시나리오 → `sphere_report.sh` (전각도 낙하 통합)
  - **IMPACT** 시나리오 → `impact_report.sh` (전위치 부분충격 통합)

`prepare` 단계에서 `postprocess` 옵션을 주지 않았거나 자동 실행(`auto_*`)을 끈 경우에도, 이 커맨드로 나중에 후처리를 수동 실행할 수 있다 (KooChainRun:306-308). PostprocessShellGenerator 는 `postprocess.enabled` 와 무관하게 항상 sh 를 생성하기 때문이다 (Runner/PostprocessShellGenerator.py:13-14).

추가로, `deep_report.sh` 가 없는 케이스라도 `Output/` 폴더(d3plot)가 있으면 그 자리에서 sh 를 fallback 생성하여 후처리를 시도한다 — 시뮬이 실패했어도 d3plot 만 있으면 후처리 가능 (KooChainRun:2589-2609).

---

## 2. 입력 옵션 · 인자 (표)

| 인자 / 옵션 | 형식 | 필수 여부 | 기본값 | 설명 | 코드 근거 |
|---|---|---|---|---|---|
| `config` | 위치 인자 (positional) | **필수** | 없음 | `runner_config.json` 파일 경로. (디렉토리가 아니라 파일을 가리킨다.) | KooChainRun:309 |
| `--deep` | 플래그 (store_true) | 선택 | 미설정 | 각 `Run_*/deep_report.sh` 만 순차 실행. | KooChainRun:311-312 |
| `--sphere` | 플래그 (store_true) | 선택 | 미설정 | `sphere_report.sh` 만 실행 (전각도 DROP). | KooChainRun:313-314 |
| `--impact` | 플래그 (store_true) | 선택 | 미설정 | `impact_report.sh` 만 실행 (전위치 부분충격 IMPACT). | KooChainRun:315-316 |
| `--all` | 플래그 (store_true) | 선택 | **사실상의 기본값** | deep 모두 실행 후 종합 리포트. 종합 리포트는 scenario mode 로 sphere/impact 자동 선택. | KooChainRun:317-318 |

> `--deep` / `--sphere` / `--impact` / `--all` 은 **상호 배타 그룹**(mutually exclusive group)이다. 동시에 두 개 이상 지정할 수 없다 (KooChainRun:310).

> 네 플래그 중 **아무 것도 주지 않으면 `--all` 과 동일**하게 동작한다. 즉 deep 전부 + (scenario mode 에 맞는) 종합 리포트 1개를 실행한다 (KooChainRun:2567-2571). 이때 `report_mode` 가 `"IMPACT"` 면 impact, 아니면 sphere 가 선택된다.

서브파서 등록 (KooChainRun:303-318):

```text
pp_parser = subparsers.add_parser(
    'postprocess',
    help='KooD3plotReader 후처리 수동 실행',
    description='runner_config.json 기반 deep_report / sphere_report 수동 실행. '
                'auto 옵션 안 줬어도 prepare 시 생성된 sh를 trigger.'
)
pp_parser.add_argument('config', help='runner_config.json 경로')
pp_group = pp_parser.add_mutually_exclusive_group()
pp_group.add_argument('--deep', action='store_true', ...)
pp_group.add_argument('--sphere', action='store_true', ...)
pp_group.add_argument('--impact', action='store_true', ...)
pp_group.add_argument('--all', action='store_true', ...)
```

### 참고: `runner_config.json` 의 `postprocess` 블록 키

이 커맨드 자체의 CLI 옵션은 위 표가 전부이다. 다만 deep_report.sh **fallback 생성**시 `runner_config["postprocess"]` 블록을 옵션으로 사용한다 (KooChainRun:2580, 2596-2601). 후처리 동작을 세밀하게 조정하려면 `prepare` 단계의 scenario.json `postprocess` 블록을 통해 다음 키를 설정한다 (Runner/PostprocessShellGenerator.py:64-93, 16-23).

| 키 | 용도 | 코드 근거 |
|---|---|---|
| `enabled` | 후처리 자동 실행 여부 (수동 trigger 에는 무관) | Runner/PostprocessShellGenerator.py:14 |
| `auto_deep` / `auto_sphere` / `auto_impact` | submit 후 자동 실행 분기 (DROP→sphere, IMPACT→impact) | KooChainRun:838, 852, 858 |
| `sif_path` | SmartTwinPostprocessor.sif 경로 (기본 `/opt/apptainers/SmartTwinPostprocessor.sif`) | Runner/PostprocessShellGenerator.py:28, 75 |
| `section_view_axes` | 단면 뷰 축 리스트 (기본 `["z"]`) | Runner/PostprocessShellGenerator.py:29, 77 |
| `section_view_fields` | 단면 뷰 필드 리스트 (기본 `["von_mises"]`) | Runner/PostprocessShellGenerator.py:30, 78 |
| `section_view_mode` | `section` / `section_3d` / `iso_surface` (기본 `section`) | Runner/PostprocessShellGenerator.py:31, 79 |
| `ua_threads` / `sv_threads` | unified_analyzer / section view 스레드 수 (기본 8 / 8) | Runner/PostprocessShellGenerator.py:32-33, 80-81 |
| `delete_d3plot_after_deep` | deep_report 성공 후 d3plot 삭제 (기본 false) | Runner/PostprocessShellGenerator.py:93 |
| `deep_extra_args` / `sphere_extra_args` / `impact_extra_args` | koo_*_report 명령 끝에 그대로 추가되는 인자 (list 권장 / 문자열도 허용) | Runner/PostprocessShellGenerator.py:16-23, 86 |

---

## 3. 사용 예제

### 3-1. CLI 명령

`Examples/portable_bundle/QUICKSTART.md:116-118` 에서 발췌 (가공 최소화):

```bash
# deep + 종합 리포트 (scenario mode 로 sphere|impact 자동 선택)
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --all

# deep_report 만
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --deep

# sphere_report 만 (전각도 DROP)
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --sphere
```

IMPACT(부분충격) 시나리오는 종합 리포트로 impact 만 실행할 수 있다 (KooChainRun:315-316, 2642-2658):

```bash
KooChainRun postprocess runner_config.json --impact
```

`sphere_report` 에서 "No analysis_results" 가 나면 deep_report 를 먼저 완료해야 한다 (`postprocess --deep` 실행 후 `--sphere`) (Examples/portable_bundle/QUICKSTART.md:250).

### 3-2. scenario.json 의 `postprocess` 블록

`prepare` 단계에서 후처리 옵션을 설정하면, 그 값이 `runner_config.json` 으로 직렬화되어 이 커맨드의 fallback 생성/종합 리포트 라우팅에 사용된다. `Examples/postprocess_pipeline/scenario_with_postprocess.json:30-44` 발췌:

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

> `deep_extra_args` pass-through 예시 (Runner/PostprocessShellGenerator.py:23):
> `"deep_extra_args": ["--per-part-render", "--yield-stress", "350"]`

---

## 4. 동작 원리 (코드 근거)

진입점은 `cmd_postprocess(args)` 이다 (KooChainRun:2532). 처리 순서:

1. **config 로드** — `args.config` 를 절대경로로 변환, 없으면 에러 종료. JSON 으로 읽어 `runner_config` 로 사용한다 (KooChainRun:2540-2545).

2. **output_dir 결정** — `runner_config["project"]["output_dir"]` 가 있으면 그것을, 없으면 `runner_config["base_dir"]/output` (없으면 config 디렉토리/output)을 사용한다. 디렉토리가 없으면 에러 종료 (KooChainRun:2547-2555).

3. **종합 리포트 mode 판정** — `report_mode_from_runner_config(runner_config)` 로 `"IMPACT"` 또는 `"DROP"` 을 판정한다 (KooChainRun:2557-2559). 판정 규칙은 다음과 같다 (Runner/PostprocessShellGenerator.py:300-327):
   - `scenario.steps[].mode` 가 모두 `IMPACT` → `"IMPACT"`, 모두 `DROP` → `"DROP"`, 혼합 → 첫 step 의 mode.
   - steps 가 비어 있으면 `scenario.doe_positions` 가 있으면 `"IMPACT"`, 아니면 `"DROP"` (기본).

4. **실행할 단계 결정** (KooChainRun:2561-2571):
   - `--deep` → deep 만
   - `--sphere` → sphere 만
   - `--impact` → impact 만
   - 그 외(`--all` 또는 무플래그) → `do_deep=True`, 그리고 `report_mode=="IMPACT"` 이면 impact, 아니면 sphere.

5. **deep 실행** (`do_deep` 일 때, KooChainRun:2584-2622):
   - `output_dir/Run_*` 디렉토리들을 정렬하여 순회한다.
   - 각 디렉토리에 `deep_report.sh` 가 없으면: `Output/` 폴더(d3plot)가 있는 경우에 한해 `build_deep_report_sh(...)` 로 sh 를 **fallback 생성**하고 `chmod 0755` 한다. `Output/` 이 없으면 skip (KooChainRun:2589-2609).
   - sh 가 있으면 `bash <sh>` 를 해당 Run 디렉토리에서 실행, 표준출력/에러를 `deep_report.log` 로 리다이렉트한다 (KooChainRun:2610-2616).
   - returncode 0 이면 성공 카운트, 아니면 실패 카운트 후 `✗ rc=...` 출력. 마지막에 done/failed 요약 출력 (KooChainRun:2617-2622).

6. **sphere 실행** (`do_sphere` 일 때, KooChainRun:2624-2640):
   - `output_dir/sphere_report.sh` 가 없으면 "prepare 시 postprocess 옵션이 있어야 자동 생성됨" 안내 후 skip.
   - 있으면 `bash sphere_report.sh` 를 output_dir 에서 실행, 로그를 `sphere_report.log` 로 기록. rc 에 따라 `✓ done` / `✗ rc=...` 출력.

7. **impact 실행** (`do_impact` 일 때, KooChainRun:2642-2658):
   - sphere 와 동일 패턴. `output_dir/impact_report.sh` → `impact_report.log`.

생성되는 후처리 sh 의 내용 자체는 PostprocessShellGenerator 가 만든다. 예를 들어 deep_report.sh 는 `apptainer exec ... python3 -m koo_deep_report <RUN_DIR> ...` 형태로, SIF 미존재 시 exit 2 하고 `set -e` 로 실패를 전파한다 (Runner/PostprocessShellGenerator.py:102-131).

### 자동 실행(auto)과의 관계

`postprocess` 커맨드는 **수동** trigger 이다. `submit` 경로에서는 별도로 `_maybe_submit_sphere_after()` 가 호출되어, `postprocess.enabled` 가 참이고 mode 에 맞는 `auto_sphere`/`auto_impact` 가 켜져 있으면 종합 리포트를 dependency job 으로 자동 제출한다 (KooChainRun:825-862). 즉 자동 실행은 submit 시점에, 수동 실행은 이 `postprocess` 커맨드로 이루어진다.

---

## 5. 주의사항 · 한계

- **`config` 인자는 디렉토리가 아니라 `runner_config.json` 파일 경로**이다. (`diagnose` 가 디렉토리를 받는 것과 다르다.) 파일이 없으면 즉시 에러 종료한다 (KooChainRun:2540-2543).
- **output_dir 가 없으면 에러 종료**한다. prepare/submit 이 끝나 결과 폴더가 생성된 뒤에 실행해야 한다 (KooChainRun:2553-2555).
- **deep 가 sphere/impact 의 선행 조건**이다. 종합 리포트는 각 케이스의 deep 결과(`report/analysis_result.json` 등)를 집계하므로, deep 이 완료되지 않으면 "No analysis_results" 류 오류가 발생할 수 있다. `--deep` 먼저 실행 후 `--sphere`(또는 `--impact`)를 권장한다 (Examples/portable_bundle/QUICKSTART.md:250).
- **sphere/impact sh 는 fallback 생성하지 않는다.** deep 와 달리, 종합 리포트 sh 가 없으면 "prepare 시 postprocess 옵션이 있어야 자동 생성됨" 안내만 출력하고 skip 한다. 즉 prepare 단계에서 `postprocess` 블록이 있어야 한다 (KooChainRun:2626-2628, 2644-2646).
- **DROP 와 IMPACT 종합 리포트는 동시에 돌지 않는다.** 무플래그/`--all` 에서는 scenario mode 로 하나만 선택된다. 과거 IMPACT 데이터에 sphere 가 잘못 돌던 버그가 있어 mode 라우팅으로 수정되었다 (KooChainRun:828-830, 2570-2571).
- **deep 실행 시 `deep_report.sh` 가 없고 `Output/` 폴더도 없으면 그 케이스는 skip** 된다 (d3plot 미생성으로 간주) (KooChainRun:2592-2594).
- 모든 실행 결과는 화면 출력이 아니라 각 디렉토리의 로그 파일(`deep_report.log` / `sphere_report.log` / `impact_report.log`)에 기록된다. 실패 시 rc 와 로그 경로가 화면에 표시되므로 해당 로그를 확인한다 (KooChainRun:2611-2658).
- 후처리 sh 는 `apptainer exec` 로 SmartTwinPostprocessor.sif 를 사용한다. SIF 가 없으면 sh 내부에서 exit 2 로 실패한다 (Runner/PostprocessShellGenerator.py:113-116).

---

## 6. 개발 현황

**구현됨.**

근거:
- `postprocess` 서브파서와 모든 플래그(`--deep`/`--sphere`/`--impact`/`--all`)가 등록되어 있고 (KooChainRun:303-318), `main()` 에서 `cmd_postprocess(args)` 로 디스패치된다 (KooChainRun:340-341).
- `cmd_postprocess` 본문이 deep / sphere / impact 실행, fallback sh 생성, mode 라우팅, 로그 기록까지 완전히 구현되어 있다 (KooChainRun:2532-2658).
- 후처리 sh 생성기(`build_deep_report_sh`, `build_sphere_report_sh`, `build_impact_report_sh`, `report_mode_from_runner_config`)가 `Runner/PostprocessShellGenerator.py` 에 존재한다 (Runner/PostprocessShellGenerator.py:57, 134, 231, 300).
- 실제 사용 예제(scenario.json `postprocess` 블록, CLI 명령)가 Examples 에 존재한다 (Examples/postprocess_pipeline/, Examples/portable_bundle/).
