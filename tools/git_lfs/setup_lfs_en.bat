@echo off
cls
echo ========================================
echo        Git LFS Setup Script
echo ========================================
echo.

REM Check Git LFS installation
echo [1/6] Checking Git LFS installation...
git lfs version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git LFS is not installed
    echo.
    echo Please install Git LFS:
    echo 1. Visit: https://git-lfs.github.io/
    echo 2. Download and install
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Git LFS is installed

REM Initialize Git LFS
echo.
echo [2/6] Initializing Git LFS...
git lfs install
if errorlevel 1 (
    echo [ERROR] Git LFS initialization failed
    pause
    exit /b 1
)
echo [SUCCESS] Git LFS initialized

REM Configure tracking rules
echo.
echo [3/6] Configuring file tracking rules...
git lfs track "*.dxf"
git lfs track "*.db"
git lfs track "*.sqlite"
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.mp4"
git lfs track "*.zip"
echo [SUCCESS] Tracking rules configured

REM Show tracking rules
echo.
echo [4/6] Current tracking rules:
git lfs track

REM Add configuration file
echo.
echo [5/6] Adding configuration file...
if exist ".gitattributes" (
    git add .gitattributes
    echo [SUCCESS] Added .gitattributes
) else (
    echo [WARNING] .gitattributes file not found
)

REM Add large files
echo.
echo [6/6] Checking and adding large files...
set "found_files=0"

if exist "DXF Graph" (
    echo   Found DXF Graph directory
    git add "DXF Graph/"
    set "found_files=1"
)

if exist "Data" (
    echo   Found Data directory
    git add "Data/"
    set "found_files=1"
)

for %%f in (*.db *.sqlite *.sqlite3) do (
    if exist "%%f" (
        echo   Found database file: %%f
        git add "%%f"
        set "found_files=1"
    )
)

if "%found_files%"=="0" (
    echo   No large files found for LFS management
)

REM Commit changes
echo.
echo Preparing to commit changes...
git status --porcelain 2>nul | findstr ".gitattributes" >nul
if errorlevel 1 (
    echo [INFO] No LFS configuration changes to commit
) else (
    echo Do you want to commit LFS configuration? (y/n)
    set /p commit_choice=
    if /i "%commit_choice%"=="y" (
        git commit -m "Configure Git LFS for large file management"
        echo [SUCCESS] LFS configuration committed
    )
)

REM Performance optimization
echo.
echo Configuring performance optimization...
git config lfs.concurrenttransfers 8
git config lfs.cachelimit 5G
echo [SUCCESS] Performance configuration completed

echo.
echo ========================================
echo           Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Push to remote repository: git push origin main
echo 2. Notify team members to install Git LFS
echo 3. Team members should run: git lfs pull
echo.
echo Team member setup guide:
echo 1. Download Git LFS: https://git-lfs.github.io/
echo 2. Clone repository or run: git lfs pull
echo.
echo Note: GitHub free account LFS quota is 1GB storage
echo.
pause
