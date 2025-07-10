@echo off
chcp 65001 >nul
echo ================================
echo Git LFS 项目配置脚本
echo ================================

echo.
echo 检查Git LFS安装状态...
git lfs version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Git LFS未安装，请先安装Git LFS
    echo 下载地址: https://git-lfs.github.io/
    echo.
    echo 或者尝试自动安装:
    echo winget install Git.Git-LFS
    pause
    exit /b 1
)
echo [成功] Git LFS已安装

echo.
echo 初始化Git LFS...
git lfs install
if %errorlevel% neq 0 (
    echo [错误] Git LFS初始化失败
    pause
    exit /b 1
)
echo [成功] Git LFS初始化完成

echo.
echo 配置文件跟踪规则...
call :track_file "*.dxf" "DXF文件"
call :track_file "DXF Graph/*.dxf" "DXF Graph目录下的DXF文件"
call :track_file "Data/**/*.csv" "Data目录下的CSV文件"
call :track_file "*.db" "数据库文件"
call :track_file "*.sqlite" "SQLite数据库文件"
call :track_file "*.sqlite3" "SQLite3数据库文件"
call :track_file "*.png" "PNG图像文件"
call :track_file "*.jpg" "JPG图像文件"
call :track_file "*.jpeg" "JPEG图像文件"
call :track_file "*.mp4" "MP4视频文件"
call :track_file "*.zip" "ZIP压缩文件"

echo.
echo 当前LFS跟踪规则:
git lfs track

echo.
echo 添加.gitattributes文件到Git...
git add .gitattributes
if %errorlevel% neq 0 (
    echo [警告] 添加.gitattributes文件失败，可能文件不存在
)

echo.
echo 添加大文件到Git LFS...
if exist "DXF Graph" (
    echo   正在添加DXF Graph目录...
    git add "DXF Graph/"
    if %errorlevel% equ 0 (
        echo   [成功] 添加DXF文件
    ) else (
        echo   [警告] 添加DXF文件失败
    )
)
if exist "Data" (
    echo   正在添加Data目录...
    git add "Data/"
    if %errorlevel% equ 0 (
        echo   [成功] 添加数据文件
    ) else (
        echo   [警告] 添加数据文件失败
    )
)

echo   检查数据库文件...
for %%f in (*.db *.sqlite *.sqlite3) do (
    if exist "%%f" (
        echo   正在添加数据库文件: %%f
        git add "%%f"
    )
)

echo.
echo 提交LFS配置...
git commit -m "配置Git LFS支持大文件管理"

echo.
echo 配置性能优化...
git config lfs.concurrenttransfers 8
git config lfs.cachelimit 5G

echo.
echo ✅ Git LFS配置完成！

echo.
echo 📋 下一步操作:
echo 1. 推送到远程仓库: git push origin main
echo 2. 通知团队成员安装Git LFS
echo 3. 团队成员重新克隆仓库或执行: git lfs pull

echo.
echo 👥 团队成员操作指南:
echo 1. 安装Git LFS: https://git-lfs.github.io/
echo 2. 克隆仓库: git clone ^<仓库地址^>
echo 3. 如果已有本地仓库: git lfs pull

echo.
echo ⚠️ 注意事项:
echo - GitHub免费账户LFS限额: 1GB存储 + 1GB/月带宽
echo - 大文件修改会产生新版本，注意存储使用量
echo - 团队所有成员都需要安装Git LFS

pause
goto :eof

:track_file
echo   跟踪 %~1 (%~2)
git lfs track %1
if %errorlevel% neq 0 (
    echo   [警告] 跟踪 %~1 失败
) else (
    echo   [成功] 已跟踪 %~1
)
goto :eof
