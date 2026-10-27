# 요소가 빠지면(읽기에서 버리거나 내보내기에서 못 쓰면) KMM 이 🔴 요약과 종료 코드 3 으로 끝나는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_export_element_loss.py
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-10-26 사용자 결정 "요소 소실 시 비 0 종료"): *NODE 가 LS-DYNA 고정폭(NID 8칸)이 아닌 덱(KooRemapper merge
예제는 NID 를 10칸에 쓴다)에서 KMM 이 절점을 NID 0 하나로 뭉쳐 읽는다. 솔리드 출력기는 그 요소들을 '출력 실패 — 스킵'
으로 건너뛰고 rc 0 으로 끝났다 — 조용한 요소 소실. 리뷰 R(10-27): 읽기에서 버린 요소(PID 에 *PART 가 없음·10절점 코너
절점 0·질량 요소의 절점 없음)도 rc 0 이었고, 셸이 없는 절점을 가리키면 트레이스백(rc 1)이었다. 이제 모두 🔴 + 종료 코드 3.
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
PTS = [(x, y, z) for z in (0, 1) for y in (0, 1) for x in range(4)]


def check(name, cond, detail=""):
    print("  %-72s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def nodes8():
    return "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(PTS))


PROPS = "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)


def deck(nid_width, bad_node=None, bad_pid=None):
    """육면체 3개(x 로 붙임). nid_width 10 이면 merge 예제처럼 NID 를 10칸에 쓴다. bad_node/bad_pid 면 요소 3 이 없는 절점/파트를 가리킨다."""
    if nid_width == 8:
        nodes = nodes8()
    else:
        nodes = "*NODE\n" + "".join(f"{i + 1:>10}{float(x):>10.1f}{float(y):>10.1f}{float(z):>10.1f}\n" for i, (x, y, z) in enumerate(PTS))
    elems = []
    for k in range(3):
        n = [k + 1, k + 2, k + 6, k + 5, k + 9, k + 10, k + 14, k + 13]
        if bad_node and k == 2:
            n[0] = bad_node
        pid = bad_pid if (bad_pid and k == 2) else 1
        elems.append(f"{k + 1:8d}{pid:8d}" + "".join(f"{v:8d}" for v in n))
    return "*KEYWORD\n" + nodes + PROPS + "*ELEMENT_SOLID\n" + "\n".join(elems) + "\n*END\n"


def shell_deck(bad_pid=None, bad_node=None):
    """셸 2개(z=0 면·z=1 면). 셸 102 가 없는 파트(bad_pid)나 없는 절점(bad_node)을 가리킨다."""
    sh = ("*PART\nskin\n" + f10(2, 2, 1) + "*SECTION_SHELL\n" + f10(2, 2) + f10(1.0, 1.0, 1.0, 1.0)
          + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))
    n2 = [9, 10, 14, bad_node or 13]
    rows = [f"{101:8d}{2:8d}" + "".join(f"{v:8d}" for v in (1, 2, 6, 5)),
            f"{102:8d}{bad_pid or 2:8d}" + "".join(f"{v:8d}" for v in n2)]
    return "*KEYWORD\n" + nodes8() + sh + "*ELEMENT_SHELL\n" + "\n".join(rows) + "\n*END\n"


def tennode_deck():
    """ten nodes format 솔리드 2개 — 요소 2 의 코너 절점 하나가 0(유효 솔리드 아님, 읽기에서 버린다)."""
    return ("*KEYWORD\n" + nodes8() + PROPS + "*ELEMENT_SOLID (ten nodes format)\n"
            + f"{1:8d}{1:8d}\n" + "".join(f"{v:8d}" for v in (1, 2, 6, 9, 0, 0, 0, 0, 0, 0)) + "\n"
            + f"{2:8d}{1:8d}\n" + "".join(f"{v:8d}" for v in (2, 3, 0, 10, 0, 0, 0, 0, 0, 0)) + "\n*END\n")


def mass_deck():
    """솔리드 1개 + 질량 요소 2개 — 질량 요소 902 는 없는 절점 999 에 붙어 있다."""
    el = f"{1:8d}{1:8d}" + "".join(f"{v:8d}" for v in (1, 2, 6, 5, 9, 10, 14, 13))
    mass = f"{901:8d}{1:8d}{1.0e-3:16.8e}{1:8d}\n{902:8d}{999:8d}{1.0e-3:16.8e}{1:8d}\n"
    return "*KEYWORD\n" + nodes8() + PROPS + "*ELEMENT_SOLID\n" + el + "\n*ELEMENT_MASS\n" + mass + "*END\n"


