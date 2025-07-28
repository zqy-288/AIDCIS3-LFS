#!/usr/bin/env python3
"""
运行主窗口的启动脚本
自动处理路径和配置文件位置
"""

import os
import sys
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent
os.chdir(project_root)  # 切换到项目根目录

# 添加必要的路径
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 导入并运行主窗口
from src.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def main():
    """主函数"""
    print(f"当前工作目录: {os.getcwd()}")
    print(f"配置文件路径: {project_root / 'config' / 'config.json'}")
    
    # 检查配置文件
    config_path = project_root / "config" / "config.json"
    if config_path.exists():
        print("✅ 配置文件存在")
    else:
        print("❌ 配置文件不存在")
    
    # 创建应用
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())