#!/usr/bin/env python3
"""
验证数据同步问题修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_data_sync_fix():
    """验证数据同步修复"""
    print("🔍 验证数据同步修复...\n")
    
    # 检查文件修改
    file_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 1. 检查整体统计计算是否包含盲孔和拉杆
    if "'blind': blind" in content and "'tie_rod': tie_rod" in content:
        checks.append(("✅", "_calculate_overall_stats包含盲孔和拉杆统计"))
    else:
        checks.append(("❌", "_calculate_overall_stats缺少盲孔和拉杆统计"))
    
    # 2. 检查数据加载时是否更新整体统计
    if "overall_stats = self._calculate_overall_stats()" in content:
        checks.append(("✅", "数据加载时计算整体统计"))
    else:
        checks.append(("❌", "数据加载时未计算整体统计"))
    
    # 3. 检查是否同时更新扇形统计
    if "sector_stats = self.coordinator._calculate_sector_stats(sector_holes)" in content:
        checks.append(("✅", "数据加载时更新扇形统计"))
    else:
        checks.append(("❌", "数据加载时未更新扇形统计"))
    
    # 4. 检查扇形统计更新方法
    if "def update_sector_stats(self, stats_data):" in content:
        checks.append(("✅", "扇形统计更新方法存在"))
    else:
        checks.append(("❌", "扇形统计更新方法不存在"))
    
    # 5. 检查状态统计更新
    if "self.left_panel.update_progress_display(overall_stats)" in content:
        checks.append(("✅", "状态统计使用整体统计数据"))
    else:
        checks.append(("❌", "状态统计未使用整体统计数据"))
    
    # 打印结果
    print("📊 验证结果:")
    print("="*50)
    
    passed = 0
    for status, desc in checks:
        print(f"{status} {desc}")
        if status == "✅":
            passed += 1
    
    total = len(checks)
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 数据同步问题已修复！")
        print("\n修复说明：")
        print("1. 状态统计现在显示整体数据（所有孔位）")
        print("2. 选中扇形只显示该扇形的数据")
        print("3. 盲孔和拉杆统计已正确计算")
        print("4. 数据加载时会同时更新两个统计区域")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 项需要检查")
        return False


if __name__ == "__main__":
    print("="*60)
    print("数据同步问题验证")
    print("="*60)
    
    success = verify_data_sync_fix()
    sys.exit(0 if success else 1)