"""
上位机软件主程序入口
管孔检测系统
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

# 添加项目根目录和src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))  # 项目根目录
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)  # 项目根目录
sys.path.insert(0, src_dir)      # src目录
# sys.path.insert(0, os.path.join(src_dir, 'modules'))  # src/modules目录已删除
sys.path.insert(0, os.path.join(src_dir, 'core', 'hardware')) # src/core/hardware目录

# 导入主窗口
from src.main_window import MainWindow


def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        ('PySide6', 'PySide6'),
        ('pyqtgraph', 'pyqtgraph'),
        ('numpy', 'numpy'),
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        error_msg = f"缺少必要的依赖包：{', '.join(missing_packages)}\n"
        error_msg += "请运行以下命令安装：\n"
        error_msg += f"pip install {' '.join(missing_packages)}"
        
        print(error_msg)
        return False
    
    return True


def setup_application():
    """设置应用程序属性"""
    # 检查是否已有应用程序实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("上位机软件")
    app.setApplicationDisplayName("管孔检测系统")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("检测系统开发团队")
    app.setOrganizationDomain("detection-system.com")

    # 设置应用程序图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))

    # 设置高DPI支持
    # 注意：在PySide6中，高DPI缩放默认启用，无需手动设置
    # Qt.AA_EnableHighDpiScaling 和 Qt.AA_UseHighDpiPixmaps 在Qt6中已弃用

    # 应用现代科技蓝主题 - 使用统一的共享主题管理器
    try:
        from src.shared.components.theme import apply_theme
        apply_theme(app)
        print("✅ 统一主题管理器 - 现代科技蓝主题已应用")
    except Exception as e:
        print(f"⚠️ 主题应用失败: {e}")
        # 继续运行，不应该因为主题失败而终止程序

    return app


def main():
    """主函数"""
    print("=" * 50)
    print("上位机软件 - 管孔检测系统")
    print("版本: 1.0.0")
    print("负责人: Tsinghua")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return 1
    
    try:
        # 创建应用程序
        app = setup_application()

        # 跳过旧的服务初始化，新版本使用内置的依赖注入
        print("使用新版本的服务架构...")
        
        # 跳过数据库初始化，新版本使用不同的数据管理方式
        print("跳过旧版数据库初始化...")

        # 创建主窗口
        main_window = MainWindow()

        # 显示主窗口
        main_window.show()

        print("应用程序启动成功")
        print("主窗口已显示")
        print("数据库初始化完成")

        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        error_msg = f"应用程序启动失败：{str(e)}"
        print(error_msg)
        
        # 如果Qt应用已创建，显示错误对话框
        try:
            QMessageBox.critical(None, "启动错误", error_msg)
        except:
            pass
            
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
