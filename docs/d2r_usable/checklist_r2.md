# D2R 실사용 2차 — 감사 결함 수정 체크리스트 (2026-10-07)

근거: 읽기 전용 적대 검증(에이전트 10 + 비평 1) + LS-DYNA Vol I 원문 대조. 사용자 결정: hourglass 는 현행(옵션 우선) 유지, 셸·빔 초기응력 소실은 문서화만.

## 코드
- [x] D2R code 2↔4 원복 (D2R 세트 code 2 = 접촉력 0 → 강체, R2D 세트 code 4) — ADV:3192/3196
- [x] D2R 켜짐 + GEN 유지 경로에서 바닥판 Type 미지정 → S2S 자동(`D2R_FLOOR_AUTO_S2S`), 명시 General → 🔴 `D2R_FLOOR_GENERAL` (매뉴얼 Remark 1)
- [x] D2R 요청 + 바닥판 CID 없음 → 🔴 `D2R_SKIPPED` 경고 (IncludeWallInGeneral / RigidWall)
- [x] 조합 C·GEN 바닥판의 FS/FD/DC/VC/VDC → `_dcval` (명시값 > 원본 > 기본)
- [x] `_d2r_num` 손실 없는 최단 지수표기(.1e→.2e→.3e), 기존 출력(1.0e+20, 1.0e-07) 바이트 유지
- [x] DropContact 키 정규화 (type/inherit_general_contact/scope 대소문자·밑줄 무시) + 시나리오 `inherit_general_contact` 별칭
- [x] `D2RLrb` 옵션 (KMM 파서 + ADV + StepConfigBuilder `lrb` + help)
- [x] EBADF 진단 힌트 문구 — NFSv4 open state 상실로 정정
- [x] help 카탈로그: D2R 8키·D2RLrb·DropContact.InheritGeneral/Type/Scope 등재

## 시험
- [x] tests/test_d2r_round2.py 신규 (KMM 6회: auto S2S·명시 General·SKIPPED·LRB·조합C FS 명시·소문자 키) + 순수 python(_d2r_num·StepConfigBuilder)
- [x] 기존 스위트 재실행 + **로그 보존** (/data/koopark/Test_flock/tests_r2/)
- [x] 회귀: D2R 미사용 덱 바이트 동일 (test_optcarda_inherit plain 경로)

## 문서
- [x] USAGE.md §1 경고 명시, §2 권장 설정(Type S2S), §4 lrb·정밀도, §6 카드 의미 정정(현장이 맞았다), §7 ③ 명령, §8 셸·빔 소실·원복 전제
- [x] context-notes 갱신

## 빌드·배포
- [x] build_without_automatedmodeller.sh (KMM + KooChainRun) → 바이너리 mtime 확인
- [x] 배포 바이너리 e2e (code 2/4, AUTO_S2S, SKIPPED, 1.0e-07 유지)
- [ ] SIF v111 + tar + Drive + 메일 → node001 배포 → sha 확인
- [ ] 커밋·푸시
