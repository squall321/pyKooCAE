#!/usr/bin/env python3
# 남은 결함 묶음 U5 판정 — *PARAMETER_EXPRESSION 이 R16 의미(정수·실수, 함수, 단항 마이너스, 이어지는 줄)로 세어지고 -&·^ 치환이 맞는지 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) A8 — R16 *PARAMETER_EXPRESSION Remark 2·3, *PARAMETER Remark 1·2.

  [1] 해석기 직접(소스에서만): 2/5 = 0·2.0/5 = 0.4, 정수 파라미터끼리의 나눗셈, -3**2 = 9·-(3**2) = -9·2**-3**2 = 512,
      sign·mod·min·max 두 인수, int·aint·nint·anint, csc·sec·ctn·sinh 무리, 이어지는 줄(앞 10칸 공백), '-&이름' 부호 바꿈(음수 값),
      '&이름^' 구분자와 CPINLSDNR, %g 로 줄어든 값. 예전엔 모두 실수로 셌고(2/5 = 0.4) -3**2 = -9 였다 — 덱의 &참조가
      LS-DYNA 와 다른 값으로 조용히 바뀌었다
  [2] KMM 덱: 위 의미가 카드 칸에 들어간 값(ENDTIM·ENDCYC·DTMIN·GLSTAT DT)과 파트 제목

실행: venv312/bin/python tests/test_remaining_parameter.py (KMM 1회, 30초 안)
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


EXPR = {   # 이름: (식 줄, 기대 값 글)
    "a": ("I a       2/5", "0"), "b": ("R b       2.0/5", "0.4"), "c": ("I c       7/2", "3"),
    "m1": ("R m1      -3**2", "9.0"), "m2": ("R m2      -(3**2)", "-9.0"), "m3": ("R m3      2**-3**2", "512.0"),
    "m4": ("R m4      - -3**2", "9.0"), "s": ("R s       sign(-4,8)", "4.0"), "md": ("I md      mod(-7,3)", "-1"),
    "md3": ("I md3     mod(7.6,3)", "2"), "n": ("I n       nint(-48.8)", "-49"), "an": ("R an      anint(-48.8)", "-49.0"),
    "it": ("I it      int(-48.1)", "-48"), "ai": ("R ai      aint(-48.1)", "-48.0"), "mn": ("R mn      min(2,3.5)", "2.0"),
    "cs": ("R cs      csc(pi/2)", "1.0"), "q": ("R q       ni/nj", "3.0"),
}


def t1():
    print("[1] 해석기 직접 — R16 의미")
    sys.path.insert(0, str(R.GEN))
    try:
        from KooCAEManager.KooParameterResolver import ParameterResolver as P
    except Exception as e:
        check("[1] KooParameterResolver 를 불러온다", False, repr(e))
        return
    r = P()
    r.DefineLine(P.ParseHeader("PARAMETER"), "I ni      7         I nj      2\n")
    hdr = P.ParseHeader("PARAMETER_EXPRESSION")
    for _, (line, _) in EXPR.items():
        r.DefineLine(hdr, line + "\n")
    r.DefineLine(hdr, "R t       1.0+\n")
    r.DefineLine(hdr, "          2.0*3\n")      # 이어지는 줄 — 앞 10칸 공백
    if hasattr(r, "EndBlock"):
        r.EndBlock()
    for name, (line, want) in EXPR.items():
        got = r.params.get(name)
        check(f"[1] {line.split(None, 2)[2]:<12} → {want}", got is not None and float(got) == float(want), f"got={got}")
    check("[1] 이어지는 줄: 'R t 1.0+' + '(10칸 공백) 2.0*3' → 7.0", r.params.get("t") is not None and float(r.params["t"]) == 7.0,
          f"got={r.params.get('t')} names={sorted(r.params)}")
    r2 = P()
    hp = P.ParseHeader("PARAMETER")
    r2.DefineLine(hp, "Rneg      -5.0      Rpos       5.0      CTST      01\n")
    r2.DefineLine(hp, "CCPINLSDNR      ^^//CINCDIR               PARAM\n")
    check("[1] '-&neg'(음수)·'-&pos' 고정폭 → '5.0'·'-5.0'",
          r2.SubstituteLine("     -&neg     -&pos\n", r2.params) == "       5.0      -5.0\n", repr(r2.SubstituteLine("     -&neg     -&pos\n", r2.params)))
    check("[1] 쉼표 줄 '-&neg,-&pos,&pos' → '5.0,-5.0,5.0'", r2.SubstituteLine("-&neg,-&pos,&pos\n", r2.params) == "5.0,-5.0,5.0\n",
          repr(r2.SubstituteLine("-&neg,-&pos,&pos\n", r2.params)))
    check("[1] CPINLSDNR '^^//' → '/home/&incdir^^test.inc' = '/home/PARAM/test.inc'",
          r2.SubstituteToken("/home/&incdir^^test.inc\n", r2.params) == "/home/PARAM/test.inc\n", repr(r2.params))
    r3 = P()
    r3.DefineLine(hp, "CTST      01\n")
    check("[1] 기본 구분자 'file_&TST^.k' → 'file_01_.k'", r3.SubstituteToken("file_&TST^.k\n", r3.params) == "file_01_.k\n")
    r4 = P()
    r4.DefineLine(hp, "R long    0.30000000000000004\n")
    out = r4.SubstituteLine("    &long\n", r4.params)
    check("[1] 칸보다 긴 값이 %g 로 줄면 토큰 폭 안에 오른쪽 맞춤(앞 칸을 자르지 않는다)", out == "     0.3\n" or out.strip() == "0.3"
          and len(out) == len("    &long\n"), repr(out))


def t2():
    print("[2] KMM 덱 — 카드 칸에 들어간 값")
    params = ("*PARAMETER\n" + "I nel     10        Rneg      -5.0      CTST      01\n"
              + "*PARAMETER_EXPRESSION\n" + "I half    nel/4\n" + "R tend    -0.1**2\n" + "R tsum    0.001+\n" + "          0.002\n")
    cards = ("*CONTROL_TERMINATION\n" + f"{'&tend':>10}{'&half':>10}{'-&neg':>10}\n" + "*DATABASE_GLSTAT\n" + f"{'&tsum':>10}{1:>10}\n")
    deck = ("*KEYWORD\n" + params + R.node_block(R.cubes(1)) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.part(1, name="&TST^body")
            + R.SOLID1 + R.ELASTIC + cards + "*END\n")
    d, rc, log = R.run("prm_e2e", {"model.k": deck})
    t = R.read(d, "model_trans.k")
    term = [l for b in R.kw_blocks(t, "*CONTROL_TERMINATION") for l in b[1]]
    v = R.try_(lambda: R.floats(term[0], 10), [])
    check("[2] rc 0, ENDTIM = (-0.1)**2 = 0.01, ENDCYC = 10/4 = 2(정수), DTMIN = -&neg = 5.0", rc == 0 and len(v) >= 3
          and R.near(v[0], 0.01) and int(v[1]) == 2 and R.near(v[2], 5.0), f"rc={rc} {term} " + log[-300:])
    gl = [l for b in R.kw_blocks(t, "*DATABASE_GLSTAT") for l in b[1]]
    g = R.try_(lambda: R.floats(gl[0], 10), [])
    check("[2] 이어지는 줄 식 tsum = 0.001+0.002 → GLSTAT DT 0.003", g and R.near(g[0], 0.003), f"{gl}")
    check("[2] 파트 제목 '&TST^body' → '01_body'", "01_body" in t and "&TST" not in t, log[-200:])


if __name__ == "__main__":
    for f in (t1, t2):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
