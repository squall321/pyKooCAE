# KooMeshModifier 모드: DEFEATURE_MESH

## 1. 목적 / 개요

`DEFEATURE_MESH`는 지정한 **솔리드 파트의 외곽면(external boundary)** 에서 `MinLength`보다 짧은 짧은변/작은 삼각형 면을 정리(collapse)하여 미세 형상을 제거(defeature)한 뒤, 정리된 외곽면을 STL로 내보내고 외부 메셔 **gmsh**로 해당 파트를 재메시하는 모드이다.

핵심 동작 흐름 (`KooDynaAdvancedModification.py:171-547`):
- 대상 파트의 외곽면 삼각형 segment / 외곽 노드 추출 (`GetExternalBoundary`, `GetExternalNodes`)
- `MinLength`보다 작은 삼각형(세 변 모두 짧음)을 무게중심으로 collapse → 퇴화 segment 제거 (1차 루프)
- `MinLength`보다 짧은 변을 node merge 로 collapse (2차 루프)
- inradius가 `MinLength/2`보다 작은 가늘고 긴 삼각형에 대해 edge flip 시도 (3차 루프)
- 남은 삼각형들을 `output.stl`로 저장 후 gmsh `mesh_shape_from_stl`로 파트 재메시

참고: 본 모드는 전용 옵션 블록 파서(`**defeaturemesh`, `KooMeshModifier.py:1616-1644`)와 dispatch(`KooMeshModifier.py:2816-2818`), 구현 메서드(`DefeatureMesh`, `KooDynaAdvancedModification.py:171`)가 모두 존재한다. 다만 입력 형상 변형이 큰 휴리스틱 알고리즘이라 결과 품질은 입력에 강하게 의존한다(아래 5절 참조).

## 2. 입력 옵션 · 인자

KooMeshModifier 입력 옵션 파일(.txt) 안에서 `*Mode` 블록에 `defeature_mesh,<modeid>`를 등록하고, 별도의 `**DefeatureMesh,<modeid>` 옵션 블록에 세부 옵션을 기술한다.

- 모드 등록: `KooMeshModifier.py:273-275` (`defeature_mesh` → `DEFEATURE_MESH`)
- 옵션 파싱: `KooMeshModifier.py:1616-1644` (`**defeaturemesh` 블록)
- 디스패치: `KooMeshModifier.py:2816-2818` → `GenerateDefeatureMesh` (`KooMeshModifier.py:2467-2469`) → `advancedModification.DefeatureMesh(curOption)`

| 옵션 카드 | 인자 | 의미 | 기본값 | 근거 |
|---|---|---|---|---|
| `PIDS` | `pid1,pid2,...` | defeature 대상 파트 ID 리스트 (한 줄에 복수 지정) | `[]` (빈 리스트) | `KooMeshModifier.py:1627-1631` |
| `PID` | `pid` | 대상 파트 ID 단건 (`PIDS`에 append) | — | `KooMeshModifier.py:1632-1635` |
| `MinLength` | `value` | collapse 임계 길이. 이보다 짧은 변/작은 면을 제거하고, gmsh 재메시의 최소 요소 크기로도 사용 | (키 없음 → KeyError) | `KooMeshModifier.py:1636-1639`, `KooDynaAdvancedModification.py:173,206,253,440,530` |

주의 사항:
- 블록 종료는 `**end` 마커로 한다 (`KooMeshModifier.py:1625-1626`). 종료 마커가 없으면 파일 끝(`if not line: break`)까지 읽는다.
- `PIDS` / `PID` 모두 동일한 `curOptions["PIDS"]` 리스트에 누적된다. 두 카드를 섞어 써도 무방하다.
- `MinLength` 카드가 없으면 `DefeatureMesh`에서 `option["MinLength"]` 접근 시 KeyError가 난다 (`KooDynaAdvancedModification.py:173`) — 반드시 지정할 것. (확인 필요: 기본값 fallback 없음)
- 라인 매칭은 부분 문자열 검사이며 순서상 `pids`를 먼저 검사하므로(`KooMeshModifier.py:1627`), `pids`가 `pid`보다 우선 매칭된다.

## 3. 사용 예제

