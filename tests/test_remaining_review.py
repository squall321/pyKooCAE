#!/usr/bin/env python3
# 남은 결함 묶음 적대 리뷰(F1~F7)와 그 확인 중 찾은 결함을 작은 덱으로 판정하는 시험
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) 바. 적대 리뷰 반영.

  [F1]  처방 운동 카드 3 이 빈 줄(모든 칸 0)이면 다음 조건의 카드를 카드 3 으로 먹어 조건이 사라졌다 → 빈 카드 3 그대로
  [F2]  카드 3 의 LRB·NODE1·NODE2(번호)·OFFSET1·OFFSET2(좌표)가 IMPORT_MERGE_K·TRANSFORM·DROP 을 따라가지 않았다
        → 번호는 따라가고, 평행 이동·배율은 좌표도 따라가고, 회전·거울은 🔴 종료 코드 3
  [F3]  DWI 덱 재질 재사용 — getter 가 없는 재질이면 앞부분이 E·ρ 0, 해석 안 된 재질·없는 번호면 KeyError
  [F4]  *LOAD_SEGMENT_SET_ID 의 ID 카드 하나 + 카드 여럿이 rc 3 으로 둘째 카드부터 빠졌다
  [F5]  빈(기본값) 카드로 끝나는 마지막 개체(*MAT_RIGID 카드 2·3)를 나누지 못해 첫 개체만 읽었다
  [F6]  CPINLSDNR 소문자 이름·여러 정의(마지막 것)
  [F7]  읽지 못한 인클루드를 RIGID_DROP_ENDTIME 이 「질량 영향 없음」으로 알렸다 → 🔴 MISSING_INCLUDE
  [A8]  R16 규칙으로 센 식 값이 실수 계산과 다르면 ⚠️ 한 줄
  [43⑤] DROP 원점 이동에 원문 *_INERTIA 무게중심(NODEID 없는 것)이 따라간다
  [E2R] ELASTIC_TO_RIGID 가 원문 재질 파트에서 AttributeError → 원인 🔴 종료 코드 1, 제외하면 rc 0

