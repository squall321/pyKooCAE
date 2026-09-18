# 층 분할 결함 수정 체크리스트 (2026-09-17)

작업은 모두 프로젝트 안에서만 한다. 검증 자산은 `work/layersplit/` (gitignore).
중단 시 이 파일의 마지막 체크 지점부터 이어간다.

## 1. 재현
- [x] `work/layersplit/` 에 모델 생성기·옵션·검사 스크립트 배치 (gen.py, split.txt, restack.yaml, check.py, dup.py)
- [x] 소스(venv312)로 KMM SolidComp 재현 — 중복 노드 확인 (수정 전 기준값 기록)
- [x] 수정 전 결과 파일 보존 (`work/layersplit/before/`)

## 2. KMM SolidComp 노드 공유 수정
- [x] `ConvertSolidtoSolidComp` 층 경계 노드를 상면 노드 기준으로 1개만 만들도록 수정
- [x] 중복 노드 0 확인 (dup.py)
- [x] z 층 경계·파트별 요소 수·평면 좌표·부피 부호가 수정 전과 같음 (check.py)
- [x] 층 경계에서 이웃 요소가 실제로 연결됨 확인 (노드 공유 개수)

## 3. 회귀 (기존 기능 보호)
- [x] DROP 덱 수정 전후 diff 0
- [x] IMPACT 덱 수정 전후 diff 0
- [x] tests/test_fall_gravity.py 통과
- [x] tests/test_cli_help.py 통과
- [x] tests/test_kam_fixes.py 통과
- [x] tests/test_drop_attitude_dt_shadow.py, test_encoding_guard.py 통과

## 4. KooRemapper restack 설명·예제
- [x] 설정 키 파싱 확인 (`base_model` 만 받는지)
- [x] help 요약·본문 문구를 실제 입력(extrude 된 솔리드)에 맞게 수정
- [x] `examples/assemble_display/*.yaml` 최상위 키(`model:`→`base_model:`) + 출력 경로 중복 수정
- [x] 고친 예제를 바이너리로 실행해 통과 확인
- [x] 카탈로그 시험 통과 (platform/backend/tests/test_catalog.py, 8건)

## 5. 빌드·배포
- [x] KMM 모듈 빌드 (`build_without_automatedmodeller.sh`)
- [x] 배포 바이너리로 기준 1~3 재확인
- [x] KooRemapper 빌드 + SIF 소스트리 갱신
- [x] SIF 생성 (v99)
- [x] SIF 로 restack 예제·help 재확인
- [x] tar 생성
- [x] node001 배포 + e2e (node002·viz 노드는 down 상태라 실패)

## 6. 마감
- [x] context-notes.md 마감 기록
- [x] pyKooCAE 커밋·push
- [x] KooRemapper 커밋·push
- [x] 메모리 갱신

## 7. 2차 — 같은 부류 결함 일괄 수정 (2026-09-18)
- [x] 형제 변환 점검 — SolidwithSlack 은 뒤에서 MergeElementNodeswithTolerance 로 합치므로 정상
- [x] UnstructuredtoStructured 정규화 분모 (minZ ≠ 0 에서 층이 눌리던 것)
- [x] UnstructuredtoStructured 층 선택 인덱스 (경계가 맞닿아 직전 층을 집던 것)
- [x] UnstructuredtoStructured 빈 구간 KDTree 예외
- [x] UnstructuredtoStructured 이미 지운 요소 재조회(KeyError) — 이 경로는 원래 동작한 적이 없었다
- [x] 임팩터 MeshSize 기본값 가드 (mm 모델 gmsh 폭주)
- [x] 임팩터 Dimension 미지정 경고 (기본 0.008 은 SI 기준)
- [x] SolidStructuredZSlack 미구현 → 조용한 무변환 대신 명시적 실패
- [x] 신규 시험 tests/test_layer_split.py (21항목) 통과
- [x] 회귀 — DROP 덱 diff 0, MeshSize 명시 DWI 덱 diff 0, 기존 시험 4종 통과
- [ ] KMM 재빌드 + 배포 바이너리 확인
- [ ] SIF v100 + tar + node001 e2e
- [ ] 커밋·push·메모리 갱신