전용 예제 파일은 저장소에 존재하지 않는다(`Examples/` 하위에 `defeaturemesh`/`DEFEATURE_MESH` 참조 없음 — grep 확인). 아래는 코드 파서(`KooMeshModifier.py:234-275`, `1616-1644`) 기준으로 재구성한 최소 옵션 블록이다.

KooMeshModifier 옵션 파일(.txt) 발췌:

```
*Mode
defeature_mesh,1
*EndMode

**DefeatureMesh,1
PIDS,101,102
MinLength,0.5
**EndDefeatureMesh
```

- `defeature_mesh,1` → modeID `1`로 `DEFEATURE_MESH` 등록 (`KooMeshModifier.py:273-275`).
- `**DefeatureMesh,1` → modeID `1`의 옵션 블록 시작, `curModeID = int(svector[1])` (`KooMeshModifier.py:1617-1618`).
- `PIDS,101,102` → 파트 101, 102가 대상 (`KooMeshModifier.py:1627-1631`).
- `MinLength,0.5` → collapse / 최소 메시 임계 길이 0.5 (`KooMeshModifier.py:1636-1639`).
- `**EndDefeatureMesh` → `**end` 부분 매칭으로 블록 종료 (`KooMeshModifier.py:1625-1626`).

단일 파트만 처리하려면 `PIDS,101` 또는 `PID,101` 한 줄을 쓰면 된다.

확인 필요: 위 블록의 정확한 동작은 코드 파서 기준으로 재구성한 것이며, 실제 검증된 예제로 확인된 것은 아니다.

## 4. 동작 원리 (코드 근거)

진입은 `GenerateDefeatureMesh`가 옵션을 그대로 넘겨 `advancedModification.DefeatureMesh(curOption)`를 호출하는 구조다 (`KooMeshModifier.py:2467-2469`). 실제 알고리즘은 `KooDynaAdvancedModification.DefeatureMesh`에 있다 (`KooDynaAdvancedModification.py:171`).

파트별 처리 (`KooDynaAdvancedModification.py:177-547`):

1. **외곽면 추출** — `elemMan.GetExternalBoundary(True)`로 외곽 삼각형 segment, `elemMan.GetExternalNodes()`로 외곽 노드를 얻어 dict 화한다 (`KooDynaAdvancedModification.py:186-190`).

2. **1차 루프 — 작은 면 collapse** — 각 segment의 세 변 길이 `l1,l2,l3`를 계산하고, `max(l1,l2,l3) < minLength`인(즉 세 변이 모두 짧은) 삼각형은 세 노드를 무게중심으로 합쳐 collapse 한다 (`KooDynaAdvancedModification.py:202-213`). 그 후 두 노드 id가 같아진 퇴화 segment를 제거하며, 제거된 게 없을 때까지 반복한다 (`KooDynaAdvancedModification.py:215-230`). 동시에 `curMaxLength`에 관측된 최대 변 길이를 누적한다 (`KooDynaAdvancedModification.py:205`).

3. **2차 루프 — 짧은 변 collapse** — segment 키를 내림차순 정렬한 뒤, 각 삼각형의 최소 변(`curMinLength`)이 `minLength`보다 작으면 그 변의 두 끝 노드를 하나로 merge 한다. 변 종류(`l1`/`l2`/`l3`)에 따라 합칠 노드를 결정하고, 인접 segment들에서 사라진 노드 id를 새 노드 id로 갱신하여 메시 위상을 유지한다 (`KooDynaAdvancedModification.py:241-420`). merge로 퇴화된 segment는 popiList에 모아 일괄 제거한다 (`KooDynaAdvancedModification.py:299-300, 400-414`).

4. **3차 루프 — 가늘고 긴 삼각형 edge flip** — Heron 공식으로 면적/내접원 반지름(`radius = area/semiperimeter`)을 구해, `radius < minLength/2`이고 가장 긴 변이 `6*radius`보다 길면 인접 삼각형과 공유 변을 flip(대각선 교체)하여 sliver를 개선한다 (`KooDynaAdvancedModification.py:433-490`).

