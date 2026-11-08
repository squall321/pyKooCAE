#!/usr/bin/env python3
# 이어서 하는 해석(누적 낙하·누적 충격) 2단계 체인의 덱 수준 판정 — 앞 단계 장치가 다음 단계에 남거나 깨지지 않는지 본다
"""누적 체인 결함 묶음(2026-11-08, docs/kmm_cumulative_chain_20261108).

  C1 낙하(바닥 = 강체벽) 누적 — KMM 이 쓴 *RIGIDWALL_PLANAR_MOVING_FORCES_ID 를 다시 읽으면 카드가 한 장 밀렸고, DTI 에 강체벽
     지우기가 없어 앞 단계 바닥 벽이 다음 단계로 갔다.
  C2 충격 누적 — 다음 단계 DTI 가 충격체와 그 접촉만 지웠다. 받침 벽·앞·가운데 단·벽 처방 운동·초기 속도가 남았다.
  C3 IncludeWallInGeneral 누적 — 첫 낙하가 만든 「모든 파트」 묶음에 지워진 바닥판 번호가 남고 새 바닥판은 없었다.
  S1 OutsideRigid* 충격 덱에 *INTERFACE_SPRINGBACK_LSDYNA 가 없어 dynain 이 나오지 않았다.
  S2 시편을 바꾼 충격(바깥을 잘라 냄·강체로 바꿈)은 이어서 하지 않는다 — DTI 가 알아보게 멈춘다(사용자 결정 11-08).

LS-DYNA 없이 판정한다 — dynain 은 앞 단계 모델 절점을 조금 옮기고 초기 응력 카드를 단 것으로 대신한다.
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def blocks_like(text, prefix):
    """머리 줄이 prefix 로 시작하는 키워드 블록마다 (키워드, 데이터 줄 — 주석·빈 줄 뺌)."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = None
            if ln.split()[0].upper().startswith(prefix):
                cur = []
                out.append((ln.split()[0].upper(), cur))
            continue
        if cur is not None and ln.strip() and not ln.startswith("$"):
            cur.append(ln)
    return out


def walls(t):
    """출력 강체벽 [(키워드, 번호 또는 None, (XT, YT, ZT, XH, YH, ZH))] — 덱 차례대로."""
    out = []
    for kw, rows in blocks_like(t, "*RIGIDWALL"):
        off = 1 if kw.endswith("_ID") else 0
        rid = R.try_(lambda: int(rows[0][:10]), -1) if off else None
        c = R.try_(lambda: R.floats(rows[off + 1], 10)[:6], None)
        out.append((kw, rid, tuple(round(x, 6) for x in c) if c and len(c) == 6 else None))
    return out


def normal(c):
    v = (c[3] - c[0], c[4] - c[1], c[5] - c[2])
    n = sum(x * x for x in v) ** 0.5
    return tuple(round(x / n, 4) for x in v) if n > 0 else None


def first_ints(t, prefix, skip_id_card=True):
    """prefix 키워드 블록마다 첫 데이터 카드의 첫 칸(_ID 꼴은 ID 카드 다음 카드)."""
    out = []
    for kw, rows in blocks_like(t, prefix):
        k = 1 if (skip_id_card and kw.endswith("_ID") and len(rows) > 1) else 0
        out.append(R.try_(lambda: int(float(rows[k][:10])), -1))
    return out


def set_parts(t):
    """*SET_PART_LIST(_TITLE) → {SID: [PID…]}."""
    out = {}
    for kw, rows in blocks_like(t, "*SET_PART_LIST"):
        k = 1 if kw.endswith("_TITLE") else 0
        if len(rows) <= k:
            continue
        sid = R.try_(lambda: int(rows[k][:10]), -1)
        out[sid] = [p for r in rows[k + 1:] for p in R.try_(lambda: R.ints(r, 10), []) if p]
    return out


def generals(t):
    """*CONTACT_AUTOMATIC_GENERAL(_ID)·SINGLE_SURFACE(_ID) → [(CID, SSID, SSTYP)] — DROP 은 기본으로 GENERAL 을 SINGLE_SURFACE 로 바꾼다."""
    out = []
    for kw, rows in blocks_like(t, "*CONTACT_AUTOMATIC_GENERAL") + blocks_like(t, "*CONTACT_AUTOMATIC_SINGLE_SURFACE"):
        k = 1 if kw.endswith("_ID") else 0
        cid = R.try_(lambda: int(rows[0][:10]), -1) if k else 0
        f = R.try_(lambda: R.ints(rows[k][:40], 10), [])
        out.append((cid, f[0] if f else None, f[2] if len(f) > 2 else None))
    return out


