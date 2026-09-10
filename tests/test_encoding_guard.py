# ascii 로케일 사고(D1~D5) 재발을 막는 회귀 테스트
"""
근본 원인은 Nuitka 컴파일 바이너리가 sys.flags.utf8_mode=0 으로 기동하는 것이다.
인터프리터는 PEP 540 으로 자동 UTF-8 이 되므로 이 파일의 검사는 '소스 구조' 와
'생성물 구조' 를 본다. 바이너리 자체 검증은 build 후 e2e 로 따로 한다.

실행: python3 tests/test_encoding_guard.py
"""
import ast
import errno
import io
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = []


def check(name, cond, detail=""):
    print("  %-62s %s" % (name, "OK" if cond else "FAIL"))
    if not cond:
        FAILS.append("%s %s" % (name, detail))


# ─────────────────────────────────────────────────────────────────────
# [1] subprocess 출력 캡처에 encoding 이 빠진 곳이 없는가
#     예외: 파이프를 바이트로 받아 호출부가 직접 처리하는 감사 완료 지점
# ─────────────────────────────────────────────────────────────────────
AUDITED_BYTES = {
    ("KooChainRun", "Popen"),                      # stdout=파일fd / communicate 결과 미사용
    ("KooChainRun", "run"),                        # stdout=파일fd
    ("Runner/CumulativeScenarioRunner.py", "Popen"),  # stderr.decode('utf-8', errors='ignore')
    ("Runner/CumulativeScenarioRunner.py", "run"),    # stdout=파일fd
}


def py_files():
    yield "KooChainRun"
    for p in sorted((ROOT / "Runner").rglob("*.py")):
        yield str(p.relative_to(ROOT))


def scan():
    subs, opens, fh = [], [], []
    for rel in py_files():
        try:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            mod = getattr(f.value, "id", "") if isinstance(f, ast.Attribute) else ""
            kw = {k.arg for k in n.keywords if k.arg}
            if mod == "subprocess" and name in ("run", "check_output", "Popen", "call", "check_call"):
                captures = bool(kw & {"capture_output", "stdout", "stderr"}) or name == "check_output"
                textual = bool(kw & {"text", "universal_newlines"})
                if (captures or textual) and "encoding" not in kw:
                    subs.append((rel, n.lineno, name))
            elif name == "open" and not isinstance(f, ast.Attribute):
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = n.args[1].value or ""
                for k in n.keywords:
                    if k.arg == "mode" and isinstance(k.value, ast.Constant):
                        mode = k.value.value or ""
                if "b" not in (mode or "") and "encoding" not in kw:
                    opens.append((rel, n.lineno))
            elif name == "FileHandler" and "encoding" not in kw:
                fh.append((rel, n.lineno))
    return subs, opens, fh


print("[1] encoding 누락 스캔")
subs, opens, fh = scan()
unaudited = [s for s in subs if (s[0], s[2]) not in AUDITED_BYTES]
check("subprocess 출력 캡처 (감사분 제외) 누락 0", not unaudited, str(unaudited))
check("text-mode open() 누락 0", not opens, str(opens[:5]))
check("logging.FileHandler 누락 0", not fh, str(fh))


# ─────────────────────────────────────────────────────────────────────
# [2] 생성 sbatch 에서 export 가 #SBATCH 앞에 오면 지시자가 무효화된다
#     sbatch 는 첫 비-주석 줄에서 지시자 파싱을 멈춘다
# ─────────────────────────────────────────────────────────────────────
print("\n[2] 생성 sbatch 지시자 순서 (export 가 #SBATCH 를 무효화하지 않는가)")
from Runner.PostprocessShellGenerator import (      # noqa: E402
    build_deep_report_sbatch, build_sphere_sbatch, build_impact_sbatch,
    build_deep_report_sh, build_sphere_report_sh, build_impact_report_sh,
)

