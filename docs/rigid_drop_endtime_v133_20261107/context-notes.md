<!-- RIGID_DROP_ENDTIME v133(마지막 강한 재접촉 규칙) — 결정·근거 노트 -->
# 결정 노트 — RIGID_DROP_ENDTIME v133 (2026-11-07)

## 결정
- **사용자(11-07).** 리포트 재계산에서 v132 ENDTIM 규칙의 결함을 찾았다. 사용자는 'v133, 문턱 0.3·v0' 을 골랐다(문턱은 옵션 키, 코드·시험·e2e·SIF 굽기까지).
- **이름(사용자 확인).** KMM `PresimStrongContact`, KCR `simulation_params.endtime_presim.strong_contact`, 표 메타 `endtime_rule`(last_strong·first_recontact)·`strong_contact`, 표 칸 `strong_end_ms`·`strong_vn_max`·`strong_end_ms_e{e}` 다.
- **범위(사용자 확인).** 중력 켬 표와 impact_conditions(중력 켬)는 v132 규칙 그대로다. 중력 켬은 튀어 오른 폰이 다시 떨어져 '바닥 벗어남'으로 끝낼 수 없다.

## 근거(리포트 재계산에서)
- 묶음은 1 ms(T_SEP_MS) 기준이다. 문턱은 묶음 안 최대 접근 속도로 판정한다. 묶음 첫 접촉 속도로 판정하면 1.0 문턱에서 5방향을 놓친다.
- 문턱별 상자 폰 결과(마찰 0.5, 총·최대·50 ms 넘는 방향)는 다음과 같다. 문턱 이상 충돌을 놓친 방향은 셋 모두 0 이다.
  - v132: 17.62 s · 198 ms · 93
  - 0.3·v0: 19.48 s · 139 ms · 56
  - 0.5·v0: 12.60 s · 76 ms · 10
  - 1.0·v0: 6.02 s · 25 ms · 0
- 마찰 0.3 은 13.47 / 19.98 / 14.19 / 7.96 s 다.
- 경계 사례가 있다. 측면 α −16°·β 14°·e 0.1 은 56 ms 에 0.30·v0 로 닿아, 0.3 문턱이면 57 ms 가 된다.
- 멈춤 없이 끝까지 돌리면 3000경우가 8 작업자로 약 1분 걸린다(v132 는 5~9 초). t_max(1 s)에 닿는 경우는 4.5% 였다. calm 멈춤은 약한 드리프트를 일찍 끝내려고 넣는다.

## 진행 기록
- **11-07 엔진(에이전트).** 계약대로 `STRONG_CONTACT`·`MAX_EVENTS_FULL`·`strong_from_events`·`run_presim(strong_contact)` 를 넣었다. 시험 88 OK.
  - **calm 에 조건 하나를 더했다.** 마지막 이벤트 뒤 1 ms 조용(마지막 묶음이 닫힘)이어야 한다. 에너지 한계는 '강한' 미래 접촉만 막는다. 그래서 1 ms 안에 붙는 약한 접촉이 tFinal 묶음 끝을 늘리는 일을 막는다.
  - `CALM_SAFETY` 1.25 는 Bullet 순차 충격량의 작은 에너지 증가를 대비한 여유다. `CALM_EVERY` 는 10 스텝이다.
  - **받아들임 시험.** 상자 1000방향 × e 3 이 멈춤 없는 기준(endtime_rule_check.py `last>=0.3`)과 1000/1000 같다(총 19.48153 s, 최대 139.05 ms).
  - 멈춤 이유는 calm 488 · clear 2491 · t_max 21(모두 e 0.1) 이다. n_unresolved 가 21 각도에서 0 이 아니다(v132 는 0). 앞으로 경고가 더 자주 보인다.
  - 첫 재접촉 칸(class·t1·t2)은 3000 경우 모두 v132 와 같다. 중력 켬·strong_contact=None 은 git 6504b11 과 비트까지 같다.
  - **성능.** 1000×3·작업자 4 에서 v133 은 28~35 s, v132 는 8~13 s 다(2.5~4배). 2만 × 3·작업자 8 은 약 15~20 분으로 본다(v132 289 s).
    - 더 조인 calm 한계 두 가지(꼭짓점별 기하 상수, 지금 v_z 빼기)도 엄밀하고 결과가 같았다. 26~30 s 로 빨라지지만, 계약 식이 단순해서 채택하지 않았다(다음 판 후보).
- **11-07 KMM 모드(에이전트).** `PresimStrongContact` 키(전체 일치, > 0, 중복·비슷한 키 막음)를 넣었다. 실제로 준 키를 `GivenKeys` 로 남겨 중력 켬 경고에 쓴다.
  - 메타는 중력 끔이면 `endtime_rule=last_strong`·`strong_contact` 이고, 중력 켬이면 `first_recontact` 만이다. impacts.csv 도 같은 메타다. 모드 시험 110 OK, 도움말 527 OK.
  - **MinimumModel 30 방향에서 v132 → v133.** 15 방향이 길어지고 7 방향이 짧아졌다. 최대는 78.9 → 64.8 ms 다.
    - 6 방향은 모든 재접촉이 0.3·v0 미만이라 1.0 ms 가 됐다. 그 가운데 3 방향은 0.26~0.29·v0 로 문턱 바로 아래다(문턱 절벽).
- **11-07 KCR(에이전트).** 시험은 endtime 149 OK, impact_conditions 105 OK 다.
  - **블록 줄과 KMM 확인은 중력 끔일 때만 한다.** 중력 켬은 v132 규칙이라 줄이 필요 없다. 보내면 KMM 이 경고를 찍고, v132 KMM 을 괜히 막는다. 중력 켬에 strong_contact 를 직접 주면 경고 한 줄을 찍는다.
  - meta gravity=1 표에는 v132 표 경고를 찍지 않는다(같은 규칙이다).
  - **바이트 대조.** 끔은 1924/1924 같다(prepare 1128 + 제출 796). 켬은 1961/1979 이고, 다른 18 개는 둘뿐이다. `PresimStrongContact,0.3` 한 줄과 가짜 apptainer INFO 줄이다.
  - **실제 바이너리 확인.** v132 KMM(/data/SmartTwinPreprocessor)은 `(KMM too old for strong_contact)` 로 막히고, v133 소스는 통과한다.
- **11-07 통합 시험.** 28 개가 모두 통과했다. RDE 8종·도움말·KMM 회귀 19종(v131_review 224 s 포함)이다.
  - encoding_guard 는 시스템 `python3` 로 돌리면 KMM import 의 `pyDOE` 가 없어 실패한다. `venv312` 로는 전부 통과다. 시스템 파이썬 환경 문제이고 v133 과 무관하다(v132 때는 시스템 python3 에도 있었던 것으로 보인다).
- **11-07 e2e v133 도구(에이전트).** `/data/koopark/Test_E2E_v133` 를 만들었다. 케이스는 a·a2·a3·a4·g·b·c·d·e·f 다.
  - g 는 상자 덱으로 리포트 기준값과 1e-6 ms 까지 대조한다. 덱 질량특성은 해석해와 1e-16 수준만 다르다.
  - v132 산출에 새 판정을 대 보니 [v133] 0 OK·9 FAIL·8 SKIP 이고, 기존 기능 38·지킴 15 는 통과했다(아는 불량 먼저).
