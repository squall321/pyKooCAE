# KooMeshModifier 모드별 상세 분석

이 폴더에는 KooMeshModifier의 각 모드에 대한 상세 분석 문서가 포함되어 있습니다.

---

## 문서 목록

### 핵심 모드 (낙하/충격 시뮬레이션)

| 파일 | 모드 | 설명 |
|------|------|------|
| [MODE_09_DROP_ATTITUDE.md](MODE_09_DROP_ATTITUDE.md) | DROP_ATTITUDE | 다양한 낙하 자세 시뮬레이션 생성 |
| [MODE_12_DROP_WEIGHT_IMPACT_TEST.md](MODE_12_DROP_WEIGHT_IMPACT_TEST.md) | DROP_WEIGHT_IMPACT_TEST | 낙하 추 충격 시험 설정 |
| [MODE_18_DYNAIN_TO_INITIAL.md](MODE_18_DYNAIN_TO_INITIAL.md) | DYNAIN_TO_INITIAL | 동적 이완 결과를 초기 조건으로 변환 |
| [MODE_20_SIMULATION_AUTOMATION.md](MODE_20_SIMULATION_AUTOMATION.md) | SIMULATION_AUTOMATION | JSON 기반 시뮬레이션 자동화 |

### 모델 변환 모드

| 파일 | 모드 | 설명 |
|------|------|------|
| [MODE_01_ELASTIC_TO_RIGID.md](MODE_01_ELASTIC_TO_RIGID.md) | ELASTIC_TO_RIGID | 탄성 재료를 강체로 변환 |
| [MODE_05_PART_EXCHANGE.md](MODE_05_PART_EXCHANGE.md) | PART_EXCHANGE | 파트 메시 변환 및 재료 교체 |
| [MODE_11_TRANSFORM.md](MODE_11_TRANSFORM.md) | TRANSFORM | 기하 변환 (이동/회전/스케일) |

---

## 모드 연계 관계도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        시뮬레이션 워크플로우                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SIMULATION_AUTOMATION (메타 모드)                                          │
│          │                                                                   │
│          ├──► DROP_ATTITUDE ──► LS-DYNA 실행 ──► dynain                    │
│          │                                           │                       │
│          │                                           ▼                       │
│          ├──► DYNAIN_TO_INITIAL ◄─────────────────────                      │
│          │          │                                                        │
│          │          ▼                                                        │
│          │    초기응력 포함 모델                                              │
│          │          │                                                        │
│          └──► DROP_WEIGHT_IMPACT_TEST (선택)                                │
│                     │                                                        │
│                     ▼                                                        │
│               최종 충격 해석                                                  │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                        모델 전처리 워크플로우                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  원본 모델                                                                   │
│      │                                                                       │
│      ├──► TRANSFORM (좌표 변환)                                             │
│      │                                                                       │
│      ├──► PART_EXCHANGE (메시/재료 변환)                                    │
│      │                                                                       │
│      └──► ELASTIC_TO_RIGID (계산 효율화)                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 핵심 워크플로우: 낙하 시험

### 1. 초기 모델 준비
```
TRANSFORM → PART_EXCHANGE → 전처리된 모델
```

### 2. 낙하 시뮬레이션 (자중 평형)
```
DROP_ATTITUDE → LS-DYNA 실행 (동적 이완) → dynain
```

### 3. 초기 조건 설정
```
DYNAIN_TO_INITIAL → 초기응력 포함 모델
```

### 4. 실제 충격 해석 (선택)
```
DROP_WEIGHT_IMPACT_TEST 또는 추가 DROP_ATTITUDE
```

---

## 참고: 미작성 모드 목록

아직 상세 분석 문서가 작성되지 않은 모드들:

| 모드 | 간단 설명 |
|------|----------|
| MATERIAL_EXCHANGE | 재료 속성 DOE 생성 |
| PART_LOCATION_DOE | 파트 위치 DOE 생성 |
| ERODING_MIN_DT | 요소 침식 시간 간격 설정 |
| PART_MORPHING | 기하 형상 모핑 |
| WEAK_COUPLING | 약결합 영역 설정 |
| DEFEATURE_MESH | 미세 기하 제거 |
| TRANSLATION_DOE | 이동 DOE 생성 |
| CONSTRAINED_NODAL_RIGIDBODY_TO_BEAM | CNRB→빔 변환 |
| WARPED_PART | 휨 변형 적용 |
| WARPED_TO_INITIAL_STRESS_PART | 휨→초기응력 변환 |
| DIMENSIONAL_TOLERANCE | 치수 공차 적용 |
| COHESIVE_BETWEEN_CONFORMAL_MESHES | 코히시브 요소 삽입 |
| CONTACT_AUTO_DECOMPOSITION | 접촉 자동 분해 |
| REMOVE_DUPLICATE_TIED_CONTACTS | 중복 접촉 제거 |

---

## 문서 읽는 순서 권장

1. **DROP_ATTITUDE** - 기본 낙하 시뮬레이션 이해
2. **DYNAIN_TO_INITIAL** - 동적 이완 결과 활용 방법
3. **DROP_WEIGHT_IMPACT_TEST** - 충격 시험 설정
4. **SIMULATION_AUTOMATION** - 전체 자동화 프레임워크 이해
5. **나머지 모드** - 필요에 따라 참조
