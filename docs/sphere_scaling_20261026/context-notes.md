<!-- sphere_report 자동화 수정 — 결정과 근거 -->
# 결정 노트 — sphere_report 자동화 (2026-10-26)

## 문서와 코드가 다른 점(대조 결과)
- 자원의 출처: 코드 기본은 8코어·16G·4h 이고, `postprocess.sphere_*` 가 없으면 LS-DYNA 런 환경값(environment.ncpu·memory)을 물려받는다 — 문서의 '8코어·32G' 는 LS-DYNA 런 설정이다. 문서의 6h 는 그 과제 설정으로 보인다(MCP scenario_builder 는 04:00:00 을 넣는다). 문서의 과제 폴더(/data/M3_P2 등)는 이 dev 서버에 없다.
- 캐시 지문은 해시가 아니라 binout·DropSet.k 의 size:mtime_ns(loader.py `_flow_fingerprint`). `_drop.k` 는 지문이 아니라 단위계·종료 시간 판정(`_deck_file`)에 쓰이고, 없으면 첫 런의 .k 로 넘어간다. 샤드 'Loaded 0 results' 의 원인은 `output/` 이 없어 `output/Run_*/DropSet.json` 을 못 읽은 것이다.
- 샤딩해도 마지막 합치기의 메모리는 줄지 않는다 — 모든 런의 흐름 dict 를 메모리에 다 든다(energy_flows). 979런 84.7 GB 는 그 단계다. 그래서 메모리 산출(①)은 병렬화(③)와 별개로 필요하다.
- 운영 클러스터의 파티션 한도(MaxTime·노드 메모리)는 여기서 볼 수 없다 — 제출 때 scontrol·sinfo 로 읽어 상한을 건다.

## 결정
- 샤딩(심볼릭 샤드 폴더 + 잡 여러 개) 대신 도구 안 병렬(`--parallel-runs`, koo_impact_report 와 같은 방식)을 고른다 — 샤드 폴더 구성을 빠뜨리면 조용히 0건이 되는 함정이 원천적으로 없고, 잡이 하나다. 노드 하나로 모자랄 만큼 커지면 그때 캐시 채우기 샤드 모드를 더한다.
- 명시값(`postprocess.sphere_*`)이 산출값보다 작으면 산출값을 쓰고 알린다 — MCP 가 모든 캠페인에 sphere_time_limit 04:00:00 을 넣어, '명시값 우선' 이면 고침이 MCP 캠페인에 먹지 않는다. 그대로 쓰려면 `postprocess.sphere_auto_resources: false`.
- 도구 옵션 지원 여부는 실행 시점(sphere_report.sh)과 제출 시점(sbatch 자원) 둘 다 SIF 의 --help 로 본다 — 옛 SIF 면 병렬을 가정하지 않는다(CPU 2·순차 시간).
- 항복응력 맵은 KMM 이 만든다 — KMM 이 이미 MAT_003·MAT_024·ORIENTED_CRACK 의 SIGY 와 파트-재질 연결, 커브를 고정폭·I10·파라미터까지 읽는다. 도구가 split() 으로 덱을 다시 읽는 것보다 튼튼하다. R16 MAT_024: "SIGY … ignored if LCSS > 0" → LCSS 커브면 첫 점 응력 × SFO + OFFO, 표(TABLE)면 맵에서 뺀다(기본값).
- (a9 반대·대안 수용) 도구 병렬화만으로는 84.7 GB 가 안 준다 — 정점은 캐시 만들기가 아니라 loader.py 가 모든 런의 흐름을 energy_flows 에 끝까지 드는 것이다(0.087 GB × 979 = 85.2 GB). 흐름 시계열이 필요한 곳은 상위 60개(_FLOW_DETAIL_LIMIT)뿐이고 나머지 소비처는 스칼라라, 1패스(병렬)는 캐시를 쓰고 스칼라만 남기고, 2패스는 상위 60개만 캐시에서 다시 읽는다 — 예상 정점 5~6 GB + 워커분. 그래서 자동화의 메모리 산식은 도구 판으로 갈린다 — 새 도구(--parallel-runs 있음) 6 GB + W × 워커 RSS(실측 전 2 GB), 옛 도구 32 + 0.10 × N GB.
