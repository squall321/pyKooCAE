# 커스텀 시나리오 예제 (Custom Scenarios)

**작성일**: 2026-01-23
**목적**: 사용자 정의 낙하 시나리오 예제 모음

---

## 📖 개요

이 폴더에는 **높이, 초기속도, 각속도 등 다양한 파라미터를 변경**한 커스텀 낙하 시나리오 예제가 포함되어 있습니다.

### 핵심 메시지

> **표준 11개 파일에 국한되지 않습니다!**
>
> 어떤 txt 파일이든 만들어서 바로 사용할 수 있습니다.

---

## 📁 포함된 파일

### Case txt 파일 (4개)

| 파일 | 케이스 수 | 변경 파라미터 | 설명 |
|------|----------|-------------|------|
| [custom_height_variation.txt](custom_height_variation.txt) | 4 | Height | 1m, 1.5m, 2m, 3m 높이 변경 |
| [custom_initial_velocity.txt](custom_initial_velocity.txt) | 4 | InitialVelocityX | 0, 5, 10, 15 m/s 초기 속도 |
| [custom_angular_velocity.txt](custom_angular_velocity.txt) | 5 | InitialAngularVelocityX/Y/Z | X, Y, Z축 회전 낙하 |
| [custom_combined_conditions.txt](custom_combined_conditions.txt) | 4 | Height + Velocity + AngularVelocity | 복합 조건 시나리오 |

### JSON 설정 파일 (5개)

| 파일 | 대응 txt | Steps | 총 Jobs |
|------|---------|-------|---------|
| [scenario_height_variation.json](scenario_height_variation.json) | custom_height_variation.txt | 3 | 12 (4 × 3) |
| [scenario_initial_velocity.json](scenario_initial_velocity.json) | custom_initial_velocity.txt | 2 | 8 (4 × 2) |
| [scenario_angular_velocity.json](scenario_angular_velocity.json) | custom_angular_velocity.txt | 2 | 10 (5 × 2) |
| [scenario_combined_conditions.json](scenario_combined_conditions.json) | custom_combined_conditions.txt | 3 | 12 (4 × 3) |
| [scenario_fibonacci_doe_cyclic.json](scenario_fibonacci_doe_cyclic.json) | (Fibonacci 생성) | 3 | 150 (10×5×3) |

---

## 🚀 사용 방법

### 1단계: txt 파일 확인

원하는 시나리오의 txt 파일을 열어봅니다.

```bash
cat custom_height_variation.txt
```

### 2단계: Designer 실행

```bash
cd /home/koopark/serviceApptainers/appt313/opt/pyKooCAE

python3 Runner/CumulativeDesigner.py \
  Examples/HWWarrantyDropTest/CustomScenarios/scenario_height_variation.json \
  -o /tmp/runner_config.json
```

### 3단계: 결과 확인

```bash
# 생성된 Step 확인
grep -c "step_number" /tmp/runner_config.json

# 각도 정보 확인
jq '.scenarios[0].steps[] | {step: .step_number, angle: .angle.name, height: .angle.height}' /tmp/runner_config.json
```

### 4단계: 실행 (Optional)

```bash
# Dry-run 테스트
python3 Runner/SimplifiedExecutor.py /tmp/runner_config.json --dry-run

# 실제 실행 (Slurm Array Job)
python3 Runner/LargeScaleDOEManager.py /tmp/runner_config.json --data-root=/data
```

---

## 📊 시나리오별 상세 정보

### 1. 높이 변경 (Height Variation)

**파일**: [custom_height_variation.txt](custom_height_variation.txt)

**목적**: 다양한 낙하 높이에서의 충격 비교

**케이스**:
```
Height_1m     : 1000mm (1.0m)
Height_1.5m   : 1500mm (1.5m, 표준)
Height_2m     : 2000mm (2.0m)
Height_3m     : 3000mm (3.0m)
```

**사용 예시**:
```bash
python3 Runner/CumulativeDesigner.py \
  Examples/HWWarrantyDropTest/CustomScenarios/scenario_height_variation.json \
  -o /tmp/height_test.json
```

**결과**: 4 케이스 × 3 Steps = 12 Jobs

---

### 2. 초기 속도 (Initial Velocity)

**파일**: [custom_initial_velocity.txt](custom_initial_velocity.txt)

**목적**: 운동 중 낙하 시뮬레이션 (운송 중 낙하 등)

