#!/usr/bin/env python3
"""
简化版检测顺序分析 - 直接构造测试数据
"""

import re

def analyze_sorting_logic():
    """分析排序逻辑问题"""
    print("\n" + "="*60)
    print("检测顺序排序逻辑分析")
    print("="*60 + "\n")
    
    # 模拟sector_1（右上象限）的Y坐标数据
    # 在Qt坐标系中，Y值越小越在上方
    # R164应该在最上方，具有最小的Y值
    print("1. 模拟数据：")
    print("-" * 50)
    
    # 创建模拟的Y坐标到行号的映射
    y_to_row_mapping = {
        -820.0: "R164",  # 最上方，Y值最小
        -815.0: "R163",
        -810.0: "R162",
        -805.0: "R161",
        -800.0: "R160",
        # ... 中间省略 ...
        -15.0: "R003",
        -10.0: "R002",
        -5.0: "R001"     # 最下方（接近中心），Y值最大
    }
    
    # 打印映射关系
    print("\nY坐标到行号的映射（示例）：")
    for y, row in sorted(y_to_row_mapping.items())[:5]:
        print(f"   Y={y:.1f} -> {row}")
    print("   ...")
    for y, row in sorted(y_to_row_mapping.items())[-3:]:
        print(f"   Y={y:.1f} -> {row}")
    
    # 当前的排序方式
    print("\n2. 当前排序方式分析：")
    print("-" * 50)
    
    sorted_y_current = sorted(y_to_row_mapping.keys(), reverse=True)
    print("\n使用 sorted(holes_by_y.keys(), reverse=True)：")
    print("（从大到小排序，即从下往上）")
    for i, y in enumerate(sorted_y_current[:5]):
        row = y_to_row_mapping[y]
        print(f"   第{i+1}个处理: Y={y:.1f} -> {row}")
    
    print(f"\n❌ 问题：第一个处理的是 {y_to_row_mapping[sorted_y_current[0]]}，而不是R164")
    
    # 正确的排序方式
    print("\n3. 正确排序方式：")
    print("-" * 50)
    
    sorted_y_correct = sorted(y_to_row_mapping.keys())
    print("\n使用 sorted(holes_by_y.keys())：")
    print("（从小到大排序，即从上往下）")
    for i, y in enumerate(sorted_y_correct[:5]):
        row = y_to_row_mapping[y]
        print(f"   第{i+1}个处理: Y={y:.1f} -> {row}")
    
    print(f"\n✅ 正确：第一个处理的是 {y_to_row_mapping[sorted_y_correct[0]]}")
    
    # 代码修改建议
    print("\n4. 修复建议：")
    print("-" * 50)
    print("\n在文件: src/pages/shared/components/snake_path/snake_path_renderer.py")
    print("第419行附近：")
    print("\n当前代码：")
    print("    if sector_name in ['sector_1', 'sector_2']:")
    print("        # 上半部分：从最大Y开始（R164在顶部）")
    print("        sorted_rows = sorted(holes_by_y.keys(), reverse=True)")
    print("\n修改为：")
    print("    if sector_name in ['sector_1', 'sector_2']:")
    print("        # 上半部分：从最小Y开始（R164在顶部，Y值最小）")
    print("        sorted_rows = sorted(holes_by_y.keys())")
    
    print("\n原因解释：")
    print("- 在Qt坐标系中，Y轴向下增长")
    print("- Y值越小，位置越靠上")
    print("- R164在最上方，具有最小的Y值")
    print("- 要从R164开始，应该从最小Y值开始，不需要reverse=True")

if __name__ == "__main__":
    analyze_sorting_logic()