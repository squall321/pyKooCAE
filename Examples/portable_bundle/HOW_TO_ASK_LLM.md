# LLM과 함께 KooChainRun 잡 만들기 — 프롬프트 템플릿 모음

다른 PC에서 Claude / GPT 등 LLM의 도움으로 시나리오를 작성하거나 트러블슈팅할 때 쓰는 표준 프롬프트 패턴.

## 사용 패턴 (3단계)

1. **첫 대화 시**: LLM에 `QUICKSTART.md` 전체를 먼저 던지기 (context 설정).
2. **시나리오 만들기**: 아래 템플릿 중 골라서 채우기.
3. **수정/디버그**: 현재 scenario.json을 붙여넣고 변경 요청.

---

## 템플릿 1 — 새 시나리오 만들기 (초안)

```
첨부한 QUICKSTART.md 참고해서 다음 조건으로 scenario.json 만들어줘:

- project_name: <원하는 이름>
- base_dir: /data/<my_user>/<my_project>
- LSTC_LICENSE_SERVER IP: <새 클러스터 IP>
- 각도 수: <N>개 (fibonacci_lattice)
- 시뮬 시간 (tFinal): <초>
- 낙하 높이: <mm>
- 모델 파일 이름: <something>.k
- 후처리: <자동 / 수동만>
- (선택) auto_deep_mode: <inline / separate_job>
- (선택) compute node RAM 한계: <GB>

JSON 출력만 해줘.
```

## 템플릿 2 — 기존 시나리오 일부 수정

```
다음 scenario.json에서 아래 항목만 바꿔줘:

[현재 scenario.json 붙여넣기]

변경:
- 각도 수를 162 → 100으로
- ncpu를 1 → 4로
- tFinal을 0.005 → 0.003으로

나머지는 그대로. JSON 출력만 해줘.
```

## 템플릿 3 — 환경 IP/경로만 새 PC에 맞게

```
다음 scenario.json의 환경 부분만 새 클러스터에 맞게 바꿔줘:

[기존 시나리오 붙여넣기]

새 환경:
- LSTC_LICENSE_SERVER: <new_IP>
- apptainer_bind: <new mount, 보통 동일>
- base_dir: /data/<new_user>/<new_project>

JSON 출력만. 변경 사항 한 줄 코멘트 추가.
```

## 템플릿 4 — 에러 디버깅

```
첨부한 QUICKSTART.md §5 트러블슈팅 참고해서 다음 문제 해결해줘:

scenario.json:
[붙여넣기]

증상:
- 명령: KooChainRun submit runner_config.json
- 출력:
```
[에러 로그 붙여넣기]
```

추가 정보:
- compute node RAM: <GB>
- 클러스터 정보: <필요시>

원인과 해결 방법을 알려주고, 수정된 scenario.json도 같이 줘.
```

## 템플릿 5 — 후처리 옵션 추가

```
다음 scenario.json에 KooD3plotReader 자동 후처리 추가해줘:

[scenario.json 붙여넣기]

요구:
- enabled: true
- 시뮬과 deep_report는 같은 잡 (default inline)
- sphere_report는 자동으로 dependent job 제출
- yield_stress: <MPa>
- section view 축: <z / x / y>

QUICKSTART.md §4.5 참고. JSON 출력만.
```

## 템플릿 6 — 결과 분석 도움

```
방금 162각도 잡이 끝났는데 sphere_report.json 안에 뭐가 들었는지 해석해줘:

[sphere_report.json 일부 붙여넣기]

특히 다음 알려줘:
- 가장 위험한 (von Mises 최대) 각도와 그 값
- 항복 응력(350MPa) 대비 안전계수
- per-part 통계에서 주의해야 할 파트
```

---

## 빠른 답변용 단축 명령 (LLM에게)

| 단축 표현 | 의미 |
|---|---|
| "IP만 바꿔줘" | `LSTC_LICENSE_SERVER`와 base_dir 같이 바꿔달라는 의도 |
| "검증용으로 작게" | 1~5각도, tFinal 0.0005, height 1500 |
| "프로덕션 표준" | Fibonacci 162, tFinal 0.005, 후처리 자동(inline) |
| "큐 회전 빠르게" | `auto_deep_mode: separate_job` 추가 |
| "디버그 모드" | `fibonacci_lattice` `num_directions: 1`, 후처리 비활성 |

---

## 주의 사항

- LLM이 추측해서 만든 JSON은 **반드시 1각도(`01_minimal_single_drop.json` 변형)로 먼저 검증**.
- `base_dir`은 절대 경로여야 함 (LLM이 가끔 상대경로 만듦).
- `apptainer_sif` / `lsdyna_apptainer_sif` 경로는 LLM이 모르므로 QUICKSTART의 §0 전제조건 확인 결과 그대로 사용.
- 시나리오 적용 전 **JSON 문법 검증**: `python3 -m json.tool scenario.json`
