#!/usr/bin/env python3
"""分析检测数量问题"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from PySide6.QtWidgets import QApplication, QGraphicsScene

# 创建QApplication以避免Qt警告
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def analyze_detection_count():
    """分析检测数量问题"""
    # 加载CAP1000 DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
    
    print(f"加载DXF文件: {dxf_path}")
    loader = DXFLoaderService()
    hole_collection = loader.load_dxf_file(dxf_path)
    
    if not hole_collection:
        print("❌ 无法加载DXF文件")
        return
        
    print(f"✅ 加载成功: {len(hole_collection.holes)} 个孔位")
    
    # 创建蛇形路径渲染器
    renderer = SnakePathRenderer()
    scene = QGraphicsScene()
    renderer.set_graphics_scene(scene)
    renderer.set_hole_collection(hole_collection)
    
    # 生成间隔4列的检测单元
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成的检测单元: {len(detection_units)} 个")
    
    # 统计每个象限的孔位数
    hole_positions = list(renderer.hole_positions.values())
    
    # 计算中心点
    if hole_positions:
        x_coords = [h.center_x for h in hole_positions]
        y_coords = [h.center_y for h in hole_positions]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        print(f"\n坐标范围:")
        print(f"X: {min_x:.1f} 到 {max_x:.1f}")
        print(f"Y: {min_y:.1f} 到 {max_y:.1f}")
        print(f"计算的中心点: ({center_x:.1f}, {center_y:.1f})")
        
        # 统计每个象限的孔位
        q1_count = sum(1 for h in hole_positions if h.center_x >= center_x and h.center_y <= center_y)
        q2_count = sum(1 for h in hole_positions if h.center_x < center_x and h.center_y <= center_y)
        q3_count = sum(1 for h in hole_positions if h.center_x < center_x and h.center_y > center_y)
        q4_count = sum(1 for h in hole_positions if h.center_x >= center_x and h.center_y > center_y)
        
        print(f"\n象限分布:")
        print(f"第1象限 (右上): {q1_count} 个孔位")
        print(f"第2象限 (左上): {q2_count} 个孔位")
        print(f"第3象限 (左下): {q3_count} 个孔位")
        print(f"第4象限 (右下): {q4_count} 个孔位")
        print(f"总计: {q1_count + q2_count + q3_count + q4_count} 个孔位")
        
        # 分析检测单元覆盖的孔位
        covered_holes = set()
        for unit in detection_units:
            for hole in unit.holes:
                covered_holes.add(hole.hole_id)
                
        print(f"\n检测单元覆盖的孔位: {len(covered_holes)} 个")
        print(f"未覆盖的孔位: {len(hole_collection.holes) - len(covered_holes)} 个")
        
        # 查看前几个检测单元
        print(f"\n前10个检测单元:")
        for i, unit in enumerate(detection_units[:10]):
            hole_ids = [h.hole_id for h in unit.holes]
            print(f"  单元{i+1}: {hole_ids}")
            
        # 检查问题：为什么只有部分孔位被处理？
        # 获取sector分组结果
        sector_holes = renderer._group_holes_by_sector(hole_positions)
        
        print(f"\n_group_holes_by_sector 分组结果:")
        for sector, holes in sector_holes.items():
            print(f"  {sector}: {len(holes)} 个孔位")

if __name__ == "__main__":
    analyze_detection_count()