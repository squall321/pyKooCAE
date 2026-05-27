# 전각도 낙하 후처리 (`postprocess`) 옵션 종합 정리

KooD3plotReader 후처리(`deep_report` 각 케이스 + `sphere_report` 통합)를 KooChainRun에 통합하기 위한 `scenario.json` 옵션의 완전 reference.

본 문서는 실제 코드(`Runner/PostprocessShellGenerator.py`, `Runner/CumulativeScenarioRunner.py`, `Runner/SlurmSubmitter.py`, `KooChainRun`)에서 grep으로 검증된 옵션만 정리했습니다.

---

## 1. 전체 구조

`scenario.json`에 `postprocess` 블록을 추가하면 후처리 동작 활성화:

```json
{
  "project_name": "...",
  "base_dir": "/data/...",
  "environment": {...},
  "scenarios": [...],
  "postprocess": {
    "enabled": true,
    "auto_deep": true,
    "auto_deep_mode": "inline",
    "auto_sphere": true,
    "yield_stress_mpa": 350
  }
}
```

`postprocess` 키가 아예 없으면 후처리 sh 생성도 안 함 (기존 KooChainRun 동작과 동일).

---

## 2. 마스터 토글 (3개) — 반드시 알아야 할 것

| 옵션 | default | 동작 |
|---|---|---|
| `enabled` | `false` | 마스터 토글. false면 자동 실행 X (sh만 생성 — 수동 trigger 가능) |
| `auto_deep` | `true` | `enabled=true` 시 각 시뮬 직후 deep_report 호출 |
| `auto_sphere` | `true` | `enabled=true` 시 모든 시뮬 끝나면 sphere_report dependent job 제출 |

### 조합별 동작

| `postprocess` 키 / `enabled` | 결과 |
|---|---|
| 키 없음 | sh 생성 안 함, 후처리 0건 — 기존 동작과 동일 |
| 키 있음 + `false` | sh만 생성 → `KooChainRun postprocess --all` 로 수동 trigger 가능 (safety mode) |
| `true` + `auto_deep=true` + `auto_sphere=true` | **표준 사용**. 자동 풀 파이프라인 |
| `true` + 하나만 true | 부분 자동 (드물게 사용) |

---

## 3. Slurm Job 분리 모드 — 핵심 결정

| 옵션 | default | 값 |
|---|---|---|
| `auto_deep_mode` | `"inline"` | `"inline"` / `"separate_job"` |

### `"inline"` (default, 권장)

```
Slurm Job 100: [시뮬 DOE001] → [deep_report DOE001]   ← 같은 잡 ID 안에서 순차
Slurm Job 101: [시뮬 DOE002] → [deep_report DOE002]
...
Slurm Job 105: [sphere_report]   ← 별도 잡 (--dependency=afterany)
```

시뮬+deep 합쳐 한 잡으로 처리. **대부분 권장**.

### `"separate_job"`

```
Slurm Job 100: [시뮬 DOE001]            ← 끝나면 deep_report sbatch 호출
Slurm Job 101: [시뮬 DOE002]
Slurm Job 106: [deep_report DOE001]    ← 별도 잡
Slurm Job 107: [deep_report DOE002]
...
Slurm Job 105: [sphere_report]
```

시뮬 노드를 즉시 해방 → 큐 회전 빠름. **대형 클러스터, 짧은 시뮬 + 무거운 deep_report** 같은 경우만.

→ **`sphere_report`는 모드 무관 항상 별도 잡** (`--dependency=afterany:<all_sim_jobs>`).

---

## 4. 후처리 콘텐츠 옵션

| 옵션 | default | 의미 |
|---|---|---|
| `yield_stress_mpa` | `350` | sphere_report 안전계수 계산 기준 (MPa) |
| `section_view_axes` | `["z"]` | deep_report 단면뷰 축. `["x"]`, `["y"]`, `["z"]`, `["x","y","z"]` 등 |
| `section_view_fields` | `["von_mises"]` | 시각화 필드. `"von_mises"` / `"strain"` / ... |
| `section_view_mode` | `"section"` | `"section"` / `"section_3d"` / `"iso_surface"` |
| `ua_threads` | `8` | unified_analyzer OpenMP threads |
| `sv_threads` | `8` | section view 동시 렌더 threads |

