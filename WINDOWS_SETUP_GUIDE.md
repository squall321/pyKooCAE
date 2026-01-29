# pyKooCAE Windows 설치 가이드

## 시스템 요구사항

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.12.x
- **RAM**: 최소 8GB (권장 16GB 이상)
- **디스크 공간**: 최소 5GB (가상환경 + 빌드 결과)
- **Visual Studio Build Tools** (Nuitka 빌드 시 필요)

---

## 설치 단계

### 1. Python 3.12 설치

1. Python 3.12 다운로드:
   - https://www.python.org/downloads/
   - Python 3.12.x (64-bit) 선택

2. 설치 시 옵션:
   - ✅ **"Add Python to PATH"** 체크
   - ✅ **"Install for all users"** 권장
   - Customize installation → **"pip"** 포함 확인

3. 설치 확인:
   ```cmd
   python --version
   # 출력: Python 3.12.x

   pip --version
   # 출력: pip xx.x.x from ...
   ```

---

### 2. Miniconda 설치 (PythonOCC를 위해 필요)

PythonOCC는 pip로 직접 설치하기 어렵기 때문에 conda를 사용합니다.

1. Miniconda 다운로드:
   - https://docs.conda.io/en/latest/miniconda.html
   - Windows 64-bit 설치 파일 다운로드

2. 설치 시 옵션:
   - ✅ **"Add Anaconda to PATH"** (선택사항, 권장하지 않음)
   - Anaconda Prompt 사용 권장

---

### 3. 가상환경 생성 (conda 사용 권장)

#### 방법 1: conda로 가상환경 생성 (권장)

```cmd
# Anaconda Prompt 실행

# Python 3.12 가상환경 생성
conda create -n pykooCAE python=3.12 -y

# 가상환경 활성화
conda activate pykooCAE

# pip 업그레이드
python -m pip install --upgrade pip
```

#### 방법 2: venv로 가상환경 생성 (PythonOCC 수동 설치 필요)

```cmd
# 프로젝트 디렉토리 생성
mkdir C:\pyKooCAE
cd C:\pyKooCAE

# 가상환경 생성
python -m venv venv312

# 가상환경 활성화
venv312\Scripts\activate

# pip 업그레이드
python -m pip install --upgrade pip
```

---

### 4. PythonOCC 설치

PythonOCC는 OpenCascade 기반 3D CAD 라이브러리입니다.

#### 방법 1: conda-forge에서 설치 (권장)

```cmd
# conda 가상환경 활성화 후
conda activate pykooCAE

# PythonOCC 설치
conda install -c conda-forge pythonocc-core=7.9.0 -y

# 설치 확인
python -c "import OCC.Core.gp; print('PythonOCC 설치 성공!')"
```

#### 방법 2: 사전 빌드된 wheel 파일 사용

1. GitHub 릴리스 페이지에서 wheel 파일 다운로드:
   - https://github.com/tpaviot/pythonocc-core/releases

2. Python 3.12 및 Windows 64-bit 버전 선택
   - 예: `pythonocc_core-7.9.0-cp312-cp312-win_amd64.whl`

3. 설치:
   ```cmd
   pip install pythonocc_core-7.9.0-cp312-cp312-win_amd64.whl
   ```

---

### 5. 핵심 패키지 설치

```cmd
# 가상환경 활성화 상태에서

# 핵심 과학 계산 라이브러리
pip install numpy==2.4.1 scipy==1.17.0 matplotlib==3.10.6

# 데이터 처리
pip install pandas==2.3.3

# 3D 처리 및 시각화
pip install vtk==9.5.2 trimesh==4.8.3 numpy-stl==3.2.0

# OpenCV
pip install opencv-python==4.13.0.90

# GUI 프레임워크
pip install PyQt5==5.15.11
```

---

### 6. 전체 패키지 일괄 설치

프로젝트 디렉토리의 `requirements_python312.txt` 사용:

```cmd
# pyKooCAE 프로젝트 디렉토리로 이동
cd C:\pyKooCAE

# requirements 파일 다운로드 (또는 복사)
# GitHub에서 requirements_python312.txt 다운로드

# 일괄 설치
pip install -r requirements_python312.txt
```

**주의**: PythonOCC는 requirements에서 제외되어 있으므로 별도 설치 필요 (위 4단계 참조)

---

### 7. Nuitka 빌드 환경 설정 (실행 파일 빌드 시 필요)

Nuitka로 Python 코드를 실행 파일로 빌드하려면 C++ 컴파일러가 필요합니다.

#### Visual Studio Build Tools 설치

1. Visual Studio Build Tools 다운로드:
   - https://visualstudio.microsoft.com/downloads/
   - "Build Tools for Visual Studio 2022" 선택

2. 설치 시 워크로드 선택:
   - ✅ **"Desktop development with C++"**
   - 필수 구성 요소:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 11 SDK (최신 버전)

3. 설치 확인:
   ```cmd
   # Developer Command Prompt for VS 2022 실행
   cl
   # Microsoft (R) C/C++ Optimizing Compiler 출력 확인
   ```