def dynain_of(model_text, kind="solid"):
    """앞 단계 결과를 대신하는 dynain — 모델 절점을 0.01 올리고 초기 응력 카드 하나."""
    p = {k: (x, y, z + 0.01) for k, (x, y, z) in R.nodes(model_text).items()}
    st = ("*INITIAL_STRESS_SOLID\n" + f10(1, 1, 0, 0, 0, 0, 0, 0) + f10(11.0, 12.0, 13.0, 1.0, 2.0, 3.0, 0.01)) if kind == "solid" else \
         ("*INITIAL_STRESS_SHELL\n" + f10(1, 1, 3, 0, 0, 0, 0, 0)
          + "".join(f10(z, 21.0, 22.0, 0.0, 2.1, 0.0, 0.0, 0.02) for z in (-0.7746, 0.0, 0.7746)))
    return "*KEYWORD\n" + R.node_block(p) + st + "*END\n"


def dti(name, deck_name, deck, dti_txt, dynain):
    """앞 단계가 적은 dynaintoinitial.txt 로 DTI 를 돌린다(dynain 자리만 바꾼다) → (폴더, rc, 로그, _dti.k)."""
    opt = "\n".join("**DynainPath,dynain" if ln.startswith("**DynainPath") else ln for ln in dti_txt.splitlines()) + "\n"
    d, rc, log = R.run(name, {deck_name: deck, "dynain": dynain}, opt)
    return d, rc, log, R.read(d, deck_name[:-2] + "_dti.k")


def runs_of(d, deck_name):
    """RunDirectoryMode 산출 [(Run 폴더, 덱, dynaintoinitial.txt)]."""
    out = []
    for r in sorted(Path(d).glob("runs/Run_*")):
        if (r / deck_name).exists():
            out.append((r, R.read(r, deck_name), R.read(r / "DynamicRelaxation", "dynaintoinitial.txt")))
    return out


def directive(dti_txt, key):
    """dynaintoinitial.txt 의 *key 줄 값 목록(없으면 None)."""
    for ln in dti_txt.splitlines():
        if ln.lower().startswith("*" + key.lower() + ","):
            return [x.strip() for x in ln.split(",")[1:] if x.strip()]
    return None


# ── C1 낙하(바닥 = 강체벽) ────────────────────────────────────────────────────────────────────────────────────
def c1():
    print("[C1] 낙하(바닥 = 강체벽) 2단계 — 앞 단계 바닥 벽이 다음 단계에 남지 않고, 새 바닥 벽 하나가 바르게 읽힌다")
    model = R.cube_deck()
    dyn = dynain_of(model)
    d1, rc1, log1 = R.run("c1_s1", {"model.k": model}, R.drop([0], "DropSurface,RigidWall\n"))
    rs = runs_of(d1, "DropSet.k")
    deck1, dti1 = (rs[0][1], rs[0][2]) if rs else ("", "")
    w1 = walls(deck1)
    check("C1 1단계: DropSet.k 에 바닥 강체벽 하나(번호 있음)", rc1 == 0 and len(w1) == 1 and (w1[0][1] or 0) > 0, f"rc={rc1} {w1}")
    rm = directive(dti1, "RemoveRigidWallbyID")
    check("C1 1단계: dynaintoinitial.txt 가 그 바닥 벽 번호를 *RemoveRigidWallbyID 로 적는다",
          bool(w1) and rm == [str(w1[0][1])], f"{rm} walls={w1}")
    d2, rc2, log2, t2 = dti("c1_dti", "DropSet.k", deck1, dti1, dyn)
    check("C1 DTI: rc 0, _dti.k 에 1단계 바닥 강체벽이 없다", rc2 == 0 and bool(t2) and walls(t2) == [], f"rc={rc2} {walls(t2)} " + log2[-300:])
    check("C1 DTI: dynain 응력(*INITIAL_STRESS_SOLID)이 이어진다", "*INITIAL_STRESS_SOLID" in t2.upper(), "")
    # 2단계 — _dti.k 를 입력으로 다시 낙하(롤 30°). 기준: 같은 각도로 처음 모델을 떨어뜨린 바닥 벽의 법선
    d3, rc3, log3 = R.run("c1_s2", {"model.k": t2}, R.drop([30], "DropSurface,RigidWall\n"))
    rs3 = runs_of(d3, "DropSet.k")
    w3 = walls(rs3[0][1]) if rs3 else []
    dr, rcr, logr = R.run("c1_ref", {"model.k": model}, R.drop([30], "DropSurface,RigidWall\n"))
    rsr = runs_of(dr, "DropSet.k")
    wr = walls(rsr[0][1]) if rsr else []
    ok = (rc3 == 0 and len(w3) == 1 and w3[0][2] is not None and bool(wr) and wr[0][2] is not None
          and normal(w3[0][2]) == normal(wr[0][2]))
    check("C1 2단계: DropSet.k 의 강체벽은 하나(2단계 바닥)이고 법선이 같은 각도 단일 낙하와 같다", ok, f"rc={rc3} {w3} ref={wr}")


