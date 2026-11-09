#!/usr/bin/env python3
# KMM 리더 크래시 묶음(2026-11-09) 판정 — 실제 덱에서 죽던 빈 칸·Fortran 지수 읽기와 *DATABASE_RBDOUT 소실을 작은 덱으로 본다
"""누적 체인 묶음의 말뭉치 대조에서 고치기 전·후 모두 rc 1 로 죽던 실제 덱 6개에서 나온 결함(docs/kmm_reader_crashes_20261109).

  R1 *INITIAL_VELOCITY 의 NSIDEX 칸이 공백 10자면 int() 로 죽었다.
  R2 *DATABASE_* 의 실수 칸이 '1.0000-06'(E 없는 Fortran 지수)면 float() 로 죽었다. 정수 칸의 '1.0' 도.
  R3 *LOAD_SEGMENT_SET(_ID) 의 빈 SF·AT 칸에서 float('') 로 죽었다(R16 기본값 SF 1.0·AT 0.0).
  R4 *DATABASE_RBDOUT 이 데이터베이스 갈래 조건에서 '*' 가 빠져 해석되지 않고, 해석 표시 때문에 원문으로도 나가지 않았다.

수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v131_review as R   # noqa: E402 — 실행·읽기·덱 조각을 같이 쓴다

FAILS = []
f10 = R.f10


def check(name, cond, detail=""):
    print("  %-100s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def block(t, kw):
    """정확히 kw 인 첫 블록의 데이터 줄(주석·빈 줄 뺌)."""
    b = R.kw_blocks(t, kw)
    return b[0][1] if b else []


NSET = "*SET_NODE_LIST\n" + f10(1) + f10(*range(1, 9))


def r1():
    print("[R1] *INITIAL_VELOCITY — NSIDEX 칸이 공백 10자")
    iv = "*INITIAL_VELOCITY\n" + f"{1:10d}" + " " * 40 + "\n" + f10(100.0, 0.0, -200.0, 0.0, 0.0, 0.0)
    d, rc, log = R.run("rc_r1", {"model.k": R.cube_deck(NSET + iv)})
    t = R.read(d, "model_trans.k")
    rows = block(t, "*INITIAL_VELOCITY")
    v = R.try_(lambda: R.floats(rows[1], 10), [])
    check("R1 rc 0·Traceback 없음, *INITIAL_VELOCITY 의 VX 100·VZ -200 이 그대로", rc == 0 and R.no_tb(log) and len(v) >= 3
          and R.near(v[0], 100.0) and R.near(v[2], -200.0), f"rc={rc} {rows} " + log[-300:])


def r2_r4():
    print("[R2·R4] *DATABASE_* — E 없는 Fortran 지수·정수값 실수, *DATABASE_RBDOUT")
    db = ("*DATABASE_GLSTAT\n" + f"{'1.0000-06':>10}{'1.0':>10}\n"
          + "*DATABASE_BINARY_D3PLOT\n" + f"{'1.0000-04':>10}\n")
    d, rc, log = R.run("rc_r2", {"model.k": R.cube_deck(db)})
    t = R.read(d, "model_trans.k")
    g = R.try_(lambda: R.floats(block(t, "*DATABASE_GLSTAT")[0], 10), [])
    p = R.try_(lambda: R.floats(block(t, "*DATABASE_BINARY_D3PLOT")[0], 10), [])
    check("R2 rc 0·Traceback 없음, GLSTAT DT 1E-6·BINARY 1, D3PLOT DT 1E-4", rc == 0 and R.no_tb(log) and len(g) >= 2
          and R.near(g[0], 1.0e-6) and int(g[1]) == 1 and p and R.near(p[0], 1.0e-4), f"rc={rc} {g} {p} " + log[-300:])
    # R4 는 따로 — R2 크래시와 섞이지 않게(예전엔 rc 0 으로 RBDOUT 만 조용히 빠졌다)
    d, rc, log = R.run("rc_r4", {"model.k": R.cube_deck("*DATABASE_RBDOUT\n" + f10(0.002, 1))})
    t = R.read(d, "model_trans.k")
    r = R.try_(lambda: R.floats(block(t, "*DATABASE_RBDOUT")[0], 10), [])
    check("R4 *DATABASE_RBDOUT(DT 0.002) 이 출력에 남는다", rc == 0 and len(r) >= 1 and R.near(r[0], 0.002), f"rc={rc} rbdout={r}")


def r3():
    print("[R3] *LOAD_SEGMENT_SET(_ID) — 빈 SF·AT")
    seg = "*SET_SEGMENT\n" + f10(5) + f10(5, 6, 7, 8)
    crv = "*DEFINE_CURVE\n" + f10(7) + f"{0.0:20.6f}{0.0:20.6f}\n" + f"{1.0:20.6f}{1.0:20.6f}\n"
    for kw, head in (("*LOAD_SEGMENT_SET", ""), ("*LOAD_SEGMENT_SET_ID", f"{11:10d}press\n")):   # 출력은 둘 다 _ID 꼴
        ld = kw + "\n" + head + f10(5, 7)
        d, rc, log = R.run(f"rc_r3_{'id' if head else 'plain'}", {"model.k": R.cube_deck(seg + crv + ld)})
        t = R.read(d, "model_trans.k")
        rows = block(t, "*LOAD_SEGMENT_SET_ID")   # KMM 기록기는 번호 없는 하중도 _ID 꼴로 쓴다
        c = R.try_(lambda: R.floats(rows[1], 10), [])
        check(f"R3 {kw}: rc 0·Traceback 없음, SSID 5·LCID 7·SF 1.0·AT 0.0", rc == 0 and R.no_tb(log) and len(c) >= 2
              and int(c[0]) == 5 and int(c[1]) == 7 and (len(c) < 3 or R.near(c[2], 1.0)) and (len(c) < 4 or c[3] == 0.0),
              f"rc={rc} {rows} " + log[-300:])


def r5():
    print("[R5] 카드 2·3 을 생략한 짧은 접촉 — R16 필수 카드(카드 1~3)라 원인을 밝혀 멈춘다(rc 1, 예전엔 TIED 가 IndexError)")
    deck = ("*KEYWORD\n" + R.node_block(R.cubes(2, dx=1.0)) + "*ELEMENT_SOLID\n" + R.hex_row(1, 1, 1) + R.hex_row(2, 2, 9)
            + R.part(1) + R.part(2) + R.SOLID1 + R.ELASTIC)
    for kw, cards in (("*CONTACT_TIED_SURFACE_TO_SURFACE", f10(2, 1, 3, 3)),
                      ("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID", f"{9:10d}short\n" + f10(2, 1, 3, 3))):
        d, rc, log = R.run(f"rc_r5_{kw[9:20].lower()}", {"model.k": deck + kw + "\n" + cards + "*END\n"})
        check(f"R5 {kw} 카드 1 만: rc 1, 「필수 카드가 2장 모자란다」 를 알린다", rc == 1 and "필수 카드가 2장 모자란다" in log,
              f"rc={rc} " + log[-300:])

REAL = (("/home/koopark/claude/KooSlurmInstallAutomationRefactory/KooSlurmInstallAutomationRefactory/dashboard/kooCAEWebAutomationServer_5001"
         "/model/koo.park/20250726084458/drop_attitude/taylor_A_dump.k", None),
        ("/home/koopark/claude/KooRemapper/build/scratch/regress/pidref_axes_9dupc4lb/ref.k", "필수 카드가 2장 모자란다"))


def real():
    print("[실제 덱] 말뭉치에서 죽던 덱(있을 때만) — 읽거나, 필수 카드가 빠진 덱이면 원인을 밝혀 멈춘다")
    for p, stop in REAL:
        if not Path(p).exists():
            print(f"  (없음 — 건너뜀) {p}")
            continue
        d, rc, log = R.run("rc_real_" + Path(p).stem, {"model.k": Path(p).read_text(errors="replace")})
        if stop is None:
            check(f"실제 덱 {Path(p).name}: rc 0·Traceback 없음", rc == 0 and R.no_tb(log), f"rc={rc} " + log[-300:])
        else:
            check(f"실제 덱 {Path(p).name}: 하중 카드는 넘어가고, 짧은 접촉에서 「{stop}」 로 멈춘다(rc 1)", rc == 1 and stop in log,
                  f"rc={rc} " + log[-300:])


if __name__ == "__main__":
    for f in (r1, r2_r4, r3, r5, real):
        f()
    print(f"\n판정 {'모두 통과' if not FAILS else str(len(FAILS)) + '건 실패'}")
    for x in FAILS:
        print("  FAIL", x[:400])
    sys.exit(1 if FAILS else 0)
