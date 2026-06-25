# 계획 — 반응 적응형 낙하 방향 샘플링 (Adaptive Orientation Refinement)

후처리(deep+sphere) 통합 모드에서, **고해상 전체 격자를 미리 고정**해 두고 progressive로
듬성듬성 전구면을 먼저 탐색한 뒤, 다음 사이클부터는 **이전 결과의 per-part 최대응력이
리스크 높은(평균 대비 z + yield 대비 절대, 둘 다) 방향 주변에 있는 "고정 격자의 미실행
점"을 우선 실행 순서로 끌어올리는** 능동 스케줄링.

> 핵심 (정정): **새 방향을 생성하지 않는다.** 후보 풀은 처음에 정한 fibonacci 전체
> 격자로 고정이고, 알고리즘은 그 격자에서 *아직 안 돈 점들의 실행 순서만* 리스크
> 기반으로 재정렬한다. 위험 영역의 (고정 격자 내) 점들이 먼저 돌아 그 영역 해상도가
> 올라가고, 위험 없는 영역의 미세점은 예산이 끊기면 실행되지 않는다.

---

## 1. 가능성 (결론: 가능)

필요한 데이터·훅이 모두 존재한다.

| 필요 | 출처 | 상태 |
|---|---|---|
| 방향별 per-part 최대응력 | deep_report `Run_*/Output/report/result.json` (`parts[pid].peak_stress`, `summary.peak_stress_global`) | ✅ |
| DOE↔방향(roll/pitch/yaw) | `runner_config` StepConfig.angle_* / `doe_angles` | ✅ |
| 정제 방향 주입 | 각도 소스 `case_txt_file`(명시 각도 리스트) | ✅ |
| 사이클 실행 | KooChainRun prepare→submit→deep/sphere (사이클당 1 DOE 세트) | ✅ |
| 0차 균등 탐색 | fibonacci `progressive`(farthest-point) — 이미 구현 | ✅ |

신규로 필요한 것은 **(a) 결과 수집·핫스팟 판정 모듈** + **(b) 정제 방향 생성** + **(c) 사이클 오케스트레이션 드라이버** 뿐이다.

---

## 2. 개념

```
사전     :  고해상 fibonacci 전체 격자 L (N_full개, progressive 순서) 고정 — 후보 풀
Cycle 0  :  L의 progressive 앞 c개 실행 (전구면 듬성듬성 균등) → deep_report
Cycle n  :  결과 harvest → 리스크(z + yield, 둘 다) 점수 → L의 "미실행" 점 중
            리스크 높은 점 근처 것을 우선 실행 (+ progressive 다음 점 일부 = 탐색)
반복     :  위험 영역의 격자점이 먼저 소비되어 그 영역 해상도↑, 나머지는 듬성한 채.
중간정지 :  전구면 듬성(0차) + 위험영역 조밀 — 예산 끊겨도 의미 있는 커버리지.
```

후보 풀 L은 처음부터 고정(새 점 생성 없음). 알고리즘은 L의 미실행 점에 대한
**실행 우선순위**만 결과 기반으로 갱신한다.

---

## 3. 알고리즘 (사이클 1개) — 고정 격자 L 위에서

표기: L=전체 격자(고정), R=이미 실행+결과 있는 점, U=L\R(미실행).

1. **Harvest** — 완료된 `Run_*/Output/report/result.json` 스캔 → R의 각 점 o 마다
   `{part_p: σ_p(o)}` (per-part 최대응력). o ↔ (roll,pitch,yaw) ↔ 단위벡터. 실패 Run 제외.

2. **per-part 리스크 (둘 다 병행)** — 각 파트 p에 대해
   - 상대: 전 방향 σ_p의 평균 μ_p·표준편차 s_p → `z_p(o)=(σ_p(o)−μ_p)/s_p`
   - 절대: `a_p(o)=σ_p(o)/yield_p` (yield 미지정 시 절대항 생략)
   방향 리스크 `risk(o)=max_p f(z_p(o), a_p(o))` — 예: `max_p max(z_p≥z_thr, a_p≥a_thr)`
   를 만족하면 핫. 점수 자체는 `risk(o)=max_p( w_z·max(0,z_p) + w_a·max(0,a_p−1) )`.
   (파트마다 임계 방향이 다른 것 — 모서리=A, 면=B — 을 per-part max가 잡음.)

3. **핫 점 집합** `Hot ⊆ R` — risk(o) 가 임계 이상.

4. **미실행 점 우선순위** — U의 각 점 u 에 대해
   `priority(u) = Σ_{h∈Hot} risk(h) · K(angdist(u,h))`
   (K=거리 커널: 반경 r 이내 1/0 또는 가우시안). **리스크 큰 점 가까이의 미실행
   격자점일수록 높은 우선순위.** → 그 영역이 먼저 채워지며 국소 해상도↑.