실행: venv312/bin/python tests/test_remaining_review.py (KMM 스무 번 안팎, 몇 분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import glob
import os
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


def rows(text, kw, keep_tail=False):
    """정확히 kw 인 블록마다 데이터 줄(주석 뺌, 빈 줄은 남김 — keep_tail 이 아니면 끝 빈 줄은 뗀다)."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            if cur is not None and not keep_tail:
                while cur and not cur[-1].strip():
                    cur.pop()
            cur = None
            if ln.split()[0].upper() == kw:
                cur = []
                out.append(cur)
            continue
        if cur is not None and not ln.startswith("$"):
            cur.append(ln.rstrip())
    if cur is not None and not keep_tail:
        while cur and not cur[-1].strip():
            cur.pop()
    return out


def outputs(d):
    """덱 옆에 새로 생긴 .k(리더 덤프 제외)와 runs 아래 .k 글을 합친 것."""
    paths = [p for p in glob.glob(str(d) + "/*.k") + glob.glob(str(d) + "/runs/**/*.k", recursive=True)
             if not p.endswith(("/model.k", "_dump.k", "/imp.k", "/base.k"))]
    return "\n".join(Path(p).read_text(errors="replace") for p in sorted(paths))


CURVE7 = "*DEFINE_CURVE\n" + f10(7) + f"{0.0:>20}{0.0:>20}\n{1.0:>20}{1.0:>20}\n"   # 점 카드는 20칸 두 칸


def f1():
    print("[F1] 빈 카드 3")
    pm = ("*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(7, 9, 0, 7, 1.0) + "\n" + f10(8, 1, 0, 7, 1.0) + f10(6, 10, 0, 7, 1.0) + "\n"
          + "*BOUNDARY_PRESCRIBED_MOTION_NODE_ID\n" + f10(71).rstrip() + "ax\n" + f10(5, 9, 0, 7, 1.0) + "\n" + f10(72).rstrip() + "b\n"
          + f10(4, 1, 0, 7, 1.0) + CURVE7)
    d, rc, log = R.run("rv_f1", {"model.k": R.cube_deck(pm)})
    t = R.read(d, "model_trans.k")
    nb = [r for b in rows(t, "*BOUNDARY_PRESCRIBED_MOTION_NODE", keep_tail=True) for r in b]
    want = [(7, 9), None, (8, 1), (6, 10), None]
    got = [None if not r.strip() else tuple(R.ints(r[:20], 10)) for r in nb]
    check("[F1] rc 0, 여러 절점 블록 = 절점 7(DOF 9)·빈 카드 3·절점 8(DOF 1)·절점 6(DOF 10)·빈 카드 3(마지막 조건의 빈 카드 3 도)",
          rc == 0 and got == want, f"rc={rc} {got} " + log[-400:])
    ib = rows(t, "*BOUNDARY_PRESCRIBED_MOTION_NODE_ID", keep_tail=True)
    ids = [(R.ints(b[0][:10], 10)[0], len(b), b[2].strip() if len(b) > 2 else None) for b in ib]
    check("[F1] _ID 꼴 — ID 71(DOF 9) 뒤 빈 카드 3, ID 72(DOF 1) 조건도 남는다(다음 ID 줄을 카드 3 으로 먹지 않는다)",
          sorted(i for i, *_ in ids) == [71, 72] and any(i == 71 and n == 3 and c == "" for i, n, c in ids), f"{ids}")


def f2():
    print("[F2] 카드 3 의 번호·좌표")
    # IMPORT_MERGE_K — 가져온 덱의 파트 2·절점 3·4 를 가리키는 카드 3
    pts = R.cubes(2)
    imp = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 2, 9) + R.part(1) + R.part(2)
           + R.SOLID1 + R.ELASTIC + "*BOUNDARY_PRESCRIBED_MOTION_RIGID\n" + f10(1, 1, 4, 7, 1.0) + f10(0.0, 0.0, 2, 3, 4) + CURVE7
           + "*END\n")
    opt = "*Inputfile\nbase.k\n*Mode\nIMPORT_MERGE_K,1\n**ImportMergeK,1\nImportFile,imp.k\n**End\n*End\n"
    d, rc, log = R.run("rv_f2m", {"base.k": R.cube_deck(), "imp.k": imp}, opt)
    t = R.read(d, "base_imported.k")
    b = rows(t, "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")
    typeid = R.ints(b[0][1][:10], 10)[0] if b and len(b[0]) > 2 else None
    c3 = R.ints(b[0][2][20:50], 10) if b and len(b[0]) > 2 else None
    nd = R.nodes(t)
    ok_nodes = c3 is not None and all(nd.get(c3[k]) == pts[2 + k] for k in (1, 2))
    check("[F2] IMPORT_MERGE_K — TYPEID 1→2 와 같이 LRB 2→3, NODE1·NODE2 3·4→11·12(그 절점 좌표가 가져온 절점 3·4)",
          rc == 0 and typeid == 2 and c3 is not None and c3[0] == 3 and c3[1:] == [11, 12] and ok_nodes, f"rc={rc} {b} " + log[-300:])
    # TRANSFORM — 평행 이동(DOF 9: OFFSET1=y, OFFSET2=z)·배율(DOF 10: z·x)·회전
    pm = "*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(7, 9, 0, 7, 1.0) + f10(0.5, 0.5) + f10(6, 10, 0, 7, 1.0) + f10(0.5, 0.25) + CURVE7
    tr = lambda line: "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\n" + line + "\n**EndTransform\n*End\n"
    for tag, line, want in (("tr", "Translation,0,100,0", [(100.5, 0.5), (0.5, 0.25)]),
                            ("sc", "Scale,2,3,4", [(1.5, 2.0), (2.0, 0.5)])):
        d, rc, log = R.run("rv_f2" + tag, {"model.k": R.cube_deck(pm)}, tr(line))
        b = rows(R.read(d, "model_trans.k"), "*BOUNDARY_PRESCRIBED_MOTION_NODE")
        got = [tuple(R.floats(b[0][k][:20], 10)) for k in (1, 3)] if b and len(b[0]) >= 4 else None
        check(f"[F2] TRANSFORM {line} — 카드 3 OFFSET1·OFFSET2 = {want}", rc == 0 and got is not None
              and all(R.near(g, w) for gg, ww in zip(got, want) for g, w in zip(gg, ww)), f"rc={rc} {got} " + log[-300:])
    d, rc, log = R.run("rv_f2rot", {"model.k": R.cube_deck(pm)}, tr("Rotation,0,0,90"))
    check("[F2] TRANSFORM Rotation — 🔴 회전축(카드 3)을 옮길 수 없다, 종료 코드 3", rc == 3 and "회전축" in log and "🔴" in log,
          f"rc={rc} " + log[-300:])
    # 파트만 옮기는 모드 — 처방 운동 절점(7, 파트 1)이 든 파트를 옮기면 🔴 종료 코드 3, 다른 파트만이면 그대로
    pts = R.cubes(2)
    two = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 2, 9) + R.part(1) + R.part(2)
           + R.SOLID1 + R.ELASTIC + "*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(7, 9, 0, 7, 1.0) + f10(0.5, 0.5) + CURVE7 + "*END\n")
    pt = lambda pid: f"*Inputfile\nmodel.k\n*Mode\nPART_TRANSLATE,1\n**PartTranslate,1\nTranslate,{pid},0,100,0\n**EndPartTranslate\n*End\n"
    d, rc, log = R.run("rv_f2pt1", {"model.k": two}, pt(1))
    check("[F2] PART_TRANSLATE 파트 1(처방 운동 절점 7 이 든 파트) — 🔴 회전축 점은 파트 이동을 따라가지 않는다, 종료 코드 3",
          rc == 3 and "PART_TRANSLATE" in log and "회전축" in log, f"rc={rc} " + log[-300:])
    d, rc, log = R.run("rv_f2pt2", {"model.k": two}, pt(2))
    check("[F2] PART_TRANSLATE 파트 2(처방 운동 절점 없음) — rc 0, 알림 없음", rc == 0 and "회전축" not in log, f"rc={rc} " + log[-300:])
    # DROP 원점 맞춤 이동(-0.5, -0.5, -0.5) — DOF 11: OFFSET1=x, OFFSET2=y
    pm11 = "*BOUNDARY_PRESCRIBED_MOTION_NODE\n" + f10(7, 11, 0, 7, 1.0) + f10(0.5, 0.5) + CURVE7
    d, rc, log = R.run("rv_f2drop", {"model.k": R.cube_deck(pm11)}, R.drop([0]))
    b = rows(outputs(d), "*BOUNDARY_PRESCRIBED_MOTION_NODE")
    got = tuple(R.floats(b[0][1][:20], 10)) if b and len(b[0]) >= 2 else None
    check("[F2] DROP 원점 맞춤 이동 — DOF 11 카드 3 OFFSET1·OFFSET2 (0.5, 0.5) → (0, 0)", rc == 0 and got is not None
          and all(abs(g) < 1e-9 for g in got), f"rc={rc} {got} " + log[-300:])


def dwi_model(mat):
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{x:16.6e}{y:16.6e}{z:16.6e}")
    return ("*KEYWORD\n*NODE\n" + "\n".join(out) + "\n*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mat
            + "*ELEMENT_SOLID\n" + "".join(f"{k:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * k - 3, 4 * k + 5)) + "\n" for k in (1, 2))
            + "*END\n")


def dwi_opt(mid):
    return ("*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nTFinal,0.001\nDT,1e-06\nLocationX,0.5\n"
            "LocationY,0.5\nHeight,10\nGravity,9810.0\nImpactorType,cylinder\nImpactorDimension,0.3,0.4,0.2,0.4,0.4\nMeshSize,0.1\n"
            f"MaterialIDImpactor,{mid}\nGenerationMode,DampingSpring\nOffsetDistance,0.05\nYoungsModulusWall,10000.0\n"
            "PoissonRatioWall,0.3\nDensityWall,1e-09\n**EndDropWeightImpactTest\n*End\n")


def front(text):
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper() == "*MAT_ELASTIC_TITLE" and i + 1 < len(lines) and lines[i + 1].strip() == "ImpactorFrontMaterial":
            for k in range(i + 2, len(lines)):
                if not lines[k].startswith("$"):
                    v = [float(x) for x in lines[k].split()]
                    return v[1], v[2]
    return None


def f3():
    print("[F3] DWI 덱 재질 재사용")
    d, rc, log = R.run("rv_f3null", {"model.k": dwi_model("*MAT_NULL\n" + f10(1, "7.85E-09"))}, dwi_opt(1))
    m = front(R.read(d, "model_dwit.k"))
    check("[F3] *MAT_NULL(값을 해석하지 않는 재질) 재사용 — rc 0, 앞부분 = 단위계 표 ρ 7.8e-9·E 2.07e5(0 아님)",
          rc == 0 and m is not None and R.near(m[0], 7.8e-9) and R.near(m[1], 2.07e5), f"rc={rc} {m} " + log[-300:])
    d, rc, log = R.run("rv_f3raw", {"model.k": dwi_model("*MAT_001\n" + f10(1, "7.85E-09", 210000, 0.3))}, dwi_opt(1))
    t = R.read(d, "model_dwit.k")
    mids = {pid: mid for pid, (_, mid) in R.part_cards(t).items()} if t else {}
    check("[F3] 원문 *MAT_001 재사용 — rc 0(예전 KeyError), 충격체 파트가 MID 1 을 가리키고 *MAT_001 이 출력에 남는다",
          rc == 0 and "*MAT_001" in t and list(mids.values()).count(1) >= 2, f"rc={rc} {mids} " + log[-300:])
    d, rc, log = R.run("rv_f3none", {"model.k": dwi_model("*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))}, dwi_opt(99))
    check("[F3] 덱에 없는 MaterialIDImpactor 99 — 🔴 종료 코드 1(예전 KeyError traceback)",
          rc == 1 and "MaterialIDImpactor 99" in log and R.no_tb(log), f"rc={rc} " + log[-300:])


def f4():
    print("[F4] *LOAD_SEGMENT_SET_ID 카드 여럿")
    extra = ("*SET_SEGMENT\n" + f10(3) + f10(1, 2, 3, 4) + "*LOAD_SEGMENT_SET_ID\n" + f10(5).rstrip() + "press\n" + f10(3, 7, 1.0)
             + f10(3, 7, 2.0) + CURVE7)
    d, rc, log = R.run("rv_f4", {"model.k": R.cube_deck(extra)})
    b = rows(R.read(d, "model_trans.k"), "*LOAD_SEGMENT_SET_ID")
    sfs = sorted(R.floats(x[1][20:30], 10)[0] for x in b if len(x) > 1 and R.ints(x[0][:10], 10)[0] == 5)
    check("[F4] rc 0, 🔴 없음, ID 5 하중 두 개(SF 1.0·2.0)가 모두 나간다", rc == 0 and "🔴" not in log and sfs == [1.0, 2.0],
          f"rc={rc} {b} " + log[-300:])


def f5():
    print("[F5] 빈 카드로 끝나는 마지막 개체")
    pts = R.cubes(3)
    deck = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 2, 9) + R.hex_row(3, 3, 17)
            + R.part(1) + R.part(2, mid=2) + R.part(3, mid=3) + R.SOLID1 + R.ELASTIC
            + "*MAT_RIGID\n" + f10(2, "7.85E-09", 210000, 0.3) + f10(0) + f10(0) + f10(3, "7.85E-09", 210000, 0.3) + "\n\n*END\n")
    d, rc, log = R.run("rv_f5", {"model.k": deck})
    t = R.read(d, "model_trans.k")
    mids = [R.ints(r[1][:10], 10)[0] for _, r in R.kw_blocks(t, "*MAT_RIGID_TITLE") if len(r) > 1] + \
           [R.ints(r[0][:10], 10)[0] for _, r in R.kw_blocks(t, "*MAT_RIGID") if r]
    check("[F5] rc 0, 🔴 없음, *MAT_RIGID MID 2·3 모두(MID 3 은 카드 2·3 이 빈 줄)", rc == 0 and "🔴" not in log
          and {2, 3} <= set(mids), f"rc={rc} {mids} " + log[-300:])


def f6():
    print("[F6] CPINLSDNR")
    sys.path.insert(0, str(R.GEN))
    from KooCAEManager.KooParameterResolver import ParameterResolver
    r = ParameterResolver()
    for hdr, line in (("PARAMETER", "ccpinlsdnr      ##//cother                OTHER"), ("PARAMETER", "CCPINLSDNR      %%//")):
        r.DefineLine(r.ParseHeader(hdr), line + "\n")
    r.EndBlock()
    check("[F6] 소문자 ccpinlsdnr 줄 — 다음 이름(other)이 정의되고, 두 번째 정의(%%//)가 이긴다(R16 「마지막 것」)",
          r.params.get("other") == "OTHER" and r.params.get("cpinlsdnr") == "%%//", f"{dict(r.params)}")


def f7():
    print("[F7] 읽지 못한 인클루드와 RIGID_DROP_ENDTIME")
    opt = ("*Inputfile\nmodel.k\n*Mode\nRIGID_DROP_ENDTIME,1\n**RigidDropEndtime,1\nHeight,1500\nAngle,A,0,0,0\n"
           "**EndRigidDropEndtime\n*End\n")
    d, rc, log = R.run("rv_f7", {"model.k": R.cube_deck("*INCLUDE\nnot_there_rv.k\n")}, opt)
    check("[F7] rc 1, 🔴 MISSING_INCLUDE(「질량에는 영향이 없다」로 알리지 않는다)",
          rc == 1 and "MISSING_INCLUDE" in log and "질량에는 영향이 없다" not in log, f"rc={rc} " + log[-400:])


def a8():
    print("[A8] R16 의미로 값이 달라지는 식 알림")
    d, rc, log = R.run("rv_a8", {"model.k": R.cube_deck("*PARAMETER_EXPRESSION\nR half      1/2\nR whole     1.0/2\n")})
    check("[A8] rc 0, 'half=1/2' 는 ⚠️(R16 = 0.0, 실수 = 0.5), 'whole=1.0/2' 는 알림 없음",
          rc == 0 and "⚠️ PARAMETER_EXPRESSION 'half=1/2'" in log and "'whole=" not in log, f"rc={rc} " + log[-300:])


def inertia():
    print("[43⑤] DROP 원점 이동과 원문 관성 무게중심")
    cn = ("*SET_NODE_LIST\n" + f10(11) + f10(1, 2, 3, 4) + "*SET_NODE_LIST\n" + f10(12) + f10(5, 6, 7, 8)
          + "*CONSTRAINED_NODAL_RIGID_BODY_INERTIA\n" + f10(50, 0, 11) + f10(0.5, 0.5, 0.0, "1.0E-3", 0) + f10(1.0, 0.0, 0.0, 1.0, 0.0, 1.0)
          + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
          + "*CONSTRAINED_NODAL_RIGID_BODY_INERTIA\n" + f10(51, 0, 12) + f10(0.25, 0.25, 0.25, "1.0E-3", 0, 5)
          + f10(1.0, 0.0, 0.0, 1.0, 0.0, 1.0) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    d, rc, log = R.run("rv_inertia", {"model.k": R.cube_deck(cn)}, R.drop([0]))
    b = rows(outputs(d), "*CONSTRAINED_NODAL_RIGID_BODY_INERTIA")
    c = {R.ints(x[0][:10], 10)[0]: tuple(R.floats(x[1][:30], 10)) for x in b if len(x) > 1}
    check("[43⑤] rc 0, NODEID 없는 몸체 50 의 무게중심 (0.5, 0.5, 0) → (0, 0, -0.5)(절점과 같은 원점 이동)",
          rc == 0 and 50 in c and all(R.near(g, w) or abs(g - w) < 1e-9 for g, w in zip(c[50], (0.0, 0.0, -0.5))), f"rc={rc} {c} " + log[-300:])
    check("[43⑤] NODEID 5 로 준 몸체 51 은 그대로(그 절점이 중심이다), 옛 알림 「자세 회전을 따라가지 않는다」 없음",
          51 in c and all(R.near(g, w) for g, w in zip(c[51], (0.25, 0.25, 0.25))) and "자세 회전을 따라가지 않는다" not in log, f"{c}")


def e2r():
    print("[E2R] ELASTIC_TO_RIGID 와 원문 재질")
    pts = R.cubes(3)
    deck = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 2, 9) + R.hex_row(3, 3, 17)
            + R.part(1) + R.part(2, mid=2) + R.part(3, mid=2) + R.SOLID1 + R.ELASTIC + "*MAT_001\n" + f10(2, "7.85E-09", 210000, 0.3)
            + "*END\n")
    for tag, exc, want in (("none", "", 1), ("exc2", "*PIDExcept,2\n", 1), ("exc23", "*PIDExcept,2,3\n", 0)):
        opt = "*Inputfile\nmodel.k\n*Mode\nELASTIC_TO_RIGID,1\n**ElasticToRigid,1\n" + exc + "**EndElasticToRigid\n*End\n"
        d, rc, log = R.run("rv_e2r_" + tag, {"model.k": deck}, opt)
        t = R.read(d, "model_etor.k")
        if want == 1:
            check(f"[E2R] {exc.strip() or '제외 없음'} — 🔴 원문 재질 파트를 강체로 바꿀 수 없다, 종료 코드 1(예전 AttributeError)",
                  rc == 1 and "ELASTIC_TO_RIGID" in log and R.no_tb(log), f"rc={rc} " + log[-300:])
        else:
            check("[E2R] *PIDExcept,2,3 — rc 0, 파트 1 은 강체, 원문 *MAT_001 은 그대로",
                  rc == 0 and "*MAT_RIGID" in t and "*MAT_001" in t, f"rc={rc} " + log[-300:])


if __name__ == "__main__":
    for f in (f1, f2, f3, f4, f5, f6, f7, a8, inertia, e2r):
        try:
            f()
        except Exception as e:   # 한 묶음이 죽어도 나머지는 본다(수정 전 코드로 돌릴 때)
            check(f"{f.__name__} 실행", False, repr(e))
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
