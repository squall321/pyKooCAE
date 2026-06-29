<!-- IC 발열 열응력(ICPower 2-pass) 시나리오 사용법 + 클러스터 e2e 안내 -->
# IC 발열 열응력 (ICPower 2-pass) — 시나리오 작성 + 클러스터 e2e

템플릿: [thermal_icpower_scenario_TEMPLATE.json](thermal_icpower_scenario_TEMPLATE.json)

ICPower 는 **2-pass** 로 돈다: pass1(열전달 solve, SOLN=1) → 온도 d3plot → pass2(구조, SOLN=0 + `*LOAD_THERMAL_D3PLOT` + CTE) → 열응력. KooChainRun 이 한 THERM 스텝 안에서 자동으로 두 패스를 엮는다(`_run_thermal_2pass`).

## 🔴 반드시 지킬 것 (안 지키면 실패)

1. **배정밀 SIF.** `environment.lsdyna_apptainer_sif` = `..._mpp_d.sif`.
   단정밀(`_mpp_s.sif`)은 thermal solver 를 `Error 40343` 으로 거부한다.
2. **전 파트 thermal 물성.** `simulation_params.thermal.materials` 에 **모델의 모든 파트 PID** 의
   `rho/hc/tc` 를 넣는다. 누락 파트는 0 으로 들어가 열전도/밀도 0 → solve 실패/발산.
   (CTE 는 미지정 시 `default_cte_1_K` 사용 — 열응력엔 영향, 열전달엔 무관.)
3. **NFS 테스트 디렉토리.** `/data/koopark/Test_*` 에서 실행(컴퓨트 노드가 봐야 함). `/tmp` 금지.

## 필드 설명 (`simulation_params.thermal`)

| 키 | 의미 | 단위(SI 입력) |
|---|---|---|
| `thermal_type` | `ICPower` 고정 (IC 발열 2-pass) | — |
| `analysis_type` | `transient`(검증됨) / `steady`(heat sink 필요, 미구현) | — |
| `unit_system` | `SI`(기본) → 코드가 ton-mm-s 로 환산 / `tonmm` | — |
| `initial_temperature_C` | 초기 온도 | °C |
| `timestep` | `{its,tmax,dtemp}` 열 timestep (transient) | s, s, °C |
| `materials` | `{ "PID": {rho,hc,tc,cte} }` **전 파트** | kg/m³, J/kg·K, W/m·K, 1/K |
| `heat_sources` | `[{part, power_W, volume_mm3}]` 발열 IC | W, mm³ → q'''=power·1000/vol [mW/mm³] |
| `default_cte_1_K` | materials 에 cte 없는 파트 기본 | 1/K |

scenario 쪽: `cumulative.mode_sequence = ["THERM"]`, `thermal_conditions`(조건 리스트=DOE 수, 없으면 단일).

## 실행 (클러스터)

```bash
# 1) 테스트 디렉토리(NFS) 준비: scenario.json + 모델(.k) 동봉
mkdir -p /data/koopark/Test_ICThermal && cd /data/koopark/Test_ICThermal
cp <template>/thermal_icpower_scenario_TEMPLATE.json scenario.json   # 편집: 전파트 물성/heat_sources/모델명
cp <your_model>.k .

# 2) prepare → submit
KooChainRun prepare scenario.json
KooChainRun submit runner_config.json --sequential
KooChainRun status        # pass1(thermal)→pass2(structural) 로그 확인
```

산출: `output/Run_<pass2>/Output/d3plot` = 열응력. pass1 온도 d3plot = `output/Run_<pass1>/Output/d3plot`
(index 에 `thermal_pass1_folder` 로 연결). 재시작 시 pass1 d3plot 있으면 재사용.

## ⚠️ 현재 한계 / 튜닝 항목 (첫 e2e 후 조정)

- **pass 별 종료시간(ENDTIM).** 현재 pass1(열, 길게 hold)·pass2(구조 explicit, 짧게)가 동일 시간을
  쓴다. 첫 e2e 는 **파이프라인 검증**(2-pass 가 엮여 도는지)이 목적이고, 실제 발열량까지 보려면
  pass1 hold 시간을 충분히 줘야 한다 → 결과 보고 조정(코드 보강 예정).
- **누적 thermal→drop(T4)** 미지원(P3). 비최종 THERM 스텝이면 경고 후 다음 스텝은 원본 모델 사용.
- steady(ATYPE=0)는 heat sink(대류/고정온도) 미구현 — transient 사용.

관련: 계획 [PLAN_ThermalStress_Automation.md](PLAN_ThermalStress_Automation.md), 체크리스트 [P2_thermal_checklist.md](P2_thermal_checklist.md)
