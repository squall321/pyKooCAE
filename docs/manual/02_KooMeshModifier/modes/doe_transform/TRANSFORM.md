# KooMeshModifier 모드: TRANSFORM

## 1. 목적 / 개요

`TRANSFORM` 모드는 입력 LS-DYNA `.k` 모델의 **전체 절점(node)에 대해 기하 변환**(평행이동, 회전, 스케일, 미러)을 일괄 적용하는 KooMeshModifier 모드입니다.

- 한 모드 블록 안에 여러 개의 변환 명령을 **순차적으로 나열**할 수 있으며, 나열된 순서대로 누적 적용됩니다.
- 변환은 OpenCASCADE의 `gp_Trsf`(회전·미러) 또는 직접 좌표 연산(평행이동·스케일)으로 수행됩니다.
- 대상은 모델의 **모든 절점**입니다. 파트/세트별 선택 적용 기능은 코드 경로상 없습니다(아래 5장 참조).

> 참고: 동일 파일 내에 PID별 평행이동 DOE를 다루는 별도 모드 `TRANSLATION_DOE`(`**translation_doe`)가 존재합니다. `TRANSFORM`은 이와 다른 모드이며, PID 필터 없이 전체 모델을 변환합니다.

---

## 2. 입력 옵션 · 인자 (표)

입력 .k 블록 헤더는 `**transform, <modeID>` 형식이며, `**end` 또는 빈 줄까지의 각 라인이 하나의 변환 명령입니다. 각 라인은 콤마 구분이며, **키워드 매칭은 부분 문자열 기준(대소문자 무시)** 입니다.

| 명령 키워드 | 인자 (콤마 구분) | 의미 | 비고 |
|---|---|---|---|
| `translation` | tx, ty, tz | (tx,ty,tz) 만큼 평행이동 | 전체 절점 좌표에 가산 |
| `rotation` | angleX, angleY, angleZ | X→Y→Z 축 순서로 원점 기준 회전 | 각도 단위 = **도(degree)** |
| `vectorrotation` | x, y, z | X축(1,0,0)을 벡터 (x,y,z) 방향으로 정렬하는 회전 | 원점 기준 |
| `vectortovectorrotation` | x1, y1, z1, x2, y2, z2 | 벡터1 → 벡터2 로 정렬하는 회전 | 원점 기준 |
| `scale` | sx, sy, sz | 축별 배율 스케일 | **원점 기준** (5장 참조) |
| `mirror` | mode (`xy` / `yz` / `xz`) | 지정 평면에 대한 미러 + 요소 connectivity 반전 | 좌표·요소 모두 반전 |

매칭 순서 주의:
- 파서는 `if "translation" ... elif "vectortovectorrotation" ... elif "vectorrotation" ... elif "rotation" ... elif "scale" ... elif "mirror"` 순으로 검사합니다 (`KooMeshModifier.py:1308-1325`).
- `rotation` 검사가 `vectorrotation`/`vectortovectorrotation` 보다 뒤(elif)에 오므로 두 벡터 회전이 먼저 매칭되어 정상 동작합니다. 다만 `vectorrotation` 라인에도 `"rotation"` 문자열이 포함되므로, 라인 작성 시 정확한 키워드를 사용해야 의도한 분기로 들어갑니다.

수치 파싱: 인자는 `KooDynaFloat(...)`로 변환됩니다 (`KooMeshModifier.py:1310 등`). `mirror`의 mode 인자만 문자열 그대로 저장됩니다(`KooMeshModifier.py:1325`).

---

## 3. 사용 예제

> **전용 예제 부재**: 저장소 `Examples/` 트리에서 `**transform` 블록을 사용하는 예제 파일은 발견되지 않았습니다(grep 결과 없음). 아래 블록은 **파서 코드(`KooMeshModifier.py:1297-1327`)에 근거하여 재구성한 입력 형식**이며, 가공을 최소화했습니다. 실제 동작 검증이 필요합니다("확인 필요").

KooMeshModifier 입력 .k 의 모드 블록 예 (재구성):

```
**transform, 1
translation, 0.0, 0.0, 10.0
rotation, 0.0, 0.0, 90.0
scale, 2.0, 2.0, 2.0
mirror, xy
**end
```

- 모드 등록 트리거: 헤더 라인에 `transform` 문자열이 포함되면 `modeList`에 `"TRANSFORM"`이 추가됩니다 (`KooMeshModifier.py:282-284`). 두 번째 콤마 필드(`svector[1]`)가 modeID입니다.
- 위 블록은 modeID=1 에 대해 평행이동 → 회전 → 스케일 → XY평면 미러 순으로 적용됩니다.

scenario.json / CLI 예제: TRANSFORM 모드를 직접 트리거하는 scenario.json 또는 CLI 예제는 코드/Examples에서 발견되지 않았습니다("확인 필요").

---

## 4. 동작 원리 (코드 근거)

1. **모드 등록 (입력 트리거)** — 헤더의 `svector[0]`에 `transform`이 포함되면 모드 리스트에 등록.
   - `KooMeshModifier.py:282-284`

2. **모드 블록 파싱** — `**transform, <id>` 이후 `**end`/빈 줄까지 각 라인을 `curOptions` 리스트(`[명령명, 인자...]`)로 누적, `modeIDOption[curModeID]`에 저장.
   - `KooMeshModifier.py:1297-1327`

