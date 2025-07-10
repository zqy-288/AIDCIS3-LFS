@echo off
cls
echo ========================================
echo     Push Project to GitHub with LFS
echo ========================================

echo.
echo Adding remaining files...
git add .

echo.
echo Committing changes...
git commit -m "Complete project setup with Git LFS

- Configure Git LFS for large file management
- Add DXF design files (测试管板.dxf)
- Add CSV measurement data (H00001, H00002)
- Add PNG image files from BISDM results
- Update UI modifications for realtime monitoring
- Add comprehensive documentation and setup scripts
- Optimize for team collaboration"

echo.
echo Current LFS files:
git lfs ls-files

echo.
echo Pushing to GitHub...
echo This may take some time for large files...
git push origin main

echo.
echo ========================================
echo           Push Complete!
echo ========================================

echo.
echo Team members can now:
echo 1. Clone the repository: git clone [repo-url]
echo 2. Install Git LFS: https://git-lfs.github.io/
echo 3. Pull LFS files: git lfs pull

echo.
echo GitHub LFS usage:
echo - Free account: 1GB storage + 1GB/month bandwidth
echo - Monitor usage in repository settings

echo.
pause
