# 테스트 시나리오 폴더

각 테스트는 독립적인 시나리오로 실행 가능합니다.

## 테스트 목록

| ID | 이름 | 설명 | 케이스 수 | 예상 시간 |
|----|------|------|----------|----------|
| Test_001 | 전각도 26방향 1회 낙하 | 가장 기본적인 테스트 | 26 | 2시간 |

## 실행 방법

각 테스트 폴더로 이동 후:

```bash
cd Test_XXX/
bash run.sh
```

또는 수동으로:

```bash
cd Test_XXX/
python ../../CumulativeDesigner.py scenario.json runner_config.json
python ../../../Runner/LargeScaleDOEManager.py runner_config.json --nodes 2 --jobs-per-node 4 --ncpu-per-job 16
```

---

**작성일**: 2026-01-23