---

## 5. Slurm 리소스 옵션 (separate_job + sphere 잡 자원)

### deep_report 잡 (separate_job 모드만 사용)

| 옵션 | default fallback | 비고 |
|---|---|---|
| `deep_ncpu` | `environment.ncpu` → `1` | deep 잡 CPU |
| `deep_memory` | `environment.memory` → `"8G"` | deep 잡 RAM |
| `deep_partition` | `environment.partition` → `""` | 보통 빈 값 = default |
| `deep_timeout_seconds` | `7200` (=2h) | inline 모드는 subprocess timeout, separate_job은 sbatch time-limit 산정 base |
| `deep_time_limit` | `(timeout_seconds + 600)` 자동 산정 | 명시 시 그대로 (HH:MM:SS) |

### sphere_report 잡 (항상 별도 잡)

| 옵션 | default fallback | 비고 |
|---|---|---|
| `sphere_ncpu` | `env.sphere_ncpu` → `env.ncpu` → `8` | sphere는 보통 1코어로 충분 |
| `sphere_memory` | `env.sphere_memory` → `env.memory` → `"16G"` | 162각도 통합이라 RAM 크게 |
| `sphere_partition` | `env.partition` → `""` | 보통 빈 값 |
| `sphere_time_limit` | `env.sphere_time_limit` → `"04:00:00"` | sphere 잡 wall-time |

**핵심**: 모든 deep/sphere 리소스 옵션은 미지정 시 `environment` 블록의 동명 키 또는 기본값 사용 → 시뮬 환경과 자동 일치, 명시할 때만 override.

---

## 6. 인프라 옵션

| 옵션 | default | 비고 |
|---|---|---|
| `sif_path` | `/opt/apptainers/SmartTwinPostprocessor.sif` | compute node SIF 절대경로 |

---

## 7. 자주 쓰는 시나리오 패턴

### 패턴 A — 표준 (가장 흔함, 대부분 이거)

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "yield_stress_mpa": 350
}
```

나머지 모두 default. **시뮬+deep 한 잡, sphere 별도 잡**. 작은~중간 클러스터에 적합.

### 패턴 B — 대규모 + 큐 회전 빠르게 (수십~수백 노드)

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_deep_mode": "separate_job",
  "auto_sphere": true,
  "yield_stress_mpa": 350,
  "deep_ncpu": 4,
  "deep_memory": "8G",
  "deep_time_limit": "02:00:00",
  "sphere_memory": "32G",
  "sphere_time_limit": "04:00:00"
}
```

시뮬 노드를 즉시 해방 → 큐가 빨리 돌고 N각도 throughput 최대.

### 패턴 C — sh만 생성 (수동 trigger)

```json
"postprocess": {
  "enabled": false,
  "yield_stress_mpa": 350,
  "section_view_axes": ["z"],
  "section_view_fields": ["von_mises"]
}
```

→ `KooChainRun postprocess <runner_config> --all/--deep/--sphere` 로 나중에 수동 실행.
디버깅·실험·후처리 SIF 미배포 환경에 유용.

### 패턴 D — 풍부한 시각화 (3축 + 필드 여러 개)

```json
"postprocess": {
  "enabled": true,
  "auto_deep": true,
  "auto_sphere": true,
  "section_view_axes": ["x", "y", "z"],
  "section_view_fields": ["von_mises", "strain"],
  "section_view_mode": "section_3d",
  "ua_threads": 16,
  "sv_threads": 16
}
```

deep_report 시간 증가 대신 시각화 풍부.

---

## 8. 수동 실행 명령

