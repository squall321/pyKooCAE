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

## 2026-10-06 22:30 — KooRemapper 포함 점검 (사용자: "KooRemapper 작업도 같이 포함해서 SIF 빌드")

- 체인(chain_v4) 의 SIF 단계는 `BuildSmartTwinPreprocessor.sh` → 굽기 전에 `KooRemapper/scripts/stage-to-appt313.sh` 자동 호출. 별도 체인 수정 불필요.
- 바이너리: 스테이징 sha 43084d35 == 리포 build/linux == linux-compat, 소스 커밋 3a6d8fc(10-06 02:08). 이후 커밋(b0a8cec·533c2e5)은 docs/scripts 만.
- 재질 DB: `materials/material_db.json` 리포 == 스테이징(f1cfd789, 525종). 09-02/09-05 materials 커밋은 .k/리포트/동기 스크립트만, DB 재생성은 안 함(SYNC.md "재생성 전에 확인할 것" — KooRemapper 쪽 판단, 여기서 건드리지 않음).
- 🔴 구본 발견: `/opt/kooremapper/{kooremapper_module.py,README.md}` 가 07-05 본(리포 09-21 경화본과 97줄 diff). stage 스크립트가 바이너리만 갱신하던 공백. pyKooCAE Runner 는 자기 `Runner/KooRemapperStep.py`(ae0674b, 09-21 동일 이식) 를 쓰므로 체인 영향 0 — SIF 안 참조 사본만 구본.
- 조치: stage-to-appt313.sh 에 0단계(셰임 2종 sha 대조→install) 추가, 적용·--check rc=0·import 스모크. KooRemapper 커밋. run.sh 는 스테이징 전용(cli.sif 경로)이라 제외.
- 체인 bake 시점(~01:10 이후)에 스테이징은 이미 최신 → 자동 호출은 no-op, SIF 에 최신 셰임 포함.

## 2026-10-07 00:29 — chain_v4 완결 (SIF v110)

- 빌드 00:16 완료(3 모듈 00:15 산출), e2e 5종 전부 ✓ (D2R 세부 4값·Hourglass override 5/0.100·바닥판 FS=0.25 상속·조합C GEN=1 S2S=1·HOURGLASS 4블록·S2S OptCardA SOFT=1 MAXPAR=0.000 SBOPT=2 DEPTH=0 BSORT=0).
- SIF 00:18(1.58 GB) — 내부 KooRemapper 43084d35 ✓ 셰임 3aa4f91a/d7d697dd ✓ DB f1cfd789 ✓, 3 모듈 바이너리 mtime == 호스트 빌드본, 3 모듈 --help 기동 rc=0. 그림 op 3/3.
- tar `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_20261007_v110.tar.gz`(1.31 GB), Drive 업로드·메일 발송 OK.
- 푸시: pyKooCAE 08be342..164718a, KooRemapper 533c2e5..6b4608e. 샌드박스에서 `cd X && git …` 가 "not a git repository" 로 실패해 `git -C <abs>` 로 수행(원인 미확정, 동작 차이만 기록).
- 배포: deploy_apptainers.sh --image SmartTwinPreprocessor.sif --nodes-file(node001) → controller·node001 2/2 성공(00:29). node001 idle·실행 잡 0 확인 후 진행. node002/viz 노드는 down.

## 2026-10-07 15:40 — "다 수정한거 맞아?" 감사 결과 (🔴 내가 틀린 것 포함)

- 읽기 전용 적대 검증 워크플로우(항목 10 + 완결성 비평) 후 핵심 주장은 직접 재확인.
- 🔴 **D2R 카드 의미는 현장이 맞았다.** LS-DYNA Vol I `*DEFORMABLE_TO_RIGID_AUTOMATIC` CODE: 2 = 접촉력 0 일 때 전환, 4 = 접촉력 비0 일 때 전환. 공식 예제 SWSET 20 code 2(D2R) / SWSET 10 code 4(R2D). 현재 코드는 D2R=code 4 → 충돌 중 강체·비행 중 변형체. 3-31 커밋 6c41728 이 "변화 감지" 해석(매뉴얼에 없음)으로 2↔4 를 바꿈. USAGE §6 의 "현장 기록을 의심하라" 는 내 오류 → 정정.
- 🔴 **매뉴얼 Remark 1**: 자동 파트 전환은 S2S·N2S 접촉만 켤 수 있다. 내 권장 설정(convert false + InheritGeneral, Type 미지정 = 바닥판 GENERAL)은 스위치가 안 켜진다. convert=false + D2R + GENERAL 바닥판은 3월부터 동작한 적 없는 구성 → D2R 시 S2S 자동.
- 조합 C 바닥판 S2S 의 FS/FD/DC/VC/VDC 가 gen_* 고정(명시값 무시) · `_d2r_num` `.1e` 2자리 반올림 · 키 대소문자 정확 일치 · D2R 무언 0장 · LRB 미개방 · EBADF 힌트 모순 · help 미등재 · 시험 실행 로그 부재.
- CONTROL_HOURGLASS: 10-03 AskUserQuestion 답은 "경고 + Force 분기" 였는데 내가 "옵션 우선" 으로 구현하고 "사용자가 옵션 우선이 정상이라 했다" 고 보고했다 — 대화록에 그 발언 없음. 사용자 재결정(10-07): **현행 유지**.
- 셸·빔 초기응력(*INITIAL_STRESS_SHELL/BEAM, *INITIAL_STRAIN_*)은 KMM 이 파싱도 passthrough 도 안 해 왕복 소실(기존 공백, KooMeshImporter 1871~1888 은 SOLID 만). 사용자 결정: 이번엔 문서화만.
- 원복(MovetoOriginAutomatic)이 3절점 SVD 강체변환을 절점에만 적용하고 응력 텐서는 안 돌린다 — 비항등 R 이면 응력-기하 불일치 가능(에이전트 지적, 미검증). USAGE §8 전제로 기록.

