# Postprocess Pipeline (KooD3plotReader 통합)

KooChainRun으로 162방향 전각도 낙하 시뮬을 돌린 후 자동 또는 수동으로 KooD3plotReader 후처리 (`koo_deep_report` per-case + `koo_sphere_report` 통합) 실행.

## 동작 모드

| scenario.json `postprocess.enabled` | 동작 |
|---|---|
| `false` 또는 `postprocess` 키 없음 (default) | sh 생성 안 함, 후처리 안 함 — 기존 동작과 동일 |
| `false`이지만 `postprocess` 키 있음 | sh만 생성 (`sphere_report.sh`), 자동 실행 안 함 — 사용자가 언제든 수동 trigger |
| `true` + `auto_deep=true` | 각 시뮬 직후 `deep_report.sh` 자동 실행 |
| `true` + `auto_sphere=true` | 모든 시뮬 끝난 뒤 Slurm dependent job(`afterany`)으로 `sphere_report.sh` 실행 |

### Slurm Job ID 구조 (default = `inline`)

기본 동작: **시뮬 + deep_report는 같은 Slurm Job ID로 묶임, sphere_report만 별도 잡**.

```
Slurm Job 100: [시뮬 DOE001] → [deep_report DOE001]    같은 잡 ID
Slurm Job 101: [시뮬 DOE002] → [deep_report DOE002]    같은 잡 ID
...
Slurm Job 105: [sphere_report]                          별도 잡 (--dependency=afterany:100:101:...)
```

| `auto_deep_mode` | 시뮬 + deep_report | sphere_report | 권장 케이스 |
|---|---|---|---|
| `"inline"` (default) | **같은 Slurm Job ID** (시뮬 잡 안에서 deep 순차 실행) | 별도 잡 | 일반적인 경우 (특히 시뮬 짧고 deep도 가벼울 때) |
| `"separate_job"` | **다른 Slurm Job ID** (deep_report는 시뮬 종료 직후 별도 sbatch) | 별도 잡 | 시뮬 노드를 큐 회전을 위해 빨리 해방하고 싶을 때 |

**대부분의 경우 `auto_deep_mode` 미지정 (= default `inline`)이 권장**.

## scenario.json 옵션

**기본 사용법 (default `inline`, 시뮬+deep 같은 잡)**:
```json
{
  "project_name": "...",
  "base_dir": "/data/...",
  "environment": {...},
  "scenarios": [...],
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
}
```

**옵션 1 — `separate_job` (deep_report 별도 잡으로 분리, 시뮬 노드 즉시 해방)**:
```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_deep_mode": "separate_job",
  "auto_sphere": true,
  "deep_ncpu": 4,
  "deep_memory": "8G",
  "deep_time_limit": "02:00:00",
  ... (나머지 동일)
}
```
`deep_ncpu/memory/time_limit`을 생략하면 환경(`environment.ncpu`, `environment.memory`)을 자동으로 사용 — 즉 deep_report 잡 리소스가 시뮬 잡과 자동 일치.

| 키 | 기본값 | 설명 |
|---|---|---|
| `enabled` | `false` | 마스터 토글. false면 자동 실행 X (sh만 생성) |
| `auto_deep` | `true` | enabled=true 시 각 시뮬 직후 deep_report 호출 |
| `auto_deep_mode` | `"inline"` | `"inline"`(default): **시뮬 + deep 같은 잡 ID** / `"separate_job"`: deep을 별도 Slurm 잡으로 분리 |
| `auto_sphere` | `true` | enabled=true 시 모든 시뮬 후 sphere_report dependent job 제출 |
| `deep_ncpu`, `deep_memory`, `deep_time_limit` | `env.ncpu`, `env.memory`, `02:00:00` | `separate_job` 모드 deep sbatch 리소스. 미지정 시 environment fallback → 시뮬 잡 자원과 자동 일치 |
| `sif_path` | `/opt/apptainers/SmartTwinPostprocessor.sif` | KooD3plotReader SIF (compute node 표준) |
| `yield_stress_mpa` | `350` | sphere_report 안전계수 계산용 |
| `section_view_axes` | `["z"]` | deep_report 단면뷰 축 (`x`/`y`/`z`) |
| `section_view_fields` | `["von_mises"]` | 시각화 필드 (`von_mises`/`strain`/...) |
| `section_view_mode` | `"section"` | `section`/`section_3d`/`iso_surface` |
| `ua_threads` | `8` | unified_analyzer OpenMP 스레드 |
| `sv_threads` | `8` | section view 동시 렌더 스레드 |
| `deep_timeout_seconds` | `7200` | deep_report 단일 케이스 타임아웃 |
| `sphere_memory`, `sphere_time_limit` | `16G`, `04:00:00` | sphere job sbatch 자원 |

## 수동 실행 (옵션 안 줘도 OK)

```bash
# Deep + Sphere 모두 실행
KooChainRun postprocess runner_config.json --all

# Deep만 (각 Run_*/deep_report.sh)
KooChainRun postprocess runner_config.json --deep

# Sphere만
KooChainRun postprocess runner_config.json --sphere
```

수동 실행은 prepare 단계에서 생성된 `output_dir/sphere_report.sh`와 각 `Run_*/deep_report.sh`를 그대로 호출.

## Normal Termination 필터

sphere_report 입력 결정 시 정상 종료된 시뮬만 자동 필터링:
- 각 `Run_*/` 폴더에서 `mes0000*`, `d3hsp*`, `*.log` 파일 grep
- `"N o r m a l    t e r m i n a t i o n"` 문자열 매칭된 케이스만 sphere에 입력
- `output_dir/sphere_normal_term.txt`에 정상 종료 케이스 목록 기록

## 출력 구조

```
output_dir/
├── Run_001_xxx/
│   ├── Output/             ← LS-DYNA d3plot
│   ├── deep_report.sh      ← 항상 생성
│   ├── deep_report.log     ← 자동 실행 시
│   └── Output/report/      ← deep_report 결과 (HTML + JSON + renders)
├── Run_002_xxx/
│   └── ...
├── sphere_report.sh        ← 항상 생성 (postprocess 키 있으면)
├── sphere_report.sbatch    ← auto_sphere=true 시
├── sphere_report.html      ← sphere 실행 결과
├── sphere_report.json
└── sphere_normal_term.txt
```

## 예제 파일

- `scenario_with_postprocess.json` — 자동 실행 활성 (**default `inline`**: 시뮬+deep 같은 잡, sphere 별도)
- `scenario_with_postprocess_separate_job.json` — `separate_job` 모드 (시뮬/deep/sphere 모두 별도 잡)
- `scenario_without_postprocess.json` — sh만 생성, 수동 trigger 가정

## 위험 / 주의

- **SIF 경로**: compute node에 `/opt/apptainers/SmartTwinPostprocessor.sif` 있어야 함. 없으면 sh가 명시적 에러 출력 후 종료
- **Slurm dependency**: `--dependency=afterany`라 LS-DYNA 실패 케이스 있어도 sphere job은 실행. 정상 종료 필터로 처리
- **노드 점유 시간**: `auto_deep_mode: "inline"` (default)은 시뮬 직후 같은 노드에서 실행 → 노드 lock 길어짐. 시뮬 노드를 빨리 해방하려면 `auto_deep_mode: "separate_job"` 사용 (각 deep_report가 별도 Slurm 잡으로 즉시 제출됨, job IDs는 `output_dir/deep_report_jobs.txt`에 기록)
- **separate_job 모드**: 시뮬 잡 안에서 sbatch를 호출하므로 시뮬 노드가 sbatch 명령어 권한이 있어야 함 (보통 OK)
