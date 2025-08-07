#!/usr/bin/env python3
"""
定时器和遍历修复的综合集成测试
验证所有修复是否正确工作
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_timer_settings():
    """测试定时器设置修复"""
    logger.info("🕐 测试1: 定时器设置")
    
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        
        controller = SimulationController()
        
        # 验证定时器设置
        assert controller.pair_detection_time == 10000, f"主定时器应为10000ms，实际为{controller.pair_detection_time}ms"
        assert controller.status_change_time == 9500, f"状态变化定时器应为9500ms，实际为{controller.status_change_time}ms"
        
        logger.info("   ✅ 定时器设置正确")
        logger.info(f"      主定时器: {controller.pair_detection_time}ms")
        logger.info(f"      状态变化: {controller.status_change_time}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 定时器测试失败: {e}")
        return False

def test_hole_pair_only_mode():
    """测试只支持HolePair模式（无后备方案）"""
    logger.info("🔗 测试2: HolePair专用模式")
    
    try:
        from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        
        # 创建测试数据
        holes = {}
        test_data = [
            ("C098R164", 98.0, -164.0, 98, 164),
            ("C102R164", 102.0, -164.0, 102, 164),  # 间隔4列配对
            ("C100R164", 100.0, -164.0, 100, 164),
            ("C104R164", 104.0, -164.0, 104, 164),  # 间隔4列配对
        ]
        
        for hole_id, x, y, col, row in test_data:
            hole = HoleData(
                center_x=x, center_y=y, radius=5.0,
                hole_id=hole_id, row=row, column=col,
                status=HoleStatus.PENDING
            )
            holes[hole_id] = hole
        
        hole_collection = HoleCollection(holes=holes)
        
        controller = SimulationController()
        controller.set_hole_collection(hole_collection)
        
        # 验证所有检测单元都是HolePair对象
        if controller.detection_units:
            for i, unit in enumerate(controller.detection_units):
                assert hasattr(unit, 'holes'), f"检测单元{i+1}不是HolePair对象"
                assert len(unit.holes) >= 1, f"检测单元{i+1}的孔位数量不足"
            
            logger.info("   ✅ 所有检测单元都是HolePair对象")
            logger.info(f"      检测单元数量: {len(controller.detection_units)}")
            
            # 验证孔位提取逻辑
            total_holes = sum(len(unit.holes) for unit in controller.detection_units)
            logger.info(f"      总孔位数: {total_holes}/{len(hole_collection.holes)}")
            
            assert total_holes == len(hole_collection.holes), "孔位数量不匹配"
            logger.info("   ✅ 孔位遍历完整性正确")
            
        else:
            logger.warning("   ⚠️ 无检测单元生成，可能需要更多测试数据")
            
        return True
        
    except Exception as e:
        logger.error(f"   ❌ HolePair测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_color_override_support():
    """测试颜色覆盖支持"""
    logger.info("🎨 测试3: 蓝色状态颜色覆盖")
    
    try:
        from src.core_business.graphics.graphics_view import OptimizedGraphicsView
        from src.core_business.models.hole_data import HoleStatus
        from PySide6.QtGui import QColor
        
        # 创建模拟图形视图
        graphics_view = OptimizedGraphicsView()
        
        # 验证方法签名支持颜色覆盖
        import inspect
        sig = inspect.signature(graphics_view.update_hole_status)
        params = list(sig.parameters.keys())
        
        assert 'color_override' in params, "update_hole_status方法缺少color_override参数"
        assert hasattr(graphics_view, 'set_hole_color_override'), "缺少set_hole_color_override方法"
        
        logger.info("   ✅ 图形视图支持颜色覆盖")
        logger.info(f"      update_hole_status参数: {params}")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 颜色覆盖测试失败: {e}")
        return False

def test_no_fallback_mode():
    """测试确认没有后备模式"""
    logger.info("🚫 测试4: 确认无后备模式")
    
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        import inspect
        
        # 检查源码中是否还有后备模式相关代码
        source = inspect.getsource(SimulationController.start_simulation)
        
        # 检查关键词
        fallback_keywords = [
            "后备方案", "fallback", "hole_list", 
            "单孔检测单元", "_start_single_hole_detection"
        ]
        
        found_fallback = []
        for keyword in fallback_keywords:
            if keyword in source:
                found_fallback.append(keyword)
        
        if found_fallback:
            logger.warning(f"   ⚠️ 可能仍有后备模式代码: {found_fallback}")
        else:
            logger.info("   ✅ 确认已删除后备模式")
            
        # 验证不存在单孔检测方法
        assert not hasattr(SimulationController, '_start_single_hole_detection'), \
               "仍存在_start_single_hole_detection方法"
               
        logger.info("   ✅ 单孔检测方法已删除")
        
        return len(found_fallback) == 0
        
    except Exception as e:
        logger.error(f"   ❌ 后备模式检查失败: {e}")
        return False

def test_simplified_logic():
    """测试简化后的逻辑"""
    logger.info("⚡ 测试5: 简化后的类型检查逻辑")
    
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        import inspect
        
        # 检查关键方法的源码
        methods_to_check = [
            'start_simulation',
            '_process_next_pair', 
            '_finalize_current_pair_status',
            '_focus_on_sector'
        ]
        
        complex_checks = 0
        for method_name in methods_to_check:
            if hasattr(SimulationController, method_name):
                method = getattr(SimulationController, method_name)
                source = inspect.getsource(method)
                
                # 计算复杂的类型检查
                if 'isinstance' in source or 'hasattr' in source:
                    complex_checks += source.count('isinstance') + source.count('hasattr')
        
        logger.info(f"   类型检查数量: {complex_checks}")
        
        # 应该只有少量必要的类型检查
        assert complex_checks <= 5, f"类型检查过多: {complex_checks}"
        
        logger.info("   ✅ 类型检查逻辑已简化")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 逻辑简化测试失败: {e}")
        return False

def run_integration_tests():
    """运行所有集成测试"""
    logger.info("🧪 开始定时器和遍历修复集成测试")
    logger.info("=" * 60)
    
    tests = [
        ("定时器设置", test_timer_settings),
        ("HolePair专用模式", test_hole_pair_only_mode),
        ("颜色覆盖支持", test_color_override_support),
        ("无后备模式", test_no_fallback_mode),
        ("简化逻辑", test_simplified_logic),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("=" * 60)
    logger.info("📊 测试结果汇总:")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🏆 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有修复验证通过！")
        return True
    else:
        logger.warning(f"⚠️ 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)