#!/usr/bin/env python3
"""
全景图移除功能的综合测试脚本
验证所有核心功能是否正常工作，包括数据加载、视图切换、扇形交互等
"""

import sys
import logging
from pathlib import Path
import traceback

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_component_structure():
    """测试组件结构完整性"""
    print("🏗️ 测试组件结构...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 测试左侧面板结构
        assert hasattr(main_view, 'left_panel'), "❌ 缺少左侧面板"
        assert not hasattr(main_view.left_panel, 'sidebar_panorama'), "❌ 左侧面板仍包含全景组件"
        assert not hasattr(main_view.left_panel, 'panorama_group'), "❌ 左侧面板仍包含全景组"
        print("✅ 左侧面板结构正确")
        
        # 测试中间面板结构
        assert hasattr(main_view, 'center_panel'), "❌ 缺少中间面板"
        assert hasattr(main_view.center_panel, 'macro_view_btn'), "❌ 缺少宏观视图按钮"
        assert hasattr(main_view.center_panel, 'micro_view_btn'), "❌ 缺少微观视图按钮"
        assert not hasattr(main_view.center_panel, 'panorama_view_btn'), "❌ 仍包含全景总览按钮"
        print("✅ 中间面板结构正确")
        
        # 测试右侧面板结构
        assert hasattr(main_view, 'right_panel'), "❌ 缺少右侧面板"
        print("✅ 右侧面板结构正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件结构测试失败: {e}")
        traceback.print_exc()
        return False

def test_default_view_mode():
    """测试默认视图模式"""
    print("🎯 测试默认视图模式...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 检查默认视图模式
        assert main_view.center_panel.current_view_mode == "micro", f"❌ 默认视图模式错误: {main_view.center_panel.current_view_mode}"
        
        # 检查按钮状态
        assert main_view.center_panel.micro_view_btn.isChecked(), "❌ 微观视图按钮未默认选中"
        assert not main_view.center_panel.macro_view_btn.isChecked(), "❌ 宏观视图按钮不应默认选中"
        
        print("✅ 默认视图模式正确")
        return True
        
    except Exception as e:
        print(f"❌ 默认视图模式测试失败: {e}")
        traceback.print_exc()
        return False

def test_view_switching():
    """测试视图切换功能"""
    print("🔄 测试视图切换功能...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 测试切换到宏观视图
        main_view.center_panel._on_view_mode_changed("macro")
        assert main_view.center_panel.current_view_mode == "macro", "❌ 宏观视图切换失败"
        assert main_view.center_panel.macro_view_btn.isChecked(), "❌ 宏观视图按钮状态错误"
        assert not main_view.center_panel.micro_view_btn.isChecked(), "❌ 微观视图按钮状态错误"
        
        # 测试切换到微观视图
        main_view.center_panel._on_view_mode_changed("micro")
        assert main_view.center_panel.current_view_mode == "micro", "❌ 微观视图切换失败"
        assert main_view.center_panel.micro_view_btn.isChecked(), "❌ 微观视图按钮状态错误"
        assert not main_view.center_panel.macro_view_btn.isChecked(), "❌ 宏观视图按钮状态错误"
        
        print("✅ 视图切换功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 视图切换测试失败: {e}")
        traceback.print_exc()
        return False

def test_panorama_widget_creation():
    """测试全景组件创建"""
    print("🌍 测试全景组件创建...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.components.center_visualization_panel import CenterVisualizationPanel
        
        center_panel = CenterVisualizationPanel()
        
        # 测试全景组件创建方法存在
        assert hasattr(center_panel, '_create_panorama_widget'), "❌ 缺少全景组件创建方法"
        assert hasattr(center_panel, '_show_panorama_view'), "❌ 缺少显示全景视图方法"
        assert hasattr(center_panel, '_show_sector_view'), "❌ 缺少显示扇形视图方法"
        
        # 测试数据加载方法
        assert hasattr(center_panel, 'load_hole_collection'), "❌ 缺少数据加载方法"
        
        print("✅ 全景组件创建功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 全景组件创建测试失败: {e}")
        traceback.print_exc()
        return False

def test_hole_data_loading():
    """测试孔位数据加载"""
    print("📊 测试孔位数据加载...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        main_view = NativeMainDetectionView()
        
        # 创建测试数据
        test_holes = {}
        for i in range(10):
            hole = HoleData(
                center_x=i * 10.0,
                center_y=i * 10.0,
                radius=5.0,
                hole_id=f"TEST_{i:03d}",
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(test_holes)
        
        # 测试数据加载方法存在
        assert hasattr(main_view, 'load_hole_collection'), "❌ 缺少数据加载方法"
        
        # 测试中间面板数据加载
        if hasattr(main_view.center_panel, 'load_hole_collection'):
            main_view.center_panel.load_hole_collection(test_collection)
            print("✅ 中间面板数据加载成功")
        
        print("✅ 孔位数据加载功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 孔位数据加载测试失败: {e}")
        traceback.print_exc()
        return False

def test_sector_interaction():
    """测试扇形交互功能"""
    print("🎯 测试扇形交互功能...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        main_view = NativeMainDetectionView()
        
        # 测试扇形点击处理方法存在
        assert hasattr(main_view, '_on_panorama_sector_clicked'), "❌ 缺少扇形点击处理方法"
        assert hasattr(main_view, '_on_sector_stats_updated'), "❌ 缺少扇形统计更新方法"
        
        # 测试协调器存在
        if main_view.coordinator:
            print("✅ 扇形协调器初始化成功")
        else:
            print("⚠️ 扇形协调器未初始化")
        
        print("✅ 扇形交互功能结构正常")
        return True
        
    except Exception as e:
        print(f"❌ 扇形交互测试失败: {e}")
        traceback.print_exc()
        return False

def test_signal_connections():
    """测试信号连接"""
    print("📡 测试信号连接...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 测试中间面板信号
        assert hasattr(main_view.center_panel, 'hole_selected'), "❌ 缺少孔位选择信号"
        assert hasattr(main_view.center_panel, 'view_mode_changed'), "❌ 缺少视图模式变化信号"
        
        # 测试右侧面板信号
        assert hasattr(main_view.right_panel, 'start_detection'), "❌ 缺少开始检测信号"
        assert hasattr(main_view.right_panel, 'start_simulation'), "❌ 缺少开始模拟信号"
        
        print("✅ 信号连接结构正常")
        return True
        
    except Exception as e:
        print(f"❌ 信号连接测试失败: {e}")
        traceback.print_exc()
        return False

def test_ui_rendering():
    """测试UI渲染"""
    print("🎨 测试UI渲染...")
    
    try:
        app = QApplication.instance()
        if not app:
            print("⚠️ 没有QApplication实例，跳过UI渲染测试")
            return True
            
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 检查组件的基本结构是否正常
        assert hasattr(main_view, 'left_panel'), "❌ 缺少左侧面板"
        assert hasattr(main_view, 'center_panel'), "❌ 缺少中间面板"
        assert hasattr(main_view, 'right_panel'), "❌ 缺少右侧面板"
        
        # 检查组件是否可以创建
        assert main_view.left_panel is not None, "❌ 左侧面板未创建"
        assert main_view.center_panel is not None, "❌ 中间面板未创建"
        assert main_view.right_panel is not None, "❌ 右侧面板未创建"
        
        print("✅ UI结构渲染正常")
        return True
        
    except Exception as e:
        print(f"❌ UI渲染测试失败: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """运行全面测试"""
    print("🚀 开始全面测试...")
    
    tests = [
        ("组件结构", test_component_structure),
        ("默认视图模式", test_default_view_mode),
        ("视图切换", test_view_switching),
        ("全景组件创建", test_panorama_widget_creation),
        ("孔位数据加载", test_hole_data_loading),
        ("扇形交互", test_sector_interaction),
        ("信号连接", test_signal_connections),
        ("UI渲染", test_ui_rendering),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print("测试总结")
    print('='*50)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有测试通过！")
        return True
    else:
        print(f"⚠️ 有 {failed} 个测试失败")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.WARNING)  # 减少日志噪音
    
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)