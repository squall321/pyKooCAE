<!-- KMM 기존 결함 묶음(v130) — 결정과 근거 -->
# 결정 노트 — KMM 기존 결함 묶음 (2026-11-03, v130)

## 조사에서 확인한 사실
- **원문 통과 규칙.** `_raw_keyword_dict` 에는 읽은 키워드가 모두 원문으로 들어간다. 쓸 때 `keywordInterpreted[kw] == True` 인 키워드와, 매니저가 이미 같은 내용을 쓴 블록만 빠진다(KooRawKeywordDedup). 그래서 해석 표시가 된 키워드의 객체를 건너뛰면 출력에서 아예 사라진다(B4 를 자리 표시로 푸는 이유).
- **B1.** R16 *DATABASE_EXTENT_INTFOR 카드 2(NWEAR·NWUSR·NHUF·NTIED·NENG·NPEN)는 "Optional Card", 기본값 0 이다. 매니저(KooDynaDatabase)는 빈 칸을 R16 기본값으로 채운다(카드 1 은 1·1·1·1·1·1·0·0).
- **B2.** get_nodes 는 없는 절점을 None 으로 돌려주고, Element.AddNode 는 None 을 조용히 건너뛴다. 그래서 HEXA8 이 절점 8개보다 적은 채 남는다. 리뷰 G 의 DWI 출력 덱은 10-24 에 고친 옛 결함(시편 절점 누락)이 만든 것이다. 솔리드 507·셸 169 절점이 *NODE 에 없다.
- **B3.** AddContactfromDynawithID 에 `contactKeyword[0] == "CONTACT_ERODING_SURFACE_TO_SURFACE_ID"`(`*` 없음)가 있다. 분기에 한 번도 못 들어가 i 가 없다. 들어가더라도 `self.createContactErodingSurfacetoSurfacewithID`(소문자 c)는 없는 함수다.
- **B4.** 배터리 default 덱의 *LOAD_SEGMENT_SET SSID 3 은 *SET_SEGMENT_GENERAL(OPTION PART 10 11 12)이다. KMM 은 이 키워드를 해석하지 않고 원문으로만 쓴다. 하중 출력기는 세트에서 `sid` 만 쓴다.
- **B5.** KooRemapper src/assembly/ModelAssembler.cpp 4459·4461·9860행이 TIED 카드 2 를 82자 고정 문자열(`…       0.0  1.0000E+20`)로 쓴다. DT 가 12자라 71~80열이 `  1.0000E+` 가 된다. R16 "characters beyond column 80 of each line are ignored". 덱 자체가 잘못된 것이라 KMM 이 짐작해 읽지 않는다.
- **C1.** SectionShell.parse 는 블록마다 카드 1·2 만 읽는다. ICOMP=1·NIP 3·각도 0/45/90 덱을 TRANSFORM 하면 출력에 ICOMP=1 만 남고 각도 카드가 사라진다(실측 /data/koopark/Test_kmm_existing_defects/probe_shell_icomp). SectionSolid 는 이미 블록의 여러 단면을 읽는다.
- **C5.** 읽기는 키워드 줄 끝 `%`(I10)·`+`(long) 을 블록마다 `_block_formats` 에 기록하고, 요소·절점 파서에만 넘긴다. 섹션 파서는 늘 10칸으로 자른다. R16 long 형식은 줄 수가 같고 칸만 20자다(ID 카드 I20·A160). 콤마 자유형식은 카드 단위로 섞을 수 있다.
- **R16 선택 카드.** "An optional card is one that may be replaced by the next keyword card. The fields in the omitted optional data cards are assigned their default values." 필수 카드는 생략할 수 없다(B6 은 덱 오류다).

## 결정
- **A 는 새 형식 TSHELL8.** 기존 TShellMode(솔리드를 *ELEMENT_TSHELL 로 쓰는 ConvertSolidtoTShell 경로)를 그대로 쓰면, 읽은 TSHELL 이 HEXA8 이 되어 솔리드 전용 처리(작은 dt 강체화 등)에 걸린다. 얇은 FPCB 가 강체로 바뀔 수 있다. 새 형식은 그런 분기를 자연히 건너뛰고, 면 계산과 존재 판정만 들어온다.
- **셸 단면 10.3e 는 이번에 안 바꾼다.** 각도 카드만 새로 쓰는 줄이라 _real10 으로 쓴다.