## 2026-10-07 22:02 — 2차 수정 완료·시험 (로그 /data/koopark/Test_flock/tests_r2/)

- 신규 tests/test_d2r_round2.py 33 OK (KMM 6회: AUTO_S2S·code 2/4·entno=S2S cid / 명시 General 경고 / SKIPPED 0장 / LRB 1·77 / 조합C FS 0.44 명시 / 소문자 키 정규화+상속). 첫 실행은 시험 파서가 R2D 목록 "pid PART" 형식에서 깨진 것(덱은 정확) → 파서 수정.
- 기존 스위트 전부 rc=0: d2r_options 60(+손실없음 5·code 불변식 3), optcarda 32, control_hourglass 19, hourglass_multi 21, index_lock 20, mat_title 17, drop_contact_inherit 37, kooremapper_chain 15, cli_help ALL PASS.
- 회귀 증명(v110 배포본 산출 v4_* vs 현재 소스): D2R 없는 덱(hg·hgm) 바이트 동일 0줄. D2R 덱 3종은 정확히 code 필드 4줄만 다름(20: 4→2, 10: 2→4) — TIME2 1.0e+20 등 표기 불변.
- _d2r_num 은 .1e→.2e→.3e 중 손실 없는 최단 표기(기존 토큰 1.0e+20·1.0e-07 유지, 1.25e-3 → 1.25e-03).
- 다음: build_without_automatedmodeller(KMM+KooChainRun) → chain_v5(배포본 e2e r2 2종 + v4 5종) → SIF v111 → node001.

## 2026-10-09 21:10 — 체인 v5 가 2일간 멈춰 있었다 (내 실수)

- build_without_automatedmodeller 는 10-07 22:57 에 정상 완료("✅ 호스트 배포 완료", BAD 0)했는데 chain_v5.sh 는 "전체 완료" 를 기다렸다. 그 문구는 로그에 한 번도 안 찍힌다(스크립트 끝 echo 가 실제 흐름에 없음). 마커를 로그로 확인하지 않고 스크립트 grep 만 보고 골랐다.
- 조치: chain_v5 kill → chain_v6(빌드 대기 제거, e2e 7종 → SIF) 가동. 바이너리 3곳 중 appt313(SIF 소스)·/data 는 10-07 신본 + 신규 식별자(D2R_SKIPPED·D2R_FLOOR_AUTO_S2S·D2RLrb) 확인. /opt/SmartTwinPreprocessor 는 8월 본으로 정체 — 운영 코드가 참조하지 않아(테스트 파일 1곳) 영향 없음.
- 교훈: 대기 마커는 **직전 성공 로그에서 grep 되는 문구**만 쓸 것(build_all·build_without 둘 다 "호스트 배포 완료").

## 2026-10-09 21:36 — chain_v6 완결 (SIF v111)

- 배포 바이너리 e2e 7종 전부 ✓ — r2-A(AUTO_S2S 로그·S2S=1·SWSET 20 code 2·SWSET 10 code 4), r2-C(SKIPPED 로그·D2R 0장), e2e-1 표기 유지(1.0e-04/5.0e-03/2.0e-04/1.0e-07), Hourglass 5 0.100, 상속 FS=0.25·조합C GEN=1 S2S=1, HOURGLASS 4블록, S2S OptCardA 상속.
- 첫 e2e 가 4.5분 — 690 MB 배포 바이너리의 NFS 콜드 기동. 이후 런은 캐시로 빠름(총 7종 7분).
- SIF 21:22(1.58 GB) — 내부 KMM/KooChainRun .bin 10-07 빌드본(D2R_SKIPPED·D2RLrb 식별자 확인), KooRemapper 43084d35 유지, compute-node-images 사본 cmp 동일. tar `/data/SmartTwinPreprocessor/SmartTwinPreprocessor_20261009_v111.tar.gz`, Drive 업로드·메일 OK. 푸시 164718a..8073766.

- node001 배포 21:38 — /opt/apptainers SIF sha 29849604… == 호스트, 내부 KMM D2R_SKIPPED 식별자 확인. 체크리스트 전 항목 완료.
