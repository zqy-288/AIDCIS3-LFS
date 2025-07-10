#!/usr/bin/env python3
"""
孔位信息显示调试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔍 孔位信息显示问题调试")
    print("=" * 60)
    
    print("📋 问题分析:")
    print("主检测页面孔位信息仍然不显示，可能的原因:")
    print()
    
    print("1️⃣ **UI组件初始化问题**")
    print("   - selected_hole_id_label 等组件可能未正确创建")
    print("   - 组件可能被其他布局覆盖")
    print("   - 组件可能不在当前可见区域")
    print()
    
    print("2️⃣ **数据流问题**")
    print("   - selected_hole 变量可能未正确赋值")
    print("   - update_hole_info_display() 可能未被调用")
    print("   - 搜索功能可能未找到孔位")
    print()
    
    print("3️⃣ **UI刷新问题**")
    print("   - Qt事件队列处理问题")
    print("   - 标签文本设置后未生效")
    print("   - 布局更新问题")
    print()
    
    print("🔧 **调试步骤**")
    print("=" * 50)
    print("请按以下步骤进行调试:")
    print()
    
    print("步骤1: 检查UI组件是否存在")
    print("  1. 启动程序: python main.py")
    print("  2. 切换到'主检测视图'选项卡")
    print("  3. 在Python控制台输入:")
    print("     print(hasattr(window, 'selected_hole_id_label'))")
    print("     print(window.selected_hole_id_label.text())")
    print()
    
    print("步骤2: 检查DXF加载和孔位数据")
    print("  1. 按Ctrl+T加载DXF")
    print("  2. 观察右下角日志是否显示:")
    print("     '✅ DXF文件加载成功'")
    print("     '📊 孔位统计: 总数=XXX'")
    print("  3. 如果没有，说明DXF加载失败")
    print()
    
    print("步骤3: 检查搜索功能")
    print("  1. 在搜索框输入'H00001'")
    print("  2. 点击搜索按钮")
    print("  3. 观察右下角日志是否显示:")
    print("     '搜索 H00001 找到 1 个孔位'")
    print("     '🔍 搜索选中孔位: H00001'")
    print("  4. 如果没有，说明搜索功能有问题")
    print()
    
    print("步骤4: 检查UI更新过程")
    print("  1. 搜索后观察日志是否显示:")
    print("     '🔄 开始UI更新...'")
    print("     '✅ 所有UI组件验证通过'")
    print("     '📝 准备设置ID标签: H00001'")
    print("     '✅ ID标签设置结果: 期望=H00001, 实际=H00001'")
    print("  2. 如果没有这些日志，说明update_hole_info_display()未被调用")
    print()
    
    print("步骤5: 手动检查UI组件")
    print("  1. 在左下角找到'孔位信息'组框")
    print("  2. 检查是否有以下标签:")
    print("     - 孔位ID: [值]")
    print("     - 位置: [值]")
    print("     - 状态: [值]")
    print("     - 半径: [值]")
    print("  3. 如果组框不存在，说明UI布局有问题")
    print()
    
    print("🚨 **可能的解决方案**")
    print("=" * 50)
    print()
    
    print("方案1: 强制UI组件可见性")
    print("  - 确保孔位信息组框在左侧面板中")
    print("  - 检查是否被其他组件遮挡")
    print("  - 调整窗口大小确保组件可见")
    print()
    
    print("方案2: 重新初始化UI组件")
    print("  - 重启程序")
    print("  - 确保在主检测视图选项卡")
    print("  - 重新加载DXF文件")
    print()
    
    print("方案3: 检查数据文件")
    print("  - 确认测试管板.dxf文件存在")
    print("  - 确认文件格式正确")
    print("  - 确认包含H00001等孔位数据")
    print()
    
    print("💡 **调试技巧**")
    print("=" * 50)
    print("1. 使用日志输出跟踪执行流程")
    print("2. 检查右下角日志区域的详细信息")
    print("3. 如果日志区域也不显示，说明整个UI有问题")
    print("4. 可以尝试调整窗口大小或重新排列面板")
    print()
    
    print("🎯 **下一步行动**")
    print("=" * 50)
    print("请按照上述调试步骤操作，并告诉我:")
    print("1. 哪一步出现了问题")
    print("2. 具体的错误信息或异常现象")
    print("3. 右下角日志显示的内容")
    print()
    print("这样我可以针对性地修复问题。")

if __name__ == "__main__":
    main()
