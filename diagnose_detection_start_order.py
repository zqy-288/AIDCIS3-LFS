#!/usr/bin/env python3
"""
诊断检测起始顺序问题
分析为什么检测从BC099R001+BC103R001开始，而不是从BC098R164+BC102R164开始
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleCollection, HoleData
from src.pages.shared.components.snake_path import PathStrategy
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer

def load_test_data():
    """加载测试数据"""
    from src.core_business.dxf_parser import DXFParser
    
    parser = DXFParser()
    dxf_file = "data/25MW钛板20250114.dxf"
    
    if not os.path.exists(dxf_file):
        print(f"❌ DXF文件不存在: {dxf_file}")
        return None
        
    result = parser.parse(dxf_file)
    if result.success:
        print(f"✅ 成功加载 {len(result.holes)} 个孔位")
        return result.holes
    else:
        print(f"❌ 加载失败: {result.error}")
        return None

def analyze_detection_order():
    """分析检测顺序"""
    print("\n" + "="*60)
    print("检测起始顺序分析")
    print("="*60 + "\n")
    
    # 加载孔位数据
    hole_collection = load_test_data()
    if not hole_collection:
        return
        
    # 创建蛇形路径渲染器
    from PySide6.QtWidgets import QGraphicsScene
    scene = QGraphicsScene()
    
    snake_path_renderer = SnakePathRenderer()
    snake_path_renderer.set_graphics_scene(scene)
    snake_path_renderer.set_hole_collection(hole_collection)
    
    # 生成间隔4列的检测单元
    print("\n生成INTERVAL_FOUR_S_SHAPE检测单元...")
    detection_units = snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n✅ 生成了 {len(detection_units)} 个检测单元")
    
    # 分析前10个检测单元
    print("\n前10个检测单元：")
    print("-" * 50)
    
    for i, unit in enumerate(detection_units[:10]):
        hole_ids = [h.hole_id for h in unit.holes]
        if len(hole_ids) == 2:
            print(f"{i+1}. {hole_ids[0]} + {hole_ids[1]} (配对)")
        else:
            print(f"{i+1}. {hole_ids[0]} (单个)")
            
        # 打印第一个孔位的坐标信息
        first_hole = unit.holes[0]
        print(f"   坐标: ({first_hole.center_x:.1f}, {first_hole.center_y:.1f})")
        
        # 从hole_id解析行列号
        import re
        match = re.match(r'([AB])C(\d{3})R(\d{3})', first_hole.hole_id)
        if match:
            side = match.group(1)
            col = int(match.group(2))
            row = int(match.group(3))
            print(f"   位置: {side}侧, 列{col}, 行{row}")
    
    # 分析为什么是这个顺序
    print("\n\n问题分析：")
    print("-" * 50)
    
    # 检查sector_1的Y坐标排序
    print("\n1. 检查sector_1（右上象限）的Y坐标排序：")
    
    # 获取sector_1的孔位
    sector_1_holes = []
    holes_list = list(hole_collection.holes.values())
    
    # 计算中心点
    min_x = min(h.center_x for h in holes_list)
    max_x = max(h.center_x for h in holes_list)
    min_y = min(h.center_y for h in holes_list)
    max_y = max(h.center_y for h in holes_list)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    print(f"\n   几何中心: ({center_x:.1f}, {center_y:.1f})")
    print(f"   坐标范围: X[{min_x:.1f}, {max_x:.1f}], Y[{min_y:.1f}, {max_y:.1f}]")
    
    # 筛选sector_1的孔位
    for hole in holes_list:
        dx = hole.center_x - center_x
        dy = hole.center_y - center_y
        
        if dx >= 0 and dy <= 0:  # Qt坐标系右上象限
            sector_1_holes.append(hole)
    
    print(f"\n   sector_1包含 {len(sector_1_holes)} 个孔位")
    
    # 按Y坐标分组
    holes_by_y = {}
    y_tolerance = 5.0
    
    for hole in sector_1_holes:
        y_rounded = round(hole.center_y / y_tolerance) * y_tolerance
        if y_rounded not in holes_by_y:
            holes_by_y[y_rounded] = []
        holes_by_y[y_rounded].append(hole)
    
    # 打印Y坐标排序情况
    print(f"\n   Y坐标分组（共{len(holes_by_y)}行）：")
    
    # 按照当前代码的排序方式
    sorted_rows_current = sorted(holes_by_y.keys(), reverse=True)
    print("\n   当前排序（reverse=True，从大到小）：")
    for i, y in enumerate(sorted_rows_current[:5]):
        row_holes = holes_by_y[y]
        # 找出这一行的典型孔位ID
        sample_hole = row_holes[0]
        match = re.match(r'([AB])C(\d{3})R(\d{3})', sample_hole.hole_id)
        if match:
            row_num = int(match.group(3))
            print(f"      第{i+1}行: Y={y:.1f}, 包含{len(row_holes)}个孔位, 行号R{row_num:03d}")
    
    # 正确的排序方式
    sorted_rows_correct = sorted(holes_by_y.keys())
    print("\n   正确排序（不反转，从小到大）：")
    for i, y in enumerate(sorted_rows_correct[:5]):
        row_holes = holes_by_y[y]
        sample_hole = row_holes[0]
        match = re.match(r'([AB])C(\d{3})R(\d{3})', sample_hole.hole_id)
        if match:
            row_num = int(match.group(3))
            print(f"      第{i+1}行: Y={y:.1f}, 包含{len(row_holes)}个孔位, 行号R{row_num:03d}")
    
    print("\n\n结论：")
    print("-" * 50)
    print("问题原因：在Qt坐标系中，Y值越小越在上方。")
    print("对于上半部分（sector_1和sector_2），R164在最上方，具有最小的Y值。")
    print("但当前代码使用了reverse=True，导致从最大Y值（最下方）开始，即从R001开始。")
    print("\n修复方案：")
    print("将419行的 sorted(holes_by_y.keys(), reverse=True) 改为 sorted(holes_by_y.keys())")
    print("这样就能确保从最小Y值（最上方的R164）开始检测。")

if __name__ == "__main__":
    analyze_detection_order()