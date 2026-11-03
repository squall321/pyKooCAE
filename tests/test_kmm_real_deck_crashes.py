# 실제 덱에서 KMM 이 죽던 기존 결함(말뭉치 V, 2026-11-03)을 작은 덱으로 재현해 고쳐졌는지 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_kmm_real_deck_crashes.py   (KMM 15회, 약 2분)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

  B1  *DATABASE_EXTENT_INTFOR 카드 1장(R16 카드 2 는 선택, 기본값 0) — 예전엔 IndexError
  B2  요소가 *NODE 에 없는 절점을 가리킴 — 예전엔 DROP 에서 SetBoundaries IndexError, TRANSFORM 은 원인 없이 rc 3
  B3  *CONTACT_ERODING_SURFACE_TO_SURFACE_ID — 예전엔 UnboundLocalError('i')
  B4  *LOAD_SEGMENT_SET 이 *SET_SEGMENT_GENERAL 을 가리킴 — 예전엔 KeyError
  B5  고정폭 10칸을 넘친 수(82자 줄) — 예전엔 원인 없는 ValueError traceback
  B6  *SECTION_SHELL 필수 카드 2 없음 — 예전엔 IndexError
  C2  KooDynaFloat 의 Fortran 꼴('4.5+01'·'1.0-3'·D 지수) — 예전엔 죽거나 조용히 기본값
  D   원문 통과 블록(*ELEMENT_DISCRETE) 키워드 줄의 '%'(I10)·'+'(long) 표시 — 예전엔 버려 LS-DYNA 가 칸을 잘못 읽었다
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
FAILS = []
TRANS = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
DROP = """*Inputfile
model.k
*RunDirectoryMode,True,runs
*Mode
DROP_ATTITUDE,1
**DropAttitude,1
EulerRolling,0
EulerPitching,0
EulerYawing,0
Height,100
InitialVelocityX,0
InitialVelocityY,0
InitialVelocityZ,0
InitialAngularVelocityX,0
InitialAngularVelocityY,0
InitialAngularVelocityZ,0
OffsetDistance,1
Density,7.85e-9
YoungsModulus,2.0e5
PoissonRatio,0.3
tFinal,0.001
dt,1e-6
RobustContact,True
**EndDropAttitude
*End
"""


