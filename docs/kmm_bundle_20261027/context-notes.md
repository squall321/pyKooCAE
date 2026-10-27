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
