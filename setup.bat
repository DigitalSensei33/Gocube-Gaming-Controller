@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   GoCube Gaming Controller - Setup
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Please install Python from https://www.python.org/downloads/
    echo ^(during install, check "Add Python to PATH"^) then run this again.
    pause
    exit /B
)

set "DEFAULT_DIR=%USERPROFILE%\GoCubeGamingController"
set /p "INSTALL_DIR=Enter install location [default: %DEFAULT_DIR%]: "
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%DEFAULT_DIR%"

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

echo.
echo Copying files to %INSTALL_DIR%...
xcopy /E /I /Y "%~dp0src" "%INSTALL_DIR%\src"
copy /Y "%~dp0run.bat" "%INSTALL_DIR%\run.bat" >nul
copy /Y "%~dp0setup.bat" "%INSTALL_DIR%\setup.bat" >nul
copy /Y "%~dp0README.md" "%INSTALL_DIR%\README.md" >nul
copy /Y "%~dp0CHANGELOG.md" "%INSTALL_DIR%\CHANGELOG.md" >nul
if exist "%~dp0LICENSE" copy /Y "%~dp0LICENSE" "%INSTALL_DIR%\LICENSE" >nul
if exist "%~dp0THIRD-PARTY-LICENSES" xcopy /E /I /Y "%~dp0THIRD-PARTY-LICENSES" "%INSTALL_DIR%\THIRD-PARTY-LICENSES"

echo.
echo ============================================
echo   Cube Configuration
echo ============================================
echo.
echo To find your cube's MAC address:
echo   Settings ^> Bluetooth ^& devices ^> Devices ^> [your GoCube] ^> Properties
echo.
set /p "MAC_ADDR=Enter your GoCube's MAC address (format XX:XX:XX:XX:XX:XX), or press Enter to skip: "

if not "!MAC_ADDR!"=="" (
    powershell -Command "(Get-Content '%INSTALL_DIR%\src\main.py') -replace 'E6:EF:C6:B0:B8:A8', '!MAC_ADDR!' | Set-Content '%INSTALL_DIR%\src\main.py'"
    echo MAC address configured.
) else (
    echo Skipped - you can manually edit src\main.py later ^(see README^).
)

echo.
echo Creating virtual environment...
python -m venv "%INSTALL_DIR%\venv"

echo.
echo Installing dependencies...
call "%INSTALL_DIR%\venv\Scripts\activate.bat"
pip install bleak pyautogui pywin32

echo.
echo ============================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Go to %INSTALL_DIR%
echo   2. Run run.bat to launch
echo.
echo   You can safely delete this downloaded folder now -
echo   everything you need is in %INSTALL_DIR%
echo ============================================
pause