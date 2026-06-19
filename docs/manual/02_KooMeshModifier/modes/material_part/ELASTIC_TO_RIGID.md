# KooMeshModifier 모드: ELASTIC_TO_RIGID

## 1. 목적/개요

`ELASTIC_TO_RIGID`는 모델에 정의된 **모든 재료(material)를 강체 재료(`*MAT_RIGID`)로 일괄 치환**하는 KooMeshModifier 모드이다. 변형 거동이 중요하지 않은 단계(예: 초기 자세 정렬, 강체 충격추, 빠른 사전 검증)에서 변형체를 강체로 단순화하여 계산을 가볍게 하거나 거동을 단순화하는 데 사용된다.

핵심 동작 3단계는 다음과 같다 (`KooMeshModifier.py:2513-2515`):

1. 재료 매니저의 모든 재료를 강체로 교체 (`ExchangetoRigid`)
2. 파트가 새 강체 재료를 참조하도록 갱신 (`UpdateMaterial`)
3. 모든 강체 파트를 하나의 강체 그룹으로 묶는 `*CONSTRAINED_RIGID_BODIES` 자동 생성 (`GenerageConstraintforAllRigidBodies`)

`*PIDExcept` 옵션으로 지정한 파트는 치환 대상에서 제외할 수 있다.

> 주의: 전체 재료를 강체로 바꾸고 모든 강체를 하나로 묶기 때문에, 이 모드는 "모델 전체를 (일부 파트를 제외한) 단일 강체로 만든다"에 가깝다. (구현 근거 → 4절)

---

## 2. 입력 옵션·인자 (표)

KooMeshModifier는 옵션 텍스트 파일(예: `ElasticToRigidOption.txt`)을 `ImportOption()`으로 읽는다 (`KooMeshModifier.py:154`). 파일 내 구조는 아래와 같다.

| 키워드 / 인자 | 위치 | 형식 | 설명 | 근거 (file:line) |
|---|---|---|---|---|
| `*Inputfile` | 헤더 | 다음 줄에 `.k` 파일명 | 수정 대상 LS-DYNA 입력 파일 | `KooMeshModifier.py:163-166` |
| `*Mode` → `ELASTIC_TO_RIGID,<modeID>` | 모드 목록 | `이름,정수ID` | 이 모드를 실행하도록 등록. `<modeID>`는 옵션 블록과 매칭되는 정수 | `KooMeshModifier.py:246-248` |
| `**ElastictoRigid,<modeID>` | 옵션 블록 시작 | `이름,정수ID` | `<modeID>`에 해당하는 옵션 블록 헤더 (대소문자 무시) | `KooMeshModifier.py:1329-1332` |
| `*PIDExcept,<pid1>,<pid2>,...` | 옵션 블록 내부 | `이름,정수PID...` | 강체 치환에서 **제외할 파트 ID 목록**. 여러 PID를 콤마로 나열 | `KooMeshModifier.py:1341-1345` |
| `**EndElastictoRigid` 또는 빈 줄 | 옵션 블록 종료 | — | 옵션 블록 종료 조건 | `KooMeshModifier.py:1337-1340` |
| `*End` | 파일 종료 | — | 옵션 파일 전체 종료 | `KooMeshModifier.py:161-162` |

옵션 파싱 결과는 `curOptions["PIDExcept"] = exceptPidList` 형태의 딕셔너리로 저장된다 (`KooMeshModifier.py:1345-1346`). `*PIDExcept` 줄이 없으면 `PIDExcept`는 빈 리스트가 되어 **모든 재료가 강체로 치환**된다.

> 확인 필요: 위 옵션 파일은 KooMeshModifier 단독 실행 시의 입력 형식이다. scenario.json / KooChainRun 워크플로우에서 이 모드를 직접 노출하는지는 본 파일 범위 밖이라 확인되지 않음.

---

## 3. 사용 예제

전용 예제(`Examples/` 하위)는 존재하지 않는다. 대신 코드 배포본의 샘플 옵션 파일을 그대로 인용한다.

### 예제 A — 단독 모드 (`ElasticToRigid_Test.txt`)

출처: `occProject/Generators/dist/Examples/5.SimulationModify/ElasticToRigid_Test.txt`

```
*Inputfile
Impact_1_00000001.k
*Mode
ELASTIC_TO_RIGID,1
**ElastictoRigid,1
*PIDExcept,5
**EndElastictoRigid
*End
```

