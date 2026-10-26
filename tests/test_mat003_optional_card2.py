# *MAT_PLASTIC_KINEMATIC 의 카드 2(SRC SRP FS VP)를 생략한 덱을 KMM 이 읽고 기본값으로 쓰는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_mat003_optional_card2.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26): R16 부록 V 는 칸마다 기본값이 있는 끝 카드를 생략해도 된다고 한다. MAT_003 카드 2 는 SRC·SRP·VP 0,
FS 기본값이 있다. KMM 은 카드 2 가 있다고 가정해 제목 없는·있는 형식 모두 IndexError 로 죽었다(덤프 파서·재질 매니저 두 곳).
또 *MAT_PLASTIC_KINEMATIC_TITLE 은 카드가 다 있어도 죽었다 — 덤프 클래스가 제목 없는 이름으로 넘겨 재질 매니저가 제목 줄을
카드 1 로 읽고 MID 검사에서 멈췄다(모든 판).
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


def deck(title, card2=False):
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]))
    kw = "*MAT_PLASTIC_KINEMATIC_TITLE\nsteel\n" if title else "*MAT_PLASTIC_KINEMATIC\n"
    mat = kw + f10(1, "7.85E-09", 210000, 0.3, 250.0, 1000.0, 0.0)          # 카드 1
    if card2:
        mat += f10(0.0, 0.0, "1.0E20", 0.0)
    return ("*KEYWORD\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + mat
            + "*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n*END\n")


def mat_cards(text):
    lines, inside, skip = [], False, 0
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith("*MAT_PLASTIC_KINEMATIC")
            skip = 1 if ln.upper().rstrip().endswith("_TITLE") else 0
            continue
        if inside and not ln.startswith("$"):
            if skip:
                skip -= 1
                continue
            lines.append(ln)
    return lines


def main():
    base = Path(tempfile.mkdtemp(prefix="mat003_"))
    for title, card2 in ((False, False), (True, False), (True, True), (False, True)):
        name = ("제목 있음" if title else "제목 없음") + (" · 카드 2 있음" if card2 else " · 카드 2 생략")
        d = base / (("title" if title else "plain") + ("_c2" if card2 else ""))
        d.mkdir()
        (d / "model.k").write_text(deck(title, card2))
        (d / "opt.txt").write_text(OPT)
        r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
        out = d / "model_trans.k"
        check(f"{name}: rc 0·출력", r.returncode == 0 and out.exists(), (r.stdout + r.stderr)[-500:])
        if not out.exists():
            continue
        cards = mat_cards(out.read_text(errors="replace"))
        ok = len(cards) >= 1 and abs(float(cards[0][40:50]) - 250.0) < 1e-9
        check(f"{name}: SIGY 250 그대로", ok, str(cards[:2]))
        fs = None
        if len(cards) >= 2 and cards[1][20:30].strip():
            fs = float(cards[1][20:30])
        check(f"{name}: 카드 2 는 기본값(FS 1e20 또는 빈 칸)", len(cards) >= 2 and (fs is None or fs >= 1e19), str(cards[:2]))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:400])
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
