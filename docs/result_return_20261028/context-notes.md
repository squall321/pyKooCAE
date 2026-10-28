<!-- 리포트 자동 귀환 요청 처리 중 내린 결정과 근거 -->
# 결정 노트 — 리포트 자동 귀환 요청 (2026-10-28)

## 대조
- 요청서 행 번호는 bf32432 기준이라 지금과 다르다. KooChainRun 의 의존 잡 제출은 1416행, postprocess 는 3186행이다.
- B 는 5baae8d 가 요청서 네 시간 뒤에 고쳤다. 커밋 메시지에 요청서 이름이 없어 전달자가 못 찾았다.
- F 의 KMM 폴백(충격체·댐퍼·바닥판)은 10-23 리뷰 E·F 묶음에서 고쳤다(tests/test_dwi_fallback_units.py).

## A + E(output_dir)
- 로더(KooD3plotReader loader.py `_discover_test_impact_runs`)는 `test_dir / "output"` 고정이다. 그리고 `test_dir/scenario.json` 은 project_name 에만, `test_dir/.impact_cache` 는 캐시에 쓴다.
- output_dir 을 통째로 링크하면 `$OUTPUT_DIR/.impact_root/output → $OUTPUT_DIR` 고리가 생긴다. `glob('**', recursive=True)` 는 디렉터리 링크를 따라가서 고리에서 끝나지 않는다. 그래서 런 폴더(`Run_*`·`results`)만 링크한다.
  곁 폴더(`<부모>/.impact_root_x`)로 두면 시나리오 폴더가 더러워지고 바인드도 하나 더 필요하다. 그래서 안에 둔다.
- 이름이 `output` 인 경우는 지금과 바이트가 같게 둔다(체인 IMPACT 기본, 템플릿 기본 격자).
- scenario.json 링크는 DWI 만 건다(prepare 가 경로를 안다). Designer 는 파일 이름을 모르므로 건드리지 않는다. 체인에서 output_dir 이름이 다르면 project_name 이 `.impact_root` 가 된다(런은 찾는다).
