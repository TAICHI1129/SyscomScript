@echo off
echo Pushing to GitHub...

git add .
if %errorlevel% neq 0 (
    echo ERROR: git add failed.
    pause
    exit /b 1
)

git commit -m "update"
if %errorlevel% neq 0 (
    echo Nothing to commit, or commit failed.
    pause
    exit /b 1
)

git push
if %errorlevel% neq 0 (
    echo ERROR: git push failed.
    echo Check your authentication and network connection.
    pause
    exit /b 1
)

echo Done! Changes pushed to GitHub.
pause