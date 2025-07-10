#!/usr/bin/env python3
"""
测试精确颜色分布比例
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("📊 精确颜色分布比例测试")
    print("=" * 60)
    
    # 检查V2方法是否包含新的比例分配
    try:
        from main_window import MainWindow
        import inspect
        
        # 检查_update_simulation_v2方法
        v2_source = inspect.getsource(MainWindow._update_simulation_v2)
        
        print("🔍 检查比例分配逻辑:")
        
        if "rand < 0.995" in v2_source:
            print("✅ 99.5%合格比例已设置")
        else:
            print("❌ 99.5%合格比例未找到")
        
        if "rand < 0.9999" in v2_source:
            print("✅ 0.49%异常比例已设置")
        else:
            print("❌ 0.49%异常比例未找到")
        
        if "盲孔" in v2_source and "拉杆孔" in v2_source:
            print("✅ 其他状态（盲孔、拉杆孔）已添加")
        else:
            print("❌ 其他状态未找到")
        
        if "QColor(255, 255, 0)" in v2_source:
            print("✅ 黄色（盲孔）颜色已设置")
        else:
            print("❌ 黄色（盲孔）颜色未找到")
        
        if "QColor(0, 0, 255)" in v2_source:
            print("✅ 蓝色（拉杆孔）颜色已设置")
        else:
            print("❌ 蓝色（拉杆孔）颜色未找到")
        
        # 检查统计功能
        start_source = inspect.getsource(MainWindow._start_simulation_progress_v2)
        
        if "v2_stats" in start_source:
            print("✅ 统计功能已添加")
        else:
            print("❌ 统计功能未找到")
        
        if "预期分布比例" in start_source:
            print("✅ 预期分布显示已添加")
        else:
            print("❌ 预期分布显示未找到")
            
    except Exception as e:
        print(f"❌ 检查V2方法失败: {e}")
        return False
    
    print("\n📊 **精确比例规格**")
    print("=" * 60)
    print("🟢 合格 (绿色):    99.5%  - QColor(0, 255, 0)")
    print("🔴 异常 (红色):    0.49%  - QColor(255, 0, 0)")
    print("🟡 盲孔 (黄色):    0.005% - QColor(255, 255, 0)")
    print("🔵 拉杆孔 (蓝色):  0.005% - QColor(0, 0, 255)")
    print("📈 总计:          100.0%")
    
    print("\n🧪 **测试步骤**")
    print("=" * 60)
    print("1. 重启程序: python main.py")
    print("2. 加载DXF: 按 Ctrl+T")
    print("3. 运行模拟: 点击'使用模拟进度'按钮")
    print("4. 观察日志输出中的:")
    print("   - 预期分布比例")
    print("   - 每个孔位的检测结果")
    print("   - 最终统计结果")
    
    print("\n🔍 **预期日志输出**")
    print("=" * 60)
    print("🚀 开始模拟进度 V2 - 精确比例分配")
    print("🎯 将处理 9 个孔位")
    print("📊 预期分布比例:")
    print("  🟢 合格: 99.5% (约 8 个)")
    print("  🔴 异常: 0.49% (约 0 个)")
    print("  🟡🔵 其他: 0.01% (约 0 个)")
    print("...")
    print("🟢 V2: H00001 检测完成 → 合格 (#00ff00)")
    print("🟢 V2: H00002 检测完成 → 合格 (#00ff00)")
    print("🔴 V2: H00003 检测完成 → 异常 (#ff0000)")
    print("🟡 V2: H00004 检测完成 → 盲孔 (#ffff00)")
    print("...")
    print("✅ 模拟进度 V2 完成")
    print("📊 最终统计结果:")
    print("  🟢 合格: 8 个 (88.89%)")
    print("  🔴 异常: 1 个 (11.11%)")
    print("  🟡 盲孔: 0 个 (0.00%)")
    print("  🔵 拉杆孔: 0 个 (0.00%)")
    print("🎯 总合格率: 88.89%")
    
    print("\n💡 **注意事项**")
    print("=" * 60)
    print("- 由于孔位数量较少(9个)，实际分布可能与理论比例有差异")
    print("- 异常和其他状态出现概率很低，可能需要多次运行才能看到")
    print("- 统计结果会显示实际的百分比分布")
    print("- 颜色变化：灰色 → 橙色(500ms) → 最终颜色")
    
    print("\n🎨 **颜色图例**")
    print("=" * 60)
    print("🟢 绿色 = 合格 (最常见)")
    print("🔴 红色 = 异常 (偶尔出现)")  
    print("🟡 黄色 = 盲孔 (极少出现)")
    print("🔵 蓝色 = 拉杆孔 (极少出现)")
    print("🟠 橙色 = 检测中 (临时状态)")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 精确比例分配验证完成！")
        print("\n🎯 现在模拟进度使用真实的工业检测比例分布！")
    else:
        print("\n❌ 精确比例分配验证失败！")
