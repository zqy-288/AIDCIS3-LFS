#!/usr/bin/env python3
"""诊断孔位ID格式"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService

def main():
    print("=" * 80)
    print("孔位ID格式诊断")
    print("=" * 80)
    
    # 加载DXF文件
    loader = DXFLoaderService()
    dxf_path = project_root / "assets/dxf/DXF Graph/东重管板.dxf"
    
    print(f"\n1. 加载DXF文件: {dxf_path}")
    hole_collection = loader.load_dxf_file(str(dxf_path))
    if not hole_collection:
        print("   ❌ 加载失败")
        return
    
    # 获取所有孔位
    all_holes = list(hole_collection.holes.values())
    print(f"\n2. 总孔位数: {len(all_holes)}")
    
    # 显示前10个孔位的ID和位置
    print("\n3. 前10个孔位:")
    print("-" * 80)
    print(f"{'索引':>6} {'孔位ID':>20} {'X坐标':>10} {'Y坐标':>10} {'推断ID':>20}")
    print("-" * 80)
    
    for i in range(min(10, len(all_holes))):
        hole = all_holes[i]
        # 根据位置推断孔位编号
        side = 'A' if hole.center_y < 0 else 'B'  # Qt坐标系
        inferred_id = f"{side}C???R???"  # 推断的格式
        print(f"{i+1:>6} {hole.hole_id:>20} {hole.center_x:>10.2f} {hole.center_y:>10.2f} {inferred_id:>20}")
    
    # 查找包含特定模式的孔位
    print("\n4. 查找包含 '164' 的孔位ID:")
    print("-" * 80)
    found_164 = False
    for hole_id, hole in hole_collection.holes.items():
        if '164' in str(hole_id):
            print(f"   找到: {hole_id} (x={hole.center_x:.2f}, y={hole.center_y:.2f})")
            found_164 = True
            if not found_164:
                break  # 只显示第一个
    
    if not found_164:
        print("   未找到包含 '164' 的孔位ID")
    
    # 分析孔位ID格式
    print("\n5. 孔位ID格式分析:")
    print("-" * 80)
    
    # 检查所有ID的格式
    id_formats = set()
    for hole_id in hole_collection.holes.keys():
        # 尝试识别格式
        if hole_id.startswith(('AC', 'BC')):
            id_formats.add("标准格式 (AC/BC)")
        elif hole_id.isdigit():
            id_formats.add("纯数字格式")
        else:
            id_formats.add(f"其他格式: {hole_id[:10]}...")
    
    for fmt in id_formats:
        print(f"   - {fmt}")
    
    # 查找最大Y值的孔位（应该是R164）
    print("\n6. 查找Y坐标最小的孔位（Qt坐标系中最上方，应该对应R164）:")
    print("-" * 80)
    
    # 按Y坐标排序
    sorted_holes = sorted(all_holes, key=lambda h: h.center_y)
    
    # 显示前10个（最上方的）
    print(f"{'孔位ID':>20} {'X坐标':>10} {'Y坐标':>10} {'说明':>30}")
    print("-" * 80)
    for i in range(min(10, len(sorted_holes))):
        hole = sorted_holes[i]
        desc = "最上方孔位" if i == 0 else f"第{i+1}上方孔位"
        print(f"{hole.hole_id:>20} {hole.center_x:>10.2f} {hole.center_y:>10.2f} {desc:>30}")


if __name__ == "__main__":
    main()