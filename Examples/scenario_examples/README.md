# scenario_examples

KooChainRun scenario.json 예제 모음 — 3 mode 각 1건씩, 2026-06 fix 후 검증된 단위계/키 이름 일관.

## 파일

| 예제 | mode | 시나리오 |
|------|------|----------|
| `drop_attitude_example.json` | DROP | Fibonacci 10 방향 낙하 |
| `impact_example.json` | IMPACT | 3x3 그리드 부분 충격 |
| `vibration_example.json` | VIBRATION | 회로 3그룹 일괄 가진 (C1/C2/C3 SF 차등) |

## 단위계 (필수 일관 유지)

모든 예제는 **LS-DYNA 표준 ton-mm-s 단위계** 사용.

| 양 | 단위 |
|----|------|
| 길이 | mm |
| 시간 | s |
| 질량 | tonne |
| 밀도 (ρ) | tonne/mm³ |
| 응력/탄성계수 (E) | MPa |
| 힘 | N (=tonne·mm/s²) |
| 중력 | g = 9810 mm/s² |

**강철 ref**: ρ=7.85e-9 tonne/mm³, E=2.0e5 MPa (200 GPa).
**Wall ref**: ρ=1.0e-9 tonne/mm³, E=1.0e4 MPa.

**주의**: `scenario.json`의 density/youngs_modulus는 **변환 없이** 그대로 deck에 박힘.
사용자가 SI (kg/m³, Pa) 입력하면 deck도 SI 숫자로 박혀 단위 혼용 → 비현실적 결과.

## 사용 방법

```bash
# 1. base_dir 경로 본인 환경에 맞게 수정
vim Examples/scenario_examples/<mode>_example.json
#    (base_dir, template, lsdyna_apptainer_env.LSTC_LICENSE_SERVER 등)

# 2. base_dir 디렉토리 + MinimumModel.k template 복사
mkdir -p /data/koopark/Example_<mode>
cp <your_model>.k /data/koopark/Example_<mode>/MinimumModel.k

# 3. prepare + submit
/data/SmartTwinPreprocessor/bin/KooChainRun prepare \
    Examples/scenario_examples/<mode>_example.json
/data/SmartTwinPreprocessor/bin/KooChainRun submit \
    /data/koopark/Example_<mode>/runner_config.json

# 4. 큐 모니터
squeue -u $USER
# 잡 완료 후
ls /data/koopark/Example_<mode>/output/Run_*/Output/
```

## 검증 포인트

### DROP_ATTITUDE
- deck `DropSet.k` 안 `*MAT_ELASTIC RigidWall` 카드의 ρ/E가 scenario.json `simulation_params.density`/`youngs_modulus` 입력값 그대로 박혔는지 확인 (drop_surface.type=Plane 시).
- d3hsp "Normal termination" 확인.

### IMPACT
- deck `DropWeightImpactTestSet.k` 안:
  - `*MAT_ELASTIC ImpactorMaterial` ρ/E = `simulation_params.impact.density`/`youngs_modulus`
  - `*MAT_RIGID WallMaterial` ρ/E = `simulation_params.wall.density`/`youngs_modulus`
- 둘 다 일치 안 하면 P0/Wall fix 미적용 (구 KooChainRun 빌드).

### VIBRATION
- deck `VibrationSet.k` 안 `*LOAD_BODY_GENERALIZED_SET_PART` 카드 (정식 LS-DYNA 키워드, Vol I 33-31).
- `_PARTS_<dir>` 이라는 비정식 키워드가 보이면 옛 빌드.
- 회로별 SF 차등 (C1/C2/C3 다른 amplitude) → deck의 AZ 필드가 각 회로별로 다른 값.

## 변경 이력 (2026-06 fix)

| Fix | 영향 mode |
|-----|----------|
| P0 — CumulativeScenarioRunner IMPACT 분기 `DensityImpactor`/etc 키 이름 일치 | IMPACT |
| P1b — DropWeightImpactWorkflow default 단위계 ton-mm-s | IMPACT (non-cumulative 흐름) |
| P1c — StepConfigBuilder DROP_ATTITUDE default 단위계 ton-mm-s | DROP |
| Wall fix — CumulativeScenarioRunner IMPACT 분기 `DensityWall`/etc 라인 추가 | IMPACT |
| Vibration Sender/Receiver/Emit fix | VIBRATION |

자세한 사유는 commit log + `docs/vibration_massive/` 참조.