## 작업 중 새로 안 것
- **C4 는 TSHELL 만의 문제가 아니었다.** PART_EXCHANGE 는 `part.section` 만 바꾸고 `part.secid` 는 그대로 둬서, 새 단면 카드는 쓰이는데 PART 카드는 옛 SECID 를 가리켰다. 모든 단면 형식이 그렇다(SOLID 실측 /data/koopark/Test_kmm_existing_defects/probe_pex_solid). `SetSection` 으로 둘 다 바꾼다. `*PIDS`(여러 파트)는 정렬 격자 변환에만 쓰이고 단면·재료 교체는 `*PID` 하나에만 적용된다. 이것은 그대로다(기능 확장).
- **D(새로 찾음) — 원문 통과 블록이 형식 표시를 잃는다.** 원문 쓰기 다섯 곳이 키워드 줄을 `f"*{kw_name}"` 로만 썼다. `*ELEMENT_DISCRETE %` 같은 I10 블록의 10칸 줄이 8칸 키워드 아래에 놓여 LS-DYNA 가 잘못 읽는다. 읽기가 블록마다 기록하던 형식을 블록 객체로 찾아 되살린다(KooRawKeywordDedup.raw_keyword_line). A 시험의 옛 출력(I10 TSHELL 블록)에서 드러났다.
  - 세트(*SET_BEAM 등)는 표준에서도 10칸이라 `%` 와 무관하다. 그리고 매니저가 해석해 다시 쓴다. 다만 long(`+`) 세트는 매니저가 10칸으로 읽어 SID 를 잃는다(아래 범위 밖).
- **A 의 Tied 감지는 맞물린 메시에서만 된다.** RobustContact 의 Tied 면 감지는 면 중심 거리(RobustContactTolerance)와 법선으로 짝을 찾는다. 리뷰 U 의 RC_tshell 덱은 솔리드 윗면 1장과 TSHELL 아랫면 2장이라(맞물리지 않음) 0 이다. TSHELL 과 무관한 알고리즘 한계다. 맞물린 덱(tests/test_tshell_element_contact.py)에서는 감지된다.
- **B5 는 KooRemapper 쪽에 수정을 요청했다(2026-11-03).** ModelAssembler.cpp 4459·4461·9860행이 82자 줄을 쓴다.

## 보았지만 범위 밖(추가)
- long(`+`)·콤마 형식은 이번에 SECTION_SHELL·SECTION_TSHELL·ELEMENT_TSHELL 만 읽는다. 다른 해석 키워드(*SET_*·*PART 등)는 여전히 10칸으로만 읽는다(예: `*SET_BEAM +` 의 SID 가 0 이 된다). 덱 전체 long(*KEYWORD LONG=Y)과 같은 일반 기능이다.

## 검증 기록
- **전체 시험(8ae3318).** 44개 가운데 42개 rc 0, test_drop_attitude_angles 는 shim 30건 통과. test_export_element_loss 는 6 FAIL 이었다. v126 의 "*NODE 고정폭" 원인 안내가 내보내기 소실 쪽에만 있었는데, B2 로 같은 덱이 읽기 소실로 바뀌어 안내가 빠진 것이다. 읽기 소실에도 안내를 찍게 하고 시험의 단계 기대를 '읽기' 로 맞췄다(7f7bf6f, 50/50).
- **말뭉치 V2(실제 덱 88건, 5625a74 ↔ 8ae3318).**
  - 같음 43.
  - rc 가 같고 다른 것 10. 주 출력 차이는 TSHELL 요소가 원문 구역에서 요소 구역으로 옮겨 간 것(같은 줄)뿐이다. 그리고 DROP 의 DropContact_OuterParts·RobustContact_SS 에 TSHELL 파트(예: 2002·2004)·면(27835 → 29587)이 더해졌다. 빠진 것은 없다.
  - 고쳐진 크래시 35. TRANSFORM 10건은 입력과 출력의 요소 줄 수가 형식별로 같다. DROP 은 14건이 rc 0, 11건이 rc 3 이다. rc 3 은 리뷰 G DWI 덱으로, 이유는 '정의 안 된 절점' 뿐이다.
  - B5 덱 1건은 원인을 짚는 ValueError 로 바뀌었다.
  - model_dump.k 는 고쳐진 사례에서 예전엔 도중에 잘려 있었다. 그래서 차이가 큰 것이 당연하다.
