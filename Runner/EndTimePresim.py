# prepare 때 KMM RIGID_DROP_ENDTIME(강체 낙하 사전 해석)을 돌려 DROP 스텝마다 쓸 각도별 종료 시간 표를 마련하는 모듈
"""
simulation_params.endtime_presim — KooChainRun prepare(CumulativeDesigner.save_runner_config)가 부른다.

  켜지면(enabled=true)
    1. DOE 의 DROP 스텝 각도(roll, pitch, yaw)를 값으로 중복 없이 모아 <output_dir>/endtime_presim/1/angles.csv 를 쓴다
    2. KMM RIGID_DROP_ENDTIME 옵션 파일을 쓰고 러너와 같은 방식(koomeshmodifier_path·apptainer 감싸기·시간 제한)으로 돌린다.
       중력 끔(기본)이면 옵션 파일에 PresimStrongContact,<strong_contact> 줄이 들어간다(v133 — 접근 속도가 strong_contact·v0
       이상인 마지막 재접촉 묶음 끝 + 여유). 그 KMM 이 이 키를 아는지 --help RIGID_DROP_ENDTIME 으로 먼저 본다
    3. 작업 폴더의 <base>_endtime.csv 를 읽어 모든 각도가 있고 endtim > 0 인지 본다 — 아니면 prepare 를 멈춘다.
       표 메타 endtime_rule·strong_contact 도 본다(check_table_rule)
  table 을 주면 2 를 건너뛰고 그 표를 쓴다. 각도는 낙하 방향 사이 각 0.01° 안으로 찾는다(KMM DROP_ATTITUDE 와 같은 규칙).

  runner_config 에 남기는 것(꺼져 있으면 키 자체가 없다)
    scenario.endtime_tables : [{"template", "table"(절대 경로), "source": "presim" | "table", "angles"}]
    scenario.doe_endtim     : {doe: {step: endtim}} — 보기용. KMM 은 표에서 직접 찾는다
  DROP 스텝 설정(누적 러너·대규모·배치)은 endtime_table_for_step() 으로 표 경로를 받아 EndTimeTable 줄을 넣는다.

KCR runner_config 의 템플릿은 project.model_file 하나다(누적 2스텝부터는 앞 스텝 _dti.k 에서 시작하지만 사전 해석은
원래 강체 형상으로 한다 — 근사). 그래서 작업 폴더 번호는 1 하나다.
KCR 의 Nuitka 빌드는 Runner 패키지만 넣으므로 표는 KooEndTimeTable(occProject)을 import 하지 않고 표준 라이브러리로 읽는다.
낙하 방향 d = Rz(-yaw)·Ry(-pitch)·Rx(-roll)·(0,0,-1) 은 KooEndTimeTable.drop_direction 과 같은 식이다(시험에서 대조).
"""
import csv
import math
import os
import re
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

MARKER = "[ENDTIME_PRESIM_FAILED]"
OPTION_FILE = "rigid_drop_endtime.txt"   # KMM 은 옵션 이름의 .txt 를 .log 로 바꿔 로그를 쓴다 — 확장자는 꼭 .txt
STDOUT_FILE = "kmm_stdout.log"
MATCH_TOL_DEG = 0.01
PRESIM_TIMEOUT = 21600   # 사전 해석 KMM 시간 제한 기본 6 시간 (presim_timeout_seconds) — 러너 KMM 의 7 일과 따로
DEFAULTS = {"enabled": False, "table": None, "restitution": [0.1, 0.3, 0.5], "friction": 0.5,
            "gravity": False, "strong_contact": 0.3, "margin_ms": 1.0, "exclude_parts": [], "workers": 8,
            "presim_timeout_seconds": PRESIM_TIMEOUT}
STRONG_CONTACT_TOL = 1e-9   # 표 메타 strong_contact 와 옵션이 이보다 더 다르면 멈춘다 (메타는 유효 10자리)


class EndTimePresimError(RuntimeError):
    """사전 해석·표 검증 실패 — prepare 를 멈춘다(조용히 tFinal 로 돌아가지 않는다)."""

    def __init__(self, msg):
        super().__init__(f"{MARKER} {msg}")


