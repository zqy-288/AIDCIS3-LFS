#!/usr/bin/env python3
"""
基本功能测试脚本
测试主要的修复是否正常工作
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView


def test_basic_functionality():
    """基本功能测试"""
    print("🧪 开始基本功能测试...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        # 创建主视图
        main_view = NativeMainDetectionView()
        
        # 测试1: 扇形统计表格
        print("\n1️⃣ 检查扇形统计表格...")
        if hasattr(main_view.left_panel, 'sector_stats_table'):
            table = main_view.left_panel.sector_stats_table
            print(f"✅ 扇形统计表格存在 ({table.rowCount()}行 x {table.columnCount()}列)")
            
            # 测试更新功能
            test_stats = {'total': 100, 'qualified': 60, 'defective': 20, 'pending': 20}
            main_view.left_panel.update_sector_stats(test_stats)
            
            # 检查值是否正确（不带"个孔位"）
            total_value = table.item(5, 1).text()
            if total_value == "100":
                print("✅ 表格数值格式正确（纯数字）")
            else:
                print(f"❌ 表格数值格式错误: '{total_value}'")
        else:
            print("❌ 扇形统计表格未找到")
        
        # 测试2: 模拟控制器
        print("\n2️⃣ 检查模拟控制器...")
        if hasattr(main_view, 'simulation_controller') and main_view.simulation_controller:
            print("✅ 模拟控制器已初始化")
            
            # 检查关键方法
            methods = ['_on_start_simulation', '_on_pause_simulation', '_on_stop_simulation',
                      '_on_simulation_progress', '_on_hole_status_updated']
            missing = [m for m in methods if not hasattr(main_view, m)]
            
            if not missing:
                print("✅ 所有模拟处理方法都存在")
            else:
                print(f"❌ 缺少方法: {missing}")
        else:
            print("❌ 模拟控制器未初始化")
        
        # 测试3: 进度更新
        print("\n3️⃣ 检查进度更新...")
        if hasattr(main_view.left_panel, 'update_progress_display'):
            print("✅ 进度更新方法存在")
            
            # 测试调用
            test_data = {'progress': 50, 'completed': 10, 'total': 20}
            try:
                main_view.left_panel.update_progress_display(test_data)
                print("✅ 进度更新调用成功")
            except Exception as e:
                print(f"❌ 进度更新失败: {e}")
        
        # 测试4: 颜色更新机制
        print("\n4️⃣ 检查颜色更新支持...")
        if main_view.simulation_controller:
            # 检查_update_hole_status方法签名
            import inspect
            sig = inspect.signature(main_view.simulation_controller._update_hole_status)
            params = list(sig.parameters.keys())
            
            if 'color_override' in params:
                print("✅ 颜色覆盖参数支持正确")
            else:
                print("❌ 缺少color_override参数")
        
        print("\n✅ 基本功能测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("模拟检测修复 - 基本功能测试")
    print("="*60)
    
    test_basic_functionality()
    print("\n测试结束")