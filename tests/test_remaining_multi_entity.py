#!/usr/bin/env python3
# 남은 결함 묶음 U2 판정 — 한 키워드 아래 여러 개체(나누기·알림)와 *RIGIDWALL_PLANAR 두 벽·끝 빈 줄을 작은 덱으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) A5·A6.

  [1] A5 나누기 동치: 한 키워드 아래 개체 둘(A) 과 키워드 둘(B) 의 출력 데이터 줄 모음이 같다 — 개체 크기가 매뉴얼로 정해진
      평범한 꼴(MAT_ELASTIC·MAT_RIGID·EOS_LINEAR_POLYNOMIAL·BOUNDARY_SPC_SET·CONSTRAINED_*·DAMPING_PART_*·DEFINE_COORDINATE_SYSTEM·
      INITIAL_VELOCITY_GENERATION·LOAD_SEGMENT_SET·DATABASE_NODAL_FORCE_GROUP). 예전엔 첫 개체만 읽고 나머지는 rc 0 으로 빠졌다.
      MAT_ELASTIC 은 E < 0 이면 카드 1.1 이 붙고, DAMPING_PART_MASS 는 FLAG = 1 이면 카드 2 가 붙는다(개체마다 크기가 다르다).
  [2] A5 알림: 나눌 수 없는 블록(_ID·_TITLE 꼴의 여러 개체, 개체 크기로 떨어지지 않는 줄 수, 개체 첫 줄 자리의 빈 줄)은 예전처럼 첫 개체만
      읽되 🔴 카드 소실 + 종료 코드 3
  [3] 한 개체 블록·끝 빈 줄은 예전 그대로(rc 0, 알림 없음)
  [5] A6 *RIGIDWALL_PLANAR: 한 블록 두 벽(네 줄), 끝 빈 줄 때문에 세 줄이 된 한 벽, 옛 KMM 꼴(ID + 카드 둘)
  [6] R16 이 밝힌 꼴은 나눈다(적대 리뷰 F4·F5): *LOAD_SEGMENT_SET_ID 의 ID 카드 하나 + 카드 여럿, *MAT_RIGID 의 빈 카드 3

