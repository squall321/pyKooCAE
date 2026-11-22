#!/usr/bin/env python3
# 남은 결함 묶음 U10 판정 — 탐침에서 찾은 것(하이픈 키워드 이름 잘림, DWI 재사용 재질의 앞부분)을 작은 덱으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) (라) 탐침 줄.

  [H]   이름에 하이픈이 든 키워드(*MAT_MOONEY-RIVLIN_RUBBER(_TITLE)·*ALE_MULTI-MATERIAL_GROUP·*MAT_3-PARAMETER_BARLAT·
        *SET_MULTI-MATERIAL_GROUP_LIST)가 *MAT_MOONEY·*ALE_MULTI 처럼 잘린 이름으로 출력됐다(rc 0, 실제 덱 145개) → 이름 그대로
  [820] DWI 에서 MaterialIDImpactor 로 덱 재질을 쓰고 앞부분 재질 키가 없으면 앞부분이 단위계 표 값이 됐다 → 그 재질의 E·ρ
  [43⑤] DROP_ATTITUDE 가 원문 *_INERTIA 몸체의 무게중심·관성 텐서를 자세에 맞춰 옮기지 않으면서 알리지 않았다 → ⚠️ 알림
  [43⑥] VIBRATION_LOAD 부피·질량이 TETRA10(·HEXA20) 파트에서 0 이었다 → 꼭짓점으로 잰다

실행: venv312/bin/python tests/test_remaining_probes.py (KMM 몇 번, 1분 안)
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


def hyphen():
    print("[H] 하이픈 키워드 이름")
    mr = "*MAT_MOONEY-RIVLIN_RUBBER_TITLE\nrubber\n" + f10(1, "1.1E-09", 0.499, 0.5, 0.1) + f10(0.0, 0.0, 0.0, 0.0)
    extra = ("*ALE_MULTI-MATERIAL_GROUP\n" + f10(1, 1) + "*SET_MULTI-MATERIAL_GROUP_LIST\n" + f10(1) + f10(1)
             + "*MAT_3-PARAMETER_BARLAT\n" + f10(9, "7.85E-09", 210000.0, 0.3, 3) + f10(0.0) * 1 + "\n" * 3)
    deck = ("*KEYWORD\n" + R.node_block(R.cubes(1)) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.part(1) + R.SOLID1 + mr + extra
            + "*END\n")
    d, rc, log = R.run("pr_hyphen", {"model.k": deck})
    kws = [ln.split()[0].upper() for ln in R.read(d, "model_trans.k").splitlines() if ln.startswith("*")]
    want = ["*MAT_MOONEY-RIVLIN_RUBBER_TITLE", "*ALE_MULTI-MATERIAL_GROUP", "*SET_MULTI-MATERIAL_GROUP_LIST", "*MAT_3-PARAMETER_BARLAT"]
    cut = [k for k in kws if k in ("*MAT_MOONEY", "*ALE_MULTI", "*SET_MULTI", "*MAT_3")]
    check("[H] rc 0, 네 키워드 이름이 출력에 그대로(잘린 *MAT_MOONEY·*ALE_MULTI·*SET_MULTI·*MAT_3 없음)",
          rc == 0 and all(w in kws for w in want) and not cut, f"rc={rc} {kws} " + log[-300:])
    t = R.read(d, "model_trans.k")
    i = t.find("*MAT_MOONEY-RIVLIN_RUBBER_TITLE")
    body = t[i:].split("\n*", 1)[0].splitlines()[1:] if i >= 0 else []
    check("[H] 무니-리블린 블록의 제목·카드가 덱 그대로", [b.rstrip() for b in body if not b.startswith("$")][:3]
          == ["rubber", f10(1, "1.1E-09", 0.499, 0.5, 0.1).rstrip(), f10(0.0, 0.0, 0.0, 0.0).rstrip()], str(body[:4]))


