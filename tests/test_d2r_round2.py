# D2R 실사용 2차(10-07 감사 수정) 회귀 시험 — code 2/4, Remark 1 S2S 자동, SKIPPED 경고, LRB, 조합C 명시값, 키 정규화
"""
실행: venv312/bin/python tests/test_d2r_round2.py   (KMM 6회 실행, 약 2~3분)

  A  GEN 유지 + D2R, Type 미지정      → 바닥판 S2S 자동(D2R_FLOOR_AUTO_S2S), D2R code 2 / R2D code 4, entno = S2S cid
  B  GEN 유지 + D2R + Type,General     → 🔴 D2R_FLOOR_GENERAL 경고, S2S 없음
  C  IncludeWallInGeneral + D2R         → 🔴 D2R_SKIPPED, D2R 카드 0장
  D  D2RLrb,1 (2파트)                   → 파트 2 의 LRB=1, 파트 1 은 0 / D2RLrb,77 → 🔴 경고 후 0
  E  조합C + FS,0.44 명시              → 바닥판 S2S FS=0.44 (원본 GENERAL 0.20 이 아님)
  F  소문자 키 type,s2s + inherit_general,True → 정규화 로그 + S2S + 상속
  순수 python: _d2r_num 손실 없음, StepConfigBuilder lrb·inherit_general_contact 방출
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
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
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
         9             0.0             0.0             1.0       0       0
        10             1.0             0.0             1.0       0       0
        11             1.0             1.0             1.0       0       0
        12             0.0             1.0             1.0       0       0
        13             0.0             0.0             2.0       0       0
        14             1.0             0.0             2.0       0       0
        15             1.0             1.0             2.0       0       0
        16             0.0             1.0             2.0       0       0
*ELEMENT_SOLID
       1       1       1       2       3       4       5       6       7       8
       2       2       9      10      11      12      13      14      15      16
*PART
P1
         1         1        15         0         0         0         0         0
*PART
P2
         2         1        15         0         0         0         0         0
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

CFG = """*Inputfile
{deck}
*RunDirectoryMode,True,{out}
*Info,T,x
*Description,d2r_r2
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
    log = r.stdout + r.stderr
    decks = [p for p in out.rglob("DropSet.k") if "Output" not in p.parts and "DynamicRelaxation" not in p.parts]
    return (decks[0].read_text(encoding="utf-8", errors="replace") if decks else ""), log, r.returncode


def d2r_cards(deck):
    """[(swset, code, entno, relsw, paired, [(pid, lrb), ...]), ...]"""
    cards, lines = [], deck.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("*DEFORMABLE_TO_RIGID_AUTOMATIC"):
            data = []
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                if not lines[i].startswith("$"):
                    data.append(lines[i])
                i += 1
            c1 = data[0]
            f = lambda k: c1[k * 10:(k + 1) * 10].strip()
            pairs = []
            for ln in data[2:]:
                # D2R 목록은 "pid lrb PART", R2D 목록은 "pid PART"
                toks = ln.split()
                if toks:
                    lrb = int(toks[1]) if len(toks) > 1 and toks[1].lstrip("-").isdigit() else 0
                    pairs.append((int(toks[0]), lrb))
            cards.append((int(f(0)), int(f(1)), int(f(5)), int(f(6)), int(f(7)), pairs))
            continue
        i += 1
    return cards


def contact_cid(deck, kw):
    """첫 *CONTACT_<kw>_ID 의 CID"""
    lines = deck.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("*CONTACT_" + kw):
            j = i + 1
            while lines[j].startswith("$"):
                j += 1
            return int(lines[j][:10].strip())
    return None


def s2s_fs(deck):
    lines = deck.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"):
            data = [x for x in lines[i + 1:i + 8] if not x.startswith("$") and not x.startswith("*")]
            return data[2][0:10].strip()      # card 2 첫 칸 FS
    return None


