<!-- 10-23 남은 Pre 결함 수정 중 결정과 근거를 적는 노트 -->
# 컨텍스트 노트 — 남은 결함 정리 (2026-10-23)

## 분류 근거
- R16 Vol I `*END`: "The *END command is optional and signals the conclusion of a keyword input file. Data in a keyword file beyond a *END command are not read by LS-DYNA."
- R16 `*INCLUDE` Remark 1: "Note that the command *END terminates the include file."
- 그래서 KMM 이 `*END` 뒤 블록을 읽던 옛 동작(마지막 블록만 버림)은 LS-DYNA 와 다르다. f1ad034 는 `*END` 가 있는 파일을 옛 동작 그대로 둬서 바이트 동일을 지켰다. 이번에는 사용자 지시로 LS-DYNA 규칙에 맞춘다.
- 우리 출력기(KMM·병합기·분해기·고급 수정·IGA·검증기)는 모두 파일 끝에 `*END` 하나만 쓴다. 병합기는 인라인할 때 `*KEYWORD`·`*END` 줄을 지운다. 러너(Runner)에는 `*END` 를 다루는 코드가 없다. 그래서 F3 는 우리 산출물을 바꾸지 않는다.
- R16 Appendix V: 빈 줄은 '기본값만 든 선택 카드' 로 읽힌다. `*ELEMENT_SHELL_THICKNESS` 의 빈 두께 카드는 '섹션 두께' 라는 뜻이 있다. 반면 순수 `*ELEMENT_SOLID`·`*ELEMENT_SHELL` 카드는 EID·PID·N 이 모두 기본값이 없어(none) 빈 줄이 정상 카드가 될 수 없다. 그래서 F1 은 이 둘의 레거시 경로만 고친다.
- R16 `*ELEMENT_SOLID`: 표준은 Card 1(EID PID)+Card 2(N1~N10)다. Remark 4 'Obsolete Card Format' 은 940~970 판의 한 줄 형식이다. `(ten nodes format)` 표기는 원문에 없다. 그래서 writer 는 결함이 아니다.
- 데이터 카드 없는 키워드: 원문에서 `*CONTROL_MPP_IO_NOTIEDIO`("This keyword has no input parameters"), `*LOAD_SEGMENT_ALE_INI`("This keyword has no data cards"), `*CHANGE_VELOCITY_ZERO` 를 찾았다. `*CONTROL_MPP_IO_NOD3DUMP` 도 같은 꼴이다. `*CONTROL_MPP_IO_NODUMP` 는 전용 클래스(ControlMppIoNodump)가 있어 이미 살아남는다.
- 빌드 컨테이너(KooSimulationPython313)의 LD_LIBRARY_PATH 는 `/opt/opencascade-7.9.0/lib:/opt/SmartTwinPreprocessor/lib/KooMeshModifier:/usr/local/lib:/.singularity.d/libs` 다. 컨테이너 안 ldd 는 `_ssl`·`_hashlib`·`readline` 의 libssl·libcrypto·libreadline 을 `/opt/SmartTwinPreprocessor/lib/KooMeshModifier` 에서 찾는다. 이 파일들은 GLIBC 2.38 을 요구해 컨테이너 자신의 `python3.12 -c 'import ssl'` 도 죽는다. `env -u LD_LIBRARY_PATH` 면 `/lib/x86_64-linux-gnu` 의 OpenSSL 3.0.2 를 찾고 정상이다. KooChainRun 배포 폴더의 libcrypto.so.3 도 2.38 이다.
- DWI: KMM DropWeightImpactTest 의 폴백값은 SI 다. 앞부분은 E 2.07e11·ρ 7800, 댐퍼는 E 1e10·ν 0.3·ρ 1000·치수 [0.001]×3(SECTION_BEAM 폭·높이·오프셋), 바닥판은 E 1e10·ρ 1000 이다. 러너 `_write_dwi_step_config` 는 충격체 본체·바닥판만 ton-mm-s 로 넘긴다. Mid 는 KMM 이 Impactor 값으로 대신 쓰므로 문제가 없다. MeshSize 는 KMM `_ResolveImpactorMeshSize` 가드(치수/8)가 이미 막고 있다.

