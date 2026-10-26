"""KooD3plotReader 후처리 sh 스크립트 텍스트 생성.

생성하는 스크립트:
- deep_report.sh: 단일 시뮬 d3plot → koo_deep_report (per-job, run_dir에 위치)
- sphere_report.sh: 전각도 DROP 통합 → koo_sphere_report (output_dir에 위치)
- impact_report.sh: 전위치 부분충격(IMPACT) 통합 → koo_impact_report (output_dir에 위치)

DROP/IMPACT 분기는 report_mode_from_runner_config() 로 판정
(DROP→sphere, IMPACT→impact, 둘 다 돌지 않음).

핵심:
- normal termination 필터 (mes0000/d3hsp/*.log에서 "N o r m a l    t e r m i n a t i o n" grep)
- 항상 sh 생성 (postprocess.enabled 무관) → 사용자가 언제든 수동 실행 가능
- enabled=true && auto_deep/auto_sphere=true 일 때만 자동 실행

인자 pass-through (KooD3plotReader post_analyze.sh 의 --deep-opts/--sphere-opts/
--impact-opts 와 동일 패턴):
- postprocess.deep_extra_args   → koo_deep_report 명령 끝에 그대로 추가
- postprocess.sphere_extra_args → koo_sphere_report 명령 끝에 추가
  (그 앞에 postprocess.hotspot_part → --hotspot-part PID,… — 전각도 핫스팟 군집을 그 파트로만,
   postprocess.sphere_viewer → --viewer canvas|plotly — 3D 인벨롭 뷰어, 기본 canvas 면 생략)
- postprocess.impact_extra_args → koo_impact_report 명령 끝에 추가
  값은 JSON 리스트(권장, 셸 분할 모호성 없음) 또는 공백 구분 문자열.
  고정 플래그 뒤에 붙으므로 argparse "마지막 우선" 으로 기본값 override 가능.
  예: "deep_extra_args": ["--per-part-render", "--yield-stress", "350"]
"""

import math
import os
import re
import shlex
from Runner._encoding import job_env_lines

DEFAULT_SIF_PATH = "/opt/apptainers/SmartTwinPostprocessor.sif"
DEFAULT_AXES = ["z"]
DEFAULT_FIELDS = ["von_mises"]
DEFAULT_MODE = "section"
DEFAULT_UA_THREADS = 8
DEFAULT_SV_THREADS = 8
DEFAULT_YIELD_STRESS = 350

# 핫스팟 군집 기본값 — koo_deep_report 의 argparse 기본값과 같은 값을 둔다.
# 값이 기본과 같으면 플래그를 방출하지 않아, 기존 시나리오의 생성물이
# 바이트 단위로 그대로 유지된다(회귀 0).
DEFAULT_HOTSPOT_TOP_PERCENT = 5.0
DEFAULT_HOTSPOT_DISTANCE_FACTOR = 1.5
DEFAULT_HOTSPOT_MIN_ELEMENTS = 5
DEFAULT_HOTSPOT_MAX_CLUSTERS = 20
DEFAULT_HOTSPOT_CRITERION = "von_mises"
DEFAULT_HOTSPOT_TIME_AGGREGATE = "elemmax_then_mean"
SPHERE_VIEWERS = ("canvas", "plotly")   # koo_sphere_report --viewer — canvas 는 외부 스크립트 0(폐쇄망 안전)
DEFAULT_SPHERE_VIEWER = "canvas"
# 기준량·시간 집계 — KooD3plotReader koo_deep_report(e8460d9)·엔진 unified_analyzer 와 같은 이름·별칭.
# 그쪽 표는 C++ parseHotspotCriterion 과 시험으로 묶여 있다. 엔진이 늘리면 여기도 늘린다.
HOTSPOT_CRITERIA = ("von_mises", "max_principal", "min_principal", "max_shear",
                    "x_tension", "y_tension", "z_tension")
HOTSPOT_TIME_AGGREGATES = ("elemmax_then_mean", "mean_then_timemax", "both")
_HOTSPOT_ALIASES = {
    "vm": "von_mises", "vonmises": "von_mises",
    "sigma1": "max_principal", "s1": "max_principal", "p1": "max_principal", "maxprincipal": "max_principal",
    "sigma3": "min_principal", "s3": "min_principal", "p3": "min_principal", "minprincipal": "min_principal",
    "maxshear": "max_shear", "tau_max": "max_shear", "taumax": "max_shear", "tresca": "max_shear",
    "xtension": "x_tension", "sigma_xx": "x_tension", "sxx": "x_tension",
    "ytension": "y_tension", "sigma_yy": "y_tension", "syy": "y_tension",
    "ztension": "z_tension", "sigma_zz": "z_tension", "szz": "z_tension",
}


def _extra_args_str(options, key):
    """postprocess[key] (list 또는 str) → 셸에 안전한 한 줄 문자열.

    list: 각 원소를 shlex.quote 로 감싸 결합 (공백/특수문자 보존).
    str:  shlex.split 후 재-quote (사용자가 통째 문자열로 줘도 안전).
    없거나 빈 값: "" (호출부에서 라인 자체를 생략).
    """
    val = (options or {}).get(key)
    if not val:
        return ""
    if isinstance(val, str):
        try:
            parts = shlex.split(val)
        except ValueError:
            parts = val.split()
    else:
        parts = [str(v) for v in val]
    return " ".join(shlex.quote(p) for p in parts)


def _hotspot_part_str(options):
    """postprocess.hotspot_part → koo_sphere_report `--hotspot-part 12,15` 문자열. 없으면 "".

    정수·정수 목록·"12,15" 문자열을 받는다. 셸 스크립트에 그대로 박히므로 숫자 PID 만 통과시키고,
    그 밖은 경고하고 버린다. 전부 버려지면 플래그를 내지 않는다(= 전 파트, sphere 기본).
    """
    val = (options or {}).get("hotspot_part")
    if val is None or val == "" or val == [] or isinstance(val, bool):
        return ""
    items = list(val) if isinstance(val, (list, tuple)) else str(val).split(",")
    pids = []
    for it in items:
        s = str(it).strip()
        if not s:
            continue
        if not re.fullmatch(r"[0-9]+", s):
            print(f"  ⚠️  postprocess.hotspot_part: 파트 ID(숫자)가 아닌 값 무시 — {s!r}")
            continue
        if s not in pids:
            pids.append(s)
    return f"--hotspot-part {','.join(pids)}" if pids else ""


def _sphere_viewer_str(options):
    """postprocess.sphere_viewer → koo_sphere_report `--viewer plotly`. 기본(canvas)이거나 없으면 "".

    plotly 는 호버·범례·축을 주지만 리포트가 약 1.6MB 커진다. 모르는 값은 경고하고 버린다.
    """
    val = (options or {}).get("sphere_viewer")
    if val in (None, ""):
        return ""
    v = str(val).strip().lower()
    if v not in SPHERE_VIEWERS:
        print(f"  ⚠️  postprocess.sphere_viewer: 알 수 없는 뷰어 무시 — {val!r} (허용: {', '.join(SPHERE_VIEWERS)})")
        return ""
    return "" if v == DEFAULT_SPHERE_VIEWER else f"--viewer {v}"


