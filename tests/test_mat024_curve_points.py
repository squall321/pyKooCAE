# *MAT_PIECEWISE_LINEAR_PLASTICITY 의 EPS1~8·ES1~8 카드가 KMM 출력에서 제자리에 남는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_mat024_curve_points.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26): 제목 없는 *MAT_PIECEWISE_LINEAR_PLASTICITY 의 카드 3(EPS1~8)·카드 4(ES1~8)를 KMM 이 i 의 홀짝으로
가르는데 카드 3 의 자리(imin)가 제목 유무로 3·4 라, 제목 없는 덱에서 EPS·ES 가 뒤바뀌어 출력됐다 — 응력-변형률 곡선이
거꾸로(변형률 칸에 250~400, 응력 칸에 0~1) 써진다. 경고 없이 1월 첫 소스부터. _TITLE 변형은 맞았다.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = Path(os.environ.get("KMM_GEN", ROOT / "occProject" / "Generators"))
PY = str(ROOT / "venv312" / "bin" / "python")
KMM_CMD = [os.environ["KMM_BIN"]] if os.environ.get("KMM_BIN") else [PY, str(GEN / "KooMeshModifier.py")]
ENV = dict(os.environ, PATH=str(ROOT / "venv312" / "bin") + ":" + os.environ.get("PATH", ""))
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
EPS = [0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
ES = [250.0, 260.0, 280.0, 300.0, 330.0, 350.0, 380.0, 400.0]
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck(title):
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]))
    kw = "*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE\nsteel\n" if title else "*MAT_PIECEWISE_LINEAR_PLASTICITY\n"
    mat = kw + f10(1, "7.85E-09", 210000, 0.3, 0.0, 0.0, 0.0, 0.0) + f10(0.0, 0.0, 0, 0, 0.0) + f10(*EPS) + f10(*ES)
    return ("*KEYWORD\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mat
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def mat_cards(text):
    """출력의 MAT_024 블록 데이터 줄(제목 줄 뺌)"""
    lines, inside = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith("*MAT_PIECEWISE_LINEAR_PLASTICITY")
            title = ln.upper().endswith("_TITLE")
            skip = 1 if title else 0
            continue
        if inside and not ln.startswith("$"):
            if skip:
                skip -= 1
                continue
            lines.append(ln)
    return lines


def floats(line):
    return [float(line[i:i + 10]) for i in range(0, len(line.rstrip()), 10)]


def main():
    base = Path(tempfile.mkdtemp(prefix="mat024_"))
    for title in (False, True):
        name = "제목 있음" if title else "제목 없음"
        d = base / ("title" if title else "plain")
        d.mkdir()
        (d / "model.k").write_text(deck(title))
        (d / "opt.txt").write_text(OPT)
        r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
        out = d / "model_trans.k"
        check(f"{name}: rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
        if not out.exists():
            continue
        cards = mat_cards(out.read_text(errors="replace"))
        check(f"{name}: 카드 4장", len(cards) >= 4, str(cards))
        if len(cards) >= 4:
            check(f"{name}: 카드 3 = EPS1~8", floats(cards[2]) == EPS, cards[2])
            check(f"{name}: 카드 4 = ES1~8", floats(cards[3]) == ES, cards[3])
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
