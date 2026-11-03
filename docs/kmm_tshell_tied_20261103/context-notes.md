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
