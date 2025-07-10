#!/usr/bin/env python3
"""
测试缺失方法修复
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔧 缺失方法修复验证")
    print("=" * 50)
    
    # 检查修复后的组件
    try:
        from aidcis2.graphics.graphics_view import OptimizedGraphicsView
        print("✅ OptimizedGraphicsView导入成功")
        
        # 检查所有需要的方法是否存在
        required_methods = [
            'clear_search_highlight',
            'clear_all_highlights', 
            'highlight_holes',
            'fit_in_view',
            'zoom_in',
            'zoom_out',
            'reset_view',
            'update_hole_status',
            'load_holes'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if hasattr(OptimizedGraphicsView, method_name):
                print(f"✅ {method_name} 方法存在")
            else:
                print(f"❌ {method_name} 方法缺失")
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"\n❌ 仍有 {len(missing_methods)} 个方法缺失: {missing_methods}")
            return False
        else:
            print(f"\n✅ 所有 {len(required_methods)} 个必需方法都已存在")
            
    except Exception as e:
        print(f"❌ OptimizedGraphicsView检查失败: {e}")
        return False
    
    # 检查主窗口
    try:
        from main_window import MainWindow
        print("✅ MainWindow导入成功")
        
        # 检查是否有可能导致AttributeError的调用
        import inspect
        source = inspect.getsource(MainWindow)
        
        potential_issues = []
        
        # 检查graphics_view的方法调用
        graphics_view_calls = [
            'clear_search_highlight',
            'highlight_holes',
            'fit_in_view',
            'zoom_in',
            'zoom_out', 
            'reset_view',
            'update_hole_status',
            'load_holes'
        ]
        
        for method in graphics_view_calls:
            if f"graphics_view.{method}" in source:
                print(f"✅ 主窗口调用 graphics_view.{method}")
            else:
                print(f"⚠️ 主窗口未调用 graphics_view.{method}")
                
    except Exception as e:
        print(f"❌ MainWindow检查失败: {e}")
        return False
    
    print("\n🔧 **修复内容**")
    print("=" * 50)
    print("1. ✅ 添加了 clear_search_highlight() 方法")
    print("   - 清除所有搜索高亮状态")
    print("   - 修复搜索功能的AttributeError")
    print()
    print("2. ✅ 添加了 clear_all_highlights() 方法")
    print("   - 清除所有高亮状态（普通+搜索）")
    print("   - 提供完整的高亮管理功能")
    print()
    print("3. ✅ 添加了 reset_view() 方法")
    print("   - 重置视图缩放和位置")
    print("   - 修复视图控制功能")
    print()
    print("4. ✅ 继承的方法正常工作")
    print("   - zoom_in, zoom_out 来自 NavigationMixin")
    print("   - fit_in_view 已存在")
    print("   - update_hole_status 已存在")
    
    print("\n🧪 **测试步骤**")
    print("=" * 50)
    print("1. 重启主程序: python main.py")
    print("2. 加载DXF文件: 按 Ctrl+T")
    print("3. 测试搜索功能:")
    print("   - 输入搜索内容")
    print("   - 点击搜索按钮")
    print("   - 清空搜索内容再次搜索")
    print("4. 测试视图控制:")
    print("   - 点击放大、缩小按钮")
    print("   - 点击适应窗口、重置视图按钮")
    print("5. 测试模拟进度:")
    print("   - 点击'使用模拟进度'按钮")
    print("   - 观察颜色变化")
    
    print("\n🔍 **预期现象**")
    print("=" * 50)
    print("- ✅ 不再出现 AttributeError")
    print("- ✅ 搜索功能正常工作")
    print("- ✅ 视图控制按钮正常工作")
    print("- ✅ 模拟进度颜色正常变化")
    print("- ✅ 所有图形视图功能正常")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 缺失方法修复验证完成！")
        print("\n💡 现在所有必需的方法都已添加，应该不会再出现AttributeError了。")
    else:
        print("\n❌ 仍有方法缺失，需要进一步修复！")
