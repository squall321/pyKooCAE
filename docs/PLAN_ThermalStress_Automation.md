# 고온 열전달·열응력 시뮬레이션 자동화 — 키워드 + 시나리오 구축 계획서

> 근거: LS-DYNA R16 매뉴얼 3-LENS 조사 + emit 인프라 코드 조사. 코드 경로는 모두
> `/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/` 기준 절대경로 표기.
> 추측/미확인은 본문에 **[추측]** / **[미확인]** 태그로 명시.

---

## 0. 현 상태 사실 확인 (가장 중요 — 착수 전 인지)

> **✅ SMOKE TEST 통과 (2026-06-14)** — `/data/koopark/Test_ThermalSmoke/thermal_smoke.k` 단일 hex 발열 deck을
> compute 노드(192.168.122.90)에서 실행하여 thermal solver 실현 가능 **확정**:
> - `*CONTROL_THERMAL_SOLVER` / `*CONTROL_THERMAL_TIMESTEP` / `*MAT_THERMAL_ISOTROPIC` /
>   `*INITIAL_TEMPERATURE_SET`(NSID=0 전체노드 허용) / `*LOAD_HEAT_GENERATION_SET_SOLID` 전부 인식 + Normal termination (3s, d3plot 온도장 출력).
> - **🔴 필수 조건**: thermal은 **배정밀도(double precision, I8R8) SIF 필수**. 단정밀도(`_mpp_s.sif`)는
>   `Error 40343: MPP version of LS-DYNA Thermal is not supported in single precision`로 거부됨.
>   → **`/opt/apptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_d.sif`** (compute 노드에 이미 존재) 사용.
>   thermal scenario.json의 `environment.lsdyna_apptainer_sif`를 `_mpp_d.sif`로 지정해야 함.
>   (기존 DROP/IMPACT/VIB explicit은 `_s.sif`로 충분 — thermal만 `_d.sif`.)
> - 부록 B-1(SIF thermal 지원), B-3(NSID=0 허용) [미확인] → **해소됨**.
>
> **✅ T1 SMOKE 추가 (2026-06-14)** — `/data/koopark/Test_T1Smoke/t1_explicit.k`:
> - T1(균일온도 열응력)은 `*LOAD_THERMAL_VARIABLE` + `*MAT_ADD_THERMAL_EXPANSION` 둘 다 인식 + Normal termination.
> - **🔴 implicit 구조해석 금지**: `*CONTROL_IMPLICIT_*`는 MPP_d 빌드에서 `MPI_Comm_dup internal error`로 죽음
>   (ncpu=1, mpirun -np 1 둘 다 동일). → **T1은 explicit 구조해석**(`*CONTROL_TIMESTEP`, 기존 DROP/IMPACT 결
>   `SetControlandDatabaseExplicit` 재사용)으로 구현. 단정밀이 아닌 `_mpp_d.sif` 사용 (CTE 열응력은 double 필요).
>   T2/T3 thermal solver(pass1)는 implicit 아님(자체 thermal timestep)이라 무관 — 구조 pass2도 explicit 권장.

코드 조사로 확인한 핵심 사실:

1. **THERM 모드는 이미 존재하지만 "껍데기"다.** `Runner/CumulativeScenarioRunner.py` L1241~1262 의 `mode == "THERM"` 분기는 KooMeshModifier용 step_config 텍스트(`THERMAL_CYCLE,1` / `**ThermalCycle` 블록)를 생성한다. 그러나 이 `ThermalCycle` 디렉티브를 **실제로 소비하는 KooDynaAdvancedModification 핸들러는 존재하지 않는다.** `grep`상 `THERMAL_CYCLE` 문자열을 참조하는 곳은 `KooDynaAutomaticSimulationScriptGenerator.py`(스크립트 텍스트)뿐이고, 실제 열 카드를 emit하는 경로는 없다. → **THERM은 미완성 스텁.**

2. **`ThermalSet.k` 파일명 강제만 준비돼 있다.** `_find_input_file()` (L1577~1594) 은 `mode=="THERM"` → `ThermalSet.k` 를 이미 매핑한다. VibrationSet.k 와 동일 컨벤션. 즉 실행 체인 진입로(입력 파일명)는 예약돼 있으나 그 파일을 만드는 emit 로직이 없다.

3. **열 카드 emit 클래스는 거의 전무하다.**
   - `KooBoundary.py` L263~484: `KooBoundaryTemperature / HeatGeneration / HeatFlux / Convection / Radiation` 는 **데이터 스텁** — emit 메서드 없음. L424 이후 블록은 `'''` 주석 처리됨. (사실 super().__init__ 호출도 `KooBoundary).__init__` 으로 깨져 있어 인스턴스화도 안 됨 — 데드코드.)
   - `KooDynaKeyword.py`: `ControlSolution`(L3955) 만 살아있음. `ControlThermalSolver / ControlThermalTimestep` 없음.
   - `KooMaterial.py`: `MAT_THERMAL_ISOTROPIC / MAT_ADD_THERMAL_EXPANSION` 클래스 없음.
   - `KooElementSet.py` (40줄): `SolidElementSet` 은 자료구조만, **emit/WriteStream 전무.**

4. **`*PART` TMID 는 이미 완전 지원.** `KooPart.py` L168 `self.tmid=0`, L978 `SetPartProperty(...,tmid)`, L1054 8번째 컬럼 emit. → 값만 채우면 됨.

