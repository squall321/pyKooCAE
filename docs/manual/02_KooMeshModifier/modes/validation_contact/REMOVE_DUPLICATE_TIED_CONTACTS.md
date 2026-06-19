# KooMeshModifier 모드: REMOVE_DUPLICATE_TIED_CONTACTS

## 1. 목적/개요

`REMOVE_DUPLICATE_TIED_CONTACTS` 모드는 입력 모델에 중복 정의된 **Tied Contact**(접착 접촉)를 자동으로 제거한다.

동일한 파트(또는 세트) 페어에 대해 Tied Contact가 두 번 이상 정의되어 있을 때, **SSID/MSID 순서에 무관하게** 같은 페어로 간주하여 가장 먼저 읽힌 하나만 남기고 나머지는 삭제한다. 동일 노드/세그먼트에 Tied 제약이 중복 부여되면 LS-DYNA에서 과구속(over-constraint)이나 경고가 발생할 수 있는데, 이를 정리하기 위한 후처리/검증 성격의 모드이다.

대상이 되는 Tied Contact 타입은 다음 3종이다 (KooContact.py:1299-1303 근거):

- `*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET` (`KooContactTiedShellEdgetoSurfaceBeamOffset`, KooContact.py:444)
- `*CONTACT_TIED_SURFACE_TO_SURFACE` (`KooContactTiedSurfacetoSurface`, KooContact.py:460)
- `*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET` (`KooContactTiedSurfacetoSurfaceOffset`, KooContact.py:476)

위 3종 외의 접촉(예: 일반 SINGLE_SURFACE, TIEBREAK 등)은 이 모드의 대상이 아니다.

---

## 2. 입력 옵션·인자(표)

KooMeshModifier 옵션 파일(`.txt`) 내에서 두 곳에 선언한다.

(1) `*Mode` 블록에 모드 등록 (KooMeshModifier.py:315-317):

| 항목 | 값 | 설명 |
|------|-----|------|
| 모드 키워드 | `REMOVE_DUPLICATE_TIED_CONTACTS` | `*Mode` 블록 줄에 `remove_duplicate_tied_contacts,<id>` 형태로 기입. 대소문자 무관(소문자 변환 후 매칭) |
| modeID | 정수 | 모드 식별 ID. 콤마 뒤 두 번째 토큰(`int(svector[1])`) |

(2) `**remove_duplicate_tied_contacts,<id>` 옵션 블록 (KooMeshModifier.py:341-369):

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `RemoveDuplicateTiedContacts` (블록 내 `remove_duplicate_tied_contacts` 줄) | bool (`true`/`false`) | `True` | 블록 진입 시 `True`로 초기화됨(KooMeshModifier.py:345). 블록 안에 `remove_duplicate_tied_contacts,true/false` 줄로 명시 가능. 값 없이 키워드만 있으면 `True` (KooMeshModifier.py:357-365) |

- 옵션 블록은 `**end` 또는 빈 줄을 만나면 종료된다 (KooMeshModifier.py:349-352).
- `#`, `$`로 시작하는 줄은 주석으로 무시된다 (KooMeshModifier.py:353-356).
- 정의되지 않은 줄이 나오면 `Invalid option` 출력 후 프로그램이 종료된다 (KooMeshModifier.py:366-368).

> 참고: 실질적으로 사용자 조정 가능한 인자는 위 on/off 플래그 하나뿐이며, 페어 비교 기준(SSID/MSID 정렬)이나 보존 규칙(먼저 읽힌 것 유지)은 코드에 하드코딩되어 있어 인자로 노출되지 않는다.

---

## 3. 사용 예제

> **전용 예제 없음** — `Examples/` 디렉터리에서 이 모드를 사용하는 시나리오/옵션 파일을 찾지 못했다(grep 결과 코드 정의부만 존재). 아래 예제는 옵션 파일 파서 규약(KooMeshModifier.py:154-369)과 다른 모드의 실제 예제(`Examples/alldropangles/drop_attitude.txt`) 형식에 근거해 구성한 것으로, 실행 검증된 예제가 아니다. **확인 필요**.

### 옵션 파일 (`remove_duplicate_tied_contacts.txt`)

```text
*Inputfile
MinimumModel.k
*Mode
REMOVE_DUPLICATE_TIED_CONTACTS,1
**remove_duplicate_tied_contacts,1
remove_duplicate_tied_contacts,true
**End
*End
```

- `*Inputfile` 다음 줄에 대상 베이스 `.k` 파일명을 지정한다 (KooMeshModifier.py:163-166).
- `*Mode` 블록의 `REMOVE_DUPLICATE_TIED_CONTACTS,1`에서 `1`이 modeID이다.
- `**remove_duplicate_tied_contacts,1`의 `1`은 위 modeID와 일치해야 옵션이 연결된다 (KooMeshModifier.py:343, 369).
- 블록 내 `remove_duplicate_tied_contacts,true` 줄은 생략 가능하다(기본 `True`).

### CLI 실행

```bash
KooMeshModifier remove_duplicate_tied_contacts.txt <작업디렉터리>
```

- 인자: `[옵션파일.txt] [작업디렉터리]` (KooMeshModifier.py:3142-3147).
- 실행 흐름: `ImportOption` → `ImportBaseFile` → `GenerateModifiedFile` (KooMeshModifier.py:3161-3166).

---

## 4. 동작 원리 (코드 근거)

