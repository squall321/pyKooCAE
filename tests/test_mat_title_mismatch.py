# *MAT_* 키워드/페이로드 불일치(bare 키워드 + 제목 줄)가 재질을 무언 손실시키던 것의 회귀 시험
"""
실행: venv312/bin/python tests/test_mat_title_mismatch.py

덱 3종으로 검증한다.
  A 정상(_TITLE)    — *MAT_VISCOELASTIC_TITLE + 제목 + $#주석 + 데이터 → mid 보존
  B 정상(bare)      — *MAT_VISCOELASTIC + $#주석 + 데이터            → mid 보존
  C 파괴(불일치)    — *MAT_VISCOELASTIC + 제목 + $#주석 + 데이터     → 에러로 중단해야 한다
                      (수정 전에는 Viscoelastic0·전필드 0·mid 재부여로 조용히 통과했다)
"""
import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
sys.path.insert(0, str(GEN))

FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


HEAD = """*KEYWORD
*TITLE
MAT title mismatch regression
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
PartUsingMid15
         1         1        15         0         0         0         0         0
*SECTION_SOLID
         1         1         0
*MAT_VISCOELASTIC
$#     mid        ro      bulk        g0        gi      beta
        471.30000E-9 66.570000 1.3400000 0.5228000 24290.000
"""
CARD = "$#     mid        ro      bulk        g0        gi      beta\n" \
       "        151.30000E-9 64.444000 48.333000 15.1040002500.00000\n"
TAIL = "*END\n"

DECKS = {
    "A_title":    HEAD + "*MAT_VISCOELASTIC_TITLE\nEpoxy_100M\n" + CARD + TAIL,
    "B_bare":     HEAD + "*MAT_VISCOELASTIC\n" + CARD + TAIL,
    "C_mismatch": HEAD + "*MAT_VISCOELASTIC\nEpoxy_100M\n" + CARD + TAIL,
}


def load(workdir, name, text):
    """덱을 읽어 (재질 dict, 예외) 를 돌려준다."""
    from KooCAEManager.KooDynaKeyword import DynaManager
    from KooCAEManager.KooMaterial import KooMaterialManager

    path = Path(workdir) / (name + ".k")
    path.write_text(text, encoding="utf-8")

    dm = DynaManager()
    dm.currentDirectory = str(workdir)
    dm.inputFile = path.name
    buf = io.StringIO()
    cwd = os.getcwd()
    try:
        with contextlib.redirect_stdout(buf):
            dm.ReadInputFile("log.txt", writelog=False)
    finally:
        os.chdir(cwd)

    mats = []
    for kw, obj in dm.dynaKeywordMan.keywords.items():
        if "VISCO" in kw and hasattr(obj, "getMatList"):
            mats.extend(obj.getMatList())

    mm = KooMaterialManager()
    err = None
    try:
        with contextlib.redirect_stdout(buf):
            for m in mats:
                mm.AddMaterialfromDyna(m)
    except Exception as exc:          # 가드가 잡으면 여기로 온다
        err = exc
    return mm.materials, err, buf.getvalue()


def main():
    with tempfile.TemporaryDirectory(prefix="mat_title_") as work:
        print("=== A 정상(_TITLE) — 제목·주석 있어도 mid 보존")
        mats, err, _ = load(work, "A_title", DECKS["A_title"])
        check("A 예외 없음", err is None, repr(err))
        check("A mid 15 존재", 15 in mats)
        check("A mid 47 존재", 47 in mats)
        check("A 재질 2개", len(mats) == 2, str(sorted(mats)))
        if 15 in mats:
            m = mats[15]
            check("A name=Epoxy_100M", m.name == "Epoxy_100M", m.name)
            check("A K=64.444", abs(m.K - 64.444) < 1e-9, str(m.K))
            check("A G0=48.333", abs(m.G0 - 48.333) < 1e-9, str(m.G0))
            check("A BETA=2500", abs(m.BETA - 2500.0) < 1e-9, str(m.BETA))

        print("=== B 정상(bare) — 제목 없이도 mid 보존")
        mats, err, _ = load(work, "B_bare", DECKS["B_bare"])
        check("B 예외 없음", err is None, repr(err))
        check("B mid 15 존재", 15 in mats)
        check("B 재질 2개", len(mats) == 2, str(sorted(mats)))
        if 15 in mats:
            check("B K=64.444", abs(mats[15].K - 64.444) < 1e-9, str(mats[15].K))

        print("=== C 파괴(bare + 제목) — 조용히 통과하면 안 된다")
        mats, err, log = load(work, "C_mismatch", DECKS["C_mismatch"])
        silent_loss = err is None and 15 not in mats
        check("C 에러로 중단됨 (무언 손실 아님)", err is not None,
              "무언 손실 재현: mid=%s" % sorted(mats))
        if err is not None:
            msg = str(err)
            check("C 메시지에 키워드 포함", "MAT_VISCOELASTIC" in msg, msg[:120])
            check("C 메시지에 _TITLE 지적 포함", "_TITLE" in msg, msg[:120])
            check("C 메시지에 문제 줄 원문 포함", "Epoxy_100M" in msg, msg[:120])
        else:
            print("     (참고) 무언 손실 상태 — 등록된 mid: %s" % sorted(mats))
            for mid, m in sorted(mats.items()):
                print("       mid=%s name=%s K=%s G0=%s" % (mid, m.name, m.K, m.G0))

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