- **아는 불량(헤드 v129 컴파일본).** test_kmm_real_deck_crashes 15 FAIL, test_section_card_sets 14 FAIL, test_tshell_element_contact 7 FAIL 이다. C2 단위 검사는 소스 트리의 KooDynaFloat 를 가져오므로 바이너리 판정이 아니다.
- **B5 근원 해결(kooremapper-fd, 2026-11-03).** 47a2c91(출력기 — TIED 카드 2 DT 를 10칸 `   1.0E+20`, 그리고 DR 종료 카드의 `1e+20` 이 정수 칸 NOSOL 에 앉던 것)·9448448(저장된 예제 덱 8개). compat 빌드 b9d4c12d(GLIBC_2.35). 그쪽 시험 tools/regress/test_card_80col.py 는 헤드 v129 SIF 안 8c7c4f87 에서 8 FAIL(아는 불량)이다. v130 굽기에서 b9d4c12d 로 스테이징되고, SIF e2e 에서 같은 시험을 다시 본다.
- **말뭉치 W(지난 말뭉치 747건, 5625a74 ↔ 8ae3318).** 같음 734 · 다름 13 이고, 모두 설명된다.
  - 리뷰 G 쉼표 자유형식 덱 3건: 셸 단면 카드 2 `1.5,1.5,1.5,1.5` 를 예전엔 고정폭으로 잘라 두께 0 으로 읽었다(조용한 손상). 이제 1.5 다(C5).
  - 요소 소실 재현 덱 3건(V126_repro_merge·_shell, M_m024_real_three_layer·_dbg): 예전 출력에 남던 데이터 없는 빈 `*ELEMENT_SOLID`·`*ELEMENT_SHELL` 머리줄이 사라졌다. 요소를 읽을 때 버리므로 생긴 차이다(B2). 둘 다 rc 3 이다.
  - TSHELL 재현 덱 7건(TT·ED):
    - TSHELL 요소가 원문 구역에서 요소 구역으로 옮겨 갔다.
    - TSHELL 만 있는 모델의 바닥판 접촉이 SSTYP 5(전체)에서 바깥 파트 셋(DropContact_OuterParts)으로 바뀌었다.
    - **바닥판 솔리드 EID 가 TSHELL EID 와 겹치던 것(옛 1~1000 대 TSHELL 1·2)이 풀렸다**(새 3~1002).
    - I10(`%`) TSHELL 블록이 있는 덱은 기존 "입력 요소 카드가 I10 이면 출력도 I10" 규칙이 이제 적용되어, 솔리드도 I10 으로 나간다(연결은 같다).

## 적대 리뷰 W (2026-11-03) — 🔴 2 · 🟡 6, 모두 고침
- **🔴1 단면 블록 빈 줄 → 유령 단면(76b14ff).** 카드 묶음 읽기가 블록 끝·앞·사이 빈 줄을 다음 단면 카드 1 로 읽었다. SECID 가 빈 단면이 maxid+1 을 받아 실제 단면 번호를 밀어냈고, 파트가 유령을 가리켰다(rc 0, 경고 없음 — v129 회귀). 카드 1 자리·블록 끝 빈 줄은 건너뛰고 센다. SECID 빈 카드 묶음은 단면으로 읽지 않는다.
- **🔴2 *PART_COMPOSITE_TSHELL·*PART_CONTACT 파트의 TSHELL 소실(250cc54).** 해석된 파트에 없는 PID 의 줄은 소실이 아니라 원문으로 남긴다. 원문 블록과 형식 목록을 같이 걸러 그 줄만 남기고, 해석 표시를 푼다. 리뷰 탐침 출력이 v129 와 바이트까지 같다. *ELEMENT_TSHELL_BETA 등 변형이 원문으로 남으면 접촉에서 빠진다고 알린다.
- **🟡3 PlaneGraded 자동 바닥판(7cec287).** TSHELL 파트를 표본에서 뺀다(v129 와 같은 크기).
- **🟡4 수동 강체화(b568567).** TSHELL 강체 파트에 TSHELL 단면을 준다. 다른 종류에도 있는 EID 의 TSHELL 은 건드리지 않고 알린다.
- **🟡5·🟡6 원문 표시(9887ebb).** I10 블록에는 늘 '%' 를 붙인다(일반 모드 기록기는 '*KEYWORD' 만 쓴다). '-' 는 'std' 로 기록해 되살린다.
- **🟡7 PART_EXCHANGE + ConvertHexato(3244b89).** 준 TSHELL 단면을 그대로 쓴다.
- **🟡8 셋 번호 충돌(ac843e3).** 해석하지 않는 *SET_SEGMENT_*·*SET_PART_*·*SET_NODE_* 원문의 번호와 자리 표시 SSID 를 셋 매니저에 예약한다.
- **⚪ 반영.**
  - KooDynaFloat 의 D 섞인 글은 예전처럼 기본값으로 돌린다(dac9b98).
  - TSHELL 발열원은 원인을 밝혀 멈춘다(390fce6).
  - TSHELL 변형은 알린다(250cc54).
