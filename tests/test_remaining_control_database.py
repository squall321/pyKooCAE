#!/usr/bin/env python3
# 남은 결함 묶음 U1 판정 — 한 벌짜리 제어·DB 카드의 선택 카드·끝 칸 소실(덱 글 되살리기)과 INTFOR·CONTACT·SOLID·EXTENT_BINARY 결함을 작은 덱으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) U1 — A1~A4 와 탐침에서 찾은 크래시 셋.

  [1] A1 기록기에 없는 끝 칸·끝 카드: TIMESTEP 카드 3·EMSCL, ACCURACY EXACC·SRTFLG, ENERGY DRLEN·DISEN, OUTPUT 카드 5 끝 칸·카드 6,
      CONTACT 카드 4 DIR_TIE·카드 7, SOLID 카드 2·3·COHEQC, DR 카드 2(IDRFLG 3), EXTENT_BINARY 카드 3·4, D3PLOT·D3DUMP 카드 2,
      기록 포맷이 자릿수를 버리던 값(T10JTOL·DT) → 출력의 같은 카드·칸에 같은 값(모양은 실제 덱에서 모은 것)
  [2] A2 *DATABASE_BINARY_INTFOR 카드 2(IOOPT)가 카드 1 을 덮어 DT 가 IOOPT 값이 되던 것 + KMM 이 쓴 덱을 다시 읽기
  [3] *DATABASE_BINARY_INTFOR_FILE — 이름 카드(쓸 때 TypeError)·선택 카드 2c 없음(IndexError)
  [4] A3 *CONTROL_CONTACT — 한 장짜리(IndexError), 3·4·5 장짜리의 카드 3~5 가 기본값으로 되돌아가던 것
  [5] A4 *CONTROL_SOLID — 빈 카드 2 + 카드 3(TET13V)
  [6] 한 장짜리 *DATABASE_EXTENT_BINARY(IndexError)
  [7] 덱 글 되살리기 규칙(소스에서만 — KooDeckEcho 를 직접 부른다): 기록기로 다 표현되는 덱은 바이트 그대로, 모드가 바꾼 칸은 모드 값,
      표기가 같아진 모드 값을 덱 글로 덮지 않음, 카드 짜임이 바뀌면 기록기 그대로, IDRFLG 가 바뀌면 끝 카드 없음, 콤마 덱 줄,
      키워드가 다른 객체에는 붙이지 않음
  [8] DROP_ATTITUDE: 모드가 바꾼 ENDTIM 은 모드 값, 모드가 새로 만든 D3PLOT 은 예전 그대로(덱 카드 2 를 잇지 않음),
      그대로 둔 TIMESTEP 카드 3·CONTACT 카드 7 은 남음

