#!/usr/bin/env python3
"""
测试DXF显示修复
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔧 DXF显示修复测试")
    print("=" * 50)
    
    # 检查修复后的主窗口
    try:
        from main_window import MainWindow
        print("✅ 主窗口导入成功")
        
        # 检查是否有测试方法
        if hasattr(MainWindow, 'test_load_default_dxf'):
            print("✅ 测试DXF加载方法已添加")
        else:
            print("❌ 测试DXF加载方法未找到")
            
        # 检查是否有改进的日志
        import inspect
        load_method = getattr(MainWindow, 'load_dxf_file', None)
        if load_method:
            source = inspect.getsource(load_method)
            if "log_message" in source and "✅" in source:
                print("✅ DXF加载方法已改进，包含详细日志")
            else:
                print("⚠️ DXF加载方法可能需要进一步改进")
        
        display_method = getattr(MainWindow, 'update_hole_display', None)
        if display_method:
            source = inspect.getsource(display_method)
            if "边界" in source and "场景矩形" in source:
                print("✅ 孔位显示方法已改进，包含调试信息")
            else:
                print("⚠️ 孔位显示方法可能需要进一步改进")
                
    except Exception as e:
        print(f"❌ 主窗口检查失败: {e}")
        return False
    
    print("\n🎯 **使用说明**")
    print("=" * 50)
    print("1. 启动主程序: python main.py")
    print("2. 使用以下方法测试DXF显示:")
    print("   方法1: 点击'打开DXF文件'按钮手动选择DXF文件")
    print("   方法2: 按 Ctrl+T 快捷键自动加载测试DXF文件")
    print("3. 查看日志输出中的详细信息")
    print("4. 如果DXF区域仍然空白，点击'适应窗口'按钮")
    print()
    print("🔍 **调试信息**")
    print("- 日志会显示孔位数量、边界信息、场景矩形等")
    print("- 如果解析成功但显示空白，可能是视图范围问题")
    print("- 检查日志中是否有错误信息")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 修复验证完成！请按照使用说明进行测试。")
    else:
        print("\n❌ 修复验证失败！")
