# KooMeshModifier 모드: MATERIAL_EXCHANGE

> 근거 코드:
> - `occProject/Generators/KooMeshModifier.py`
> - `occProject/Generators/KooCAEManager/KooDynaAdvancedModification.py`
> - `occProject/Generators/KooCAEManager/KooMaterial.py`
> - `occProject/Generators/KooCAEManager/KooOperator.py`

## 1. 목적/개요

`MATERIAL_EXCHANGE` 모드는 입력 .k 안에 사용자가 명시한 **재료 카드(material keyword) 템플릿**을 받아, 그 안에 들어간 **변수 토큰(variable token)** 을 사용자가 나열한 값 리스트로 치환해 가며 **값 하나당 하나씩 별도의 .k 파일**을 생성한다. 즉 동일 모델에 대해 재료 물성(예: 항복강도, 탄성계수 등)만 바꾼 여러 변형(variation) .k 파일을 자동으로 찍어내는 **재료 물성 DOE/스윕(sweep)** 용도이다.

치환된 재료는 `matManager.AddMaterialfromDyna()` 로 등록되며, 각 변형마다 전체 모델이 재료가 교체된 상태로 `*Keyword … *End` 형식의 .k 파일로 기록된다 (KooDynaAdvancedModification.py:4895-4898).

> 참고: 전용 예제 파일 없음. 본 문서는 코드 근거로만 작성됨. (Examples 디렉터리에 `material_exchange` 관련 입력/시나리오 파일 부재 확인.)

## 2. 입력 옵션·인자 (표)

입력은 KooMeshModifier 입력 .k(제어 파일)의 두 블록으로 나뉜다.

### 2-1. `*mode` 블록 (모드 등록 트리거)

`*mode` 블록 안에 한 줄로 모드를 등록한다 (KooMeshModifier.py:234-251).

| 토큰 | 의미 | 비고 |
|------|------|------|
| `material_exchange` | 모드 식별자 (대소문자 무관, `svector[0]`) | line 249 |
| `<modeID>` | 모드 ID (정수, `svector[1]`) | `**materialexchange` 옵션 블록과 매칭되는 키 (line 251) |

형식: `material_exchange,<modeID>`

### 2-2. `**materialexchange,<modeID>` 옵션 블록

옵션 블록은 `**materialexchange,<modeID>` 로 시작하고 `**end` 로 끝난다 (KooMeshModifier.py:1645-1695). 내부에 `*varlist` 와 `*mid` 하위 블록을 둔다.

| 하위 키워드 | 형식 | 의미 | 근거 |
|-------------|------|------|------|
| `*varlist,<varname>,<v1>,<v2>,...` | 콤마 구분 | 변수 이름과 그 변수에 대입할 값 리스트. 값들은 `KooDynaFloat` 로 파싱됨. `curOptions["Vars"][<varname>]` 에 저장 | line 1659-1667 |
| `*mid,<keyword_name>` | 콤마 구분 헤더 + 다음 줄들 | 치환 대상 재료 카드 본문. 헤더 다음 줄부터 `*` 가 나올 때까지를 카드 본문으로 읽음 | line 1670-1692 |
| (재료 카드 본문) | 고정폭 10칼럼 | `parse_whole(line, [10]*8)` 로 각 줄을 8개 10폭 필드로 분해 | line 1689-1690 |
| `$` 로 시작하는 줄 | 주석 | `*mid` 본문 읽기 중 건너뜀 | line 1684-1685 |

