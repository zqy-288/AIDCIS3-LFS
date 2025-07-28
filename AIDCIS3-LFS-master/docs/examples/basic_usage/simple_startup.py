#!/usr/bin/env python3
"""
示例名称: 简单应用启动

功能描述:
- 演示最基本的AIDCIS3-LFS应用启动方式
- 展示MVVM架构的协调器模式使用
- 提供最小化的错误处理

使用方法:
python simple_startup.py

依赖要求:
- Python 3.8+
- PySide6 >= 6.0.0
- AIDCIS3-LFS项目源码

作者: AIDCIS3-LFS团队
创建时间: 2025-07-25
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
except ImportError as e:
    print(f"❌ PySide6导入失败: {e}")
    print("请安装PySide6: pip install PySide6")
    sys.exit(1)

try:
    from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
except ImportError as e:
    print(f"❌ 项目模块导入失败: {e}")
    print("请确保在项目根目录运行此示例")
    sys.exit(1)


def main():
    """
    主函数 - 演示最简单的应用启动流程
    
    这个示例展示了AIDCIS3-LFS的基本启动模式：
    1. 创建Qt应用实例
    2. 创建主窗口协调器
    3. 显示主窗口
    4. 运行事件循环
    """
    
    print("🚀 启动AIDCIS3-LFS应用...")
    
    # 1. 创建Qt应用实例
    app = QApplication(sys.argv)
    
    # 设置应用基本信息
    app.setApplicationName("AIDCIS3-LFS")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AIDCIS3-LFS Team")
    
    print("✅ Qt应用实例创建成功")
    
    try:
        # 2. 创建主窗口协调器（MVVM架构的核心）
        coordinator = MainWindowCoordinator()
        print("✅ 主窗口协调器创建成功")
        
        # 3. 显示主窗口
        coordinator.show()
        print("✅ 主窗口显示成功")
        
        print("🎉 应用启动完成，进入事件循环...")
        print("💡 提示：关闭窗口或按Ctrl+C退出应用")
        
        # 4. 运行Qt事件循环
        return app.exec()
        
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        return 1


def cleanup():
    """
    清理函数 - 在应用退出时调用
    """
    print("🧹 正在清理应用资源...")


if __name__ == "__main__":
    try:
        # 运行主函数
        exit_code = main()
        
        # 清理资源
        cleanup()
        
        # 退出
        print(f"👋 应用已退出，退出代码: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断执行")
        cleanup()
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 未处理的异常: {e}")
        cleanup()
        sys.exit(1)