def _number(key, v, lo, hi=None, above=False):
    """v 가 lo 이상(above=True 면 lo 보다 큰), hi 이하인 숫자인지 본다 — bool 은 숫자로 치지 않는다."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not (
            (v > lo if above else v >= lo) and (hi is None or v <= hi)):
        span = f"{lo} 보다 큰" if above else f"{lo} 이상" if hi is None else f"{lo}~{hi}"
        raise EndTimePresimError(f"simulation_params.endtime_presim.{key} 는 {span} 숫자여야 한다: {v!r} (bad value)")
    return v


def presim_options(sim_params):
    """simulation_params.endtime_presim → 기본값을 채운 dict. 없거나 꺼져 있으면 None. 모르는 키는 경고만 한다."""
    raw = (sim_params or {}).get("endtime_presim")
    if raw is None or raw is False:
        return None
    if raw is True:
        raw = {"enabled": True}
    if not isinstance(raw, dict):
        raise EndTimePresimError(f"simulation_params.endtime_presim 은 객체여야 한다: {raw!r} (bad value)")
    for k in raw:
        if k not in DEFAULTS:
            print(f"⚠️  simulation_params.endtime_presim.{k}: 모르는 키라 무시한다 (unknown key, ignored)")
    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        raise EndTimePresimError(f"simulation_params.endtime_presim.enabled 는 true/false 여야 한다: {enabled!r} (bad value)")
    if not enabled:
        return None
    opts = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    e = opts["restitution"]
    opts["restitution"] = [_number("restitution", x, 0.0, 1.0) for x in (e if isinstance(e, list) else [e])]
    if not opts["restitution"]:
        raise EndTimePresimError("simulation_params.endtime_presim.restitution 이 비어 있다 (bad value)")
    _number("friction", opts["friction"], 0.0)
    _number("margin_ms", opts["margin_ms"], 0.0)
    _number("strong_contact", opts["strong_contact"], 0.0, above=True)
    _number("presim_timeout_seconds", opts["presim_timeout_seconds"], 1)
    if not isinstance(opts["gravity"], bool):
        raise EndTimePresimError(f"simulation_params.endtime_presim.gravity 는 true/false 여야 한다: {opts['gravity']!r} (bad value)")
    if opts["gravity"] and "strong_contact" in raw:   # 중력 켬은 v132 규칙 — KMM 에 넘기지 않는다(build_option_text)
        print("⚠️  simulation_params.endtime_presim.strong_contact: gravity=true 면 쓰지 않는다 — 중력 켬 표는 첫 재접촉 "
              "묶음 끝 + 여유(v132 규칙)다 (ignored with gravity)")
    w = opts["workers"]
    if isinstance(w, bool) or not isinstance(w, int) or w < 1:
        raise EndTimePresimError(f"simulation_params.endtime_presim.workers 는 1 이상 정수여야 한다: {w!r} (bad value)")
    parts = opts["exclude_parts"]
    parts = list(parts) if isinstance(parts, list) else [parts]
    if any(isinstance(p, bool) or not isinstance(p, int) for p in parts):
        raise EndTimePresimError(f"simulation_params.endtime_presim.exclude_parts 는 PID 정수 목록이어야 한다: {parts!r} (bad value)")
    opts["exclude_parts"] = parts
    if opts["table"] is not None and not (isinstance(opts["table"], str) and opts["table"].strip()):
        raise EndTimePresimError(f"simulation_params.endtime_presim.table 은 표 파일 경로여야 한다: {opts['table']!r} (bad value)")
    return opts


def drop_direction(roll, pitch, yaw=0.0):
    """KMM DropAttitude 규약의 낙하 방향(덱 좌표계) — KooEndTimeTable.drop_direction 과 같은 식."""
    r, p, y = (math.radians(float(v)) for v in (roll, pitch, yaw))
    dx, dy, dz = math.sin(p) * math.cos(r), -math.sin(r), -math.cos(p) * math.cos(r)
    return (dx * math.cos(y) + dy * math.sin(y), -dx * math.sin(y) + dy * math.cos(y), dz)


def _same_direction(d1, d2, tol_deg=MATCH_TOL_DEG):
    return sum(a * b for a, b in zip(d1, d2)) >= math.cos(math.radians(tol_deg))


def direction_lookup(rows):
    """표 줄(dir·endtim) → 낙하 방향 d 를 받아 사이 각 0.01° 이하인 줄들의 endtim 최대(없으면 None)를 돌려주는 함수.
    각도마다 표 전체를 순수 파이썬으로 훑으면 2만 × 2만에 100 초 가까이 걸려 numpy 행렬곱(D·d) 한 번으로 찾는다."""
    import numpy as np
    D = np.array([r["dir"] for r in rows], dtype=float).reshape(-1, 3)
    E = np.array([r["endtim"] for r in rows], dtype=float)
    cos_tol = math.cos(math.radians(MATCH_TOL_DEG))

    def find(d):
        hit = D @ np.asarray(d, dtype=float) >= cos_tol
        return float(E[hit].max()) if hit.any() else None
    return find


def find_endtim(rows, roll, pitch, yaw=0.0):
    """표에서 낙하 방향 사이 각이 0.01° 이하인 줄들의 endtim 최대(KMM DROP_ATTITUDE 와 같은 규칙). 없으면 None."""
    return direction_lookup(rows)(drop_direction(roll, pitch, yaw))


def _drop_steps(runner_steps):
    return {int(s["step"]) for s in runner_steps or [] if s.get("mode") == "DROP"}


def _unique_name(raw, used, i):
    base = re.sub(r"[^A-Za-z0-9_+.\-]", "_", str(raw or "")) or f"A{i:04d}"
    name, k = base, 2
    while name in used:
        name, k = f"{base}_{k}", k + 1
    used.add(name)
    return name


def collect_drop_angles(doe_angles, runner_steps):
    """DOE 각도표에서 DROP 스텝 각도만 값으로 중복 없이 → [(name, roll, pitch, yaw), ...] (DOE·스텝 순서).

    doe_angles: {doe(1-based): {step: {angle_name, roll, pitch, yaw}}} — 키는 str·int 어느 쪽이든 된다.
    이름은 처음 나온 DOE 각도 이름(파일에 안전한 글자만, 겹치면 _2, _3 …)이다. 열 스텝(0/0/0) 등 DROP 이 아닌 스텝은 뺀다.
    """
    drop = _drop_steps(runner_steps)
    out, seen, used = [], set(), set()
    for doe in sorted(doe_angles, key=int):
        steps = doe_angles[doe]
        for step in sorted(steps, key=int):
            if int(step) not in drop:
                continue
            a = steps[step]
            key = (float(a["roll"]), float(a["pitch"]), float(a["yaw"]))
            if key not in seen:
                seen.add(key)
                out.append((_unique_name(a.get("angle_name"), used, len(out) + 1),) + key)
    return out


def write_angles_csv(path, angles):
    """KMM AngleFile — name,roll,pitch,yaw (도). 값은 DOE 와 같은 float 그대로(스텝 설정의 Euler 줄과 같은 글자)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "roll", "pitch", "yaw"])
        w.writerows(angles)


def build_option_text(template, angle_file, height, opts, fibonacci=None, strong_contact=None):
    """KMM RIGID_DROP_ENDTIME 옵션 파일. StepConfigBuilder 처럼 '키,값' 한 줄씩이고 블록 안에 빈 줄이 없다
    (KMM 은 빈 줄에서 블록을 끝낸다). ExcludePart 는 줄 때만 쓴다.
    fibonacci=N 이면 AngleFile 대신 'Fibonacci,N'(실제 낙하 방향 균일 N 점)을 쓴다 — impact_conditions 사전 해석.
    strong_contact 를 주면 PresimGravity 다음에 'PresimStrongContact,<값>'(v133 KMM 키)을 쓴다 — endtime_presim 중력 끔만
    준다. impact_conditions·중력 켬은 주지 않아 옵션 파일이 v132 와 바이트까지 같다."""
    lines = ["*Inputfile", template, "*Mode", "RIGID_DROP_ENDTIME,1", "**RigidDropEndtime,1",
             f"Height,{height}",
             f"Fibonacci,{fibonacci}" if fibonacci else f"AngleFile,{angle_file}",
             "Restitution," + ",".join(str(e) for e in opts["restitution"]),
             f"Friction,{opts['friction']}",
             f"PresimGravity,{1 if opts['gravity'] else 0}"]
    if strong_contact is not None:
        lines.append(f"PresimStrongContact,{strong_contact}")
    lines.append(f"MarginMs,{opts['margin_ms']}")
    if opts["exclude_parts"]:
        lines.append("ExcludePart," + ",".join(str(p) for p in opts["exclude_parts"]))
    lines += [f"Workers,{opts['workers']}", "**EndRigidDropEndtime", "*End"]
    return "\n".join(lines) + "\n"


