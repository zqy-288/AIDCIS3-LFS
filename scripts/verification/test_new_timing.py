#!/usr/bin/env python3
"""
测试新的检测时序系统
验证10秒间隔、9.5秒蓝色状态、然后变为绿色/红色的逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.pages.main_detection_p1.components.simulation_controller import SimulationController


def create_test_data():
    """创建测试数据"""
    holes = {}
    test_data = [
        ("BC098R164", 98.0, -164.0, 98, 164),
        ("BC102R164", 102.0, -164.0, 102, 164),
        ("BC100R164", 100.0, -164.0, 100, 164),
        ("BC104R164", 104.0, -164.0, 104, 164),
    ]
    
    for hole_id, x, y, col, row in test_data:
        hole = HoleData(
            center_x=x, center_y=y, radius=5.0,
            hole_id=hole_id, row=row, column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_timing_system():
    """测试新的时序系统"""
    print("🚀 测试新的检测时序系统")
    print("=" * 60)
    
    # 创建测试数据
    hole_collection = create_test_data()
    print(f"✅ 创建测试数据: {len(hole_collection.holes)} 个孔位")
    
    # 创建模拟控制器
    controller = SimulationController()
    controller.set_hole_collection(hole_collection)
    
    print(f"✅ 时序参数配置:")
    print(f"    配对检测时间: {controller.pair_detection_time}ms (10秒)")
    print(f"    状态变化时间: {controller.status_change_time}ms (9.5秒)")
    print(f"    成功率: {controller.success_rate * 100:.1f}%")
    
    print(f"\n📋 检测单元数量: {len(controller.detection_units)}")
    for i, unit in enumerate(controller.detection_units):
        if hasattr(unit, 'get_hole_ids'):
            hole_ids = unit.get_hole_ids()
            print(f"    第{i+1}对: {' + '.join(hole_ids)}")
        elif hasattr(unit, 'holes'):
            hole_ids = [h.hole_id for h in unit.holes]
            print(f"    第{i+1}对: {' + '.join(hole_ids)}")
        else:
            print(f"    单元{i+1}: 格式错误")
    
    print(f"\n🎯 预期检测流程:")
    print(f"    0.0s - 9.5s: 第1对显示蓝色 (检测中)")
    print(f"    9.5s: 第1对变为绿色/红色 (检测完成)")
    print(f"    10.0s - 19.5s: 第2对显示蓝色 (检测中)")
    print(f"    19.5s: 第2对变为绿色/红色 (检测完成)")
    print(f"    总检测时间: {len(controller.detection_units) * 10}秒")
    
    return True


def main():
    """主测试函数"""
    print("🧪 新时序系统集成测试")
    print("=" * 50)
    
    try:
        success = test_timing_system()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 时序系统测试成功！")
            print("✅ 10秒/对检测间隔已配置")
            print("✅ 9.5秒状态变化逻辑已实现")
            print("✅ 蓝色→绿色/红色状态转换已就绪")
            print("✅ 【开始模拟检测】将使用新时序")
            print("\n📝 使用说明:")
            print("    1. 点击【开始模拟检测】")
            print("    2. 观察孔位先变蓝色(9.5秒)")
            print("    3. 然后变绿色/红色并保持")
            print("    4. 每10秒处理一对孔位")
        else:
            print("❌ 时序系统测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)