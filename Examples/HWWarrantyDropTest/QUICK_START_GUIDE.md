# 누적 낙하 자동화 - Quick Start 가이드

**작성일**: 2026-01-23
**버전**: 2.0 (KooChainRun)
**상태**: ✅ 전체 시스템 구현 완료

---

## 🎯 개요

이 가이드는 **KooChainRun** CLI를 사용하여 누적 낙하 자동화 시스템을 **5분 안에** 실행할 수 있도록 도와줍니다.

### 시스템 구성

```
scenario.json → koocr prepare → runner_config.json → koocr submit → Slurm 실행
```

---

## 📦 설치 및 준비

### KooChainRun CLI 확인

```bash
# koocr 실행 파일 확인
ls -l /opt/pyKooCAE/koocr

# 실행 권한 확인
chmod +x /opt/pyKooCAE/koocr

# PATH에 추가 (선택사항)
export PATH="/opt/pyKooCAE:$PATH"

# 버전 확인
/opt/pyKooCAE/koocr --version
```

### Python 의존성

```bash
# 필수 패키지 (이미 설치되어 있어야 함)
python3 -c "import numpy; print('numpy OK')"
```

---

## 🚀 빠른 시작 (3분)

### Step 1: 사용자 JSON 작성

**예시**: 3회 연속 낙하 (F1_Back, same_angle 전략)

```json
{
  "project_name": "MyFirstCumulativeDrop",
  "base_dir": "/path/to/working/directory",

  "scenarios": [
    {
      "scenario_name": "Test_3Steps",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "cuboid_geometry": {
          "include_faces": true,
          "include_edges": false,
          "include_corners": false
        }
      },
      "cumulative": {
        "num_steps": 3,
        "mode_sequence": ["DROP", "DROP", "DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

**저장**: `my_config.json`

---

### Step 2: KooChainRun으로 설정 준비

```bash
koocr prepare my_config.json
```

**출력**:
```
================================================================================
KooChainRun - Prepare Configuration
================================================================================
Scenario: /path/to/my_config.json
Output:   /path/to/runner_config.json

✅ Successfully generated: /path/to/runner_config.json
```

---

### Step 3: 작업 제출

```bash
koocr submit runner_config.json \
    --nodes 2 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

**출력**:
```
================================================================================
KooChainRun - Submit Jobs
================================================================================
Config:         /path/to/runner_config.json
Nodes:          2
Jobs per node:  4
CPUs per job:   16
Total parallel: 8

1️⃣  runid 디렉토리 생성 중...
✅ 26개 runid 디렉토리 생성 완료

2️⃣  Slurm Array Job 제출 중...
✅ Step 1 제출 완료 (Job ID: 123456)

================================================================================
✅ Jobs submitted successfully
================================================================================

Next steps:
  Check status:    koocr status /path/to/runner_config.json
  Collect results: koocr collect /path/to/runner_config.json
```

---

### Step 4: 진행 상황 확인

```bash
koocr status
```

**출력**:
```
====================================================================================================
🚀 Cumulative Scenario Executor - MyFirstCumulativeDrop
====================================================================================================

총 시나리오 수: 1

────────────────────────────────────────────────────────────────────────────────────────────────────
[1/1] 시나리오: Test_3Steps (Test_3Steps_S003)
────────────────────────────────────────────────────────────────────────────────────────────────────
총 Step 수: 3

  ┌─ Step 1 ─────────────────────────────────────────────────
  │ Template: DROP_FIRST
  │ Mode: DROP
  │ Angle: F1_Back (Roll=0.00, Pitch=0.00, Yaw=0.00)
  │ Input: Step001.k
  │ Output: Step001
  └───────────────────────────────────────────────────────────────────────
  [DRY-RUN] Step 1 시뮬레이션 스킵

  ... (Step 2, 3 동일)

✅ 모든 시나리오 실행 완료!
```

#### 3-3. 특정 시나리오만 실행

```bash
python3 Runner/SimplifiedExecutor.py runner_config.json --scenario=Test_3Steps_S003 --dry-run
```

---

## 📚 사용 예시

### 예시 1: Cuboid 3회 누적 낙하 (same_angle)

**시나리오**: F1_Back을 3회 반복 낙하

```json
{
  "scenario_name": "Cuboid_3Steps_SameAngle",
  "angle_source": {
    "source_type": "cuboid_geometry",
    "cuboid_geometry": {
      "include_faces": true,
      "include_edges": true,
      "include_corners": true
    }
  },
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "same_angle"
    }
  }
}
```

**결과**:
- Step 1: F1_Back (Roll=0°, Pitch=0°) - DROP_FIRST
- Step 2: F1_Back (Roll=0°, Pitch=0°) - DROP_CUMULATIVE
- Step 3: F1_Back (Roll=0°, Pitch=0°) - DROP_CUMULATIVE

---

### 예시 2: Fibonacci 5회 누적 낙하 (cyclic)

**시나리오**: Fibonacci 26 포인트, cyclic 전략 (offset=1)

