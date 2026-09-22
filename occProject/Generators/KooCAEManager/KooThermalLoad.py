"""Thermal Load: 고온 열전달·열응력 시뮬레이션 카드 적용.

P1 (T1 — 균일 온도 열응력, 구조 only):
- 전 노드 균일 온도장 (*LOAD_THERMAL_VARIABLE, T = base + scale·f(t))
- 파트별 열팽창계수 CTE (*MAT_ADD_THERMAL_EXPANSION) → 열변형/응력
- explicit 구조해석 (implicit는 MPP_d 빌드에서 MPI_Comm_dup 결함 → 회피)
- double precision SIF 필수 (단정밀은 thermal 거부)

LS-DYNA 카드 (Vol I 33-159~169, Vol II 03_MAT):
    *DEFINE_CURVE       (온도 램프 곡선)
    *LOAD_THERMAL_VARIABLE  (전 노드 T = base + scale·곡선)
    *MAT_ADD_THERMAL_EXPANSION (파트별 CTE)

KooVibrationLoad 결 답습 — registry 소스(ThermalSource) → 이 모듈이 카드 emit.
"""


def apply_thermal_load(dynaImporter, option):
    """열하중 적용 진입 (T1 균일온도).

    Args:
        dynaImporter: KooDynaImporter
        option: dict
            - ThermalType: 'UniformChamber' (default, T1) | 'ICPower' (P2)
            - BaseTempC: 초기/기준 온도 [°C] (t=0)
            - TargetTempC: 목표 온도 [°C]
            - RampTimeS: 램프 시간 [s] (0→ramp, hold)
            - TempCurve: [[t, factor], ...] 직접 곡선 (있으면 Base/Target/Ramp 무시)
            - PartCTE: dict {pid: cte_1_K} 파트별 열팽창계수
            - DefaultCTE: 미지정 파트 기본 CTE
    """
    thermal_type = option.get("ThermalType", "UniformChamber")
    if thermal_type == "ICPower":
        # 2-pass: Phase=thermal(pass1, 온도 solve) / structural(pass2, 열응력)
        if str(option.get("Phase", "thermal")).lower() == "structural":
            _apply_ic_structural(dynaImporter, option)
        else:
            _apply_ic_power(dynaImporter, option)
        return
    if thermal_type != "UniformChamber":
        raise NotImplementedError(
            f"[THERMAL_LOAD] '{thermal_type}' 미지원 (UniformChamber=T1 / ICPower=T2·T3).")

    base_temp = float(option.get("BaseTempC", 25.0))
    target_temp = float(option.get("TargetTempC", 85.0))
    ramp_time = float(option.get("RampTimeS", 1.0e-3))  # explicit이라 짧은 시뮬

    # 온도 곡선: 직접 입력 우선, 없으면 base→target 램프
    temp_curve = option.get("TempCurve", None)
    curve_mode = str(option.get("TempCurveMode", "factor")).strip().lower()
    if temp_curve and len(temp_curve) >= 2:
        a1 = [pt[0] for pt in temp_curve]
        o1 = [pt[1] for pt in temp_curve]
        if curve_mode == "absolute":
            # 커브 종축이 ℃ 절대온도 → T = 0 + 1·f(t) 로 그대로 쓴다 (열충격 프로파일 작성이 자연스럽다)
            ts = 1.0
            tb = 0.0
        else:
            # factor(0~1) — 기존 동작. T = base + (target-base)·f(t)
            ts = target_temp - base_temp
            tb = base_temp
    else:
        # base(t=0) → target(ramp_time) 램프. factor 0→1 곡선 + ts=ΔT, tb=base
        a1 = [0.0, ramp_time]
        o1 = [0.0, 1.0]
        ts = target_temp - base_temp
        tb = base_temp

    part_cte = option.get("PartCTE", {})
    default_cte = float(option.get("DefaultCTE", 1.7e-5))  # 일반 금속 ~17e-6/K

    _mode_note = " (커브 종축=절대온도)" if (temp_curve and curve_mode == "absolute") else ""
    print(f"[THERMAL_LOAD] UniformChamber: {base_temp}°C → {target_temp}°C "
          f"(ΔT={target_temp - base_temp:.1f}, ramp={ramp_time}s){_mode_note}")

    # 1. *DEFINE_CURVE (온도 램프)
    defineMan = dynaImporter.defineManager
    new_lcid = _alloc_lcid(defineMan)
    if hasattr(defineMan, 'CreateDefineCurvewithID'):
        defineMan.CreateDefineCurvewithID(
            LCID=new_lcid, A1=a1, O1=o1, name="ThermLoad_temp_curve")
    else:
        raise RuntimeError("[THERMAL_LOAD] DefineManager.CreateDefineCurvewithID not found")
    print(f"  → *DEFINE_CURVE LCID={new_lcid} ({len(a1)} points), ts={ts:.3e}, tb={tb:.3e}")

    # 2. *LOAD_THERMAL_VARIABLE (전 노드 NSID=0, T = tb + ts·f(t))
    loadMan = dynaImporter.loadManager
    loadMan.CreateLoadThermalVariable(ts=ts, tb=tb, lcid=new_lcid, nsid=0)
    print(f"  → *LOAD_THERMAL_VARIABLE NSID=0 (전 노드), T={tb}+{ts}·f(t)")

    # 3. *MAT_ADD_THERMAL_EXPANSION (파트별 CTE)
    partMan = dynaImporter.partManager
    matMan = dynaImporter.matManager
    all_pids = list(getattr(partMan, 'parts', {}).keys())
    if not all_pids:
        raise ValueError("[THERMAL_LOAD] 파트가 없음 — 모델 로드 확인")
    for pid in all_pids:
        cte = float(part_cte.get(pid, part_cte.get(str(pid), default_cte)))
        matMan.CreateAddThermalExpansionMaterial(pid=pid, lcid=0, mult=cte)
        src = "지정" if (pid in part_cte or str(pid) in part_cte) else "default"
        print(f"  → *MAT_ADD_THERMAL_EXPANSION PID={pid}, CTE={cte:.3e} ({src})")

    # 4. 환경조건(대류·규정온도) — 지정 시에만. UniformChamber 는 전 절점 규정온도라
    #    보통 필요 없지만, 표면 대류를 함께 보고 싶을 때 쓸 수 있다.
    apply_ambient_boundary(dynaImporter, option)


