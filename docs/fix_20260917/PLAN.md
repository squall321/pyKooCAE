# 2026-09-17 help 작업 중 발견한 결함 6건 수정

## 대상과 방향
| # | 결함 | 수정 |
|---|---|---|
| 1 | drop_weight_impact 워크플로우 충격 속도 이중 가산 | 워크플로우가 `InitialVelocityZ,0` + `Gravity,9810` 을 넘긴다 (속도는 KMM 이 Height 로 한 번만 계산) |
| 2 | Height > 100 이면 mm, ≤ 100 이면 m 로 g 추정 | KMM 에 `Gravity` 키 추가. 없으면 **모델 재질 밀도 중앙값**으로 단위계 판정 (< 1e-7 → ton-mm-s g=9810, 1~1e5 → kg-m-s g=9.81). 판정 불가일 때만 옛 추정 + 🔴 경고. scenario `simulation_params.gravity` 로도 지정 |
| 3 | KooRemapper restack material_card mid 칸 숫자/MAT01 → PART mid=0 + 재질 카드 누락 | `MID<숫자>` 가 없으면 첫 데이터 줄 첫 필드를 라벨로 보고 새 MID 부여·치환 |
| 4 | KooRemapper matswap 이 3필드 PART(generate box) 에서 PID not found | PART 카드 3필드 이상 허용, EOSID/HGID 없으면 0 |
| 5 | KAM `exit()` 이 컴파일 바이너리에서 NameError, 게이트 실패 종료 코드 불명확 | `sys.exit(1)` + 계산 노드 대역(192.168.122.x) 허용 |
| 6 | KAM CAP/솔더 Evolver 가 작업 폴더 Library/Evolver 에만 의존 | 작업 폴더에 없으면 설치본(/opt·실행파일 기준·/data)을 찾아 작업 폴더 Library/Evolver 에 evolver 링크 생성. 못 찾으면 종료 코드 1 |

## 기존 동작 보호
- 2: 기존 시나리오(mm 모델 height>100, SI 모델 height≤100)는 같은 g 가 나와야 한다 → 실제 예제 모델들로 신구 g 비교
- 3·4: 기존 예제 결과와 명령 40개 신구 비교, 단위시험
- 6: 작업 폴더에 Library/Evolver 가 이미 있으면 기존 경로 그대로
