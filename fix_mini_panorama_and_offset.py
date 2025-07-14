#!/usr/bin/env python3
"""
修复小型全景图实时更新和中间列偏移问题的诊断脚本
"""

import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("AIDCIS 小型全景图和偏移问题修复诊断")
    print("=" * 80)
    
    # 检查文件是否存在
    files_to_check = [
        "src/aidcis2/graphics/dynamic_sector_view.py",
        "src/main_window.py",
        "src/aidcis2/graphics/graphics_view.py"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            return
    
    print("\n问题诊断:")
    print("-" * 40)
    
    # 问题1: 小型全景图找不到孔位
    print("\n1. 小型全景图找不到孔位的问题:")
    print("   原因: 初始化和查找时使用了不一致的数据结构")
    print("   - 初始化时使用 hole_collection (HoleCollection对象)")
    print("   - 更新时期望找到 hole_id")
    print("   解决: 确保setData和查找时使用相同的hole_id")
    
    # 问题2: 中间列偏移被覆盖
    print("\n2. 中间列偏移被覆盖的问题:")
    print("   原因: 多个地方在设置变换后又调用了居中操作")
    print("   - graphics_view.py 的 resizeEvent")
    print("   - fit_in_view_with_margin 的多次 centerOn")
    print("   - QTimer 延迟调用的居中操作")
    print("   解决: 使用 disable_auto_center 标志禁用所有自动居中")
    
    # 问题3: 信号连接问题
    print("\n3. _synchronize_panorama_status 未被调用:")
    print("   原因: 信号连接可能在错误的时机或参数不匹配")
    print("   解决: 在模拟更新时直接调用同步函数")
    
    print("\n修复建议:")
    print("-" * 40)
    print("1. 修改 _initialize_mini_panorama_data 确保数据一致性")
    print("2. 在所有自动居中操作前检查 disable_auto_center 标志")
    print("3. 在模拟更新时添加直接同步调用")
    
    print("\n验证步骤:")
    print("-" * 40)
    print("1. 启动程序并加载数据")
    print("2. 开始培训模拟")
    print("3. 观察小型全景图是否实时更新绿点")
    print("4. 观察中间列是否有向右偏移效果")
    print("5. 查看日志确认 _synchronize_panorama_status 被调用")
    
    print("\n日志关键词:")
    print("-" * 40)
    print("- '🎯 [小型全景图] 找到目标孔位'")
    print("- '✅ [小型全景图] 状态已更新'")
    print("- '🔄 [调试] _synchronize_panorama_status 被调用'")
    print("- '✅ 扇形已应用偏移显示'")
    print("- '🚫 跳过强制居中（disable_auto_center=True）'")

if __name__ == "__main__":
    main()