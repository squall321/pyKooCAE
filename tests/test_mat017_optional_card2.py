# *MAT_ORIENTED_CRACK(MAT_017) 의 카드 2(SOFT CVELO)를 생략한 덱을 KMM 이 읽고 R16 기본값으로 쓰는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_mat017_optional_card2.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26, 리뷰 L): R16 MAT_017 카드 2 는 "Crack Propagation Card. Optional card"(SOFT 기본 1.0, CVELO 0.0).
KMM 재질 매니저가 카드 2 가 있다고 가정해 생략한 덱에서 IndexError 로 죽었다(덤프 파서는 이미 선택 카드로 읽었다).
0c6aecf(MAT_003 카드 2)와 같은 계열. 빈 SOFT 는 R16 기본값 1.0 으로 쓴다.
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
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck(card2):
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]))
    mat = "*MAT_ORIENTED_CRACK\n" + f10(1, "2.5E-09", 70000, 0.22, 45.0, 0.0, 30.0, 0.0)     # 카드 1 (FS 30)
    if card2 is not None:
        mat += card2
    return ("*KEYWORD\n" + nodes + "*PART\nglass\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mat
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def mat_cards(text):
    lines, inside = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith("*MAT_ORIENTED_CRACK")
            continue
        if inside and not ln.startswith("$"):
            lines.append(ln)
    return lines


def fields(line, n):
    return [line[i * 10:(i + 1) * 10].strip() for i in range(n)]


def main():
    base = Path(tempfile.mkdtemp(prefix="mat017_"))
    cases = (("카드 2 생략", None, 1.0, 0.0), ("카드 2 빈 줄", "\n", 1.0, 0.0),
             ("카드 2 있음(SOFT 0.5·CVELO 100)", f10(0.5, 100.0), 0.5, 100.0))
    for i, (name, card2, soft, cvelo) in enumerate(cases):
        d = base / f"c{i}"
        d.mkdir()
        (d / "model.k").write_text(deck(card2))
        (d / "opt.txt").write_text(OPT)
        r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
        out = d / "model_trans.k"
        check(f"{name}: rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
        if not out.exists():
            continue
        cards = mat_cards(out.read_text(errors="replace"))
        c1 = fields(cards[0], 8) if cards else []
        ok1 = len(c1) == 8 and abs(float(c1[4]) - 45.0) < 1e-9 and abs(float(c1[6]) - 30.0) < 1e-9
        check(f"{name}: 카드 1 SIGY 45·FS 30 그대로", ok1, str(cards[:2]))
        c2 = fields(cards[1], 2) if len(cards) > 1 else []
        ok2 = len(c2) == 2 and abs(float(c2[0] or 0) - soft) < 1e-9 and abs(float(c2[1] or 0) - cvelo) < 1e-9
        check(f"{name}: 카드 2 SOFT {soft}·CVELO {cvelo}", ok2, str(cards[:2]))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
