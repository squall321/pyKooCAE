# 실행 모드 기술 문서

KooChainRun의 DOE 실행 시 I/O 병목 및 성능 최적화를 위한 두 가지 옵션과 그 조합에 대한 기술적 특성을 정리한다.

---

## 배경: NFS I/O 병목 문제

다수의 compute node가 동시에 공유 NFS(`/data/`)에서 시뮬레이션을 실행하면:
- KooMeshModifier: 모델 파일 읽기 + DropSet.k 출력
- LS-DYNA: 입력 파일 읽기 + d3plot, dynain 출력
- 26개 노드 x 128코어가 동시 I/O 시 NVMe 포화 → signal 12, hang, 라이선스 타임아웃 발생

---

## 옵션 1: Scratch Run

### 개요
compute node의 **로컬 디스크**(`/scratch`)에서 시뮬레이션을 수행하고, 완료 후 결과만 NFS로 복사한다.

### scenario.json 설정
```json
{
  "environment": {
    "scratch_run": {
      "enabled": true,
      "scratch_base": "/scratch",
      "cleanup_on_success": true
    }
  }
}
```

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `enabled` | `false` | scratch 모드 활성화 여부 |
| `scratch_base` | `/scratch` | compute node 로컬 디스크 경로 |
| `cleanup_on_success` | `true` | 성공 시 scratch 디렉토리 삭제 여부 |

### 실행 흐름 (sbatch 스크립트 내부)

```
1. SCRATCH_DIR 생성
   /scratch/$SLURM_JOB_ID/DOE_{N}/

2. NFS → scratch 복사
   - 모델 파일 (*.k)
   - runner_config.json (경로 치환: output_dir → scratch)
   - (batch 모드 시) pregenerated DropSet.k
   - (Step 2+ 시) 이전 step dynain

3. trap EXIT 설정
   - 정상/비정상 종료 모두 cleanup 함수 실행

4. scratch에서 시뮬레이션 실행
   - KooMeshModifier (batch가 아닌 경우)
   - LS-DYNA

5. EXIT trap 실행
   - Run_* 폴더 + simulation_index → NFS 원본 위치 복사
   - cleanup_on_success=true && exit_code=0 시 scratch 삭제
   - 실패 시 scratch 유지 (디버깅용)
```

### 기술적 특성

**장점**
- NFS I/O 부하 분산: 시뮬레이션 중 I/O가 로컬 디스크에서 수행됨
- LS-DYNA 성능 향상: d3plot 출력이 로컬 디스크 속도로 수행
- 기존 코드 변경 없음: CumulativeScenarioRunner는 수정 불필요 (sbatch 스크립트 레벨에서 처리)
- multi-step 시나리오에서도 작동

**단점**
- scratch 디스크 용량 제한: 대형 모델의 d3plot이 수십 GB일 수 있음
- 결과 복사 시간 추가: 시뮬레이션 완료 후 NFS로 rsync/cp (네트워크 대역폭 의존)
- 노드 장애 시 결과 유실: trap이 실행되지 못하면 scratch에만 결과 잔존
- 실행 중 진행상황 실시간 확인 불가: NFS에 파일이 없으므로 로그 파일로만 확인

**용량 가이드**
- DOE당 필요 공간: 모델 크기 + d3plot (수 GB ~ 수십 GB)
- 권장 scratch 용량: DOE당 50GB 이상
- 6TB 로컬 디스크: 동시 26개 DOE x 50GB = 1.3TB → 충분

### 적용 범위

| 제출 방식 | 지원 여부 |
|-----------|----------|
| Cumulative (`_submit_cumulative`) | 지원 (구현 완료) |
| LargeScaleDOEManager (Array Job) | 지원 (구현 완료) |

---

## 옵션 2: Batch KooMeshModifier

### 개요
KooMeshModifier를 **헤드노드에서 일괄 실행**하여 모든 DOE의 DropSet.k를 사전 생성한다. compute node에서는 **LS-DYNA만** 실행한다.

### scenario.json 설정
```json
{
  "scenarios": [{
    "batch_koomeshmodifier": true,
    "cumulative": {
      "num_steps": 1
    }
  }]
}
```