def check(name, cond, detail=""):
    print("  %-74s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def base(extra="", nodes_upper=True, shell_card2=True):
    """솔리드 두 덩이(파트 1·2, 각 1요소) + 셸 하나(파트 3). nodes_upper=False 면 위 덩이 절점 9~16 을 빼 둔다(B2)."""
    pts = [(x, y, z) for z in (0.0, 1.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    pts += [(x, y, z) for z in (1.0, 2.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    pts += [(2, 0, 0), (3, 0, 0), (3, 1, 0), (2, 1, 0)]
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n"
                                for i, (x, y, z) in enumerate(pts) if nodes_upper or not 9 <= i + 1 <= 16)
    els = ("*ELEMENT_SOLID\n" + f"{1:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n"
           + f"{2:8d}{2:8d}" + "".join(f"{n:8d}" for n in range(9, 17)) + "\n"
           + "*ELEMENT_SHELL\n" + "".join(f"{x:8d}" for x in (3, 3, 17, 18, 19, 20)) + "\n")
    shell = "*SECTION_SHELL\n" + f10(2, 2, 0.8333, 3, 1, 0, 0, 0) + (f10(0.5, 0.5, 0.5, 0.5, 0.0, 0, 0, 0) if shell_card2 else "")
    props = ("*PART\nlower\n" + f10(1, 1, 1) + "*PART\nupper\n" + f10(2, 1, 1) + "*PART\nplate\n" + f10(3, 2, 1)
             + "*SECTION_SOLID\n" + f10(1, 1) + shell + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3))
    return "*KEYWORD\n" + nodes + els + props + extra + "*END\n"


def run(name, deck, opt):
    d = Path(tempfile.mkdtemp(prefix=f"kmmcrash_{name}_"))
    (d / "model.k").write_text(deck)
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def out_text(d, name):
    ps = sorted(d.rglob(name))
    return ps[0].read_text(errors="replace") if ps else ""


def block(text, kw):
    """첫 kw 블록의 데이터 줄(주석 제외)."""
    lines, out, on = text.splitlines(), [], False
    for ln in lines:
        if ln.startswith("*"):
            if on:
                break
            on = ln.strip().upper() == kw
            continue
        if on and ln.strip() and not ln.startswith("$"):
            out.append(ln)
    return out


def no_traceback(log):
    return "Traceback (most recent call last)" not in log


def main():
    # B1 — 카드 1장 DATABASE_EXTENT_INTFOR
    d, rc, log = run("b1", base("*DATABASE_EXTENT_INTFOR\n" + f10(0, 1, 1, 1, 1, -1, 0, 0)), TRANS)
    b = block(out_text(d, "model_trans.k"), "*DATABASE_EXTENT_INTFOR")
    check("B1: rc 0 · traceback 없음", rc == 0 and no_traceback(log), f"rc={rc} " + log[-500:])
    check("B1: 카드 1 값 그대로(0 1 1 1 1 -1 0 0)·카드 2 는 R16 기본값 0",
          len(b) >= 1 and b[0].split() == ["0", "1", "1", "1", "1", "-1", "0", "0"]
          and (len(b) == 1 or set(b[1].split()) <= {"0"}), str(b))

    # B3 — ERODING_SURFACE_TO_SURFACE_ID
    ero = ("*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n" + f"{401:10d}{'eroding_region':>70}\n" + f10(1, 2, 3, 3, 0, 0, 1, 1)
           + f10(0.3, 0.2, 0.0, 0.0, 0.0, 2, 0.0, "1.0E+20") + f10(1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0) + f10(1, 1, 1))
    d, rc, log = run("b3", base(ero), TRANS)
    t = out_text(d, "model_trans.k")
    b = block(t, "*CONTACT_ERODING_SURFACE_TO_SURFACE_ID")
    check("B3: rc 0 · traceback 없음", rc == 0 and no_traceback(log), f"rc={rc} " + log[-500:])
    check("B3: 접촉 CID 401·SSID 1·MSID 2·SYM/EROSOP/IADJ 1 1 1 그대로",
          len(b) >= 5 and b[0].split()[0] == "401" and b[1].split()[:2] == ["1", "2"] and b[4].split()[:3] == ["1", "1", "1"], str(b))

    # B4 — SET_SEGMENT_GENERAL 을 가리키는 LOAD_SEGMENT_SET
    gen = ("*SET_SEGMENT_GENERAL\n" + f10(3, 0.0, 0.0, 0.0, 0.0) + f10("PART", 1, 2) + "*DEFINE_CURVE\n" + f10(9001)
           + f"{0.0:>20}{1.0:>20}\n{1.0:>20}{1.0:>20}\n" + "*LOAD_SEGMENT_SET\n" + f10(3, 9001, 0.0993, 0.0))
    d, rc, log = run("b4", base(gen), TRANS)
    t = out_text(d, "model_trans.k")
    ls = [ln for kw in ("*LOAD_SEGMENT_SET", "*LOAD_SEGMENT_SET_ID") for ln in block(t, kw)]
    check("B4: rc 0 · traceback 없음", rc == 0 and no_traceback(log), f"rc={rc} " + log[-500:])
    check("B4: 하중이 SSID 3·LCID 9001 로 남음", any(ln.split()[:2] == ["3", "9001"] for ln in ls), str(ls))
    check("B4: *SET_SEGMENT_GENERAL 원문이 남음", len(block(t, "*SET_SEGMENT_GENERAL")) == 2, str(block(t, "*SET_SEGMENT_GENERAL")))

    # B6 — SECTION_SHELL 카드 2 없음
    d, rc, log = run("b6", base(shell_card2=False), TRANS)
    check("B6: rc 0 · traceback 없음", rc == 0 and no_traceback(log), f"rc={rc} " + log[-500:])
    check("B6: 필수 카드 2 가 없다고 알림", "카드 2" in log and "SECTION_SHELL" in log, log[-600:])

    # B2 — 정의 안 된 절점(위 덩이 절점 9~16 없음)
    for mode, opt in (("trans", TRANS), ("drop", DROP)):
        d, rc, log = run(f"b2_{mode}", base(nodes_upper=False), opt)
        check(f"B2 {mode}: traceback 없음 · rc 3(요소 소실)", rc == 3 and no_traceback(log), f"rc={rc} " + log[-500:])
        check(f"B2 {mode}: 소실 원인 '정의 안 된 절점' 을 적음", "정의 안 된 절점" in log, log[-600:])

    # B5 — 82자 줄(DT 가 12자로 10칸을 넘침, KooRemapper ModelAssembler 꼴)
    tied = ("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET\n" + f10(1, 2, 3, 3, 0, 0, 1, 1)
            + "       0.0       0.0       0.0       0.0       0.0         0       0.0  1.0000E+20\n"
            + f10(0.0, 0.0, 0.005, 0.005, 0.0, 0.0, 0.0, 0.0))
    d, rc, log = run("b5", base(tied), TRANS)
    check("B5: traceback 대신 원인을 짚는 오류(칸 원문·10칸·80열)",
          rc != 0 and "1.0000E+" in log and "10칸" in log and "80" in log, f"rc={rc} " + log[-600:])

    # D — 원문 통과 블록의 키워드 줄 형식 표시('%'=I10·'+'=long). *ELEMENT_DISCRETE 는 KMM 이 해석하지 않는 키워드이고 표준 칸이
    #     I8 이라 표시가 뜻을 가진다. 예전엔 '*ELEMENT_DISCRETE' 만 써서 10칸·20칸 원문 줄을 LS-DYNA 가 8칸으로 잘못 읽었다
    raw = ("*ELEMENT_DISCRETE %\n" + f"{9:10d}{3:10d}{17:10d}{18:10d}{0:10d}{1.0:16.4f}{0:10d}{0.0:16.4f}\n"
           + "*ELEMENT_DISCRETE +\n" + f"{10:20d}{3:20d}{19:20d}{20:20d}\n")
    d, rc, log = run("d_marker", base(raw), TRANS)
    t = out_text(d, "model_trans.k")
    disc = [ln for ln in t.splitlines() if "ELEMENT_DISCRETE" in ln]
    check("D: rc 0", rc == 0 and no_traceback(log), f"rc={rc} " + log[-500:])
    check("D: 원문 블록 '*ELEMENT_DISCRETE %'(I10) 표시가 남음", "*ELEMENT_DISCRETE %" in disc, str(disc))
    check("D: 원문 블록 '*ELEMENT_DISCRETE +'(long) 표시가 남음", "*ELEMENT_DISCRETE +" in disc, str(disc))

    # 리뷰 W 🟡5·🟡6 — 덱 전체 *KEYWORD I10=Y 여도 원문 I10 블록에 '%' (일반 모드 출력은 '*KEYWORD' 만 쓴다), '-'(표준 강제)는 '-' 로
    g = base("*ELEMENT_DISCRETE\n" + f"{9:10d}{3:10d}{17:10d}{18:10d}{0:10d}{1.0:16.4f}{0:10d}{0.0:16.4f}\n"
             + "*ELEMENT_DISCRETE -\n" + f"{10:8d}{3:8d}{19:8d}{20:8d}{0:8d}{1.0:16.4f}{0:8d}{0.0:16.4f}\n").replace("*KEYWORD\n", "*KEYWORD I10=Y\n", 1)
    # 덱 전체 I10 이면 *NODE·*ELEMENT 도 10칸이어야 한다 — 이 시험은 원문 블록만 보므로 그 둘은 % 표시로 8칸을 지킨다
    g = g.replace("*NODE\n", "*NODE -\n").replace("*ELEMENT_SOLID\n", "*ELEMENT_SOLID -\n").replace("*ELEMENT_SHELL\n", "*ELEMENT_SHELL -\n")
    d, rc, log = run("w_i10", g, TRANS)
    t = out_text(d, "model_trans.k")
    disc = [ln for ln in t.splitlines() if ln.startswith("*ELEMENT_DISCRETE")]
    check("🟡5 덱 전체 I10=Y: 원문 블록에 '*ELEMENT_DISCRETE %'", rc in (0, 3) and "*ELEMENT_DISCRETE %" in disc, f"rc={rc} {disc} {t.splitlines()[:1]}")
    check("🟡6 '-'(표준 강제) 원문 블록은 '*ELEMENT_DISCRETE -'", "*ELEMENT_DISCRETE -" in disc, str(disc))
    # 리뷰 W 🟡8 — 원문 *SET_SEGMENT_GENERAL 2 와 KMM 이 새로 만드는 세그먼트 셋 번호가 겹치지 않는다(DROP RobustContact)
    seg = ("*SET_SEGMENT\n" + f10(1) + f10(1, 2, 3, 4) + "*SET_SEGMENT_GENERAL\n" + f10(2, 0.0, 0.0, 0.0, 0.0) + f10("PART", 1)
           + "*DEFINE_CURVE\n" + f10(9001) + f"{0.0:>20}{1.0:>20}\n{1.0:>20}{1.0:>20}\n"
           + "*LOAD_SEGMENT_SET\n" + f10(2, 9001, 1.0, 0.0))
    d, rc, log = run("w_ssid", base(seg), DROP)
    ds = sorted(d.rglob("DropSet.k"))
    t = ds[0].read_text(errors="replace") if ds else ""
    lines = t.splitlines()
    sids = []
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*SET_SEGMENT") and not u.startswith("*SET_SEGMENT_GENERAL"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            if u.endswith("_TITLE"):
                data = data[1:]
            if data:
                sids.append(int(float(data[0][:10])))
    check("🟡8 세그먼트 셋 번호: KMM 이 쓰는 셋 번호가 겹치지 않고 원문 GENERAL 2 와도 다름",
          rc == 0 and len(sids) == len(set(sids)) and 2 not in sids, f"rc={rc} sids={sids} " + log[-300:])

    # 리뷰 X 🟡2 — 원문 셋 번호 예약이 '--2024'·'①②' 같은 *_TITLE 제목에서 int() 로 죽지 않는다
    weird = "".join(f"*SET_PART_ADD_TITLE\n{t}\n" + f10(sid) + f10(1) for t, sid in (("--2024", 7), ("①②", 8)))
    d, rc, log = run("x_title", base(weird), TRANS)
    check("X🟡2 원문 *SET_PART_ADD_TITLE 제목 '--2024'·'①②': 죽지 않음", rc == 0 and no_traceback(log), f"rc={rc} " + log[-400:])
    # 리뷰 X 🟡3 — 요소 셋 계열도 예약: 원문 *SET_SOLID_GENERAL 1 이 있으면 THERMAL 발열원 *SET_SOLID 가 1 을 받지 않는다
    therm = ("*Inputfile\nmodel.k\n*RunDirectoryMode,True,out\n*Mode\nTHERMAL_LOAD,1\n**ThermalLoad,1\nThermalType,ICPower\n"
             "Phase,thermal\nAnalysisType,transient\nUnitSystem,SI\nInitialTemperatureC,25\nTimestepIts,0.01\nMaterials\n"
             "1,7.85e-09,4.6e+08,50\n2,7.85e-09,4.6e+08,50\nEndMaterials\nHeatSources\n1,1.5,8.0\nEndHeatSources\n**EndThermalLoad\n*End\n")
    d, rc, log = run("x_solidset", base("*SET_SOLID_GENERAL\n" + f10(1) + f10("PART", 2)), therm)
    ts = sorted(d.rglob("ThermalSet.k"))
    t = ts[0].read_text(errors="replace") if ts else ""
    lines = t.splitlines()
    ssids = []
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*SET_SOLID") and not u.startswith("*SET_SOLID_GENERAL"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            if u.endswith("_TITLE"):
                data = data[1:]
            if data:
                ssids.append(int(float(data[0][:10])))
    check("X🟡3 요소 셋 번호: KMM 의 *SET_SOLID 가 원문 *SET_SOLID_GENERAL 1 과 겹치지 않음",
          rc == 0 and ssids and 1 not in ssids and len(ssids) == len(set(ssids)), f"rc={rc} ssids={ssids} " + log[-300:])
    # 리뷰 X ⚪4 — long('+') 원문 셋의 20칸 SID 도 예약(원문 번호를 KMM 의 다음 번호 2 로 둬야 충돌이 드러난다)
    lseg = ("*SET_SEGMENT\n" + f10(1) + f10(1, 2, 3, 4) + "*SET_SEGMENT_GENERAL +\n" + f"{2:20d}\n" + f"{'PART':>20}{1:20d}\n")
    d, rc, log = run("x_long", base(lseg), DROP)
    ds = sorted(d.rglob("DropSet.k"))
    t = ds[0].read_text(errors="replace") if ds else ""
    lines = t.splitlines()
    sids = []
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*SET_SEGMENT") and not u.startswith("*SET_SEGMENT_GENERAL"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            if u.endswith("_TITLE"):
                data = data[1:]
            if data:
                sids.append(int(float(data[0][:10])))
    check("X⚪4 long 원문 *SET_SEGMENT_GENERAL + 2(=KMM 의 다음 번호): KMM 세그먼트 셋이 2 를 받지 않음", rc == 0 and 2 not in sids and len(sids) == len(set(sids)),
          f"rc={rc} sids={sids}")
    # 리뷰 Y 🟡2 — 원문 *SET_*_TITLE 의 제목 줄이 비어도 그 SID 를 예약한다(빈 줄을 먼저 거르면 제목 대신 SID 줄이 빠졌다)
    bseg = ("*SET_SEGMENT\n" + f10(1) + f10(1, 2, 3, 4) + "*SET_SEGMENT_GENERAL_TITLE\n\n" + f10(2, 0.0, 0.0, 0.0, 0.0) + f10("PART", 1))
    d, rc, log = run("y_blanktitle", base(bseg), DROP)
    ds = sorted(d.rglob("DropSet.k"))
    t = ds[0].read_text(errors="replace") if ds else ""
    lines = t.splitlines()
    sids = []
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*SET_SEGMENT") and not u.startswith("*SET_SEGMENT_GENERAL"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            if u.endswith("_TITLE"):
                data = data[1:]
            if data:
                sids.append(int(float(data[0][:10])))
    check("Y🟡2 빈 제목 원문 *SET_SEGMENT_GENERAL_TITLE 2: KMM 세그먼트 셋이 2 를 받지 않음", rc == 0 and sids and 2 not in sids and len(sids) == len(set(sids)),
          f"rc={rc} sids={sids}")

    # C2 — KooDynaFloat 단위 시험
    sys.path.insert(0, str(GEN))
    from KooCAEManager.KooOperator import KooDynaFloat
    cases = [("4.5+01", 45.0), ("1.0-3", 0.001), ("1.0D-3", 0.001), ("  2.5d2", 250.0), ("-3.0E+2", -300.0),
             ("0.8333", 0.8333), ("", 7.0), ("abc", 7.0), ("1e3", 1000.0), ("-.5-1", -0.05),
             ("1D", 7.0), ("1.0D", 7.0), ("1e1d", 7.0), ("D1", 7.0)]   # D 가 섞인 수 아닌 글은 예전처럼 기본값(리뷰 W)
    for s, want in cases:
        try:
            got = KooDynaFloat(s, 7.0)
        except Exception as e:
            got = repr(e)
        check(f"C2: KooDynaFloat({s!r}) = {want}", isinstance(got, float) and abs(got - want) <= 1e-12 * max(1.0, abs(want)), str(got))
    try:
        KooDynaFloat("  1.0000E+", 1.0)
        check("C2: '  1.0000E+' 는 원인을 짚는 ValueError", False, "예외 없음")
    except ValueError as e:
        check("C2: '  1.0000E+' 는 원인을 짚는 ValueError", "1.0000E+" in str(e) and "10칸" in str(e), str(e))
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
