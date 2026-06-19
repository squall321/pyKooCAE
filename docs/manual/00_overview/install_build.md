# 빌드 · 배포 가이드

## 1. 목적 / 개요

pyKooCAE는 세 개의 Python 모듈을 **Nuitka standalone** 으로 컴파일하여 단일 실행 바이너리(`*.bin`)로 만든 뒤, 두 곳의 배포 대상에 설치하는 구조다.

- **KooMeshModifier** — 전처리(메시 회전/contact/바닥판 생성 등)
- **KooAutomatedModeller** — 자동 모델링
- **KooChainRun** — 워크플로우 CLI (prepare/submit/status/collect 등)

빌드는 모두 프로젝트 루트의 `venv312`(Python 3.12) 가상환경을 사용하며, 컴파일된 바이너리에 더해 외부 런타임(`Library/gmsh`, `Library/Evolver`, `Library/OCC`)을 번들링한다. 빌드 산출물은 `build_dist/`에 모이고, 그대로 `appt313/opt/SmartTwinPreprocessor`(컨테이너 내부 설치 경로)와 `/data/SmartTwinPreprocessor`(공유 NFS 배포 경로)에 `sudo`로 복사된다.

실행 환경(SIF) 두 종은 별도이며 빌드 스크립트가 생성하지 않는다(아래 5장 참조):
- `SmartTwinPreprocessor.sif` — 전처리(KooMeshModifier) 실행 환경 (mesh)
- `SmartTwinPostprocessor.sif` — 후처리(KooD3plotReader) 실행 환경 (post)

근거: `build_all_python312.sh:60-142`(3모듈 Nuitka 빌드), `build_all_python312.sh:165-201`(Library 번들), `build_all_python312.sh:237-311`(2곳 배포), `docs/FullAngleDrop_HPC_Workflow.md:23-24`(SIF 역할).

## 2. 입력 옵션 · 인자 (표)

### 2.1 빌드 스크립트별 역할

| 스크립트 | 빌드 대상 | 배포 | 근거 (file:line) |
|---|---|---|---|
| `build_all_python312.sh` | KooMeshModifier + KooAutomatedModeller + KooChainRun (3모듈 전부) + Library(gmsh/Evolver/OCC) | `appt313/opt/SmartTwinPreprocessor` + `/data/SmartTwinPreprocessor` (3모듈 + Library) | 빌드 `build_all_python312.sh:60-142`, Library `:165-201`, 배포 `:237-311` |
| `build_without_automatedmodeller.sh` | KooMeshModifier + KooChainRun (KooAutomatedModeller는 기존 빌드 백업·복원) + Library | 위 2곳 (KooChainRun + KooMeshModifier + Library; AutomatedModeller 미배포) | 빌드 `build_without_automatedmodeller.sh:66-123`, 백업/복원 `:41-44`,`:126-132`, 배포 `:194-249` |
| `build_KooChainRun_python312.sh` | KooChainRun 단독 | 위 2곳 (KooChainRun만) | 빌드 `build_KooChainRun_python312.sh:39-55`, 배포 `:79-121` |
| `occProject/Generators/build_automatedmodeller_python312.sh` | KooAutomatedModeller 단독 | **배포 없음** — `occProject/Generators/KooAutomatedModeller.dist/`에만 생성 | 빌드 `build_automatedmodeller_python312.sh:23-33`, 산출 `:39-40` |

> 참고: `build_automatedmodeller_python312.sh`는 cwd 기준 `KooAutomatedModeller.dist` 로만 출력하고 SmartTwinPreprocessor 설치/배포 단계가 없다(`build_automatedmodeller_python312.sh:35-47`). `build_dist/`로의 재배치나 `sudo` 설치는 `build_all_*`/`build_without_*` 의 `mv KooAutomatedModeller.dist ...` 단계에서만 일어난다(`build_all_python312.sh:101-102`).

### 2.2 명령행 인자

| 인자 | 적용 스크립트 | 동작 | 근거 |
|---|---|---|---|
| (없음) | 전부 | INCREMENTAL — Nuitka 캐시 보존, 변경 모듈만 재빌드 | `build_all_python312.sh:28-30`,`:45-47` |
| `--clean` | `build_all`, `build_without_automatedmodeller`, `build_KooChainRun` | CLEAN — `*.build`/`*.dist`/`.nuitka` 캐시 삭제 후 전체 재빌드 | `build_all_python312.sh:9-12`,`:40-44` / `build_KooChainRun_python312.sh:30-35` |