def apply_ambient_boundary(dynaImporter, option):
    """환경조건(대류·규정온도) 경계조건을 외피에 적용한다 — 국부 발열과 함께 쓸 수 있다.

    국부 발열(ICPower heat_sources)만 있으면 단열체라 온도가 계속 오른다. 환경온도를 유지하려면
    외피에 대류 경계조건이 필요하고, 열충격의 표면 온도 구배도 여기서 나온다.

    option["Ambient"] = {
        "mode": "convection" | "temperature",   # 대류(h, T∞) | 규정온도
        "h": 열전달계수 [ton-mm-s 에서 mW/mm²·K],
        "temp_C": 환경온도 [℃] (상수),
        "temp_curve": [[t, T], ...]  # 있으면 시간에 따라 변하는 환경온도(열충격 프로파일)
        "pids": [pid, ...]           # 없으면 전 파트 외피
    }
    반환: 적용한 경계조건 개수 (Ambient 가 없으면 0)
    """
    amb = option.get("Ambient") or {}
    if not amb:
        return 0
    mode = str(amb.get("mode", "convection")).strip().lower()
    partMan = dynaImporter.partManager
    segMan = dynaImporter.segmentSetManager
    bndMan = dynaImporter.boundaryNodeManager
    defineMan = dynaImporter.defineManager

    pids = amb.get("pids") or list(getattr(partMan, "parts", {}).keys())
    pids = [p for p in pids if p in getattr(partMan, "parts", {})]
    if not pids:
        print("WARNING [AMBIENT]: 적용할 파트가 없다 — 건너뛴다")
        return 0

    # 환경온도 커브 (있으면) — T∞ 를 시간에 따라 바꿔 열충격 프로파일을 만든다
    tlcid = 0
    temp_curve = amb.get("temp_curve") or []
    if len(temp_curve) >= 2:
        tlcid = _alloc_lcid(defineMan)
        a1 = [float(pt[0]) for pt in temp_curve]
        o1 = [float(pt[1]) for pt in temp_curve]
        defineMan.CreateDefineCurvewithID(LCID=tlcid, A1=a1, O1=o1, name="Ambient_temp_curve")
        print(f"  → *DEFINE_CURVE LCID={tlcid} (환경온도 {len(a1)}점, {o1[0]}→{o1[-1]}℃)")

    temp_c = float(amb.get("temp_C", 25.0))
    # 🔴 TMULT(=tinf 인자)는 커브가 있을 때 '곱수'다 — 커브 종축이 절대온도이므로 1.0 을 줘야 한다.
    #    커브가 없으면 TLCID=0 이고 TMULT 가 상수 T∞ 로 쓰인다.
    tmult = 1.0 if tlcid else temp_c
    applied = 0
    for pid in pids:
        elemMan = partMan.parts[pid].elementManager
        segments = elemMan.GetExternalBoundary(True)
        if not segments:
            print(f"WARNING [AMBIENT]: PID {pid} 외피 세그먼트가 없다 — 건너뛴다")
            continue
        if mode == "temperature":
            # 규정온도는 노드 세트로 — 외피 노드 전체
            nodes = {}
            for seg in segments:
                for nid in seg:
                    nodes[nid] = nid
            nsetMan = dynaImporter.nodeSetManager
            nset = nsetMan.CreateNodeSetwithNodes(
                f"Ambient_PID{pid}", 0.0, 0.0, 0.0, 0.0, "MECH", 0,
                [partMan.parts[pid].nodeManager.nodes[nid] for nid in nodes
                 if nid in partMan.parts[pid].nodeManager.nodes])
            bndMan.CreateBoundaryTemperatureSet(nset, temp=tmult, lcid=tlcid,
                                                name=f"AmbientTemp_PID{pid}")
            print(f"  → *BOUNDARY_TEMPERATURE_SET PID={pid} ({len(nodes)} 노드, "
                  + (f"T=커브 {tlcid} x {tmult}" if tlcid else f"T={temp_c}℃") + ")")
        else:
            h = float(amb.get("h", 0.0))
            if h <= 0.0:
                print(f"WARNING [AMBIENT]: PID {pid} 대류 h 가 0 이하 — 건너뛴다 (h 를 지정할 것)")
                continue
            # solver 는 MECH — 검증된 덱(*SET_SEGMENT)이 쓰는 값이다. THERMAL 은 이 카드의 값 공간에 없다
            segSet = segMan.CreateSegmentSet(solver="MECH", name=f"Ambient_PID{pid}")
            segSet.AddSegments(segments)
            bndMan.CreateBoundaryConvectionSet(segSet, h=h, tinf=tmult, tlcid=tlcid,
                                               name=f"AmbientConv_PID{pid}")
            print(f"  → *BOUNDARY_CONVECTION_SET PID={pid} ({len(segments)} 세그먼트, h={h}, "
                  + (f"T∞=커브 {tlcid} x {tmult}" if tlcid else f"T∞={temp_c}℃") + ")")
        applied += 1
    return applied


