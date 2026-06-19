# KooChainRun collect

## 1. 목적 / 개요

`collect` 커맨드는 실행이 완료된 시뮬레이션 결과를 수집하여 요약 리포트를 생성하는 서브커맨드입니다. argparse 등록 시의 설명은 다음과 같습니다.

- help: `Collect simulation results`
- description: `Gather completed results from execution directory`

(근거: `KooChainRun:200-204`)

동작은 `runner_config.json`의 `mode` 값에 따라 세 갈래로 분기합니다.

| mode 값 | 동작 |
|---------|------|
| `part_validation` | `Runner.PartValidationWorkflow.collect_part_validation` 호출 (파트별 PASS/FAIL/PENDING 집계 + `validation_report.json` 생성) |
| `drop_weight_impact` | `Runner.DropWeightImpactWorkflow.collect_drop_weight_impact` 호출 (케이스별 집계 + `dwi_report.json` 생성) |
| 그 외 (일반 DOE) | `LargeScaleDOEManager` 경로 — **결과 수집 미구현(TODO)**, 수동 복사 안내만 출력 |

(근거: `KooChainRun:2026-2054`)

## 2. 입력 옵션 · 인자 (표)

`collect` 서브파서에는 위치 인자 2개만 정의되어 있고, 추가 플래그(`--`)는 없습니다.

| 인자 | 종류 | 필수 | 기본값 | 설명 | 근거 |
|------|------|------|--------|------|------|
| `config` | 위치 인자 | 예 | 없음 | `runner_config.json` 파일 경로 | `KooChainRun:205-208` |
| `output_dir` | 위치 인자 | 아니오 (`nargs='?'`) | `./results` | 수집 결과 출력 디렉터리 | `KooChainRun:209-214` |

주의: `--data-root` 플래그는 `collect`가 아니라 `submit` 서브파서에만 정의되어 있습니다(`KooChainRun:130-134`). `cmd_collect`는 `args.data_root if hasattr(args, 'data_root') else '/data'`로 접근하는데(`KooChainRun:2048`), `collect` 네임스페이스에는 `data_root` 속성이 없으므로 항상 기본값 `'/data'`로 평가됩니다.

또한 `output_dir`는 일반 DOE 경로에서만 사용됩니다. `part_validation` / `drop_weight_impact` 모드 분기는 `output_dir` 인자를 받기 전(`Path(args.output_dir)` 호출 이전)에 `return` 하므로, 두 모드에서는 `output_dir`를 지정해도 무시되고 출력 경로는 `runner_config`의 `output_dir` 필드를 기준으로 결정됩니다(`KooChainRun:2026-2036`, `PartValidationWorkflow.py:146`, `DropWeightImpactWorkflow.py:153`).

## 3. 사용 예제

### CLI 명령 (Examples 발췌)

일반 DOE / 드롭 테스트 (`Examples/HWWarrantyDropTest/Tests/README.md:266`, `Examples/HWWarrantyDropTest/USER_GUIDE.md:606`):

```bash
/opt/pyKooCAE/KooChainRun collect runner_config.json results/
```

part_validation 모드 (`Examples/part_validation/README.txt:39`):

```bash
KooChainRun collect runner_config.json
```

drop_weight_impact 모드 (`Examples/drop_weight_impact/run.sh:141`):

```bash
KooChainRun collect $SCRIPT_DIR/runner_config.json
```

### 모드 분기를 결정하는 runner_config.json 키

`cmd_collect`는 config 파일을 읽어 `rc.get("mode")`로 분기합니다(`KooChainRun:2024-2032`). 따라서 다음과 같은 `mode` 필드가 수집 동작을 좌우합니다.

```json
{
  "mode": "part_validation",
  "output_dir": "..."
}
```

```json
{
  "mode": "drop_weight_impact",
  "output_dir": "...",
  "manifest": "..."
}
```

(drop_weight_impact는 `output_dir` 외에 `manifest` 경로 키를 사용 — `DropWeightImpactWorkflow.py:153-154`)

## 4. 동작 원리 (코드 근거)

### 공통 진입

1. `config_path = Path(args.config).resolve()` 후 파일 존재 확인, 없으면 종료(`KooChainRun:2017-2021`).
2. config를 JSON으로 로드하여 `mode`로 분기(`KooChainRun:2024-2032`).

### part_validation 분기 (`PartValidationWorkflow.py:141-206`)

