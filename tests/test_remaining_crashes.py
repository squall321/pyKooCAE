#!/usr/bin/env python3
# 남은 결함 묶음 U6 판정 — 올바른 입력에서 죽던 것(빔 끝 빈 줄·PART_VALIDATION_SPLIT·속도 키·인클루드·원통 DWI·Slack 표본)을 작은 덱으로 본다
"""남은 결함 묶음(docs/kmm_kcr_remaining_20261121) B1~B6·A15.

  [B1] *ELEMENT_BEAM 끝 빈 줄 → 예전 int('') ValueError(rc 1). 이제 알리고 건너뛴다(rc 0, 요소 그대로)
  [B2] PART_VALIDATION_SPLIT 솔리드 파트 → 예전 AttributeError(rc 1). 파트 덱에 파트의 재료도 들어간다(예전엔 빈 글이라 빠졌다)
  [B3] DROP_ATTITUDE 에 처음 속도·각속도 키가 없으면 → 예전 KeyError(rc 1). 이제 0(정지 낙하)
  [B4] 읽기 권한 없는 *INCLUDE → 예전 PermissionError 트레이스백. 이제 🔴 원인 + 종료 코드 1(트레이스백 없음)
  [A15] 없는 *INCLUDE → 예전 경고 한 줄 뒤 *INCLUDE 줄까지 출력에서 사라졌다. 이제 🔴 + 주 출력에 *INCLUDE 줄 원문(rc 0)
  [B5] 파트 지정 원통 DWI(2단·4값) → 예전 NameError(rc 1). 이제 덱을 쓴다
  [B6] PART_EXCHANGE SolidwithSlack: 통계 표본이 걸러지면 그만큼 모자랐다(3개 요청 → 1개). 빠진 줄은 KeyError·IndexError.
       이제 요청 수만큼 만들고, 없는 줄은 기본값(*NumberofElements 100, 구속 없음)이거나 원인 + 종료 코드 1

실행: venv312/bin/python tests/test_remaining_crashes.py (KMM 약 15회, 1~3분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다
import test_v131_modes as M    # noqa: E402

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-104s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def b1():
    print("[B1] *ELEMENT_BEAM 끝 빈 줄")
    pts = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0)}
    deck = ("*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_BEAM\n" + f"{1:8d}{1:8d}{1:8d}{2:8d}{3:8d}\n" + "\n"
            + R.part(1, 1, 1, "beam") + "*SECTION_BEAM\n" + f10(1, 1, 1.0, 2) + f10(1.0, 1.0, 0.0, 0.0) + R.ELASTIC + "*END\n")
    d, rc, log = R.run("cr_b1", {"model.k": deck})
    beams = R.elements(R.read(d, "model_trans.k"), "*ELEMENT_BEAM")
    check("[B1] rc 0·Traceback 없음, 빔 EID 1 그대로, 빈 줄 알림", rc == 0 and R.no_tb(log) and 1 in beams and "빈 줄" in log,
          f"rc={rc} {beams} " + log[-300:])


VSPLIT = ("*Inputfile\nmodel.k\n*Mode\nPART_VALIDATION_SPLIT,1\n**PartValidationSplit,1\n*Height,100.0\n*tFinal,0.0005\n*Dt,1e-05\n"
          "*OutputDir,validation_output\n*MinElements,1\n**End\n*End\n")


def b2():
    print("[B2] PART_VALIDATION_SPLIT 솔리드 파트")
    d, rc, log = R.run("cr_b2", {"model.k": R.cube_deck(n=3)}, VSPLIT)
    p = Path(d) / "validation_output" / "Part_000001.k"
    t = p.read_text(errors="replace") if p.exists() else ""
    mats = [b for b in R.kw_blocks(t, "*MAT_ELASTIC_TITLE") + R.kw_blocks(t, "*MAT_ELASTIC")]
    mids = {R.try_(lambda: int(rows[-1][:10])) for _, rows in mats if rows}
    check("[B2] rc 0, Part_000001.k 에 파트 재료(MID 1)·단면이 있다", rc == 0 and p.exists() and 1 in mids and "*SECTION_SOLID" in t,
          f"rc={rc} mids={mids} " + log[-300:])


def b3():
    print("[B3] DROP_ATTITUDE — 처음 속도·각속도 키 없음")
    opt = ("*Inputfile\nmodel.k\n*Mode\nDROP_ATTITUDE,1\n**DropAttitude,1\nEulerRolling,0\nEulerPitching,0\nEulerYawing,0\nHeight,100\n"
           "OffsetDistance,0.05\nDensity,7.85e-9\nYoungsModulus,2.0e5\nPoissonRatio,0.3\ntFinal,0.001\ndt,1e-5\n**EndDropAttitude\n*End\n")
    d, rc, log = R.run("cr_b3", {"model.k": R.cube_deck()}, opt)
    t = R.read(d, "model_drop.k")
    check("[B3] rc 0·Traceback 없음, 낙하 덱이 있다(*INITIAL_VELOCITY)", rc == 0 and R.no_tb(log) and "*INITIAL_VELOCITY" in t,
          f"rc={rc} " + log[-300:])


def b4_a15():
    print("[B4·A15] *INCLUDE — 읽기 권한 없음·없는 파일")
    d, rc, log = R.run("cr_a15", {"model.k": R.cube_deck("*INCLUDE\nlib/missing_mat.k\n")})
    t = R.read(d, "model_trans.k")
    check("[A15] 없는 인클루드: rc 0, 🔴 알림, 주 출력에 *INCLUDE 줄 원문(lib/missing_mat.k)", rc == 0 and "🔴" in log
          and "lib/missing_mat.k" in t, f"rc={rc} " + log[-300:])
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="cr_b4_", dir=os.environ.get("V131_TMP") or None))
    inc = tmp / "locked.k"
    inc.write_text("*MAT_ELASTIC\n" + f10(9, "7.85E-09", 210000.0, 0.3))
    os.chmod(inc, 0)
    try:
        if os.access(inc, os.R_OK):   # root 로 돌면 권한이 막지 못한다 — 판정할 수 없다
            print("  (읽기 권한을 막을 수 없는 계정 — B4 건너뜀)")
            return
        d, rc, log = R.run("cr_b4", {"model.k": R.cube_deck(f"*INCLUDE\n{inc}\n")})
        check("[B4] 읽을 수 없는 인클루드: 🔴 원인 + 종료 코드 1, Traceback 없음", rc == 1 and "🔴" in log and R.no_tb(log),
              f"rc={rc} " + log[-300:])
    finally:
        os.chmod(inc, 0o644)


DWIP = ("*Inputfile\nmodel.k\n*Mode\nDROP_WEIGHT_IMPACT_TEST,1\n**DropWeightImpactTest,1\nGenerationMode,Part\nPartIDs,1\n"
        "LocationMode,2X1\nHeight,100\nInitialVelocityX,0\nInitialVelocityY,0\nInitialVelocityZ,0\nGravity,9810\n"
        "ImpactorType,Cylinder\nImpactorDimension,{dim}\nMeshSize,0.25\nTFinal,0.0001\nDT,1e-05\nOffsetDistance,0.05\n"
        "**EndDropWeightImpactTest\n*End\n")


def b5():
    print("[B5] 파트 지정 원통 DWI")
    for label, dim in (("2단", "0.5,0.6,0.3,0.3,0.6"), ("4값", "0.5,0.6,0.3,0.3")):
        d, rc, log = R.run("cr_b5", {"model.k": M.base_deck(raw=True)}, DWIP.format(dim=dim))
        outs = sorted(Path(d).glob("model_MODE_DWIP_CYL_*.k"))
        check(f"[B5] 원통 {label}: rc 0·Traceback 없음, 위치 둘의 덱", rc == 0 and R.no_tb(log) and len(outs) == 2,
              f"rc={rc} {[p.name for p in outs]} " + log[-300:])


def slack_deck():
    """파트 1 = x 방향 육면체 다섯 기둥, 파트 2 = 위쪽 판 하나."""
    pts, col, nid = {}, {}, 1
    for i in range(6):
        for (y, z) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            pts[nid] = (float(i), float(y), float(z))
            col[(i, y, z)] = nid
            nid += 1
    rows = []
    for e in range(5):
        n = [col[(e, 0, 0)], col[(e + 1, 0, 0)], col[(e + 1, 1, 0)], col[(e, 1, 0)], col[(e, 0, 1)], col[(e + 1, 0, 1)],
             col[(e + 1, 1, 1)], col[(e, 1, 1)]]
        rows.append(f"{e + 1:8d}{1:8d}" + "".join(f"{x:8d}" for x in n) + "\n")
    for k, (x, y, z) in enumerate(((-1, -1, 3), (6, -1, 3), (6, 2, 3), (-1, 2, 3), (-1, -1, 3.5), (6, -1, 3.5), (6, 2, 3.5), (-1, 2, 3.5))):
        pts[100 + k] = (float(x), float(y), float(z))
    rows.append(f"{10:8d}{2:8d}" + "".join(f"{100 + k:8d}" for k in range(8)) + "\n")
    return "*KEYWORD\n" + R.node_block(pts) + "*ELEMENT_SOLID\n" + "".join(rows) + R.part(1) + R.part(2) + R.SOLID1 + R.ELASTIC + "*END\n"


def slack_opt(extra):
    return ("*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,1\n*ConvertHexaTo,(SolidwithSlack,1,0,0,10,0,0,1)\n"
            + extra + "**End\n*End\n")


def b6():
    print("[B6] SolidwithSlack — 표본 수·빠진 줄")
    cases = [
        ("표본 1 + 통계 3(좁은 범위 1.19~1.21) → 덱 4개", "*DesiredLengthRatioSamples,1.05\n*DesiredLengthRatioStatistics,3,1.2,0.2,1.19,1.21\n"
         "*ConstraintPIDs,2\n*NumberofElements,10\n", 0, 4),
        ("*NumberofElements 없음 → 기본 100, 덱 1개", "*DesiredLengthRatioSamples,1.05\n*ConstraintPIDs,2\n", 0, 1),
        ("*ConstraintPIDs 없음 → 구속 없이 덱 1개", "*DesiredLengthRatioSamples,1.05\n*NumberofElements,10\n", 0, 1),
        ("*NumberofElements 1 → 🔴 종료 코드 1", "*DesiredLengthRatioSamples,1.05\n*ConstraintPIDs,2\n*NumberofElements,1\n", 1, 0),
        ("표본·통계 둘 다 없음 → 🔴 종료 코드 1", "*ConstraintPIDs,2\n*NumberofElements,10\n", 1, 0),
        ("뽑을 수 없는 통계(표준편차 0 으로 둘) → 🔴 종료 코드 1", "*DesiredLengthRatioStatistics,2,1.2,0.0,1.19,1.21\n*NumberofElements,10\n", 1, 0),
    ]
    for label, extra, want_rc, want_n in cases:
        d, rc, log = R.run("cr_b6", {"model.k": slack_deck()}, slack_opt(extra))
        outs = sorted(Path(d).glob("model_SolidWithSlack_*.k"))
        loud = want_rc == 0 or ("🔴" in log and R.no_tb(log))
        check(f"[B6] {label}", rc == want_rc and len(outs) == want_n and loud, f"rc={rc} n={len(outs)} " + log[-300:])


if __name__ == "__main__":
    for f in (b1, b2, b3, b4_a15, b5, b6):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:500])
    sys.exit(1 if FAILS else 0)