def _hotspot_args_str(options):
    """postprocess 의 hotspot_* 전용 키 → koo_deep_report 플래그 문자열.

    CLI 이름과 1:1 로 대응한다(`--hotspot-top-percent` ↔ `hotspot_top_percent`).
    기존 `section_view_mode` ↔ `--section-view-mode` 와 같은 관례다.

    · `hotspot_clusters` 가 참이 아니면 **아무것도 방출하지 않는다** →
      기존 시나리오의 생성 스크립트가 바이트 단위로 그대로 유지된다.
    · 값이 기본값과 같으면 그 플래그도 생략한다(명령줄을 짧게 유지).
    · `deep_extra_args` 는 이 뒤에 붙으므로, 둘 다 주면 **extra_args 가 이긴다**
      (고정 플래그를 뒤에서 덮는 기존 규약과 동일).
    """
    opts = options or {}
    if not opts.get("hotspot_clusters"):
        return ""

    parts = ["--hotspot-clusters"]

    def add(key, flag, default, cast):
        if key not in opts:
            return
        try:
            v = cast(opts[key])
        except (TypeError, ValueError):
            print(f"  ⚠️  postprocess.{key} 값을 해석할 수 없어 무시합니다: {opts[key]!r}")
            return
        if v == default:
            return                      # 기본값이면 생략
        parts.extend([flag, repr(v) if isinstance(v, float) else str(v)])

    add("hotspot_top_percent", "--hotspot-top-percent",
        DEFAULT_HOTSPOT_TOP_PERCENT, float)
    add("hotspot_distance_factor", "--hotspot-distance-factor",
        DEFAULT_HOTSPOT_DISTANCE_FACTOR, float)
    add("hotspot_min_elements", "--hotspot-min-elements",
        DEFAULT_HOTSPOT_MIN_ELEMENTS, int)
    add("hotspot_max_clusters", "--hotspot-max-clusters",
        DEFAULT_HOTSPOT_MAX_CLUSTERS, int)

    # 기준량 — 문자열("von_mises,min_principal") 또는 배열 둘 다. 모르는 이름은
    # 여기서 걸러 즉시 알린다(SIF 안에서 걸리면 리포트가 통째로 안 나온 뒤에야 안다).
    crit = _normalize_hotspot_criterion(opts.get("hotspot_criterion"))
    if crit and crit != DEFAULT_HOTSPOT_CRITERION:
        parts.extend(["--hotspot-criterion", crit])

    # 시간 집계 — 기본(elemmax_then_mean)이면 생략. 모르는 값은 경고하고 버린다(기준량과 같은 규칙).
    agg = opts.get("hotspot_time_aggregate")
    if agg not in (None, ""):
        a = str(agg).strip().lower().replace("-", "_").replace(" ", "_")
        if a not in HOTSPOT_TIME_AGGREGATES:
            print(f"  ⚠️  postprocess.hotspot_time_aggregate: 알 수 없는 방식 무시 — {agg!r} "
                  f"(허용: {', '.join(HOTSPOT_TIME_AGGREGATES)})")
        elif a != DEFAULT_HOTSPOT_TIME_AGGREGATE:
            parts.extend(["--hotspot-time-aggregate", a])

    return " ".join(shlex.quote(x) for x in parts)


def _normalize_hotspot_criterion(value):
    """hotspot_criterion 값 → 'a,b' 정규 문자열. 없거나 비면 None."""
    if value is None:
        return None
    items = [str(x) for x in value] if isinstance(value, (list, tuple)) else str(value).split(",")
    out = []
    for it in items:
        k = it.strip().strip('"').strip("'").lower().replace("-", "_").replace(" ", "_")
        if not k:
            continue
        k = _HOTSPOT_ALIASES.get(k, k)
        if k not in HOTSPOT_CRITERIA:
            print(f"  ⚠️  postprocess.hotspot_criterion: 알 수 없는 기준량 무시 — {it.strip()!r} "
                  f"(허용: {', '.join(HOTSPOT_CRITERIA)})")
            continue
        if k not in out:
            out.append(k)
    return ",".join(out) if out else None


def build_deep_report_sh(run_dir, sif_path=None, options=None):
    """단일 시뮬용 deep_report.sh 텍스트 생성.

    Args:
        run_dir: LS-DYNA 결과(d3plot)가 있는 디렉토리 (절대경로)
        sif_path: SmartTwinPostprocessor.sif 경로 (default: /opt/apptainers/...)
        options: dict
            - section_view_axes: list, 기본 ["z"]
            - section_view_fields: list, 기본 ["von_mises"]
            - section_view_mode: "section" | "section_3d" | "iso_surface"
            - ua_threads: int (unified_analyzer)
            - sv_threads: int (section view)
            - hotspot_clusters: bool — 핫스팟 군집 활성화 (기본 False)
            - hotspot_top_percent: float (기본 5.0)
            - hotspot_distance_factor: float (기본 1.5)
            - hotspot_min_elements: int (기본 5)
            - hotspot_max_clusters: int (기본 20)
              → CLI 이름과 1:1. hotspot_clusters 가 꺼져 있으면 아무것도 방출 안 함.
            - deep_extra_args: list|str — 임의 koo_deep_report 인자 pass-through
              (고정 플래그·핫스팟 플래그 **뒤에** 추가되므로 둘 다 주면 이쪽이 이긴다.
               예: ["--per-part-render","--element-quality"])

    Returns:
        sh 스크립트 문자열 (실행 가능, chmod +x 후 bash 실행)
    """
    sif = sif_path or DEFAULT_SIF_PATH
    opts = options or {}
    axes = opts.get("section_view_axes", DEFAULT_AXES)
    fields = opts.get("section_view_fields", DEFAULT_FIELDS)
    mode = opts.get("section_view_mode", DEFAULT_MODE)
    ua = opts.get("ua_threads", DEFAULT_UA_THREADS)
    sv = opts.get("sv_threads", DEFAULT_SV_THREADS)

    axes_str = " ".join(axes)
    fields_str = " ".join(fields)
    # 핫스팟 군집 — 전용 키(hotspot_*) 에서 플래그 생성.
    # 비활성이면 빈 문자열이라 기존 생성물이 그대로 유지된다.
    hotspot = _hotspot_args_str(opts)
    hotspot_line = f" \\\n    {hotspot}" if hotspot else ""
    # 임의 koo_deep_report 인자 pass-through (고정 플래그 뒤 → override 가능).
    # 🔴 전용 키보다 **뒤에** 붙는다 — 둘 다 주면 extra_args 가 이긴다.
    extra = _extra_args_str(opts, "deep_extra_args")
    extra_line = f" \\\n    {extra}" if extra else ""
    # deep_report 성공 후 d3plot 삭제 여부 (디스크 절약, 기본 OFF).
    # set -e 라서 koo_deep_report 가 성공해 아래 done 줄에 도달했을 때만 삭제됨
    # (실패 시 d3plot 보존). impact aggregate 는 report/(analysis_result.json
    # +motion/) 만 읽으므로 영향 없음 — 단 koo_impact_report 가 d3plot 부재 시
    # deep output 재사용을 지원해야 함(force_reuse).
    delete_d3plot = bool(opts.get("delete_d3plot_after_deep", False))
    cleanup_block = ""
    if delete_d3plot:
        cleanup_block = (
            '\n# deep_report 성공 후 d3plot 삭제 (디스크 절약). report/ 보존.\n'
            'echo "[deep_report] d3plot 삭제: $RUN_DIR"\n'
            'rm -f "$RUN_DIR"/d3plot "$RUN_DIR"/d3plot[0-9]* 2>/dev/null || true\n'
        )

    return f"""#!/bin/bash
# Auto-generated by KooChainRun PostprocessShellGenerator
# Per-case deep_report (KooD3plotReader)
set -e
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8


RUN_DIR="{run_dir}"
SIF_PATH="{sif}"
REPORT_DIR="$RUN_DIR/report"

mkdir -p "$REPORT_DIR"

if [ ! -f "$SIF_PATH" ]; then
    echo "[deep_report] ERROR: SIF not found: $SIF_PATH" >&2
    exit 2
fi

echo "[deep_report] start: $RUN_DIR"
apptainer exec --bind /data:/data,"$RUN_DIR":"$RUN_DIR" \\
    "$SIF_PATH" python3 -m koo_deep_report "$RUN_DIR" \\
    -o "$REPORT_DIR" \\
    --section-view \\
    --section-view-backend software \\
    --section-view-mode {mode} \\
    --section-view-axes {axes_str} \\
    --section-view-fields {fields_str} \\
    --ua-threads {ua} \\
    --sv-threads {sv}{hotspot_line}{extra_line}

echo "[deep_report] done: $REPORT_DIR"
{cleanup_block}"""


