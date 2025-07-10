@echo off
cls
echo ========================================
echo     Setup GitHub Repository and Push
echo ========================================

echo.
echo Current Git status:
git status --short

echo.
echo Checking if GitHub remote is configured...
git remote -v
if %errorlevel% neq 0 (
    echo No remote repository configured.
) else (
    echo Remote repository found.
)

echo.
echo ========================================
echo     GitHub Repository Setup Guide
echo ========================================

echo.
echo To push your project to GitHub, you need to:
echo.
echo 1. CREATE GITHUB REPOSITORY:
echo    - Go to https://github.com
echo    - Click "New repository" or "+"
echo    - Repository name: AIDCIS2-AIDCIS3
echo    - Description: 管孔检测系统上位机软件
echo    - Set to Public or Private (your choice)
echo    - DO NOT initialize with README (we already have one)
echo    - Click "Create repository"

echo.
echo 2. COPY THE REPOSITORY URL:
echo    - After creating, GitHub will show you the repository URL
echo    - It looks like: https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git
echo    - Copy this URL

echo.
echo 3. CONFIGURE REMOTE AND PUSH:
set /p repo_url="Enter your GitHub repository URL (or press Enter to skip): "

if "%repo_url%"=="" (
    echo.
    echo Skipped. You can set up the remote later with:
    echo git remote add origin https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git
    echo git push -u origin main
    goto :end
)

echo.
echo Setting up remote repository...
git remote add origin %repo_url%
if %errorlevel% neq 0 (
    echo Failed to add remote. The remote might already exist.
    echo Trying to update existing remote...
    git remote set-url origin %repo_url%
)

echo.
echo Adding any remaining files...
git add .

echo.
echo Checking if there are changes to commit...
git status --porcelain | findstr "." >nul
if %errorlevel% equ 0 (
    echo Committing remaining changes...
    git commit -m "Final cleanup and prepare for GitHub upload"
) else (
    echo No changes to commit.
)

echo.
echo Pushing to GitHub...
echo This may take some time due to Git LFS files...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo           SUCCESS!
    echo ========================================
    echo.
    echo ✅ Project successfully pushed to GitHub!
    echo.
    echo 🎉 Your repository is now available at:
    echo    %repo_url%
    echo.
    echo 👥 Team members can now:
    echo    1. Install Git LFS: https://git-lfs.github.io/
    echo    2. Clone: git clone %repo_url%
    echo    3. Pull LFS files: git lfs pull
    echo    4. Install dependencies: pip install -r requirements.txt
    echo    5. Run: python src/main.py
    echo.
    echo 📋 Next steps:
    echo    - Share the repository URL with your team
    echo    - Add collaborators in GitHub repository settings
    echo    - Monitor Git LFS usage in repository settings
    
) else (
    echo.
    echo ========================================
    echo           PUSH FAILED
    echo ========================================
    echo.
    echo ❌ Failed to push to GitHub. Common issues:
    echo.
    echo 1. AUTHENTICATION:
    echo    - Make sure you're logged into Git
    echo    - Use: git config --global user.name "Your Name"
    echo    - Use: git config --global user.email "your.email@example.com"
    echo    - You may need to set up a Personal Access Token
    echo.
    echo 2. REPOSITORY ACCESS:
    echo    - Make sure the repository exists on GitHub
    echo    - Check if you have push permissions
    echo    - Verify the repository URL is correct
    echo.
    echo 3. GIT LFS QUOTA:
    echo    - GitHub free accounts have 1GB LFS storage limit
    echo    - Check your LFS usage in repository settings
    echo.
    echo 4. NETWORK:
    echo    - Check your internet connection
    echo    - Try again in a few minutes
    echo.
    echo You can try pushing again with:
    echo git push origin main
)

:end
echo.
echo ========================================
echo     Git LFS File Summary
echo ========================================
echo.
echo LFS managed files:
git lfs ls-files

echo.
echo Repository size optimization:
echo - Large files are stored in Git LFS
echo - Clone speed is optimized
echo - Team collaboration is efficient

echo.
pause
