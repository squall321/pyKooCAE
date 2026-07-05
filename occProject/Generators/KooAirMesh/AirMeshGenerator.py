# AIRMESH 오케스트레이터: 문제정의 JSON 로드/검증 → 파이프라인 실행 → 리포트/Complete 라인
# 기계 계약: exit code는 항상 0. 성공="Complete AIRMESH : <report경로>" / 실패="AIRMESH FAILED : <사유>"
import copy
import json
import os
import time

_CONFIG_DEFAULTS = {
    "airmesh_version": None,   # 필수 (=1)
    "input_step": None,        # 필수
    "mesh_size": None,         # 필수 (>0, 모델 단위)
    "units": "model",          # 문서화 라벨 (변환 없음)
    "occ_target_unit": "",
    "padding": 0.0,            # 스칼라 또는 [x-,x+,y-,y+,z-,z+]
    "padding_relative": False,
    "solid_selection": "all",  # "all" 또는 1-based 인덱스 리스트
    "heal": "auto",            # auto | always | never
    "heal_tolerance": 1e-8,
    "mesh": {
        "mode": "tetra",       # v1: tetra만 (hex_core는 Phase 5 예약)
        "algorithm3d": "hxt",  # hxt | delaunay | frontal
        "fallback": True,
        "optimize": True,
        "threads": 0,
        "size_guard": True,
        "max_estimated_elements": 50000000,
    },
    "outputs": {
        "prefix": None,        # 기본: config 파일명 stem
        "dir": None,           # 기본: cwd (KAM workdir 관행)
        "air_stl": True,
        "split_stls": True,
        "volume_mesh": "msh",  # msh | vtk | both | none
        "geometry_debug": False,
        "stl_binary": True,
        "fix_orientation": True,
    },
    "validation": {
        "volume_error_warn": 0.05,
        "min_sicn_warn": 0.10,
        "fail_on_inverted": True,
    },
}


def load_config(config_path):
    """JSON 로드 + 디폴트 병합 + 검증. (cfg, errors, warnings) 반환."""
    errors, warnings = [], []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user = json.load(f)
    except Exception as e:
        return None, ["config JSON 파싱 실패: {e}".format(e=e)], warnings
    if not isinstance(user, dict):
        return None, ["config 최상위는 객체(dict)여야 함"], warnings

    cfg = copy.deepcopy(_CONFIG_DEFAULTS)
    _merge(cfg, user, "", errors, warnings)
    _validate(cfg, config_path, errors)
    return cfg, errors, warnings


def _merge(base, user, prefix, errors, warnings):
    for key, val in user.items():
        if key not in base:
            warnings.append("알 수 없는 설정 키 무시: {p}{k}".format(p=prefix, k=key))
            continue
        if isinstance(base[key], dict) and base[key]:
            if isinstance(val, dict):
                _merge(base[key], val, prefix + key + ".", errors, warnings)
            else:
                errors.append("{p}{k}는 객체여야 함".format(p=prefix, k=key))
        else:
            base[key] = val


def _validate(cfg, config_path, errors):
    def _num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    if cfg["airmesh_version"] != 1:
        errors.append("airmesh_version은 1이어야 함 (현재: {v})".format(
            v=cfg["airmesh_version"]))
    if not isinstance(cfg["input_step"], str) or not cfg["input_step"]:
        errors.append("input_step (STEP 파일 경로) 필수")
    if not (_num(cfg["mesh_size"]) and cfg["mesh_size"] > 0):
        errors.append("mesh_size는 양수 필수")

    pad = cfg["padding"]
    if isinstance(pad, list):
        if len(pad) != 6 or not all(_num(v) and v >= 0 for v in pad):
            errors.append("padding 리스트는 음이 아닌 수 6개 [x-,x+,y-,y+,z-,z+]")
    elif not (_num(pad) and pad >= 0):
        errors.append("padding은 음이 아닌 수 또는 6-리스트")

    sel = cfg["solid_selection"]
    if sel != "all" and not (
            isinstance(sel, list) and sel
            and all(isinstance(i, int) and i >= 1 for i in sel)):
        errors.append('solid_selection은 "all" 또는 1-based 정수 리스트')

    if cfg["heal"] not in ("auto", "always", "never"):
        errors.append('heal은 auto|always|never (현재: {v})'.format(v=cfg["heal"]))
    if not (_num(cfg["heal_tolerance"]) and cfg["heal_tolerance"] > 0):
        errors.append("heal_tolerance는 양수")
    outp = cfg["outputs"]
    if outp["prefix"] is not None and (
            not isinstance(outp["prefix"], str) or not outp["prefix"]):
        errors.append("outputs.prefix는 null 또는 비어있지 않은 문자열")
    if outp["dir"] is not None and not isinstance(outp["dir"], str):
        errors.append("outputs.dir는 null 또는 문자열")
    if cfg["mesh"]["mode"] != "tetra":
        errors.append('mesh.mode는 v1에서 "tetra"만 지원 (hex_core는 Phase 5 예정)')
    if cfg["mesh"]["algorithm3d"] not in ("hxt", "delaunay", "frontal"):
        errors.append("mesh.algorithm3d는 hxt|delaunay|frontal")
    if cfg["outputs"]["volume_mesh"] not in ("msh", "vtk", "both", "none"):
        errors.append("outputs.volume_mesh는 msh|vtk|both|none")

    if not errors:
        # 경로 해석: input_step은 config 파일 위치 기준
        config_dir = os.path.dirname(os.path.abspath(config_path))
        step = cfg["input_step"]
        if not os.path.isabs(step):
            step = os.path.join(config_dir, step)
        cfg["input_step"] = os.path.normpath(step)
        if not os.path.exists(cfg["input_step"]):
            errors.append("STEP 파일이 없음: {p}".format(p=cfg["input_step"]))
        ext = os.path.splitext(cfg["input_step"])[1].lower()
        if ext not in (".stp", ".step"):
            errors.append("input_step 확장자는 .stp/.step (현재: {e})".format(e=ext))

        out = cfg["outputs"]
        if not out["prefix"]:
            out["prefix"] = os.path.splitext(os.path.basename(config_path))[0]
        out_dir = out["dir"] or os.getcwd()
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(os.getcwd(), out_dir)
        out["dir"] = os.path.normpath(out_dir)


