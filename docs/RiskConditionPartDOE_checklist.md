# 취약조건 × 파트이동 DOE — 체크리스트

계획: [PLAN_RiskConditionPartDOE.md](PLAN_RiskConditionPartDOE.md)

## Phase 0 — 포맷 확정
- [x] 코드 구조 조사 (KMM 다중 *Mode, 누적 dti 승계, AdaptiveOrientation 재사용 가능)
- [x] 포맷 사용자 승인 (2026-08-05)

## Phase 1 — 조건 열거 (각도/위치)
- [x] `AngleSourceType.EXPLICIT` + `ExplicitAnglesConfig` 추가
- [x] `parse_explicit_angles()` — inline `angles` / `file` 양자택일, 동시 지정 시 에러
- [x] `CumulativeDesigner._parse_angle_source()` 에 explicit 분기 배선
- [x] `parse_manual()` dict 형식 + `file` 수용, 배열 하위호환 유지
- [x] 검증: 기존 `[[x,y],...]` 시나리오 회귀 0

## Phase 2 — 파트이동 축
- [x] `Runner/PartMoveDOE.py` 신규 — `PartMoveCase`, `parse_part_doe()`
- [x] lhs / grid / explicit 3종 샘플링
- [x] pid 미존재·범위 역전·빈 parts 검증 에러
- [x] 단위 테스트: 샘플 수·seed 재현성·생략축 0.0

## Phase 3 — Designer 결합
- [x] 조건×이동 곱 (`doe_index = cond_idx * n_moves + move_idx`)
- [x] condition 이름 `{조건}__{이동}` 생성
- [x] `doe_part_moves` 카탈로그 방출 (`apply_step` 키만)
- [x] 총 케이스 수 로그 (tolerance 병용 시 3중곱 경고)
- [x] 🔴 검증: `part_doe` 없는 scenario → runner_config 바이트 동일

## Phase 4 — KMM `PART_TRANSLATE`
- [x] 파서 등록 (`part_translate` → modeList)
- [x] 디스패치 (`GeneratePartTranslate`)
- [x] `KooDynaAdvancedModification.PartTranslate()` 본체 — 적용 후 원복 없음
- [x] 검증: 이동만 단독 실행 → 노드 좌표 diff 확인
- [x] 검증: `PART_TRANSLATE` + `DROP_ATTITUDE` 체이닝 단일 .k

## Phase 5 — Runner 배선
- [x] `_get_doe_part_moves(doe_index, step_num)`
- [x] DROP 옵션 txt 에 블록 삽입 (모드 번호 재배치)
- [x] IMPACT 옵션 txt 에 블록 삽입
- [x] 검증: 누적 2스텝 — step1 만 이동

## Phase 6 — harvest 커맨드
- [x] `KooChainRun harvest` 서브커맨드
- [x] DROP/IMPACT 자동 판별
- [x] `--top` / `--hot-only` / `--z-thr` / `--yield-factor`
- [x] 출력 JSON → `explicit.file` / `manual.file` 왕복 e2e

## Phase 7 — 배포
- [x] 회귀 스위트 전체 통과
- [x] 매뉴얼 `doe_methods.md` 갱신
- [x] 커밋 (ef89f9c~affa4fe, 7건)
- [x] 🔴 모듈빌드 → SIF 소스트리 → SIF → tar v84 → node001 (2026-08-11)
- [x] 🔴 호스트 배포(/data·/opt) 복구 — glibc 가드가 빌드를 컨테이너 안에서
      재실행해 sudo 부재로 v81 이후 계속 실패하던 것. 컨테이너 밖에서 메움
- [x] 빌드 스크립트 근본 수정 — 배포 단계를 glibc 가드 밖으로 분리 (bb685e9, v87 까지 실전 검증)
- [x] harvest --yield / --yield-by-part (9bdddf1)
- [ ] 실클러스터 e2e (실제 잡 제출) — 사용자 실행 필요
- [ ] 물성 파일 경로 확인 → tools/fix_mat_plasticity_cards.py 적용 (사용자 제공 필요)
- [ ] M3 실덱 확인 — 합성 재현으로만 검증됨 (사용자 제공 필요)
- [ ] 중복 tar v83 정리 (root 소유, 사용자 승인 필요)
