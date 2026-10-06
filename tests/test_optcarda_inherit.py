# OptCardA(SOFT SOFSCL LCIDAB MAXPAR SBOPT DEPTH BSORT FRCFRQ) 상속 + robust_contact 우선 회귀 시험
"""
실행: venv312/bin/python tests/test_optcarda_inherit.py   (KMM 3회 실행, 약 1~2분)

원본 GENERAL 을 기본값과 '다른' 값으로 박고 세 케이스를 돌려 필드별로 가린다.
  plain    — InheritGeneral 미지정 → 기본값(SOFT=2 MAXPAR=1.025 ...) 그대로 (회귀 0)
  inherit  — InheritGeneral,True → OptCardA 전 필드가 원본 GENERAL 값
  robust   — + RobustContact,True → SOFT=2·DEPTH=3 강제가 상속을 이긴다
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")
FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


DECK = """*KEYWORD
*NODE
         1             0.0             0.0             0.0       0       0
         2             1.0             0.0             0.0       0       0
         3             1.0             1.0             0.0       0       0
         4             0.0             1.0             0.0       0       0
         5             0.0             0.0             1.0       0       0
         6             1.0             0.0             1.0       0       0
         7             1.0             1.0             1.0       0       0
         8             0.0             1.0             1.0       0       0
*ELEMENT_SOLID
       1       1       1       2       3       4       5       6       7       8
*PART
P1
         1         1        15         0         0         0         0         0
*SECTION_SOLID
         1         1         0
*MAT_VISCOELASTIC_TITLE
Epoxy
        151.30000E-9 64.444000 48.333000 15.1040002500.00000
*CONTACT_AUTOMATIC_GENERAL_ID
        99GeneralAll
         0         0         2         0         0         0         0         0
      0.20      0.15       0.0       0.0      30.0         0     0.0001.0000E+20
    1.0000    1.0000    0.0000    0.0000    1.0000    1.0000    1.0000    1.0000
         1     0.100         0     0.000         2         0         0         1