def run_from_config(config_path):
    """AIRMESH 전체 실행. 모든 예외를 내부에서 잡는다 — KAM __main__으로 전파 금지."""
    t_start = time.time()
    report = {"status": "failed", "error": None, "airmesh_version": 1,
              "warnings": []}
    report_path = None
    try:
        cfg, errors, cfg_warnings = load_config(config_path)
        report["warnings"].extend(cfg_warnings)
        if errors:
            for w in cfg_warnings:
                print("[AIRMESH] 경고: {w}".format(w=w))
            for e in errors:
                print("[AIRMESH] config 오류: {e}".format(e=e))
            report["error"] = {"code": "E_CONFIG", "message": "; ".join(errors)}
            # config가 불완전해도 리포트는 best-effort로 남긴다 (cwd + config stem)
            stem = os.path.splitext(os.path.basename(config_path))[0]
            report_path = os.path.join(os.getcwd(), stem + "_report.json")
            print("AIRMESH FAILED : invalid config ({n} errors)".format(n=len(errors)))
            return
        report["config_echo"] = copy.deepcopy(cfg)
        report["units_label"] = cfg["units"]
        report_path = os.path.join(
            cfg["outputs"]["dir"], cfg["outputs"]["prefix"] + "_report.json")
        os.makedirs(cfg["outputs"]["dir"], exist_ok=True)

        print("[AIRMESH] 입력 STEP : {p}".format(p=cfg["input_step"]))
        print("[AIRMESH] mesh_size={h} ({u}), padding={pad}, 출력 ={d}".format(
            h=cfg["mesh_size"], u=cfg["units"], pad=cfg["padding"],
            d=cfg["outputs"]["dir"]))

        try:
            from KooAirMesh import AirMeshCore  # lazy: libgmsh CDLL 로드 지점
        except (ImportError, OSError) as e:
            # 모듈 부재(ImportError) / .so 로드 실패(OSError). 심볼 지연 실패(O10)는
            # run_pipeline 첫 호출에서 AirMeshError(E_GMSH_INIT)로 잡힌다.
            report["error"] = {"code": "E_GMSH_INIT",
                               "message": "gmsh/trimesh 로드 실패: {e}".format(e=e)}
            print("AIRMESH FAILED : gmsh 라이브러리 로드 실패 — 배포본에 libgmsh.so 포함 여부 확인 : {e}".format(e=e))
            return
        try:
            AirMeshCore.run_pipeline(cfg, report)
        except AirMeshCore.AirMeshError as e:
            report["error"] = {"code": e.code, "message": e.message}
            for w in report["warnings"]:
                print("[AIRMESH] 경고: {w}".format(w=w))
            print("AIRMESH FAILED : [{c}] {m}".format(c=e.code, m=e.message))
            return

        report["status"] = "ok"
        for w in report["warnings"]:
            print("[AIRMESH] 경고: {w}".format(w=w))
        print("[AIRMESH] 사면체 {n}개, minSICN {q:.3f}, 총 {t:.2f}초".format(
            n=report["mesh"]["n_tets"],
            q=report["mesh"]["quality"]["minSICN"]["min"],
            t=report["timings_s"]["total"]))
    except Exception as e:
        report["error"] = {"code": "E_UNEXPECTED", "message": repr(e)}
        print("AIRMESH FAILED : 예기치 못한 오류 : {e!r}".format(e=e))
    finally:
        report["elapsed_s"] = round(time.time() - t_start, 3)
        if report_path:
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                if report["status"] == "ok":
                    print("Complete AIRMESH : {p}".format(p=report_path))
                else:
                    print("[AIRMESH] 실패 리포트 기록 : {p}".format(p=report_path))
            except Exception as e:
                # 기계 계약은 이진이어야 한다 — 성공했어도 리포트가 없으면 FAILED로 알림
                if report["status"] == "ok":
                    print("AIRMESH FAILED : 리포트 기록 실패 (메시/STL 산출물은 생성됨) : {e!r}".format(e=e))
                else:
                    print("[AIRMESH] 리포트 기록 실패 : {e!r}".format(e=e))
