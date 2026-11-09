<!-- KMM 리더 크래시 묶음 — 결정·근거 노트 -->
# 결정 노트 — KMM 리더 크래시 묶음 (2026-11-09)

## 결정
- **사용자(11-09).** 누적 체인 묶음 뒤 「찾은 결함 셋 고치기」. 배포는 고친 뒤 다시 묻는다.

## 조사
- R1: InitialVelocity.parse 의 `len(parameters1[1]) > 0 and int(parameters1[1]) > 0` — 공백 10자는 길이가 10 이라 int() 로 간다. 받는 쪽(KooInitial *INITIAL_VELOCITY)은 이미 KooDynaInt·KooDynaFloat.
- R2: SetDatabasefromDyna 의 변환은 모두 빈 칸을 먼저 기본값으로 바꾸거나 건너뛴다 — 남은 위험은 E 없는 Fortran 지수(867·885·1068행 float)와 '2.0' 꼴 정수. KooDynaFloat 는 '1.0000-06' 을 1e-06 으로 읽고(_fortran_float), 못 읽는 글은 까닭을 밝혀 멈춘다.
- R4: 첫 조건의 `"DATABASE_RBDOUT"` 에 `*` 가 없어 918행 `*DATABASE_RBDOUT` 갈래에 닿지 못한다. importer 는 keywordInterpreted["DATABASE_RBDOUT"] = True 라 원문 통과도 막는다.
- R4 확인: *DATABASE_RBDOUT 만 든 덱을 TRANSFORM 0 으로 돌리면 rc 0 인데 출력에 RBDOUT 이 없다(고치기 전 a1c4ec6).
- KMM 기록기는 번호 없는 *LOAD_SEGMENT_SET 도 *LOAD_SEGMENT_SET_ID 로 쓴다(기존 규칙) — 시험은 _ID 꼴을 읽는다.

## R5 결정 — 짧은 접촉은 멈춘다
- ref.k 는 하중 카드를 고치자 다음 크래시가 *CONTACT_TIED_SURFACE_TO_SURFACE(카드 1 만)에서 났다 — KooContact.AddContactfromDyna 가 카드 2·3 을 꼭 있다고 보고 IndexError.
- 처음엔 빈 카드로 채워 기본값으로 읽게 했다가 거뒀다. KooDynaKeyword._contact_cards 가 이미 주요 접촉 8종(AUTOMATIC_GENERAL·SINGLE_SURFACE·SURFACE_TO_SURFACE·ERODING 등, _ID 포함)에
  「필수 카드가 N장 모자란다(카드 1~3). 덱을 확인하라」 로 멈추고 있었다(v131 I8 의 R16 필수 카드 규칙). TIED 등 그 검사를 거치지 않던 종류도 KooContact 에서 같은 문구로 멈추게 했다 —
  빠진 필수 카드를 기본값으로 메우면 LS-DYNA 가 다르게 읽을 위험을 가린다.
- 그래서 ref.k 는 「읽어 냄」 이 아니라 「원인을 밝혀 멈춤」(rc 1)이 기대값이다. 웹 자동화 taylor_A_dump.k 는 rc 0.

## 회귀·말뭉치(11-09)
- tests/ 61개(새 시험 포함) 모두 rc 0 — 실행기 /data/koopark/Test_reader_crashes_20261109/run_suite.sh(pytest 를 import 하는 파일만 /usr/bin/python3 -m pytest).
- 말뭉치 대조(corpus_run.py, gen_a1c4ec6 ↔ 지금): 웹 자동화 taylor_A·taylor_A_dump 4덱이 rc 1 → 0. KooRemapper ref·out 은 짧은 접촉에서 필수 카드로 멈춘다(rc 1, 이유를 알림).
  🔴 배터리 연구 덱 3개(case_*_phase1_*_merged)는 *DATABASE_RBDOUT(2.0E-05 0 0 1)이 고치기 전 출력에 없었다 — 이제 돌아온 2줄만 다르다. 나머지 덱은 바이트 같음.
- RBDOUT 기록기는 DT 를 10.3e 로 쓰고 LCUR 0 을 빈 칸으로 쓴다(다른 ASCII 데이터베이스 카드와 같은 기존 꼴, 뜻은 같음).
