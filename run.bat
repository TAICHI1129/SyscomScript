@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo ================================
echo    SyscomScript Runner
echo ================================
echo.

set count=0
echo Available files in code\:
echo.
for %%f in (code\*.scs) do (
    set /a count+=1
    echo   [!count!] %%~nxf
)

if %count%==0 (
    echo   (no .scs files found in code\)
    echo   Place your .scs file in the code\ folder.
    pause
    exit /b
)

echo.
set /p filename="Enter file name (e.g. hello.scs): "

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