5. **다음 배치 선정 (탐색/활용 혼합)** — 크기 c 배치를
   - 활용: priority 상위 `c·(1−explore)` 개 (U에서)
   - 탐색: progressive 순서상 가장 앞선 미실행 `c·explore` 개 (전역 커버리지 계속)
   로 구성. (둘 다 U=고정 격자의 미실행 점 — 새 점 생성 없음.)

6. **Emit & 제출** — 선정된 (고정 격자의) 점들을 `case_txt` 명시 리스트로 기록 →
   동일 모델/접촉/postprocess 시나리오에 `angle_source=case_txt_file` 로 prepare+submit.

7. **정지** — 총 실행 예산 B 도달 / U 소진 / 핫 집합 안정(새 핫 없음).

---

## 4. 아키텍처 / 통합

- **신규**: `Runner/AdaptiveOrientation.py`
  - `harvest_results(output_dir) -> {dir_vec: {pid: peak_stress}}`
  - `score_hotspots(samples, z_thr, parts_filter) -> [hot_dirs]`
  - `refine(hot_dirs, all_dirs, radius/method, budget) -> [new (roll,pitch,yaw)]`
  - `write_case_txt(dirs, path)`
- **신규 드라이버**: KooChainRun 서브커맨드 `adapt`(또는 `koo_adaptive_drop`)
  - 적응 config 읽기(cycles, budget, z_thr, refine_radius, explore_ratio, parts_filter)
  - cycle 0 = progressive fibonacci → submit → 완료 대기(기존 status/collect + deep done 마커)
  - harvest→score→refine→case_txt→submit 반복
- **재사용**: `case_txt_file` 소스, 기존 submit/deep/sphere, result.json, progressive 정렬.
- 변경 최소 — 기존 단발 파이프라인은 그대로, 위에 적응 루프만 얹음.

---

## 4-1. 실행 모델 — "잡을 처음에 다 던지는데 slurm으로 조정되나?"

**slurm 단독으로는 안 된다.** slurm 스케줄러(FIFO/fairshare/backfill)는 응력 결과를
모르므로, 다 던지면 그냥 큐 순서대로 실행할 뿐 위험영역 우선이 안 된다. 적응시키려면
**결과를 읽어 slurm의 실행 순서 노브(우선순위·hold)를 조작하는 컨트롤러**가 있어야 한다.
두 가지 방식:

### 모델 A — 웨이브 제출 (권장: 단순·견고)
사이클마다 그 배치만 제출 → 완료(+deep_report) 대기 → 결과로 다음 배치 선정 → 제출.
- 장점: scontrol 불필요, 사이클 경계 명확, 로직 단순.
- 단점: 웨이브 사이 노드 유휴(그 사이클 최후 잡+deep 끝날 때까지). 사이클 수만큼 갭.
- "다 던지기"와는 다름 — **나눠 던진다.**

### 모델 B — 전체 제출 + slurm 우선순위/hold 조정 (고이용률)
전체 격자 잡을 처음에 다 제출하되 **cycle-0(coarse)만 정상, 나머지는 `--hold`(또는
최저 우선순위)** 로 둔다. 컨트롤러가 완료 잡의 result.json을 폴링 → 리스크 계산 →
위험영역 근처 hold 잡을 **`scontrol release` / `scontrol update job priority=…`** 로
풀어 slurm이 다음에 돌리게 함. 위험 없는 영역 잡은 hold인 채 → 예산 도달 시 `scancel`.
- 장점: 노드 항상 일감 있음(유휴 최소), "다 던지기"와 호환, 큐가 길수록(노드 적고 N 큼)
  유리.
- 단점: scontrol 관리 + 잡↔방향 매핑 추적 필요. 리스크는 deep_report 후에야 확정이라
  컨트롤러가 deep 결과를 기다려야 함(이건 두 모델 공통).
- 슬럼 메커니즘: `sbatch --hold`, `scontrol release <jid>`, `scontrol update jobid=<jid>
  priority=<n>`, `scancel`.

### 모델 C — 기본은 progressive run, 재우선순위는 생성된 스크립트로 on-demand (채택)
사용자 제안. **default 실행은 원안 그대로** — `run`/`submit`이 progressive(듬성→촘촘)
순서로 전체를 던진다(적응 없음, 동작 변경 없음). 추가로 `prepare`가 기존
stop.sh/rerun.sh/diagnose.sh 처럼 **`reprioritize.sh`(또는 `KooChainRun reprioritize <dir>`)**
를 하나 생성. 사용자가 **원할 때 그 스크립트를 실행**하면:
1. 완료 잡 result.json harvest → 리스크(z + yield, 둘 다) 계산 → 핫 방향
2. **대기(PD) 중인** 잡↔방향 매핑(jobs.json/simulation_index) 으로, 핫 영역 근처
   대기 잡은 앞으로, 먼 잡은 뒤로 재배치
