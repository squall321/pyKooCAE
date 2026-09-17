# SmartTwinPreprocessor 전 도구 `--help` — 모드별 사용법 + 검색 + 검증된 사례

## 1. 요구
모든 SmartTwinPreprocessor 도구의 `--help` 에 각 모드 사용법을 넣는다.
`--help <검색어>` 로 특정 모드를 찾으면 **실제로 돌아가는 사례**를 함께 보여 LLM 이 사용법을 바로 알게 한다.

## 2. 현황 (2026-09-17 실측)

| 도구 | 지금 `--help` | 모드 |
|---|---|---|
| KooMeshModifier | 🔴 `--help` 를 옵션 파일명으로 받아 **멈춤** + `--help.log` 생성 | 32 |
| KooAutomatedModeller | 🔴 **기동 즉시 FileNotFoundError** — 배포본이 4월 빌드(re-exec 가드 전). 전 모드 사용 불가 | 7 |
| KooChainRun | argparse 서브커맨드만. scenario.json 모드·키 설명 없음 | 11 서브커맨드 + 시나리오 모드 |
| KooRemapper (C++) | 명령 목록 + `help <명령>`(41 중 36 상세). 검색 없음, `<명령> --help` 은 오류 | 41 |

## 3. 설계

### 공통 CLI 계약 (네 도구 동일)
```
TOOL --help                 개요 + 모드 목록(한 줄 요약) + 검색법
TOOL --help <검색어...>     모드 이름 정확 일치 → 상세 / 아니면 이름·별칭·요약·키 검색
TOOL --help all             전 모드 상세 (LLM 이 한 번에 읽기용)
TOOL --help format          입력 파일 형식 등 공통 주제
```
- help 처리는 **무거운 import(OCC·Qt) 전에** 한다 — 빠르고, 환경 문제로 죽지 않게.
- 파일을 만들지 않는다. exit 0.

### 상세 항목 구성 (LLM 이 읽기 좋은 고정 구조)
`이름 / 요약 / 언제 쓰나 / 입력 키 표(키·형식·기본값·필수·뜻) / 사례(그대로 복사해 쓰는 전체 입력) / 주의 / 관련 모드`

### 정확성 원칙
- 키·기본값은 **파서 코드에서** 뽑는다. 기존 매뉴얼·옛 예제는 참고만 — "재구성·확인 필요" 표기와 코드가 모르는 키명(옛 DropWeightImpactTest.txt 의 `YoungModulus`·`Density`)이 섞여 있다. (TRANSFORM 은 매뉴얼의 `Translation` 이 맞고 `Translate` 는 무시된다 — 처음 판단 정정)
- **모든 사례는 실제로 돌려 검증**하고, 검증 스크립트를 회귀 시험으로 남긴다.
  - KMM: 사례 옵션 파일을 실제 파서로 읽어 모드 등록·키 인식 확인 + 대표 모드는 컴파일 바이너리 e2e
  - KAM: 사례 입력으로 실제 바이너리 실행
  - KooChainRun: 사례 scenario.json 을 배포 바이너리 `prepare`
  - KooRemapper: 사례 YAML 을 실제 바이너리로 실행

## 4. 단계
- P0 공통 엔진 (Python) — `occProject/Generators/KooCLIHelp/`
- P1 KMM 카탈로그 (32) + 검증
- P2 KAM 카탈로그 (7) + 검증 + 🔴 배포본 기동 불가 해소(재빌드)
- P3 KooChainRun 주제(시나리오 모드·키·후처리) + 검증
- P4 KooRemapper(C++) 검색·`<명령> --help`·부족한 5개 사례
- P5 전체 빌드 → SIF → tar → node001, 배포 바이너리로 help e2e
