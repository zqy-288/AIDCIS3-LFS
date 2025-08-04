#!/usr/bin/env python3
"""
简单测试panorama迁移
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("开始测试panorama包迁移...")

# 测试1: 导入主包
try:
    import src.modules.panorama_view
    print("✅ 1. 导入主包成功")
except Exception as e:
    print(f"❌ 1. 导入主包失败: {e}")

# 测试2: 导入容器
try:
    from src.modules.panorama_view.core import PanoramaDIContainer
    print("✅ 2. 导入容器成功")
except Exception as e:
    print(f"❌ 2. 导入容器失败: {e}")

# 测试3: 导入适配器
try:
    from src.modules.panorama_view.adapters import CompletePanoramaWidgetAdapter
    print("✅ 3. 导入适配器成功")
except Exception as e:
    print(f"❌ 3. 导入适配器失败: {e}")

# 测试4: 检查旧路径兼容性
try:
    import warnings
    with warnings.catch_warnings(record=True) as w:
        from src.core_business.graphics.panorama import PanoramaDIContainer as OldContainer
        if w:
            print("✅ 4. 旧路径兼容性正常（显示警告）")
        else:
            print("⚠️ 4. 旧路径兼容但无警告")
except Exception as e:
    print(f"❌ 4. 旧路径兼容失败: {e}")

print("\n测试完成！")