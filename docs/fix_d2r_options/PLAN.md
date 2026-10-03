# DEFORMABLE_TO_RIGID_AUTOMATIC 세부 옵션 개방 계획 (2026-10-03)

## 신고와 확인

"KMM 이 D2R 옵션을 고정해서 쓴다. 시나리오를 수정해도 nrbf 같은 게 반영 안 된다" — **사실이다.**
`nrbf`·`ncsf`·`rwf`·`dtmax`·`time1`·`time2`·`time3` 는 시나리오·러너·KMM 파서 어디에서도 읽지 않는다
(전수 검색 0건). `KooDynaAdditional.py:455-456` 에서 리터럴로 박혀 넘어간다.

```python
d2r = KooDeformableToRigidAutomatic(
    swset, code, 0.0, 1e20, 0.0, entno, relsw, paired,
    0, 0, 0, 0.0, d2r_pids, r2d_pids, offset)
```

카드 클래스는 14필드를 다 받는데 **매니저 계층에서 막혀** 있다.

## 목표

8개 값 필드를 시나리오에서 지정 가능하게 하고, **미지정 시 현재 리터럴이 기본값**으로 들어가
기존 모델은 회귀 0 이 되게 한다.

| 필드 | 기본값 | 의미 |
|---|---|---|
| `time1` | 0.0 | 스위치 허용 시작 시각 |
| `time2` | 1e20 | 스위치 허용 종료 시각 (현재 사실상 무제한) |
| `time3` | 0.0 | |
| `nrbf` | 0 | 강체 절점 처리 |
| `ncsf` | 0 | 접촉면 처리 |
| `rwf` | 0 | rigidwall 처리 |
| `dtmax` | 0.0 | 전환 시 최대 시간증분 |
| `offset` | 0.0 | |

## 범위 밖 — 자동 유지

`swset`·`code`·`relsw`·`paired` 는 **쌍(paired) 스위치 메커니즘**을 정의한다
(20/4/10/1 ↔ 10/2/20/-1). `entno` 는 바닥판 접촉 CID, D2R/R2D 파트 목록은 모델 전 파트다.
열면 짝이 깨진 카드를 만들 수 있어 자동으로 둔다. 필요하면 별건으로 다룬다.

## 🔴 부분일치 순서 함정 (조사로 확정)

KMM 파서 키는 **소문자 부분일치**다. 그래서 `DeformableToRigidTime1` 처럼 이름 지으면
기존 `"deformabletorigid"` 분기에 먼저 걸려 `svector[1]="0.5"` → `=="true"` → **False**,
즉 **D2R 이 조용히 꺼진다.** [[project-dtmin-erosion-divergence]] 의 "IMPACT는 dt 브랜치 위!" 와 같은 계열.

충돌 전수 검사 결과.
- `d2r` 를 포함하는 기존 키 **0건** → 접두사 `D2R` 안전
- `d2rdtmax` 안에 `dt`, `d2roffset` 안에 `et`·`ro`·`set` 이 포함되나 **전부 무해**:
  - DropAttitude 체인의 `dt` 는 `line.split(",")[0].strip().lower() == "dt"` **정확 일치**
  - `et`(621)·`ro`(637) 는 다른 모드 블록 — 기존 `DeformableToRigid` 가 "et" 를 포함하면서도
    정상 동작하는 것이 증거다
  - `set`(1766) 은 신규 삽입 위치(1656)보다 **뒤** → 신규가 먼저 평가된다

→ 키는 `D2RTime1`·`D2RNrbf` 등 **`D2R` 접두사**, 삽입 위치는 **기존 `deformabletorigid` 분기 바로 앞**.

## 단계

### P0 재현 고정
- `tests/test_d2r_options.py` — 기본값 덱 / 전필드 지정 덱 / 부분 지정 덱
- 검증: 현재 코드에서 기본값 덱이 `0.0 1e+20 0.0 … 0 0 0 0.0` 를 내는 것을 기준선으로 고정

### P1 매니저 — 인자 개방 (기본값 = 현재 리터럴)
- `CreateDeformableToRigidAutomatic(..., time1=0.0, time2=1e20, time3=0.0, nrbf=0, ncsf=0, rwf=0, dtmax=0.0)`
- 검증: 인자 미지정 호출이 기존과 **바이트 동일** 카드 생성

### P2 KMM 파서 — D2R* 키 8개
- `deformabletorigid` 분기 **앞**에 삽입
- 검증: `DeformableToRigid,True` 단독이 여전히 True (순서 함정 회귀 시험)

### P3 발행 지점 — 옵션 전달
- `KooDynaAdvancedModification.py:3042/3046` 두 호출에 옵션값 전달
- 검증: 지정값이 두 카드 모두에 반영

### P4 러너 — dict 형태 지원
- `deformable_to_rigid: true` (기존) / `{...}` (신규) 둘 다 수용
- 검증: bool 형태 출력 불변

### P5 회귀·빌드
- 기존 DROP 덱 바이트 동일, 기존 스위트 전부 통과
- KooMeshModifier 재빌드 → SIF → 메일
