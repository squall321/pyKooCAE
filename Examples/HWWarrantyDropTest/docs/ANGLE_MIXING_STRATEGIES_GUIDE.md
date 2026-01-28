# 각도 믹싱 전략 가이드 (Angle Mixing Strategies)

**작성일**: 2026-01-23
**모듈**: [AngleMixingStrategy.py](../../Runner/AngleMixingStrategy.py)

---

## 📖 개요

각도 믹싱 전략은 누적 낙하 시뮬레이션에서 **각 Step별로 어떤 각도를 사용할지** 결정하는 메커니즘입니다.

### 핵심 개념

- **Base 각도**: 초기에 생성된 기본 각도 리스트 (Fibonacci, Case txt 등)
- **DOE 확장**: Tolerance를 적용하여 각 Base 각도를 여러 개로 확장
- **누적 Step**: 3~5회 연속 낙하를 시뮬레이션
- **믹싱 전략**: 각 Step에서 어떤 각도를 선택할지 결정

---

## 🎯 5가지 믹싱 전략

| 전략 | 설명 | 사용 케이스 | 파라미터 |
|------|------|------------|----------|
| **same_angle** | 동일 각도 반복 | 단순 반복 낙하 | 없음 |
| **cyclic** | 순환 (인덱스 + offset) | 다양한 각도 조합 | `cyclic_offset` |
| **random** | 랜덤 샘플링 | 무작위 조합 | `random_seed` |
| **opposite** | 대칭 각도 교대 | 양방향 충격 | 없음 |
| **custom_mapping** | 사용자 정의 매핑 | 특수 시나리오 | `step_to_index_map` |

---

## 1️⃣ same_angle (동일 각도 반복)

### 설명

모든 Step에서 **동일한 Base 각도를 반복**합니다.

### JSON 설정

```json
{
  "angle_mixing": {
    "strategy": "same_angle"
  }
}
```

### 동작 예시

**Base 각도**: `[A, B, C, D, E]` (5개)
**num_steps**: 3

| DOE | Step 1 | Step 2 | Step 3 |
|-----|--------|--------|--------|
| A_DOE001 | A | A | A |
| A_DOE002 | A | A | A |
| B_DOE001 | B | B | B |
| C_DOE001 | C | C | C |

### 사용 케이스

- 표준 Case txt 파일 (F1_Back 26회 반복 등)
- 동일 조건 반복 검증
- 내구성 테스트

### 실제 사용 예시

```bash
# user_config.json
{
  "scenarios": [{
    "angle_source": {
      "source_type": "case_txt_file",
      "case_txt_file": {"file_path": "FullAngleDrop/standard_26cases.txt"}
    },
    "cumulative": {
      "num_steps": 3,
      "mode_sequence": ["DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {"strategy": "same_angle"}
    }
  }]
}
```

**결과**: F1_Back → F1_Back → F1_Back (26개 × 3 Steps = 78 Jobs)

---

## 2️⃣ cyclic (순환)

### 설명

Base 각도 리스트를 **순환하면서 샘플링**합니다. `cyclic_offset`만큼 인덱스를 증가시킵니다.

### JSON 설정

```json
{
  "angle_mixing": {
    "strategy": "cyclic",
    "cyclic_offset": 1
  }
}
```

### 동작 예시

**Base 각도**: `[A, B, C, D, E]` (5개)
**num_steps**: 3
**cyclic_offset**: 1

| DOE | Step 1 | Step 2 | Step 3 |
|-----|--------|--------|--------|
| A_DOE001 (idx=0) | A (0) | B (0+1) | C (0+2) |
| A_DOE002 (idx=1) | B (1) | C (1+1) | D (1+2) |
| A_DOE003 (idx=2) | C (2) | D (2+1) | E (2+2) |
| A_DOE004 (idx=3) | D (3) | E (3+1) | A (3+2, wraps) |
| A_DOE005 (idx=4) | E (4) | A (4+1, wraps) | B (4+2, wraps) |

### Wrapping (순환) 동작

