<!-- 낙하·부분충격 리포트 자동 귀환 요청서(REQUEST-drop-impact-result-return.md) 처리 계획 -->
# 계획 — 리포트 자동 귀환 요청 A~F (2026-10-28)

요청서는 `docs/REQUEST-drop-impact-result-return.md`(dd26d62, 기준 bf32432)다. 걸린 쪽은 KooRemapper
`platform/docs/REQUEST-postprocess-operation.md` §7-1(DynaForge 후처리 예약 연산)이고, 전달자는 kooremapper-4a 다.

## 대조 결과 (현재 코드 015ac05)

| | 요청 | 지금 |
|---|---|---|
| A | 부분충격 prepare 가 impact_report.sh 를 만든다 | **미해결** — DWI prepare 는 .sh 를 안 쓴다 |
| B | 초속 이중 합산 | **해결** 5baae8d(9-17). v97 이후 SIF 에 들어 있다 |
| C | 후처리 실패를 종료 코드로 | **미해결** — cmd_postprocess 는 늘 0, impact 구버전 SIF 는 exit 0 |
| D | sphere JSON | **미해결** — .sh 가 `--json` 만 주고 `--format` 을 안 준다 |
| E | 드라이버 deep 을 줄이고 DWI output_dir 을 따른다 | **미해결** — `--all` 은 이미 있는 deep 도 다시 돌고, 출력 폴더는 `project.output_dir`→`<config>/output` 만 본다 |
| F | 예제·폴백 SI 물성 | **폴백은 해결** 7b31d09·1de4a5a·94ba214·7afefc5(10-23). 예제 파일은 남았다 |

## 할 일 (커밋 단위)

1. **A + E(output_dir)** — 서로 걸려 있어 한 묶음.
   - KooChainRun: 출력 폴더 해석을 헬퍼 하나로 모은다(`project.output_dir` → 최상위 `output_dir`(DWI) → `<base_dir>/output`). 쓰는 곳은 postprocess 와 의존 잡 제출, 두 곳이다.
   - DWI prepare: `postprocess` 블록이 있으면 output_dir 에 impact_report.sh 를 쓴다(Designer 와 같은 계약: enabled 와 관계없이).
   - impact_report.sh: 로더는 `<test_dir>/output` 만 읽는다. output_dir 이름이 `output` 이 아니면
     `$OUTPUT_DIR/.impact_root/output/` 에 런 폴더(`Run_*`·`results`) 링크를 만들어 그것을 test_dir 로 쓴다. 이름이 `output` 이면 지금과 바이트가 같다.
2. **C** — `KooChainRun postprocess` 종료 코드: 0 모두 성공 / 1 하나라도 실패 / 3 실패는 없고 건너뜀이 있음. 끝에 요약 한 줄을 찍는다.
   impact_report.sh 의 구버전 SIF 건너뜀은 `exit 0` 대신 `exit 4` 로 하고, postprocess 는 이를 건너뜀으로 센다.
3. **E(deep)** — `--all`(과 플래그 없음)은 deep 산출물(`Output/report/{result,analysis_result}.json`)이 이미 있는 Run 을 건너뛴다. 판정은 sphere_report.sh 와 같다. `--deep` 을 명시하면 지금처럼 전부 다시 돈다.
4. **D** — sphere_report.sh 가 `--format html json terminal` 을 준다. 도구의 `--help` 에 `--format` 이 있을 때만 준다(옛 SIF 보호). `sphere_extra_args` 의 `--format` 이 뒤에 붙어 이긴다.
5. **E(DWI deep)** — DWI run.sh 가 체인과 같은 계약(`postprocess.enabled && auto_deep`, 기본 inline)으로 LS-DYNA 뒤 deep 을 돈다.
   그러면 드라이버 `--all` 은 deep 을 건너뛰고, 의존 impact 잡은 Run 마다 unified_analyzer 를 돌지 않는다. `separate_job` 은 DWI 에서 지원하지 않는다고 알리고 run.sh 에 넣지 않는다.
6. **F(예제)** — 모델 단위계를 확인한 뒤 예제 scenario 의 SI 물성을 덱 단위로 바꾼다. 범위는 별도로 판단한다.
7. 시험 `tests/test_result_return.py` — 새 검사는 부모 판에서 실패하는지 먼저 본다. 회귀: DWI postprocess 없음 prepare 산출물과 체인 `output` 이름 impact_report.sh 의 바이트 비교.
8. 빌드 → SIF 소스 트리 → SIF → tar → 노드(메모리 절차 `feedback_always_sif_tar_after_any_module`). 무거운 작업은 다른 세션 빌드와 겹치지 않게 확인한 뒤 한다.

## 이 리포가 정한 것 (요청서 §4)

- 초속 주체: 워크플로가 `InitialVelocityZ,0` 을 쓰고 KMM 이 Height 로 만든다(5baae8d 에서 이미 정함).
- 단위계 키: 만들지 않는다. KMM 이 재질 밀도와 Gravity 로 판정한다(10-23). `UnitSystem` 은 열하중 전용(기본 SI)으로 남는다.
- impact_report 실행 주체: **의존 잡**(submit 이 거는 것)이 정본이다. 드라이버 post_exec 의 `postprocess --all` 은 deep 이 채워져 있으면 deep 을 건너뛰지만, 종합 리포트를 다시 만든다. 하나로 줄이려면 템플릿 post_exec 를 바꿔야 한다(KooSlurm 에 알린다).
- 귀환 매니페스트: KooSlurm 이 쓴다. pyKooCAE 는 종료 코드와 요약 줄을 준다.