def batch_kmm_path(env):
    """batch_koomeshmodifier(헤드 노드에서 KMM 한 번으로 모든 DOE)가 돌릴 KMM → (경로, 호스트 KMM 으로 바꿨나).
    SIF 가 없고 경로가 /opt/ 로 시작하면 koochainrun_path 옆의 호스트 KooMeshModifier 를 쓴다 —
    KooChainRun _prepare_batch_koomeshmodifier 가 이 함수를 부른다(prepare 의 KMM 버전 확인과 같은 실행 파일)."""
    path = env.get("koomeshmodifier_path", "/opt/SmartTwinPreprocessor/bin/KooMeshModifier")
    if not env.get("apptainer_sif", "") and path.startswith("/opt/"):
        kcr_host = env.get("koochainrun_path", "")
        if kcr_host:
            host = os.path.join(str(Path(kcr_host).parent), "KooMeshModifier")
            if os.path.isfile(host):
                return host, True
    return path, False


def _head_kmm(environment, batch):
    """그 표 줄을 읽을 KMM → (실행 파일, 사람이 읽을 설명). batch=True 면 batch_koomeshmodifier 의 것, 아니면 러너의 것."""
    if batch:
        kmm = batch_kmm_path(environment)[0]
    else:
        from Runner.PathResolver import find_koomeshmodifier
        kmm = environment.get("koomeshmodifier_path") or find_koomeshmodifier()
    sif = environment.get("apptainer_sif")
    return kmm, (f"SIF {sif} 안의 {kmm}" if sif else kmm) + (" — batch_koomeshmodifier" if batch else "")


def head_kmm_command(environment, args, batch=False):
    """prepare(헤드 노드)에서 KMM(args)을 돌릴 명령 → (cmd, 끝나면 부를 정리 함수).

    실행 파일은 그 표 줄을 읽을 KMM 과 같다(_head_kmm). apptainer 감싸기는 러너와 같은 ApptainerWrapper 지만 임시 폴더는
    environment.apptainer_tmpdir(없으면 시스템 임시 폴더) 아래 이번 실행 것(apptainer_job_<pid>)이다. 새로 만들었으면 정리
    함수가 지우고 APPTAINER_TMPDIR 를 되돌린다 — 러너 기본값 /opt/tmp 는 헤드 노드에 없을 수 있고, 남은 폴더가 쌓인다.
    """
    from Runner.CumulativeScenarioRunner import ApptainerWrapper
    kmm = _head_kmm(environment, batch)[0]
    if not environment.get("apptainer_sif"):
        return [kmm] + list(args), lambda: None
    w = ApptainerWrapper({"environment": {**environment,
                                          "apptainer_tmpdir": environment.get("apptainer_tmpdir") or tempfile.gettempdir()}})
    made, old = not os.path.isdir(w.apptainer_tmpdir), os.environ.get("APPTAINER_TMPDIR")
    cmd = w.wrap_command([kmm] + list(args), use_lsdyna=False)

    def done():
        if made:
            shutil.rmtree(w.apptainer_tmpdir, ignore_errors=True)
        if old is None:
            os.environ.pop("APPTAINER_TMPDIR", None)
        else:
            os.environ["APPTAINER_TMPDIR"] = old
    return cmd, done


def _run_group(cmd, cwd, timeout, stdout):
    """cmd 를 새 세션(프로세스 묶음)으로 돌린다 → (rc, stdout 이 PIPE 면 글 아니면 None). stderr 는 stdout 에 합친다.
    시간 초과·Ctrl-C 면 묶음 전체(apptainer·KMM·작업자 프로세스)를 SIGKILL 하고 예외를 다시 올린다 — subprocess.run 의
    시간 초과는 맨 앞 프로세스만 죽여 KMM 작업자가 헤드 노드에 남는다. 새 세션이라 터미널 Ctrl-C 는 직접 넘겨야 한다."""
    p = subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, start_new_session=True,
                         text=True, encoding="utf-8", errors="replace")
    try:
        out, _ = p.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.wait()
        raise
    return p.returncode, out


def run_kmm(environment, work_dir, timeout, batch=False):
    """KMM 을 러너(_run_koomeshmodifier)와 같은 실행 파일·apptainer 감싸기·cwd 로 돈다(batch=True 면 batch_koomeshmodifier 의
    KMM — 표를 만든 KMM 이 표를 읽는다). 시간 제한은 presim_timeout_seconds, 넘으면 프로세스 묶음째 죽인다(_run_group).

    다른 점: 작업 폴더를 KMM 둘째 인자(working_directory)로 절대 경로로 준다. KMM 은 덱을 읽으며 덱 폴더로 chdir 하므로
    인자 하나일 때의 기본값 '.' 은 그 뒤 템플릿 폴더를 가리킨다 — 산출물이 사용자 템플릿 옆에 떨어지지 않게 한다.
    헤드 노드에서 돌므로 러너의 cleanup_after_exec(사용자의 squashfuse 를 모두 pkill)는 부르지 않는다.
    출력은 메모리에 담지 않고 작업 폴더의 kmm_stdout.log 에 쓴다. → (rc, cmd, 로그 경로)
    """
    cmd, done = head_kmm_command(environment, [OPTION_FILE, work_dir], batch)
    log_path = os.path.join(work_dir, STDOUT_FILE)
    try:
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("$ " + " ".join(cmd) + "\n")
            log.flush()
            rc, _ = _run_group(cmd, work_dir, timeout, log)
    finally:
        done()
    return rc, cmd, log_path


def _tail(path, n=20):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()[-n:]
    except OSError:
        return
    print(f"  ── {path} 끝 {len(lines)}줄 ──")
    for line in lines:
        print("  | " + line)


