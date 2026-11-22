#!/usr/bin/env python3
# 남은 결함 묶음 U7·U8 판정 — 재질 유효숫자·처방 운동 카드 3·Fast DROP 접촉 번호·D2R 의 MAT_RIGID·IMPORT_MERGE_K 침식·가지 접촉·TRANSFORM 알림
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) A9·B7·A10~A14.

  [A9]  재질 기록기가 유효숫자 4자리(>10.3e)로 덱 값을 깎았다(E 210040.5 → 2.100e+05) → 4자리로 담기는 값은 예전 바이트 그대로,
        아니면 10칸 최대 정밀도
  [B7]  처방 운동 카드 3(|DOF| 9·10·11, VAD 4)이 오면 멈췄다(rc 1) → 카드 1 뒤에 그대로 옮긴다
  [A10] Fast DROP 여러 각도에서 바닥 접촉 CID 가 각도마다 하나씩 밀렸다 → 각도마다 같다
  [A11] DROP DeformableToRigid 의 D→R·R→D 목록에 *MAT_RIGID 파트가 들어갔다(R16: 처음부터 강체) → R→D 에서 빼고, D→R 은 LRB 로
        합칠 때만
  [A12] IMPORT_MERGE_K 침식 원문의 빈 카드·빈 칸과 0 을 다르게 봐 같은 침식에 거짓 rc 3 → rc 0
  [A13] IMPORT_MERGE_K 가 가지(SSTYP 7)를 가리키는 접촉을 옮겨 기준 덱의 같은 번호 가지를 조용히 가리켰다 → 옮기지 않고 🔴 rc 3
  [A14] TRANSFORM 이 *DEFINE_BOX·강체벽 등의 좌표를 옮기지 않으면서 알리지 않았다 → ⚠️ 알림(rc 0)

실행: venv312/bin/python tests/test_remaining_modes.py (KMM 약 15회, 1~3분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다
import test_v131_modes as M    # noqa: E402
from test_d2r_round2 import d2r_cards   # noqa: E402

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def data_rows(text, kw):
    return [rows for _, rows in R.kw_blocks(text, kw)]


def card1(text, kw):
    """kw·kw_TITLE 블록의 카드 1 칸 값들(제목 꼴은 둘째 줄)."""
    out = []
    for k in (kw, kw + "_TITLE"):
        for _, rows in R.kw_blocks(text, k):
            i = 1 if k.endswith("_TITLE") else 0
            if len(rows) > i:
                v = R.try_(lambda: R.floats(rows[i], 10), None)
                if v:
                    out.append(v)
    return out


def a9():
    print("[A9] 재질 기록기 유효숫자")
    mats = ("*MAT_ELASTIC\n" + f10(1, "7.8512E-09", 210040.5, 0.3)
            + "*MAT_PIECEWISE_LINEAR_PLASTICITY\n" + f10(2, "7.85E-09", 210000.0, 0.3, 355.25, 1234.56) + f10(0.0, 0.0) + "\n" * 2
            + "*MAT_RIGID\n" + f10(3, "7.85E-09", 210040.5, 0.3) + f10(0, 0, 0) + "\n")
    deck = ("*KEYWORD\n" + R.node_block(R.cubes(3)) + "*ELEMENT_SOLID\n" + "".join(R.hex_row(k + 1, k + 1, 8 * k + 1) for k in range(3))
            + R.part(1, 1, 1) + R.part(2, 1, 2) + R.part(3, 1, 3) + R.SOLID1 + mats + "*END\n")
    d, rc, log = R.run("md_a9", {"model.k": deck})
    t = R.read(d, "model_trans.k")
    el = [v for v in card1(t, "*MAT_ELASTIC") if int(v[0]) == 1]
    check("[A9] MAT_ELASTIC 밀도 7.8512E-09·E 210040.5 그대로", rc == 0 and el and R.near(el[0][1], 7.8512e-9, 1e-12)
          and el[0][2] == 210040.5, f"rc={rc} {el} " + log[-200:])
    plp = card1(t, "*MAT_PIECEWISE_LINEAR_PLASTICITY")
    check("[A9] PLP SIGY 355.25·ETAN 1234.56 그대로", plp and plp[0][4] == 355.25 and plp[0][5] == 1234.56, str(plp))
    rg = [v for v in card1(t, "*MAT_RIGID") if int(v[0]) == 3]
    check("[A9] MAT_RIGID E 210040.5 그대로", rg and rg[0][2] == 210040.5, str(rg))
    d, rc, log = R.run("md_a9_plain", {"model.k": R.cube_deck()})
    t2 = R.read(d, "model_trans.k")
    line = [rows[1 if h.split()[0].upper().endswith("_TITLE") else 0] for h, rows in R.kw_blocks(t2, "*MAT_ELASTIC")
            + R.kw_blocks(t2, "*MAT_ELASTIC_TITLE") if len(rows) > 1 or not h.split()[0].upper().endswith("_TITLE")]
    check("[A9] 4자리로 담기는 값(7.85E-09·210000·0.3)은 예전 바이트 그대로", rc == 0 and line
          and line[0].rstrip() == f"{1:10d}{7.85e-09:10.3e}{210000.0:10.3e}{0.3:10.3e}", str(line))


RIG = ("*KEYWORD\n" + R.node_block(R.cubes(3)) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 4, 9) + R.hex_row(3, 5, 17)
       + R.part(1) + R.part(4, 1, 4) + R.part(5, 1, 5) + R.SOLID1 + R.ELASTIC
       + "*MAT_RIGID\n" + f10(4, "7.85E-09", 210000.0, 0.3) + "*MAT_RIGID\n" + f10(5, "7.85E-09", 210000.0, 0.3)
       + "*DEFINE_CURVE\n" + f10(10) + f"{0.0:20.4f}{0.0:20.4f}\n{1.0:20.4f}{1.0:20.4f}\n")