실행: venv312/bin/python tests/test_remaining_multi_entity.py (KMM 약 60회, 3~6분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def deck_m(extra):
    """정육면체 다섯 — 1·5 탄성(파트 1·5), 2·3·4 강체(파트 2·3·4). 노드 셋 11·12·13, 파트 셋 21~24, 세그먼트 셋 31·32, 커브 10."""
    rigid = lambda mid: "*MAT_RIGID\n" + f10(mid, "7.85E-09", 210000.0, 0.3) + f10(0, 0, 0) + "\n"
    return ("*KEYWORD\n" + R.node_block(R.cubes(5)) + "*ELEMENT_SOLID\n" + "".join(R.hex_row(k + 1, k + 1, 8 * k + 1) for k in range(5))
            + R.part(1) + R.part(2, mid=2) + R.part(3, mid=2) + R.part(4, mid=2) + R.part(5) + R.SOLID1 + R.ELASTIC + rigid(2)
            + "*SET_NODE_LIST\n" + f10(11) + f10(1, 2, 3, 4) + "*SET_NODE_LIST\n" + f10(12) + f10(5, 6, 7, 8)
            + "*SET_NODE_LIST\n" + f10(13) + f10(33, 34, 35, 36)
            + "".join("*SET_PART_LIST\n" + f10(s) + f10(p) for s, p in ((21, 1), (22, 5), (23, 3), (24, 4)))
            + "*SET_SEGMENT\n" + f10(31) + f10(1, 2, 3, 4) + "*SET_SEGMENT\n" + f10(32) + f10(33, 34, 35, 36)
            + "*DEFINE_CURVE\n" + f10(10) + f"{0.0:20.4f}{0.0:20.4f}\n" + f"{1.0:20.4f}{1.0:20.4f}\n" + extra + "*END\n")


def body_lines(text):
    """출력의 데이터 줄 모음(키워드·주석 줄 제외) — 블록 나눔과 무관한 비교용."""
    return Counter(l.rstrip() for l in text.splitlines() if l.strip() and l[0] not in "*$")


# 이름: (키워드, [개체 1 줄들], [개체 2 줄들]) — 평범한 꼴, 개체 크기는 R16 매뉴얼
SPLIT = {
    "MAT_ELASTIC": ("*MAT_ELASTIC", [f10(7, "7.85E-09", 210000.0, 0.3)], [f10(8, "2.70E-09", 70000.0, 0.33)]),
    "MAT_ELASTIC_E<0": ("*MAT_ELASTIC", [f10(7, "7.85E-09", -210000.0, 0.3), f10(0.0, 0.0, 0.0, 0.0)],
                        [f10(8, "2.70E-09", 70000.0, 0.33)]),
    "MAT_RIGID": ("*MAT_RIGID", [f10(7, "7.85E-09", 210000.0, 0.3), f10(0, 0, 0), f10(0.0)],
                  [f10(8, "2.70E-09", 70000.0, 0.33), f10(1.0, 4, 7), f10(0.0)]),
    "EOS_LP": ("*EOS_LINEAR_POLYNOMIAL", [f10(7, 0.0, 1.0), f10(0.0, 0.0)], [f10(8, 0.0, 2.0), f10(0.0, 0.0)]),
    "SPC_SET": ("*BOUNDARY_SPC_SET", [f10(11, 0, 1, 1, 1)], [f10(13, 0, 1, 1, 1)]),
    "EXTRA_NODES_NODE": ("*CONSTRAINED_EXTRA_NODES_NODE", [f10(2, 1)], [f10(2, 2)]),
    "EXTRA_NODES_SET": ("*CONSTRAINED_EXTRA_NODES_SET", [f10(2, 11)], [f10(2, 13)]),
    "NODE_SET": ("*CONSTRAINED_NODE_SET", [f10(11, 7)], [f10(13, 7)]),
    "JOINT_SPH": ("*CONSTRAINED_JOINT_SPHERICAL", [f10(9, 17)], [f10(10, 18)]),
    "CNRB": ("*CONSTRAINED_NODAL_RIGID_BODY", [f10(101, 0, 11)], [f10(102, 0, 13)]),
    "DAMP_PART_MASS": ("*DAMPING_PART_MASS", [f10(1, 10, 1.0, 1), f10(1.0, 1.0, 1.0, 0.0, 0.0, 0.0)], [f10(5, 10, 1.0)]),
    "DAMP_PART_MASS_SET": ("*DAMPING_PART_MASS_SET", [f10(21, 10, 1.0)], [f10(22, 10, 1.0)]),
    "DAMP_PART_STIFF": ("*DAMPING_PART_STIFFNESS", [f10(1, 0.1)], [f10(5, 0.1)]),
    "DAMP_PART_STIFF_SET": ("*DAMPING_PART_STIFFNESS_SET", [f10(21, 0.1)], [f10(22, 0.1)]),
    "DEFINE_CSYS": ("*DEFINE_COORDINATE_SYSTEM", [f10(1, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0), f10(0.0, 1.0, 0.0)],
                    [f10(2, 5.0, 0.0, 0.0, 6.0, 0.0, 0.0), f10(5.0, 1.0, 0.0)]),
    "IV_GEN": ("*INITIAL_VELOCITY_GENERATION", [f10(1, 2, 0.0, 1.0, 0.0, 0.0), f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)],
               [f10(5, 2, 0.0, 2.0, 0.0, 0.0), f10(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)]),
    "LOAD_SEGMENT_SET": ("*LOAD_SEGMENT_SET", [f10(31, 10, 1.0)], [f10(32, 10, 2.0)]),
    "NODAL_FORCE_GROUP": ("*DATABASE_NODAL_FORCE_GROUP", [f10(11)], [f10(13)]),
}

# _ID·_TITLE 꼴 — 여러 개체가 (ID·제목 카드 + 카드) 짝인지 ID 하나 아래 카드 여럿인지 매뉴얼이 밝히지 않는다 → 나누지 않고 알린다
LOUD = {
    "SPC_SET_ID": ("*BOUNDARY_SPC_SET_ID", [f10(5), f10(11, 0, 1, 1, 1)], [f10(6), f10(13, 0, 1, 1, 1)]),
    "SPC_NODE_ID": ("*BOUNDARY_SPC_NODE_ID", [f10(5), f10(1, 0, 1, 1, 1)], [f10(6), f10(2, 0, 1, 1, 1)]),
    "NODE_SET_ID": ("*CONSTRAINED_NODE_SET_ID", [f10(5), f10(11, 7)], [f10(6), f10(13, 7)]),
    "JOINT_SPH_ID": ("*CONSTRAINED_JOINT_SPHERICAL_ID", [f10(5), f10(9, 17)], [f10(6), f10(10, 18)]),
    "CNRB_TITLE": ("*CONSTRAINED_NODAL_RIGID_BODY_TITLE", ["first\n", f10(101, 0, 11)], ["second\n", f10(102, 0, 13)]),
    "MAT_ELASTIC_TITLE": ("*MAT_ELASTIC_TITLE", ["steel\n", f10(7, "7.85E-09", 210000.0, 0.3)], ["alu\n", f10(8, "2.70E-09", 70000.0, 0.33)]),
    "MAT_RIGID_TITLE": ("*MAT_RIGID_TITLE", ["r1\n", f10(7, "7.85E-09", 210000.0, 0.3), f10(0, 0, 0), f10(0.0)],
                        ["r2\n", f10(8, "2.70E-09", 70000.0, 0.33), f10(0, 0, 0), f10(0.0)]),
    "DEFINE_CSYS_TITLE": ("*DEFINE_COORDINATE_SYSTEM_TITLE", ["c1\n", f10(1, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0), f10(0.0, 1.0, 0.0)],
                          ["c2\n", f10(2, 5.0, 0.0, 0.0, 6.0, 0.0, 0.0), f10(5.0, 1.0, 0.0)]),
}


