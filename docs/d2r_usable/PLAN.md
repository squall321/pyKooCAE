# D2R 실사용 가능하게 만들기 + DR 기반 전각도 낙하 점검 (2026-10-06)

## 배경

현장 문서 `deformable_to_rigid 적용 난점 정리 v1.0` 이 "현재 툴체인에서 D2R은 쓸 수 없다"
고 결론했다. 검토해 보니 결론의 **원인 귀속이 틀렸고**, v109 에서 이미 상당 부분이 열렸다.

## 실측으로 확정한 것 (2026-10-06)

원본 GENERAL 을 `FS=0.20 FD=0.15 VDC=30.0 | SOFT=1 MAXPAR=0.000 SBOPT=2 DEPTH=0 BSORT=0`
으로 박아 4케이스를 돌려 필드별 상속 여부를 가렸다.

| 케이스 | 바닥판 FS/FD/VDC | SOFT | SBOPT | DEPTH | MAXPAR | BSORT |
|---|---|---|---|---|---|---|
| 원본 GENERAL | 0.20/0.15/30.0 | 1 | 2 | 0 | 0.000 | 0 |
| `SS_plain` (현 상태) | 0.3/0.2/10.0 🔴 | 2 🔴 | 3 🔴 | 35 🔴 | 1.025 🔴 | 100 🔴 |
| `SS_inherit` | 0.2/0.15/30.0 ✓ | 2 🔴 | 3 🔴 | 35 🔴 | 1.025 🔴 | 100 🔴 |
| `GEN_plain` | 0.2/0.15/30.0 ✓ | 1 ✓ | 0 ✓ | 0 ✓ | 1.025 🔴 | 100 🔴 |
| `GEN_inherit` | 동일 | ✓ | ✓ | ✓ | 🔴 | 🔴 |

🔴 **결론: `convert_general_to_single_surface: false` 하나로 문서 §5 가 거의 해소된다.**
남는 불일치는 `MAXPAR`·`BSORT` 둘뿐이고, 이는 쪼개짐이 아니라 **양 경로 공통 기본값**
(`opt_MAXPAR=1.025`, `opt_BSORT=100`)이 입력 덱 값을 덮어쓰는 것이다 — OptCardA 는
어느 경로에서도 상속되지 않는다.

내부 SS 는 이미 FS/FD/VDC 를 상속한다 → 문서 §5 의 FS/FD/VDC 항목은 **바닥판 S2S 에만** 해당.
문서도 `(S2S)` 로 표기해 정확했다.

## 문서 주장별 판정

| # | 주장 | 판정 |
|---|---|---|
| 1 | `include_wall_in_general: true` 면 D2R 0장 | **맞다** (`dropContactCID = None`) |
| 2 | 카드 만들면 전역 접촉이 쪼개진다 | **원인 오귀속** — `convert_general_to_single_surface`(기본 true) 때문 |
| 3 | 중복계산 아니다 | **맞다**. 구조적 근거 추가: 내부 `MSID=0/MSTYP=0` 단면, 바닥판 `MSTYP=3` 양면 |
| 4 | SOFT·VDC·MAXPAR·SBOPT·DEPTH·BSORT 전부 바뀐다 | **부분 수정** — 위 표. GEN 경로면 MAXPAR·BSORT 만 |
| 5 | beam/shell-edge 접촉 사라진다 | **맞다, 단 회피 가능** — GEN 유지하면 발생 안 함 |
| 6 | `time3=0` 채터 | **맞다**. v109 부터 `D2RTime3` 로 설정 가능 |
| 7 | 채터 막으면 발산 | **전제 확인 필요** — v109 이전 writer 가 0.05 미만을 0.0 으로 기록 |
| 8 | 카드 의미가 반대 | **코드 의도와 상충** — 재현 필요 |
| 9 | `MRB=0` + CNRB → Error 30164 | 선행 기록, 미재현 |

## 단계

