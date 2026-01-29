@echo off
REM KooChainRun (koocr) 빌드 스크립트 - Windows
REM 사용법: build_koocr_windows.bat

setlocal enabledelayedexpansion

echo ================================================================================
echo KooChainRun (koocr) 빌드 (Windows)
echo ================================================================================
echo.

REM Python 가상환경 확인
if exist venv312\Scripts\python.exe (
    set PYTHON=venv312\Scripts\python.exe
    echo venv: venv312
) else if exist ..\venv312\Scripts\python.exe (
    set PYTHON=..\venv312\Scripts\python.exe
    echo venv: ..\venv312
) else (
    echo ERROR: Python 가상환경을 찾을 수 없습니다.
    echo venv312\Scripts\python.exe 또는 ..\venv312\Scripts\python.exe가 필요합니다.
    exit /b 1
)

REM Python 버전 확인
echo Python:
%PYTHON% --version
echo.

REM 기존 빌드 결과 제거
echo 기존 빌드 결과 제거 중...
if exist koocr.build rmdir /s /q koocr.build
if exist koocr.dist rmdir /s /q koocr.dist
if exist koocr.exe del /f /q koocr.exe

echo.
echo Nuitka 빌드 시작...
%PYTHON% -m nuitka koocr ^
    --standalone ^
    --follow-imports ^
    --include-package=Runner ^
    --jobs=8 ^
    --show-progress ^
    --windows-console-mode=force ^
    --output-dir=. ^
    --assume-yes-for-downloads

echo.
echo ================================================================================
echo 빌드 완료!
echo ================================================================================
echo 출력 디렉토리: %CD%\koocr.dist
echo 실행 파일: %CD%\koocr.dist\koocr.exe
echo.

if exist koocr.dist\koocr.exe (
    echo 빌드 정보:
    dir koocr.dist\koocr.exe
    echo.
    echo 실행 테스트:
    koocr.dist\koocr.exe --version
) else (
    echo ERROR: 빌드 실패 - koocr.exe를 찾을 수 없습니다.
)

echo.
echo 배포 방법:
echo   1. koocr.dist 폴더를 원하는 위치로 복사
echo   2. 환경 변수 PATH에 koocr.dist 경로 추가
echo   3. 또는 koocr.exe를 C:\Windows\System32로 복사 (관리자 권한 필요)

endlocal
