# 컴파일 바이너리가 ascii 로케일로 기동해 한글 입출력이 죽는 것을 막는 런타임 가드
"""
왜 필요한가
-----------
CPython 인터프리터는 PEP 540 에 따라 로케일이 C/POSIX 이면 UTF-8 모드를 자동으로 켠다.
Nuitka 로 컴파일한 산출물은 그 자동 활성화를 받지 못하고 ``sys.flags.utf8_mode == 0``
으로 기동한다. 그래서 ``LANG`` 이 없는 Slurm 환경에서

    locale.getpreferredencoding(False) -> 'ANSI_X3.4-1968'

가 되고, ``subprocess(text=True)`` 의 파이프 디코딩, text-mode ``open()``,
``logging.FileHandler`` 가 전부 ascii 로 동작해 한글에서 죽는다.

``sys.stdout`` 만 UTF-8 로 감싸는 것으로는 못 막는다. 그건 우리 출력만 덮고,
위 세 경로는 ``locale.getpreferredencoding()`` 을 따로 조회하기 때문이다.

한계
----
``sys.getfilesystemencoding()`` 은 인터프리터 시작 시 고정이라 여기서 못 바꾼다.
한글이 든 경로/인자로 자식을 띄우는 경우는 프로세스 시작 전에 환경변수가
설정돼 있어야만 살아난다 (``SHELL_LOCALE_PREAMBLE`` 참조).
"""

import io
import locale
import os
import sys

#: setlocale 시도 순서. glibc 2.35+ 는 C.UTF-8 을 내장하므로 보통 첫 항목에서 성공한다.
_LOCALE_CANDIDATES = ("C.UTF-8", "C.utf8", "en_US.UTF-8", "ko_KR.UTF-8")

_ASCII_ALIASES = ("ascii", "ansi_x3.4-1968", "us-ascii", "c", "posix")

#: 생성한 셸 스크립트(sbatch 등) 맨 앞에 넣을 로케일 전문.
#: 자식 프로세스가 '시작 시점부터' UTF-8 이 되게 하는 유일한 방법 —
#: 파일시스템/argv 인코딩은 시작 후에는 못 바꾼다.
#: ⚠️ f-string 템플릿 안에 그대로 넣을 수 있도록 중괄호를 쓰지 않는다.
SHELL_LOCALE_PREAMBLE = (
    "# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──\n"
    "export LANG=C.UTF-8\n"
    "export LC_ALL=C.UTF-8\n"
    "export PYTHONUTF8=1\n"
    "export PYTHONIOENCODING=utf-8\n"
    "\n"
)


def _is_ascii_like(name):
    return (name or "").strip().lower().replace("_", "-") in _ASCII_ALIASES


def enforce_utf8_runtime():
    """이 프로세스와 자식 프로세스의 텍스트 인코딩을 UTF-8 로 고정한다.

    진입점 최상단에서 한 번만 호출한다. 반환값은 진단용 dict.
    """
    info = {"locale": None, "preferred_before": None, "preferred_after": None,
            "stdio_wrapped": False, "utf8_mode": getattr(sys.flags, "utf8_mode", 0)}

    try:
        info["preferred_before"] = locale.getpreferredencoding(False)
    except Exception:
        pass

    # ① 로케일 — getpreferredencoding() 을 쓰는 모든 경로(subprocess/open/logging)를 한 번에 덮는다
    for cand in _LOCALE_CANDIDATES:
        try:
            locale.setlocale(locale.LC_ALL, cand)
            info["locale"] = cand
            break
        except locale.Error:
            continue

    try:
        info["preferred_after"] = locale.getpreferredencoding(False)
    except Exception:
        pass

    # ② 이미 만들어진 stdout/stderr 는 로케일 변경의 영향을 받지 않으므로 따로 감싼다
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        buf = getattr(stream, "buffer", None)
        if buf is None:
            continue
        if _is_ascii_like(getattr(stream, "encoding", None)):
            setattr(sys, name, io.TextIOWrapper(buf, encoding="utf-8",
                                                errors="replace", line_buffering=True))
            info["stdio_wrapped"] = True

    # ③ 자식 프로세스 — 이 값들은 자식이 '시작할 때' 읽으므로
    #    자식의 파일시스템/argv 인코딩까지 UTF-8 이 된다 (우리 것은 이미 늦었다)
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ["PYTHONUTF8"] = "1"
    if _is_ascii_like(os.environ.get("LANG")) or not os.environ.get("LANG"):
        os.environ["LANG"] = info["locale"] or "C.UTF-8"
    if _is_ascii_like(os.environ.get("LC_ALL")) or not os.environ.get("LC_ALL"):
        os.environ["LC_ALL"] = info["locale"] or "C.UTF-8"

    return info


def job_env_lines(environment):
    """scenario.json 의 ``environment.job_env`` 를 셸 export 줄로 만든다.

    로케일 전문 **뒤에** 놓아야 사용자 지정이 기본값을 이긴다.
    값은 셸 특수문자를 위해 반드시 인용한다.

    예::

        "environment": {"job_env": {"LANG": "ko_KR.UTF-8", "OMP_PROC_BIND": "close"}}
    """
    import shlex
    job_env = (environment or {}).get("job_env") or {}
    if not isinstance(job_env, dict) or not job_env:
        return ""
    out = ["# ── environment.job_env (사용자 지정, 위 기본값을 덮어쓴다) ──\n"]
    for k, v in job_env.items():
        key = str(k).strip()
        if not key or not key.replace("_", "").isalnum():
            continue                      # 셸 주입 방지: 식별자만 허용
        out.append("export %s=%s\n" % (key, shlex.quote(str(v))))
    return "".join(out) + "\n" if len(out) > 1 else ""
