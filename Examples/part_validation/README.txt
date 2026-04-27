================================================================================
Part Validation — 파트별 낙하 검증 시뮬레이션
================================================================================

목적:
  전각도 낙하 해석 전에, 각 파트를 독립적으로 0도 낙하시켜
  해석이 정상 종료되는지 사전 확인.
  터지는 파트 = 메시 품질 문제 (찌그러진 요소, 퇴화 요소 등)

================================================================================
사용법
================================================================================

1. scenario.json 작성
   - model_file: 원본 모델 경로
   - output_dir: 결과 출력 디렉토리
   - simulation_params: 낙하 높이, 종료 시간
   - environment: Slurm/솔버 설정

2. prepare (모델 분할 + runner_config + run.sh 생성)

   KooChainRun prepare scenario.json

   결과:
   - validation_output/Part_XXXXXX.k  (파트별 독립 모델)
   - validation_output/run.sh          (Slurm array job 스크립트)
   - validation_output/validation_manifest.json (파트 정보 + Tied 관계)
   - runner_config.json                (KooChainRun submit용)

3. submit (Slurm으로 전체 파트 병렬 실행)

   KooChainRun submit runner_config.json

   또는 직접:
   sbatch validation_output/run.sh

4. collect (결과 수집)

   KooChainRun collect runner_config.json

   결과:
   - validation_output/validation_report.json (PASS/FAIL 리포트)

================================================================================
scenario.json 필드 설명
================================================================================

  mode              "part_validation" (필수)
  model_file        원본 LS-DYNA 키워드 파일 (.k) 경로
  output_dir        출력 디렉토리 (상대/절대 경로)

  simulation_params:
    height           낙하 높이 (mm, 기본 100)
    tFinal           종료 시간 (s, 기본 0.0005)
    dt               출력 간격 (s, 기본 0.00001)

  environment:
    sif_path          Apptainer SIF 경로 (없으면 직접 실행)
    solver_command    LS-DYNA 실행 명령 (기본 "ls-dyna")
    koomeshmodifier_path  KooMeshModifier 바이너리 경로
    ncpu              파트당 CPU 수 (기본 4)
    memory            파트당 메모리 (기본 "4G")
    partition         Slurm 파티션 (기본 "normal")

  min_elements       이 개수 미만 요소를 가진 파트는 건너뜀 (기본 10)
  except_pids        제외할 PID 리스트 (기본 [])

================================================================================
각 파트별 모델 (.k) 구성
================================================================================

  - 원본 파트의 노드/요소/재료/섹션만 포함
  - 10x10 quad shell 바닥판 자동 생성
  - 바닥판 위치: 파트 하단에서 height(mm) 아래
  - 0도 자유낙하 초기속도 자동 계산 (v = sqrt(2*g*h))
  - AUTOMATIC_SURFACE_TO_SURFACE 접촉 (SOFT=2, DEPTH=35)
  - CONTROL_TIMESTEP: TSSFAC=0.67, ERODE=1

================================================================================
결과 해석
================================================================================

  PASS  = 해석 정상 종료 → 해당 파트 메시 문제 없음
  FAIL  = 해석 비정상 종료 → 메시 품질 확인 필요
         - d3plot 확인: validation_output/results/Part_XXXXXX/
         - 에러 로그: validation_output/logs/slurm_*_*.err

  모든 파트가 PASS이면 전각도 낙하 진행 가능

================================================================================
예시
================================================================================

  # 1. 준비
  cd Examples/part_validation
  KooChainRun prepare scenario.json

  # 2. 실행
  KooChainRun submit runner_config.json

  # 3. 결과 확인
  KooChainRun collect runner_config.json

  # 4. 실패 파트 확인
  cat validation_output/validation_report.json

================================================================================