*END
"""
# 원본 OptCardA: SOFT=1 SOFSCL=0.100 LCIDAB=0 MAXPAR=0.000 SBOPT=2 DEPTH=0 BSORT=0 FRCFRQ=1

CFG = """*Inputfile
{deck}
*RunDirectoryMode,True,{out}
*Info,T,x
*Description,optcarda
*Creator,a,a@a,C,A
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,100
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,0.05
Density,7.85e-9
YoungsModulus,2.0e5
PoissonRatio,0.3
tFinal,0.001
dt,1e-6
DropSurface,Plane,300,300,20,30,30,2
DeformableToRigid,True{extra}
**EndDropAttitude
*End
"""


def run(work, name, extra):
    out = Path(work) / ("out_" + name)
    cfg = Path(work) / ("cfg_" + name + ".txt")
    cfg.write_text(CFG.format(deck=Path(work) / "model.k", out=out, extra=extra), encoding="utf-8")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), str(cfg)], cwd=work,
                       capture_output=True, text=True, timeout=900)
    decks = [p for p in out.rglob("DropSet.k")
             if "/Output/" not in str(p) and "/DynamicRelaxation/" not in str(p)]
    return (decks[0] if decks else None), r.stdout + r.stderr


def optcards(deck):
    """접촉별 OptCardA 를 {접촉종류: [SOFT,SOFSCL,LCIDAB,MAXPAR,SBOPT,DEPTH,BSORT,FRCFRQ]} 로."""
    L = deck.read_text(encoding="utf-8").splitlines()
    res, i = {}, 0
    while i < len(L):
        if L[i].startswith("*CONTACT_AUTOMATIC_") and "TIED" not in L[i]:
            kw = L[i].replace("*CONTACT_AUTOMATIC_", "").split("_ID")[0]
            d, j = [], i + 1
            while j < len(L) and not L[j].startswith("*"):
                if not L[j].startswith("$"):
                    d.append(L[j])
                j += 1
            if len(d) >= 5:
                a = d[4]
                res[kw] = [a[k * 10:(k + 1) * 10].strip() for k in range(8)]
            i = j
        else:
            i += 1
    return res


def main():
    with tempfile.TemporaryDirectory(prefix="optcarda_", dir=str(ROOT / "tests")) as work:
        (Path(work) / "model.k").write_text(DECK, encoding="utf-8")

        print("=== plain — 기본값 유지 (회귀 0)")
        d, log = run(work, "plain", "")
        check("덱 생성", d is not None, log[-300:])
        if d:
            oc = optcards(d)
            ss, s2s = oc.get("SINGLE_SURFACE"), oc.get("SURFACE_TO_SURFACE")
            check("SS 존재", ss is not None); check("S2S 존재", s2s is not None)
            if ss:  check("SS  기본 SOFT=2 MAXPAR=1.025 DEPTH=35", ss[0] == "2" and ss[3] == "1.025" and ss[5] == "35", str(ss))
            if s2s: check("S2S 기본 SOFT=2 MAXPAR=1.025 DEPTH=35", s2s[0] == "2" and s2s[3] == "1.025" and s2s[5] == "35", str(s2s))

        print("=== inherit — OptCardA 전 필드가 원본 GENERAL")
        d, log = run(work, "inherit", "\nDropContact.InheritGeneral,True")
        check("덱 생성", d is not None, log[-300:])
        check("상속 로그 출력", "OptCardA 상속 from GENERAL" in log)
        if d:
            oc = optcards(d)
            for kw in ("SINGLE_SURFACE", "SURFACE_TO_SURFACE"):
                a = oc.get(kw)
                check(f"{kw} 존재", a is not None)
                if not a: continue
                for idx, name, want in ((0, "SOFT", "1"), (3, "MAXPAR", "0.000"),
                                        (4, "SBOPT", "2"), (5, "DEPTH", "0"), (6, "BSORT", "0")):
                    check(f"{kw} {name}={want}", a[idx] == want, f"{a[idx]!r}")

        print("=== robust — SOFT=2·DEPTH=3 강제가 상속을 이긴다")
        d, log = run(work, "robust", "\nDropContact.InheritGeneral,True\nRobustContact,True")
        check("덱 생성", d is not None, log[-300:])
        check("로그에 강제값 유지 표시", "robust_contact" in log and "강제값 유지" in log)
        if d:
            oc = optcards(d)
            ss = oc.get("SINGLE_SURFACE")
            check("SS 존재", ss is not None)
            if ss:
                check("SS SOFT=2 (robust 강제)", ss[0] == "2", ss[0])
                check("SS DEPTH=3 (robust 강제)", ss[5] == "3", ss[5])
                check("SS MAXPAR=0.000 (나머지는 상속)", ss[3] == "0.000", ss[3])
                check("SS BSORT=0 (나머지는 상속)", ss[6] == "0", ss[6])

    print("=== 소스 불변식")
    SRC = (GEN / "KooCAEManager" / "KooDynaAdvancedModification.py").read_text(encoding="utf-8")
    check("상속 블록 존재", "_inh_a = {}" in SRC)
    check("robust 시 SOFT·DEPTH 제외", 'if robust_contact and _n in ("SOFT", "DEPTH"):' in SRC)
    check("SS 변환 리터럴 0/1.025 → 변수", "ss.SetOptCardA(SOFT_opt, SOFSCL_opt, LCIDAB_opt, MAXPAR_opt" in SRC)
    check("바닥판 S2S 가 _inh_a 폴백 사용", 'drop_contact.get("MAXPAR", _inh_a.get("MAXPAR", 1.025))' in SRC)
    check("정수 필드 int 정리 + 실수 필드 표기 보존", "int(float(_raw))" in SRC and "_inh_a[_n] = _raw" in SRC)

    print()
    if FAILS:
        print("FAILED %d" % len(FAILS))
        for f in FAILS:
            print("  - %s" % f)
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