5. **emit 패턴 2종이 공존한다.**
   - **패턴 A** (`KooDynaKeyword.py`): `DynaKeyword` 서브클래스 + `writeParameter`(`f"{str(e):>10}"` 10컬럼 우정렬 자동). CONTROL 계열은 이 베이스가 정석.
   - **패턴 B** (`KooMaterial.py`/`KooLoad.py`/`KooInitial.py`/`KooPart.py`): 독립 클래스 + `format(x, ">10")`/`">10.3e"`/`">10.3f"`, `$$` 헤더 직접 `stream.write`. MAT/LOAD/INITIAL/SET 계열이 이 결.

이 계획은 위 사실 위에서 **`*LOAD_BODY_PARTS_<dir>` → `*LOAD_BODY_GENERALIZED_SET_PART` 교체 때 쓴 결**(VibrationSource.py registry + StepConfigBuilder serializer + CumulativeScenarioRunner 분기 + ThermalSet.k)을 그대로 답습한다.

---

## 1. 목표 시나리오 정의

| ID | 이름 | 해석 종류 | LS-DYNA 정식화 | 비고 |
|---|---|---|---|---|
| **T1** | 챔버 균일 온도 열응력 (간이법) | 구조 only + 노드 온도장 | `*LOAD_THERMAL_VARIABLE` (또는 LOAD_CURVE) + `*MAT_ADD_THERMAL_EXPANSION` | 열전달 해석 **불필요**. 전 노드 균일 ΔT → CTE로 열변형. 챔버 85°C / -40°C. 가장 싸고 가장 먼저 구현. |
| **T2** | IC 발열 정상상태 → 열응력 | 2-pass: ① steady thermal ② structural | pass1: `*CONTROL_SOLUTION SOLN=1` + thermal solver(ATYPE=0) → d3plot 온도 / pass2: `*LOAD_THERMAL_D3PLOT` + CTE | 온도장이 균일하지 않은 실제 발열 분포. |
| **T3** | IC 발열 과도(파워 프로파일) → 열응력 | 2-pass 또는 연성 | thermal transient(ATYPE=1) + `*LOAD_HEAT_GENERATION_SET_SOLID`(시간곡선) → 시간별 온도 d3plot → 구조 | 1800s 홀드 / 파워 on-off 프로파일. |
| **T4** | 고온 열응력 상태 → 낙하 (누적) | THERMAL_TO_DROP 누적 | T2/T3 결과 응력장(`dynain`) + 온도 IC → DROP 모드 입력 | 기존 누적 체인(DROP 결)과 결합. **[추측]** dynain에 thermal IC 포함 여부 검증 필요. |

**단계적 가치 순서**: T1(독립, 1주) → T2(2-pass 인프라) → T3(과도/곡선) → T4(누적 결합). T1 만으로도 사용자가 즉시 쓸 수 있는 산출물이 나온다.

---

## 2. 추가해야 할 LS-DYNA 키워드 전체 목록

### 2.0 시나리오별 카드 매트릭스

| 카드 | T1 | T2 | T3 | T4 | 패턴 | emit 상태 |
|---|:--:|:--:|:--:|:--:|:--:|---|
| `*CONTROL_SOLUTION` (SOLN) | 0 | 1/2 | 1/2 | 0(drop) | A | **기존** (값만) |
| `*CONTROL_THERMAL_SOLVER` | — | ● | ● | — | A | 신규 |
| `*CONTROL_THERMAL_TIMESTEP` | — | (정상) | ● | — | A | 신규 |
| `*MAT_THERMAL_ISOTROPIC` | — | ● | ● | — | B | 신규 |
| `*MAT_ADD_THERMAL_EXPANSION` | ● | ● | ● | ●(상속) | B | 신규 |
| `*PART` TMID 필드 | — | ● | ● | — | B | **기존** (값만) |
| `*LOAD_HEAT_GENERATION_SET_SOLID` | — | (정상 가능) | ● | — | B | 신규 |
| `*SET_SOLID` | — | ● | ● | — | B | 신규(emit) |
| `*BOUNDARY_CONVECTION_SET` | — | ● | ● | — | A | 신규 |
| `*BOUNDARY_TEMPERATURE_SET` | — | ○ | ○ | — | A | 신규 |
| `*INITIAL_TEMPERATURE_SET/NODE` | (T1대안) | ● | ● | ● | B | 신규 |
| `*LOAD_THERMAL_VARIABLE` | ● | — | — | — | B | 신규 |
| `*LOAD_THERMAL_D3PLOT` | — | ●(pass2) | ●(pass2) | — | B(필드없음) | 신규 |
| `*DEFINE_CURVE` (파워/h/T∞) | — | ● | ● | ●(기존) | A | **기존** [미확인] |

(● 필수 / ○ 선택 / — 불필요)

> **[추측]** T4 가 누적 dynain에 온도장을 함께 실으려면 `*INITIAL_TEMPERATURE` 를 dynain 재작성 단계에 주입해야 한다. dynain 처리 경로는 본 계획 범위 밖이라 P3 검증 게이트로 분리.

---

### 2.1 *CONTROL_SOLUTION

| 필드 | 컬럼 | 의미 | T1 | T2/T3 | T4 |
|---|---|---|:--:|:--:|:--:|
| SOLN | 1–10 | 0=구조 / 1=열 / 2=연성 | 0 | **1**(2-pass thermal) 또는 **2**(연성) | 0 |
| NLQ | 11–20 | 벡터길이 | 0 | 0 | 0 |
| ISNAN | 21–30 | NaN검사 | 0 | 0 | 0 |
| LCINT | 31–40 | 커브 재이산화 점수 | 100 | 100 | 100 |

