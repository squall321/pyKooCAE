<!-- 강체 낙하 사전 해석 → 각도별 종료 시간(RIGID_DROP_ENDTIME, v132) — 결정·근거 노트 -->
# 결정 노트 — 강체 낙하 사전 해석 → 각도별 종료 시간 (2026-11-07, v132)

## 결정
- **사용자(11-07).** 프로토타입(`/home/koopark/kooOmniDropAnalyzer/fullangle_mbd`)을 SmartTwin 프리프로세서에 정식으로 넣으라고 했다. 흐름은 덱 → OBJ·외곽형상·I·A → 2차 충격 사전 해석 → 각도별 tFinal 이다. KMM 이 그 결과를 받아 각도별 ENDTIM 을 쓰게 하라고도 했다. SIF 로 묶는 기존 패턴을 지키고 서브에이전트를 많이 쓰라고 했다.
- 질문 넷의 답은 다음과 같다.
  - 구조: KMM 새 모드 + KCR 자동 연결.
  - 이름: RIGID_DROP_ENDTIME 계열.
  - 물리: 리포트처럼 중력을 켠다.
  - 범위: SIF v132·tar·Drive/메일까지.
- **"I A" 해석.** 관성(I)·면적(A)으로 본다. 질량특성 JSON 에 질량·무게중심·관성 텐서·주축·바운딩 박스·OBB·외곽면 면적·껍질 부피와 면적을 모두 넣는다.

## 조사에서 정한 것 (근거)
- **KMM 리더를 다시 쓴다.** 새 파서는 만들지 않는다. *PARAMETER·I10·*INCLUDE·고정폭·10절점 결함 이력이 리더에 쌓여 있다.
  - 질량·무게중심·관성 코드는 없다. VIB `_compute_part_mass_volume` 은 TETRA10·HEXA20 이 0 이고, 밀도 0 재질·요소 두께·질량 요소를 빠뜨린다. VIBRATION_LOAD 가 쓰므로 고치지 않고, 새 모듈에 새로 짠다.
- **모드 등록 함정**(부분 문자열, 앞에서 먼저 맞으면 끝).
  - 모드 이름에 `drop_attitude`·`transform`·`merge_k` 등이 들어가면 그 모드로 잡힌다. `rigid_drop_endtime` 은 어느 것과도 겹치지 않는다.
  - 블록 머리에 `*end`·`*mode`·`*step`·`*info`·`dropattitude` 가 들어가면 안 된다. `**rigiddropendtime` 은 괜찮다.
  - test_cli_help 는 `self.modeList.append("NAME")` 을 정규식으로 세어 카탈로그와 양방향 대조한다(큰따옴표, `[A-Z_]`).
- **DROP_ATTITUDE 블록은 줄 전체를 부분 문자열로 본다**(`"tfinal" in line.lower()` 등). 그래서 `EndTimeTable` 은 블록 검사 맨 앞에 두고, 키 이름 전체 일치로만 받는다.
- **각도별 ENDTIM 자리.**
  - 누적 경로는 DOE·스텝마다 옵션 파일을 따로 쓴다(StepConfigBuilder `tFinal,` 줄). 그래서 KMM 이 표를 받기만 하면 된다.
  - Fast DOE(한 옵션 파일에 여러 각도, KCR 배치 경로)는 ENDTIM 을 각도 반복 전에 한 번 캐시에 굽는다. 이 경로는 KMM 수정 없이는 각도별 값이 불가능하다. 사용자 요청("kmm쪽에도")이 바로 이 자리다.
- **낙하 방향 규약**: d = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1) 이다(ADV:2355-2371, AngleSourceParser `_physical_drop_dir`).
  - 기기는 돌리지 않고 바닥 법선과 속도를 돌린다.
  - 바닥은 등방이고 초기 회전이 없으면 결과는 d 에만 달려 있다(yaw 로 법선 둘레를 도는 것은 무관).
- **중력.**
  - DROP_ATTITUDE 덱에는 LOAD_BODY 가 없다. g 는 √(2gh) 에만 쓴다.
  - 사용자는 리포트처럼 중력 켬을 골랐다. 덱과의 차이는 알고 고른 것이다.
  - 중력을 켜면 rebound 분류(무게중심 상승 > 1 mm)가 생긴다. 회전으로 온 충격이 rebound 로 잘못 분류되는 위험은 B 가 잰다.
- **tFinal 규칙**(프로토타입 tfinal_map.py 그대로).
  - 슬랩다운: 2차 충격 묶음 끝 + 1 ms.
  - 그 밖: 1차 충돌 끝 + 1 ms.
  - 반발계수 셋 가운데 최대를 쓴다.
  - 정확한 각도에서 돌리므로 이웃 6방향 최대(conservative)는 쓰지 않는다.
- **단위.** 출력 `endtim` 은 덱 시간 단위다. mm-t-s·m-kg-s 는 s, mm-kg-ms·mm-g-ms 는 ms 다. 소비 쪽(KMM)은 단위를 모른 채 그대로 넣는다.
- **바닥판 제외.** SimpleDrop·DropSet 에는 바닥판이 파트로 들어 있다(DropSet 은 SI 밀도라 1.4e10 t). 모든 절점이 SPC 로 묶인 파트는 자동으로 빼고 이유를 남긴다. `ExcludePart` 로 직접 뺄 수도 있다.

## 진행 기록
- (작업하며 덧붙인다)