- **⚪ 그대로 둠.**
  - *CONTACT_ERODING_*_ID 의 ERODING 카드(필수 조건부 카드)가 빠진 덱의 IndexError — 덱 오류다.
  - 콤마·long *NODE 는 여전히 못 읽어, B2 가 요소를 원인과 함께 버린다(rc 3, 고정폭 안내).
  - HEXA8 파트에 TSHELL 단면을 변환 없이 붙이는 PART_EXCHANGE 는 경고하지 않는다.
- **아는 불량(8ae3318 스냅숏).** test_section_card_sets 4 FAIL, test_tshell_element_contact 7 FAIL, test_kmm_real_deck_crashes 7 FAIL 이다. 고친 트리는 23/23·19/19·36/36 이다.
- **최종 트리(dac9b98) 검증.**
  - 전체 시험: 44개 모두 통과(test_drop_attitude_angles 는 shim).
  - 말뭉치 V3(실제 덱): 사례별 rc 가 V2(8ae3318) 와 같다. 예외는 072 하나로, kooremapper-fd 가 그 예제 덱의 82자 줄을 고쳐 입력이 바뀐 것이다(두 트리 모두 rc 3).
  - V2 대비 새 출력 차이는 29파일이고, 모두 리뷰 W 수정의 의도한 결과다.
    - `*KEYWORD i10=y` 덱(KooRemapper load 예제 4건)의 원문 블록 CONTROL_IMPLICIT_*·CONTACT_TIED_*_TITLE 에 '%' 가 붙었다(🟡5).
    - 배터리 gas wound 2건에서 RobustContact_SS 번호가 315 → 504 가 됐다. 덱의 원문 *SET_SEGMENT_GENERAL 503 을 예약했기 때문이다(🟡8). 예전 315 는 우연히 안 겹쳤을 뿐이다.

## 집중 리뷰 X (2026-11-03, 대상 dac9b98) — 🔴 1 · 🟡 2 · ⚪ 6
- **🔴1 _TITLE 단면 블록의 빈 줄 → 유령 단면(1227bac).** 76b14ff 는 _TITLE 이 아닌 블록만 고쳤다. _TITLE 블록에서는 단면 사이 빈 줄을 다음 제목으로, 진짜 제목을 SECID 로 읽었다. 정수가 아닌 SECID 가 KooDynaInt 로 0 이 되어 maxid+1 을 받았고, 뒤의 실제 단면 번호를 밀어냈다(rc 0).
  - 제목 자리 빈 줄 다음 줄이 정수가 아닌 제목이고, 그다음 줄이 정수 SECID 카드이면 그 빈 줄을 건너뛴다. 아니면 LS-DYNA 처럼 빈 제목으로 둔다.
  - SECID 가 비었거나 양의 정수가 아닌 카드 묶음은 단면으로 만들지 않고 알린다. KMM 은 이름 SECID 를 지원하지 않는다.
  - 범위 밖으로 보고된 *SECTION_SOLID(_TITLE) 의 같은 꼴(블록 끝 빈 줄 → 유령 NewSolidSection, v129 부터)도 같은 규칙으로 고쳤다.