def build_sphere_report_sh(output_dir, sif_path=None, options=None, runs_subdir="runs"):
    """다각도 통합 sphere_report.sh 텍스트 생성. normal termination 필터 포함.

    Args:
        output_dir: 모든 시뮬 결과의 루트 (절대경로). base_dir/output 형태
        sif_path: SmartTwinPostprocessor.sif 경로
        options: dict
            - yield_stress_mpa: float (default 350)
            - hotspot_part: int | list | "12,15" — 전각도 핫스팟 군집을 그 파트로만(--hotspot-part)
            - sphere_viewer: "canvas"(기본) | "plotly" — 3D 인벨롭 뷰어(--viewer)
            - sphere_extra_args: list | str — 임의 koo_sphere_report 인자 pass-through
            - yield_map: 파트별 항복응력 JSON 경로(덱 단위, 상대 경로는 Designer 가 scenario.json 폴더 기준으로 바꿔 넘기고, 그 밖의 호출은 현재 폴더 기준) — 도구가 --yield-map 을 알 때만 넘긴다. 없으면 도구가
              DropSet.json 의 model.part_yield(KMM 이 덱에서 쓴 값)를 쓴다
        실행 시점에 SIF 의 --help 로 --parallel-runs 를 확인해 있으면 SLURM_CPUS_PER_TASK 만큼 병렬로 돌린다.
        runs_subdir: output_dir 안의 시뮬 폴더 prefix (default "runs")
                     실제로는 output_dir/Run_*/ 패턴이므로 runs_subdir은 호환용

    Returns:
        sh 스크립트 문자열

    KooD3plotReader sphere 구조:
        test_dir/output/Run_*/              (시뮬 결과 + DropSet.json)
        test_dir/analysis_results/Run_*/    (deep_report 결과 + result.json)
        test_dir/runner_config.json         (project 메타데이터)

    우리 구조 매핑:
        test_dir = output_dir의 parent (base_dir)
        analysis_results는 base_dir에 만들고 각 Run_*/Output/report symlink
    """
    sif = sif_path or DEFAULT_SIF_PATH
    opts = options or {}
    yield_stress = opts.get("yield_stress_mpa", DEFAULT_YIELD_STRESS)
    yield_map = opts.get("yield_map") or ""
    if yield_map:   # 잡은 --chdir=/data 에서 돈다 — 상대 경로는 지금 굳힌다(Designer 는 이미 scenario.json 폴더 기준으로 넘김)
        yield_map = os.path.abspath(str(yield_map))
    # 핫스팟 파트 필터 → 그 뒤에 임의 koo_sphere_report 인자 pass-through (고정 플래그 뒤 → override 가능)
    tail = " ".join(x for x in (_hotspot_part_str(opts), _sphere_viewer_str(opts),
                                _extra_args_str(opts, "sphere_extra_args")) if x)
    extra_line = f" \\\n    {tail}" if tail else ""

    return f"""#!/bin/bash
# Auto-generated by KooChainRun PostprocessShellGenerator
# Multi-angle sphere_report (KooD3plotReader)
# Normal termination 필터: Run_*/Output/{{mes0000,d3hsp,*.log}}에서 "N o r m a l    t e r m i n a t i o n" 매칭
set -e
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8


OUTPUT_DIR="{output_dir}"
SIF_PATH="{sif}"
YIELD_STRESS={yield_stress}
# sphere_report는 test_dir = output_dir의 parent (base_dir)
TEST_DIR="$(dirname "$OUTPUT_DIR")"
ANALYSIS_DIR="$TEST_DIR/analysis_results"
REPORT_HTML="$OUTPUT_DIR/sphere_report.html"
REPORT_JSON="$OUTPUT_DIR/sphere_report.json"
NORMAL_LIST="$OUTPUT_DIR/sphere_normal_term.txt"

if [ ! -f "$SIF_PATH" ]; then
    echo "[sphere_report] ERROR: SIF not found: $SIF_PATH" >&2
    exit 2
fi

# Normal termination 필터 + deep_report 결과를 analysis_results/<Run_*>로 symlink
> "$NORMAL_LIST"
rm -rf "$ANALYSIS_DIR" && mkdir -p "$ANALYSIS_DIR"
N_TOTAL=0
N_NORMAL=0
N_NO_DEEP=0
for d in "$OUTPUT_DIR"/Run_*/ "$OUTPUT_DIR"/{runs_subdir}/*/; do
    [ -d "$d" ] || continue
    N_TOTAL=$((N_TOTAL + 1))
    OUT="$d/Output"
    if ! grep -q "N o r m a l    t e r m i n a t i o n" \\
            "$OUT"/mes0000* "$OUT"/d3hsp* "$OUT"/*.log 2>/dev/null; then
        continue
    fi
    echo "$OUT" >> "$NORMAL_LIST"
    BASENAME=$(basename "$d")
    REPORT_DIR="$OUT/report"
    if [ -d "$REPORT_DIR" ] && ([ -f "$REPORT_DIR/result.json" ] || [ -f "$REPORT_DIR/analysis_result.json" ]); then
        ln -sf "$REPORT_DIR" "$ANALYSIS_DIR/$BASENAME"
        N_NORMAL=$((N_NORMAL + 1))
    else
        N_NO_DEEP=$((N_NO_DEEP + 1))
    fi
done
echo "[sphere_report] normal termination + deep_report 완료: $N_NORMAL / $N_TOTAL (deep_report 미완료: $N_NO_DEEP)"

if [ "$N_NORMAL" -eq 0 ]; then
    echo "[sphere_report] ERROR: deep_report 완료된 정상 종료 시뮬 0개 → sphere_report skip" >&2
    if [ "$N_NO_DEEP" -gt 0 ]; then
        echo "  hint: KooChainRun postprocess --deep 먼저 실행" >&2
    fi
    exit 1
fi

# 이 SIF 의 koo_sphere_report 가 아는 옵션만 넘긴다 — 옛 SIF 와 섞여도 모르는 옵션으로 죽지 않게
TOOL_HELP="$(apptainer exec "$SIF_PATH" python3 -m koo_sphere_report --help 2>&1 || true)"
# argparse 옵션 정의 줄(줄 머리 공백 정확히 두 칸 뒤 '-')의 옵션 부분만 본다 — 접힌 설명 글·usage 속 낱말에 속지 않게
# (Python _help_has_option 과 같은 규칙: 옵션 부분을 ', ' 로 갈라 각 조각의 첫 낱말이 그 옵션과 같은가)
has_opt() {{
    printf '%s\\n' "$TOOL_HELP" | awk -v f="$1" '
        {{ sub(/\\r$/, "") }}
        substr($0, 1, 3) == "  -" && substr($0, 1, 4) != "  - " {{
            inv = substr($0, 3); sub(/  .*/, "", inv)
            n = split(inv, parts, ", ")
            for (i = 1; i <= n; i++) {{ split(parts[i], w, /[ =]/); if (w[1] == f) found = 1 }}
        }}
        END {{ exit found ? 0 : 1 }}'
}}
EXTRA=()
if has_opt --parallel-runs; then
    EXTRA+=(--parallel-runs "${{SLURM_CPUS_PER_TASK:-1}}")
elif [ "${{SPHERE_SIZED_FOR:-}}" = parallel ]; then
    echo "[sphere_report] 🔴 경고: 이 잡의 자원은 병렬 도구(--parallel-runs) 기준인데 이 노드 SIF 의 koo_sphere_report 는 옛 판이다 — 메모리·시간이 모자랄 수 있다(헤드와 노드의 SIF 판을 맞출 것): $SIF_PATH" >&2
fi
YIELD_MAP={shlex.quote(str(yield_map))}
if [ -n "$YIELD_MAP" ]; then
    if [ ! -f "$YIELD_MAP" ]; then
        echo "[sphere_report] 경고: yield_map 파일이 없다 — $YIELD_MAP (덱 파트별 항복응력·단일 기본값으로 판정)" >&2
    elif has_opt --yield-map; then
        EXTRA+=(--yield-map "$YIELD_MAP")
    else
        echo "[sphere_report] 경고: 이 SIF 의 koo_sphere_report 는 --yield-map 을 모른다 — 단일 항복응력 $YIELD_STRESS 로 판정" >&2
    fi
fi

echo "[sphere_report] start: test_dir=$TEST_DIR (analysis_results=$N_NORMAL, 추가 옵션: ${{EXTRA[*]:-없음}})"
TOOL_LOG="$OUTPUT_DIR/sphere_report.tool.log"
set -o pipefail
apptainer exec --bind /data:/data,"$TEST_DIR":"$TEST_DIR" \\
    "$SIF_PATH" python3 -m koo_sphere_report \\
    --test-dir "$TEST_DIR" \\
    -o "$REPORT_HTML" \\
    --json "$REPORT_JSON" \\
    --yield-stress "$YIELD_STRESS" "${{EXTRA[@]}}"{extra_line} 2>&1 | tee "$TOOL_LOG"
set +o pipefail
# 도구가 결과를 하나도 못 읽고도 rc 0 으로 끝나는 판(샤드 폴더에 output/ 이 빠진 경우 등)을 막는다 — 잡 성공으로 오인됐다
LOADED="$(grep -oE 'Loaded [0-9]+ results' "$TOOL_LOG" | tail -1 | grep -oE '[0-9]+' || true)"
if [ -z "$LOADED" ]; then
    echo "[sphere_report] 경고: 도구 출력에 'Loaded N results' 줄이 없어 결과 0건 여부를 셸이 확인하지 못했다 — $TOOL_LOG" >&2
fi
if [ -n "$LOADED" ] && [ "$LOADED" -eq 0 ]; then
    echo "[sphere_report] ERROR: koo_sphere_report 가 결과를 하나도 읽지 못했다(Loaded 0, analysis_results=$N_NORMAL) — 빈 리포트다" >&2
    exit 3
fi
if [ -n "$LOADED" ] && [ "$LOADED" -lt "$N_NORMAL" ]; then
    echo "[sphere_report] 경고: analysis_results $N_NORMAL 개 중 $LOADED 개만 읽었다" >&2
fi

echo "[sphere_report] done: $REPORT_HTML"
"""