> `build_automatedmodeller_python312.sh` 는 `--clean` 옵션이 없고 항상 `KooAutomatedModeller.build/.dist/.nuitka` 를 지운 뒤 빌드한다(`build_automatedmodeller_python312.sh:18-19`).

### 2.3 공통 Nuitka 옵션

| 옵션 | 의미 | 적용 모듈 |
|---|---|---|
| `--standalone` | 의존성 포함 독립 실행 디렉토리(`*.dist`) 생성 | 전부 |
| `--enable-plugin=pyqt5` | PyQt5 플러그인 | KooMeshModifier, KooAutomatedModeller |
| `--include-package=OCC / vtk / vtkmodules / trimesh` | 패키지 포함 | KooMeshModifier, KooAutomatedModeller |
| `--include-package-data=trimesh` | trimesh 데이터 포함 | KooMeshModifier, KooAutomatedModeller |
| `--include-package=Runner` + `--include-module=Runner.*` | Runner 패키지 및 개별 모듈 명시 포함 | KooChainRun |
| `--jobs=8` | 병렬 컴파일 8 잡 | 전부 |
| `--follow-imports` | import 추적 | 대부분 |
| `--show-progress` | 진행률 표시 | 전부 |

근거: KooMeshModifier `build_all_python312.sh:60-70`, KooChainRun `:112-135`(개별 `--include-module` 목록 포함), KooAutomatedModeller `:85-95`.

## 3. 사용 예제 (실제 CLI 명령)

### 3.1 전체 빌드 (3모듈 + 배포)
```bash
# 프로젝트 루트에서. sudo 필요 (배포 cp).
bash build_all_python312.sh           # incremental
bash build_all_python312.sh --clean   # 캐시 삭제 후 전체 재빌드
```
근거: 사용법 주석 `build_all_python312.sh:3-5`.

### 3.2 KooAutomatedModeller 제외 빌드 (전처리 변경 시 빠른 재빌드)
```bash
bash build_without_automatedmodeller.sh           # incremental
bash build_without_automatedmodeller.sh --clean
```
근거: `build_without_automatedmodeller.sh:4-6`. (KooAutomatedModeller 기존 빌드를 `/tmp/...AutoMod_backup_$$` 로 백업했다가 복원: `:41-44`, `:126-132`)

### 3.3 KooChainRun 단독 빌드 (CLI 코드만 수정했을 때)
```bash
bash build_KooChainRun_python312.sh           # incremental
bash build_KooChainRun_python312.sh --clean
```
근거: `build_KooChainRun_python312.sh:3-5`.

### 3.4 빌드 후 검증 / 환경 설정
```bash
# build_all 스크립트가 마지막에 안내하는 검증·환경 설정
build_dist/bin/KooMeshModifier --help
build_dist/bin/KooAutomatedModeller --help
build_dist/bin/KooChainRun --version

export PATH=<...>/SmartTwinPreprocessor/bin:$PATH
```
근거: 검증 명령 `build_all_python312.sh:227-230`, PATH 안내 `:324-325`. 배포 직후 `--version` 자동 호출: `:276`, `:310`.

## 4. 동작 원리 (코드 근거)

### 4.1 venv312 사용
모든 빌드는 프로젝트 루트의 `venv312` 인터프리터로 Nuitka를 호출한다.
- 루트 모듈: `./venv312/bin/python -m nuitka ...` (`build_all_python312.sh:60`, `:112`)
- `occProject/Generators` 안에서는 상대경로: `../../venv312/bin/python -m nuitka ...` (`build_all_python312.sh:60`, `build_automatedmodeller_python312.sh:23`)
- 빌드 시작 시 버전 확인: `Python: $(./venv312/bin/python --version)` (`build_all_python312.sh:24`)

> 실측: `venv312`는 Python 3.12.12 (`./venv312/bin/python --version` 실행 확인).

