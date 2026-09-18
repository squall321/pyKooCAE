# 작업 노트 — 두께방향 층 분할 (2026-09-17)

계속 덧붙여 쓴다. 중단 후 이어갈 때 여기부터 읽는다.

## 결정 1 — 작업 폴더는 프로젝트 안 `work/layersplit`
사용자 지시로 `/tmp`·스크래치패드 대신 프로젝트 내부만 쓴다. `.gitignore` 에 `work/` 한 줄 추가했다.
앞서 `/data/koopark/Test_layersplit` 에서 돌린 확인 자산(gen.py·check.py·dup.py·split.txt·restack.yaml)은
이 폴더로 복제해 쓰고, 중단되어도 같은 스크립트로 같은 값을 다시 얻을 수 있게 한다.

## 사실 1 — SolidComp 결함의 위치
`KooDynaAdvancedModification.ConvertSolidtoSolidComp` 는 층(plane) 루프 안에서 상면 세그먼트마다
`nodeMan.CreateNode` 를 4번 호출한다. 세그먼트 사이에 공유가 없으므로 중간 평면의 노드가
요소 개수 × 4 개 만들어진다. 상·하면은 원본 노드를 그대로 쓰므로 그 두 면만 연결돼 있다.
측정값(수정 전): 노드 280 / 고유 위치 140, 중간 평면 5개마다 중복 28개.

## 결정 2 — 수정 방향은 "상면 노드 기준 1개"
세그먼트가 아니라 **상면 노드 id** 를 키로 층별 노드를 한 번만 만들고 재사용한다.
상면 노드 ↔ 하면 노드 대응은 이미 `revidDict` 로 있으니 보간식은 그대로 쓴다.
좌표식·층 위치(posList)·파트 생성·파트셋 처리는 손대지 않는다 → z 층 경계와 파트 구성은 불변.

## 사실 2 — KooRemapper restack 은 코드가 맞고 설명이 틀림
`ModelAssembler::applyRestack` 은 파트 노드를 두께 방향 기둥으로 묶고(기둥 높이 균일 검사),
바닥 층에서 footprint 를 뽑아 층을 재생성한다. 즉 입력은 extrude 된 헥사 솔리드다.
help 요약("셸/면을 ... 돌출")과 영문 본문("Source shell part ID")만 틀렸다. help 안의 사례는
`generate box`(솔리드) → restack 이라 맞다. 저장소 예제는 `model:` 키라 실패(`base_model` 필요).

## 사실 3 — 수정 결과 (2026-09-17 22:00)
`ConvertSolidtoSolidComp` 수정 후 층 경계 노드가 공유된다. 같은 모델에서
노드 280→140, 중복 0, z 층 경계·파트별 요소 수·평면 좌표·부피 부호는 그대로.
층 경계 노드가 공유하는 요소 수는 2→8 로 늘었고, KooRemapper restack 결과와 노드 위치 집합이 완전히 같다.
회귀: DROP 덱·IMPACT(DWI) 덱이 수정 전후 바이트 동일(diff 0), tests 5종 통과.

## 사실 4 — 회귀 중 발견한 별건: DWI 임팩터 메시 기본값 0.001
`MeshSize` 를 안 주면 `KooDynaAdvancedModification` 이 0.001 을 쓴다(3381·3815·4584행).
mm 단위 모델에서 지름 2 mm 구를 0.001 mm 로 메시하려 들어 gmsh 가 14 GB 까지 먹고 폭주했다.
(이전 fix_20260917 검증 때는 gmsh 셔밍 오류로 즉시 실패해 드러나지 않았다.)
이번 회귀 입력에는 `MeshSize,0.5` 를 명시해 우회했다. **미수정 — 사용자 판단 필요.**

## 결정 3 — KooRemapper 는 origin/main 기준으로 작업
브랜치가 21:02 에 origin/main 으로 리셋되어 help 카탈로그 위치가 바뀌었다
(`platform/core/kooremapper_core/catalog_data.json`, 소비자는 `catalog.py`).
`description` 은 이미 정확했고 `summary` 만 "shell surface" 였다. 여기와 `src/main.cpp` 의 영문 help 를 고쳤다.
예제는 키 두 가지가 낡아 있었다 — `model:`(파서는 `base_model:` 만 받음), `output:` 에 붙은
`examples/assemble_display/` 접두사(현재 바이너리는 YAML 폴더 기준으로 경로를 풀어 중복됨).
둘 다 고치고 4개 예제를 SIF 바이너리로 실행해 통과 확인했다.

## 결정 4 — KooRemapper 갈래 충돌 정리 (2026-09-17 22:1x)
상태를 정리하면 이랬다.
- `origin/feat/kooremapper-platform`(5088fd7) — 이전 세션의 결함 수정 20여 건을 포함한 본줄기. 63 커밋이 main 에 없다.
  예제 YAML 의 `model:`·출력 경로 중복은 **여기서 이미 고쳐져 있었다**(983dcab·3a68a0f).
- `origin/main`(88c3802) — 카탈로그·플랫폼 수정 3건(90386dc·f745f7c·88c3802)만 따로 얹혀 있다.
- 로컬 `feat/kooremapper-platform` 은 21:02 에 origin/main 으로 리셋돼 있었고, 내 이번 수정은 그 위 작업트리에 있었다.

정리 방법: `integrate/restack-help-20260917` 을 origin/feat/kooremapper-platform 에서 만들고 `origin/main` 을 병합(충돌 0).
그 위에 이번 help·카탈로그 문구 수정만 다시 얹었다. 작업트리에 있던 예제 YAML 수정은 platform 쪽과 내용이 같아 버렸다.
🔴 주의: 내 첫 패치는 재질 카드를 **정렬 전 버전으로 되돌리는** 내용을 품고 있었다(내 기준 커밋이 main 이었기 때문).
patch 적용 대신 병합본 위에서 손으로 다시 고쳐 platform 의 10열 정렬을 지켰다.

