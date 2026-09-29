# 체크리스트 — `*MAT_*` 키워드/페이로드 불일치 수정

## 조사 (완료)
- [x] `_TITLE` 분기 존재 확인 — `KooMaterial.py:1485`, 정상 동작 재현
- [x] 파괴 재현 — bare 키워드 + 제목 줄 → `Viscoelastic0`·전필드 0·mid 재부여·원 mid 소실
- [x] 무언 손실 4단계 연쇄 확정 (`KooDynaInt`→0, `AddMaterial` 재부여)
- [x] 신고의 "간헐적/경쟁 조건" 반증 — 같은 덱이면 결정적
- [x] 요청 #2 회귀 위험 확인 — `id=0` 자동부여를 팩토리 5곳이 의도적으로 사용
- [x] `AddMatViscoelasticTitle` 인자 뒤바뀜은 죽은 경로 확인 (호출처 0)

## P0 회귀 시험
- [x] `tests/test_mat_title_mismatch.py` 작성 (덱 3종, 16항목)
- [x] 기준선 고정 — 수정 전 C 덱이 `Viscoelastic0`·mid 15 소실 재현
- [x] 정상덱 2종 통과 확인 (A 8항목 · B 4항목)

## P1 MID 선언 기반 검증
- [x] `_GuardMaterialMID` 추가 (+46줄, CRLF 보존)
- [x] 에러 메시지 4요소 포함 — 시험으로 검증
- [x] 파괴덱 → ValueError 중단
- [x] 정상덱 2종 → 동작 불변

## P2 mid 집합 불변식
- [x] `_ReportMaterialMIDInvariant` 추가 (+53줄)
- [x] 참조 소실은 🔴, 미참조 소실은 Info — 중단 안 함
- [x] 실제 덱 **10개**에서 오탐 0 (raw 보존 시험덱 `Test_kmm_preserve` 포함)

## P3 회귀 증명
- [x] DROP `DropSet.k` **바이트 동일** (변경 전/후 동일 옵션파일로 생성). `DropSet.json` 은 `run_id` 한 필드만 다름, 산출물 구성 동일
- [~] IMPACT 덱 미생성 — 대신 `test_thermal_chain`(THERM 포함)·`test_fall_gravity`·`test_layer_split` 통과로 대체. 공유 코드 변경이 재질 파싱 진입부 1곳 + 임포트 후 로그 1곳이라 모드별 방출 경로를 거치지 않는다
- [x] `test_thermal_chain` ALL PASS (THERM 덱 카드 단위 단언)
- [x] 6종 전부 rc=0 — `test_mat_title_mismatch`·`test_layer_split`·`test_fall_gravity`·`test_kooremapper_chain_config`·`test_cli_help`·`test_thermal_chain`

## 마감
- [x] 신고자 회신용 정리 → `회신.md`
- [x] 커밋
