#!/usr/bin/env python3
"""
UI布局增强截图脚本
生成增强后的UI布局截图用于验证
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QPixmap
    
    # 导入增强后的组件
    from src.modules.main_detection_view import MainDetectionView
    
    class ScreenshotWindow(QMainWindow):
        """截图窗口"""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("AIDCIS3-LFS UI布局增强演示")
            self.setMinimumSize(1400, 900)
            
            # 创建主检测视图
            self.main_detection_view = MainDetectionView()
            self.setCentralWidget(self.main_detection_view)
            
            # 设置一些演示数据
            self.setup_demo_data()
            
            # 设置定时器来截图
            QTimer.singleShot(2000, self.take_screenshot)
        
        def setup_demo_data(self):
            """设置演示数据"""
            try:
                # 更新文件信息
                self.main_detection_view.update_file_info(
                    "/demo/workpiece_sample.dxf", 
                    "3.2 MB", 
                    "0.8 秒"
                )
                
                # 更新进度数据
                self.main_detection_view.update_rates_display(73.5, 89.2)
                self.main_detection_view.update_time_display("00:12:45", "00:04:15")
                
                # 设置工具栏产品名称
                if hasattr(self.main_detection_view, 'toolbar') and self.main_detection_view.toolbar:
                    self.main_detection_view.set_toolbar_product("产品型号-ABC123")
                
                # 添加一些日志消息来展示功能
                self.main_detection_view.log_message("系统初始化完成", "green")
                self.main_detection_view.log_message("DXF文件加载成功", "blue")
                self.main_detection_view.log_message("批次检测开始", "blue")
                self.main_detection_view.log_message("检测进度: 73.5%", "blue")
                self.main_detection_view.log_message("发现2个异常孔位", "orange")
                
                print("✅ 演示数据设置完成")
                
            except Exception as e:
                print(f"❌ 设置演示数据失败: {e}")
        
        def take_screenshot(self):
            """截图"""
            try:
                # 截取整个窗口
                pixmap = self.grab()
                
                # 保存截图
                screenshot_path = project_root / "ui_enhancement_screenshot.png"
                success = pixmap.save(str(screenshot_path))
                
                if success:
                    print(f"✅ 截图已保存: {screenshot_path}")
                    print("📸 展示了以下UI布局增强:")
                    print("   - 顶部工具栏 (产品选择、搜索、过滤)")
                    print("   - 左侧面板增强 (380px宽度、批次进度、时间跟踪、全景预览位置、扇形统计位置)")
                    print("   - 中间面板增强 (层级化视图控制框架)")
                    print("   - 右侧面板增强 (模拟功能组、导航功能组、文件操作组、6个视图控制按钮)")
                else:
                    print("❌ 截图保存失败")
                
                # 退出应用
                QApplication.quit()
                
            except Exception as e:
                print(f"❌ 截图失败: {e}")
                QApplication.quit()
    
    def main():
        """主函数"""
        print("🚀 开始UI布局增强截图...")
        
        app = QApplication(sys.argv)
        
        # 创建并显示窗口
        window = ScreenshotWindow()
        window.show()
        
        # 运行应用
        app.exec()
        
        print("🎉 UI布局增强截图完成")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装PySide6: pip install PySide6")
    sys.exit(1)
except Exception as e:
    print(f"❌ 截图脚本运行失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)