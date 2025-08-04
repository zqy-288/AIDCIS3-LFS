#!/usr/bin/env python3
"""修复蛇形路径生成以覆盖所有孔位"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from typing import List, Dict, Tuple
from dataclasses import dataclass
from src.core_business.models.hole_data import HoleData, HoleCollection
from src.pages.shared.components.snake_path.snake_path_renderer import HolePair

@dataclass
class GridPosition:
    """网格位置"""
    row_idx: int
    col_idx: int
    hole: HoleData

def create_detection_units_for_all_holes(hole_collection: HoleCollection) -> List[HolePair]:
    """为所有孔位创建检测单元（确保100%覆盖）"""
    
    # 获取所有孔位
    holes = list(hole_collection.holes.values())
    print(f"Total holes: {len(holes)}")
    
    # 按Y坐标分组（行）
    holes_by_y = {}
    y_tolerance = 5.0  # Y坐标容差
    
    for hole in holes:
        y_rounded = round(hole.center_y / y_tolerance) * y_tolerance
        if y_rounded not in holes_by_y:
            holes_by_y[y_rounded] = []
        holes_by_y[y_rounded].append(hole)
    
    print(f"Found {len(holes_by_y)} rows")
    
    # 对每行按X坐标排序
    for y in holes_by_y:
        holes_by_y[y].sort(key=lambda h: h.center_x)
    
    # 按Y坐标排序所有行（从上到下）
    sorted_rows = sorted(holes_by_y.keys(), reverse=True)
    
    # 生成检测单元
    detection_units = []
    
    for row_idx, y in enumerate(sorted_rows):
        row_holes = holes_by_y[y]
        
        # S形路径：奇数行从左到右，偶数行从右到左
        if row_idx % 2 == 1:
            row_holes = list(reversed(row_holes))
        
        # 创建间隔4的配对
        processed = set()
        
        # 先处理所有可以配对的
        for i in range(len(row_holes)):
            if i in processed:
                continue
                
            # 尝试找到间隔4的配对
            if i + 4 < len(row_holes) and (i + 4) not in processed:
                # 创建配对
                pair = HolePair(
                    holes=[row_holes[i], row_holes[i + 4]],
                    is_pair=True
                )
                detection_units.append(pair)
                processed.add(i)
                processed.add(i + 4)
        
        # 处理剩余的单个孔位
        for i in range(len(row_holes)):
            if i not in processed:
                single = HolePair(
                    holes=[row_holes[i]],
                    is_pair=False
                )
                detection_units.append(single)
    
    return detection_units

def test_full_coverage():
    """测试完整覆盖"""
    from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 加载DXF
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    # 生成检测单元
    detection_units = create_detection_units_for_all_holes(hole_collection)
    
    # 统计覆盖的孔位
    covered_holes = set()
    for unit in detection_units:
        for hole in unit.holes:
            covered_holes.add(hole.hole_id)
    
    print(f"\nResults:")
    print(f"Total detection units: {len(detection_units)}")
    print(f"Total holes covered: {len(covered_holes)}")
    print(f"Coverage: {len(covered_holes)}/{len(hole_collection.holes)} = {len(covered_holes)/len(hole_collection.holes)*100:.1f}%")
    
    # 统计配对和单个
    paired = sum(1 for u in detection_units if u.is_pair)
    single = sum(1 for u in detection_units if not u.is_pair)
    print(f"Paired units: {paired}")
    print(f"Single units: {single}")

if __name__ == "__main__":
    test_full_coverage()