# 시뮬레이션 디렉토리 구조 예제

각 테스트 시나리오에서 생성되는 디렉토리 구조를 보여줍니다.

---

## 기본 구조 개념

실제 시뮬레이션 실행 시 다음 구조로 생성됩니다:

```
/data/Test_XXX_YYY/
├── runid_00001/
│   ├── metadata.json          # 이 runid의 전체 정보 (각도, Step 시퀀스)
│   ├── Step001/
│   │   ├── Step001.k          # LS-DYNA 입력 파일
│   │   ├── messag             # LS-DYNA 실행 로그
│   │   ├── d3plot*            # 결과 파일 (바이너리)
│   │   ├── dynain             # 변형 상태 (Step 2+로 전달)
│   │   └── Step001.lock       # 완료 플래그
│   ├── Step002/               # (multi-step인 경우에만)
│   └── Step003/
├── runid_00002/
└── ...
```

---

## Test_001: 26방향 1회 낙하

**총 runid 개수**: 26개 (Face 6 + Edge 12 + Corner 8)
**Steps per runid**: 1

### 디렉토리 예시

```
/data/Test_001_Full26_1Step/
├── runid_00001/ (F1_Back, Roll=0.0°, Pitch=0.0°)
│   ├── metadata.json
│   └── Step001/
│       └── README.txt
├── runid_00002/ (F2_Front, Roll=180.0°, Pitch=0.0°)
│   ├── metadata.json
│   └── Step001/
│       └── README.txt
├── runid_00003/ (F3_Right, Roll=0.0°, Pitch=-90.0°)
│   ├── metadata.json
│   └── Step001/
│       └── README.txt
...
├── runid_00026/ (F6_Bottom, Roll=-90.0°, Pitch=0.0°)
│   ├── metadata.json
│   └── Step001/
│       └── README.txt
```

### metadata.json 예시

```json
{
  "runid": "runid_00001",
  "doe_index": 0,
  "scenario_name": "Full_26_Directions_Single_Drop",
  "total_steps": 1,
  "base_angle": {
    "name": "F1_Back",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "steps": [
    {
      "step_number": 1,
      "mode": "DROP",
      "template": "DROP_FIRST",
      "angle": {
        "name": "F1_Back",
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0
      },
      "input_file": "Step001.k",
      "dynain_source": null
    }
  ]
}
```

---

## Test_002: 26방향 3회 연속 낙하

**총 runid 개수**: 26개
**Steps per runid**: 3 (동일 각도 반복)

### 디렉토리 예시

```
/data/Test_002_Full26_3Step/
├── runid_00001/ (F1_Back)
│   ├── metadata.json
│   ├── Step001/ (첫 낙하, DROP_FIRST)
│   │   ├── Step001.k
│   │   ├── messag
│   │   ├── d3plot*
│   │   ├── dynain              # Step 2로 전달
│   │   └── Step001.lock
│   ├── Step002/ (2차 낙하, DROP_CUMULATIVE)
│   │   ├── Step002.k
│   │   ├── initial.k           # dynain → initial 변환 결과
│   │   ├── messag
│   │   ├── d3plot*
│   │   ├── dynain              # Step 3로 전달
│   │   └── Step002.lock
│   └── Step003/ (3차 낙하, DROP_CUMULATIVE)
│       ├── Step003.k
│       ├── initial.k
│       ├── messag
│       ├── d3plot*
│       └── Step003.lock
├── runid_00002/ (F2_Front)
│   ├── metadata.json
│   ├── Step001/
│   ├── Step002/
│   └── Step003/
...
```

### metadata.json 예시 (3-step)

```json
{
  "runid": "runid_00001",
  "doe_index": 0,
  "scenario_name": "Full_26_Directions_3_Consecutive_Drops",
  "total_steps": 3,
  "base_angle": {
    "name": "F1_Back",
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "steps": [
    {
      "step_number": 1,
      "mode": "DROP",
      "template": "DROP_FIRST",
      "angle": { "name": "F1_Back", "roll": 0.0, "pitch": 0.0, "yaw": 0.0 },
      "input_file": "Step001.k",
      "dynain_source": null
    },
    {
      "step_number": 2,
      "mode": "DROP",
      "template": "DROP_CUMULATIVE",
      "angle": { "name": "F1_Back", "roll": 0.0, "pitch": 0.0, "yaw": 0.0 },
      "input_file": "Step002.k",
      "dynain_source": "Step001/dynain"
    },
    {
      "step_number": 3,
      "mode": "DROP",
      "template": "DROP_CUMULATIVE",
      "angle": { "name": "F1_Back", "roll": 0.0, "pitch": 0.0, "yaw": 0.0 },
      "input_file": "Step003.k",
      "dynain_source": "Step002/dynain"
    }
  ]
}
```

---

## Test_003: 6면 Cyclic 3회 낙하

