# 시뮬레이션 모드 및 컨디션 참조

## 1. 시뮬레이션 모드 (Mode) 정의

### 1.1 모드 목록 및 구현 상태

| 모드 코드 | 전체 모드명 | 설명 | KooMeshModifier | Runner | 상태 |
|-----------|------------|------|-----------------|--------|------|
| `DROP` | DROP_ATTITUDE | 낙하 시뮬레이션 | ✅ 완료 | ✅ 완료 | **사용 가능** |
| `THERM` | THERMAL_CYCLE | 열응력/열사이클 해석 | ❌ 미구현 | ⚠️ 템플릿만 | **구현 필요** |
| `DWI` | DROP_WEIGHT_IMPACT | 중량 충격 시뮬레이션 | ✅ 완료 | ❌ 미구현 | **연동 필요** |
| `STAT` | STATIC_LOAD | 정적 하중 해석 | ❌ 미구현 | ❌ 미구현 | **구현 필요** |
| `VIB` | VIBRATION | 진동 해석 | ❌ 미구현 | ❌ 미구현 | **구현 필요** |
| `COMB` | COMBINED | 복합 조건 해석 | ❌ 미구현 | ❌ 미구현 | **구현 필요** |

### 1.2 모드별 상세 설명

#### DROP (낙하 시뮬레이션) - ✅ 완료
```
KooMeshModifier 모드: DROP_ATTITUDE
입력 파라미터:
  - euler_roll, euler_pitch, euler_yaw (각도)
  - height_mm (낙하 높이, mm)
  - surface (바닥면 종류)
출력 파일: DropSet.k
```

#### THERM (열응력 해석) - ⚠️ 부분 구현
```
KooMeshModifier 모드: THERMAL_CYCLE (미구현)
입력 파라미터:
  - target_temp_C (목표 온도, °C)
  - hold_time_s (유지 시간, 초)
  - initial_temp_C (초기 온도, 기본 25°C)
  - ramp_time_s (승온/냉각 시간, 초)
출력 파일: ThermalSet.k (예정)

상태: Runner에 템플릿만 존재, KooMeshModifier에 실제 모드 구현 필요
```

#### DWI (중량 충격 시뮬레이션) - ⚠️ KooMeshModifier만 완료
```
KooMeshModifier 모드: DROP_WEIGHT_IMPACT_TEST
입력 파라미터: (기존 구현 확인 필요)
출력 파일: DWISet.k

상태: KooMeshModifier에 존재, Runner 연동 필요
```

#### STAT (정적 해석) - ❌ 미구현
```
KooMeshModifier 모드: STATIC_LOAD (예정)
입력 파라미터:
  - load_type (하중 타입)
  - load_value (하중 크기)
  - constraint_type (구속 조건)
출력 파일: StaticSet.k (예정)
```

#### VIB (진동 해석) - ❌ 미구현
```
KooMeshModifier 모드: VIBRATION (예정)
입력 파라미터:
  - frequency_range (주파수 범위)
  - acceleration (가속도)
  - analysis_type (modal, random, sine 등)
출력 파일: VibrationSet.k (예정)
```

---

## 2. 컨디션 (Condition) 정의

### 2.1 DROP 모드 컨디션

#### Face (면) - F1~F6
| 코드 | 설명 | Roll | Pitch | Yaw | 구현 |
|------|------|------|-------|-----|------|
| F1 | Back (후면) | 0° | 0° | 0° | ✅ |
| F2 | Front (전면) | 180° | 0° | 0° | ✅ |
| F3 | Right (우측면) | 0° | -90° | 0° | ✅ |
| F4 | Left (좌측면) | 0° | 90° | 0° | ✅ |
| F5 | Top (상단) | 90° | 0° | 0° | ✅ |
| F6 | Bottom (하단) | -90° | 0° | 0° | ✅ |

#### Edge (모서리) - E1~E12
| 코드 | 설명 | Roll | Pitch | Yaw | 구현 |
|------|------|------|-------|-----|------|
| E1 | 상단-후면 모서리 | 45° | 0° | 0° | ✅ |
| E2 | 하단-후면 모서리 | -45° | 0° | 0° | ✅ |
| E3 | 우측-후면 모서리 | 0° | 45° | 0° | ✅ |
| E4 | 좌측-후면 모서리 | 0° | -45° | 0° | ✅ |
| E5 | 상단-우측 모서리 | 45° | 45° | 0° | ✅ |
| E6 | 하단-우측 모서리 | -45° | 45° | 0° | ✅ |
| E7 | 상단-좌측 모서리 | 45° | -45° | 0° | ✅ |
| E8 | 하단-좌측 모서리 | -45° | -45° | 0° | ✅ |
| E9 | 상단-전면 모서리 | 135° | 0° | 0° | ✅ |
| E10 | 하단-전면 모서리 | -135° | 0° | 0° | ✅ |
| E11 | 우측-전면 모서리 | 0° | 135° | 0° | ✅ |
| E12 | 좌측-전면 모서리 | 0° | -135° | 0° | ✅ |

