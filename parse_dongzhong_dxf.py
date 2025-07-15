#!/usr/bin/env python3
"""
东重管板DXF解析器 - 提取完整孔位信息和网格坐标
"""

import ezdxf
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass
class Hole:
    hole_id: str
    center_x: float
    center_y: float
    radius: float
    row: Optional[int] = None
    column: Optional[int] = None

def parse_dxf_holes(dxf_file_path: str, expected_radius: float = 8.865, tolerance: float = 0.1) -> List[Hole]:
    """解析DXF文件中的孔位"""
    print(f"正在解析DXF文件: {dxf_file_path}")
    
    try:
        doc = ezdxf.readfile(dxf_file_path)
    except Exception as e:
        print(f"读取DXF文件失败: {e}")
        return []
    
    modelspace = doc.modelspace()
    holes = []
    hole_counter = 1
    
    # 按圆心位置分组的圆弧
    arc_groups = defaultdict(list)
    
    print("扫描圆弧实体...")
    arc_count = 0
    
    for entity in modelspace:
        if entity.dxftype() == 'ARC':
            arc_count += 1
            # 使用dxf属性获取圆心坐标
            center_x = entity.dxf.center.x
            center_y = entity.dxf.center.y
            center = (round(center_x, 2), round(center_y, 2))
            radius = entity.dxf.radius
            
            # 过滤掉边界弧和不符合孔径的弧
            if abs(radius - expected_radius) <= tolerance and radius < 100:
                arc_groups[center].append(entity)
        
        elif entity.dxftype() == 'CIRCLE':
            center_x = entity.dxf.center.x
            center_y = entity.dxf.center.y
            center = (round(center_x, 2), round(center_y, 2))
            radius = entity.dxf.radius
            
            if abs(radius - expected_radius) <= tolerance and radius < 100:
                # AI员工3号修改开始 - 临时使用H格式，稍后转换为新格式
                hole = Hole(
                    hole_id=f"H{hole_counter:05d}",
                    center_x=center[0],
                    center_y=center[1],
                    radius=radius
                )
                # AI员工3号修改结束
                holes.append(hole)
                hole_counter += 1
    
    print(f"发现 {arc_count} 个圆弧实体")
    print(f"发现 {len(arc_groups)} 个可能的孔位（圆弧组）")
    
    # 处理圆弧组，检查是否形成完整的圆
    for center, arcs in arc_groups.items():
        if len(arcs) >= 2:  # 至少两个弧段
            total_angle = 0
            for arc in arcs:
                start_angle = arc.dxf.start_angle
                end_angle = arc.dxf.end_angle
                angle_diff = end_angle - start_angle
                if angle_diff < 0:
                    angle_diff += 360
                total_angle += angle_diff
            
            # 检查是否接近360度
            if abs(total_angle - 360) <= 10:
                avg_radius = sum(arc.dxf.radius for arc in arcs) / len(arcs)
                
                # AI员工3号修改开始 - 临时使用H格式，稍后转换为新格式
                hole = Hole(
                    hole_id=f"H{hole_counter:05d}",
                    center_x=center[0],
                    center_y=center[1],
                    radius=avg_radius
                )
                # AI员工3号修改结束
                holes.append(hole)
                hole_counter += 1
    
    print(f"总共识别出 {len(holes)} 个孔位")
    return holes

# AI员工3号修改开始 - 新格式ID转换函数
def convert_to_new_hole_id(row: int, column: int) -> str:
    """将行列坐标转换为新格式孔位ID: C{col:03d}R{row:03d}"""
    return f"C{column:03d}R{row:03d}"
# AI员工3号修改结束

