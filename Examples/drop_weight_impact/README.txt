================================================================================
Drop Weight Impact — 전위치 부분충격 시뮬레이션
================================================================================

목적:
  모델 표면의 여러 위치에 충격자(Ball/Cylinder)를 떨어뜨리는
  부분충격(Ball Drop) 시뮬레이션을 자동으로 생성/실행/수집.

================================================================================
빠른 시작
================================================================================

  # 기본 설정으로 실행
  ./run.sh

  # 옵션 조정
  ./run.sh --nodes 10 --ncpu-per-job 32

  # 설정만 생성 (제출 안 함)
  ./run.sh --dry-run

================================================================================
수동 실행
================================================================================

  # 1. 준비
  KooChainRun prepare scenario.json

  # 2. 실행
  KooChainRun submit runner_config.json

  # 3. 결과 수집
  KooChainRun collect runner_config.json

================================================================================
run.sh 옵션
================================================================================

  --nodes N          Slurm 노드 수 (기본: 5)
  --jobs-per-node N  노드당 동시 실행 Job 수 (기본: 2)
  --ncpu-per-job N   Job당 CPU 수 (기본: 16)
  --dry-run          설정 생성만, 제출 안 함
  -h, --help         도움말

================================================================================
scenario.json 옵션
================================================================================

  mode                  "drop_weight_impact" (필수)
  model_file            원본 LS-DYNA 모델 경로
  output_dir            결과 출력 디렉토리

  simulation_params:
    tFinal              종료 시간 (s, 기본 0.001)
    dt                  출력 간격 (s, 기본 0.000001)

    impactor:           충격자 설정
      type              "Sphere" 또는 "Cylinder"
      radius            반경 (mm)
      height            낙하 높이 (mm) → 속도 v=sqrt(2*g*h) 자동 계산
      density           밀도 (톤/mm^3)
      youngs_modulus     탄성 계수 (MPa)
      poisson_ratio      포아송 비

    locations:          충격 위치 DOE
      mode              "grid" — 격자 (기본)
                        "list" — 좌표 직접 지정
                        "lhs"  — Latin Hypercube Sampling

      --- grid 모드 ---
      x_range           [min, max] mm (생략 시 모델 bbox 자동)
      y_range           [min, max] mm (생략 시 모델 bbox 자동)
      x_count           X 격자 수 (기본 7)
      y_count           Y 격자 수 (기본 13)
      spacing           격자 간격 mm (x_count/y_count 대신 사용)
      margin            bbox 대비 범위 비율 (기본 0.9 = 90%)

      --- list 모드 ---
      points            [[x1,y1],[x2,y2],...] 직접 좌표

      --- lhs 모드 ---
      n_samples          샘플 수 (기본 50)
      x_range / y_range  범위 (생략 시 bbox 자동)

    generation_mode     "DampingSpring" — 댐퍼 스프링 (기본)
                        "OutsideRigidPart" — 반경 밖 파트 강체화
                        "OutsideRigidElement" — 반경 밖 요소 강체화
    boundary_distance   강체화 반경 mm (0=비활성)
    offset_distance     충격자-모델 간격 mm (기본 0.05)

    wall:               바닥판 물성
      youngs_modulus     탄성 계수
      poisson_ratio      포아송 비
      density           밀도

  environment:          실행 환경
    sif_path            Apptainer SIF 경로 (없으면 직접 실행)
    solver_command      LS-DYNA 명령 (기본 "ls-dyna")
    koomeshmodifier_path KooMeshModifier 바이너리
    koochainrun_path    KooChainRun 바이너리
    ncpu                코어 수 (기본 4)
    memory              메모리 (기본 "4G")
    partition           Slurm 파티션 (기본 "normal")

================================================================================
충격 위치 예시
================================================================================

  격자 (자동 범위):
    "locations": {"mode": "grid", "x_count": 5, "y_count": 5, "margin": 0.9}
    → 모델 bbox 90% 범위에 5x5=25개 격자

  격자 (간격 지정):
    "locations": {"mode": "grid", "spacing": 10.0}
    → 10mm 간격, 모델 크기에 따라 개수 자동

  좌표 직접:
    "locations": {"mode": "list", "points": [[0,0],[10,20],[-15,30]]}

  LHS (랜덤):
    "locations": {"mode": "lhs", "n_samples": 100, "margin": 0.85}

================================================================================
출력 구조
================================================================================

  dwi_output/
  ├── configs/                  step_config 파일들
  │   ├── dwi_0001.txt
  │   ├── dwi_0002.txt
  │   └── ...
  ├── results/                  케이스별 결과
  │   ├── dwi_0001/
  │   │   ├── *.k              생성된 모델
  │   │   ├── d3plot           결과
  │   │   ├── simulation_index.json  메타데이터 (충격 위치 포함)
  │   │   └── status.txt       PASS/FAIL
  │   └── ...
  ├── logs/                    Slurm 로그
  ├── dwi_manifest.json        전체 케이스 목록
  ├── dwi_report.json          결과 리포트
  ├── run.sh                   Slurm array job
  └── runner_config.json

================================================================================
메타데이터 (각 해석 파일에 포함)
================================================================================

  simulation_index.json:
  {
    "location": {
      "x": 15.0,
      "y": -30.0,
      "z": 4.5,
      "impact_direction": [0, 0, -1],
      "parts_in_radius": { ... }
    },
    "impactor": {
      "type": "Sphere",
      "radius": 5.0,
      "mass": 0.0041,
      ...
    },
    "doe": {
      "index": 42,
      "total_count": 91
    }
  }

================================================================================