## 작업 중 결정
- F7 방향을 바꿨다. 처음에는 '러너가 ton-mm-s 값을 명시' 였다. 그런데 저장소의 IMPACT 시나리오 둘(Test_Impact_Grid5x5·Spacing5mm)이 SI 치수(0.008·0.5·0.001)를 직접 준다. 그러니 IMPACT 는 SI 모델에도 쓰이고, 러너가 mm 값을 박으면 SI 모델이 반대로 틀어진다. 그래서 KMM 이 중력 판정(_ResolveFallGravity)과 같은 재질 밀도 판정으로 폴백을 고르게 했다(_DwiFallbacks). 러너 IMPACT 는 mesh_size·dimension_damper 가 없으면 줄을 쓰지 않는다. SI 시나리오는 값을 직접 주므로 그대로다.
- byPart(Part) 경로는 손대지 않았다. 부품 생성기가 원래 mm 폴백(E 2.07e5·ρ 7.8e-9, 바닥판 E 1e6·ρ 1e-9)을 쓰고, 댐퍼 코드는 `'''` 문자열 안의 죽은 코드다.
- 남긴 것: IMPACT 의 dimension·height·offset_distance 기본값은 여전히 SI 크기(0.008·0.5·1e-5)다. 시나리오에서 빠지면 mm 덱에 아주 작은 충격체가 만들어진다. 충격체 치수는 사용자가 꼭 주는 값이라 이번에는 그대로 둔다(보고).
- F5 는 '매니저가 쓰지 않은 키워드' 만 되살린다. 데이터 없는 `*DEFINE_CURVE` 처럼 필수 카드가 빠진 키워드도 원문대로 남는다. 예전에는 조용히 지웠고, 원래 덱도 LS-DYNA 오류다. 무엇을 남겼는지는 한 줄로 알린다(dca2d5f).
- 시험 중 실패 둘(이미 통과하던 [3]·기준 케이스)은 코드 탓이 아니었다. 19:55 호스트 메모리 고갈(NVRM out of memory, earlyoom 이 NewsKooo 워커·kube 파드를 계속 죽임) 탓이었다. 메모리를 회복한 뒤 다시 돌리니 예상한 실패만 남았다.
- 메모리 고갈의 주범은 cpptools(48.9 GB 익명 메모리)였다. 그런데 이것은 pyKooCAE 가 아니라 **KooD3plotReader** 작업 공간의 것이었다(workspaceStorage c814e896 = 색인 캐시 이름). 처음에 pyKooCAE 의 Nuitka 빌드 폴더로 오진했다. 사용자 승인(PID 명시)으로 종료만 했다. pyKooCAE 설정 파일은 만들지 않았고, 62 GB 색인 캐시도 지우지 않았다(지우면 처음부터 다시 색인). KooD3plotReader/.vscode/settings.json 의 제외 목록은 이름이 정확히 같은 폴더만 뺀다. 그래서 build_norender·.work/review/build_*·viewer/third_party·references·apptainer 가 색인에 남는다. 그 프로젝트 담당과 정할 일이다.

## 적대 리뷰 D·E 와 반영
- 리뷰 E(DWI·빌드)
  - A1 확정: 단위계 판정이 명시한 Gravity 를 무시했다. Gravity 9.81 인 SI 덱도 더미 재질 밀도 탓에 ton-mm-s 폴백을 받았다. 반대로 밀도를 못 읽는 mm 덱은 Gravity 9810 이어도 SI 폴백을 받았다. → 1de4a5a. Gravity → 밀도 → 미판정 순서다.
  - A2: 내 리뷰 요청서의 '8pi·15pi 단계 설정이 같다' 는 틀렸다. dimension_damper 를 안 주는 예제는 이제 DimensionDamper 줄이 빠진다. 다만 누적 IMPACT 템플릿은 BoundaryDistance 를 쓰지 않아 댐퍼 보 자체가 안 생기므로 덱 영향은 없다.
  - A3(근거 정정): Test_Impact_Grid5x5·Spacing5mm 은 SI 값을 준 시나리오다. 그런데 템플릿 MinimumModel 은 ton-mm-s(ρ 1.8e-9~2.8e-9, 71×147×9 mm)다. 그러니 'IMPACT 가 SI 모델에 쓰인다' 는 근거는 틀렸다. 저장소에 SI IMPACT 모델은 없다. 그 두 시나리오는 0.008 mm 충격체를 만드는 잘못된 예제다(보고). 그래도 KMM 쪽 판정은 어느 단위계 모델이든 맞게 고르므로 그대로 둔다.
  - 반영: 앞부분 재질은 충격체 재질을 물려받는다(1de4a5a). 3단 실린더 NameError(26acfeb), 도움말 문구(5242b55), 가드 정리를 늘 적용(3433f46), 배포 GLIBC 검사(b3a3cd1).
  - 남긴 것
    - KAM 배포 폴더에도 GLIBC 2.38 libcrypto·libreadline 이 있다. build_all 로 KAM 까지 다시 빌드해야 없어진다.
    - 누적 DWI 체인에서 벽·댐퍼가 단계마다 겹친다(옛 판과 같다). 라이선스가 만료돼 실제 해석으로는 검증하지 못했다.
    - DWI OutsideRigid* 산출 덱이 Run_* 아래가 아니라 모델 옆에 써진다.
    - mesh_size 가드는 실린더의 가장 큰 치수를 써서 메시가 거칠 수 있다.
    - 재질이 짝수 개일 때 중앙값은 위쪽 값으로 판정한다.
