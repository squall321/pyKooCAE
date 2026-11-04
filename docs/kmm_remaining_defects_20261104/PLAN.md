<!-- KMM 남은 기존 결함 묶음(v131) — 계획 -->
# 계획 — KMM 남은 기존 결함 묶음 (2026-11-04, v131)

## 배경
v130(기존 결함 묶음) 작업과 적대 리뷰 W~Z 에서 범위 밖으로 남긴 기존 결함이 있다(docs/kmm_existing_defects_20261103/context-notes.md 마지막 절). 사용자는 "남은거 해결 ㄱㄱ" 라고 했다. 정해 준 것은 다음 셋이다.
- 셸 단면 실수는 덱 값 그대로 쓴다(10.3e → 10칸 최대 정밀도).
- 덱 전체 `*KEYWORD LONG=Y/S` 는 알아보게 멈춘다(rc 1).
- 검증 뒤 v131 배포까지 간다(v130 과 같은 사슬).

함께, 보류해 둔 Post v43(KooD3plotReader main eccde7f)을 먼저 낸다. 그 뒤속으로 KooChainRun sphere 워커 메모리(SPHERE_NEW_MEM_PER_WORKER_GB 2 → 0.5 GB, a9 실측)를 v131 에 넣는다.

## 무엇을 고치나
| 번호 | 결함 | 고치는 방향(조사 뒤 확정) |
|---|---|---|
| I1 | I10=Y 덱의 DropSet.k 가 `*KEYWORD I10=Y` 를 남기면서 *ELEMENT_MASS 등을 8칸으로 쓴다(LS-DYNA 가 잘못 읽음) | KMM 이 쓰는 블록도 I10 규칙을 따른다 |
| I2 | *DEFINE_CURVE 콤마 점 줄 ValueError | 콤마 줄은 콤마로 나눈다 |
| I3 | 콤마 *MAT_RIGID 카드 2 ValueError | 같은 방식 |
| I4 | 콤마·long *NODE 를 못 읽는다(요소가 '정의 안 된 절점' 으로 소실, rc 3) | 고정폭 빠른 길은 그대로 두고 콤마·long 만 따로 읽는다 |
| I5 | 덱 전체 LONG=Y/S 를 잘못 읽어 쓰레기 출력 | 읽기 시작에서 알아보고 rc 1 로 멈춘다 |
| I6 | 셸 단면 실수 10.3e(유효숫자 4자리) | _real10 으로 덱 값 그대로 |
| I7 | model_dump.k 의 *SECTION_SOLID COHOFF·GASKETT 가 4·5번째 칸 | R16 7·8번째 칸 |
| I8 | *CONTACT_ERODING_*_ID 의 ERODING 카드가 빠진 덱 IndexError | 원인을 짚는 오류 |
| M1 | DECOMPOSE_K 가 원문 요소만 쓰는 절점을 빼먹는다 | 쓰이지 않은 절점도 내보낸다 |
| M2 | IMPORT_MERGE_K — PART.secid 미동기·psid 오프셋 0·*SET_NODE_LIST/*SET_PART_LIST 크래시·원문 블록 소실 | 하나씩 고친다 |
| M3 | FastDOE 기록기가 원문 블록을 쓰지 않는다 | 일반 내보내기와 같은 원문 기록기 |
| M4 | DTI 가 dynain 의 *INITIAL_STRESS_TSHELL 을 버린다 | 원문 통과 또는 해석 |
| M5 | DWI OutsideRigid* 산출 덱이 Run_* 밖에 써진다 | 다른 생성 방식과 같은 자리 |
| M6 | MIRROR 가 TSHELL8 연결을 뒤집지 않는다 | HEXA8 과 같은 뒤집기 |
| M7 | 같은 실행에서 ConvertHexato,TShell 로 만든 TShellMode 파트를 TSHELL 판정에서 놓친다 | 판정에 TShellMode 를 넣는다 |
| M8 | PART_EXCHANGE 가 HEXA8 파트에 *SECTION_TSHELL 만 붙여도 경고가 없다 | 경고 |
| P1 | *PART_CONTACT 파트의 요소 소실(rc 3) | 파트로 읽고 접촉 카드는 원문 그대로 |
| P2 | *ELEMENT_SHELL_THICKNESS 의 요소별 두께가 출력에서 사라진다 | 두께 카드를 지니고 *ELEMENT_SHELL_THICKNESS 로 쓴다 |
| P3 | NODUMP 를 매니저가 쓰지 못한다(비교 문자열 버그) | 고친다 |
| P4 | *SECTION_SOLID ELFORM 101~105 사용자 요소 카드가 유령 단면 | 셸처럼 원문 카드로 지닌다 |
| K1 | KooChainRun sphere 워커 메모리 2 GB(실측 0.3 GB) | 0.5 GB |
| R1·R2 | (조사 중 찾음) 원문 *PART_* 변형 PID·원문 요소 EID 를 번호 매기기에 넣지 않아 DROP 바닥판 등과 겹침 | 예약한다 |
| P2b | (P2 중 찾음) 2차 셸 MIRROR YZ·XZ 의 중간 절점이 다른 변에 붙음 | 새 변의 중간 절점 |
| M2e | (M2 중 찾음) IMPORT_MERGE_K 가 같은 번호의 기준 덱 곡선·경계·HOURGLASS·CONTROL 을 덮고, 구속·감쇠·강체벽이 밀리지 않은 PID·NSID 로 기준 덱을 가리킴 | 공통 DB 는 보존·충돌 🔴, 경계는 새 번호, 밀 수 없는 카드는 옮기지 않고 🔴, 설정은 기준 덱 |
| B1~B3 | (M2 중 찾음) *BOUNDARY_PRESCRIBED_MOTION_RIGID PID 를 절점으로 찾음·*BOUNDARY_PRESCRIBED_MOTION_NODE 크래시·SPC 블록 되풀이 | 고친다 |
| X1·X2 | 원문 재질의 거짓 'MID 소실'·서로 다른 모드의 같은 모드 ID | 해석한 재질만 대조·rc 1 |
| KW | (M3 중 찾음) 메인 기록기 등 최종 기록기 여럿이 *KEYWORD 줄 옵션을 버림 | 원본 *KEYWORD 줄(249cdef 규칙) |
| RV | (적대 리뷰 R1~R3) 콤마 요소·이력·ID 카드 잘림·크래시, long 사용자 단면 20칸, 여러 카드 처방 운동, *PART_CONTACT·접촉 끝 빈 카드, DEATH·BIRTH 정밀도, 'D' 지수 절점, 원문 번호 예약(둘째 파트·실수 칸), Fast DROP 바닥판 EID·PID, I10 기본값, D2R 두 번, 섞인 두께 블록, IMPORT_MERGE_K(접촉·뿌리 매니저·원문 번호·재질·INCLUDE_TRANSFORM·비교), 좌표계 출력, DECOMPOSE False, DWI 복합재, 옵션 블록 두 벌, sphere x.5 GB, DTI 범위, *NODE 없는 덱, *SET_NODE_LIST_GENERATE | 하나씩 고치고 test_v131_review 로 본다 |

## 하지 않는 것
- 덱 전체 LONG=Y/S 지원(사용자 결정: 알아보고 멈춤).
- IMPACT 기본 치수의 SI 크기·누적 DWI 체인의 벽·댐퍼 겹침·Test_Impact 예제 값(설계 문제, 이번 목록 밖).

## 성공 기준
- 항목마다 아는 불량 시험이 먼저 실패하고, 고친 뒤 통과한다.
- 기존 시험 전부 통과.
- 말뭉치 W(지난 747건)·V(실제 덱 88건)는 v130(52fbded) 대비 의도한 다름만 나온다. 셸 단면 정밀도 변경으로 셸 덱 출력이 바뀌는 것은 의도한 것이고, 값은 덱 그대로여야 한다.
- 적대 리뷰 → 고침 → 캡 빌드 → 컴파일본·SIF e2e(아는 불량 먼저) → v131 굽기·tar·Drive·메일 → push → 헤드 /opt(하드 링크 백업).
