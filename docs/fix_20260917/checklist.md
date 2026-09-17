# 체크리스트
- [x] 2 KMM Gravity 키 파싱 (DROP_ATTITUDE, DROP_WEIGHT_IMPACT_TEST)
- [x] 2 밀도 기반 g 판정 헬퍼 + 4곳(DropAttitude, DWI 3함수) 적용 + 메타데이터
- [x] 2 러너 simulation_params.gravity → Gravity (DROP·IMPACT)
- [x] 2 기존 예제 모델 신구 g 비교 (차이는 mm 모델 height≤100 뿐이어야)
- [x] 1 DWI 워크플로우 InitialVelocityZ,0 + Gravity,9810
- [x] 3 restack 라벨 MID
- [x] 4 matswap 3필드 PART
- [x] 5 KAM sys.exit + IP 대역
- [x] 6 Evolver 작업폴더 준비 헬퍼
- [x] help 문구 갱신 (KMM·KCR·KAM·KooRemapper) + 사례 재검증
- [x] 회귀 시험 추가·실행
- [x] 빌드 → KooRemapper compat → SIF v96 → tar → node001 → 배포본 e2e: 낙하 50mm -990.5·DWI 500 -3132.0 (옛 -6264), node001 KAM Access granted·PKG 메시
- [x] v96 e2e 에서 추가 발견·수정: CAP Evolver 보조 파일(stl.cmd) 미연결 309d8ef, Evolver 오류 뒤 입력 대기 무한 정지 7eb8238
- [x] KAM 단독 재빌드(dist 구성 v96 과 동일 165) → SIF v97 → node001 e2e: CAP 완주(솔더 STEP·Evolver 링크 자동), *Bogus 키워드 rc=1, restack/matswap 회귀·help 사례 46 통과, 낙하 -990.5·DWI -3132.0 재확인

## 2차 (재점검 "더 수정할건 없어?")
- [x] g 판정 g-cm-s 오판 범위 좁힘 (060f20a) + IMPACT gravity 끝단 시험 (8e3f7bd)
- [x] KMM 파서 키 190개·러너 출력 줄 106개 가림 감사 — 추가 결함 없음 (dt 외)
- [x] KMM bare exit 6곳 + KooNode 중복 노드 exit(0) → sys.exit(1) (aef1f9d)
- [x] KMM·KAM ascii 기동 가드 (LANG 없는 환경 UnicodeEncodeError rc=120) + KMM 로그 경로 + KAM 모르는 모드·입력 없음 rc=1 (2b52381)
- [x] KooRemapper meshfix 리눅스 gmsh 탐색 + matdb 기본 DB 실행 파일 기준 (KooRemapper 2418c22)
- [x] drop_weight_impact 예제 9개 단위, part_validation 모델 경로, TRANSLATION_DOE 매뉴얼 (0b79c68)
- [x] 전체 빌드 → KooRemapper compat → SIF v98 → node001 e2e 전 항목 통과: --cleanenv(LANG 없음) KMM 완주·한글 로그, 낙하 -990.5·DWI -3132.0, g-cm-s WARNING, KMM 잘못된 모드 rc=1(NameError 0), KAM PKG·CAP·pkg/입력없음/*Bogus rc=1, KooRemapper meshfix(SIF gmsh) 포함 사례 47 통과·restack/matswap 회귀·matdb DB 생략 525 로드, help 4종
