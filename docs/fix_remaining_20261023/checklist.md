<!-- 10-23 남은 Pre 결함 6건 수정 체크리스트 -->
# 체크리스트 — 남은 결함 정리 (2026-10-23)

- [x] 분류 — 원문(R16 *END·*INCLUDE·Appendix V·*ELEMENT_SOLID)·코드·컨테이너 ldd 로 결함 6건 + 비결함 1건 확인
- [x] F3 `*END` 에서 읽기 멈춤 + 뒤 키워드 안내 — 9ae1eb6 (F2 와 함께)
- [x] F2 Ctrl-Z 앞까지만 읽기 — 9ae1eb6
- [x] F4 순환 인클루드 건너뛰기 — 592fb88
- [x] F1 솔리드·셸 레거시 경로 빈 줄 건너뛰기 + 안내 — c33a0a2
- [x] F5 데이터 없는 키워드 출력 보존(매니저가 안 쓴 것만) — 71c910b·dca2d5f
- [x] F7 DWI·IMPACT 폴백을 KMM 이 단위계(재질 밀도)로 고름 + IMPACT 템플릿이 SI 기본값을 강제하지 않음 — 7b31d09
- [x] F6 빌드 컨테이너 LD_LIBRARY_PATH 정리 — 81dcc93 (배포 폴더 확인은 빌드에서)
- [x] 회귀 — 시험 25개 통과, MinimumModel md5 동일, 리뷰 말뭉치 84덱 중 바뀐 10덱 전부 표의 범주
- [x] 적대 리뷰 D(리더)·E(DWI·빌드) — 확정 2건(Ctrl-Z 첫 0x1A 절단, Gravity 무시) + 기존 결함 8건 반영(커밋 13개)
- [x] 3차 리뷰 F — 확정 6건 + 기존 결함 3건 반영(커밋 11개), 깨진 중간 커밋 바로잡음
- [x] 4차 리뷰 G(반영분) — 확정 7건·개연 4건·기존 결함 여럿(아래에서 반영)
- [x] 리뷰 G 반영 — 커밋 8개(b1a9527·96ba149·3dd79ae·f915f9b·40c4eab·029b84a·d3f5cff·f43035f) + 시험 tests/test_reader_review_g.py(수정 전 44건 모두 실패, 지금 모두 통과)
  - [x] G1·G5·P1 빈 줄을 부록 V 대로 읽기 — *NODE 빈 줄은 건너뛰고 알림, *DEFINE_CURVE 빈 점 카드는 (0,0) 으로 읽고 알림, THICKNESS 는 카드 1 자리 빈 줄 건너뜀·카드 2 자리 빈 줄은 기본값·끝에서 빠진 카드 2 도 기본값(8칸·I10)
  - [x] 해석 키워드 전수 점검 — 블록 끝에 빈 줄 하나를 넣고 출력 비교(크래시·조용한 변화)
  - [x] G2·P2 Ctrl-Z 처리 공용 함수(리더·MERGE_K) + MERGE_K 줄 나누기를 리더와 같게('\n' 만)
  - [x] G3 인클루드의 *PARAMETER 를 메인 파일 치환 전에 미리 읽기
  - [x] G3·G4·P3 미정의 &참조 경고 — 남은 &참조는 곧 미치환, 숫자 줄만 셈, *INCLUDE 제외, 앞 칸에 붙은 참조 포함
  - [x] G6 CASE 표지 판정 공용화 — MERGE_K·DECOMPOSE_K 도 쓰지 않고 알림
  - [x] (전수 점검) *SET_SEGMENT(_TITLE) 블록 끝 빈 줄 → 절점 0 세그먼트
  - [x] G7 *SET_SHELL·*SET_SHELL_TITLE SID 카드 + 셸 셋 기록기(셸 셋 든 덱은 7월 판부터 출력에서 죽음), MAT_ADD_EROSION 4·5번째 카드, CONTROL_ADAPTIVE 8번째 칸·ADPTYP 7 머리말
  - [x] (기존 결함) DWI DampingSpring 에서 BoundaryDistance>0 이고 시편 파트가 2개 이상이면 시편 절점이 *NODE 에서 빠짐
- [ ] 전체 회귀(시험·MinimumModel·말뭉치) + 5차 리뷰 H(반영분만)
- [ ] 빌드 → 배포 폴더 GLIBC 전수(≤2.35) → 컴파일본 e2e(Test_E2E_v120 + 새 덱) → SIF v122(KooRemapper 세션이 v121 을 먼저 올림 — 굽기 전에 알림) → tar → Drive·메일
- [ ] 메모리·노트·푸시
