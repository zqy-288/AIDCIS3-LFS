#!/usr/bin/env python3
"""
诊断扇形分配问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.core_business.hole_numbering_service import HoleNumberingService
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer


def diagnose_sectors():
    """诊断扇形分配"""
    print("=" * 80)
    print("诊断扇形分配问题")
    print("=" * 80)
    
    # 加载DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    
    print(f"\n加载DXF文件: {dxf_path}")
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    if not hole_collection:
        print("❌ 加载DXF文件失败")
        return
    
    print(f"✅ 成功加载 {len(hole_collection.holes)} 个孔位")
    
    # 应用编号
    numbering_service = HoleNumberingService()
    numbered_collection = numbering_service.apply_numbering(hole_collection)
    
    # 创建渲染器
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(numbered_collection)
    
    # 获取孔位列表
    holes = list(numbered_collection.holes.values())
    
    # 计算整体边界
    min_x = min(h.center_x for h in holes)
    max_x = max(h.center_x for h in holes)
    min_y = min(h.center_y for h in holes)
    max_y = max(h.center_y for h in holes)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    print(f"\n整体边界:")
    print(f"  X: {min_x:.1f} 到 {max_x:.1f}, 中心: {center_x:.1f}")
    print(f"  Y: {min_y:.1f} 到 {max_y:.1f}, 中心: {center_y:.1f}")
    
    # 分组
    sector_groups = renderer._group_holes_by_sector_v2(holes)
    
    print("\n扇形分组结果:")
    for sector_name in ['sector_1', 'sector_2', 'sector_3', 'sector_4']:
        sector_holes = sector_groups[sector_name]
        if sector_holes:
            # 计算扇形边界
            s_min_x = min(h.center_x for h in sector_holes)
            s_max_x = max(h.center_x for h in sector_holes)
            s_min_y = min(h.center_y for h in sector_holes)
            s_max_y = max(h.center_y for h in sector_holes)
            
            print(f"\n{sector_name}: {len(sector_holes)} 个孔位")
            print(f"  X范围: {s_min_x:.1f} 到 {s_max_x:.1f}")
            print(f"  Y范围: {s_min_y:.1f} 到 {s_max_y:.1f}")
            
            # 显示一些样本孔位
            print("  样本孔位:")
            for i, hole in enumerate(sector_holes[:5]):
                print(f"    {hole.hole_id}: ({hole.center_x:.1f}, {hole.center_y:.1f})")
    
    # 检查特殊孔位
    print("\n特殊孔位检查:")
    special_holes = [
        "BC098R164", "BC102R164", "BC098R001", "BC102R001",
        "AC098R164", "AC102R164", "AC098R001", "AC102R001"
    ]
    
    for hole_id in special_holes:
        if hole_id in numbered_collection.holes:
            hole = numbered_collection.holes[hole_id]
            x, y = hole.center_x, hole.center_y
            dx = x - center_x
            dy = y - center_y
            
            # 判断应该在哪个扇形
            if dx >= 0 and dy >= 0:
                expected = "sector_1"
            elif dx < 0 and dy >= 0:
                expected = "sector_2"
            elif dx < 0 and dy < 0:
                expected = "sector_3"
            else:
                expected = "sector_4"
            
            # 找到实际所在扇形
            actual = None
            for sector_name, sector_holes in sector_groups.items():
                if hole in sector_holes:
                    actual = sector_name
                    break
            
            status = "✅" if expected == actual else "❌"
            print(f"  {status} {hole_id}: ({x:.1f}, {y:.1f}) - 期望:{expected}, 实际:{actual}")


if __name__ == "__main__":
    diagnose_sectors()