세부 동작 메모:
- 변수 토큰 매칭은 **`format(varname, '>10')`**(폭 10, 우측 정렬) 한 문자열과 재료 카드 필드를 **완전 일치**로 비교한다 (KooMeshModifier.py 1689 의 10폭 파싱 + KooDynaAdvancedModification.py:4873, 4887). 즉 재료 카드 템플릿 안에서 바꾸고 싶은 필드에는 변수 이름을 적어두고, 그 이름이 10폭 필드에 그대로 들어가야 매칭된다. **확인 필요**: 변수 이름 길이/공백 패딩이 정확히 10폭 필드와 일치해야 하므로 사용자가 폭을 맞춰 입력해야 한다.
- `*mid` 헤더 이름에 `title` 이 포함된 경우 첫 본문 줄은 분해 없이 통째로(`[line]`) 저장한다 (line 1686-1687) — `*MAT_..._TITLE` 카드의 제목 줄 처리.
- 여러 `*mid` 블록을 둘 수 있으나, 파서가 `curOptions["MIDs"][name] = curKeyword` 를 루프 종료 후 한 번만 대입하므로 **마지막 `*mid` 블록만 저장될 수 있음** (line 1692 가 while 루프 밖에 위치). **확인 필요**: 다중 `*mid` 동시 등록은 의도대로 동작하지 않을 가능성. 단일 재료 카드 사용 권장.

## 3. 사용 예제

> 전용 예제 파일이 저장소에 없어, 아래는 **코드의 파서/치환 규칙(KooMeshModifier.py:1645-1695, KooDynaAdvancedModification.py:4858-4898)에서 역산한 최소 형식 예시**이다. 실제 입력 작성 시 칼럼 폭(10) 정렬에 주의할 것.

KooMeshModifier 제어 .k (개념 예시):

```
*mode
material_exchange,1
*
**materialexchange,1
*varlist,SIGY,    1.0e2,    1.5e2,    2.0e2
*mid,*MAT_PIECEWISE_LINEAR_PLASTICITY
$#     mid        ro         e        pr      sigy      etan
         1   7.8e-9    2.1e5      0.3      SIGY       0.0
**end
*end
```

- `*varlist,SIGY,...` : 변수 `SIGY` 에 3개 값(1.0e2 / 1.5e2 / 2.0e2)을 정의.
- `*mid,*MAT_...` : 재료 카드 템플릿. `sigy` 필드에 변수 이름 `SIGY`(10폭 정렬) 를 둠.
- 결과: 값 3개 각각에 대해 `SIGY` 가 치환된 .k 파일 3개 생성.

출력 파일명은 `<입력파일경로>_<varname>_<값>.k` 형태로 만들어진다 (KooDynaAdvancedModification.py:4890-4893). 예: 입력이 `model.k` 이고 변수가 `SIGY`, 값이 `1.000e+02` 이면 대략 `model_      SIGY_ 1.000e+02.k` (변수명/값 문자열이 10폭/`>10.3e` 포맷으로 들어가 공백 포함).

## 4. 동작 원리 (코드 근거)

1. **모드 등록** — `*mode` 블록에서 `material_exchange` 토큰을 만나면 `modeList` 에 `"MATERIAL_EXCHANGE"`, `modeIDList` 에 모드 ID 추가
   - `KooMeshModifier.py:249-251`
2. **옵션 파싱** — `**materialexchange,<modeID>` 블록을 읽어 `curOptions["Vars"]`(변수→값 리스트)와 `curOptions["MIDs"]`(재료 카드 본문)를 구성, `self.modeIDOption[curModeID]` 에 저장
   - `KooMeshModifier.py:1645-1695`
   - 값 파싱: `KooDynaFloat` (`KooOperator.py:23-31`, 비수치/빈값은 기본 0.0)
   - 카드 본문 줄 파싱: `parse_whole(line, [10,10,10,10,10,10,10,10])` (`KooMeshModifier.py:1689`)
3. **디스패치** — `GenerateModifiedFile()` 루프에서 `mode == "MATERIAL_EXCHANGE"` 분기 → `GenerateMaterialExchange(modeid)` 호출, 파일명 접미사 `_mex` 누적
   - `KooMeshModifier.py:2789-2791`
4. **핸들러** — `GenerateMaterialExchange` 는 입력 파일 경로(확장자 `.k` 제거)와 옵션을 묶어 `advancedModification.MaterialExchange(curOption, filePath)` 호출
   - `KooMeshModifier.py:2518-2523`
