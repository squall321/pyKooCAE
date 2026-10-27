# KAM 패키지 *Define CurveFunction 식 회귀 시험 — 허용 식은 예전 eval 과 같은 값, 위험 식은 코드 실행 없이 거절
"""
실행: venv312/bin/python tests/test_kam_curve_function.py
수정 전 코드로 볼 때: KAM_GEN=<옛 occProject/Generators> …

배경 (2026-10-27): PackageGenerator.CreateCurveFunctionforPackage 가 옵션 파일의 식 글을 eval 했다 — 옵션 파일 한 줄로
임의 코드가 돈다(os.system 등). 이제 AST 화이트리스트(수·사칙·**·%·//·math/np 한 인자 함수·pi·e·tau)로 계산한다.
실제 경로(ImportPackage → CreateDefine)를 자식 프로세스로 돌린다. 9**9**9 같은 식에서 예전 코드가 멈추므로 시간 제한을 둔다.
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEN = Path(os.environ.get("KAM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
BASE = Path(tempfile.mkdtemp(prefix="kam_curvefn_"))
FAILS = []
CHILD = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from KooODBCADManager.PackageGenerator import PackageUserdefined
p = PackageUserdefined()
p.ImportPackage(sys.argv[2])
p.CreateDefine(None)
print("RESULT " + json.dumps({str(k): {"a1": [float(a) for a in v.a1], "o1": [float(o) for o in v.o1]}
                              for k, v in p.defineManager.defines.items()}))
"""
GOOD = [  # (LCID, 변수, 식) — 기준 x 0~2 를 0.5 간격
    (101, {"E": "2.5"}, "{E}*{x}**2+1"),
    (102, {}, "sin({x})*exp(-{x})"),
    (103, {}, "np.sqrt({x}+1)+np.sin({x})"),
    (104, {}, "math.cos({x})-math.pi"),
    (105, {}, "pi*{x}+e-tau"),
    (106, {}, "abs(-{x})+fabs({x})"),
    (107, {}, "{x}%0.3+{x}//0.7"),
    (108, {}, "-{x}+(+{x})*2"),
    (109, {}, "(1+{x})**0.5+2**10+2**-3"),
    (110, {}, "log10({x}+1)+log({x}+1)+radians({x})+degrees({x})"),
    (111, {}, "sinh({x})+cosh({x})+tanh({x})+floor({x}*3)+ceil({x}*3)"),
    (112, {}, "np.arctan({x})+np.exp(-{x})+np.log1p({x})+np.pi"),
    (113, {}, "round({x}*10)/10+int({x})+float({x})"),
    (114, {"E": "2.5"}, "{E}"),
    # 리뷰 R7 — 정수 거듭제곱은 정수 그대로(예전 eval: 3**65%7 = 5, (2**65+1)-2**65 = 1)
    (115, {}, "3**65%7+{x}"),
    (116, {}, "(2**65+1)-2**65+{x}"),
    # 리뷰 R8 — 예전에 되던 안전한 식: 조건식·비교(연쇄)·and/or·not·~·남은 math 한 인자 함수·np.round·True·inf
    (117, {}, "{x}/0.1 if {x}<0.1 else 1.0"),
    (118, {}, "({x}<0.5)*2+(0<{x}<=1.5)"),
    (119, {}, "erf({x})+erfc({x})+gamma({x}+1)+lgamma({x}+2)+cbrt({x})+exp2({x})"),
    (120, {}, "np.round({x}*3)+True"),
    (121, {}, "({x}>0 and {x}) or 0.25"),
    (122, {}, "(not {x})+~int({x}*2)"),
    (123, {}, "{x} if {x}<inf else 0"),
    (124, {}, "{x} if {x}<np.inf else np.nan"),
]


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def block(lcid, variables, expr):
    return (f"CurveFunction,{lcid},0,1.0,1.0,0.0,0.0,0,0\n" + "".join(f"{k},{v}\n" for k, v in variables.items())
            + "x,0,0.5,2\n" + expr + "\n")


def run(name, text, timeout=120):
    d = BASE / name
    d.mkdir()
    (d / "pkg.txt").write_text("*Define\n" + text + "*End\n")
    try:
        r = subprocess.run([PY, "-c", CHILD, str(GEN), str(d / "pkg.txt")], cwd=d, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return d, None, "시간 초과"
    return d, r.returncode, r.stdout + r.stderr


def expected(variables, expr):
    """예전 eval 과 같은 이름공간(PackageGenerator 의 from math import *·np)으로 계산한 기대값 — 시험이 정한 식만."""
    ns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    ns["np"], ns["math"] = np, math       # PackageGenerator 이름공간에는 별표 import 로 math 모듈도 보인다
    xs = np.arange(0.0, 2.0 + 0.5, 0.5).tolist()
    out = []
    for x in xs:
        s = expr
        for k, v in variables.items():
            s = s.replace("{" + k + "}", v)
        out.append(float(eval(s.replace("{x}", str(x)), ns)))
    return xs, out


def main():
    print(f"KAM_GEN={GEN}  BASE={BASE}")
    d, rc, log = run("good", "".join(block(*g) for g in GOOD))
    got = {}
    for ln in log.splitlines():
        if ln.startswith("RESULT "):
            got = json.loads(ln[7:])
    check(f"허용 식 {len(GOOD)}개: rc 0 · 커브 {len(GOOD)}개", rc == 0 and len(got) == len(GOOD), f"rc={rc} " + log[-800:])
    for lcid, variables, expr in GOOD:
        xs, want = expected(variables, expr)
        c = got.get(str(lcid), {})
        check(f"LCID {lcid} {expr}: 값이 eval 과 같음", c.get("a1") == xs and c.get("o1") == want, f"{c} != {want}")

    mark = BASE / "MARK"
    bad = [
        ("os_system", f"__import__('os').system('touch {mark}')"),
        ("open_file", "open('/etc/hostname').read().__len__()"),
        ("subclasses", "().__class__.__bases__[0].__subclasses__().__len__()"),
        ("comprehension", "[{x} for _ in ()].__len__()"),
        ("lambda", "(lambda: {x})()"),
        ("exec", "exec('import os')"),
        ("unknown_name", "{x}+undefined_name"),
        ("big_pow", "9**9**9"),
        ("square_chain", "np.square(" * 20 + "2**100" + ")" * 20),
    ]
    for name, expr in bad:
        d, rc, log = run("bad_" + name, block(201, {}, expr), timeout=60)
        check(f"거절 {name}: rc 1 · 'Error : DEFINE_CURVE_FUNCTION' · 결과 없음",
              rc == 1 and "Error : DEFINE_CURVE_FUNCTION" in log and "RESULT" not in log, f"rc={rc} " + log[-500:])
    check("위험 식이 실행되지 않음(os.system 이 만든 파일 없음)", not mark.exists(), str(mark))

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