- 입력 파일 `Impact_1_00000001.k`의 재료를 강체로 치환하되, **PID 5는 제외**.
- 모드 ID `1`이 `*Mode`의 `ELASTIC_TO_RIGID,1`과 `**ElastictoRigid,1` 블록을 연결한다.

### 예제 B — 다른 모드와 연계 (`ElasticToRigidOption.txt`)

출처: `occProject/Generators/dist/Examples/5.SimulationModify/ElasticToRigidOption.txt`

```
*Inputfile
Impact_1_00000001.k
*Mode
ELASTIC_TO_RIGID,1
PART_EXCHANGE,2
**ElastictoRigid,1
*PIDExcept,5
**EndElastictoRigid
**PartExchange,2
*PID,5
*SECTION_SOLID_TITLE
ImpactBallSection
$$   SECID    ELFORM       AET    COHOFF   GASKETT
       SID         1
*MAT_ELASTIC_TITLE
Steel
$$     MID        RO         E        PR        DA        DB         K
       MID 1.100e+03 2.413e+09 3.700e-01
**EndPartExchange
*End
```

- `ELASTIC_TO_RIGID`(ID 1)로 PID 5를 제외한 전체를 강체화한 뒤, `PART_EXCHANGE`(ID 2)로 PID 5에 탄성(Steel) 재료/섹션을 재할당하는 조합. 즉 "PID 5만 탄성 충격구로 남기고 나머지는 강체"라는 시나리오.
- 모드는 `*Mode`에 나열된 순서대로 실행된다 (`KooMeshModifier.py:2783-2787`).

---

## 4. 동작 원리 (코드 근거)

### 4.1 디스패치

`GenerateModifiedFile()`이 등록된 모드를 순회하며 `ELASTIC_TO_RIGID`일 때 `GenerateElasticToRigid(modeid)`를 호출하고, 출력 파일명에 `_etor` 접미사를 붙인다 (`KooMeshModifier.py:2786-2788`).

### 4.2 핵심 처리: `GenerateElasticToRigid`

`KooMeshModifier.py:2501-2515`:

```python
def GenerateElasticToRigid(self, modeid):
    curOption = self.modeIDOption[modeid]
    curPIDExcept = curOption["PIDExcept"]
    curMIDExcept = []
    for pid in curPIDExcept:
        if pid not in self.dynaImporter.partManager.parts:
            continue
        part = self.dynaImporter.partManager.parts[pid]
        if part.mid != 0:
            curMIDExcept.append(part.mid)

    self.dynaImporter.matManager.ExchangetoRigid(curMIDExcept)
    self.dynaImporter.partManager.UpdateMaterial(self.dynaImporter.matManager)
    self.dynaImporter.constrainedManager.GenerageConstraintforAllRigidBodies(self.dynaImporter.partManager, 1)
```

- **PID → MID 변환**: `*PIDExcept`로 받은 것은 파트 ID이지만, 제외 단위는 재료 ID(MID)이다. 각 제외 PID의 파트에서 `part.mid`를 읽어 `curMIDExcept`(제외 재료 목록)로 변환한다 (`KooMeshModifier.py:2504-2511`). 존재하지 않는 PID나 `mid==0`인 파트는 무시된다.

### 4.3 재료 강체화: `ExchangetoRigid` / `GenerateRigidMaterials`

`KooMaterial.py:976-979`에서 `GenerateRigidMaterials`로 강체 재료 딕셔너리를 만든 뒤, 현재 재료 목록을 강체 목록으로 교체한다(원본은 `tmpMaterials`에 보관).

`KooMaterial.py:958-974` — 제외 MID가 아닌 모든 재료에 대해, 원본 재료의 `E`, `nu`, `rho`를 그대로 가져와 **동일 MID의** `KooMaterialRigid`를 생성한다:

```python
for matid in self.materials:
    ...  # curMIDExcept 에 속하면 skip
    mat = self.materials[matid]
    E = mat.GetE(); nu = mat.GetNu(); rho = mat.GetRho()
    name = "Rigid" + mat.name
    newRigidMat = KooMaterialRigid(matid, name, rho, E, nu)
    self.rigidMaterials[matid] = newRigidMat
```

- 강체 재료는 **같은 MID를 재사용**하고 이름 앞에 `Rigid` 접두어를 붙인다.
- 보존되는 물성은 밀도(RO), 탄성계수(E), 푸아송비(PR)뿐이며, 나머지 `*MAT_RIGID` 파라미터(CMO, CON1/2, 구속 플래그 등)는 `KooMaterialRigid` 기본값(대부분 0)으로 생성된다 (`KooMaterial.py:402-420`).

