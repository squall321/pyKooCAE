<!-- KMM v126 묶음 — 결정과 근거 -->
# 결정 노트 — KMM v126 묶음 (2026-10-27)

## 조사에서 확인한 사실
- **merge 덱의 요소 소실.** `KooRemapper/examples/merge/three_layer.k` 의 *NODE 는 NID 를 10칸에 쓴다(LS-DYNA 는 8칸).
  - KMM 은 앞 8칸을 비었다고 읽어 절점 36개를 NID 0 하나로 뭉친다.
  - 요소는 등록된다(개수 검사 "입력 12 = 등록 12"). 그런데 절점 목록이 짧아 솔리드 출력기에서 IndexError 가 나고, 12개 모두 '출력 실패 — 스킵' 이 된다. 결과는 rc 0 이다.
- **셸·빔·질량 출력기는 예외를 받지 않는다.** 같은 덱을 셸로 만들면 IndexError 트레이스백으로 rc 1 이다. 시끄럽지만 이미 비 0 이다.
- **러너는 KMM rc≠0 이면 멈춘다.** LargeScaleDOE(`exit $KM_EXIT`)·DWI(`FAIL (KooMeshModifier)`)·Cumulative(`return None`)·PartValidation·DOEParallel 이 그렇다. MCP 도 rc≠0 은 실패로 본다.
- **KMM 종료 코드는 지금 0·1 뿐이다.** gmsh 를 못 찾으면 `sys.exit()` 로 rc 0 인 곳이 13곳 있다(KooMeshManagerGMSH·KooPart). 이번 범위 밖이라 알리기만 한다.
- **KMM 바이너리에 PyYAML 이 이미 들어 있다.** dist 에 yaml/ 이 있고, .bin 에 yaml.constructor 가 있다. 간접 포함이라 KMM 코드에서 직접 import 해 빌드가 늘 따라가게 한다.
- **KAM 식.** `*define` 의 curvefunction 블록이다. 식 줄은 쉼표로 나눠 1칸일 때만 식이라, 식에는 쉼표가 없다(여러 인자 함수는 못 쓴다).
  - eval 이름공간은 PackageGenerator 모듈 전역이다. `from math import *`·`np`·내장 함수가 다 보인다.
  - 출력은 `format(v, ">20.13e")` 라 int·float·np.float64 가 같은 글이 된다.
  - 저장소·/data/koopark·~/claude 에서 curvefunction 을 쓴 옵션 파일은 찾지 못했다.

## 결정
- **종료 코드 3.** 1 은 예외·입력 오류로 이미 쓴다. "출력은 썼지만 요소가 빠졌다" 를 따로 알아볼 수 있게 3 을 쓴다. 출력 .k 는 진단용으로 남긴다. 러너가 rc 를 보고 멈추므로 다음 단계로 넘어가지 않는다.
- **세는 곳은 솔리드 출력기의 건너뛰기 두 곳이다.** 셸·빔 출력기는 이미 비 0 이라 건드리지 않는다(외과적 변경).
- **MAT_017 은 양수인 SIGY·FS 중 작은 것이다.** FS 가 0 이하이면 SIGY 를 쓴다. SIGY 가 0 이하이고 FS 가 양수이면 FS 를 쓴다. 둘 다 0 이하이면 지금처럼 맵에 넣지 않는다.
- **`*Recipe` 는 글로 펼친 뒤 원래 파서로 읽는다.** KMM 옵션 파서는 손으로 짠 큰 반복문이다. 파서를 고치지 않고, 앞에서 MCP 와 같은 옵션 글로 바꿔 넘긴다. `*Recipe` 가 없으면 원래 파일을 그대로 연다(동작 변화 0).
- **경로 바꿔 쓰기는 하지 않는다.** MCP 는 옵션 안 절대경로 파일을 작업 폴더로 복사하고 이름만 남긴다. KMM 은 그 자리에서 돌므로 경로를 그대로 둔다. 경로가 없는 레시피는 MCP 가 만든 stmc_options.txt 와 바이트가 같다.