def t1():
    print("[1] A5 나누기 동치 — 한 키워드 아래 개체 둘 = 키워드 둘")
    d0, rc0, _ = R.run("me_base", {"model.k": deck_m("")})
    base = body_lines(R.read(d0, "model_trans.k"))
    for name, (kw, e1, e2) in SPLIT.items():
        a = kw + "\n" + "".join(e1) + "".join(e2)
        b = kw + "\n" + "".join(e1) + kw + "\n" + "".join(e2)
        da, rca, la = R.run("me_a_" + name.replace("<", "lt"), {"model.k": deck_m(a)})
        db, rcb, lb = R.run("me_b_" + name.replace("<", "lt"), {"model.k": deck_m(b)})
        oa, ob = R.read(da, "model_trans.k"), R.read(db, "model_trans.k")
        A, B = body_lines(oa), body_lines(ob)
        miss = list((B - A).elements())
        # 헛판정 막기: 키워드 둘 출력(B)이 바탕 덱보다 두 개체 몫(줄 둘 이상)을 더 가져야 한다 — 안 쓰는 개체를 버리는 기록기면 무의미
        extra = sum((B - base).values())
        # E < 0 재료의 카드 1.1 은 KMM 이 옮기지 않는다 — 둘 다 🔴 + 종료 코드 3 (조용히 빠지지 않는다)
        want = 3 if name == "MAT_ELASTIC_E<0" else 0
        loud_ok = want == 0 or ("카드 1.1" in la and "카드 1.1" in lb)
        check(f"[1] {name}: rc {want}·{want}, 개체 둘 블록 출력 = 키워드 둘 출력(데이터 줄 모음, B 의 더한 줄 {extra})",
              rca == want and rcb == want and loud_ok and oa and A == B and extra >= 2,
              f"rc={rca}/{rcb} A에없음={miss[:4]} A에만={list((A - B).elements())[:4]} " + (la[-300:] if rca else ""))


def t2():
    print("[2] A5 알림 — 나눌 수 없는 블록은 첫 개체만 읽고 🔴 + 종료 코드 3")
    cases = dict(LOUD)
    e = SPLIT["MAT_RIGID"][1]
    cases["MAT_RIGID 3+1줄"] = ("*MAT_RIGID", e, [f10(8, "2.70E-09", 70000.0, 0.33)])
    cases["MAT_RIGID 개체 사이 빈 줄"] = ("*MAT_RIGID", e + ["\n"], SPLIT["MAT_RIGID"][2])   # 개체 첫 줄 자리의 빈 줄 — 경계 불명
    for name, (kw, e1, e2) in cases.items():
        a = kw + "\n" + "".join(e1) + "".join(e2)
        d, rc, log = R.run("me_loud_" + "".join(c if c.isalnum() else "_" for c in name), {"model.k": deck_m(a)})
        check(f"[2] {name}: 종료 코드 3·🔴 카드 소실 알림(키워드 이름)", rc == 3 and "🔴" in log and kw[1:] in log and R.no_tb(log),
              f"rc={rc} " + log[-400:])