3. 재실행 가능(idempotent) — 결과가 쌓일수록 다시 돌려 큐를 갱신
- 장점: default 경로 무변경, daemon 불필요, "다 던지고 필요할 때 조정" = 사용자 그림.
  웨이브 갭도 없음(잡은 계속 돌고 있음).
- 적응은 순수 **opt-in**(스크립트를 안 돌리면 그냥 progressive 순서대로 끝남).

#### 재배치 메커니즘 — `scontrol top` 우선, hold 폴백 (채택)
1. **주: `scontrol top <jobid>`** — 사용자가 자기 대기 잡을 큐 맨 앞으로 올리는 명령
   (admin 불필요, 단 클러스터가 `enable_user_top` 켜야 동작). 위험영역 근처 대기 잡을
   priority 순으로 `top` 호출 → 그게 다음에 실행됨. (가장 가까운 핫부터 마지막에 top
   하면 최종적으로 큐 최상단을 차지.)
2. **폴백: `scontrol hold`/`release`** — `top` 이 막힌(enable_user_top off) 클러스터면,
   핫 영역에서 **먼 대기 잡을 hold** 로 뒤로 보내 핫 근처 잡이 먼저 돌게 함. 재실행 시
   새로 풀 것 release, 막을 것 hold.
3. 스크립트는 시작 시 `scontrol top` 가용성 1회 탐지 → 가능하면 1, 아니면 2.
- 우선순위 직접 "올리기"(`priority=`/음수 nice)는 operator 권한이라 안 씀.
- 실행 중/완료 잡은 영향 없음(대기 PD 잡만 재배치).

> 결론: **slurm 스케줄러가 자동으로 하는 게 아니라, 생성된 reprioritize 스크립트가
> 결과를 읽고 대기 잡을 hold/release 로 재배치**한다. 모델 C(=사용자 제안)를 채택.
> 모델 A/B 는 대안으로 남김.

> 참고: 현재 KooChainRun `submit`/`prepare`엔 reprioritize 훅이 없다 — 신규로
> `reprioritize` 스크립트 생성 + 그 안의 harvest/risk/hold 로직을 추가.

## 5. 결정 필요 (사용자 확인)

| 항목 | 옵션 / 권장 |
|---|---|
| 핫 임계 | z-score `≥1.0`(느슨)~`≥2.0`(엄격) 또는 상위 X% / 권장 z≥1.5 + 절대(yield) 병행 |
| 정제 방식 | 측지선 bisection(권장) vs 구면캡 패치 |
| 정제 반경/깊이 | 사이클마다 국소 간격 절반(bisection) / 최소각 도달 시 정지 |
| 탐색:활용 비율 | 예: 사이클당 70% 정제 + 30% progressive 신규 / 조정 가능 |
| 예산 | 총 방향 수 상한, 최대 사이클 수 |
| per-part 범위 | 전체 파트 vs 관심 파트셋(critical parts filter) |
| 기준 | 상대(평균 대비 z, 사용자 명시) vs 절대(yield 대비) vs 둘 다 |

---

## 6. 리스크 & 완화

- 그리디 과집중 → 탐색 비율 + 영역당 정제 상한.
- 초기 데이터 희소 → 신뢰 불가한 μ/s → 적응 전 최소 N 요구(cycle 0 충분히 dense).
- result.json 의존 → deep_report 성공 전제(방법1 재사용 경로).
- 방향마다 KooMeshModifier 재생성 비용 → 불가피(사이클 예산으로 통제).

---

## 7. 단계별 구현 체크리스트

- [ ] **P1 분석(무신규시뮬)**: AdaptiveOrientation.harvest + per-part z-score + 핫 선정.
      완료된 fibonacci DROP 테스트 디렉토리로 검증(결과만 읽어 핫 방향 뽑기).
- [ ] **P2 정제생성**: 측지선 bisection + dedup + 예산 → case_txt emit. 단위 검증.
- [ ] **P3 드라이버**: 적응 루프(config, 완료대기, 다음 사이클 submit) + 탐색/활용 + 정지조건.
- [ ] **P4 e2e**: 클러스터(빌드/배포 후) 소규모 다사이클 실행 검증.

---

## 8. 참고 (코드 근거)

- progressive 정렬: `Runner/AngleSourceParser.py` `_farthest_point_order`
- per-part 응력: `koo_deep_report` `result.json` (`parts[pid].peak_stress`)
- 각도 소스: `Runner/AngleSourceParser.py` `parse_case_txt_file_angles` / `CaseTxtFileConfig`
- DOE 방향: `Runner/CumulativeDesigner.py` StepConfig.angle_*
- 후처리 통합: `Examples/postprocess_pipeline/` + `Runner/SlurmSubmitter._maybe_submit_sphere_job`
