<!-- KCR v134 — 사전 해석 ENDTIM 으로 DROP DOE 의 실행 순서·동시 칸 수를 정하는 계획과 계약 -->
# 계획 — KCR v134 DOE 실행 순서·칸 수 (2026-11-08)

## 왜
전각도 낙하는 사전 해석(endtime_presim·impact_conditions)으로 각도마다 ENDTIM 을 미리 안다. 사용자는 이것으로 몇 대에서·어떤 순서로 풀지 미리 정해, 결과를 가장 빨리 얻고 싶어 한다.

## 조사에서 바뀐 전제
- DROP 기본 제출(`submit --mode cumulative`)은 Slurm 배열이 아니다. DOE 마다 sbatch 를 하나씩 DOE 번호 순서로 내고, 동시 상한은 없다.
  - `exclusive` 기본 켬이라 노드당 1잡이고, 실제 동시 수는 빈 노드 수다.
  - 배열·`%N` 은 `--mode large-scale` 에만 있고, jobs.json·rerun·harvest 와 이어져 있지 않다.
- `--sequential` 은 `--nodes` 개 칸 잡에 `(d − 1) % N` 라운드로빈으로 DOE 를 나눈다. 칸 수가 곧 동시 상한이다.
- KCR D2R 은 비행 중 강체·접촉 중 변형체로 오가는 짝 스위치다. 접촉 구간 합은 Σ ENDTIM 의 0.5% 다. 실행 시간 자료는 없다(LS-DYNA 라이선스 10-16 만료).
- DOE 번호는 표 7종·alias·파일 이름·jobs.json·impact index.json·Post 계약의 정체성이다. 그래서 **번호는 그대로 두고 제출 순서·칸 배정만 바꾼다.**

## 얼마나 줄어드나 (2만 방향 ENDTIM 표, 잡당 고정비 300 s · 해석 1 ms 당 20 s 가정)
| 경우 | 지금 | 긴 것부터 | 비고 |
| --- | --- | --- | --- |
| 기본 제출(빈 노드를 Slurm 이 채움) | — | 0~0.5% | 피보나치 순서가 이미 길고 짧은 것을 섞어, 하한(max(최장, 합 ÷ N))에 붙어 있다 |
| `--sequential` 고정 칸, 2만 개 | 라운드로빈 | N 50·100·300·1000 에서 2.9·4.2·11·26% | |
| `--sequential` 고정 칸, 100 개 | 라운드로빈 | N 4·10·25·50 에서 15·19·37·38% | |
| 무릎 대수 | — | 100 개 약 25~30, 2만 개 약 4000 | 넘으면 최장 잡이 완료 시각을 정한다 |

기본 제출에서는 순서 효과가 거의 없다. 그래도 공짜이고, 긴 잡이 끝 무렵에 몰리는 나쁜 경우를 막는다. 큰 효과는 고정 칸 배정과 대수 추천에 있다.

## 사용자 결정 (11-08)
- 목표는 최단 완료(긴 것부터, LPT)다.
- 동시 칸 수는 상한(노드·라이선스) 안에서 자동이다. 완료 시각이 더 줄지 않는 가장 작은 대수(무릎)다.
- 반영은 기본 제출을 긴 것부터, `--sequential` 은 칸 수 고정에 긴 것부터 가장 빈 칸으로 넣는다. 배열(`%N`)은 만들지 않는다.
- D2R 은 ENDTIM 비례로 두고 '보정 안 됨' 으로 표시한다.
- 시간은 상대값에 기본 고정비·ms 당 시간(키로 바꿈)이다.
- 키는 `environment.schedule` 이다. 기본으로 켠다 — ENDTIM 표(doe_endtim)가 있으면 자동이고, `"schedule": false` 나 `{"enabled": false}` 로 끈다(11-08 확인).

## 계약 (이름 사용자 확인 11-08)
### 1. 새 모듈 `Runner/DoeSchedule.py` (순수 함수)
- `doe_costs(runner_config, opts)` → `{doe: 초}`.
  - 비용 = overhead_seconds + seconds_per_ms × Σ_스텝 T_ms(d, s).
  - T 는 `doe_endtim` 값(덱 시간 단위 → ms), 없는 스텝은 tFinal 이다.
  - DR(dynamic relaxation) 켜진 둘째 스텝부터는 + tFinal 이다. 기존 F_d 와 같은 구조이고, 올림 없이 연속값이다.
  - 표가 없으면 None(모든 DOE 비용 같음 → 지금 동작 그대로).
