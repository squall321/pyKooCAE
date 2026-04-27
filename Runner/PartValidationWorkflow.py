"""
PartValidationWorkflow — 파트별 낙하 검증 워크플로우

KooChainRun prepare/submit에서 part_validation 모드일 때 호출.

흐름:
    1. prepare: scenario.json → 원본 모델 로드 → 파트별 .k 분할 → runner_config.json + run.sh 생성
    2. submit: run.sh를 sbatch로 제출 (Slurm array job)
    3. collect: 결과 수집 → validation_report.json
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def prepare_part_validation(user_config, scenario_path, output_path):
    """part_validation scenario를 처리하여 파트별 .k + runner_config + run.sh 생성.

    Args:
        user_config: scenario.json dict
        scenario_path: scenario.json 경로 (Path)
        output_path: runner_config.json 경로 (Path)
    """
    scenario_dir = scenario_path.parent

    # 모델 파일 경로
    model_file = user_config.get("model_file", "")
    if not model_file:
        print("❌ Error: part_validation 모드에는 'model_file' 필드가 필요합니다.")
        sys.exit(1)
    if not os.path.isabs(model_file):
        model_file = str(scenario_dir / model_file)
    if not os.path.exists(model_file):
        print(f"❌ Error: 모델 파일을 찾을 수 없습니다: {model_file}")
        sys.exit(1)

    # 출력 디렉토리
    output_dir = user_config.get("output_dir", str(scenario_dir / "validation_output"))
    if not os.path.isabs(output_dir):
        output_dir = str(scenario_dir / output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 옵션
    sim_params = user_config.get("simulation_params", {})
    environment = user_config.get("environment", {})
    option = {
        "height": sim_params.get("height", 100.0),
        "tFinal": sim_params.get("tFinal", 0.0005),
        "dt": sim_params.get("dt", 0.00001),
        "except_pids": user_config.get("except_pids", []),
        "min_elements": user_config.get("min_elements", 1),
        "environment": environment,
    }

    print("=" * 80)
    print("KooChainRun - Part Validation (prepare)")
    print("=" * 80)
    print(f"  모델: {model_file}")
    print(f"  출력: {output_dir}")
    print(f"  높이: {option['height']}mm, tFinal: {option['tFinal']}s")
    print()

    # 1. step_config 생성 (KooMeshModifier용)
    print("1/3: step_config 생성 중...")
    step_config_path = os.path.join(output_dir, "step_config_validation.txt")
    _write_validation_step_config(step_config_path, model_file, output_dir, option)

    # 2. KooMeshModifier 실행 (subprocess)
    print("2/3: KooMeshModifier로 파트 분할 중...")
    from Runner.PathResolver import find_koomeshmodifier
    koomeshmodifier = environment.get("koomeshmodifier_path", find_koomeshmodifier())
    cmd = [koomeshmodifier, step_config_path]
    print(f"  실행: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"❌ KooMeshModifier 실행 실패 (exit={result.returncode})")
        print(result.stderr[-500:] if result.stderr else "")
        sys.exit(1)
    print(result.stdout[-500:] if result.stdout else "")

    # 3. manifest 읽기 + runner_config.json 생성
    print("3/3: runner_config.json 생성 중...")
    manifest_path = os.path.join(output_dir, "validation_manifest.json")
    if not os.path.exists(manifest_path):
        print(f"❌ Error: manifest 생성 실패: {manifest_path}")
        sys.exit(1)
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    total_parts = len(manifest.get("parts", {}))
    if total_parts == 0:
        print("⚠️ 분할할 파트가 없습니다.")
        return

    runner_config = _generate_runner_config(manifest, user_config, output_dir, environment)
    with open(str(output_path), 'w', encoding='utf-8') as f:
        json.dump(runner_config, f, indent=2, ensure_ascii=False)

    print()
    print(f"✅ Part Validation 준비 완료!")
    print(f"  파트 수: {total_parts}")
    print(f"  runner_config: {output_path}")
    print(f"  run.sh: {output_dir}/run.sh")
    print(f"  manifest: {output_dir}/validation_manifest.json")
    print()
    print(f"실행: sbatch {output_dir}/run.sh")
    print(f"  또는: KooChainRun submit {output_path} --mode doe")


def submit_part_validation(runner_config_path, args):
    """part_validation runner_config를 Slurm에 제출."""
    with open(runner_config_path, 'r', encoding='utf-8') as f:
        runner_config = json.load(f)

    if runner_config.get("mode") != "part_validation":
        print("❌ Error: part_validation 모드가 아닙니다.")
        return

    run_sh = runner_config.get("run_sh", "")
    if not run_sh or not os.path.exists(run_sh):
        print(f"❌ Error: run.sh를 찾을 수 없습니다: {run_sh}")
        return

    print("=" * 80)
    print("KooChainRun - Part Validation (submit)")
    print("=" * 80)
    print(f"  run.sh: {run_sh}")

    # sbatch 제출
    result = subprocess.run(["sbatch", run_sh], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {result.stdout.strip()}")
    else:
        print(f"❌ sbatch 실패: {result.stderr}")


def collect_part_validation(runner_config_path, output_report=None):
    """part_validation 결과 수집."""
    with open(runner_config_path, 'r', encoding='utf-8') as f:
        runner_config = json.load(f)

    output_dir = runner_config.get("output_dir", "")
    manifest_path = os.path.join(output_dir, "validation_manifest.json")

    if not os.path.exists(manifest_path):
        print(f"❌ Error: manifest를 찾을 수 없습니다: {manifest_path}")
        return

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    results = {}
    pass_count = 0
    fail_count = 0
    pending_count = 0

    for pid_str, pinfo in manifest["parts"].items():
        part_name = pinfo.get("name", f"Part_{pid_str}")
        basename = pinfo["file"].replace(".k", "")
        status_file = os.path.join(output_dir, "results", basename, "status.txt")

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = f.read().strip()
            if "PASS" in status:
                pass_count += 1
                results[pid_str] = {"name": part_name, "status": "PASS"}
            else:
                fail_count += 1
                results[pid_str] = {"name": part_name, "status": status}
        else:
            pending_count += 1
            results[pid_str] = {"name": part_name, "status": "PENDING"}

    total = len(manifest["parts"])

    print("=" * 80)
    print("KooChainRun - Part Validation (결과)")
    print("=" * 80)
    print(f"  전체: {total}, PASS: {pass_count}, FAIL: {fail_count}, PENDING: {pending_count}")
    print()

    if fail_count > 0:
        print("❌ 실패 파트:")
        for pid_str, r in results.items():
            if r["status"] != "PASS" and r["status"] != "PENDING":
                print(f"  PID {pid_str} ({r['name']}): {r['status']}")
        print()

    # 리포트 저장
    report = {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "pending": pending_count,
        "details": results,
    }
    if output_report is None:
        output_report = os.path.join(output_dir, "validation_report.json")
    with open(output_report, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  리포트: {output_report}")


def _generate_runner_config(manifest, user_config, output_dir, environment):
    """part_validation용 runner_config.json 생성."""
    return {
        "mode": "part_validation",
        "project_name": user_config.get("project_name", "PartValidation"),
        "output_dir": output_dir,
        "run_sh": os.path.join(output_dir, "run.sh"),
        "manifest": os.path.join(output_dir, "validation_manifest.json"),
        "total_parts": len(manifest["parts"]),
        "environment": environment,
        "simulation_params": user_config.get("simulation_params", {}),
    }


def _write_validation_step_config(step_config_path, model_file, output_dir, option):
    """KooMeshModifier용 PART_VALIDATION_SPLIT step_config 파일 작성."""
    height = option.get("height", 100.0)
    tFinal = option.get("tFinal", 0.0005)
    dt = option.get("dt", 0.00001)
    min_elements = option.get("min_elements", 1)
    except_pids = option.get("except_pids", [])

    lines = [
        "*Inputfile",
        model_file,
        "*Mode",
        "PART_VALIDATION_SPLIT,1",
        "**PartValidationSplit,1",
        f"*Height,{height}",
        f"*tFinal,{tFinal}",
        f"*Dt,{dt}",
        f"*OutputDir,{output_dir}",
        f"*MinElements,{min_elements}",
    ]
    if except_pids:
        lines.append("*ExceptPID," + ",".join(str(p) for p in except_pids))
    lines.append("**EndPartValidationSplit")
    lines.append("*End")

    with open(step_config_path, 'w') as f:
        f.write("\n".join(lines) + "\n")