```json
{
  "scenario_name": "Fibonacci_5Steps_Cyclic",
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {
      "num_points": 26
    }
  },
  "cumulative": {
    "num_steps": 5,
    "mode_sequence": ["DROP", "DROP", "DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "cyclic",
      "cyclic_offset": 1
    }
  }
}
```

**결과**:
- Step 1: P0001 - DROP_FIRST
- Step 2: P0002 - DROP_CUMULATIVE
- Step 3: P0003 - DROP_CUMULATIVE
- Step 4: P0004 - DROP_CUMULATIVE
- Step 5: P0005 - DROP_CUMULATIVE

---

### 예시 3: Case txt 파일 + Opposite 전략

**시나리오**: 표준 Case txt 파일 사용, opposite 전략

```json
{
  "scenario_name": "CaseTxt_4Steps_Opposite",
  "angle_source": {
    "source_type": "case_txt_file",
    "case_txt_file": {
      "file_path": "FullAngleDrop/26case_6F12E8C_cuboid.txt"
    }
  },
  "cumulative": {
    "num_steps": 4,
    "mode_sequence": ["DROP", "DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "opposite"
    }
  }
}
```

**결과**:
- Step 1: F1_Back (Roll=0°, Pitch=0°) - DROP_FIRST
- Step 2: F1_Back_OPPOSITE (Roll=180°, Pitch=0°) - DROP_CUMULATIVE
- Step 3: F1_Back (Roll=0°, Pitch=0°) - DROP_CUMULATIVE
- Step 4: F1_Back_OPPOSITE (Roll=180°, Pitch=0°) - DROP_CUMULATIVE

---

### 예시 4: 열응력 → 낙하 전환

**시나리오**: 열응력 2회 → 낙하 1회

```json
{
  "scenario_name": "Thermal_To_Drop",
  "angle_source": {
    "source_type": "cuboid_geometry",
    "cuboid_geometry": {
      "include_faces": true,
      "include_edges": false,
      "include_corners": false
    }
  },
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["THERM", "THERM", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "same_angle"
    }
  }
}
```

**결과**:
- Step 1: F1_Back - THERMAL_FIRST
- Step 2: F1_Back - THERMAL_CUMULATIVE
- Step 3: F1_Back - THERMAL_TO_DROP

---

### 예시 5: Tolerance/DOE 적용 (LHS)

**시나리오**: Fibonacci + Tolerance ±2° + LHS 5 samples

```json
{
  "scenario_name": "Fibonacci_WithTolerance_LHS",
  "angle_source": {
    "source_type": "fibonacci_lattice",
    "fibonacci_lattice": {
      "num_points": 10
    }
  },
  "tolerance": {
    "roll": {"tolerance": 2.0},
    "pitch": {"tolerance": 2.0},
    "yaw": {"tolerance": 1.0},
    "doe_type": "lhs",
    "doe_count": 5
  },
  "cumulative": {
    "num_steps": 3,
    "mode_sequence": ["DROP", "DROP", "DROP"],
    "base_angle_index": 0,
    "angle_mixing": {
      "strategy": "cyclic",
      "cyclic_offset": 1
    }
  }
}
```

**결과**:
- Step 1: P0001_DOE001 (Roll=-180.08°, Pitch=-91.61°) - DROP_FIRST
- Step 2: P0001_DOE002 (Roll=-179.57°, Pitch=-89.60°) - DROP_CUMULATIVE
- Step 3: P0001_DOE003 (Roll=-181.96°, Pitch=-89.25°) - DROP_CUMULATIVE

---

## 🔧 고급 기능

### 1. 다중 시나리오 실행

하나의 JSON에 여러 시나리오를 정의:

```json
{
  "project_name": "MultiScenarioProject",
  "scenarios": [
    {
      "scenario_name": "Scenario1",
      ...
    },
    {
      "scenario_name": "Scenario2",
      ...
    },
    {
      "scenario_name": "Scenario3",
      ...
    }
  ]
}
```

**실행**:
```bash
# 모든 시나리오 실행
python3 Runner/SimplifiedExecutor.py runner_config.json --dry-run

# 특정 시나리오만 실행
python3 Runner/SimplifiedExecutor.py runner_config.json --scenario=Scenario2 --dry-run
```

---

### 2. 5가지 각도 소스 타입

#### 2-1. Cuboid Geometry

```json
"angle_source": {
  "source_type": "cuboid_geometry",
  "cuboid_geometry": {
    "include_faces": true,
    "include_edges": true,
    "include_corners": true
  }
}
```

#### 2-2. Fibonacci Lattice

```json
"angle_source": {
  "source_type": "fibonacci_lattice",
  "fibonacci_lattice": {
    "num_points": 413
  }
}
```

#### 2-3. Pitching Sweep

```json
"angle_source": {
  "source_type": "pitching_sweep",
  "pitching_sweep": {
    "pitch_min": -90.0,
    "pitch_max": 90.0,
    "pitch_step": 10.0,
    "roll_fixed": 0.0,
    "yaw_fixed": 0.0
  }
}
```

#### 2-4. Rolling Sweep

