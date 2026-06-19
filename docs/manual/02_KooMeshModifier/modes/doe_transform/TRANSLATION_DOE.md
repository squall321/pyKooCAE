# KooMeshModifier 모드: TRANSLATION_DOE

> 근거 코드: `occProject/Generators/KooMeshModifier.py` (모드 등록 / 입력 블록 파서 / 디스패치), `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py` (핵심 구현 `TranslationDOE()`), `occProject/Generators/KooCAEManager/KooPart.py` (`Translate()`).

---

## 1. 목적 / 개요

`TRANSLATION_DOE` 는 지정한 파트(PID)들을 X/Y/Z 방향으로 일련의 값만큼 평행이동(translation)시킨 **여러 개의 변형 모델(.k)을 한 번에 생성**하는 DOE(Design Of Experiments) 생성 모드이다.

- 파트별로 X/Y/Z 이동량 리스트를 주면, 리스트 인덱스 `i` 단위로 샘플을 만든다. 즉 샘플 `i` 는 모든 파트를 각자의 `X[i], Y[i], Z[i]` 만큼 이동시킨 모델이다.
- 샘플마다 `<입력파일>_TranslationDOE_<i>.k` 파일을 출력하고, 전체 샘플의 이동량 메타데이터를 `<입력파일>_TranslationDOE.json` 으로 기록한다.
- 한 샘플을 쓴 뒤에는 이동을 역으로 되돌려(원위치 복원) 다음 샘플을 만든다 → 누적 이동이 아니라 **원본 기준 절대 이동**이다.

근거: 디스패치 `GenerateModifiedFile()` 내 `elif mode == "TRANSLATION_DOE": self.GenerateTranslationDOE(modeid)` (KooMeshModifier.py:2822-2824) → `GenerateTranslationDOE()` (KooMeshModifier.py:2491-2495) → `advancedModification.TranslationDOE()` (KooDynaAdvancedModification.py:6331-6390).

---

## 2. 입력 옵션 · 인자 (표)

입력은 KooMeshModifier 옵션 파일(`.txt`)의 두 부분으로 구성된다.

### 2.1 `*Mode` 블록 — 모드 등록 (트리거)

```
*Mode
translation_doe,<모드ID>
*End
```

| 토큰 | 의미 | 코드 근거 |
|---|---|---|
| `translation_doe` | 모드 키워드(대소문자 무시). 매칭 시 `modeList`에 `"TRANSLATION_DOE"` 추가 | KooMeshModifier.py:279-281 |
| `<모드ID>` | `svector[1]` 정수. 옵션 블록과 매칭되는 모드 ID | KooMeshModifier.py:281 |

### 2.2 `**Translation_DOE` 블록 — 옵션 정의

```
**Translation_DOE,<모드ID>
TranslationX,<PID>,<X0>,<X1>,...,<Xn>
TranslationY,<PID>,<Y0>,<Y1>,...,<Yn>
TranslationZ,<PID>,<Z0>,<Z1>,...,<Zn>
**End
```

| 라인 | 인자 형식 | 동작 | 코드 근거 |
|---|---|---|---|
| `**Translation_DOE` | `,<모드ID>` | 옵션 블록 시작. `curModeID = int(svector[1])` | KooMeshModifier.py:1254-1256 |
| `TranslationX` | `,<PID>,<값들...>` | 해당 PID의 X 이동량 리스트. `svector[2:]` 를 `KooDynaFloat` 로 파싱 | KooMeshModifier.py:1266-1276 |
| `TranslationY` | `,<PID>,<값들...>` | 해당 PID의 Y 이동량 리스트 | KooMeshModifier.py:1277-1285 |
| `TranslationZ` | `,<PID>,<값들...>` | 해당 PID의 Z 이동량 리스트 | KooMeshModifier.py:1286-1294 |
| `**End` (또는 빈 줄) | — | 블록 종료 | KooMeshModifier.py:1262-1265 |

세부 동작:

