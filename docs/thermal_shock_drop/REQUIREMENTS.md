# 열충격 → 낙하 시나리오 — 가능 범위와 필요한 것 (2026-09-21)

요구: **국부 발열(칩 자체발열)과 환경조건(챔버 온도) 모두** 표현할 수 있어야 하고, 그 열응력을 품은 상태로 낙하로 이어져야 한다.

아래는 코드 근거(파일:줄)와 배포본 실행으로 확인한 것이다. 25 에이전트 교차조사 + 반박 검증을 거쳤고,
초안에서 틀렸던 두 곳(경계조건 카드 "없음", 자원 설정)은 정정했다.
시나리오 초안은 [Examples/thermal_shock_drop/](../../Examples/thermal_shock_drop/).

## 1. 지금 되는 것

| 열하중 | 지정 | 덱에 들어가는 카드 | 해석 성격 |
|---|---|---|---|
| **환경조건(챔버)** | `thermal.thermal_type: UniformChamber` + `base_temp_C`/`target_temp_C`/`ramp_time_s` | `*DEFINE_CURVE` + `*LOAD_THERMAL_VARIABLE`(NSID=0, ts=ΔT, tb=base) + 파트별 `*MAT_ADD_THERMAL_EXPANSION` **이 3종뿐** | `*CONTROL_SOLUTION` 은 입력값(SOLN=0) 유지 — **열해석이 아니라 전 절점 규정온도를 준 explicit 구조해석** |
| **국부 발열** | `thermal_type: ICPower` + `materials`(파트별 rho·hc·tc) + `heat_sources`(파트·W·mm³) | pass1 `*CONTROL_SOLUTION(SOLN=1)`·`*CONTROL_THERMAL_SOLVER/TIMESTEP`·`*MAT_THERMAL_ISOTROPIC`·`*INITIAL_TEMPERATURE_SET`·`*SET_SOLID`+`*LOAD_HEAT_GENERATION` / pass2 구조 + `LOAD_THERMAL_D3PLOT` + CTE | 2-pass 열전도 → 온도장 → 열응력 |

- ICPower 는 **클러스터 e2e 완주 기록이 있다**(pass1→pass2 Normal termination). 과거 막혔던 온도 d3plot 패밀리(`T=`) 문제는
  커밋 `67f5b55` 로 해소됐고 `d3plot_merged` 산출물이 남아 있다. 골든 자산은 `/data/koopark/Test_ICThermal/`.
- 스텝별 값 덮어쓰기 가능 — `cumulative.step_params.<스텝번호>` > `simulation_params.thermal` > 기본값
  (`CumulativeScenarioRunner._therm_get`, :1688-1694). `mode_sequence: ["THERM","THERM","DROP"]` 로
  −40 ℃ → +125 ℃ **반쪽 사이클 1스텝** 매핑이 되고 6스텝까지 옵션파일 방출을 확인했다.
- `thermal_conditions` 개수 = DOE 수. 단 **이름만 바뀌고 물리값은 전 DOE 동일**하다(`CumulativeDesigner.py:226-270`).
  −40/125 와 −55/150 을 한 시나리오로 동시에 돌릴 수는 없다.

## 2. 막힌 것

### B1. THERM 스텝이 dynain 을 만들지 않는다 🔴
`*INTERFACE_SPRINGBACK_LSDYNA` 는 `DropAttitude`(KooDynaAdvancedModification.py:2226)와
`DropWeightImpactTest`(:3938)에서만 발행된다. `ThermalLoad`(:5266-5321)는 발행하지 않는다.
러너는 비-ICPower 스텝마다 `Output/dynain` 을 기다리고(`CumulativeScenarioRunner.py:1256-1268`,
기본 `timeout_dynain_seconds` = 604800 초 = 7일) 없으면 실패 처리한다 → **사실상 hang**.

- 우회(실증됨): 입력 `.k` 에 전 파트를 담은 `*SET_PART_LIST` + `*INTERFACE_SPRINGBACK_LSDYNA` 를 미리 넣으면
  KMM THERMAL_LOAD 가 그대로 보존한다. `/data/koopark/Test_ICThermal/MinimumModel.k` 에는 이미 들어 있다.
- 우회(방어): `environment.timeout_dynain_seconds: 600` 로 낮춰 hang 대신 빠른 실패로 만든다.
- 구현안: `ThermalLoad` 에도 두 낙하 모드와 같은 springback 카드 발행을 추가한다.

