#!/usr/bin/env python3
"""
简化的模拟进度测试 - 验证PathSegmentType.NORMAL错误修复
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

def test_enum_values():
    """测试PathSegmentType枚举值"""
    try:
        from src.core_business.graphics.snake_path_renderer import PathSegmentType
        from src.pages.shared.components.snake_path.snake_path_renderer import PathSegmentType as SharedPathSegmentType
        
        logger.info("✅ 测试PathSegmentType枚举值:")
        
        # 测试核心业务模块
        logger.info(f"  核心模块 - A_SIDE_NORMAL: {PathSegmentType.A_SIDE_NORMAL}")
        logger.info(f"  核心模块 - B_SIDE_NORMAL: {PathSegmentType.B_SIDE_NORMAL}")
        logger.info(f"  核心模块 - COMPLETED: {PathSegmentType.COMPLETED}")
        logger.info(f"  核心模块 - CURRENT: {PathSegmentType.CURRENT}")
        
        # 测试共享模块
        logger.info(f"  共享模块 - A_SIDE_NORMAL: {SharedPathSegmentType.A_SIDE_NORMAL}")
        logger.info(f"  共享模块 - B_SIDE_NORMAL: {SharedPathSegmentType.B_SIDE_NORMAL}")
        logger.info(f"  共享模块 - COMPLETED: {SharedPathSegmentType.COMPLETED}")
        logger.info(f"  共享模块 - CURRENT: {SharedPathSegmentType.CURRENT}")
        
        # 验证NORMAL不存在
        try:
            normal = PathSegmentType.NORMAL
            logger.error(f"❌ PathSegmentType.NORMAL仍然存在: {normal}")
            return False
        except AttributeError:
            logger.info("✅ PathSegmentType.NORMAL已正确移除")
            
        try:
            shared_normal = SharedPathSegmentType.NORMAL
            logger.error(f"❌ SharedPathSegmentType.NORMAL仍然存在: {shared_normal}")
            return False
        except AttributeError:
            logger.info("✅ SharedPathSegmentType.NORMAL已正确移除")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 枚举测试失败: {e}")
        return False

def test_simulation_controller():
    """测试模拟控制器基本功能"""
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QObject
        
        # 创建测试应用
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        logger.info("🧪 测试模拟控制器...")
        
        # 创建模拟控制器
        controller = SimulationController()
        logger.info("✅ 模拟控制器创建成功")
        
        # 创建测试孔位数据
        test_holes = {}
        for i in range(1, 5):  # 创建4个测试孔位
            hole_id = f"BC{i:03d}R164"
            test_holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=100.0 * i,
                center_y=100.0,
                radius=5.0  # 使用radius而不是diameter
            )
        
        hole_collection = HoleCollection(holes=test_holes)
        controller.load_hole_collection(hole_collection)
        logger.info("✅ 测试孔位数据加载成功")
        
        # 测试路径生成
        controller.snake_path_renderer.set_hole_collection(hole_collection)
        from src.pages.shared.components.snake_path import PathStrategy
        detection_units = controller.snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        
        if detection_units:
            logger.info(f"✅ 路径生成成功: {len(detection_units)} 个检测单元")
        else:
            logger.warning("⚠️ 路径生成返回空列表")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 模拟控制器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始简化模拟测试")
    
    # 测试1: 枚举值
    logger.info("\n" + "="*50)
    logger.info("测试1: PathSegmentType枚举值")
    logger.info("="*50)
    enum_ok = test_enum_values()
    
    # 测试2: 模拟控制器
    logger.info("\n" + "="*50)
    logger.info("测试2: 模拟控制器基本功能")
    logger.info("="*50)
    controller_ok = test_simulation_controller()
    
    # 总结
    logger.info("\n" + "="*50)
    logger.info("测试总结")
    logger.info("="*50)
    logger.info(f"枚举值测试: {'✅ 通过' if enum_ok else '❌ 失败'}")
    logger.info(f"控制器测试: {'✅ 通过' if controller_ok else '❌ 失败'}")
    
    if enum_ok and controller_ok:
        logger.info("🎉 所有测试通过! PathSegmentType.NORMAL错误已修复")
        return 0
    else:
        logger.error("💥 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())