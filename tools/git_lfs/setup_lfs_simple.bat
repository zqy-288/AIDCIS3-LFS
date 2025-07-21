@echo off
chcp 65001 >nul
cls
echo ========================================
echo        Git LFS 简化配置脚本
echo ========================================
echo.

REM 检查Git LFS
echo [1/6] 检查Git LFS安装...
git lfs version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git LFS未安装
    echo.
    echo 请安装Git LFS:
    echo 1. 访问: https://git-lfs.github.io/
    echo 2. 下载并安装
    echo 3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)
echo [成功] Git LFS已安装

REM 初始化Git LFS
echo.
echo [2/6] 初始化Git LFS...
git lfs install
if errorlevel 1 (
    echo [错误] Git LFS初始化失败
    pause
    exit /b 1
)
echo [成功] Git LFS初始化完成

REM 配置跟踪规则
echo.
echo [3/6] 配置文件跟踪规则...
git lfs track "*.dxf"
git lfs track "*.db"
git lfs track "*.sqlite"
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.mp4"
git lfs track "*.zip"
echo [成功] 跟踪规则配置完成

REM 显示跟踪规则
echo.
echo [4/6] 当前跟踪规则:
git lfs track

REM 添加配置文件
echo.
echo [5/6] 添加配置文件...
if exist ".gitattributes" (
    git add .gitattributes
    echo [成功] 已添加.gitattributes
) else (
    echo [警告] .gitattributes文件不存在
)

REM 添加大文件
echo.
echo [6/6] 检查并添加大文件...
set "found_files=0"

if exist "DXF Graph" (
    echo   发现DXF Graph目录
    git add "DXF Graph/"
    set "found_files=1"
)

if exist "Data" (
    echo   发现Data目录
    git add "Data/"
    set "found_files=1"
)

for %%f in (*.db *.sqlite *.sqlite3) do (
    if exist "%%f" (
        echo   发现数据库文件: %%f
        git add "%%f"
        set "found_files=1"
    )
)

if "%found_files%"=="0" (
    echo   未发现需要LFS管理的大文件
)

REM 提交更改
echo.
echo 准备提交更改...
git status --porcelain | find ".gitattributes" >nul
if errorlevel 1 (
    echo [信息] 没有需要提交的LFS配置更改
) else (
    echo 是否要提交LFS配置? (y/n)
    set /p commit_choice=
    if /i "%commit_choice%"=="y" (
        git commit -m "配置Git LFS支持大文件管理"
        echo [成功] LFS配置已提交
    )
)

REM 性能优化
echo.
echo 配置性能优化...
git config lfs.concurrenttransfers 8
git config lfs.cachelimit 5G
echo [成功] 性能配置完成

echo.
echo ========================================
echo           配置完成!
echo ========================================
echo.
echo 下一步操作:
echo 1. 推送到远程仓库: git push origin main
echo 2. 通知团队成员安装Git LFS
echo 3. 团队成员执行: git lfs pull
echo.
echo 团队成员安装指南:
echo 1. 下载Git LFS: https://git-lfs.github.io/
echo 2. 克隆仓库或执行: git lfs pull
echo.
echo 注意: GitHub免费账户LFS限额为1GB存储
echo.
pause