### B2. THERM 스텝이 `dynaintoinitial.txt` 를 만들지 않는다 🔴 체인의 핵심 결손
이월 배관(dynain → DYNAIN_TO_INITIAL → `*INITIAL_STRESS_SOLID` + 변형좌표)은 DROP/IMPACT 쪽에 완성돼 있는데,
THERM 은 그 입구를 만들지 않는다(생성처는 :3104-3130, :4494-4497 두 곳뿐).
비최종 THERM 스텝은 항상 degraded → **다음 낙하 스텝이 원본 모델로 되돌아가 열응력이 조용히 사라진다.**

- 방어: `environment.strict_accumulation: true` (🔴 `execution` 이 아니라 **`environment`** — `CumulativeDesigner.py:967`).
  켜면 조용한 소실 대신 스텝 실패로 멈춘다.
- 우회(2단계 수동 브릿지): §4 런북 참조.
- 구현안: `ThermalLoad` 에 `DynamicRelaxation/dynaintoinitial.txt` 생성 블록 추가(낙하 모드와 동일 형식).

### B3. 국부 발열과 환경조건을 동시에 못 쓴다 🔴 요구사항 직결
`thermal_type` 이 배타다. ICPower 는 `initial_temperature_C` 로 **출발 온도**만 환경온도로 둘 수 있고,
그 온도를 **유지**하거나 시간에 따라 바꿀 수단이 없다(단열체 내부 발열 → 온도가 계속 상승. 코드도
`steady(ATYPE=0)는 heat sink 필요 — 미구현` 을 경고한다).

- 🔴 **정정(2026-09-22)**: 처음에 "카드 클래스가 이미 있다"고 적었으나 틀렸다. `KooCAEManager/KooBoundary.py` 의
  `KooBoundaryConvection`·`KooBoundaryTemperature` 는 **CAD 형상용 클래스로 LS-DYNA writer 도 매니저도 없다**
  (초기화도 `super(X).__init__` 오용으로 깨져 있다). 그래서 실제로는 카드 구현이 필요했다.
- ✅ **구현 완료**: `KooBoundaryNode.py` 에 `KooBoundaryConvectionSet`·`KooBoundaryTemperatureSet` 카드 클래스와
  매니저 API 를 추가하고, `KooThermalLoad.apply_ambient_boundary` 로 외피 세그먼트에 적용한다.
  옵션은 `Ambient` 블록(mode/h/temp_C/pids/TempCurve), 시나리오는 `simulation_params.thermal.ambient`.
  국부 발열(`heat_sources`)과 **동시 사용 가능**하다.
- 구현안: (1) 옵션 키 `Convection`(h, T∞ 곡선)·`BoundaryTemperature` 를 THERMAL_LOAD 파서에 추가하고
  외피 세그먼트에 적용, (2) `heat_sources` 를 환경조건과 함께 허용(또는 ICPower 에 T∞ 곡선 키 추가).
  이게 들어가면 환경온도 유지·열충격 표면 구배·ICPower steady 가 한 번에 열린다.

### B4. 열충격의 공간 구배를 못 만든다
`UniformChamber` 는 전 절점 동일 온도라 두께방향 구배가 0 이다. 규격(JESD22-A106·IEC 60068-2-14)의 급랭 전이 구간에서
나오는 구배 응력은 재현되지 않는다. 지금 정직하게 말할 수 있는 범위는 **"균일 ΔT 에서의 파트 간 CTE 불일치·구속 응력"** 이다.
두꺼운 유리·세라믹처럼 구배가 지배적인 대상에는 부적합하다 — B3 배선이 전제다.

### B5. dwell(유지)·사이클 횟수를 시나리오로 못 준다
`ENDTIM` 이 `RampTimeS` 로 고정된다(`KooDynaAdvancedModification.py:5278`). 목표 온도 도달 순간 해석이 끝나 유지 구간이 없다.
KMM 파서는 `TempCurve … EndTempCurve` 를 지원하지만(`KooMeshModifier.py:2549-2562`) 러너가 직렬화하지 않아
scenario.json 으로는 도달할 수 없다(`CumulativeScenarioRunner.py:1755-1772`).
⚠️ 게다가 `TempCurve` 의 종축은 **절대온도가 아니라 0~1 factor** 다(`KooThermalLoad.py:49-61`). KMM help 서술과 어긋난다.

- 우회: 반쪽 사이클 = THERM 스텝 1개로 매핑(사이클 수 = 스텝 수). 유지가 꼭 필요하면 옵션파일을 손으로 고쳐 KMM 단독 실행.
- 구현안: `thermal.temp_curve: [[t, factor], …]` 직렬화(3줄) + help 문구 정정 + `tFinal` 분리.

