# 체크리스트
## P0 공통 엔진
- [x] 렌더·검색·argv 가로채기, 무거운 import 전 처리
- [x] 엔진 단위 시험 (tests/test_cli_help.py [엔진]·[사본])
## P1 KMM
- [x] 파서에서 모드별 키 기계 추출
- [x] 32 모드 카탈로그 (KooCLIHelp/kmm_catalog.py)
- [x] 사례 파서 검증 (전 모드 37 사례)
- [x] 대표 13 모드 소스 실행 e2e — 출력 파일명 실측 반영 (/data/koopark/Test_CLIHelp_e2e)
- [ ] 배포 바이너리 help e2e (P5)
- [x] `--help` 멈춤·로그 생성 해소 (import 전 처리, 0.04 s, 파일 생성 0)
## P2 KAM
- [x] 6 모드(+CAP 별칭) 카탈로그 · 사례 파서 검증 (LSDYNADOE 는 빈 스텁이라 제외)
- [x] 소스 실행 e2e: PKG STEP·AIRMESH 산출물 확인 (/data/koopark/Test_CLIHelp_e2e/KAM)
- [ ] PKG 메시·CAP 는 gmsh 번들 바이너리로 e2e (소스 환경 gmsh 셔임 깨짐) — P5
- [x] `--help` 를 re-exec·라이선스 게이트 전에 처리
- [ ] 배포본 기동 불가 해소
## P3 KooChainRun
- [ ] 시나리오 모드·키 주제 · 예제 prepare 검증
## P4 KooRemapper
- [ ] 검색 · `<명령> --help` · 부족한 사례
## P5 배포
- [ ] 전체 빌드 · SIF · tar · node001 · 배포본 help e2e

## 도중 발견
- [x] DROP_ATTITUDE `dt` 부분일치가 RigidifySmallDtThreshold·DropContact.DTSTIF/DTPCHK 를 삼킴 → 17226d6 수정·회귀시험
- [ ] drop_weight_impact 워크플로우 충격 속도 이중 가산 (Height + InitialVelocityZ) — 사용자 결정 필요, help 에 경고만 반영