```
*CONTROL_SOLUTION
$$   SOLN       NLQ     ISNAN     LCINT
         1         0         0       100
```
매뉴얼: Vol I R16, 13_CONTROL.pdf p.12-527~529.
인프라: `KooDynaKeyword.py` `ControlSolution` (L3955) — **이미 emit 가능**. 단, 현재 헤더가 `SOLNF`로 표기됨(L3986). 첫 필드 세터만 추가하면 됨(현재 세터 없음).

---

### 2.2 *CONTROL_THERMAL_SOLVER

**Card 1 (필수)**

| 필드 | 컬럼 | 의미 | T2(정상) | T3(과도) |
|---|---|---|:--:|:--:|
| ATYPE | 1–10 | 0=정상 / 1=과도 | **0** | **1** |
| PTYPE | 11–20 | 0=선형 / 1=비선형(Gauss) / 2=비선형(요소평균) | **2** | **2** |
| SOLVER | 21–30 | 11=직접 / 12=대각CG(MPP기본) | **11**(연성) / 12(열 단독 대형) | 11 / 12 |
| (blank) | 31–40 | — | — | — |
| GPT | 41–50 | Solid 적분점 (0→8) | 8 | 8 |
| EQHEAT | 51–60 | 일→열 환산 | 1.0 | 1.0 |
| FWORK | 61–70 | 소성일→열 분율 | 1.0 | 1.0 |
| SBC | 71–80 | Stefan-Boltzmann | 0 (복사 시 단위계값) | 0 |

```
*CONTROL_THERMAL_SOLVER
$$  ATYPE     PTYPE    SOLVER              GPT    EQHEAT     FWORK       SBC
         1         2        11                   8       1.0       1.0       0.0
```
> 31–40(blank) 컬럼은 빈 10칸으로 유지해야 GPT가 41–50에 정확히 떨어진다. writeParameter는 리스트 원소를 순서대로 10컬럼씩 찍으므로, **빈 필드를 빈 문자열 `""` 원소로 명시**해야 컬럼이 맞는다.

매뉴얼: Vol I, 13_CONTROL.pdf p.12-568~574.
인프라: `KooDynaKeyword.py` `ControlSolution` 옆 신규 `ControlThermalSolver(DynaKeyword)`. Card 2a(MSGLVL/MAXITR/ABSTOL/RELTOL/OMEGA/.../TSF, **TSF=1.0 절대 유지**)·Card 3(MXDMP/DTVF/VARDEN/NCYCL)는 옵션 — 1차 구현은 Card 1만, 옵션은 default 의존.

---

### 2.3 *CONTROL_THERMAL_TIMESTEP

| 필드 | 컬럼 | 의미 | T3(과도) |
|---|---|---|:--:|
| TS | 1–10 | 0=고정 / 1=가변 | **1** |
| TIP | 11–20 | 0.5=Crank-Nicolson / 1.0=완전음해 | **1.0** |
| ITS | 21–30 | 초기 열 스텝 | **0.1~1.0** |
| TMIN | 31–40 | 최소 스텝 | 1e-3~0.01 |
| TMAX | 41–50 | 최대 스텝 | **10~30** |
| DTEMP | 51–60 | 스텝당 최대 ΔT | **5~10** |
| TSCP | 61–70 | 스텝 감소계수 | 0.5 |
| LCTS | 71–80 | (시간,새스텝) 커브 | 0 |

```
*CONTROL_THERMAL_TIMESTEP
$$     TS       TIP       ITS      TMIN      TMAX     DTEMP      TSCP      LCTS
         1       1.0       1.0      0.01      20.0       5.0       0.5         0
```
매뉴얼: Vol I, 13_CONTROL.pdf p.12-575~577.
인프라: 신규 `ControlThermalTimestep(DynaKeyword)`. (T2 정상상태면 timestep 카드 불필요.)

---

### 2.4 *MAT_THERMAL_ISOTROPIC (MAT_T01)

**Card 1**: `TMID, TRO, TGRLC, TGMULT, TLAT, HLAT` / **Card 2**: `HC, TC`

| Card.필드 | 변수 | Si칩 (ton-mm-s) |
|---|---|---|
| 1.1 | TMID | 101 |
| 1.2 | TRO (0→구조밀도) | 2.33E-9 |
| 1.3 | TGRLC (발열곡선) | 0 |
| 1.4 | TGMULT (상수발열) | 0.0 |
| 2.1 | HC (비열) | 7.0E8 |
| 2.2 | TC (열전도도) | 150.0 |

```
*MAT_THERMAL_ISOTROPIC
$$   TMID       TRO     TGRLC    TGMULT
       101   2.33E-9       0.0       0.0
$$     HC        TC
     7.0E8     150.0
```
매뉴얼: Vol II R16, 04_MAT_THERMAL.pdf p.2-3.
인프라: `KooMaterial.py` 신규 `KooMaterialThermalIsotropic(KooMaterial)`, 패턴 B 2장 카드. 구조 MID와 별도 번호공간 — 충돌 방지 위해 TMID는 100번대 권장.

---

### 2.5 *MAT_ADD_THERMAL_EXPANSION

