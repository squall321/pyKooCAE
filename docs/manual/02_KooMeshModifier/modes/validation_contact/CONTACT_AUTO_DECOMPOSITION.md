# KooMeshModifier 모드: CONTACT_AUTO_DECOMPOSITION

## 1. 목적 / 개요

`CONTACT_AUTO_DECOMPOSITION` 은 **전역 접촉(Single Surface 계열) 카드 1개를 파트 쌍 단위의 `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE`(S2S) 카드 다수로 자동 분해**하는 모드다. 동작의 핵심은 두 단계다 (KooDynaAdvancedModification.py:6319-6329):

1. 입력 `.k` 블록에 명시한 접촉 카드를 모델에 추가한다 (`AddContactfromDynawithID`).
2. 그 접촉을 기준으로, 각 파트의 바운딩 박스를 마진만큼 확장해 **겹치는 파트 쌍**을 찾아 쌍마다 S2S 접촉을 새로 만들고, 원본 전역 접촉은 제거한다 (`ConvertAss5ToAstsPartPairs`).

분해 대상이 되는 원본 접촉은 다음 중 하나여야 한다 (KooContact.py:1180-1192):
- `*CONTACT_AUTOMATIC_SINGLE_SURFACE` 또는 `*CONTACT_SINGLE_SURFACE` 로서 `MSTYP == 5` 또는 `SSTYP == 5` 인 경우(타입 5 = "전체/Part Set 5" 의미의 Single Surface 입력)
- `*CONTACT_AUTOMATIC_GENERAL`

위 조건에 맞지 않으면 분해를 수행하지 않고 메시지 출력 후 반환한다 (KooContact.py:1191-1193).

> 참고: 함수명 `ConvertAss5ToAstsPartPairs` 의 "Ass5"=Automatic Single Surface(type 5), "Asts"=Automatic Surface To Surface 를 의미한다.

## 2. 입력 옵션 · 인자 (표)

입력 트리거: KooMeshModifier 입력 파일의 모드 라인에 `contact_auto_decomposition,<modeID>`(소문자 비교), 옵션 블록 헤더는 `**ContactAutoDecomposition,<modeID>` (KooMeshModifier.py:309-311, 393-395).

| 옵션 | 형식 | 기본값 | 의미 | 근거 (file:line) |
|---|---|---|---|---|
| `SearchMarginX` | `SearchMarginX,<float>` | `1.5` | X축 바운딩 박스 확장 배율. 확장량 = `xLength*(margin-1)/2`, 단 절대 최소 마진(`absoluteMarginX=5.0`) 미만이면 절대값 사용 | KooMeshModifier.py:397, 416-418 / KooContact.py:1204, 1178 |
| `SearchMarginY` | `SearchMarginY,<float>` | `1.5` | Y축 확장 배율. 절대 최소 `absoluteMarginY=5.0` | KooMeshModifier.py:398, 419-421 / KooContact.py:1205, 1178 |
| `SearchMarginZ` | `SearchMarginZ,<float>` | `1.5` | Z축 확장 배율. 절대 최소 `absoluteMarginZ=0.5` | KooMeshModifier.py:399, 422-424 / KooContact.py:1206, 1178 |
| `ContactKeyword` | `ContactKeyword` 다음 줄부터 LS-DYNA 접촉 카드 본문(고정폭 10칸 필드) | `""`(빈 값) | 추가·분해할 원본 접촉 카드. 첫 줄은 `*CONTACT_..._ID` 키워드, 이후 줄은 10칸 단위로 분할되어 파라미터로 파싱됨. 다음 `*` 키워드 또는 빈 줄에서 종료 | KooMeshModifier.py:400, 425-444 |

옵션 키 비교는 모두 소문자 변환 후 부분 문자열 매칭이다 (KooMeshModifier.py:416-425). 블록은 빈 줄/`**end`/`*` 키워드에서 종료된다 (KooMeshModifier.py:404-407, 433).

`ContactKeyword` 파싱 세부 (KooMeshModifier.py:425-444):
- `ContactKeyword` 라벨 바로 다음 줄 = 키워드명(예: `*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID`).
- 그 다음 줄들은 `[line[i:i+10] for i in range(0,len(line),10)]` 로 **10칸 고정폭 분할**되어 리스트로 저장된다.
- `$`/`#` 줄은 건너뛴다.
- `ContactAutoDecomposition` 실행 시, 카드의 두 번째 데이터 행(`contactKeyword[1][0]`)에 들어있는 `"       CID"` 플레이스홀더 문자열을 현재 최대 CID+1 로 치환한다 (KooDynaAdvancedModification.py:6325-6327). 즉 카드의 ID 필드에 `CID`(우측 정렬 10칸) 를 적어두면 자동 ID 배정이 된다 — **확인 필요**(실제 입력 파일 관례를 확인하는 전용 예제가 없음).

