# KooChainRun (koocr)

**Sequential CAE Analysis Workflow Manager**

KooChainRun is a command-line tool for managing multi-step chained CAE simulations with automatic Slurm job submission and dependency management.

---

## Features

- ✅ **Simple CLI**: Single command interface for complex workflows
- ✅ **Automatic Slurm Integration**: Array jobs with dependency chains
- ✅ **HPC Resource Management**: Explicit node, job, and CPU allocation
- ✅ **Multi-Step Chaining**: Automatic dynain → Initial.k → next step
- ✅ **Progress Monitoring**: Track completion across thousands of cases
- ✅ **Result Collection**: Automated gathering of completed simulations

---

## Installation

### Option 1: Direct Execution

```bash
# Make koocr executable
chmod +x /path/to/pyKooCAE/koocr

# Add to PATH (optional)
export PATH="/path/to/pyKooCAE:$PATH"

# Or create symlink
ln -s /path/to/pyKooCAE/koocr /usr/local/bin/koocr
```

### Option 2: Apptainer Integration

```bash
# In Apptainer definition file
%post
    ln -s /opt/pyKooCAE/koocr /usr/local/bin/koocr
    chmod +x /opt/pyKooCAE/koocr

# Usage
apptainer exec koomesh.sif koocr prepare scenario.json
```

---

## Quick Start

### 1. Prepare Configuration

Convert user-friendly `scenario.json` to detailed `runner_config.json`:

```bash
koocr prepare scenario.json
```

Or specify output path:

```bash
koocr prepare scenario.json -o custom_config.json
```

### 2. Submit Jobs

Submit to Slurm with resource allocation:

```bash
koocr submit runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16
```

This will:
- Create all runid directories
- Generate metadata.json for each case
- Submit Slurm array jobs with dependencies
- Set up automatic step chaining

### 3. Monitor Progress

Check execution status:

```bash
koocr status

# Or with specific config
koocr status runner_config.json
```

### 4. Collect Results

Gather completed results:

```bash
koocr collect runner_config.json results/
```

---

## CLI Commands

### `koocr prepare`

**Purpose**: Generate runner configuration from scenario

**Usage**:
```bash
koocr prepare <scenario.json> [-o OUTPUT]
```

**Arguments**:
- `scenario`: Path to scenario.json file
- `-o, --output`: Output path for runner_config.json (optional)

**Example**:
```bash
koocr prepare Examples/HWWarrantyDropTest/Tests/Test_001/scenario.json
```

---

### `koocr submit`

**Purpose**: Submit jobs to Slurm cluster

**Usage**:
```bash
koocr submit <runner_config.json> [OPTIONS]
```

**Options**:
- `--nodes N`: Number of nodes to use (default: 2)
- `--jobs-per-node N`: Jobs per node (default: 4)
- `--ncpu-per-job N`: CPUs per job (default: 16)
- `--data-root PATH`: Execution root directory (default: /data)

**Example**:
```bash
koocr submit runner_config.json --nodes 10 --jobs-per-node 4 --ncpu-per-job 16
```

**Resource Calculation**:
```
Total concurrent jobs = nodes × jobs-per-node
Example: 10 nodes × 4 jobs/node = 40 concurrent jobs

CPU usage per node = jobs-per-node × ncpu-per-job
Example: 4 jobs × 16 CPUs = 64 CPUs per node (50% of 128-core node)
```

---

### `koocr status`

**Purpose**: Check execution status

**Usage**:
```bash
koocr status [runner_config.json]
```

**Example**:
```bash
koocr status
koocr status runner_config.json --watch
```

Shows:
- Slurm queue status
- Running jobs
- Completed cases

---

### `koocr collect`

**Purpose**: Collect simulation results

**Usage**:
```bash
koocr collect <runner_config.json> [OUTPUT_DIR]
```

**Arguments**:
- `config`: Path to runner_config.json
- `output_dir`: Output directory (default: ./results)

**Example**:
```bash
koocr collect runner_config.json results/
```

---

## Complete Workflow Example