### 제약 사항
- **num_steps == 1인 경우에만 사용 가능**: multi-step에서는 이전 step의 dynain이 필요하므로 사전 생성 불가
- num_steps > 1 시 자동으로 일반 모드 fallback

### 실행 흐름

```
[헤드노드 - KooChainRun submit]
1. 전체 DOE의 각도 정보로 batch config 생성
2. KooMeshModifier 실행 (Apptainer 래핑)
   - 모든 DOE의 DropSet.k를 {output_dir}/pregenerated/에 출력
   - DOE 완료 시 .done 마커 파일 생성
3. .done 파일 polling → 준비된 DOE부터 즉시 sbatch 제출

[compute node - KooChainRun run --skip-koomeshmodifier --pregenerated-dir]
4. pregenerated에서 DropSet.k 복사
5. LS-DYNA만 실행
```

### .done 파일 폴링 메커니즘

KooMeshModifier가 DOE를 하나씩 생성하므로 (대형 모델에서 DOE당 수 분), 완료 즉시 compute node에 제출하여 파이프라인 효율을 높인다.

```
시간축 →

KooMeshModifier: [DOE1 생성][DOE2 생성][DOE3 생성]...
                      ↓         ↓         ↓
sbatch 제출:     [DOE1 제출][DOE2 제출][DOE3 제출]...
                      ↓         ↓         ↓
LS-DYNA:         [DOE1 실행   ][DOE2 실행   ][DOE3 실행   ]...
```

.done 파일이 아닌 DropSet.k 존재만으로 판단하면 **파일이 아직 쓰이는 중**일 수 있어 빈 파일이 복사되는 문제가 발생한다. .done은 KooMeshModifier가 해당 DOE의 모든 파일을 완전히 출력한 후에만 생성된다.

### 기술적 특성

**장점**
- compute node에서 Apptainer + KooMeshModifier 오버헤드 제거
- KooMeshModifier는 한 번만 실행 (100 DOE를 한 프로세스에서 순차 생성)
- compute node는 LS-DYNA에만 집중

**단점**
- 헤드노드에 부하 집중: 대형 모델 처리 시 헤드노드 CPU/메모리 사용
- DOE 생성 시간이 길 수 있음: 대형 모델에서 DOE당 ~4분 (1000 DOE = ~67시간)
- KooMeshModifier 실패 시 미생성 DOE는 제출되지 않음 (안전 fallback)
- 1-step 시나리오에서만 사용 가능

### KooMeshModifier 성능 병목 (참고)

대형 모델에서 DOE당 ~4분 소요되는 원인:
- `WriteModifiedFile()`: 매 DOE마다 **전체 모델을 재직렬화** (~40-50%)
- `SyncronizeMaxID()`: 매 DOE마다 **전체 element를 스캔** (~30-40%)
- `UpdateContactGraph()`: 매 DOE마다 **contact bbox 재계산** (~10-15%)

DOE간 실제로 변하는 것은 impact box 위치/회전과 초기속도뿐이나, 현재 구조상 매번 전체 모델을 처음부터 다시 쓰는 구조이다. 최적화하려면 대규모 리팩토링이 필요하다.

---

## 옵션 조합

### 조합별 특성

| # | scratch_run | batch_koomesh | NFS I/O | KooMeshModifier 위치 | 적용 시나리오 |
|---|-------------|---------------|---------|---------------------|-------------|
| A | ❌ | ❌ | 높음 (전체) | compute node | 소규모 테스트 |
| B | ❌ | ✅ | 중간 (LS-DYNA만) | 헤드노드 | 1-step, 소수 노드 |
| C | ✅ | ❌ | 낮음 (결과 복사만) | compute node (scratch) | **multi-step 대규모** |
| D | ✅ | ✅ | 최소 (결과 복사만) | 헤드노드 | **1-step 대규모** |

### 권장 사용 시나리오