- **🟡2 셋 번호 예약이 이상한 제목에서 죽는다(11d208e).** `isdigit` 은 참인데 int() 가 못 읽는 글('--2024'·'①②')에서 ValueError(rc 1)가 났고, *_TITLE 블록의 제목 줄까지 봤다. 정수 정규식으로 보고 제목 줄은 뺀다.
- **🟡3 요소 셋 계열은 예약하지 않았다(11d208e).** THERMAL 발열원 *SET_SOLID 가 원문 *SET_SOLID_GENERAL 과 같은 번호를 받았다. *SET_SOLID·SHELL·BEAM·TSHELL·DISCRETE_* 를 partManager.elementManager.maxSID 에 예약한다.
- **⚪4 long 셋(11d208e).** long('+') 원문 블록은 20칸으로 SID 를 읽는다.
- **⚪5 데이터 줄까지 예약(11d208e).** 블록마다 첫 데이터 줄(카드 1 의 SID)만 본다. 절점·파트 번호까지 잡으면 새 셋 번호가 1e8 을 넘어 *ELEMENT_MASS_NODE_SET 의 8칸 NSID 가 넘칠 수 있었다.
- **⚪6 TSHELL 원문 통과 안내(97aaff9).** 어떤 *PART 계열에도 없는 PID 나 *PART 가 없는 덱(dynain)에서도 "PART_COMPOSITE_TSHELL·PART_CONTACT 등" 이라고 적어 오해를 불렀다. 덱에 *PART 가 없으면 그렇게 알리고, 아니면 "…이거나 덱에 *PART 가 없는 PID" 로 적는다. 동작은 v129 처럼 원문 통과 그대로다.
- **⚪ 그대로 둠.**
  - ⚪7 I10=Y 덱에서는 모든 원문 블록에 '%' 가 붙는다. 뜻은 전역 I10=Y 와 같다.
  - ⚪8 PlaneGraded·수동 강체화·TSHELL 발열원 판정은 `type == "TSHELL8"` 로만 한다. 같은 실행에서 ConvertHexato,TShell 로 만든 HEXA8 TShellMode 파트는 빠진다(v129 와 같다).
- **아는 불량(dac9b98 스냅숏).** test_section_card_sets 3 FAIL, test_kmm_real_deck_crashes 3 FAIL 이다. 고친 트리는 28/28·39/39 다.
- **리뷰 W 탐침 재실행(리뷰 X 항목 7).** p3_sec·p11_partvar·p13b/c 배터리 TSHELL·p2_floor·p6_rigidify·p5_i10·p10_pex·p14_ssid 모두 기대대로다. p4_kdf(입력 101,475개)에서 v129 에서 값으로 읽히던 입력은 모두 같은 값이고, 새로 예외가 나는 입력은 0건이다.
- **말뭉치 W2(5625a74 ↔ dac9b98).** 같음 734 · 다름 13 이다. 다른 13건의 출력 해시가 W(8ae3318) 와 한 줄도 다르지 않다. 리뷰 W 수정은 지난 말뭉치 출력을 바꾸지 않았다.

## 집중 리뷰 Y (2026-11-03, 대상 97aaff9) — 🟡 3 · ⚪ 2
- 정상 덱에서는 회귀가 없었다. 실제 덱 4,675개의 *SECTION_SHELL·TSHELL·SOLID(_TITLE) 블록 26,070개를 dac9b98 과 97aaff9 로 읽은 결과가 같았고, 예외·새 경고가 0이었다(모두 정수 SECID).
- **🟡1 정수값 실수 SECID 를 버렸다(c22d68d, 1227bac 회귀).** `_secid_bad` 가 정수 정규식만 받아 SECID '1.0'(Altair 등)과 R 형 *PARAMETER 치환값 '3.0' 을 버렸다(v129·dac9b98 은 받았다). KooDynaInt 처럼 정수값 실수를 받는 `_whole_int` 를 두고 `_first_int` 도 같이 쓴다. '1.5' 같은 정수 아닌 수는 그대로 거절한다.
- **🟡2 빈 제목 원문 셋의 번호 예약이 빠졌다(c70259e, 11d208e 회귀).** 빈 줄을 먼저 거른 뒤 _TITLE 제목을 떼어, 빈 제목 블록에서는 SID 줄이 빠졌다. DROP RobustContact_SS 가 원문 *SET_SEGMENT_GENERAL_TITLE 2 와 같은 번호를 받았다(rc 0). 제목을 먼저 떼고 빈 줄을 거른다.
- **🟡3 _TITLE 단면 사이 빈 줄이 2개 이상이면 어긋났다(c22d68d, X 🔴1 덜 고침).** 셸은 3줄 짝이라 진짜 제목이 카드 2 로 먹혀 뒤 단면이 모두 사라졌다. 빈 줄 덩어리 다음이 정수 아닌 제목 + 정수 카드면 덩어리 전체를, 바로 정수 카드 1 이면 마지막 빈 줄 하나만 빈 제목으로 남기고 건너뛴다. 숫자로 시작하는 제목('2024')은 LS-DYNA 도 잘못 읽으므로 그대로 둔다.
- **⚪4 안내 문구(fcae54f).** *PART_COMPOSITE_TSHELL 만 있는 덱도 "이 덱에 *PART 가 없어" 로 찍혔다. "KMM 이 파트로 읽은 *PART 가 없어(dynain 이거나 *PART_COMPOSITE_TSHELL 등만 있는 덱)" 로 고쳤다.
- **⚪5 콤마·long *SECTION_SOLID(_TITLE)(c22d68d, 기존 결함).** 예전엔 콤마 줄이 유령 단면이 됐고, 1227bac 는 경고 뒤 버렸다. 셸 단면(C5)과 같이 블록 형식을 넘겨 `_card_fields` 로 읽는다. 고정폭 줄은 예전과 같다.
- **⚪ 그대로 둠.**
  - *SECTION_SOLID ELFORM 101~105 사용자 요소 카드는 카드 1 로 읽혀 유령 단면이 될 수 있다(v129 도 같음). 셸처럼 원문 카드로 남기려면 솔리드 사용자 요소 카드 배치를 매뉴얼로 확인해야 해서 이번에는 보고만 한다.
  - 파트가 없는 SECID 를 가리키면 지금은 경고만 찍는다. rc 3 으로 올리면 KMM 이 해석하지 않는 단면 종류(*SECTION_DISCRETE 등)를 가리키는 정상 파트까지 걸린다.
