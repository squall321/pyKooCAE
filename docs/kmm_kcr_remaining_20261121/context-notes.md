<!-- KMM·KCR 남은 결함 묶음 — 결정 기록 -->
# 결정 기록 — KMM·KCR 남은 결함 묶음 (2026-11-21)

## 요청 해석
- 「남은 결함 모두」 = 이 저장소(KMM·KCR·KAM) 기록에 열린 결함 가운데 지금 재현되고, 사용자 결정으로 닫히지 않았고, 바깥에 막히지 않은 것. 재현 중 찾은 같은 계열의 조용한 소실도 넣는다.
- 분류: A 지금 고칠 결함 · B 이미 고쳐짐(기록이 낡음) · C 사용자 결정으로 닫힘 · D 바깥에 막힘 · E 설계 한계(구현하거나 조용하지 않게).
- 빌드·굽기·헤드 교체는 그때 새로 승인받는다.

## 조사에서 얻은 것
- 리더는 해석하는 키워드 180개 가운데 118개 클래스가 줄 수를 고정해 읽는다(첫 개체만). R16 일반 규칙은 한 키워드 아래 카드 묶음 반복을 허용한다 → A5.
- 해석 키워드가 잃는 길은 둘이다. ① 클래스가 그 줄·칸을 아예 읽지 않는다 ② 읽었지만 관리자·기록기가 싣지 않는다. 「읽은 칸」 감시로는 ②를 못 본다 — 입력·출력 대조(접붙이기 감사)만 본다.
- 접붙이기 감사(실제 덱 3450개에서 제어·DB 블록 모양 수집 → 작은 덱에 붙여 TRANSFORM 0 왕복): EXTENT_BINARY 278/569 블록 카드 3·4 소실, D3PLOT 카드 2 소실 8, BINARY_INTFOR 값 바뀜 5/40(KMM 이 쓴 덱 포함), CONTROL_SOLID 카드 2·3 소실 9/468, CONTROL_CONTACT 1장 블록 rc 1(4)·4장 블록 카드 4 값 0 으로(1). 정밀도 손실은 실제 블록에서 0건.
- 가져오기 때 값 고치기는 제어·DB 모두 「빈 칸 → 기본값」뿐이다(일부러 값을 바꾸는 곳 없음) → 덱 글 병합이 되돌려 놓을 「의도된 수정」이 없다.
- Fast DOE 캐시는 글(문자열)이고 `_ApplyDropEndTime` 은 제어·DB 머리 글이 캐시에 정확히 한 번 나오는지만 본다 → 기록기가 객체 상태의 결정적 함수이기만 하면 병합과 맞는다.

## 결정
1. **A1 은 「덱 글 병합」으로 한다**(모델 확장 아님). 견준 대안 — 모든 칸을 덱 글로(빈 칸까지: 모든 덱의 바이트가 바뀐다), 손대지 않은 블록은 원문 통째로(주석·형식이 바뀐다), 클래스마다 칸 추가(카드가 늘 때마다 또 샌다). 병합은 지금 출력이 수치로 충실한 곳을 바이트 그대로 두고, 바뀌는 바이트가 모두 「되살아난 값」이라 회귀 증명이 쉽다.
2. **모드가 새로 만든 객체는 덱 정보를 잇지 않는다.** DROP 의 `SetControlandDatabaseExplicit` 는 D3PLOT·INTFOR·NODOUT·ELOUT·NCFORC 를 새 객체로 바꾼다 — 그 카드는 모드가 통째로 정한 것이라 덱의 D3PLOT 카드 2 는 따라가지 않는다(지금과 같다, 설계). 객체가 살아 있는 EXTENT_BINARY·CONTROL_* 는 끝 카드가 되살아난다.
3. **제어·DB 기록기의 실수 포맷은 그대로 둔다.** 덱에서 온 값은 병합이 덱 글로 되살리고, 모드가 정한 값(ENDTIM·dt·출력 간격)은 지금 글 그대로다 — 기존 산출물이 흔들리지 않는다. 정밀도 보존 도우미는 개체 기록기(재질·LOAD_SEGMENT)에만 쓴다.
4. **A5 나누기는 보수적으로.** 끝 빈 줄을 뗀 길이가 카드 수의 정확한 배수(2개체 이상)이고 가운데 빈 줄이 없을 때만 나눈다. 줄 간격을 띄운 덱(빈 줄이 카드마다 끼인 것)은 지금처럼 읽는다. 카드 수가 내용에 따라 달라지는 키워드(DAMPING_PART_MASS FLAG, INITIAL_VELOCITY NSIDEX)는 내용을 보고 센다. 길이가 가변인 키워드(CONTACT·SET·DEFINE_CURVE·PART_COMPOSITE 등)와 선택 카드가 있는 한 벌짜리 키워드는 나누지 않는다.
5. **LOAD_SEGMENT 는 고친다(삭제·우회 아님).** 지금은 가져오기에서 항상 죽으므로 「기존 동작」이 없다 — 회귀 위험이 없다.
6. 숫자 아닌 글을 `KooDynaFloat` 가 조용히 기본값으로 읽는 것은 그대로 둔다(전 코드가 쓰는 함수라 범위가 넓다). 제어·DB 카드에서는 병합이 덱 글을 되살리므로 틀 글(`{{…}}`)도 남는다. 한계로 보고.