def c1_fast():
    print("[C1] 여러 각도(Fast) 낙하 + RigidWall — 각도마다 제 바닥 벽 번호를 적는다")
    model = R.cube_deck()
    d, rc, log = R.run("c1f_s1", {"model.k": model}, R.drop([0, 30], "DropSurface,RigidWall\n"))
    rs = runs_of(d, "DropSet.k")
    got = [(walls(deck), directive(txt, "RemoveRigidWallbyID")) for _, deck, txt in rs]
    ok = rc == 0 and len(got) == 2 and all(len(w) == 1 and rm == [str(w[0][1])] for w, rm in got)
    check("C1 Fast 2각도: Run 마다 바닥 벽 하나, dynaintoinitial.txt 의 *RemoveRigidWallbyID 가 그 벽 번호", ok, f"rc={rc} {got}")
    for i, (_, deck, txt) in enumerate(rs):
        dd, rc2, log2, t2 = dti(f"c1f_dti{i}", "DropSet.k", deck, txt, dynain_of(model))
        check(f"C1 Fast 각도 {i + 1} DTI: _dti.k 에 바닥 강체벽이 없다", rc2 == 0 and bool(t2) and walls(t2) == [], f"rc={rc2} {walls(t2)}")


# ── C3 IncludeWallInGeneral ─────────────────────────────────────────────────────────────────────────────────────
def c3():
    print("[C3] 바닥판을 전체 접촉에 넣는 설정(IncludeWallInGeneral) 2단계 — 둘째 낙하의 바닥판도 전체 접촉 범위에 든다")
    model = R.cube_deck()
    d1, rc1, log1 = R.run("c3_s1", {"model.k": model}, R.drop([0], "IncludeWallInGeneral,True\n"))
    rs = runs_of(d1, "DropSet.k")
    deck1, dti1 = (rs[0][1], rs[0][2]) if rs else ("", "")
    plate1 = sorted(set(R.part_cards(deck1)) - set(R.part_cards(model)))
    g1, s1 = generals(deck1), set_parts(deck1)
    in1 = [g for g in g1 if g[2] == 2 and plate1 and plate1[0] in s1.get(g[1], [])]
    check("C3 1단계: 바닥판 파트가 전체 접촉(파트 묶음) 범위에 든다", rc1 == 0 and len(plate1) == 1 and len(in1) == 1, f"rc={rc1} plate={plate1} {g1} {s1}")
    d2, rc2, log2, t2 = dti("c3_dti", "DropSet.k", deck1, dti1, dynain_of(model))
    s2 = set_parts(t2)
    stale = {sid: p for sid, p in s2.items() if plate1 and plate1[0] in p}
    check("C3 DTI: 지운 바닥판 번호가 파트 묶음에 남지 않는다", rc2 == 0 and bool(t2) and plate1 != [] and not stale, f"rc={rc2} {s2}")
    d3, rc3, log3 = R.run("c3_s2", {"model.k": t2}, R.drop([30], "IncludeWallInGeneral,True\n"))
    rs3 = runs_of(d3, "DropSet.k")
    deck3 = rs3[0][1] if rs3 else ""
    plate3 = sorted(set(R.part_cards(deck3)) - set(R.part_cards(t2)))
    g3, s3 = generals(deck3), set_parts(deck3)
    covered = [g for g in g3 if (g[2] == 2 and plate3 and plate3[0] in s3.get(g[1], [])) or g[2] == 5]
    check("C3 2단계: 새 바닥판이 전체 접촉 범위에 든다", rc3 == 0 and len(plate3) == 1 and len(covered) >= 1, f"rc={rc3} plate={plate3} {g3} {s3}")
    # 한 단계 — 모델에 GENERAL(모든 파트 묶음)이 처음부터 있으면 DROP 이 그것을 SINGLE_SURFACE 로 바꾼다. 바닥판이 그 범위에 들어야 한다
    gen = ("*SET_PART_LIST\n" + f10(9) + f10(1) + "*CONTACT_AUTOMATIC_GENERAL_ID\n" + f"{5:10d}usergen\n" + f10(9, 0, 2, 0)
           + f10(0.2, 0.1) + f10(1.0, 1.0))
    d4, rc4, log4 = R.run("c3_usergen", {"model.k": R.cube_deck(gen)}, R.drop([0], "IncludeWallInGeneral,True\n"))
    rs4 = runs_of(d4, "DropSet.k")
    deck4 = rs4[0][1] if rs4 else ""
    plate4 = sorted(set(R.part_cards(deck4)) - {1})
    g4, s4 = generals(deck4), set_parts(deck4)
    cov4 = [g for g in g4 if (g[2] == 2 and plate4 and plate4[0] in s4.get(g[1], [])) or g[2] == 5]
    check("C3 한 단계(모델에 GENERAL): 바닥판이 바뀐 접촉 범위에 든다", rc4 == 0 and len(plate4) == 1 and len(cov4) >= 1,
          f"rc={rc4} plate={plate4} {g4} {s4} " + log4[-300:])


