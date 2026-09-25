# 방향별 deep_report 샘플 (light 변형)

`Run_20260522_094055_9f4583` 한 방향의 `--no-render` 산출물에서 경량 파일만 뽑았다.

| 파일 | 내용 |
|---|---|
| `report.html` | 방향별 리포트 본문. 렌더 영상이 없으니 그대로 열면 된다 |
| `result.json` | 요약 지표 (94 KB) |
| `contact_metrics.json` | 파트쌍 접촉력 계측 (뉴턴 3법칙 검산 포함) |
| `energy_flow_edges.csv` | 에너지 흐름 그래프 간선 |

동봉하지 않은 것.
- `analysis_result.json` — 96 MB. 집계 리포트의 실제 입력이지만 용량 때문에 제외
- `motion/` `stress/` `strain/` `surface/` — 합계 약 70 MB
- full 변형의 `renders/section_view_*/section_view.mp4` — 25개 217 MB

전체는 원본 경로에 있다.
`/data/koopark/Test_Postprocess_v14/output/Run_20260522_094055_9f4583/Output/{report,report_norender}/`
