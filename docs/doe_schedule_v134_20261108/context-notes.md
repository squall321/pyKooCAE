<!-- KCR v134 DOE 실행 순서·칸 수 — 결정·근거 노트 -->
# 결정 노트 — KCR v134 DOE 실행 순서·칸 수 (2026-11-08)

## 결정
- **사용자(11-08, 첫 묻기).** 목표 최단 완료, 칸 수는 상한 안 자동(무릎), 반영은 'Slurm 배열 순서·%N', D2R 은 시나리오에서 읽어 맞춤을 골랐다.
- **조사 뒤 다시 물음(11-08).** 배열·%N 은 DROP 기본 제출에 없다. 제가 처음에 있다고 잘못 설명했다. 다시 물어 다음을 골랐다.
  - 기본 제출은 긴 것부터, `--sequential` 은 칸 수 고정에 긴 것부터 가장 빈 칸으로 넣는다.
  - D2R 은 ENDTIM 비례로 두고 '보정 안 됨' 표시만 한다.
  - 시간은 상대값에 기본 고정비다.
- **이름·기본(11-08 확인).** `environment.schedule` 이고, ENDTIM 표가 있으면 자동으로 켠다.
- DOE 번호는 바꾸지 않는다. 재번호는 표 7종·alias·IC 이름·Post 계약을 함께 바꿔야 하고, 다시 prepare 한 폴더에서 러너가 엉뚱한 완료 Run 을 건너뛸 수 있다.

## 근거
- **조사(Explore 에이전트).**
  - 제출 경로: cumulative 는 KooChainRun:2588, sequential 은 :2402-2406, batch 는 :2322-2386, rerun 은 :3070-3239 이고 JobManager.resubmit_does 는 :399 다.
  - doe_endtim 형태는 `{"<DOE>": {"<step>": endtim}}` 이고 DROP 스텝만, 덱 시간 단위다.
  - 이 호스트 Slurm 은 MaxArraySize 10001, Licenses null, backfill, priority/multifactor 다. 노드 node001·002 는 2 CPU VM 이고 꺼져 있다.
- **실측 시간.** Test_005(ENDTIM 5 ms, 1 MPP)는 1089~1188 s 로, 해석 1 ms 당 약 226 s 다. Test_Cum26x3 의 DR 스텝은 약 1.6배다(F_d 는 2배로 잡는다).
- **이득 추정**(scratchpad lpt_gain.py·lane_gain.py, 고정비 300 s · 20 s/ms).
  - 기본 제출(Slurm 동적): 2만 개는 N 2~1000 에서 0~0.5%, 100 개는 −1.2~0.7% 다. 피보나치 순서가 이미 섞여 있어 하한에 붙는다.
  - `--sequential` 고정 칸: 2만 개는 N 50·100·300·1000 에서 2.9·4.2·11·26%, 100 개는 N 4·10·25·50 에서 15·19·37·38% 다.
  - 무릎(Σ ÷ 최장)은 100 개 21~29, 2만 개 3000~4300 이다. 큰 집합은 라이선스·노드 상한이 먼저 걸린다.

## KCR 연결 (11-08, 서브에이전트)
- 계획은 KooChainRun `_doe_schedule` 한 곳에서 짠다. 요약 한 줄을 찍고 `slurm_scripts/schedule.json` 을 쓴다. 틀린 값은 ❌ 뒤 종료 1 이고, 부르는 곳은 모두 sbatch·jobs.json 전이다(2차: 표가 없으면 값을 보지 않는다).
- 기본 제출·batch 폴링은 `_doe_order`(표가 있으면 order, 없으면 1..N)를 돈다. batch 는 같은 폴링에 함께 보인 .done 만 긴 것부터라 효과는 작다(KMM 생성 순서가 먼저다).
- `--sequential` 칸 `--time` 은 지금 식 그대로다(칸 F_d 합의 최대를 모든 칸에). 칸마다 다르게 하지 않았다.
- rerun 은 대상만으로 계획을 짠다(`build_schedule(does=)`). `--sequential` rerun 칸 수도 무릎이다(상한 = 노드 수(--nodes 또는 자동 감지)·licenses·max_concurrent·대상 수). 표 밖 DOE 는 2차에서 바뀌었다(아래).
- rerun 은 `slurm_scripts/schedule_rerun.json` 에 쓴다(mode rerun) — submit 의 schedule.json 을 덮지 않는다(메인 세션 후속, 9a6d0cb).
- prepare 에서 틀린 값은 ❌ 한 줄만 찍고 prepare 는 마친다(표가 있을 때만 — 2차). runner_config 를 쓴 뒤라 멈추면 반쯤 된 상태가 남고, submit·rerun 이 sbatch 전에 멈춘다.
- jobs.json 은 형식·필드 그대로이고 키 순서만 제출 순서다. 읽는 곳(JobManager·AdaptiveReprioritize)은 모두 DOE 키로 찾는다.
- 바이트 동일은 test_kcr_doe_schedule [0] 의 GOLDEN(ddd1a4c 코드로 뽑음)과, HEAD 사본과 화면 출력까지 직접 비교(PID·rerun 시각 빼고)로 봤다. scratch_run 도 직접 비교로 같다.
- test_kcr_endtime_presim 의 라운드로빈 기대값(:840)은 schedule false 로 남겼다. 기본 제출 --time(:835)은 순서와 무관해 켠 채로 둔다.

