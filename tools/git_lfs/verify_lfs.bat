@echo off
cls
echo Git LFS Setup Verification
echo ===========================

echo.
echo Checking Git LFS version:
git lfs version

echo.
echo Checking LFS tracking rules:
git lfs track

echo.
echo Checking LFS managed files:
git lfs ls-files

echo.
echo Checking Git status:
git status --short

echo.
echo Ready to push to GitHub with:
echo git push origin main

echo.
pause
