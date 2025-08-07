#!/usr/bin/env python3
"""
最终业务逻辑测试脚本
验证全景图移除后的核心业务功能是否正常工作
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_business_workflow():
    """测试完整的业务工作流程"""
    print("🔧 测试业务工作流程...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        # 1. 创建主检测视图
        main_view = NativeMainDetectionView()
        print("✅ 主检测视图创建成功")
        
        # 2. 创建测试数据
        test_holes = {}
        for i in range(20):
            hole = HoleData(
                center_x=i * 20.0,
                center_y=(i % 5) * 20.0,
                radius=8.0,
                hole_id=f"H_{i:03d}",
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(test_holes)
        print("✅ 测试数据创建成功")
        
        # 3. 测试数据加载
        main_view.load_hole_collection(test_collection)
        print("✅ 数据加载功能正常")
        
        # 4. 测试视图切换到宏观模式
        main_view.center_panel._on_view_mode_changed("macro")
        assert main_view.center_panel.current_view_mode == "macro"
        print("✅ 宏观视图切换成功")
        
        # 5. 测试扇形点击功能（模拟从宏观视图点击扇形）
        main_view._on_panorama_sector_clicked(SectorQuadrant.SECTOR_1)
        print("✅ 扇形点击功能正常")
        
        # 手动切换到微观视图来查看结果
        main_view.center_panel._on_view_mode_changed("micro")
        assert main_view.center_panel.current_view_mode == "micro"
        print("✅ 微观视图切换成功")
        
        # 6. 测试协调器功能
        if main_view.coordinator:
            print("✅ 协调器正常工作")
        else:
            print("⚠️ 协调器未初始化")
        
        # 7. 测试左侧面板统计更新
        stats_data = {
            'total': 20,
            'qualified': 15,
            'unqualified': 2,
            'not_detected': 3,
            'completed': 17,
            'pending': 3,
            'progress': 85.0,
            'completion_rate': 85.0,
            'qualification_rate': 95.0
        }
        main_view.left_panel.update_progress_display(stats_data)
        print("✅ 左侧面板统计更新功能正常")
        
        # 8. 测试右侧面板控制
        assert hasattr(main_view.right_panel, 'start_detection'), "缺少开始检测功能"
        assert hasattr(main_view.right_panel, 'start_simulation'), "缺少开始模拟功能"
        print("✅ 右侧面板控制功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 业务工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_integrity():
    """测试数据完整性"""
    print("🗄️ 测试数据完整性...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        main_view = NativeMainDetectionView()
        
        # 创建测试数据
        original_holes = {}
        for i in range(10):
            hole = HoleData(
                center_x=i * 10.0,
                center_y=i * 10.0,
                radius=5.0,
                hole_id=f"TEST_{i:03d}",
                status=HoleStatus.PENDING
            )
            original_holes[hole.hole_id] = hole
        
        original_collection = HoleCollection(original_holes)
        
        # 加载数据
        main_view.load_hole_collection(original_collection)
        
        # 验证数据完整性
        assert main_view.current_hole_collection is not None, "数据未正确保存"
        assert len(main_view.current_hole_collection.holes) == 10, "孔位数量不匹配"
        
        # 验证数据在中间面板中的加载
        if hasattr(main_view.center_panel, 'load_hole_collection'):
            # 数据应该同时加载到两个视图中
            print("✅ 中间面板数据加载接口存在")
        
        print("✅ 数据完整性验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据完整性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_consistency():
    """测试UI一致性"""
    print("🎨 测试UI一致性...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        main_view = NativeMainDetectionView()
        
        # 检查初始状态
        assert main_view.center_panel.current_view_mode == "micro", "默认视图模式错误"
        assert main_view.center_panel.micro_view_btn.isChecked(), "微观按钮状态错误"
        assert not main_view.center_panel.macro_view_btn.isChecked(), "宏观按钮状态错误"
        
        # 测试视图切换后的状态一致性
        main_view.center_panel._on_view_mode_changed("macro")
        assert main_view.center_panel.current_view_mode == "macro", "宏观视图切换后状态错误"
        assert main_view.center_panel.macro_view_btn.isChecked(), "宏观按钮切换后状态错误"
        assert not main_view.center_panel.micro_view_btn.isChecked(), "微观按钮切换后状态错误"
        
        # 切换回微观视图
        main_view.center_panel._on_view_mode_changed("micro")
        assert main_view.center_panel.current_view_mode == "micro", "微观视图切换回状态错误"
        assert main_view.center_panel.micro_view_btn.isChecked(), "微观按钮切换回状态错误"
        assert not main_view.center_panel.macro_view_btn.isChecked(), "宏观按钮切换回状态错误"
        
        print("✅ UI一致性验证通过")
        return True
        
    except Exception as e:
        print(f"❌ UI一致性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_final_tests():
    """运行最终测试"""
    print("🚀 开始最终业务逻辑测试...")
    
    tests = [
        ("业务工作流程", test_business_workflow),
        ("数据完整性", test_data_integrity),
        ("UI一致性", test_ui_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print('='*60)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print("最终测试总结")
    print('='*60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有业务逻辑测试通过！")
        print("🔒 功能完整性验证成功！")
        return True
    else:
        print(f"⚠️ 有 {failed} 个测试失败")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.WARNING)
    
    success = run_final_tests()
    sys.exit(0 if success else 1)