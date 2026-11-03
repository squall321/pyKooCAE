<!-- KMM 기존 결함 묶음(v130) — 계획 -->
# 계획 — KMM 기존 결함 묶음 (2026-11-03, v130)

## 배경
v129(TSHELL 단면·TIED 두께) 작업 중에 실제 덱 말뭉치와 적대 리뷰 U 에서 기존 결함이 드러났다. 사용자는 "기존 결함들도 다 해결해야지" 라고 했고, 범위는 **이번 보고분 전부**로, 검증 뒤 **v130 배포까지** 가기로 정했다.

## 무엇을 고치나
| 번호 | 결함 | 고치는 방향 |
|---|---|---|
| A | KMM 이 *ELEMENT_TSHELL 을 해석하지 않아(원문 통과) TSHELL 파트가 DROP_ATTITUDE 의 모든 접촉 집합(SINGLE_SURFACE·바닥판 Outer·RobustContact 면·Tied 면 감지·D2R 쌍)에서 빠진다 | *ELEMENT_TSHELL 을 SolidElement 형식 "TSHELL8" 로 읽고, *ELEMENT_TSHELL 로 다시 쓴다. 면 계산(SetBoundaries)만 HEXA8 과 같게 한다. 솔리드 전용 처리(HEXA8·TETRA4·PENTA6 분기)는 TSHELL8 을 건너뛰므로 작은 dt 강체화·재메싱·층 분할에 잘못 걸리지 않는다. *ELEMENT_TSHELL_BETA 같은 변형은 원문 그대로 둔다 |
| B1 | *DATABASE_EXTENT_INTFOR 카드가 한 장이면 IndexError(배터리 생성기 덱) | R16 카드 2 는 선택 카드(기본값 0)다. 없으면 빈 칸으로 넘긴다 |
| B2 | 요소가 *NODE 에 없는 절점을 가리키면, 절점이 모자란 요소가 남아 SetBoundaries 에서 IndexError(DROP). TRANSFORM 은 원인 없이 "내보내기에서 못 씀" 으로만 rc 3 | 읽을 때 "정의 안 된 절점" 이유로 요소 소실 장부(IMPORT_LOSS)에 올리고 요소는 넣지 않는다 → 🔴 + rc 3 에 원인이 나온다 |
| B3 | *CONTACT_ERODING_SURFACE_TO_SURFACE_ID 가 UnboundLocalError('i') | 분기 비교에 `*` 가 빠졌고, 생성 함수 이름도 대소문자가 틀렸다(createContact… → CreateContact…). 둘 다 고치고 SYM·EROSOP·IADJ 는 KooDynaInt 로 읽는다 |
| B4 | *LOAD_SEGMENT_SET(_ID) 가 KMM 이 해석하지 않는 세트(*SET_SEGMENT_GENERAL 등)를 가리키면 KeyError | 세트를 SSID 만 든 자리 표시로 두고 같은 SSID 로 쓴다. 세트 원문은 그대로 나간다. 알림 한 줄 |
| B5 | 고정폭 10칸을 넘친 수(`  1.0000E+`)에서 KooDynaFloat ValueError | 덱 자체가 잘못됐다(KooRemapper ModelAssembler 가 82자 줄을 씀, LS-DYNA 도 80열까지만 읽음). KMM 은 원인을 짚는 오류를 내고, KooRemapper 쪽에 출력기 수정을 요청한다 |
| B6 | *SECTION_SHELL 필수 카드 2 가 없으면 IndexError | 경고하고 빈 칸(기본값)으로 읽는다 |
| C1 | 한 *SECTION_TSHELL·*SECTION_SHELL 블록 아래 단면이 여럿이면 두 번째부터 사라진다. 그리고 **새로 찾은 것** — *SECTION_SHELL ICOMP=1 의 각도 카드가 출력에서 사라진다(복합 셸 적층이 조용히 틀어짐) | R16 "For each section include a set of the following cards. This input ends at the next keyword" 대로 카드 묶음을 차례로 읽는다. ICOMP=1 이면 각도 NIP 개를 읽고 쓴다 |
| C2 | KooDynaFloat 가 Fortran 이 받는 꼴(`4.5+01`·`1.0-3`)에서 죽고, `1.0D-3` 은 조용히 기본값으로 바꾼다 | 지금 읽히는 값은 그대로 두고, 이 꼴들만 제대로 읽는다. 그래도 숫자가 아니면 원인을 짚는 오류 |
| C3 | ICOMP 판정이 키워드 리더(float==1)와 단면 매니저(KooDynaInt 반올림)에서 다르다 | 같은 규칙(KooDynaInt)으로 맞춘다 |
| C4 | PART_EXCHANGE 가 TSHELL 단면을 파트에 못 붙인다(AddSectionfromDyna 가 None) | TSHELL·SOLID_PERI 분기도 단면을 돌려준다 |
| C5 | *SECTION_TSHELL 의 long(`+`)·콤마 자유형식에서 SECID 를 잃는다 | 블록 형식(읽기가 이미 기록함)을 파서에 넘겨 long 은 20칸, 콤마 줄은 콤마로 나눈다. 같은 파서를 고치는 SECTION_SHELL 에도 적용한다 |

## 하지 않는 것(이번 범위 밖, 보고)
- 셸 단면 실수의 10.3e(유효숫자 4자리) 출력. 모든 셸 덱 출력이 바뀌고 기존 v119 바이트 동일 판정도 깨진다.
- *KEYWORD LONG=Y(덱 전체 long). KMM 전체가 10칸 기준이라 별도 기능이다.
- 예전 미수정분: *ELEMENT_SHELL_THICKNESS·IMPORT_MERGE_K PART.secid·NODUMP·DWI OutsideRigid 위치. 사용자가 이번 범위에서 뺐다.
- MIRROR 모드의 TSHELL 연결 뒤집기(기존 결함). 지금도 원문 요소는 미러되지 않는다.

## 성공 기준
- 항목마다 아는 불량 시험이 먼저 실패하고, 고친 뒤 통과한다.
- 기존 시험 전부 통과.
- 말뭉치 U(지난 739건 + 재현 덱)는 옛 트리 5625a74 대비 의도한 다름만 나온다.
- 말뭉치 V(실제 덱 88건)에서 rc 1 기존 실패 36건이 사라진다. B5 덱만 원인을 짚는 오류로 남는다. TSHELL 덱은 DROP 접촉 집합에 TSHELL 파트가 들어간다.
- 적대 리뷰 → 고침 → 캡 빌드 → 컴파일본·SIF e2e(아는 불량 먼저) → v130 굽기·tar·Drive·메일 → push → 헤드 /opt(하드 링크 백업).