자동 안 했거나 fail 시 (또는 `enabled=false`인 경우):

```bash
# Deep + Sphere 모두
KooChainRun postprocess <runner_config.json> --all

# Deep만 (각 Run_*/deep_report.sh)
KooChainRun postprocess <runner_config.json> --deep

# Sphere만 (deep 먼저 완료되어 있어야 함)
KooChainRun postprocess <runner_config.json> --sphere
```

SmartTwinMCP에서는 `job_postprocess` tool 호출:
```json
{"registry_id": 42, "mode": "all"}
```

---

## 9. 출력 위치 (참고)

```
output_dir/
├── Run_<timestamp>_<hash>/
│   ├── Output/
│   │   ├── d3plot, mes0000, d3hsp, *.log   ← LS-DYNA 결과
│   │   └── report/                          ← deep_report 결과 (HTML + JSON + renders)
│   └── deep_report.sh                       ← 항상 생성 (수동 실행 가능)
├── deep_report_jobs.txt                     ← separate_job 모드 시 잡 ID 기록
├── sphere_report.sh                         ← 항상 생성
├── sphere_report.sbatch                     ← auto_sphere=true 시
├── sphere_report.html                       ← Mollweide projection 통합 보고서 ★ 핵심 결과
├── sphere_report.json
└── sphere_normal_term.txt                   ← 정상 종료 시뮬 목록 (필터 결과)
```

---

## 10. Normal Termination 필터 (자동, 옵션 없음)

`sphere_report.sh`가 자동으로:

1. 각 `Run_*/Output/{mes0000,d3hsp,*.log}` grep
2. `"N o r m a l    t e r m i n a t i o n"` 매칭 케이스만 sphere 입력
3. fail 케이스는 자동 제외, `sphere_normal_term.txt`에 정상 목록 기록

→ 일부 시뮬 fail해도 sphere는 정상 케이스로 동작.

---

## 11. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| sphere_report "No analysis_results" | deep_report 먼저 완료 필요 → `KooChainRun postprocess --deep` 먼저 |
| sphere_report "정상 종료 시뮬 0개" | 모든 시뮬이 fail. `output/slurm_scripts/*.log`에서 LS-DYNA fail 원인 확인 |
| `SIF not found` | compute node에 `/opt/apptainers/SmartTwinPostprocessor.sif` 배포 필요 |
| deep_report.sh 누락 (시뮬 fail 후 후처리 시도) | KooChainRun postprocess --deep이 fallback으로 자동 생성 (v1.4.0+) |
| deep_report 실행 매우 느림 | `ua_threads`/`sv_threads` 증가 또는 `deep_ncpu` 증가 (separate_job 모드) |
| sphere job OOM | `sphere_memory: "32G"` 또는 더 크게 |

---

## 12. 참고 자료 (이 repo)

- `Examples/postprocess_pipeline/README.md` — 후처리 작성 규칙 요약
- `Examples/postprocess_pipeline/scenario_with_postprocess.json` — 표준 패턴 (A)
- `Examples/postprocess_pipeline/scenario_with_postprocess_separate_job.json` — 패턴 (B)
- `Examples/postprocess_pipeline/scenario_without_postprocess.json` — 패턴 (C)
- `docs/FullAngleDrop_HPC_Workflow.md` — 전각도 + 후처리 종합 가이드 (§3.5 Slurm Job ID 구조)
- `Examples/portable_bundle/03_fibonacci_162_with_postprocess.json` — portable baseline (패턴 A)
- `Examples/portable_bundle/04_fibonacci_162_separate_job.json` — portable baseline (패턴 B)

---

## 13. 변경 이력

- v1.4.0: `auto_deep_mode` 옵션 추가 (`inline` / `separate_job`)
- v1.4.0: `deep_report_jobs.txt` 자동 기록 (separate_job 모드)
- v1.4.0: deep/sphere 리소스 옵션의 `environment` fallback 체인

---

**버전:** KooChainRun v1.4.0+ 기준
