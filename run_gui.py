#!/usr/bin/env python3
"""
GUI启动器 - 新平级P架构
"""

import sys
import os
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动GUI应用程序"""
    print("🚀 启动AIDCIS3-LFS GUI界面...")
    print("使用新平级P架构")
    print()
    
    try:
        # 方法1: 尝试使用新的主窗口聚合器
        from src.main_window_aggregator import main as aggregator_main
        print("✅ 使用主窗口聚合器启动")
        aggregator_main()
        
    except ImportError as e:
        print(f"❌ 聚合器导入失败: {e}")
        
        try:
            # 方法2: 回退到聚合引用文件
            from src.main_window import main as window_main
            print("✅ 使用聚合引用文件启动")
            window_main()
            
        except Exception as e2:
            print(f"❌ 启动失败: {e2}")
            print("请检查依赖和环境配置")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 应用程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()