def read_endtime_csv(path):
    """<base>_endtime.csv → (meta, rows). '#' 줄은 meta, rows 는 name·roll·pitch·yaw·endtim·dir·raw(줄 글자 그대로).
    형식이 틀리면 멈춘다. 엑셀이 붙이는 BOM 은 떼고 읽는다(utf-8-sig) — 남으면 첫 '#' 메타 줄을 칸 이름으로 잘못 읽는다."""
    meta, body = {}, []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for line in f:
            if line.startswith("#"):
                k, _, v = line[1:].strip().partition("=")
                meta[k.strip()] = v.strip()
            elif line.strip():
                body.append(line)
    reader = csv.DictReader(body)
    missing = [c for c in ("roll", "pitch", "yaw", "endtim") if c not in (reader.fieldnames or [])]
    if missing:
        raise EndTimePresimError(f"표 {path} 에 칸 {missing} 이 없다 (missing columns)")
    rows = []
    for n, raw in enumerate(reader, start=1):
        try:
            row = {"name": (raw.get("name") or "").strip(), "roll": float(raw["roll"]), "pitch": float(raw["pitch"]),
                   "yaw": float(raw["yaw"]), "endtim": float(raw["endtim"])}
        except (TypeError, ValueError):
            raise EndTimePresimError(f"표 {path} {n}번째 줄의 숫자를 읽지 못했다: {dict(raw)} (bad number)") from None
        if not row["endtim"] > 0.0 or math.isinf(row["endtim"]):
            raise EndTimePresimError(f"표 {path} {n}번째 줄({row['name']}) endtim 이 양수가 아니다: {raw['endtim']!r} "
                                     f"(endtim must be positive)")
        row["dir"] = drop_direction(row["roll"], row["pitch"], row["yaw"])
        row["raw"] = raw
        rows.append(row)
    if not rows:
        raise EndTimePresimError(f"표 {path} 에 각도 줄이 없다 (no data rows)")
    return meta, rows


def _endtims_for(rows, angles, table, by_name):
    """요청한 각도마다 endtim → {(roll, pitch, yaw): endtim}. 하나라도 없으면 멈춘다.
    by_name(사전 해석 표): 우리가 쓴 이름의 줄이 있고 그 줄의 방향도 같아야 한다. 값은 KMM 과 같은 방향 찾기로 정한다."""
    named = {r["name"]: r for r in rows}
    find = direction_lookup(rows)
    out, missing = {}, []
    for name, roll, pitch, yaw in angles:
        d = drop_direction(roll, pitch, yaw)
        if by_name and (name not in named or not _same_direction(named[name]["dir"], d)):
            missing.append(name)
            continue
        e = find(d)
        if e is None:
            missing.append(f"{name}({roll}, {pitch}, {yaw})")
            continue
        out[(roll, pitch, yaw)] = e
    if missing:
        more = " …" if len(missing) > 10 else ""
        raise EndTimePresimError(f"표 {table} 에 DROP 각도 {len(missing)}/{len(angles)}개가 없다: "
                                 f"{', '.join(missing[:10])}{more} (angles missing)")
    return out


def _run_presim(opts, sim_params, environment, template, work, angles, batch=False):
    """angles.csv·옵션 파일을 쓰고 KMM 을 돌려 <base>_endtime.csv 경로를 돌려준다. 실패하면 멈춘다."""
    if not os.path.isfile(template):
        raise EndTimePresimError(f"사전 해석할 템플릿(project.model_file)이 없다: {template} (template not found)")
    os.makedirs(work, exist_ok=True)
    base = os.path.splitext(os.path.basename(template))[0]
    table = os.path.join(work, f"{base}_endtime.csv")
    if os.path.exists(table):
        os.remove(table)   # 지난 prepare 의 표를 이번 결과로 잘못 읽지 않게
    angle_file = os.path.join(work, "angles.csv")
    write_angles_csv(angle_file, angles)
    with open(os.path.join(work, OPTION_FILE), "w", encoding="utf-8") as f:
        f.write(build_option_text(template, angle_file, sim_params.get("height", 1500), opts,
                                  strong_contact=None if opts["gravity"] else opts["strong_contact"]))
    timeout = opts["presim_timeout_seconds"]
    print(f"  [endtime_presim] KMM RIGID_DROP_ENDTIME 실행 — 각도 {len(angles)}개, 작업 폴더 {work}")
    log_path = os.path.join(work, STDOUT_FILE)
    try:
        rc, _cmd, log_path = run_kmm(environment, work, timeout, batch)
    except subprocess.TimeoutExpired:
        _tail(log_path)
        raise EndTimePresimError(f"KMM 사전 해석이 {timeout}초 안에 끝나지 않았다 — KMM 프로세스 묶음을 멈췄다. 각도·작업자가 "
                                 f"많으면 simulation_params.endtime_presim.presim_timeout_seconds 를 늘릴 것(기본 "
                                 f"{PRESIM_TIMEOUT}). 로그 {log_path} (timeout)") from None
    except OSError as e:
        raise EndTimePresimError(f"KMM 을 실행하지 못했다: {e} — environment.koomeshmodifier_path·apptainer_sif·"
                                 f"apptainer_tmpdir 를 확인할 것 (cannot run KMM)") from None
    if rc == 3:
        _tail(log_path)
        raise EndTimePresimError(f"KMM 이 덱을 읽으며 요소를 버렸다(종료 코드 3 — 예: *PART_INERTIA 파트, 정의 안 된 절점). "
                                 f"질량특성·볼록 껍질이 모자랄 수 있다 — {os.path.join(work, base + '_rigidbody.json')} 의 "
                                 f"warnings·excluded_parts 를 볼 것. 받아들일 수 있으면 검토한 표를 table 로 줄 것. 로그 {log_path} "
                                 f"(KMM rc=3 element loss)")
    if rc != 0:
        _tail(log_path)
        raise EndTimePresimError(f"KMM 사전 해석이 실패했다(종료 코드 {rc}) — 로그 {log_path} (KMM rc={rc})")
    if not os.path.isfile(table):
        _tail(log_path)
        raise EndTimePresimError(f"KMM 이 끝났는데 표가 없다: {table} — 로그 {log_path} (table not written)")
    return table


