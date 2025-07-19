#!/usr/bin/env python3
"""
AIDCIS3-LFS 主启动脚本 v2.0.0
重定向到统一的主程序入口
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# 导入统一的主程序
from main_window import main

if __name__ == "__main__":
    print("🔄 重定向到统一启动入口...")
    print("📍 使用 src/main_window.py 作为主程序入口")
    print("")
    
    # 调用统一的main函数
    exit_code = main()
    
    sys.exit(exit_code)