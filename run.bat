@echo off
:: Check for admin rights, elevate if needed
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo This script needs administrator privileges so keypresses can
    echo reach your game window.
    echo.
    echo A Windows permission prompt will appear shortly asking to approve this.
    echo.
    echo If you'd rather not allow it here, you can cancel the prompt and
    echo instead right-click run.bat directly and choose "Run as administrator".
    echo.
    timeout /t 8 >nul
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo ERROR: Setup has not been run yet.
    echo Please run setup.bat first.
    pause
    exit /B
)

echo ============================================
echo   GoCube Gaming Controller
echo ============================================
echo.

call "%~dp0venv\Scripts\activate.bat"
python "%~dp0src\main.py"

echo.
echo ============================================
echo   Session ended.
echo   This window stayed open so you can review
echo   any messages or errors above.
echo   Safe to close whenever you're ready.
echo ============================================
pause