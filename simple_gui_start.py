#!/usr/bin/env python3
"""
简单的GUI启动脚本 - 仅启动MainWindow，不执行自动测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

def main():
    """启动主窗口"""
    print("🚀 启动GUI应用...")
    
    try:
        # 导入Qt
        from PySide6.QtWidgets import QApplication
        
        # 创建应用
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 导入并创建主窗口
        from src.main_window import MainWindow
        window = MainWindow()
        
        # 显示窗口
        window.show()
        window.raise_()  # 确保窗口在前台
        
        print("✅ GUI已启动，进入事件循环...")
        
        # 运行应用事件循环
        return app.exec()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())