- **아는 불량(97aaff9 스냅숏).** test_section_card_sets 4 FAIL, test_kmm_real_deck_crashes 1 FAIL, test_tshell_element_contact 1 FAIL 이다. 고친 트리는 33/33·39/39·20/20 이다.
- **말뭉치 W3(5625a74 ↔ 97aaff9).** 450건까지 같음 447 · 다름 3(W 와 같은 쉼표 덱 3건, 해시까지 같음)이었다. 최종 트리로 W4 를 돌리려고 멈췄다.
- **전체 시험(97aaff9).** 44개 모두 통과(test_drop_attitude_angles 는 shim 30건).
- **말뭉치 V5(실제 덱 88건, 5625a74 ↔ fcae54f).** V3(dac9b98) 와 사례별 출력 해시가 같고, 다른 것은 019 한 건이다.
  - 019 는 KooRemapper offset 예제 03_tshell_result.k 의 낡은 사본(09-17, Test_CLIHelp_e2e)이다. 그쪽이 ff52566 에서 고치기 전 출력이라 *SECTION_TSHELL 에 셸 카드 2(t1~t4 1.5)가 붙어 있다.
  - dac9b98 은 그 줄을 다음 단면 카드 1 로 읽고 SECID '1.500e+00' 을 반올림해 유령 단면 2 를 만들었다. 지금은 정수가 아니라고 알리고 버려, 출력이 v129 와 같다(리뷰 X 🔴1 의 의도). 지금 KooRemapper 예제는 한 줄 섹션이라 알릴 것은 없다.
  - 두 판 모두 rc 3 인데, 원인은 덱 자체(솔리드 600개의 PID 에 *PART 없음)다.
  - 고쳐진 TRANSFORM 10건의 요소 줄 수(count_elems)도 V3 와 같다.

## 집중 리뷰 Z (2026-11-03, 대상 fcae54f) — 🔴 0 · 🟡 1(기존) · ⚪ 2
- 회귀는 없었다.
  - 말뭉치 4,675 파일의 단면 블록 26,070개가 dac9b98·97aaff9 와 모두 같았다.
  - 실제 덱 6개의 model_dump.k·model_trans.k 가 97aaff9 와 바이트까지 같았다.
  - 무작위 정상 블록 44,855개가 정답과 100% 같았다.
  - `_whole_int` 가 받은 무작위 78,669개는 모두 KooDynaInt 와 같은 정수였다.
- **🟡1 *PART 정수 칸의 정수값 실수(694494c, v129 부터).** `_part_int_or_blank`·`_part_int_or_empty` 가 int() 만 써서 '3.0'(R 형 &sec)·'82.0' 을 0 으로 읽었다. 단면은 c22d68d 부터 그 SECID 를 받는데 PART 는 SECID 0 을 내보냈고(rc 0), PID '93.0' 파트는 빠졌다. int() 가 실패할 때만 `_whole_int` 로 받는다(예전 값은 그대로). 말뭉치 5,930 덱의 PART 카드에서 이 꼴은 0건이다.
- **COHOFF·GASKETT 칸(694494c, v129 부터 — 리뷰 Z 참고 항목).** KooSection 이 *SECTION_SOLID(_TITLE) 카드 1 의 빈 칸 4·5번째에서 읽어, 덱 값(7·8번째)이 출력에서 0.000e+00 이 됐다. 쓰기와 같은 7·8번째 칸에서 읽는다.
  - 말뭉치 835덱에 0 이 아닌 COHOFF·GASKETT 는 없다. 그래서 출력이 바뀌는 덱도 없다.
  - 덤프(model_dump.k) 기록기는 COHOFF·GASKETT 를 4·5번째 칸에 쓴다(확인용 사본이라 그대로 둠). 덤프를 다시 읽으면 그 값은 예전처럼 0 이 된다.
