# 체크리스트
## P0 공통 엔진
- [x] 렌더·검색·argv 가로채기, 무거운 import 전 처리
- [x] 엔진 단위 시험 (tests/test_cli_help.py [엔진]·[사본])
## P1 KMM
- [x] 파서에서 모드별 키 기계 추출
- [x] 32 모드 카탈로그 (KooCLIHelp/kmm_catalog.py)
- [x] 사례 파서 검증 (전 모드 37 사례)
- [x] 대표 13 모드 소스 실행 e2e — 출력 파일명 실측 반영 (/data/koopark/Test_CLIHelp_e2e)
- [x] 배포 바이너리 help e2e — node001 SIF v95 에서 DROP_ATTITUDE·RIGIDIFY 실행 통과
- [x] `--help` 멈춤·로그 생성 해소 (import 전 처리, 0.04 s, 파일 생성 0)
## P2 KAM
- [x] 6 모드(+CAP 별칭) 카탈로그 · 사례 파서 검증 (LSDYNADOE 는 빈 스텁이라 제외)
- [x] 소스 실행 e2e: PKG STEP·AIRMESH 산출물 확인 (/data/koopark/Test_CLIHelp_e2e/KAM)
- [x] PKG 메시·CAP SIF v95 e2e (헤드노드 — node001 IP 미등록). CAP 는 작업 폴더 Library/Evolver 필요 → help 주의 추가 (다음 빌드에 반영)
- [x] `--help` 를 re-exec·라이선스 게이트 전에 처리
- [x] 배포본 기동 불가 해소 (v95 재빌드)
## P3 KooChainRun
- [x] 시나리오 모드 5 + 워크플로우 2 + 명령 11 카탈로그 (Runner/cli_help_kcr.py)
- [x] 사례 검증: prepare(Designer) → runner_config → 러너 step config → KMM 파싱 (DWI·part_validation 포함)
- [x] `KooChainRun --help [검색어]` 연결, `<명령> --help` 는 argparse 유지
## P4 KooRemapper
- [x] tools/help/ops_help.py 정본 → HelpCatalogData.inc 생성 (48 op)
- [x] help 검색·help all·`<op> --help`·인자 없음 개요 (KooRemapper 7981ca1)
- [x] 사례 46개를 help 출력에서 파싱해 실행 검증 (meshfix·warpage 제외), 단위시험 52/52, 명령 40개 신구 차이 0
- [x] compat 빌드(GLIBC_2.34) → opt/kooremapper/bin, SIF 안에서 사례 46개 통과
## P5 배포
- [x] 전체 빌드 · SIF v95 · tar · node001 · 배포본 help e2e (KMM·KAM·KooChainRun help all, KooChainRun prepare DOE 26)
- [ ] KAM CAP 주의 문구 수정분은 다음 빌드에 반영

## 도중 발견
- [x] DROP_ATTITUDE `dt` 부분일치가 RigidifySmallDtThreshold·DropContact.DTSTIF/DTPCHK 를 삼킴 → 17226d6 수정·회귀시험
- [ ] drop_weight_impact 워크플로우 충격 속도 이중 가산 (Height + InitialVelocityZ) — 사용자 결정 필요, help 에 경고만 반영
- [ ] Height ≤ 100 을 m 로 간주하는 g 추정 (DROP/IMPACT) — 사용자 결정 필요, help 에 🔴 경고
- [ ] KooRemapper restack 숫자 MID → PART mid=0 · matswap 이 generate box 모델에서 PID not found — 보고만
