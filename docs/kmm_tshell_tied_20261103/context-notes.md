<!-- KMM TSHELL·TIED 보존 — 결정과 근거 -->
# 결정 노트 — KMM TSHELL 단면·TIED 두께 보존 (2026-11-03)

## 조사에서 확인한 사실
- **TSHELL 읽기(KooSection.py KooSectionManager).** *SECTION_TSHELL·*SECTION_TSHELL_TITLE 두 갈래 모두 elform·shrf·nip·qr·icomp·tshear 를 지역 변수로만 읽는다. sec 에는 하나도 넣지 않는다.
  - 칸 차례가 틀렸다. qr 을 [4](실제 PROPT), icomp 를 [5](실제 QR), tshear 를 [6](실제 ICOMP)에서 읽는다.
  - 각도 카드는 틀린 icomp 로 판단해, 실제 ICOMP=1 덱에서도 대개 각도를 버린다.
- **TSHELL 키워드 클래스(KooDynaKeyword SectionTShell·SectionTShellTitle).** 읽기 칸은 맞다(ICOMP=6번 칸). 이 덤프 경로가 아니라 단면 매니저가 문제다.
- **출력.** KooSectionTShell.GenerateDynaKeyword 는 늘 *SECTION_TSHELL_TITLE 로 쓰고, 실수는 10.3e 다. 셸 단면도 10.3e 다(유효숫자 4자리).
- **TIED 0.005.** KooDynaAdvancedModification 의 RobustContact 블록이 `tied_params.setdefault("SAST", 0.005)`·`setdefault("SBST", 0.005)` 뒤 ModifyTiedParameters 로 모든 TIED 접촉의 SST·MST 를 바꾼다(3d3f50c, 4-22).
  - 근거 기록은 없다. 메모리에 남은 예시 시나리오의 tied_options(SAST 0.005·SBST 0.005·THKOPT 1)가 그대로 기본값이 된 것으로 보인다.
  - KooChainRun(StepConfigBuilder)은 tied_options 를 받은 그대로 넘기고 자체 기본값이 없다.
- **R16.** 접촉 SAST·SBST 는 셸·빔의 접촉 두께를 덮어쓴다(솔리드 무관).
  - TIED 묶기 기준(General Remarks 4)은 δ = max(0.6×(노드 두께 + 세그먼트 두께), 0.05×세그먼트 최소 대각선)이다. 솔리드는 노드 두께 0, 세그먼트 두께 = 부피/면적이다. 음수 두께면 δ = |δ1| 이다.

## 결정
- **TSHELL 실수는 _real10 으로 쓴다.** 값을 지키는 가장 짧은 10칸 표기다. 10.3e 는 5/6 을 0.8333 으로 줄인다. "덱 값 그대로" 가 요청이라 값 손실이 없는 쪽을 쓴다. 셸 단면은 이번에 건드리지 않는다(보고 없음).
- **각도는 NIP 개만 쓴다.** 더 쓰면 LS-DYNA 가 남는 카드를 다음 단면의 카드 1 로 읽는다.
- **TIED 는 TiedOptions 에 SAST·SBST(또는 SST·MST)를 줄 때만 바꾼다.** 기본값을 없애 덱 값이 남는다. 바꿀 때는 접촉 수와 값을 로그에 남긴다.

## 작업 중 새로 안 것 (2026-11-03)
- **키워드 읽기도 각도를 버렸다.** 처음 노트에는 "읽기 칸은 맞다" 고 적었지만, SectionTShell·SectionTShellTitle 의 `parameters[6] == "1"` 은 늘 거짓이었다. parse_whole 은 칸을 공백째("         1") 돌려준다. 단면 매니저만 고친 첫 판에서 각도가 여전히 빠져 알았다. `_tshell_icomp_on` 으로 실수 비교한다(864524d).
- **DROP 시험 옵션.** DROP_ATTITUDE 는 InitialVelocity·InitialAngularVelocity 6키가 없으면 KeyError 로 멈춘다. 시험 옵션에 넣었다(제품 동작과는 무관).
- **TIED 로그.** TiedOptions 로 바꿀 때만 "RobustContact: TiedOptions 로 TIED 접촉 N개의 … 를 바꿨다" 를 찍는다. 안 주면 아무 줄도 없고 덱 값이 남는다.
- **TiedOptions 는 RobustContact,True 일 때만 읽힌다.** 예전과 같다. help 에 그렇게 적었다.

