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

## 회귀에서 나온 것(2026-10-26)
- 시험 31종 중 test_encoding_guard 1종 실패 — 7a0b513 의 새 subprocess 세 곳(sphere_tool_flags 의 apptainer … --help, partition_limits 의 scontrol·sinfo)이 `text=True` 만 주고 encoding 을 뺐다. 컴파일본은 utf8_mode=0 이라 한글 도움말에서 UnicodeDecodeError → `except Exception` 이 받아 '옛 도구' 로 보고 순차 자원(130G·2일 반)을 잡았을 것이다 — 조용한 강등. 302b2d4 로 Runner 의 다른 호출과 같은 `encoding='utf-8', errors='replace'` 를 붙였다. 컴파일본 e2e(아래)는 한글 도움말을 내는 가짜 apptainer 로 이 경로를 밟는다.
- MAT_003 _TITLE '모든 판에서 죽음' 확인 — MID 가드(3efb757, 09-29) 이전 판(4fbfe9f)으로도 돌렸다. 짧은 제목·긴 제목(42자) 모두 KooMaterial.AddMaterialfromDyna 의 `firstLine[1]` IndexError 로 죽는다. 그러니 예전 산출물이 조용히 틀린 재질로 나간 적은 없다(죽었을 뿐).
- 이 서버 덱 13,852개(결과 폴더 제외 walk) 중 MAT_003 _TITLE 은 6개 — KooRemapper 예제 사본(assemble_display/mat_all.k) 4, 내 시험 산출 2. 카드 2 생략은 0. 운영 덱은 여기서 볼 수 없다.
- 말뭉치 L 은 진행 중에 155건 동일·0건 다름 — MAT_024 점 입력·MAT_003 _TITLE 이 말뭉치에 없고 part_yield 는 DropSet.json(메타)이라 덱 출력이 안 바뀌는 게 맞다.

## 컴파일본 e2e 설계 — KooChainRun sphere 자원
- 하네스 /data/koopark/Test_E2E_v125/kcr_sphere — 가짜 sbatch·scontrol·sinfo·squeue·apptainer 를 PATH 앞에 두고 컴파일 KooChainRun 으로 979런(피보나치 979) 시나리오를 prepare·submit 한다. 실제 Slurm 에는 아무것도 가지 않는다(가짜 sinfo 가 노드 목록을 비워 SSH 점검도 건너뛴다).
- 판정: 새 도구 16·38G·05:41:00, 옛 도구 2·130G·2-12:45:00, 파티션 한도(2-00:00:00·64000MB) 상한 + 🔴 두 건, 시나리오의 명시값(16G·02:00:00)보다 산출값이 크면 산출값 + 알림, sphere_report.sh 가 Loaded 0 이면 rc 3·3/3 이면 rc 0, 새 도구에만 --parallel-runs 16.
- 아는 불량 먼저 — 빌드 전에 v124 바이너리로 돌려 실패하는지 본다(빌드가 /data/SmartTwinPreprocessor/bin 을 덮으므로 순서가 중요).

## 리뷰 L(2026-10-26) → 수정 묶음 M
리뷰 L 확정 L-1~L-6(L-5 는 bc16e34 로 이미 고침) + 가능성 항목 일부 + 범위 밖 기존 결함. 서버 덱 13,869 스캔으로 빈도를 쟀다.

