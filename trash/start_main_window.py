#!/usr/bin/env python3
"""
快速启动主窗口的脚本
可以从src目录直接运行: python3 start_main_window.py
"""

import sys
import os

# 确保路径正确设置
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))  # 添加项目根目录

# 导入并运行主窗口
from main_window import MainWindow
from PySide6.QtWidgets import QApplication

def main():
    """主函数"""
    print("🚀 启动 AIDCIS3-LFS 主窗口...")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 创建应用
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    print("✅ 主窗口已显示")
    
    # 运行应用
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())