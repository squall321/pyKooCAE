# 열충격 → 낙하 시나리오 초안

요구사항·제약·구현 필요 항목은 [../../docs/thermal_shock_drop/REQUIREMENTS.md](../../docs/thermal_shock_drop/REQUIREMENTS.md) 를 먼저 읽을 것.
세 파일 모두 배포본(`/data/SmartTwinPreprocessor/bin/KooChainRun prepare`)으로 검증했다.

| 파일 | 내용 | 지금 돌아가는가 |
|---|---|---|
| `scenario_1_chamber_only.json` | 환경조건 — 챔버 25 → −40 ℃ 균일 ΔT 열응력, 1스텝 | ✅ 돈다 (조건 2개 = DOE 2개) |
| `scenario_2_icpower_only.json` | 국부 발열 — 칩(PID 2) 2 W, ICPower 2-pass, 1스텝 | ✅ 돈다 (배정밀 필수, e2e 골든 있음) |
| `scenario_3_shock_then_drop.json` | 열충격 반쪽사이클 2스텝 → 낙하 | ⛔ 아직 — THERM 이 dynain·`dynaintoinitial.txt` 를 안 만들어 이월이 끊긴다 |

## 쓰기 전에 고쳐야 하는 값
- `base_dir` — 실제 테스트 폴더(NFS `/data/...`)로.
- `scenarios[].template` — 모델 `.k` 경로. **열 스텝 입력에는 낙하용 카드를 남기지 말고**,
  전 파트를 담은 `*SET_PART_LIST` + `*INTERFACE_SPRINGBACK_LSDYNA` 를 넣어 둘 것(없으면 dynain 이 안 나온다).
- `thermal.part_cte` / `materials` — 모델의 실제 PID 로. ICPower 는 **전 파트** rho·hc·tc 가 있어야 한다(빠지면 0 으로 조용히 들어간다).
- `heat_sources[].volume_mm3` — 발열 파트의 실제 부피.

## 자원 설정을 건드리지 말 것
`ncpu: 2` / `memory: "3G"` / `lsdyna_memory: "300m"` 은 현재 node001 의 Slurm 배분(2 CPU·4 GB)에 맞춘 값이다.
크게 적으면 sbatch 가 영구 PENDING 된다. `lsdyna_memory` 를 지우면 `memory` 값이 LS-DYNA 실행라인으로 새어 들어간다.

## 3번을 지금 돌리고 싶으면
REQUIREMENTS.md §4 의 2단계 수동 브릿지를 쓴다 — 1번으로 dynain 확보 → KMM `DYNAIN_TO_INITIAL` 1회 →
`_dti.k` 에서 열하중 카드 정리 → 그 파일을 template 으로 하는 **DROP 전용 시나리오**(이때는 `angle_source` 정상 동작).