## 마감 (2026-09-18 00:30) — SIF v99
- KMM 재빌드(build_without_automatedmodeller.sh) → /opt·/data·appt313 소스트리 갱신(22:54).
  배포 바이너리로 재확인: 중복 0, 공유 8, 나머지 값 동일.
- KooRemapper 는 `scripts/build_linux_compat.sh`(debian:12 빌더, GLIBC_2.34)로 빌드해
  `appt313/opt/kooremapper/bin/KooRemapper` 에 설치(백업 .bak 남김).
- SIF 빌드는 **sudo 필요**(샌드박스 하위가 root 소유). `sudo bash BuildSmartTwinPreprocessor.sh`.
- SIF v99 + tar `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_20260918_v99.tar.gz`, node001 배포·e2e 통과.
  node002·viz-node001·viz-node002 는 down 이라 배포 실패(기존 상태).
- KooRemapper help 사례 스위트는 SIF 안에서 **건너뜀 0, ALL PASS**. 호스트에서만 matdb 가 실패하는데
  사례가 `/opt/kooremapper/materials/material_db.json`(SIF 내부 경로)을 가리키기 때문이다(meshfix 와 같은 환경 의존).

## 2차 (2026-09-18) — 같은 부류 결함 일괄 수정

감사 워크플로우(6차원)는 세션 종료로 중단돼 결론을 남기지 못했다. 의심 지점이 이미 특정돼 있어
직접 실행으로 확인했다. 확인된 것만 고쳤고, 근거는 전부 실행 결과다.

### UnstructuredtoStructured + LayerThickness — 원래 동작한 적 없음
4건이 겹쳐 있었다.
1. 정규화 분모가 `zLocationList[-1]`(= minZ + 총두께) 이라 minZ ≠ 0 이면 층이 아래로 눌렸다 → 총두께로 나눈다.
2. 층별 KDTree 선택이 겹침 검사라 경계가 맞닿은 직전 층(k-1)을 먼저 집었다 → k 번째 층은 k 번째 구간.
3. 구간에 원본 요소 중심이 없으면 `KDTree([])` 가 ValueError → 빈 구간은 None, 전체 KDTree 로 대체.
4. `cureidnodes = part.elementManager.elements[eid].nodes` 는 **이미 지운 요소**를 조회해 KeyError.
   대입만 하고 쓰지 않는 죽은 값이라 제거했다(판정에 쓰는 bbox 는 eidtoMinMax 에 이미 있다).
🔴 4번 때문에 이 경로는 입력과 무관하게 항상 죽었다. 수정 전 코드로 빈 구간이 없는 입력을 돌려 KeyError 를 재현해 확인했다.
수정 후 flat(minZ=0)·오프셋(minZ=10)·2파트 스택 모두 올바른 층 경계와 PID 배정을 낸다.

### 임팩터 기본값 (DWI 3개 진입점 공통)
`Dimension` 기본 [0.008], `MeshSize` 기본 0.001 은 SI(m) 기준 — 8mm 임팩터를 8분할한 값이다.
mm 모델에서 2mm 구를 0.001mm 로 메시하려다 gmsh 가 14GB 를 먹었다.
`_ResolveImpactorMeshSize` 가 치수 대비 분할 수가 100 을 넘으면 치수/8 로 대체하고 경고한다.
기본 치수 0.008 은 정확히 0.001 이 나와 기존 SI 입력은 값이 변하지 않는다(시험으로 고정).
`_ResolveImpactorDimension` 은 값은 그대로 두고 미지정 경고만 남긴다.

### 형제 변환
`ConvertSolidtoSolidwithSlack` 도 세그먼트마다 CreateNode 하지만 뒤에서 `MergeElementNodeswithTolerance()`
로 합치므로 결과가 끊기지 않는다 — 수정 불필요.
`ConvertSolidtoStructuredSolidwithZSlack` 은 격자 인덱싱까지만 있고 모델에 반영이 없어, 조용히 원본을
그대로 내보냈다(변환된 것으로 오인). 명시적 실패(sys.exit(1))로 바꿨다. 미완성 코드는 주석과 함께 남겼다.

### 손대지 않기로 한 것
- **KMM 옵션 파서의 조용한 무시**: 모드별 키 화이트리스트가 필요해 전 모드에 영향을 준다. 위험 대비 이득이 낮다.
- **KAM `*Layer` 블록의 모르는 키**: 970줄 중첩 분기에 `svector[0]` 비교가 109개다. PKG 생성을 깨뜨릴 위험이 크다.
  (최상위 키워드는 이미 `Keyword Error ... is not supported` + exit 1 로 막혀 있다.)

### 2차 마감 (2026-09-18 11:10) — SIF v100
KMM 재빌드(10:35) → /opt·/data·appt313 소스트리 갱신 → SIF v100(10:55) →
tar `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_20260918_v100.tar.gz` → node001 배포(11:03).
node001 e2e 6항목 통과 — SolidComp 중복 0·공유 8, U2S minZ=10 층 경계 10/10.2/10.7/11,
U2S 2파트 PID 배정, DWI MeshSize 경고 후 완주, ZSlack 종료 코드 1, restack 정상.
node002·viz 노드 2대는 여전히 SSH 불가(down).
검증 자산 노드측 `/data/koopark/Test_layersplit_v100`, 호스트측 `work/layersplit/audit`.