# ── C2·S1·S2 충격 ───────────────────────────────────────────────────────────────────────────────────────────
GRID = {i * 4 + j + 1: (float(j), float(i), 0.0) for i in range(4) for j in range(4)}
QUADS = "".join(f"{3 * i + j + 1:8d}{1:8d}" + "".join(f"{n:8d}" for n in (4 * i + j + 1, 4 * i + j + 2, 4 * i + j + 6, 4 * i + j + 5)) + "\n"
                for i in range(3) for j in range(3))
PLATE = ("*KEYWORD\n*CONTROL_TERMINATION\n" + f10(0.001) + R.node_block(GRID) + "*ELEMENT_SHELL\n" + QUADS + R.part(1, 1, 1, "plate")
         + "*SECTION_SHELL\n" + f10(1, 2) + f10(0.5, 0.5, 0.5, 0.5) + "*MAT_ELASTIC\n" + f10(1, "2.70E-09", 70000, 0.33) + "*END\n")
IMPS = (("sphere", "ImpactorType,Sphere\nImpactorDimension,0.5\n"),
        ("cyl3", "ImpactorType,Cylinder\nImpactorDimension,0.3,0.4,0.2,0.35,0.2,0.4,0.2\n"))


def dwi_opt(mode, imp, extra=""):
    return ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,runs\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.0001\n"
            "DT,1e-05\nLocationX,1.5\nLocationY,1.5\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\n"
            + imp + "MeshSize,0.25\nDensityImpactor,7.85e-09\nYoungsModulusImpactor,200000.0\nPoissonRatioImpactor,0.3\n"
            f"GenerationMode,{mode}\n{extra}OffsetDistance,0.05\nYoungsModulusWall,10000.0\nPoissonRatioWall,0.3\nDensityWall,1e-09\n"
            "**EndDropWeightImpactTest\n*End\n")


def apparatus(t, spec_pids):
    """시편 밖 장치 — 파트·처방 운동 RIGID·초기 속도 GENERATION·SPC 세트 수."""
    return {"parts": sorted(set(R.part_cards(t)) - set(spec_pids)),
            "pm_rigid": len(blocks_like(t, "*BOUNDARY_PRESCRIBED_MOTION_RIGID")),
            "ivg": len(blocks_like(t, "*INITIAL_VELOCITY_GENERATION")),
            "spc_set": len(blocks_like(t, "*BOUNDARY_SPC_SET"))}


