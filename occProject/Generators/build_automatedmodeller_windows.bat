@echo off
REM KooAutomatedModeller 빌드 스크립트 - Windows
REM 사용법: build_automatedmodeller_windows.bat

setlocal enabledelayedexpansion

echo ================================================================================
echo KooAutomatedModeller 빌드 (Windows)
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
if exist KooAutomatedModeller.build rmdir /s /q KooAutomatedModeller.build
if exist KooAutomatedModeller.dist rmdir /s /q KooAutomatedModeller.dist

echo.
echo Nuitka 빌드 시작...
echo 주의: 빌드에 20-40분 소요될 수 있습니다.
%PYTHON% -m nuitka KooAutomatedModeller.py ^
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
REM AIRMESH: gmsh Python API는 ctypes(WinDLL)로 gmsh-4.15.dll을 로드하므로 Nuitka가
REM 번들하지 않음 - dist 루트에 수동 복사 필수 (리눅스 libgmsh.so.4.15 복사와 대칭).
REM 누락 시 AIRMESH 모드가 첫 gmsh 호출에서 DLL-not-found로 실패 (다른 5개 모드는 무관).
echo AIRMESH: gmsh-4.15.dll 복사 중...
set GMSHDLL=
if exist ..\..\venv312\Lib\site-packages\gmsh-4.15.dll set GMSHDLL=..\..\venv312\Lib\site-packages\gmsh-4.15.dll
if exist ..\..\venv312\Lib\gmsh-4.15.dll set GMSHDLL=..\..\venv312\Lib\gmsh-4.15.dll
if not "!GMSHDLL!"=="" (
    copy /y "!GMSHDLL!" KooAutomatedModeller.dist\ >nul
    echo   복사됨: !GMSHDLL!
) else (
    echo   경고: gmsh-4.15.dll을 찾지 못함 - AIRMESH 모드가 동작하지 않습니다.
    echo   venv에서 위치 확인 후 KooAutomatedModeller.dist\ 로 수동 복사하세요.
)

echo ================================================================================
echo 빌드 완료!
echo ================================================================================
echo 출력 디렉토리: %CD%\KooAutomatedModeller.dist
echo 실행 파일: %CD%\KooAutomatedModeller.dist\KooAutomatedModeller.exe
echo.

if exist KooAutomatedModeller.dist\KooAutomatedModeller.exe (
    echo 빌드 정보:
    dir KooAutomatedModeller.dist\KooAutomatedModeller.exe
    echo.
    echo 빌드 크기:
    for /f "tokens=3" %%a in ('dir /s KooAutomatedModeller.dist ^| findstr "바이트"') do set SIZE=%%a
    echo 전체 크기: !SIZE! 바이트
) else (
    echo ERROR: 빌드 실패 - KooAutomatedModeller.exe를 찾을 수 없습니다.
)

echo.
echo 실행 방법:
echo   KooAutomatedModeller.dist\KooAutomatedModeller.exe

endlocal
