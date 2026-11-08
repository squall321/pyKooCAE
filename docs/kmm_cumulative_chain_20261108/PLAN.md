<!-- KMM 누적 체인 결함 묶음 — 계획 -->
# 계획 — KMM 누적 체인 결함 묶음 (2026-11-08)

## 배경
v131 때 범위 밖으로 미룬 기존 결함 가운데 큰 것 셋은 모두 여러 단계를 이어서 하는 해석(누적 낙하·누적 충격)에서 생긴다
(docs/kmm_remaining_defects_20261104/context-notes.md 「다음 판으로 넘기는 기존 결함」). 사용자는 11-08 에 이 묶음을 먼저 하자고 했다.

이어서 하는 해석의 각 단계는 앞 단계의 응력·변형만 이어받아야 하고, 바닥·충격 장치는 그 단계가 새로 만든 것만 있어야 한다.
지금은 앞 단계 장치가 남거나 깨진 채로 다음 단계에 간다.

판 번호는 굽는 차례로 정해진다(kooomnidropanalyzer-43 도 다음 판을 준비 중) — 문서에서는 번호 대신 「누적 체인 묶음」 이라 부른다.

## 무엇을 고치나
| 번호 | 결함 | 고치는 방향 |
|---|---|---|
| C1 | 낙하(바닥 = 강체벽) 누적 — `getRigidWallPlanarMovingForcesID` 가 이름표를 `_ID` 없이 넘겨 다시 읽을 때 카드가 한 장 밀린다. DTI 에 강체벽 지우기가 없다 | 이름표를 고치고, DTI 에 `*RemoveRigidWallbyID` 를 더하고, DROP 이 만든 바닥 벽 번호를 dynaintoinitial.txt 에 적는다(단일 각도·여러 각도 Fast 둘 다). 셋을 함께 — 이름표만 고치면 앞 단계 벽이 살아나 다음 낙하가 조용히 틀린다 |
| C2 | 충격 누적 — 다음 단계 DTI 가 충격체와 그 접촉만 지운다. 받침 벽·앞·가운데 단·댐퍼·SPC·벽 처방 운동·초기 속도가 남는다. RemovePart 는 그 파트를 가리키는 처방 운동·초기 속도·파트 묶음 번호를 지우지 않는다 | DWI 가 만든 파트·카드를 dynaintoinitial.txt 에 모두 적고 DTI 가 지운다. RemovePart 가 그 파트를 가리키는 카드(*BOUNDARY_PRESCRIBED_MOTION_RIGID·*INITIAL_VELOCITY_GENERATION·*SET_PART 의 번호)도 정리한다 |
| C3 | 바닥판을 전체 접촉에 넣는 설정(IncludeWallInGeneral) 누적 — 첫 낙하가 만든 「모든 파트」 묶음에 지워진 바닥판 번호가 남고, 둘째 낙하는 전체 접촉이 있으니 새 바닥판도 들어 있다고 여긴다(실제로는 없다) | 기존 전체 접촉이 파트 묶음으로 범위를 정하면 새 바닥판을 그 묶음에 넣는다(모든 파트 대상이면 그대로). DTI 가 지운 파트 번호를 파트 묶음에서 뺀다 |
| W1 | 강체벽 기록기 — 제목을 버림, 좌표를 10.4f(정밀도 손실), *RIGIDWALL_PLANAR 를 MOVING_FORCES(MASS 0)로 다시 씀, *RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID 의 BIRTH 0 → 1E20(벽이 켜지지 않음), 번호 없는 FLAT_DISPLAY IndexError(rc 1) | 읽은 종류·제목·값을 그대로 쓴다(_real10). MASS 0 의 뜻은 매뉴얼로 확인 |
| W2 | 바닥 벽 정의 차례가 경로마다 다르다(단일 각도 = 덱 강체벽 앞, Fast = 뒤). 강체벽을 종류별로 읽어 덱 차례와 다르다 | 한 가지 차례로(D2R CODE 1·3 ENTNO·RWFORC 는 정의 차례를 쓴다) |
| W3 | DROP 이 덱 사용자 강체벽을 모델 이동·회전에 맞춰 옮기지 않는다(코드 읽기) | 조사 뒤 확정 — 모델과 함께 움직여야 하는 경우만 |
| S1 | OutsideRigid*·byPart 충격 덱에 *INTERFACE_SPRINGBACK_LSDYNA 가 없으면 dynain 이 안 나와 이어서 할 수 없다(코드 읽기) | 이어서 하는 단계면 DampingSpring 경로처럼 카드를 넣는다 |
| S2 | 시편을 잘라 내는 충격(BoundaryDistance≠0)을 이어서 하면 바깥 요소를 지운 시편이 댐퍼·SPC 와 함께 다음 단계로 간다 | 사용자 결정에 따른다(멈춤 또는 경고 후 계속) |

## 하지 않는 것(다음으로)
- byPart 원통 DWI 가 늘 rc 1(정의 안 된 nodeMan) — 한 번도 끝까지 돈 적 없는 경로라 시험과 함께 따로 연다.
- ConvertSolidtoSolidwithSlack 재시도, IDAM≠0 침식 거짓 rc 3, 재질 유효숫자 4자리(mat_prec), 처방 운동 카드 3, SSTYP 7,
  *DEFINE_BOX_LOCAL TRANSFORM 원점, D2R 목록의 MAT_RIGID, Fast DROP 바닥 접촉 CID 증가, DTI 키워드 종류 단위, 죽은 코드 — 누적 체인과 무관.

## 검증
- 아는 불량 먼저: 지금 main(v133 소스)으로 2단계 체인 덱을 만들어 결함이 보이는지(새 시험이 실패하는지) 확인한 뒤 고친다.
- 새 시험(덱 수준): 낙하 RigidWall 2단계·충격 2단계(DampingSpring·OutsideRigid)·IncludeWallInGeneral 2단계. 단계마다 덱의 강체벽·파트·
  처방 운동·초기 속도·SPC·접촉·파트 묶음의 개수와 번호를 본다. 앞 단계 응력(*INITIAL_STRESS)이 이어지는지도 본다.
- 회귀: 기존 시험(test_v131_review 등)·kooomnidropanalyzer-43 의 test_drop_endtime_table·test_drop_rigid_spin(DROP_ATTITUDE 를 건드리면
  /data/koopark/Test_E2E_v133 케이스 b·c 도)·말뭉치 비교(의도한 다름만).
- 적대 리뷰는 에이전트 한두 개로(큰 워크플로우는 사용자 확인 뒤).
- 🔴 LS-DYNA 라이선스가 10-16 부터 만료 상태라 실제 해석으로 결과를 볼 수 없다. 덱 수준 판정과 대역 솔버로 체인 배선만 확인하고, 보고에 그렇게 적는다.
- 빌드 뒤 컴파일본으로 같은 시험을 다시 돌린다.

## 배포(사용자 결정에 따라)
KMM·KCR 빌드(메모리 상한 scope) → SIF 굽기 → tar·Drive·메일 → 헤드 /opt 교체 → 노드는 VM 을 켤 때. 빌드·굽기는 다른 세션에 알리고 한 번에 하나만 한다.

## 조율
- kooomnidropanalyzer-43: 이 파일들을 고칠 계획 없음(11-08). 그쪽 다음 작업은 Runner(대규모 DOE·Slurm 순서·EndTimePresim) — CumulativeScenarioRunner.py 를
  건드리게 되면 서로 먼저 알린다.
- DROP_ATTITUDE 의 EndTimeTable·RigidAngularVelocity(v132) 를 건드리면 그쪽 시험과 e2e 를 돌린다.
