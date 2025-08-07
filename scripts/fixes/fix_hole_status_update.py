#!/usr/bin/env python3
"""
修复孔位状态更新问题
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_simulation_controller():
    """修复simulation_controller中的状态更新问题"""
    file_path = project_root / "src/pages/main_detection_p1/components/simulation_controller.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复错误的属性名
    # 将 detection_status 改为 status
    content = content.replace(
        "self.hole_collection.holes[hole_id].detection_status = status",
        "self.hole_collection.holes[hole_id].status = status"
    )
    
    # 同时修复其他可能的 detection_status 引用
    content = content.replace(
        "if hole.detection_status == HoleStatus.QUALIFIED:",
        "if hole.status == HoleStatus.QUALIFIED:"
    )
    content = content.replace(
        "elif hole.detection_status == HoleStatus.DEFECTIVE:",
        "elif hole.status == HoleStatus.DEFECTIVE:"
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修复了 {file_path}")
    return True


def verify_hole_data_attributes():
    """验证HoleData类的属性"""
    from src.core_business.models.hole_data import HoleData, HoleStatus
    
    # 创建测试实例
    hole = HoleData(
        hole_id="TEST",
        center_x=0,
        center_y=0,
        radius=10,
        status=HoleStatus.PENDING
    )
    
    # 检查属性
    print("\nHoleData 属性检查:")
    print(f"- status 属性存在: {hasattr(hole, 'status')}")
    print(f"- detection_status 属性存在: {hasattr(hole, 'detection_status')}")
    print(f"- 当前 status 值: {hole.status}")
    
    # 测试状态更新
    hole.status = HoleStatus.QUALIFIED
    print(f"- 更新后 status 值: {hole.status}")
    
    return True


def main():
    print("=== 修复孔位状态更新问题 ===\n")
    
    # 1. 验证HoleData属性
    print("1. 验证HoleData属性...")
    verify_hole_data_attributes()
    
    # 2. 修复simulation_controller
    print("\n2. 修复simulation_controller...")
    fix_simulation_controller()
    
    print("\n✅ 修复完成！")
    print("\n建议:")
    print("1. 运行 diagnose_hole_status_update.py 验证修复效果")
    print("2. 检查其他文件中是否有类似的错误引用")


if __name__ == "__main__":
    main()