## 구현하며 정한 것(2026-11-22)
7. **덱 글 되살리기(A1) 규칙** — `KooCAEManager/KooDeckEcho.py`. 가져온 직후 객체에 덱 블록·그때의 기록 결과(base)·속성 사본을 붙이고, 두 관리자 기록기(제어 15개·DB 키 루프)가 쓸 때 지금 기록 결과(now)와 맞춘다. 데이터 줄 수가 base·now 다르면 now 그대로(모드가 카드 짜임을 바꿨다). 칸: 모드가 바꿨으면(now ≠ base) now / 기록기에 없는 끝 칸·끝 카드는 덱 글(값 0 인 끝 칸과 맨 끝의 빈·0 카드는 붙이지 않는다 — LS-DYNA 는 빈 숫자 칸을 0 으로 읽는다) / 덱 빈칸·수치 같음·(now 빈칸이고 덱 0) → now / 다르면 덱 글. 바꾼 칸이 없는 줄은 now 줄 바이트 그대로.
   - 안전장치: 바뀐 속성 수가 기록에 보이는 바뀐 칸 수보다 많으면 모델 칸은 now(모드 값의 4자리 표기가 가져온 때와 같아 덱 글이 모드 값을 덮는 것 방지). 기록기 키워드 줄이 덱 키워드와 다르면 붙이지 않는다(이름 없는 INTFOR_FILE·INTFOR 를 FILE 이 덮은 자리). 붙이기는 예외를 내지 않고(실패 → 안 붙임), 병합이 죽으면 now 를 쓰고 경고 한 줄. DR 카드 2 는 IDRFLG 가 바뀌면 붙이지 않는다. CONTROL_SOLID 카드 2 는 8칸, INTFOR_FILE 이름 줄은 글 한 칸.
   - grep 확인: 제어·DB 를 쓰는 곳은 두 관리자 기록기뿐(주 출력·Fast DOE 베이스·노드 앞 판·`_ApplyDropEndTime`), 모드가 객체 칸을 제자리에서 바꾸는 곳은 ENDTIM·DTMIN·IHQ·QH 넷뿐, `_RestoreBaseState` 는 두 관리자를 건드리지 않는다 → Fast DOE `cached_base.count(old) == 1` 그대로(test_drop_endtime_table 63건 통과).
