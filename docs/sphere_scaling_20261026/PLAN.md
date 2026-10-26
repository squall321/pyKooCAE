<!-- sphere_report 자동화 — 런 수 기반 자원·도구 안 병렬·조용한 0건·파트별 항복응력 계획 -->
# sphere_report 자동화 수정 계획 (2026-10-26)

근거: 「sphere_report 자동화 수정안 v1.0」(M3_P2 979런 실패·수동 12샤드 복구 실측). 그 문서의 /data/M3_P2 등은
이 dev 서버에 없다(운영 클러스터 기록으로 보임) — 수치는 그 문서의 실측을 쓰고, 코드는 이 저장소·KooD3plotReader 로 대조했다.

## 무엇이 틀렸나 (코드 대조)
1. 자원이 런 수와 무관하다 — `Runner/PostprocessShellGenerator.build_sphere_sbatch` 가 `postprocess.sphere_*` 가 없으면
   **LS-DYNA 런 환경값**(environment.ncpu·memory)을 그대로 물려받고, 시간은 고정(코드 기본 4h, MCP scenario_builder 도 04:00:00).
   부르는 곳은 둘 — `KooChainRun._maybe_submit_sphere_after`, `Runner/SlurmSubmitter._maybe_submit_sphere_job`.
2. 도구가 0건이어도 rc 0 — `koo_sphere_report/__main__.py` 가 `Loaded 0 results` 뒤 빈 리포트를 쓰고 끝난다.
3. 도구가 순차다 — `koo_sphere_report/loader.py` 흐름 루프가 런마다(캐시 miss 면 binout 처리 ~3.2분) 한 줄로 돈다.
   koo_impact_report 에는 이미 `--parallel-runs`(ProcessPoolExecutor, SLURM_CPUS_PER_TASK 자동)가 있다.
4. 항복응력이 350 고정 — `PostprocessShellGenerator.DEFAULT_YIELD_STRESS`, 도구는 `--yield-stress` 하나뿐.

## 나누기
- pyKooCAE(이 세션): ① 자원 산출, ④ 항복응력 맵을 KMM 이 덱에서 만들고 자동화가 넘긴다, ②③④ 의 자동화 쪽 배선.
- KooD3plotReader(a9 세션과 조율): ② 0건 비정상 종료, ③ `--parallel-runs`(캐시 채우기 선행 단계), ④ `--yield-map` 소비.

## 설계
- ① n_runs = runner_config 의 DOE 수(배열 잡이라 jobs.json 잡 ID 수 ≠ 런 수). 명시 `postprocess.sphere_*` 는 그대로 우선.
  LS-DYNA environment 의 ncpu·memory 는 더 이상 물려받지 않는다. 기본 산식(문서 실측 979런 84.7 GB·런당 3.2분):
  메모리 = max(32, 32 + 0.10×N) GB, 시간(시간) = max(4, 2 + 0.06×N / W), CPU = W(도구가 병렬을 지원하면 min(16, max(2, ⌈N/50⌉)), 아니면 2).
  제출 시 파티션 MaxTime·노드 메모리를 읽어(scontrol·sinfo) 넘으면 상한으로 줄이고 알린다.
- ③ sphere_report.sh 가 실행 시점에 SIF 의 `koo_sphere_report --help` 로 `--parallel-runs`·`--yield-map` 지원을 확인하고, 될 때만 넘긴다
  (옛 SIF 와 섞여도 argparse 오류로 죽지 않게 — impact V6 와 같은 방식).
- ④ KMM DROP 모드가 낙하 덱을 쓸 때 파트별 항복응력 맵(JSON)을 함께 쓴다 — MAT_003·MAT_024(SIGY, LCSS 면 커브 첫 응력 × SFO + OFFO)·
  MAT_ORIENTED_CRACK. 맵에 없는 파트(탄성·강체·해석 안 하는 재질형)는 도구가 `--yield-stress` 로 판정하고 리포트에 그렇다고 적는다.

## 검증
- ① 단위 시험(n_runs 별 #SBATCH 값·명시값 우선·environment 무시·상한), ③④ 는 옛 SIF(옵션 없음)와 새 SIF 양쪽에서 sphere_report.sh 가 도는지.
- ④ 맵: MAT_003·MAT_024(SIGY·LCSS)·탄성·강체 덱으로 기대 맵 대조. 기존 시험 전부·MinimumModel md5.
- 빌드(KMM·KCR) → SIF v125 → tar. 도구 쪽은 Post v42.
