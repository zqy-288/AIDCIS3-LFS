#!/usr/bin/env python3
"""诊断孔位数量不一致问题"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager
from src.core_business.graphics.sector_types import SectorQuadrant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def diagnose_hole_count():
    """诊断孔位数量问题"""
    # 加载DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    
    if not Path(dxf_path).exists():
        logging.error(f"DXF文件不存在: {dxf_path}")
        return
    
    # 使用DXF加载服务
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    if not hole_collection:
        logging.error("加载DXF文件失败")
        return
    
    logging.info(f"=== DXF文件加载结果 ===")
    logging.info(f"总孔位数: {len(hole_collection.holes)}")
    
    # 使用扇形分配管理器
    manager = SectorAssignmentManager()
    manager.set_hole_collection(hole_collection)
    
    # 统计各扇形孔位数
    sector_counts = manager.get_all_sector_counts()
    
    logging.info(f"\n=== 扇形分配结果 ===")
    total_in_sectors = 0
    unique_holes = set()
    
    for sector in SectorQuadrant:
        count = sector_counts.get(sector, 0)
        holes = manager.get_sector_holes(sector)
        unique_count = len(set(h.hole_id for h in holes))
        
        logging.info(f"{sector.value}: {count} 个孔位 (唯一: {unique_count})")
        total_in_sectors += count
        
        # 收集所有孔位ID
        for hole in holes:
            unique_holes.add(hole.hole_id)
    
    logging.info(f"\n=== 统计分析 ===")
    logging.info(f"原始总数: {len(hole_collection.holes)}")
    logging.info(f"扇形分配总和: {total_in_sectors}")
    logging.info(f"唯一孔位数: {len(unique_holes)}")
    
    if total_in_sectors != len(hole_collection.holes):
        logging.warning(f"⚠️ 扇形分配总和与原始总数不一致！")
        logging.warning(f"差异: {total_in_sectors - len(hole_collection.holes)}")
        
        # 检查是否有重复分配
        all_hole_ids = []
        for sector in SectorQuadrant:
            holes = manager.get_sector_holes(sector)
            all_hole_ids.extend([h.hole_id for h in holes])
        
        # 找出重复的孔位
        from collections import Counter
        counter = Counter(all_hole_ids)
        duplicates = [(hole_id, count) for hole_id, count in counter.items() if count > 1]
        
        if duplicates:
            logging.warning(f"\n发现 {len(duplicates)} 个重复分配的孔位:")
            for hole_id, count in duplicates[:10]:  # 只显示前10个
                logging.warning(f"  {hole_id}: 出现 {count} 次")
    
    # 检查扇形边界附近的孔位
    logging.info(f"\n=== 扇形边界检查 ===")
    # 获取管板中心
    bounds = hole_collection.get_bounds()
    center_x = (bounds[0] + bounds[2]) / 2
    center_y = (bounds[1] + bounds[3]) / 2
    logging.info(f"管板中心: ({center_x:.1f}, {center_y:.1f})")
    
    # 检查一些边界孔位
    boundary_holes = []
    for hole in list(hole_collection.holes.values())[:20]:
        dx = hole.center_x - center_x
        dy = hole.center_y - center_y
        
        # 检查是否在坐标轴附近（可能在扇形边界）
        if abs(dx) < 50 or abs(dy) < 50:
            sector = SectorQuadrant.from_position(hole.center_x, hole.center_y, center_x, center_y)
            boundary_holes.append((hole.hole_id, hole.center_x, hole.center_y, sector))
    
    if boundary_holes:
        logging.info("边界附近的孔位示例:")
        for hole_id, x, y, sector in boundary_holes[:5]:
            logging.info(f"  {hole_id}: ({x:.1f}, {y:.1f}) -> {sector.value}")

if __name__ == "__main__":
    diagnose_hole_count()