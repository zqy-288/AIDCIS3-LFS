#!/usr/bin/env python3
"""
调试模拟检测问题
检查定时器设置和数据覆盖问题
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

def check_timer_settings():
    """检查定时器设置"""
    logger.info("=== 检查定时器设置 ===")
    
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        
        controller = SimulationController()
        
        # 检查定时器间隔设置
        main_interval = controller.simulation_timer.interval()
        status_change_time = controller.status_change_time
        
        logger.info(f"主定时器间隔: {main_interval}ms")
        logger.info(f"状态变化时间: {status_change_time}ms")
        
        # 用户需求：蓝色9.5秒，然后0.5秒后变最终状态
        # 意味着：主定时器应该是10秒间隔，状态变化应该是9.5秒
        expected_main_interval = 10000  # 10秒
        expected_status_change = 9500   # 9.5秒
        
        logger.info(f"期望主定时器间隔: {expected_main_interval}ms")
        logger.info(f"期望状态变化时间: {expected_status_change}ms")
        
        timing_correct = (main_interval == expected_main_interval and 
                         status_change_time == expected_status_change)
        
        if timing_correct:
            logger.info("✅ 定时器设置正确")
        else:
            logger.warning("❌ 定时器设置不正确，需要修复")
            
        return timing_correct
        
    except Exception as e:
        logger.error(f"❌ 检查定时器设置失败: {e}")
        return False

def check_hole_data_coverage():
    """检查孔位数据覆盖"""
    logger.info("\n=== 检查孔位数据覆盖 ===")
    
    try:
        # 检查CAP1000数据是否包含25270个孔位
        from src.models.product_model import get_product_manager
        
        product_manager = get_product_manager()
        products = product_manager.get_all_products()
        
        cap1000_found = False
        for product in products:
            if "CAP1000" in product.get("name", ""):
                cap1000_found = True
                logger.info(f"找到CAP1000产品: {product.get('name')}")
                
                # 尝试加载数据
                try:
                    hole_collection = product_manager.load_product_holes(product["name"])
                    if hole_collection:
                        hole_count = len(hole_collection.holes)
                        logger.info(f"CAP1000孔位数量: {hole_count}")
                        
                        if hole_count == 25270:
                            logger.info("✅ 孔位数量正确")
                            return True
                        else:
                            logger.warning(f"❌ 孔位数量不正确，期望25270，实际{hole_count}")
                            return False
                    else:
                        logger.error("❌ 无法加载CAP1000孔位数据")
                        return False
                except Exception as e:
                    logger.error(f"❌ 加载CAP1000数据失败: {e}")
                    return False
        
        if not cap1000_found:
            logger.error("❌ 未找到CAP1000产品")
            return False
            
    except Exception as e:
        logger.error(f"❌ 检查孔位数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_snake_path_generation():
    """检查蛇形路径生成"""
    logger.info("\n=== 检查蛇形路径生成 ===")
    
    try:
        from src.pages.main_detection_p1.components.simulation_controller import SimulationController
        from src.core_business.models.hole_data import HoleCollection, HoleData
        
        # 创建测试数据
        holes = {}
        for i in range(100):  # 测试100个孔位
            hole_id = f"TEST{i:03d}"
            holes[hole_id] = HoleData(
                center_x=i * 10,
                center_y=(i // 10) * 10,
                radius=2.5,
                hole_id=hole_id
            )
        
        hole_collection = HoleCollection(holes=holes)
        logger.info(f"创建测试数据: {len(holes)} 个孔位")
        
        # 测试蛇形路径生成
        controller = SimulationController()
        controller.load_hole_collection(hole_collection)
        
        # 模拟start_simulation的路径生成部分
        from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer
        from src.pages.shared.components.snake_path import PathStrategy
        from PySide6.QtWidgets import QGraphicsScene
        
        snake_path_renderer = SnakePathRenderer()
        scene = QGraphicsScene()
        snake_path_renderer.set_graphics_scene(scene)
        snake_path_renderer.set_hole_collection(hole_collection)
        
        try:
            detection_units = snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            if detection_units:
                logger.info(f"✅ 蛇形路径生成成功: {len(detection_units)} 个检测单元")
                
                # 计算总孔位数
                total_holes = 0
                for unit in detection_units:
                    if hasattr(unit, 'holes'):
                        total_holes += len(unit.holes)
                    else:
                        total_holes += 1
                        
                logger.info(f"蛇形路径覆盖孔位数: {total_holes}")
                
                if total_holes == len(holes):
                    logger.info("✅ 蛇形路径覆盖完整")
                    return True
                else:
                    logger.warning(f"❌ 蛇形路径覆盖不完整: {total_holes}/{len(holes)}")
                    return False
            else:
                logger.error("❌ 蛇形路径生成失败：返回空列表")
                return False
                
        except Exception as e:
            logger.error(f"❌ 蛇形路径生成异常: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 蛇形路径生成检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("🔍 开始调试模拟检测问题\n")
    
    results = {
        "定时器设置": check_timer_settings(),
        "孔位数据覆盖": check_hole_data_coverage(),
        "蛇形路径生成": check_snake_path_generation()
    }
    
    logger.info("\n=== 调试结果总结 ===")
    for name, result in results.items():
        status = "✅ 正常" if result else "❌ 异常"
        logger.info(f"{name}: {status}")
    
    # 分析可能的问题
    logger.info("\n=== 问题分析 ===")
    if not results["定时器设置"]:
        logger.info("🔧 需要修复定时器设置：")
        logger.info("   - 主定时器改为10000ms（10秒）")
        logger.info("   - 状态变化定时器改为9500ms（9.5秒）")
    
    if not results["孔位数据覆盖"]:
        logger.info("🔧 需要检查数据加载：")
        logger.info("   - 确认CAP1000数据文件完整性")
        logger.info("   - 检查产品加载逻辑")
    
    if not results["蛇形路径生成"]:
        logger.info("🔧 需要修复算法问题：")
        logger.info("   - 检查蛇形路径生成算法")
        logger.info("   - 验证后备方案逻辑")
    
    success_count = sum(results.values())
    logger.info(f"\n总体状态: {success_count}/{len(results)} 项正常")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)