## 구현하며 정한 것
- **요소 소실 기록은 중복 없는 EID 목록이다.** 한 실행에서 같은 요소를 여러 파일에 쓰면 실패 횟수(n)가 겹친다. 그래서 알림의 개수는 중복을 뺀 요소 수다. 출력 .k 는 남기고, 알림은 콘솔과 <옵션>.log 둘 다에 남는다(DualOutput 이 살아 있을 때 찍는다).
- **help format '실행' 에 종료 코드를 적었다.** "0 정상 · 1 오류 · 3 요소 소실". MCP 카탈로그 생성기가 이 주제를 읽으므로, 다음 재생성 때 MCP 설명에도 들어간다.
- **`*Recipe` 매개변수 글 → 타입.** JSON 수와 같게 정수 글은 int, 나머지는 float 이다(7 → "7", 7.0 → "7.0", 1e3 → "1000.0"). inf·nan 은 거절한다. boolean 은 true/false(대소문자 무관)만 받는다. string 은 앞뒤 공백을 뗀다.
- **`*Recipe` 와 같이 쓴 머리 줄.** *Recipe 앞 줄과 매개변수 뒤 *End 앞 줄은 *Mode 앞에 둔다. *End 뒤 줄은 *End 뒤에 그대로 둔다. 머리가 `*Inputfile`·모델뿐이면 MCP 글과 바이트가 같다(시험으로 확인).
- **`*Recipe` 가 없는 파일은 바이트에서 `^\s*\*recipe` 만 찾는다.** 디코딩도 하지 않는다. 그래서 cp949 같은 비 UTF-8 옵션 파일도 예전과 똑같이 읽는다.
- **KAM 평가기는 예전 이름공간의 같은 객체를 쓴다.** PackageGenerator 모듈의 sin·log·pi 등이 전부 math 의 같은 객체임을 확인했다(별표 import 가 가린 이름 없음). np. 접두는 numpy 함수 그대로라 np.float64 값도 예전과 같다. 내부 이름은 `_ast`·`_math`·`_op`·`_np` 별칭으로 두었다. 별표 import 로 덮이지 않게 하려는 것이다.
- **KAM 식 결과가 복소수(음수의 분수 거듭제곱)면 여기서 거절한다.** 예전엔 쓰기 단계에서 알 수 없는 format 오류가 났다.

## 시험 묶음에서 본 것
- `test_drop_attitude_angles.py` 는 pytest 를 import 한다. venv312 에는 pytest 가 없어 run_suite.sh 로는 rc 1 이다(10-26 에도 같았고, 그때는 pytest 대역 실행기 run_pytest_shim.py 로 돌렸다). 회귀가 아니다.

## 리뷰 R(10-27) — 9건과 처리
- **R1(중간, 확정) 읽기에서 버린 요소는 rc 0** → fbe4eca. 솔리드 PID 미존재·10절점 코너 절점 0·2줄 짝 이상, 셸·빔 PID 미존재(예전엔 완전 무언), 질량 요소 행·절점 없음을 IMPORT_LOSS 에 적고 종료 코드 3.
  - 영향은 말뭉치 P 앞 518건으로 미리 쟀다. 읽기 소실이 있는 사례는 3건이고, 모두 실제 소실이다.
    - C_real_kr_offset: KooRemapper offset 결과. PID 1 요소 600개에 *PART 1 이 없다. 지금 KooRemapper 예제 01·02 도 같다(KooRemapper 세션에 알릴 것).
    - C_g6_mix_ten_pidmiss: 탐침.
    - H_t7_mass_roundtrip_old2: 옛 8칸 질량 출력.
  - 말뭉치 P 의 다름 1건(F_z1_node_mid_ctrlz, rc 0 → 3)도 절점 12 줄 가운데의 Ctrl-Z 로 요소 2 가 빠지는 실제 소실이다.
- **R2(중간, 확정) *Recipe 앞의 *End → 모드 0개, rc 0, 입력 model.k 다시 쓰기** → d547730. ImportOption 끝에서 읽은 모드·ID 를 레시피와 대조한다. 다르면 🔴 + 종료 코드 1 이고 아무것도 쓰지 않는다.
  - 모드 0개 실행이 입력 `<모델>.k` 를 덮어쓰는 것 자체는 옛 동작이다(레시피 밖). 알리기만 한다.
- **R3(중간, 가능성) MAT_017 FS 는 최대 주응력 기준인데 리포트는 von Mises 와 비교** → d545b9b. 사용자 결정 min(SIGY, FS) 는 그대로다. 파트마다 `criterion`(max_principal·von_mises)을 적어 후처리(a9)가 FS 를 σ1 과 비교할 수 있게 했다. 사용자에게 전제를 알린다.
- **R4(낮음) BOM 첫 줄 *Recipe 못 찾음**, **R5(낮음) 펼친 값의 스키마 검사 없음**, **R6(낮음) *Mode 부분 문자열 오탐** → d547730.
  - R5 는 MCP 생성기 규칙(카탈로그 키 타입: 실수 number|string, 정수 integer|string, 참거짓 boolean|string, 나머지 무엇이든)을 그대로 옮겼다. kmm_chain 의 options 는 MCP 도 타입을 보지 않는다.