#### Nuitka 설치

```cmd
pip install nuitka==2.8.10
```

---

### 8. 추가 유틸리티 패키지 설치 (선택)

#### 3D 처리 도구

```cmd
pip install pyvista==0.45.3 pyvistaqt==0.12.1
pip install pymeshlab==2024.12
pip install open3d==0.19.0
pip install vedo==2025.2.0
```

#### Jupyter 환경

```cmd
pip install jupyter==1.1.1 ipython==9.6.0
pip install notebook==7.4.4
```

#### 웹 시각화

```cmd
pip install plotly==6.3.1 dash==3.2.0
pip install kaleido==0.2.1
```

---

## 설치 검증

### 1. Python 및 핵심 라이브러리 테스트

```cmd
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import scipy; print(f'SciPy: {scipy.__version__}')"
python -c "import matplotlib; print(f'Matplotlib: {matplotlib.__version__}')"
python -c "import vtk; print(f'VTK: {vtk.VTK_VERSION}')"
```

### 2. PythonOCC 테스트

```python
python -c "from OCC.Core.gp import gp_Pnt; p = gp_Pnt(1, 2, 3); print(f'Point: ({p.X()}, {p.Y()}, {p.Z()})')"
```

예상 출력: `Point: (1.0, 2.0, 3.0)`

### 3. PyQt5 테스트

```python
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 설치 성공!')"
```

### 4. trimesh 테스트

```python
python -c "import trimesh; print(f'trimesh: {trimesh.__version__}')"
```

---

## Windows에서 빌드하기

### koocr 빌드 (간단한 CLI 도구)

```cmd
cd C:\pyKooCAE

python -m nuitka koocr ^
    --standalone ^
    --follow-imports ^
    --include-package=Runner ^
    --jobs=8 ^
    --show-progress ^
    --windows-console-mode=force

# 출력: koocr.dist\koocr.exe
```

### KooMeshModifier 빌드 (GUI 도구)

```cmd
cd C:\pyKooCAE\occProject\Generators

python -m nuitka KooMeshModifier.py ^
    --standalone ^
    --enable-plugin=pyqt5 ^
    --jobs=8 ^
    --include-package=OCC ^
    --include-package=vtk ^
    --include-package=vtkmodules ^
    --include-package=trimesh ^
    --include-package-data=trimesh ^
    --follow-imports ^
    --show-progress ^
    --windows-console-mode=disable

# 출력: KooMeshModifier.dist\KooMeshModifier.exe
```

**빌드 시간**:
- koocr: ~5-10분
- KooMeshModifier: ~20-40분 (대량의 C++ 의존성)

---

## 문제 해결

### Q1: "python" 명령을 찾을 수 없음

**A**: Python PATH 설정 확인
```cmd
# 환경 변수에 Python 경로 추가
# 제어판 → 시스템 → 고급 시스템 설정 → 환경 변수
# Path에 추가: C:\Users\<사용자>\AppData\Local\Programs\Python\Python312
```

### Q2: pip 설치 시 "Microsoft Visual C++ 14.0 is required" 에러

**A**: Visual Studio Build Tools 설치 (위 7단계 참조)

### Q3: PythonOCC import 에러

**A**: conda로 설치했는지 확인
```cmd
conda list | findstr pythonocc
# pythonocc-core가 목록에 있어야 함
```

### Q4: Nuitka 빌드 시 "cl.exe not found" 에러

**A**: Developer Command Prompt for VS 2022 사용
```cmd
# 시작 메뉴에서 검색:
# "Developer Command Prompt for VS 2022"
```

### Q5: vtk import 시 DLL 에러

**A**: Visual C++ Redistributable 설치
- https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 참고 링크

### 공식 문서
- Python 3.12: https://www.python.org/downloads/
- Miniconda: https://docs.conda.io/en/latest/miniconda.html
- PythonOCC: https://github.com/tpaviot/pythonocc-core
- Nuitka: https://nuitka.net/

### 패키지 문서
- NumPy: https://numpy.org/doc/
- SciPy: https://scipy.org/
- VTK: https://vtk.org/
- PyQt5: https://www.riverbankcomputing.com/software/pyqt/

### 개발 도구
- Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
- Git for Windows: https://git-scm.com/download/win

---

## 파일 구조 (설치 후)

```
C:\pyKooCAE\
├── venv312\                    # 가상환경 (또는 conda env)
├── koocr                       # koocr CLI 도구
├── Runner\                     # Runner 모듈
│   ├── CumulativeDesigner.py
│   ├── PathResolver.py
│   └── ...
├── occProject\
│   └── Generators\
│       ├── KooMeshModifier.py
│       └── KooAutomatedModeller.py
├── requirements_python312.txt  # 패키지 목록
└── requirements_python312_full.txt  # 전체 의존성 목록
```

---

**작성**: 2026-01-29
**대상**: Windows 10/11 + Python 3.12
**작성자**: pyKooCAE Team
