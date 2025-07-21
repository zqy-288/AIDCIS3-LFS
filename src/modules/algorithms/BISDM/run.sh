#!/bin/bash
# 工业内窥镜图像处理系统 - 快速启动脚本

echo "🔬 工业内窥镜图像处理系统"
echo "=================================="

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 检查环境
echo "📋 环境检查..."
python3 -c "
try:
    import cv2, numpy, torch, torchvision, matplotlib
    from tqdm import tqdm
    print('✅ 所有依赖包已就绪')
    print(f'  - OpenCV: {cv2.__version__}')
    print(f'  - NumPy: {numpy.__version__}')
    print(f'  - PyTorch: {torch.__version__}')
except ImportError as e:
    print(f'❌ 依赖包缺失: {e}')
    exit(1)
"

# 运行主程序
echo ""
echo "🚀 启动图像处理..."
echo "=================================="
python3 main.py

echo ""
echo "✅ 处理完成！"
echo "📁 输出文件位于: output_22.8.1/" 