- **R7(낮음) 정수 거듭제곱 가드가 정수 의미를 바꿈**, **R8(낮음) 예전에 되던 안전한 식(조건식·비교·erf 등) 거절** → 1c2d801.
  - 정수는 정수 그대로 계산하고, 결과가 100만 비트를 넘을 때만 OverflowError 로 거절한다.
  - 연쇄 비교는 실제 비교 결과(np.bool_ 포함)를 돌려준다. 처음에 파이썬 bool 로 돌려주다가 무작위 대조에서 191건이 나왔다.
  - 그 뒤 무작위 식 49,630개 대조에서 불일치 0 이다(Test_E2E_v126/kam_diff_eval.py).
- **R9(낮음) 셸이 없는 절점을 가리키면 트레이스백** → fbe4eca. 셸·빔·질량 출력기도 요소 단위로 건너뛰고 기록한다.
- **참고(범위 밖)** 리뷰가 덧붙인 두 건은 알리기만 한다.
  - PART_VALIDATION_SPLIT 은 솔리드 파트가 있으면 AttributeError(KooPartValidator.py:325)로 죽는다.
  - 그 모드의 자체 요소 출력기는 장부를 거치지 않는다.
- **내보내기 장부 메모리.** 예전 판은 빠진 EID 를 전부 담아, 큰 덱에서 전부 빠지면 수백 MB 가 될 수 있었다. 이제 횟수와 앞 10개만 담는다. 알림 문구는 '요소 N개' 에서 'N건' 으로 바꿨다(같은 요소를 여러 파일에 쓰면 겹친다).

## 리뷰 S(10-27, 리뷰 R 고침 재검토) — 9건과 처리
- **S1(높음, 확정) DTI 가 실제 dynain 에서 늘 종료 코드 3** → de5e5bc.
  - LS-DYNA dynain 은 *PART 없이 요소를 싣는다. DTI 는 dynain 을 따로 읽어 절점·초기응력만 쓰므로, dynain 읽기 전후로 읽기 장부를 되돌린다.
  - 합성 dynain 시험 두 곳(test_thermal_chain·thermal_chain_sim)은 요소 블록이 없어 이 회귀를 놓쳤다. 실제처럼 *ELEMENT_SOLID 를 넣었다. 교훈은 "합성 입력은 실제 산출물 꼴을 따른다" 이다.
  - 그대로 냈다면 누적 낙하·열 이월(dynaintoinitial.txt) 체인이 전부 멈췄을 것이다. 9월 실제 체인 로그에도 dynain 의 '🔴 43657개 소실' 줄이 있다.
- **S2 질량 블록 빈 줄 → rc 3**, **S7 같은 파트 EID 중복이 '소실 0'** → 584dc70.
- **S3 줄머리 NBSP·전각 공백·ZWSP·CR 줄끝에서 *Recipe 를 못 찾음** → 4afbf7c.
  - 일반 가드도 넣었다(584dc70). 돈 모드가 없으면 출력 이름이 입력과 같아 입력 덱을 다시 쓰던 옛 동작을 막는다(🔴 + 종료 코드 1).
  - 러너(StepConfigBuilder·CumulativeScenarioRunner·PartValidation·DWI)와 MCP 가 만드는 옵션 파일은 모두 *Mode 목록이 있다.
- **S4(설계) min(SIGY, FS) 로 하나만 남기면 다른 기준 한계를 못 본다** → d70f16d.
  - 파트마다 limits=[{value, criterion, source}] 로 양수인 한계를 모두 적는다. 사용자 결정(yield·source·criterion = min)은 그대로다.
  - a9 는 한계마다 안전율을 내 작은 쪽을 쓰면 된다. FS 는 σ1, SIGY 는 σvm 과 비교한다.
- **S5 np.square 겹치기로 정수 폭증**, **S9 np.inf·np.nan** → a462dfe.
- **S6 *PART_CONTACT 파트 요소도 'PID 에 *PART 없음' 으로 안내** → 584dc70. 원인 안내 줄을 붙였다.
  - KMM 은 PART_CONTACT 를 키워드로는 읽지만 파트로 만들지 않는다. 그 파트의 요소는 예전부터 조용히 빠졌다(이제 rc 3).
  - 지원하려면 별도 기능 작업이 필요하다.
