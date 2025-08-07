#!/usr/bin/env python3
"""
测试全景图移除和视图切换功能
验证修改后的主检测视图是否正常工作
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_view_switching():
    """测试视图切换功能"""
    try:
        # 导入主检测视图
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        app = QApplication([])
        
        # 创建主检测视图实例
        main_view = NativeMainDetectionView()
        
        print("✅ 主检测视图创建成功")
        
        # 检查左侧面板是否移除了全景预览
        if hasattr(main_view.left_panel, 'sidebar_panorama'):
            print("❌ 左侧面板仍然包含全景预览组件")
            return False
        else:
            print("✅ 左侧面板已成功移除全景预览组件")
        
        # 检查中间面板的视图模式
        if main_view.center_panel.current_view_mode == "micro":
            print("✅ 中间面板默认为微观视图模式")
        else:
            print(f"❌ 中间面板默认模式错误: {main_view.center_panel.current_view_mode}")
            return False
        
        # 检查是否有两个视图按钮
        if hasattr(main_view.center_panel, 'panorama_view_btn'):
            print("❌ 中间面板仍然包含全景总览按钮")
            return False
        else:
            print("✅ 中间面板已移除全景总览按钮")
        
        # 检查macro和micro按钮是否存在
        if hasattr(main_view.center_panel, 'macro_view_btn') and hasattr(main_view.center_panel, 'micro_view_btn'):
            print("✅ 中间面板包含宏观和微观视图按钮")
        else:
            print("❌ 中间面板缺少视图切换按钮")
            return False
        
        # 测试视图切换
        def test_switch_to_macro():
            print("🔄 测试切换到宏观视图...")
            main_view.center_panel._on_view_mode_changed("macro")
            if main_view.center_panel.current_view_mode == "macro":
                print("✅ 成功切换到宏观视图")
            else:
                print("❌ 宏观视图切换失败")
        
        def test_switch_to_micro():
            print("🔄 测试切换到微观视图...")
            main_view.center_panel._on_view_mode_changed("micro")
            if main_view.center_panel.current_view_mode == "micro":
                print("✅ 成功切换到微观视图")
            else:
                print("❌ 微观视图切换失败")
        
        # 显示窗口
        main_view.show()
        
        # 设置定时器进行自动测试
        timer = QTimer()
        test_steps = [
            (1000, test_switch_to_macro),
            (2000, test_switch_to_micro),
            (3000, lambda: print("✅ 所有测试完成")),
            (3500, app.quit)
        ]
        
        for delay, func in test_steps:
            QTimer.singleShot(delay, func)
        
        print("🚀 启动GUI测试...")
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_modules():
    """测试模块导入"""
    print("📦 测试模块导入...")
    
    try:
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        print("✅ 主检测视图导入成功")
        
        from src.pages.main_detection_p1.components.center_visualization_panel import CenterVisualizationPanel
        print("✅ 中间可视化面板导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 开始测试全景图移除功能...")
    
    # 测试模块导入
    if not test_import_modules():
        sys.exit(1)
    
    # 测试视图切换
    if not test_view_switching():
        sys.exit(1)
    
    print("🎉 所有测试通过！")