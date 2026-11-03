# *SECTION_SHELL·*SECTION_TSHELL(_TITLE) 카드 묶음(한 블록 여러 단면·ICOMP 각도·사용자 요소 카드·long·콤마)과 PART_EXCHANGE TSHELL 단면을 보는 회귀 시험
"""
실행: venv312/bin/python tests/test_section_card_sets.py   (KMM 6회, 약 40초)
수정 전 코드로 볼 때: KMM_GEN=<옛 occProject/Generators> … / 컴파일본: KMM_BIN=<KooMeshModifier 실행 파일> …

배경 (2026-11-03, 기존 결함 묶음 C1·C3·C4·C5): R16 "For each … section include a set of the following cards. This input ends at
the next keyword". 예전엔 블록마다 첫 단면만 읽어 같은 블록의 다음 단면이 사라졌고, *SECTION_SHELL ICOMP=1 의 각도 카드는
읽지도 쓰지도 않았다(복합 셸 적층이 조용히 틀어짐). long('+')·콤마 형식은 SECID 를 잃었다. PART_EXCHANGE 는 TSHELL 단면을
파트에 붙이지 못했다('Invalid section ID').
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


def check(name, cond, detail=""):
    print("  %-76s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


def f20(*v):
    return "".join(f"{x:>20}" for x in v) + "\n"


# 셸: (SECID, ELFORM, SHRF, NIP, PROPT, QR, ICOMP, SETYP), (T1~T4, NLOC, MAREA, IDOF), 각도
SH = {21: ((21, 2, 0.8333, 3, 1, 0.0, 1, 1), (0.3, 0.3, 0.3, 0.3, 0.0, 0.0, 0.0), [0.0, 45.0, 90.0]),
      22: ((22, 16, 0.8333, 2, 1, 0.0, 0, 1), (0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0), []),
      23: ((23, 2, 0.8333, 10, 1, 0.0, 1, 1), (0.4, 0.4, 0.4, 0.4, 0.0, 0.0, 0.0), [9.0 * k for k in range(10)]),
      24: ((24, 2, 0.8333, 2, 1, 0.0, 0, 1), (0.6, 0.6, 0.6, 0.6, 0.0, 0.0, 0.0), []),
      25: ((25, 2, 0.8333, 3, 1, 0.0, 1, 1), (0.2, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0), [15.0, 30.0, 45.0])}
USER_CARDS = [f10(1, 0, 0, 0, 0, 2, 0, 0).rstrip("\n"), f10(0.0, 0.0, 2.0).rstrip("\n"), f10(1.5, 2.5).rstrip("\n")]
# 두꺼운 셸: (SECID, ELFORM, SHRF, NIP, PROPT, QR, ICOMP, TSHEAR), 각도
TS = {31: ((31, 3, 0.8333, 5, 1, 0.0, 0, 0), []),
      32: ((32, 5, 0.75, 3, 2, 0.5, 1, 1), [0.0, 45.0, 90.0]),
      33: ((33, 1, 0.8333, 2, 1, 0.0, 0, 0), []),
      34: ((34, 2, 0.8333, 2, 1, 0.0, 1, 0), [30.0, 60.0]),
      35: ((35, 2, 0.8333333, 4, 1, 0.0, 0, 0), []),
      36: ((36, 1, 0.8333, 2, 1, 0.0, 1, 0), [10.0, 20.0])}


def sh_cards(k):
    c1, c2, ang = SH[k]
    s = f10(*c1) + f10(*c2, 0)
    for i in range(0, len(ang), 8):
        s += f10(*ang[i:i + 8])
    return s


def ts_cards(k):
    c1, ang = TS[k]
    return f10(*c1) + (f10(*ang) if ang else "")


def deck():
    secs = ("*SECTION_SHELL\n" + sh_cards(21) + sh_cards(22)                                  # 한 블록 두 단면 + ICOMP 각도
            + "*SECTION_SHELL_TITLE\nskin\n" + sh_cards(23) + "core\n" + sh_cards(24)        # _TITLE 두 단면 + 각도 두 카드
            + "*SECTION_SHELL\n25,2,0.8333,3,1,0.0,1,1\n0.2,0.2,0.2,0.2,0.0,0.0,0.0,0\n15.0,30.0,45.0\n"  # 콤마
            + "*SECTION_SHELL\n" + f10(26, 101, 1.0, 2, 1, 0.0, 0, 1) + f10(0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0)
            + "\n".join(USER_CARDS) + "\n"                                                    # ELFORM 101 사용자 요소 카드
            + "*SECTION_TSHELL\n" + ts_cards(31) + ts_cards(32)                               # 한 블록 두 단면
            + "*SECTION_TSHELL_TITLE\nt33\n" + ts_cards(33)
            + "t34\n" + f10(34, 2, 0.8333, 2, 1, 0.0, "1.0", 0) + f10(30.0, 60.0)              # ICOMP '1.0' 표기(C3)
            + "*SECTION_TSHELL +\n" + f20(35, 2, 0.8333333, 4, 1, 0.0, 0, 0)                  # long 형식(C5)
            + "*SECTION_TSHELL\n36,1,0.8333,2,1,0.0,1,0\n10.0,20.0\n")                         # 콤마(C5)
    parts = "".join(f"*PART\np{k}\n" + f10(k, k, 1) for k in list(SH) + [26] + list(TS))
    pts = [(x, y, 0.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    nodes = "*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(pts))
    els = "*ELEMENT_SHELL\n" + "".join(f"{x:8d}" for x in (1, 21, 1, 2, 3, 4)) + "\n"
    return "*KEYWORD\n" + nodes + els + parts + secs + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*END\n"


def num(s):
    s = s.strip()
    return float(s) if s else 0.0


def out_sections(text):
    """출력 단면 → {SECID: (종류, 카드1 수, 카드2 수, 각도, 남은 원문 줄)}"""
    out, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        u = lines[i].strip().upper()
        if u.startswith("*SECTION_SHELL") or u.startswith("*SECTION_TSHELL"):
            shell = u.startswith("*SECTION_SHELL")
            i += 1
            data = []
            while i < len(lines) and not lines[i].startswith("*"):
                if not lines[i].startswith("$"):
                    data.append(lines[i])
                i += 1
            if "_TITLE" in u:
                data = data[1:]
            if not data:
                continue
            c1 = [num(data[0][k * 10:(k + 1) * 10]) for k in range(8)]
            rest = data[1:]
            c2 = []
            if shell and rest:
                c2 = [num(rest[0][k * 10:(k + 1) * 10]) for k in range(7)]
                rest = rest[1:]
            ang, extra = [], []
            n_ang = (int(c1[3]) if int(c1[3]) > 0 else 2) if int(c1[6]) == 1 else 0
            for ln in rest:
                if len(ang) < n_ang:
                    ang += [num(ln[k * 10:(k + 1) * 10]) for k in range(8) if ln[k * 10:(k + 1) * 10].strip()]
                else:
                    extra.append(ln.rstrip())
            out[int(c1[0])] = ("SHELL" if shell else "TSHELL", c1, c2, ang, extra)
            continue
        i += 1
    return out


def close(a, b, rel):
    return all(abs(x - y) <= rel * max(1.0, abs(y)) for x, y in zip(a, b)) and len(a) == len(b)


def run(name, deck_text, opt):
    d = Path(tempfile.mkdtemp(prefix=f"seccards_{name}_"))
    (d / "model.k").write_text(deck_text)
    (d / "opt.txt").write_text(opt)
    r = subprocess.run(KMM_CMD + ["opt.txt"], cwd=d, capture_output=True, text=True, timeout=900, env=ENV)
    return d, r.returncode, r.stdout + r.stderr


def main():
    d, rc, log = run("trans", deck(), TRANS)
    outs = sorted(d.glob("model_trans.k"))
    check("TRANSFORM: rc 0 · 출력 있음", rc == 0 and bool(outs), f"rc={rc} " + log[-600:])
    got = out_sections(outs[0].read_text(errors="replace")) if outs else {}
    for k, (c1, c2, ang) in SH.items():
        g = got.get(k)
        ok = (g is not None and g[0] == "SHELL" and close(g[1], [float(x) for x in c1], 1e-3)
              and close(g[2], [float(x) for x in c2], 1e-3) and close(g[3], ang, 1e-12))
        check(f"SHELL {k}: 카드 1·2 값과 각도 {len(ang)}개 그대로", ok, str(g))
    g = got.get(26)
    check("SHELL 26(ELFORM 101): 사용자 요소 카드 3줄이 원문 그대로", g is not None and g[4][:3] == [c.rstrip() for c in USER_CARDS], str(g))
    for k, (c1, ang) in TS.items():
        g = got.get(k)
        ok = (g is not None and g[0] == "TSHELL" and close(g[1], [float(x) for x in c1], 1e-12) and close(g[3], ang, 1e-12))
        check(f"TSHELL {k}: 카드 1 값과 각도 {len(ang)}개 그대로", ok, str(g))

    # C4 — PART_EXCHANGE 로 파트 31 에 새 TSHELL 단면
    pex = ("*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,31\n*SECTION_TSHELL\n"
           + f"{'SID':>10}" + f10(5, 0.75, 3, 1, 0.0, 0, 1).rstrip("\n") + "\n**EndPartExchange\n*End\n")
    d, rc, log = run("pex", deck(), pex)
    outs = [p for p in sorted(d.glob("*.k")) if p.name != "model.k" and "dump" not in p.name]
    check("C4 PART_EXCHANGE: rc 0 · 'Invalid section ID' 없음", rc == 0 and "Invalid section ID" not in log and bool(outs),
          f"rc={rc} " + log[-600:])
    if outs:
        t = outs[0].read_text(errors="replace")
        lines = t.splitlines()
        secid = None
        for i, ln in enumerate(lines):
            if ln.strip().upper().startswith("*PART"):
                data = [x for x in lines[i + 1:i + 6] if not x.startswith("$")]
                if len(data) >= 2 and data[1][:10].strip() == "31":
                    secid = int(float(data[1][10:20]))
        sec = out_sections(t).get(secid) if secid is not None else None
        check("C4 PART_EXCHANGE: 파트 31 이 새 TSHELL 단면(ELFORM 5·SHRF 0.75·NIP 3·TSHEAR 1)을 가리킴",
              sec is not None and sec[0] == "TSHELL" and close(sec[1][1:8], [5, 0.75, 3, 1, 0.0, 0, 1], 1e-12), f"secid={secid} sec={sec}")
    # C4 — SOLID 단면 교체도 PART 카드 SECID 가 새 단면을 가리킨다(예전엔 part.section 만 바뀌어 옛 SECID 그대로)
    pts = [(x, y, z) for z in (0.0, 1.0) for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1))]
    sdeck = ("*KEYWORD\n*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}\n" for i, (x, y, z) in enumerate(pts))
             + "*ELEMENT_SOLID\n" + f"{1:8d}{5:8d}" + "".join(f"{n:8d}" for n in range(1, 9)) + "\n"
             + "*PART\nblock\n" + f10(5, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*END\n")
    spex = ("*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,5\n*SECTION_SOLID_TITLE\nnewsec\n"
            + f"{'SID':>10}{2:>10}\n**EndPartExchange\n*End\n")
    d, rc, log = run("pex_solid", sdeck, spex)
    t = (d / "model_pex.k").read_text(errors="replace") if (d / "model_pex.k").exists() else ""
    lines = t.splitlines()
    pid_line = next((lines[i + 2] for i, ln in enumerate(lines) if ln.strip().upper().startswith("*PART") and i + 3 < len(lines)
                     and lines[i + 2].startswith("$") is False and lines[i + 2][:10].strip() == "5"), None)
    if pid_line is None:   # 제목 줄 뒤에 주석 줄이 끼는 꼴
        pid_line = next((ln for ln in lines if ln[:10].strip() == "5" and len(ln) >= 20 and ln[10:20].strip()), None)
    new_secid = None
    for i, ln in enumerate(lines):
        if ln.strip().upper().startswith("*SECTION_SOLID"):
            data = [x for x in lines[i + 1:i + 4] if not x.startswith("$")]
            if len(data) >= 2 and data[1][10:20].strip() == "2":
                new_secid = data[1][:10].strip()
    check("C4 PART_EXCHANGE(SOLID): PART 5 의 SECID 가 새 단면(ELFORM 2)", rc == 0 and pid_line is not None and new_secid is not None
          and pid_line[10:20].strip() == new_secid, f"rc={rc} pid_line={pid_line!r} new_secid={new_secid}")
    # 리뷰 W 🔴1 — 단면 블록 끝·앞·사이 빈 줄이 다음 단면 카드 1 로 읽혀 유령 단면(SECID 빈 NewSection)이 생기고 파트가 그것을 가리켰다
    bdeck = ("*KEYWORD\n*NODE\n" + "".join(f"{i + 1:8d}{float(x):16.6f}{float(y):16.6f}{0.0:16.6f}\n"
                                         for i, (x, y) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))))
             + "*ELEMENT_SHELL\n" + "".join(f"{x:8d}" for x in (1, 41, 1, 2, 3, 4)) + "\n"
             + "".join(f"*PART\np{k}\n" + f10(k, k, 1) for k in (41, 42, 43, 44, 45))
             + "*SECTION_SHELL\n" + f10(41, 2, 0.8333, 3, 1, 0, 0, 1) + f10(0.5, 0.5, 0.5, 0.5, 0.0, 0, 0, 0) + "\n"            # 끝 빈 줄
             + "*SECTION_SHELL\n\n" + f10(42, 2, 0.8333, 3, 1, 0, 0, 1) + f10(0.7, 0.7, 0.7, 0.7, 0.0, 0, 0, 0) + "\n"     # 앞·사이 빈 줄
             + f10(43, 16, 0.8333, 2, 1, 0, 0, 1) + f10(0.9, 0.9, 0.9, 0.9, 0.0, 0, 0, 0)
             + "*SECTION_TSHELL\n" + f10(44, 1, 0.8333, 3, 1, 0.0, 0, 0) + "\n"                                               # 끝 빈 줄
             + "*SECTION_SOLID\n" + f10(45, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3) + "*END\n")
    d, rc, log = run("blank", bdeck, TRANS)
    t = (d / "model_trans.k").read_text(errors="replace") if (d / "model_trans.k").exists() else ""
    lines = t.splitlines()
    secs = {}
    for i, ln in enumerate(lines):
        u = ln.strip().upper()
        if u.startswith("*SECTION_"):
            data = []
            for x in lines[i + 1:i + 6]:
                if x.startswith("*"):
                    break
                if not x.startswith("$"):
                    data.append(x)
            if u.endswith("_TITLE"):
                data = data[1:]
            if data:
                secs[int(float(data[0][:10]))] = (u.replace("_TITLE", ""), num(data[0][10:20]), num(data[1][:10]) if len(data) > 1 else None)
    parts = {}
    for i, ln in enumerate(lines):
        if ln.strip().upper().startswith("*PART"):
            data = [x for x in lines[i + 1:i + 5] if not x.startswith("$")]
            if len(data) >= 2:
                parts[int(data[1][:10])] = int(float(data[1][10:20]))
    check("🔴1 빈 줄: rc 0", rc == 0, f"rc={rc} " + log[-500:])
    check("🔴1 빈 줄: 단면은 41~45 다섯뿐(유령 NewSection 없음)", sorted(secs) == [41, 42, 43, 44, 45], str(secs))
    check("🔴1 빈 줄: 파트 41~45 가 자기 단면을 가리킴", all(parts.get(k) == k for k in (41, 42, 43, 44, 45)), str(parts))
    check("🔴1 빈 줄: 셸 42·43 두께 0.7·0.9, TSHELL 44·SOLID 45 형식 그대로",
          secs.get(42, ("", 0, 0))[2] == 0.7 and secs.get(43, ("", 0, 0))[2] == 0.9 and secs.get(44, ("",))[0] == "*SECTION_TSHELL"
          and secs.get(45, ("",))[0] == "*SECTION_SOLID", str(secs))
    check("🔴1 빈 줄: 건너뛴 빈 줄을 알림", "빈 줄" in log and "SECTION_SHELL" in log, log[-400:])
    # 리뷰 W 🟡7 — PART_EXCHANGE 로 *SECTION_TSHELL 과 *ConvertHexato,TShell 을 함께 주면 그 단면을 쓴다(예전엔 기본 New TShell 로 덮음)
    cpex = ("*Inputfile\nmodel.k\n*Mode\nPART_EXCHANGE,1\n**PartExchange,1\n*PID,5\n*SECTION_TSHELL\n"
            + f"{'SID':>10}" + f10(5, 0.75, 3, 1, 0.0, 0, 1).rstrip("\n") + "\n*ConvertHexato,TShell,(0,0,1),5.0\n**EndPartExchange\n*End\n")
    d, rc, log = run("pex_conv", sdeck, cpex)
    t = (d / "model_pex.k").read_text(errors="replace") if (d / "model_pex.k").exists() else ""
    secs = out_sections(t)
    lines = t.splitlines()
    psec = None
    for i, ln in enumerate(lines):
        if ln.strip().upper().startswith("*PART"):
            data = [x for x in lines[i + 1:i + 5] if not x.startswith("$")]
            if len(data) >= 2 and data[1][:10].strip() == "5":
                psec = int(float(data[1][10:20]))
    g = secs.get(psec)
    check("🟡7 PART_EXCHANGE + ConvertHexato: 파트 5 가 준 TSHELL 단면(ELFORM 5·SHRF 0.75·NIP 3·TSHEAR 1)을 가리킴",
          rc == 0 and g is not None and g[0] == "TSHELL" and close(g[1][1:8], [5, 0.75, 3, 1, 0.0, 0, 1], 1e-12), f"rc={rc} psec={psec} sec={g}")
    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}")
        for f in FAILS:
            print("  -", f[:900])
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
