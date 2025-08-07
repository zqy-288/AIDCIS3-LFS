#!/usr/bin/env python3
"""
验证全景图自适应功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 读取修改后的文件内容
file_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")

print("="*60)
print("全景图自适应功能验证")
print("="*60)

# 检查关键的修改
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
    # 检查是否移除了 setMaximumHeight
    if "self.sidebar_panorama.setMaximumHeight" in content:
        print("❌ 错误: 仍然存在 setMaximumHeight 限制")
    else:
        print("✅ 正确: 已移除 setMaximumHeight 限制")
    
    # 检查是否设置了 QSizePolicy.Expanding
    if "QSizePolicy.Expanding" in content:
        print("✅ 正确: 已设置 QSizePolicy.Expanding")
    else:
        print("❌ 错误: 未设置 QSizePolicy.Expanding")
    
    # 检查是否设置了最小高度
    if "self.sidebar_panorama.setMinimumHeight" in content:
        print("✅ 正确: 已设置最小高度")
    else:
        print("❌ 错误: 未设置最小高度")
    
    # 检查是否为panorama_group添加了拉伸因子
    if "layout.addWidget(self.panorama_group, 1)" in content:
        print("✅ 正确: 已为panorama_group添加拉伸因子")
    else:
        print("❌ 错误: 未为panorama_group添加拉伸因子")
    
    # 检查是否移除了末尾的addStretch
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "layout.addWidget(self.panorama_group" in line:
            # 检查后续几行是否有 addStretch
            has_stretch_after = False
            for j in range(i+1, min(i+5, len(lines))):
                if "layout.addStretch()" in lines[j]:
                    has_stretch_after = True
                    break
            if not has_stretch_after:
                print("✅ 正确: panorama_group后没有addStretch")
            else:
                print("❌ 错误: panorama_group后仍有addStretch")
            break

print("\n" + "="*60)
print("总结:")
print("左侧全景图现在应该能够:")
print("1. 随窗口高度变化而自动调整大小")
print("2. 保持最小高度200像素")
print("3. 在垂直方向上扩展填充可用空间")
print("="*60)