| 시나리오 | 권장 조합 | 이유 |
|----------|-----------|------|
| Test_001~003 (26개, 소규모) | A | 오버헤드 불필요 |
| Test_004 (181 DOE, 1-step) | D | 대규모 1-step |
| Test_005 (100 DOE, 1-step) | B 또는 D | 중규모, 필요에 따라 |
| Test_006 (1,146 DOE) | C 또는 D | 대규모, NFS 병목 심각 |
| Test_007 (10,313 DOE) | C 또는 D | 초대규모, scratch 필수 |
| Multi-step (3-step 이상) | C | batch 불가, scratch로 I/O 분산 |

### 조합 D 실행 흐름 (scratch + batch)

```
[헤드노드]
1. KooMeshModifier 일괄 실행 → /data/.../pregenerated/
2. .done 폴링 → 준비된 DOE부터 sbatch 제출

[compute node]
3. scratch 디렉토리 생성
4. pregenerated DropSet.k → scratch 복사
5. scratch에서 LS-DYNA 실행
6. 결과 → NFS 복사
```

---

## 디렉토리 구조

### 조합 A (기본)
```
/data/.../output/
├── Run_{run_id}/          # compute node가 NFS에서 직접 생성
│   ├── DropSet.k
│   ├── d3plot*
│   └── dynain
├── simulation_index.json
└── checkpoint.json
```

### 조합 D (scratch + batch)
```
/data/.../output/
├── pregenerated/                # 헤드노드에서 생성
│   ├── batch_config.txt
│   ├── Run_1/DropSet.k + .done
│   ├── Run_2/DropSet.k + .done
│   └── ...
├── Run_{run_id}/                # compute node에서 scratch → NFS 복사
│   ├── DropSet.k
│   ├── d3plot*
│   └── dynain
├── simulation_index.json
├── simulation_index_doe_001.json  # scratch 모드: DOE별 index
├── simulation_index_doe_002.json
└── checkpoint.json

/scratch/$SLURM_JOB_ID/DOE_001/  # compute node 로컬 (실행 중에만 존재)
├── runner_config.json            # 경로 치환된 config
├── pregenerated/Run_1/DropSet.k
└── output/Run_{run_id}/
    ├── d3plot*
    └── dynain
```

---

## 테스트 예제

### Test_008_Fibonacci_100_v2 (batch만)
```json
"batch_koomeshmodifier": true
// scratch_run 없음
```

### Test_009_ScratchRun_100 (scratch + batch)
```json
"batch_koomeshmodifier": true,
"scratch_run": {
  "enabled": true,
  "scratch_base": "/scratch",
  "cleanup_on_success": true
}
```

### scratch만 사용 (batch 없이)
```json
"batch_koomeshmodifier": false,  // 또는 생략
"scratch_run": {
  "enabled": true,
  "scratch_base": "/scratch",
  "cleanup_on_success": true
}
```

---

## 제출 방식별 지원 현황

| 기능 | Cumulative (개별 sbatch) | LargeScaleDOEManager (Array Job) |
|------|--------------------------|----------------------------------|
| scratch_run | 지원 | 지원 |
| batch_koomeshmodifier | 지원 | 미지원 (별도 관리 체계) |
| ntasks 설정 | `--ntasks={ncpu} --cpus-per-task=1` | `--ntasks={ncpu} --cpus-per-task=1` |
| 완료 추적 | simulation_index.json | .lock 파일 |
| Step 의존성 | KooChainRun 내부 처리 | `--dependency=afterok:{job_id}` |

---

## 오프라인 서버 배포 체크리스트

1. `/data/SmartTwinPreprocessor/` 업데이트 (SmartTwinPreprocessor.tar.gz)
2. scenario.json의 `apptainer_bind`에 overlay 확인:
   ```
   /data/SmartTwinPreprocessor:/opt/SmartTwinPreprocessor
   ```
   → SIF 내 구버전 KooMeshModifier를 호스트의 신버전으로 덮어씌움
3. compute node `/scratch` 디렉토리 존재 및 쓰기 권한 확인
4. compute node 로컬 디스크 용량 확인 (DOE당 최소 50GB 권장)

---

**작성일**: 2026-02-15
