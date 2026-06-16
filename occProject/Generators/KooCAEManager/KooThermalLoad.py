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
    if thermal_type != "UniformChamber":
        raise NotImplementedError(
            f"[THERMAL_LOAD] P1은 UniformChamber만 지원. '{thermal_type}'는 P2 (IC 발열)에서.")

    base_temp = float(option.get("BaseTempC", 25.0))
    target_temp = float(option.get("TargetTempC", 85.0))
    ramp_time = float(option.get("RampTimeS", 1.0e-3))  # explicit이라 짧은 시뮬

    # 온도 곡선: 직접 입력 우선, 없으면 base→target 램프
    temp_curve = option.get("TempCurve", None)
    if temp_curve and len(temp_curve) >= 2:
        a1 = [pt[0] for pt in temp_curve]
        o1 = [pt[1] for pt in temp_curve]
        # 곡선이 factor(0~1)면 base/target로 ts/tb 환산, 절대온도면 그대로
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

    print(f"[THERMAL_LOAD] UniformChamber: {base_temp}°C → {target_temp}°C "
          f"(ΔT={ts:.1f}, ramp={ramp_time}s)")

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


# ============================================================================
# helpers
# ============================================================================
def _alloc_lcid(defineMan):
    """기존 LCID 중 max + 1."""
    existing = list(getattr(defineMan, 'defines', {}).keys())
    return (max(existing) + 1) if existing else 1
