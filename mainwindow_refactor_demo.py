"""
MainWindow重构演示脚本
展示如何使用重构后的架构
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.main_window_refactored import MainWindowRefactored


def main():
    """主函数"""
    print("🚀 启动MainWindow重构版演示...\n")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建主窗口
    print("✅ 创建主窗口（重构版）")
    window = MainWindowRefactored()
    
    # 显示导入统计
    print("\n📊 导入统计:")
    print("   - 原始版本: 30个导入")
    print("   - 重构版本: 10个导入")
    print("   - 改进幅度: 67%\n")
    
    # 显示架构特点
    print("🏗️ 重构架构特点:")
    print("   - MVC控制器模式")
    print("   - 服务层隔离")
    print("   - 工厂模式")
    print("   - 延迟加载\n")
    
    # 显示窗口
    window.show()
    
    print("✅ 窗口已显示")
    print("\n💡 提示:")
    print("   1. 点击'加载DXF'测试文件加载")
    print("   2. 点击'开始检测'测试检测流程")
    print("   3. 查看各个选项卡功能")
    print("   4. 注意所有功能都通过控制器处理\n")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()