### 4.4 파트 재료 갱신: `UpdateMaterial`

`KooPart.py:3027-3035` — 각 파트의 `material.id`(MID)가 강체화된 재료 목록에 있으면 해당 강체 재료로 `SetMaterial` 한다. 동일 MID를 재사용하므로 파트는 자동으로 강체 재료를 가리키게 된다. (`KooPartComposite`는 별도 분기로 두지만 본문에서 추가 처리는 없음 — 확인 필요)

### 4.5 강체 통합: `GenerageConstraintforAllRigidBodies`

`KooConstrained.py:675-697` — 파트 매니저를 순회하여 재료 타입이 `KooMaterialRigid`인 파트를 모두 모은 뒤(`rigidList`), 첫 번째 파트를 마스터(`pidL`)로 삼고 나머지 파트를 종속(`pidC`)으로 하는 `*CONSTRAINED_RIGID_BODIES`를 `iflag=1`로 생성한다. 즉 **모든 강체 파트가 하나의 강체로 묶인다**. 강체 파트가 없으면 메시지만 출력하고 종료한다.

### 4.6 출력

별도 출력 핸들러를 두지 않으므로 기본 경로를 탄다. `GenerateModifiedFile`이 `WriteModifiedFile("_etor")`를 호출하여 (`KooMeshModifier.py:2885-2888`), 입력 파일명 뒤에 `_etor`를 붙인 `.k` 파일로 저장한다 (`KooMeshModifier.py:2906-2932`). 예: `Impact_1_00000001.k` → `Impact_1_00000001_etor.k`. 강체화된 `*MAT_RIGID_TITLE` 재료와 자동 생성된 `*CONSTRAINED_RIGID_BODIES` 카드가 포함된다.

---

## 5. 주의사항·한계

- **전체 강체화 + 단일 통합**: 제외 파트를 빼면 모델 내 모든 재료가 강체가 되고, 모든 강체 파트가 하나의 `*CONSTRAINED_RIGID_BODIES`로 묶인다 (`KooConstrained.py:692-697`). 부분적으로만 강체화하려면 `*PIDExcept`로 남길 파트를 명시해야 한다.
- **제외 단위는 재료(MID)**: 입력은 PID이지만 내부적으로 그 파트의 MID로 변환되어 제외된다 (`KooMeshModifier.py:2504-2511`). **동일 MID를 공유하는 다른 파트도 함께 제외**되는 점에 유의.
- **존재하지 않는 PID / mid==0 무시**: 잘못된 PID나 재료가 없는 파트는 조용히 건너뛴다 (경고 없음) (`KooMeshModifier.py:2507-2510`).
- **물성 보존 범위 제한**: E/nu/rho만 원본에서 가져오며, 그 외 `*MAT_RIGID` 옵션은 기본값으로 생성된다 (`KooMaterial.py:973`, `402-420`). 특정 강체 구속(CMO/CON) 설정이 필요하면 후처리가 필요하다.
- **Composite 파트**: `UpdateMaterial`에서 `KooPartComposite`는 별도 분기로 갈라지지만 강체 재료 재할당 로직이 보이지 않는다 — composite 파트의 강체화 동작은 확인 필요 (`KooPart.py:3029-3035`).
- **scenario.json 노출 여부 확인 필요**: 본 모드의 정식 입력 경로는 옵션 텍스트 파일이며, 상위 워크플로우(KooChainRun scenario.json)에서의 직접 노출 여부는 본 파일 근거만으로 확정 불가.

---

## 6. 개발 현황

**구현됨**

근거:
- 입력 트리거 등록 (`KooMeshModifier.py:246-248`), 옵션 블록 파싱 (`KooMeshModifier.py:1329-1346`), 디스패치 (`KooMeshModifier.py:2786-2788`), 핵심 메서드 `GenerateElasticToRigid` (`KooMeshModifier.py:2501-2515`)가 모두 존재.
- 하위 처리 `ExchangetoRigid`/`GenerateRigidMaterials` (`KooMaterial.py:958-979`), `UpdateMaterial` (`KooPart.py:3027-3035`), `GenerageConstraintforAllRigidBodies` (`KooConstrained.py:675-697`) 구현 확인.
- 동작 가능한 샘플 옵션 파일 2종 존재 (`dist/Examples/5.SimulationModify/ElasticToRigid_Test.txt`, `ElasticToRigidOption.txt`).

단, 전용 회귀 예제(`Examples/` 하위)와 자동화/CI 검증 흔적은 발견되지 않았다 — 검증 커버리지는 확인 필요.
