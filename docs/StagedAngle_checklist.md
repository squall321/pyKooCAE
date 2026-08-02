# Staged 각도 샘플링 체크리스트

## 조사·설계
- [x] 기존 `parse_fibonacci_lattice` / `_physical_lattice` 구조 파악
- [x] 단계 간 중첩 성립 여부 실측 → 0/120 (중첩 없음 확인)
- [x] 결정론 확인 (같은 설정 2회 동일)
- [x] 누적 품질 실측 (120→500, 120→500→1000)
- [x] 제거 알고리즘 2종 비교 → prev별 최근접 채택
- [x] 개수 규약 확정 (num_points = 최종 누적 총량)
- [x] PLAN 문서 작성

## 구현
- [x] `FibonacciLatticeConfig.previous_stages` 필드 추가
- [x] `_angular_remove_nearest()` 헬퍼 추가
- [x] `parse_fibonacci_lattice` staged 분기
- [x] 입력 검증 (오름차순·양수·num_points 미만)
- [x] `CumulativeDesigner._parse_angle_source` 배선

## 검증
- [x] 회귀 0 — `previous_stages` 미설정 시 기존 출력 바이트 동일
- [x] 방출 개수 == num_points - previous_stages[-1]
- [x] 누적 중복 0 (0.1° 이내)
- [x] 결정론 — 2회 실행 동일
- [x] 단계 경로 일관성 — 신규분이 이전 누적과 교집합 0
- [x] 잘못된 입력이 명확히 거부되는지
- [x] scenario.json → prepare e2e

## 배포
- [ ] 커밋
- [ ] KooChainRun 빌드
- [ ] SIF 소스 트리 갱신 (`appt313/opt/SmartTwinPreprocessor`) ← 빼먹기 쉬움
- [ ] SIF + tar
- [ ] node001 배포