### B6. THERM 이 섞이면 낙하 자세 DOE 를 못 쓴다
`mode_sequence` 에 THERM 이 하나라도 있으면 Designer 가 `_process_thermal_scenario` 로 분기해
`angle_source` 를 통째로 무시하고 전 스텝 각도를 0/0/0 으로 채운다(`CumulativeDesigner.py:209-224`, :252-270).
`prepare` 실험으로 확인했다(angle 3점 + 조건 2개 → DOE 2개, 각도 전부 0).

- 우회(실증됨): `prepare` 후 `runner_config.json` 의 `scenario.doe_angles[<doe>][<낙하스텝>]` 의 roll/pitch/yaw 를 직접 편집한다.
  러너는 이 표만 본다. 또는 낙하를 별도 DROP 시나리오로 분리한다.
- 구현안: THERM 스텝은 `thermal_conditions`, DROP 스텝은 `angle_source` 를 쓰도록 DOE 생성을 교차.

### B7. 이월 덱에 열하중이 남는다 (수동 브릿지 시 주의)
`DYNAIN_TO_INITIAL` 은 `LOAD_*` 를 지우지 않는다. 그래서 열 스텝 기반 `_dti.k` 는 `*LOAD_THERMAL_VARIABLE` + 램프 커브를
낙하 덱까지 끌고 간다 → 낙하 t=0 에 base 온도로 되돌아갔다가 다시 승온한다.
또한 미해석 키워드 raw 블록이 **두 번** 출력되어 열하중·CTE 카드가 2배로 들어가는 것도 관측됐다(별개 KMM 결함 의심, 미수정).

- 처리: 목적에 따라 하나를 고르고 명시한다. (A) **응력만 이월** — `_dti.k` 에서 `*LOAD_THERMAL_VARIABLE`·`*DEFINE_CURVE(ThermLoad_temp_curve)` 삭제,
  CTE 카드는 1개만 남긴다. (B) **온도 유지 낙하** — 커브를 t=0 부터 factor 1.0 인 평탄 2점 커브로 바꾼다.

### B8. 준정적 열응력을 만들 수 없다
THERM 에 `dynamic_relaxation` 이 배선돼 있지 않고 ENDTIM=ramp 라 램프 종료 즉시 끝난다 → 관성 링잉이 섞인 응력이 이월된다.
우회는 `ramp_time_s` 를 구조 최저 고유주기보다 충분히 길게 잡고 모델의 `*DAMPING_*` 로 죽이는 것뿐이다.

## 3. 준비물

### 모델 (`.k`)
- 단위계 **ton-mm-s** 통일. 열 스텝 전용 입력을 따로 준비한다 — THERMAL_LOAD 는 **가산만** 하므로
  `*INITIAL_VELOCITY`·낙하판 파트·rigidwall 이 남아 있으면 열해석이 오염된다.
- **전 파트를 담은 `*SET_PART_LIST` + `*INTERFACE_SPRINGBACK_LSDYNA`** (B1 우회. 없으면 dynain 이 안 나와 7일 대기).
- **CTE**: `thermal.part_cte {pid: 1/K}`, 미지정은 `default_cte_1_K`. (FR4 ~1.8e-5, Si ~2.6e-6, Cu ~1.7e-5)
- **ICPower 는 전 파트 열물성 필수** — `materials {pid: {rho, hc, tc}}` (SI 로 주면 코드가 ton-mm-s 로 환산).
  🔴 빠진 파트는 **예외 없이 0 으로 카드가 써지는 무증상 경로**다. 실행 로그의 `→ *MAT_THERMAL_ISOTROPIC TMID=…` 줄에서
  rho·hc·tc 가 0 인 파트가 없는지 반드시 확인한다.
- **발열원**: `heat_sources [{part, power_W, volume_mm3}]`. 부피는 직접 줘야 하고 0 이면 오류, 발열 파트는 솔리드여야 한다.

### 솔버·클러스터
- **배정밀 필요 여부**: ICPower(열솔버 사용)는 배정밀 필수. node001 에 `LSDynaBasic_aocc420_ompi4.0.5_mpp_d.sif` 확인했다.
  UniformChamber 는 열솔버 카드를 안 쓰므로 단정밀도 이론상 가능하지만 완주 기록이 없다 — 그냥 배정밀을 쓰는 게 안전하다.
  두 이미지 모두 `/opt/ls-dyna/lsdyna_R16.1.1` 심링크로 정밀도에 맞는 바이너리를 노출하므로 `lsdyna_apptainer_sif` 한 줄만 바꾸면 된다.
- **자원** 🔴 현재 node001 의 Slurm 배분은 **2 CPU · 4 GB** 다. `ncpu`·`memory` 를 크게 적으면 sbatch 가 영구 PENDING 이 된다.
  `ncpu: 2`, `memory: "3G"`, **`lsdyna_memory: "300m"`** 를 명시한다. `lsdyna_memory` 를 빼면 `memory` 의 "3G" 가
  LS-DYNA 실행라인에 새어 들어간다. 배정밀은 1 word = 8 byte 라 같은 `300m` 이 두 배 메모리다.
