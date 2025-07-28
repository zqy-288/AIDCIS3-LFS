#!/bin/bash
# 从src目录运行main_window.py的脚本

echo "🚀 启动 AIDCIS3-LFS 主窗口..."
echo "当前目录: $(pwd)"

# 切换到src目录
cd "$(dirname "$0")/src" || exit 1

# 运行主窗口
python3 main_window.py

echo "✅ 程序已退出"