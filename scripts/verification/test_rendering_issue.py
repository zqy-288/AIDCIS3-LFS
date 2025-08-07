#!/usr/bin/env python3
"""
测试渲染问题的简单脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append('.')

# 设置环境变量避免Qt相关警告
os.environ['QT_QPA_PLATFORM'] = 'minimal'

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_simulation_controller():
    """测试模拟控制器"""
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建测试数据
        holes = {}
        for i in range(10):
            hole_id = f"TEST{i:03d}"
            holes[hole_id] = HoleData(
                center_x=i * 10, 
                center_y=i * 5, 
                radius=2.5, 
                hole_id=hole_id
            )
        
        hole_collection = HoleCollection(holes=holes)
        logger.info(f"✅ 创建测试数据: {len(holes)} 个孔位")
        
        # 创建模拟控制器
        controller = SimulationController()
        logger.info("✅ 创建模拟控制器成功")
        
        # 监听状态更新
        updates = []
        def on_status_update(hole_id, status):
            updates.append((hole_id, status))
            logger.info(f"📝 状态更新: {hole_id} -> {status}")
        
        controller.hole_status_updated.connect(on_status_update)
        
        # 加载数据
        controller.load_hole_collection(hole_collection)
        logger.info("✅ 加载孔位数据成功")
        
        # 启动模拟 (这会创建检测单元)
        logger.info("🚀 启动模拟...")
        controller.start_simulation()
        
        # 检查检测单元 (在启动后)
        detection_units = controller.get_detection_units_count()
        total_holes = controller.get_total_holes_count()
        logger.info(f"📊 检测单元: {detection_units}, 总孔位: {total_holes}")
        
        # 等待一些更新
        import time
        time.sleep(2)
        
        # 手动触发一个状态更新测试
        controller._update_hole_status("TEST001", HoleStatus.QUALIFIED)
        
        logger.info(f"📈 收到 {len(updates)} 个状态更新")
        
        # 停止模拟
        controller.stop_simulation()
        logger.info("⏹️ 模拟已停止")
        
        return len(updates) > 0
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graphics_view():
    """测试图形视图"""
    try:
        from src.core_business.graphics.graphics_view import OptimizedGraphicsView
        from src.core_business.models.hole_data import HoleCollection, HoleData
        
        # 创建测试数据
        holes = {}
        for i in range(5):
            hole_id = f"VIEW{i:03d}"
            holes[hole_id] = HoleData(
                center_x=i * 20, 
                center_y=i * 10, 
                radius=3.0, 
                hole_id=hole_id
            )
        
        hole_collection = HoleCollection(holes=holes)
        logger.info(f"✅ 创建视图测试数据: {len(holes)} 个孔位")
        
        # 创建图形视图
        graphics_view = OptimizedGraphicsView()
        logger.info("✅ 创建图形视图成功")
        
        # 加载孔位
        graphics_view.load_holes(hole_collection)
        logger.info("✅ 加载孔位到视图成功")
        
        # 检查场景项
        scene_items = len(graphics_view.scene.items())
        hole_items = len(graphics_view.hole_items)
        logger.info(f"📊 场景项: {scene_items}, 孔位项: {hole_items}")
        
        return scene_items > 0 and hole_items > 0
        
    except Exception as e:
        logger.error(f"❌ 视图测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("🔍 开始渲染问题诊断")
    
    # 测试1: 模拟控制器
    logger.info("\n=== 测试1: 模拟控制器 ===")
    sim_ok = test_simulation_controller()
    
    # 测试2: 图形视图
    logger.info("\n=== 测试2: 图形视图 ===")  
    view_ok = test_graphics_view()
    
    # 总结
    logger.info("\n=== 诊断结果 ===")
    logger.info(f"模拟控制器: {'✅ 正常' if sim_ok else '❌ 异常'}")
    logger.info(f"图形视图: {'✅ 正常' if view_ok else '❌ 异常'}")
    
    if sim_ok and view_ok:
        logger.info("🎉 基础组件功能正常，问题可能在连接或数据传递")
    elif not sim_ok:
        logger.info("⚠️ 模拟控制器有问题")
    elif not view_ok:
        logger.info("⚠️ 图形视图有问题")
    else:
        logger.info("❌ 多个组件有问题")

if __name__ == "__main__":
    main()