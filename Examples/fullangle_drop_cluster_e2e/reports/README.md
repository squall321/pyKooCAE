# 생성된 리포트

2026-05-22 에 완주한 20방향 낙하 해석을, 2026-09-25 에 현재 배포본
(`SmartTwinPostprocessor.sif`, 2026-09-18 판)으로 후처리해 만든 것이다.

| 파일 | 내용 | 크기 |
|---|---|---|
| `sphere_report.html` | 전각도 집계 리포트. 탭 16개 | 7.8 MB |
| `sphere_report.json.gz` | 같은 리포트의 기계 판독형 (gzip) | 2.2 MB |
| `sample_direction_light/` | 방향별 리포트 — light 변형 1방향 | 7 MB |
| `sample_direction_full/` | 방향별 리포트 — full 변형 1방향 | 7 MB |

탭 구성: Overview, Mollweide Map, Time History, Part Risk, Heatmap, Directional,
Failure, Statistics, Impact Analysis, Part Analysis, Advanced, Render Export,
Energy Flow, Contact Profile, Tolerance DOE, Set Report.

2026-05 구판은 탭이 12개였다. Energy Flow·Contact Profile·Tolerance DOE·Set Report 가 이후 추가분이다.

## d3plot 없이 리포트를 다시 뜨려면

`sphere_report.json` 만 있으면 된다. d3plot 363 GB 가 없어도 HTML 이 나온다.

```bash
gunzip -k sphere_report.json.gz
apptainer exec /data/SmartTwinPostprocessor/SmartTwinPostprocessor.sif \
    python3 -m koo_sphere_report --from-json sphere_report.json \
    --format html -o sphere_report_regen.html
```

실측 49초. 탭 구성은 16개로 동일하다.

🔴 다만 **완전히 같은 파일이 나오지는 않는다.** 직접 생성분은 내장 데이터가 7.9 MB,
`--from-json` 재생성분은 5.1 MB 다(약 35% 적다). JSON 에 담긴 시계열이 이미 한 번 줄여진
것이라 차트 해상도가 낮아진다. 수치 요약·탭 구성·방향 20개는 같다.

## 동봉하지 않은 것

- `d3plot` 원본 — 방향당 약 19 GB, 20방향 363 GB
- 방향별 `analysis_result.json` — 각 96 MB. 집계 리포트의 실제 입력
- full 변형의 단면뷰 영상 — 방향당 25개 217 MB

원본 경로: `/data/koopark/Test_Postprocess_v14/`