- **⚪2 그대로 둠.** 빈 줄로 띄운 _TITLE 단면의 제목이 '2.0'·'1e3' 처럼 정수값 실수 꼴이면 카드 1 로 읽힌다. 숫자 제목('2024')과 같은 한계이고 LS-DYNA 도 그렇게 읽는다. 말뭉치 0건이다.
- **⚪3 그대로 둠(기존 한계).** *SECTION_SOLID ELFORM 101~105 의 속성 카드('1.0 2.0')가 다시 유령 단면이 된다. 97aaff9 는 '1.0' 을 거절해 우연히 막고 있었다. v129 와 같다.
- **참고(범위 밖).** 콤마 *MAT_RIGID 카드 2('1,7,7')에서 ValueError(KooDynaKeyword 8621, 배터리 meshless structure.k, 두 판 같음).
- **아는 불량(fcae54f 스냅숏).** test_section_card_sets 2 FAIL 이다(파트 91·92 SECID 0·93 소실, COHOFF·GASKETT 0). 고친 트리는 36/36 이다.
- **말뭉치 W4(5625a74 ↔ fcae54f).** 401건까지 같음 398 · 다름 3(W 와 같음)이었다. 최종 트리로 W5 를 돌리려고 멈췄다.
- **전체 시험(fcae54f).** 44개 모두 통과(shim 30건).
- **말뭉치 W5(지난 말뭉치 747건, 5625a74 ↔ 694494c — 최종 트리).** 같음 733 · 다름 14 · 새 크래시 0. 13건은 W 와 출력 해시까지 같고, 더해진 것은 L_P7_long 하나다.
- **말뭉치 W5 의 L_P7_long(덱 전체 `*KEYWORD LONG=S`, 범위 밖).** v129 는 20칸 *SECTION_SOLID 줄을 10칸으로 읽어 SECID 빈 유령 NewSolidSection 1(쓰레기 COHOFF 1.0)을 만들고 바닥판 단면을 2 로 밀었다. 지금은 1227bac 규칙대로 빈 SECID 카드를 단면으로 만들지 않고 알려, 바닥판 단면이 1 이다. 두 판 모두 rc 3 이다(*PART 도 잘못 읽어 요소 소실 — 이 덱의 출력은 쓰지 말라고 이미 알린다).
- **말뭉치 V6(실제 덱 88건, 5625a74 ↔ 694494c).** 출력 176개(사례 × 옛·새)가 V5(fcae54f) 와 바이트까지 같다. 694494c 는 실제 덱 출력을 바꾸지 않는다. V3 대비 차이는 019 한 건(위 V5 설명) 그대로이고, count_elems 도 같다.

## 빌드·배포 기록 (v130)
- **굽기 전 확인(21:1x).** 헤드 /opt = compute-node-images = v129(79275a4f), 마지막 tar v129, 잡 없음, 가용 36 GB. KooRemapper 스테이징은 굽기에서 8c7c4f87 → b9d4c12d(GLIBC_2.35, `stage-to-appt313.sh --check`).
- **빌드(52fbded, 21:19~22:13).** build_without_automatedmodeller.sh --clean 을 캡 scope(MemoryMax 24G·adj 1000)로 돌렸다(BUILD_RC 0, 최저 가용 24.2 GB). 2.35 컨테이너에서 다시 돌고, 가드가 밖에서 /data·SIF 소스 트리에 배포했다.
  - KMM 36ab6c8e → **0a832f04**(22:03). KAM 은 580f028e 그대로다.
  - KooChainRun 6b19f55d → **74a62ce8**(22:12). Runner 소스는 v129 뒤로 바뀌지 않았다. 배포 폴더 348개 파일 가운데 .bin 하나만 다르고, 차이는 31바이트다.
    - ELF 빌드 ID 20바이트가 다르다.
    - Nuitka 상수 묶음 안에서 원소 두 개(`M`·`Otuple`)의 직렬화 순서가 바뀌었고, 그 체크섬 4바이트가 달라졌다. 문자열 집합 순서는 파이썬 해시 무작위화를 따르므로, 집합 내용이 같아 동작도 같다.
    - v129 에서 sha 가 같았던 것은 원소 2개 순서가 우연히 같았기 때문이다.