def prepare_endtime_tables(sim_params, environment, model_file, output_dir, scenario_dir, doe_angles, runner_steps,
                           batch=False):
    """켜져 있으면 표를 마련해 (endtime_tables, doe_endtim), 꺼져 있거나 DROP 스텝이 없으면 (None, None).

    doe_angles: save_runner_config 의 DOE 각도표(1-based), runner_steps: scenario.steps([{step, mode, ...}]).
    batch: batch_koomeshmodifier 로 돌 시나리오인가 — 그러면 표 줄을 읽을 KMM(버전 확인·사전 해석)이 헤드 노드 일괄 KMM 이다.
    실패(러너 KMM 이 EndTimeTable 을 모름·사전 해석 KMM 이 PresimStrongContact 를 모름(중력 끔, v132 이하)·KMM rc≠0(3 = 요소
    소실)·시간 초과·표 없음·각도 빠짐·endtim≤0·table 파일 없음·표 높이·v0·사전 해석 중력이 시나리오와 다름·표 strong_contact 가
    옵션과 다름·mm-kg-ms·mm-g-ms 덱인데 simulation_params.gravity 없음)는 EndTimePresimError — prepare 가 멈춘다.
    """
    opts = presim_options(sim_params)
    if opts is None:
        return None, None
    angles = collect_drop_angles(doe_angles, runner_steps)
    if not angles:
        print("⚠️  simulation_params.endtime_presim: DROP 스텝이 없어 사전 해석을 건너뛴다 (no DROP step)")
        return None, None
    template = os.path.abspath(model_file)
    # 러너가 쓸 KMM 이 EndTimeTable 을 아는지 먼저 — 옛 KMM 은 그 줄을 다른 키로 잘못 읽는다(table 지름길도 같다)
    check_kmm_supports(environment, ("EndTimeTable",), os.path.abspath(output_dir), EndTimePresimError, batch)
    if opts["table"]:
        table = opts["table"].strip()
        table = os.path.abspath(table if os.path.isabs(table) else os.path.join(scenario_dir, table))
        if not os.path.isfile(table):
            raise EndTimePresimError(f"simulation_params.endtime_presim.table 파일이 없다: {table} (table not found)")
        source = "table"
        print(f"  [endtime_presim] 사전 해석을 건너뛰고 주어진 표를 쓴다: {table}")
    else:
        if not opts["gravity"]:   # 옵션 파일에 PresimStrongContact 줄이 들어간다 — v132 KMM 은 그 줄에서 rc 1 로 죽는다
            check_kmm_strong_contact(environment, os.path.abspath(output_dir), batch)
        table = _run_presim(opts, sim_params, environment, template,
                            os.path.abspath(os.path.join(output_dir, "endtime_presim", "1")), angles, batch)
        source = "presim"
    meta, rows = read_endtime_csv(table)
    check_table_drop(meta, sim_params, table, EndTimePresimError, "endtime_presim", gravity=opts["gravity"],
                     template=template)
    check_table_rule(meta, table, opts["strong_contact"])
    per_angle = _endtims_for(rows, angles, table, by_name=(source == "presim"))
    report_reach(rows, sim_params, "endtime_presim")
    drop = _drop_steps(runner_steps)
    doe_endtim = {}
    for doe in sorted(doe_angles, key=int):
        for step in sorted(doe_angles[doe], key=int):
            if int(step) in drop:
                a = doe_angles[doe][step]
                doe_endtim.setdefault(str(doe), {})[str(step)] = \
                    per_angle[(float(a["roll"]), float(a["pitch"]), float(a["yaw"]))]
    vals = list(per_angle.values())
    print(f"✅ 각도별 종료 시간 표: {table} — DROP 각도 {len(angles)}개, endtim {min(vals):g} ~ {max(vals):g} "
          f"(덱 시간 단위)")
    report_time_factor(doe_endtim, sim_params, "endtime_presim")
    return [{"template": template, "table": table, "source": source, "angles": len(angles)}], doe_endtim


KMM_HELP_TIMEOUT = 300
_KMM_HELP_CACHE = {}   # (실행 파일, SIF, 모드) → (--help 종료 코드, 출력)


def _kmm_help(environment, mode, work_dir, err, batch=False):
    """그 표 줄을 읽을 KMM 의 '--help <mode>' → (종료 코드, 출력, 사람이 읽을 KMM 설명).

    실행 파일·apptainer 감싸기는 head_kmm_command 와 같다(러너 KMM, batch=True 면 batch_koomeshmodifier 의 KMM — 사전 해석
    run_kmm 도 같은 실행 파일). prepare(프로세스)마다 (실행 파일, SIF, 모드) 하나에 한 번만 묻고 기억한다.
    시간 초과·실행 못 함은 err 로 멈춘다.
    """
    kmm, where = _head_kmm(environment, batch)
    key = (kmm, environment.get("apptainer_sif") or "", mode)
    try:
        if key not in _KMM_HELP_CACHE:
            os.makedirs(work_dir, exist_ok=True)
            cmd, done = head_kmm_command(environment, ["--help", mode], batch)
            try:
                rc, out = _run_group(cmd, work_dir, KMM_HELP_TIMEOUT, subprocess.PIPE)
            finally:
                done()
            _KMM_HELP_CACHE[key] = (rc, out or "")
    except subprocess.TimeoutExpired:
        raise err(f"러너가 쓸 KMM({where})의 --help {mode} 가 {KMM_HELP_TIMEOUT}초 안에 끝나지 않았다 "
                  f"(KMM version check timeout)") from None
    except OSError as e:
        raise err(f"KMM 을 실행하지 못했다: {e} — 러너가 쓸 KMM({where}). prepare 는 헤드 노드에서 그 KMM 으로 버전을 확인한다"
                  f"(table 을 줘도) — 헤드 노드에서 돌 수 있어야 한다. environment.koomeshmodifier_path·apptainer_sif·"
                  f"apptainer_tmpdir 를 확인할 것 (cannot run KMM)") from None
    rc, text = _KMM_HELP_CACHE[key]
    return rc, text, where


