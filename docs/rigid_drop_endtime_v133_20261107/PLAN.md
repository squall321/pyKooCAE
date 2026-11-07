<!-- RIGID_DROP_ENDTIME v133 — ENDTIM 규칙을 '마지막 강한 재접촉까지'로 고치는 계획과 계약 -->
# 계획 — RIGID_DROP_ENDTIME v133 ENDTIM 규칙 (2026-11-07)

## 왜
v132 ENDTIM 은 1차 묶음 뒤 첫 재접촉 묶음 끝 + 1 ms 다. 상자 폰(150×75×7.5 mm, 200 g, 1.5 m) 1000방향 × e 3종을 멈춤 없이 끝까지 돌려 봤다(중력 끔, 마찰 0.5).

| 문제 | 크기 |
| --- | --- |
| 슬랩다운이 꼭짓점별로 1 ms 넘게 갈라져 와 더 센 뒷부분이 ENDTIM 뒤에 옴 | 1차 충돌 속도 이상(≥ 1.0·v0) 충돌을 놓친 방향 244(24%), 마찰 0.3 은 323(32%). 최대 1.86·v0, ENDTIM 뒤 중앙값 2.2 ms·최대 18.4 ms |
| 약한 스침 뒤에 진짜 슬랩다운이 옴 | 위 244 가운데 26 |
| 거의 멈춰 돌다 수백 ms 뒤 스치는 약한 접촉(0.03~0.06·v0)이 2차로 잡힘 | 측면 ±15° 에서 521 ms |

근거와 재현은 /home/koopark/kooOmniDropAnalyzer/fullangle_mbd/ 의 `endtime_rule_check.py`·context-notes(2차 리뷰)와 리포트 '방향별 tFinal 맵' 절이다.

## 사용자 결정 (11-07)
- 규칙을 '2차 묶음 뒤에도 이어 돌려, 접근 속도가 문턱을 넘는 마지막 재접촉 묶음 끝 + 1 ms' 로 고친다. 문턱 기본 0.3·v0, 옵션 키로 바꾼다. 코드·시험·e2e·SIF 굽기까지 한다.
- 이름은 Strong 계열이다(아래 계약).
- 중력 켬 표(PresimGravity 1)와 충격 조건(impact_conditions, 중력 켬)은 v132 규칙 그대로다.

## 계약
### 1. 엔진 `KooCAEManager/KooRigidDropPresim.py`
- 상수 `STRONG_CONTACT = 0.3`, `MAX_EVENTS_FULL = 200`.
- `_simulate(..., strong_vn=None)` — `strong_vn` 이 숫자이고 중력 끔일 때만 새 멈춤 규칙이다(아니면 v132 와 비트까지 같다).
  - 2차 묶음 뒤 1 ms 조용 멈춤(`second`)을 쓰지 않는다.
  - 멈춤은 `clear`(기존: 무게중심이 r_max 보다 높고 올라가는 중), `calm`(새), `t_max`, `max_events`(MAX_EVENTS_FULL)다.
  - `calm` 은 접촉 중이 아니고 이벤트가 하나 이상이며, 다음 두 조건이 함께 설 때다.
    - v_z ≥ 0
    - ω_max·r_max < strong_vn·v_ref. 여기서 ω_max = √(2·(E − ½·m·v_z²) / I_min)이고, E 는 지금 운동 에너지(병진 + 회전)다.
  - `calm` 의 근거는 다음과 같다. 중력이 없으면 비행 중 v 는 일정하다. 바닥 법선 충격량은 v_z 를 늘리기만 하고, 마찰은 수평이며, 접촉은 에너지를 늘리지 않는다. 그래서 앞으로 어느 접촉점의 접근 속도도 ω_max·r_max 를 넘지 못한다.
- `strong_from_events(events, v_ref, strong_vn, t_sep_ms=T_SEP_MS)` → `(t1_end_ms, strong_end_ms 또는 nan, strong_vn_max)`.
  - 묶음은 1 ms(t_sep) 기준이고, 묶음 세기는 묶음 안 최대 접근 속도 ÷ v_ref(이벤트 `-vn_mps`)다.
  - strong = 2차 이후 묶음 가운데 세기 ≥ strong_vn 인 마지막 묶음의 끝이다.
  - strong_vn_max = 2차 이후 묶음 세기의 최대(재접촉 없으면 nan)다.
