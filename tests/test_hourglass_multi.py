# *HOURGLASS 가 첫 줄 하나만 보존되던 결함의 회귀 시험
"""
실행: venv312/bin/python tests/test_hourglass_multi.py

*HOURGLASS 는 파트별 hourglass 제어 카드다(*PART 의 HGID 가 참조).
예전에는 hourglassKeywords[0][0] 로 첫 블록 첫 줄만 읽어 HGID 1 외 전부가
경고 없이 사라졌고, write 도 parameters[0] 하나만 썼다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "occProject" / "Generators"))

FAILS = []


def check(name, cond, detail=""):
    print("  %-64s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def main():
    from KooCAEManager.KooDynaKeyword import Hourglass
    from KooCAEManager.KooDynaAdditional import KooDynaAdditionalManager

    # 한 블록 3줄 + 별도 블록 1줄 = HGID 4개
    blocks = [
        ["         1         5     0.100         0       1.5      0.06                    ",
         "         2         4     0.200         0       1.5      0.06                    ",
         "         3         6     0.300         0       1.5      0.06                    "],
        ["         4         1     0.400         0       1.5      0.06                    "],
    ]

    print("=== 파싱 — 전 블록·전 줄")
    hg = Hourglass()
    hg.parse(blocks)
    check("4개 파싱", len(hg.parameters) == 4, str(len(hg.parameters)))
    hgids = [p[0].strip() for p in hg.parameters]
    check("HGID 1,2,3,4 순서 보존", hgids == ["1", "2", "3", "4"], str(hgids))
    ihqs = [p[1].strip() for p in hg.parameters]
    check("IHQ 5,4,6,1 보존", ihqs == ["5", "4", "6", "1"], str(ihqs))

    print("=== 빈 줄은 건너뛴다")
    hg2 = Hourglass()
    hg2.parse([["         7         5     0.100         0       1.5      0.06", "   ", ""]])
    check("빈 줄 제외하고 1개", len(hg2.parameters) == 1, str(len(hg2.parameters)))

    print("=== getHourglass — 매니저로 전부 전달")
    items = hg.getHourglass()
    check("4개 전달", len(items) == 4, str(len(items)))
    check("각 항목이 *HOURGLASS 키워드", all(i[0] == "*HOURGLASS" for i in items))

    print("=== 매니저 등록 — HGID 별로 전부 남는다")
    mgr = KooDynaAdditionalManager()
    for item in items:
        mgr.SetAdditionalfromDyna(item)
    check("hourglasses 4개", len(mgr.hourglasses) == 4, str(sorted(mgr.hourglasses)))
    check("HGID 키 1,2,3,4", sorted(mgr.hourglasses) == [1, 2, 3, 4], str(sorted(mgr.hourglasses)))
    for hgid, ihq, qm in ((1, 5, 0.1), (2, 4, 0.2), (3, 6, 0.3), (4, 1, 0.4)):
        o = mgr.hourglasses.get(hgid)
        check(f"HGID {hgid}: IHQ={ihq} QM={qm}",
              o is not None and o.IHQ == ihq and abs(o.QM - qm) < 1e-9,
              f"{getattr(o,'IHQ',None)}/{getattr(o,'QM',None)}")

    print("=== 출력 — 전 항목이 덱에 실린다")
    kw = mgr.WritetoDynaKeyword()
    check("*HOURGLASS 4블록", kw.count("*HOURGLASS") == 4, str(kw.count("*HOURGLASS")))
    for hgid in ("1", "2", "3", "4"):
        check(f"HGID {hgid} 출력됨",
              any(l.split() and l.split()[0] == hgid
                  for l in kw.splitlines() if not l.startswith(("*", "$"))))

    print("=== 소스 불변식")
    SRC = (ROOT / "occProject" / "Generators" / "KooCAEManager"
           / "KooDynaKeyword.py").read_text(encoding="utf-8")
    check("첫줄만 읽는 코드 제거",
          "self.parse_whole(hourglassKeywords[0][0]" not in SRC)
    check("parameters[0] 만 쓰는 코드 제거",
          "for j in range(len(self.parameters[0])):" not in SRC)
    check("개수 불변식 로그 존재", "*HOURGLASS 개수 불일치" in SRC)

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
