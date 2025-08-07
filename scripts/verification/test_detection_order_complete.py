#!/usr/bin/env python3
"""
完整测试检测顺序 - 创建更多孔位以确保能形成配对
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def create_complete_test_holes():
    """创建完整的测试孔位数据 - 确保有足够的列形成配对"""
    holes = []
    
    # 创建更多列的数据，确保能形成间隔4列的配对
    # 列号范围：C094到C106（覆盖间隔4列的情况）
    columns = list(range(94, 107))  # C094 到 C106
    rows = [1, 2, 163, 164]  # 选择关键行
    
    for col in columns:
        for row in rows:
            # A侧（y > 0）
            hole_id_a = f"AC{col:03d}R{row:03d}"
            x_a = -1000 - (col - 94) * 48  # 负x坐标
            y_a = 10 + (row - 1) * 12 if row <= 82 else 10 + (163 - row) * 12
            
            # B侧（y < 0）
            hole_id_b = f"BC{col:03d}R{row:03d}"
            x_b = 1000 + (col - 94) * 48  # 正x坐标
            y_b = -10 - (row - 1) * 12 if row <= 82 else -10 - (163 - row) * 12
            
            # 创建A侧孔位
            hole_a = HoleData(
                hole_id=hole_id_a,
                center_x=x_a,
                center_y=y_a,
                radius=5.0
            )
            holes.append(hole_a)
            
            # 创建B侧孔位
            hole_b = HoleData(
                hole_id=hole_id_b,
                center_x=x_b,
                center_y=y_b,
                radius=5.0
            )
            holes.append(hole_b)
    
    # 创建孔位字典
    holes_dict = {hole.hole_id: hole for hole in holes}
    return HoleCollection(holes=holes_dict)


def test_detection_order():
    """测试检测顺序"""
    print("=" * 80)
    print("完整测试检测顺序和配对")
    print("=" * 80)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    # 创建测试数据
    hole_collection = create_complete_test_holes()
    print(f"\n创建了 {len(hole_collection.holes)} 个测试孔位")
    
    # 显示创建的孔位
    print("\n创建的孔位示例:")
    all_holes = list(hole_collection.holes.values())
    for i, hole in enumerate(all_holes[:10]):
        print(f"  {hole.hole_id}: ({hole.center_x:.1f}, {hole.center_y:.1f})")
    
    # 创建渲染器并生成路径
    print("\n" + "-" * 60)
    print("生成检测路径...")
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成了 {len(detection_units)} 个检测单元")
    
    # 统计配对情况
    pair_count = sum(1 for unit in detection_units if unit.is_pair and len(unit.holes) > 1)
    single_count = sum(1 for unit in detection_units if not unit.is_pair or len(unit.holes) == 1)
    print(f"配对单元: {pair_count}, 单孔单元: {single_count}")
    
    # 显示前20个检测单元
    print("\n前20个检测单元:")
    print("-" * 60)
    
    for i, unit in enumerate(detection_units[:20]):
        if unit.is_pair and len(unit.holes) == 2:
            print(f"{i+1:3d}. {unit.holes[0].hole_id} + {unit.holes[1].hole_id} (配对)")
        else:
            print(f"{i+1:3d}. {unit.holes[0].hole_id} (单孔)")
    
    # 验证起始位置
    print("\n" + "=" * 60)
    print("验证起始位置:")
    print("-" * 60)
    
    if len(detection_units) > 0:
        first_unit = detection_units[0]
        if first_unit.is_pair and len(first_unit.holes) == 2:
            first_holes = f"{first_unit.holes[0].hole_id} + {first_unit.holes[1].hole_id}"
            # 检查是否从R164行开始
            if "R164" in first_holes:
                print(f"✅ 检测从R164行开始: {first_holes}")
            else:
                print(f"❌ 检测未从R164行开始: {first_holes}")
        else:
            hole_id = first_unit.holes[0].hole_id
            if "R164" in hole_id:
                print(f"✅ 检测从R164行开始: {hole_id}")
            else:
                print(f"❌ 检测未从R164行开始: {hole_id}")
    
    # 分析扇形顺序
    print("\n扇形处理顺序分析:")
    print("-" * 60)
    
    current_sector = None
    sector_changes = []
    sector_hole_count = {}
    
    for i, unit in enumerate(detection_units):
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
        
        # 统计每个扇形的孔位数
        if sector not in sector_hole_count:
            sector_hole_count[sector] = 0
        sector_hole_count[sector] += len(unit.holes)  # 配对算2个孔
        
        if sector != current_sector:
            current_sector = sector
            sector_changes.append((i, sector))
    
    for idx, (unit_idx, sector) in enumerate(sector_changes):
        holes_in_sector = sector_hole_count.get(sector, 0)
        print(f"{idx+1}. 从单元 {unit_idx+1} 开始: {sector} (包含 {holes_in_sector} 个孔)")
    
    # 验证扇形顺序
    expected_order = ["sector_1 (右上)", "sector_2 (左上)", "sector_3 (左下)", "sector_4 (右下)"]
    actual_order = [sector for _, sector in sector_changes]
    
    print("\n" + "=" * 60)
    print("扇形顺序验证:")
    print(f"期望顺序: {' → '.join(expected_order)}")
    print(f"实际顺序: {' → '.join(actual_order)}")
    
    if actual_order == expected_order:
        print("✅ 扇形顺序正确!")
    else:
        print("❌ 扇形顺序不正确!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_detection_order()