```bash
#!/bin/bash
# Complete drop test workflow

# 1. Prepare configuration
koocr prepare drop_scenario.json

# 2. Submit with 10 nodes, 4 jobs per node, 16 CPUs each
# Total: 40 concurrent jobs, 64 CPUs per node
koocr submit runner_config.json \
    --nodes 10 \
    --jobs-per-node 4 \
    --ncpu-per-job 16

# 3. Monitor progress
koocr status runner_config.json

# 4. After completion, collect results
koocr collect runner_config.json results/

# 5. Analyze results
ls results/
```

---

## Scenario.json Format

```json
{
  "project_name": "MyDropTest",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna"
  },
  "scenarios": [
    {
      "scenario_name": "Full_26_Directions",
      "angle_source": {
        "source_type": "cuboid_geometry",
        "cuboid_geometry": {
          "include_faces": true,
          "include_edges": true,
          "include_corners": true
        }
      },
      "cumulative": {
        "num_steps": 3,
        "mode_sequence": ["DROP", "DROP", "DROP"],
        "base_angle_index": 0,
        "angle_mixing": {
          "strategy": "same_angle"
        }
      }
    }
  ]
}
```

---

## Advanced Usage

### Custom Slurm Concurrency

Control maximum concurrent jobs with `--jobs-per-node`:

```bash
# Conservative: 20 concurrent jobs (10 nodes × 2 jobs)
koocr submit config.json --nodes 10 --jobs-per-node 2

# Balanced: 40 concurrent jobs (10 nodes × 4 jobs)
koocr submit config.json --nodes 10 --jobs-per-node 4

# Aggressive: 80 concurrent jobs (10 nodes × 8 jobs)
koocr submit config.json --nodes 10 --jobs-per-node 8
```

### Multi-Step Chaining

KooChainRun automatically handles:

1. **Step 1**: KooMeshModifier (rotate) → LS-DYNA → dynain
2. **Step 2**:
   - DYNAIN_TO_INITIAL (dynain → Initial.k)
   - KooMeshModifier (rotate Initial.k)
   - LS-DYNA → new dynain
3. **Step 3+**: Repeat Step 2 process

All steps are submitted with Slurm dependencies:
```bash
#SBATCH --dependency=afterok:$PREV_JOB_ID
```

---

## Troubleshooting

### koocr: command not found

```bash
# Check if koocr is executable
ls -l /path/to/pyKooCAE/koocr

# Make executable
chmod +x /path/to/pyKooCAE/koocr

# Add to PATH
export PATH="/path/to/pyKooCAE:$PATH"
```

### Import errors

```bash
# Ensure Python can find Runner modules
export PYTHONPATH="/path/to/pyKooCAE:$PYTHONPATH"
```

### Slurm job failures

```bash
# Check Slurm logs
koocr status
squeue -u $USER

# Check job output
cat RUNDIR/runid_00001/Step001/slurm-*.out

# Check lock files
find RUNDIR -name "*.lock" | wc -l
```

---

## Integration with Existing Code

KooChainRun is a wrapper around existing modules:

| KooChainRun Command | Underlying Module |
|---------------------|-------------------|
| `koocr prepare` | `Runner/CumulativeDesigner.py` |
| `koocr submit` | `Runner/LargeScaleDOEManager.py` |
| `koocr status` | (New implementation) |
| `koocr collect` | `Runner/LargeScaleDOEManager.collect_results()` |

Old scripts still work:
```bash
# Old way (still supported)
python3 Runner/CumulativeDesigner.py scenario.json runner_config.json
python3 Runner/LargeScaleDOEManager.py runner_config.json --nodes 2

# New way (recommended)
koocr prepare scenario.json
koocr submit runner_config.json --nodes 2
```

---

## Version History

### v1.0.0 (2026-01-23)
- Initial release
- CLI commands: prepare, submit, status, collect
- Automatic Slurm integration
- Multi-step chaining support

---

## License

Copyright © 2026 Koo Engineering. All rights reserved.

---

## Support

- Documentation: `/opt/pyKooCAE/Examples/HWWarrantyDropTest/README.md`
- Issues: Contact Koo Engineering
- Examples: `/opt/pyKooCAE/Examples/`