실행: venv312/bin/python tests/test_remaining_control_database.py (KMM 약 15회, 1~3분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import io
import re
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


def blocks_of(text, kw):
    """키워드가 정확히 kw 인 블록들의 데이터 줄(주석 '$' 뺌, 가운데 빈 줄은 남김 — 빈 카드도 카드다)."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("*"):
            cur = [] if ln.split()[0].upper() == kw else None
            if cur is not None:
                out.append(cur)
        elif cur is not None and not ln.startswith("$"):
            cur.append(ln)
    for b in out:
        while b and not b[-1].strip():
            b.pop()
    return out


def one(text, kw):
    b = blocks_of(text, kw)
    return b[0] if len(b) == 1 else None


_FEXP = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)$")


def num(s):
    s = s.strip()
    m = _FEXP.match(s)
    if m:
        s = m.group(1) + "e" + m.group(2)
    try:
        return float(s.replace("d", "e").replace("D", "e"))
    except ValueError:
        return None


def fields(line, w=10):
    if "," in line:
        return [x.strip() for x in line.split(",")]
    line = line.rstrip()
    return [line[i:i + w].strip() for i in range(0, len(line), w)]


def same(a, b):
    na = num(a)
    nb = num(b) if b else (0.0 if na is not None else None)   # 빈칸 ≡ 0
    if na is not None and nb is not None:
        return abs(na - nb) <= 1e-12 * max(1.0, abs(na), abs(nb))
    return a.upper() == b.upper()


def lost(deck_lines, out_lines, widths=None):
    """덱 칸 가운데 출력의 같은 카드·칸에 같은 값으로 없는 것들."""
    bad = []
    if out_lines is None:
        return ["출력에 블록이 없거나 둘 이상"]
    for i, ln in enumerate(deck_lines):
        w = (widths or {}).get(i, 10)
        o = out_lines[i] if i < len(out_lines) else None
        for j, a in enumerate(fields(ln, w)):
            if not a:
                continue
            if o is None:
                bad.append(f"카드 {i + 1} 없음")
                break
            fo = fields(o, w)
            b = fo[j] if j < len(fo) else ""
            if not same(a, b):
                bad.append(f"카드 {i + 1} 칸 {j + 1}: {a} → {b or '(없음)'}")
    return bad


PSET = "*SET_PART_LIST\n" + f10(21) + f10(1)

# 실제 덱에서 모은 꼴(graft 감사) — 기록기에 없는 끝 칸·끝 카드, 자릿수를 버리던 값
TAIL = {
    "*CONTROL_TIMESTEP": [f10(0.0, 0.9, 0, 0.0, "-1.0E-6", 0, 0, 0), f10("", "", 0, "", "", 0.0, 0.25, 0), f10("", 1, "1.0E-5", 1)],
    "*CONTROL_ACCURACY": [f10(1, 2, 0, 0, 1, 1)],
    "*CONTROL_ENERGY": [f10(2, 2, 2, 2, 2, 2, 2, 2)],
    "*CONTROL_OUTPUT": [f10(1, 0, 0, 0, 0.0, 0, 100, 5000), f10(0, 0, 2, 50, 0, 0.0, 0, 0), f10(2, 0, 1, 0, 0, 0, 10.0, 1),
                        f10(0, 0, 0, 0, 0, 0, 0, 0), f10(0, 0, 0, 0, 0, 1, 1), f10(1, 1, 1)],
    "*CONTROL_CONTACT": [f10(0.1, 0.0, 1, 0, 1, 0, 1, 0), f10(0, 0, 100, 0, 4.0, 0, 0, 1), f10(0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
                         f10(2, 1, 0, 1, 0, 1, 0.5, 1), f10(0, 0, 0, 0.0, 1.0, 0, 0.0, 0), f10(0, 0, 0, 0, 0, "", 0.0, 0),
                         f10(1, 0, 0, 1)],
    "*CONTROL_SOLID": [f10(0, 0, 4, 1, 0, 0.2125, 0, 0), "".join(f"{x:>8}" for x in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)), f10(1, 0, 1)],
    "*CONTROL_DYNAMIC_RELAXATION": [f10(250, 0.001, 0.995, "1.0E99", 0.0, 0, 0.04, 3), f10(21)],
    "*DATABASE_EXTENT_BINARY": [f10(0, 0, 3, 1, 1, 1, 1, 1), f10(0, 0, 0, 1, 1, 1, 2, 1), f10(0, 0, 1.0, 0, 0, 0, "STRESS", "STRESS"),
                                f10(1, 0)],
    "*DATABASE_BINARY_D3PLOT": [f10("1.2345E-4", 0, 0, 0, 0, 0), f10(1)],
    "*DATABASE_BINARY_D3DUMP": [f10(10000), f10(1)],
}
SOLID_W = {1: 8}


def deck(cards, extra=""):
    return R.cube_deck(PSET + "".join(kw + "\n" + "".join(c if c.endswith("\n") else c + "\n" for c in lines)
                                      for kw, lines in cards.items()) + extra)


def t1():
    print("[1] A1 기록기에 없는 끝 칸·끝 카드·자릿수를 버리던 값")
    d, rc, log = R.run("u1_tail", {"model.k": deck(TAIL)})
    out = R.read(d, "model_trans.k")
    check("[1] rc 0·Traceback 없음", rc == 0 and R.no_tb(log), f"rc={rc} " + log[-400:])
    for kw, lines in TAIL.items():
        dl = [c.rstrip("\n") for c in lines]
        bad = lost(dl, one(out, kw), SOLID_W if kw == "*CONTROL_SOLID" else None)
        check(f"[1] {kw}: 덱 {len(dl)}장의 모든 칸이 출력의 같은 카드·칸에", not bad, str(bad[:6]))
    # 두 번째 왕복 — KMM 이 쓴 덱을 다시 읽어도 같은 값(되살린 꼬리가 다음 읽기에서 칸을 밀지 않는다)
    d2, rc2, log2 = R.run("u1_tail2", {"model.k": out})
    out2 = R.read(d2, "model_trans.k")
    bad2 = {kw: lost([c.rstrip("\n") for c in lines], one(out2, kw), SOLID_W if kw == "*CONTROL_SOLID" else None)
            for kw, lines in TAIL.items()}
    check("[1] 두 번째 왕복(출력 → 입력)도 rc 0·모든 칸 그대로", rc2 == 0 and not any(bad2.values()),
          f"rc={rc2} " + str({k: v[:3] for k, v in bad2.items() if v}) + log2[-300:])
    check("[1] 두 번째 왕복의 제어·DB 블록이 첫 왕복과 같다(되살리기가 고정점)",
          all(one(out, kw) == one(out2, kw) for kw in TAIL), str([kw for kw in TAIL if one(out, kw) != one(out2, kw)]))


def t2():
    print("[2] A2 *DATABASE_BINARY_INTFOR 카드 2 가 카드 1 을 덮던 것")
    blk = "*DATABASE_BINARY_INTFOR\n" + f10("2.500E-04", "", 0, 0, 0, 0) + f10(1)
    d, rc, log = R.run("u1_intfor", {"model.k": R.cube_deck(blk)})
    out = R.read(d, "model_trans.k")
    b = one(out, "*DATABASE_BINARY_INTFOR")
    v = R.try_(lambda: (num(b[0][:10]), int(b[1][:10])), (None, None))
    check("[2] rc 0, DT 2.5E-4 그대로·IOOPT 1 그대로", rc == 0 and v[0] is not None and R.near(v[0], 2.5e-4) and v[1] == 1,
          f"rc={rc} {b} " + log[-300:])
    d2, rc2, _ = R.run("u1_intfor2", {"model.k": out})
    b2 = one(R.read(d2, "model_trans.k"), "*DATABASE_BINARY_INTFOR")
    v2 = R.try_(lambda: (num(b2[0][:10]), int(b2[1][:10])), (None, None))
    check("[2] KMM 이 쓴 덱을 다시 읽어도 DT 2.5E-4·IOOPT 1", rc2 == 0 and v2[0] is not None and R.near(v2[0], 2.5e-4) and v2[1] == 1,
          f"rc={rc2} {b2}")


def t3():
    print("[3] *DATABASE_BINARY_INTFOR_FILE — 이름 카드·선택 카드 2c")
    for tag, tail, ioopt in (("2c", f10(1), 1), ("no2c", "", 0)):
        blk = "*DATABASE_BINARY_INTFOR_FILE\nmy_intfor\n" + f10("1.0E-4", 0, 0, 0, 0, 0) + tail
        d, rc, log = R.run(f"u1_intforfile_{tag}", {"model.k": R.cube_deck(blk)})
        b = one(R.read(d, "model_trans.k"), "*DATABASE_BINARY_INTFOR_FILE")
        ok = (rc == 0 and R.no_tb(log) and b is not None and len(b) >= 2 and b[0].strip() == "my_intfor"
              and R.near(num(b[1][:10]) or 0.0, 1e-4) and (len(b) < 3 and ioopt == 0 or len(b) >= 3 and int(b[2][:10]) == ioopt))
        check(f"[3] 카드 2c {'있음' if tail else '없음'}: rc 0·Traceback 없음, 이름·DT 1E-4·IOOPT {ioopt}", ok, f"rc={rc} {b} " + log[-300:])


def t4():
    print("[4] A3 *CONTROL_CONTACT — 한 장짜리·3·4·5 장짜리")
    c = TAIL["*CONTROL_CONTACT"]
    for n in (1, 3, 4, 5):
        dl = [x.rstrip("\n") for x in c[:n]]
        d, rc, log = R.run(f"u1_cc{n}", {"model.k": R.cube_deck("*CONTROL_CONTACT\n" + "".join(c[:n]))})
        bad = lost(dl, one(R.read(d, "model_trans.k"), "*CONTROL_CONTACT"))
        check(f"[4] {n}장짜리: rc 0·Traceback 없음, 덱 칸이 모두 같은 카드·칸에", rc == 0 and R.no_tb(log) and not bad,
              f"rc={rc} {bad[:6]} " + log[-300:])


def t5():
    print("[5] A4 *CONTROL_SOLID — 빈 카드 2 + 카드 3")
    dl = [f10(0, 0, 4, 1, 0, 0.0, 0, 0).rstrip("\n"), "", f10(1, 0, 0).rstrip("\n")]
    d, rc, log = R.run("u1_solid_blank2", {"model.k": R.cube_deck("*CONTROL_SOLID\n" + "\n".join(dl) + "\n")})
    b = one(R.read(d, "model_trans.k"), "*CONTROL_SOLID")
    check("[5] rc 0, 출력 카드 3(세 번째 데이터 줄) TET13V 1", rc == 0 and b is not None and len(b) == 3 and not b[1].strip()
          and R.try_(lambda: int(b[2][:10])) == 1, f"rc={rc} {b} " + log[-300:])


def t6():
    print("[6] 한 장짜리 *DATABASE_EXTENT_BINARY")
    dl = [f10(0, 0, 3, 1, 1, 1, 1, 1).rstrip("\n")]
    d, rc, log = R.run("u1_eb1", {"model.k": R.cube_deck("*DATABASE_EXTENT_BINARY\n" + dl[0] + "\n")})
    bad = lost(dl, one(R.read(d, "model_trans.k"), "*DATABASE_EXTENT_BINARY"))
    check("[6] rc 0·Traceback 없음, 카드 1 칸 그대로", rc == 0 and R.no_tb(log) and not bad, f"rc={rc} {bad} " + log[-300:])


def t7():
    print("[7] 덱 글 되살리기 규칙(KooDeckEcho 직접)")
    sys.path.insert(0, str(R.GEN))
    try:
        from KooCAEManager import KooDeckEcho as E
        from KooCAEManager.KooDynaControl import KooControlManager, KooControlShell
        from KooCAEManager.KooDynaDatabase import KooDatabaseManager
    except Exception as e:   # 수정 전 나무엔 KooDeckEcho 가 없다
        check("[7] KooDeckEcho 를 불러온다", False, repr(e))
        return

    def render(obj, echo=True):
        s = io.StringIO()
        (E.write(obj, s) if echo else obj.WriteStreamDynaKeyword(s))
        return s.getvalue()

    def data(text):
        return [l for l in text.splitlines() if not l.startswith(("*", "$"))]

    cm = KooControlManager()
    cm.SetControlTermination(0.001, 0, 0.0, 0.0, 1.0e8, 0)
    t = cm.controlTermination
    E.attach(t, "CONTROL_TERMINATION", [f10("1.0E-3", 0, "0.0", "", "1.0E8", 0)])
    check("[7] 기록기로 다 표현되는 덱(1.0E-3·빈칸·1.0E8) → 기록기 출력과 바이트까지 같다", render(t) == render(t, False))
    t.ENDTIM = 0.004
    check("[7] 모드가 바꾼 칸은 모드 값", data(render(t))[0][:10] == format(0.004, ">10.3e"), data(render(t)))
    t.ENDTIM = 0.0012341   # 덱에서 막 가져온 상태로
    E.attach(t, "CONTROL_TERMINATION", [f10("0.0012341", 0, 0.0, 0.0, 1.0e8, 0)])
    check("[7] 기록 포맷이 버린 자릿수는 덱 글로 되살린다(0.0012341)", data(render(t))[0][:10].strip() == "0.0012341", data(render(t)))
    t.ENDTIM = 0.0012342   # 표기(1.234e-03)는 가져온 때와 같지만 값은 바뀌었다 → 덱 글로 덮으면 안 된다
    check("[7] 표기가 같아진 모드 값은 덱 글로 덮지 않는다", data(render(t))[0][:10] == format(0.0012342, ">10.3e"), data(render(t)))

    cm.SetControlDynamicRelaxation(250, 0.001, 0.995, 1.0e99, 0.0, 0, 0.04, 3)
    dr = cm.controlDynamicRelaxation
    E.attach(dr, "CONTROL_DYNAMIC_RELAXATION", [f10(250, 0.001, 0.995, "1.0E99", 0.0, 0, 0.04, 3), f10(21)], None, None, ("IDRFLG",))
    check("[7] DR 카드 2(DRPSET 21)를 끝 카드로 붙인다", data(render(dr))[-1].strip() == "21", data(render(dr)))
    dr.IDRFLG = 0
    check("[7] IDRFLG 가 바뀌면 끝 카드를 붙이지 않는다", len(data(render(dr))) == 1, data(render(dr)))

    cm.SetControlAccuracy(1, 2, 0, 0)
    ac = cm.controlAccuracy
    E.attach(ac, "CONTROL_ACCURACY", ["1,2,0,0,1,1"])
    check("[7] 콤마 덱 줄의 끝 칸(EXACC·SRTFLG)을 10칸으로 붙인다", data(render(ac))[0] == f10(1, 2, 0, 0, 1, 1).rstrip("\n"),
          data(render(ac)))

    sh = KooControlShell()
    sh._num_cards = 1
    E.attach(sh, "CONTROL_SHELL", [f10(20.0, 0, -1, 0, 2, 2, 1, 0), f10(1.0, 0, 0, 1, 0)])
    has_tail = len(data(render(sh))) == 2
    sh._num_cards = 2   # 모드가 카드 짜임을 바꿨다 → 기록기 그대로
    check("[7] 카드 짜임이 바뀌면 기록기 그대로", has_tail and render(sh) == render(sh, False), (has_tail, render(sh)))

    dm = KooDatabaseManager()
    dm.SetDatabaseBinaryIntfor(1e-4, 0, 0, 0, 0, 0, 0)
    it = dm.database["BINARY_INTFOR"]
    E.attach(it, "DATABASE_BINARY_INTFOR_FILE", ["name", f10("1.0E-4")])
    check("[7] 키워드 줄이 다른 객체(INTFOR 로 쓰는 객체에 INTFOR_FILE 블록)에는 붙이지 않는다",
          getattr(it, "_deck_lines", None) is None and render(it) == render(it, False))
    dm.SetDatabaseGlstat(1.0e-5, 1)
    g = dm.database["GLSTAT"]
    E.attach(g, "DATABASE_GLSTAT", [f10("1.0E-5", 1, "", 0)])
    check("[7] 0 을 빈칸으로 쓰는 기록기(GLSTAT LCUR·OPTION) — 바이트 그대로", render(g) == render(g, False))


def t8():
    print("[8] DROP_ATTITUDE — 모드가 바꾼 칸·새로 만든 카드·그대로 둔 끝 카드")
    cards = {k: TAIL[k] for k in ("*CONTROL_TIMESTEP", "*CONTROL_CONTACT", "*DATABASE_BINARY_D3PLOT")}
    cards["*CONTROL_TERMINATION"] = [f10(0.5, 0, 0.0, 0.0, "1.0E8", 0)]
    opt = ("*Inputfile\nmodel.k\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,0\nEulerPitching,0\nEulerYawing,0\nHeight,100\n"
           "InitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nInitialAngularVelocityX,0\nInitialAngularVelocityY,0\n"
           "InitialAngularVelocityZ,0\nOffsetDistance,0.05\nDensity,7.85e-9\nYoungsModulus,2.0e5\nPoissonRatio,0.3\ntFinal,0.001\n"
           "dt,1e-5\n**EndDropAttitude\n*End\n")
    d, rc, log = R.run("u1_drop", {"model.k": deck(cards)}, opt)
    out = R.read(d, "model_drop.k")   # 한 각도는 <이름>_drop.k
    check("[8] rc 0·낙하 덱", rc == 0 and bool(out), f"rc={rc} {[p.name for p in Path(d).iterdir()]} " + log[-300:])
    tm = one(out, "*CONTROL_TERMINATION")
    check("[8] ENDTIM 은 모드 값(tFinal 0.001), 나머지 칸(ENDMAS 1.0E8)은 그대로", tm is not None and R.near(num(tm[0][:10]) or 0, 0.001)
          and R.near(num(tm[0][40:50]) or 0, 1.0e8), str(tm))
    d3 = one(out, "*DATABASE_BINARY_D3PLOT")
    check("[8] 모드가 새로 만든 D3PLOT 은 예전 그대로(DT = dt·덱 카드 2 없음)", d3 is not None and len(d3) == 1
          and R.near(num(d3[0][:10]) or 0, 1e-5), str(d3))
    ts = [c.rstrip("\n") for c in TAIL["*CONTROL_TIMESTEP"]]
    check("[8] 그대로 둔 TIMESTEP 의 카드 3·EMSCL 이 남는다", not lost(ts, one(out, "*CONTROL_TIMESTEP")), str(one(out, "*CONTROL_TIMESTEP")))
    cc = [c.rstrip("\n") for c in TAIL["*CONTROL_CONTACT"]]
    check("[8] 그대로 둔 CONTACT 의 카드 4 DIR_TIE·카드 7 이 남는다", not lost(cc, one(out, "*CONTROL_CONTACT")), str(lost(cc, one(out, "*CONTROL_CONTACT"))))


if __name__ == "__main__":
    for f in (t1, t2, t3, t4, t5, t6, t7, t8):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
