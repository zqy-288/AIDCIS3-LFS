#!/usr/bin/env python3
"""分析漏检的孔位"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from PySide6.QtWidgets import QApplication, QGraphicsScene

# 创建QApplication
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def analyze_missed_holes():
    """分析漏检的孔位"""
    # 加载DXF
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    print(f"Total holes in collection: {len(hole_collection.holes)}")
    
    # 创建渲染器并生成检测单元
    renderer = SnakePathRenderer()
    scene = QGraphicsScene()
    renderer.set_graphics_scene(scene)
    renderer.set_hole_collection(hole_collection)
    
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"Generated detection units: {len(detection_units)}")
    
    # 收集所有被覆盖的孔位
    covered_holes = set()
    for unit in detection_units:
        for hole in unit.holes:
            covered_holes.add(hole.hole_id)
    
    print(f"Covered holes: {len(covered_holes)}")
    
    # 找出未被覆盖的孔位
    all_hole_ids = set(hole_collection.holes.keys())
    missed_holes = all_hole_ids - covered_holes
    
    print(f"\nMissed holes: {len(missed_holes)}")
    
    if missed_holes:
        # 分析漏检孔位的特征
        print("\nAnalyzing missed holes...")
        
        # 按Y坐标分组
        missed_by_y = {}
        for hole_id in list(missed_holes)[:20]:  # 只看前20个
            hole = hole_collection.holes[hole_id]
            y_rounded = round(hole.center_y / 5.0) * 5.0
            if y_rounded not in missed_by_y:
                missed_by_y[y_rounded] = []
            missed_by_y[y_rounded].append(hole)
        
        # 打印漏检孔位信息
        print("\nSample missed holes (first 20):")
        for y in sorted(missed_by_y.keys(), reverse=True):
            holes = missed_by_y[y]
            x_positions = [h.center_x for h in holes]
            print(f"  Y={y:.1f}: {len(holes)} holes at X={[f'{x:.1f}' for x in sorted(x_positions)]}")
        
        # 检查边缘情况
        print("\nChecking edge cases...")
        all_holes = list(hole_collection.holes.values())
        
        # 找出每行的孔位数量
        holes_per_row = {}
        for hole in all_holes:
            y_rounded = round(hole.center_y / 5.0) * 5.0
            if y_rounded not in holes_per_row:
                holes_per_row[y_rounded] = []
            holes_per_row[y_rounded].append(hole)
        
        # 统计每行的孔位数量分布
        row_counts = {}
        for y, holes in holes_per_row.items():
            count = len(holes)
            if count not in row_counts:
                row_counts[count] = 0
            row_counts[count] += 1
        
        print("\nHoles per row distribution:")
        for count in sorted(row_counts.keys()):
            print(f"  {count} holes/row: {row_counts[count]} rows")
        
        # 检查间隔4配对的问题
        print("\nChecking interval-4 pairing issues...")
        problem_rows = []
        for y, holes in holes_per_row.items():
            holes.sort(key=lambda h: h.center_x)
            # 如果行中的孔位数不能被4整除，可能有问题
            if len(holes) % 4 not in [0, 1]:  # 0或1是正常的
                problem_rows.append((y, len(holes)))
        
        if problem_rows:
            print(f"Found {len(problem_rows)} rows with potential pairing issues:")
            for y, count in sorted(problem_rows)[:10]:
                print(f"  Y={y:.1f}: {count} holes (remainder: {count % 4})")

if __name__ == "__main__":
    analyze_missed_holes()