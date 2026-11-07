<!-- 충격 조건 DOE 결과를 원래 낙하 각도 구면 지도로 그려 달라는 Post(KooD3plotReader) 팀 요청 계약서 -->
# Post 요청 — 충격 조건 DOE 결과를 원래 낙하 각도 구면 지도로 (2026-11-07, pyKooCAE v132)

읽는 사람: KooD3plotReader(Post) 구면 보고서(koo_sphere_report) 담당 세션.

## 무엇이 바뀌나
지금 전각도 낙하는 낙하 각도마다 FEM 을 하나씩 돌린다. v132 는 두 번째 방식을 더한다.
1. 강체 사전 해석(PyBullet)으로 2만 방향을 돌린다.
2. 각 방향의 1차·2차 충돌 직전 상태(자세·무게중심 속도·각속도)를 모은다.
3. 그 가운데 대표 N 개(기본 100)만 FEM 으로 짧게 돌린다. 각 대표는 충돌 하나만 담는다(ENDTIM ≈ 1~2 ms).
   - 절반은 심각도 상위에서 고른다. 심각도 = 충격량 × 접근 속도이고, 서로 가까운 것은 건너뛴다.
   - 나머지 절반은 상태 공간을 고르게 덮도록 고른다.
4. 모든 (원래 각도, 반발계수 e, 충돌 차수 k)는 가장 가까운 대표 DOE 에 묶인다.
5. `KooChainRun harvest --impact-map` 이 대표 DOE 의 FEM 결과(파트별 최대 응력)를 원래 각도·충돌 차수별 표로 펼친다.

그래서 구면 지도의 점은 '그 각도를 직접 돌린 FEM' 이 아니라 **그 각도의 1·2차 충돌을 대표하는 DOE 의 FEM** 이다. 지도에 이 사실을 꼭 드러내 주세요.

## 넘겨주는 파일
| 파일 | 자리 | 내용 |
|---|---|---|
| `per_angle_risk_summary.csv` | `<test_dir>/` (harvest --impact-map 산출) | **원래 각도마다 한 줄** — 1·2차 충돌과 e 가운데 최대 |
| `per_angle_risk.csv` | `<test_dir>/` | (원래 각도, e, k)마다 한 줄 — 차수별 층을 그릴 때 |
| `index.json` | `<output_dir>/impact_conditions/` | 대표 조건과 배정 전체(메타데이터 정본) |

### per_angle_risk_summary.csv 칸
| 칸 | 뜻 |
|---|---|
| `angle` | 원래 낙하 각도 이름(P0001…P20000) |
| `roll,pitch,yaw` | KMM DROP_ATTITUDE 오일러 각(도) |
| `dx,dy,dz` | **물리 낙하 방향**(기기 좌표, 기기가 바닥으로 움직이는 방향) = Rz(−yaw)·Ry(−pitch)·Rx(−roll)·(0,0,−1) |
| `peak_stress` | 묶인 대표 DOE 들의 최대 응력 가운데 최대(결과 없으면 빈칸) |
| `worst_pid,worst_part` | 그 최대가 나온 파트 |
| `ratio` | peak/허용값(`--yield` 를 줄 때만) |
| `governing_e,governing_k,governing_doe` | 최대를 낸 반발계수·충돌 차수(1 또는 2)·DOE 번호 |
| `n_impacts,n_missing` | 이 각도에 묶인 (e, k) 수, 결과 없는 수 |

per_angle_risk.csv 는 위 각도 칸에 `e,k,doe,distance` 를 더해 (e, k)마다 한 줄이다. `distance` 는 그 충돌 상태와 대표 상태 사이의 거리다(특징 공간, 0 = 대표 자신). 클수록 추정이 거칠다.

### index.json (요약)
- `format = "impact_conditions/index v1"`
- `source{deck, impacts_csv, rigidbody_json, presim{...}}`
- `features{definition, L, selection{severity, severity_min_distance, ...}}`
- `conditions[{doe, name(IC001…), source{원래 각도·e·k·class·contact_type·vn_contact·v·w·att·J}, endtim, n_members, severity, severity_rank|"coverage", nearest_pick_distance}]`
- `assignments[{angle, roll, pitch, yaw, dx, dy, dz, e, k, doe, distance}]`

DOE 번호는 runner_config `scenario.doe_impact_meta` 와 simulation_index.json 의 alias(`_DOE###_`)로 Run 폴더에 이어진다.

## 방향 규약 — 주의
- 구면 보고서의 `_angle_vec`(v = (cosφcosλ, cosφsinλ, sinφ))은 lat/lon 매개 공간이다. 위 `dx,dy,dz` 는 **실제 낙하 방향**(KMM DropAttitude 규약)이다.
- 둘은 같은 각도에서 최대 153° 다를 수 있다(pyKooCAE 메모 project_drop_sampling_physical_frame).
- 이 표를 그릴 때는 `dx,dy,dz` 를 쓰거나, roll/pitch 에서 같은 규약으로 다시 계산해 주세요. 정본 식은 pyKooCAE `occProject/Generators/KooCAEManager/KooEndTimeTable.py` 의 `drop_direction` 이다.

## 요청
1. koo_sphere_report 에 이 표를 받는 입력을 더해 주세요(예: `--impact-map <per_angle_risk_summary.csv>`). 원래 각도(2만 점)마다 peak_stress(또는 ratio)를 구면에 칠한다.
2. 차수별 층(1차만·2차만·최대)을 고를 수 있으면 좋다. 원천은 per_angle_risk.csv 의 `k` 다.
3. 범례·도움말에 "대표 충격 조건 FEM 에서 펼친 추정값" 이라고 적고, 툴팁에 governing_doe·조건 이름(IC###)·distance 를 보여 주세요.
4. 빈칸(결과 없는 DOE)은 칠하지 말고 따로 센다.

## 아직 확인하지 못한 것
- LS-DYNA 라이선스가 만료돼 대표 DOE 를 실제 FEM 으로 돌려 보지 못했다. 강체 회전 초기조건(*INITIAL_VELOCITY_GENERATION)은 매뉴얼 근거와 카드 값 검사까지만 했다.
- harvest --impact-map 은 가짜 result.json 으로만 시험했다.

문의: pyKooCAE 쪽 kooomnidropanalyzer 세션. 계획 문서는 `docs/rigid_drop_endtime_20261107/PLAN.md` §7·§8 이다.
