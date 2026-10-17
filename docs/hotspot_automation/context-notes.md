<!-- 핫스팟 자동 후처리 배선 작업의 결정과 근거 -->
# 컨텍스트 노트 — 핫스팟 고도화 배선

## 2026-10-16
- 발견 경위 — 사용자 질문 "핫스팟·후처리 고도화가 다 반영됐나". 배포본 버전(호스트 2df44eb, Post SIF 3992a94)은
  최신이고 MCP post_* 는 `--help` 플래그를 전부 가졌다. 그런데 엔진 기능이 표준 경로(`koo_deep_report`)에서 막혀
  있었다 — 9월 커밋이 C++ 만 고치고 파이썬 허용 목록을 안 바꿨다. 회신 문서의 YAML(`criteria`)도 deep 경로에선 안 통한다.
- 1 을 KooD3plotReader 배포 뒤로 미룬 이유 — KooChainRun 이 지금 새 기준을 넘기면 deep 이 rc=1 로 죽는다.
  지금은 KooChainRun 이 모르는 기준을 경고하고 버린다(von_mises 로 돈다) — 나쁘지만 멈추지는 않는다.
- `hotspot_part` 는 셸 스크립트에 박히므로 숫자 PID 만 통과(그 밖은 경고하고 버린다, 전부 버려지면 플래그 없음 = 전 파트).
  `sphere_extra_args` 보다 앞에 둬서 추가 인자가 이긴다(deep 의 hotspot 키와 같은 규칙).

## 2026-10-17
- MCP 의 KooRemapper 카탈로그는 리포 HEAD 가 아니라 **배포 바이너리의 소스 커밋**(5a0fbd6)에서 가져왔다. HEAD 의 두 커밋은
  아직 노드에 없는 수정의 설명이라, 넣으면 도구 설명이 노드 동작과 어긋난다. 그 차이만큼 벤더링 비교 시험은 다음 배포까지 실패한다.
- 캠페인 경로 e2e 는 LS-DYNA 라이선스 만료(10-16) 때문에 **대역 솔버**로 했다 — `environment.lsdyna_path` 를 지난 실해석 결과
  (Test_chdir_health)를 링크·복사하는 스크립트로 바꾸고 LS-DYNA SIF·MPI 를 껐다. 러너는 종료 코드 0 과 `Output/dynain` 만 보므로
  그 뒤의 런타임 deep_report.sh 생성·자동 실행은 실제와 같다. 해석 자체는 검증 대상이 아니다. 시험 폴더 /data/koopark/Test_HotspotKeys_v118.
- 판정은 의미로 — 요청한 기준 집합과 항목 수, `mean_timemax` 의 존재(대조군에선 0개), 그리고 mean_timemax ≤ elemmax_then_mean
  (시간 극값의 평균은 평균의 시간 극값보다 작을 수 없다). 같은 기준의 stress_mean 이 시간 집계를 켜도 23/23 같았다.
- 캠페인 deep report 는 `--section-view` 가 늘 붙어 파트마다 구역 뷰를 그린다(2 CPU 노드에서 파트당 약 2.5분). `--no-render` 로는 안 꺼진다.
  끄는 키는 없다 — 바꿀 일은 아니고, 대형 모델 후처리 시간 예측에 참고.