- 키워드 매칭은 부분 문자열 + 소문자 비교다(`"translationx" in line.lower()` 등). `TranslationX` / `translationx` 모두 인식.
- 같은 PID에 대해 처음 들어온 축은 나머지 두 축을 `[0.0]*len(리스트)` 로 채운다(KooMeshModifier.py:1271-1294). 즉 한 축만 주어도 나머지 축은 0 이동으로 자동 채워짐.
- 샘플 개수는 **첫 PID의 X 리스트 길이**로 결정된다: `numofSamples = len(firstpidTransXList)` (KooDynaAdvancedModification.py:6334-6336).

> 확인 필요(코드상 버그 가능성): 옵션 블록 파서의 자동 0-채움 로직은 `if pid not in curOptions["Translation"]:` 인 분기에서 `curOptions["Translation"][pid]["Y"] = ...` 를 수행하는데(KooMeshModifier.py:1271-1274 등), `curOptions["Translation"][pid]` 를 `{}` 로 먼저 초기화하는 코드가 없어 `KeyError` 가 발생할 수 있다. 즉 "한 PID에 대해 X/Y/Z 를 모두 명시"하지 않고 일부 축만 주는 사용은 현재 코드에서 실패할 소지가 있다. 안전하게는 **각 PID에 X/Y/Z 세 줄을 모두 기재**하는 것을 권장한다. (정밀 검증 필요)

---

## 3. 사용 예제

> 전용 예제 파일 없음 — 본 저장소 `Examples/` 트리에서 `translation_doe` 입력 .k/옵션 파일을 찾지 못함(검색 결과 0건). 아래 예제는 위 2장의 파서 코드 근거(KooMeshModifier.py:1254-1296)로부터 구성한 최소 형태이며 실모델로 검증된 것은 아니다.

옵션 파일(.txt) 예 — PID 100, 200 을 2개 샘플로 이동:

```
*Inputfile
MinimumModel.k
*Mode
translation_doe,1
*End

**Translation_DOE,1
TranslationX,100,0.0,5.0
TranslationY,100,0.0,0.0
TranslationZ,100,0.0,0.0
TranslationX,200,0.0,-3.0
TranslationY,200,0.0,2.0
TranslationZ,200,0.0,0.0
**End
```

위 입력은 다음을 생성한다(샘플 수 = 첫 PID X 리스트 길이 = 2):

- `MinimumModel_TranslationDOE_0.k` — 샘플 0 (모든 이동량 0, 사실상 원본)
- `MinimumModel_TranslationDOE_1.k` — 샘플 1 (PID100 +5X / PID200 -3X,+2Y)
- `MinimumModel_TranslationDOE.json` — 샘플별 PID 이동량 메타

> 옵션 파일 확장자는 코드상 `.txt` 가 표준이다(로그 파일명 `optionName.replace(".txt", ".log")` 변환 전제, KooMeshModifier.py:3150). 상세는 `docs/manual/02_KooMeshModifier/input_format.md` 참조.

`<입력파일>_TranslationDOE.json` 출력 구조(코드 근거 KooDynaAdvancedModification.py:6378-6389):

```json
{
    "0": {
        "filePath": ".../MinimumModel_TranslationDOE_0.k",
        "parts": {
            "100": {"transX": 0.0, "transY": 0.0, "transZ": 0.0},
            "200": {"transX": 0.0, "transY": 0.0, "transZ": 0.0}
        }
    },
    "1": { "...": "..." }
}
```

---

## 4. 동작 원리 (코드 근거)