## 3. 사용 예제

> **전용 예제 없음.** `Examples/` 트리에 `contact_auto_decomposition` / `**ContactAutoDecomposition` 입력 파일이 존재하지 않는다(grep 0건). 코드 내 예제 경로(KooMeshModifier.py:3052-3055 `5.SimulationModify/ContactAutoDecomposition`)는 주석 처리된 데드코드이며 실제 파일은 없다. 아래는 입력 파서(KooMeshModifier.py:393-446)와 사내 참고 매뉴얼(occProject/manual/02_KooMeshModifier_Modes_Reference.md:738-748)을 근거로 한 최소 재구성 예시로, 검증된 실행 산출물이 아니다 — 확인 필요.

```text
**ContactAutoDecomposition,1
SearchMarginX,1.5
SearchMarginY,1.5
SearchMarginZ,1.5
ContactKeyword
*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID
       CIDGlobalContact
         0         0         5
**end
```

주의:
- 두 번째 데이터 행 첫 10칸에 `       CID`(우측 정렬 `CID`)를 두면 실행 시 현재 최대 CID+1 로 치환된다 (KooDynaAdvancedModification.py:6326-6327).
- 분해되려면 원본 접촉이 Single Surface(`MSTYP`/`SSTYP` 중 하나 = 5) 또는 `*CONTACT_AUTOMATIC_GENERAL` 이어야 한다 (KooContact.py:1182-1186). 위 예시는 `SSTYP=5`(3번째 필드) 가정.
- 블록 종료 마커는 코드상 `**end`(부분 문자열, KooMeshModifier.py:406)로 인식된다. 사내 참고 매뉴얼은 `**EndContactAutoDecomposition` 으로 적혀 있으나 `**end` 를 포함하므로 동일하게 동작한다.
- 사내 참고 매뉴얼의 예시는 `*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE`(이미 S2S)로 적혀 있는데, 이는 분해 대상 조건(Single Surface/General)에 맞지 않아 실제로는 분해되지 않는다 — 코드 기준으로는 부적절한 예시다.

## 4. 동작 원리 (코드 근거)

1. **입력 트리거 등록**: 모드 라인의 `contact_auto_decomposition` 매칭 → `modeList` 에 `"CONTACT_AUTO_DECOMPOSITION"` 추가 (KooMeshModifier.py:309-311).
2. **옵션 블록 파싱**: `**contactautodecomposition` 헤더에서 `SearchMarginX/Y/Z`, `ContactKeyword` 를 읽어 `modeIDOption[modeID]` 에 저장. 마진 기본 1.5, ContactKeyword 는 10칸 고정폭 분할 (KooMeshModifier.py:393-446).
3. **dispatch**: 실행 시 `mode == "CONTACT_AUTO_DECOMPOSITION"` 분기에서 `GenerateContactAutoDecomposition(modeid)` 호출, 출력 파일 접미사 `_cad` 부여 (KooMeshModifier.py:2855-2857).
4. **위임**: `GenerateContactAutoDecomposition` → `advancedModification.ContactAutoDecomposition(curOption)` (KooMeshModifier.py:2587-2589).
5. **접촉 추가**: `ContactKeyword` 가 있으면 ID 플레이스홀더(`CID`)를 현재 최대 CID+1 로 치환 후, `contactManager.AddContactfromDynawithID(contactKeyword)` 로 모델에 접촉 카드 생성 (KooDynaAdvancedModification.py:6325-6328). `AddContactfromDynawithID` 는 키워드명에 따라 Single Surface / General / S2S / Tied 등 적절한 접촉 객체를 생성한다 (KooContact.py:958-1017).
6. **분해 본체** `ConvertAss5ToAstsPartPairs(partManager, cid, ...)` (KooContact.py:1178-1291):
   - 대상 접촉 유효성 검사: ASS/SS(`MSTYP`/`SSTYP`=5) 또는 AUTOMATIC_GENERAL 만 진행, 아니면 반환 (KooContact.py:1180-1193).
   - **바운딩 박스 계산**: 요소가 있는 모든 파트의 박스를 구해(`GetBoundaryBox`) 축별로 확장. 확장량 = `max(축길이*(margin-1)/2, 절대마진)` (KooContact.py:1196-1215).
   - **파트 쌍 탐색**: `find_contact_pairs_sweep(boundBoxDict, tol=0.0)` — X축 정렬 후 스윕&프룬으로 박스가 겹치는 파트 쌍 집합을 구한다 (KooContact.py:1219; KooOperator.py:301-331).
   - **속성 상속**: 원본 접촉의 FS/FD/DC/.../OptCardA~F 등 마찰·옵션 카드 값을 신규 S2S 에 복사 (KooContact.py:1221-1249, 1277-1282).
   - **Tied 쌍 제외**: 기존 Tied(S2S/Offset/Shell edge) 접촉이 PID 쌍(SSTYP=3,MSTYP=3)을 구속 중이면 그 쌍은 S2S 생성에서 건너뛴다(이중 구속 방지) (KooContact.py:1251-1273).
   - **S2S 생성**: 각 쌍에 대해 `CreateContactAutomaticSurfacetoSurface(...)` 로 PID 기반(SSTYP=MSTYP=3) S2S 생성, 이름은 `S2S_P<a>_<nameA>_to_P<b>_<nameB>`(70자 제한) (KooContact.py:1268-1286).
   - **원본 제거**: `RemoveContactbyID(cid)` 로 원본 전역 접촉 삭제 (KooContact.py:1288-1289).
   - 완료 로그: 생성 S2S 수 / Tied 제외 수 / 전체 bbox 쌍 수 출력 (KooContact.py:1290-1291).