ENVV = {"partition": "normal", "ncpu": 4, "job_env": {"OMP_PROC_BIND": "close"}}
generated = {
    "deep_report.sbatch": build_deep_report_sbatch(
        "/data/run", "/data/run/deep_report.sh", environment=ENVV, dependency_id="777"),
    "sphere.sbatch": build_sphere_sbatch("/data/out", environment=ENVV, dependency_ids=["777"]),
    "impact.sbatch": build_impact_sbatch("/data/out", environment=ENVV, dependency_ids=["777"]),
    "deep_report.sh": build_deep_report_sh("/data/run", sif_path="/x.sif"),
    "sphere_report.sh": build_sphere_report_sh("/data/out", sif_path="/x.sif"),
    "impact_report.sh": build_impact_report_sh("/data/out", sif_path="/x.sif"),
}


def first_command_line(text):
    """sbatch 가 지시자 파싱을 멈추는 지점 (shebang 이후 첫 비-주석·비-공백 줄)."""
    for i, l in enumerate(text.splitlines()):
        if i == 0 and l.startswith("#!"):
            continue
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        return i, l
    return None, None


for name, text in generated.items():
    lines = text.splitlines()
    sb = [i for i, l in enumerate(lines) if l.startswith("#SBATCH")]
    idx, cmd = first_command_line(text)
    if sb:
        check("%-22s 모든 #SBATCH 가 첫 명령줄보다 앞" % name,
              idx is not None and max(sb) < idx, "첫 명령줄 %r @%s" % (cmd, idx))
    check("%-22s 로케일 전문 포함" % name, "export LC_ALL=C.UTF-8" in text)

# job_env 는 기본값 뒤에 와야 덮어쓸 수 있다
t = generated["deep_report.sbatch"]
check("job_env 가 로케일 기본값 뒤", t.index("OMP_PROC_BIND") > t.index("export LC_ALL"))
check("#SBATCH --dependency 보존", "#SBATCH --dependency=afterok:777" in t)
check("#SBATCH --partition 보존", "#SBATCH --partition=normal" in t)

# 셸 주입 방어
from Runner._encoding import job_env_lines                     # noqa: E402
inj = job_env_lines({"job_env": {"A;rm -rf /": "1", "OK_VAR": "a b'c"}})
check("job_env 부적합 키 거부", "rm -rf" not in inj, inj)
check("job_env 값 인용", "'a b'" in inj or '"a b' in inj or "\\'" in inj, inj)


# ─────────────────────────────────────────────────────────────────────
# [3] 증분 f.write 로 만드는 sbatch 도 전문이 마지막 #SBATCH 뒤에 있는가
# ─────────────────────────────────────────────────────────────────────
print("\n[3] 증분 sbatch 생성부 소스 구조")


