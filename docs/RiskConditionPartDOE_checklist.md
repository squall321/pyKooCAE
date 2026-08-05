# 취약조건 × 파트이동 DOE — 체크리스트

계획: [PLAN_RiskConditionPartDOE.md](PLAN_RiskConditionPartDOE.md)

## Phase 0 — 포맷 확정
- [x] 코드 구조 조사 (KMM 다중 *Mode, 누적 dti 승계, AdaptiveOrientation 재사용 가능)
- [ ] 포맷 사용자 승인

## Phase 1 — 조건 열거 (각도/위치)
- [ ] `AngleSourceType.EXPLICIT` + `ExplicitAnglesConfig` 추가
- [ ] `parse_explicit_angles()` — inline `angles` / `file` 양자택일, 동시 지정 시 에러
- [ ] `CumulativeDesigner._parse_angle_source()` 에 explicit 분기 배선
- [ ] `parse_manual()` dict 형식 + `file` 수용, 배열 하위호환 유지
- [ ] 검증: 기존 `[[x,y],...]` 시나리오 회귀 0

## Phase 2 — 파트이동 축
- [ ] `Runner/PartMoveDOE.py` 신규 — `PartMoveCase`, `parse_part_doe()`
- [ ] lhs / grid / explicit 3종 샘플링
- [ ] pid 미존재·범위 역전·빈 parts 검증 에러
- [ ] 단위 테스트: 샘플 수·seed 재현성·생략축 0.0

## Phase 3 — Designer 결합
- [ ] 조건×이동 곱 (`doe_index = cond_idx * n_moves + move_idx`)
- [ ] condition 이름 `{조건}__{이동}` 생성
- [ ] `doe_part_moves` 카탈로그 방출 (`apply_step` 키만)
- [ ] 총 케이스 수 로그 (tolerance 병용 시 3중곱 경고)
- [ ] 🔴 검증: `part_doe` 없는 scenario → runner_config 바이트 동일

## Phase 4 — KMM `PART_TRANSLATE`
- [ ] 파서 등록 (`part_translate` → modeList)
- [ ] 디스패치 (`GeneratePartTranslate`)
- [ ] `KooDynaAdvancedModification.PartTranslate()` 본체 — 적용 후 원복 없음
- [ ] 검증: 이동만 단독 실행 → 노드 좌표 diff 확인
- [ ] 검증: `PART_TRANSLATE` + `DROP_ATTITUDE` 체이닝 단일 .k

## Phase 5 — Runner 배선
- [ ] `_get_doe_part_moves(doe_index, step_num)`
- [ ] DROP 옵션 txt 에 블록 삽입 (모드 번호 재배치)
- [ ] IMPACT 옵션 txt 에 블록 삽입
- [ ] 검증: 누적 2스텝 — step1 만 이동

## Phase 6 — harvest 커맨드
- [ ] `KooChainRun harvest` 서브커맨드
- [ ] DROP/IMPACT 자동 판별
- [ ] `--top` / `--hot-only` / `--z-thr` / `--yield-factor`
- [ ] 출력 JSON → `explicit.file` / `manual.file` 왕복 e2e

## Phase 7 — 배포
- [ ] 회귀 스위트 전체 통과
- [ ] 매뉴얼 `doe_methods.md` 갱신
- [ ] 커밋
- [ ] 🔴 모듈빌드 → SIF 소스트리 갱신 → SIF → tar → 노드배포
</content>
</invoke>
