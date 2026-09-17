# 결정 노트
## 왜 매뉴얼을 그대로 옮기지 않나
KMM 매뉴얼 34개는 에이전트가 코드를 읽고 쓴 것이라 "예제 부재 — 재구성, 확인 필요" 가 많고,
TRANSFORM 은 키를 `translation` 으로 안내하지만 실제로 검증된 사용은 `Translate,0,0,0` 이다.
LLM 이 help 를 믿고 그대로 쓰므로, help 의 사례는 **돌려 본 것만** 넣는다.

## 사례는 파서로 돌린 것만 (2026-09-17)
tests/test_cli_help.py 가 사례마다 ImportOption 결과를 verify 기대치와 비교한다. 이 과정에서 드러난 것.
- 옛 예제 DropWeightImpactTest.txt 의 `YoungModulus`·`Density` 는 파서가 모르는 키라 무시된다 → 카탈로그는 러너 템플릿 키(`YoungsModulusImpactor` 등)를 쓴다.
- 매뉴얼 TRANSLATION_DOE 예제는 `*End` 뒤에 블록을 둬서 아예 읽히지 않는다.
- PART_MORPHING 변위 부호는 옛 예제 주석과 반대 (양수 = Pull).
- DROP_ATTITUDE 는 RunDirectoryMode 가 없으면 DropSet.k 가 아니라 <모델>_drop.k 를 쓴다 (실행 실측).

## Height 단위 추정 (DROP_ATTITUDE·DROP_WEIGHT_IMPACT_TEST)
KMM 은 Height > 100 이면 mm(g=9810), 이하면 m(g=9.81) 로 추정해 √(2gh) 를 InitialVelocity 에 더한다.
mm 모델에서 100 mm 이하는 틀린 속도가 된다. help 에 🔴 경고와 우회(Height,0 + InitialVelocityZ)를 넣었다.
drop_weight_impact 워크플로우는 vz 를 직접 계산해 InitialVelocityZ 로 주면서 Height 도 줘서 이중 가산된다
(배포 바이너리 실측: H=500 → -6264 mm/s, 의도 -3132). 고치는 방식(단위 키 추가 vs Height,0)은 사용자 결정 사항이라 코드는 두었다.

## 키 표 대신 세로 목록
긴 키 이름·설명 때문에 표가 180 칸을 넘어 터미널에서 깨졌다. `이름 [형식 · 기본/필수]` + 들여쓴 설명으로 바꿨다.

## KooChainRun 은 사례를 끝단까지 돌린다
scenario.json 은 prepare 가 통과해도 러너가 만드는 KMM 옵션 파일에서 틀릴 수 있다(예: dt 키 삼킴).
그래서 [KCR] 시험은 Designer → runner_config → 러너 `_create_step_config` → KMM ImportOption 까지 간다.
`KooChainRun --help` 만 카탈로그로 가로채고 `<명령> --help` 는 argparse 그대로 둔 이유는 명령별 옵션의 정본이 argparse 이기 때문.

## KooRemapper 는 정본을 Python 에 두고 C++ 를 생성한다
사례(YAML·명령)를 C++ 문자열로 손으로 옮기면 검증과 출력이 어긋난다. ops_help.py 한 곳에서
(1) run_help_examples.py 가 사례를 직접 돌려 검증하고 (2) gen_help_cpp.py 가 HelpCatalogData.inc 를 만들고
(3) --from-help 가 빌드된 바이너리의 help 출력을 다시 파싱해 돌린다. 세 단계가 같은 사례를 본다.
사례는 `generate box` 로 시작 모델을 만들어 빈 폴더에서 돈다 (저장소 예제 파일이 꼭 필요한 op 만 "필요한 입력" 으로 표기).
산출물 존재만으로는 부족했다 — restack 이 mid=0 덱을 만들고도 성공해서 *PART mid=0 검사를 추가했다.

## 검색에서 별칭 완전일치를 결정으로 쓰지 않는다 (KooRemapper)
"초기응력" 같은 일반어가 한 op 의 별칭이면 그 op 로 바로 가버려 다른 후보가 가려졌다. 이름 완전일치만 상세로 가고 별칭은 검색 점수로만 쓴다.
(Python 엔진은 별칭이 모드 고유어라 완전일치를 유지)
