#!/usr/bin/env python3
"""
快速修复验证脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def verify_color_fix():
    """验证颜色修复"""
    print("🔵 验证检测中颜色修复")
    print("-" * 30)
    
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查V2模拟方法
        v2_source = inspect.getsource(MainWindow._update_simulation_v2)
        
        if "QColor(0, 123, 255)" in v2_source:
            print("✅ 检测中颜色已修复为蓝色")
        else:
            print("❌ 检测中颜色未修复")
            return False
        
        if "🔵 V2:" in v2_source:
            print("✅ 日志emoji已更新为蓝色")
        else:
            print("❌ 日志emoji未更新")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 颜色修复验证失败: {e}")
        return False

def verify_ui_fix():
    """验证UI显示修复"""
    print("\n🖥️ 验证孔位信息显示修复")
    print("-" * 30)
    
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查UI更新方法
        ui_source = inspect.getsource(MainWindow.update_hole_info_display)
        
        if "UI更新:" in ui_source:
            print("✅ UI更新日志已添加")
        else:
            print("❌ UI更新日志未添加")
            return False
        
        if ".update()" in ui_source:
            print("✅ 强制UI刷新已添加")
        else:
            print("❌ 强制UI刷新未添加")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ UI修复验证失败: {e}")
        return False

def verify_data_check():
    """验证数据检查功能"""
    print("\n📊 验证数据可用性检查")
    print("-" * 30)
    
    try:
        from main_window.main_window import MainWindow
        
        # 创建窗口实例
        window = MainWindow()
        
        # 测试H00001（有数据）
        result_h1 = window._check_hole_data_availability('H00001')
        if result_h1['realtime_support']:
            print("✅ H00001数据检查正确（支持实时监控）")
        else:
            print("❌ H00001数据检查错误")
            return False
        
        # 测试H00003（无数据）
        result_h3 = window._check_hole_data_availability('H00003')
        if not result_h3['realtime_support']:
            print("✅ H00003数据检查正确（不支持实时监控）")
        else:
            print("❌ H00003数据检查错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据检查验证失败: {e}")
        return False

def verify_button_logic():
    """验证按钮逻辑"""
    print("\n🎮 验证按钮控制逻辑")
    print("-" * 30)
    
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查孔位选择方法
        select_source = inspect.getsource(MainWindow.on_hole_selected)
        
        if "has_data" in select_source and "setEnabled" in select_source:
            print("✅ 按钮状态控制逻辑已添加")
        else:
            print("❌ 按钮状态控制逻辑未添加")
            return False
        
        if "setToolTip" in select_source:
            print("✅ 按钮工具提示已添加")
        else:
            print("❌ 按钮工具提示未添加")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 按钮逻辑验证失败: {e}")
        return False

def verify_operation_methods():
    """验证操作方法"""
    print("\n🔄 验证操作方法修复")
    print("-" * 30)
    
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查实时监控方法
        realtime_source = inspect.getsource(MainWindow.goto_realtime)
        if "H00001" in realtime_source and "H00002" in realtime_source:
            print("✅ 实时监控数据检查已添加")
        else:
            print("❌ 实时监控数据检查未添加")
            return False
        
        # 检查历史数据方法
        history_source = inspect.getsource(MainWindow.goto_history)
        if "H00001" in history_source and "H00002" in history_source:
            print("✅ 历史数据检查已添加")
        else:
            print("❌ 历史数据检查未添加")
            return False
        
        # 检查标记异常方法
        mark_source = inspect.getsource(MainWindow.mark_defective)
        if "确认标记异常" in mark_source:
            print("✅ 标记异常确认对话框已添加")
        else:
            print("❌ 标记异常确认对话框未添加")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 操作方法验证失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🔧 孔位选择和操作功能修复验证")
    print("=" * 50)
    
    all_passed = True
    
    # 验证各个修复
    if not verify_color_fix():
        all_passed = False
    
    if not verify_ui_fix():
        all_passed = False
    
    if not verify_data_check():
        all_passed = False
    
    if not verify_button_logic():
        all_passed = False
    
    if not verify_operation_methods():
        all_passed = False
    
    print("\n" + "=" * 50)
    print("📊 验证结果总结")
    print("=" * 50)
    
    if all_passed:
        print("✅ 所有修复验证通过！")
        print("\n🎯 修复内容:")
        print("1. 🔵 检测中颜色: 橙色 → 蓝色")
        print("2. 🖥️ 孔位信息显示: 添加UI更新和强制刷新")
        print("3. 📊 数据可用性: H00001/H00002有数据，其他无数据")
        print("4. 🎮 按钮控制: 智能启用/禁用和工具提示")
        print("5. 🔄 操作方法: 数据检查和确认对话框")
        
        print("\n🧪 测试建议:")
        print("1. 运行完整测试: python run_all_tests.py")
        print("2. 手动测试: python main.py")
        print("   - 加载DXF: 按 Ctrl+T")
        print("   - 搜索H00001: 应显示完整信息")
        print("   - 运行模拟: 检测中应显示蓝色")
        print("   - 测试按钮: 有数据时可用，无数据时禁用")
        
    else:
        print("❌ 部分修复验证失败！")
        print("请检查失败的项目并重新修复。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 修复验证成功！")
        sys.exit(0)
    else:
        print("\n💥 修复验证失败！")
        sys.exit(1)