def model():
    """1×1×2 블록(육면체 2개, mm) — 재질 1: ρ 7.85E-09, E 210000."""
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{x:16.6e}{y:16.6e}{z:16.6e}")
    return ("*KEYWORD\n*NODE\n" + "\n".join(out) + "\n*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*ELEMENT_SOLID\n"
            + "".join(f"{k:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * k - 3, 4 * k + 5)) + "\n" for k in (1, 2))
            + "*END\n")


def mat(text, title):
    """*MAT_ELASTIC_TITLE 제목이 title 인 블록의 (RO, E)."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper() == "*MAT_ELASTIC_TITLE" and i + 1 < len(lines) and lines[i + 1].strip() == title:
            for k in range(i + 2, len(lines)):
                if lines[k].startswith("*"):
                    break
                if not lines[k].startswith("$"):
                    v = [float(x) for x in lines[k].split()]
                    return v[1], v[2]
    return None


def dwi_reuse():
    print("[820] DWI MaterialIDImpactor 재사용 — 앞부분 재질")
    opt = ("*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.001\nDT,1e-06\nLocationX,0.5\n"
           "LocationY,0.5\nHeight,10\nGravity,9810.0\nImpactorType,cylinder\nImpactorDimension,0.3,0.4,0.2,0.4,0.4\nMeshSize,0.1\n"
           "MaterialIDImpactor,1\nGenerationMode,DampingSpring\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\nPoissonRatioWall,0.3\n"
           "DensityWall,1e-09\n**EndDropWeightImpactTest\n*End\n")
    d, rc, log = R.run("pr_dwi_reuse", {"model.k": model()}, opt)
    m = mat(R.read(d, "model_dwit.k"), "ImpactorFrontMaterial")
    check("[820] rc 0, 앞부분 재질 = 재사용한 재질 1 의 ρ 7.85E-09·E 210000(단위계 표 7.8e-9·2.07e5 아님)",
          rc == 0 and m is not None and R.near(m[0], 7.85e-9) and R.near(m[1], 210000.0), f"rc={rc} {m} " + log[-300:])
    # 값을 해석하지 않는 재질(번호 꼴 *MAT_001)은 GetE·GetRho 가 0.0 — 물려받으면 앞부분이 E·ρ 0 이 된다 → 단위계 표 값 그대로
    d, rc, log = R.run("pr_dwi_reuse_raw", {"model.k": model().replace("*MAT_ELASTIC\n", "*MAT_001\n")}, opt)
    m = mat(R.read(d, "model_dwit.k"), "ImpactorFrontMaterial")
    check("[820] 번호 꼴 *MAT_001 재사용 — rc 0, 앞부분 재질 = 단위계 표 ρ 7.8e-9·E 2.07e5(0 아님)",
          rc == 0 and m is not None and R.near(m[0], 7.8e-9) and R.near(m[1], 2.07e5), f"rc={rc} {m} " + log[-300:])


def inertia_notice():
    print("[43⑤] DROP_ATTITUDE — 원문 *_INERTIA 몸체 알림")
    cnrb = ("*SET_NODE_LIST\n" + f10(11) + f10(1, 2, 3, 4) + "*CONSTRAINED_NODAL_RIGID_BODY_INERTIA\n" + f10(50, 0, 11)
            + f10(0.5, 0.5, 0.0, "1.0E-3", 0) + f10(1.0, 0.0, 0.0, 1.0, 0.0, 1.0) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    d, rc, log = R.run("pr_inertia", {"model.k": R.cube_deck(cnrb)}, R.drop([0]))
    check("[43⑤] rc 0, ⚠️ *CONSTRAINED_NODAL_RIGID_BODY_INERTIA 무게중심·텐서 알림", rc == 0 and "무게중심(XC·YC·ZC)" in log
          and "*CONSTRAINED_NODAL_RIGID_BODY_INERTIA" in log, f"rc={rc} " + log[-300:])


def vib_tet10():
    print("[43⑥] VIBRATION_LOAD — TETRA10 파트 부피")
    corners = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0), 4: (0.0, 0.0, 1.0)}
    mids = [(1, 2), (2, 3), (1, 3), (1, 4), (2, 4), (3, 4)]
    pts = dict(corners)
    for k, (a, b) in enumerate(mids):
        pts[5 + k] = tuple((corners[a][i] + corners[b][i]) / 2 for i in range(3))
    deck = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID (ten nodes format)\n" + f"{1:8d}{1:8d}\n"
            + "".join(f"{n:8d}" for n in range(1, 11)) + "\n" + R.part(1) + "*SECTION_SOLID\n" + f10(1, 16) + R.ELASTIC + "*END\n")
    opt = ("*Inputfile\nmodel.k\n*Mode\nVIBRATION_LOAD,1\n**VibrationLoad,1\nDirection,Z\nLoadType,Force\nRelativeMode,Explicit\n"
           "LoadCurve\n0.0, 0.0\n0.001, 100.0\nEndLoadCurve\nPartFactors\n1, 1.0\nEndPartFactors\n**EndVibrationLoad\n*End\n")
    d, rc, log = R.run("pr_vib_tet10", {"model.k": deck}, opt)
    import re
    m = re.search(r"PID 1: volume=([0-9.eE+-]+)", log)
    v = float(m.group(1)) if m else None
    check("[43⑥] rc 0, TETRA10 한 개의 부피 = 1/6(예전 0)", rc == 0 and v is not None and R.near(v, 1.0 / 6.0, 1e-4),
          f"rc={rc} volume={v} " + log[-300:])


if __name__ == "__main__":
    for f in (hyphen, dwi_reuse, inertia_notice, vib_tet10):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
