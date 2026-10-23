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
