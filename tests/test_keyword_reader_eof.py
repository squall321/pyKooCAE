# 키워드 리더 파일 끝 블록(*END 없음·마지막 *INCLUDE)과 10절점 블록 오면체 개수 검사 회귀 시험
"""
실행: venv312/bin/python tests/test_keyword_reader_eof.py

배경 (2026-10-23, 적대 리뷰 중 발견)
  [1] ReadKeywordsfromFile 은 다음 '*' 줄을 만날 때만 블록을 마감했다. 그래서 *END 없이 끝나는
      파일의 마지막 블록이 사라졌다. 솔리드면 KeyError 크래시가 나고, 마지막이 *INCLUDE 면 그 파일을
      아예 읽지 않았다(요소 0, rc 0 — 무증상). 이제 끝에 *END 가 있는 것처럼 마감한다.
      마지막 *INCLUDE 뒤 빈 줄(빈 이름이 폴더로 열려 죽음)·데이터 없는 마지막 키워드(KeyError)도 같은 규칙이다.
  [2] KooPart mode2(10절점 형식)의 오면체 분기가 등록 수를 올리지 않아 '🔴 개수 불일치' 오탐이 났다.
  [3] 회귀: *END 가 있던 파일은 옛 동작 그대로다. *END 뒤에 놓인 꼬리(잡문·*NODE·*INCLUDE)를
      새로 읽지 않는다 — 출력이 *END 로 끝난 덱과 바이트 같아야 한다.
  [4] (2026-10-23 추가) *END 에서 그 파일 읽기를 멈춘다. R16 *END "Data in a keyword file beyond a
      *END command are not read", *INCLUDE "*END terminates the include file". 옛 판은 *END 뒤 블록을
      (마지막만 빼고) 읽어 출력의 *END 앞으로 옮겼다 — *END 뒤에 꺼 둔 카드가 살아났다.
  [5] (2026-10-23 추가) Ctrl-Z(0x1A, DOS 파일 끝 표시) 앞까지만 읽는다. 옛 판은 그 줄을 데이터로 먹어 죽었다.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "occProject" / "Generators"
PY = str(ROOT / "venv312" / "bin" / "python")
OPT = "*Inputfile\nmodel.k\n*Mode\nTRANSFORM,1\n**Transform,1\nTranslation,0,0,0\n**EndTransform\n*End\n"
BASE = Path(tempfile.mkdtemp(prefix="reader_eof_"))
FAILS = []


def check(name, cond, detail=""):
    print("  %-70s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


def nodes():
    out, nid = [], 0
    for z in range(3):
        for (x, y) in ((0, 0), (1, 0), (1, 1), (0, 1)):
            nid += 1
            out.append(f"{nid:8d}{float(x):16.6f}{float(y):16.6f}{float(z):16.6f}")
    return "*NODE\n" + "\n".join(out) + "\n"


def f10(*v):
    return "".join(f"{x:>10}" for x in v) + "\n"


PROPS = "*PART\nblock\n" + f10(1, 1, 1) + "*SECTION_SOLID\n" + f10(1, 1) + "*MAT_ELASTIC\n" + f10(1, "7.85E-09", 210000, 0.3)
SOLID = "*ELEMENT_SOLID\n" + "".join(f"{e:8d}{1:8d}" + "".join(f"{n:8d}" for n in range(4 * e - 3, 4 * e + 5)) + "\n"
                                     for e in (1, 2))
WANT = [ln for ln in SOLID.splitlines()[1:]]


def run_kmm(files):
    d = Path(tempfile.mkdtemp(dir=BASE))
    for name, text in files.items():
        Path(d, name).write_text(text)
    Path(d, "opt.txt").write_text(OPT)
    r = subprocess.run([PY, str(GEN / "KooMeshModifier.py"), "opt.txt"], cwd=d, capture_output=True, text=True,
                       timeout=600)
    out = Path(d, "model_trans.k")
    text = out.read_text() if out.exists() else ""
    els, f = [], False
    for ln in text.splitlines():
        if ln.startswith("*ELEMENT_SOLID"):
            f = True
            continue
        if ln.startswith("*"):
            f = False
        elif f and not ln.startswith("$") and len(ln.split()) >= 3:
            els.append(ln)
    return r.returncode, r.stdout + r.stderr, text, els


print("[1] 파일 끝 블록 — *END 없이 끝나는 파일")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + PROPS + "*INCLUDE\nsub.k\n*END\n", "sub.k": "*KEYWORD\n" + nodes() + SOLID})
check("인클루드가 *END 없이 *ELEMENT_SOLID 로 끝남 — rc 0", rc == 0, log[-300:])
check("  요소가 같은 모델 한 파일 출력과 같다", els == WANT, f"{els}")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID})
check("메인 덱이 *END 없이 *ELEMENT_SOLID 로 끝남 — rc 0", rc == 0, log[-300:])
check("  요소 보존", els == WANT, f"{els}")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + PROPS + "*INCLUDE\na.k\n*END\n",
                           "a.k": "*KEYWORD\n" + nodes() + "*INCLUDE\nb.k\n", "b.k": "*KEYWORD\n" + SOLID + "*END\n"})
check("인클루드의 마지막 키워드가 *INCLUDE(중첩) — 그 파일도 읽는다", rc == 0 and els == WANT, f"rc={rc} {els}")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + PROPS + "*INCLUDE\nsub.k\n\n",
                           "sub.k": "*KEYWORD\n" + nodes() + SOLID + "*END\n"})
check("마지막 *INCLUDE 뒤에 빈 줄 — 빈 이름은 건너뛰고 sub.k 를 읽는다", rc == 0 and els == WANT, f"rc={rc} {log[-200:]}")
rc, log, _, els = run_kmm({"model.k": "*KEYWORD\n" + nodes() + PROPS + SOLID + "*DEFINE_CURVE\n"})
check("데이터 없는 마지막 키워드 — *END 가 있을 때처럼 경고하고 rc 0",
      rc == 0 and els == WANT and "Empty keyword found: DEFINE_CURVE" in log, f"rc={rc} {log[-200:]}")

print("[2] 10절점 형식 블록의 오면체 — 개수 검사 오탐 없음")
el = lambda e, ns: f"{e:8d}{1:8d}\n" + "".join(f"{n:8d}" for n in ns) + "\n"  # noqa: E731
penta = ("*KEYWORD\n" + nodes() + PROPS + "*ELEMENT_SOLID (ten nodes format)\n" + el(1, list(range(1, 9)) + [0, 0])
         + el(2, [1, 2, 3, 5, 6, 7, 7, 7, 0, 0]) + el(3, [5, 6, 7, 8, 9, 10, 10, 10, 0, 0]) + "*END\n")
rc, log, _, els = run_kmm({"model.k": penta})
check("육면체 1 + 오면체 2 — 요소 3 출력", rc == 0 and len(els) == 3, f"rc={rc} {els}")
check("  개수 검사 '입력 3 = 등록 3', 🔴 없음", "입력 3 = 등록 3" in log and "개수 불일치" not in log,
      [ln for ln in log.splitlines() if "개수" in ln])

print("[3] 회귀 — *END 뒤 꼬리는 읽지 않는다(출력이 *END 로 끝난 덱과 바이트 같다)")
deck = "*KEYWORD\n" + nodes() + PROPS + SOLID + "*END\n"
rc, log, ref, els = run_kmm({"model.k": deck})
check("기준 덱(*END 로 끝남) — rc 0·요소 보존·*END 하나", rc == 0 and els == WANT and ref.count("*END") == 1, f"rc={rc}")
parked = "*KEYWORD\n*PART\nparked\n" + f10(2, 1, 1) + "*ELEMENT_SOLID\n" + f"{9:8d}{2:8d}" + "".join(
    f"{n:8d}" for n in range(1, 9)) + "\n*END\n"
for label, tail in (("빈 줄·잡문", "\ngarbage after end line\n"),
                    ("*NODE 로 절점 1 재정의", "*NODE\n       1        5.000000        5.000000        5.000000\n"),
                    ("*INCLUDE parked.k(파트 2·요소 9)", "*INCLUDE\nparked.k\n")):
    rc, log, text, els = run_kmm({"model.k": deck + tail, "parked.k": parked})
    check(f"*END 뒤 {label} — 출력이 기준과 같다", rc == 0 and text == ref, f"rc={rc} els={els}")

print("[4] *END 에서 그 파일 읽기를 멈춘다 — 뒤의 블록이 여럿이어도")
three = ("*NODE\n       1        5.000000        5.000000        5.000000\n*PART\nparked3\n" + f10(3, 1, 1)
         + "*INCLUDE\nparked.k\n")
rc, log, text, els = run_kmm({"model.k": deck + three, "parked.k": parked})
check("메인 덱 *END 뒤 블록 셋(*NODE·*PART·*INCLUDE) — 출력이 기준과 같다", rc == 0 and text == ref, f"rc={rc} els={els}")
check("  뒤 키워드 3개를 읽지 않았다고 알린다", "*END 뒤 키워드 3개" in log,
      [ln for ln in log.splitlines() if "*END" in ln])
inc_main = "*KEYWORD\n" + PROPS + "*INCLUDE\nsub.k\n*END\n"
sub = "*KEYWORD\n" + nodes() + SOLID + "*END\n"
rc, log, inc_ref, els = run_kmm({"model.k": inc_main, "sub.k": sub})
check("기준 — 인클루드가 *END 로 끝남", rc == 0 and els == WANT, f"rc={rc}")
rc, log, text, els = run_kmm({"model.k": inc_main, "sub.k": sub + three, "parked.k": parked})
check("인클루드 *END 뒤 블록 셋 — 그 파일만 끝나고 출력은 기준과 같다", rc == 0 and text == inc_ref, f"rc={rc} els={els}")
parent = "*KEYWORD\n" + PROPS + "*INCLUDE\nn.k\n" + SOLID + "*END\n"
rc, log, par_ref, els = run_kmm({"model.k": parent, "n.k": "*KEYWORD\n" + nodes() + "*END\n"})
check("기준 — 절점만 든 인클루드 뒤에 부모가 요소를 정의", rc == 0 and els == WANT, f"rc={rc}")
rc, log, text, els = run_kmm({"model.k": parent, "n.k": "*KEYWORD\n" + nodes() + "*END\n"
                              + "*NODE\n       1        5.000000        5.000000        5.000000\n"})
check("인클루드의 *END 뒤 블록은 버리고 부모 파일은 이어 읽는다", rc == 0 and text == par_ref, f"rc={rc} els={els}")

print("[5] Ctrl-Z(0x1A) — 그 앞까지만 읽는다")
noend = "*KEYWORD\n" + nodes() + PROPS + SOLID
rc, log, ref0, els = run_kmm({"model.k": noend})
check("기준 — *END 없이 *ELEMENT_SOLID 로 끝남", rc == 0 and els == WANT, f"rc={rc}")
for label, tail in (("마지막 줄 뒤 Ctrl-Z", "\x1a"),
                    ("Ctrl-Z 뒤에 *NODE(절점 1 재정의)", "\x1a\n*NODE\n       1        5.000000        5.000000        5.000000\n")):
    rc, log, text, els = run_kmm({"model.k": noend + tail})
    check(f"{label} — 출력이 기준과 같다", rc == 0 and text == ref0, f"rc={rc} {log[-200:]}")
rc, log, text, els = run_kmm({"model.k": noend[:-1] + "\x1a"})
check("마지막 데이터 줄에 붙은 Ctrl-Z — 그 앞까지 읽는다", rc == 0 and text == ref0, f"rc={rc} {log[-200:]}")

print()
if FAILS:
    print(f"FAIL {len(FAILS)}건 — 실행 폴더를 남긴다: {BASE}")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
shutil.rmtree(BASE)
print("ALL PASS")