| 필드 | 변수 | Default | 값 (Si칩 CTE) |
|---|---|---|---|
| 1 | PID | none | 1 |
| 2 | LCID (0→상수) | none | 0 |
| 3 | MULT (상수 CTE) | 1.0 | 2.6E-6 |
| 4–7 | LCIDY/MULTY/LCIDZ/MULTZ | LCID/MULT | (등방 생략) |

```
*MAT_ADD_THERMAL_EXPANSION
$$    PID      LCID      MULT
         1         0   2.6E-6
```
매뉴얼: Vol II, 03_MAT_Part1.pdf p.129-140.
인프라: `KooMaterial.py` `KooMaterialAddErosion` 옆 신규 `KooMaterialAddThermalExpansion(KooMaterial)`. **T1~T4 전부 필요** (CTE가 열응력의 근원). 이방성 FR4(z방향 ~50e-6)는 LCIDZ/MULTZ 사용.

---

### 2.6 *LOAD_HEAT_GENERATION_SET_SOLID

**Card 1**: `SID, LCID, MULT, WBLCID, CBLCID, TBLCID`

| 필드 | 변수 | 의미 | T3 (3W 칩, 부피 100mm³) |
|---|---|---|---|
| 1 | SID | 요소 set ID | 100 |
| 2 | LCID | q''' 곡선(0→MULT상수, >0→시간곡선) | 0(정상) 또는 곡선ID(과도) |
| 3 | MULT | q''' [mW/mm³] 상수/배율 | **30.0** (3000mW/100mm³) |
| 4–6 | WBLCID/CBLCID/TBLCID | 생체열(미사용) | 0 0 0 |