def assign_grid_positions(holes: List[Hole], row_tolerance: float = 5.0) -> None:
    """分配网格位置"""
    print(f"分配网格位置，Y坐标容差: {row_tolerance}mm")
    
    # 按Y坐标排序（从高到低）
    holes_by_y = sorted(holes, key=lambda h: h.center_y, reverse=True)
    
    # 分配行号
    current_row = 1
    current_y = holes_by_y[0].center_y
    
    for hole in holes_by_y:
        if abs(hole.center_y - current_y) > row_tolerance:
            current_row += 1
            current_y = hole.center_y
        hole.row = current_row
    
    # 在每行内按X坐标排序并分配列号
    rows = defaultdict(list)
    for hole in holes:
        rows[hole.row].append(hole)
    
    for row_num, row_holes in rows.items():
        row_holes.sort(key=lambda h: h.center_x)
        for col_num, hole in enumerate(row_holes, 1):
            hole.column = col_num
            # AI员工3号修改开始 - 更新为新格式ID
            hole.hole_id = convert_to_new_hole_id(hole.row, hole.column)
            # AI员工3号修改结束
    
    max_row = max(hole.row for hole in holes)
    max_cols_per_row = max(len(row_holes) for row_holes in rows.values())
    
    print(f"网格结构: {max_row} 行, 最大 {max_cols_per_row} 列")
    # AI员工3号修改开始 - 输出格式转换信息
    print(f"✅ 已将所有孔位ID转换为新格式 C{{col:03d}}R{{row:03d}}")
    # AI员工3号修改结束

def generate_correspondence_table(holes: List[Hole], output_file: str = "dongzhong_hole_grid.json"):
    """生成Row/Column对应表"""
    print(f"生成对应表到文件: {output_file}")
    
    # 按行和列排序
    holes_sorted = sorted(holes, key=lambda h: (h.row, h.column))
    
    # 创建对应表数据
    correspondence_data = {
        "project_name": "东重管板",
        "total_holes": len(holes),
        "grid_info": {
            "total_rows": max(hole.row for hole in holes),
            "row_tolerance_mm": 5.0,
            "coordinate_system": "DXF_standard"
        },
        "holes": []
    }
    
    for hole in holes_sorted:
        hole_data = {
            "hole_id": hole.hole_id,
            "coordinates": {
                "x_mm": hole.center_x,
                "y_mm": hole.center_y
            },
            "grid_position": {
                "row": hole.row,
                "column": hole.column
            },
            "radius_mm": hole.radius
        }
        correspondence_data["holes"].append(hole_data)
    
    # 保存到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correspondence_data, f, ensure_ascii=False, indent=2)
    
    # AI员工3号修改开始 - 更新表头显示新格式
    # 生成简化的表格输出
    print("\n" + "="*80)
    print("东重管板 Row/Column 对应表 (前20项) - 新格式 C{col:03d}R{row:03d}")
    print("="*80)
    print(f"{'孔编号(新)':<12} | {'X坐标(mm)':<10} | {'Y坐标(mm)':<10} | {'行(Row)':<6} | {'列(Column)':<8}")
    print("-" * 80)
    # AI员工3号修改结束
    
    for i, hole in enumerate(holes_sorted[:20]):
        print(f"{hole.hole_id:<12} | {hole.center_x:<10.2f} | {hole.center_y:<10.2f} | {hole.row:<6} | {hole.column:<8}")
    
    if len(holes) > 20:
        print(f"... (还有 {len(holes) - 20} 个孔位)")
    
    # 统计信息
    rows = defaultdict(int)
    for hole in holes:
        rows[hole.row] += 1
    
    print(f"\n网格统计信息:")
    print(f"总孔数: {len(holes)}")
    print(f"总行数: {len(rows)}")
    print(f"每行孔数范围: {min(rows.values())} - {max(rows.values())}")
    
    # 显示前几行的孔数分布
    print(f"\n前10行孔数分布:")
    for row_num in sorted(rows.keys())[:10]:
        print(f"第{row_num}行: {rows[row_num]}个孔")

def main():
    """主函数"""
    dxf_file = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    
    print("🎯 东重管板DXF完整解析")
    print("=" * 60)
    
    # 解析孔位
    holes = parse_dxf_holes(dxf_file)
    
    if not holes:
        print("❌ 未能解析到任何孔位")
        return False
    
    # 分配网格位置
    assign_grid_positions(holes)
    
    # 生成对应表
    generate_correspondence_table(holes)
    
    print("\n✅ 解析完成!")
    return True

if __name__ == "__main__":
    success = main()