#!/usr/bin/env python3
"""诊断扇形过滤问题"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查关键方法
print("=== 检查扇形过滤相关方法 ===")

# 1. 检查 _show_sector_in_view 方法
file_path = project_root / "src/pages/main_detection_p1/native_main_detection_view_p1.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
# 查找 _show_sector_in_view 方法
import re
match = re.search(r'def _show_sector_in_view\(self, sector\):(.*?)(?=\n    def|\Z)', content, re.DOTALL)
if match:
    print("\n_show_sector_in_view 方法内容：")
    print("-" * 50)
    lines = match.group(0).split('\n')
    for i, line in enumerate(lines[:20]):  # 只显示前20行
        print(f"{i+1}: {line}")
    print("-" * 50)
    
    # 检查是否有 item.setVisible 调用
    if 'item.setVisible' in match.group(0):
        print("✅ 找到 item.setVisible 调用")
    else:
        print("❌ 没有找到 item.setVisible 调用")
        
    # 检查是否有 sector_hole_ids 
    if 'sector_hole_ids' in match.group(0):
        print("✅ 找到 sector_hole_ids 变量")
    else:
        print("❌ 没有找到 sector_hole_ids 变量")

# 2. 检查协调器的 get_current_sector_holes 方法
print("\n=== 检查协调器方法 ===")
coord_file = project_root / "src/pages/main_detection_p1/components/panorama_sector_coordinator.py"
if coord_file.exists():
    with open(coord_file, 'r', encoding='utf-8') as f:
        coord_content = f.read()
        
    # 查找 get_current_sector_holes 方法
    match = re.search(r'def get_current_sector_holes\(self.*?\):(.*?)(?=\n    def|\Z)', coord_content, re.DOTALL)
    if match:
        print("\nget_current_sector_holes 方法找到")
        # 检查返回值
        if 'return' in match.group(0):
            print("✅ 方法有返回值")
        else:
            print("❌ 方法没有返回值")
    else:
        print("❌ 没有找到 get_current_sector_holes 方法")

print("\n=== 诊断建议 ===")
print("1. 检查协调器是否正确返回了扇形孔位")
print("2. 检查场景过滤逻辑是否正确执行")
print("3. 确认 item.setVisible(False) 是否真的隐藏了孔位")
print("4. 检查是否需要调用场景的 update() 方法")