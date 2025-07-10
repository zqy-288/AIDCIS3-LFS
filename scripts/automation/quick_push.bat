@echo off
cls
echo ========================================
echo        Quick Push to GitHub
echo ========================================

echo.
echo Adding any remaining files...
git add .

echo.
echo Current status:
git status --short

echo.
echo Checking for changes to commit...
git status --porcelain | findstr "." >nul
if %errorlevel% equ 0 (
    echo Found changes to commit...
    git commit -m "Final project cleanup and organization"
) else (
    echo No new changes to commit.
)

echo.
echo Checking remote repository...
git remote -v

echo.
echo If you see a remote URL above, the push will proceed.
echo If not, you need to set up the GitHub repository first.

echo.
set /p confirm="Continue with push? (y/N): "
if /i not "%confirm%"=="y" (
    echo Push cancelled.
    goto :end
)

echo.
echo Pushing to GitHub...
echo This may take time due to Git LFS files...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ Successfully pushed to GitHub!
) else (
    echo.
    echo ❌ Push failed. Run setup_github_and_push.bat for detailed setup.
)

:end
echo.
pause
