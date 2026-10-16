<!-- KooChainRun 자동 후처리에 핫스팟 고도화(기준 7종·시간 집계·전각도 파트 필터)를 잇는 계획 -->
# 계획 — 핫스팟 고도화를 자동 후처리·MCP 까지 잇기 (2026-10-16)

## 왜
KooD3plotReader 엔진(`unified_analyzer`)은 9월에 기준 7종·시간 집계·전각도 수집을 갖췄는데, 배포본에서
- `koo_deep_report` 가 새 기준 4종을 거절하고 시간 집계를 넘기지 않는다(실측 rc=1) → KooD3plotReader 쪽
- KooChainRun 자동 후처리는 기준 3종만 받고, 전각도 파트 필터(`--hotspot-part`)를 안 넘긴다 → 이 리포
- KooChainRun 도움말에 `hotspot_*` 키가 없어 MCP 시나리오 도구 설명에도 없다 → 이 리포·MCP

## 무엇을 (사용자 결정 2026-10-16 — 1~4 전부, KooD3plotReader 쪽은 그쪽 세션에 요청)
1. 기준 7종·시간 집계 — KooD3plotReader 가 `koo_deep_report` 를 고친 **뒤에** KooChainRun 키 배선(먼저 넣으면 deep 이 거절해 자동 후처리가 깨진다)
2. `postprocess.hotspot_part` → `koo_sphere_report --hotspot-part` (sphere 는 이미 지원)
3. 도움말(`postprocess_json` 주제·DROP 키)에 `hotspot_*` 문서화 → MCP 시나리오 도구 재생성
4. 3D 인벨롭 — KooD3plotReader 쪽 구현(요청서 §2), 새 CLI 옵션이 생기면 키로 잇는다

요청서: `KooD3plotReader: docs/requests/hotspot-wiring-request-2026-10-16.md`

## 순서
2·3 지금 → KooD3plotReader §1 배포 알림 → 1 → 빌드·SIF·tar·노드 → MCP 재생성 → 배포본 e2e(핫스팟 켠 캠페인 후처리)
무거운 빌드는 KooD3plotReader Post SIF 빌드와 겹치지 않게 한 번에 하나.