def check_kmm_supports(environment, keys, work_dir, err, batch=False):
    """그 표 줄을 읽을 KMM 이 DROP_ATTITUDE 키(keys)를 아는지 '--help DROP_ATTITUDE' 로 본다 — 모르면 err 로 멈춘다.

    실행 파일·apptainer 감싸기·기억은 _kmm_help 와 같다(러너 KMM, batch=True 면 batch_koomeshmodifier 의 KMM).
    table 지름길도 묻는다 — 그래서 헤드 노드에서 그 KMM(또는 SIF)이 돌아야 한다. 옛 KMM(v131 이하)은 EndTimeTable 줄을
    다른 키로 잘못 읽는다 — 경로에 height 가 들면 Height=0, tfinal·density·dropsurface 가 들면 그 값을 덮고, runid 가 들면
    죽는다. 그래서 그런 줄을 쓰기 전에 막는다.
    """
    rc, text, where = _kmm_help(environment, "DROP_ATTITUDE", work_dir, err, batch)
    missing = [k for k in keys if k not in text]
    if missing:
        tail = " | ".join(text.strip().splitlines()[-2:])[:240]
        raise err(f"러너가 쓸 KMM({where})이 DROP_ATTITUDE 키 {missing} 를 모른다. 이 KMM(v131 이하)은 그 줄을 다른 키로 잘못 "
                  f"읽는다(경로에 height 가 들면 Height=0, tfinal·density·dropsurface 를 덮고, runid 가 들면 죽는다). "
                  f"environment.apptainer_sif 를 v132 이상 SmartTwinPreprocessor SIF 로 바꿀 것 — SIF 없이 쓰면 "
                  f"koomeshmodifier_path 를 v132 이상 KMM 으로. --help 종료 코드 {rc}: {tail} (KMM version skew)")


def check_kmm_strong_contact(environment, work_dir, batch=False):
    """endtime_presim(중력 끔) 사전 해석 KMM 이 RIGID_DROP_ENDTIME 키 PresimStrongContact 를 아는지 '--help RIGID_DROP_ENDTIME'
    으로 본다 — 모르면 멈춘다. v132 이하 KMM 은 모르는 블록 키에서 종료 코드 1 로 죽으므로 사전 해석을 돌리기 전에 까닭을 알린다.
    사전 해석 KMM 은 run_kmm 과 같은 실행 파일이다(_kmm_help). table 지름길·중력 켬·impact_conditions 는 그 줄을 쓰지 않아 묻지 않는다.
    """
    rc, text, where = _kmm_help(environment, "RIGID_DROP_ENDTIME", work_dir, EndTimePresimError, batch)
    if "PresimStrongContact" not in text:
        tail = " | ".join(text.strip().splitlines()[-2:])[:240]
        raise EndTimePresimError(f"사전 해석 KMM({where})이 RIGID_DROP_ENDTIME 키 PresimStrongContact 를 모른다. strong_contact"
                                 f"(중력 끔 종료 시간 규칙의 문턱)를 넘기려면 v133 이상 KMM 이 필요하다 — 이 KMM(v132 이하)은 그 줄에서 "
                                 f"종료 코드 1 로 멈춘다. environment.apptainer_sif 를 v133 이상 SmartTwinPreprocessor SIF 로 바꿀 것 — "
                                 f"SIF 없이 쓰면 koomeshmodifier_path 를 v133 이상 KMM 으로. --help 종료 코드 {rc}: {tail} "
                                 f"(KMM too old for strong_contact)")


G_SI = 9.81
_LEN_TO_M = {"mm": 1e-3, "m": 1.0}
_TIME_TO_S = {"s": 1.0, "ms": 1e-3}


def drop_v0(height, units, gravity=None):
    """낙하 높이(덱 길이) → √(2gh), 덱 단위. units 는 '<길이>-<질량>-<시간>'(mm-t-s·m-kg-s·mm-kg-ms·mm-g-ms).
    gravity(덱 단위, simulation_params.gravity)가 있으면 그 g, 없으면 9.81 m/s² 를 덱 단위로 — KMM DROP_ATTITUDE 와 같다."""
    parts = str(units).split("-")
    L, T = _LEN_TO_M[parts[0]], _TIME_TO_S[parts[-1]]
    g = float(gravity) if gravity else G_SI * T * T / L
    return math.sqrt(2.0 * g * float(height))


UNITS_NEED_GRAVITY = ("mm-kg-ms", "mm-g-ms")   # FEM KMM _ResolveFallGravity 가 재질 밀도로 못 알아내는 단위계


