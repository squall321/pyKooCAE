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