5. **치환·생성 본체** — `MaterialExchange(option, filePath)`
   - 변수 리스트 중 첫 변수의 길이를 `size` 로 잡아 그 횟수만큼 반복 (`KooDynaAdvancedModification.py:4866-4869`)
   - 각 반복에서 변수별 현재 값을 취함. 인덱스가 리스트 길이를 넘으면 **마지막 값으로 채움**(클램프) (line 4874-4877)
   - 재료 카드를 `copy.deepcopy` 한 뒤, 필드가 `format(varname,'>10')` 와 일치하면 `format(curVal,'>10.3e')` 로 치환 (line 4882-4888)
   - 치환된 카드를 `matManager.AddMaterialfromDyna(modifiedMatKeyword)` 로 등록 (line 4889) — 카드 종류별 처리는 `KooMaterial.py:1156` `AddMaterialfromDyna`
   - 변수/값을 이어붙여 파일명 접미사 생성 후 `<filePath><suffix>.k` 로 전체 모델 기록: `*Keyword` + `WriteStreamDynaKeyword()` + `*End` (line 4890-4898)
6. **기본 출력 동반** — `MATERIAL_EXCHANGE` 는 `_skip_default_write` 를 설정하지 않으므로, 위 변형 .k 들과 **별개로** 기본 `WriteModifiedFile(additionalword)`(접미사 `_mex`)도 실행됨
   - `KooMeshModifier.py:2883-2888`, `2906-2914`

## 5. 주의사항·한계

- **변수 토큰은 10폭 필드 완전 일치로만 치환**된다 (KooDynaAdvancedModification.py:4873, 4887). 재료 카드 템플릿에서 변수 이름을 정확히 10칼럼 폭에 맞춰 배치하지 않으면 치환이 일어나지 않는다. **확인 필요** (폭 패딩 규칙은 사용자 입력 책임).
- **치환 값 포맷이 `>10.3e` 로 고정**(유효숫자 3자리 지수 표기)된다 (line 4883). 정밀도가 필요한 값은 손실될 수 있다.
- **다중 `*mid` 블록은 마지막 것만 저장될 수 있음** — `curOptions["MIDs"][name] = curKeyword` 가 while 루프 밖에서 한 번만 실행됨 (KooMeshModifier.py:1692). 한 모드에 재료 카드 하나만 두는 것을 권장. **확인 필요**.
- **반복 횟수는 첫 번째 변수의 값 개수로 결정**된다 (line 4866-4867). 변수별 값 개수가 다르면 짧은 변수는 마지막 값으로 클램프되고 (line 4874-4877), 첫 변수보다 긴 변수의 초과 값은 무시된다.
- 비수치/빈 값은 `KooDynaFloat` 기본값 `0.0` 으로 들어간다 (KooOperator.py:23-31) — 오타 시 0으로 조용히 대체될 수 있음.
- 출력 파일명에 변수명/값 포맷 문자열(공백 포함 10폭)이 그대로 들어가 **파일명에 공백이 포함**될 수 있다 (line 4890-4893). **확인 필요** (후속 스크립트에서 경로 처리 주의).
- 변형 .k 외에 기본 `_mex.k` 도 함께 생성된다 (5.6항 참조).

## 6. 개발 현황

**구현됨.**

근거: `*mode` 등록부(KooMeshModifier.py:249-251), 옵션 블록 파서(1645-1695), 디스패치 분기(2789-2791), 핸들러(2518-2523), 치환·파일 생성 본체(KooDynaAdvancedModification.py:4858-4898)가 모두 존재하며 동작 경로가 연결되어 있다.

단, **전용 예제/시나리오 파일이 저장소에 없어 실사용 검증 근거는 미확인**이며, 다중 `*mid` 처리·10폭 정렬 의존성 등 일부 동작은 본문 "확인 필요" 표기 참조.
