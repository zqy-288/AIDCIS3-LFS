@echo off
cls
echo ========================================
echo        Git LFS Setup Verification
echo ========================================
echo.

echo [1] Checking Git LFS installation...
git lfs version
if errorlevel 1 (
    echo [ERROR] Git LFS not installed
    pause
    exit /b 1
)
echo [SUCCESS] Git LFS is installed
echo.

echo [2] Checking LFS tracking rules...
git lfs track
echo.

echo [3] Checking LFS files...
git lfs ls-files
echo.

echo [4] Checking Git status...
git status --short
echo.

echo [5] Checking file sizes...
if exist "DXF Graph\测试管板.dxf" (
    for %%f in ("DXF Graph\测试管板.dxf") do echo DXF file size: %%~zf bytes
)

if exist "Data\H00001\CCIDM\measurement_data_Fri_Jul__4_18_40_29_2025.csv" (
    for %%f in ("Data\H00001\CCIDM\measurement_data_Fri_Jul__4_18_40_29_2025.csv") do echo CSV H00001 size: %%~zf bytes
)

if exist "Data\H00002\CCIDM\measurement_data_Sat_Jul__5_15_18_46_2025.csv" (
    for %%f in ("Data\H00002\CCIDM\measurement_data_Sat_Jul__5_15_18_46_2025.csv") do echo CSV H00002 size: %%~zf bytes
)

echo.
echo [6] LFS environment info...
git lfs env
echo.

echo ========================================
echo        Verification Complete
echo ========================================
echo.
echo Ready to push to GitHub:
echo   git push origin main
echo.
pause