def c2():
    print("[C2] 충격 2단계 — 다음 단계에 앞 단계 충격 장치(충격체·받침 벽·앞·가운데 단·처방 운동·초기 속도·접촉)가 남지 않는다")
    for mode in ("DampingSpring", "OutsideRigidElement"):
        for name, imp in IMPS:
            d1, rc1, log1 = R.run(f"c2_{mode}_{name}", {"model.k": PLATE}, dwi_opt(mode, imp))
            rs = runs_of(d1, "DropWeightImpactTestSet.k")
            deck1, dti1 = (rs[0][1], rs[0][2]) if rs else ("", "")
            a1 = apparatus(deck1, [1])
            check(f"C2 {mode}·{name} 1단계: 장치가 있다(파트·처방 운동·초기 속도)",
                  rc1 == 0 and len(a1["parts"]) >= 2 and a1["pm_rigid"] >= 1 and a1["ivg"] >= 1, f"rc={rc1} {a1} " + log1[-300:])
            d2, rc2, log2, t2 = dti(f"c2_{mode}_{name}_dti", "DropWeightImpactTestSet.k", deck1, dti1, dynain_of(PLATE, "shell"))
            a2 = apparatus(t2, [1])
            check(f"C2 {mode}·{name} DTI: 장치가 하나도 남지 않고 시편 파트 1 만 남는다",
                  rc2 == 0 and bool(t2) and a2 == {"parts": [], "pm_rigid": 0, "ivg": 0, "spc_set": 0} and 1 in R.part_cards(t2),
                  f"rc={rc2} {a2} " + log2[-300:])
            left = R.cons_of(t2)
            check(f"C2 {mode}·{name} DTI: 접촉이 남지 않는다(DWI 가 만든 접촉뿐인 덱)", rc2 == 0 and left == [], f"{left}")
            check(f"C2 {mode}·{name} DTI: dynain 응력(*INITIAL_STRESS_SHELL)이 이어진다", "*INITIAL_STRESS_SHELL" in t2.upper(), "")
            if name == "sphere":
                d3, rc3, log3 = R.run(f"c2_{mode}_s2", {"model.k": t2}, dwi_opt(mode, imp))
                rs3 = runs_of(d3, "DropWeightImpactTestSet.k")
                a3 = apparatus(rs3[0][1], [1]) if rs3 else {}
                check(f"C2 {mode}·{name} 2단계: 장치는 1단계와 같은 수(한 벌)", rc3 == 0 and a3 and len(a3["parts"]) == len(a1["parts"])
                      and a3["pm_rigid"] == a1["pm_rigid"] and a3["ivg"] == a1["ivg"], f"rc={rc3} {a3} 1단계={a1}")


def s1():
    print("[S1] 충격 덱에 dynain 요청 카드(*INTERFACE_SPRINGBACK_LSDYNA) — 모든 생성 방식")
    for mode in ("DampingSpring", "OutsideRigidElement", "OutsideRigidPart"):
        d, rc, log = R.run(f"s1_{mode}", {"model.k": PLATE}, dwi_opt(mode, IMPS[0][1]))
        rs = runs_of(d, "DropWeightImpactTestSet.k")
        deck = rs[0][1] if rs else ""
        check(f"S1 {mode}: 충격 덱에 *INTERFACE_SPRINGBACK_LSDYNA 가 있다", rc == 0 and "*INTERFACE_SPRINGBACK_LSDYNA" in deck.upper(), f"rc={rc}")


def s2():
    print("[S2] 시편을 바꾼 충격(바깥을 잘라 냄·강체로 바꿈)은 이어서 하지 않는다 — DTI 가 rc 1 로 멈추고 까닭을 알린다")
    for mode, extra in (("DampingSpring", "BoundaryDistance,0.6\n"), ("OutsideRigidElement", "BoundaryDistance,0.6\n"),
                        ("OutsideRigidPart", "BoundaryDistance,0.6\n"),
                        ("DampingSpring", "StressWaveVelocity,5000\nDistanceMargin,1.2\n")):
        tag = mode + ("_auto" if "StressWave" in extra else "")
        d1, rc1, log1 = R.run(f"s2_{tag}", {"model.k": PLATE}, dwi_opt(mode, IMPS[0][1], extra))
        rs = runs_of(d1, "DropWeightImpactTestSet.k")
        deck1, dti1 = (rs[0][1], rs[0][2]) if rs else ("", "")
        check(f"S2 {tag} 1단계: 충격 덱은 그대로 만든다(이어서 하지 않는 충격은 막지 않는다)", rc1 == 0 and bool(deck1), f"rc={rc1} " + log1[-300:])
        d2, rc2, log2, t2 = dti(f"s2_{tag}_dti", "DropWeightImpactTestSet.k", deck1, dti1, dynain_of(PLATE, "shell"))
        check(f"S2 {tag} DTI: rc 1, _dti.k 없음, 까닭(시편)을 알린다", rc2 == 1 and not t2 and "시편" in log2, f"rc={rc2} " + log2[-300:])


if __name__ == "__main__":
    for f in (c1, c1_fast, c3, c2, s1, s2):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:400])
    sys.exit(1 if FAILS else 0)
