# 내보내기에서 요소가 빠지면 KMM 이 🔴 요약과 종료 코드 3 으로 끝나는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_export_element_loss.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26 사용자 결정 "요소 소실 시 비 0 종료"): *NODE 가 LS-DYNA 고정폭(NID 8칸)이 아닌 덱(KooRemapper merge
예제는 NID 를 10칸에 쓴다)에서 KMM 이 절점을 NID 0 하나로 뭉쳐 읽는다. 솔리드 출력기는 그 요소들을 '출력 실패 — 스킵'
으로 건너뛰고 rc 0 으로 끝났다 — 조용한 요소 소실. 이제 건너뛴 요소가 하나라도 있으면 🔴 + 종료 코드 3 이다.
"""
import os
import re
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
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def deck(nid_width, bad_node=None):
    """육면체 3개(x 로 붙임). nid_width 10 이면 merge 예제처럼 NID 를 10칸에 쓴다. bad_node 면 요소 3 이 없는 절점을 가리킨다."""
    pts = [(x, y, z) for z in (0, 1) for y in (0, 1) for x in range(4)]
    if nid_width == 8:
        nodes = "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(pts))
    else:
        nodes = "".join(f"{i + 1:>10}{float(x):>10.1f}{float(y):>10.1f}{float(z):>10.1f}\n" for i, (x, y, z) in enumerate(pts))
    elems = []
    for k in range(3):
        n = [k + 1, k + 2, k + 6, k + 5, k + 9, k + 10, k + 14, k + 13]
        if bad_node and k == 2:
            n[0] = bad_node
        elems.append(f"{k + 1:8d}{1:8d}" + "".join(f"{v:8d}" for v in n))
    return ("*KEYWORD\n*NODE\n" + nodes + "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1)
            + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*ELEMENT_SOLID\n" + "\n".join(elems) + "\n*END\n")


def solid_eids(text):
    eids, inside = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith("*ELEMENT_SOLID")
            continue
        if inside and ln.strip() and not ln.startswith("$"):
            eids.append(int(ln[:8]))
    return eids


def run(d, text):
    d.mkdir()
    (d / "model.k").write_text(text)
    (d / "opt.txt").write_text(OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    out = d / "model_trans.k"
    return r, (out.read_text(errors="replace") if out.exists() else None), r.stdout + r.stderr


def main():
    base = Path(tempfile.mkdtemp(prefix="elemloss_"))
    r, out, log = run(base / "ok8", deck(8))
    check("표준 8칸 *NODE: rc 0", r.returncode == 0, log[-600:])
    check("표준 8칸 *NODE: 요소 3개 그대로", out is not None and solid_eids(out) == [1, 2, 3], str(out and solid_eids(out)))
    check("표준 8칸 *NODE: 요소 소실 알림 없음", "요소 소실" not in log, log[-600:])

    r, out, log = run(base / "nid10", deck(10))
    check("NID 10칸 *NODE(merge 예제 꼴): 종료 코드 3", r.returncode == 3, f"rc={r.returncode} " + log[-800:])
    check("NID 10칸 *NODE: 🔴 요소 소실 요약(3개)", re.search(r"🔴 요소 소실.*3개", log) is not None, log[-800:])
    check("NID 10칸 *NODE: 흔한 원인(*NODE 고정폭) 안내", "*NODE" in log and "고정폭" in log, log[-800:])
    check("NID 10칸 *NODE: 진단용 출력 .k 는 남는다", out is not None, "")

    r, out, log = run(base / "missing_node", deck(8, bad_node=999))
    check("없는 절점을 가리키는 요소 1개: 종료 코드 3", r.returncode == 3, f"rc={r.returncode} " + log[-800:])
    check("없는 절점: 🔴 요약에 EID 3·1개", re.search(r"🔴 요소 소실.*1개", log) is not None and "3" in log, log[-800:])
    check("없는 절점: 나머지 요소 1·2 는 출력", out is not None and solid_eids(out) == [1, 2], str(out and solid_eids(out)))

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