def check_table_drop(meta, sim_params, path, err, label, gravity=None, template=None):
    """표 메타가 이 시나리오의 낙하·옵션과 같은지 본다. 다르면 err 로 멈추고, 메타가 없으면 경고만 한다.

      height·v0(units): simulation_params.height·gravity 의 √(2gh) 와 상대 1e-3 넘게 다르면 멈춤 — 다른 높이·g 로 만든 표는
                        이 낙하의 종료 시간·충돌 상태가 아니다
      gravity          : 주면(옵션의 사전 해석 중력 true/false) 메타 gravity(0/1)와 다르면 멈춤
      deck             : template 을 주면 메타 deck 경로와 다를 때 경고(같은 기기의 사본일 수 있다)
      units            : mm-kg-ms·mm-g-ms 인데 simulation_params.gravity 가 없으면 멈춤 — FEM 의 KMM DROP_ATTITUDE 는 이 단위의
                        g 를 재질 밀도로 알아내지 못하고 9810(mm-t-s 값) 또는 9.81 을 쓴다
    """
    height = float(sim_params.get("height", 1500))
    bad, notes = [], []

    def differ(a, b):
        return abs(a - b) > 1e-3 * max(abs(a), abs(b), 1e-300)
    try:
        if meta.get("height") not in (None, "") and differ(float(meta["height"]), height):
            bad.append(f"높이 {float(meta['height']):g} ≠ 시나리오 simulation_params.height {height:g}")
    except ValueError:
        notes.append(f"height 메타 {meta.get('height')!r} 를 읽지 못했다")
    if meta.get("v0") not in (None, "") and meta.get("units"):
        try:
            want = drop_v0(height, meta["units"], sim_params.get("gravity"))
            if differ(float(meta["v0"]), want):
                bad.append(f"v0 {float(meta['v0']):.6g} ≠ 시나리오 √(2gh) {want:.6g} ({meta['units']}"
                           f"{', g=' + str(sim_params['gravity']) if sim_params.get('gravity') else ''})")
        except (KeyError, ValueError, IndexError):
            notes.append(f"v0·units 메타({meta.get('v0')!r}, {meta.get('units')!r})를 읽지 못했다")
    else:
        notes.append("v0·units 메타가 없어 낙하 속도를 확인하지 못했다")
    if gravity is not None and meta.get("gravity") not in (None, ""):
        on = {"1": True, "true": True, "0": False, "false": False}.get(str(meta["gravity"]).strip().lower())
        if on is None:
            notes.append(f"gravity 메타 {meta['gravity']!r} 를 읽지 못했다")
        elif on != bool(gravity):
            bad.append(f"사전 해석 중력 {'켬' if on else '끔'}(메타 gravity={meta['gravity']}) ≠ 옵션 gravity "
                       f"{str(bool(gravity)).lower()}")
    if template and meta.get("deck") and os.path.abspath(meta["deck"]) != os.path.abspath(template):
        notes.append(f"표를 만든 덱 {meta['deck']} 이 이 시나리오 템플릿 {template} 과 다르다 — 같은 기기인지 확인할 것")
    if meta.get("t_sep_ms") in (None, ""):
        notes.append("t_sep_ms 메타가 없다 — 1·2차 충격을 가른 간격을 모른다")
    for n in notes:
        print(f"⚠️  {label}: 표 {path} — {n}")
    if bad:
        raise err(f"표 {path} 의 낙하 조건이 이 시나리오와 다르다: {'; '.join(bad)} — 이 높이·g·중력으로 표를 다시 만들 것 "
                  f"(table drop mismatch)")
    units = str(meta.get("units") or "").strip()
    if units in UNITS_NEED_GRAVITY and not sim_params.get("gravity"):
        g = drop_v0(0.5, units) ** 2   # √(2·g·0.5)² = g — 9.81 m/s² 를 이 단위로
        raise err(f"덱 단위가 {units}(표 메타)인데 simulation_params.gravity 가 없다 — FEM 의 KMM DROP_ATTITUDE 는 이 단위의 g 를 "
                  f"재질 밀도로 알아내지 못하고 9810(mm-t-s 의 값) 또는 9.81 을 쓴다. simulation_params.gravity 에 {g:g}"
                  f"(9.81 m/s² 를 {units} 로)를 줄 것 (gravity required for {units})")


def check_table_rule(meta, path, strong_contact):
    """표 메타의 종료 시간 규칙(v133)을 본다 — endtime_presim(사전 해석·table 지름길)만 부른다. impact_conditions 는 v132 그대로.

      endtime_rule 없음 : v132 표(1차 뒤 첫 재접촉 묶음 끝 + 여유)라 경고 한 줄. 메타 gravity 가 켬이면 경고하지 않는다 —
                          중력 켬은 v133 도 같은 규칙이다
      last_strong       : 중력 끔 표. 메타 strong_contact 가 옵션 strong_contact 와 1e-9 넘게 다르면 멈춘다
      first_recontact   : 중력 켬 표 — strong_contact 를 보지 않는다
    """
    rule = str(meta.get("endtime_rule") or "").strip()
    if not rule:
        grav = {"1": True, "true": True, "0": False, "false": False}.get(str(meta.get("gravity") or "").strip().lower())
        if grav is not True:
            print(f"⚠️  endtime_presim: 표 {path} — endtime_rule 메타가 없는 v132 표다(1차 뒤 첫 재접촉 묶음 끝 + 여유). 슬랩다운이 "
                  f"꼭짓점마다 갈라져 오면 더 센 뒷부분을 놓칠 수 있다. v133 이상 KMM 으로 표를 다시 만들 것 "
                  f"(v132 first-recontact table)")
        return
    if rule == "first_recontact":
        return
    if rule != "last_strong":
        print(f"⚠️  endtime_presim: 표 {path} — 모르는 endtime_rule={rule} 라 strong_contact 를 확인하지 못했다 (unknown endtime_rule)")
        return
    try:
        got = float(meta.get("strong_contact"))
    except (TypeError, ValueError):
        print(f"⚠️  endtime_presim: 표 {path} — endtime_rule=last_strong 인데 strong_contact 메타 {meta.get('strong_contact')!r} 를 "
              f"읽지 못해 문턱을 확인하지 못했다 (strong_contact unreadable)")
        return
    if not abs(got - float(strong_contact)) <= STRONG_CONTACT_TOL:
        raise EndTimePresimError(f"표 {path} 의 문턱 strong_contact={meta['strong_contact']}(endtime_rule=last_strong)가 옵션 "
                                 f"simulation_params.endtime_presim.strong_contact {strong_contact!r} 와 다르다 — 이 문턱으로 표를 "
                                 f"다시 만들거나 옵션을 표에 맞출 것 (strong_contact mismatch)")


def report_reach(rows, sim_params, label):
    """표의 reach(첫 접촉점에서 바닥 위 접촉점까지 가장 먼 거리, 덱 길이)·n_unresolved 를 알린다.
    reach 가 메시 바닥판 한 변의 절반보다 길면 경고한다(RigidWall 은 판 크기와 무관). 칸이 없으면 아무것도 안 한다."""
    def num(r, c):
        v = (r["raw"].get(c) or "").strip()
        try:
            return float(v) if v else None
        except ValueError:
            return None
    reach = [(num(r, "reach"), r["name"]) for r in rows if num(r, "reach") is not None]
    unres = [r["name"] for r in rows if (num(r, "n_unresolved") or 0) > 0]
    if reach:
        rmax, who = max(reach)
        ds = sim_params.get("drop_surface", {}) or {}
        kind = ds.get("type", "Plane")
        if kind == "RigidWall":
            print(f"  [{label}] 바닥 위 도달 거리 reach 최대 {rmax:g} (덱 길이, {who}) — RigidWall 이라 판 크기와 무관")
        else:
            size = ds.get("size", [200, 200, 20] if kind == "PlaneGraded" else [300, 300, 20])
            half = min(float(size[0]), float(size[1])) / 2.0
            print(f"  [{label}] 바닥 위 도달 거리 reach 최대 {rmax:g} (덱 길이, {who}) — 바닥판 {size[0]}×{size[1]} 반폭 {half:g}")
            if rmax > half:
                n_over = sum(1 for x, _ in reach if x > half)
                print(f"⚠️  {label}: reach 가 바닥판 반폭보다 긴 각도 {n_over}개(최대 {rmax:g}) — 기기가 판 가장자리를 넘을 수 "
                      f"있다. simulation_params.drop_surface.size 를 한 변 {2.0 * rmax:g} 이상으로 키울 것 (plate reach)")
    if unres:
        more = " …" if len(unres) > 10 else ""
        print(f"⚠️  {label}: n_unresolved > 0 인 각도 {len(unres)}개 — 중력 끔 사전 해석이 끝을 보지 못하고 시간 상한(v133 은 "
              f"이벤트 상한도)에서 멈춰 그 뒤 충돌이 endtim 에 들지 않았다(짧을 수 있다): {', '.join(unres[:10])}{more}")