인덱스가 리스트 크기를 초과하면 **0부터 다시 시작** (modulo 연산):

```
idx = (current_idx + step_number * cyclic_offset) % len(base_angles)
```

### 사용 케이스

- Fibonacci Lattice 누적 낙하
- 다양한 각도 조합 테스트
- 공간적으로 균등 분포된 충격

### 실제 사용 예시

```bash
# user_config.json
{
  "scenarios": [{
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": {"num_points": 10}
    },
    "tolerance": {
      "roll": {"tolerance": 1.0},
      "pitch": {"tolerance": 1.0},
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
  }]
}
```

**결과**: 10 Fibonacci × 5 DOE × 3 Steps = 150 Jobs
**검증 보고서**: [WORKFLOW_VERIFICATION_REPORT.md](WORKFLOW_VERIFICATION_REPORT.md)

---

## 3️⃣ random (랜덤)

### 설명

Step 2부터 **랜덤하게 Base 각도를 샘플링**합니다. Step 1은 항상 자기 자신입니다.

### JSON 설정

```json
{
  "angle_mixing": {
    "strategy": "random",
    "random_seed": 42
  }
}
```

### 동작 예시

**Base 각도**: `[A, B, C, D, E]` (5개)
**num_steps**: 4
**random_seed**: 42 (재현성)

| DOE | Step 1 | Step 2 | Step 3 | Step 4 |
|-----|--------|--------|--------|--------|
| A_DOE001 | A | C (random) | E (random) | B (random) |
| B_DOE001 | B | D (random) | A (random) | E (random) |
| C_DOE001 | C | B (random) | C (random) | D (random) |

### 파라미터

- **random_seed** (optional): 난수 시드 (재현성 보장)
  - 지정하지 않으면 매번 다른 결과

### 사용 케이스

- 무작위 충격 시나리오
- Monte Carlo 시뮬레이션
- 탐색적 분석

### 실제 사용 예시

```bash
# user_config.json
{
  "scenarios": [{
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": {"num_points": 26}
    },
    "cumulative": {
      "num_steps": 5,
      "mode_sequence": ["DROP", "DROP", "DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {
        "strategy": "random",
        "random_seed": 42
      }
    }
  }]
}
```

**결과**: 26개 × 5 Steps = 130 Jobs (랜덤 각도 조합)

---

## 4️⃣ opposite (대칭 각도)

### 설명

Step 1과 Step 2를 **구면 대칭 각도로 교대**합니다.

### 대칭 각도 계산

```python
opposite_roll = (roll + 180.0) % 360.0 - 180.0
opposite_pitch = -pitch
opposite_yaw = yaw  # 보통 0
```

### JSON 설정

```json
{
  "angle_mixing": {
    "strategy": "opposite"
  }
}
```

### 동작 예시

**Base 각도**: `F1_Back (Roll=-180°, Pitch=-90°)`
**num_steps**: 4

| DOE | Step 1 | Step 2 | Step 3 | Step 4 |
|-----|--------|--------|--------|--------|
| F1_Back | F1_Back (-180°, -90°) | F1_Back_OPP (0°, 90°) | F1_Back | F1_Back_OPP |

### 사용 케이스

- 양방향 충격 테스트
- 대칭 조건 검증
- 반복 충격 내구성

### 실제 사용 예시

```bash
# user_config.json
{
  "scenarios": [{
    "angle_source": {
      "source_type": "case_txt_file",
      "case_txt_file": {"file_path": "FullAngleDrop/standard_26cases.txt"}
    },
    "cumulative": {
      "num_steps": 4,
      "mode_sequence": ["DROP", "DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {"strategy": "opposite"}
    }
  }]
}
```

**결과**: F1_Back → F1_Back_OPPOSITE → F1_Back → F1_Back_OPPOSITE (26개 × 4 Steps = 104 Jobs)

---

## 5️⃣ custom_mapping (사용자 정의)

### 설명

Step별로 사용할 각도 인덱스를 **사용자가 직접 지정**합니다.

### JSON 설정

