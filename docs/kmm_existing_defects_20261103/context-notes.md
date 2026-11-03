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