## 말뭉치·배포 준비
- 옛 트리 645098e(= v126·v127 KMM 코드, occProject 는 015ac05 이후 그대로), 새 트리 0d9c65b. 둘 다 /data/koopark/Test_kmm_tshell_tied/ 에 git archive 로 고정했다. 다른 세션이 작업 트리를 고쳐도 섞이지 않는다.
- 지난 말뭉치 덱 739건에는 *SECTION_TSHELL·RobustContact 덱이 하나도 없다. 그래서 실제 TSHELL·TIED 덱을 찾아 따로 넣는다.
- 굽기 전 상태: 헤드 /opt = compute-node-images = v127(4d31651f), /data 마지막 tar v128 → 다음 v129. KooRemapper 스테이징 8c7c4f87 그대로(--check). KCR·KAM 소스는 v127 빌드(d2b6d0f) 뒤 그대로라 빌드는 build_without_automatedmodeller.sh(KMM+KCR) 로 한다.
- **말뭉치 V(실제 덱).** /data·KooDynaAdvanced·KooRemapper 예제에서 *SECTION_TSHELL·*CONTACT_TIED_ 덱 1008개를 찾았다. 독립 덱(*NODE·*ELEMENT 있음, INCLUDE 없음, 50 MB 이하) 가운데 단면·접촉 블록 내용이 고유한 122개를 골랐고, 그중 78개를 돌린다. TSHELL 18개는 TRANSFORM, TIED 70개는 DROP_ATTITUDE+RobustContact 다. 배터리 TIED 전용 덱은 TIED 개수가 다른 6개만 넣었다. 판정은 다른 블록이 TSHELL 단면·TIED 카드 3(SST·MST)뿐인지, 그리고 새 출력의 TSHELL 값이 입력 덱과 같은지다.

## 보았지만 범위 밖
- KooRemapper 예제 replace_test/tshell_base.k 는 *SECTION_SHELL 카드 2(T1~T4)가 없는 합성 덱이다. KMM 키워드 읽기(SectionShell.parse)가 IndexError 로 rc 1 이다. 옛 코드도 같다(TSHELL 수정과 무관).
- **말뭉치 V 결과(88건).** 의도한 다름 45 · 같음 43 · 예상 밖 0 이다.
  - TSHELL: 실제 덱 8개가 경로를 지났다. 다른 블록은 TSHELL 단면뿐이고, 새 출력 값은 입력 덱과 같다. 이 덱들은 SECID·ELFORM 만 있는 짧은 카드라, 바뀐 것은 실수 표기(1.000e+00 → 1.000)뿐이다. 기본값이 아닌 값은 합성 시험(tests/test_tshell_section_preserve.py)이 본다.
  - TIED: 37개에서 다른 블록이 카드 3 SST·MST 뿐이다(옛 0.005). 새 값은 입력 덱 값이고, 접촉 수는 옛 출력과 같다(RobustContact 의 중복 TIED 제거는 그대로). 같음 7건은 입력에 이미 0.005 가 있던 KMM 출력이거나, 옛 덮어쓰기가 닿지 않던 *CONTACT_TIED_SURFACE_TO_SURFACE_TITLE 꼴이다.
  - rc 1 36건은 옛 코드도 같은 오류다(아래). 그래서 배터리 TSHELL 덱 10개는 TSHELL 경로까지 가지 못했다.
- **보았지만 범위 밖 — 실제 덱에서 KMM 이 죽는 기존 결함(옛 코드도 같음).**
  - KooDynaKeyword parse IndexError 14건 — 배터리 생성기 덱. 예: *DATABASE_EXTENT_INTFOR 카드가 하나뿐인데 카드 2 를 찾는다(DatabaseExtentIntfor.parse).
  - KooElement.SetBoundaries IndexError 11건 — 리뷰 G DWI 출력 덱의 DROP+RobustContact.
  - KooContact.AddContactfromDynawithID UnboundLocalError 'i' 6건 — 배터리 wound 덱.
  - KooLoad.AddLoadfromDyna KeyError 3 4건 — 배터리 default 덱.
  - KooDynaFloat '  1.0000E+' 1건 — KooRemapper offset/04_shell_result.k(10칸을 넘는 실수).

