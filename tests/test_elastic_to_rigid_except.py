# ELASTIC_TO_RIGID + *PIDExcept 재질 소실 회귀 시험 — 제외 파트 재질 보존·공유 MID 분리·제외 없음 바이트 동일
"""
실행: venv312/bin/python tests/test_elastic_to_rigid_except.py   (KMM 4회, 약 1분)

예전 동작(2026-10-13 smarttwin-mcp e2e 로 발견): ExchangetoRigid 가 재질 표를 '제외되지 않은 재질의 강체 사본'
으로 통째로 바꿔서
  - 제외 파트의 재질이 출력에서 사라졌고(separate_exc),
  - 제외 파트와 MID 를 같이 쓰는 파트는 강체화도 보존도 안 돼 재질이 하나도 남지 않았다(shared_exc).
두 경우 모두 덱이 없는 MID 를 참조해 LS-DYNA 가 입력 단계에서 죽는다. 제외가 없는 경로는 바뀌면 안 된다.
"""
import os
import re
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


SHARED = """*KEYWORD
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
*END
"""
# 파트 2 가 따로 MID 16 을 쓰는 판
SEPARATE = SHARED.replace(
    "         2         1        15         0         0         0         0         0",
    "         2         1        16         0         0         0         0         0").replace(
    "*END\n", "*MAT_VISCOELASTIC_TITLE\nEpoxy2\n        161.30000E-9 64.444000 48.333000 15.1040002500.00000\n*END\n")


def run(work: Path, deck: str, except_line: str) -> str:
    (work / "model.k").write_text(deck)
    (work / "opt.txt").write_text("*Inputfile\nmodel.k\n*Mode\nELASTIC_TO_RIGID,1\n**ElastictoRigid,1\n"
                                  + except_line + "**EndElastictoRigid\n*End\n")
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=work,
                       capture_output=True, text=True, timeout=600)
    out = work / "model_etor.k"
    assert out.exists(), r.stdout[-2000:] + r.stderr[-2000:]
    return out.read_text()


def mats_and_parts(deck: str):
    t = deck.splitlines()
    mats, parts = {}, {}
    for i, line in enumerate(t):
        if line.startswith("*MAT"):
            j = i + 1 + (1 if line.endswith("_TITLE") else 0)
            while t[j].startswith("$"):
                j += 1
            mats[int(t[j][:10])] = line
        if line.startswith("*PART"):
            j = i + 2
            while t[j].startswith("$"):
                j += 1
            parts[int(t[j][:10])] = int(t[j][20:30])
    return mats, parts


def main():
    base = Path("/data/koopark") if Path("/data/koopark").is_dir() else None
    tmp = Path(tempfile.mkdtemp(prefix="test_etor_", dir=base))
    results = {}
    for name, deck, exc in (("shared_all", SHARED, ""), ("shared_exc", SHARED, "*PIDExcept,2\n"),
                            ("separate_all", SEPARATE, ""), ("separate_exc", SEPARATE, "*PIDExcept,2\n")):
        w = tmp / name
        w.mkdir()
        results[name] = run(w, deck, exc)

    print("=== 제외 없음 — 모든 파트 강체")
    for name in ("shared_all", "separate_all"):
        mats, parts = mats_and_parts(results[name])
        check(f"{name}: 모든 재질이 MAT_RIGID", all("RIGID" in k for k in mats.values()), str(mats))
        check(f"{name}: 파트 MID 가 전부 정의됨", set(parts.values()) <= set(mats), f"{parts} {mats}")

    print("=== 제외 있음 — 제외 파트 재질 보존")
    mats, parts = mats_and_parts(results["separate_exc"])
    check("separate_exc: 파트 2 의 MID 16 이 남아 있다", 16 in mats, str(mats))
    check("separate_exc: MID 16 은 원래 재질(VISCOELASTIC)", "VISCOELASTIC" in mats.get(16, ""), str(mats))
    check("separate_exc: 파트 1 의 MID 15 는 강체", "RIGID" in mats.get(15, ""), str(mats))
    check("separate_exc: 참조 누락 0", set(parts.values()) <= set(mats), f"{parts} {mats}")

    mats, parts = mats_and_parts(results["shared_exc"])
    check("shared_exc: 제외 파트 2 는 원래 MID 15 그대로", parts.get(2) == 15, str(parts))
    check("shared_exc: MID 15 는 원래 재질(VISCOELASTIC)", "VISCOELASTIC" in mats.get(15, ""), str(mats))
    check("shared_exc: 파트 1 은 새 MID 로 분리", parts.get(1) not in (None, 15), str(parts))
    check("shared_exc: 파트 1 의 새 MID 는 강체", "RIGID" in mats.get(parts.get(1), ""), str(mats))
    check("shared_exc: 참조 누락 0", set(parts.values()) <= set(mats), f"{parts} {mats}")

    print()
    if FAILS:
        print("FAIL %d:" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        print("work:", tmp)
        sys.exit(1)
    print("ALL OK  (work: %s)" % tmp)


if __name__ == "__main__":
    main()
