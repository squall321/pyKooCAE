<!-- sphere_report 자동화 수정 체크리스트 -->
# 체크리스트 — sphere_report 자동화 (2026-10-26)

- [x] 대조 — 문서 진단을 코드로 확인(자원 고정·rc 0·순차 루프·350 고정), 정정 4건(context-notes)
- [x] 계획 PLAN.md, a9 에 도구 쪽 인터페이스 제안
- [x] ① build_sphere_sbatch — 런 수 N 으로 자원 산출, LS-DYNA environment 의 ncpu·memory 를 물려받지 않음, 명시값보다 산출값이 크면 산출값 + 알림, 파티션 상한 + 알림
- [x] ① 두 호출부가 N(runner_config 의 step 총수)·도구 옵션 지원 여부를 넘김 — KooChainRun._maybe_submit_sphere_after, SlurmSubmitter._maybe_submit_sphere_job
- [x] ②③④ sphere_report.sh — 실행 시점에 --parallel-runs·--yield-map 지원 확인 후 넘김, 'Loaded 0 results' 를 셸에서도 잡아 비 0 종료(옛 SIF 대비)
- [x] ④ KMM — DropSet.json 에 model.part_yield(덱 단위·unit 힌트) — 별도 파일·경로 배선 대신(a9 합의)
- [x] ④ (경로 배선 필요 없어짐 — 도구가 DropSet.json 에서 읽음. postprocess.yield_map 은 덮어쓰기용으로만)
- [x] 시험 — tests/test_sphere_automation.py(자원 17·배선 8·맵 9, 수정 전 실패 확인)
- [x] 곁에서 찾아 고친 기존 결함 — 320b250 제목 없는 MAT_024 EPS·ES 뒤바뀜 출력, 0c6aecf MAT_003 _TITLE 항상 죽음·카드 2 생략 죽음
- [x] 시험 31종 — encoding_guard 가 새 subprocess 3곳의 encoding 누락을 잡음 → 302b2d4, 다시 전부 통과
- [x] MAT_003 _TITLE '모든 판에서 죽음' — 09-29 가드 이전 판으로도 확인(조용한 오출력 없음), 서버 덱 13,852 중 해당 6(예제 사본·내 시험)
- [ ] 컴파일본 e2e 하네스(Test_E2E_v125/kcr_sphere) — v124 로 먼저 실패 확인 → v125 로 통과
- [x] 회귀 L — MinimumModel md5 그대로·말뭉치 L 703건 모두 같음(658965c 대비)
- [x] 적대 리뷰 L — 확정 6(L-5 는 bc16e34 로 이미), 가능성 8, 범위 밖 5 → 수정 묶음 M
- [x] M Runner(ae3818d) — R1 노드별 메모리·R2 CPU 상한+W 맞춤·R3 무제한 명시값·R4 ncpu 읽기·R5 --help 옵션 줄·R6 SIF 판 엇갈림 경고·Loaded 줄 없음·yield_map 절대 경로
- [x] M KMM(62ba543 K2·96acbaa K3·68b954b K4·253df8c K1) — K1 εp=0 보간/외삽·K2 DEFINE_CURVE 머리 정밀도·K3 MAT_017 카드 2·K4 MAT_024 카드 3·4 생략
- [x] M 시험 — 새 검사 모두 수정 전 판에서 실패 확인(아는 불량 먼저)
- [x] 시험 33종 전부 통과(새 시험 3종 포함)·MinimumModel md5 그대로(ec4c907d·53d24150)
- [x] a9 지적(metavar 없으면 'PARALLEL_RUNS')은 실측상 잡힘 — argparse 실출력 시험으로 굳힘(1633041)
- [x] 말뭉치 M — 715건: 같음 705(예전 말뭉치 703 전부), 다름 10 = 전부 의도(리뷰 L 탐침·시험 덱 — 커브 머리 값 보존, MAT_024 EPS·ES 순서, 옛 판 rc 1 → rc 0: MAT_003 _TITLE·MAT_017 카드 2·MAT_024 카드 생략)
- [x] 집중 리뷰 M — 확정 3·가능성 3·범위 밖 6
- [x] N Runner(b215be9) — 한 노드에 맞춤·--help 정의 줄 토큰·yield_map scenario 폴더·미설정 메모리
- [x] N KMM(24135b3·4a0e219) — _real10 'E-5' 꼴·BPM SF·커브 점 안정 정렬, 새 검사 모두 수정 전 판에서 실패 확인
- [ ] 시험 전부·말뭉치 N(리뷰 M 탐침 포함)·집중 리뷰 N(진행 중)
- [ ] 빌드 KMM·KCR → SIF v125 → tar → Drive·메일, 헤드 /opt
- [ ] a9 — ② 0건 비 0 종료 ③ --parallel-runs(선행 캐시 채우기) ④ --yield-map → Post v42