### 4.2 디렉토리 재배치와 symlink
각 모듈은 `*.dist` 로 컴파일된 뒤 `build_dist/lib/<모듈>` 로 옮겨지고, `build_dist/bin/<모듈>` 은 `../lib/<모듈>/<모듈>.bin` 를 가리키는 상대 symlink로 만든다.
- KooMeshModifier: `mv KooMeshModifier.dist .../lib/KooMeshModifier` + `ln -sf ../lib/.../KooMeshModifier.bin .../bin/KooMeshModifier` (`build_all_python312.sh:76-77`)
- KooChainRun: `build_all_python312.sh:141-142`
- KooChainRun 엔트리는 `.py` 확장자 없는 `KooChainRun/KooChainRun` 파일을 직접 빌드한다(`build_all_python312.sh:112` 의 `./KooChainRun`).

### 4.3 Library(gmsh / Evolver / OCC) 번들
`build_dist/Library/` 를 비우고(`build_all_python312.sh:39` 의 `build_dist` 삭제 직전 `/tmp/...Library_backup_$$` 로 백업: `:34-38`), 다음 우선순위로 소스를 정한다.
1. 프로젝트 루트 `Library/`
2. 직전 빌드 백업 `$LIBRARY_BACKUP`

근거: 소스 결정 `build_all_python312.sh:154-163`. 항목별 복사:
- **gmsh** `Library/gmsh-4.14.1-Linux64` — KooMeshModifier/KooAutomatedModeller가 subprocess로 호출 (`build_all_python312.sh:171-177`)
- **Evolver** `Library/Evolver` — WarpageSolderJoint에서 호출, 바이너리+스크립트 (`build_all_python312.sh:184-190`)
- **OCC** `Library/OCC` — pythonOCC 네이티브 `.so`, LD_LIBRARY_PATH 로 로드 (`build_all_python312.sh:195-201`)

> 실측: 루트 `Library/` 에는 `gmsh-4.14.1-Linux64`, `Evolver`, `evolver` 가 존재하고 `OCC` 는 없음(스크립트의 "이미 Nuitka standalone에 포함되었을 수 있음" 경로: `build_all_python312.sh:200`).

### 4.4 배포 대상 두 곳
빌드 산출물을 `sudo` 로 두 위치에 복사한다.

1. **`$SCRIPT_DIR/../SmartTwinPreprocessor`** (= `appt313/opt/SmartTwinPreprocessor`)
   - `lib/<모듈>` 교체 + `bin/<모듈>` symlink + `Library/` 복사 (`build_all_python312.sh:237-271`)
   - 구버전 잔재 `koocr` 제거 로직 포함 (`:244-248`)
2. **`/data/SmartTwinPreprocessor`** (공유 NFS, 존재 시에만)
   - 3모듈 `lib`/`bin` 만 추가 배포 (Library 미포함) (`build_all_python312.sh:283-311`)

> 실측: `appt313/opt/SmartTwinPreprocessor/bin` 에 3개 모듈 symlink + `Library/{Evolver,gmsh-4.14.1-Linux64}` 확인. `/data/SmartTwinPreprocessor/{bin,lib}` 에 3개 모듈 확인.

`build_without_automatedmodeller.sh` 도 동일 2곳에 배포하되 KooMeshModifier+KooChainRun만 복사한다(`build_without_automatedmodeller.sh:205-243`). `build_KooChainRun_python312.sh` 는 KooChainRun만(`:92-118`).

### 4.5 SIF 역할 (빌드와 분리)
SIF는 빌드 스크립트 산출물이 아니라 compute node `/opt/apptainers/` 에 별도 배포되는 실행 환경 컨테이너다.

| SIF | 역할 | 근거 |
|---|---|---|
| `SmartTwinPreprocessor.sif` (mesh) | KooMeshModifier 실행 환경 (OCC/vtk/trimesh/gmsh) | `docs/FullAngleDrop_HPC_Workflow.md:23`, `:62`; scenario `apptainer_sif` 기본값 (예: `Examples/HWWarrantyDropTest/Tests/Test_001_Full26_1Step/scenario.json:9`) |
| `SmartTwinPostprocessor.sif` (post) | KooD3plotReader 후처리 실행 환경 (deep/sphere report) | `docs/FullAngleDrop_HPC_Workflow.md:24`, `:77`; 코드 기본값 `Runner/PostprocessShellGenerator.py:28` (`DEFAULT_SIF_PATH = "/opt/apptainers/SmartTwinPostprocessor.sif"`) |