def endtime_time_factor(config, doe=None, step=None):
    """종료 시간 표가 tFinal 보다 길 때의 시간 배율 ceil(endtim ÷ tFinal) — 1 이상. doe·step 을 주면 그 스텝의 값,
    아니면 모든 DOE·스텝 가운데 최대. scenario.doe_endtim 이 없으면 1 이라 time_limit·timeout 은 예전 그대로다."""
    table = ((config or {}).get("scenario") or {}).get("doe_endtim") or {}
    if not table:
        return 1
    tfinal = float(((config or {}).get("simulation_params") or {}).get("tFinal", 0.005))
    if doe is None:
        vals = [v for st in table.values() for v in st.values()]
    else:
        vals = [(table.get(str(doe)) or {}).get(str(step))]
    vals = [float(v) for v in vals if v is not None]
    if not vals or not tfinal > 0:
        return 1
    return max(1, math.ceil(round(max(vals) / tfinal, 9)))


def doe_time_factors(config):
    """DOE 마다 wall-clock 배율 F_d = Σ_s (r_{d,s} + [DR 켬 이고 s ≥ 2]) → {doe(1-based): F_d}.
    r_{d,s} = endtime_time_factor(그 DOE·스텝) — 표에 없는 스텝(열 등)은 1. 표(scenario.doe_endtim)가 없으면 None 이라
    호출 쪽은 예전 배율을 그대로 쓴다. r 이 모두 1 이면 KooChainRun _step_dr_time_factor(1 + (스텝 수 − 1)·(DR 이면 2,
    아니면 1))와 같다 — 표가 있어도 짧으면 예전 시간 그대로다."""
    scenario = (config or {}).get("scenario") or {}
    table = scenario.get("doe_endtim") or {}
    if not table:
        return None
    try:
        total = max(1, int(scenario.get("total_steps", 1)))
    except (TypeError, ValueError):
        total = 1
    dr = ((config or {}).get("simulation_params") or {}).get("dynamic_relaxation", False)
    dr_on = bool(dr.get("enabled", True)) if isinstance(dr, dict) else bool(dr)
    n = int(scenario.get("doe_count") or max(int(k) for k in table))
    return {d: sum(endtime_time_factor(config, d, s) + (1 if dr_on and s >= 2 else 0) for s in range(1, total + 1))
            for d in range(1, n + 1)}


def slurm_seconds(text):
    """Slurm 시간 형식(MM, MM:SS, HH:MM:SS, D-HH, D-HH:MM, D-HH:MM:SS) → 초. 읽지 못하면 ValueError."""
    s = str(text).strip()
    days, rest = s.split("-", 1) if "-" in s else ("0", s)
    f = [int(x) for x in rest.split(":")]
    if not 1 <= len(f) <= 3 or int(days) < 0 or min(f) < 0:
        raise ValueError(f"Slurm 시간 형식이 아니다: {text!r}")
    if "-" in s:
        h, m, sec = (f + [0, 0])[:3]
    elif len(f) == 3:
        h, m, sec = f
    else:
        h, m, sec = (0, f[0], 0) if len(f) == 1 else (0, f[0], f[1])
    return int(days) * 86400 + h * 3600 + m * 60 + sec


def slurm_hms(seconds):
    """초 → H:MM:SS (시간은 24 를 넘어도 된다 — KooChainRun _hms_scale 과 같은 글)."""
    seconds = int(seconds)
    return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def partition_max(partition, timeout=5):
    """sinfo -p <파티션> -h -o %l → (글, 초). UNLIMITED·조회 실패·읽지 못함이면 None."""
    try:
        r = subprocess.run(["sinfo", "-p", partition, "-h", "-o", "%l"], capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        text = r.stdout.strip().split("\n")[0].strip() if r.returncode == 0 else ""
        if not text or text.upper() in ("UNLIMITED", "INFINITE"):
            return None
        return text, slurm_seconds(text)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def report_time_factor(doe_endtim, sim_params, label):
    """prepare 때 시간 배율을 알린다 — submit 의 DOE time_limit·스텝 timeout_per_step_seconds 에 곱해질 값."""
    f = endtime_time_factor({"scenario": {"doe_endtim": doe_endtim}, "simulation_params": sim_params})
    if f > 1:
        mx = max(v for st in doe_endtim.values() for v in st.values())
        print(f"  [{label}] 가장 긴 endtim {mx:g} 가 tFinal {float(sim_params.get('tFinal', 0.005)):g} 의 {f}배 이하 — "
              f"시간 제한을 늘린다: submit 의 DOE time_limit 은 DOE 마다 Σ 스텝(ceil(endtim ÷ tFinal) + DR), 러너 스텝 "
              f"timeout_per_step_seconds·deep report·대규모 배열은 그 스텝 배율 (파티션 최대에서 자른다)")
    return f


def endtime_table_for_step(config, step_num):
    """이 스텝 설정에 넣을 EndTimeTable 절대 경로. DROP 스텝이 아니거나 표가 없으면 None — runner_config 에서만 읽는다.

    템플릿은 하나라 첫 항목이 그것이다. scratch_run 은 project.model_file 을 scratch 사본으로 바꾸므로 템플릿 경로로
    맞춰 찾지 않는다(표는 공유 디스크의 절대 경로 그대로 쓴다).
    """
    scenario = (config or {}).get("scenario") or {}
    tables = scenario.get("endtime_tables") or []
    if not tables:
        return None
    for s in scenario.get("steps") or []:
        if str(s.get("step")) == str(step_num):
            return tables[0]["table"] if s.get("mode") == "DROP" else None
    return None
