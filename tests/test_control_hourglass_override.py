# 입력 덱에 *CONTROL_HOURGLASS 가 있으면 옵션이 경고 없이 무시되던 것의 회귀 시험
"""
실행: venv312/bin/python tests/test_control_hourglass_override.py

검증
  1 옵션 지정 + 덱에 카드 있음 → 옵션이 이긴다 + 변경 알림
  2 옵션 미지정 + 덱에 카드 있음 → 덱 값 유지 (회귀 0)
  3 덱에 카드 없음 → 옵션값, 없으면 기본 5/0.1
  4 소스 불변식 — controlTermination 과 같은 패턴(옵션 우선)이고 Force 류 플래그가 없다
  5 파서는 점 표기를 요구한다 (ControlHourglass.IHQ,5)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "occProject" / "Generators"))

FAILS = []


def check(name, cond, detail=""):
    print("  %-66s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


SRC = (ROOT / "occProject" / "Generators" / "KooCAEManager"
       / "KooDynaAdvancedModification.py").read_text(encoding="utf-8")
PARSER = (ROOT / "occProject" / "Generators" / "KooMeshModifier.py").read_text(encoding="utf-8")


class _FakeHG:
    def __init__(self, IHQ, QH):
        self.IHQ, self.QH = IHQ, QH


def apply_override(deck_hg, ch):
    """수정된 분기와 동일한 로직을 재현해 결과를 돌려준다."""
    if deck_hg is None:
        return _FakeHG(int(ch.get("IHQ", 5)), ch.get("QH", 0.1)), False
    changed = False
    if ch:
        prev = (deck_hg.IHQ, deck_hg.QH)
        if "IHQ" in ch:
            deck_hg.IHQ = int(ch["IHQ"])
        if "QH" in ch:
            deck_hg.QH = ch["QH"]
        changed = (deck_hg.IHQ, deck_hg.QH) != prev
    return deck_hg, changed


def main():
    print("=== 1 옵션 지정 + 덱에 카드 있음 → 옵션 우선")
    hg, changed = apply_override(_FakeHG(4, 0.05), {"IHQ": 5, "QH": 0.1})
    check("IHQ 5 로 덮어씀", hg.IHQ == 5, str(hg.IHQ))
    check("QH 0.1 로 덮어씀", hg.QH == 0.1, str(hg.QH))
    check("변경 알림 발생", changed)

    print("=== 2 옵션 미지정 + 덱에 카드 있음 → 덱 값 유지 (회귀 0)")
    hg, changed = apply_override(_FakeHG(4, 0.05), {})
    check("IHQ 4 유지", hg.IHQ == 4, str(hg.IHQ))
    check("QH 0.05 유지", hg.QH == 0.05, str(hg.QH))
    check("알림 없음", not changed)

    print("=== 2b 부분 지정 — 준 것만 덮어쓴다")
    hg, changed = apply_override(_FakeHG(4, 0.05), {"IHQ": 6})
    check("IHQ 만 6 으로", hg.IHQ == 6, str(hg.IHQ))
    check("QH 는 덱 값 0.05 유지", hg.QH == 0.05, str(hg.QH))

    print("=== 3 덱에 카드 없음")
    hg, _ = apply_override(None, {})
    check("기본 IHQ=5", hg.IHQ == 5, str(hg.IHQ))
    check("기본 QH=0.1", hg.QH == 0.1, str(hg.QH))
    hg, _ = apply_override(None, {"IHQ": 7, "QH": 0.2})
    check("옵션값 IHQ=7", hg.IHQ == 7, str(hg.IHQ))
    check("옵션값 QH=0.2", hg.QH == 0.2, str(hg.QH))

    print("=== 4 소스 불변식")
    check("elif ch: 분기 존재 (옵션 우선)", "elif ch:" in SRC)
    check("덮어쓸 때 변경 알림 출력", "옵션 값 IHQ=" in SRC)
    check("Force 류 플래그 없음 (불필요한 설정 추가 안 함)",
          "ControlHourglassForce" not in SRC and "HourglassForce" not in PARSER)
    check("controlTermination 은 여전히 덱 값을 덮어쓴다 (일관성)",
          "cm.controlTermination.ENDTIM = tFinal" in SRC)

    print("=== 5 파서는 점 표기를 요구한다")
    check('"controlhourglass." 분기 존재', 'elif "controlhourglass." in line.lower():' in PARSER)
    check("키는 점 뒤에서 뽑는다", 'split(".")[1]' in PARSER)

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