- `lpt_order(costs)` → 비용 내림차순 DOE 목록이다. 같으면 DOE 번호 오름차순(결정적)이다.
- `lpt_lanes(costs, n)` → 칸 n 개에 긴 것부터 가장 빈 칸으로 넣는다(같으면 낮은 칸 번호). 칸 안 순서도 긴 것부터다.
- `makespan(costs, n)`·`lower_bound(costs, n)` = max(최장, 합 ÷ n).
- `knee_n(costs, cap, tol)` → n ≤ cap 가운데 makespan(n) ≤ (1 + tol)·makespan(cap) 인 가장 작은 n 이다.
- `d2r_active(runner_config)` → drop_surface.deformable_to_rigid 가 켜졌고 게이트를 지나 카드가 생기는지 본다. 게이트는 RigidWall 아님·include_wall_in_general 아님·바닥 접촉 S2S 다.

### 2. 키 `environment.schedule` (environment 는 runner_config 로 그대로 넘어간다)
| 키 | 기본 | 뜻 |
| --- | --- | --- |
| `enabled` | true | 표가 있으면 켠다. false(또는 `"schedule": false`)면 지금 동작 그대로 |
| `licenses` | null | LS-DYNA 동시 라이선스 수. 칸 상한 = licenses ÷ licenses_per_job |
| `licenses_per_job` | 1 | 잡 하나가 쓰는 라이선스 수 |
| `max_concurrent` | null | 그 밖의 동시 상한 |
| `overhead_seconds` | 300 | 잡당 고정비(KMM·apptainer 기동·대기 0~300 s 평균·리포트) |
| `seconds_per_ms` | 20 | 해석 1 ms 당 시간 — 보정 안 됨(Test_005 1 MPP 226 s/ms 에서 16~32 코어로 줄인 추정) |
| `knee_tolerance` | 0.05 | 무릎 판정 여유 |

### 3. KCR (`KooChainRun`)
- **submit 기본(cumulative).** sbatch 순서를 `lpt_order` 로 바꾼다. 스크립트·jobs.json 형식은 그대로다(키 순서만 제출 순서).
- **`--sequential`.**
  - 칸 수 = knee_n(비용, cap) 이다. cap = min(--nodes, licenses ÷ licenses_per_job, max_concurrent).
  - 배정은 `lpt_lanes` 이고, 칸별 `--time` 은 지금처럼 칸의 F_d 합 최대다.
- **rerun.** 대상 DOE 를 `lpt_order` 로 다시 제출하고, `--sequential` rerun 은 `lpt_lanes` 로 한다.
- **`slurm_scripts/schedule.json`.** 비용·순서·칸 배정·cap·무릎·대수별 예상 완료 시각·하한·D2R 표시·가정값(보정 안 됨)을 남긴다.
- **prepare.** 표가 있으면 미리보기 한 줄을 찍는다(DOE 수·예상 합·최장·무릎 대수).

### 4. 지켜야 할 것
- `enabled` 가 꺼졌거나 표가 없으면 지금과 바이트까지 같다(스크립트·jobs.json·제출 순서). 켜졌어도 비용이 모두 같으면 순서는 DOE 번호 순서다.
- DOE 번호·표·alias·파일 이름은 바꾸지 않는다.
- impact_conditions 의 심각도 순서·progressive 피보나치·reprioritize 는 켜졌을 때 제출 순서를 덮어쓴다. 문서에 적고, 끄는 길(`enabled: false`)을 둔다.

## 시험·검증
- `tests/test_doe_schedule.py`: LPT 를 작은 집합의 전수 탐색과 대조한다. 그 밖에 하한·무릎·같은 값 처리·단위 환산·DR·D2R 게이트를 본다.
- KCR 가짜 sbatch 시험: 기본 제출 순서, `--sequential` 칸 수·배정·`--time`, rerun 순서, schedule.json, 꺼짐 바이트 동일을 본다. 기존 시험의 라운드로빈 기대값(test_kcr_endtime_presim.py:840)은 꺼짐 경우로 남긴다.
- 2만 방향 표로 위 이득 표를 다시 낸다(시험 안 수치).
- 실제 클러스터 제출은 이 호스트 노드가 꺼져 있어 못 한다. 가짜 sbatch 까지만 본다.

## 다른 세션
pykoocae-53 이 KMM 누적 체인 결함(KooDynaAdvancedModification·KooMeshImporter·KooDynaAdditional·DTI)을 고친다. v134 는 KooChainRun·Runner(DoeSchedule 새로·JobManager·CumulativeDesigner 미리보기)만 고친다. CumulativeScenarioRunner.py 는 건드리지 않는다. 빌드는 서로 알린 뒤 하나씩 한다.
