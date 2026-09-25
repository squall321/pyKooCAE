# 방향별 deep_report 샘플 (full 변형)

`Run_20260522_094238_01adb3` 한 방향의 렌더·단면뷰 포함 산출물에서 경량 파일만 뽑았다.
`--sv-threads 12` 로 34분 21초, 최대 RSS 33.2 GiB, 전체 403 MB.

| 파일 | 내용 |
|---|---|
| `report.html` | 방향별 리포트 본문 |
| `result.json` | 요약 지표 |
| `contact_metrics.json` | 파트쌍 접촉력 계측 |
| `energy_flow_edges.csv` | 에너지 흐름 그래프 간선 |

🔴 `report.html` 은 단면뷰 영상을 `renders/section_view_*/section_view.mp4` 상대경로로 참조한다.
영상 25개 217 MB 는 동봉하지 않았으므로 **단면뷰 패널이 비어 보인다.** 영상까지 보려면 원본 경로에서 열 것.
`/data/koopark/Test_Postprocess_v14/output/Run_20260522_094238_01adb3/Output/report/report.html`

## 두 변형의 수치가 완전히 같지는 않다

같은 방향(`9f4583`)을 두 변형으로 돌려 비교한 결과.

| 파일 | 결과 |
|---|---|
| `contact_metrics.json` | 바이트 동일 |
| `energy_flow_edges.csv` | 바이트 동일 |
| `result.json` | **파트 1개만 다름** (23개 중 PID 14 `PKG\PKG 2`) |
| `analysis_result.json` | 다름 |

다른 항목은 응력·변형률 피크뿐이다. 변위·가속도 피크는 일치한다.

```
peak_stress          18.64575598  vs  19.04540767   (2.1%)
time_of_peak_stress  0.001353408  vs  0.001352394   (다른 상태를 골랐다)
peak_strain          1.244992e-05 vs  1.264130e-05
```

원인은 확정됐다 — 변형 차이가 아니라 **light 쪽에 걸었던 `ulimit -v` 40 GB** 다.
60 GB 로 다시 돌리면 두 변형이 일치한다. 자세한 것은 [../../RESOURCES.md](../../RESOURCES.md) 의
재현성 절을 볼 것. 🔴 `ulimit -v` 를 실측 요구량 근처에 두면 후처리가 **경고 없이** 피크를
낮게 보고한다.
