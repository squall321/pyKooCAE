# Apptainer Integration Guide

**작성일**: 2026-01-23
**버전**: 1.0

---

## 개요

KooChainRun은 **Apptainer 컨테이너**를 통해 KooMeshModifier와 LS-DYNA를 실행할 수 있습니다.

### 시스템 구조

```
헤드 노드 (Job 제출)
    ↓
Slurm 스케줄러
    ↓
컴퓨트 노드들
    ├── /path/to/koomesh.sif (KooMeshModifier 컨테이너)
    ├── /path/to/lsdyna.sif (LS-DYNA 컨테이너, 선택사항)
    └── /data (공유 스토리지)
```

---

## 설정 방법

### 1. **scenario.json에 Apptainer 경로 추가**

```json
{
  "project_name": "MyProject",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna",

    "apptainer_sif": "/shared/containers/koomesh.sif",
    "apptainer_bind": "/data:/data,/scratch:/scratch",

    "lsdyna_apptainer_sif": "/shared/containers/lsdyna.sif",
    "lsdyna_apptainer_bind": "/data:/data"
  },
  "scenarios": [...]
}
```

### 2. **설정 항목 설명**

| 항목 | 필수 | 설명 | 기본값 |
|------|------|------|--------|
| `apptainer_sif` | ❌ | KooMeshModifier용 SIF 파일 경로 | `None` (직접 실행) |
| `apptainer_bind` | ❌ | KooMeshModifier용 바인드 마운트 | `/data:/data` |
| `lsdyna_apptainer_sif` | ❌ | LS-DYNA용 SIF 파일 경로 | `None` (직접 실행) |
| `lsdyna_apptainer_bind` | ❌ | LS-DYNA용 바인드 마운트 | `/data:/data` |

### 3. **Apptainer 없이 실행**

Apptainer 설정을 생략하면 **직접 실행**됩니다:

```json
{
  "project_name": "MyProject",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna"
  },
  "scenarios": [...]
}
```

생성되는 Slurm 스크립트:
```bash
# 직접 실행
/opt/KooMeshModifier/run.sh --input=input.txt
mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k
```

---

## 생성되는 Slurm 스크립트

### **Apptainer 사용 시**

```bash
#!/bin/bash
#SBATCH --job-name=MyProject
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16

# KooMeshModifier 실행 (Apptainer)
apptainer exec --bind /data:/data /shared/containers/koomesh.sif \
    /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA 실행 (Apptainer)
apptainer exec --bind /data:/data /shared/containers/lsdyna.sif \
    mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k memory=60000m ncpu=16
```

### **Apptainer 미사용 시**

```bash
#!/bin/bash
#SBATCH --job-name=MyProject
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16

# KooMeshModifier 실행 (직접)
/opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA 실행 (직접)
mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k memory=60000m ncpu=16
```

---

## 사용 시나리오

### **시나리오 1: KooMeshModifier만 Apptainer**

```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna",
    "apptainer_sif": "/shared/containers/koomesh.sif"
  }
}
```

결과:
```bash
# KooMeshModifier: Apptainer로 실행
apptainer exec --bind /data:/data /shared/containers/koomesh.sif \
    /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA: 직접 실행
mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k
```

### **시나리오 2: 둘 다 Apptainer**

```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna",
    "apptainer_sif": "/shared/containers/koomesh.sif",
    "lsdyna_apptainer_sif": "/shared/containers/lsdyna.sif"
  }
}
```

결과:
```bash
# KooMeshModifier: koomesh.sif
apptainer exec --bind /data:/data /shared/containers/koomesh.sif \
    /opt/KooMeshModifier/run.sh --input=input.txt

# LS-DYNA: lsdyna.sif
apptainer exec --bind /data:/data /shared/containers/lsdyna.sif \
    mpirun -np 16 /opt/lsdyna/bin/ls-dyna i=input.k
```

### **시나리오 3: 같은 Apptainer 사용**

KooMeshModifier와 LS-DYNA가 같은 컨테이너에 있는 경우:

```json
{
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna",
    "apptainer_sif": "/shared/containers/all-in-one.sif",
    "lsdyna_apptainer_sif": "/shared/containers/all-in-one.sif"
  }
}
```

---

## 바인드 마운트 설정

### **단일 경로**

```json
{
  "environment": {
    "apptainer_bind": "/data:/data"
  }
}
```

### **여러 경로**

```json
{
  "environment": {
    "apptainer_bind": "/data:/data,/scratch:/scratch,/home:/home"
  }
}
```

### **읽기 전용 마운트**

```json
{
  "environment": {
    "apptainer_bind": "/data:/data:ro,/scratch:/scratch"
  }
}
```

---

## 실전 예제

### **예제 1: 기본 설정 (HPC 클러스터)**

```json
{
  "project_name": "DropTest_Production",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna",
    "apptainer_sif": "/shared/apptainers/koomesh_v1.0.sif",
    "apptainer_bind": "/data:/data",
    "lsdyna_apptainer_sif": "/shared/apptainers/lsdyna_R14.sif",
    "lsdyna_apptainer_bind": "/data:/data"
  },
  "scenarios": [...]
}
```

### **예제 2: 개발 환경 (Apptainer 없이)**

```json
{
  "project_name": "DropTest_Dev",
  "environment": {
    "koomeshmodifier_path": "/opt/KooMeshModifier/run.sh",
    "lsdyna_path": "/opt/lsdyna/bin/ls-dyna"
  },
  "scenarios": [...]
}
```

---

## 문제 해결

### **문제 1: SIF 파일을 찾을 수 없음**

```
ERROR: container not found: /shared/containers/koomesh.sif
```

**해결**:
1. SIF 파일 경로 확인:
   ```bash
   ls -l /shared/containers/koomesh.sif
   ```
2. 모든 컴퓨트 노드에서 접근 가능한지 확인
3. 경로를 절대 경로로 지정

### **문제 2: 바인드 마운트 실패**

```
FATAL: container creation failed: mount /data->/data error
```

**해결**:
1. 디렉토리 존재 여부 확인:
   ```bash
   ls -ld /data
   ```
2. 권한 확인:
   ```bash
   ls -ld /data
   ```
3. 바인드 경로 수정

### **문제 3: MPI 오류**

```
mpirun: command not found
```

**해결**:
- MPI가 컨테이너 내부 또는 외부에 설치되어 있어야 함
- Apptainer에서 MPI 사용 시 호스트 MPI와 컨테이너 MPI 버전 일치 필요

---

## 성능 고려사항

### **Apptainer Overhead**

| 항목 | 직접 실행 | Apptainer 실행 | 오버헤드 |
|------|----------|----------------|----------|
| 시작 시간 | ~0.1초 | ~0.5초 | +0.4초 |
| 실행 시간 | 기준 | 기준 + 1% | ~1% |
| 메모리 | 기준 | 기준 + 100MB | +100MB |

**결론**: 긴 시뮬레이션(수 시간)에서는 오버헤드 무시 가능

### **최적화 팁**

1. **SIF 파일 위치**: 빠른 스토리지에 배치 (NFS보다 로컬 or 병렬 FS)
2. **바인드 마운트 최소화**: 필요한 경로만 마운트
3. **캐시 활용**: `APPTAINER_CACHEDIR` 설정

---

## 추가 자료

- [Apptainer 공식 문서](https://apptainer.org/docs/)
- [KooMeshModifier 매뉴얼](../../../docs/KooMeshModifier.md)
- [LS-DYNA 매뉴얼](https://www.lstc.com/manuals)

---

**작성자**: Koo Engineering
**최종 수정**: 2026-01-23
