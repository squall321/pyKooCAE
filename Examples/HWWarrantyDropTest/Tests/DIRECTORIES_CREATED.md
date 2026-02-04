# 생성된 시뮬레이션 디렉토리

각 테스트 시나리오의 MinimumModel.k를 사용하여 실제 시뮬레이션 디렉토리 구조를 생성했습니다.

## 생성된 디렉토리 요약

| 테스트 | runid 개수 | Steps/runid | 총 Step 디렉토리 | 용도 |
|--------|-----------|-------------|----------------|------|
| Test_001_Full26_1Step | 26 | 1 | 26 | 26방향 1회 낙하 |
| Test_002_Full26_3Step | 26 | 3 | 78 | 26방향 3회 연속 낙하 (same angle) |
| Test_003_6Faces_Cyclic | 6 | 3 | 18 | 6면 3회 낙하 (cyclic angle) |
| Test_004_Pitching_Sweep | 181 | 1 | 181 | Pitch -90° ~ +90° (1° 간격) |
| Test_005_Fibonacci_100 | 100 | 1 | 100 | Fibonacci 100방향 균일분포 |

**총 runid 개수**: 339개
**총 Step 디렉토리**: 403개

---

## 디렉토리 위치

모든 디렉토리는 `/data` 아래에 생성되었습니다:

```
/data/
├── Test_001_Full26_1Step/
│   ├── runid_00001/ ~ runid_00026/
│   │   ├── metadata.json
│   │   └── Step001/
├── Test_002_Full26_3Step/
│   ├── runid_00001/ ~ runid_00026/
│   │   ├── metadata.json
│   │   ├── Step001/
│   │   ├── Step002/
│   │   └── Step003/
├── Test_003_6Faces_Cyclic/
│   ├── runid_00001/ ~ runid_00006/
│   │   ├── metadata.json
│   │   ├── Step001/
│   │   ├── Step002/
│   │   └── Step003/
├── Test_004_Pitching_Sweep/
│   ├── runid_00001/ ~ runid_00181/
│   │   ├── metadata.json
│   │   └── Step001/
└── Test_005_Fibonacci_100/
    ├── runid_00001/ ~ runid_00100/
        ├── metadata.json
        └── Step001/
```

---

## Test_001: 26방향 1회 낙하

**경로**: `/data/Test_001_Full26_1Step`
**runid 개수**: 26 (Face 6 + Edge 12 + Corner 8)
**각도 믹싱**: same_angle (단일 낙하이므로 해당 없음)

### 예시 runid

```bash
$ ls /data/Test_001_Full26_1Step/
runid_00001  runid_00002  runid_00003  ...  runid_00026
```

### metadata.json 예시

