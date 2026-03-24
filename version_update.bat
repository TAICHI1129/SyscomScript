@echo off
echo === Updating SyscomScript ===
echo.

set REPO_USER=TAICHI1129
set REPO_NAME=SyscomScript
set BRANCH=main
set ZIP_URL=https://github.com/TAICHI1129/SyscomScript.git
set ZIP_FILE=update.zip

cd /d %~dp0

git --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Executing a pull in git…
    git pull origin %BRANCH%
    echo.
    echo === Update Complete ===
    pause
    exit /b
)

echo Git cannot be found. Switching to ZIP download method…
echo.

echo Downloading ZIP…
curl -L "%ZIP_URL%" -o "%ZIP_FILE%"
if %errorlevel% neq 0 (
    echo Failed to download the ZIP.
    pause
    exit /b
)

echo Expanding…
powershell -command "Expand-Archive -Force '%ZIP_FILE%' '.'"

set EXTRACTED=%REPO_NAME

if exist "%EXTRACTED%" (
    echo Overwriting the extracted files…
    xcopy "%EXTRACTED%\*" ".\" /E /H /Y >nul
    echo Cleaning up…
    rmdir /S /Q "%EXTRACTED%"
)

del "%ZIP_FILE%"

echo.
echo === Update Complete ===
pause