8. **A3** 한 장짜리 CONTROL_CONTACT 의 카드 2 는 빈 칸(두 장짜리의 빈 칸과 같은 읽기 — 0). 카드 3 PTSCL·카드 5 RWKSF 빈칸은 R16 기본값 1.0 으로 읽는다(0 이 「기본값」 뜻이라는 말이 매뉴얼에 없다) — 3~5 장짜리는 예전 출력(세터 기본값 1.0) 그대로, 6~7 장짜리의 빈 PTSCL 은 0.000e+00 → 1.000e+00 으로 바뀐다(말뭉치 12·14·16번).
9. **A4** 카드 3 만 자료가 있으면 빈 카드 2 줄을 먼저 쓴다(카드 순서). PM 이 모두 0 인 카드 2 는 예전처럼 쓰지 않는다.
10. **INTFOR_FILE** 이름은 글자로(리더가 목록으로 줬다), 카드 2c 는 선택(없으면 IOOPT 0), 이름은 왼쪽부터 쓴다. 모드가 이름 있는 INTFOR 를 만드는 곳은 없다.
11. **A5 표** — 개체 크기가 R16 로 정해진 평범한 꼴만 나눈다: MAT_ELASTIC(E < 0 이면 2)·MAT_RIGID 3·EOS_LINEAR_POLYNOMIAL 2·MAT_ADD_PZELECTRIC 7·BOUNDARY_SPC_SET·CONSTRAINED_EXTRA_NODES_NODE/SET·CONSTRAINED_NODE_SET·CONSTRAINED_JOINT_SPHERICAL·CONSTRAINED_NODAL_RIGID_BODY·DAMPING_PART_STIFFNESS(_SET)·LOAD_SEGMENT_SET·DATABASE_NODAL_FORCE_GROUP 1, DAMPING_PART_MASS(_SET)(FLAG = 1 이면 2), DEFINE_COORDINATE_SYSTEM·INITIAL_VELOCITY_GENERATION·RIGIDWALL_PLANAR 2. _ID·_TITLE 꼴은 (ID 카드 + 카드) 짝 반복인지 ID 하나 아래 카드 여럿인지 매뉴얼이 밝히지 않아 나누지 않고, 한 개체보다 길면 🔴 카드 소실(rc 3). 가운데 빈 줄·나누어떨어지지 않는 줄 수도 🔴 rc 3. 표에 없는 다른 재료·단면 꼴의 한 블록 여러 개체는 이번에 다루지 않았다(남은 한계로 보고). MAT_ELASTIC 카드 1.1(E < 0)은 KMM 이 옮기지 않는다 → 🔴 rc 3. KooRemapper 가 *MAT_ELASTIC 두 개체를 한 블록에 쓴다(REMAP 체인 입력) — 이번 나누기로 읽힌다.
12. **NODAL_FORCE_GROUP**(새로 찾음): 키워드를 둘로 써도 매니저가 한 자리("NODAL_FORCE_GROUP")에 담아 하나만 남았다 → 그룹마다 열쇠(첫 것은 예전 열쇠).
13. **A7** *LOAD_SEGMENT(_ID) 는 개체 단위로 읽고(카드 2 는 N5 ≠ 0 일 때만), 올바른 *LOAD_SEGMENT_ID(ID 카드·카드 1·카드 2)로 쓴다. 절점은 객체로 들고 쓸 때 번호. 없는 절점 → 🔴 rc 3, _ID 한 블록 여러 개체 → 🔴 rc 3. **하중 ID 겹침**(새로 찾음): `loads` 사전 열쇠가 겹치면 덮어 앞 하중이 rc 0 으로 빠졌다(*LOAD_NODE_POINT 가 번호 1 → *LOAD_SEGMENT_SET_ID 1) → KMM 이 매긴 번호면 그 하중을 새 번호로 옮기고, 덱 ID 끼리 겹치면 새 열쇠에 둔다(쓰는 ID 는 덱 그대로). SF·AT 는 `_e10`(4자리로 담기는 값은 예전 바이트 그대로).
14. **말뭉치 25개(U1+U2)** — 바뀐 줄 전부 설명: KMM 이 쓴 DROP 덱의 INTFOR DT·NPLTC·IOOPT 복구(00·01·11·13·15·17), D3THDT DT 99999 자릿수(02~07), CONTACT 카드 4 복구(10·12·14·16, KMM 이 쓴 4장짜리), 6~7장짜리 빈 PTSCL 1.0(12·14·16), SOLID 빈 카드 2 + 카드 3 TET13V(10·12·14·16), 옛 LS-DYNA 꼴 SHELL 카드 2 의 6·7칸(NFAIL1·NFAIL4 자리) 되살림(12·14·16), EXTENT_BINARY 카드 3(12~24). rc 바뀜 0, 나누기 영향 0.
15. KooDynaControl·KooDynaDatabase·KooLoad·KooMaterial 등 KooCAEManager 의 많은 파일이 CRLF 다 — 고칠 때 바이트로 바꾼다(text 모드로 열면 LF 로 바뀐다).