def eids_of(text, kw, width=8):
    eids, inside = [], False
    for ln in text.splitlines():
        if ln.startswith("*"):
            inside = ln.upper().startswith(kw)
            continue
        if inside and ln.strip() and not ln.startswith("$"):
            eids.append(int(ln[:width]))
    return eids


def run(d, text):
    d.mkdir()
    (d / "model.k").write_text(text)
    (d / "opt.txt").write_text(OPT)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=600, env=ENV)
    out = d / "model_trans.k"
    return r, (out.read_text(errors="replace") if out.exists() else None), r.stdout + r.stderr


def lost(name, r, log, stage, count, hint):
    check(f"{name}: 종료 코드 3", r.returncode == 3, f"rc={r.returncode} " + log[-800:])
    check(f"{name}: 🔴 요소 소실({stage}) {count}", re.search(rf"🔴 요소 소실: {stage}.*{count}", log) is not None, log[-800:])
    check(f"{name}: 원인 안내({hint})", hint in log, log[-800:])


def main():
    base = Path(tempfile.mkdtemp(prefix="elemloss_"))
    r, out, log = run(base / "ok8", deck(8))
    check("표준 8칸 *NODE: rc 0", r.returncode == 0, log[-600:])
    check("표준 8칸 *NODE: 요소 3개 그대로", out is not None and eids_of(out, "*ELEMENT_SOLID") == [1, 2, 3], str(out and eids_of(out, "*ELEMENT_SOLID")))
    check("표준 8칸 *NODE: 요소 소실 알림 없음", "요소 소실" not in log, log[-600:])

    r, out, log = run(base / "nid10", deck(10))
    lost("NID 10칸 *NODE(merge 예제 꼴)", r, log, "내보내기", "3건", "고정폭")
    check("NID 10칸 *NODE: 진단용 출력 .k 는 남는다", out is not None, "")

    r, out, log = run(base / "missing_node", deck(8, bad_node=999))
    lost("없는 절점을 가리키는 솔리드 1개", r, log, "내보내기", "1건", "고정폭")
    check("없는 절점: 나머지 요소 1·2 는 출력", out is not None and eids_of(out, "*ELEMENT_SOLID") == [1, 2], str(out and eids_of(out, "*ELEMENT_SOLID")))

    r, out, log = run(base / "pid_missing", deck(8, bad_pid=7))
    lost("*PART 없는 PID 의 솔리드 1개", r, log, "읽기", "1개", "*PART")
    check("PID 미존재: 나머지 요소 1·2 는 출력", out is not None and eids_of(out, "*ELEMENT_SOLID") == [1, 2], str(out and eids_of(out, "*ELEMENT_SOLID")))

    r, out, log = run(base / "shell_pid_missing", shell_deck(bad_pid=9))
    lost("*PART 없는 PID 의 셸 1개", r, log, "읽기", "1개", "*PART")
    check("셸 PID 미존재: 셸 101 은 출력", out is not None and eids_of(out, "*ELEMENT_SHELL") == [101], str(out and eids_of(out, "*ELEMENT_SHELL")))

    r, out, log = run(base / "shell_missing_node", shell_deck(bad_node=999))
    lost("없는 절점을 가리키는 셸 1개(예전엔 트레이스백)", r, log, "내보내기", "1건", "고정폭")
    check("셸 없는 절점: 셸 101 은 출력", out is not None and eids_of(out, "*ELEMENT_SHELL") == [101], str(out and eids_of(out, "*ELEMENT_SHELL")))

    r, out, log = run(base / "tennode_corner0", tennode_deck())
    lost("ten nodes format 코너 절점 0 인 솔리드 1개", r, log, "읽기", "1개", "코너")

    r, out, log = run(base / "mass_missing_node", mass_deck())
    lost("없는 절점에 붙은 질량 요소 1개", r, log, "읽기", "1개", "절점")
    check("질량 요소 901 은 출력", out is not None and eids_of(out, "*ELEMENT_MASS") == [901], str(out and eids_of(out, "*ELEMENT_MASS")))

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