def build_impact_report_sh(output_dir, sif_path=None, options=None):
    """전위치 부분충격(IMPACT) 통합 impact_report.sh 텍스트 생성.

    sphere_report 와 같은 aggregate 리포트지만 더 단순하다:
    koo_impact_report 의 flat-DOE 경로(load_partial_impact_doe_report)가
    내부에서 unified_analyzer 를 Run 마다 직접 실행하므로, sphere 처럼
    deep_report 결과를 analysis_results/ 로 symlink 하는 dance 가 불필요하다.
    (normal-termination 사전 필터는 v1 생략 — 로더가 깨진 Run 을 자체 skip.)

    Args:
        output_dir: 모든 시뮬 결과의 루트 (절대경로). base_dir/output 형태
        sif_path: SmartTwinPostprocessor.sif 경로
        options: dict
            - impact_yield_stress: float (optional). 있으면 --yield-stress 부착,
              없으면 per-part *MAT 카드 사용 (impact 단위는 deck 의존이므로
              sphere 의 yield_stress_mpa 를 재사용하지 않는다).

    Returns:
        sh 스크립트 문자열

    매핑: test_dir = output_dir 의 parent (base_dir), sphere 와 동일.
          koo_impact_report --test-dir 가 test_dir/output/Run_*/Output/d3plot
          + step_config.txt 를 자동 탐색한다.
    """
    sif = sif_path or DEFAULT_SIF_PATH
    opts = options or {}
    yield_stress = opts.get("impact_yield_stress", None)
    yield_line = ""
    if yield_stress not in (None, "", 0):
        yield_line = f' \\\n    --yield-stress "{yield_stress}"'
    # 임의 koo_impact_report 인자 pass-through (고정 플래그 뒤 → override 가능)
    extra = _extra_args_str(opts, "impact_extra_args")
    extra_line = f" \\\n    {extra}" if extra else ""

    return f"""#!/bin/bash
# Auto-generated by KooChainRun PostprocessShellGenerator
# Multi-position partial-impact impact_report (KooD3plotReader)
set -e
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8


OUTPUT_DIR="{output_dir}"
SIF_PATH="{sif}"
# impact_report 는 test_dir = output_dir 의 parent (base_dir)
TEST_DIR="$(dirname "$OUTPUT_DIR")"
REPORT_HTML="$OUTPUT_DIR/impact_report.html"
REPORT_JSON="$OUTPUT_DIR/impact_report.json"

if [ ! -f "$SIF_PATH" ]; then
    echo "[impact_report] ERROR: SIF not found: $SIF_PATH" >&2
    exit 2
fi

# Old-SIF soft-degrade: koo_impact_report 미포함 SIF(2.3.x 이전)면 경고 후 skip.
if ! apptainer exec "$SIF_PATH" python3 -c "import koo_impact_report" >/dev/null 2>&1; then
    echo "[impact_report] WARN: SIF 에 koo_impact_report 없음 (구버전 SIF?) — skip" >&2
    exit 0
fi

echo "[impact_report] start: test_dir=$TEST_DIR"
apptainer exec --bind /data:/data,"$TEST_DIR":"$TEST_DIR" \\
    "$SIF_PATH" python3 -m koo_impact_report \\
    --test-dir "$TEST_DIR" \\
    --format html json \\
    --output "$REPORT_HTML" \\
    --json "$REPORT_JSON"{yield_line}{extra_line}

echo "[impact_report] done: $REPORT_HTML"
"""