```
*SET_SOLID
$$    SID
       100
*LOAD_HEAT_GENERATION_SET_SOLID
$$    SID      LCID      MULT    WBLCID    CBLCID    TBLCID
       100         0      30.0         0         0         0
```
> **체적당** 발열률. 총 W를 칩 부피로 나눈다. 과도 파워 프로파일은 LCID에 (time, q''') 곡선 지정.

매뉴얼: Vol I, 33_LOAD.pdf p.33-67~68.
인프라: `KooLoad.py` 신규 `KooLoadHeatGenerationSetSolid` (패턴 B) + `*SET_SOLID` emit(2.7).

---

### 2.7 *SET_SOLID

요소 set 정의. 8개/줄. `KooElementSet.py` `SolidElementSet` 가 자료(`self.elements` dict)만 보유 → **writer 신규 필수.**

```
*SET_SOLID
$$    SID
       100
$$    EID       EID       EID       EID       EID       EID       EID       EID
      1001      1002      1003      1004      1005      1006      1007      1008
```
매뉴얼: Vol I, 49_SET.pdf (SET_SOLID). 인프라: `SolidElementSet` 에 `WriteStreamDynaKeyword(stream)` 추가 (패턴 B), 또는 part 전체를 set으로 묶을 땐 `*SET_PART` + `*LOAD_HEAT_GENERATION_SET_SOLID`가 아닌 part 기반 카드 검토. **[추측]** part 단위 발열이면 PID 그대로 쓰는 게 단순.

---

### 2.8 *BOUNDARY_CONVECTION_SET

**Card 1a**: `SSID, PSEROD` / **Card 2**: `HLCID, HMULT, TLCID, TMULT, LOC`

| Card.필드 | 변수 | 의미 | h=10 W/m²K, T∞=85°C |
|---|---|---|---|
| 1a.1 | SSID | segment set ID | 200 |
| 1a.2 | PSEROD | 침식 상속 part set | 0 |
| 2.1 | HLCID | h 곡선(0→상수) | 0 |
| 2.2 | HMULT | h [mW/mm²K] | **0.01** (10 W/m²K) |
| 2.3 | TLCID | T∞ 곡선(0→상수) | 0 |
| 2.4 | TMULT | T∞ [°C] | **85.0** |
| 2.5 | LOC | thick shell 면 | 0 |

```
*BOUNDARY_CONVECTION_SET
$$   SSID    PSEROD
       200         0
$$  HLCID     HMULT     TLCID     TMULT       LOC
        0      0.01         0      85.0         0
```
> q''=h(T_surf−T∞). 단위환산: 1 W/m²K = 0.01 mW/mm²K (ton-mm-s).

매뉴얼: Vol I, 05_BOUNDARY.pdf p.5-30~32.
인프라: `KooDynaKeyword.py` 신규 `BoundaryConvectionSet(DynaKeyword)` (`BoundarySPCSet` 옆). **segment set(SSID)** 가 필요 — segment set emit 경로 재사용 검토. **[미확인]** 현 코드의 SEGMENT_SET emit 위치 확인 필요(robust_contact가 segment set을 다루므로 거기 재사용 가능성 높음).

---

### 2.9 *BOUNDARY_TEMPERATURE_SET / *INITIAL_TEMPERATURE_SET / *LOAD_THERMAL_VARIABLE / *LOAD_THERMAL_D3PLOT

| 카드 | 필드 | 용도 |
|---|---|---|
| `*BOUNDARY_TEMPERATURE_SET` | `NSID, TLCID, TMULT, LOC, TDEATH, TBIRTH` | 고정 표면온도 BC (T2/T3 선택) |
| `*INITIAL_TEMPERATURE_SET` | `NSID, TEMP, LOC` | 초기 온도장 (T2/T3 t=0, T4 낙하 직전 온도) |
| `*LOAD_THERMAL_VARIABLE` | C1:`NSID,NSIDEX,BOXID` C2:`TS,TB,LCID,...` | **T1 핵심** — T=TB+TS·f(t) 노드 온도. 구조 only. |
| `*LOAD_THERMAL_D3PLOT` | (필드 없음, 실행라인 `T=<rootname>`) | **T2/T3 pass2** — 선행 thermal d3plot 온도 로드. |

```
$ --- T1: 챔버 균일 온도 (25°C → 85°C 램프) ---
*LOAD_THERMAL_VARIABLE
$$   NSID    NSIDEX     BOXID
         0         0         0
$$     TS        TB      LCID
      60.0      25.0       901
$ LCID 901: (0,0)→(600,1) 램프 → T = 25 + 60·f(t)
```
매뉴얼: Vol I, 33_LOAD.pdf p.33-159~169 / 05_BOUNDARY.pdf p.5-146~147 / 28_INITIAL.pdf.
인프라:
- `*LOAD_THERMAL_VARIABLE/D3PLOT`: `KooLoad.py` 신규 (패턴 B). D3PLOT은 필드 없음 — 헤더 1줄만.
- `*INITIAL_TEMPERATURE_SET`: `KooInitial.py` `KooInitialStressSolid` 옆 신규 `KooInitialTemperatureSet` (패턴 B).
- `*BOUNDARY_TEMPERATURE_SET`: `KooDynaKeyword.py` 신규 (패턴 A).
- `*LOAD_THERMAL_D3PLOT`은 카드만으로 부족 — pass2 실행커맨드에 `T=<pass1_d3plot_rootname>` 필요. **32ieee 금지(배정밀), rootname 충돌 금지(`jobid=`)** — 실행 체인(§5)에서 처리.

---

## 3. emit 구현 매핑

> KooLoadBodyParts→LOAD_BODY_GENERALIZED_SET_PART 교체 때 쓴 결 그대로.

| 카드 | 모듈 (절대경로) | 옆 클래스 / 라인 | 신규/기존 | 패턴 |
|---|---|---|---|---|
| `*CONTROL_SOLUTION` | `occProject/Generators/KooCAEManager/KooDynaKeyword.py` | `ControlSolution` L3955 | **기존**(SOLN 세터 추가) | A |
| `*CONTROL_THERMAL_SOLVER` | 〃 | `ControlSolution` 옆 신규 | 신규 | A |
| `*CONTROL_THERMAL_TIMESTEP` | 〃 | 신규 | 신규 | A |
| `*BOUNDARY_CONVECTION_SET` | 〃 | `BoundarySPCSet` L428 옆 | 신규 | A |
| `*BOUNDARY_TEMPERATURE_SET` | 〃 | 〃 | 신규 | A |
| `*MAT_THERMAL_ISOTROPIC` | `KooCAEManager/KooMaterial.py` | `KooMaterial` L129 옆 | 신규 | B |
| `*MAT_ADD_THERMAL_EXPANSION` | 〃 | `KooMaterialAddErosion` L179 옆 | 신규 | B |
| `*LOAD_HEAT_GENERATION_SET_SOLID` | `KooCAEManager/KooLoad.py` | `KooLoadBodyParts` L123 옆 | 신규 | B |
| `*LOAD_THERMAL_VARIABLE` | 〃 | 신규 | 신규 | B |
| `*LOAD_THERMAL_D3PLOT` | 〃 | 신규(헤더만) | 신규 | B |
| `*SET_SOLID` emit | `KooCAEManager/KooElementSet.py` | `SolidElementSet` L32 | 신규 메서드 | B |
| `*INITIAL_TEMPERATURE_SET` | `KooCAEManager/KooInitial.py` | `KooInitialStressSolid` L4 옆 | 신규 | B |
| `*PART` TMID | `KooCAEManager/KooPart.py` | L1054 | **기존** | B |
| THERM mode emit | `Runner/CumulativeScenarioRunner.py` L1241 | THERM 분기 재작성 | **재작성** | — |
| thermal step builder | `Runner/StepConfigBuilder.py` | `build_vibration_load_config` L284 대칭 | 신규 `build_thermal_config` | — |
| thermal source 정규화 | `Runner/ThermalSource.py` (신규) | `VibrationSource.py` 미러 | 신규 | registry |

**패턴 A 주의(빈 필드 컬럼정렬)**: `writeParameter` 는 `parameters[ith]` 리스트를 순서대로 10컬럼씩 찍는다. SOLVER(21-30) 다음 blank(31-40) 후 GPT(41-50)처럼 중간 빈 필드가 있으면 **리스트에 `""` 원소를 명시**해야 컬럼이 맞는다(VibrationSource 결에는 이 함정이 없었으므로 신규 위험요소).

**패턴 B 주의(부동소수 포맷)**: 발열률/물성은 `">10.3e"`, CTE는 `">10.3e"`, 정수ID는 `">10"`. `KooMaterialAddErosion` 가 `NUMFIP` 같은 정수를 `">10.3e"`로 찍는 기존 결이 있으나, 신규 코드는 정수는 `">10"` 권장.

---

## 4. scenario.json 구축 방법

### 4.1 스키마 — `thermal_source` 블록 (zero-hardcode registry)

VibrationSource 의 registry+decorator+open-set discriminator 구조를 미러링.

```
thermal_source = {
  "source_type": <open-set str>,   # "uniform_chamber" | "ic_heat_steady" | "ic_heat_transient"
  "analysis_type": "steady" | "transient",   # ATYPE 매핑
  "unit_system": "SI",             # 입력 단위 (코드가 ton-mm-s로 자동 환산, §4.3)
  "materials": { <pid>: {"rho":, "hc":, "tc":, "cte":} , ... },  # SI 입력
  "heat_sources": [                # ic_heat_* 전용
     {"part": <pid>, "power_W": 3.0, "volume_mm3": 100.0,
      "profile": {"kind":"inline","points":[[0,0],[60,1],[1800,1]]} } ],
  "convection": [                  # 선택
     {"segment_set": <ssid> | "part_external": <pid>,
      "h_W_m2K": 10.0, "tinf_C": 85.0} ],
  "boundary_temperature": [ {"node_set":<nsid>, "temp_C": 85.0} ],
  "initial_temperature_C": 25.0,
  "ramp": {"target_C": 85.0, "hold_s": 1800, "ramp_s": 600}  # uniform_chamber 전용
}
```

`source_type` 별 resolver(`@register_thermal_source`)가 위 블록을 `ThermalLoadSpec`(frozen dataclass)으로 정규화. **enum 금지**(VibrationSource 채택안 D 답습) — 미등록 type 시 `Registered: [...]` 카탈로그를 에러에 포함.

### 4.2 시나리오 T1~T4 전체 예제

**T1 — 챔버 균일 온도 열응력**
```json
{
  "project": "chamber_thermal",
  "mode": "THERM",
  "model_file": "/data/.../MinimumModel.k",
  "scenario": [{
    "step": 1, "condition": "hot85",
    "thermal_source": {
      "source_type": "uniform_chamber",
      "analysis_type": "structural_only",
      "unit_system": "SI",
      "ramp": {"target_C": 85.0, "hold_s": 1800, "ramp_s": 600},
      "initial_temperature_C": 25.0,
      "materials": {
        "1": {"cte": 2.6e-6}, "2": {"cte": 14e-6}, "3": {"cte": 23.6e-6}
      }
    }
  }]
}
```

**T2 — IC 발열 정상상태 → 열응력 (2-pass)**
```json
{
  "project": "ic_steady", "mode": "THERM",
  "model_file": "/data/.../board.k",
  "scenario": [{
    "step": 1, "condition": "steady3W",
    "thermal_source": {
      "source_type": "ic_heat_steady",
      "analysis_type": "steady",
      "unit_system": "SI",
      "materials": {
        "1": {"rho":2330,"hc":700,"tc":150,"cte":2.6e-6},
        "2": {"rho":1850,"hc":1100,"tc":0.3,"cte":14e-6},
        "3": {"rho":2700,"hc":896,"tc":167,"cte":23.6e-6}
      },
      "heat_sources": [{"part":1,"power_W":3.0,"volume_mm3":100.0}],
      "convection": [{"part_external":3,"h_W_m2K":10.0,"tinf_C":85.0}],
      "initial_temperature_C": 25.0
    }
  }]
}
```

**T3 — IC 발열 과도(파워 프로파일) → 열응력**
```json
{
  "project": "ic_transient", "mode": "THERM",
  "model_file": "/data/.../board.k",
  "scenario": [{
    "step": 1, "condition": "transient3W_1800s",
    "thermal_source": {
      "source_type": "ic_heat_transient",
      "analysis_type": "transient",
      "unit_system": "SI",
      "timestep": {"its":0.5,"tmax":20.0,"dtemp":5.0},
      "materials": {
        "1": {"rho":2330,"hc":700,"tc":150,"cte":2.6e-6},
        "2": {"rho":1850,"hc":1100,"tc":0.3,"cte":14e-6}
      },
      "heat_sources": [{
        "part":1,"power_W":3.0,"volume_mm3":100.0,
        "profile":{"kind":"inline","points":[[0,0],[1,1],[1700,1],[1800,0]]}
      }],
      "convection": [{"part_external":2,"h_W_m2K":10.0,"tinf_C":85.0}],
      "initial_temperature_C": 25.0
    }
  }]
}
```

**T4 — 고온 열응력 → 낙하 (누적)**
```json
{
  "project": "thermal_drop", "mode": "THERMAL_TO_DROP",
  "model_file": "/data/.../board.k",
  "scenario": [
    {"step":1,"mode":"THERM","condition":"transient3W",
     "thermal_source": { "...": "T3와 동일" }},
    {"step":2,"mode":"DROP","condition":"corner_1m",
     "drop_attitude": {"face":"C1","height_m":1.0},
     "carry_thermal_ic": true}
  ]
}
```
> **[추측]** `carry_thermal_ic`/`THERMAL_TO_DROP` 는 dynain 재작성에 `*INITIAL_TEMPERATURE` 주입을 요구. 기존 누적 체인이 dynain 응력만 잇는지, 온도도 잇는지 P3에서 검증.

### 4.3 단위 규약 (SI 입력 → 코드 자동 환산)

사용자는 **SI로 입력**, resolver가 ton-mm-s로 환산(LENS 3 표 채택):

| 물리량 | SI 단위 | ×계수 | ton-mm-s |
|---|---|---|---|
| 밀도 ρ | kg/m³ | ×1e-12 | ton/mm³ |
| 비열 HC | J/kg·K | ×1e6 | mJ/ton·K |
| 열전도도 TC | W/m·K | ×1 | mW/mm·K (동일) |
| CTE | 1/K | ×1 | 1/K (동일) |
| 발열 q''' | W/m³ → power_W/volume_mm3 | mW/mm³ = power_W·1000/vol_mm3 | mW/mm³ |
| 대류 h | W/m²K | ×1e-3 | mW/mm²K (0.01=10) |
| 온도 | °C | (절대온도 변환은 BC가 상대값이면 불필요) | °C |

> 환산은 **resolver 한 곳**에서만(zero-hardcode). 검증 테스트에 SI→ton-mm-s 라운드트립 단위테스트 필수(`Runner/_test_vibration_load_curve_roundtrip.py` 결).

---

## 5. 실행 체인 설계

```
scenario.json
  └─ CumulativeDesigner._process_thermal_scenario()   (신규, _process_vibration_scenario 결)
       └─ ThermalSource.parse_thermal_source() → ThermalLoadSpec
            └─ save_runner_config() → runner_config.json (doe_thermals 카탈로그)
  └─ CumulativeScenarioRunner  mode=="THERM" 분기 재작성
       └─ StepConfigBuilder.build_thermal_config() → step_config.txt
            └─ KooMeshModifier 실행 → Run_<id>/ThermalSet.k + .done   ← VibrationSet 결
       └─ _find_input_file(run_dir,"THERM") → Run_<id>/ThermalSet.k (이미 매핑됨)
       └─ LS-DYNA 실행
```

**2-pass (T2/T3) 디렉토리 구조** — pass1 d3plot 온도를 pass2가 `*LOAD_THERMAL_D3PLOT T=...`로 소비:
```
Run_<id>/
  thermal/                      # pass1: SOLN=1, ATYPE
    ThermalSet.k                # MAT_THERMAL + HEAT_GEN + CONVECTION + CONTROL_THERMAL_*
    d3plot, d3plot01...         # 온도장
    .done
  structural/                   # pass2: SOLN=0
    StructuralSet.k             # MAT(구조) + MAT_ADD_THERMAL_EXPANSION + LOAD_THERMAL_D3PLOT
    실행라인: ... T=../thermal/d3plot jobid=struct
    .done
```
> **주의(매뉴얼)**: pass1 d3plot은 **배정밀(32ieee 금지)**, pass2와 d3plot rootname 충돌 금지(`jobid=`).
> **연성(SOLN=2) 대안**: 단일 패스로 thermal+structural 동시 — 2-pass보다 단순하나 비용↑. T2는 2-pass, T3 연성은 옵션. **[미확인]** SIF의 LS-DYNA 빌드가 thermal solver(SOLVER=11 직접) 지원하는지 §7 smoke test로 선검증.

**`.done` 마커**: VibrationSet 결 그대로 — KooMeshModifier가 ThermalSet.k 생성 후 `ThermalSet.k.done` 터치. Runner는 .done 폴링으로 다음 단계 진행.

---

## 6. 구현 순서 (P1/P2/P3 게이트)

### P1 — T1 (균일 온도 열응력, 구조 only)
| # | 작업 | 파일 | 검증 게이트 |
|---|---|---|---|
| 1.1 | `KooMaterialAddThermalExpansion` emit | `KooMaterial.py` | 단위 test: deck 스니펫 컬럼 == §2.5 |
| 1.2 | `LoadThermalVariable` emit | `KooLoad.py` | 단위 test: §2.9 컬럼 일치 |
| 1.3 | `ThermalSource.py` registry + `uniform_chamber` resolver | `Runner/ThermalSource.py` (신규) | SI→ton-mm-s 라운드트립 test |
| 1.4 | `build_thermal_config` | `Runner/StepConfigBuilder.py` | step_config 텍스트 골든 |
| 1.5 | THERM 분기 재작성(T1 경로) | `CumulativeScenarioRunner.py` L1241 | ThermalSet.k + .done 생성 e2e |
| **게이트 P1** | | | **bin mtime 확인 후** T1 e2e: NFS 테스트 디렉토리(`/data/koopark/Test_*`)에서 LS-DYNA 완주 + 열응력 비0 |

### P2 — T2/T3 (IC 발열 + 2-pass)
| # | 작업 | 파일 |
|---|---|---|
| 2.1 | `ControlThermalSolver` / `ControlThermalTimestep` (빈필드 컬럼 함정 주의) | `KooDynaKeyword.py` |
| 2.2 | `KooMaterialThermalIsotropic` (2장 카드) | `KooMaterial.py` |
| 2.3 | `SolidElementSet.WriteStreamDynaKeyword` + `KooLoadHeatGenerationSetSolid` | `KooElementSet.py` / `KooLoad.py` |
| 2.4 | `BoundaryConvectionSet` + segment set 경로(robust_contact 재사용 확인) | `KooDynaKeyword.py` |
| 2.5 | `InitialTemperatureSet` / `LoadThermalD3plot` | `KooInitial.py` / `KooLoad.py` |
| 2.6 | 2-pass 디렉토리 + `T=`/`jobid=` 실행라인 | `CumulativeScenarioRunner.py` |
| **게이트 P2** | | T2 steady e2e + T3 transient(1800s 축소판) e2e, pass2 온도장 로드 확인 |

### P3 — T4 (THERMAL_TO_DROP 누적)
| # | 작업 |
|---|---|
| 3.1 | dynain 온도 IC 주입 가능성 검증 (**[추측] 우선 검증**) |
| 3.2 | THERMAL_TO_DROP 모드 + carry_thermal_ic |
| **게이트 P3** | 열응력 → 낙하 누적 e2e, 응력장+온도장 연속성 확인 |

> 모든 게이트: **빌드 후 bin mtime 확인**(`build_KooChainRun_python312.sh` / KooMeshModifier 빌드), **NFS 테스트 디렉토리 강제**(`/tmp` 금지), 자가진행 금지·사용자 검사 약속 준수 (MEMORY 철칙).

---

## 7. 수동 smoke test deck (P1 착수 전 — SIF thermal solver 지원 확인)

**목적**: 자동화 착수 전, SIF 내 LS-DYNA가 thermal solver(SOLVER=11)와 SOLN=1 과도 열해석을 지원하는지 **최소 deck**으로 선검증. 한 변 1mm 단일 hex, 발열 → 온도 상승 확인.

```
*KEYWORD
*TITLE
thermal smoke - single hex transient heat-up
$
*CONTROL_SOLUTION
$$   SOLN
         1
*CONTROL_THERMAL_SOLVER
$$  ATYPE     PTYPE    SOLVER              GPT    EQHEAT     FWORK       SBC
         1         2        11                   8       1.0       1.0       0.0
*CONTROL_THERMAL_TIMESTEP
$$     TS       TIP       ITS      TMIN      TMAX     DTEMP      TSCP      LCTS
         1       1.0       0.1     0.001      10.0       5.0       0.5         0
*CONTROL_TERMINATION
$$  ENDTIM
     100.0
$
*PART
$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID
         1         1         1         0         0         0         0       101
*SECTION_SOLID
$$    SECID    ELFORM
         1         1
*MAT_RIGID
$$      MID        RO         E        PR
         1   2.33E-9   1.0E11      0.30
$$      CMO
         0
$$      
*MAT_THERMAL_ISOTROPIC
$$   TMID       TRO     TGRLC    TGMULT
       101   2.33E-9       0.0       0.0
$$     HC        TC
     7.0E8     150.0
$
*INITIAL_TEMPERATURE_SET
$$   NSID      TEMP
         0      25.0
$
*SET_SOLID
$$    SID
       100
$$    EID
         1
*LOAD_HEAT_GENERATION_SET_SOLID
$$    SID      LCID      MULT    WBLCID    CBLCID    TBLCID
       100         0      30.0         0         0         0
$
*DATABASE_TPRINT
$$       DT
       1.0
*DATABASE_BINARY_D3PLOT
$$       DT
      10.0
$
*NODE
$$    NID               X               Y               Z
         1             0.0             0.0             0.0
         2             1.0             0.0             0.0
         3             1.0             1.0             0.0
         4             0.0             1.0             0.0
         5             0.0             0.0             1.0
         6             1.0             0.0             1.0
         7             1.0             1.0             1.0
         8             0.0             1.0             1.0
*ELEMENT_SOLID
$$   EID     PID
         1         1         1         2         3         4         5         6         7         8
*END
```
> 기대: d3hsp에 "thermal" 솔버 초기화 + tprint에 온도가 25→상승. SOLVER=11이 라이선스/빌드 미지원이면 d3hsp 에러 → 자동화 진입 전 SIF/라이선스 조치 필요.
> **[미확인]**: `*INITIAL_TEMPERATURE_SET NSID=0`(전체 노드) 허용 여부는 매뉴얼 재확인 권장(일부 버전은 명시 set 요구). 미지원 시 `*INITIAL_TEMPERATURE_NODE`로 노드 8개 개별 부여.
> **[미확인]**: 발열 단독에 BC가 전무하면 무한히 데워짐(정상) — smoke test는 상승 추세만 확인하면 충분.

---

## 부록 A. 전자기기 대표 물성표 (SI → ton-mm-s, LENS 3)

| 재료 | ρ(SI) | HC(SI) | TC(SI) | CTE | ρ(t/mm³) | HC(mJ/t·K) | TC |
|---|---|---|---|---|---|---|---|
| Si 칩 | 2330 | 700 | 150 | 2.6e-6 | 2.33e-9 | 7.0e8 | 150 |
| FR4 보드 | 1850 | 1100 | 0.3(z~50e-6) | 14e-6 | 1.85e-9 | 1.1e9 | 0.3 |
| 솔더 SAC305 | 7400 | 230 | 58 | 22e-6 | 7.4e-9 | 2.3e8 | 58 |
| Al 6061 | 2700 | 896 | 167 | 23.6e-6 | 2.7e-9 | 8.96e8 | 167 |
| 구리 | 8960 | 385 | 400 | 16.5e-6 | 8.96e-9 | 3.85e8 | 400 |

## 부록 B. 미확인/추측 목록 (착수 전 해소 권장)

1. **[미확인]** SIF의 LS-DYNA가 thermal solver 지원 — §7 smoke test로 선검증 (P1 사전조건).
2. **[미확인]** segment set emit 경로 — robust_contact가 SINGLE_SURFACE용 segment set을 emit하므로 BOUNDARY_CONVECTION_SET의 SSID에 재사용 가능성 높음. 코드 위치 확인 필요.
3. **[추측]** T4 dynain 온도 IC 연속 — 기존 누적은 응력만일 수 있음. P3 선검증.
4. **[미확인]** `*INITIAL_TEMPERATURE_SET NSID=0` 전체노드 허용 여부.
5. **[미확인]** `*DEFINE_CURVE` emit 클래스 존재 여부(파워/h/T∞ 곡선용) — 기존 가정이나 grep 미확인.
6. **[주의]** 패턴 A writeParameter 빈필드 컬럼정렬 — `""` 원소 명시 필요(SOLVER↔GPT 사이 blank).
