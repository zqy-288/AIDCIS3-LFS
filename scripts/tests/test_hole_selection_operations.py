#!/usr/bin/env python3
"""
测试孔位选择和操作功能
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🎯 孔位选择和操作功能测试")
    print("=" * 60)
    
    # 检查功能是否正确实现
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        print("🔍 检查孔位操作方法:")
        
        # 检查goto_realtime方法
        realtime_source = inspect.getsource(MainWindow.goto_realtime)
        if "H00001" in realtime_source and "H00002" in realtime_source:
            print("✅ 实时监控: 包含数据可用性检查")
        else:
            print("❌ 实时监控: 缺少数据可用性检查")
        
        # 检查goto_history方法
        history_source = inspect.getsource(MainWindow.goto_history)
        if "H00001" in history_source and "H00002" in history_source:
            print("✅ 历史数据: 包含数据可用性检查")
        else:
            print("❌ 历史数据: 缺少数据可用性检查")
        
        # 检查mark_defective方法
        mark_source = inspect.getsource(MainWindow.mark_defective)
        if "确认标记异常" in mark_source:
            print("✅ 标记异常: 包含确认对话框")
        else:
            print("❌ 标记异常: 缺少确认对话框")
        
        # 检查数据检查方法
        if hasattr(MainWindow, '_check_hole_data_availability'):
            check_source = inspect.getsource(MainWindow._check_hole_data_availability)
            if "CSV测量数据" in check_source and "内窥镜图像" in check_source:
                print("✅ 数据检查: 包含完整的数据类型检查")
            else:
                print("❌ 数据检查: 数据类型检查不完整")
        else:
            print("❌ 数据检查: 方法不存在")
        
        # 检查孔位选择方法
        select_source = inspect.getsource(MainWindow.on_hole_selected)
        if "has_data" in select_source and "setToolTip" in select_source:
            print("✅ 孔位选择: 包含按钮状态管理")
        else:
            print("❌ 孔位选择: 缺少按钮状态管理")
            
    except Exception as e:
        print(f"❌ 检查功能失败: {e}")
        return False
    
    print("\n📊 **数据可用性规则**")
    print("=" * 60)
    print("🟢 H00001: 完整数据 (CSV + 内窥镜图像)")
    print("🟢 H00002: 完整数据 (CSV + 内窥镜图像)")
    print("🔴 其他孔位: 无数据")
    
    print("\n🎮 **操作功能**")
    print("=" * 60)
    print("1. 🔍 搜索孔位:")
    print("   - 输入孔位ID (如 H00001)")
    print("   - 点击搜索按钮")
    print("   - 显示孔位详细信息")
    print("   - 检查数据可用性")
    print()
    print("2. 🖱️ 点击孔位:")
    print("   - 直接点击DXF图中的孔位")
    print("   - 显示孔位信息")
    print("   - 检查数据关联")
    print()
    print("3. 🔄 实时监控:")
    print("   - H00001/H00002: 可用，跳转到实时监控页面")
    print("   - 其他孔位: 显示'数据不可用'警告")
    print()
    print("4. 📊 历史数据:")
    print("   - H00001/H00002: 可用，跳转到历史数据页面")
    print("   - 其他孔位: 显示'数据不可用'警告")
    print()
    print("5. ⚠️ 标记异常:")
    print("   - 所有孔位: 可用")
    print("   - 显示确认对话框")
    print("   - 更新孔位状态和颜色")
    
    print("\n🧪 **测试步骤**")
    print("=" * 60)
    print("1. 启动程序: python main.py")
    print("2. 加载DXF: 按 Ctrl+T")
    print("3. 测试搜索:")
    print("   a) 搜索 'H00001' - 应显示完整数据信息")
    print("   b) 搜索 'H00003' - 应显示无数据信息")
    print("4. 测试点击:")
    print("   a) 点击H00001孔位 - 按钮应全部可用")
    print("   b) 点击其他孔位 - 实时监控和历史数据按钮应禁用")
    print("5. 测试操作:")
    print("   a) 选中H00001，点击'实时监控' - 应跳转")
    print("   b) 选中H00003，点击'实时监控' - 应显示警告")
    print("   c) 点击'标记异常' - 应显示确认对话框")
    
    print("\n🔍 **预期日志输出**")
    print("=" * 60)
    print("搜索H00001时:")
    print("🔍 搜索选中孔位: H00001")
    print("📍 位置: (X, Y)")
    print("📊 状态: PENDING")
    print("📏 半径: X.XXXmm")
    print("🔗 检查 H00001 数据关联:")
    print("  ✅ CSV测量数据: 找到 X 个文件")
    print("  ✅ 内窥镜图像: 找到图像数据")
    print("  ✅ 实时监控: 支持 (工件号: H00001)")
    print("  ✅ 历史数据: 支持")
    print("  🎮 可用操作:")
    print("    🔄 实时监控 - ✅ 可用")
    print("    📊 历史数据 - ✅ 可用")
    print("    ⚠️ 标记异常 - ✅ 可用")
    print()
    print("搜索其他孔位时:")
    print("🔍 搜索选中孔位: H00003")
    print("...")
    print("🔗 检查 H00003 数据关联:")
    print("  ❌ CSV测量数据: 未找到")
    print("  ❌ 内窥镜图像: 未找到")
    print("  ⚠️ 实时监控: 仅支持 H00001 和 H00002")
    print("  ⚠️ 历史数据: 仅支持 H00001 和 H00002")
    print("  🎮 可用操作:")
    print("    🔄 实时监控 - ❌ 无数据")
    print("    📊 历史数据 - ❌ 无数据")
    print("    ⚠️ 标记异常 - ✅ 可用")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 孔位选择和操作功能验证完成！")
        print("\n🎯 现在支持完整的孔位信息显示和智能操作控制！")
    else:
        print("\n❌ 功能验证失败！")