```json
{
  "angle_mixing": {
    "strategy": "custom_mapping",
    "step_to_index_map": [0, 5, 10, 3, 7]
  }
}
```

### 동작 예시

**Base 각도**: `[A, B, C, ..., Z]` (26개)
**step_to_index_map**: `[0, 5, 10, 3, 7]`
**num_steps**: 5

| DOE | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 |
|-----|--------|--------|--------|--------|--------|
| All | A (idx=0) | F (idx=5) | K (idx=10) | D (idx=3) | H (idx=7) |

### 사용 케이스

- 특정 각도 시퀀스 지정
- 실험 설계 (DOE)
- 복잡한 시나리오

### 실제 사용 예시

```bash
# user_config.json
{
  "scenarios": [{
    "angle_source": {
      "source_type": "case_txt_file",
      "case_txt_file": {"file_path": "FullAngleDrop/standard_26cases.txt"}
    },
    "cumulative": {
      "num_steps": 3,
      "mode_sequence": ["DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {
        "strategy": "custom_mapping",
        "step_to_index_map": [0, 12, 25]
      }
    }
  }]
}
```

**결과**: F1_Back (0) → F3_Right (12) → E4_Bottom (25) (26개 × 3 Steps = 78 Jobs)

---

## 🔍 전략 선택 가이드

### 사용 목적별 추천

| 목적 | 추천 전략 | 이유 |
|------|----------|------|
| 표준 반복 낙하 | **same_angle** | 가장 단순, 재현성 높음 |
| Fibonacci 누적 낙하 | **cyclic** | 공간적으로 균등 분포 |
| 무작위 조합 탐색 | **random** | 다양한 시나리오 커버 |
| 양방향 충격 | **opposite** | 대칭 조건 검증 |
| 특수 시퀀스 | **custom_mapping** | 완전한 제어 |

### 각도 소스별 추천

| 각도 소스 | 추천 전략 | 설명 |
|----------|----------|------|
| **case_txt_file** | `same_angle` | 표준 26 케이스 반복 |
| **fibonacci_lattice** | `cyclic` | 균등 분포 유지 |
| **cuboid_geometry** | `same_angle` | F/E/C 정의 명확 |
| **pitching_sweep** | `cyclic` | Pitch 범위 커버 |
| **rolling_sweep** | `cyclic` | Roll 범위 커버 |

---

## 💡 실전 예시

### 예시 1: Fibonacci 1000포인트 + Cyclic

```json
{
  "project_name": "Large_Scale_Fibonacci",
  "scenarios": [{
    "scenario_name": "Fibonacci_1000_Cyclic",
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": {"num_points": 1000}
    },
    "tolerance": {
      "roll": {"tolerance": 1.0},
      "pitch": {"tolerance": 1.0},
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
  }]
}
```

**결과**: 1,000 × 5 DOE × 3 Steps = **15,000 Jobs**

---

### 예시 2: Standard 26 Cases + Same Angle

```json
{
  "project_name": "Standard_26_Repeat",
  "scenarios": [{
    "scenario_name": "Standard_26_3x",
    "angle_source": {
      "source_type": "case_txt_file",
      "case_txt_file": {
        "file_path": "FullAngleDrop/standard_26cases.txt"
      }
    },
    "cumulative": {
      "num_steps": 3,
      "mode_sequence": ["DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {"strategy": "same_angle"}
    }
  }]
}
```

**결과**: 26 × 3 Steps = **78 Jobs**

---

### 예시 3: Fibonacci 10 + DOE 5 + Random

```json
{
  "project_name": "Random_Mixing_Test",
  "scenarios": [{
    "scenario_name": "Fibonacci_10_Random",
    "angle_source": {
      "source_type": "fibonacci_lattice",
      "fibonacci_lattice": {"num_points": 10}
    },
    "tolerance": {
      "roll": {"tolerance": 1.0},
      "pitch": {"tolerance": 1.0},
      "doe_type": "lhs",
      "doe_count": 5
    },
    "cumulative": {
      "num_steps": 4,
      "mode_sequence": ["DROP", "DROP", "DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {
        "strategy": "random",
        "random_seed": 42
      }
    }
  }]
}
```

