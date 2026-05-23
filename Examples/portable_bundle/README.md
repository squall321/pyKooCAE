# Portable Bundle — 새 환경(다른 PC)에서 KooChainRun 잡 던지기

다른 PC에서 **실행 파일 + 시나리오 + 이 문서**만 가지고 동일한 LS-DYNA 전각도 낙하 잡을 던지기 위한 패키지.

## 가져갈 것 (2개)

1. **실행 파일 tar**: `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_*.tar.gz` (~1.2 GB)
2. **이 폴더 통째로**: `Examples/portable_bundle/` (시나리오 4종 + QUICKSTART + README + HOW_TO_ASK_LLM)
   ```bash
   tar czf portable_bundle.tar.gz Examples/portable_bundle/
   ```

→ 새 PC에서 `tar` 2개만 풀면 시작 가능. **시작은 [QUICKSTART.md](QUICKSTART.md) 부터 읽으세요**.

## 새 PC에서 한 번만 설치

```bash
# 1. tar 풀기 (sudo)
sudo tar xzf SmartTwinPreprocessor_*.tar.gz -C /data/SmartTwinPreprocessor/
sudo tar xzf SmartTwinPreprocessor_*.tar.gz -C /opt/SmartTwinPreprocessor/  # 둘 다 같은 내용

# 2. PATH 확인
/data/SmartTwinPreprocessor/bin/KooChainRun --version
# → KooChainRun 1.4.0
```

## 시나리오 선택

| 파일 | 각도 수 | 시간 | 후처리 | 용도 |
|---|---|---|---|---|
| `01_minimal_single_drop.json` | 1 | 5-10분 | X | 새 환경 첫 검증 — 잡이 떠지는지 확인 |
| `02_fibonacci_5.json` | 5 | 15-30분 | O (inline) | 워크플로우 + 후처리 전체 검증 |
| `03_fibonacci_162_with_postprocess.json` | 162 | 4-12시간 | O (inline, default) | **표준 프로덕션 잡** |
| `04_fibonacci_162_separate_job.json` | 162 | 위와 동일 | O (separate_job) | 시뮬 노드 회전 빠르게, 큐 활용 최적화 |

## 새 PC에서 반드시 바꿔야 할 것 (시나리오 파일)

각 시나리오 JSON에서 다음 3가지만 환경에 맞게 수정:

| 키 | 예시 (현재 클러스터) | 새 PC에서 |
|---|---|---|
| `base_dir` | `/data/koopark/Quick_Fib5` | `/data/<your_user>/<your_project>` |
| `environment.lsdyna_apptainer_env.LSTC_LICENSE_SERVER` | `CHANGE_ME_TO_YOUR_LICENSE_IP` | 새 클러스터의 LSTC 라이센스 서버 IP |
| `environment.apptainer_bind` | `/data:/data,/shared:/shared` | 새 클러스터에서 마운트할 호스트 경로 |

**나머지 환경 옵션(`apptainer_sif`, `lsdyna_apptainer_sif`, `koomeshmodifier_path`, `lsdyna_path` 등)은 클러스터 셋업이 동일하면 그대로 OK.**

## 잡 던지기 (3 단계)

```bash
# 1. 작업 디렉토리 + 모델 준비
mkdir -p /data/<user>/<project>
cd /data/<user>/<project>
cp /path/to/MinimumModel.k .         # 또는 본인 모델 파일
cp /path/to/portable_bundle/02_fibonacci_5.json scenario.json
vi scenario.json                      # base_dir, IP 수정

# 2. prepare → submit
/data/SmartTwinPreprocessor/bin/KooChainRun prepare scenario.json
/data/SmartTwinPreprocessor/bin/KooChainRun submit runner_config.json

# 3. 상태 확인 + 후처리 (자동/수동)
squeue -u $USER                                          # 잡 진행
ls output/Run_*/Output/d3plot                            # 결과
ls output/sphere_report.html                             # 후처리 결과 (자동 시)
# 수동 후처리가 필요한 경우:
/data/SmartTwinPreprocessor/bin/KooChainRun postprocess runner_config.json --all
```

## 트러블슈팅

- **시뮬 5초 만에 fail (MPI_ABORT errorcode 1)** → `LSTC_LICENSE_SERVER` IP 확인
- **`squashfuse: not found`** → compute node에 `apt install libfuse2` 필요
- **sbatch 거부 (Memory)** → `environment.memory` / `lsdyna_memory` 줄이기 (compute node RAM 확인: `scontrol show node`)
- **sphere_report "No analysis_results"** → deep_report 먼저 완료 필요 (`postprocess --deep` 먼저 실행)

자세한 트러블슈팅은 `../QUICKSTART.md` 또는 `../../docs/FullAngleDrop_HPC_Workflow.md` 참조.

## LLM과 함께 작업할 때

다른 PC에서 LLM(Claude/GPT)으로 시나리오 수정하려면 `HOW_TO_ASK_LLM.md` 참고. 표준 요청 프롬프트 템플릿이 있음.
