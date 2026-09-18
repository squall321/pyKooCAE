# 두께방향 층 분할 결함 수정 계획 (2026-09-17)

## 배경

"z 로 extrude 된 메시를 층별 두께로 나눠 격자 재생성" 요청을 확인하다가 두 가지가 드러났다.

1. **KMM `PART_EXCHANGE` + `*ConvertHexato,SolidComp`** — 층 두께·파트·재질은 맞게 나오지만
   중간 층 경계 노드를 **요소마다 따로** 만든다. 같은 위치에 노드가 겹쳐(고유 위치 140곳에 노드 280개)
   층 내부가 평면 방향으로 끊어진다. 실측: `work/layersplit` 플레이트(평면 12요소, 두께 1.0, 2층)를
   0.2/0.5/0.3 + 요소수 1/2/3 으로 분할 → 중간 5개 평면마다 중복 노드 28개.
   근거 `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
   `ConvertSolidtoSolidComp` — 상면 세그먼트 루프 안에서 `nodeMan.CreateNode` 를 호출한다.
2. **KooRemapper `restack`** — 동작은 정상(노드 공유, 평면 메시 보존, 층별 `num_elements`).
   설명만 틀렸다. help 한 줄 요약·영문 본문이 "셸 면을 돌출"이라고 하는데 코드는 extrude 된
   헥사 솔리드를 받는다. 저장소 예제 `examples/assemble_display/b7_*.yaml` 은 최상위 키를
   `model:` 로 써서 그대로 돌리면 `base_model not specified` 로 실패한다.

## 목표

- KMM `SolidComp` 가 층 경계 노드를 이웃 요소와 공유하도록 고친다. 다른 모드·다른 변환은 건드리지 않는다.
- KooRemapper `restack` 의 help 문구와 저장소 예제를 실제 동작에 맞춘다.
- 두 수정 모두 회귀 0 을 증명하고, 모듈 빌드 → SIF 소스트리 → SIF → tar 순서로 배포한다.

## 성공 기준 (검증 방법)

| # | 기준 | 검증 |
|---|------|------|
| 1 | SolidComp 결과에 같은 위치 중복 노드 0 | `work/layersplit/dup.py` — 고유 위치 = 노드 수 |
| 2 | z 층 경계·파트별 요소 수·평면 좌표는 수정 전과 동일 | `work/layersplit/check.py` 출력 비교 |
| 3 | 뒤집힌 요소 0, 고아 노드 0 | 같은 스크립트 |
| 4 | 기존 모드 회귀 0 | DROP/IMPACT 덱 수정 전후 diff 0 + tests/ 기존 스위트 통과 |
| 5 | KooRemapper 예제·help 가 실제로 돌아감 | 고친 yaml 을 바이너리로 실행, help 사례 스위트 통과 |
| 6 | 배포본에서 재확인 | 빌드 후 KMM 바이너리로 1~3 재실행, SIF 로 KooRemapper 재실행 |

## 작업 순서

1. 프로젝트 안 작업폴더(`work/layersplit`)에 재현 자산 복제 → 소스(venv312)로 결함 재현
2. `ConvertSolidtoSolidComp` 노드 공유 수정
3. 기준 1~3 확인 + 회귀(기준 4)
4. KooRemapper help·예제 수정, 기준 5 확인
5. 빌드 → SIF 소스트리 갱신 → SIF → tar, 기준 6 확인
6. 커밋·push (양쪽 저장소)

## 범위 밖

- `ConvertSolidtoSolidwithSlack` / `SolidStructuredZSlack` (같은 파일의 다른 변환, 이번 요청과 무관)
- `UnstructuredtoStructured` 의 bbox 격자 재생성 로직