결정:
- R1 파티션 노드 메모리는 노드별 값(sinfo -N "%c %m")의 최댓값 — `sinfo -o %m` 는 이질 파티션에서 **최솟값+"+"** 다(man sinfo). viz 는 3584+ 인데 18997MB 노드가 있다.
- R2 CPU 도 노드 코어 수로 상한, 새 도구는 W 를 CPU·메모리에 맞게 줄이고 시간·메모리를 W 로 다시 잰다(6+2W ≤ 노드 메모리). 옛 도구는 CPU 만 줄인다(단일 스레드).
- R3 명시 시간 UNLIMITED·INFINITE·0 은 '제한 없음'(man sbatch) — 명시값을 지키되 파티션 MaxTime 이 유한하면 그 한도로(넘으면 영원히 PENDING). 메모리 0 은 '노드 전체' — 지키고 상한 검사에서 뺀다.
- R4 sphere_ncpu 는 int(float()) 로 읽고 못 읽으면 무시+알림 — 예전엔 LS-DYNA 잡을 다 낸 뒤 traceback 으로 submit 이 죽었다.
- R5 --help 탐지는 argparse 옵션 정의 줄로 좁힌다(설명 글 속 언급에 속지 않게) — Python·셸 같은 규칙.
- R6 sbatch 가 SPHERE_SIZED_FOR(parallel|sequential)를 내보내고, 노드 SIF 도구가 옛 판인데 병렬 기준으로 잡혔으면 🔴 경고(헤드·노드 SIF 판 엇갈림 — 지금 Post v41 이 실제로 헤드만 배포된 상태다). 'Loaded N results' 줄이 없으면 경고. yield_map 상대 경로는 생성 시점에 절대 경로로.
- K1 MAT_024 초기 항복 = εp=0 에서의 값 — 커브(LCSS)는 SFA·OFFA 로 가로축, SFO·OFFO 로 세로축을 바꾼 뒤 0 에서 선형 보간/외삽, EPS·ES 도 같은 규칙(R16 EPS1: "If the first point is nonzero, the yield stress is extrapolated", DEFINE_CURVE Remark: 구성식은 외삽). 예전엔 '가장 작은 변형률 점'.
- K2 DEFINE_CURVE 머리 SFA·SFO·OFFA·OFFO 를 >10.3f 로 써 SFO 1e-6 → 0.000 → LS-DYNA 기본값 1.0 → 커브 10⁶ 배(1월부터). 10.3f 가 값을 그대로 담으면 예전 바이트 그대로, 아니면 값을 지키는 가장 짧은 표기(10칸 이내). 서버 덱 1,175 커브 중 20개가 손실(실 덱 uvssoc SFO 0.0316 → 0.032).
- K3 MAT_017 카드 2 는 R16 "Optional card"(SOFT 1.0·CVELO 0.0) — 생략하면 IndexError 였다. 0c6aecf 와 같은 고침.
- K4 MAT_024 카드 3·4 는 칸이 모두 기본값을 가진 카드라 부록 V 상 끝에서 생략할 수 있다. 08-17 가드(29eb785)는 "LS-DYNA 도 다음 키워드를 카드 3 으로 삼킨다" 며 거절했는데 부록 V 와 반대다(키워드 줄이 데이터 카드를 끝낸다). KooRemapper 예제(merge/three_layer.k)가 바로 그 꼴이다. 빈 카드로 채운다.

알리기만(이번에 고치지 않음):
- *DEFINE_COORDINATE_SYSTEM 을 KMM 이 출력에 쓰지 않는다(KooDefineManager 는 커브만 쓴다) — 서버 덱 153 블록, MinimumModel 의 CID 90(항등 축)도 매번 빠지나 참조하는 카드가 없다. 참조가 있으면 LS-DYNA 가 멈춘다(조용하지 않음). 쓰려면 DROP 회전·TRANSFORM 을 좌표계에도 걸어야 한다.
- LONG=S 덱을 rc 0 으로 깨뜨려 쓴다(리뷰 P7_long), MooneyRivlin TITLE 키워드 오타, MAT_017 은 SIGY(항복)를 맵에 쓰지만 파괴는 FS(최대주응력) — 취성 파트 안전율 해석은 사용자 판단, >10.3f 는 다른 모듈에도 184곳(대개 KMM 이 정한 값).

## 수정 묶음 M 회귀(2026-10-26)
- 시험 33종 전부 통과, MinimumModel md5 그대로(ec4c907d·53d24150).
- 말뭉치 M(658965c 대비 715건 — 리뷰 C~K 사례 703 + 리뷰 L 탐침 + 시험 덱): 같음 705, 다름 10 — 전부 바뀐 코드를 밟는 탐침·시험 덱이고 의도한 변화다.
  - 커브 머리 0.001·0.000 → 0.0012·1e-06·4e-04·0.00025.
  - 제목 없는 MAT_024 의 EPS·ES 줄 순서.
  - 옛 판 rc 1 → rc 0: MAT_003 _TITLE·MAT_017 카드 2 생략·MAT_024 카드 생략·P4 13파트 덱.
  - 패딩한 MAT_024 덤프는 빈 선택 카드를 쓰고 알림 한 줄을 남긴다.
- a9 지적(metavar 없으면 argparse 가 'PARALLEL_RUNS' 로 찍는다)은 실측상 탐지된다 — 규칙이 metavar 를 보지 않는다. 시험으로 굳혔다(1633041).