def b7():
    print("[B7] 처방 운동 카드 3")
    for kw, body, first, card3 in (
            ("RIGID", f10(4, 3, 4, 10, 1.0) + f10(5.0, 0.0, 5, 0, 0) + f10(5, 1, 0, 10, 2.0), 4, f10(5.0, 0.0, 5, 0, 0)),
            ("RIGID_ID", f"{71:10d}a\n" + f10(4, 9, 2, 10, 1.0) + f10(5.0, 0.0, 0, 0, 0) + f"{72:10d}b\n" + f10(5, 1, 0, 10, 2.0), 4,
             f10(5.0, 0.0, 0, 0, 0))):
        d, rc, log = R.run("md_b7", {"model.k": RIG + f"*BOUNDARY_PRESCRIBED_MOTION_{kw}\n" + body + "*END\n"})
        t = R.read(d, "model_trans.k")
        rows = [r for k in ("*BOUNDARY_PRESCRIBED_MOTION_RIGID", "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID") for r in data_rows(t, k)]
        flat = [ln for r in rows for ln in r]
        idx = [i for i, ln in enumerate(flat) if R.try_(lambda: int(ln[:10])) == first and R.try_(lambda: int(ln[10:20])) in (3, 9)]
        ok = (rc == 0 and idx and idx[0] + 1 < len(flat) and flat[idx[0] + 1].rstrip() == card3.rstrip("\n").rstrip()
              and sum(1 for ln in flat if R.try_(lambda: int(ln[:10])) == 5 and R.try_(lambda: int(ln[10:20])) == 1) == 1)
        check(f"[B7] *BOUNDARY_PRESCRIBED_MOTION_{kw}: rc 0, 카드 3 이 그 조건의 카드 1 바로 뒤, 둘째 조건(PID 5) 하나",
              ok, f"rc={rc} {flat} " + log[-300:])


def a10():
    print("[A10] Fast DROP 여러 각도 — 바닥 접촉 번호")
    d, rc, log = R.run("md_a10", {"model.k": R.cube_deck()}, R.drop([0, 30, 60]))
    outs = R.dropsets(d)
    cids = [sorted(R.cons_of(t)) for t in outs]
    check("[A10] rc 0, 각도 셋의 접촉 CID 목록이 모두 같다", rc == 0 and len(outs) == 3 and cids[0] == cids[1] == cids[2], f"rc={rc} {cids}")