1. **모드 등록** — `*Mode` 블록에서 `translation_doe,<id>` 를 만나면 `modeList`에 `"TRANSLATION_DOE"`, `modeIDList`에 ID 추가 (KooMeshModifier.py:279-281).
2. **옵션 파싱** — `**translation_doe,<id>` 블록을 읽어 `curOptions["Translation"][pid] = {"X":[...], "Y":[...], "Z":[...]}` 구조로 채우고 `self.modeIDOption[curModeID]` 에 저장 (KooMeshModifier.py:1254-1296).
3. **디스패치** — `GenerateModifiedFile()` 에서 `mode == "TRANSLATION_DOE"` 분기 → `GenerateTranslationDOE(modeid)` 호출, 출력 접미사 `_trans` 추가 (KooMeshModifier.py:2822-2824).
4. **핸들러** — `GenerateTranslationDOE()` 가 입력 파일 경로(확장자 `.k` 제거)와 옵션을 만들어 `advancedModification.TranslationDOE(curOption, filePath)` 호출 (KooMeshModifier.py:2491-2495).
5. **핵심 루프** (`TranslationDOE()`, KooDynaAdvancedModification.py:6331-6390):
   - 샘플 수 결정: `numofSamples = len(translationDict[firstpid]["X"])` (6334-6336).
   - 샘플 `i` 마다:
     - 모든 PID에 대해 `part.Translate(transX, transY, transZ)` 로 노드 좌표 이동 (6354-6360). `KooPart.Translate()` 는 파트 요소의 모든 노드를 `node.Translate(dx,dy,dz)` 로 옮긴다 (KooPart.py:252-256).
     - 모델을 `_TranslationDOE_<i>.k` 로 출력 (6362-6377).
     - **역이동으로 원위치 복원**: `part.Translate(-transX, -transY, -transZ)` 후 메타데이터(`jsonDict[i]["parts"][pid]`) 기록 (6381-6387). → 다음 샘플은 다시 원본 기준에서 이동.
   - 전체 메타를 `_TranslationDOE.json` 으로 직렬화 (6389).
6. **Fast DOE 모드** — 샘플이 2개 이상(`numofSamples > 1`)이면 노드 외 키워드(pre/post)를 1회 캐시(`WriteStreamPreNodesKeyword` / `WriteStreamPostNodesKeyword`)해 두고, 매 샘플은 노드 스트림만 다시 써서 I/O를 줄인다. 초기화 실패 시 기존 전체 write 방식으로 폴백 (KooDynaAdvancedModification.py:6341-6377).

---

## 5. 주의사항 · 한계

- **샘플 수 기준은 첫 PID의 X 리스트 길이** 하나뿐이다(6334-6336). 다른 PID/축의 리스트 길이가 이와 다르면, 인덱스 접근(`translationDict[pid]["X"][i]` 등, 6356-6358)에서 길이 불일치로 `IndexError` 가 날 수 있다 → **모든 PID·모든 축의 리스트 길이를 동일하게** 맞출 것. (코드상 길이 검증 로직 없음)
- 이동은 **원본 기준 절대 이동**이며 샘플 간 누적되지 않는다(매 샘플 후 역이동 복원, 6386).
- 각 PID는 X/Y/Z 세 축을 모두 명시하는 것을 권장(2.2의 자동 0-채움 `KeyError` 가능성, 확인 필요).
- 출력 .k 파일명/JSON 파일명은 입력 파일 경로 기준으로 고정 생성된다(`_TranslationDOE_<i>.k`, `_TranslationDOE.json`). 디렉토리/접미사 커스터마이즈 옵션은 코드상 없음.
- 회전/스케일/미러가 필요하면 본 모드가 아니라 `TRANSFORM` 모드(KooMeshModifier.py:1297-1327)를 사용한다. `TRANSLATION_DOE` 는 평행이동 DOE 전용이다.
- 본 모드에 대한 저장소 내 예제·테스트 입력이 확인되지 않음 → 실모델 동작은 미검증(확인 필요).

---

## 6. 개발 현황

**구현됨 (부분 검증)**

- 근거: 모드 등록(KooMeshModifier.py:279-281), 옵션 파서(1254-1296), 디스패치(2822-2824), 핸들러(2491-2495), 핵심 구현(KooDynaAdvancedModification.py:6331-6390)이 모두 존재하며 코드 경로가 끊김 없이 연결됨.
- 단, (a) 옵션 파서의 자동 0-채움 분기에 `KeyError` 가능성(2.2, KooMeshModifier.py:1271-1294), (b) 리스트 길이 불일치 검증 부재, (c) 저장소 내 예제/테스트 부재로 인해 **실모델 end-to-end 동작은 미검증**. → 한 PID에 X/Y/Z 전부 + 동일 길이 리스트로 사용하는 정상 경로 한정 "구현됨"으로 판단하며, 부분 축 입력 경로는 "확인 필요".