```bash
$ cat /data/Test_001_Full26_1Step/runid_00001/metadata.json
```

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
  "steps": [...]
}
```

---

## Test_002: 26방향 3회 연속 낙하

**경로**: `/data/Test_002_Full26_3Step`
**runid 개수**: 26
**각도 믹싱**: same_angle (동일 각도 3회 반복)

### 누적 낙하 구조

각 runid는 3개의 Step 디렉토리를 가집니다:
- **Step001**: DROP_FIRST (첫 낙하)
- **Step002**: DROP_CUMULATIVE (Step001의 변형 상태에서 2차 낙하)
- **Step003**: DROP_CUMULATIVE (Step002의 변형 상태에서 3차 낙하)

### metadata.json 특징

```json
{
  "steps": [
    {
      "step_number": 1,
      "template": "DROP_FIRST",
      "angle": {"name": "F1_Back", "roll": 0.0, ...},
      "dynain_source": null
    },
    {
      "step_number": 2,
      "template": "DROP_CUMULATIVE",
      "angle": {"name": "F1_Back", "roll": 0.0, ...},
      "dynain_source": "Step001/dynain"
    },
    {
      "step_number": 3,
      "template": "DROP_CUMULATIVE",
      "angle": {"name": "F1_Back", "roll": 0.0, ...},
      "dynain_source": "Step002/dynain"
    }
  ]
}
```

**주의**: Step 2와 Step 3는 `dynain_source`를 통해 이전 Step의 변형 상태를 받아옵니다.

---

## Test_003: 6면 Cyclic 3회 낙하

**경로**: `/data/Test_003_6Faces_Cyclic`
**runid 개수**: 6 (Face만)
**각도 믹싱**: cyclic (각 Step마다 다음 각도로 순환)

### Cyclic 각도 패턴

각 runid는 서로 다른 시작 각도에서 시작하여 순환합니다:

**runid_00001 (F1_Back 시작)**:
- Step 1: F1_Back (Roll=0.0°)
- Step 2: F2_Front (Roll=180.0°)
- Step 3: F3_Right (Pitch=-90.0°)

**runid_00002 (F2_Front 시작)**:
- Step 1: F2_Front (Roll=180.0°)
- Step 2: F3_Right (Pitch=-90.0°)
- Step 3: F4_Left (Pitch=90.0°)

**runid_00003 (F3_Right 시작)**:
- Step 1: F3_Right (Pitch=-90.0°)
- Step 2: F4_Left (Pitch=90.0°)
- Step 3: F5_Top (Pitch=90.0°, Roll=90.0°)

... (순환 계속)

### metadata.json 예시

```bash
$ cat /data/Test_003_6Faces_Cyclic/runid_00001/metadata.json
```

Step마다 **다른 각도**가 적용된 것을 확인할 수 있습니다:

```json
{
  "base_angle": {"name": "F1_Back", ...},
  "steps": [
    {"step_number": 1, "angle": {"name": "F1_Back", "roll": 0.0, "pitch": 0.0}},
    {"step_number": 2, "angle": {"name": "F2_Front", "roll": 180.0, "pitch": 0.0}},
    {"step_number": 3, "angle": {"name": "F3_Right", "roll": 0.0, "pitch": -90.0}}
  ]
}
```

---

## Test_004: Pitch 각도 스윕

**경로**: `/data/Test_004_Pitching_Sweep`
**runid 개수**: 181 (Pitch -90° ~ +90°, 1° 간격)
**각도 믹싱**: same_angle (단일 낙하)

### 각도 분포

- **runid_00001**: Pitch = -90.0° (수직 아래)
- **runid_00091**: Pitch = 0.0° (수평)
- **runid_00181**: Pitch = +90.0° (수직 위)

Roll과 Yaw는 모두 0° 고정.

---

## Test_005: Fibonacci Lattice 100방향

**경로**: `/data/Test_005_Fibonacci_100`
**runid 개수**: 100
**각도 믹싱**: same_angle (단일 낙하)

### Fibonacci Spiral 알고리즘

구형 표면에 거의 완벽하게 균일 분포된 100개 방향을 Fibonacci Spiral 알고리즘으로 생성했습니다.

각 runid의 각도는 황금비(Golden Ratio)를 사용하여 계산되므로 극점 집중 없이 균일하게 분포됩니다.

---

## 생성 과정

1. **scenario.json 업데이트**: 각 테스트의 `template` 경로를 로컬 `MinimumModel.k`로 변경
2. **runner_config.json 생성**: `KooChainRun prepare` 명령으로 실행 설정 생성
3. **디렉토리 생성**: `create_directories.py` 스크립트로 runid 및 Step 디렉토리 생성
4. **metadata.json 생성**: 각 runid의 각도 정보와 Step 시퀀스를 metadata.json에 저장

---

## 실행 명령

각 테스트 디렉토리에서 실제 시뮬레이션을 실행하려면:

```bash
cd /opt/pyKooCAE/Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step
bash run.sh
```

run.sh는 다음을 수행합니다:
1. `KooChainRun prepare`: scenario.json → runner_config.json
2. `KooChainRun submit`: Slurm Array Job 제출 (시뮬레이션 실행)

---

## 버그 수정 내역

디렉토리 생성 과정에서 다음 버그들이 발견되어 수정되었습니다:

### 1. doe_index 중복 버그
**파일**: [Runner/CumulativeDesigner.py:152](../../../Runner/CumulativeDesigner.py#L152)
**문제**: Tolerance가 없을 때 모든 케이스의 doe_index가 0으로 설정됨
**해결**: 각 케이스에 고유한 doe_index (0, 1, 2, ...) 부여

### 2. Cyclic 각도 믹싱 버그
**파일**: [Runner/CumulativeDesigner.py:187](../../../Runner/CumulativeDesigner.py#L187)
**문제**: `base_angles_for_mixing`이 단일 base_name 그룹만 포함하여 cyclic 작동 안 함
**해결**: 모든 base 각도를 `all_base_angles`로 수집하여 cyclic에 사용

### 3. fibonacci_lattice 파라미터 호환성
**파일**: [Runner/CumulativeDesigner.py:252](../../../Runner/CumulativeDesigner.py#L252)
**문제**: scenario.json에서 `num_directions` 사용 시 인식 안 됨
**해결**: `num_directions`를 `num_points`의 별칭으로 허용

---

**생성일**: 2026-01-29
**도구**: KooChainRun prepare + create_directories.py
**총 디렉토리 크기**: ~0 bytes (시뮬레이션 파일 없음, 구조만 생성)