- tFinal(중력 끔) = (strong_end 가 있으면 그것, 없으면 t1_end) + margin. 중력 켬은 v132 `tfinal_ms` 그대로다.
- `run_presim(..., strong_contact=STRONG_CONTACT)`.
  - 중력 끔이면 위 규칙을 쓴다. 표 줄에 `strong_end_ms`·`strong_vn_max`(governing e)와 e 마다 `strong_end_ms_e{e}` 를 더한다.
  - 기존 칸(class·t1_end_ms·t2_start_ms·t2_end_ms 와 e 별)은 뜻을 그대로 둔다(첫 재접촉 묶음 기준).
  - `n_unresolved`(중력 끔) = 시뮬이 t_max·max_events 로 끝난 e 의 수다.
  - `reach_m` 은 새 tFinal 안의 이벤트 기준이다.
  - 중력 켬이면 새 칸 값은 nan 이고 규칙은 v132 다.
- `impact_rows` 는 그대로다(중력 끔이면 k ≥ 3 묶음 줄이 생긴다).

### 2. KMM 모드 `KooRigidDropEndtime.py`
- 키 `PresimStrongContact`(실수 > 0, 기본 0.3)를 둔다. 키 이름 전체 일치이고, 틀린 값은 ValueError 다(KMM rc 1).
- 중력 켬과 함께 오면 경고 한 줄을 남기고 무시한다.
- 표 메타에 `endtime_rule=last_strong`(중력 끔)·`first_recontact`(중력 켬)와 `strong_contact=<값>` 을 더한다.
- rigidbody.json presim.params 와 START 로그에도 남긴다.
- 도움말 `KooCLIHelp/kmm_catalog.py` 의 RIGID_DROP_ENDTIME 키 목록에 넣는다.

### 3. KCR `Runner/EndTimePresim.py`·`Runner/cli_help_kcr.py`·`docs/manual/01_KooChainRun/scenarios/scenario_reference.md`
- `simulation_params.endtime_presim.strong_contact`(실수 > 0, 기본 0.3) → 블록 줄 `PresimStrongContact,<값>`.
- 사전 해석 KMM 이 그 키를 아는지 `--help RIGID_DROP_ENDTIME` 으로 본다. 모르면 EndTimePresimError 로 멈춘다(v133 KMM 필요).
- table 지름길 표의 메타를 본다.
  - `endtime_rule` 이 없으면(v132 표) 경고한다. 슬랩다운 뒷부분을 놓칠 수 있다.
  - `strong_contact` 가 옵션과 다르면 멈춘다.
- impact_conditions 는 바꾸지 않는다(중력 켬 → v132 규칙).

### 4. 지켜야 할 것
- `strong_vn=None` 이거나 중력 켬이면 엔진 결과가 v132 와 같다.
- RIGID_DROP_ENDTIME 을 안 쓰는 KMM·KCR 출력은 바이트가 같다.
- 표 읽기(KMM EndTimeLookup·KCR)는 새 칸·메타가 있어도 없어도 된다.

## 시험·검증
- 엔진: calm 건전성(멈춤 규칙 끈 실행과 tFinal 같음), 상자 예시(꼭짓점 갈라진 슬랩다운 포함·약한 늦은 스침 제외), 중력 켬 v132 동일.
- 모드·KCR 단위 시험, 기존 묶음(KMM 26·KCR 1128/1918 바이트) 회귀.
- e2e `/data/koopark/Test_E2E_v133` — v132 바이너리는 새 기능 FAIL 을 먼저 확인한다.
- 성능: 2만 방향 × e 3 의 시간을 v132(289 s)와 비교한다.

## 무거운 작업 일정
pykoocae-53 의 Post v48 굽기·판정 동안은 코드·가벼운 시험만 한다(작업자 ≤ 4). 그쪽이 알린 뒤 빌드·굽기를 한다. 헤드 /opt 교체는 그때 사용자에게 묻는다.
