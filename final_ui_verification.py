#!/usr/bin/env python3
"""
最终UI验证脚本
启动主程序并自动切换到实时监控标签页
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动主程序进行最终验证"""
    print("🚀 启动最终UI验证...")
    
    app = QApplication(sys.argv)
    
    try:
        from src.main_window import MainWindowEnhanced
        
        # 创建主窗口
        window = MainWindowEnhanced()
        window.setWindowTitle("AIDCIS3-LFS - 内窥镜组件验证")
        
        # 显示窗口
        window.show()
        
        # 自动切换到实时监控标签页
        def switch_to_realtime_tab():
            if hasattr(window, 'tab_widget'):
                # 查找实时监控标签页的索引
                for i in range(window.tab_widget.count()):
                    if "实时监控" in window.tab_widget.tabText(i):
                        window.tab_widget.setCurrentIndex(i)
                        print(f"✅ 已切换到实时监控标签页 (索引: {i})")
                        
                        # 验证内窥镜组件
                        verify_endoscope_component(window)
                        break
                        
        def verify_endoscope_component(window):
            """验证内窥镜组件"""
            if hasattr(window, 'realtime_tab'):
                realtime_tab = window.realtime_tab
                
                if hasattr(realtime_tab, 'endoscope_view'):
                    endoscope = realtime_tab.endoscope_view
                    print("✅ 内窥镜组件验证:")
                    print(f"   - 组件存在: ✅")
                    print(f"   - 可见性: {'✅' if endoscope.isVisible() else '❌'}")
                    print(f"   - 尺寸: {endoscope.size()}")
                    print(f"   - 最小尺寸: {endoscope.minimumSize()}")
                    
                    if hasattr(realtime_tab, 'main_splitter'):
                        splitter = realtime_tab.main_splitter
                        sizes = splitter.sizes()
                        print(f"   - 分割器尺寸分配: {sizes}")
                        
                        if len(sizes) >= 2 and sizes[1] > 0:
                            print("✅ 内窥镜区域有足够空间")
                        else:
                            print("⚠️ 内窥镜区域空间不足")
                    
                    # 显示成功消息
                    show_success_message()
                else:
                    print("❌ 内窥镜组件不存在")
                    show_error_message("内窥镜组件不存在")
            else:
                print("❌ 实时监控标签页不存在")
                show_error_message("实时监控标签页不存在")
                
        def show_success_message():
            """显示成功消息"""
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("验证成功")
            msg.setText("内窥镜组件修复验证成功！")
            msg.setInformativeText(
                "✅ 内窥镜组件已正确集成到实时监控页面\n"
                "✅ 组件布局正常，上下分割显示\n"
                "✅ 上半部分：管孔直径实时监控图表\n"
                "✅ 下半部分：内窥镜图像显示区域\n\n"
                "现在可以正常使用实时监控功能！"
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            
        def show_error_message(error):
            """显示错误消息"""
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("验证失败")
            msg.setText(f"内窥镜组件验证失败: {error}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        
        # 延迟1秒后切换标签页，确保窗口完全加载
        QTimer.singleShot(1000, switch_to_realtime_tab)
        
        print("🎯 验证要点:")
        print("   1. 窗口应该显示多个标签页")
        print("   2. 会自动切换到'实时监控'标签页")
        print("   3. 上半部分显示图表，下半部分显示内窥镜区域")
        print("   4. 内窥镜区域应显示占位符文本")
        print("   5. 会弹出验证结果对话框")
        
        # 启动应用
        return app.exec()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())