#### Corner (꼭짓점) - C1~C8
| 코드 | 설명 | Roll | Pitch | Yaw | 구현 |
|------|------|------|-------|-----|------|
| C1 | 후면-상단-우측 꼭짓점 | 35.264° | 45° | 0° | ✅ |
| C2 | 후면-상단-좌측 꼭짓점 | -35.264° | 45° | 0° | ✅ |
| C3 | 후면-하단-우측 꼭짓점 | 35.264° | -45° | 0° | ✅ |
| C4 | 후면-하단-좌측 꼭짓점 | -35.264° | -45° | 0° | ✅ |
| C5 | 전면-상단-우측 꼭짓점 | 144.736° | 45° | 0° | ✅ |
| C6 | 전면-상단-좌측 꼭짓점 | -144.736° | 45° | 0° | ✅ |
| C7 | 전면-하단-우측 꼭짓점 | 144.736° | -45° | 0° | ✅ |
| C8 | 전면-하단-좌측 꼭짓점 | -144.736° | -45° | 0° | ✅ |

### 2.2 THERM 모드 컨디션 (예정)

| 코드 | 설명 | 파라미터 | 구현 |
|------|------|----------|------|
| HOT85 | 85°C 고온 | target_temp_C=85 | ⚠️ 템플릿 |
| HOT125 | 125°C 고온 | target_temp_C=125 | ❌ |
| COLD-40 | -40°C 저온 | target_temp_C=-40 | ⚠️ 템플릿 |
| COLD-20 | -20°C 저온 | target_temp_C=-20 | ❌ |
| CYC01~CYC10 | 열사이클 1~10회 | cycles=N | ⚠️ 템플릿 |

### 2.3 DWI 모드 컨디션 (예정)

| 코드 | 설명 | 파라미터 | 구현 |
|------|------|----------|------|
| IMP01 | 충격 조건 1 | (추후 정의) | ❌ |
| IMP02 | 충격 조건 2 | (추후 정의) | ❌ |

### 2.4 STAT 모드 컨디션 (예정)

| 코드 | 설명 | 파라미터 | 구현 |
|------|------|----------|------|
| BEND01 | 굽힘 하중 1 | (추후 정의) | ❌ |
| TWIST01 | 비틀림 하중 1 | (추후 정의) | ❌ |
| PRESS01 | 압축 하중 1 | (추후 정의) | ❌ |

### 2.5 VIB 모드 컨디션 (예정)

| 코드 | 설명 | 파라미터 | 구현 |
|------|------|----------|------|
| RAND01 | 랜덤 진동 1 | (추후 정의) | ❌ |
| SINE01 | 사인 진동 1 | (추후 정의) | ❌ |

---

## 3. 구현 파일 위치

### 3.1 설계자 (Designer)

| 파일 | 역할 | 위치 |
|------|------|------|
| KooDynaAutomaticSimulationScriptGenerator.py | 모드/컨디션 파싱, runner_config.json 생성 | `occProject/Generators/KooCAEManager/` |
| KooDynaAdvancedModification.py | 실제 모드 실행 로직 (DROP_ATTITUDE 등) | `occProject/Generators/KooCAEManager/` |

### 3.2 실행자 (Runner)

| 파일 | 역할 | 위치 |
|------|------|------|
| CumulativeScenarioRunner.py | 시나리오 실행, 모드별 설정 파일 생성 | `Runner/` |
| AliasManager.py | 별칭 관리 | `Runner/` |
| run_scenario.sh | SLURM 단일 실행 | `Runner/` |
| run_scenario_parallel.sh | SLURM 병렬 실행 | `Runner/` |

---

## 4. 구현 우선순위

### 즉시 사용 가능 (Phase 1 완료)
1. ✅ DROP 모드 + F1~F6, E1~E12, C1~C8 컨디션
2. ✅ runner_config.json 생성
3. ✅ simulation_index.json 관리
4. ✅ 체크포인트/재시작

### 다음 구현 필요 (Phase 2)
1. ⚠️ **THERM 모드**: KooMeshModifier에 THERMAL_CYCLE 모드 구현
2. ⚠️ **DWI 모드**: Runner에 DROP_WEIGHT_IMPACT_TEST 연동

### 추후 구현 (Phase 3)
1. ❌ STAT 모드: 정적 해석
2. ❌ VIB 모드: 진동 해석
3. ❌ COMB 모드: 복합 조건

---

## 5. 사용 예시

### 5.1 DROP 전용 시나리오
```json
{
  "steps": [
    {"mode": "DROP", "condition": "F1", "params": {"height_mm": 1500}},
    {"mode": "DROP", "condition": "E3", "params": {"height_mm": 1500}},
    {"mode": "DROP", "condition": "C2", "params": {"height_mm": 1500}}
  ]
}
```

### 5.2 혼합 시나리오 (THERM + DROP) - THERM 구현 후 사용 가능
```json
{
  "steps": [
    {"mode": "THERM", "condition": "HOT85", "params": {"target_temp_C": 85}},
    {"mode": "THERM", "condition": "COLD-40", "params": {"target_temp_C": -40}},
    {"mode": "DROP", "condition": "F1", "params": {"height_mm": 1500}},
    {"mode": "DROP", "condition": "E5", "params": {"height_mm": 1500}}
  ]
}
```

---

## Author

- Creator: koo.park
- Email: koo.park@samsung.com
- Group: CAE
