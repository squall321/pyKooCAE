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

## CLI 도움말(11-09)
- v135 에서 DTI 지시어 둘(*RemoveRigidWallbyID·*SpecimenModified)을 더하고 kmm_catalog 를 고치지 않았다(카탈로그 규칙: 키를 바꾸면 사례·설명도). 이번 빌드에 같이 싣는다.
- 사례 「누적 낙하 다음 단계」 는 DROP 이 적는 꼴 그대로(*RemovePartbyID·*RemoveContactbyID·*RemoveRigidWallbyID) — 파싱 기대치만 본다(번호 900·1 은 예시).
- 아는 불량 확인: 새 카탈로그 + v135 이전 파서(gen_f3a49d9)면 RemoveRigidWallIDList·SpecimenModified 두 항목 FAIL(AIRMESH#1 FAIL 은 옛 트리를 링크로 엮은 탓, 무관).

## 배포 v136 (11-11, 사용자 승인 「배포」)
- **빌드 전 확인.** origin/main = HEAD 4d8eb00(그사이 남의 push 없음), occProject/·Runner/ 미커밋 없음. 헤드 /opt·compute-node-images Pre = v135 da892a35, 마지막 tar v135. kooomnidropanalyzer-43 에 알림 — 그쪽 진행 작업 없음, 헤드 교체 알림까지 소스 안 건드림.
- **아는 불량(컴파일본).** 헤드 v135 SIF 안 KMM(c18245a2)으로 새 시험 1 OK / 8 FAIL — 소스 아는 불량(gen_a1c4ec6)과 같다.
- **빌드.** build_capped_v136.sh(root scope MemoryMax 24G·oom_score_adj 1000·가용 8.5 GB 워치독)로 build_without_automatedmodeller.sh --clean — 16:43~17:39 BUILD_RC 0, 최저 가용 28.2 GB. KMM 41f37642(17:29), KCR 35511107(v135 와 바이트 같음 — 이번 커밋은 KMM 쪽만), KAM 580f028e 그대로. NFS·SIF 소스 트리 같음. 빌드 로그 error 류 100줄은 Nuitka 진행 메시지.
- **컴파일본 시험(host_v136, KMM_BIN·C.UTF-8).** 리더 크래시 9/9·누적 체인 51/51·v131 리뷰 107/107. 호스트 e2e(e2e_rde.sh host, GOLDEN = 이 폴더 사본 — 43 기준과 diff 없음) ALL PASS 100(v135 와 같은 100), f 회귀 7종 FAIL 0.
- **굽기 직전(17:5x).** 헤드·compute-node-images da892a35, 마지막 tar v135, 잡 0, KooRemapper c5f74c18(원본 = 스테이징, v135 와 같음) — kooremapper-fd·4a 에 알림.
- **굽기(17:5x, BAKE_RC 0).** SIF v136 1c973c25(1,615,892,480 B) = compute-node-images. 안의 바이너리 KMM 41f37642·KCR 35511107·KAM 580f028e·KooRemapper c5f74c18(굽기 검증 기대 = 실제, 그림 op 3/3). tar v136 1,379,317,626 B, Drive ApptainerImages:SmartTwinPreprocessor/(SIF·tar), 메일 sent OK. kooremapper-fd·4a 에 끝 알림.
- **SIF 판정(kmm_sif.sh, SIF = 새로 구운 것).** 리더 크래시 9/9·누적 체인 51/51·v131 리뷰 107/107. e2e_rde.sh sif ALL PASS 100(SIF 안 KMM 41f37642), f 회귀 7종 FAIL 0.
- **헤드 /opt(18:25).** 잡 0. compute-node-images 사본을 .new 로 cp -p → 지금 헤드를 하드 링크 `SmartTwinPreprocessor_backup_20261111_182504.sif`(v135 da892a35, 옛 inode) → .new 를 rename. 새 헤드 1c973c25(새 inode). 헤드 SIF 로 리더 크래시 9/9, `--help DYNAIN_TO_INITIAL` 에 *RemoveRigidWallbyID·*SpecimenModified·사례 2 가 나온다.
- 노드(node001·002)는 VM 이 꺼져 있어 대상 아님 — 켤 때 사용자 확인 뒤 Pre v136·Post v51.