**케이스**:
```
Static_Drop    : 0 m/s (정적 낙하)
Moving_5mps    : 5 m/s (5000 mm/s, X축)
Moving_10mps   : 10 m/s (10000 mm/s, X축)
Moving_15mps   : 15 m/s (15000 mm/s, X축)
```

**물리적 의미**:
- 0 m/s: 일반 낙하 시험
- 5 m/s: 컨베이어 벨트 속도
- 10 m/s: 차량 저속 충돌
- 15 m/s: 빠른 운송 조건

**사용 예시**:
```bash
python3 Runner/CumulativeDesigner.py \
  Examples/HWWarrantyDropTest/CustomScenarios/scenario_initial_velocity.json \
  -o /tmp/velocity_test.json
```

**결과**: 4 케이스 × 2 Steps = 8 Jobs

---

### 3. 각속도 (Angular Velocity)

**파일**: [custom_angular_velocity.txt](custom_angular_velocity.txt)

**목적**: 회전하며 낙하하는 조건 시뮬레이션

**케이스**:
```
Static             : 회전 없음 (0, 0, 0)
Spinning_X_100     : X축 회전 (100 rad/s)
Spinning_Y_100     : Y축 회전 (100 rad/s)
Spinning_Z_100     : Z축 회전 (100 rad/s)
Spinning_XYZ_50    : 3축 동시 회전 (50 rad/s)
```

**물리적 의미**:
- 100 rad/s ≈ 955 RPM (분당 회전수)
- 낙하 중 회전으로 인한 추가 충격 분석

**사용 예시**:
```bash
python3 Runner/CumulativeDesigner.py \
  Examples/HWWarrantyDropTest/CustomScenarios/scenario_angular_velocity.json \
  -o /tmp/spin_test.json
```

**결과**: 5 케이스 × 2 Steps = 10 Jobs

---

### 4. 복합 조건 (Combined Conditions)

**파일**: [custom_combined_conditions.txt](custom_combined_conditions.txt)

**목적**: 여러 파라미터를 동시에 변경한 복잡한 시나리오

**케이스**:
```
Standard_1.5m            : 표준 조건 (1.5m, 속도 0, 회전 0)
High_2m_Vel5             : 높이 2m + 초기속도 5 m/s
Low_1m_Spin              : 높이 1m + 3축 회전 50 rad/s
Complex_3m_Vel10_Spin    : 높이 3m + 속도 10 m/s + 회전 75 rad/s
```

**사용 예시**:
```bash
python3 Runner/CumulativeDesigner.py \
  Examples/HWWarrantyDropTest/CustomScenarios/scenario_combined_conditions.json \
  -o /tmp/combined_test.json
```

**결과**: 4 케이스 × 3 Steps = 12 Jobs

---

### 5. Fibonacci + DOE + Cyclic (검증 완료)

**파일**: [scenario_fibonacci_doe_cyclic.json](scenario_fibonacci_doe_cyclic.json)

**목적**: Fibonacci 각도 + DOE 확장 + Cyclic 믹싱 전략

**설정**:
```json
{
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
    "angle_mixing": {
      "strategy": "cyclic",
      "cyclic_offset": 1
    }
  }
}
```

**검증 상태**: ✅ 전체 통과
- 총 Step 수: 150개 (10 × 5 × 3)
- Cyclic 믹싱: 정상 작동
- Cyclic Wrapping: 정상 작동

**상세 보고서**: [../WORKFLOW_VERIFICATION_REPORT.md](../WORKFLOW_VERIFICATION_REPORT.md)

---

## 🎨 나만의 커스텀 txt 만들기

### txt 파일 형식

```txt
*Inputfile
MinimumModel.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ Case1_Name,Case2_Name,Case3_Name
EulerRolling,-180,0,90
EulerPitching,-90,-45,0
EulerYawing,0,0,0
Height,1500,2000,2500
InitialVelocityX,0,5000,10000
InitialVelocityY,0,0,0
InitialVelocityZ,0,0,0
InitialAngularVelocityX,0,50,100
InitialAngularVelocityY,0,0,0
InitialAngularVelocityZ,0,0,0
**EndDropAttitude
*End
```

### 필수 vs 선택 파라미터

**필수**:
- `EulerRolling` (Roll 각도)
- `EulerPitching` (Pitch 각도)
- `EulerYawing` (Yaw 각도)

