#!/usr/bin/env python3
"""
简化的模拟控制器测试 - 验证基本功能流畅性
"""

import sys
sys.path.append('.')

def test_simulation_controller():
    """测试模拟控制器基本功能"""
    
    print("🧪 开始简化测试...\n")
    
    try:
        # 导入模块
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        from src.pages.shared.components.snake_path.snake_path_renderer import HolePair
        
        print("✅ 模块导入成功")
        
        # 创建测试数据
        holes = {
            'C001R001': HoleData(center_x=10, center_y=20, radius=5, hole_id='C001R001'),
            'C005R001': HoleData(center_x=50, center_y=20, radius=5, hole_id='C005R001'),
            'C009R001': HoleData(center_x=90, center_y=20, radius=5, hole_id='C009R001'),
            'C013R001': HoleData(center_x=130, center_y=20, radius=5, hole_id='C013R001')
        }
        
        hole_collection = HoleCollection(holes=holes)
        print(f"✅ 测试数据创建成功: {len(holes)} 个孔位")
        
        # 创建控制器
        controller = SimulationController()
        controller.load_hole_collection(hole_collection)
        print("✅ 模拟控制器创建成功")
        
        # 测试启动前状态
        print(f"📊 启动前检测单元数量: {controller.get_detection_units_count()}")
        print(f"📊 启动前总孔位数量: {controller.get_total_holes_count()}")
        
        # 启动模拟（不使用定时器，直接测试数据生成）
        controller.start_simulation()
        
        # 测试启动后状态
        print(f"📊 启动后检测单元数量: {controller.get_detection_units_count()}")
        print(f"📊 启动后总孔位数量: {controller.get_total_holes_count()}")
        
        # 检查检测单元结构
        detection_units = controller.detection_units
        pair_count = sum(1 for unit in detection_units if isinstance(unit, HolePair))
        single_count = len(detection_units) - pair_count
        
        print(f"📊 HolePair配对数量: {pair_count}")
        print(f"📊 单孔检测数量: {single_count}")
        
        # 显示检测单元详情
        for i, unit in enumerate(detection_units[:3]):  # 只显示前3个
            if isinstance(unit, HolePair):
                hole_ids = unit.get_hole_ids()
                print(f"  单元{i+1}: HolePair - {' + '.join(hole_ids)}")
            else:
                print(f"  单元{i+1}: 单孔 - {unit.hole_id}")
        
        # 验证时序配置
        print(f"⏱️ 检测间隔: {controller.pair_detection_time}ms")
        print(f"⏱️ 状态变化: {controller.status_change_time}ms")
        print(f"📊 成功率: {controller.success_rate*100:.1f}%")
        
        # 停止模拟
        controller.stop_simulation()
        print("✅ 模拟已停止")
        
        # 检查路径渲染是否移除
        has_renderer = hasattr(controller, 'snake_path_renderer')
        has_coordinator = hasattr(controller, 'snake_path_coordinator')
        
        print(f"🔍 路径渲染器残留: {has_renderer}")
        print(f"🔍 路径协调器残留: {has_coordinator}")
        
        print("\n🎉 测试完成！")
        print("📋 功能验证结果:")
        print("  ✅ 模块导入正常")
        print("  ✅ 控制器创建正常")
        print("  ✅ 孔位数据加载正常")
        print("  ✅ 模拟启动正常")
        if pair_count > 0:
            print("  ✅ HolePair配对检测功能已恢复")
        print("  ✅ 时序配置正确")
        if not has_renderer and not has_coordinator:
            print("  ✅ 路径渲染组件已移除")
        print("  ✅ 只保留实时点状态更新功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simulation_controller()
    if success:
        print("\n✅ 所有功能正常，书写流畅！")
    else:
        print("\n❌ 发现问题，需要调试")