def has_sbatch(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "#SBATCH" in n.value:
            return True
    return False


for rel in ["Runner/SlurmSubmitter.py", "Runner/DOEParallelOptimizer.py",
            "Runner/LargeScaleDOEManager.py"]:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    blocks = 0
    ok = True
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        if not any(isinstance(i.context_expr, ast.Call)
                   and getattr(i.context_expr.func, "id", None) == "open" for i in node.items):
            continue
        sb_last = pre_at = None
        for st in node.body:
            if has_sbatch(st):
                sb_last = st.end_lineno
            src = ast.dump(st)
            if "SHELL_LOCALE_PREAMBLE" in src:
                pre_at = st.lineno
        if sb_last is None:
            continue
        blocks += 1
        if pre_at is None or pre_at < sb_last:
            ok = False
    check("%-34s 전문이 마지막 #SBATCH 뒤 (%d블록)" % (rel, blocks), ok and blocks > 0)


# ─────────────────────────────────────────────────────────────────────
# [4] 런타임 가드
# ─────────────────────────────────────────────────────────────────────
print("\n[4] enforce_utf8_runtime")
from Runner._encoding import enforce_utf8_runtime, SHELL_LOCALE_PREAMBLE   # noqa: E402
info = enforce_utf8_runtime()
import locale                                                              # noqa: E402
check("getpreferredencoding 이 UTF-8", "utf-8" in locale.getpreferredencoding(False).lower(), str(info))
check("자식용 PYTHONUTF8=1", os.environ.get("PYTHONUTF8") == "1")
check("자식용 LC_ALL 이 UTF-8", "UTF-8" in os.environ.get("LC_ALL", ""))
check("셸 전문에 중괄호 없음 (f-string 안전)",
      "{" not in SHELL_LOCALE_PREAMBLE and "}" not in SHELL_LOCALE_PREAMBLE)


# ─────────────────────────────────────────────────────────────────────
# [5] D5 — 닫힌 fd(EBADF)를 120초 재시도하지 않고 즉시 실패하는가
# ─────────────────────────────────────────────────────────────────────
print("\n[5] _flock_with_timeout")
from Runner.CumulativeScenarioRunner import _flock_with_timeout   # noqa: E402
import fcntl, tempfile, time                                      # noqa: E402

f = open(tempfile.mktemp(), "a", encoding="utf-8")
bad_fd = f.fileno()
f.close()                       # fd 를 닫아 EBADF 를 만든다
t0 = time.time()
raised = None
try:
    _flock_with_timeout(bad_fd, fcntl.LOCK_EX, timeout=120)
except Exception as e:
    raised = e
el = time.time() - t0
check("EBADF 는 즉시 실패", raised is not None and el < 5, "%.1fs %r" % (el, raised))
check("EBADF 를 TimeoutError(=stale lock)로 오진하지 않음",
      not isinstance(raised, TimeoutError), repr(raised))
check("EBADF 오류에 errno 명시", isinstance(raised, OSError) and raised.errno == errno.EBADF,
      repr(raised))

# 정상 경로는 여전히 동작해야 한다
lf = open(tempfile.mktemp(), "a", encoding="utf-8")
try:
    _flock_with_timeout(lf, fcntl.LOCK_EX, timeout=5)
    _flock_with_timeout(lf, fcntl.LOCK_UN)
    check("정상 lock/unlock 회귀 없음", True)
except Exception as e:
    check("정상 lock/unlock 회귀 없음", False, repr(e))
finally:
    lf.close()


# ─────────────────────────────────────────────────────────────────────
# [6] D4 — 결정적 실패는 재시도하지 않는가
# ─────────────────────────────────────────────────────────────────────
print("\n[6] 결정적 실패 분류")
from Runner.CumulativeScenarioRunner import CumulativeScenarioRunner as CSR  # noqa: E402


class _Stub:
    DETERMINISTIC_ERRORS = CSR.DETERMINISTIC_ERRORS
    _run_step_classified = CSR._run_step_classified

    def __init__(self, exc):
        self.exc = exc
        self.calls = 0

    def run_single_step(self, doe, cfg):
        self.calls += 1
        raise self.exc


for exc, label, want in [
    (UnicodeDecodeError("ascii", b"\xea", 0, 1, "ordinal not in range(128)"), "UnicodeDecodeError", True),
    (FileNotFoundError(2, "no such file"), "FileNotFoundError", True),
    (RuntimeError("솔버 일시 오류"), "RuntimeError(일시적)", False),
]:
    st = _Stub(exc)
    ok, det = st._run_step_classified(1, {})
    check("%-24s → 결정적=%s" % (label, want), (ok is False) and (det is want), str((ok, det)))

# 락 없는 폴백이 남아 있지 않은가
csr_src = (ROOT / "Runner/CumulativeScenarioRunner.py").read_text(encoding="utf-8")
check("lock 없이 index 직접 읽기 폴백 제거", "lock 없이 index 직접 읽기" not in csr_src)
check("lock 없이 직접 쓰기 폴백 제거", "lock 없이 직접 쓰기" not in csr_src)


print("\n" + "=" * 72)
if FAILS:
    print("실패 %d건" % len(FAILS))
    for x in FAILS:
        print("  -", x)
    sys.exit(1)
print("전부 통과")
