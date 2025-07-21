#!/bin/bash

# ==============================================================================
# 工业内窥镜图像处理系统 - 一键安装脚本 (Linux/macOS)
# ==============================================================================

set -e  # 遇到错误立即退出

echo "🔬 工业内窥镜图像处理系统 - 安装程序"
echo "=================================================="

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
min_version="3.9"

if [ "$(printf '%s\n' "$min_version" "$python_version" | sort -V | head -n1)" != "$min_version" ]; then
    echo "❌ 错误: 需要Python 3.9或更高版本，当前版本: $python_version"
    exit 1
else
    echo "✅ Python版本检查通过: $python_version"
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: pip3未找到，请先安装pip"
    exit 1
else
    echo "✅ pip检查通过"
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "⚠️  虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装项目依赖..."
pip install -r requirements.txt

# 验证安装
echo "🧪 验证安装..."
python3 -c "
import cv2
import numpy
import torch
import torchvision
import sklearn
from tqdm import tqdm
print('✅ 所有依赖安装成功!')
print(f'OpenCV版本: {cv2.__version__}')
print(f'NumPy版本: {numpy.__version__}')
print(f'PyTorch版本: {torch.__version__}')
"

# 创建必要目录
echo "📁 创建输出目录..."
mkdir -p output logs

echo ""
echo "🎉 安装完成！"
echo "=================================================="
echo "📖 使用方法:"
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 运行主程序: python main.py"
echo "   3. 查看配置: python -c 'from utils.config import Config; print(Config().get_processing_summary())'"
echo ""
echo "📚 更多信息请查看 README.md"
echo "==================================================" 