def main():
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    work = tempfile.mkdtemp(prefix="d2r_r2_", dir="/data/koopark" if Path("/data/koopark").is_dir() else None)
    (Path(work) / "model.k").write_text(DECK, encoding="utf-8")
    GEN_KEEP = "\nConvertGeneralToSingleSurface,False"

    print("=== A  GEN 유지 + D2R, Type 미지정 → S2S 자동 + code 2/4")
    deck, log, rc = run(work, "A", GEN_KEEP)
    check("A KMM rc=0", rc == 0, str(rc))
    check("A D2R_FLOOR_AUTO_S2S 로그", "D2R_FLOOR_AUTO_S2S" in log)
    check("A 바닥판 S2S 1개", deck.count("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE") == 1)
    check("A 내부 GENERAL 1개", deck.count("*CONTACT_AUTOMATIC_GENERAL") == 1)
    cards = d2r_cards(deck)
    check("A D2R 카드 2장", len(cards) == 2, str(len(cards)))
    if len(cards) == 2:
        d2r = [c for c in cards if c[0] == 20][0]
        r2d = [c for c in cards if c[0] == 10][0]
        check("A SWSET 20 code 2 (접촉력 0 → 강체)", d2r[1] == 2, str(d2r))
        check("A SWSET 10 code 4 (접촉력 비0 → 변형체)", r2d[1] == 4, str(r2d))
        check("A relsw/paired 쌍 유지 (10,1)/(20,-1)", (d2r[3], d2r[4], r2d[3], r2d[4]) == (10, 1, 20, -1))
        cid = contact_cid(deck, "AUTOMATIC_SURFACE_TO_SURFACE")
        check("A entno = 바닥판 S2S CID", d2r[2] == cid and r2d[2] == cid, "%s vs %s" % (d2r[2], cid))
        check("A D2R 목록 2파트 LRB 0", d2r[5] == [(1, 0), (2, 0)], str(d2r[5]))

    print("=== B  GEN 유지 + D2R + Type,General → 경고, S2S 없음")
    deck, log, rc = run(work, "B", GEN_KEEP + "\nDropContact.Type,General")
    check("B KMM rc=0", rc == 0, str(rc))
    check("B 🔴 D2R_FLOOR_GENERAL 경고", "D2R_FLOOR_GENERAL" in log)
    check("B S2S 없음 (명시 General 존중)", "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" not in deck)
    check("B D2R 카드는 생성 (entno=GENERAL)", len(d2r_cards(deck)) == 2)

    print("=== C  IncludeWallInGeneral + D2R → SKIPPED 경고, 0장")
    deck, log, rc = run(work, "C", "\nIncludeWallInGeneral,True")
    check("C KMM rc=0", rc == 0, str(rc))
    check("C 🔴 D2R_SKIPPED 경고", "D2R_SKIPPED" in log)
    check("C D2R 카드 0장", len(d2r_cards(deck)) == 0)

    print("=== D  D2RLrb")
    deck, log, rc = run(work, "D1", GEN_KEEP + "\nD2RLrb,1")
    cards = d2r_cards(deck)
    d2r = [c for c in cards if c[0] == 20]
    check("D1 파트2 LRB=1, 파트1 은 0", bool(d2r) and d2r[0][5] == [(1, 0), (2, 1)], str(d2r[0][5] if d2r else cards))
    deck, log, rc = run(work, "D2", GEN_KEEP + "\nD2RLrb,77")
    cards = d2r_cards(deck)
    d2r = [c for c in cards if c[0] == 20]
    check("D2 모델에 없는 LRB → 🔴 경고", "D2RLrb=77" in log)
    check("D2 LRB 0 으로 복귀", bool(d2r) and d2r[0][5] == [(1, 0), (2, 0)], str(d2r[0][5] if d2r else cards))

    print("=== E  조합C + FS 명시 → 바닥판 S2S FS=0.44")
    deck, log, rc = run(work, "E", GEN_KEEP + "\nDropContact.Type,SurfaceToSurface\nDropContact.FS,0.44")
    check("E KMM rc=0", rc == 0, str(rc))
    fs = s2s_fs(deck)
    check("E 바닥판 S2S FS=0.44 (명시값 > 원본 0.20)", fs is not None and abs(float(fs) - 0.44) < 1e-9, str(fs))

    print("=== F  소문자 키 정규화 (type,s2s + inherit_general,True)")
    deck, log, rc = run(work, "F", GEN_KEEP + "\nDropContact.type,s2s\nDropContact.inherit_general,True")
    check("F KMM rc=0", rc == 0, str(rc))
    check("F 'type → Type' 해석 로그", "DropContact.type → Type" in log)
    check("F 'inherit_general → InheritGeneral' 해석 로그", "inherit_general → InheritGeneral" in log)
    check("F 바닥판 S2S 생성", deck.count("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE") == 1)
    fs = s2s_fs(deck)
    check("F 상속 FS=0.20 (원본 GENERAL)", fs is not None and abs(float(fs) - 0.20) < 1e-9, str(fs))

    print("=== 순수 python")
    sys.path.insert(0, str(GEN))
    sys.path.insert(0, str(ROOT))
    from KooCAEManager.KooDynaAdditional import _d2r_num
    for v, exp in ((1e20, "   1.0e+20"), (1e-7, "   1.0e-07"), (1.25e-3, "  1.25e-03"), (0.0, "       0.0")):
        check("_d2r_num %r" % v, _d2r_num(v) == exp, repr(_d2r_num(v)))
    from Runner.StepConfigBuilder import build_drop_attitude_config
    import inspect
    sig = inspect.signature(build_drop_attitude_config)
    src = (ROOT / "Runner" / "StepConfigBuilder.py").read_text(encoding="utf-8")
    check("StepConfigBuilder lrb → D2RLrb 매핑", '("lrb", "D2RLrb")' in src)
    check("StepConfigBuilder inherit_general_contact 별칭", "inherit_general_contact" in src and "DropContact.InheritGeneral" in src)

    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        print("work:", work)
        sys.exit(1)
    print("ALL OK  (work: %s)" % work)


if __name__ == "__main__":
    main()
