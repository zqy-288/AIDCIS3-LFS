"""
上位机软件主程序入口
管孔检测系统
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

# 添加当前目录和模块目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))
sys.path.insert(0, os.path.join(current_dir, 'hardware'))
sys.path.insert(0, os.path.join(current_dir, 'models'))

from main_window import MainWindow
from modules.models import db_manager


def remove_all_inline_styles(widget, count=0):
    """递归移除所有内联样式"""
    if widget and hasattr(widget, 'styleSheet'):
        if widget.styleSheet():
            widget.setStyleSheet("")
            count += 1
            
    # 递归处理子widget
    if hasattr(widget, 'findChildren'):
        from PySide6.QtWidgets import QWidget
        for child in widget.findChildren(QWidget):
            count = remove_all_inline_styles(child, count)
            
    return count


def force_dark_palette_to_all(app, theme_manager):
    """强制为所有组件应用深色调色板"""
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
    
    palette = QPalette()
    colors = theme_manager.COLORS
    
    # 设置所有颜色角色
    palette.setColor(QPalette.Window, QColor(colors['background_primary']))
    palette.setColor(QPalette.WindowText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Base, QColor(colors['background_secondary']))
    palette.setColor(QPalette.AlternateBase, QColor(colors['background_tertiary']))
    palette.setColor(QPalette.ToolTipBase, QColor(colors['background_tertiary']))
    palette.setColor(QPalette.ToolTipText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Text, QColor(colors['text_primary']))
    palette.setColor(QPalette.BrightText, QColor(colors['text_secondary']))
    palette.setColor(QPalette.Button, QColor(colors['background_tertiary']))
    palette.setColor(QPalette.ButtonText, QColor(colors['text_primary']))
    palette.setColor(QPalette.Link, QColor(colors['accent_primary']))
    palette.setColor(QPalette.Highlight, QColor(colors['accent_primary']))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    
    # 应用到应用程序和所有widget
    app.setPalette(palette)
    for widget in app.allWidgets():
        if widget:
            widget.setPalette(palette)


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

    # 应用现代科技蓝深色主题作为默认主题 - 强制模式
    try:
        from modules.theme_manager import theme_manager
        
        # 1. 首先设置全局强制深色样式表
        colors = theme_manager.COLORS
        global_dark_style = f"""
        * {{
            background-color: {colors['background_primary']} !important;
            color: {colors['text_primary']} !important;
        }}
        QMainWindow {{
            background-color: {colors['background_primary']} !important;
        }}
        QLabel {{
            color: {colors['text_primary']} !important;
        }}
        QPushButton {{
            background-color: {colors['background_tertiary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
        }}
        QTabWidget::pane {{
            background-color: {colors['background_secondary']} !important;
        }}
        QTabBar::tab {{
            background-color: {colors['background_tertiary']} !important;
            color: {colors['text_primary']} !important;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['accent_primary']} !important;
            color: white !important;
        }}
        """
        app.setStyleSheet(global_dark_style)
        
        # 2. 然后应用主题管理器的深色主题
        theme_manager.apply_dark_theme(app)
        print("🎨 强制深色主题已应用（全局!important样式）")
    except Exception as e:
        print(f"⚠️ 主题应用失败: {e}")

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

        # 初始化数据库
        print("初始化数据库...")
        db_manager.create_sample_data()

        # 创建主窗口
        main_window = MainWindow()
        
        # 强制确保深色主题生效（基于成功的主题切换工具经验）
        try:
            from modules.theme_manager import theme_manager
            
            print("🎨 强制确保深色主题生效...")
            
            # 1. 首先移除所有内联样式（这是关键！）
            print("📝 移除所有内联样式...")
            count = remove_all_inline_styles(main_window)
            print(f"✅ 已移除 {count} 个内联样式")
            
            # 2. 再次强制应用深色主题
            theme_manager.apply_dark_theme(app)
            
            # 3. 强制应用深色调色板到所有组件
            force_dark_palette_to_all(app, theme_manager)
            
            # 4. 强制刷新所有组件样式
            for widget in app.allWidgets():
                if widget:
                    try:
                        widget.style().unpolish(widget)
                        widget.style().polish(widget)
                        if hasattr(widget, 'update') and callable(widget.update):
                            try:
                                widget.update()
                            except TypeError:
                                pass
                    except Exception:
                        pass
            
            print("✅ 深色主题强制确保完成")
            
        except Exception as e:
            print(f"⚠️ 强制主题应用失败: {e}")
            import traceback
            traceback.print_exc()

        # 显示主窗口
        main_window.show()
        
        # 最后一次强制确保深色主题（在所有组件初始化完成后）
        def final_theme_force():
            try:
                print("🔥 最终强制深色主题...")
                from modules.theme_manager import theme_manager
                
                # 移除任何可能的新增内联样式
                count = remove_all_inline_styles(main_window)
                if count > 0:
                    print(f"⚠️ 发现并移除了 {count} 个新的内联样式")
                
                # 强制应用深色主题
                theme_manager.apply_dark_theme(app)
                force_dark_palette_to_all(app, theme_manager)
                
                # 强制刷新
                main_window.repaint()
                
                print("✅ 最终深色主题强制完成")
                
            except Exception as e:
                print(f"最终主题强制失败: {e}")
        
        # 延迟500ms执行，确保所有组件都已完全初始化
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, final_theme_force)

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