**결과**: 10 × 5 DOE × 4 Steps = **200 Jobs** (랜덤 조합)

---

## 🛠️ 구현 세부사항

### 모듈 위치

[AngleMixingStrategy.py](../../Runner/AngleMixingStrategy.py)

### 핵심 함수

```python
def generate_cumulative_angle_sequence(
    base_angles: List[Tuple[str, float, float, float]],
    num_steps: int,
    config: CumulativeAngleConfig,
    base_angle_index: int
) -> List[Tuple[str, float, float, float]]:
    """
    누적 각도 시퀀스 생성

    Args:
        base_angles: Base 각도 리스트
        num_steps: 총 Step 수
        config: 믹싱 전략 설정
        base_angle_index: 시작 각도 인덱스

    Returns:
        각 Step별 각도 리스트 (길이 = num_steps)
    """
```

### 데이터 클래스

```python
@dataclass
class CumulativeAngleConfig:
    mixing_strategy: MixingStrategy
    cyclic_offset: int = 1
    random_seed: Optional[int] = None
    step_to_index_map: Optional[List[int]] = None
```

---

## ⚠️ 주의사항

### 1. DOE와의 관계

- 믹싱 전략은 **각 DOE마다 독립적으로 적용**됩니다
- 예: Fibonacci 10 × DOE 5 = 50개 DOE → 각 DOE가 자신의 Step 시퀀스를 가짐

### 2. base_angle_index

- **사용 안 함** (현재 구현에서는 각 DOE의 인덱스를 자동 계산)
- JSON에 지정해도 무시됨

### 3. Cyclic Wrapping

- `cyclic_offset`이 클 경우 **빠르게 순환**합니다
- 예: offset=5, num_points=10 → 2번 순환 후 모두 커버

### 4. Random 재현성

- `random_seed`를 지정하지 않으면 **매번 다른 결과**
- 프로덕션에서는 항상 seed 지정 권장

---

## 📊 성능 비교

### 계산 복잡도

| 전략 | 시간 복잡도 | 공간 복잡도 |
|------|------------|------------|
| same_angle | O(1) | O(1) |
| cyclic | O(1) | O(1) |
| random | O(1) | O(1) |
| opposite | O(1) | O(1) |
| custom_mapping | O(1) | O(num_steps) |

**결론**: 모든 전략이 매우 효율적 (O(1))

---

## 📚 관련 문서

- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - 전체 시스템 개요
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - 빠른 시작 가이드
- [WORKFLOW_VERIFICATION_REPORT.md](WORKFLOW_VERIFICATION_REPORT.md) - Cyclic 전략 검증
- [Context/CumulativeDrop_Context_v2.1.md](Context/CumulativeDrop_Context_v2.1.md) - 설계 문맥
- [DROP_MODE_V2_PLAN.md](DROP_MODE_V2_PLAN.md) - V2 계획서

---

## 🔗 코드 예시

### Python 직접 사용

```python
from Runner.AngleMixingStrategy import (
    generate_cumulative_angle_sequence,
    CumulativeAngleConfig,
    MixingStrategy
)

# Base 각도 준비
base_angles = [
    ("F1_Back", -180.0, -90.0, 0.0),
    ("F2_Front", 0.0, 90.0, 0.0),
    ("F3_Right", 90.0, 0.0, 0.0),
    ("F4_Left", -90.0, 0.0, 0.0),
]

# Cyclic 전략
config = CumulativeAngleConfig(
    mixing_strategy=MixingStrategy.CYCLIC,
    cyclic_offset=1
)

# Step 시퀀스 생성 (4 Steps)
sequence = generate_cumulative_angle_sequence(
    base_angles, num_steps=4, config=config, base_angle_index=0
)

# 결과
# Step 1: F1_Back (idx=0)
# Step 2: F2_Front (idx=1)
# Step 3: F3_Right (idx=2)
# Step 4: F4_Left (idx=3)
```

---

**작성자**: koo.park
**버전**: 1.0
**날짜**: 2026-01-23
