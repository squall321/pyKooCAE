#!/bin/bash
# Direct Input Workflow 테스트 스크립트
# 사용법: ./test_direct_input.sh

set -e

echo "=================================================="
echo "Direct Input Workflow 테스트"
echo "=================================================="

# 1. 테스트 입력 파일 준비
echo ""
echo "Step 1: 테스트 입력 파일 생성..."
mkdir -p test_inputs

cat > test_inputs/step1.k << 'EOF'
*KEYWORD
*TITLE
Test Input File - Step 1
$# Custom mesh for drop simulation
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
3, 1.0, 1.0, 0.0
4, 0.0, 1.0, 0.0
*ELEMENT_SHELL
1, 1, 1, 2, 3, 4
*END
EOF

cat > test_inputs/step2.k << 'EOF'
*KEYWORD
*TITLE
Test Input File - Step 2
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
3, 1.0, 1.0, 0.0
4, 0.0, 1.0, 0.0
*ELEMENT_SHELL
1, 1, 1, 2, 3, 4
*END
EOF

cat > test_inputs/step3.k << 'EOF'
*KEYWORD
*TITLE
Test Input File - Step 3
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
3, 1.0, 1.0, 0.0
4, 0.0, 1.0, 0.0
*ELEMENT_SHELL
1, 1, 1, 2, 3, 4
*END
EOF

echo "✅ 테스트 입력 파일 생성 완료"

# 2. 설정 파일 생성
echo ""
echo "Step 2: 설정 파일 생성..."

cat > direct_input_test_config.json << EOF
{
  "project_name": "DirectInput_Test",
  "job_name": "Test_CustomMesh",
  "num_steps": 3,
  "input_files": [
    "$(pwd)/test_inputs/step1.k",
    "$(pwd)/test_inputs/step2.k",
    "$(pwd)/test_inputs/step3.k"
  ],
  "use_koomesh": true,
  "use_lsdyna": true,
  "koomesh_params": {
    "template": "DROP_FIRST",
    "result_dir": "./"
  },
  "lsdyna_params": {
    "memory": 60000
  },
  "step_resources": {
    "1": {
      "nnodes": 2,
      "ncpus_per_node": 32,
      "memory_per_node": "64G",
      "walltime": "02:00:00",
      "partition": "normal"
    },
    "2": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "memory_per_node": "128G",
      "walltime": "04:00:00",
      "partition": "normal"
    },
    "3": {
      "nnodes": 4,
      "ncpus_per_node": 32,
      "memory_per_node": "128G",
      "walltime": "06:00:00",
      "partition": "normal"
    }
  }
}
EOF

echo "✅ 설정 파일 생성 완료: direct_input_test_config.json"

# 3. Dry-run 테스트
echo ""
echo "Step 3: Dry-run 테스트..."
python3 ../../Runner/DirectInputWorkflow.py \
    direct_input_test_config.json \
    --dry-run

echo ""
echo "=================================================="
echo "✅ 테스트 완료!"
echo "=================================================="
echo ""
echo "실제 제출하려면:"
echo "  python3 ../../Runner/DirectInputWorkflow.py direct_input_test_config.json"
echo ""
echo "모니터링 포함:"
echo "  python3 ../../Runner/DirectInputWorkflow.py direct_input_test_config.json --monitor"
echo ""
