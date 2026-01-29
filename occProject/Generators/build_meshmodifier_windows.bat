@echo off
REM KooMeshModifier 빌드 스크립트 - Windows
REM 사용법: build_meshmodifier_windows.bat

setlocal enabledelayedexpansion

echo ================================================================================
echo KooMeshModifier 빌드 (Windows)
echo ================================================================================
echo.

REM Python 가상환경 확인
if exist ..\..\venv312\Scripts\python.exe (
    set PYTHON=..\..\venv312\Scripts\python.exe
    echo venv: ..\..\venv312
) else (
    echo ERROR: Python 가상환경을 찾을 수 없습니다.
    echo ..\..\venv312\Scripts\python.exe가 필요합니다.
    exit /b 1
)

REM Python 버전 확인
echo Python:
%PYTHON% --version
echo.

REM 기존 빌드 결과 제거
echo 기존 빌드 결과 제거 중...
if exist KooMeshModifier.build rmdir /s /q KooMeshModifier.build
if exist KooMeshModifier.dist rmdir /s /q KooMeshModifier.dist

echo.
echo Nuitka 빌드 시작...
echo 주의: 빌드에 20-40분 소요될 수 있습니다.
%PYTHON% -m nuitka KooMeshModifier.py ^
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
    --windows-console-mode=disable ^
    --output-dir=. ^
    --assume-yes-for-downloads

echo.
echo ================================================================================
echo 빌드 완료!
echo ================================================================================
echo 출력 디렉토리: %CD%\KooMeshModifier.dist
echo 실행 파일: %CD%\KooMeshModifier.dist\KooMeshModifier.exe
echo.

if exist KooMeshModifier.dist\KooMeshModifier.exe (
    echo 빌드 정보:
    dir KooMeshModifier.dist\KooMeshModifier.exe
    echo.
    echo 빌드 크기:
    for /f "tokens=3" %%a in ('dir /s KooMeshModifier.dist ^| findstr "바이트"') do set SIZE=%%a
    echo 전체 크기: !SIZE! 바이트
) else (
    echo ERROR: 빌드 실패 - KooMeshModifier.exe를 찾을 수 없습니다.
)

echo.
echo 실행 방법:
echo   KooMeshModifier.dist\KooMeshModifier.exe

endlocal
