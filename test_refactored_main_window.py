"""测试重构后的主窗口"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from src.main_window.main_window import MainWindow


def test_main_window():
    """测试主窗口功能"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 记录启动成功
    window.log_message("✅ 重构后的主窗口启动成功")
    window.log_message("📋 模块化架构加载完成:")
    window.log_message("  - UI组件: 工具栏、信息面板、可视化面板、操作面板")
    window.log_message("  - 管理器: 检测、模拟、产品、搜索、DXF")
    window.log_message("  - 服务: 状态服务、导航服务")
    window.log_message("🎯 请测试各项功能是否正常")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    test_main_window()