- **시간**: sbatch `--time` 은 `environment.timeout` × 2 로 정해진다. `time_limit` 은 **죽은 키**다.
  러너의 wall-clock 절단은 `timeout_per_step_seconds` 로 별개다 — 둘 다 맞춘다.
- **라이선스**: `lsdyna_apptainer_env.LSTC_LICENSE_SERVER = 192.168.122.1`.
  LSTC 서버는 `@reboot` + 매분 워치독 크론이 걸려 있어 재부팅 후 수동 기동은 불필요하다(과거 기록은 stale).
- **노드**: node001 만 idle. node002·viz 2대는 down.

### 산출물 검증
- 열 카드: `ThermalSet.k` 에서 `grep '\*LOAD_THERMAL_VARIABLE' -A4`(ts=ΔT, tb=base), `grep -c '\*MAT_ADD_THERMAL_EXPANSION'`
  (= 전체 파트 수인지), `grep -c SPRINGBACK`(=1 이어야 dynain 이 나온다).
- 이월: 낙하 스텝 입력 덱에 `*INITIAL_STRESS_SOLID`(또는 dynain include)가 있는지. 없으면 B2 에 걸린 것이다.
- `simulation_index.json` 의 `degraded` 필드 — 값이 있으면 그 스텝의 열응력이 낙하로 넘어가지 않았다는 뜻이다.
- ⚠️ `ThermalSet.json` 의 `scenario_mode` 가 `%DROP%` 로 박혀 있고 온도·CTE 항목이 없다. 산출물만으로 열조건을 되짚을 수 없다.

## 4. 런북 — 지금 당장 열충격→낙하를 얻는 2단계 수동 브릿지

1. **열 스텝**: `scenario_1_chamber_only.json`(또는 `_2_icpower_only`)으로 `num_steps: 1` THERM 을 완주시킨다.
   입력 `.k` 에 springback 카드가 있어야 `Run_*/Output/dynain` 이 나온다.
2. **브릿지**: KMM `DYNAIN_TO_INITIAL` 옵션 파일을 손으로 써서 1회 실행한다
   (`*DynainPath` = 그 dynain, `*IncludeStress,True`, `*RemoveDynamicRelaxation,True`). 산출 `_dti.k` 를 얻는다.
3. **정리**: `_dti.k` 에서 B7 처리를 한다(응력만 이월할지 온도 유지할지 고르고, 중복 raw 블록도 확인).
4. **낙하 스텝**: 그 `_dti.k` 를 `template` 으로 하는 **DROP 전용 시나리오**를 만든다. 이때는 `angle_source` 가 정상 동작하므로
   26 방향이든 특정 모서리든 자유롭게 줄 수 있다(B6 회피).

## 5. 구현 우선순위

| 순위 | 항목 | 효과 | 규모 |
|---|---|---|---|
| 1 | B1+B2 — THERM 에 springback 카드 + `dynaintoinitial.txt` 발행 | 열충격→낙하 체인이 자동으로 성립 | 낙하 모드의 기존 블록 이식 |
| 2 | B3 — `KooBoundary` 의 대류·온도 경계조건을 THERMAL_LOAD 에 배선 | **국부 발열 + 환경조건 동시**, 열충격 구배, ICPower steady | 파서 키 + 세그먼트 적용 |
| 3 | B7 — 이월 시 열하중 정책(제거/평탄화) 옵션화 | 낙하 중 온도 재램프·이중가산 방지 | 옵션 1개 |
| 4 | B5 — `temp_curve` 직렬화 + `tFinal` 분리 + help 정정 | dwell·사이클 프로파일 | 3~5줄 |
| 5 | B6 — THERM 조건축 × 낙하 각도축 교차 | 한 시나리오로 다방향 낙하 | Designer 분기 |

## 6. 재사용 자산
- `/data/koopark/Test_ICThermal/` — ICPower 1스텝 e2e 골든(pass1/pass2 덱·산출물). 물성값 참조 기준으로 쓸 것.
- `/data/koopark/Test_ThermalT1/` — UniformChamber 모델 + scenario(클러스터 e2e 흔적 없음).
- `docs/thermal_icpower_README.md`, `docs/thermal_icpower_scenario_TEMPLATE.json` — 정본으로 볼 문서.
- ⚠️ `docs/manual/.../THERMAL_LOAD.md` §5·§6 과 KMM help 의 ICPower 예제(SI/ton-mm-s 혼용)는 코드와 어긋난다. 믿지 말 것.