def report_mode_from_runner_config(runner_config):
    """runner_config 에서 종합 리포트 모드를 판정: "IMPACT" | "DROP".

    DROP→sphere_report, IMPACT→impact_report 라우팅에 사용. KooD3plotReader
    scripts/post_analyze.sh 의 scenario.json mode_sequence 판정과 동일 규칙:
      - 모든 step mode 가 IMPACT → "IMPACT"
      - 모든 step mode 가 DROP   → "DROP"
      - mixed → 첫 step mode
      - 비어있음 → doe_positions(IMPACT) vs doe_angles(DROP) fallback,
        그것도 없으면 "DROP" (현행 기본 동작 보존)

    1차 소스는 runner_config["scenario"]["steps"][].mode
    (CumulativeDesigner 가 cumulative step 당 1개씩 직렬화).
    """
    rc = runner_config or {}
    # DWI(drop_weight_impact) runner_config 는 chain 스키마(scenario.steps /
    # doe_positions)가 없어 기본값 DROP 으로 떨어져 sphere 로 오라우팅됐음
    # (2026-07-10 job 806 실측) — 최상위 mode 디스패치 키를 최우선 판정.
    if str(rc.get("mode", "")).lower() == "drop_weight_impact":
        return "IMPACT"
    sc = rc.get("scenario") or {}
    steps = sc.get("steps") or []
    modes = [str(s.get("mode", "")).upper() for s in steps if s.get("mode")]
    if modes:
        if all(m == "IMPACT" for m in modes):
            return "IMPACT"
        if all(m == "DROP" for m in modes):
            return "DROP"
        return modes[0]
    # Fallback: IMPACT 시나리오만 doe_positions 를 emit, DROP 은 doe_angles.
    if sc.get("doe_positions"):
        return "IMPACT"
    return "DROP"


def build_deep_report_sbatch(run_dir, sh_path, options=None, environment=None,
                              dependency_id=None, job_name_suffix=""):
    """단일 시뮬용 deep_report sbatch (separate_job 모드).

    LS-DYNA 잡 끝나면 dependent 잡으로 별도 노드에서 deep_report 실행 → 시뮬 노드 해방.

    Args:
        run_dir: Run_*/ 폴더 (sbatch output 위치 + cwd)
        sh_path: deep_report.sh 절대경로
        options: dict (deep_timeout_seconds, deep_memory, deep_ncpu, deep_time_limit, deep_partition)
        environment: dict (ncpu, memory, partition default fallback)
        dependency_id: Slurm job ID (afterok). 없으면 즉시 실행
        job_name_suffix: 잡 이름 suffix (보통 Run_id)

    Returns:
        sbatch 텍스트
    """
    import os as _os
    opts = options or {}
    env = environment or {}
    job_env_block = job_env_lines(env)
    ncpu = opts.get("deep_ncpu", env.get("ncpu", 1))
    memory = opts.get("deep_memory", env.get("memory", "8G"))
    partition = opts.get("deep_partition", env.get("partition", ""))
    timeout_s = opts.get("deep_timeout_seconds", 7200)
    time_limit = opts.get("deep_time_limit", _seconds_to_slurm_time(timeout_s + 600))

    deps = ""
    if dependency_id:
        deps = f"#SBATCH --dependency=afterok:{dependency_id}\n"
    partition_line = f"#SBATCH --partition={partition}\n" if partition else ""

    suffix = f"_{job_name_suffix}" if job_name_suffix else ""
    return f"""#!/bin/bash
#SBATCH --job-name=deep_report{suffix}
#SBATCH --output={run_dir}/deep_report.slurm.out
#SBATCH --error={run_dir}/deep_report.slurm.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={ncpu}
#SBATCH --mem={memory}
#SBATCH --time={time_limit}
#SBATCH --chdir=/data
{partition_line}{deps}
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

{job_env_block}bash {sh_path}
"""


def _seconds_to_slurm_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"


# ── sphere_report 자원 — 런 수 N 으로 잰다(「sphere_report 자동화 수정안 v1.0」 실측) ──────────────────
# 예전엔 런이 10개든 1000개든 LS-DYNA 런 환경값(environment.ncpu·memory)과 고정 시간을 줘, M3_P2(979런)가
# 24시간 TIMEOUT·MaxRSS 84.7 GB 로 산출물 0개였다.
# - 옛 도구(모든 런의 흐름을 끝까지 메모리에 든다): 0.087 GB/런 → 32 + 0.10 GB/런.
# - 새 도구(koo_sphere_report --parallel-runs — 같은 판에 2패스, 상위 60개 흐름만 든다): 누적 ≈ 5.3 GB
#   + 워커마다 런 하나(실측 전 보수 2 GB). --help 에 --parallel-runs 가 있으면 새 도구로 본다.
# - 시간: 캐시 miss 런당 ≈ 3.2분(단일 스레드) → 0.06 h/런, 워커 W 개면 W 로 나눈다. 합치기·HTML 몫 2 h.
SPHERE_OLD_MEM_BASE_GB = 32
SPHERE_OLD_MEM_PER_RUN_GB = 0.10
SPHERE_NEW_MEM_BASE_GB = 6
SPHERE_NEW_MEM_PER_WORKER_GB = 2
SPHERE_HOURS_BASE = 2.0
SPHERE_HOURS_PER_RUN = 0.06
SPHERE_MIN_HOURS = 4.0
SPHERE_MAX_WORKERS = 16


def count_runs(runner_config):
    """runner_config 의 시뮬레이션 수 — 시나리오의 step 하나가 Run 하나다(sphere 가 모으는 Run_* 의 상한).
    jobs.json 의 잡 ID 수는 배열 잡이라 런 수가 아니다. 셀 수 없으면 None."""
    try:
        n = sum(len(sc.get("steps") or []) for sc in (runner_config or {}).get("scenarios") or [])
    except (AttributeError, TypeError):
        return None
    return n or None


def _help_has_option(text, flag):
    """argparse --help 에서 flag 가 옵션 정의 줄에 있는가 — sphere_report.sh 의 has_opt 와 같은 규칙.
    정의 줄 = 줄 머리 공백 정확히 두 칸 뒤 '-'(argparse 기본 들여쓰기). 그 줄의 옵션 부분(처음 나오는 두 칸 공백 앞)을
    ', ' 로 갈라 각 조각의 첫 낱말(공백·'=' 앞)이 flag 와 같아야 한다 — '-j N, --flag N'·'--flag {1,2,4}'·'--flag [N ...]'·
    '-y A B, --flag A B' 를 잡고, 더 깊게 들여 접힌 설명 글·usage·epilog 속 언급에는 속지 않는다(옛 도구에 모르는 옵션을
    넘기면 argparse 로 죽는다)."""
    for ln in (text or "").splitlines():
        if not ln.startswith("  -") or ln.startswith("  - "):
            continue
        inv = re.split(r" {2,}", ln[2:], maxsplit=1)[0]
        if any(re.split(r"[ =]", part, maxsplit=1)[0] == flag for part in inv.split(", ")):
            return True
    return False


