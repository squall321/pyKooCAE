# prepare 때 KMM RIGID_DROP_ENDTIME(강체 낙하 사전 해석)을 돌려 DROP 스텝마다 쓸 각도별 종료 시간 표를 마련하는 모듈
"""
simulation_params.endtime_presim — KooChainRun prepare(CumulativeDesigner.save_runner_config)가 부른다.

  켜지면(enabled=true)
    1. DOE 의 DROP 스텝 각도(roll, pitch, yaw)를 값으로 중복 없이 모아 <output_dir>/endtime_presim/1/angles.csv 를 쓴다
    2. KMM RIGID_DROP_ENDTIME 옵션 파일을 쓰고 러너와 같은 방식(koomeshmodifier_path·apptainer 감싸기·시간 제한)으로 돌린다
    3. 작업 폴더의 <base>_endtime.csv 를 읽어 모든 각도가 있고 endtim > 0 인지 본다 — 아니면 prepare 를 멈춘다
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
import subprocess

MARKER = "[ENDTIME_PRESIM_FAILED]"
OPTION_FILE = "rigid_drop_endtime.txt"   # KMM 은 옵션 이름의 .txt 를 .log 로 바꿔 로그를 쓴다 — 확장자는 꼭 .txt
STDOUT_FILE = "kmm_stdout.log"
MATCH_TOL_DEG = 0.01
DEFAULTS = {"enabled": False, "table": None, "restitution": [0.1, 0.3, 0.5], "friction": 0.5,
            "gravity": False, "margin_ms": 1.0, "exclude_parts": [], "workers": 8}


class EndTimePresimError(RuntimeError):
    """사전 해석·표 검증 실패 — prepare 를 멈춘다(조용히 tFinal 로 돌아가지 않는다)."""

    def __init__(self, msg):
        super().__init__(f"{MARKER} {msg}")


def _number(key, v, lo, hi=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not (v >= lo and (hi is None or v <= hi)):
        span = f"{lo} 이상" if hi is None else f"{lo}~{hi}"
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
    if not isinstance(opts["gravity"], bool):
        raise EndTimePresimError(f"simulation_params.endtime_presim.gravity 는 true/false 여야 한다: {opts['gravity']!r} (bad value)")
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


def find_endtim(rows, roll, pitch, yaw=0.0):
    """표에서 낙하 방향 사이 각이 0.01° 이하인 줄들의 endtim 최대(KMM DROP_ATTITUDE 와 같은 규칙). 없으면 None."""
    d = drop_direction(roll, pitch, yaw)
    hits = [r["endtim"] for r in rows if _same_direction(r["dir"], d)]
    return max(hits) if hits else None


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


def build_option_text(template, angle_file, height, opts):
    """KMM RIGID_DROP_ENDTIME 옵션 파일. StepConfigBuilder 처럼 '키,값' 한 줄씩이고 블록 안에 빈 줄이 없다
    (KMM 은 빈 줄에서 블록을 끝낸다). ExcludePart 는 줄 때만 쓴다."""
    lines = ["*Inputfile", template, "*Mode", "RIGID_DROP_ENDTIME,1", "**RigidDropEndtime,1",
             f"Height,{height}",
             f"AngleFile,{angle_file}",
             "Restitution," + ",".join(str(e) for e in opts["restitution"]),
             f"Friction,{opts['friction']}",
             f"PresimGravity,{1 if opts['gravity'] else 0}",
             f"MarginMs,{opts['margin_ms']}"]
    if opts["exclude_parts"]:
        lines.append("ExcludePart," + ",".join(str(p) for p in opts["exclude_parts"]))
    lines += [f"Workers,{opts['workers']}", "**EndRigidDropEndtime", "*End"]
    return "\n".join(lines) + "\n"


def run_kmm(environment, work_dir, timeout):
    """KMM 을 러너(_run_koomeshmodifier)와 같은 방식으로 돈다 — koomeshmodifier_path, apptainer 감싸기, cwd, 시간 제한.

    다른 점: 작업 폴더를 KMM 둘째 인자(working_directory)로 절대 경로로 준다. KMM 은 덱을 읽으며 덱 폴더로 chdir 하므로
    인자 하나일 때의 기본값 '.' 은 그 뒤 템플릿 폴더를 가리킨다 — 산출물이 사용자 템플릿 옆에 떨어지지 않게 한다.
    헤드 노드에서 돌므로 러너의 cleanup_after_exec(사용자의 squashfuse 를 모두 pkill)는 부르지 않는다.
    출력은 메모리에 담지 않고 작업 폴더의 kmm_stdout.log 에 쓴다. → (rc, cmd, 로그 경로)
    """
    from Runner.PathResolver import find_koomeshmodifier
    from Runner.CumulativeScenarioRunner import ApptainerWrapper
    kmm = environment.get("koomeshmodifier_path") or find_koomeshmodifier()
    cmd = ApptainerWrapper({"environment": environment}).wrap_command([kmm, OPTION_FILE, work_dir], use_lsdyna=False)
    log_path = os.path.join(work_dir, STDOUT_FILE)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        r = subprocess.run(cmd, cwd=work_dir, stdout=log, stderr=subprocess.STDOUT, timeout=timeout,
                           encoding="utf-8", errors="replace")
    return r.returncode, cmd, log_path


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
    """<base>_endtime.csv → (meta, rows). '#' 줄은 meta, rows 는 name·roll·pitch·yaw·endtim·dir. 형식이 틀리면 멈춘다."""
    meta, body = {}, []
    with open(path, newline="", encoding="utf-8") as f:
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
        rows.append(row)
    if not rows:
        raise EndTimePresimError(f"표 {path} 에 각도 줄이 없다 (no data rows)")
    return meta, rows


def _endtims_for(rows, angles, table, by_name):
    """요청한 각도마다 endtim → {(roll, pitch, yaw): endtim}. 하나라도 없으면 멈춘다.
    by_name(사전 해석 표): 우리가 쓴 이름의 줄이 있고 그 줄의 방향도 같아야 한다. 값은 KMM 과 같은 방향 찾기로 정한다."""
    named = {r["name"]: r for r in rows}
    out, missing = {}, []
    for name, roll, pitch, yaw in angles:
        if by_name and (name not in named or not _same_direction(named[name]["dir"], drop_direction(roll, pitch, yaw))):
            missing.append(name)
            continue
        e = find_endtim(rows, roll, pitch, yaw)
        if e is None:
            missing.append(f"{name}({roll}, {pitch}, {yaw})")
            continue
        out[(roll, pitch, yaw)] = e
    if missing:
        more = " …" if len(missing) > 10 else ""
        raise EndTimePresimError(f"표 {table} 에 DROP 각도 {len(missing)}/{len(angles)}개가 없다: "
                                 f"{', '.join(missing[:10])}{more} (angles missing)")
    return out


def _run_presim(opts, sim_params, environment, template, work, angles):
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
        f.write(build_option_text(template, angle_file, sim_params.get("height", 1500), opts))
    timeout = environment.get("timeout_koomeshmodifier_seconds", 604800)
    print(f"  [endtime_presim] KMM RIGID_DROP_ENDTIME 실행 — 각도 {len(angles)}개, 작업 폴더 {work}")
    log_path = os.path.join(work, STDOUT_FILE)
    try:
        rc, _cmd, log_path = run_kmm(environment, work, timeout)
    except subprocess.TimeoutExpired:
        _tail(log_path)
        raise EndTimePresimError(f"KMM 사전 해석이 {timeout}초 안에 끝나지 않았다 — 로그 {log_path} (timeout)") from None
    except OSError as e:
        raise EndTimePresimError(f"KMM 을 실행하지 못했다: {e} — environment.koomeshmodifier_path·apptainer_sif·"
                                 f"apptainer_tmpdir 를 확인할 것 (cannot run KMM)") from None
    if rc != 0:
        _tail(log_path)
        raise EndTimePresimError(f"KMM 사전 해석이 실패했다(종료 코드 {rc}) — 로그 {log_path} (KMM rc={rc})")
    if not os.path.isfile(table):
        _tail(log_path)
        raise EndTimePresimError(f"KMM 이 끝났는데 표가 없다: {table} — 로그 {log_path} (table not written)")
    return table


def prepare_endtime_tables(sim_params, environment, model_file, output_dir, scenario_dir, doe_angles, runner_steps):
    """켜져 있으면 표를 마련해 (endtime_tables, doe_endtim), 꺼져 있거나 DROP 스텝이 없으면 (None, None).

    doe_angles: save_runner_config 의 DOE 각도표(1-based), runner_steps: scenario.steps([{step, mode, ...}]).
    실패(KMM rc≠0·시간 초과·표 없음·각도 빠짐·endtim≤0·table 파일 없음)는 EndTimePresimError — prepare 가 멈춘다.
    """
    opts = presim_options(sim_params)
    if opts is None:
        return None, None
    angles = collect_drop_angles(doe_angles, runner_steps)
    if not angles:
        print("⚠️  simulation_params.endtime_presim: DROP 스텝이 없어 사전 해석을 건너뛴다 (no DROP step)")
        return None, None
    template = os.path.abspath(model_file)
    if opts["table"]:
        table = opts["table"].strip()
        table = os.path.abspath(table if os.path.isabs(table) else os.path.join(scenario_dir, table))
        if not os.path.isfile(table):
            raise EndTimePresimError(f"simulation_params.endtime_presim.table 파일이 없다: {table} (table not found)")
        source = "table"
        print(f"  [endtime_presim] 사전 해석을 건너뛰고 주어진 표를 쓴다: {table}")
    else:
        table = _run_presim(opts, sim_params, environment, template,
                            os.path.abspath(os.path.join(output_dir, "endtime_presim", "1")), angles)
        source = "presim"
    meta, rows = read_endtime_csv(table)
    height = sim_params.get("height", 1500)
    try:
        if "height" in meta and abs(float(meta["height"]) - float(height)) > 1e-9 * max(1.0, abs(float(height))):
            print(f"⚠️  endtime_presim: 표의 낙하 높이 {meta['height']} 가 simulation_params.height {height} 와 다르다 "
                  f"— 이 높이로 표를 다시 만들 것 (height mismatch)")
    except ValueError:
        pass
    per_angle = _endtims_for(rows, angles, table, by_name=(source == "presim"))
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
    return [{"template": template, "table": table, "source": source, "angles": len(angles)}], doe_endtim


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
