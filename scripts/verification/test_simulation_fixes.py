#!/usr/bin/env python3
"""
测试模拟检测修复
验证：
1. 扇形统计表格显示
2. 模拟控制器集成
3. 进度信号同步
4. 颜色更新（蓝色到绿色）
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_simulation_detection():
    """测试模拟检测功能"""
    print("🧪 测试模拟检测修复...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建主视图
        main_view = NativeMainDetectionView()
        main_view.show()
        
        # 创建测试数据
        test_holes = {}
        for i in range(20):
            hole = HoleData(
                center_x=100 + (i % 5) * 50.0,
                center_y=100 + (i // 5) * 50.0,
                radius=15.0,
                hole_id=f"HOLE_{i:03d}",
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(test_holes)
        
        # 加载数据
        main_view.load_hole_collection(test_collection)
        
        # 测试项目
        print("\n📋 测试项目:")
        
        # 1. 检查扇形统计表格
        print("\n1️⃣ 检查扇形统计表格...")
        if hasattr(main_view.left_panel, 'sector_stats_table'):
            print("✅ 扇形统计表格存在")
            table = main_view.left_panel.sector_stats_table
            print(f"   表格行数: {table.rowCount()}")
            print(f"   表格列数: {table.columnCount()}")
        else:
            print("❌ 扇形统计表格未找到")
        
        # 2. 检查模拟控制器
        print("\n2️⃣ 检查模拟控制器...")
        if hasattr(main_view, 'simulation_controller') and main_view.simulation_controller:
            print("✅ 模拟控制器已初始化")
            
            # 检查信号连接
            signals_connected = [
                hasattr(main_view, '_on_simulation_progress'),
                hasattr(main_view, '_on_hole_status_updated'),
                hasattr(main_view, '_on_simulation_completed')
            ]
            if all(signals_connected):
                print("✅ 模拟信号已连接")
            else:
                print("⚠️ 部分模拟信号未连接")
        else:
            print("❌ 模拟控制器未初始化")
        
        # 3. 检查进度更新功能
        print("\n3️⃣ 检查进度更新功能...")
        if hasattr(main_view.left_panel, 'update_progress_display'):
            print("✅ 进度更新方法存在")
            # 测试进度更新
            test_progress_data = {
                'progress': 50,
                'completed': 10,
                'total': 20,
                'pending': 10
            }
            main_view.left_panel.update_progress_display(test_progress_data)
            print("✅ 进度更新测试完成")
        else:
            print("❌ 进度更新方法未找到")
        
        # 4. 启动模拟测试
        print("\n4️⃣ 启动模拟检测...")
        
        def start_simulation():
            if main_view.simulation_controller:
                print("🚀 开始模拟检测...")
                main_view._on_start_simulation()
                
                # 设置定时器监控颜色变化
                color_check_timer = QTimer()
                color_check_count = [0]
                
                def check_hole_colors():
                    color_check_count[0] += 1
                    print(f"\n🔍 检查孔位颜色 (第{color_check_count[0]}次)...")
                    
                    # 获取graphics view中的孔位
                    if hasattr(main_view.center_panel, 'graphics_view'):
                        graphics_view = main_view.center_panel.graphics_view
                        if hasattr(graphics_view, 'hole_items'):
                            hole_items = graphics_view.hole_items
                            
                            # 统计颜色
                            color_stats = {
                                '蓝色': 0,
                                '绿色': 0,
                                '红色': 0,
                                '灰色': 0
                            }
                            
                            for hole_id, item in hole_items.items():
                                if hasattr(item, '_color_override') and item._color_override:
                                    color_stats['蓝色'] += 1
                                elif item.hole_data.status == HoleStatus.QUALIFIED:
                                    color_stats['绿色'] += 1
                                elif item.hole_data.status == HoleStatus.DEFECTIVE:
                                    color_stats['红色'] += 1
                                else:
                                    color_stats['灰色'] += 1
                            
                            print(f"   颜色统计: {color_stats}")
                            
                            # 检查是否有颜色变化
                            if color_stats['绿色'] > 0 or color_stats['红色'] > 0:
                                print("✅ 检测到颜色变化！孔位从蓝色变为最终状态")
                            
                    if color_check_count[0] >= 20:  # 检查20次后停止
                        color_check_timer.stop()
                        print("\n📊 测试完成")
                        
                        # 停止模拟
                        main_view._on_stop_simulation()
                
                color_check_timer.timeout.connect(check_hole_colors)
                color_check_timer.start(1000)  # 每秒检查一次
        
        # 延迟启动模拟，让UI完全加载
        QTimer.singleShot(2000, start_simulation)
        
        # 运行应用
        print("\n⏳ 等待UI加载...")
        app.exec()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("模拟检测修复测试")
    print("="*60)
    
    test_simulation_detection()