def _apply_ic_power(dynaImporter, option):
    """T2/T3 — IC 발열 thermal pass(pass1). 검증된 thermal_smoke.k 결(transient ATYPE=1).

    pass1 은 온도장만 푼다(SOLN=1, 구조 X). 결과 d3plot 온도를 pass2(구조+LOAD_THERMAL_D3PLOT
    +CTE)가 소비한다. termination/d3plot/구조 MAT 은 T1 과 동일하게 상위 deck 조립이 담당.

    option:
        analysis_type: 'transient'(기본·검증됨) | 'steady'(heat sink 필요 — 미구현 경고)
        unit_system:   'SI'(기본) | 'tonmm'
        materials:     {pid: {rho,hc,tc,(cte)}}  SI: rho kg/m³, hc J/kg·K, tc W/m·K
        heat_sources:  [{part, power_W, volume_mm3}]  q'''=power_W·1000/vol [mW/mm³]
        initial_temperature_C: 25.0
        timestep:      {its,tmax,dtemp}  (transient)
    """
    # 단위 환산은 여기 한 곳에서만 (SI → ton-mm-s)
    SI = str(option.get("unit_system", "SI")).upper() == "SI"
    rho_f = 1.0e-12 if SI else 1.0   # kg/m³ → ton/mm³
    hc_f = 1.0e6 if SI else 1.0      # J/kg·K → mJ/ton·K
    tc_f = 1.0                       # W/m·K → mW/mm·K (동일)

    partMan = dynaImporter.partManager
    matMan = dynaImporter.matManager
    loadMan = dynaImporter.loadManager
    initMan = dynaImporter.initialManager
    ctrl = dynaImporter.controlManager
    elemMan = partMan.elementManager

    analysis = str(option.get("analysis_type", "transient")).lower()
    atype = 0 if analysis == "steady" else 1
    if atype == 0:
        print("[THERMAL_LOAD] ⚠ steady(ATYPE=0)는 heat sink(경계) 필요 — 미구현. transient 권장.")

    # 1. CONTROL — thermal solve (SOLN=1)
    ctrl.SetControlSolution(SOLN=1)
    ctrl.SetControlThermalSolver(ATYPE=atype, PTYPE=2, SOLVER=11, GPT=8)
    if atype == 1:
        ts = option.get("timestep", {}) or {}
        ctrl.SetControlThermalTimestep(
            TS=1, TIP=1.0,
            ITS=float(ts.get("its", 1.0)),
            TMAX=float(ts.get("tmax", 20.0)),
            DTEMP=float(ts.get("dtemp", 5.0)))
    print(f"[THERMAL_LOAD] ICPower pass1 (thermal, ATYPE={atype})")

    # 2. *MAT_THERMAL_ISOTROPIC (파트별) + *PART TMID
    mats = option.get("materials", {}) or {}
    parts = getattr(partMan, "parts", {})
    if not parts:
        raise ValueError("[THERMAL_LOAD] 파트가 없음 — 모델 로드 확인")
    for pid in list(parts.keys()):
        m = mats.get(pid, mats.get(str(pid), {})) or {}
        tro = float(m.get("rho", 0.0)) * rho_f
        hc = float(m.get("hc", 0.0)) * hc_f
        tc = float(m.get("tc", 0.0)) * tc_f
        matMan.CreateThermalIsotropicMaterial(tmid=pid, tro=tro, hc=hc, tc=tc)
        parts[pid].tmid = pid  # PART TMID → 열물성 참조
        print(f"  → *MAT_THERMAL_ISOTROPIC TMID={pid} (rho={tro:.3e}, hc={hc:.3e}, tc={tc:.3e})")

    # 3. *INITIAL_TEMPERATURE_SET (전 노드 NSID=0)
    init_t = float(option.get("initial_temperature_C", 25.0))
    initMan.CreateInitialTemperatureSet(nsid=0, temp=init_t)
    print(f"  → *INITIAL_TEMPERATURE_SET NSID=0 T={init_t}°C")

    # 4. heat sources — *SET_SOLID(칩 요소) + *LOAD_HEAT_GENERATION_SET_SOLID
    for hs in option.get("heat_sources", []) or []:
        pid = hs.get("part")
        power_W = float(hs.get("power_W", 0.0))
        vol = float(hs.get("volume_mm3", 0.0))
        if vol <= 0:
            raise ValueError(f"[THERMAL_LOAD] heat_source part={pid}: volume_mm3>0 필요")
        q = power_W * 1000.0 / vol   # mW/mm³
        # 파트 요소는 파트별 elementManager 에 저장됨(import 가 element.pid 를 안 채움) —
        # 기존 working 코드(KooDynaAdvancedModification 2822/4321) 와 동일하게 p.elementManager.elements 사용.
        part_obj = parts.get(pid)
        if part_obj is None:
            raise ValueError(f"[THERMAL_LOAD] heat_source part={pid}: 파트 없음")
        eids = list(getattr(part_obj.elementManager, "elements", {}).keys())
        if not eids:
            raise ValueError(f"[THERMAL_LOAD] heat_source part={pid}: solid 요소 없음")
        # SET 은 export 가 쓰는 글로벌 partManager.elementManager 에 생성(KooMeshImporter:2087)
        # solver="" → SolidSet 가 DA1 컬럼에 solver 를 쓰므로(클래스 한계), 빈 값으로 둬서
        # DA1 오염 방지(MECH 기본). 검증 smoke 도 plain SET_SOLID(MECH)로 통과.
        sset = elemMan.CreateSolidSet(name=f"HeatGen_PID{pid}", solver="", elemList=eids)
        loadMan.CreateLoadHeatGenerationSetSolid(sid=sset.sid, lcid=0, mult=q)
        print(f"  → *SET_SOLID(sid={sset.sid}, {len(eids)} elems) + "
              f"*LOAD_HEAT_GENERATION q'''={q:.3e} mW/mm³ (PID={pid}, {power_W}W/{vol}mm³)")

    # 5. 환경조건(대류·규정온도) — 국부 발열과 함께 걸 수 있다. 없으면 무동작
    apply_ambient_boundary(dynaImporter, option)