## 적대 리뷰 U (2026-11-03) — 🔴 없음
- 실제 TSHELL 덱 TRANSFORM 3·DROP_ATTITUDE 1, 단위 탐침 28건. 탐침은 /data/koopark/review_U/ 에 있다.
- **🟡1 고침(aa0e07c).** NIP 0·ICOMP 1 이면 각도를 0개 읽어 각도 카드가 사라졌다. R16 NIP "EQ.0: set to 2 integration points" 에 맞춰 각도만 2개로 센다. NIP 칸은 0 그대로 쓴다. 키워드 클래스(SectionTShell.parse)는 ICOMP 가 켜지면 블록의 남은 줄을 다 읽으므로 이 문제가 없다.
- **🟡2 고침(5625a74).** 0d9c65b 의 로그는 받은 키를 그대로 "바꿨다"고 찍었다. 칸 이름은 대문자만 맞아 `TiedOptions.sast` 는 아무것도 안 바꾸는데도 그랬다.
  - 이제 ModifyTiedParameters 가 맞는 칸이 없는 키와 SST·MST 와 같이 준 SAST·SBST 를 "⚠ … 무시한 키" 로 적는다. 바꿀 칸이 없으면 접촉을 세지 않는다.
  - 마지막 줄은 실제로 바꾼 칸과 값만 적는다("TIED 접촉 N개의 SST=0.1 를 바꿨다").
  - 키를 대문자로 바꿔 주는 것은 하지 않았다. 지금 조용히 무시되는 키가 갑자기 적용되는 동작 변화라서다. 경고로 보이게만 했다.
- **⚪7 고침(5625a74).** help 와 docs/SmartTwinPreprocessor_Programs.txt 의 "SAST/SBST 디폴트 0.005" 를 고쳤다. 바뀌는 접촉 꼴(*CONTACT_TIED_SURFACE_TO_SURFACE(_OFFSET)(_ID)·SHELL_EDGE_TO_SURFACE_BEAM_OFFSET(_ID))과 대문자 규칙도 적었다. KooSlurm MCP 사본 meta.yaml 의 옛 help 문구는 그쪽 리포라 손대지 않았다(0.005 를 넣지는 않는다).
- **🟡3 기존 결함, 사용자 결정으로 넘김.** KooMeshImporter 는 *ELEMENT_TSHELL 을 읽지 않고 원문으로만 다시 쓴다. 그래서 TSHELL 파트는 DROP_ATTITUDE 의 SINGLE_SURFACE·바닥판 Outer·RobustContact 면·Tied 면 감지에서 모두 빠진다. 옛 코드도 같다.
  - H8·H9 FPCB 가 *ELEMENT_TSHELL 이면, 단면 값이 맞아진 뒤에도 FPCB 에 접촉이 없다.
  - 고치려면 TSHELL 요소를 읽어 면을 만들어야 한다. 이는 공유 경로(내보내기·요소 소실 장부)를 건드리는 설계 결정이다. 이번 배포에는 넣지 않았다.
- **⚪ 참고만(기존·드묾).**
  - 한 *SECTION_TSHELL 키워드 아래 단면이 여럿이면 두 번째부터 사라진다(키워드 리더가 블록마다 카드 1 하나만 읽는다).
  - QR·각도 칸의 Fortran 줄임 지수('4.5+01')에서 KooDynaFloat 가 ValueError 로 죽는다. 이 칸을 이제 읽게 되어 드러났다. 조용히 틀리는 쪽이 아니라 크게 죽는 쪽이다.
  - ICOMP 판정이 두 곳에서 다르다('0.6' 같은 잘못된 값만 해당). 키워드 리더는 float==1, 단면은 KooDynaInt 반올림이다.
  - PART_EXCHANGE 는 TSHELL 단면을 파트에 붙이지 못한다(AddSectionfromDyna 가 None).
- **말뭉치 U 를 최종 트리로 다시 돌리지 않는 이유.** 0d9c65b → 5625a74 차이는 두 가지뿐이다. 하나는 ICOMP 1·NIP 0 이하 TSHELL 의 각도 개수, 다른 하나는 TiedOptions 를 준 RobustContact 의 로그·무시 키다. 말뭉치 U 덱에는 *SECTION_TSHELL 도 RobustContact 도 없다(TT_ 재현 덱 제외 — 그 출력은 같은 칸을 같은 값으로 바꾼다). 실제 덱 말뭉치 V 와 전체 시험은 최종 트리로 다시 돌린다.
