#!/usr/bin/env python3
"""诊断扇形统计显示6274孔位的问题"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.core_business.dxf_parser import DXFParser
from src.core_business.graphics.sector_types import SectorQuadrant
from src.pages.main_detection_p1.components.panorama_sector_coordinator import PanoramaSectorCoordinator
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager

def diagnose_sector_assignment():
    """诊断扇形分配问题"""
    app = QApplication(sys.argv)
    
    # 加载DXF数据
    parser = DXFParser()
    dxf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "Data/Products/CAP1000/dxf/CAP1000.dxf")
    
    print("1. 加载DXF文件...")
    hole_collection = parser.parse_file(dxf_path)
    if not hole_collection:
        print("加载DXF文件失败")
        return
    print(f"   总孔数: {len(hole_collection.holes)}")
    
    # 创建扇形分配管理器
    print("\n2. 创建扇形分配管理器...")
    manager = SectorAssignmentManager()
    manager.set_hole_collection(hole_collection)
    
    # 获取各扇形的孔位数
    print("\n3. 各扇形孔位数统计:")
    sector_counts = manager.get_all_sector_counts()
    total_assigned = 0
    for sector in SectorQuadrant:
        count = sector_counts.get(sector, 0)
        holes = manager.get_sector_holes(sector)
        print(f"   {sector.value}: {count} 个孔位 (实际获取: {len(holes)} 个)")
        total_assigned += count
        
        # 显示前5个孔位ID作为样本
        if holes:
            sample_ids = [h.hole_id for h in holes[:5]]
            print(f"      样本孔位: {sample_ids}")
    
    print(f"\n   已分配总数: {total_assigned}")
    print(f"   原始总数: {len(hole_collection.holes)}")
    
    # 创建协调器并测试
    print("\n4. 创建扇形协调器...")
    coordinator = PanoramaSectorCoordinator()
    coordinator.load_hole_collection(hole_collection)
    
    # 检查协调器的扇形孔位映射
    print("\n5. 协调器扇形孔位映射:")
    for sector in SectorQuadrant:
        holes = coordinator.sector_holes_map.get(sector, [])
        print(f"   {sector.value}: {len(holes)} 个孔位")
    
    # 模拟点击一个扇形
    print("\n6. 模拟点击扇形1...")
    test_sector = SectorQuadrant.SECTOR_1
    coordinator.set_current_sector(test_sector)
    
    # 获取扇形统计
    sector_holes = coordinator.sector_holes_map.get(test_sector, [])
    stats = coordinator._calculate_sector_stats(sector_holes)
    
    print(f"\n7. 扇形1统计结果:")
    print(f"   总数: {stats['total']} (应该是 {len(sector_holes)})")
    print(f"   待检: {stats['pending']}")
    print(f"   合格: {stats['qualified']}")
    print(f"   异常: {stats['defective']}")
    print(f"   盲孔: {stats['blind']}")
    print(f"   拉杆: {stats['tie_rod']}")
    
    # 检查是否有问题
    if stats['total'] == len(hole_collection.holes):
        print(f"\n❌ 问题确认: 扇形统计显示了所有孔位 ({stats['total']})，而不是该扇形的孔位 ({len(sector_holes)})")
    else:
        print(f"\n✅ 扇形统计正确: 显示 {stats['total']} 个孔位")

if __name__ == "__main__":
    diagnose_sector_assignment()