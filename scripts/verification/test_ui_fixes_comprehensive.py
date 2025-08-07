#!/usr/bin/env python3
"""
综合测试UI修复
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_ui_fixes():
    """测试UI修复"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    test_results = {
        'default_micro_view': False,
        'no_multiple_zoom': False,
        'correct_detection_order': False,
        'correct_sector_assignment': False,
        'errors': []
    }
    
    try:
        # 导入必要的模块
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
        from src.core_business.hole_numbering_service import HoleNumberingService
        
        # 创建主视图
        print("\n" + "="*80)
        print("开始UI修复测试")
        print("="*80)
        
        view = NativeMainDetectionView()
        
        # 测试1: 检查默认视图模式
        print("\n1. 测试默认微观视图...")
        if hasattr(view, 'center_panel') and view.center_panel:
            if hasattr(view.center_panel, 'micro_view_btn'):
                is_micro_checked = view.center_panel.micro_view_btn.isChecked()
                current_mode = getattr(view.center_panel, 'current_view_mode', None)
                
                print(f"   微观视图按钮选中: {is_micro_checked}")
                print(f"   当前视图模式: {current_mode}")
                
                test_results['default_micro_view'] = (
                    is_micro_checked and current_mode == "micro"
                )
        
        # 加载测试数据
        print("\n2. 加载测试数据...")
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        if Path(dxf_path).exists():
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                # 应用编号
                numbering_service = HoleNumberingService()
                numbered_collection = numbering_service.apply_numbering(hole_collection)
                
                # 加载到视图
                view.load_hole_collection(numbered_collection)
                print(f"   ✅ 加载了 {len(numbered_collection.holes)} 个孔位")
                
                # 等待加载完成
                app.processEvents()
                QTimer.singleShot(100, app.quit)
                app.exec()
                
                # 测试2: 检查是否有多次缩放
                print("\n3. 测试扇形切换缩放...")
                
                # 监听缩放事件
                zoom_count = 0
                original_fit_to_window = None
                
                if hasattr(view, 'center_panel') and view.center_panel:
                    graphics_view = getattr(view.center_panel, 'graphics_view', None)
                    if graphics_view:
                        # 记录原始方法
                        if hasattr(graphics_view, 'fit_to_window_width'):
                            original_fit_to_window = graphics_view.fit_to_window_width
                            
                            def track_zoom(*args, **kwargs):
                                nonlocal zoom_count
                                zoom_count += 1
                                print(f"   检测到缩放 #{zoom_count}")
                                return original_fit_to_window(*args, **kwargs)
                            
                            graphics_view.fit_to_window_width = track_zoom
                
                # 切换扇形测试
                if view.coordinator:
                    from src.core_business.graphics.sector_types import SectorQuadrant
                    
                    # 记录初始状态
                    initial_sector = view.coordinator.current_sector
                    print(f"   初始扇形: {initial_sector}")
                    
                    # 切换到另一个扇形
                    zoom_count = 0  # 重置计数
                    view.coordinator.select_sector(SectorQuadrant.SECTOR_2)
                    
                    # 等待处理
                    app.processEvents()
                    QTimer.singleShot(500, app.quit)
                    app.exec()
                    
                    print(f"   切换扇形后缩放次数: {zoom_count}")
                    test_results['no_multiple_zoom'] = zoom_count <= 1
                
                # 测试3: 检查检测顺序
                print("\n4. 测试检测顺序...")
                if view.simulation_controller:
                    view.simulation_controller.load_hole_collection(numbered_collection)
                    view.simulation_controller._generate_detection_units()
                    
                    if view.simulation_controller.detection_units:
                        # 检查前10个单元
                        first_10 = view.simulation_controller.detection_units[:10]
                        print("   前10个检测单元:")
                        
                        for i, unit in enumerate(first_10):
                            if unit.is_pair and len(unit.holes) >= 2:
                                print(f"   {i+1}. {unit.holes[0].hole_id} + {unit.holes[1].hole_id}")
                            else:
                                print(f"   {i+1}. {unit.holes[0].hole_id}")
                        
                        # 检查第一个是否包含R164
                        first_unit = view.simulation_controller.detection_units[0]
                        first_hole_id = first_unit.holes[0].hole_id
                        
                        test_results['correct_detection_order'] = "R164" in first_hole_id
                
                # 测试4: 检查扇形分配
                print("\n5. 测试扇形分配...")
                if view.coordinator and hasattr(view.coordinator, 'sector_assignment_manager'):
                    sam = view.coordinator.sector_assignment_manager
                    
                    # 获取特定孔位的扇形
                    from src.core_business.graphics.sector_types import SectorQuadrant
                    
                    test_holes = {
                        "BC098R001": SectorQuadrant.SECTOR_1,  # 应该在右上
                        "AC098R001": SectorQuadrant.SECTOR_2,  # 应该在左上
                        "AC098R164": SectorQuadrant.SECTOR_3,  # 应该在左下
                        "BC098R164": SectorQuadrant.SECTOR_4,  # 应该在右下
                    }
                    
                    all_correct = True
                    for hole_id, expected_sector in test_holes.items():
                        if hole_id in sam.sector_assignments:
                            actual_sector = sam.sector_assignments[hole_id]
                            is_correct = actual_sector == expected_sector
                            all_correct &= is_correct
                            
                            status = "✅" if is_correct else "❌"
                            print(f"   {status} {hole_id}: {actual_sector} (期望: {expected_sector})")
                    
                    test_results['correct_sector_assignment'] = all_correct
        
        else:
            test_results['errors'].append(f"DXF文件不存在: {dxf_path}")
    
    except Exception as e:
        test_results['errors'].append(str(e))
        import traceback
        traceback.print_exc()
    
    # 输出测试结果
    print("\n" + "="*80)
    print("测试结果总结")
    print("="*80)
    
    print(f"1. 默认微观视图: {'✅ 通过' if test_results['default_micro_view'] else '❌ 失败'}")
    print(f"2. 无多次缩放: {'✅ 通过' if test_results['no_multiple_zoom'] else '❌ 失败'}")
    print(f"3. 检测顺序正确: {'✅ 通过' if test_results['correct_detection_order'] else '❌ 失败'}")
    print(f"4. 扇形分配正确: {'✅ 通过' if test_results['correct_sector_assignment'] else '❌ 失败'}")
    
    if test_results['errors']:
        print("\n错误:")
        for error in test_results['errors']:
            print(f"  - {error}")
    
    # 计算通过率
    passed = sum([
        test_results['default_micro_view'],
        test_results['no_multiple_zoom'],
        test_results['correct_detection_order'],
        test_results['correct_sector_assignment']
    ])
    total = 4
    pass_rate = (passed / total) * 100
    
    print(f"\n总体通过率: {pass_rate:.0f}% ({passed}/{total})")
    
    return test_results


if __name__ == "__main__":
    test_ui_fixes()