#!/usr/bin/env python3
"""
简单的孔位显示测试 - 绕过蛇形路径问题
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append('.')

# 设置环境变量避免Qt相关警告
os.environ['QT_QPA_PLATFORM'] = 'minimal'

# 禁用matplotlib避免字体缓存问题
import matplotlib
matplotlib.use('Agg')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    """测试孔位数据是否正确传递到视图"""
    try:
        # 简单测试：检查模拟控制器是否能正确更新孔位状态（不启动定时器）
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建简单测试数据
        holes = {
            "TEST001": HoleData(center_x=10, center_y=20, radius=2.5, hole_id="TEST001"),
            "TEST002": HoleData(center_x=30, center_y=40, radius=2.5, hole_id="TEST002"),
        }
        hole_collection = HoleCollection(holes=holes)
        logger.info(f"✅ 创建测试数据: {len(holes)} 个孔位")
        
        # 创建模拟控制器但不启动定时器
        controller = SimulationController()
        logger.info("✅ 创建模拟控制器")
        
        # 测试状态更新信号
        updates = []
        def on_update(hole_id, status):
            updates.append((hole_id, status))
            logger.info(f"📝 收到状态更新: {hole_id} -> {status}")
        
        controller.hole_status_updated.connect(on_update)
        
        # 加载数据
        controller.load_hole_collection(hole_collection)
        logger.info("✅ 加载数据完成")
        
        # 手动触发状态更新测试（不需要启动定时器）
        logger.info("🧪 测试状态更新...")
        controller._update_hole_status("TEST001", HoleStatus.QUALIFIED)
        controller._update_hole_status("TEST002", HoleStatus.DEFECTIVE)
        
        logger.info(f"📊 收到 {len(updates)} 个状态更新")
        
        # 测试图形视图
        logger.info("\n=== 测试图形视图 ===")
        from src.core_business.graphics.graphics_view import OptimizedGraphicsView
        
        view = OptimizedGraphicsView()
        logger.info("✅ 创建图形视图")
        
        view.load_holes(hole_collection)
        logger.info("✅ 加载孔位到视图")
        
        # 检查场景项
        scene_items = len(view.scene.items())
        hole_items = len(view.hole_items)
        logger.info(f"📊 场景项: {scene_items}, 孔位项字典: {hole_items}")
        
        # 测试状态更新是否影响视图
        if hole_items > 0:
            logger.info("🎨 测试视图状态更新...")
            if hasattr(view, 'update_hole_status'):
                view.update_hole_status("TEST001", HoleStatus.QUALIFIED)
                logger.info("✅ 视图状态更新成功")
            else:
                logger.info("⚠️ 视图没有update_hole_status方法")
        
        return len(updates) > 0 and scene_items > 0
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🔍 简单孔位显示测试")
    success = main()
    logger.info(f"\n=== 测试结果 ===")
    logger.info(f"{'✅ 成功' if success else '❌ 失败'}")