- **호스트 e2e(컴파일본).** 바이너리는 NFS 와 SIF 소스 트리가 같다. 10절점·파일끝 판정기 8/8, KMM 시험 17종 0 FAIL, KCR 결과 귀환·--help·sphere 4종 통과다. 같은 최종 시험에서 헤드 v129 는 크래시 21·단면 26·TSHELL 13 FAIL 이다(아는 불량).
- **SIF v130(22:28).** sha256 9d166fd0, 1,581,842,432 B 이고 compute-node-images 도 같다. tar v130 은 1,346,209,884 B 이고, Drive(ApptainerImages:SmartTwinPreprocessor/)에 올렸고 메일은 sent OK 다. KooRemapper 는 굽기 첫 단계에서 8c7c4f87 → b9d4c12d 가 됐다.
- **SIF e2e.** SIF 안 KMM·KAM·KCR 이 소스 트리와 같다. KooRemapper b9d4c12d 의 test_card_80col 은 18/18 이다(v129 SIF 는 8 FAIL). 10절점 8/8, KMM 시험 17종 0 FAIL, KAM 곡선 식도 통과다.
- **push(52fbded).** b72807f..52fbded 다.
- **헤드 /opt(22:51).** v130(9d166fd0)이 됐다. v129(79275a4f)는 하드 링크 `SmartTwinPreprocessor_backup_20261103_225131.sif` 다. 교체 뒤 헤드 /opt 껍데기로 KMM 시험 5종과 KooRemapper 80열 시험이 모두 통과했다. 노드(node001·002·viz)는 down 이라 미배포다.
- **알림.** kooremapper-fd 에 v130·b9d4c12d·시험 결과를 보냈다. H8·H9 캠페인 쪽은 보고 세션을 특정하지 못해, 사용자에게 전달 글을 드린다(v130 부터 TSHELL FPCB 가 접촉 집합에 들어가 v129 와 결과가 달라진다).

## 이번 범위 밖으로 남긴 기존 결함(리뷰 W·X·Y·Z 에서 보고, v129 도 같음)
- DECOMPOSE_K 는 원문 요소만 쓰는 절점을 출력하지 않는다(TSHELL 원문 통과 파트의 절점 50개 소실).
- I10=Y 덱의 DropSet.k 는 `*KEYWORD I10=Y` 를 남기는데 *ELEMENT_MASS 는 8칸으로 쓴다.
- *DEFINE_CURVE 의 콤마 점 줄에서 ValueError(KooDefine._curve_points) — 배터리 예제 덱이 rc 1.
- IMPORT_MERGE_K 는 가져올 덱에 *SET_NODE_LIST·*SET_PART_LIST 가 있으면 죽고, 가져온 덱의 원문 블록을 버린다. psid 오프셋은 늘 0 이다.
- FastDOE 의 Pre/PostNodes 기록기는 원문 블록을 쓰지 않는다.
- *INITIAL_STRESS_TSHELL 파서가 없어 DTI 가 dynain 의 TSHELL 응력을 버린다.
- *PART_CONTACT 로 정의한 솔리드는 rc 3 소실 그대로다.
- *CONTACT_ERODING_*_ID 의 ERODING 카드가 빠진 덱의 IndexError(덱 오류).
- 콤마·long *NODE 는 못 읽는다(B2 가 요소를 원인과 함께 버린다, rc 3).
- 셸 단면 실수의 10.3e 출력, *KEYWORD LONG=Y, MIRROR 의 TSHELL, ICOMP 판정의 TShellMode 파트.
- *SECTION_SOLID ELFORM 101~105 사용자 요소 카드(유령 단면이 될 수 있다).
- 덤프(model_dump.k)의 *SECTION_SOLID COHOFF·GASKETT 칸 배치(4·5번째), 콤마 *MAT_RIGID 카드 2 의 ValueError.
- 예전 미수정분: *ELEMENT_SHELL_THICKNESS·IMPORT_MERGE_K PART.secid·NODUMP·DWI OutsideRigid 위치.