def _apply_ic_structural(dynaImporter, option):
    """T2/T3 pass2 — 구조 해석(SOLN=0 explicit): 선행 thermal d3plot 온도 + CTE → 열응력.

    온도장은 *LOAD_THERMAL_D3PLOT 로 읽는다(파일 경로는 LS-DYNA 실행라인 T= 로 지정 — F2).
    CTE 는 materials[pid].cte 우선, 없으면 PartCTE/DefaultCTE (T1 결).
    SOLN/termination/database/구조 MAT 은 T1 과 동일하게 상위 deck 조립이 담당.
    """
    SI = str(option.get("unit_system", "SI")).upper() == "SI"  # CTE 는 ×1 (SI=tonmm 동일)
    mats = option.get("materials", {}) or {}
    part_cte = option.get("PartCTE", {}) or {}
    default_cte = float(option.get("DefaultCTE", 1.7e-5))

    partMan = dynaImporter.partManager
    matMan = dynaImporter.matManager
    loadMan = dynaImporter.loadManager
    parts = getattr(partMan, "parts", {})
    if not parts:
        raise ValueError("[THERMAL_LOAD] 파트가 없음 — 모델 로드 확인")

    # 1. *MAT_ADD_THERMAL_EXPANSION (파트별 CTE) — 열응력의 근원
    for pid in list(parts.keys()):
        m = mats.get(pid, mats.get(str(pid), {})) or {}
        cte = m.get("cte", part_cte.get(pid, part_cte.get(str(pid), default_cte)))
        cte = float(cte)
        matMan.CreateAddThermalExpansionMaterial(pid=pid, lcid=0, mult=cte)
        print(f"  → *MAT_ADD_THERMAL_EXPANSION PID={pid}, CTE={cte:.3e}")

    # 2. *LOAD_THERMAL_D3PLOT (선행 thermal d3plot 온도 로드; 파일은 실행라인 T= 로 지정)
    loadMan.CreateLoadThermalD3plot()
    print("[THERMAL_LOAD] ICPower pass2 (structural): CTE + LOAD_THERMAL_D3PLOT (온도←pass1 d3plot)")


# ============================================================================
# helpers
# ============================================================================
def _alloc_lcid(defineMan):
    """기존 LCID 중 max + 1."""
    existing = list(getattr(defineMan, 'defines', {}).keys())
    return (max(existing) + 1) if existing else 1