7. **출력**: `_skip_default_write` 미설정이므로 공용 `WriteModifiedFile` 로 `<입력파일명>_cad.k` 가 기록된다 (KooMeshModifier.py:2855-2857, 2882-2891, 2906-2932).

## 5. 주의사항 · 한계

- **대상 접촉 제한**: Single Surface(MSTYP/SSTYP=5) 또는 AUTOMATIC_GENERAL 만 분해된다. 다른 타입을 주면 조용히 분해를 건너뛴다(반환만) (KooContact.py:1182-1193).
- **바운딩 박스 근접 = 접촉 가정**: 실제 접촉 여부가 아니라 **박스 겹침**으로만 쌍을 만든다. 마진이 크면 불필요한 S2S 가 과다 생성될 수 있고, 작으면 초기 간격이 있는 진짜 접촉 쌍을 놓칠 수 있다 (KooContact.py:1204-1219).
- **절대 최소 마진 하드코딩**: `absoluteMarginX/Y/Z = 5.0/5.0/0.5` 가 함수 기본 인자로 고정되어 입력 블록에서 조정 불가. 모델 단위(mm 가정)에 따라 의미가 달라진다 — 단위 확인 필요 (KooContact.py:1178, 1204-1206).
- **Tied 쌍만 제외**: 이중 구속 방지는 Tied 접촉이 PID 쌍(SSTYP=3,MSTYP=3)일 때만 적용된다. Tied 가 Segment Set/Node Set 측을 쓰면 경고만 출력하고 제외하지 못한다 → 수동 점검 필요 (KooContact.py:1257-1262).
- **요소 없는 파트 무시**: 요소가 없는 파트는 바운딩 박스 계산에서 제외되어 쌍 후보에서 빠진다 (KooContact.py:1197-1198).
- **ID 플레이스홀더 관례 미검증**: `ContactKeyword` 의 `CID` 치환은 카드 2번째 행 첫 10칸(`contactKeyword[1][0]`)에만 적용된다. 전용 예제가 없어 실제 입력 작성 관례는 확인 필요 (KooDynaAdvancedModification.py:6325-6327).
- **전용 예제 부재**: `Examples/` 에 입력 파일이 없어 3장 예시는 코드 근거 재구성이다. 코드 내 예제 경로(KooMeshModifier.py:3052-3055)는 주석 처리된 데드코드.

## 6. 개발 현황

**구현됨.**

- 근거: 입력 트리거 등록 (KooMeshModifier.py:309-311), 옵션 파서 (KooMeshModifier.py:393-446), dispatch 분기 (KooMeshModifier.py:2855-2857), 위임 메서드 `GenerateContactAutoDecomposition` (KooMeshModifier.py:2587-2589), 핵심 구현 `ContactAutoDecomposition` (KooDynaAdvancedModification.py:6319-6329), 분해 본체 `ConvertAss5ToAstsPartPairs` (KooContact.py:1178-1291), 접촉 생성 `AddContactfromDynawithID` (KooContact.py:958-1017), 파트 쌍 탐색 `find_contact_pairs_sweep` (KooOperator.py:301-331).
- 미확인 부분: 전용 예제/입력 파일 부재로 `ContactKeyword`/`CID` 입력 관례와 실제 단위계 검증 불가 — 확인 필요.