- **S8 레시피 lines·options 형식(손으로 쓴 판)** → 4afbf7c.
- **알리기만 하는 것.**
  - 옛 eval 은 메서드 지역 변수(SFO·LCID 등)도 보였다. 쓰는 옵션 파일은 없다.
  - *ELEMENT_BEAM 끝 빈 줄 ValueError 는 옛 동작이다.

## 리뷰 T(10-27, 리뷰 S 고침 확인) — 낮음 5건과 처리
- 다섯 커밋 모두 해당 지적을 닫았다. 높음·중간은 없었다. 이 고침들이 만든 낮은 결함을 2632734·3296a37·2762399 로 고쳤다.
- **T1** DTI 장부 되돌리기가 *PART 를 실은 dynain 의 실제 소실까지 지웠다. dynain 에 파트가 없을 때만 되돌린다.
- **T2** S7 중복 검사가 같은 파트의 질량 요소 덮임을 '솔리드 EID 중복' 으로 알렸다. 질량 소실로 따로 센다.
- **말뭉치 R 의 새 다름 2건(D_c01·D_c07)** 은 자기 자신을 *INCLUDE 하는 탐침이다. 같은 요소를 두 번 읽어 S7 이 소실로 셌다(오탐). 덮인 요소가 지금 요소와 같으면(종류·절점) 경고만 낸다.
- **T3** 모드 0개 가드가 경로만 비교해 .key 입력(modeley.k)을 놓쳤다. '접미사 없음' 으로 판정한다. 모드가 하나라도 돌면 접미사가 붙고, 자체 출력 모드는 기본 출력을 쓰지 않는다.
- **T4** 줄머리 LRM·RLM·ZWNJ·ZWJ·soft hyphen 을 놓쳤다. 범주 Cf 글자를 모두 뗀다.
  - 매우 낮음 한 건도 고쳤다. splitlines() 와 ImportOption 의 줄 나눔이 달랐다(\x0b·\x85·U+2028). \n·\r·\r\n 에서만 나눈다.
- **T5** 상한 검사를 감싸는 함수로 두어 식 길이 한도가 절반(약 500항)이 됐다. 값을 만드는 자리에서 직접 검사한다.

## 리뷰 라운드에서 배운 것
- 검출을 넓히면 "그 요소를 정말 잃었나" 를 늘 따진다. 실제 dynain(요소는 있고 파트는 없음), 자기 *INCLUDE(같은 요소 두 번)가 그랬다. 출력에 정보가 남아 있는데 rc 3 이면, 사용자 결정의 뜻(조용한 소실 금지)과 다른 쪽으로 틀린 것이다.
- 합성 입력은 실제 산출물 꼴을 따른다. 합성 dynain 에 요소 블록이 없어 S1 을 놓쳤다.

## 말뭉치 S(최종) — 다름 13건 내역
- 738건 중 725건은 산출물 md5 와 rc 가 b480941 과 같다. 다름 13건은 모두 KMM 출력에서 요소가 실제로 빠지는 경우다. 예전 rc 0(또는 크래시 rc 1)이던 것이 rc 3 으로 드러났다.
  - 탐침·시험 덱이 7건이다. C_g6(PID 미존재)·F_z1(*NODE 안 Ctrl-Z)·H_t7 두 건(옛 8칸 질량 출력)·L_P7·V126 두 건이다.
  - 실제 예제가 4건이다. C_real_kr_offset 은 KooRemapper offset 결과로, PID 1 요소 600개에 *PART 1 이 없다. M_m024 두 건은 KooRemapper merge 의 10칸 *NODE 다.
  - J_M6_comma 는 쉼표(자유 형식)로 쓴 *ELEMENT_MASS 2행을 KMM 이 못 읽는다. LS-DYNA 는 읽는다.
  - J_Y5 는 *PARAMETER_LOCAL 인클루드를 passthrough 로 넘겨, 그 안의 *PART 2 를 쓰는 본 파일 셸 9개가 빠진다.
  - I_X4b 는 8절점 두께 셸 EID 21 출력 실패다. 예전엔 트레이스백이었다.
- J_M6·J_Y5·PART_CONTACT 는 KMM 리더의 기존 한계다. 이번에 '조용한 소실' 에서 'rc 3' 으로 바뀌었을 뿐이고 지원 작업은 따로다.