def sphere_tool_flags(sif_path=None, timeout=180):
    """SIF 안 koo_sphere_report --help 가 아는 플래그 집합(--parallel-runs·--yield-map). 확인하지 못하면 빈 집합 — 옛 도구로 본다."""
    import subprocess
    try:
        r = subprocess.run(["apptainer", "exec", sif_path or DEFAULT_SIF_PATH, "python3", "-m", "koo_sphere_report", "--help"],
                           capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
    except Exception:  # noqa: BLE001 — apptainer 없음·시간 초과 등은 '모름'
        return set()
    text = (r.stdout or "") + (r.stderr or "")
    return {f for f in ("--parallel-runs", "--yield-map") if _help_has_option(text, f)}


def _slurm_minutes(text):
    """Slurm 시간 글 → 분. 'UNLIMITED' 나 못 읽는 글은 None. (D-HH:MM:SS·D-HH:MM·D-HH·HH:MM:SS·MM:SS·MM)"""
    s = str(text).strip()
    if not s or s.upper() in ("UNLIMITED", "INFINITE", "NONE", "N/A"):
        return None
    try:
        days = 0
        if "-" in s:
            d, s = s.split("-", 1)
            days = int(d)
            p = [int(x) for x in s.split(":")] + [0, 0]
            h, m, sec = p[0], p[1], p[2]
        else:
            p = [int(x) for x in s.split(":")]
            h, m, sec = {3: (p + [0])[:3], 2: [0] + p, 1: [0, p[0], 0]}[len(p)]
    except (ValueError, KeyError):
        return None
    return days * 1440 + h * 60 + m + (1 if sec > 0 else 0)


def _fmt_slurm_time(minutes):
    minutes = int(math.ceil(minutes))
    d, rem = divmod(minutes, 1440)
    h, m = divmod(rem, 60)
    return f"{d}-{h:02d}:{m:02d}:00" if d else f"{h:02d}:{m:02d}:00"


def _mem_gb(text):
    """'32G'·'32000M'·'1T'·'32000'(Slurm 기본 단위 MB) → GB. 못 읽으면 None."""
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([KMGT]?)B?\s*", str(text).upper())
    if not m:
        return None
    return float(m.group(1)) * {"K": 1 / 1048576, "M": 1 / 1024, "G": 1.0, "T": 1024.0}[m.group(2) or "M"]


def partition_limits(partitions, timeout=30):
    """쉼표로 준 파티션들 가운데 가장 넉넉한 MaxTime(분)·노드 코어 수·노드 메모리(GB) — Slurm 은 잡이 들어가는 파티션·노드를 고른다.
    노드 값은 노드마다 읽는다 — `sinfo -o %m` 는 노드가 섞인 파티션에서 최솟값에 '+' 를 붙인다(man sinfo).
    파티션을 주지 않으면(sbatch 에 --partition 이 없으면) 잡이 가는 기본 파티션(Default=YES)을 본다.
    {'max_minutes': 분 또는 None(무제한), 'nodes': [(코어, 메모리 GB — 1GB 밑은 0.0)], 'max_cpus': 코어, 'max_mem_gb': GB}.
    잡은 한 노드에 들어가야 하므로 자원 산정은 nodes(노드 모양)를 쓴다 — 코어 최대 노드와 메모리 최대 노드가 다를 수 있다.
    읽지 못하면 빈 dict(상한을 걸지 않는다)."""
    import subprocess
    names = [p.strip() for p in str(partitions or "").split(",") if p.strip()]
    out = {}
    try:
        if not names:
            r = subprocess.run(["scontrol", "-o", "show", "partition"], capture_output=True, text=True, timeout=timeout,
                               encoding='utf-8', errors='replace')
            names = re.findall(r"^PartitionName=(\S+).*\bDefault=YES\b", r.stdout or "", re.M)
            if not names:
                return {}
        times = []
        for p in names:
            r = subprocess.run(["scontrol", "show", "partition", p], capture_output=True, text=True, timeout=timeout,
                               encoding='utf-8', errors='replace')
            mt = re.search(r"MaxTime=(\S+)", r.stdout or "")
            if mt:
                times.append(_slurm_minutes(mt.group(1)))
        if times:
            out["max_minutes"] = None if any(t is None for t in times) else max(times)
        r = subprocess.run(["sinfo", "-N", "-h", "-p", ",".join(names), "-o", "%c %m"], capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        rows = [ln.split() for ln in (r.stdout or "").splitlines()]
        rows = [(int(c), float(m.rstrip("+"))) for c, m in (x for x in rows if len(x) == 2)
                if re.fullmatch(r"\d+", c) and re.fullmatch(r"\d+(\.\d+)?\+?", m)]
        # 노드 모양(코어, 메모리 GB) — 요청은 한 노드에 들어가야 한다. 1GB 밑(RealMemory 미설정이면 1MB)은 0.0 — --mem=0 만 받는다
        nodes = sorted({(c, m / 1024.0 if m >= 1024 else 0.0) for c, m in rows})
        if nodes:
            out["nodes"] = nodes
            out["max_cpus"] = max(c for c, _ in nodes)
            mems = [m for _, m in nodes if m]
            if mems:
                out["max_mem_gb"] = max(mems)
    except Exception:  # noqa: BLE001 — Slurm 명령이 없는 곳(시험·로컬)에서는 상한 없이
        return {}
    return out


def sphere_resources(n_runs, parallel, ncpu=None):
    """런 수 → (CPU, 메모리 GB, 시간 분). parallel = 도구가 --parallel-runs(2패스)를 아는가. ncpu 를 주면 그 수를 워커로 본다."""
    n = max(1, int(n_runs))
    if parallel:
        w = int(ncpu) if ncpu else min(SPHERE_MAX_WORKERS, max(2, math.ceil(n / 50)))
        mem = SPHERE_NEW_MEM_BASE_GB + w * SPHERE_NEW_MEM_PER_WORKER_GB
        cpus = w
    else:   # 옛 도구는 단일 스레드 — 8코어를 줘도 7개가 논다
        w = 1
        mem = SPHERE_OLD_MEM_BASE_GB + SPHERE_OLD_MEM_PER_RUN_GB * n
        cpus = int(ncpu) if ncpu else 2
    hours = max(SPHERE_MIN_HOURS, SPHERE_HOURS_BASE + SPHERE_HOURS_PER_RUN * n / w)
    return cpus, int(math.ceil(mem)), int(math.ceil(hours * 60))


def _positive_int(value):
    """'8'·8·'8.0' → 8. 못 읽거나 1 보다 작으면 None."""
    try:
        n = int(float(str(value).strip()))
    except (TypeError, ValueError, OverflowError):
        return None
    return n if n >= 1 else None


def _time_unlimited(text):
    """명시 시간이 '제한 없음' 인가 — UNLIMITED·INFINITE·0 (man sbatch: "A time limit of zero requests that no time limit be imposed")."""
    return str(text).strip().upper() in ("UNLIMITED", "INFINITE") or _slurm_minutes(text) == 0


def _node_shapes(lim):
    """partition_limits 결과의 노드 모양 [(코어, 메모리 GB)]. 코어·메모리 None 은 모름(상한 없음). 메모리 0.0 은 RealMemory 가
    1GB 밑인 노드(미설정이면 1MB — slurm.conf "RealMemory … The default value is 1") — Slurm 은 설정된 RealMemory 로 노드를
    거르므로(node_scheduler.c _build_node_list) 그 노드는 --mem=0(노드 메모리 전부)만 받는다.
    nodes 가 없으면(시험 주입) max_cpus·max_mem_gb 를 노드 하나로 본다."""
    raw = lim.get("nodes") or ([(lim.get("max_cpus"), lim.get("max_mem_gb"))]
                               if (lim.get("max_cpus") or lim.get("max_mem_gb") is not None) else [])
    return [(c or None, None if m is None else (float(m) if m >= 1 else 0.0)) for c, m in raw]


def _sphere_auto_resources(n_runs, sif_path, partition, explicit_ncpu, explicit_mem, explicit_time,
                           tool_flags=None, limits=None):
    """sphere 잡 자원을 런 수로 잰다. 명시값이 산출값보다 크면 명시값, 작으면 산출값을 쓰고 알린다(MCP 가 모든 캠페인에
    sphere_time_limit 04:00:00 을 넣어 '명시값 우선' 이면 고침이 먹지 않는다). 노드가 감당하지 못하면 줄이고 알린다 —
    요청(CPU·메모리)은 한 노드에 함께 들어가야 한다(아니면 Slurm 이 "Requested node configuration is not available" 로
    거절한다).
    - 새 도구: 노드마다 코어·메모리(6+2W, 명시 메모리가 더 크면 그것)에 맞는 가장 큰 W 를 골라 다시 잰다.
    - 옛 도구: 들어가는 노드가 없을 때만 줄인다.
    - 어느 쪽이든 메모리를 아는 노드에 못 들어가고 RealMemory 미설정 노드(--mem=0 만 받음)가 있으면 --mem=0 으로 낸다.
      그것도 없으면 메모리가 가장 큰 노드에 맞추고 🔴 로 알린다.
    Returns: (cpus, memory, time_limit, parallel)"""
    flags = sphere_tool_flags(sif_path) if tool_flags is None else tool_flags
    parallel = "--parallel-runs" in flags
    notes = []
    ncpu = None
    if explicit_ncpu is not None:
        ncpu = _positive_int(explicit_ncpu)
        if ncpu is None:
            notes.append(f"sphere_ncpu {explicit_ncpu!r} 를 정수로 읽지 못해 무시한다")
    lim = partition_limits(partition) if limits is None else limits
    shapes = _node_shapes(lim)
    known = [x for x in shapes if x[1] != 0.0]      # 메모리를 알거나(>0) 모름(None)
    zero = [x for x in shapes if x[1] == 0.0]       # RealMemory 미설정 — --mem=0 만 받는다
    em = _mem_gb(explicit_mem) if explicit_mem is not None else None    # 0 = 노드 메모리 전부(man sbatch)
    cpus, mem_gb, minutes = sphere_resources(n_runs, parallel, ncpu)
    node, whole = None, em == 0     # 맞춘 노드 모양, --mem=0(노드 메모리 전부)으로 낼까

    def _gb(m):
        return "모름" if m is None else f"{int(m)}G"

    def _mem_ok(x, g):          # 이 노드가 --mem=gG 를 받는가 — 미설정(0.0) 노드는 --mem=0 만
        return x[1] is None or (x[1] > 0 and x[1] >= g)

    if parallel and shapes:
        def w_on(x):            # 이 노드에서 코어·모형 메모리(6+2W)가 함께 맞는 가장 큰 W(메모리 모름·미설정은 코어만)
            w = min(cpus, x[0]) if x[0] else cpus
            if x[1]:
                w = min(w, int((x[1] - SPHERE_NEW_MEM_BASE_GB) // SPHERE_NEW_MEM_PER_WORKER_GB))
            return w
        if whole:                                           # 명시 --mem=0 — 어느 노드든 메모리를 받는다
            pool = shapes
        elif em and any(_mem_ok(x, em) for x in known):    # 명시 메모리를 받는 노드가 있으면 그 가운데서
            pool = [x for x in known if _mem_ok(x, em)]
        else:                                               # 명시 메모리를 받는 노드가 없으면 W 를 위해 고르고 아래서 깎는다(🔴)
            pool = known
        cand = [(w_on(x), math.inf if x[1] is None else x[1], x) for x in pool]
        cand = [t for t in cand if t[0] >= 1]
        if cand:
            w, _, node = max(cand, key=lambda t: (t[0], t[1]))
        elif zero:              # 메모리를 아는 노드엔 워커 하나도 못 들어가고 미설정 노드가 있다 — --mem=0
            node = max(zero, key=lambda x: x[0] or math.inf)
            w, whole = (min(cpus, node[0]) if node[0] else cpus), True
        else:                   # 워커 하나도 못 들이는 노드뿐 — 메모리가 가장 큰 노드에 1워커부터, 아래서 메모리를 줄인다(🔴)
            node = max(known, key=lambda x: (math.inf if x[1] is None else x[1], x[0] or math.inf))
            w = max(1, w_on(node))
        if w != cpus:
            notes.append(f"워커 {cpus} → {w} — 코어 {node[0] or '모름'}·메모리 "
                         f"{'미설정(--mem=0)' if node[1] == 0.0 else _gb(node[1])} 노드에 맞춘다")
            cpus, mem_gb, minutes = sphere_resources(n_runs, True, w)
    if em is not None and (em == 0 or em >= mem_gb):
        memory = str(explicit_mem)
    else:
        if explicit_mem is not None:
            notes.append(f"메모리 {explicit_mem} 이 {n_runs}런 산출값 {mem_gb}G 보다 작아 {mem_gb}G 를 쓴다")
        memory = f"{mem_gb}G"
    need_gb = None if em == 0 else (_mem_gb(memory) or 0.0)
    if shapes and not parallel:
        # 옛 도구 — 메모리를 받는 노드 가운데 코어도 맞는 노드가 있으면 그대로, 코어만 모자라면 코어 큰 노드에 맞춘다
        pool = shapes if whole else [x for x in known if _mem_ok(x, need_gb)]
        if pool:
            if not any((not x[0] or x[0] >= cpus) for x in pool):
                node = max(pool, key=lambda x: x[0] or math.inf)
        elif zero:              # 메모리를 아는 노드는 못 받고 미설정 노드가 있다 — --mem=0
            node, whole = max(zero, key=lambda x: x[0] or math.inf), True
        else:                   # 어느 노드도 그 메모리를 못 받는다 — 메모리가 가장 큰 노드에 맞추고 아래서 줄인다(🔴)
            node = max(known, key=lambda x: (math.inf if x[1] is None else x[1], x[0] or math.inf))
        if node and node[0] and cpus > node[0]:
            notes.append(f"CPU {cpus} 가 노드 코어 {node[0]} 를 넘어 {node[0]} 로 줄인다")
            cpus = node[0]
    if whole and em != 0:
        lack = [x for x in known if x[1] and need_gb and x[1] < need_gb]
        notes.append(("🔴 " if lack else "") + f"메모리 {memory} 를 받는 노드가 RealMemory 미설정 노드뿐이라 --mem=0(노드 메모리 전부)으로"
                     f" 낸다 — 그 노드의 실제 메모리는 모른다"
                     + (f". --mem=0 은 메모리를 아는 노드({', '.join(_gb(x[1]) for x in lack)})에도 앉을 수 있고 거기선 모자란다"
                        if lack else ""))
        memory = "0"
    if node and node[1] and not whole and (_mem_gb(memory) or 0.0) > node[1]:
        cap = int(node[1])
        notes.append(f"🔴 메모리 {memory} 가 노드 메모리 {cap}G 를 넘어 {cap}G 로 줄인다 — OOM 이 날 수 있다")
        memory = f"{cap}G"
    et = _slurm_minutes(explicit_time) if explicit_time is not None else None
    if explicit_time is not None and _time_unlimited(explicit_time):
        time_limit, req_minutes = str(explicit_time), math.inf
    elif et is not None and et >= minutes:
        time_limit, req_minutes = str(explicit_time), et
    else:
        if explicit_time is not None:
            notes.append(f"시간 {explicit_time} 이 {n_runs}런 산출값 {_fmt_slurm_time(minutes)} 보다 짧아 산출값을 쓴다")
        time_limit, req_minutes = _fmt_slurm_time(minutes), minutes
    if lim.get("max_minutes") and req_minutes > lim["max_minutes"]:
        cap_t = _fmt_slurm_time(lim["max_minutes"])
        if minutes > lim["max_minutes"]:
            notes.append(f"🔴 시간 {time_limit} 이 파티션 한도 {cap_t} 를 넘어 한도로 줄인다 — 끝나지 못할 수 있다"
                         + ("" if parallel else " (병렬 도구(--parallel-runs) 판 SIF 면 크게 준다)"))
        else:
            notes.append(f"시간 {time_limit} 을 파티션 한도 {cap_t} 로 줄인다 — 한도를 넘는 요청은 PENDING 에 머문다")
        time_limit = cap_t
    print(f"[Sphere Postprocess] 자원 — {n_runs}런, 도구 {'병렬(--parallel-runs)' if parallel else '순차'}: "
          f"CPU {cpus} · 메모리 {memory} · 시간 {time_limit}")
    for n in notes:
        print(f"  ⚠️  {n}")
    return cpus, memory, time_limit, parallel


def build_sphere_sbatch(output_dir, sif_path=None, options=None, environment=None,
                        dependency_ids=None, runs_subdir="runs", n_runs=None, tool_flags=None, limits=None):
    """Slurm dependent sphere job용 sbatch 텍스트.

    Args:
        output_dir: 시뮬 루트 (절대경로)
        sif_path, options, runs_subdir: build_sphere_report_sh와 동일
        environment: dict (ncpu, memory, partition 등)
        dependency_ids: list[str] of Slurm job IDs (afterany)
        n_runs: 캠페인 런 수(count_runs) — 주면 자원을 런 수로 잰다(_sphere_auto_resources).
            options.sphere_auto_resources=false 거나 n_runs 가 없으면 예전 규칙(명시값 > environment > 기본)
        tool_flags, limits: 시험용 주입(없으면 SIF --help·scontrol 로 읽는다)

    Returns:
        sbatch 스크립트 문자열
    """
    env = environment or {}
    job_env_block = job_env_lines(env)
    opts = options or {}
    partition = opts.get("sphere_partition", env.get("partition", ""))
    explicit_ncpu = opts.get("sphere_ncpu", env.get("sphere_ncpu"))
    explicit_mem = opts.get("sphere_memory", env.get("sphere_memory"))
    explicit_time = opts.get("sphere_time_limit", env.get("sphere_time_limit"))
    sized_line = ""
    if n_runs and opts.get("sphere_auto_resources", True):
        ncpu, memory, time_limit, parallel = _sphere_auto_resources(
            n_runs, sif_path or opts.get("sif_path"), partition, explicit_ncpu, explicit_mem, explicit_time,
            tool_flags=tool_flags, limits=limits)
        # 자원을 어느 도구 판 기준으로 잡았는지 — 노드 SIF 가 옛 판이면 sphere_report.sh 가 경고한다(헤드·노드 SIF 엇갈림)
        sized_line = f"export SPHERE_SIZED_FOR={'parallel' if parallel else 'sequential'}\n"
    else:
        # 예전 규칙: options(postprocess block) > environment > default
        ncpu = explicit_ncpu if explicit_ncpu is not None else env.get("ncpu", 8)
        memory = explicit_mem if explicit_mem is not None else env.get("memory", "16G")
        time_limit = explicit_time if explicit_time is not None else "04:00:00"
    job_name = "sphere_report"

    deps = ""
    if dependency_ids:
        deps = f"#SBATCH --dependency=afterany:{':'.join(str(i) for i in dependency_ids)}\n"

    partition_line = f"#SBATCH --partition={partition}\n" if partition else ""

    return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={output_dir}/sphere_report.slurm.out
#SBATCH --error={output_dir}/sphere_report.slurm.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={ncpu}
#SBATCH --mem={memory}
#SBATCH --time={time_limit}
#SBATCH --chdir=/data
{partition_line}{deps}
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

{job_env_block}{sized_line}bash {output_dir}/sphere_report.sh
"""


def build_impact_sbatch(output_dir, sif_path=None, options=None, environment=None,
                        dependency_ids=None):
    """Slurm dependent impact job 용 sbatch 텍스트 (sphere sbatch 와 대칭).

    Args:
        output_dir: 시뮬 루트 (절대경로)
        sif_path, options: build_impact_report_sh 와 동일
        environment: dict (ncpu, memory, partition 등)
        dependency_ids: list[str] of Slurm job IDs (afterany)

    Returns:
        sbatch 스크립트 문자열
    """
    env = environment or {}
    job_env_block = job_env_lines(env)
    opts = options or {}
    # 우선순위: options(postprocess block) > environment > default
    ncpu = opts.get("impact_ncpu", env.get("impact_ncpu", env.get("ncpu", 8)))
    memory = opts.get("impact_memory", env.get("impact_memory", env.get("memory", "16G")))
    partition = opts.get("impact_partition", env.get("partition", ""))
    time_limit = opts.get("impact_time_limit", env.get("impact_time_limit", "04:00:00"))
    job_name = "impact_report"

    deps = ""
    if dependency_ids:
        deps = f"#SBATCH --dependency=afterany:{':'.join(str(i) for i in dependency_ids)}\n"

    partition_line = f"#SBATCH --partition={partition}\n" if partition else ""

    return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={output_dir}/impact_report.slurm.out
#SBATCH --error={output_dir}/impact_report.slurm.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={ncpu}
#SBATCH --mem={memory}
#SBATCH --time={time_limit}
#SBATCH --chdir=/data
{partition_line}{deps}
# ── 로케일 고정 (컴파일 바이너리의 ascii 기동 방지) ──
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

{job_env_block}bash {output_dir}/impact_report.sh
"""
