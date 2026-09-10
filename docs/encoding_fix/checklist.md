# ascii 사고 수정 — 체크리스트

계획: [PLAN.md](PLAN.md) · 노트: [context-notes.md](context-notes.md)

## 0. 원인 규명
- [x] 인터프리터로는 재현 불가 확인 (PEP 540 자동 UTF-8 모드)
- [x] Nuitka 프로브 컴파일 → `utf8_mode=0` 실측
- [x] 보고서와 동일 문구의 `UnicodeDecodeError` 재현
- [x] 기존 stdio 래핑(17–23행)이 왜 무력한지 규명
- [x] `setlocale` 벨트가 미수정 호출부를 덮는지 실측
- [x] `getfilesystemencoding` 은 안 덮인다 → D3 등급 정정 근거

## 1. 1층 벨트
- [x] `Runner/_encoding.py` 신규 — `enforce_utf8_runtime()` + 셸 전문 상수
- [x] `KooChainRun` 진입점 배선 (기존 17–23행 대체)
- [x] `CumulativeScenarioRunner` / `LargeScaleDOEManager` `__main__` 배선
- [x] 컴파일 프로브로 `env -i` 통과 증명

## 2. D1 — subprocess (44지점)
- [x] 자동 수정 + AST 재스캔으로 잔여 0 증명
- [x] `text=False`(bytes) 5지점은 손대지 않음 확인

## 3. D2 — 로그 스트림
- [x] `logging.FileHandler(..., encoding='utf-8')`
- [x] 확장: text-mode `open()` 47지점

## 4. D3 — 제출 환경
- [x] 생성 셸 스크립트 14지점에 로케일 전문
- [x] `environment.job_env` 스키마 필드

## 5. D4 — 결정적 실패 즉시 중단
- [x] Unicode*/FileNotFound/PermissionError 재시도 제외

## 6. D5 — 락
- [x] `_flock_with_timeout` fd 수명 (Errno 9)
- [x] 락 없는 폴백 제거

## 7. 마감
- [x] 회귀 테스트 (기존 스위트 — hotspot 12체크 통과)
- [x] 신규 회귀 테스트 `tests/test_encoding_guard.py` (35체크)
- [x] 커밋 (의미 단위 분할)
- [x] 빌드 → 배포 바이너리 e2e (잡 1137~1140, D1·D2 경로 실증)
- [x] 🔴 KooChainRun 자체 템플릿 8곳 누락 발견·수정 (run_doe_NNN.sh 포함)
- [ ] SIF 갱신 → node001 배포
