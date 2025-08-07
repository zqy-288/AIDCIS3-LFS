#!/usr/bin/env python3
"""
验证修复是否正常工作 - 简化版本
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_fixes():
    """验证所有修复是否正常工作"""
    print("🔍 验证修复功能...\n")
    
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    
    # 导入必要的类
    from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
    from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
    
    results = []
    
    try:
        # 1. 创建主视图
        print("1️⃣ 创建主视图...")
        main_view = NativeMainDetectionView()
        results.append("✅ 主视图创建成功")
        
        # 2. 检查扇形统计表格
        print("2️⃣ 检查扇形统计表格...")
        if hasattr(main_view.left_panel, 'sector_stats_table'):
            table = main_view.left_panel.sector_stats_table
            results.append(f"✅ 扇形统计表格存在 ({table.rowCount()}行 x {table.columnCount()}列)")
            
            # 测试更新
            test_stats = {'total': 100, 'qualified': 60, 'defective': 20, 'pending': 20}
            main_view.left_panel.update_sector_stats(test_stats)
            
            # 检查数值格式
            total_text = table.item(5, 1).text()
            if total_text == "100":  # 应该是纯数字，不是"100 个孔位"
                results.append("✅ 表格数值格式正确（纯数字）")
            else:
                results.append(f"❌ 表格数值格式错误: '{total_text}'")
        else:
            results.append("❌ 扇形统计表格不存在")
        
        # 3. 检查模拟控制器
        print("3️⃣ 检查模拟控制器...")
        if hasattr(main_view, 'simulation_controller') and main_view.simulation_controller:
            results.append("✅ 模拟控制器已初始化")
            
            # 检查信号处理方法
            methods = ['_on_start_simulation', '_on_pause_simulation', '_on_stop_simulation']
            missing = [m for m in methods if not hasattr(main_view, m)]
            if not missing:
                results.append("✅ 模拟控制方法都存在")
            else:
                results.append(f"❌ 缺少方法: {missing}")
        else:
            results.append("❌ 模拟控制器未初始化")
        
        # 4. 检查进度更新功能
        print("4️⃣ 检查进度更新...")
        if hasattr(main_view.left_panel, 'update_progress_display'):
            test_progress = {'progress': 75, 'completed': 15, 'total': 20}
            main_view.left_panel.update_progress_display(test_progress)
            results.append("✅ 进度更新功能正常")
        else:
            results.append("❌ 进度更新方法不存在")
        
        # 5. 测试颜色更新参数
        print("5️⃣ 检查颜色更新支持...")
        if main_view.simulation_controller:
            # 检查方法签名
            import inspect
            sig = inspect.signature(main_view.simulation_controller._update_hole_status)
            if 'color_override' in sig.parameters:
                results.append("✅ 颜色覆盖参数支持正确")
            else:
                results.append("❌ 缺少color_override参数")
        
    except Exception as e:
        results.append(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 打印结果
    print("\n📊 验证结果:")
    print("="*50)
    success_count = 0
    for result in results:
        print(result)
        if result.startswith("✅"):
            success_count += 1
    
    total = len(results)
    print(f"\n总计: {success_count}/{total} 项通过")
    
    if success_count == total:
        print("\n🎉 所有功能验证通过！修复完全成功！")
        return True
    else:
        print(f"\n⚠️ 有 {total - success_count} 项未通过")
        return False


if __name__ == "__main__":
    print("="*60)
    print("模拟检测修复验证")
    print("="*60)
    
    # 直接运行验证，不启动GUI循环
    success = verify_fixes()
    sys.exit(0 if success else 1)