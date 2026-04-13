@echo off
setlocal EnableDelayedExpansion

echo.
echo   Trisynth Compiler -- Local Setup (Windows)
echo   ==========================================
echo.

set "SCRIPT_DIR=%~dp0"

REM Check GCC (MinGW)
where gcc >nul 2>&1
if errorlevel 1 (
    echo   [!] gcc not found. Please ensure MinGW or similar is installed if compiling locally.
) else (
    echo   [OK] gcc found
)

REM Check NASM - If not found, download portable local version
where nasm >nul 2>&1
if errorlevel 1 (
    echo   [-^>] nasm not found globally. Downloading portable local version...
    if not exist "%SCRIPT_DIR%bin\windows" mkdir "%SCRIPT_DIR%bin\windows"
    if not exist "%SCRIPT_DIR%bin\windows\nasm.exe" (
        powershell -Command "Invoke-WebRequest -Uri 'https://www.nasm.us/pub/nasm/releasebuilds/2.16.01/win64/nasm-2.16.01-win64.zip' -OutFile 'nasm.zip'"
        powershell -Command "Expand-Archive -Path 'nasm.zip' -DestinationPath '.' -Force"
        move /y "nasm-2.16.01\nasm.exe" "%SCRIPT_DIR%bin\windows\" >nul
        move /y "nasm-2.16.01\ndisasm.exe" "%SCRIPT_DIR%bin\windows\" >nul
        rmdir /s /q "nasm-2.16.01"
        del "nasm.zip"
    )
    echo   [OK] Portable nasm downloaded into bin\windows\
) else (
    echo   [OK] nasm found globally
)

echo   [OK] trisynth.exe binary is ready to execute.

echo.
echo   Setup complete. Usage:
echo     trisynth.exe file.tri
echo     trisynth.exe file.tri --verbose
echo.
pause