### P1 OptCardA 상속 (요청 ④)
`MAXPAR`·`BSORT`·`SOFT`·`SBOPT`·`DEPTH`·`SOFSCL`·`FRCFRQ`·`LCIDAB` 을
`InheritGeneral` 대상에 추가. 🔴 `robust_contact` 의 `SOFT=2`·`DEPTH=3` 강제
(`:2519-2520`)와 충돌하므로 **robust_contact 가 켜져 있으면 강제값 우선**으로 가드.
- 검증: 4케이스 전부 OptCardA 까지 원본 GENERAL 값, robust_contact 켠 케이스는 2/3 유지,
  기본 경로 덱 바이트 동일

### P2 D2R 사용 가이드 (요청 ②)
게이트 3개(`include_wall_in_general`·`drop_surface.type=RigidWall`·`convertToSS`)와
v109 옵션 전체, 검증 절상을 `docs/d2r_usable/USAGE.md` 로.

### P3 DR 기반 전각도 낙하 점검 (신규 요청)
DR 로 안정화한 모델을 기준으로 전각도 낙하가 되는지 확인.
- DR 배선: `simulation_params.dynamic_relaxation` → `DynainDynamicRelaxation*` 4줄
  (`StepConfigBuilder.py:11-37`). DROP/IMPACT 공용
- 점검 항목
  1. DR 스텝 산출물(`dynain`)이 다음 스텝 입력으로 이월되는가 (`DYNAIN_TO_INITIAL`)
  2. 이월된 `_dti.k` 를 **새 자세로 회전**할 때 초기응력이 함께 회전하는가
  3. 각도 DOE × DR 조합에서 각 DOE 가 독립 DR 을 받는가, 아니면 1회만 받는가
  4. DR + D2R 동시 사용 시 충돌 여부
- 🔴 2번이 핵심 위험이다. `*INITIAL_STRESS_SOLID` 는 전역 좌표계 텐서라
  자세 회전 시 변환이 필요하다. 누락되면 조용히 틀린 초기응력으로 해석한다

### P4 회귀·빌드
기존 스위트 + 신규, 기본 경로 바이트 동일, KMM 재빌드 → e2e → SIF → 메일

## 진행 현황 (2026-10-06)

| 단계 | 상태 |
|---|---|
| P1 OptCardA 상속 | ✅ 구현. 4케이스 + robust 케이스 실측. 기본 경로 바이트 동일. SS 변환 리터럴 `0, 1.025` → `LCIDAB_opt, MAXPAR_opt` 변수화(아니면 SS 쪽 상속이 무언 no-op). 실수 필드는 원문 표기 보존, 정수만 int |
| P2 USAGE.md | ✅ `docs/d2r_usable/USAGE.md` — 게이트 3개·접촉 구성·우선순위·세부필드·트리거 범위·카드 의미·검증 절상·DR 관계 |
| P3 DR 전각도 점검 | ✅ 모델 절점 0개 회전(바닥판만) → 초기응력 텐서 회전 불필요. DR·D2R 독립 |
| P4 회귀·빌드 | 🔄 시험 통과 후 커밋 → KMM 재빌드 → e2e → SIF → 메일 |

### 부수 발견 (범위 밖, 기록)
- robust_contact 의 `DEPTH=3` 강제가 **바닥판 S2S 에는 한 번도 적용된 적이 없다** — `opt_*` 계열만
  강제하고 바닥판은 지역변수를 쓴다. 수정 전부터의 공백. robust 의도가 "전 접촉" 이면 별건 수정 필요.
- 현장 §8(V0/V1/V2)은 v109 이전 writer 가 0.05 미만을 0.0 으로 기록한 버전이라 전제 확인 필요.
  덱이 이 머신에 없어(`/data/koopark/d2rt_out` 부재) 확인 명령만 전달.
- 현장 §9 #8(카드 의미 반대)은 코드 의도(비행 중 강체)와 상충 — 재현 필요.
