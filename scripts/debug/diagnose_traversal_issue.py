#!/usr/bin/env python3
"""
诊断检测遍历不完整的根本原因
分析数据流和算法逻辑
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/Users/vsiyo/Desktop/AIDCIS3-LFS')

from src.core.shared_data_manager import SharedDataManager
from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathStrategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def diagnose_traversal_completeness():
    """诊断遍历完整性问题"""
    
    logger.info("🔍 开始诊断检测遍历完整性问题...")
    
    # 1. 验证数据源完整性
    logger.info("📊 Step 1: 验证数据源完整性")
    diagnose_data_source()
    
    # 2. 验证蛇形路径算法
    logger.info("🐍 Step 2: 验证蛇形路径算法")
    diagnose_snake_path_algorithm()
    
    # 3. 验证检测单元生成
    logger.info("🔧 Step 3: 验证检测单元生成")
    diagnose_detection_units()
    
    logger.info("✅ 诊断完成")

def diagnose_data_source():
    """诊断数据源"""
    try:
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/workfiles/dongzhong.dxf"
        
        # 检查文件是否存在
        if not Path(dxf_path).exists():
            logger.error(f"❌ DXF文件不存在: {dxf_path}")
            return
            
        logger.info(f"✅ DXF文件存在: {dxf_path}")
        
        # 加载数据
        data_manager = SharedDataManager()
        data_manager.load_hole_data_from_dxf(dxf_path)
        
        # 获取孔位集合
        hole_collection = data_manager.get_current_hole_collection()
        if not hole_collection:
            logger.error("❌ 无法获取孔位集合")
            return
            
        logger.info(f"📈 孔位集合统计:")
        logger.info(f"   总孔位数: {len(hole_collection.holes)}")
        
        # 按扇形分析
        sector_stats = {}
        for hole_id, hole in hole_collection.holes.items():
            sector = getattr(hole, 'sector', 'unknown')
            if sector not in sector_stats:
                sector_stats[sector] = 0
            sector_stats[sector] += 1
            
        logger.info(f"   扇形分布:")
        for sector, count in sorted(sector_stats.items()):
            logger.info(f"     扇形 {sector}: {count} 个孔位")
            
        # 分析孔位坐标范围
        if hole_collection.holes:
            x_coords = [hole.center_x for hole in hole_collection.holes.values()]
            y_coords = [hole.center_y for hole in hole_collection.holes.values()]
            
            logger.info(f"   坐标范围:")
            logger.info(f"     X: {min(x_coords):.2f} ~ {max(x_coords):.2f}")
            logger.info(f"     Y: {min(y_coords):.2f} ~ {max(y_coords):.2f}")
            
        return hole_collection
        
    except Exception as e:
        logger.error(f"❌ 数据源诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def diagnose_snake_path_algorithm():
    """诊断蛇形路径算法"""
    try:
        # 获取数据
        hole_collection = diagnose_data_source()
        if not hole_collection:
            return
            
        logger.info("🐍 测试蛇形路径生成算法...")
        
        # 创建渲染器
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        # 测试不同策略
        strategies = [
            (PathStrategy.INTERVAL_FOUR_S_SHAPE, "INTERVAL_FOUR_S_SHAPE"),
            (PathStrategy.SEQUENTIAL_S_SHAPE, "SEQUENTIAL_S_SHAPE"),
            (PathStrategy.INTERVAL_TWO_S_SHAPE, "INTERVAL_TWO_S_SHAPE")
        ]
        
        for strategy, name in strategies:
            logger.info(f"   测试策略: {name}")
            try:
                detection_units = renderer.generate_snake_path(strategy)
                if detection_units:
                    # 统计配对和单孔
                    pair_count = sum(1 for unit in detection_units if hasattr(unit, 'holes') and len(unit.holes) > 1)
                    single_count = len(detection_units) - pair_count
                    
                    # 计算总孔位数
                    total_holes = 0
                    for unit in detection_units:
                        if hasattr(unit, 'holes'):
                            total_holes += len(unit.holes)
                        else:
                            total_holes += 1
                    
                    logger.info(f"     ✅ 成功生成 {len(detection_units)} 个检测单元")
                    logger.info(f"        配对: {pair_count} 个")
                    logger.info(f"        单孔: {single_count} 个")
                    logger.info(f"        总孔位: {total_holes} 个")
                    logger.info(f"        覆盖率: {total_holes/len(hole_collection.holes)*100:.2f}%")
                else:
                    logger.warning(f"     ⚠️ 策略 {name} 未生成检测单元")
                    
            except Exception as e:
                logger.error(f"     ❌ 策略 {name} 失败: {e}")
                
    except Exception as e:
        logger.error(f"❌ 蛇形路径算法诊断失败: {e}")
        import traceback
        traceback.print_exc()

def diagnose_detection_units():
    """诊断检测单元生成过程"""
    try:
        # 获取数据
        hole_collection = diagnose_data_source()
        if not hole_collection:
            return
            
        logger.info("🔧 分析检测单元生成过程...")
        
        # 模拟simulation_controller的逻辑
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        # 尝试生成检测单元
        logger.info("   步骤1: 尝试生成HolePair检测单元")
        try:
            detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            if detection_units:
                logger.info(f"   ✅ 生成了 {len(detection_units)} 个HolePair检测单元")
                
                # 分析单元组成
                for i, unit in enumerate(detection_units[:5]):  # 只显示前5个
                    if hasattr(unit, 'holes'):
                        hole_ids = [h.hole_id for h in unit.holes]
                        logger.info(f"      单元 {i+1}: {hole_ids}")
                    else:
                        logger.info(f"      单元 {i+1}: {unit.hole_id}")
                        
                if len(detection_units) > 5:
                    logger.info(f"      ... 还有 {len(detection_units)-5} 个单元")
                    
            else:
                logger.warning("   ⚠️ HolePair生成失败，尝试后备方案")
                
                # 后备方案：单孔列表
                hole_list = list(hole_collection.holes.values())
                hole_list.sort(key=lambda h: (h.center_y, h.center_x))
                detection_units = hole_list
                
                logger.info(f"   ✅ 后备方案生成了 {len(detection_units)} 个单孔检测单元")
                
        except Exception as e:
            logger.error(f"   ❌ 检测单元生成失败: {e}")
            return
            
        # 分析检测单元转换为孔位列表的过程
        logger.info("   步骤2: 分析检测单元 -> 孔位列表转换")
        snake_sorted_holes = []
        
        for unit in detection_units:
            if hasattr(unit, 'holes'):
                snake_sorted_holes.extend(unit.holes)
            else:
                snake_sorted_holes.append(unit)
                
        logger.info(f"   ✅ 转换后孔位列表长度: {len(snake_sorted_holes)}")
        logger.info(f"   覆盖率: {len(snake_sorted_holes)/len(hole_collection.holes)*100:.2f}%")
        
        # 检查是否有重复
        hole_ids = [h.hole_id for h in snake_sorted_holes]
        unique_ids = set(hole_ids)
        if len(hole_ids) != len(unique_ids):
            logger.warning(f"   ⚠️ 发现重复孔位: {len(hole_ids) - len(unique_ids)} 个")
            
        # 检查是否有遗漏
        original_ids = set(hole_collection.holes.keys())
        snake_ids = set(hole_ids)
        missing_ids = original_ids - snake_ids
        if missing_ids:
            logger.warning(f"   ⚠️ 遗漏孔位: {len(missing_ids)} 个")
            logger.info(f"      前5个遗漏ID: {list(missing_ids)[:5]}")
        else:
            logger.info("   ✅ 无遗漏孔位")
            
    except Exception as e:
        logger.error(f"❌ 检测单元诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_traversal_completeness()