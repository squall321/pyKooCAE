"""
DropWeightImpactWorkflow — 전위치 부분충격 시뮬레이션 워크플로우

KooChainRun prepare/submit에서 drop_weight_impact 모드일 때 호출.

흐름:
    1. prepare: scenario.json → 충격 위치 DOE 생성 → 파트별 step_config + run.sh
    2. submit: Slurm array job으로 전위치 병렬 실행
    3. collect: 결과 수집 + 충격 위치별 리포트
"""

import os
import sys
import json
import math
import subprocess
import numpy as np
from pathlib import Path


def prepare_drop_weight_impact(user_config, scenario_path, output_path):
    """drop_weight_impact scenario → step_config 생성 + run.sh.

    Args:
        user_config: scenario.json dict
        scenario_path: scenario.json 경로 (Path)
        output_path: runner_config.json 경로 (Path)
    """
    scenario_dir = scenario_path.parent

    model_file = user_config.get("model_file", "")
    if not model_file:
        print("❌ Error: 'model_file' 필드가 필요합니다.")
        sys.exit(1)
    if not os.path.isabs(model_file):
        model_file = str(scenario_dir / model_file)
    if not os.path.exists(model_file):
        print(f"❌ Error: 모델 파일 없음: {model_file}")
        sys.exit(1)

    output_dir = user_config.get("output_dir", str(scenario_dir / "dwi_output"))
    if not os.path.isabs(output_dir):
        output_dir = str(scenario_dir / output_dir)
    os.makedirs(output_dir, exist_ok=True)

    sim_params = user_config.get("simulation_params", {})
    environment = user_config.get("environment", {})

    print("=" * 80)
    print("KooChainRun - Drop Weight Impact (prepare)")
    print("=" * 80)
    print(f"  모델: {model_file}")
    print(f"  출력: {output_dir}")

    # 1. 충격 위치 DOE 생성 (모델 bbox 자동 계산)
    locations = sim_params.get("locations", {})
    loc_x, loc_y = _generate_impact_locations(locations, model_file=model_file)
    total_cases = len(loc_x)
    print(f"  충격 위치: {total_cases}개")

    # 2. 충격자 설정
    impactor = sim_params.get("impactor", {})
    tFinal = sim_params.get("tFinal", 0.001)
    dt = sim_params.get("dt", 0.000001)
    gen_mode = sim_params.get("generation_mode", "DampingSpring")
    boundary_dist = sim_params.get("boundary_distance", 0.0)

    # 3. step_config 파일들 생성
    print(f"\n  step_config 생성 중...")
    config_dir = os.path.join(output_dir, "configs")
    os.makedirs(config_dir, exist_ok=True)

    manifest = {
        "mode": "drop_weight_impact",
        "model_file": model_file,
        "output_dir": output_dir,
        "total_cases": total_cases,
        "cases": [],
    }

    for i in range(total_cases):
        config_name = f"dwi_{i+1:04d}.txt"
        config_path = os.path.join(config_dir, config_name)

        _write_dwi_step_config(
            config_path, model_file, output_dir,
            loc_x[i], loc_y[i], i + 1, total_cases,
            impactor, tFinal, dt, gen_mode, boundary_dist,
            sim_params
        )

        manifest["cases"].append({
            "index": i + 1,
            "config": config_name,
            "location_x": loc_x[i],
            "location_y": loc_y[i],
        })
        print(f"    [{i+1}/{total_cases}] x={loc_x[i]:.2f}, y={loc_y[i]:.2f}")

    # 4. manifest 저장
    manifest_path = os.path.join(output_dir, "dwi_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 5. run.sh 생성
    run_sh_path = os.path.join(output_dir, "run.sh")
    _generate_dwi_run_sh(run_sh_path, output_dir, config_dir, total_cases, environment)

    # 6. runner_config.json
    runner_config = {
        "mode": "drop_weight_impact",
        "project_name": user_config.get("project_name", "DWI"),
        "output_dir": output_dir,
        "run_sh": run_sh_path,
        "manifest": manifest_path,
        "total_cases": total_cases,
        "environment": environment,
    }
    with open(str(output_path), 'w', encoding='utf-8') as f:
        json.dump(runner_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Drop Weight Impact 준비 완료!")
    print(f"  케이스 수: {total_cases}")
    print(f"  runner_config: {output_path}")
    print(f"  run.sh: {run_sh_path}")
    print(f"  manifest: {manifest_path}")
    print(f"\n실행: sbatch {run_sh_path}")


def submit_drop_weight_impact(runner_config_path, args):
    """drop_weight_impact 제출."""
    with open(runner_config_path, 'r') as f:
        rc = json.load(f)

    run_sh = rc.get("run_sh", "")
    if not os.path.exists(run_sh):
        print(f"❌ Error: run.sh 없음: {run_sh}")
        return

    result = subprocess.run(["sbatch", run_sh], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {result.stdout.strip()}")
    else:
        print(f"❌ sbatch 실패: {result.stderr}")


def collect_drop_weight_impact(runner_config_path):
    """drop_weight_impact 결과 수집."""
    with open(runner_config_path, 'r') as f:
        rc = json.load(f)

    output_dir = rc.get("output_dir", "")
    manifest_path = rc.get("manifest", "")
    if not os.path.exists(manifest_path):
        print(f"❌ Error: manifest 없음")
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    pass_count = 0
    fail_count = 0
    pending_count = 0
    results = []

    for case in manifest["cases"]:
        idx = case["index"]
        case_dir = os.path.join(output_dir, "results", f"dwi_{idx:04d}")
        status_file = os.path.join(case_dir, "status.txt")

        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = f.read().strip()
            if "PASS" in status:
                pass_count += 1
            else:
                fail_count += 1
        else:
            status = "PENDING"
            pending_count += 1

        results.append({
            "index": idx,
            "x": case["location_x"],
            "y": case["location_y"],
            "status": status,
        })

    total = len(manifest["cases"])
    print("=" * 80)
    print("Drop Weight Impact 결과")
    print("=" * 80)
    print(f"  전체: {total}, PASS: {pass_count}, FAIL: {fail_count}, PENDING: {pending_count}")

    if fail_count > 0:
        print("\n❌ 실패 케이스:")
        for r in results:
            if "PASS" not in r["status"] and r["status"] != "PENDING":
                print(f"  #{r['index']} x={r['x']:.2f} y={r['y']:.2f}: {r['status']}")

    report_path = os.path.join(output_dir, "dwi_report.json")
    with open(report_path, 'w') as f:
        json.dump({"total": total, "pass": pass_count, "fail": fail_count,
                    "pending": pending_count, "details": results}, f, indent=2)
    print(f"  리포트: {report_path}")


def _parse_bbox_from_kfile(model_file):
    """모델 .k 파일에서 노드 좌표만 빠르게 읽어 바운딩 박스 반환.
    Returns: (xmin, xmax, ymin, ymax, zmin, zmax) 또는 None
    """
    xmin = ymin = zmin = float('inf')
    xmax = ymax = zmax = float('-inf')
    in_node = False
    count = 0

    with open(model_file, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line.startswith('*'):
                if line.upper().startswith('*NODE'):
                    in_node = True
                    continue
                elif in_node:
                    in_node = False
                continue
            if not in_node:
                continue
            # 고정 포맷 (8+16+16+16) 또는 자유 포맷
            try:
                if len(line) >= 56:
                    x = float(line[8:24])
                    y = float(line[24:40])
                    z = float(line[40:56])
                else:
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    else:
                        continue
                xmin = min(xmin, x); xmax = max(xmax, x)
                ymin = min(ymin, y); ymax = max(ymax, y)
                zmin = min(zmin, z); zmax = max(zmax, z)
                count += 1
            except (ValueError, IndexError):
                continue

    if count == 0:
        return None
    return (xmin, xmax, ymin, ymax, zmin, zmax)


def _generate_impact_locations(locations, model_file=None):
    """충격 위치 DOE 생성."""
    mode = locations.get("mode", "grid")

    # x_range / y_range 자동 계산 (없으면 모델 bbox 기반)
    x_range = locations.get("x_range", None)
    y_range = locations.get("y_range", None)
    margin = locations.get("margin", 0.9)

    if (x_range is None or y_range is None) and model_file:
        bbox = _parse_bbox_from_kfile(model_file)
        if bbox:
            cx = (bbox[0] + bbox[1]) / 2.0
            cy = (bbox[2] + bbox[3]) / 2.0
            half_x = (bbox[1] - bbox[0]) / 2.0 * margin
            half_y = (bbox[3] - bbox[2]) / 2.0 * margin
            if x_range is None:
                x_range = [cx - half_x, cx + half_x]
            if y_range is None:
                y_range = [cy - half_y, cy + half_y]
            print(f"    모델 bbox: X=[{bbox[0]:.1f},{bbox[1]:.1f}] Y=[{bbox[2]:.1f},{bbox[3]:.1f}] Z=[{bbox[4]:.1f},{bbox[5]:.1f}]")
            print(f"    충격 범위 (margin={margin}): X=[{x_range[0]:.1f},{x_range[1]:.1f}] Y=[{y_range[0]:.1f},{y_range[1]:.1f}]")

    if x_range is None:
        x_range = [-30, 30]
    if y_range is None:
        y_range = [-60, 60]

    if mode == "grid":
        x_count = locations.get("x_count", 7)
        y_count = locations.get("y_count", 13)
        # spacing으로도 지정 가능
        spacing = locations.get("spacing", 0)
        if spacing > 0:
            x_count = max(2, int((x_range[1] - x_range[0]) / spacing) + 1)
            y_count = max(2, int((y_range[1] - y_range[0]) / spacing) + 1)
            print(f"    spacing={spacing}mm → {x_count}x{y_count} = {x_count*y_count}개")

        x_vals = np.linspace(x_range[0], x_range[1], x_count)
        y_vals = np.linspace(y_range[0], y_range[1], y_count)
        loc_x, loc_y = [], []
        for x in x_vals:
            for y in y_vals:
                loc_x.append(float(x))
                loc_y.append(float(y))
        return loc_x, loc_y

    elif mode == "list":
        points = locations.get("points", [])
        loc_x = [p[0] for p in points]
        loc_y = [p[1] for p in points]
        return loc_x, loc_y

    elif mode == "lhs":
        n_samples = locations.get("n_samples", 50)
        try:
            from scipy.stats import qmc
            sampler = qmc.LatinHypercube(d=2)
            sample = sampler.random(n=n_samples)
        except ImportError:
            # scipy 없으면 random fallback
            sample = np.random.rand(n_samples, 2)
        loc_x = (sample[:, 0] * (x_range[1] - x_range[0]) + x_range[0]).tolist()
        loc_y = (sample[:, 1] * (y_range[1] - y_range[0]) + y_range[0]).tolist()
        return loc_x, loc_y

    else:
        print(f"⚠️ 알 수 없는 location mode: {mode}, 기본 (0,0)")
        return [0.0], [0.0]


def _write_dwi_step_config(config_path, model_file, output_dir,
                            loc_x, loc_y, index, total,
                            impactor, tFinal, dt, gen_mode, boundary_dist,
                            sim_params):
    """단일 충격 위치용 step_config 작성."""
    imp_type = impactor.get("type", "Sphere")
    imp_radius = impactor.get("radius", 5.0)
    imp_height = impactor.get("height", 100)
    imp_density = impactor.get("density", 7850)
    imp_E = impactor.get("youngs_modulus", 200e9)
    imp_nu = impactor.get("poisson_ratio", 0.3)

    # 속도 계산 (자유낙하)
    g = 9810.0  # mm/s^2
    vz = -math.sqrt(2.0 * g * imp_height)

    lines = [
        "*Inputfile",
        model_file,
        f"*RunDirectoryMode,True,{output_dir}/results/dwi_{index:04d}",
        f"*Info,DWI,Case{index:04d}",
        f"*Description,DWI Case{index}/{total} x={loc_x:.2f} y={loc_y:.2f}",
        "*Creator,automation,auto@system.com,CAE,AUTO",
        "*Mode",
        "DROP_WEIGHT_IMPACT_TEST,1",
        "**DropWeightImpactTest,1",
        f"TFinal,{tFinal}",
        f"DT,{dt}",
        f"LocationX,{loc_x}",
        f"LocationY,{loc_y}",
        f"Height,{imp_height}",
        f"InitialVelocityX,0",
        f"InitialVelocityY,0",
        f"InitialVelocityZ,{vz}",
        f"ImpactorType,{imp_type}",
    ]

    if imp_type.lower() == "sphere":
        lines.append(f"ImpactorDimension,{imp_radius}")
    elif imp_type.lower() == "cylinder":
        front_r = impactor.get("front_radius", imp_radius)
        outer_r = impactor.get("outer_radius", imp_radius * 2)
        front_h = impactor.get("front_height", imp_radius)
        back_h = impactor.get("back_height", imp_radius * 2)
        back_r = impactor.get("back_radius", outer_r)
        lines.append(f"ImpactorDimension,{front_r},{outer_r},{front_h},{back_h},{back_r}")

    lines.extend([
        f"DensityImpactor,{imp_density}",
        f"YoungsModulusImpactor,{imp_E}",
        f"PoissonRatioImpactor,{imp_nu}",
        f"GenerationMode,{gen_mode}",
    ])

    if boundary_dist > 0:
        lines.append(f"BoundaryDistance,{boundary_dist}")

    # 추가 옵션
    offset_dist = sim_params.get("offset_distance", 0.05)
    lines.append(f"OffsetDistance,{offset_dist}")

    # 바닥판 설정
    wall = sim_params.get("wall", {})
    wall_E = wall.get("youngs_modulus", 200e9)
    wall_nu = wall.get("poisson_ratio", 0.3)
    wall_density = wall.get("density", 7850)
    lines.extend([
        f"YoungsModulusWall,{wall_E}",
        f"PoissonRatioWall,{wall_nu}",
        f"DensityWall,{wall_density}",
    ])

    lines.append("**EndDropWeightImpactTest")
    lines.append("*End")

    with open(config_path, 'w') as f:
        f.write("\n".join(lines) + "\n")


def _generate_dwi_run_sh(run_sh_path, output_dir, config_dir, total_cases, environment):
    """Slurm array job용 run.sh."""
    env = environment
    ncpu = env.get("ncpu", 4)
    memory = env.get("memory", "4G")
    partition = env.get("partition", "normal")
    sif_path = env.get("sif_path", "")
    koomeshmodifier = env.get("koomeshmodifier_path", "/data/SmartTwinPreprocessor/bin/KooMeshModifier")
    solver_cmd = env.get("solver_command", "ls-dyna")

    script = f"""#!/bin/bash
#SBATCH --job-name=DWI
#SBATCH --array=1-{total_cases}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={ncpu}
#SBATCH --mem={memory}
#SBATCH --partition={partition}
#SBATCH --output={output_dir}/logs/slurm_%A_%a.out
#SBATCH --error={output_dir}/logs/slurm_%A_%a.err

mkdir -p {output_dir}/logs
mkdir -p {output_dir}/results

# step_config 파일 찾기
CONFIG_FILES=($(ls {config_dir}/dwi_*.txt | sort))
IDX=$((SLURM_ARRAY_TASK_ID - 1))
CONFIG=${{CONFIG_FILES[$IDX]}}
BASENAME=$(basename "$CONFIG" .txt)

echo "=== DWI: $BASENAME ==="
echo "  Config: $CONFIG"

# 1. KooMeshModifier로 .k 파일 생성
WORKDIR={output_dir}/results/$BASENAME
mkdir -p $WORKDIR

{koomeshmodifier} $CONFIG
if [ $? -ne 0 ]; then
    echo "FAIL (KooMeshModifier)" > $WORKDIR/status.txt
    exit 1
fi

# 2. 생성된 .k 파일 찾기 + LS-DYNA 실행
KFILE=$(ls $WORKDIR/*.k 2>/dev/null | head -1)
if [ -z "$KFILE" ]; then
    echo "FAIL (no .k file)" > $WORKDIR/status.txt
    exit 1
fi

cd $WORKDIR
"""

    if sif_path:
        script += f"""apptainer exec {sif_path} {solver_cmd} i=$(basename $KFILE) ncpu={ncpu} memory={memory}
"""
    else:
        script += f"""{solver_cmd} i=$(basename $KFILE) ncpu={ncpu} memory={memory}
"""

    script += f"""
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "PASS" > $WORKDIR/status.txt
else
    echo "FAIL (exit=$EXIT_CODE)" > $WORKDIR/status.txt
fi

echo "=== Done: $BASENAME (exit=$EXIT_CODE) ==="
"""

    with open(run_sh_path, 'w') as f:
        f.write(script)
    os.chmod(run_sh_path, 0o755)