## 적대 리뷰 반영 (11-08, 2차 — 결정은 메인 세션 확정)
- **knee_tolerance 기본 0.** 0.05 는 실제 2만 표 앞 500 개·`--nodes 19` 에서 18 칸을 골라 v133 라운드로빈보다 3.6% 늦었다. 0 이면 무릎은 makespan(n) ≤ makespan(상한) 인 가장 작은 n 이라 상한 칸 LPT 보다 늦지 않다. 키는 그대로 바꿀 수 있다.
  - 그래도 '켬 ≤ 라운드로빈' 은 늘 참은 아니다. LPT 자체가 라운드로빈에 우연히 질 수 있다(무릎 = 상한인 경우들). 작은 합성 집합(DOE 2~60) 99,764 경우 중 81 경우가 그랬고 최대 약 2% 였다. 실제 2만 표 앞 100 개의 칸 7 에서 0.28%, 앞 1000 개의 칸 37 에서 0.51% 였다.
  - 실제 전체 표(2만 표 N 2..60·100·200·500·1000·2000·5000 등 86 개, 100 방향 표 N 1..100)와 표 모양 합성(DOE 60·200·1000)에서는 모든 N 에서 성립했다. 시험([7])은 이 둘을 엄격히 보고, 작은 합성 집합은 '무릎 칸 완료 ≤ 상한 칸 LPT 완료' 만 본다. 늘 참이게 하려면 LPT 와 라운드로빈 중 짧은 쪽을 고르는 규칙이 더 필요하다(결정 필요, 넣지 않음).
- **다시 셈한 이득(실제 표·기본 가정·무릎 0).** 2만 표: N 50·100·300·1000 에서 2.92·4.16·11.02·26.14%(무릎 50·100·300·1000). 100 방향 표: N 4·10·25·50 에서 14.82·18.55·36.76·37.77%(무릎 4·10·25·31). 0.05 였다면 2만 표 N 50·100 에서 −1.16·0.04% 였다. 기본 제출 이득은 사실상 0(−1.2 ~ +0.5%)이다.
- **칸이 줄면 알림.** submit --sequential·sequential rerun 이 `--nodes`(rerun 은 노드 수)보다 적은 칸을 쓰면 `fewer_slots_line` 한 줄이다. 이유는 상한(licenses·max_concurrent·DOE 수)과 무릎을 나눠 적고, 무릎 칸·상한 칸 예상 완료를 함께 적는다.
- **시간 단위.** 표 메타 time_unit → units 끝(mm-t-s → s, mm-kg-ms → ms) → tFinal 짐작(0.5 이상 ms) 차례다. 짐작하면 알림을 남기고, 계획의 알림은 요약 줄 아래 '    · …' 로 찍는다(submit·rerun·prepare).
- **끔·표 없음은 값을 보지 않는다.** schedule_options 는 false·{"enabled": false} 면 다른 키를 보지 않는다. KooChainRun(_doe_schedule·prepare 미리보기)은 doe_endtim 이 없으면 schedule_options 전에 None 이다. 바이트 동일·검사·경고 없음이 schedule 값과 무관하다.
- **rerun 검사 순서.** cmd_rerun 은 대상이 정해진 바로 뒤에 계획을 짠다. 확인 묻기·--cleanup-stale 삭제 전에 틀린 값으로 멈추고, --dry-run 도 요약 줄을 찍는다(dry-run 은 schedule_rerun.json 을 쓰지 않는다). --sequential 은 그 계획을 _rerun_sequential 에 넘기고, 상한의 노드 수가 다르면(--nodes 없이 자동 감지) 다시 짠다 — 이때 요약 줄이 두 번 나온다.
- **표 밖 DOE(rerun --does).** 표 안 DOE 만으로 짜고 알림을 남긴다. 표 밖 DOE 는 받은 순서 그대로 맨 뒤에 낸다 — 기본은 order 뒤, sequential 은 마지막 칸 맨 뒤다. 그 DOE 의 예전 실패 동작(스크립트 없음·러너 실패)은 그대로다.
- **슬롯 스크립트·batch.** 켜면 `echo "DOEs: …"` 와 'submitted — DOE …' 줄은 DOE 목록(앞 6 개 + …)이다. batch 와 --sequential 을 함께 주면 batch 가 이기므로 `_seq` 를 끄고 칸 없이 mode submit 으로 적는다(마지막 요약은 --nodes).
- **돌연변이.** 리뷰에서 살아남은 M1(첫 sbatch 실패 판정)·M3(sequential rerun --nodes 상한)·M4(KMM 종료 뒤 batch 순서)를 잡는 시험을 넣었다. 새 동작용 돌연변이까지 12 개 모두 잡힌다(scratchpad r8/mutants2.py).

## 알려진 기존 결함 (고치지 않음 — v134 이전부터)
- 꺼짐에서 `submit --sequential --nodes` 가 DOE 수보다 크면 빈 칸의 `doe_list[0]` 에서 IndexError 로 죽는다(켜면 상한이 DOE 수라 생기지 않는다).
- `--sequential` 로 낸 뒤 기본 rerun 은 jobs.json 의 script_path(run_seq_NNN.sh)를 DOE 마다 다시 낸다 — 같은 칸 스크립트가 DOE 수만큼 겹쳐 돈다.
- 꺼짐에서 `rerun --does 3,3` 처럼 같은 DOE 를 두 번 주면 두 번 낸다(켜면 표 안 DOE 는 한 번).
- jobs.json 없이 rerun 하면 resubmit_does 의 load_jobs 가 FileNotFoundError 로 죽는다(상태 표는 경고 뒤 빈 상태로 돈다).