1. **모드 등록** — 옵션 파일의 `*Mode` 블록에서 `remove_duplicate_tied_contacts` 토큰을 만나면 `modeList`에 `"REMOVE_DUPLICATE_TIED_CONTACTS"`, `modeIDList`에 ID를 추가한다.
   - 근거: `KooMeshModifier.py:315-317`

2. **옵션 파싱** — `**remove_duplicate_tied_contacts` 블록을 읽어 `curOptions["RemoveDuplicateTiedContacts"]`를 채운 뒤 `self.modeIDOption[curModeID]`에 저장한다.
   - 근거: `KooMeshModifier.py:341-369`

3. **디스패치** — `GenerateModifiedFile`의 모드 분기에서 `REMOVE_DUPLICATE_TIED_CONTACTS`이면 `GenerateRemoveDuplicateTiedContacts(modeid)`를 호출하고 출력 파일명 접미사 `_rdc`를 추가한다.
   - 근거: `KooMeshModifier.py:2810-2812`

4. **위임** — `GenerateRemoveDuplicateTiedContacts`는 `advancedModification.RemoveDuplicateTiedContacts(curOption)`를 호출하고, 이는 다시 `contactManager.RemoveDuplicateTiedContacts()`로 위임한다.
   - 근거: `KooMeshModifier.py:2459-2461`, `KooDynaAdvancedModification.py:6439-6445`

5. **핵심 중복 제거 로직** — `KooContact.py:1293-1321`
   - 등록된 모든 접촉을 순회하며 Tied 타입 3종(KooContact.py:1299-1303)에 해당하는 것만 처리.
   - 각 접촉의 `(SSID, MSID)`를 `tuple(sorted([SSID, MSID]))`로 **정렬**하여 순서 무관 페어 키를 만든다 (KooContact.py:1310).
   - 이미 본 페어(`seenPairs`)이면 제거 목록(`contactsToRemove`)에 추가, 처음 보는 페어이면 `seenPairs`에 등록 → **먼저 읽힌 접촉이 보존**된다 (KooContact.py:1312-1315).
   - 제거 목록을 `RemoveContact(contact)`로 삭제 — 내부적으로 `del self.contacts[contact.cid]` (KooContact.py:1317-1318, 809-810).
   - 제거 개수를 출력하고 반환: `[RemoveDuplicateTiedContacts] Removed N duplicate tied contacts` (KooContact.py:1320-1321).

6. **출력 파일 작성** — 모드 처리 후 `WriteModifiedFile("_rdc")`로 수정된 모델을 기록한다. 출력 파일명은 `<입력파일명>_rdc.k` 형태이며 `*KEYWORD` 헤더와 함께 전체 DYNA 키워드를 다시 쓴다.
   - 근거: `KooMeshModifier.py:2812`(접미사), `2885-2888`, `2906-2914`(파일명/작성)

---

## 5. 주의사항·한계

- **페어 동일성 판정 기준이 SSID/MSID 값뿐이다.** `sorted([SSID, MSID])`만 비교하므로(KooContact.py:1310), Contact Type이 서로 달라도(예: TIED_SURFACE_TO_SURFACE vs TIED_SURFACE_TO_SURFACE_OFFSET) 같은 ID 페어이면 중복으로 간주되어 둘 중 하나가 삭제된다. 서로 다른 의도로 정의한 접촉이 의도치 않게 제거될 수 있으니 결과를 확인할 것.
- **SSTYP/MSTYP(세트 타입)는 비교에 포함되지 않는다.** SSID/MSID가 Part ID인지 Segment Set ID인지 구분 없이 숫자만 비교하므로, 우연히 같은 번호의 다른 종류 세트가 충돌할 가능성이 있다. **확인 필요**.
- **보존되는 접촉은 "먼저 읽힌 것"이다.** dict 순회 순서(`self.contacts.items()`)에 의존하므로, 어떤 정의를 남길지 명시적으로 선택할 수 없다.
- 대상은 **Tied 3종에 한정**된다(KooContact.py:1299-1303). 그 외 접촉 중복은 처리하지 않는다.
- on/off 플래그(`RemoveDuplicateTiedContacts=false`)가 옵션으로 파싱되긴 하나(KooMeshModifier.py:357-365), 디스패치/위임 경로(`GenerateRemoveDuplicateTiedContacts` → `RemoveDuplicateTiedContacts`)는 이 값을 검사하지 않고 항상 `contactManager.RemoveDuplicateTiedContacts()`를 실행한다(KooMeshModifier.py:2459-2461, KooDynaAdvancedModification.py:6439-6445). 즉 `false`로 설정해도 제거가 수행될 수 있다. **확인 필요**.

---

## 6. 개발 현황

**구현됨** — 모드 등록(KooMeshModifier.py:315-317), 옵션 파싱(341-369), 디스패치(2810-2812), 위임(2459-2461 → KooDynaAdvancedModification.py:6439-6445), 핵심 로직(KooContact.py:1293-1321)이 모두 존재하고 연결되어 동작 가능한 완결 경로를 갖는다.

단, 다음 두 항목은 코드상 정합성 측면에서 **부분구현/확인 필요**:
- on/off 플래그가 실제 실행 분기에서 사용되지 않는 것으로 보임(5절 참조).
- `Examples/`에 전용 검증 예제가 없어 실제 모델에서의 동작 검증 자료가 부재함.