5. **STL 내보내기** — 정리된 segment들을 삼각형 좌표 배열로 변환해 `numpy-stl`(`from stl import mesh`)로 현재 작업 디렉터리에 `output.stl`로 저장한다 (`KooDynaAdvancedModification.py:499-520`).

6. **gmsh 재메시** — `KooMeshManagerGMSH`를 만들고, 대상 파트의 기존 요소를 모두 제거(`RemoveAllElements`)하고 요소가 쓰던 노드만 남긴 뒤(`RemoveNodesExceptNodes`), `mesh_shape_from_stl("output.stl", minLength, curMaxLength, None, nodeMan.maxID+1, elemMan.maxID+1)`로 STL 형상을 다시 메싱한다 (`KooDynaAdvancedModification.py:522-530`). 즉 `minLength`/`curMaxLength`가 gmsh의 최소/최대 요소 크기로, 기존 max ID 이후 번호로 새 노드/요소를 부여한다 (`mesh_shape_from_stl` 시그니처: `KooMeshManagerGMSH.py:765`).

출력: dispatch 후 메인 루프에서 `additionalword += "_def"`가 붙은 이름으로 수정 모델이 기록된다 (`KooMeshModifier.py:2818`, `WriteModifiedFile`: `KooMeshModifier.py:2886-2888`). 부산물로 작업 디렉터리에 `output.stl`이 생성된다 (`KooDynaAdvancedModification.py:519`).

## 5. 주의사항 · 한계

- **솔리드 파트 + 삼각 외곽면 가정**: 알고리즘이 외곽면 segment를 3-노드 삼각형으로 다루므로(`segment[0..2]`, `KooDynaAdvancedModification.py:198-204`), 외곽면이 삼각형으로 추출되는 파트를 전제로 한다. 임의 메시에서의 일반성은 코드상 보장되지 않는다 (확인 필요).
- **`MinLength` 필수**: 미지정 시 KeyError로 실패한다 (`KooDynaAdvancedModification.py:173`). fallback 기본값이 없다.
- **`output.stl` 작업 디렉터리 의존**: `os.getcwd()` 기준으로 `output.stl`을 쓰고 다시 읽는다 (`KooDynaAdvancedModification.py:518-530`). 동시 실행/다중 파트 시 동일 파일명을 공유하므로 충돌·덮어쓰기 가능성 (확인 필요).
- **의존성**: `numpy-stl`(`from stl import mesh`)과 gmsh(`KooMeshManagerGMSH`)가 필요하다 (`KooDynaAdvancedModification.py:499, 522`).
- **edge flip의 평균화 코드는 비활성**: collapse 시 이웃 평균 좌표 계산 블록은 대부분 주석 처리되어 있어(`numNeighbors`가 항상 0) 실제로는 단순 node merge로 동작한다 (`KooDynaAdvancedModification.py:283-298, 301-304` 등). 코드 내 `n3.z = zNeighbor/...` 등 일부 좌표 갱신은 비활성 분기라 실 영향은 없으나 의도와 다를 수 있다 (확인 필요).
- **결과 품질 비결정성**: 휴리스틱 collapse/flip 순서가 segment 순회·정렬에 의존하므로(`KooDynaAdvancedModification.py:237-239`), 입력에 따라 결과 메시 품질 편차가 클 수 있다.

## 6. 개발 현황

**부분구현.**

근거:
- 모드 등록(`KooMeshModifier.py:273-275`), 옵션 블록 파서(`KooMeshModifier.py:1616-1644`), dispatch(`KooMeshModifier.py:2816-2818`), 구현 메서드 본체(`KooDynaAdvancedModification.py:171-547`)가 모두 존재하고 STL 추출 + gmsh 재메시까지 연결되어 있다.
- 다만 (a) collapse 시 이웃 평균화 로직이 주석 처리되어 단순 merge 로만 동작하고(`KooDynaAdvancedModification.py:283-304` 등), (b) `output.stl`을 고정 파일명으로 쓰고 읽으며, (c) `MinLength` fallback이 없는 등 운영 견고성·검증이 미흡하다.
- 전용 예제(`Examples/`)와 검증 케이스가 없어 실제 동작 검증 여부는 **확인 필요**.