```json
"angle_source": {
  "source_type": "rolling_sweep",
  "rolling_sweep": {
    "roll_min": -180.0,
    "roll_max": 170.0,
    "roll_step": 10.0,
    "pitch_fixed": 0.0,
    "yaw_fixed": 0.0
  }
}
```

#### 2-5. Case txt 파일

```json
"angle_source": {
  "source_type": "case_txt_file",
  "case_txt_file": {
    "file_path": "FullAngleDrop/fibonacci_10deg_413cases.txt",
    "selected_indices": [0, 1, 2, 10, 100]
  }
}
```

---

### 3. 5가지 각도 믹싱 전략

#### 3-1. same_angle (동일 각도 반복)

```json
"angle_mixing": {
  "strategy": "same_angle"
}
```

#### 3-2. cyclic (순환)

```json
"angle_mixing": {
  "strategy": "cyclic",
  "cyclic_offset": 1
}
```

#### 3-3. random (랜덤)

```json
"angle_mixing": {
  "strategy": "random",
  "random_seed": 42
}
```

#### 3-4. opposite (대칭 각도)

```json
"angle_mixing": {
  "strategy": "opposite"
}
```

#### 3-5. custom_mapping (사용자 정의)

```json
"angle_mixing": {
  "strategy": "custom_mapping",
  "custom_mapping": {
    "1": 0,
    "2": 2,
    "3": 4
  }
}
```

---

### 4. 3가지 DOE 타입

#### 4-1. LHS (Latin Hypercube Sampling) - 권장

```json
"tolerance": {
  "roll": {"tolerance": 2.0},
  "pitch": {"tolerance": 2.0},
  "yaw": {"tolerance": 1.0},
  "doe_type": "lhs",
  "doe_count": 10
}
```

#### 4-2. Grid (전체 조합)

```json
"tolerance": {
  "roll": {"tolerance": 2.0},
  "pitch": {"tolerance": 2.0},
  "doe_type": "grid",
  "doe_count": 3
}
```
**주의**: doe_count=3이면 3×3×3=27개 샘플 생성

#### 4-3. Random (랜덤)

```json
"tolerance": {
  "roll": {"tolerance": 2.0},
  "pitch": {"tolerance": 2.0},
  "doe_type": "random",
  "doe_count": 10
}
```

---

## 📂 파일 구조

### 입력 파일

```
my_project/
├── my_config.json              # 사용자 JSON 설정
├── FullAngleDrop/              # 표준 Case txt 파일 (11개)
│   ├── 26case_6F12E8C_cuboid.txt
│   ├── fibonacci_10deg_413cases.txt
│   └── ...
```

### 출력 파일

```
my_project/
├── runner_config.json          # Designer 출력 (Executor 입력)
├── Step001/                    # Step 1 결과
│   ├── Step001.k
│   ├── dynain
│   └── ...
├── Step002/                    # Step 2 결과
│   ├── Step002.k
│   ├── dynain
│   └── ...
```

---

## ⚠️ 주의사항

### 1. KooMeshModifier 연동 필요

현재 SimplifiedExecutor는 **dry-run 모드만** 지원합니다.

실제 시뮬레이션 실행을 위해서는:
- KooMeshModifier 연동 필요
- DROP_ATTITUDE, DYNAIN_TO_INITIAL, THERMAL_CYCLE 호출
- LS-DYNA 실행 및 dynain 파일 생성 대기

### 2. 경로 설정

- `base_dir`: 작업 디렉토리 절대 경로
- `file_path`: Case txt 파일 절대 경로 또는 상대 경로

### 3. 템플릿 자동 선택

템플릿은 **자동으로 선택**됩니다. JSON에 템플릿을 지정할 필요 없습니다.

---

## 🆘 문제 해결

### Q1: "파일을 찾을 수 없습니다" 오류

**원인**: 경로 설정 오류

**해결**:
```bash
# 절대 경로 사용
"file_path": "/home/user/pyKooCAE/Examples/..."

# 또는 현재 디렉토리 기준 상대 경로
"file_path": "FullAngleDrop/26case_6F12E8C_cuboid.txt"
```

### Q2: "모듈을 찾을 수 없습니다" 오류

**원인**: Python 경로 문제

**해결**:
```bash
# Runner 디렉토리에서 실행
cd /path/to/pyKooCAE
python3 Runner/CumulativeDesigner.py ...
```

### Q3: Fibonacci 포인트 개수 선택

**권장 값**:
- 26 포인트: ~40° 간격
- 103 포인트: ~20° 간격
- 413 포인트: ~10° 간격
- 1,650 포인트: ~5° 간격

---

## 📞 문의

**작성자**: koo.park
**이메일**: koo.park@samsung.com
**부서**: CAE, HE

---

## 🔗 참고 문서

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - 전체 구현 요약
- [CumulativeDrop_Context_v2.1.md](Context/CumulativeDrop_Context_v2.1.md) - 컨텍스트 문서
- [DROP_MODE_V2_PLAN.md](DROP_MODE_V2_PLAN.md) - DROP MODE V2 상세 설계

---

**버전**: 1.0
**작성일**: 2026-01-23
**상태**: ✅ 시스템 구현 완료
