# 상류 수정 PR 자료 (KooD3plotReader 후처리 팀 → pyKooCAE)

## 브랜치
`fix/drop-attitude-corner-and-label` — origin 에 push 완료 (a13c2de)

커밋 3개
- `97ca863` fix(angles): 코너 8케이스 9.74° 오차 + 회귀 테스트 30건
- `bd62551` fix(runner): DropSet 라벨 전 런 고정 + corner_map 단일화
- `a13c2de` docs(upstream): 보고서 동봉

## PR 생성
이 환경의 `gh` CLI 는 snap 격리 문제로 실행되지 않고 `GH_TOKEN` 도 만료라
자동 생성하지 못했습니다. 아래 링크로 만들면 됩니다.

  https://github.com/squall321/pyKooCAE/pull/new/fix/drop-attitude-corner-and-label

제목
  fix(angles,runner): 코너 낙하 9.74° 오차 + DropSet 라벨 전 런 고정

본문
  `PR_BODY.md` 내용을 그대로 붙여넣으면 됩니다.

## 파일
- `PR_BODY.md` — PR 본문
- `01-corner-angles.patch` — 코너 각도만 담은 단독 패치 (참고용, 브랜치에 이미 반영됨)
- `../UPSTREAM_ISSUES_FROM_KooD3plotReader.md` — 근거·실측·수학 유도 전문
