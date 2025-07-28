"""
主窗口聚合引用文件 - 新平级P架构
将四个P级页面（P1检测、P2实时、P3统计、P4报告）聚合为统一的主窗口

此文件现在是一个轻量级的聚合器，真正的实现位于各个平级P包中
"""

import sys
import logging
import warnings
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入新的平级P架构
try:
    # 导入新平级P架构的主窗口聚合器
    from src.main_window_aggregator import MainWindowAggregator
    
    logging.getLogger(__name__).info("✅ 成功导入新平级P架构主窗口聚合器")
    
    # 主窗口类（使用P1架构）
    MainWindowEnhanced = MainWindowAggregator
    MainWindow = MainWindowAggregator
    
except ImportError as e:
    logging.getLogger(__name__).error(f"❌ 新平级P架构导入失败: {e}")
    logging.getLogger(__name__).warning("⚠️ 回退到原始架构...")
    
    # 回退到原始实现
    try:
        # 导入原始备份实现
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "main_window_original", 
            str(Path(__file__).parent / "main_window_original_backup.py")
        )
        main_window_original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_window_original)
        
        MainWindowEnhanced = main_window_original.MainWindowEnhanced
        MainWindow = main_window_original.MainWindowEnhanced
        
        logging.getLogger(__name__).info("✅ 原始架构加载成功")
        
    except Exception as fallback_error:
        logging.getLogger(__name__).error(f"❌ 原始架构加载也失败: {fallback_error}")
        
        # 最终回退：创建一个基础窗口
        from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
        
        class FallbackMainWindow(QMainWindow):
            """回退主窗口"""
            def __init__(self):
                super().__init__()
                self.setWindowTitle("AIDCIS3-LFS (回退模式)")
                central = QWidget()
                layout = QVBoxLayout(central)
                layout.addWidget(QLabel("主窗口加载失败，请检查配置"))
                self.setCentralWidget(central)
                
        MainWindowEnhanced = FallbackMainWindow
        MainWindow = FallbackMainWindow


def main():
    """
    应用程序入口点
    支持P1架构和原始架构的自动切换
    """
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    try:
        # 创建主窗口实例
        window = MainWindowEnhanced()
        window.show()
        
        logging.getLogger(__name__).info(f"🚀 主窗口启动成功: {type(window).__name__}")
        
        sys.exit(app.exec())
        
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ 应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()


# 导出列表（向后兼容）
__all__ = [
    'MainWindowEnhanced',
    'MainWindow', 
    'main'
]


# 架构信息
def get_architecture_info():
    """获取当前使用的架构信息"""
    return {
        'current_architecture': 'FlatP' if 'MainWindowAggregator' in str(type(MainWindowEnhanced)) else 'Original',
        'package_location': 'src.pages.* (平级P包)',
        'fallback_available': True,
        'features': [
            '平级P页面架构',
            'P1-P4级别清晰',
            '独立功能模块',
            '统一聚合接口'
        ]
    }