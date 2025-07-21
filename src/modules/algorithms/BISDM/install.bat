@echo off
REM ==============================================================================
REM 工业内窥镜图像处理系统 - 一键安装脚本 (Windows)
REM ==============================================================================

echo 🔬 工业内窥镜图像处理系统 - 安装程序
echo ==================================================

REM 检查Python是否安装
echo 📋 检查Python安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Python未安装或未添加到PATH
    echo 请从 https://python.org 下载并安装Python 3.9+
    pause
    exit /b 1
) else (
    echo ✅ Python检查通过
)

REM 检查pip
echo 📋 检查pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: pip未找到
    pause
    exit /b 1
) else (
    echo ✅ pip检查通过
)

REM 创建虚拟环境
echo 📦 创建虚拟环境...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ 虚拟环境创建成功
) else (
    echo ⚠️  虚拟环境已存在，跳过创建
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 升级pip
echo ⬆️  升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 📥 安装项目依赖...
pip install -r requirements.txt

REM 验证安装
echo 🧪 验证安装...
python -c "import cv2; import numpy; import torch; import torchvision; from tqdm import tqdm; print('✅ 所有依赖安装成功!')"

REM 创建必要目录
echo 📁 创建输出目录...
if not exist "output" mkdir output
if not exist "logs" mkdir logs

echo.
echo 🎉 安装完成！
echo ==================================================
echo 📖 使用方法:
echo    1. 激活虚拟环境: .venv\Scripts\activate.bat
echo    2. 运行主程序: python main.py
echo    3. 查看配置: python -c "from utils.config import Config; print(Config().get_processing_summary())"
echo.
echo 📚 更多信息请查看 README.md
echo ==================================================
pause 