#!/usr/bin/env python3
"""
AIDCIS3-LFS 主启动脚本 v3.0.0 (修复版)
重定向到修复后的统一启动入口
"""

import sys
import os
from pathlib import Path

print("🔄 重定向到修复后的启动入口...")
print("📍 使用统一的ApplicationCore启动方式")
print("🔧 避免重复初始化问题")
print("")

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    # 导入并运行修复后的启动脚本
    try:
        import startup_fixed
        exit_code = startup_fixed.main()
        sys.exit(exit_code)
    except ImportError:
        print("❌ 修复后的启动脚本不存在，回退到原始方式")
        # 回退到原始启动方式
        from main_window import main
        exit_code = main()
        sys.exit(exit_code)
