# 컨텍스트 노트 — D2R 실사용 + DR 전각도 점검 (2026-10-06)

## 현장 문서의 원인 오귀속
"IncludeWallInGeneral=False 로 바꾸면 전역 접촉이 쪼개진다" → 쪼개는 것은
`convert_general_to_single_surface`(기본 true). 4케이스 실측으로 확정.
GEN 유지(`false`)만으로 FS·FD·VDC·SOFT·SBOPT·DEPTH 가 원본과 일치하고 beam 접촉도 유지된다.
남는 것은 MAXPAR·BSORT — 양 경로 공통 기본값(1.025/100)이 입력 덱을 덮는 것.
→ OptCardA 상속(이번 구현)으로 해소.

## OptCardA 는 어느 경로에서도 상속되지 않았다
SINGLE_SURFACE 변환이 OptCard B~F 는 `if contact_g.OptCardB:` 로 보존하면서 **A 만 예외**.
SS 변환의 `SetOptCardA(SOFT_opt, SOFSCL_opt, 0, 1.025, ...)` 는 LCIDAB·MAXPAR 가 **리터럴**이라
변수로 바꾸지 않으면 상속해도 SS 쪽엔 효과가 없었다(무언 no-op 함정) → `LCIDAB_opt`·`MAXPAR_opt` 신설.

## robust_contact 우선 — 사용자 결정
`robust_contact` 의 SOFT=2·DEPTH=3 강제는 segfault·관통 방지 의도라 상속보다 우선.
구현: 상속 블록이 robust 시 SOFT·DEPTH 를 `_inh_a` 에 넣지 않음 + 강제 블록이 뒤에서 덮음.

## 🔴 발견 — robust_contact 강제가 바닥판 S2S 에는 한 번도 걸린 적이 없다
`opt_SOFT=2; opt_DEPTH=3` 는 `opt_*` 계열(내부 SS 교체·GEN 경로)에만 적용된다.
바닥판 S2S 는 자기 지역변수(`SOFT = drop_contact.get("SOFT", 2)` 등)를 쓰므로
**robust 를 켜도 DEPTH=35 그대로**다(SOFT 는 기본값이 2 라 우연히 일치).
수정 전부터의 공백이고 이번 변경과 무관 → 범위 밖. robust 의도가 "전 접촉" 이면 별건으로 고쳐야 한다.

## 상속값은 10칸 패딩 문자열로 들어온다
`_general_snapshot.OptCardA` 의 원소가 덱에서 읽힌 경우 `'     0.100'` 같은 문자열이다.
`format(x, ">10")` 출력엔 문제없지만 하류 산술에서 깨지므로 `float()`/`int(float())` 로 정리.
정수 필드는 `'2.0'` 표기도 받는다([[project-a27-solid-2card-loss]] 의 KooDynaInt 교훈).

## DR 기반 전각도 낙하 — 초기응력 회전 불필요 (실측)
`DropAttitude` 는 모델을 회전시키지 않고 바닥판 법선·속도·각속도를 **역회전**시킨다.
자세 (0,0) vs (45,30): 모델 절점 8개 좌표 0개 변경, 바닥판 절점 2883개 변경.
→ `*INITIAL_STRESS_SOLID` 는 전역 좌표 텐서 그대로 전 자세에 유효. DR·D2R 은 서로 독립.

### 🔴 내 오판 — 파싱 오류로 결론을 한 번 뒤집었다
처음 코드 주석(`inverse rotation for plane normal`)으로 "모델 고정" 이라 판단 → 실측에서
"절점 2891개 중 md5 다름" 을 보고 "회전된다" 로 뒤집음 → 절점 ID 를 **8칸**으로 읽어 29개만
잡은 파싱 오류였음. **10칸**으로 바로잡으니 모델 절점은 완전 동일.
교훈: 실측이 추론과 어긋나면 **실측 도구부터** 의심한다. NODE 는 10칸 ID 다([[project-i10-full-io]]).

## 현장 문서 §8 (V0/V1/V2) 전제 확인 필요
v109 이전 writer 가 time1/time3/dtmax/offset 을 `%10.1f` 로 써서 0.05 미만이 0.0 으로 기록됐다.
V0(TIME3=1e-3)·V1(2e-3/5e-3)·V2(3e-3/1e-2) 를 그 경로로 썼다면 **전부 0.0** 이 되어 세 케이스가
동일해지는데 전환 횟수가 달랐으므로 d2rfix.py 로 직접 패치했을 가능성이 크다.
덱이 이 머신에 없어(`/data/koopark/d2rt_out` 부재) 확인 못 함 — 현장에 확인 명령 전달.

## 현장 문서 §9 #8 (카드 의미 반대) — 코드 의도와 상충
생성 카드는 SWSET20/code4/relsw10 (접촉력→0 시 D→R) + SWSET10/code2/relsw20 (접촉력 발생 시 R→D)
= **비행 중 강체** 가 의도. 현장 관측이 반대라면 code/relsw 값이 틀렸다는 뜻이라 재현 필요.
