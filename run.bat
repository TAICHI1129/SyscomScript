@echo off
cd /d %~dp0

echo ================================
echo    SyscomScript Runner
echo ================================
echo.
echo Available files in code\:
echo.

for %%f in (code\*.scs) do (
    echo   %%~nxf
)

echo.
set /p filename="Enter file name (e.g. hello.scs): "

if "%filename%"=="" (
    echo No file name entered.
    pause
    exit /b 1
)

if not exist "code\%filename%" (
    echo.
    echo ERROR: code\%filename% not found.
    pause
    exit /b 1
)

echo.
echo Running code\%filename% ...
echo --------------------------------
python syscom.py "code\%filename%"
echo --------------------------------
echo.
pause