> compute node `/opt/apptainers/` 는 로컬 디스크(NFS 아님)라 SIF 변경 시 노드별 `ssh + sudo cp` 필요 (`docs/FullAngleDrop_HPC_Workflow.md:32`).

## 5. 주의사항 · 한계

- **`sudo` 필요.** 배포 단계의 `cp`/`rm`/`ln` 이 root 소유 경로(`appt313/opt/...`, `/data/SmartTwinPreprocessor`)를 건드린다 (`build_all_python312.sh:252-264`, `:293-305`). MEMORY 의 "tar 생성 sudo 필요" 와 일치.
- **소스 직접 복사 금지.** Python 소스를 Nuitka 배포 경로에 그대로 복사해서는 안 되며, 코드 변경 후 반드시 재빌드해야 한다(MEMORY: "Python source files can't be directly copied to Nuitka deployment").
- **`build_automatedmodeller_python312.sh` 단독 실행은 배포까지 가지 않는다.** `KooAutomatedModeller.dist/` 만 만들 뿐 SmartTwinPreprocessor 설치 단계가 없다(`build_automatedmodeller_python312.sh` 전체에 STP_DIR 로직 없음). 배포가 필요하면 `build_all_python312.sh` 사용.
- **`build_without_automatedmodeller.sh` 의 AutomatedModeller 복원 의존성.** 직전 `build_dist/lib/KooAutomatedModeller` 가 있어야 백업·복원된다(`:41-44`). 없으면 결과물에 AutomatedModeller가 빠진다(복원 블록은 백업 존재 시에만 실행: `:126-132`).
- **Library 소스가 없으면 경고만 출력하고 진행.** 루트 `Library/` 와 백업이 모두 없으면 `⚠️` 출력 후 계속 — 배포 환경에서 `/opt/gmsh-4.14.1-Linux64` 또는 PATH 가 필요해진다(`build_all_python312.sh:161-163`, `:175-177`).
- **incremental 빌드 캐시 주의.** 기본은 캐시 보존이라 변경이 반영 안 되는 의심 시 `--clean` 사용 (`build_all_python312.sh:46`).
- **`/data/SmartTwinPreprocessor` 는 존재할 때만 배포.** 디렉토리가 없으면 해당 단계를 건너뛴다(`build_all_python312.sh:284`).
- **gmsh 버전 하드코딩.** `gmsh-4.14.1-Linux64` 디렉토리명이 스크립트에 고정되어 있어 버전 변경 시 스크립트 수정 필요(`build_all_python312.sh:171-173`).

## 6. 개발 현황

**구현됨.**

- 4개 빌드 스크립트 모두 존재·동작:
  - `build_all_python312.sh`, `build_KooChainRun_python312.sh`, `build_without_automatedmodeller.sh` — 프로젝트 루트 확인.
  - `build_automatedmodeller_python312.sh` — `occProject/Generators/` 에 존재(루트 아님). 지시문의 경로(루트)와 다름 → **확인 필요: 문서에서는 실제 경로 `occProject/Generators/build_automatedmodeller_python312.sh` 로 표기함.**
- 배포 대상 두 곳 실재 확인: `appt313/opt/SmartTwinPreprocessor/{bin,lib,Library}`, `/data/SmartTwinPreprocessor/{bin,lib}` (3모듈 바이너리·symlink 존재).
- `venv312` (Python 3.12.12) 실재.
- SIF 역할은 코드 기본값(`Runner/PostprocessShellGenerator.py:28`)과 문서(`docs/FullAngleDrop_HPC_Workflow.md:23-24`)로 교차 확인.

**확인 필요 항목:**
- `Library/OCC` 는 루트에 없음 — OCC `.so` 가 Nuitka standalone 에 이미 포함되는지 여부는 스크립트 주석상의 추정(`build_all_python312.sh:200`)이며 실제 standalone 내용 검증은 안 함.
- SIF 파일 자체(`*.sif`)는 이 빌드 스크립트들이 만들지 않으며, 본 문서의 빌드 흐름 범위 밖이다(SIF 빌드/배포는 별도 도구: `docs/FullAngleDrop_HPC_Workflow.md:33`).
