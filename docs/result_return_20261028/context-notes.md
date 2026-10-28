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

## C — 종료 코드
- 0 성공 · 1 실패 · 3 건너뜀. 1 은 이미 쓰던 값(runner_config·output_dir 없음, 잡히지 않은 예외)과 같게 뒀고, 2 는 argparse 가 쓴다.
- 건너뜀은 ".sh 없음·구버전 SIF·deep 을 돌 Run 없음" 이다. 결과 0건(sphere exit 1·3, impact 'No usable runs')은 리포트를 요청했는데 못 만든 것이라 실패로 센다.
- deep 의 "Output/ 없음"(해석이 산출물을 못 남김)은 단계 상태에 넣지 않는다. 요약 숫자로만 보인다. 해석 실패는 collect·status 몫이다.
- impact_report.sh 구버전 SIF 는 exit 0 → 4(IMPACT_RC_NO_TOOL). 의존 잡이 FAILED 4 로 보이는 게 맞다("리포트 없음" ≠ "성공").
- KooSlurm(0a8c9cca) 은 리포트 유무를 파일로 판정하고 rc 는 PP_RC=$? 로 매니페스트에 적기만 한다(set -e 아님). 그래서 비 0 이 생겨도 그쪽 흐름은 안 깨진다.

## E — deep
- `--all` 은 deep 산출물이 있으면 건너뛰고, `--deep` 을 명시하면 다시 돈다. 새 플래그 없이 "다시 뽑기" 길을 남겼다.
- KooSlurm 은 리포트 잡이 있으면 post_exec `--all` 을 생략한다. 그러면 DWI 는 deep 생산자가 없어진다 → run.sh inline deep(abc2eb5). 이는 chain 과 같은 계약(auto_deep 기본 true)이 DWI 에서만 빠져 있던 것이다.
- DWI deep 셸은 케이스마다 Run_<ts> 이름을 prepare 때 모르므로 `RUN_DIR="${1:?…}"` 하나를 두고 run.sh 가 실행 폴더를 넘긴다. Run_*/deep_report.sh(per-Run)는 만들지 않는다. postprocess 가 필요하면 fallback 으로 만든다.
- impact 의존 잡 자원(environment.ncpu·memory 상속)은 건드리지 않았다. inline deep 이면 리포트 잡은 집계만 한다. 모자라면 postprocess.impact_ncpu·impact_memory 가 이미 있다.

## D — sphere JSON
- 기본으로 켰다. 셸이 이미 `--json` 경로를 줘서 의도가 분명했고, harvest 가 1순위로 이 JSON 을 읽는다.
- 실측(10-25 SIF, 20런, 캐시 있음): html 33.1초·749 MB, html+json 34.6초·749 MB. JSON 25.3 MB(런당 약 1.3 MB). 1000런이면 1 GB 대 파일이 된다. 끄는 길은 sphere_extra_args 의 `--format`.
- 도구 `--help` 에 `--format` 이 있을 때만 준다(has_opt). 지금 SIF 와 10-17 백업 SIF 둘 다 있다.

## F — 예제
- 부분충격 예제 9개는 0b79c68(9-17)에서 이미 ton-mm-s 다.
- HWWarrantyDropTest 추적 9개의 바닥판 ρ 7850·E 2e11 은 MinimumModel(ρ 1.8e-9~2.8e-9, ton-mm-s)과 어긋난다. 같은 값이 공용 `/data/scenario` 프리셋에도 있다. 프리셋을 고치면 운영 해석 결과가 바뀌고 예제만 고치면 둘이 갈라진다 → **사용자 결정**으로 남겼다.