3. **디스패치** — 실행 시 `mode == "TRANSFORM"` 분기에서 `self.Transform(modeid)` 호출, 출력 파일명 접미사 `_trans` 부여.
   - `KooMeshModifier.py:2825-2827`

4. **위임** — `Transform(modeid)` → `modeIDOption[modeid]`(옵션 리스트)을 `advancedModification.Transform(curOption)`으로 전달.
   - `KooMeshModifier.py:2497-2499`

5. **변환 실행** — `KooDynaAdvancedModification.Transform(option)`이 옵션 리스트를 순회하며 각 명령을 처리.
   - 정의: `KooDynaAdvancedModification.py:3081`
   - `translation` → `nodeMan.MoveNodes(tx,ty,tz)` (`:3086-3090`), 좌표 가산 (`KooNode.py:879-882`)
   - `rotation` → 각 축 `gp_Trsf.SetRotation`(라디안 변환 `math.radians`)을 X·Y·Z 순서로 곱(`Multiplied`)하여 `nodeMan.Transform(combinedTrsf)` (`:3091-3106`)
   - `scale` → `nodeMan.Scaling(sx,sy,sz)` (`:3107-3111`); 실제 구현은 좌표에 배율 직접 곱(`KooNode.py:913-915`)
   - `mirror` → mode(`xy`/`yz`/`xz`)에 따라 `gp_Trsf.SetMirror`로 모든 절점 변환 후, 각 파트의 `elementManager.SetMirrorConnectivity{XY,YZ,XZ}Plane()`으로 요소 connectivity 반전 (`:3112-3138`, `KooElement.py:327/358/389`)
   - `vectorrotation` → X축과 입력벡터의 외적을 회전축, 사잇각을 회전각으로 `nodeMan.Transform` (`:3139-3159`)
   - `vectortovectorrotation` → 벡터1·벡터2 외적을 축, 사잇각을 회전각으로 `nodeMan.Transform` (`:3160-3183`)

6. **출력** — 별도 `_skip_default_write` 설정이 없으므로 기본 경로로 변환된 모델을 기록: 입력 파일명 + `_trans.k` (`KooMeshModifier.py:2826-2827`, `WriteModifiedFile` `:2906-2914`).

---

## 5. 주의사항 · 한계

- **전역 적용(파트 선택 불가)**: 모든 변환은 모델 내 전체 절점에 적용됩니다. PID/세트별 선택 변환 인자는 파서·실행 코드에 없습니다 (`KooDynaAdvancedModification.py:3081-3183`). 파트별 평행이동이 필요하면 `TRANSLATION_DOE` 모드를 참고하십시오.
- **회전·스케일·미러 기준은 원점(0,0,0)**:
  - `rotation`/`vectorrotation`/`vectortovectorrotation`의 회전축은 모두 `gp_Pnt(0,0,0)` 기준 (`:3096,3099,3102,3157,3181`).
  - `scale`은 중심 기준 스케일 코드가 주석 처리되어 있고, 실제로는 좌표에 배율을 직접 곱하므로 **원점 기준 스케일**입니다 (`KooNode.py:910-915`). 모델이 원점에서 떨어져 있으면 위치까지 함께 이동·확대됩니다.
- **각도 단위**: `rotation`은 도(degree) 입력 → 내부에서 `math.radians` 변환 (`:3097,3100,3103`). `vectorrotation`/`vectortovectorrotation`은 벡터 사잇각을 그대로 사용(`gp_Vec.Angle`은 라디안 반환)하므로 각도 인자가 아닌 벡터 인자입니다.
- **vectorrotation 예외 처리**: 길이 0 벡터, 또는 입력 벡터가 정확히 X축(1,0,0)인 경우 메시지 출력 후 해당 명령을 건너뜁니다 (`:3144-3149`). `vectortovectorrotation`은 두 벡터 중 하나가 0이거나 두 벡터가 동일하면 건너뜁니다 (`:3167-3175`).
- **mirror는 좌표 + 요소 connectivity를 함께 반전**하여 요소 jacobian 부호를 보존합니다. 단, 미러 처리는 헤더에서 지원하는 평면이 `xy`/`yz`/`xz` 3종뿐이며 그 외 문자열은 무시됩니다 (`:3115-3138`).
- **키워드 부분 문자열 매칭**: 라인 키워드는 부분 문자열로 검사되므로 오타·혼동에 주의해야 합니다(2장 매칭 순서 참조).
- **예제·테스트 부재**: 본 모드에 대한 Examples/scenario.json 예제가 없어 실사용 입력 포맷의 세부(콤마 공백 허용 여부 등)는 코드 근거 외 검증되지 않았습니다("확인 필요").

---

## 6. 개발 현황

**구현됨 (부분 검증 불가)**

- 근거: 입력 트리거(`KooMeshModifier.py:282-284`), 블록 파서(`:1297-1327`), 디스패치(`:2825-2827`), 위임(`:2497-2499`), 실행 로직(`KooDynaAdvancedModification.py:3081-3183`)이 모두 존재하고 호출 체인이 연결되어 있습니다. 6개 변환(translation/rotation/vectorrotation/vectortovectorrotation/scale/mirror) 모두 코드로 구현되어 있습니다.
- 다만 전용 예제·테스트가 저장소에 없어 실행 결과의 정합성(특히 원점 기준 scale 의도 여부)은 코드 정적 분석에 기반하며, 실제 e2e 검증은 "확인 필요" 입니다.