16. **A8** R16 Remark 2·3 그대로 — 정수 리터럴·I 파라미터는 정수로 세고(2/5 = 0, 정수 나눗셈은 0 쪽으로 버림), 실수와 섞이면 실수. I 결과는 예전처럼 NINT(덱 규약). sign·atan2·min·max·mod 는 두 인수, mod 는 정수(실수는 NINT)·부호는 첫 인수(Fortran MOD). 단항 ±가 ** 보다 먼저(괄호 없이 붙은 '-a**b' 만 (-a)**b, '-(3**2)' 는 그대로). 정수 거듭제곱은 63비트를 넘으면 평가 실패(멈춤 없음), 음수 지수는 Fortran 정수 결과. 유한하지 않은 값은 평가 실패. 이어지는 줄(앞 10칸 공백)은 다음 식 줄·키워드·파일 끝에서 정의한다. '-&이름' 은 수 값일 때만 부호를 바꾼다(고정폭·쉼표 데이터 줄, 주석·키워드 줄은 아님). '&이름^' 은 길이를 바꾸는 치환(값 + '_' 또는 CPINLSDNR). 그대로 둔 것(시끄럽게 실패): Fortran d 지수·0 으로 시작하는 정수가 든 식, 쉼표 줄 안의 <식>.
17. **U6** B1 빔 빈 줄은 다른 요소 리더처럼 알리고 건너뛴다. B2 단면은 GenerateDynaKeyword 글로 쓰고, 해석한 재료도 그때 글을 만든다(파트 덱에 재료가 빠지던 것 — 새로 찾음). B3 속도 키는 다른 충격 모드처럼 0. B4 있는데 못 읽는 인클루드는 rc 1(환경 문제). A15 없는 인클루드는 rc 0 + 🔴, 주 출력·MERGE_K 출력에 덱에 쓴 글 그대로의 *INCLUDE 줄(파일 이름만 바꾸지 않는다 — 복사할 파일이 없다), 다른 모드 출력(낙하 덱 등)에는 없다(통과 인클루드와 같은 길). B5 3단 원통 byPart 는 원래 미지원(NotImplementedError 문구) — 남은 한계. B6 *NumberofElements 를 안 쓰면 원래 뜻대로 100(파서가 0 을 넣어 죽었다), 구속 줄 없으면 구속 없이, 표본·통계 둘 다 없거나 요소 수 1·없는 구속 파트·뽑을 수 없는 통계는 🔴 rc 1(모델을 바꾸기 전에 확인).
18. **U9 KCR** C1 칸 수를 DOE 수로 줄인다(표 켬과 같다). C2 jobs.json 의 sequential_slot 이 있는 DOE 는 칸 스크립트로 다시 내지 않는다 — DOE 하나짜리 스크립트(순차 제출도 만든다)가 있으면 그것으로, 없으면 `rerun --sequential` 알림. C3 겹친 --does 는 한 번. C4 jobs.json 없으면 기본 스크립트로 내고 새로 쓴다. sbatch 실패: submit(기본·--sequential)·rerun(기본·--sequential) 모두 덜 냈으면 끝에 🔴 + 종료 코드 1(낸 잡은 그대로, 첫 잡 실패는 예전처럼 바로 멈춤). batch_koomeshmodifier 갈래는 그대로(자기 집계가 있다).

## 기록이 낡은 것(다시 고치지 않는다)
*MAT_RIGID 카드 2 빈 줄, NUL 채움, 자기 자신 인클루드, *ELEMENT_SOLID 끝 빈 줄, 데이터 없는 키워드, PART_EXCHANGE TSHELL 단면, 셸 요소 두께 소실, IMPORT_MERGE_K PART.secid, BPM DEATH·BIRTH 표기, 요소 소실 rc 0(이미 rc 3) — 지금 소스에서 재현되지 않는다. 메모리·문서의 「미수정」 표기를 정리한다.

## 죽은 코드(보고만, 지우지 않는다)
`KooDatabaseBinaryIntfor.WriteDynaKeyword`(없는 부모 메서드 호출), `KooDatabaseManager.GenerateDynaKeyword`·`KooMeshImporter.ExportDynaString`·`KooSimulationGenerator.ExportDynaFile`(부르는 곳 없음), `KooLoadManager.AddLoad`(없는 속성 사용).