def t6():
    print("[6] R16 이 밝힌 꼴은 나눈다(적대 리뷰 F4·F5) — 한 블록 출력 = 키워드 둘 출력")
    e = SPLIT["MAT_RIGID"][1]
    cases = {
        # *LOAD_SEGMENT_SET_ID: ID 카드 하나 + 카드 여럿("as many segment set cards as necessary") — 쓰는 ID 는 같다
        "LOAD_SEGMENT_SET_ID 카드 둘": ("*LOAD_SEGMENT_SET_ID", [f10(5), f10(31, 10, 1.0)], [f10(5), f10(32, 10, 2.0)], 1),
        # *MAT_RIGID 카드 2·3 은 비워도 된다 — 가운데·끝 개체의 빈 카드 3
        "MAT_RIGID 빈 카드 3": ("*MAT_RIGID", [e[0], e[1], "\n"], [SPLIT["MAT_RIGID"][2][0], f10(0, 0, 0), "\n"], 0),
    }
    for name, (kw, e1, e2, id_rows) in cases.items():
        a = kw + "\n" + "".join(e1) + "".join(e2[id_rows:])   # ID 꼴은 ID 카드를 한 번만
        b = kw + "\n" + "".join(e1) + kw + "\n" + "".join(e2)
        da, rca, la = R.run("me_r16a_" + "".join(c if c.isalnum() else "_" for c in name), {"model.k": deck_m(a)})
        db, rcb, lb = R.run("me_r16b_" + "".join(c if c.isalnum() else "_" for c in name), {"model.k": deck_m(b)})
        A, B = body_lines(R.read(da, "model_trans.k")), body_lines(R.read(db, "model_trans.k"))
        check(f"[6] {name}: rc 0·0, 🔴 없음, 한 블록 출력 = 키워드 둘 출력", rca == 0 and rcb == 0 and "🔴" not in la and A == B and A,
              f"rc={rca}/{rcb} A에없음={list((B - A).elements())[:4]} A에만={list((A - B).elements())[:4]} " + la[-300:])


def t3():
    print("[3] 한 개체 블록·끝 빈 줄은 예전 그대로")
    for name in ("MAT_RIGID", "DEFINE_CSYS", "MAT_ELASTIC"):
        kw, e1, _ = SPLIT[name]
        d, rc, log = R.run("me_one_" + name, {"model.k": deck_m(kw + "\n" + "".join(e1) + "\n\n")})
        check(f"[3] {name} 한 개체 + 끝 빈 줄 둘: rc 0·🔴 없음", rc == 0 and "🔴" not in log, f"rc={rc} " + log[-300:])


def rw_rows(text):
    """출력의 *RIGIDWALL_PLANAR* 블록 데이터 줄(주석 뺌) 목록."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = [] if ln.split()[0].upper().startswith("*RIGIDWALL_PLANAR") else None
            if cur is not None:
                out.append(cur)
        elif cur is not None and ln.strip() and not ln.startswith("$"):
            cur.append(ln)
    return out


def t5():
    print("[5] A6 *RIGIDWALL_PLANAR — 두 벽·끝 빈 줄·옛 KMM 꼴")
    w1 = [f10(11, 0, 0), f10(0.0, 0.0, -1.0, 0.0, 0.0, 0.0)]
    w2 = [f10(13, 0, 0), f10(0.0, 0.0, 9.0, 0.0, 0.0, 8.0)]
    d, rc, log = R.run("me_rw2", {"model.k": deck_m("*RIGIDWALL_PLANAR\n" + "".join(w1 + w2))})
    rws = rw_rows(R.read(d, "model_trans.k"))
    zs = sorted(R.try_(lambda: R.floats(b[-1], 10)[2], None) for b in rws if b)
    check("[5] 한 블록 두 벽: rc 0, 벽 둘(ZT -1·9)", rc == 0 and len(rws) == 2 and zs == [-1.0, 9.0], f"rc={rc} {rws} " + log[-300:])
    d, rc, log = R.run("me_rw_blank", {"model.k": deck_m("*RIGIDWALL_PLANAR\n" + "".join(w1) + "\n")})
    rws = rw_rows(R.read(d, "model_trans.k"))
    nsid = R.try_(lambda: int(rws[0][-2][:10]), None)
    check("[5] 끝 빈 줄이 붙은 한 벽: NSID 11·ZT -1 로 읽는다(예전엔 세 줄이라 ID 카드로 잘못 읽었다)",
          rc == 0 and len(rws) == 1 and nsid == 11 and R.near(R.floats(rws[0][-1], 10)[2], -1.0), f"rc={rc} {rws} " + log[-300:])
    d, rc, log = R.run("me_rw_legacy", {"model.k": deck_m("*RIGIDWALL_PLANAR\n" + f10(5) + "".join(w1))})
    rws = rw_rows(R.read(d, "model_trans.k"))
    check("[5] 옛 KMM 꼴(ID 5 + 카드 둘): 예전처럼 벽 하나·NSID 11", rc == 0 and len(rws) == 1
          and R.try_(lambda: int(rws[0][-2][:10])) == 11, f"rc={rc} {rws} " + log[-300:])


if __name__ == "__main__":
    for f in (t1, t2, t3, t5, t6):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
