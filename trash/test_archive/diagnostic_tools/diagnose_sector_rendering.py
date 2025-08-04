#!/usr/bin/env python3
"""
诊断扇形渲染问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager
from src.core_business.graphics.sector_types import SectorQuadrant


def diagnose_sector_assignment():
    """诊断扇形分配问题"""
    print("\n" + "="*60)
    print("扇形分配诊断")
    print("="*60)
    
    # 1. 加载DXF数据
    print("\n1. 加载DXF数据...")
    dxf_path = str(Path(__file__).parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf")
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    if not hole_collection:
        print("❌ DXF加载失败")
        return
        
    print(f"✅ 加载成功: {len(hole_collection.holes)} 个孔位")
    
    # 2. 创建扇形分配管理器并执行分配
    print("\n2. 执行扇形分配...")
    manager = SectorAssignmentManager()
    manager.set_hole_collection(hole_collection)
    
    # 3. 检查分配结果
    print("\n3. 分配结果统计:")
    sector_counts = manager.get_all_sector_counts()
    total_assigned = sum(sector_counts.values())
    
    for sector, count in sorted(sector_counts.items(), key=lambda x: x[0].value):
        percentage = (count / total_assigned * 100) if total_assigned > 0 else 0
        print(f"   {sector.value}: {count:,} 个孔位 ({percentage:.1f}%)")
    
    print(f"\n   总计: {total_assigned:,} 个孔位已分配")
    
    # 4. 检查中心点计算
    print("\n4. 中心点信息:")
    if manager.sector_center:
        print(f"   中心点: ({manager.sector_center.x():.1f}, {manager.sector_center.y():.1f})")
    else:
        print("   ❌ 中心点未计算")
    
    # 5. 检查每个扇形的样本孔位
    print("\n5. 每个扇形的样本孔位:")
    for sector in SectorQuadrant:
        info = manager.get_sector_info(sector)
        if info:
            print(f"\n   {sector.value}:")
            print(f"   - 定义: {info['quadrant_definition']}")
            print(f"   - 孔位数: {info['hole_count']}")
            print(f"   - 前5个孔位:")
            for i, hole in enumerate(info['sample_holes'][:5]):
                print(f"     {i+1}. {hole['hole_id']}: ({hole['center_x']:.1f}, {hole['center_y']:.1f})")
    
    # 6. 验证分配逻辑
    print("\n6. 验证分配逻辑:")
    if manager.sector_center:
        center_x = manager.sector_center.x()
        center_y = manager.sector_center.y()
        
        # 选择每个象限的测试点
        test_points = [
            ("右上测试点", center_x + 100, center_y - 100, SectorQuadrant.SECTOR_1),
            ("左上测试点", center_x - 100, center_y - 100, SectorQuadrant.SECTOR_2),
            ("左下测试点", center_x - 100, center_y + 100, SectorQuadrant.SECTOR_3),
            ("右下测试点", center_x + 100, center_y + 100, SectorQuadrant.SECTOR_4),
        ]
        
        for name, x, y, expected_sector in test_points:
            dx = x - center_x
            dy = y - center_y
            
            # 使用相同的分配逻辑
            if dx >= 0 and dy <= 0:
                actual_sector = SectorQuadrant.SECTOR_1
            elif dx < 0 and dy <= 0:
                actual_sector = SectorQuadrant.SECTOR_2
            elif dx < 0 and dy > 0:
                actual_sector = SectorQuadrant.SECTOR_3
            else:
                actual_sector = SectorQuadrant.SECTOR_4
            
            result = "✅" if actual_sector == expected_sector else "❌"
            print(f"   {name} ({x:.1f}, {y:.1f}): 预期={expected_sector.value}, 实际={actual_sector.value} {result}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    diagnose_sector_assignment()