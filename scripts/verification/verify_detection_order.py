#!/usr/bin/env python3
"""
验证检测顺序 - 使用实际的DXF文件
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.components.simulation_controller import SimulationController
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.core_business.hole_numbering_service import HoleNumberingService


def verify_detection_order():
    """验证实际的检测顺序"""
    print("=" * 80)
    print("验证实际DXF文件的检测顺序")
    print("=" * 80)
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    if not Path(dxf_path).exists():
        print(f"❌ DXF文件不存在: {dxf_path}")
        return
    
    print(f"\n加载DXF文件: {dxf_path}")
    
    # 创建加载器并加载数据
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    if not hole_collection:
        print("❌ 加载DXF文件失败")
        return
    
    print(f"✅ 成功加载 {len(hole_collection.holes)} 个孔位")
    
    # 应用编号
    numbering_service = HoleNumberingService()
    numbered_collection = numbering_service.apply_numbering(hole_collection)
    
    # 创建模拟控制器
    controller = SimulationController()
    controller.load_hole_collection(numbered_collection)
    
    # 生成检测路径
    controller._generate_detection_units()
    
    print(f"\n生成了 {len(controller.detection_units)} 个检测单元")
    
    # 显示前20个检测单元
    print("\n前20个检测单元:")
    print("-" * 80)
    
    for i, unit in enumerate(controller.detection_units[:20]):
        if unit.is_pair and len(unit.holes) == 2:
            print(f"{i+1:3d}. {unit.holes[0].hole_id} + {unit.holes[1].hole_id}")
        else:
            print(f"{i+1:3d}. {unit.holes[0].hole_id}")
    
    # 验证起始位置
    print("\n" + "=" * 60)
    print("验证起始位置:")
    
    if len(controller.detection_units) > 0:
        first_unit = controller.detection_units[0]
        if first_unit.is_pair and len(first_unit.holes) == 2:
            first_holes = f"{first_unit.holes[0].hole_id} + {first_unit.holes[1].hole_id}"
            expected_holes = ["BC098R164", "BC102R164"]
            actual_holes = [first_unit.holes[0].hole_id, first_unit.holes[1].hole_id]
            
            if all(h in actual_holes for h in expected_holes):
                print(f"✅ 检测起始位置正确: {first_holes}")
            else:
                print(f"❌ 检测起始位置错误: {first_holes}")
                print(f"   期望包含: BC098R164 + BC102R164")
    
    # 分析扇形顺序
    print("\n扇形处理顺序分析:")
    print("-" * 60)
    
    current_sector = None
    sector_changes = []
    sector_hole_count = {}
    
    for i, unit in enumerate(controller.detection_units[:200]):  # 只看前200个
        # 使用第一个孔位判断扇形
        hole = unit.holes[0]
        x, y = hole.center_x, hole.center_y
        
        # 判断扇形
        if x > 0 and y > 0:
            sector = "sector_1 (右上)"
        elif x < 0 and y > 0:
            sector = "sector_2 (左上)"
        elif x < 0 and y < 0:
            sector = "sector_3 (左下)"
        else:  # x > 0 and y < 0
            sector = "sector_4 (右下)"
        
        # 统计
        if sector not in sector_hole_count:
            sector_hole_count[sector] = 0
        sector_hole_count[sector] += len(unit.holes)
        
        if sector != current_sector:
            current_sector = sector
            if len(sector_changes) < 5:  # 只记录前5个变化
                sector_changes.append((i, sector))
    
    for idx, (unit_idx, sector) in enumerate(sector_changes):
        print(f"{idx+1}. 从检测单元 {unit_idx+1} 开始: {sector}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    verify_detection_order()