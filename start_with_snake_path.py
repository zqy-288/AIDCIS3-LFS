#!/usr/bin/env python3
"""
启动脚本 - 专门用于测试蛇形路径功能
跳过字体缓存，直接启动GUI
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量来加速matplotlib
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

def main():
    """简化的主函数"""
    print("\n" + "="*60)
    print("🐍 蛇形路径测试启动器")
    print("="*60)
    
    try:
        # 导入Qt
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        print("✅ Qt模块导入成功")
        
        # 创建应用
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        print("✅ Qt应用创建成功")
        
        # 导入主窗口
        from src.main_window import MainWindow
        print("✅ MainWindow导入成功")
        
        # 创建主窗口
        print("🏗️ 创建主窗口...")
        window = MainWindow()
        print("✅ 主窗口创建成功")
        
        # 显示窗口
        window.show()
        print("✅ 主窗口显示成功")
        
        # 设置自动加载测试数据的定时器
        def auto_load_test_data():
            print("\n🔄 自动加载测试数据...")
            try:
                window.test_load_default_dxf()
                print("✅ 测试数据加载成功")
                
                # 延迟启用蛇形路径
                QTimer.singleShot(2000, lambda: enable_snake_path(window))
            except Exception as e:
                print(f"❌ 测试数据加载失败: {e}")
        
        def enable_snake_path(window):
            try:
                print("\n🐍 自动启用蛇形路径...")
                if hasattr(window, 'snake_path_checkbox'):
                    window.snake_path_debug_checkbox.setChecked(True)
                    window.snake_path_checkbox.setChecked(True)
                    print("✅ 蛇形路径已启用")
                    
                    # 显示提示信息
                    print("\n" + "="*60)
                    print("🎯 蛇形路径测试就绪！")
                    print("="*60)
                    print("测试步骤:")
                    print("1. 查看主视图中的蛇形路径显示")
                    print("2. 在工具栏切换不同策略")
                    print("3. 切换不同扇形查看路径同步")
                    print("4. 查看操作日志面板的调试信息")
                    print("="*60)
                else:
                    print("❌ 未找到蛇形路径控件")
            except Exception as e:
                print(f"❌ 启用蛇形路径失败: {e}")
        
        # 设置3秒后自动加载数据
        QTimer.singleShot(3000, auto_load_test_data)
        
        print("\n🚀 启动Qt事件循环...")
        print("提示: 程序启动后会自动加载测试数据并启用蛇形路径")
        
        # 运行应用
        return app.exec()
        
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())