**총 runid 개수**: 6개 (Face만)
**Steps per runid**: 3 (순환 각도)

### 디렉토리 예시

```
/data/Test_003_6Faces_Cyclic/
├── runid_00001/ (F1_Back 시작)
│   ├── metadata.json
│   ├── Step001/ (F1_Back, Roll=0.0°)
│   ├── Step002/ (F2_Front, Roll=180.0°)    # Cyclic 믹싱
│   └── Step003/ (F3_Right, Pitch=-90.0°)
├── runid_00002/ (F2_Front 시작)
│   ├── metadata.json
│   ├── Step001/ (F2_Front, Roll=180.0°)
│   ├── Step002/ (F3_Right, Pitch=-90.0°)
│   └── Step003/ (F4_Left, Pitch=90.0°)
...
```

**Cyclic 각도 믹싱**: 각 runid는 다른 시작 각도에서 시작하여 순환 패턴으로 낙하 각도가 변경됩니다.

---

## Test_004: Pitch 각도 스윕

**총 runid 개수**: 181개 (Pitch -90° ~ +90°, 1° 간격)
**Steps per runid**: 1

### 디렉토리 예시

```
/data/Test_004_Pitching_Sweep/
├── runid_00001/ (Pitch_-90.0, Roll=0.0°, Pitch=-90.0°)
│   ├── metadata.json
│   └── Step001/
├── runid_00002/ (Pitch_-89.0, Roll=0.0°, Pitch=-89.0°)
│   ├── metadata.json
│   └── Step001/
...
├── runid_00091/ (Pitch_+0.0, Roll=0.0°, Pitch=0.0°)  # 수평
│   ├── metadata.json
│   └── Step001/
...
├── runid_00181/ (Pitch_+90.0, Roll=0.0°, Pitch=+90.0°)
│   ├── metadata.json
│   └── Step001/
```

**각도 분포**: Pitch 각도만 -90° ~ +90° 범위에서 1° 간격으로 변화, Roll과 Yaw는 0° 고정

---

## Test_005: Fibonacci Lattice 100방향

**총 runid 개수**: 100개 (구면 균일분포)
**Steps per runid**: 1

### 디렉토리 예시

```
/data/Test_005_Fibonacci_100/
├── runid_00001/ (P0001, Roll=0.0°, Pitch=-90.0°)
│   ├── metadata.json
│   └── Step001/
├── runid_00002/ (P0002, Roll=137.5°, Pitch=-85.8°)
│   ├── metadata.json
│   └── Step001/
├── runid_00003/ (P0003, Roll=-85.0°, Pitch=-81.7°)
│   ├── metadata.json
│   └── Step001/
...
├── runid_00100/ (P0100, Roll=0.0°, Pitch=90.0°)
│   ├── metadata.json
│   └── Step001/
```

**알고리즘**: Fibonacci Spiral을 사용하여 구형 표면에 거의 완벽하게 균일 분포된 100개 방향 생성

---

## 실제 디렉토리 생성

### 예제 구조 생성 (테스트용)

```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests

# 각 테스트의 예제 구조 생성 (처음 3개 runid만)
python3 create_example_structure.py \
    Test_001_Full26_1Step/runner_config.json \
    /tmp/example_Test_001 \
    3
```

### 실제 시뮬레이션 실행

```bash
cd Test_001_Full26_1Step
bash run.sh
```

run.sh 스크립트는 다음을 수행:
1. `KooChainRun prepare`: scenario.json → runner_config.json 생성
2. `KooChainRun submit`: Slurm Array Job 제출

KooChainRun submit이 실행하는 작업:
1. runid 디렉토리 사전 생성 (`runid_00001`, `runid_00002`, ...)
2. 각 runid에 metadata.json 저장
3. Slurm Array Job 제출 (Step별 dependency 설정)

---

## metadata.json 활용

각 runid의 metadata.json은 다음 정보를 포함:

- **runid**: 고유 식별자 (runid_00001, runid_00002, ...)
- **doe_index**: DOE 케이스 인덱스 (0부터 시작)
- **scenario_name**: 시나리오 이름
- **total_steps**: 총 Step 수
- **base_angle**: 기준 각도 (첫 Step 각도)
- **steps**: 각 Step의 상세 정보
  - step_number: Step 번호
  - mode: 실행 모드 (DROP, DYNAIN_TO_INITIAL 등)
  - template: 템플릿 타입 (DROP_FIRST, DROP_CUMULATIVE)
  - angle: 각도 정보 (name, roll, pitch, yaw)
  - input_file: 입력 파일명
  - dynain_source: DYNAIN 소스 경로 (Step 2+)

이 정보는 KooMeshModifier와 LS-DYNA 실행 시 사용되어 올바른 각도로 모델을 회전하고 시뮬레이션을 수행합니다.

---

**생성일**: 2026-01-29
**버전**: 1.0