**선택** (기본값 자동 설정):
- `Height` (기본값: 1500mm)
- `InitialVelocityX/Y/Z` (기본값: 0)
- `InitialAngularVelocityX/Y/Z` (기본값: 0)

### 파일 생성 예시

```bash
# 1. 새 txt 파일 생성
cat > /data/my_custom_scenario.txt << 'EOF'
*Inputfile
MinimumModel.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ MyCase1,MyCase2
EulerRolling,-180,-180
EulerPitching,-90,-90
EulerYawing,0,0
Height,1200,1800
InitialVelocityX,0,7500
**EndDropAttitude
*End
EOF

# 2. JSON 설정 생성
cat > /data/my_scenario.json << 'EOF'
{
  "project_name": "My_Custom_Test",
  "scenarios": [{
    "scenario_name": "My_Scenario",
    "angle_source": {
      "source_type": "case_txt_file",
      "case_txt_file": {
        "file_path": "/data/my_custom_scenario.txt"
      }
    },
    "cumulative": {
      "num_steps": 2,
      "mode_sequence": ["DROP", "DROP"],
      "base_angle_index": 0,
      "angle_mixing": {"strategy": "same_angle"}
    }
  }]
}
EOF

# 3. 실행
python3 Runner/CumulativeDesigner.py /data/my_scenario.json -o /data/runner_config.json
```

---

## 📋 주의사항

### 1. 개수 일치

모든 파라미터의 값 개수가 동일해야 합니다.

❌ **잘못된 예시**:
```
EulerRolling,0,90,180      # 3개
EulerPitching,-90,-45      # 2개 (불일치!)
```

✅ **올바른 예시**:
```
EulerRolling,0,90,180      # 3개
EulerPitching,-90,-45,0    # 3개 (일치)
```

### 2. 파일 경로

- **절대 경로**: `/home/user/data/my_scenario.txt`
- **상대 경로**: `Examples/HWWarrantyDropTest/CustomScenarios/my_scenario.txt`

### 3. 단위

| 파라미터 | 단위 | 예시 |
|---------|------|------|
| EulerRolling/Pitching/Yawing | degree (°) | -180 ~ 180 |
| Height | mm | 1500 (= 1.5m) |
| InitialVelocityX/Y/Z | mm/s | 5000 (= 5 m/s) |
| InitialAngularVelocityX/Y/Z | rad/s | 100 (≈ 955 RPM) |

### 4. Case 이름

- `$` 라인에 comma-separated로 작성
- 공백 포함 가능 (자동 trim)
- 생략 시 자동 생성 (P0001, P0002, ...)

---

## 🔗 관련 문서

- [ANGLE_MIXING_STRATEGIES_GUIDE.md](../ANGLE_MIXING_STRATEGIES_GUIDE.md) - 각도 믹싱 전략 상세
- [COMPLETE_SYSTEM_OVERVIEW.md](../COMPLETE_SYSTEM_OVERVIEW.md) - 전체 시스템 개요
- [QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md) - 빠른 시작 가이드
- [WORKFLOW_VERIFICATION_REPORT.md](../WORKFLOW_VERIFICATION_REPORT.md) - Fibonacci 검증 보고서

---

## 💡 실전 팁

### 1. 빠른 프로토타이핑

간단한 txt 파일로 먼저 테스트:

```bash
# 케이스 2개, Step 2개 (총 4 Jobs)
cat > quick_test.txt << 'EOF'
*Inputfile
MinimumModel.k
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
$ Test1,Test2
EulerRolling,-180,-180
EulerPitching,-90,-90
EulerYawing,0,0
Height,1500,2000
**EndDropAttitude
*End
EOF
```

### 2. 대규모 확장

검증 후 DOE 추가:

```json
{
  "tolerance": {
    "roll": {"tolerance": 1.0},
    "pitch": {"tolerance": 1.0},
    "doe_type": "lhs",
    "doe_count": 10
  }
}
```

→ 2 케이스 × 10 DOE × 2 Steps = 40 Jobs

### 3. 믹싱 전략 활용

다양한 각도 조합:

```json
{
  "angle_mixing": {
    "strategy": "cyclic",
    "cyclic_offset": 1
  }
}
```

→ 순차적으로 다른 각도 적용

---

**작성자**: koo.park
**버전**: 1.0
**날짜**: 2026-01-23
