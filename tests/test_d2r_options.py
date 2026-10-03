# DEFORMABLE_TO_RIGID_AUTOMATIC 세부 옵션 개방 회귀 시험
"""
실행: venv312/bin/python tests/test_d2r_options.py

검증
  A 기본값 — 세부 옵션 미지정 시 예전 리터럴(0.0/1e20/0.0, 0/0/0/0.0) 그대로 (회귀 0)
  B 전필드 지정 — 8개 값이 두 카드 모두에 반영
  C 부분 지정 — 준 것만 바뀌고 나머지는 기본값
  D 🔴 순서 함정 — D2R* 키가 있어도 DeformableToRigid 가 True 로 유지된다
  E 러너 — bool 형태 출력 불변 / dict 형태가 D2R* 줄 방출
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "occProject" / "Generators"))

FAILS = []


def check(name, cond, detail=""):
    print("  %-64s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def card_fields(kw_text):
    """WriteDynaKeyword 출력에서 card1/card2 숫자 필드를 뽑는다 ($ 주석 제외)."""
    rows = [ln for ln in kw_text.splitlines()
            if ln.strip() and not ln.startswith("*") and not ln.lstrip().startswith("$")]
    return [r.split() for r in rows]


def main():
    from KooCAEManager.KooDynaAdditional import KooDynaAdditionalManager as KooAdditionalManager

    print("=== A 기본값 (세부 미지정) — 예전 리터럴과 동일해야 한다")
    mgr = KooAdditionalManager()
    d = mgr.CreateDeformableToRigidAutomatic(
        swset=20, code=4, entno=1, relsw=10, paired=1,
        d2r_pids=[(1, 0)], r2d_pids=[])
    check("time1=0.0", d.time1 == 0.0, str(d.time1))
    check("time2=1e20", d.time2 == 1e20, str(d.time2))
    check("time3=0.0", d.time3 == 0.0, str(d.time3))
    check("nrbf=0", d.nrbf == 0, str(d.nrbf))
    check("ncsf=0", d.ncsf == 0, str(d.ncsf))
    check("rwf=0", d.rwf == 0, str(d.rwf))
    check("dtmax=0.0", d.dtmax == 0.0, str(d.dtmax))
    check("offset=0.0", d.offset == 0.0, str(d.offset))
    base_kw = d.WriteDynaKeyword()

    print("=== B 전필드 지정 — 값이 그대로 반영")
    mgr2 = KooAdditionalManager()
    d2 = mgr2.CreateDeformableToRigidAutomatic(
        swset=20, code=4, entno=7, relsw=10, paired=1,
        d2r_pids=[(1, 0)], r2d_pids=[],
        time1=1e-4, time2=5e-3, time3=2e-4,
        nrbf=1, ncsf=2, rwf=3, dtmax=1e-7, offset=0.5)
    for name, got, want in (("time1", d2.time1, 1e-4), ("time2", d2.time2, 5e-3),
                            ("time3", d2.time3, 2e-4), ("nrbf", d2.nrbf, 1),
                            ("ncsf", d2.ncsf, 2), ("rwf", d2.rwf, 3),
                            ("dtmax", d2.dtmax, 1e-7), ("offset", d2.offset, 0.5)):
        check(f"{name}={want}", got == want, f"{got}")
    kw2 = d2.WriteDynaKeyword()
    check("카드 출력에 지정값 반영", "5" in kw2 and len(card_fields(kw2)) >= 2)
    check("기본값 카드와 다름 (실제로 바뀜)", kw2 != base_kw)

    print("=== C 부분 지정 — 준 것만 바뀜")
    mgr3 = KooAdditionalManager()
    d3 = mgr3.CreateDeformableToRigidAutomatic(
        swset=10, code=2, entno=3, relsw=20, paired=-1,
        d2r_pids=[], r2d_pids=[1], dtmax=2e-7)
    check("dtmax 만 변경", d3.dtmax == 2e-7, str(d3.dtmax))
    check("time2 는 기본값 유지", d3.time2 == 1e20, str(d3.time2))
    check("nrbf 는 기본값 유지", d3.nrbf == 0, str(d3.nrbf))

    print("=== D 🔴 파서 순서 함정 — D2R* 가 있어도 DeformableToRigid 는 True")
    SRC = (ROOT / "occProject" / "Generators" / "KooMeshModifier.py").read_text(encoding="utf-8")
    i_generic = SRC.index('elif "deformabletorigid" in line.lower():')
    for k in ("d2rtime1", "d2rtime2", "d2rtime3", "d2rnrbf",
              "d2rncsf", "d2rrwf", "d2rdtmax", "d2roffset"):
        i = SRC.index(f'elif "{k}" in line.lower():')
        check(f"{k} 분기가 generic 보다 앞", i < i_generic, f"{i} vs {i_generic}")
    check("DropAttitude 의 dt 분기는 정확일치 (D2RDtmax 안전)",
          'line.split(",")[0].strip().lower() == "dt"' in SRC)

    print("=== E 러너 — bool 불변 / dict 방출")
    from Runner.StepConfigBuilder import build_drop_attitude_config as _probe  # noqa: F401
    SB = (ROOT / "Runner" / "StepConfigBuilder.py").read_text(encoding="utf-8")
    check("bool True 는 DeformableToRigid,True 한 줄", 'd2r_line = "\\nDeformableToRigid,True"' in SB)
    check("dict 분기 존재", "isinstance(d2r_raw, dict)" in SB)
    check("8개 키 매핑 존재", SB.count("D2RTime1") >= 1 and SB.count("D2ROffset") >= 1)
    check("swset/code/relsw/paired 는 노출 안 함",
          "D2RSwset" not in SB and "D2RCode" not in SB)

    print("=== F 🔴 포맷 정밀도 — 작은 값이 0.0 으로 사라지지 않는다")
    from KooCAEManager.KooDynaAdditional import _d2r_num
    check("0.0 은 기존 출력 유지", _d2r_num(0.0) == format(0.0, ">10.1f"), repr(_d2r_num(0.0)))
    check("1e20 은 기존 출력 유지", _d2r_num(1e20) == "   1.0e+20", repr(_d2r_num(1e20)))
    for v in (1e-7, 1e-4, 2e-4, 5e-3):
        out = _d2r_num(v)
        check(f"{v:g} 이 0.0 으로 사라지지 않음",
              float(out) == v, f"{out!r} -> {float(out)}")
        check(f"{v:g} 출력 폭 10칸", len(out) == 10, f"{len(out)}")
    check("0.5 는 고정소수점 유지", _d2r_num(0.5).strip() == "0.5", repr(_d2r_num(0.5)))

    # 카드 전체 출력에 실제로 실리는지
    mgr4 = KooAdditionalManager()
    d4 = mgr4.CreateDeformableToRigidAutomatic(
        swset=20, code=4, entno=1, relsw=10, paired=1,
        d2r_pids=[(1, 0)], r2d_pids=[],
        time1=1e-4, time3=2e-4, dtmax=1e-7, offset=0.5)
    kw4 = d4.WriteDynaKeyword()
    for token in ("1.0e-04", "2.0e-04", "1.0e-07"):
        check(f"카드에 {token} 기재", token in kw4, kw4.splitlines()[2] if len(kw4.splitlines()) > 2 else "")
    rows = card_fields(kw4)
    check("card1 필드 8개", len(rows[0]) == 8, str(rows[0]))
    check("card2 필드 7개", len(rows[1]) == 7, str(rows[1]))

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