- 리뷰 D(리더·파서)
  - 확정: Ctrl-Z 를 첫 0x1A 에서 잘라, 주석·*TITLE 안 0x1A 뒤가 조용히 사라지거나 새로 죽었다. MERGE_K 가 만든 덱에서도 생겼다. → 94ecd32 에서 파일 끝에 붙은 것만 지우게 했다.
  - 반영(옛 판부터 있던 결함): *END 뒤 PARAMETER 가 앞 값을 덮음(11283e1), 매니저 재사용 초기화(db7d554), 덤프 BULK_VISCOSITY 줄바꿈(05a1911), CASE 표지를 되살리지 않음(034e268), MERGE_K 가 *END 뒤·0x1A 까지 펼침(07c3be9).
  - 남긴 것
    - 빈 두께 카드가 든 *ELEMENT_SHELL_THICKNESS 는 IndexError 로 죽는다(옛 판과 같다). LS-DYNA 에서는 '섹션 두께' 를 뜻하는 정상 카드다.
    - 매니저는 *CONTROL_MPP_IO_NODUMP 를 쓰지 못한다(비교 문자열 버그, write 메서드 없음). 지금은 원문 보존 기록기만 이 카드를 쓴다.
    - 4~5월 KMM 산출물 가운데 IGA 인클루드를 *END 째 펼친 파일은 이제 첫 *END 에서 멈추고 크게 알린다. LS-DYNA 도 같게 읽는다.
    - 데이터 없는 필수 카드(빈 *DEFINE_CURVE, 이름이 다른 두 번째 빈 *MAT_ELASTIC)는 원문대로 남는다(의도, 원래 덱도 LS-DYNA 오류).
- 3차 리뷰(F)는 위 반영분을 다시 본다.

## 3차 리뷰 F 와 반영
- 확정 6건
  1. MERGE_K 가 0x1A 대신 빈 데이터 줄을 남겼다. 다시 읽으면 크래시였고, *NODE 면 원점의 절점 0 이 조용히 생겼다. 줄바꿈 보충을 원문으로 판단한 탓이다. → f5e88ff 는 잘라 낸 본문으로 판단한다.
  2. '*END ,' 를 키워드 루프는 END 로 보는데 PARAMETER·MERGE_K 판정은 아니었다. → ff4b94a·f5e88ff 는 루프와 같은 keyword_line_name() 을 쓴다(루프는 그대로).
  3. 3단 실린더 다위치에서 26acfeb 뒤로 크래시 대신 조용히 틀린 덱이 나왔다(중간단 요소가 쌓임). DampingSpring 도 옛 판부터 같았다(FastDOE 는 중간단이 아예 빠지고, 경계 거리가 있으면 IVG·접촉이 겹침). → 7afefc5 는 아홉 곳에서 중간단을 앞부분과 똑같이 다룬다. 경계 댐퍼 대상 루프에서도 빠져 있어, 위치가 하나여도 충격체 중간단에 댐퍼가 붙을 수 있었다.
  4. 명시한 Gravity 가 뚜렷한 밀도 판정과 엇갈려도 아무 말 없이 Gravity 를 따랐다. → 94ba214 는 엇갈림을 🔴 로 알린다(순서는 Gravity 그대로).
  5. 끝의 Ctrl-Z 를 지울 때 그 앞 빈 줄(빈 카드일 수 있음)까지 지웠다. → 2993cb6.
  6. *END 뒤에서만 정의한 파라미터가 조용히 0 이 됐다(미정의 &참조에 경고가 없던 기존 결함이 드러남). → 927a00f 는 맨 위 파일 읽기 뒤에 🔴 로 알린다.
- 같이 고친 기존 결함: I10 THICKNESS 빈 두께 카드(728836e), 덤프 머리말 줄바꿈 일곱 곳(adad01a), 데이터 있는 *CASE_BEGIN 이 짝 없이 남던 것(aec40e8).
- 실수 정정: 리뷰 F 반영 커밋 셋(4380c15·bb70c89·84a374f)을 -U0 hunk 로 나눠 올리다 KooDynaKeyword.py 가 깨졌다(IndentationError, def WriteOutputFile 줄 빠짐). 푸시 전에 f5e88ff 로 되돌려 -U3 로 다시 커밋했다(2993cb6·927a00f·1ba5fde·94ba214). 그 뒤 오늘 커밋 29개의 .py 38판이 모두 파싱되는 것을 확인했다. 교훈: 같은 파일을 hunk 로 나눠 올릴 때는 커밋마다 `git show :path` 를 파싱해 본다.
- 이 호스트의 ~/.local/bin/gmsh 는 시스템 파이썬으로 돌아 충격체가 0 요소였다. 그래서 DWI 시험은 venv312/bin 을 PATH 앞에 둔다(충격체 형상까지 실제로 메시).
- 남긴 것(보고)
  - KMM 출력기는 *ELEMENT_SHELL_THICKNESS 를 쓰지 않는다. 요소별 두께가 일반 *ELEMENT_SHELL 로 바뀌며 사라진다.
  - 메인 파일은 인클루드에서 정의한 파라미터를 치환하지 못한다(이제 🔴 로 알림).
  - *PARAMETER 중복 정의는 LS-DYNA 기본(DFLAG=1, 새 정의 무시)과 달리 나중 값을 쓴다.
  - MaterialIDImpactor 재사용 + 앞부분 키 없음이면 앞부분이 표 값이 된다(재사용 재질을 물려받지 않음).
  - NUL 패딩은 지우지 않는다.
