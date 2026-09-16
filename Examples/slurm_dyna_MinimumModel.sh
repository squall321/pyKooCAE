#!/bin/bash
#SBATCH --job-name=dyna_MinimumModel
#SBATCH --partition=normal
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=1
#SBATCH --time=168:00:00

#SBATCH --output=/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/dyna_MinimumModel_%j.out
#SBATCH --error=/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/dyna_MinimumModel_%j.err
#SBATCH --chdir=/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples

echo "=========================================="
echo "LS-DYNA Job Start"
echo "=========================================="
echo "입력 파일: MinimumModel.k"
echo "작업 디렉토리: /home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples"
echo "SIF 버전: aocc420_mpp_s"
echo "SIF 파일: /home/koopark/serviceApptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif"
echo "CPU: 2"
echo "LS-DYNA 메모리: 500m"
echo "파티션: normal"
echo "노드: $(hostname)"
date
echo ""

export APPTAINER_TMPDIR=/data/tmp
mkdir -p $APPTAINER_TMPDIR

apptainer exec \
    --bind /data:/data \
    --env LSTC_FILE=/opt/ls-dyna_license/LSTC_FILE \
    --env LSTC_LICENSE_SERVER=192.168.122.1 \
    --env FI_PROVIDER=tcp \
    --env I_MPI_FABRICS=ofi \
    --env LD_LIBRARY_PATH=/opt/openmpi/lib \
    /home/koopark/serviceApptainers/LSDynaBasic_aocc420_ompi4.0.5_mpp_s.sif \
    mpirun -np 2 /opt/ls-dyna/lsdyna_R16.1.1 i=MinimumModel.k memory=500m

echo ""
echo "=========================================="
echo "LS-DYNA Job End"
echo "=========================================="
date