def a11():
    print("[A11] DROP DeformableToRigid — *MAT_RIGID 파트")
    for opt, want_d2r in (("DeformableToRigid,True\n", {1}), ("DeformableToRigid,True\nD2RLrb,1\n", {1, 4, 5})):
        d, rc, log = R.run("md_a11", {"model.k": RIG + "*END\n"}, R.drop([0], opt))
        outs = R.dropsets(d)
        cards = d2r_cards(outs[0]) if outs else []
        d2r = {p for c in cards if c[1] == 2 for p, _ in c[5]}
        r2d = {p for c in cards if c[1] == 4 for p, _ in c[5]}
        check(f"[A11] {opt.strip().replace(chr(10), ' ')}: R→D 에 MAT_RIGID 파트(4·5) 없음, D→R = {sorted(want_d2r)}",
              rc == 0 and r2d == {1} and d2r == want_d2r, f"rc={rc} d2r={d2r} r2d={r2d}")


def a12_a13():
    print("[A12·A13] IMPORT_MERGE_K — 침식 빈 카드 대 0, 가지 접촉")
    one = lambda pid, sec, mid, name: ("*KEYWORD\n" + R.node_block(R.cubes(1)) + "*ELEMENT_SOLID\n" + R.hex_row(1, pid, 1)
                                       + R.part(pid, sec, mid, name) + "*SECTION_SOLID\n" + f10(sec, 1))
    steel = "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
    ero = ("*MAT_ADD_EROSION\n" + f10(1, 0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0) + f10(0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0)
           + f10(1, 0, 0, 0.0, 1.0, 0.0, 1.0, 0) + f10(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0) + f10(0.0, 0.5, "1.0E+20", 0.0))   # IDAM 1(카드 3)
    base = one(1, 1, 1, "a") + steel + ero + "\n" + f10(0.5, 0.0, 1.0) + "*END\n"
    imp = one(1, 1, 1, "b") + steel + ero + f10(0.0, 0.0, 0.0, 0.0) + f10(0.5, 0.0, 1.0) + "*END\n"
    d, rc, log = R.run("md_a12", {"base.k": base, "imp.k": imp}, R.IMO)
    check("[A12] 가운데 빈 카드 대 0 카드 — 같은 침식이라 rc 0(거짓 번호 충돌 없음)", rc == 0 and "🔴" not in log, f"rc={rc} " + log[-300:])
    branch = ("*SET_PART_TREE\n" + f10(7, 1) + f10(1) + "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n" + f"{9:10d}br\n"
              + f10(7, 1, 7, 3) + f10(0.0, 0.0) + f10(1.0, 1.0))
    imp2 = one(1, 1, 1, "b") + steel + branch + "*END\n"
    d, rc, log = R.run("md_a13", {"base.k": one(1, 1, 1, "a") + steel + "*END\n", "imp.k": imp2}, R.IMO)
    out = R.read(d, "base_imported.k")
    stypes = [R.floats(rows[1], 10)[2:4] for _, rows in R.kw_blocks(out, "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID") if len(rows) > 1]
    check("[A13] 가지(SSTYP 7) 접촉은 옮기지 않고 🔴 + 종료 코드 3", rc == 3 and "가지" in log and not any(7 in s for s in stypes),
          f"rc={rc} {stypes} " + log[-300:])


def a14():
    print("[A14] TRANSFORM — 옮기지 않는 좌표 카드 알림")
    box = "*DEFINE_BOX\n" + f10(1, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
    opt = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,10,0,0\n**EndTransform\n*End\n"
    d, rc, log = R.run("md_a14", {"model.k": R.cube_deck(box)}, opt)
    check("[A14] rc 0, ⚠️ 알림에 *DEFINE_BOX", rc == 0 and "TRANSFORM" in log and "*DEFINE_BOX(1)" in log, f"rc={rc} " + log[-300:])
    d, rc, log = R.run("md_a14_none", {"model.k": R.cube_deck()}, opt)
    check("[A14] 그런 카드가 없으면 알림 없음", rc == 0 and "*DEFINE_BOX" not in log and "좌표·벡터는 그대로" not in log, log[-200:])


if __name__ == "__main__":
    for f in (a9, b7, a10, a11, a12_a13, a14):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
