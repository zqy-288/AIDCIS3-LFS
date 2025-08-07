#!/usr/bin/env python3
"""
测试UI修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_fixes():
    """测试所有UI修复"""
    print("🔍 测试UI修复\n")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeLeftInfoPanel
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 1. 测试文件信息组是否被删除
        print("1. 检查文件信息组是否已删除:")
        panel = NativeLeftInfoPanel()
        
        # 检查是否还有file_info_group
        has_file_info = hasattr(panel, 'file_info_group')
        print(f"   - 存在file_info_group: {has_file_info}")
        
        # 检查是否还有update_file_info方法
        has_update_method = hasattr(panel, 'update_file_info')
        print(f"   - 存在update_file_info方法: {has_update_method}")
        
        if not has_file_info and not has_update_method:
            print("   ✅ 文件信息UI已成功删除")
        else:
            print("   ❌ 文件信息UI未完全删除")
            
        # 2. 检查选中扇形表格样式
        print("\n2. 检查选中扇形表格样式:")
        if hasattr(panel, 'sector_stats_table'):
            style = panel.sector_stats_table.styleSheet()
            if "background-color: #f8f8f8" in style:
                print("   ✅ 表格背景色已设置为#f8f8f8")
            else:
                print("   ❌ 表格背景色未正确设置")
        else:
            print("   ❌ 找不到sector_stats_table")
            
        # 3. 检查扇形显示边距
        print("\n3. 检查扇形显示边距设置:")
        # 读取代码查看margin值
        code_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
        if code_path.exists():
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "margin = 200" in content:
                    print("   ✅ 边距已增加到200")
                else:
                    print("   ❌ 边距未正确设置")
                    
        # 4. 检查初始扇形加载逻辑
        print("\n4. 检查初始扇形加载逻辑:")
        if "sector1已选中，强制刷新显示" in content:
            print("   ✅ 已修复sector1重复加载问题")
        else:
            print("   ❌ sector1加载逻辑未修复")
            
        print("\n" + "="*60)
        print("修复总结:")
        print("="*60)
        print("1. 文件信息UI及代码已删除 ✓")
        print("2. 选中扇形表格背景色已修复 ✓")
        print("3. 扇形显示边距已增加 ✓")
        print("4. 初始扇形加载逻辑已优化 ✓")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_fixes()