- `output_dir/validation_manifest.json`을 manifest로 읽음(`PartValidationWorkflow.py:146-154`). manifest 없으면 에러 출력 후 반환(`:149-151`).
- manifest의 각 파트에 대해 `output_dir/results/<basename>/status.txt`를 확인(`:161-177`).
  - 파일 내용에 `"PASS"` 포함 → PASS 카운트(`:169-171`).
  - status.txt가 있으나 PASS 아님 → FAIL 카운트(`:172-174`).
  - status.txt 없음 → PENDING 카운트(`:175-177`).
- 전체/PASS/FAIL/PENDING 요약과 실패 파트 목록 출력(`:181-192`).
- 리포트를 `output_dir/validation_report.json`(또는 인자 `output_report`)에 JSON으로 저장(`:194-206`).

### drop_weight_impact 분기 (`DropWeightImpactWorkflow.py:148-206`)

- config의 `manifest` 경로를 읽음. 없으면 에러 출력 후 반환(`:153-157`).
- manifest의 각 case에 대해 `output_dir/results/dwi_<idx:04d>/status.txt` 확인(`:167-181`).
  - `"PASS"` 포함 → PASS / 그 외 → FAIL / 파일 없음 → PENDING(`:172-181`).
- case별 `index`, `location_x`, `location_y`, `status`를 결과 리스트에 적재(`:183-188`).
- 요약과 실패 케이스(좌표 포함) 출력(`:190-200`).
- 리포트를 `output_dir/dwi_report.json`에 JSON으로 저장(`:202-206`).

### 일반 DOE 분기 (미구현)

- `LargeScaleDOEManager(runner_config_path=..., data_root='/data')`를 인스턴스화(`KooChainRun:2046-2049`).
- 실제 수집 로직은 TODO 주석으로 남아 있고, 다음 안내만 출력(`KooChainRun:2051-2054`):
  ```
  ⚠️  Result collection not yet implemented
  Manual collection:
    cp -r RUNDIR/runid_*/ <output_dir>/
  ```

## 5. 주의사항 · 한계

- **일반 DOE 모드 수집 미구현**: `mode`가 `part_validation`/`drop_weight_impact`가 아닌 경우, 결과를 실제로 복사·집계하지 않고 수동 복사 안내만 출력합니다(`KooChainRun:2051-2054`). 즉 `output_dir` 인자를 주어도 자동 복사는 일어나지 않습니다.
- **`output_dir` 인자 무시 케이스**: part_validation / drop_weight_impact 모드는 `output_dir` 인자를 받기 전에 분기·반환하므로, 해당 모드에서 두 번째 위치 인자는 효과가 없습니다. 출력 경로는 config의 `output_dir` 필드를 따릅니다(§2 참조).
- **status.txt 기반 판정**: 두 모드 모두 케이스/파트별 `status.txt` 파일 존재 여부와 그 안의 `"PASS"` 문자열로 상태를 판정합니다. status.txt가 생성되기 전에 collect를 실행하면 PENDING으로 집계됩니다(`PartValidationWorkflow.py:166-177`, `DropWeightImpactWorkflow.py:172-181`).
- **manifest 의존성**: part_validation은 `output_dir/validation_manifest.json`, drop_weight_impact는 config의 `manifest` 경로가 있어야 동작합니다. 없으면 에러 메시지 출력 후 조용히 반환(`return`)합니다 — 종료 코드는 0(`PartValidationWorkflow.py:149-151`, `DropWeightImpactWorkflow.py:155-157`).
- **`--data-root` 미적용**: collect 서브커맨드는 `--data-root`를 받지 않으며, 일반 DOE 분기의 `data_root`는 항상 `/data`로 고정됩니다(§2 참조).

## 6. 개발 현황

**부분구현**

근거:
- part_validation 모드 수집: 구현됨 (`PartValidationWorkflow.py:141-206`, manifest 파싱 + status 집계 + `validation_report.json` 생성).
- drop_weight_impact 모드 수집: 구현됨 (`DropWeightImpactWorkflow.py:148-206`, manifest 파싱 + status 집계 + `dwi_report.json` 생성).
- 일반 DOE 모드 수집: **미구현** — `# TODO: Implement result collection` 주석과 "Result collection not yet implemented" 안내 출력에 그침(`KooChainRun:2051-2054`).
